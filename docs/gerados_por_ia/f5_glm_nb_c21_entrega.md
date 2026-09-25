The user wants me to create a JavaScript file for offline sync indicator functionality for a medical project (MedIA). The task is:

1. Create `backend/app/static/js/offline_sync_indicator.js`
2. Detect online/offline status via `navigator.onLine`
3. Manage IndexedDB local storage for contingency
4. Display a visual badge at the top of the medical record showing 'Nº de atendimentos aguardando upload' (Number of appointments awaiting upload)

The guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest test coverage.

Wait — the main deliverable is a JavaScript file, but the guidelines mention Python. This is a bit of a mixed task. The JavaScript file is the primary artifact, but since the architecture guidelines mention Python/Pydantic/SQLAlchemy/pytest, I should probably also provide:

1. The main JavaScript file (offline_sync_indicator.js) — the core deliverable
2. Possibly a backend endpoint to receive the synced appointments (since the JS needs to upload to somewhere) — this would use FastAPI, Pydantic v2, SQLAlchemy 2.0
3. Tests with pytest

Let me think about what makes sense. The task C21 is specifically about the frontend indicator and local storage. But the "upload" part implies a backend endpoint. Given the guidelines explicitly mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, and pytest coverage, I should deliver:

1. **`backend/app/static/js/offline_sync_indicator.js`** — the main JS module:
   - Online/offline detection via `navigator.onLine` + `online`/`offline` events
   - IndexedDB management (database for storing pending appointments)
   - Badge UI showing count of pending uploads
   - Auto-sync when back online
   - Integration with SOAP-formatted appointments, CIAP-2, CID-10, CNS/CPF validation

2. **Backend sync endpoint** (to receive uploads) — FastAPI with Pydantic v2 schemas, SQLAlchemy 2.0 model, CNS/CPF validation, CIAP-2/CID-10 validation

3. **Pytest tests** — for the backend endpoint and validators

Let me design this carefully.

### JavaScript Module Design

The JS file should be a self-contained module (IIFE or ES module). Given it's served as static JS, I'll use an IIFE pattern or ES module. Let me use an ES module pattern but also make it work when loaded via `<script>` tag. Actually, for static files in FastAPI, ES modules work fine with `<script type="module">`. But to be safe and dependency-free, I'll write it as an IIFE that exposes a global `MedIAOfflineSync` API.

Key components:

1. **ConnectivityMonitor**:
   - `navigator.onLine` initial check
   - `window.addEventListener('online', ...)` and `offline`
   - Also do periodic heartbeat ping to `/api/v1/health` or similar to detect "online but server unreachable" (navigator.onLine can be true even without real connectivity — it only checks network interface). This is important for medical contingency: navigator.onLine is unreliable. I'll implement a heartbeat check.

2. **IndexedDBManager** (offline queue):
   - DB name: `media_offline_db`, version 1
   - Object store: `pending_appointments` with keyPath `id` (uuid), indexes: `created_at`, `sync_attempts`, `status`
   - Store full appointment record: patient CNS/CPF, SOAP fields (subjective, objective, assessment, plan), CIAP-2 code, CID-10 code, timestamp, device metadata
   - CRUD: `enqueue`, `listPending`, `markSynced` (remove), `incrementAttempts`, `countPending`
   - Handle storage quota errors

3. **SyncEngine**:
   - When online: POST pending appointments to `/api/v1/appointments/sync` (batch endpoint with idempotency via `client_uuid`)
   - Exponential backoff on failure
   - Idempotency: server checks `client_uuid` uniqueness
   - On success: remove from queue, update badge

4. **BadgeUI**:
   - Fixed badge at top of prontuário (medical record page)
   - States: "Online — sincronizado", "Offline — Nº de atendimentos aguardando upload", "Sincronizando..."
   - ARIA live region for accessibility
   - Colors: green (online/synced), amber (pending), red (offline), blue (syncing)

5. **Form interception**:
   - Hook into the prontuário form submit; if offline, save to IndexedDB instead of POST
   - Provide `MedIAOfflineSync.captureAppointment(data)` public API

Also should include:
- CNS validation (algorithm per Ministério da Saúde — the CNS check digit algorithm)
- CPF validation
- Data schema for the appointment record

Let me write the CNS validation algorithm:
- CNS must be 15 digits, starting with 1, 2, 7, 8, or 9
- For CNS starting with 1 or 2: sum = Σ (digit[i] * (15 - i)) for i=0..14; result must be divisible by 11
- For CNS starting with 7, 8, 9: different algorithm — sum of digit * weight, where weight cycles... Actually the algorithm: multiply digits by 15,14,13,...,2 (positions), sum. If sum % 11 == 0, valid. For 7/8/9 series: sum digits * weights [15,14,...,2], if remainder != 0, subtract... Let me recall correctly.

The official CNS validation (from Ministério da Saúde / Cartão Nacional de Saúde):

For CNS numbers starting with 1 or 2:
- Digits: d1..d15
- Sum = d1*15 + d2*14 + ... + d15*1
- Valid if Sum % 11 == 0

For CNS starting with 7, 8, or 9:
- Sum = d1*15 + ... + d15*1
- If Sum % 11 == 0 → valid
- Else: compute rest = Sum % 11; if (11 - rest)... hmm.

Actually the standard algorithm for 7/8/9 series:
```
soma = 0
for i in 0..14: soma += digito[i] * (15 - i)
resto = soma % 11
if resto != 0:
    resto = 11 - resto
    if resto in [0, 1, 10, 11]: invalid
    ... 
```

Hmm, let me recall the actual algorithm. The commonly cited one (from the "Validação do CNS" documentation):

```python
def valida_cns(cns):
    cns = cns.strip().replace('.', '').replace(' ', '')
    if len(cns) != 15:
        return False
    # Only numbers, or starts with 7/8/9 and may contain letters? No — CNS is 15 digits.
    if not cns.isdigit():
        return False
    if cns[0] not in '123789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if soma % 11 == 0:
        return True
    return False
```

Wait, that's not quite right for the 7/8/9 series. Let me think again. The definitive algorithm:

For CNS provisório (starting 7, 8, 9):
```
peso = 15
soma = 0
for each digit:
    soma += digit * peso
    peso -= 1
resto = soma % 11
if resto == 0:
    valid
else:
    dv = 11 - resto
    # then check: dv must be... 
```

Hmm, actually I recall the algorithm being:

```
def _valida_cns(cns: str) -> bool:
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] not in {'1', '2', '7', '8', '9'}:
        return False
    soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
    return soma % 11 == 0
```

Yes — I believe the unified algorithm is: weighted sum with weights 15 down to 1, and the sum must be divisible by 11. This works for both series. Let me verify with a known valid CNS: "700 0000 0000 0003"? Hmm, I don't have a known test vector memorized precisely. 

Actually, there's a well-known Python implementation (from the `validate-docbr` library or similar):

```python
def validate_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] in '0123456' and cns[0] not in '12':  # hmm
        ...
```

The docbr implementation:
```python
def validate(self, cns):
    cns = self._only_digits(cns)
    if len(cns) != 15 or len(set(cns)) == 1:
        return False
    # CNS definitivo starts with 1,2; provisório 7,8,9
    if cns[0] not in ['1', '2', '7', '8', '9']:
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if soma % 11 == 0:
        return True
    return False
```

Hmm wait, but I've also seen a version where for 7/8/9 there's a different computation:

From the official documentation (Manual de instruções do CNS):
- CNS definitive (1 or 2): sum of digit × weight (15 to 1), must be divisible by 11.
- CNS provisional (7, 8, 9): same weighted sum, but if not divisible by 11, compute rest = soma % 11, then dv = 11 - rest, and if dv in (10, 11) → invalid... 

Actually no. Let me look at this from memory of the actual reference implementation used widely (e.g., in the "brasilapi" or DBC/PHP implementations):

PHP reference (from https://github.com/.../valida_cns):
```php
function validaCNS($cns) {
    // CNS definitivo ou provisório
    if (strlen(preg_replace('/[^\d]/', '', $cns)) != 15) return false;
    $cns = preg_replace('/[^\d]/', '', $cns);
    if (preg_match('/^[1-2]/', $cns)) {
        // série definitiva
        $pis = $cns;
        $soma = 0;
        for ($i = 0; $i < 15; $i++) {
            $soma += $pis[$i] * (15 - $i);
        }
        if ($soma % 11 == 0) return true;
        return false;
    } elseif (preg_match('/^[7-9]|^0/', $cns)) {
        // série provisória — algoritmo diferente
        $pis = $cns;
        $soma = 0;
        for ($i = 0; $i < 15; $i++) {
            $soma += $pis[$i] * (15 - $i);
        }
        $resto = $soma % 11;
        if ($resto == 0) return true;
        $dv = 11 - $resto;
        // verifica
        $digito = intval($pis[14]); // hmm no...
    }
}
```

Hmm, I genuinely remember there being a two-branch algorithm. Let me reconstruct the provisional CNS algorithm properly:

The provisional CNS (7/8/9) algorithm:
1. Compute soma = Σ digit[i] × (15 − i)
2. resto = soma % 11
3. If resto == 0 → valid
4. Else: dv = 11 − resto; if dv == 11 → dv = 0? ... then check if dv equals... 

Actually here's the algorithm I recall from the official spec for CNS provisório:

```
soma = Σ (dígito × peso), pesos 15..1
resto = soma % 11
se resto == 0 → válido
senão:
    dv = 11 - resto
    se dv == 11 → dv = 0  (não sei)
    se dv == 10 → inválido
    senão: substituir o último dígito? 
```

Hmm, this is getting complicated. Let me think about what's actually verifiable. 

The most widely used and cited implementation is this one (found in many repos, attributed to the MS algorithm):

```python
def valida_cns(cns: str) -> bool:
    cns = ''.join(filter(str.isdigit, cns))
    if len(cns) != 15:
        return False
    if cns[0] not in '123789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

And there are test vectors. A commonly cited valid CNS: "116 8096 8600 0241"? Hmm. Let me try to verify one: CNS "700000000000003"? 

Let me compute for a candidate: I recall test CNS "116587645000001"? Not sure.

Actually, there IS a two-branch algorithm. From the official "Cartão Nacional de Saúde" documentation (and reproduced in the well-known JS library `cns-validator`):

For CNS starting with 1 or 2 (definitive):
- pesos: 15, 14, 13, ..., 1
- soma must be divisible by 11

For CNS starting with 7, 8 or 9 (provisional):
- pesos: 15, 14, ..., 1
- soma = Σ
- resto = soma % 11
- if resto == 0 → valid
- else: dv = 11 − resto; if dv == 11 → dv = 0; if dv == 10 → invalid; else the last digit must equal dv? No wait...

Hmm, actually I found it in memory — the provisional algorithm:

```
soma = Σ d[i] * (15 - i)
resto = soma % 11
if resto != 0:
    dv = 11 - resto
    if dv == 11: dv = 0
    if dv == 10: return False
    # o último dígito deve ser o dv? Não...
```

OK here's the thing — I recall the actual algorithm from the reference implementation in the "valida-cns" npm package:

```javascript
function isValidCNS(cns) {
  cns = cns.replace(/\D/g, '');
  if (cns.length !== 15) return false;
  if (/^([1-2]\d{10}00[01]\d)$/.test(cns)) return true; // hmm no
  ...
}
```

No. Let me just go with the widely accepted single-algorithm version, which is what most Brazilian health IT systems use and what appears in the reference documentation:

**Algorithm (both series):**
1. Remove non-digits; must have exactly 15 digits.
2. First digit must be 1, 2, 7, 8, or 9.
3. soma = Σ_{i=0}^{14} d[i] × (15 − i)
4. Valid iff soma % 11 == 0.

Actually wait — I now clearly remember there's a special case. The full official algorithm:

```
Para CNS iniciando em 1 ou 2:
  soma = Σ d[i] × (15 − i)
  válido se soma % 11 == 0

Para CNS iniciando em 7, 8 ou 9:
  soma = Σ d[i] × (15 − i)
  resto = soma % 11
  se resto == 0 → válido
  senão:
    dv = 11 − resto
    se dv == 11 → dv = 0
    se dv == 10 → inválido
    senão → válido se o 15º dígito... 
```

Hmm no. OK, let me actually reconstruct from the true source. The official algorithm from DATASUS ("Validação do número do CNS"):

```
1) O número do CNS é composto por 15 dígitos.
2) Para números iniciados com 1 ou 2 (CNS definitivo):
   - Multiplicar cada dígito pelo peso correspondente (15, 14, 13, ..., 1)
   - Somar os resultados
   - O número é válido se a soma for divisível por 11
3) Para números iniciados com 7, 8 ou 9 (CNS provisório):
   - Multiplicar cada dígito pelo peso (15, 14, ..., 1) e somar
   - Se a soma for divisível por 11 → válido
   - Caso contrário:
     - Calcular o resto: resto = soma % 11
     - dv = 11 − resto
     - Se dv == 11 → dv = 0
     - Se dv == 10 → número inválido
     - Senão → válido (??)
```

That last "senão → válido" doesn't make sense as validation. 

Let me try a different approach: find a known valid provisional CNS and test. Known test vectors I've seen in test suites:
- Valid definitive: "116809686000241"? Let me compute: digits 1,1,6,8,0,9,6,8,6,0,0,0,2,4,1 with weights 15,14,13,12,11,10,9,8,7,6,5,4,3,2,1:
  1×15=15, 1×14=14, 6×13=78, 8×12=96, 0×11=0, 9×10=90, 6×9=54, 8×8=64, 6×7=42, 0×6=0, 0×5=0, 0×4=0, 2×3=6, 4×2=8, 1×1=