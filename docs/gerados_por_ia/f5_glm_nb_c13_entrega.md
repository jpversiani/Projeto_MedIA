The user is asking me to create a JavaScript file for offline sync indicator functionality for a medical project (Projeto MedIA - Brazilian SUS/APS healthcare system). The task is C13: Offline Sync Indicator and Local Storage.

The task specifically asks for:
- `backend/app/static/js/offline_sync_indicator.js`
- Detect online/offline status via `navigator.onLine`
- Manage IndexedDB local storage for contingency
- Display visual badge at top of the medical record showing "Nº de atendimentos aguardando upload" (number of appointments awaiting upload)

The guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest test coverage.

Interesting tension here: the main deliverable is a JavaScript file, but the guidelines mention Python. I should focus on the JavaScript file as the primary deliverable since that's what's explicitly requested, but I can also provide:
1. The main JS file (offline_sync_indicator.js)
2. Possibly a Python endpoint that the JS would sync to (to show integration)
3. Tests - since they mention pytest coverage, I could provide Python tests for the sync endpoint, and maybe JS tests with Jest

Let me think about what a complete, high-quality deliverable looks like:

1. **`backend/app/static/js/offline_sync_indicator.js`** - The main file:
   - IIFE or module pattern to avoid global pollution
   - Detect online/offline via `navigator.onLine` + `online`/`offline` events
   - IndexedDB management: database `media_offline_db`, object store `atendimentos_pendentes` (pending appointments)
   - Store SOAP-structured appointment data (with CIAP-2, CID-10 fields, CNS/CPF patient identification)
   - Badge UI at top of prontuário showing count of pending appointments
   - Sync logic: when online, attempt to POST to backend endpoint, handle success/failure, retry queue
   - LGPD considerations (Brazilian data protection law) - relevant for health data
   - Audit trail considerations

2. **Backend endpoint** (Python 3.12, Pydantic v2, SQLAlchemy 2.0) - `POST /api/v1/sync/atendimentos` to receive synced appointments. This shows the integration and lets me demonstrate the Python guidelines.

3. **Tests**:
   - pytest for the backend endpoint
   - Maybe Jest tests for the JS (optional but good)

Let me design the JS file carefully:

```javascript
/**
 * offline_sync_indicator.js
 * Projeto MedIA — C13: Indicador e Armazenamento Local de Sincronização Offline
 * ...
 */
```

Key features:
- `OfflineSyncIndicator` module (IIFE with revealing module pattern, or ES module? Since it's served as static JS and included via script tag, IIFE is safer; but I could support both. Let me use an IIFE that also exposes to window, with JSDoc types.)
- IndexedDB setup: DB name `media_offline_db`, version 1, store `atendimentos_pendentes` with keyPath `id` (uuid), indexes: `created_at`, `status`, `paciente_cns`
- Record schema for pending appointment:
  ```js
  {
    id: uuid,
    criado_em: ISO string,
    status: 'pendente' | 'em_envio' | 'erro',
    tentativas: number,
    payload: {
      paciente: { cns, cpf?, nome? },  // identification by CNS/CPF per guidelines
      atendimento: {
        data_atendimento,
        profissional_cns? / profissional_id,
        ciap2: [...],  // CIAP-2 codes
        cid10: [...],  // CID-10 codes
        soap: { s, o, a, p },  // SOAP method
        ...
      }
    }
  }
  ```
- Online/offline detection: `navigator.onLine`, `window.addEventListener('online'/'offline')`, plus periodic ping to `/api/v1/health` for more reliability (navigator.onLine can be true but server unreachable)
- Badge UI: fixed bar at top of prontuário, ARIA live region for accessibility, shows "N atendimentos aguardando upload" (singular/plural handling in Portuguese)
- Sync: when online, process queue sequentially, POST each to endpoint with CSRF token if present, mark success → delete from IndexedDB; on failure increment tentativas, exponential backoff
- Events: dispatch custom events `offline-sync:changed` so other modules can react
- Public API: `OfflineSyncIndicator.init(config)`, `.adicionarAtendimento(payload)`, `.contarPendentes()`, `.sincronizarAgora()`, `.listarPendentes()`

Security considerations:
- Don't store more than necessary (LGPD data minimization)
- Validate CNS checksum before storing? Could include a CNS validation function — that's a nice touch aligned with SUS guidelines. CNS validation algorithm: starts with 1, 2, 7, 8 or 9; checksum with weights.
- Sanitize any DOM insertion (use textContent, not innerHTML) to avoid XSS.

Accessibility: `role="status"`, `aria-live="polite"`.

Now the backend endpoint. Let me write:

- `backend/app/api/v1/endpoints/sync.py` — router with `POST /sync/atendimentos` accepting a batch, Pydantic v2 models with strict validation:
  - `PacienteIdentificacao`: cns (validated), cpf optional (validated), 
  - `AtendimentoSOAP`: subjetivo, objetivo, avaliacao, plano
  - `AtendimentoOfflinePayload`: ciap2 codes list (validate format: letter + 2 digits), cid10 codes (format validation)
- SQLAlchemy 2.0 style: `select()` statements, `Mapped`/`mapped_column`
- Service to persist into `atendimentos` table with `origem='offline'`, idempotency via `uuid_evento` unique constraint
- CNS/CPF validators in `backend/app/utils/documentos.py` maybe — but to keep the answer focused, I can include validators inline or as a small utils module.

Tests:
- `backend/tests/test_sync_atendimentos.py` — pytest with httpx/TestClient, covering: successful sync, invalid CNS, invalid CIAP-2, idempotency (duplicate uuid), offline queue flow.
- Maybe `backend/tests/js/test_offline_sync_indicator.js` with Jest for the JS — fakeIndexedDB. This might be a lot. The instruction says "Manter conformidade total e cobertura de testes automatizados com pytest." — pytest specifically. So Python tests are the priority. I could add a brief Jest test file as optional. Let me include a compact Jest test too since the JS is the main deliverable and needs coverage; but the guideline says pytest. I'll include pytest tests for the endpoint and a small Jest suite for the JS as complementary. Actually, to keep response manageable, I'll include both but keep the Jest one concise.

Let me think about response format: This is a coding task. The user is a "coder agent" persona. They want precise execution. I should provide the files with code blocks, organized by file path, with brief explanations. Headers per file, minimal prose. Length: this will be long due to code, but that's appropriate. I should avoid excessive commentary.

Let me now write the actual code carefully.

### 1. `backend/app/static/js/offline_sync_indicator.js`

```javascript
/**
 * Projeto MedIA — C13: Indicador e Armazenamento Local de Sincronização Offline
 * ---------------------------------------------------------------------------
 * - Detecta conectividade via navigator.onLine + eventos 'online'/'offline'
 *   e confirma disponibilidade real do backend com ping periódico.
 * - Persiste atendimentos (método SOAP, CIAP-2/CID-10, identificação CNS/CPF)
 *   no IndexedDB enquanto offline (contingência APS/SUS).
 * - Exibe badge fixo no topo do prontuário: "N atendimento(s) aguardando upload".
 * - Sincroniza automaticamente ao reconectar, com retentativas e backoff.
 *
 * Conformidade: LGPD (minimização de dados — armazenamento local temporário,
 * finalidade restrita à contingência), rastreabilidade via uuid_evento.
 */
```

Structure:

```javascript
(function (window, document) {
  'use strict';

  const CONFIG_PADRAO = {
    urlSync: '/api/v1/sync/atendimentos',
    urlHealth: '/api/v1/health',
    dbName: 'media_offline_db',
    dbVersion: 1,
    storeName: 'atendimentos_pendentes',
    intervaloPingMs: 30000,
    maxTentativas: 8,
    backoffBaseMs: 2000,
    loteSync: 10,
  };

  // --- CNS validation (SUS) ---
  function validarCNS(cns) { ... }

  // --- CPF validation ---
  function validarCPF(cpf) { ... }

  // --- uuid ---
  function gerarUuid() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    // fallback RFC4122 v4
  }
```

CNS validation algorithm (official):
- CNS must be 15 digits
- First digit must be 1, 2, 7, 8, or 9
- For CNS starting with 1 or 2 (definitive): checksum via sum of digits multiplied by weights 15,14,13,...,2; sum + 111 must be divisible by 11? Let me recall the correct algorithm.

The standard CNS validation (from SUS documentation):

For CNS starting with 1, 2 or 7, 8, 9:
- Pseudo-CNS (7,8,9) are provisional and use a different algorithm.

Algorithm for definitive CNS (1 or 2):
```
soma = 0
pesos = 15, 14, 13, ..., 2 (15 weights for 15 digits)
for i in 0..14: soma += digito[i] * peso[i]
resto = soma % 11
if resto == 0: válido
```
Wait, that's not quite it. Let me recall properly.

The widely used algorithm:

```js
function validaCNS(vlrCNS) {
  // vlrCNS: 15 digits
  var soma = 0;
  if (['1','2','7','8','9'].indexOf(vlrCNS[0]) === -1) return false;
  // pis = CNS
  var resto = 0, dv = 0;
  soma = 0;
  for (var i = 0; i < 15; i++) {
    soma += parseInt(vlrCNS[i]) * (15 - i);
  }
  resto = soma % 11;
  if (resto !== 0) {
    resto = 11 - resto;
  }
  ...
}
```

Hmm, actually the canonical algorithm from the "Cartão Nacional de Saúde" validation (used widely in Brazilian systems):

```js
function validaCNS(cns) {
  cns = cns.replace(/\D/g, '');
  if (cns.length !== 15) return false;
  if (!/^[1-9]/.test(cns)) return false;
  if (!['1','2','7','8','9'].includes(cns[0])) return false;

  let soma = 0;
  for (let i = 0; i < 15; i++) {
    soma += Number(cns[i]) * (15 - i);
  }
  const resto = soma % 11;
  if (resto !== 0) return false;  // ???
}
```

Hmm, I remember there are two variants: one for CNS starting with 1/2 and another for 7/8/9 (provisional). Let me reconstruct from the official algorithm (from DATASUS / ConecteSUS):

Official JS (from SUS e-SUS / widely circulated):

```js
function validaCNS(vlrCNS) {
   // Formulário: soma = soma + (peso * dígito); pesos 15..2
   var soma = new Number(0);
   if (vlrCNS.trim() == "") return false;
   switch ((vlrCNS.trim()).substring(0,1)) {
       case '1': case '2': case '7': case '8': case '9':
           // pis = vlrCNS
           for (var i = 0; i < 15; i++) {  // hmm
               ...
           }
   }
}
```

The actual canonical implementation (from the Ministry of Health sample):

```js
function validaCNS(vlrCNS) {
   var soma = new Number(0);
   if (vlrCNS.trim() == "") return false;
   switch ((vlrCNS.trim()).substring(0,1)) {
      case '1':
      case '2':
      case '7':
      case '8':
      case '9':
         var pis = vlrCNS.trim().toString();
         if (pis.length != 15) return false;
         var resto = 0, dv = 0, soma = 0;
         soma = soma + (parseInt(pis.substring(0,1),10) * 15);
         soma = soma + (parseInt(pis.substring(1,2),10) * 14);
         soma = soma + (parseInt(pis.substring(2,3),10) * 13);
         soma = soma + (parseInt(pis.substring(3,4),10) * 12);
         soma = soma + (parseInt(pis.substring(4,5),10) * 11);
         soma = soma + (parseInt(pis.substring(5,6),10) * 10);
         soma = soma + (parseInt(pis.substring(6,7),10) * 9);
         soma = soma + (parseInt(pis.substring(7,8),10) * 8);
         soma = soma + (parseInt(pis.substring(8,9),10) * 7);
         soma = soma + (parseInt(pis.substring(9,10),10) * 6);
         soma = soma + (parseInt(pis.substring(10,11),10) * 5);
         soma = soma + (parseInt(pis.substring(11,12),10) * 4);
         soma = soma + (parseInt(pis.substring(12,13),10) * 3);
         soma = soma + (parseInt(pis.substring(13,14),10) * 2);
         soma = soma + (parseInt(pis.substring(14,15),10) * 1);
         resto = soma % 11;
         if (resto != 0) {
            resto = 11 - resto;
            if (resto == 10 || resto == 11) {
               // se resto 10 ou 11 → dv = 11 - resto + ... hmm
            }
         }
         ...
   }
}
```

Hmm, I recall the full official algorithm handles the case where the computed DV would be > 9 by a "regime" adjustment: when resto is 10 or 11, they add 100 to... Actually the official algorithm:

```
resto = soma % 11;
if (resto != 0) {
   resto = 11 - resto;
}
if (resto == 10 || resto == 11) {
   dv = resto - 10? 
```

Let me look at this differently. The official DATASUS validation code (I've seen it many times):

```js
function validaCNS(vlrCNS) {
	var soma = new Number(0);
	if (vlrCNS.trim() == "") {
		return false;
	}
	switch ((vlrCNS.trim()).substring(0,1)) {
		case '1':
		case '2':
		case '7':
		case '8':
		case '9':
			var pis = vlrCNS.trim().toString();
			if (pis.length != 15) {
				return false;
			}
			var resto = 0;
			var dv = 0;
			var soma = 0;
			soma = soma + (parseInt(pis.substring(0, 1), 10) * 15);
			soma = soma + (parseInt(pis.substring(1, 2), 10) * 14);
			soma = soma + (parseInt(pis.substring(2, 3), 10) * 13);
			soma = soma + (parseInt(pis.substring(3, 4), 10) * 12);
			soma = soma + (parseInt(pis.substring(4, 5), 10) * 11);
			soma = soma + (parseInt(pis.substring(5, 6), 10) * 10);
			soma = soma + (parseInt(pis.substring(6, 7), 10) * 9);
			soma = soma + (parseInt(pis.substring(7, 8), 10) * 8);
			soma = soma + (parseInt(pis.substring(8, 9), 10) * 7);
			soma = soma + (parseInt(pis.substring(9, 10), 10) * 6);
			soma = soma + (parseInt(pis.substring(10, 11), 10) * 5);
			soma = soma + (parseInt(pis.substring(11, 12), 10) * 4);
			soma = soma + (parseInt(pis.substring(12, 13), 10) * 3);
			soma = soma + (parseInt(pis.substring(13, 14), 10) * 2);
			soma = soma + (parseInt(pis.substring(14, 15), 10) * 1);
			resto = soma % 11;
			if (resto != 0) {
				resto = 11 - resto;
			}
			if (resto == 10 || resto == 11) {
				dv = resto - 10;  // ??? 
			}
			...
```

Hmm, I genuinely don't remember the exact handling of resto 10/11 in the official code. Let me think about the actual mathematical rule.

The CNS check digit rule (official from Ministério da Saúde / "Fórmula de validação do CNS"):

1. Multiply digits by weights 15, 14, 13, ..., 1 (left to right).
2. Sum all results.
3. The sum must be divisible by 11 (resto == 0) for the CNS to be valid.

Wait — I think that's actually the rule: "A soma dos resultados deve ser divisível por 11." Yes! The official rule is: sum of digit×weight must be divisible by 11. If `soma % 11 ==