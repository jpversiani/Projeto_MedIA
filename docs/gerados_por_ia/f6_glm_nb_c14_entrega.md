The user wants me to create a JavaScript file `backend/app/static/js/copiloto_sidebar.js` for a medical teleconsultation copilot sidebar widget. This is a frontend JavaScript file, but the guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, etc. The task itself is clearly a frontend JS widget, so I should focus on creating the JavaScript file as requested, but I can also consider that the widget will consume backend APIs.

Let me think about what this widget needs:

1. **Alertas piscantes de risco/alergia** (Blinking risk/allergy alerts) - Real-time alerts about patient risks and allergies
2. **Botão 'Preencher SOAP com Sugestão da IA'** (Button 'Fill SOAP with AI Suggestion') - A button that fills the SOAP note with AI suggestions
3. **Sugestões de exames complementares e dosagens usuais do SUS** (Suggestions for complementary exams and usual SUS dosages)

The context is:
- MedIA project
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Teleconsultation screen for doctors (Home Office)
- C14 feature

Since it's a JS file, I should write clean, well-structured JavaScript. The guidelines mention Python, but the file requested is JS. I'll create the JS widget with:
- A class-based widget architecture
- WebSocket or polling for real-time updates
- Integration points with backend APIs (which would be Python/Pydantic/SQLAlchemy)
- Accessibility considerations
- LGPD compliance considerations (medical data)

Let me design the widget:

```javascript
/**
 * Copiloto Sidebar Widget - MedIA C14
 * Painel lateral do copiloto na tela de teleatendimento do médico (Home Office)
 */
```

Key features:
1. Real-time alerts (blinking) for risks/allergies - could use WebSocket (Socket.IO or native WS)
2. SOAP fill button - calls backend AI endpoint, then dispatches event or directly fills form fields
3. Exam suggestions and SUS dosages - rendered lists with CIAP-2/CID-10 codes

I should structure it well:

- `CopilotoSidebar` class
- Configuration (API endpoints, WebSocket URL)
- State management
- Rendering methods
- Event handlers
- Safety: the AI suggestion is a *suggestion*, doctor must review (important for medical safety - CFM resolution on telemedicine)

Important considerations for SUS/APS context:
- CIAP-2 codes for primary care
- CID-10 for diagnoses
- CNS (Cartão Nacional de Saúde) identification
- SOAP method (Subjetivo, Objetivo, Avaliação, Plano)
- RENAME/SUS standard medications (Rename 2022 - Relação Nacional de Medicamentos Essenciais)
- Dosages per SUS protocols

Let me write the JS file. I'll make it comprehensive:

```javascript
/* =========================================================================
 * MedIA — C14: Painel Lateral do Copiloto (Tela de Teleatendimento Médico)
 * -------------------------------------------------------------------------
 * Widget de front-end para a sala de teleatendimento (Home Office) do médico.
 * 
 * Funcionalidades:
 *   1. Alertas piscantes de risco/alergia em tempo real (WebSocket).
 *   2. Botão "Preencher SOAP com Sugestão da IA" (SOAP: S/O/A/P).
 *   3. Sugestões de exames complementares e dosagens usuais do SUS (RENAME).
 *
 * Conformidade:
 *   - Padrões SUS/APS: CIAP-2, CID-10, método SOAP, identificação por CNS/CPF.
 *   - LGPD: nenhum dado sensível é persistido no client (sessionStorage limpo).
 *   - Segurança assistencial: sugestões da IA são sempre "sugestões" — a
 *     decisão clínica final é do médico (CFM Res. 2.314/2022 — telemedicina).
 * ========================================================================= */
```

Structure:

```javascript
(function (window, document) {
  'use strict';

  // ------------------------------------------------------------------
  // Constantes e configuração
  // ------------------------------------------------------------------
  const COPILOTO_CONFIG = Object.freeze({
    API_BASE: '/api/v1',
    ENDPOINTS: {
      alertas: '/api/v1/copiloto/alertas',
      sugestoesSoap: '/api/v1/copiloto/sugestoes/soap',
      exames: '/api/v1/copiloto/sugestoes/exames',
      dosagens: '/api/v1/copiloto/sugestoes/dosagens',
      auditoria: '/api/v1/copiloto/auditoria'
    },
    WS_PATH: '/ws/copiloto',
    RECONNECT_MS: 5000,
    POLL_FALLBACK_MS: 30000,
    BLINK_CLASS: 'copiloto-alerta--piscante',
    ...
  });
```

Then the main class with methods:
- constructor
- init / mount
- connectWebSocket (with fallback polling)
- handleAlerta (add blinking alert)
- renderAlertas
- solicitarSugestaoSoap (calls API, fills SOAP form)
- preencherCamposSOAP (S, O, A, P fields)
- renderExames (with CIAP-2/CID-10)
- renderDosagens (SUS usual dosages)
- audit logging (important for medical AI - every AI suggestion accepted/rejected should be logged)
- accessibility (ARIA live regions for alerts)

Also CSS injection for blinking animation (or assume CSS exists — better to inject minimal styles so the widget is self-contained).

Let me also think about the SOAP form integration. The teleconsultation screen presumably has a SOAP form with fields like `#soap-subjetivo`, `#soap-objetivo`, `#soap-avaliacao`, `#soap-plano`. The widget should:
1. Fetch AI suggestion from backend
2. Show a preview/diff for the doctor to review
3. On confirmation, fill the fields (append or replace, doctor chooses)
4. Log to audit trail

For alerts:
- Types: 'alergia' (allergy), 'risco' (risk), 'interacao_medicamentosa' (drug interaction), 'dose_maxima' etc.
- Severity: 'critico', 'alto', 'moderado', 'info'
- Blinking for critical/high
- ARIA role="alert" / aria-live="assertive"

For exams and dosages:
- Exams: list with CIAP-2 code, justification, SUS availability
- Dosages: medication (DCB - Denominação Comum Brasileira), presentation, dosage per protocol, Rename reference

Let me write the full code. I'll aim for a production-quality, well-documented file. Since the guidelines mention pytest coverage, I could also mention that the backend endpoints consumed are tested in Python, but the file itself is JS. Maybe I should also provide a brief note about the expected backend contract (Pydantic schemas) so the JS matches. Actually, the task says "crie backend/app/static/js/copiloto_sidebar.js" — just the JS file. But to be helpful and align with the architecture guidelines, I can include the expected API contract as JSDoc comments, and optionally suggest the Pydantic schemas. I'll keep the main deliverable the JS file, with a concise contract documentation at the top.

Let me be careful about the format: the response should be the code file primarily, with maybe brief explanation. The user is a coder agent, so a complete, well-commented file is expected. I'll write it in Portuguese (comments) since the project is Brazilian SUS-focused and the request is in Portuguese.

Let me draft the code:

```javascript
/* =============================================================================
 * MedIA · C14 — Painel Lateral do Copiloto (Teleatendimento Médico · Home Office)
 * =============================================================================
 * Arquivo : backend/app/static/js/copiloto_sidebar.js
 * Escopo  : Widget client-side acoplado à sala de teleconsulta do médico.
 *
 * Funcionalidades (C14):
 *   [1] Alertas PISCANTES de risco/alergia em tempo real (WebSocket + fallback).
 *   [2] Botão "Preencher SOAP com Sugestão da IA" (S·O·A·P).
 *   [3] Sugestões de exames complementares e dosagens usuais do SUS (RENAME).
 *
 * Contrato com o backend (FastAPI + Pydantic v2 — ver schemas em
 * backend/app/schemas/copiloto.py):
 *   GET  /api/v1/copiloto/atendimentos/{id}/alertas      -> Lista[AlertaOut]
 *   GET  /api/v1/copiloto/atendimentos/{id}/sugestoes    -> SugestaoOut
 *   POST /api/v1/copiloto/atendimentos/{id}/soap/aceitar -> AuditoriaOut
 *   WS   /ws/copiloto/{atendimento_id}                   -> eventos push
 *
 * Conformidade:
 *   - SUS/APS: CIAP-2 (motivo de contato/avaliação), CID-10 (avaliação),
 *     método SOAP, paciente identificado por CNS (fallback CPF).
 *   - LGPD/Lei 13.789/2018: dados exibidos apenas em sessão; nada é
 *     persistido em localStorage; telemetria pseudonimizada.
 *   - Segurança assistencial: toda sugestão da IA é OPCIONAL e exige
 *     revisão explícita do médico (CFM Res. 2.314/2022). Nenhum campo
 *     do prontuário é sobrescrito sem confirmação.
 * ========================================================================== */
```

Now the IIFE:

```javascript
(function (window, document) {
  'use strict';

  /* ==========================================================================
   * 1. CONFIGURAÇÃO
   * ========================================================================*/

  const CONFIG = Object.freeze({
    API_BASE: '/api/v1/copiloto',
    WS_BASE: (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host,
    WS_PATH: '/ws/copiloto',
    RECONNECT_DELAY_MS: 5000,
    MAX_RECONNECT_ATTEMPTS: 8,
    POLL_FALLBACK_MS: 30000,
    REQUEST_TIMEOUT_MS: 15000,
    DEBOUNCE_MS: 400,

    // Severidades que disparam o estado "piscante" (anim. CSS).
    SEVERIDADES_PISCANTES: new Set(['critico', 'alto']),

    // IDs dos campos SOAP no formulário da teleconsulta (contrato com o template).
    SOAP_FIELD_IDS: Object.freeze({
      S: 'soap-subjetivo',
      O: 'soap-objetivo',
      A: 'soap-avaliacao',
      P: 'soap-plano'
    })
  });
```

Then severity metadata:

```javascript
  const SEVERIDADE = Object.freeze({
    critico: { rotulo: 'CRÍTICO', ordem: 0 },
    alto: { rotulo: 'ALTO', ordem: 1 },
    moderado: { rotulo: 'MODERADO', ordem: 2 },
    info: { rotulo: 'INFORMATIVO', ordem: 3 }
  });
```

Types of alerts:

```javascript
  const TIPO_ALERTA = Object.freeze({
    ALERGIA: 'alergia',
    RISCO: 'risco',
    INTERACAO: 'interacao_medicamentosa',
    DOSE_MAXIMA: 'dose_maxima_excedida',
    RED_FLAG: 'red_flag_clinica'
  });
```

Utility functions: `qs`, `el` (create element), `debounce`, `fetchComTimeout`, `escapeHtml`, `formatarDataHora`.

Then the main class:

```javascript
  class CopilotoSidebar {
    constructor(opcoes = {}) { ... }
    montar() { ... }
    ...
  }
```

Constructor takes: `atendimentoId`, `container` (or auto-create), `medico` info, `paciente` info (cns, cpf mascarado), callbacks.

Key methods:

1. `montar()` — builds DOM skeleton:
   - header with title "Copiloto Clínico (IA)" + patient identification (CNS masked)
   - section: alertas (aria-live="assertive")
   - section: SOAP suggestion (button + preview modal/panel)
   - section: exames complementares
   - section: dosagens usuais SUS
   - footer: disclaimer "Sugestões geradas por IA. Decisão final: médico assistente." + timestamp

2. WebSocket connection with reconnection and polling fallback:
   - `conectarWebSocket()`
   - `agendarReconexao()`
   - `iniciarPollingFallback()`

3. Alert handling:
   - `receberAlerta(alerta)` — dedupe by id, sort by severity, render
   - `renderizarAlerta(alerta)` — creates element with blink class if severity in SEVERIDADES_PISCANTES
   - `dispensarAlerta(id)` — doctor acknowledges (logged for audit)

4. SOAP:
   - `solicitarSugestaoSOAP()` — button handler; sets loading state; GET sugestoes
   - `renderizarPreviaSOAP(sugestao)` — shows preview with the 4 sections, CIAP-2/CID-10 chips
   - `aplicarSugestaoSOAP(modo)` — 'substituir' | 'anexar'; fills fields; dispatches CustomEvent 'copiloto:soap-aplicado'; POST audit
   - `descartarSugestaoSOAP()`

5. Exames & dosagens:
   - `carregarSugestoesApoio()` — GET exames + dosagens
   - `renderizarExames(lista)`
   - `renderizarDosagens(lista)`

6. Audit:
   - `registrarAuditoria(acao, detalhe)` — fire-and-forget POST; also console.debug

7. Accessibility & lifecycle:
   - ARIA roles, keyboard focus management
   - `destruir()` — cleanup timers, WS, listeners

CSS injection: I'll inject a `<style>` element with the widget styles including `@keyframes copiloto-piscar` for the blinking. Use `prefers-reduced-motion` media query to disable blinking for accessibility (important!). Blinking alerts should still be distinguishable (e.g., static red border + icon when reduced motion).

Let me also handle the "piscante" requirement explicitly: `.copiloto-alerta--piscante { animation: copiloto-piscar 1s steps(2, start) infinite; }` with keyframes toggling background/border.

For the SOAP fill: the button "Preencher SOAP com Sugestão da IA". After fetching, show preview with checkboxes per section (S/O/A/P) so the doctor picks what to apply, plus mode (substituir/anexar). Then apply.

Data contracts (JSDoc typedefs):

```javascript
/**
 * @typedef {Object} AlertaOut
 * @property {string}  id            - UUID do alerta.
 * @property {'alergia'|'risco'|'interacao_medicamentosa'|'dose_maxima_excedida'|'red_flag_clinica'} tipo
 * @property {'critico'|'alto'|'moderado'|'info'} severidade
 * @property {string}  titulo
 * @property {string}  descricao
 * @property {string|null} substancia    - Ex.: "Dipirona" (alergia).
 * @property {string|null} cid10         - Ex.: "I10" (risco).
 * @property {string|null} ciap2         - Ex.: "K86" (hipertensão não controlada).
 * @property {string|null} fonte         - Ex.: "RMCA", "e-SUS APS", "HSC-v2".
 * @property {string}  criado_em     - ISO-8601.
 */
```

```javascript
/**
 * @typedef {Object} SugestaoSOAPOut
 * @property {string} id
 * @property {string} subjetivo
 * @property {string} objetivo
 * @property {{texto: string, cid10: string|null, ciap2: string|null}} avaliacao
 * @property {string} plano
 * @property {number} confianca  - 0..1
 * @property {string} modelo     - identificação do modelo/versão (rastreabilidade)
 * @property {string} gerado_em
 */
```

```javascript
/**
 * @typedef {Object} ExameSugeridoOut
 * @property {string} id
 * @property {string} nome          - Ex.: "Creatinina sérica".
 * @property {string|null} cid10
 * @property {string|null} ciap2
 * @property {string} justificativa
 * @property {string} prioridade    - 'rotina'|'urgente'
 * @property {boolean} disponivel_sus
 */
```

```javascript
/**
 * @typedef {Object} DosagemSUSOut
 * @property {string} id
 * @property {string} medicamento   - DCB (Denominação Comum Brasileira).
 * @property {string} apresentacao  - Ex.: "comprimido 500 mg".
 * @property {string} posologia     - Ex.: "500 mg via oral, 8/8 h, por 5 dias".
 * @property {string|null} cid10
 * @property {string} referencia    - Ex.: "RENAME 2022", "PNMM", "Protocolo e-SUS APS".
 */
```

WS message: `{ evento: 'novo_alerta' | 'alerta_resolvido', dados: AlertaOut }`.

Now, about the "strict typing with Pydantic v2" — that's backend; the JS mirrors it via JSDoc typedefs. I'll note that.

Should I also include a small pytest note? The deliverable is the JS file. I could add a short section at the end of my answer mentioning the expected backend contract and that endpoints should be covered by pytest. But the main thing is the JS file. Maybe I'll keep the answer focused: the JS file + brief notes on integration contract. The user said "Execute com precisão conforme as diretrizes" — the guidelines are Python-oriented but the file is JS; I'll deliver the JS file and document the contract so the Python side (Pydantic schemas) matches, and mention testability.

Actually, let me reconsider: maybe I should also provide the minimal Pydantic schemas as a companion? The task explicitly says create the JS file. I'll deliver the JS file as the main artifact, and include a compact "contr