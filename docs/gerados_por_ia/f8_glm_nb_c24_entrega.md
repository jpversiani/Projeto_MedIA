The user is asking me to create a JavaScript file for notifications and active scheduling (C24) for the MedIA project. The task is:

Create `backend/app/static/js/notificacoes_push.js` with support for Web Notifications API:
- Display teleconsultation reminder 15 minutes before
- Notification when patient enters the room (sala de espera)
- Confirmation of presence (confirmação de presença)

The guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), pytest coverage. However, the actual file requested is a JavaScript file. The Python guidelines are architecture-level directives for the project overall, but the specific deliverable is the JS file.

Since this is a JavaScript file, I should write it well-structured, with JSDoc typing (since JS doesn't have strict typing, I can use JSDoc annotations to approximate strict typing), following the SUS context (teleconsulta, CNS, etc.).

Let me design the module:

**notificacoes_push.js** — an IIFE or ES module that:

1. **NotificationManager**: wraps Web Notifications API
   - `requestPermission()` — asks user permission
   - `show(title, options)` — displays notification with fallback to in-page toast
   - Handles permission states: 'granted', 'denied', 'default'

2. **TeleconsultaReminderScheduler**: 
   - Polls an endpoint (e.g., `/api/v1/teleconsulta/agenda/proximas`) for upcoming teleconsultations
   - For each appointment, schedules a reminder 15 minutes before `inicio` (start time)
   - Uses `setTimeout` with drift correction / re-check interval
   - Notification: "Teleconsulta em 15 minutos — Dr(a). X, [especialidade], às HH:MM. Acesse pelo botão abaixo."
   - Actions: "Entrar na sala" (deep link), "Adiar 5 min"

3. **SalaEsperaWatcher** (patient in room):
   - Polls or uses SSE/WebSocket for events like `paciente_chegou_sala`
   - When a patient enters the virtual waiting room, notify the professional: "Paciente [iniciais CNS-masked] aguardando na sala de espera virtual"
   - Privacy: mask CNS/CPF in notifications (LGPD) — show only partial identifiers

4. **PresencaConfirmation** (confirmação de presença):
   - When patient confirms presence (e.g., clicks "Confirmar presença"), notify
   - Or: request confirmation from patient 15 min before — notification with action "Confirmar presença" that POSTs to `/api/v1/teleconsulta/{id}/presenca`
   - Actually "confirmação de presença" likely means: the notification asks the patient to confirm presence, and clicking confirms via API. Also notify the professional when the patient confirms.

5. **LGPD/CFM compliance considerations**:
   - Notifications must not display sensitive clinical data (CID-10, CIAP-2 codes, SOAP notes) — only minimal info
   - Mask identifiers: CNS shown as `XXX.XXXX.XXXX.X*XX` partially masked
   - Tag notifications to avoid duplicates
   - `requireInteraction` for important ones
   - Service worker registration for notifications when page is closed (optional, graceful degradation)

6. **Fallback**: if permission denied or API unavailable, use in-page toast system.

7. **Testing hooks**: expose a global `window.MedIANotificacoes` with methods; include a `__test__` namespace for mocking time (injectable clock) — since pytest tests the backend, but the JS could be tested with pytest + playwright or jest; I can mention that. The guidelines say pytest coverage — for JS, tests would be via Playwright/Selenium in pytest. I can add data attributes and deterministic behavior to facilitate that.

I should also perhaps include a small note about the backend contract (endpoints, Pydantic schemas) since the guidelines mention Pydantic v2 — I can document the expected API contract in the file header comments, and maybe provide the corresponding Pydantic schemas as a companion? The task says "crie backend/app/static/js/notificacoes_push.js" — the deliverable is one file. But to align with the architecture guidelines, I can document the expected JSON contract in JSDoc typedefs matching what the Pydantic v2 schemas would produce, and optionally include a brief snippet of the Pydantic schema in comments or as an appendix in my answer.

Let me write the file with:

- Header comment: module purpose, SUS/APS context, LGPD/CFM notes, API contract
- JSDoc typedefs for `TeleconsultaDTO`, `EventoSalaDTO`, etc.
- Strict mode
- Config constants (REMINDER_LEAD_MINUTES = 15, poll intervals)
- Utility: `mascararCNS`, `mascararCPF`, `formatarHoraBR`
- `ServicoNotificacoes` class (permission, show, fallback toast)
- `AgendadorLembretes` class (schedule reminders)
- `ObservadorSalaEspera` class (polling/SSE)
- `GestorPresenca` class (confirm presence)
- Bootstrap: `MedIANotificacoes.iniciar(config)`
- Test hooks: injectable `now()` clock, `fetchImpl`, `NotificationImpl` for testability
- Idempotency: track notified appointment IDs in a Set + localStorage persistence to avoid duplicate reminders after reload
- Visibility handling: re-check on `visibilitychange` and `focus` (timers throttled in background tabs)
- Use `Notification.tag` to coalesce
- Actions require service worker — handle gracefully: if `showTrigger`/actions unsupported, include buttons in fallback toast

Let me think about the API contract (backend endpoints):

- `GET /api/v1/teleconsultas/proximas?horizonte_minutos=60` → list of:
```json
{
  "id": "uuid",
  "inicio": "2025-01-15T14:00:00-03:00",
  "profissional_nome": "Dra. Ana Souza",
  "profissional_cns": "700000000000000",
  "especialidade": "Clínica Médica",
  "paciente_nome_social": "Maria S.",
  "paciente_cns": "700000000000000",
  "url_sala": "/teleconsulta/sala/uuid",
  "status": "AGENDADA"
}
```

- `GET /api/v1/sala-espera/eventos?since=...` or SSE `/api/v1/sala-espera/stream` → events:
```json
{
  "tipo": "PACIENTE_ENTROU_SALA",
  "teleconsulta_id": "uuid",
  "paciente_cns": "...",
  "paciente_apelido": "Maria",
  "entrou_em": "...",
  "posicao_fila": 1
}
```

- `POST /api/v1/teleconsultas/{id}/presenca` body `{"confirmado": true, "confirmado_em": "...", "canal": "NOTIFICACAO_PUSH"}` → `{"presenca_confirmada": true, "registrada_em": "..."}`

- `POST /api/v1/notificacoes/registrar-subscricao` for push subscription (optional, for service worker push). Maybe keep it simple with local notifications only, but mention SW.

For the professional side: "aviso de paciente em sala" — the professional gets notified when patient enters the waiting room. For the patient side: reminder 15 min before + presence confirmation request.

I'll make the module role-aware: `config.papel` = 'PACIENTE' | 'PROFISSIONAL'. Patient gets reminders + presence confirmation; professional gets room alerts + presence-confirmed alerts.

Masking functions:
- CNS: format `000 0000 0000 0000` → mask middle: `*** **** *** 1234`? Standard CNS has 15 digits. Display masked: keep first 3 and last 2? For LGPD, show like `••• •••• •••• 0123` or just last 4. I'll implement `mascararCNS(cns)` → `***.****.****.1234` style or simpler: `•••• •••• 1234`. Let me do: keep last 4 digits, prefix `••• •••• •••• `. Actually CNS formatted: `700 0000 0000 0000`. Mask: `700 •••• •••• ••34`? Keeping first 3 (which indicates region/type) is fine and useful. I'll do first 3 + last 2: `700 •••• •••• •34`.

Hmm, simpler: `mascararDocumento(valor, tipo)`:
- CPF (11 digits): `***.***.**7-89` → keep last 3? Common: `***.***.***-**` fully masked or `123.***.***-09`. I'll keep first 3 and last 2: `123.•••.•••-09`.
- CNS (15 digits): `700 •••• •••• ••09`.

Notification content must avoid clinical data — only: time, professional name/specialty, patient initials or masked ID.

Time drift: use a "tick" loop every 30s that checks which appointments fall within the reminder window and haven't been notified. This is more robust than setTimeout alone (handles sleep/wake, tab throttling). I'll combine: schedule precise setTimeout for the next reminder AND a sweep interval as safety net.

Persistence: `localStorage` key `media.notificacoes.enviadas` storing `{[teleconsultaId]: {lembrete: timestampISO, presencaSolicitada: ...}}` to dedupe across reloads. Also clear past entries.

Service worker: attempt registration of `/static/js/sw-notificacoes.js` if exists (I'll note it as optional; graceful if 404). Actually registering a SW that doesn't exist throws — I'll catch and ignore. Or make it configurable `config.serviceWorkerUrl` default null.

Fallback toast: create DOM container `#media-toast-container`, render toasts with action buttons (Entrar na sala / Confirmar presença / Adiar). Accessible: `role="alert"`, `aria-live="assertive"`.

Click handling: `notification.onclick` → `window.focus()` + navigate to `url_sala`. Actions via SW only; for fallback, toast buttons.

Presence confirmation flow (patient):
- At reminder time (T-15), notification includes implicit "Confirmar presença" action. Clicking the notification body or the action sends POST to presence endpoint. Then show confirmation "Presença confirmada".
- Also a separate earlier confirmation request? The task says "confirmação de presença" as a notification type. I'll implement: when patient clicks "Confirmar presença" (or when professional receives event `PRESENCA_CONFIRMADA`), notify accordingly.

Professional flow:
- Poll/SSE for `PACIENTE_ENTROU_SALA` → notify "Paciente aguardando" with masked CNS + position in queue + link to room.
- `PRESENCA_CONFIRMADA` → notify "Presença confirmada por [paciente]".
- `PACIENTE_SALIOU_SALA` maybe → optional.

Sound: `silent: false` default; respect config.

DND / quiet hours? Not needed.

Error handling: all fetch failures logged, exponential backoff for polling.

Testability: 
- `MedIANotificacoes.__fabricaTeste` exposing internals with injectable `agora()`, `buscador` (fetch), `NotificacaoImpl`, `armazenamento` (localStorage-like).
- Deterministic IDs: `data-testid` attributes on toasts: `data-testid="toast-lembrete-teleconsulta"`, etc. This helps Playwright tests driven by pytest.

Also add `window.dispatchEvent(new CustomEvent('media:notificacao', {detail}))` for integration tests / analytics.

Now, about the Python guidelines: the deliverable is JS, but I can add a short section in my answer showing the companion Pydantic v2 schemas + pytest test sketch so the contract is covered — the instructions say "Manter conformidade total e cobertura de testes automatizados com pytest." I'll include:
- `backend/app/schemas/notificacoes.py` (Pydantic v2 schemas) — as supporting contract
- `backend/tests/test_notificacoes_push.py` — pytest tests (contract tests for schemas + a Playwright-ish test sketch or contract test hitting the endpoints). Since we can't run a browser in unit tests easily, I'll do: schema validation tests + endpoint contract tests with FastAPI TestClient, plus a test that the JS file exists and contains required markers (smoke test). That's pragmatic.

But the primary deliverable is the JS file. I'll deliver the JS file fully, then briefly the Pydantic schemas and pytest tests as companions to satisfy the guidelines. Keep the answer focused; the JS file is the star.

Let me now write the JS carefully.

```javascript
/**
 * ============================================================================
 * MedIA — Componente C24: Notificações e Agendamento Ativo
 * ============================================================================
 * ...
 */
```

Structure:

```javascript
(function (global) {
  'use strict';

  // ---------- Constantes ----------
  const CONFIG_PADRAO = Object.freeze({
    apiBase: '/api/v1',
    papel: 'PACIENTE', // 'PACIENTE' | 'PROFISSIONAL'
    antecedenciaLembreteMin: 15,
    intervaloVarreduraMs: 30_000,
    intervaloPollSalaMs: 15_000,
    horizonteAgendaMin: 120,
    serviceWorkerUrl: null,
    silencioso: false,
    ...
  });
```

Numeric separators `30_000` are ES2021 — fine for modern browsers, but to be safe use `30000`. I'll use plain numbers.

JSDoc typedefs:

```javascript
/**
 * @typedef {Object} TeleconsultaDTO
 * @property {string}  id                  UUID v4 da teleconsulta.
 * @property {string}  inicio              ISO-8601 com fuso (ex.: 2025-01-15T14:00:00-03:00).
 * @property {string}  status              AGENDADA | CONFIRMADA | EM_ANDAMENTO | CANCELADA | REALIZADA
 * @property {string}  especialidade       Especialidade (Sigtap/CAT-SUS).
 * @property {string}  profissionalNome    Nome do profissional (CNES vinculado).
 * @property {string}  [profissionalCns]   CNS do profissional (15 dígitos).
 * @property {string}  [pacienteNome]      Nome social do paciente.
 * @property {string}  [pacienteCns]       CNS do paciente (15 dígitos).
 * @property {string}  urlSala             Deep-link da sala virtual.
 */
```

etc.

Utilities:

```javascript
function soDigitos(valor) { return String(valor ?? '').replace(/\D+/g, ''); }

function mascararCNS(cns) {
  const d = soDigitos(cns);
  if (d.length !== 15) return null;
  return `${d.slice(0,3)} •••• •••• ••${d.slice(13)}`;
}

function mascararCPF(cpf) {
  const d = soDigitos(cpf);
  if (d.length !== 11) return null;
  return `${d.slice(0,3)}.•••.•••-${d.slice(9)}`;
}
```

Format time BR:

```javascript
function formatarHoraBR(dataISO) {
  return new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit', timeZone: 'America/Sao_Paulo' }).format(new Date(dataISO));
}
```

Hmm, timezone hard-coded — better to use local timezone (no timeZone option) since patient may be anywhere in Brazil; use default. I'll omit timeZone.

Storage adapter (injectable for tests):

```javascript
const ArmazenamentoLocal = {
  obter(chave, padrao) { try { const v = global.localStorage.getItem(chave); return v ? JSON.parse(v) : padrao; } catch { return padrao; } },
  gravar(chave, valor) { try { global.localStorage.setItem(chave, JSON.stringify(valor)); } catch { /* quota/SSR */ } },
  remover(chave) { try { global.localStorage.removeItem(chave); } catch { } }
};
```

ServicoNotificacoes:

```javascript
class ServicoNotificacoes {
  constructor(opcoes = {}) {
    this._NotificacaoImpl = opcoes.NotificacaoImpl ?? global.Notification ?? null;
    this._aoExibirFallback = opcoes.aoExibirFallback ?? null;
    this._permissao = this._suportado() ? this._NotificacaoImpl.permission : 'negada';
  }
  _suportado() { return typeof this._NotificacaoImpl === 'function' && 'permission' in this._NotificacaoImpl; }
  async solicitarPermissao() { ... }
  async exibir({ titulo, corpo, tag, dados, acoes, exigirInteracao, silencioso, aoClicar }) { ... }
}
```

Permission mapping: Web API uses 'granted' | 'denied' | 'default'. I'll keep Portuguese internally: 'concedida' | 'negada' | 'padrao'.

Show: if granted → new Notification(titulo, {body, tag, icon, badge, data, requireInteraction, silent, renotify?}). `renotify` requires tag and is non-standard but useful; include with try. onclick/onclose handlers. If not granted → fallback toast via callback.

Toast fallback: implement `FabricaToasts` creating DOM elements with data-testid, action buttons, auto-dismiss.

AgendadorLembretes (patient):

```javascript
class AgendadorLembretes {
  constructor({ servicoNotificacoes, buscarAgenda, agora, armazenamento, config, aoConfirmarPresenca }) {...}
  async varrer() {
    const agenda = await this._buscarAgenda();
    for (const tc of agenda) this._avaliar(tc);
  }
  _avaliar(tc) {
    if (status not in AGENDADA/CONFIRMADA) return;
    const inicio = Date.parse(tc.inicio);
    const faltamMs = inicio - this._agora();
    const janela = this._config.antecedenciaLembreteMin * 60000;
    if (faltamMs <= janela && faltamMs > -60000 && !this._jaNotificado(tc