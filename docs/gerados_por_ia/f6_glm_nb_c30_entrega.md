Let me analyze this task carefully.

The task is to create a JavaScript file: `backend/app/static/js/copiloto_sidebar.js` — a widget for the doctor's telehealth screen (Home Office) that displays in real-time:
- Blinking risk/allergy alerts
- Button 'Preencher SOAP com Sugestão da IA' (Fill SOAP with AI Suggestion)
- Suggestions for complementary exams and usual SUS dosages

The architecture guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest test coverage.

However, the actual file requested is a JavaScript file. The Python guidelines are context for the project, but the deliverable here is the JS widget. I should also consider creating tests — but pytest is for Python. For JS, tests would typically be Jest, but the guidelines say pytest. Hmm. The task says "Manter conformidade total e cobertura de testes automatizados com pytest" — so maybe I should also provide a Python test that tests the endpoint the widget consumes, or at least mock the backend contract. But the primary deliverable is the JS file.

Let me think about what a complete, high-quality answer looks like:

1. The main file: `backend/app/static/js/copiloto_sidebar.js` — a self-contained widget (vanilla JS, no dependencies, since it's a static file served by FastAPI). It should:
   - Connect to a WebSocket endpoint (e.g., `/ws/copiloto/{atendimento_id}`) for real-time updates
   - Poll a REST fallback endpoint (e.g., `/api/v1/copiloto/{atendimento_id}/sugestoes`)
   - Render blinking alerts for risk/allergy (with accessibility considerations — prefers-reduced-motion)
   - Render a button "Preencher SOAP com Sugestão da IA" that fetches the AI SOAP suggestion and dispatches an event / fills the SOAP form fields (S, O, A, P)
   - Render suggestions of complementary exams and usual SUS dosages
   - Handle CNS/CPF display, CIAP-2/CID-10 codes
   - LGPD considerations (no logging of sensitive data, consent)
   - Security: escape HTML (XSS prevention), sanitize, use textContent
   - Reconnection with exponential backoff
   - Configurable via data attributes or a global config

2. Since the guidelines emphasize Python/Pydantic/SQLAlchemy/pytest, I should probably also provide:
   - The backend contract (Pydantic schemas) that the JS consumes — maybe briefly
   - A pytest test file that tests the endpoint serving the copiloto data (e.g., `backend/tests/test_copiloto_api.py`) to satisfy "cobertura de testes automatizados com pytest"

But the instruction says "crie backend/app/static/js/copiloto_sidebar.js" — the main deliverable. I'll focus on that but include supporting artifacts: the API contract (Pydantic models) and pytest tests for the backend endpoints the widget consumes, plus maybe a JS test harness note. Actually, to keep it focused, I'll deliver:

1. `backend/app/static/js/copiloto_sidebar.js` (main, complete)
2. Supporting: `backend/app/schemas/copiloto.py` (Pydantic v2 contract) — brief
3. `backend/tests/test_copiloto_sidebar_contract.py` (pytest) — tests the API contract the JS depends on
4. Maybe a small CSS file? The widget could inject its own styles via JS to be self-contained. That's better — self-contained widget that injects CSS. But blinking alerts need CSS animation; I can inject a `<style>` tag from JS. That keeps it to one file as requested.

Let me design the JS widget carefully.

### Widget design

**Name/namespace**: `MedIACopilotoSidebar` — an IIFE or ES module? Static file served by FastAPI; to be safe, use an IIFE attaching to `window.MedIACopilotoSidebar` with a factory `init(options)`. Also support ES module? Keep it simple: IIFE with UMD-ish pattern.

**Configuration**: read from a DOM element `<div id="copiloto-sidebar" data-atendimento-id="..." data-ws-url="..." data-api-base="...">` or passed options. Defaults:
- `apiBase`: `/api/v1`
- `wsUrl`: `/ws/copiloto`
- `atendimentoId`: required
- `medicoId`, `pacienteCns` maybe
- `pollIntervalMs`: 15000 fallback
- `locale`: pt-BR

**Real-time**: WebSocket first; on message types:
- `alerta` (risk/allergy alerts) — severity: `critico`, `alto`, `moderado`
- `sugestao_soap` — AI SOAP suggestion
- `sugestao_exames` — complementary exams
- `dosagens` — usual SUS dosages
- `status` — connection/model status

Fallback: REST polling `GET {apiBase}/copiloto/{atendimentoId}/snapshot` returning all sections.

**Alerts**: blinking (CSS animation `copiloto-alerta-piscar`), with `aria-live="assertive"`, role="alert". Respect `prefers-reduced-motion: reduce` — then no blink, use static highlight. Severity colors: critico = red, alto = orange, moderado = yellow. Each alert: type (ALERGIA, RISCO, INTERACAO, etc.), description, source (e.g., "Registro nacional", "Prontuário"), CID-10/CIAP-2 codes if applicable.

**SOAP button**: "Preencher SOAP com Sugestão da IA". On click:
- If suggestion available, dispatch a custom event `copiloto:preencher-soap` with the SOAP payload `{S, O, A, P}` and also attempt to fill form fields if present (`#soap-subjetivo`, `#soap-objetivo`, `#soap-avaliacao`, `#soap-plano` or `name="soap_s"` etc.). Also confirm before overwriting non-empty fields (LGPD/patient safety — doctor must review; add disclaimer "Sugestão gerada por IA — revisão obrigatória do profissional").
- Show loading state while fetching if not yet available: `GET {apiBase}/copiloto/{atendimentoId}/sugestao-soap`.
- Record audit: `POST {apiBase}/copiloto/{atendimentoId}/auditoria` with action `SOAP_SUGESTAO_APLICADA` (audit trail requirement).

**Exams suggestions**: list with exam name, CIAP-2 code maybe, justification, priority. Each with checkbox "adicionar ao plano" maybe — keep simple: display list with "Incluir no Plano (P)" button per item that appends to the P field or dispatches event.

**Dosages**: list of drug + presentation + usual SUS dose (posologia), with reference (e.g., "RENIFER / Manual APS", "Formulário Terapêutico Nacional — FTN"). Disclaimer: "Verificar sempre protocolo vigente e allergies".

**Security**:
- All dynamic content rendered with `textContent` (no innerHTML with user data). I'll build DOM nodes programmatically or use a tiny `el()` helper.
- Escape anything.
- Validate WebSocket origin? The browser handles it; but check `event.origin`? For WS, `e.origin` check is good practice.
- Don't store PHI in localStorage. Keep in memory only.
- No console logging of patient data.

**Accessibility**: aria-live regions, roles, keyboard focus, contrast, reduced motion.

**Resilience**: reconnect with exponential backoff + jitter, max attempts; fallback to polling; online/offline events; visibilitychange to refresh.

**i18n**: pt-BR strings hardcoded (SUS context) but centralized in a STRINGS object.

**CNS validation**: maybe a helper to format CNS (mask 000 0000 0000 0000) — display patient identifier. The widget might display patient header: name (masked? no — doctor needs name), CNS, age, allergies count. Keep minimal: header with patient name + CNS formatted.

Let me also define the data contract (Pydantic):

```python
class AlertaRisco(BaseModel):
    id: str
    tipo: Literal["ALERGIA", "RISCO", "INTERACAO_MEDICAMENTOSA", "DADOS_VITAIS_CRITICOS", "OUTRO"]
    severidade: Literal["CRITICO", "ALTO", "MODERADO"]
    descricao: str
    fonte: str | None
    cid10: str | None
    ciap2: str | None
    criado_em: datetime

class SugestaoSOAP(BaseModel):
    subjetivo: str
    objetivo: str
    avaliacao: str  # with CID-10 / CIAP-2 hypotheses
    plano: str
    cid10_sugeridos: list[str]
    ciap2_sugeridos: list[str]
    confianca: float  # 0..1
    modelo: str
    gerado_em: datetime
    requer_revisao_medica: Literal[True] = True

class ExameComplementar(BaseModel):
    id, nome, codigo (SUS SIGTAP?), justificativa, prioridade: Literal["ROTINA","URGENTE","URGENCIA"], ciap2?

class DosagemSUS(BaseModel):
    id, medicamento, apresentacao, posologia, via, referencia (e.g., "FTN/RENIFER 2024"), alerta_alergia_relacionada?

class CopilotoSnapshot(BaseModel):
    atendimento_id: UUID
    paciente: PacienteResumo (nome, cns, idade, sexo)
    alertas: list[AlertaRisco]
    sugestao_soap: SugestaoSOAP | None
    exames: list[ExameComplementar]
    dosagens: list[DosagemSUS]
    atualizado_em: datetime
```

And pytest tests: use FastAPI TestClient with a stub router to validate the contract + a test that the static JS file exists and contains required markers (id strings, event names) — a "contract test" ensuring frontend/backend agreement. That's a nice touch: test that JS references the same event names and endpoints. Also test CNS formatting function? That's JS... can't test with pytest directly. But we can test the API endpoints.

Given the constraints, I'll produce:

1. **Main deliverable**: `backend/app/static/js/copiloto_sidebar.js` — thorough, production-quality, ~600-800 lines with JSDoc.
2. **Contract schemas**: `backend/app/schemas/copiloto.py` (Pydantic v2, strict typing).
3. **Router**: maybe minimal `backend/app/api/v1/endpoints/copiloto.py`? That might be too much scope. The task says create the JS file. But "cobertura de testes automatizados com pytest" — I'll include a pytest file that tests the contract and the JS contract markers. To make tests meaningful, I'll include a minimal router with a snapshot endpoint (in-memory stub) so tests pass. Hmm, but the real backend presumably exists (this is C30 in a series; other cards created backend). I'll provide the schemas + a thin router stub + tests, clearly marked as the contract the widget consumes. Actually, to avoid overreach, I could provide schemas + tests that validate schemas and the JS↔API contract. Let me include a small router since tests need an endpoint; I'll mark it as reference implementation to be wired into the existing app.

Let me be careful about length — the answer will be long but should be well-organized. The user asked in Portuguese, so respond in Portuguese.

Now let me write the JS file in detail.

```javascript
/**
 * ============================================================================
 * MedIA — Copiloto Clínico (Painel Lateral) — Tela de Teleatendimento Médico
 * Card C30 — Home Office / Teleatendimento (APS / SUS)
 * ============================================================================
 * ...
 */
```

Structure:

```javascript
(function (global) {
  'use strict';

  // ---------- Constantes / Strings ----------
  const STRINGS = {...};
  const SEVERIDADE = { CRITICO: {...}, ALTO: {...}, MODERADO: {...} };
  const WS_MSG_TYPES = {...}; // must match backend enums

  // ---------- Utilidades ----------
  function el(tag, attrs, children) {...} // safe DOM builder using textContent
  function formatarCNS(cns) {...}
  function validarCNS(cns) {...} // dígitos verificadores (SUS) — nice touch
  function formatarDataISO(iso) {...} // pt-BR
  function debounce / etc.

  // ---------- Estado ----------
  class CopilotoStore { ... } // holds snapshot, emits change events

  // ---------- Widget ----------
  class CopilotoSidebar {
    constructor(root, opcoes) {...}
    init() {...}
    // render sections
    _renderCabecalho(), _renderAlertas(), _renderSOAP(), _renderExames(), _renderDosagens(), _renderRodape()
    // realtime
    _conectarWebSocket(), _agendarReconnect(), _iniciarPolling()
    // actions
    _aplicarSugestaoSOAP(), _incluirExameNoPlano(exame), _registrarAuditoria(acao, detalhe)
    // soap form integration
    _preencherFormularioSOAP(sugestao)
    destroy()
  }

  // auto-init from DOM
  function autoInit() {...}
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', autoInit); else autoInit();

  global.MedIACopilotoSidebar = { init: ..., CopilotoSidebar };
})(window);
```

Key details:

**CNS validation algorithm** (SUS): CNS has 15 digits; starting with 1, 2, 7, 8, 9. Validation: for CNS starting with 1 or 2: sum with weights 15 down to 2, mod 11, dv = 11 - resto; if dv == 11 → dv = 0... Actually the standard algorithm:

For CNS [1|2]:
```
soma = Σ (digito[i] * peso[i]) where pesos = 15,14,...,1? 
```
Let me recall: The classic algorithm:
```
pesos = [15,14,13,12,11,10,9,8,7,6,5,4,3,2]
soma = n[0]*15 + n[1]*14 + ... + n[13]*2
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0
if dv != n[14]: invalid
```
Hmm, actually the well-known algorithm:

```
function validaCNS(cns) {
  cns = cns.replace(/\D/g, '');
  if (cns.length !== 15) return false;
  if (!/[1-9]/.test(cns[0])) return false;
  if ('789'.includes(cns[0])) {
    // CNS provisório: soma = Σ digito * peso (pesos 15..2 for first 14? no...)
  }
}
```

The standard algorithm for CNS (both permanent 1/2 and provisional 7/8/9):

```
soma = 0
for i in 0..14: soma += Number(cns[i]) * (15 - i)
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0  // actually if resto == 0 then dv = 11 - 0 = 11 → becomes 0? 
```
Hmm, let me recall precisely. The official algorithm (from Cadastro Nacional de Usuários do SUS):

```
rotina = "1" (1/2) or "2" (7/8/9)
For 1/2:
  soma = n1*15 + n2*14 + ... + n14*2
  resto = soma % 11
  dv = 11 - resto
  if dv == 11: dv = 0
  if dv == 10: invalid
  compare with n15
For 7/8/9:
  soma = n1*15 + ... + n15*1  (all 15 digits with weights 15..1)
  if soma % 11 == 0: valid
```

Yes! That's right:
- Permanent cards (starting 1 or 2): weights 15 to 2 over the first 14 digits; dv = 11 - (soma % 11); if dv == 11 → dv = 0; if dv == 10 → invalid; dv must equal 15th digit.
- Provisional (7, 8, 9): sum of all 15 digits with weights 15 down to 1 must be divisible by 11.

I'll implement `validarCNS` accordingly — nice SUS-compliance touch. And `formatarCNS` → `000 0000 0000 0000`.

**Blinking alerts CSS** (injected):

```css
@keyframes copiloto-piscar-critico {
  0%, 100% { background-color: #d32f2f; }
  50% { background-color: #ffcdd2; } /* or opacity */
}
@media (prefers-reduced-motion: reduce) {
  .copiloto-alerta--critico { animation: none !important; ... }
}
```

Better: blink the border/outline + icon, keep text readable. Use `animation: copiloto-piscar 1s steps(2, start) infinite` alternating background. Ensure contrast. Also a "silenciar" (acknowledge) button per alert to stop blinking after the doctor acknowledges (patient safety: don't let it blink forever, but keep visible). Good UX: "Reconhecer" button stops animation but keeps alert pinned with a static warning style.

**SOAP form integration**: The widget tries to find fields by common selectors:
```javascript
const SOAP_SELECTORS = {
  S: ['#soap-subjetivo', '[name="soap_subjetivo"]', '#id_soap_subjetivo', 'textarea[name="subjetivo"]'],
  O: [...], A: [...], P: [...]
};
```
If found and field non-empty → require confirmation (dialog) before overwrite. Always dispatch `CustomEvent('copiloto:preencher-soap', { detail: { sugestao, atendimentoId }, bubbles: true })` so the host app can handle it. Also dispatch `copiloto:exame-incluir` per exam.

**Audit**: POST to `{apiBase}/atendimentos/{id}/copiloto/auditoria` with `{