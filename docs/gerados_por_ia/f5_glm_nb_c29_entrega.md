The user wants me to create a JavaScript file for offline sync indicator functionality for a medical project (MedIA). The task is:

1. Create `backend/app/static/js/offline_sync_indicator.js`
2. Detect online/offline status via `navigator.onLine`
3. Manage IndexedDB for local contingency storage
4. Display a visual badge at the top of the medical record showing "Nº de atendimentos aguardando upload" (Number of appointments awaiting upload)

The guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest test coverage.

However, the actual file requested is a JavaScript file. The Python guidelines seem to be general project guidelines, but the specific task is the JS file. I should focus on creating a high-quality JavaScript file, but I could also mention/include supporting Python backend pieces if relevant (like the sync endpoint contract), and possibly tests. But the primary deliverable is the JS file.

Let me think about what a well-architected offline sync indicator JS file should include:

1. **Online/Offline detection**:
   - `navigator.onLine` initial check
   - `window.addEventListener('online', ...)` and `window.addEventListener('offline', ...)`
   - Optionally periodic heartbeat ping to server to verify actual connectivity (navigator.onLine can be unreliable - it only detects network interface status, not actual internet connectivity)

2. **IndexedDB management**:
   - Database name, version, object stores
   - Store for pending appointments (atendimentos) awaiting upload
   - CRUD operations: add, getAll, delete, count, update
   - Handle IndexedDB unavailability (private browsing, old browsers)
   - Schema: appointment data with CIAP-2 codes, CID-10, SOAP notes, CNS/CPF patient identification, timestamp, sync status, retry count

3. **Visual badge**:
   - Badge at top of prontuário (medical record)
   - Shows count of pending appointments
   - States: online (green), offline (amber/red), pending count
   - ARIA attributes for accessibility
   - Update on changes

4. **Sync logic**:
   - When back online, attempt to sync pending items
   - Retry with exponential backoff
   - Conflict handling basics
   - CSRF token handling
   - Fetch to backend endpoint (e.g., `/api/v1/sync/atendimentos`)

5. **Data integrity for SUS/APS compliance**:
   - Store complete appointment data: patient CNS/CPF, CIAP-2 codes, CID-10, SOAP structure (S, O, A, P fields), professional ID, date, etc.
   - Validation before storing
   - UUID for idempotency (client-generated UUID to avoid duplicates on retry)

6. **Security considerations**:
   - Don't store sensitive data in plaintext? Ideally encrypt, but for a JS file, we can note that. Maybe basic structure for encryption hook.
   - Same-origin requests, credentials

Let me write a comprehensive, well-structured JS file with:
- IIFE or ES module pattern
- Configuration constants
- IndexedDB wrapper with Promises
- Status manager
- UI badge component (created dynamically or attached to existing element)
- Sync queue manager with retry/backoff
- Event system (CustomEvents)
- Public API exposure (e.g., `window.MedIAOfflineSync`)
- JSDoc comments

Also, since the guidelines mention pytest coverage, I should probably include a Python test file or at least mention how to test. But the JS file itself would be tested with Jest/Playwright typically. The guidelines say "Manter conformidade total e cobertura de testes automatizados com pytest" — maybe I should include a pytest test that verifies the static file is served and contains key elements, or a test for the sync endpoint contract. Let me include:

1. The main JS file (primary deliverable)
2. Optionally a small pytest test file that validates the static asset exists, is served, and includes required behaviors (basic smoke test via httpx/TestClient)
3. Maybe a brief note about the expected backend contract

Actually, let me think about scope. The task says "Execute com precisão conforme as diretrizes" — execute precisely according to guidelines. The main deliverable is the JS file. I'll create:

1. `backend/app/static/js/offline_sync_indicator.js` — the complete, production-quality JS
2. A pytest test file `backend/tests/static/test_offline_sync_indicator.py` or similar that smoke-tests the asset (existence, served route, key markers) — this aligns with the pytest guideline
3. Brief documentation of the sync API contract expected

Let me design the JS file carefully:

```javascript
/**
 * MedIA — Indicador e Armazenamento Local de Sincronização Offline (C29)
 * ...
 */
```

Structure:

```javascript
(function (global) {
  'use strict';

  // ===== Configuração =====
  const CONFIG = Object.freeze({
    DB_NAME: 'media_offline_db',
    DB_VERSION: 1,
    STORE_ATENDIMENTOS: 'atendimentos',
    STORE_META: 'meta',
    SYNC_ENDPOINT: '/api/v1/sync/atendimentos',
    HEALTH_ENDPOINT: '/api/v1/health',
    HEARTBEAT_INTERVAL_MS: 30000,
    MAX_RETRY_PER_ITEM: 5,
    BACKOFF_BASE_MS: 2000,
    BACKOFF_MAX_MS: 60000,
    BADGE_ID: 'media-offline-sync-badge',
    ...
  });
```

IndexedDB schema:
- Store `atendimentos`: keyPath `uuid` (client-generated UUID v4), indexes: `created_at`, `status`, `tentativas`
- Record fields (SUS/APS compliant):
  - `uuid`: string (idempotency key)
  - `paciente`: { cns, cpf, nome? } — CNS validated with 11 or 17 digits
  - `profissional_cns`: string
  - `ubs_id` / `cnes`: unit code
  - `data_atendimento`: ISO string
  - `soap`: { s, o, a, p } — SOAP method fields
  - `ciap2`: array of codes (e.g., "A01")
  - `cid10`: array of codes
  - `status`: 'pendente' | 'sincronizando' | 'sincronizado' | 'erro'
  - `tentativas`: number
  - `ultimo_erro`: string|null
  - `criado_em`: ISO timestamp
  - `atualizado_em`: ISO timestamp
  - `versao_esquema`: number

Validation functions:
- `validarCNS(cns)`: validates CNS according to SUS rules (11 digits starting with 1,2,7,8,9 or 17-digit provisional cards). The CNS checksum algorithm: sum with weights 15 down to 2 for first 11 digits... Let me recall the CNS validation algorithm:

For 11-digit CNS:
- Digits must start with 1, 2, 7, 8, or 9
- Multiply first 11 digits by weights 15,14,13,...,5
- Sum the results
- The check: `resto = soma % 11`, `dv = 11 - resto`. If dv == 11, dv = 0. If dv == 10... Actually the algorithm: 

The standard CNS validation:
```
soma = soma dos produtos dos 12 primeiros dígitos pelos pesos 15,14,...,4
resto = soma % 11
if resto != 0: dv = 11 - resto else dv = 0
```
Wait, let me be precise. The commonly used algorithm (from DATASUS):

```
pesos = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]  # for 15 digits
```

Actually for the 15-digit CNS (which includes the 11-digit + "000" + check?), the common algorithm:

The CNS has 15 digits. First 11 digits + 4 check digits? No — CNS is 15 digits: 7,8,9 starting ones have 11 digits + 4 more? Let me recall properly.

CNS (Cartão Nacional de Saúde) definitive cards have 15 digits, starting with 1, 2, 7, 8, or 9. The validation algorithm:

```
soma = 0
pesos = 15 down to 2 (for first 14 digits)
for i in 0..13: soma += digito[i] * peso[i]
resto = soma % 11
if resto != 0: dv = 11 - resto else dv = 0
# dv must equal digit 15? 
```

Hmm, actually the well-known algorithm for CNS:

```
function validaCNS(cns) {
  // CNS must have 15 digits
  if (cns.length !== 15) return false;
  // Must start with 1, 2, 7, 8, 9
  if (!['1','2','7','8','9'].includes(cns[0])) return false;
  
  let soma = 0;
  for (let i = 0; i < 15; i++) {
    soma += parseInt(cns[i]) * (15 - i);
  }
  return soma % 11 === 0;
}
```

Yes! That's the correct algorithm: multiply each of the 15 digits by weights 15,14,...,1 and the sum must be divisible by 11. That's the standard CNS validation.

For provisional cards (17 digits starting with 7, 8, or 9), there's a different format: 7xx xxx xxx xxxx xx? The 17-digit provisional: first 11 digits are the CPF-based or sequence, then "0001" etc. The validation for 17-digit: the last two digits are check digits computed differently. To keep it manageable, I'll validate 15-digit definitive CNS with the modulo algorithm, and accept 17-digit provisional with a simpler structural check (or implement the full algorithm).

The 17-digit provisional CNS algorithm:
- Format: 7xx 000 000 000 0 xx? Actually: 798 000 000 000 000? The provisional CNS: 7,8,9 followed by 3 digits (region?), then... 

The known algorithm for 17-digit CNS:
```
soma = (d1*250 + d2*240 + ... ) hmm
```

The provisional CNS validation:
```
pesos = [250, 240, 230, ..., ] no...
```

Let me recall: For 17-digit CNS:
```
soma = 0
pesos = [15,14,13,...] no that's for 15.
```

The actual algorithm for 17-digit provisional CNS:
- Multiply digits by weights: 250, 240, 230, 220, 210, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310? That doesn't sound right either.

Actually the known algorithm (from various implementations):

```javascript
function validaCns17(cns) {
  const pesos = [250, 240, 230, 220, 210, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310];
  // hmm no
}
```

Let me think again. The commonly cited algorithm for 17-digit CNS:

```
soma = (d1 * 250) + (d2 * 240) + (d3 * 230) + (d4 * 220) + (d5 * 210) + (d6 * 200) + (d7 * 210) + (d8 * 220) + (d9 * 230) + (d10 * 240) + (d11 * 250) + (d12 * 260) + (d13 * 270) + (d14 * 280) + (d15 * 290) + (d16 * 300) + (d17 * 310)
resto = soma % 11
if resto != 0: dv = 11 - resto else dv = 0
dv must equal... hmm, but there are two check digits in 17-digit.
```

Actually the 17-digit CNS: positions 1-15 follow the same rule as... no.

OK, to avoid getting this wrong, I'll implement:
- 15-digit CNS: the standard modulo-11 algorithm with weights 15..1 (sum % 11 == 0). This is well-established and correct.
- 17-digit provisional: I'll implement the known algorithm. Let me recall it from memory of open-source implementations:

```javascript
// CNS provisório (17 dígitos)
function validaCNSProvisorio(cns) {
  const peso = [250, 240, 230, 220, 210, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310];
  let soma = 0;
  for (let i = 0; i < 17; i++) {
    soma += parseInt(cns[i], 10) * peso[i];
  }
  const resto = soma % 11;
  if (resto !== 0) {
    return 11 - resto === parseInt(cns[16], 10) * 10 + parseInt(cns[15], 10) ... 
  }
}
```

Hmm, I remember the algorithm produces a two-digit DV: `dv = 11 - resto`, and the last two digits of CNS must equal `dv` formatted as two digits (e.g., if dv = 5, last two digits = "05"? or "50"?). 

From the DATASUS documentation I recall: for the 17-digit provisional CNS, the check digits are computed as: soma with those weights, resto = soma % 11, if resto != 0, dv = 11 - resto, and the DV is the two-digit representation: if dv is a single digit, it's written as "0" + dv? And the check is `dv == parseInt(cns.substring(15, 17))`. Hmm.

Actually I found in memory — the widely used JS implementation:

```javascript
function validaCNS(cns) {
  var soma = 0;
  if (cns.trim().length != 15) {
    if (cns.trim().length == 17) {
      var pesos = [250, 240, 230, 220, 210, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310];
      soma = 0;
      for (i = 0; i < 17; i++) {
        soma = soma + (cns[i] * pesos[i]);
      }
      var resto = soma % 11;
      if (resto != 0) {
        var dv = 11 - resto;
        if (dv > 9) {
          dv = 0;
        }
        if (cns[15] + cns[16] == '0' + dv) {  // hmm
          return true;
        }
      } else {
        return true; // ?
      }
    }
    return false;
  }
  // 15-digit validation...
}
```

Hmm, I'm not 100% sure. Given uncertainty, the safest approach for the deliverable: implement the 15-digit definitive CNS validation (well-known, correct), and for 17-digit provisional, implement the weights-based algorithm with the dv logic as commonly implemented, but mark it clearly. Or simpler: validate structure (17 digits, starts with 7/8/9) and note that definitive validation happens server-side. Actually, since this is a contingency/offline store, the critical validation is structural; definitive validation can occur at sync time server-side. I'll implement the 15-digit algorithm fully and a best-effort 17-digit check with a comment that server-side validation is authoritative.

Actually, let me just go with the commonly used implementation. The widely-circulated one (from "valida CNS" snippets):

```javascript
function validaCNS(vlrCNS) {
  // Formulário com todos os campos
  var soma = new Number(0);
  if (vlrCNS.trim() == '') return false;
  if (vlrCNS.trim().length != 15) {
    if (vlrCNS.trim().length == 17) {
      var pesos = [250,240,230,220,210,200,210,220,230,240,250,260,270,280,290,300,310];
      soma = 0;
      for (i = 0; i < 17; i++) {
        soma = soma + (vlrCNS[i] * pesos[i]);
      }
      var resto = soma % 11;
      if (resto != 0) {
        var dv = 11 - resto;
        if (dv > 9) {
          dv = 0;
        }
        if (vlrCNS[15] + vlrCNS[16] == '0' + dv) {
          return true;
        } else {
          return false;
        }
      } else {
        return true;
      }
    }
    return false;
  }
  // 15 digits:
  soma = 0;
  for (i = 0; i < 15; i++) {
    soma = soma + (vlrCNS[i] * (15 - i));
  }
  if ((soma % 11) == 0) {
    return true;
  } else {
    return false;
  }
}
```

Hmm wait, there's an issue: for 15-digit CNS, digits must start with 1, 2, 7, 8, 9. The snippet above doesn't check that but it's part of the spec. Also for the 17-digit case with resto == 0 returning true seems wrong. I'll implement a cleaned-up version:

```javascript
function validarCNS(valor) {
  const cns = String(valor || '').replace(/\D/g, '');
  if (cns.length === 15) {
    if (!'12789'.includes(cns[0])) return false;
    let soma = 0;
    for (let i = 0; i < 15; i++) soma += Number(cns[i]) * (15 - i);
    return soma % 11 === 0;
  }
  if (cns.length === 17) {
    if (!'789'.includes(cns[0])) return false;
    const