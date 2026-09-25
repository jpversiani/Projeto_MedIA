The user wants me to create a JavaScript file for offline sync indicator functionality for a medical project (Projeto MedIA) - a Brazilian SUS/APS (Primary Health Care) system. The task is:

1. Create `backend/app/static/js/offline_sync_indicator.js`
2. Detect online/offline status via `navigator.onLine`
3. Manage IndexedDB for local contingency storage
4. Display visual badge at top of medical record showing "Nº de atendimentos aguardando upload" (number of appointments waiting for upload)

The guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest test coverage.

Since the main deliverable is a JavaScript file, I should focus on that, but given the guidelines mention Python testing with pytest, I should probably also provide:
1. The main JavaScript file (offline_sync_indicator.js)
2. Possibly a Python test file for testing the JS (or at least a test that validates the static file exists and serves correctly)
3. Maybe a backend endpoint for sync that the JS would call

Let me think about what makes sense here. The task C37 is specifically about the frontend JS file. But the architecture guidelines mention Python backend. A complete solution would include:

1. **`backend/app/static/js/offline_sync_indicator.js`** - The main deliverable:
   - Online/offline detection via `navigator.onLine` + `online`/`offline` events
   - IndexedDB management for contingency storage of appointments (atendimentos)
   - Visual badge showing count of pending uploads
   - Sync logic when back online

2. **Backend support** - Since the JS needs an endpoint to sync to, I could provide:
   - A Pydantic v2 schema for the sync payload (AtendimentoSync)
   - A SQLAlchemy 2.0 model or at least the endpoint
   - Validation of CNS/CPF

3. **Tests** - pytest tests. For JS, typically you'd use Jest, but the guidelines say pytest. I can write pytest tests that:
   - Validate the JS file exists and is served
   - Test the backend sync endpoint
   - Possibly use pytest-playwright or just test the API side

Let me design the JavaScript file carefully:

```javascript
/**
 * offline_sync_indicator.js
 * Projeto MedIA — C37: Indicador e Armazenamento Local de Sincronização Offline
 * ...
 */
```

Key features:
1. **Connection monitoring**: `navigator.onLine`, `window.addEventListener('online'/'offline')`, plus periodic ping to a health endpoint (since navigator.onLine can be unreliable - it only detects network interface status, not actual connectivity).

2. **IndexedDB management**:
   - DB name: `media_offline_db`, version 1
   - Object store: `atendimentos_pendentes` with keyPath `id_local` (UUID generated client-side)
   - Indexes: `created_at`, `sync_status`
   - Store SOAP-structured appointments with CIAP-2 codes, CID-10, patient CNS/CPF
   - CRUD: save pending appointment, list, count, mark synced, remove

3. **Badge UI**:
   - Fixed position badge at top of prontuário
   - Shows "N atendimentos aguardando upload" 
   - States: online (green/synced), offline (yellow/red warning), syncing (blue spinner)
   - ARIA attributes for accessibility

4. **Sync queue processing**:
   - When online, POST pending appointments to `/api/v1/prontuario/atendimentos/sync`
   - Retry with exponential backoff
   - CSRF token handling
   - Idempotency via `id_local` (client-generated UUID) to avoid duplicates

5. **LGPD considerations**: Store minimal data locally, sensitive health data in IndexedDB should be encrypted ideally — at minimum note it. Actually for a real medical app, storing PHI locally is sensitive. I should mention that data is stored locally only for contingency and cleared after sync. Maybe add a note about session-based clearing.

Let me write the JS with strict quality:

```javascript
'use strict';

/**
 * ============================================================================
 * Projeto MedIA — C37: Indicador e Armazenamento Local de Sincronização Offline
 * ============================================================================
 * ...
 */
```

Structure:
- IIFE or module pattern
- Constants for DB config
- `OfflineSyncIndicator` class or module object with methods:
  - `init(config)`
  - `_openDatabase()` — IndexedDB open with upgrade
  - `_saveAtendimento(payload)`
  - `_listPendentes()`
  - `_countPendentes()`
  - `_removeAtendimento(idLocal)`
  - `_updateBadge()`
  - `_setConnectionStatus(isOnline)`
  - `_processarFilaSync()`
  - `_pingServidor()`
  - Public API: `window.MedIAOfflineSync = { salvarAtendimento, ... }`

Also expose a global hook so the prontuário form can call `MedIAOfflineSync.salvarAtendimento(dados)` when a submit fails offline.

Data model for a pending appointment (aligned with SUS/APS):
```javascript
{
  id_local: uuid,           // idempotency key
  cns_profissional: ...,
  cns_paciente / cpf_paciente,
  cid10_cod, ciap2_cod,
  soap: { subjetivo, objetivo, avaliacao, plano },
  data_atendimento,
  ubs_id / unidade_saude_id,
  criado_em: ISO timestamp,
  tentativas_sync: 0,
  status: 'PENDENTE' | 'SINCRONIZADO' | 'ERRO'
}
```

Badge HTML injected at top of `#prontuario-container` or `body`:
```html
<div id="media-offline-badge" role="status" aria-live="polite">
  <span class="media-offline-badge__dot"></span>
  <span class="media-offline-badge__text">...</span>
</div>
```

CSS injected via a `<style>` tag or separate. I'll inject minimal CSS via JS to keep it self-contained (single-file deliverable).

Sync endpoint: `POST /api/v1/atendimentos/sync-lote` (batch). Payload: `{ atendimentos: [...] }`. Response: `{ sincronizados: [id_local...], rejeitados: [{id_local, motivo}] }`.

Retry: exponential backoff with jitter, max attempts (e.g., 5), then mark as ERRO but keep in DB for manual retry.

Also handle `visibilitychange` and `focus` to attempt sync when tab regains focus.

Now for the backend part — to make this a complete, testable vertical slice, I'll provide:

1. **Pydantic v2 schemas** (`backend/app/schemas/atendimento_sync.py`):
   - `AtendimentoSyncPayload` with validation of CNS (15 digits with check digit algorithm), CPF (11 digits with check digits), CID-10 format, CIAP-2 format (letter + 2 digits)
   - `AtendimentoSyncLote` (batch)
   - `AtendimentoSyncResultado`

2. **SQLAlchemy 2.0 model** — maybe just reference existing `Atendimento` model, or define a minimal one. To keep focused, I'll define the sync router that validates and persists. Actually, to keep the answer manageable, I'll provide:
   - `backend/app/schemas/atendimento_sync.py` (Pydantic v2, strict typing)
   - `backend/app/api/v1/endpoints/sync_offline.py` (FastAPI router)
   - `backend/app/utils/documentos.py` — CNS/CPF validators (or include in schemas)

3. **pytest tests**:
   - `backend/tests/test_sync_offline_api.py` — API tests with httpx/TestClient
   - `backend/tests/test_offline_sync_indicator_js.py` — validates the JS artifact is served with correct content-type and contains key functions (smoke test), since pytest is the mandated framework.

CNS validation algorithm (Brazilian SUS card):
- CNS must have 15 digits
- Starting with 1, 2, 7, 8, or 9
- Algorithm: for CNS starting with 1/2 (definitive): sum = sum over 15 digits of digit[i] * (15 - i); must be divisible by 11. Actually the standard algorithm:

For CNS [1|2] + 14 digits:
```
soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
if soma % 11 == 0: valid
```
For CNS starting with 7, 8, 9 (provisional): format 7XX XXX XXX XXX X00? The provisional ones: 898989... The algorithm for 7/8/9: 
```
cns must match: [789] + 11 digits + "0001"? 
```
Actually provisional CNS: 7, 8 or 9 followed by 14 digits where the last four are derived: the check is: take first 11 digits, compute via the same weight method... Let me recall the standard Python implementation:

```python
def valida_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] in '12':
        # soma ponderada
        soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
        return soma % 11 == 0
    elif cns[0] in '789':
        # provisional: 7/8/9 + 11 digits + 0001? 
        # Actually: cns[12:15] must be '000' + check? 
```

The standard algorithm for provisional CNS (7,8,9):
- The CNS has 15 digits: 7/8/9 + 11 random + 4 digits where the last 4 are computed: 
- Take the first 11 digits, compute rest: 
```
soma = sum(int(d) * w for d, w in zip(cns[:11], range(15, 5, -1)))  # weights 15..5
resto = soma % 11
dv = 11 - resto if resto > 1 else 0 - resto? 
```

Hmm, let me recall the official algorithm from DATASUS:

For CNS starting with 1 or 2:
```
soma = 0
for i in 0..14:
    soma += cns[i] * (15 - i)
resto = soma % 11
valid if resto == 0
```

For CNS starting with 7, 8 or 9 (temporary):
```
soma = 0
for i in 0..10 (first 11 digits):
    soma += cns[i] * (15 - i)
resto = soma % 11
if resto != 0:
    dv = 11 - resto
else:
    dv = 0
# then: pin = str(dv) + "0001"? 
```

Actually the known algorithm: for temporary CNS, digits 12-15 are: dv followed by "0001"? Let me recall the JS implementation widely used:

```javascript
function validaCNS(vetorCNS) {
  var soma = 0;
  if (vetorCNS[0] == '1' || vetorCNS[0] == '2') {
    for (i = 0; i < 15; i++) {
      soma += parseInt(vetorCNS[i]) * (15 - i);
    }
    if ((soma % 11) == 0) return true; else return false;
  } else {
    // 7,8,9
    soma = 0;
    for (i = 0; i < 11; i++) soma += parseInt(vetorCNS[i]) * (15 - i);
    var resto = soma % 11;
    var dv = 11 - resto;
    if (dv > 9) {
      // dv becomes two digits: 1 and dv-10
      var resultado = dv.toString(); // e.g., "10" or "11"
      var pin = resultado.split('');
      var pis = vetorCNS.substring(0, 11) + pin[0] + pin[1]; // 13 digits
      soma = 0;
      for (i = 0; i < 13; i++) soma += parseInt(pis[i]) * (15 - i);
      resto = soma % 11;
      var dvFinal = 11 - resto;
      var resultadoFinal = pis + dvFinal + "01"; // 15 digits? pis is 13, + dv + "01" = 15? 13+1+2 = 16. Hmm.
    }
  }
}
```

Let me get the canonical one right. The official DATASUS algorithm (from the "Rotina de validação do CNS"):

```
Para CNS iniciando com 1 ou 2:
  soma = Σ (dígito_i × peso_i), pesos de 15 a 1 (posição 0 → peso 15, posição 14 → peso 1)
  válido se soma % 11 == 0

Para CNS iniciando com 7, 8 ou 9:
  soma = Σ (dígito_i × peso_i) para os 11 primeiros dígitos, pesos 15 a 5
  resto = soma % 11
  dv = 11 - resto
  se dv > 9: dv vira dois dígitos (ex: 10 → '1','0'), formando "pis" de 13 dígitos:
      pis = primeiros 11 dígitos + os dois dígitos do dv
      refaz soma com pesos 15 a 3 sobre os 13 dígitos
      resto = soma % 11
      dv = 11 - resto
      resultado = pis + dv + "01"  → 13 + 1 + 2 = 16? 
```

Hmm, that gives 16. Let me recount: pis = 11 + 2 = 13 digits. Then resultado = pis (13) + dv (1) + "01" (2) = 16. That's wrong; CNS is 15 digits.

Let me look at the widely-circulated implementation:

```javascript
function validaCNS(vetorCNS) {
  var soma = new Number(0);
  var i = new Number(0);
  var dv = new Number(0);
  var pis = new String();
  var resultado = new String();
  var resto = 0;
  var mult = new Array(15);

  if (window.event) { ... }

  if (vetorCNS.trim().length != 15) { return false; }

  // Se os primeiros caracteres são 1 ou 2
  if ((vetorCNS.charAt(0) == '1') || (vetorCNS.charAt(0) == '2')) {
    for (i = 0; i < 15; i++) {
      soma = soma + (parseInt(vetorCNS.substring(i, i + 1)) * (15 - i));
    }
    resto = (soma % 11);
    if (resto != 0) {
      return false;
    } else {
      return true;
    }
  } else {
    // Se os primeiros caracteres são 7, 8 ou 9
    for (i = 0; i < 11; i++) {
      soma = soma + (parseInt(vetorCNS.substring(i, i + 1)) * (15 - i));
    }
    resto = soma % 11;
    dv = 11 - resto;
    if (dv > 9) {
      pis = vetorCNS + '0';  // hmm no
    }
    ...
  }
}
```

Actually the canonical one from DATASUS (used in many repos):

```javascript
} else {
  soma = 0;
  for (i = 0; i < 11; i++) {
    soma = soma + (parseInt(vetorCNS.substring(i, i + 1)) * (15 - i));
  }
  resto = soma % 11;
  dv = 11 - resto;
  if (dv > 9) {
    pis = vetorCNS.substring(0, 11) + '0' + dv;  // no...
  }
}
```

Hmm, I remember the actual algorithm: when dv > 9, you split dv into two digits and add them into the sequence, then recompute:

```javascript
if (dv > 9) {
  resultado = dv + '';  // "10" or "11"
  pis = vetorCNS.substring(0, 11) + resultado.substring(0, 1) + resultado.substring(1, 2);
  // pis has 13 digits
  soma = 0;
  for (i = 0; i < 13; i++) {
    soma = soma + (parseInt(pis.substring(i, i + 1)) * (15 - i));
  }
  resto = soma % 11;
  dv = 11 - resto;
  resultado = pis + dv + '01';  // 13 + 1 + 2 = 16?? 
}
```

Wait — pis = 11 + 2 = 13. resultado = pis + dv + "01" = 13 + 1 + 2 = 16. That can't be right.

Let me reconsider. Maybe pis = vetorCNS.substring(0, 11) + resultado.substring(0,1) — only first digit? No...

Actually, I recall the correct algorithm now. The provisional CNS: digits 1-11 are random, digits 12-15 are check. The check computation:

1. soma = Σ_{i=0}^{10} d_i × (15 − i)
2. resto = soma % 11
3. dv = 11 − resto
4. If dv == 10 or 11, then dv is treated as two characters appended, making the base 13 digits, then recompute: soma2 = Σ_{i=0}^{12} base_i × (15 − i), resto2 = soma2 % 11, dv2 = 11 − resto2, and final = base + dv2 + "01"? That's 13 + 1 + 2 = 16 again. Hmm.

Wait — maybe when dv > 9, the "01" suffix replaces... Let me think about actual valid provisional CNS numbers. A known valid provisional CNS example: "700000000000000"? Let's test with the 1/2 algorithm... no, that's for 7.

Known test vectors for provisional CNS: "898989000000000"? Hmm