The user wants me to create a JavaScript file for notifications and active scheduling component (C8) for the MedIA project. The task is:

- Create `backend/app/static/js/notificacoes_push.js` with Web Notifications API support
- Display teleconsultation reminder 15 minutes before
- Notification when patient enters waiting room
- Confirmation of presence (confirmação de presença)

The guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest test coverage.

However, the main deliverable is a JavaScript file. The guidelines about Python seem to be general project guidelines, but the specific task is JavaScript. I should focus on the JavaScript file but can mention how it integrates with the backend (endpoints it would consume). Since the task explicitly asks for the JS file, I'll create a comprehensive, well-documented JavaScript module.

Let me think about what this file needs:

1. **Web Notifications API integration**:
   - Request permission
   - Check permission status
   - Show notifications

2. **Teleconsultation reminder 15 minutes before**:
   - Poll or receive schedule of teleconsultations
   - Schedule reminders (setTimeout or check loop)
   - Show notification 15 min before

3. **Patient in waiting room notification**:
   - Poll backend endpoint (or WebSocket/SSE) for patient check-in events
   - Show notification

4. **Presence confirmation (confirmação de presença)**:
   - Allow user to confirm presence via notification action or UI
   - POST to backend endpoint

Since it's for SUS/APS context, I should include:
- LGPD considerations (data minimization, no sensitive data in notifications)
- CNS validation possibly
- Integration with backend endpoints (Flask/FastAPI typical)

Let me design the module:

```javascript
/**
 * MedIA — Componente C8: Notificações Push e Agendamento Ativo
 * ...
 */
```

Structure:
- IIFE or ES module? For static JS served by Flask, an ES module or a global namespace object. I'll use an ES module pattern with a global fallback, or just a clean IIFE attached to `window.MedIA.Notificacoes`. Let me use a modern approach: ES module with named exports plus auto-init, but since it's served statically and might be included via `<script>`, I'll make it work both ways. Actually, simpler: use an IIFE that exposes `window.MedIANotificacoes` and supports `data-*` config attributes.

Key features:

1. `PermissionManager` — handles Notification.permission, requests permission on user gesture.

2. `AgendaService` — fetches teleconsultations from `/api/v1/agenda/teleconsultas?profissional_cns=...` or similar.

3. `Scheduler` — computes reminder times (start - 15 min), uses `setTimeout` with drift correction, re-syncs on visibilitychange.

4. `SalaEsperaWatcher` — polls `/api/v1/sala-espera/eventos?since=...` (long-poll or SSE fallback). Show notification "Paciente em sala de espera".

5. `PresencaService` — confirm presence: POST `/api/v1/teleconsultas/{id}/presenca` with CNS, timestamp.

6. Fallback in-page toast when notifications denied or page focused.

7. LGPD: notifications must not contain sensitive clinical data (CID-10, etc.) — only minimal info: patient name initials maybe, time. I'll implement a `sanitizarTextoNotificacao` that masks CNS/CPF and limits data.

8. Accessibility: aria-live for toasts.

9. Testing hooks: expose internals for tests; the JS itself can be tested with Jest, but guidelines say pytest — I can note that backend endpoints are tested with pytest and provide a small pytest example testing the API contract the JS consumes? The task says "Manter conformidade total e cobertura de testes automatizados com pytest." Since the deliverable is JS, I could include a pytest test that verifies the static file is served and contains required functions, plus contract tests for the endpoints. I'll include a small pytest file suggestion as complementary (e.g., `backend/tests/static/test_notificacoes_push_js.py`) that checks the JS contract (endpoints, function names) — that's a reasonable interpretation to satisfy pytest coverage requirement.

Let me write the JS carefully.

Endpoints contract (documented):
- `GET /api/v1/agenda/teleconsultas?data_inicio=&data_fim=` → list of `{id, agendado_em (ISO 8601 com tz), paciente: {nome, cns?}, modalidade, status}`
- `GET /api/v1/sala-espera/eventos?since=<ISO>` → `{eventos: [{id, tipo: "CHEGADA_PACIENTE", paciente: {nome, iniciais}, teleconsulta_id, ocorrido_em}]}`
- `POST /api/v1/teleconsultas/{id}/presenca` body `{confirmado_em, cns_profissional?}` → `{status: "CONFIRMADA"}`

Also maybe WebSocket via `/ws/sala-espera`. I'll implement polling with configurable interval and optional SSE.

Time handling: reminder at `agendado_em - 15min`. Use `setTimeout` capped (max ~2^31-1 ms ≈ 24.8 days) — for longer, chain timeouts. Also re-check every minute for drift; re-sync when tab becomes visible.

Notification actions: Web Notifications can have actions only in Service Worker (`showNotification` with actions). For page-level `new Notification()`, actions aren't supported. To support "Confirmar presença" action button, ideally use a Service Worker. I can include a note and code path: if `navigator.serviceWorker` available and registration exists, use `registration.showNotification` with actions `[{action: 'confirmar-presenca', title: 'Confirmar presença'}]` and handle `notificationclick`. Otherwise fallback to page notification + in-page toast with button.

I'll include a minimal service worker registration snippet? The task says create the JS file; I can embed SW handling if a SW exists at `/static/js/sw-notificacoes.js` (optional). I'll add graceful detection.

CNS validation: implement `validarCNS` (SUS card number) — checksum algorithm (PISO/DV). CNS has 15 digits starting with 1, 2, 7, 8, or 9. Validation: for starting with 1 or 2, use the classic algorithm with weights 15..2 and mod 11; for 7/8/9, different (mask 111...). I'll implement the standard one:

```js
function validarCNS(cns) {
  cns = cns.replace(/\D/g, '');
  if (cns.length !== 15) return false;
  if (!/^[1-9]/.test(cns)) return false;
  // soma ponderada
  const soma = [...cns].reduce((acc, d, i) => acc + parseInt(d, 10) * (15 - i), 0);
  return soma % 11 === 0;
}
```

That's the standard algorithm for CNS (definitive cards 1/2 and provisional 7/8/9 all use this? Actually the 7/8/9 ones use a different validation with fixed prefix "111 111 111" plus 6 digits... The common algorithm: for CNS starting with 1 or 2: weights 15 to 2, sum % 11 == 0. For 7, 8, 9: the number is formed as 7/8/9 + 8 random digits + 2 check digits computed via a different scheme; the widely used JS validation handles all with the same weighted sum? Let me recall the classic "validaCNS" JS:

```js
function validaCNS(vCNS) {
  var soma = 0; var resto = 0; var dv = 0; var peso = 0; var i = 0;
  vCNS = vCNS.replace(/[^\d]/g, '');
  if (vCNS.length !== 15) return false;
  if (/^[1-9]/.test(vCNS) === false) return false; // hmm actually 7,8,9 allowed
  for (i = 0; i < 15; i++) { /* ... */ }
}
```

The canonical algorithm (from DATASUS):

- If CNS starts with 1 or 2: multiply digits by weights 15,14,...,1? Actually weights 15 down to 2 for the first 14 digits, then DV = 11 - (soma % 11), if DV == 11 then DV = 0... Hmm, there are variants. The most common implementation:

```js
soma = 0;
for (i = 0; i < 15; i++) {
  soma += parseInt(vCNS[i]) * (15 - i);
}
resto = soma % 11;
if (resto != 0) return false; // soma must be divisible by 11
```

Yes — the well-known validation: the full 15-digit number weighted 15..1 summed must be divisible by 11. That works for cards 1/2. For 7/8/9 (provisional), the check is different: they're generated as `7/8/9 + 8 digits + 2 DV` where DV computed via a specific routine; but the common "validaCNS" scripts treat all with the same weighted-sum-divisible-by-11 rule? Actually no — provisional CNS (7/8/9) validation: the last two digits are check digits computed with a different algorithm (based on the "Cartão Nacional de Saúde provisório"). Many public implementations only validate 1/2 with the mod-11 rule and 7/8/9 with a separate routine:

```js
if (primeiroDigito >= 7) {
  // valida: 111111111 + ... hmm
}
```

The DATASUS routine for 7/8/9: the CNS provisório is composed of: first digit (7,8,9) + 8 random digits + 2 DVs? Or "111 111 111" prefix? Let me recall: CNS provisório format: `7xx xxxx xxxx xxxx`? The known algorithm from "validador CNS" (e.g., from the one widely circulated):

```js
function validaCNS(vCNS) {
  // Formato: 15 dígitos, iniciando com 1, 2, 7, 8 ou 9
  if (vCNS.length !== 15) return false;
  var tipo = vCNS.charAt(0);
  if ('12789'.indexOf(tipo) === -1) return false;
  if (tipo === '1' || tipo === '2') {
    // soma ponderada 15..1 deve ser múltiplo de 11
    var soma = 0;
    for (var i = 0; i < 15; i++) soma += parseInt(vCNS.charAt(i), 10) * (15 - i);
    return soma % 11 === 0;
  } else {
    // provisório: valida com pesos alternados 1 e 2? 
  }
}
```

Hmm. For provisional (7/8/9), the known algorithm: take the first 13 digits, compute DV with weights alternating... Actually the provisional CNS uses the "módulo 11" with weights pattern "1 2 1 2 ..." (like a Luhn-ish doubling). Let me recall the actual DATASUS spec: "CNS Provisório – números iniciados com 7, 8 ou 9: composto por 1 dígito inicial + 8 dígitos aleatórios + 2 dígitos verificadores + 4 dígitos '0000'"? Not sure.

Given ambiguity, I'll implement the widely used combined validator that handles both: the popular implementation (from "Validador de CNS" JS used in many systems):

```js
function validaCNS(vCNS) {
  vCNS = vCNS.replace(/\D/g, '');
  if (vCNS.length !== 15) return false;
  var soma = 0, i, peso = 15;
  for (i = 0; i < 15; i++) { soma += parseInt(vCNS.charAt(i),10) * peso; peso--; }
  var resto = soma % 11;
  if (resto === 0) return true;
  // se não, tenta regra do provisório? 
}
```

Actually the widely circulated one (from BuscaCNS / "valida_cns.js"):

```js
function validaCNS(vCNS) {
  var soma = new Number(0);
  var resto = 0;
  var dv = 0;
  var peso = 0;
  var i = 0;
  vCNS = vCNS.trim();
  if ((vCNS == '000000000000000') || ...) return false;
  if (vCNS.length != 15) return false;
  // Se começa com 7, 8 ou 9: 
  if ((vCNS.substr(0,1) == '7') || (vCNS.substr(0,1) == '8') || (vCNS.substr(0,1) == '9')) {
     soma = 0;
     for (i = 0; i < 15; i++) {
        // pesos alternando? 
     }
  }
}
```

I remember the actual algorithm for provisional: multiply digits alternately by 5,4,3,2,9,8,7,6,5,4,3,2,9,8? Hmm no.

Let me just recall the official DATASUS routine (from "Manual de integração com o Cartão Nacional de Saúde"):

For CNS definitive (1 or 2):
- Number: 15 digits. Take first 14? Actually: the CNS has 15 digits where the last is DV. Compute: multiply the 15 digits by weights 15 to 1 respectively; sum; if sum % 11 == 0 → valid. Yes, this is the documented one: "A soma dos produtos dos dígitos pelos pesos 15,14,...,1 deve ser divisível por 11."

For CNS provisório (7, 8, 9):
- The provisório is: first digit (7/8/9) + 8 random digits + 2 DV + "0000"? Hmm, no: provisório CNS format is 15 digits: `7/8/9 + 8 dígitos + 2 DVs + 4 dígitos`? I think provisório: `7/8/9` + 8 random + 2 DV + 4 zeros? Not certain.

The documented algorithm for provisório (from DATASUS "CNS provisório"): 
- Take the first 13 digits (1 initial + 8 random + ... hmm).

Actually I found in memory: the provisório CNS validation uses weights sequence "5 4 3 2 9 8 7 6 5 4 3 2 9 8 7"? That doesn't ring right either.

Alternative memory: The provisional CNS check uses the same mod-11 but with the number formed differently. Many implementations do:

```js
if (primeiro === '7' || '8' || '9') {
  // dv = resto da divisão da soma ponderada (pesos 15..2 sobre os 14 primeiros dígitos) por 11
  // dv = 11 - resto; if dv >= 10 => dv = 0? then compare with digits 14-15?
}
```

Honestly, for the purposes of this component, precise CNS validation is a nice-to-have; the backend (Python) is the source of truth for validation. In the JS I can include a lightweight CNS mask/validation for UX with the mod-11 rule for 1/2 and a documented fallback for 7/8/9 (accept format only, defer to backend). That's defensible and I'll comment it clearly. Or implement the full known algorithm.

Let me try to reconstruct the real provisional algorithm from the DATASUS "valida CNS" that circulates (I've seen this code):

```js
function validaCNS(vCNS) {
  var soma = 0, resto = 0, dv = 0, peso = 0, p = 0, i = 0, multiplicador = 0;
  vCNS = vCNS.replace(/\D/g,'');
  if (vCNS.length !== 15) return false;
  if (vCNS.charAt(0) === '1' || vCNS.charAt(0) === '2') {
    peso = 15;
    for (i = 0; i < 15; i++) { soma += parseInt(vCNS.charAt(i)) * peso; peso--; }
    resto = soma % 11;
    return resto === 0;
  } else if ('789'.includes(vCNS.charAt(0))) {
    // CNS provisório
    peso = 15; // ? 
  }
}
```

Hmm, I genuinely recall that the provisional uses: pesos = [15,14,...] too but the check is that (soma % 11) computed over first 13 digits yields DV via 11 - resto, and DV can be 0-10 where 10 is represented... The provisional CNS actually has this structure: `7/8/9 + 8 dígitos aleatórios + 2 dígitos verificadores + 4 dígitos '0000'`? No wait — I think provisório is 15 digits where positions: 1 (7/8/9), 2-9 random, 10-11 DV, 12-15 = "0000"? That would make provisório end with 0000. Hmm, I've seen provisional CNS like "700000000000000"-ish? Not sure.

Actually, from the official document "CNS - Cartão Nacional de Saúde" (DATASUS): "O CNS provisório é formado por: dígito inicial (7, 8 ou 9) + 8 dígitos aleatórios + 2 dígitos verificadores + 4 dígitos '0000'." Hmm, that gives 1+8+2+4 = 15. And the DV calculation: "multiplica-se os 11 primeiros dígitos (1+8+2? no...)". 

I recall the DV algorithm for provisório: weights cycle "1,2,3,4,5,6,7,8,9,1,2,3..."? 

OK — decision: In the JS, I'll