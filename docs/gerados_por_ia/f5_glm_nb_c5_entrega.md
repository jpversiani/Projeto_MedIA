The user wants me to create a JavaScript file for offline sync indicator functionality for a medical project (MedIA) - specifically `backend/app/static/js/offline_sync_indicator.js`. This should:

1. Detect online/offline status via `navigator.onLine`
2. Manage IndexedDB for local contingency storage
3. Display a visual badge at the top of the medical record showing 'Nº de atendimentos aguardando upload' (Number of appointments awaiting upload)

The guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest test coverage.

Since the main task is a JavaScript file, but the guidelines mention Python testing, I should probably also provide:
1. The main JavaScript file (offline_sync_indicator.js)
2. Possibly a Python test file for testing the static asset/serving, or a pytest test that validates the JS file exists and has proper structure
3. Maybe a Pydantic model for the sync payload schema that the JS will use

Let me think about what makes sense architecturally:

The JavaScript file needs to:
- Listen to `online`/`offline` events
- Use IndexedDB to store pending appointments (atendimentos) when offline
- Show a badge with count of pending uploads
- Sync when back online
- Follow LGPD/SUS compliance (data should be encrypted or at least handled carefully)

For the Python side, I should create:
- A Pydantic schema for the sync payload (AtendimentoSync) with validation of CNS, CPF, CIAP-2 codes, CID-10 codes
- An API endpoint for batch sync (maybe just the schema, since the task focuses on the JS)
- Pytest tests

Let me design the JavaScript file:

```javascript
/**
 * MedIA — Indicador e Armazenamento Local de Sincronização Offline (C5)
 * ...
 */
```

Key components:
1. `OfflineSyncIndicator` class or IIFE module
2. IndexedDB wrapper with database name like `mediA_offline`, object store `pending_atendimentos`
3. Event listeners for `online`/`offline`
4. Badge rendering in DOM
5. Sync queue processing when online
6. CNS validation (basic checksum) before storing locally
7. LGPD considerations - data stored locally only, minimal necessary data

IndexedDB structure:
- DB: `media_offline_db` version 1
- Store: `pending_atendimentos` with keyPath `id` (uuid), indexes: `created_at`, `sync_status`
- Records: { id, cns, cpf, cid10, ciap2, soap: {subjetivo, objetivo, avaliacao, plano}, created_at, sync_status: 'pending' | 'syncing' | 'error', attempts }

Badge UI:
- Fixed position or at top of prontuário
- Shows "N atendimentos aguardando upload" when offline or pending > 0
- Green when synced, amber when pending, red when offline

For the Python side:
- `backend/app/schemas/sync.py` with Pydantic v2 models: `AtendimentoOfflinePayload`, `AtendimentoSyncBatch`, `SyncResponse`
- Validators: CNS (checksum algorithm), CPF (checksum), CIAP-2 (letter+2 digits), CID-10 (regex)
- `backend/tests/test_offline_sync.py` with pytest tests

Actually, the task says "crie backend/app/static/js/offline_sync_indicator.js" - the primary deliverable is the JS file. But the guidelines say to maintain pytest coverage. So I should include tests. Since it's a JS file, testing it with pytest would mean either:
1. Testing the API endpoint that receives the sync
2. Using a JS test runner via subprocess (not ideal)
3. Testing that the file serves correctly and contains required functions

I think the most sensible approach: provide the JS file as the main deliverable, plus the Pydantic schema for the sync API contract (which the JS depends on), plus pytest tests for the schema/endpoint. Maybe also a simple pytest that validates the static file integrity (exists, has key functions, no syntax errors via node if available).

Let me write the code.

First, the JavaScript file:

```javascript
/* SPDX-License-Identifier: AGPL-3.0-or-later */
/**
 * MedIA — Módulo C5: Indicador e Armazenamento Local de Sincronização Offline
 * ---------------------------------------------------------------------------
 * - Detecta status de conectividade via navigator.onLine + eventos online/offline
 * - Persiste atendimentos em IndexedDB (contingência offline, LGPD art. 46 —
 *   dados mínimos, sem tráfego de PII enquanto offline)
 * - Exibe badge visual no topo do prontuário:
 *     "Nº de atendimentos aguardando upload"
 * - Padrões SUS/APS: SOAP, CIAP-2, CID-10, identificação CNS/CPF
 *
 * Uso:
 *   <script src="/static/js/offline_sync_indicator.js" defer></script>
 *   <div id="offline-sync-badge-root"></div>  (opcional; senão, injeta no body)
 *
 * API pública (window.MediaOfflineSync):
 *   .status()            -> {online, pending, syncing}
 *   .enqueue(atendimento) -> Promise<string id>
 *   .flush()             -> Promise<{sent, failed}>
 *   .onChange(cb)        -> registra listener de mudança de estado
 */
```

Then the implementation. Let me write it carefully:

```javascript
(function (global) {
  'use strict';

  // ------------------------------------------------------------------
  // Constantes
  // ------------------------------------------------------------------
  const DB_NAME = 'media_offline_db';
  const DB_VERSION = 1;
  const STORE_ATENDIMENTOS = 'pending_atendimentos';
  const SYNC_ENDPOINT = '/api/v1/sync/atendimentos';
  const MAX_BATCH = 50;
  const MAX_ATTEMPTS = 5;
  const RETRY_BACKOFF_MS = 15000;

  // ------------------------------------------------------------------
  // Validações leves (espelham Pydantic no backend — defesa em profundidade)
  // ------------------------------------------------------------------
  const RE_CNS = /^\d{15}$/;
  const RE_CPF = /^\d{11}$/;
  const RE_CIAP2 = /^[A-Z]\d{2}$/;
  const RE_CID10 = /^[A-TV-Z][0-9][0-9AB](\.[0-9A-TV-Z]{1,4})?$/;

  function validarCNS(cns) {
    // Algoritmo oficial de dígito verificador do CNS (Cartão Nacional de Saúde)
    if (!RE_CNS.test(cns)) return false;
    if (/^[7-9]/.test(cns)) return false; // CNS provisório legado não aceito p/ titular
    const soma = cns.split('').reduce((acc, d, i) => acc + Number(d) * (15 - i), 0);
    return soma % 11 === 0;
  }
  ...
```

Wait, the CNS validation algorithm: The standard CNS checksum uses weights 15 down to 1 (pesos de 15 a 1... actually it's multiplication by weights starting at 5? Let me recall.

The CNS validation algorithm (official from DATASUS):
- CNS must have 15 digits
- Starting numbers: 1, 2, 7, 8, 9 (7-9 are provisional)
- Algorithm: multiply each digit by weights from 15 down to 1? No...

Actually the correct algorithm: 
```
soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
if soma % 11 == 0: valid
```
Yes, that's the standard: pesos 15,14,13,...,1. The remainder must be 0. Let me verify with a known valid CNS: 000 0000 0000 0000? soma = 0, 0 % 11 == 0 — that would pass, but all zeros is typically rejected. Common test: CNS "116 8094 7610 0004"? Hmm, I don't remember exact valid CNS examples. The standard algorithm from DATASUS documentation:

```
function validaCNS(v) {
  var soma = 0;
  if (v.trim().length != 15 || !/^[1-8]/.test(v)) return false;
  for (var i = 0; i < 15; i++) {
    var j = 15 - i;
    soma += v[i] * j;
  }
  return soma % 11 == 0;
}
```

Yes, that's the widely used implementation. First digit must be 1-8 (9 is also used for provisional in some docs; actually provisional cards start with 7, 8, 9). The DATASUS routine accepts 1-9? The common JS implementation checks `/^[1-2|7-9]/`... Let me just check first char in [1-9] and use the soma % 11 == 0. Actually many implementations: `if (v[0] == '0') return false;` Hmm.

The official DATASUS validation (from the "Rotinas de validação" doc):
- CNS definitive: starts with 1 or 2 (or 7, 8, 9 for provisional)
- The checksum: sum of digit_i * (15 - i) must be divisible by 11.

I'll implement: 15 digits, first digit in 1-9, soma % 11 === 0. That's safe.

CPF validation: standard mod-11 check digits.

```javascript
function validarCPF(cpf) {
  if (!RE_CPF.test(cpf)) return false;
  if (/^(\d)\1{10}$/.test(cpf)) return false; // sequências repetidas
  const calcDV = (base, pesoInicial) => {
    let soma = 0;
    for (let i = 0; i < base.length; i++) soma += Number(base[i]) * (pesoInicial - i);
    const resto = (soma * 10) % 11;
    return resto === 10 ? 0 : resto;
  };
  return calcDV(cpf.slice(0, 9), 10) === Number(cpf[9]) &&
         calcDV(cpf.slice(0, 10), 11) === Number(cpf[10]);
}
```

Now the IndexedDB wrapper:

```javascript
function abrirDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (ev) => {
      const db = ev.target.result;
      if (!db.objectStoreNames.contains(STORE_ATENDIMENTOS)) {
        const store = db.createObjectStore(STORE_ATENDIMENTOS, { keyPath: 'id' });
        store.createIndex('idx_created_at', 'created_at', { unique: false });
        store.createIndex('idx_sync_status', 'sync_status', { unique: false });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}
```

Then operations: enqueue, countPending, listPending, markSynced, delete, updateAttempts.

Badge UI:

```javascript
function renderBadge(state) {
  // badge no topo do prontuário
}
```

Badge states:
- offline + pending > 0: amber/red "N atendimento(s) aguardando upload — modo offline"
- offline + pending == 0: "Modo offline — dados salvos localmente"
- online + pending > 0: "N aguardando upload — sincronizando..."
- online + pending == 0: hidden or green "Sincronizado"

Accessibility: role="status", aria-live="polite".

Sync flush: POST batches to SYNC_ENDPOINT with fetch, handle 2xx -> delete records; 4xx validation error -> mark as error (don't retry infinitely); 5xx -> keep pending, backoff.

Also handle `visibilitychange` and periodic retry timer.

Storage quota / LGPD: keep minimal data, provide `clearAll()`.

Let me also think about the "prontuário" integration: the badge should be at the top of the prontuário page. I'll look for a container `#prontuario-root` or `[data-prontuario-top]` or inject at top of `main`.

Now the Python side. I'll create:

1. `backend/app/schemas/sync.py` — Pydantic v2 schemas:

```python
from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


class Identificador(str, Enum): ...
```

CNS validation in Python:

```python
def validar_cns(cns: str) -> bool:
    if not re.fullmatch(r"\d{15}", cns):
        return False
    if cns[0] not in "123456789":
        return False
    soma = sum(int(d) * (15 - i) for i, d in enumerate(cns))
    return soma % 11 == 0
```

CPF:

```python
def validar_cpf(cpf: str) -> bool:
    if not re.fullmatch(r"\d{11}", cpf):
        return False
    if len(set(cpf)) == 1:
        return False
    def dv(base: str, peso: int) -> int:
        s = sum(int(d) * (peso - i) for i, d in enumerate(base))
        r = (s * 10) % 11
        return 0 if r == 10 else r
    return dv(cpf[:9], 10) == int(cpf[9]) and dv(cpf[:10], 11) == int(cpf[10])
```

CIAP-2: letter + 2 digits: `^[A-Z]\d{2}$` (CIAP-2 codes like A01, K29, P76... actually CIAP-2 codes are letter + 2 digits, e.g., "A01", "K29"). Yes.

CID-10: `^[A-TV-Z]\d{2}(\.\d{1,2})?$` roughly. CID-10 categories: letter A-Z except U? Actually U is used (U04.9 SARS, U07.1 COVID). Hmm, CID-10 includes U codes (U00-U99 added later). The regex `[A-Z]\d{2}` is fine. Some use `[A-TV-Z]` excluding U for older versions. I'll use `[A-Z]\d{2}(\.\d{0,2})?` to be safe. Actually the JS one I wrote excludes U — let me include U since COVID-19 is U07.1. I'll use `[A-Z]\d{2}(\.[0-9A-Z]{1,4})?`.

Models:

```python
class SOAPRecord(BaseModel):
    subjetivo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=8000)]
    objetivo: ...
    avaliacao: ...
    plano: ...

class AtendimentoOfflineIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id_cliente: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-...", min_length=36, max_length=36)]  # UUID gerado no cliente
    cns: Annotated[str, StringConstraints(min_length=15, max_length=15, pattern=r"^\d{15}$")]
    cpf: ... | None
    cid10: list[str] | None
    ciap2: list[str] | None
    soap: SOAPRecord
    criado_em: datetime
    ...
```

At least one of cid10/ciap2 required (model_validator) — SUS/APS requires either CIAP-2 (APS) or CID-10.

Batch:

```python
class SyncBatchIn(BaseModel):
    atendimentos: list[AtendimentoOfflineIn] = Field(min_length=1, max_length=50)

class SyncResultItem(BaseModel):
    id_cliente: str
    status: Literal["aceito", "duplicado", "rejeitado"]
    detalhe: str | None = None

class SyncBatchOut(BaseModel):
    processados: int
    aceitos: int
    resultados: list[SyncResultItem]
```

2. SQLAlchemy 2.0 model for received sync records — maybe `backend/app/models/atendimento_sync.py`:

```python
class AtendimentoSync(Base):
    __tablename__ = "atendimento_sync"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    id_cliente: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True)  # idempotência
    cns: Mapped[str] = mapped_column(String(15), index=True)
    ...
```

Hmm, but the task is focused on the JS. Including a full endpoint + model + tests might be a lot, but the guidelines say "cobertura de testes automatizados com pytest" and "tipagem estrita com Pydantic v2 e SQLAlchemy 2.0". I think a reasonable scope:

- Main deliverable: `backend/app/static/js/offline_sync_indicator.js` (complete, production-quality)
- Supporting contract: `backend/app/schemas/sync.py` (Pydantic v2) — the API contract the JS consumes
- SQLAlchemy 2.0 model for persistence: `backend/app/models/atendimento_sync.py`
- Router: `backend/app/routers/sync.py` (endpoint POST /api/v1/sync/atendimentos) — maybe brief
- Tests: `backend/tests/test_offline_sync.py` with pytest covering validators, schema, endpoint, and a static-asset integrity test (file exists, contains required functions, balanced braces / basic checks; optionally run `node --check` if node available).

That's a comprehensive deliverable. Let me be careful about length — this could get very long. The user asked to "Execute com precisão" — they want the code. I'll aim for complete but not bloated. I'll keep the router concise.

Let me now write the JS file in full.

```javascript
/* SPDX-License-Identifier: AGPL-3.0-or-later */
/**
 * MedIA — C5: Indicador e Armazenamento Local de Sincronização Offline
 * =====================================================================
 *
 * Responsabilidades
 * -----------------
 * 1. Detectar conectividade (navigator.onLine + eventos online/offline +
 *    probe real de rede para mitigar falsos positivos de hotspots cativos).
 * 2. Persistir atendimentos