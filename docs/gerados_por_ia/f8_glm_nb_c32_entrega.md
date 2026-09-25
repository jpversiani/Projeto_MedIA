The user is asking me to create a JavaScript file for web notifications in a healthcare project (MedIA - related to Brazilian SUS/APS healthcare system). The task is:

1. Create `backend/app/static/js/notificacoes_push.js` with Web Notifications API support:
   - Reminder of teleconsultation 15 minutes before
   - Notification when patient enters the room (sala de espera)
   - Confirmation of presence (confirmação de presença)

The guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest test coverage.

However, the main deliverable is a JavaScript file. The guidelines about Python are architecture directives for the project context, but the file itself is JavaScript. I should:

1. Create the JavaScript file with Web Notifications API
2. Since the guidelines mention pytest coverage, I should probably also provide a test file (pytest with playwright or similar for JS testing, or pytest testing the backend endpoints that feed notifications). Actually, for JS testing with pytest, we could use pytest-playwright or test the API endpoints. Let me think about what makes sense.

The task says "Manter conformidade total e cobertura de testes automatizados com pytest" - maintain full compliance and automated test coverage with pytest. So I should provide tests too.

Let me design the JavaScript module:

**notificacoes_push.js** - A module that:
1. Requests notification permission
2. Connects to a WebSocket or polls an API endpoint for events
3. Handles three event types:
   - `teleconsulta_lembrete` - 15 min before teleconsultation
   - `paciente_em_sala` - patient entered waiting room
   - `confirmacao_presenca` - presence confirmation
4. Shows notifications via `new Notification()` or ServiceWorkerRegistration.showNotification()
5. Fallback to in-page toasts if permission denied
6. Scheduling: for teleconsultation reminders, it can schedule locally based on appointment times fetched from API (setTimeout with 15 min before start)

Architecture considerations:
- LGPD compliance: notifications shouldn't display sensitive health data (CID-10, diagnoses) in system notifications - only minimal info. This is important for healthcare. Notifications should show minimal data (patient name maybe, or even just "Você tem uma teleconsulta em 15 minutos").
- CNS/CPF identification: use CNS when available.
- The JS should be an ES module or IIFE? For a Flask backend serving static JS, probably a plain script or ES module. I'll make it an ES module with a global fallback, or just a well-structured IIFE/class. Let me use a class-based approach with ES module export plus window attachment for compatibility.

Let me write the code:

```javascript
/**
 * MedIA — Notificações Push (Web Notifications API)
 * Componente C32
 * ...
 */
```

Key features:
1. `NotificationPermissionManager` - request permission
2. `NotificacoesPushClient` class:
   - constructor(config): apiBase, wsUrl, pollingInterval, lembreteAntecedenciaMinutos (15)
   - `iniciar()` - request permission, connect WebSocket, start polling fallback, schedule reminders
   - `solicitarPermissao()`
   - `conectarWebSocket()` - listen for events
   - `agendarLembretesTeleconsulta()` - fetch agenda, schedule setTimeout for each teleconsulta at start - 15min
   - `exibirNotificacao(titulo, opcoes)` - via ServiceWorker if available, else Notification
   - handlers for each event type
   - fallback toast in DOM
   - `destruir()` - cleanup

Event payload examples (aligned with backend):
```json
{
  "tipo": "TELECONSULTA_LEMBRETE",
  "cns_paciente": "700000000000000" (or null),
  "cpf_paciente": "...",
  "teleconsulta_id": "...",
  "inicio_em": "2025-01-01T10:00:00-03:00",
  "profissional": "Dr. ...",
  "link_sala": "/teleconsulta/sala/..."
}
```

LGPD: don't include CID-10 or diagnosis in notification body. I'll add a sanitizer that strips sensitive fields (cid10, ciap2, descricao_clinica) from notification content — good compliance touch.

Also include:
- Deduplication of notifications (avoid duplicates via event IDs)
- Reconnect with exponential backoff for WebSocket
- Fallback polling to `/api/v1/notificacoes/pendentes`
- Visibility: only notify when appropriate; still show even if page hidden (that's the point of notifications)

For tests with pytest: I can provide:
- `backend/tests/test_notificacoes_push.py` — testing the backend endpoint that serves pending notifications (if I define a contract) — but the task is only the JS file. However guidelines say pytest coverage. I could provide pytest tests using Playwright to test the JS behavior, or tests for a small Flask endpoint contract.

Given the scope, I'll deliver:
1. `backend/app/static/js/notificacoes_push.js` — the main component
2. `backend/tests/test_notificacoes_push.py` — pytest tests. For JS testing in pytest, options:
   - Use `pytest-playwright` to load a test page and assert notification behavior (permission mocked).
   - Or test the API contract with a fake server.

I think a pragmatic approach: provide pytest tests that use Playwright to load a fixture HTML page that loads the JS with a mocked Notification API and mocked fetch/WebSocket, asserting the three notification types fire correctly, dedup works, and 15-min scheduling works (with clock injection). That's realistic.

Alternatively, simpler: node-based tests via pytest subprocess. But Playwright is the standard for browser JS testing with pytest.

Let me write the JS carefully.

```javascript
/* eslint-env browser */
/**
 * ============================================================================
 * MedIA · Componente C32 — Notificações e Agendamento Ativo
 * ============================================================================
 * ...
 */
```

Design:

```javascript
(function (global) {
  'use strict';

  const TIPOS_EVENTO = Object.freeze({
    TELECONSULTA_LEMBRETE: 'TELECONSULTA_LEMBRETE',
    PACIENTE_EM_SALA: 'PACIENTE_EM_SALA',
    CONFIRMACAO_PRESENCA: 'CONFIRMACAO_PRESENCA',
  });

  const ANTECEDENCIA_LEMBRETE_MS = 15 * 60 * 1000; // 15 minutos

  // Campos clínicos sensíveis que NUNCA podem aparecer em notificações do SO (LGPD)
  const CAMPOS_SENSIVEIS = Object.freeze(['cid10', 'ciap2', 'descricao_clinica', 'soap', 'anamnese']);

  function agoraMs() { return Date.now(); }

  function sanitizar(dados) { ... shallow copy removing sensitive fields ... }

  function formatarIdentificacao(paciente) {
    // Prioriza CNS (padrão SUS); fallback CPF mascarado
  }

  function mascararCpf(cpf) { return `***.***.${cpf.slice(-3)}-${cpf.slice(-2)}`? } 
```

Hmm, actually for notifications, even name might be fine. Let's show name + masked doc.

Class `NotificacoesPush`:

```javascript
class NotificacoesPush {
  constructor(opcoes = {}) {
    this.apiBase = opcoes.apiBase ?? '/api/v1';
    this.wsUrl = opcoes.wsUrl ?? null;
    this.antecedenciaMs = opcoes.antecedenciaMs ?? ANTECEDENCIA_LEMBRETE_MS;
    this.intervaloPollingMs = opcoes.intervaloPollingMs ?? 30000;
    this.canal = opcoes.canal ?? 'media-notificacoes';
    this._permissao = 'default';
    this._timers = new Set();
    this._agendamentos = new Map(); // teleconsulta_id -> timer
    this._idsProcessados = new Set(); // dedupe
    this._ws = null;
    this._pollingTimer = null;
    this._tentativaReconexao = 0;
    this._destruido = false;
    this._registroSW = opcoes.registroSW ?? null;
    this._onNotificacao = opcoes.onNotificacao ?? null; // hook para testes/telemetria
  }
  ...
}
```

Methods:
- `async iniciar()` — request permission, connect WS, schedule reminders from agenda, start polling fallback
- `async solicitarPermissao()` — returns 'granted' | 'denied' | 'default'
- `async _carregarAgenda()` — GET `${apiBase}/teleconsulta/agenda?status=agendada` returns list with inicio_em
- `agendarLembretes(teleconsultas)` — for each, compute delay = inicio - 15min - now; if 0 < delay, setTimeout; if already within window and not notified, fire now
- `_programarLembrete(teleconsulta)`
- `async conectarWebSocket()`
- `_processarEvento(evento)` — dedupe by evento.id, route by tipo
- `_notificarTeleconsultaLembrete(dados)`
- `_notificarPacienteEmSala(dados)`
- `_notificarConfirmacaoPresenca(dados)`
- `async exibir(titulo, corpo, opcoes)` — use SW showNotification if available, else `new Notification`, else toast fallback; returns boolean
- `_toastFallback(titulo, corpo)`
- `parar()` / `destruir()`

Notification click: focus the room link (`onclick` -> window.focus + location). For SW notifications, we can't attach onclick directly; we'd handle in SW. For simplicity, use `new Notification` with onclick when SW not available; if SW available, pass data and note that SW should handle `notificationclick`. I'll include a small note and pass `data: { url }`.

Also handle `Notification.requestPermission()` promise vs callback (Safari older). I'll wrap:

```javascript
function pedirPermissao() {
  if (!('Notification' in global)) return Promise.resolve('unsupported');
  if (global.Notification.permission !== 'default') return Promise.resolve(global.Notification.permission);
  return new Promise((resolve) => {
    const resultado = global.Notification.requestPermission((estado) => resolve(estado));
    if (resultado && typeof resultado.then === 'function') resultado.then(resolve);
  });
}
```

WebSocket reconnect with exponential backoff: base 1000ms, factor 2, max 30s, jitter.

Polling fallback: GET `${apiBase}/notificacoes/pendentes?desde=<iso>` returns events list; process each.

Scheduling reminders: also re-check agenda periodically (e.g., every 5 min) to pick up new appointments. I'll add `intervaloAgendaMs = 5 * 60 * 1000`.

Clock: allow injecting `agoraFn` for tests.

Dedup: keep Set of processed IDs with max size (e.g., 500) — prune oldest. Simple: if size > 500, clear? Better: use Map with timestamps and prune entries older than 24h. Keep simple: Set with cap.

Sanitization: build notification body from whitelisted fields only, never from raw payload. That's the safest: construct strings explicitly. I'll still sanitize payload copy passed to `data`.

Tagging: use `tag` per type + id so notifications replace rather than stack: e.g., `tag: 'media-lembrete-<id>'`.

Renotify: with tag reuse, set `renotify: true` when using SW.

Now the three notification texts (pt-BR, SUS context):

1. Lembrete teleconsulta:
   - Título: `Teleconsulta em 15 minutos`
   - Corpo: `${paciente} — ${profissional} · ${hora}. Toque para entrar na sala virtual.`
   Actually who receives this? Could be the patient's portal or the professional. The component is generic; event includes role context. Keep generic: "Sua teleconsulta com Dr. X começa às HH:MM."

2. Paciente em sala (professional side):
   - Título: `Paciente aguardando na sala`
   - Corpo: `${nome} (CNS ...1234) está na sala de espera da teleconsulta.`

3. Confirmação de presença:
   - Título: `Presença confirmada`
   - Corpo: `${nome} confirmou presença para a teleconsulta de HH:MM.`

Include `requireInteraction` for lembrete? Maybe true for lembrete (important), false for others. Keep configurable.

Also add `silent` false default.

Now the pytest tests. I'll write `backend/tests/test_notificacoes_push.py` using Playwright:

- Fixture: create a temp HTML page that loads the JS and a test harness script that mocks `Notification`, `WebSocket`, `fetch`. Serve via `page.route` or set content directly with `page.set_content` and add script tag pointing to the file path served... Playwright `set_content` with inline script referencing file:// might be tricky. Better: use `page.route('**/static/js/notificacoes_push.js', ...)` fulfilling with the file content, then `page.set_content(html)`.

Tests:
1. `test_lembrete_teleconsulta_15_minutos` — inject fake agenda with inicio = now + 15min + 2s? That would wait 2s. Better: use `antecedenciaMs` and fake clock. The JS uses `Date.now()`; I can allow option `agoraFn`. In browser test, override `Date.now` via `page.add_init_script` to a controllable clock. Simpler: schedule a teleconsulta starting in 15min + 3s with antecedenciaMs = 15min → delay ≈ 3s → wait ~4s for notification. Acceptable test duration. Or make antecedencia configurable: set inicio = now + 20s, antecedenciaMs = 15min → delay = 20s - 15min < 0 → fires immediately (within window). Hmm that tests "already within window fires now". For the exact 15-min behavior, better to test the computation: expose a pure function `calcularAtrasoLembrete(inicioEm, agoraMs, antecedenciaMs)` and unit-test it via `page.evaluate`. Plus an integration test with short delay.

Let me expose the module for tests: attach to `window.MedIANotificacoes` with internals for testing (`__teste` namespace exposing pure functions). That's pragmatic.

2. `test_paciente_em_sala_notificacao` — dispatch fake WS message, assert Notification constructed with correct title/body and no sensitive fields.
3. `test_confirmacao_presenca` — same.
4. `test_sem_permissao_usa_toast` — permission denied → DOM toast fallback created.
5. `test_dedupe` — same event id twice → only one notification.
6. `test_sanitizacao_lgpd` — event containing cid10 → body does not contain it.

Mock Notification in init script:

```javascript
window.__notificacoesCriadas = [];
class FakeNotification {
  constructor(titulo, opcoes) { window.__notificacoesCriadas.push({ titulo, opcoes }); this.close = () => {}; }
  static get permission() { return window.__permissaoSimulada || 'granted'; }
  static requestPermission(cb) { const p = Promise.resolve(window.__permissaoSimulada || 'granted'); if (cb) p.then(cb); return p; }
}
window.Notification = FakeNotification;
```

Mock WebSocket:

```javascript
window.__wsMensagens = [];
class FakeWebSocket {
  constructor(url) { this.url = url; FakeWebSocket.instancia = this; this.readyState = 0; }
  send() {}
  close() { this.readyState = 3; }
  // helper: servidor simula mensagem
  _servidorMensagem(dados) { this.onmessage && this.onmessage({ data: JSON.stringify(dados) }); }
  _servidorAberto() { this.readyState = 1; this.onopen && this.onopen(); }
}
window.WebSocket = FakeWebSocket;
```

Mock fetch for agenda/pendentes endpoints via `page.route`.

The JS module: I'll write it as an IIFE attaching `window.MedIANotificacoes = { NotificacoesPush, TIPOS_EVENTO, calcularAtrasoLembrete, ... }` and also `export` if module? Can't do both cleanly without UMD tricks. For Flask static file loaded via `<script src>`, IIFE global is right. I'll do IIFE + `typeof module !== 'undefined'` export guard for Node tests maybe. Keep IIFE + global.

Let me now write the full JS file with good docs, JSDoc types, pt-BR comments (project is Brazilian SUS). Code comments in Portuguese makes sense given the context.

Also include a small auto-init snippet: if `document.currentScript` has data attributes (data-api-base, data-ws-url), auto-start on DOMContentLoaded. Nice for drop-in usage.

Let me write it:

```javascript
/**
 * ============================================================================
 *  MedIA · Componente C32 — Notificações e Agendamento Ativo
 *  backend/app/static/js/notificacoes_push.js
 * ============================================================================
 *  Suporte a Web Notifications API para o fluxo de teleconsulta do SUS/APS:
 *
 *   1. TELECONSULTA_LEMBRETE  — lembrete disparado 15 minutos antes do início;
 *   2. PACIENTE_EM_SALA       — aviso ao profissional quando o paciente entra
 *                               na sala de espera virtual;
 *   3. CONFIRMACAO_PRESENCA   — confirmação de presença do paciente.
 *
 *  Conformidade:
 *   - LGPD/CFM: notificações carregam APENAS dados mínimos (nome, CNS/CPF
 *     mascarado, horário). Campos clínicos (CID-10, CIAP-2, SOAP) são
 *     removidos por lista de bloqueio antes de qualquer exibição.
 *   - Identificação prioriza CNS (padrão SUS) com fallback a CPF mascarado.
 *   - Transporte: WebSocket (tempo real) com fallback de polling REST.
 *
 *  Uso mínimo:
 *    <script src="/static/js/notificacoes_push.js"
 *            data-api-base="/api/v1"
 *            data-ws-url="wss://host/ws/notificacoes"></script>
 *  ou programático:
 *    const push = new MedIANotificacoes.NotificacoesPush({ wsUrl: '...' });
 *    await push.iniciar();
 * ============================================================================
 */
```

Then the IIFE.

Full code plan:

```javascript
(function (global) {
  'use strict';

  // ------------------------------------------------------------------
  // Constantes
  // ------------------------------------------------------------------
  const TIPOS_EVENTO = Object.freeze({
    TELECONS