The user wants me to create a JavaScript file for notifications and active scheduling (C16) for the MedIA project. The task is:

Create `backend/app/static/js/notificacoes_push.js` with support for Web Notifications API:
- Display teleconsultation reminder 15 minutes before
- Notification when patient enters waiting room (sala de espera)
- Confirmation of presence (confirmação de presença)

The guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP, CNS/CPF), and pytest test coverage. However, the main deliverable is a JavaScript file. The Python guidelines apply to the broader architecture context — but since the deliverable is JS, I should focus on that. However, I could also provide supporting Python code (e.g., an API endpoint contract, Pydantic schemas for notifications, and pytest tests) to comply with the architecture guidelines.

Let me think about what makes sense:

1. **Main deliverable**: `backend/app/static/js/notificacoes_push.js` — a vanilla JS module (or class) that:
   - Requests Notification permission
   - Polls or connects (SSE/WebSocket) to backend for notification events
   - Shows notifications:
     - Teleconsulta reminder 15 min before (based on scheduled time)
     - Patient in waiting room (professional side)
     - Presence confirmation (patient confirmed attendance)
   - Handles fallbacks (permission denied, unsupported browsers)
   - In-page toast fallback when notifications are denied or page is focused
   - LGPD considerations (health data — avoid exposing sensitive data in notification body; use generic text)
   - CNS/CPF masking considerations — don't leak full identifiers in notifications

2. **Supporting backend contract** (to comply with architecture guidelines): I can include:
   - Pydantic v2 schemas for notification payloads (`NotificationOut`, etc.)
   - SQLAlchemy 2.0 model for notifications (optional)
   - FastAPI endpoints (SSE endpoint for notifications stream, or polling endpoint)
   - pytest tests

Given the instruction says "Execute com precisão conforme as diretrizes" and the guidelines mention Python typing, Pydantic, SQLAlchemy, pytest — I should deliver the JS file as the core, plus the backend contract (schemas + endpoint + tests) to make it a complete, compliant component. But I must be careful not to bloat. The task explicitly says "crie backend/app/static/js/notificacoes_push.js" — so the JS file is the primary artifact. The architecture guidelines suggest the surrounding Python ecosystem should be consistent. I'll provide:

1. The JS file (main, detailed, well-commented in Portuguese)
2. A brief backend contract: Pydantic v2 schemas + FastAPI SSE endpoint + SQLAlchemy model (concise)
3. pytest tests for the backend contract
4. Maybe a small JS test note (pytest can't test JS; but I can mention integration tests or provide a minimal test using the endpoint)

Let me design the JS file:

```javascript
/**
 * MedIA — Componente C16: Notificações e Agendamento Ativo
 * ...
 */
```

Key features:

- `NotificationManager` class (IIFE or ES module). Since it's served as static JS, I'll use an ES module or a global class. To be safe with older setups, use an IIFE exposing `window.MedIANotificacoes`. Actually ES modules are fine in modern browsers; but Flask static files often loaded via `<script src>`. I'll write it as an IIFE that attaches to window, with `'use strict'`.

- Configuration: endpoints configurable via `data-*` attributes on a mount element or a global config object `window.MEDIA_CONFIG`.

- Permission flow:
  - `Notification.requestPermission()` on user gesture (button click), not on page load (best practice).
  - Handle `granted`, `denied`, `default`.

- Event sources:
  - SSE via `EventSource` to `/api/v1/notificacoes/stream` (preferred), with fallback to polling `/api/v1/notificacoes/pendentes` every N seconds.
  - Handle reconnection with exponential backoff.

- Notification types (enum aligned with backend):
  - `LEMBRETE_TELECONSULTA` — 15 min before: the backend sends scheduled events, but the client can also compute locally from the agenda. The spec says "exibição de lembrete de teleconsulta 15 minutos antes" — I'll implement both: client-side scheduler that checks upcoming appointments (fetched from `/api/v1/teleconsultas/proximas`) and schedules a timeout for (start - 15min), plus server-pushed events.
  - `PACIENTE_EM_SALA` — patient checked into waiting room (professional side).
  - `CONFIRMACAO_PRESENCA` — patient confirmed presence.

- Notification content: title, body, icon, tag (to dedupe), requireInteraction for reminders, data with URL to open on click (e.g., join teleconsultation room).

- Click handling: `notification.onclick` → `window.focus()` + navigate to `data.url`.

- LGPD/CFM compliance: notification body must not contain sensitive clinical data (CID-10, diagnoses). Use generic messages. Mask CNS/CPF — never display them. Log audit events? Keep minimal.

- Toast fallback: if permission denied or `Notification` unsupported, render in-page toasts (accessible, aria-live).

- Service Worker registration for notifications when page closed? That's advanced; I can include optional SW registration hook (`navigator.serviceWorker.ready` → `registration.showNotification`) with graceful fallback to `new Notification()`. I'll include it as optional if a SW path is configured.

- Local scheduler for the 15-min reminder:
  - Fetch upcoming teleconsultations: `[{ id, inicio (ISO 8601 with timezone), paciente_label, url_sala }]`
  - For each, compute `inicio - 15*60*1000 - Date.now()`; if between 0 and some max (e.g., 24h), `setTimeout`. Cap timeouts (browsers throttle long timers in background tabs; also re-check periodically). Use a re-check loop every minute to avoid drift and handle timers killed in background.
  - Dedupe with a Set of shown IDs (and persist in sessionStorage to avoid duplicates on reload within session).

- Heartbeat/ack: mark notification as read via POST `/api/v1/notificacoes/{id}/ack`.

- Accessibility: aria-live region for toasts.

- Timezone: use ISO strings with offset; parse with `Date`. Brazil: America/Sao_Paulo. Use `Intl.DateTimeFormat('pt-BR', { timeZone: 'America/Sao_Paulo' })` for display.

- CNS validation? Not needed in JS here, but masking helper could exist. Keep a `mascararIdentificador` helper that never exposes full CNS/CPF — actually better: backend sends only `paciente_label` like "Paciente M. S." — client just displays. I'll include a sanitizer that strips any CNS/CPF-like sequences from notification text as defense-in-depth (regex for 11-digit CPF patterns and CNS 15-digit patterns) — that's a nice compliance touch.

Let me write the code.

Structure of the JS file:

```javascript
/**
 * ============================================================================
 * MedIA — C16: Componente de Notificações e Agendamento Ativo
 * ----------------------------------------------------------------------------
 * ...header docs...
 * ============================================================================
 */
(function (window, document) {
  'use strict';

  const TIPOS_NOTIFICACAO = Object.freeze({
    LEMBRETE_TELECONSULTA: 'LEMBRETE_TELECONSULTA',
    PACIENTE_EM_SALA: 'PACIENTE_EM_SALA',
    CONFIRMACAO_PRESENCA: 'CONFIRMACAO_PRESENCA',
  });

  const CONFIG_PADRAO = Object.freeze({
    endpointStream: '/api/v1/notificacoes/stream',
    endpointPendentes: '/api/v1/notificacoes/pendentes',
    endpointAck: '/api/v1/notificacoes/{id}/ack',
    endpointAgenda: '/api/v1/teleconsultas/proximas',
    intervaloPollingMs: 30000,
    antecedenciaLembreteMs: 15 * 60 * 1000,
    cicloReavaliacaoAgendaMs: 60 * 1000,
    janelaAgendaMs: 24 * 60 * 60 * 1000,
    fusoExibicao: 'America/Sao_Paulo',
    usarServiceWorker: true,
    caminhoServiceWorker: '/static/js/sw-notificacoes.js',
    maxReconexoes: 8,
  });
  
  ...
})(window, document);
```

Classes/functions:

- `NotificacoesPush` main class:
  - `constructor(opcoes)` merges config
  - `iniciar()` — bind, fetch agenda, open stream
  - `solicitarPermissao()` — must be called from user gesture; returns promise
  - `_conectarStream()` — EventSource with onmessage; parse JSON; validate with `_validarPayload` (lightweight schema check); route to `_processarNotificacao`
  - `_iniciarPolling()` fallback
  - `_processarNotificacao(payload)` — dedupe by id, sanitize text, show
  - `_exibir(notificacao)` — SW or Notification API or toast
  - `_agendarLembretes()` — fetch agenda, compute timers
  - `_verificarAgenda()` — periodic re-check
  - `_montarTitulo/Corpo` per type
  - `_registrarAck(id)`
  - `_toastFallback(notificacao)`
  - `_sanitizarTexto(texto)` — strip CPF/CNS patterns
  - `_deveExibirLembrete(teleconsulta)` — time math

- Dedupe: `Set` + `sessionStorage` key `media.notific.exibidas`.

- Auto-init: `document.addEventListener('DOMContentLoaded', ...)` reading `#media-notificacoes` element with data attributes, or `window.MEDIA_NOTIFICACOES_CONFIG`.

Payload contract (Pydantic):

```python
class NotificacaoBase(BaseModel):
    id: UUID
    tipo: TipoNotificacao  # enum
    titulo: str
    corpo: str
    ocorrido_em: datetime
    url_destino: str | None
    requer_interacao: bool = False
    tag: str | None
```

Backend: FastAPI SSE endpoint streaming `text/event-stream`, SQLAlchemy 2.0 model `Notificacao`, and a scheduler note (APScheduler or celery beat) that generates `LEMBRETE_TELECONSULTA` 15 min before — but the JS also has a client-side scheduler as redundancy. The task focuses on the JS; I'll provide a compact but complete backend contract module + tests.

Given the response length constraints, I'll aim for:

1. `backend/app/static/js/notificacoes_push.js` — full, ~350-450 lines with comments.
2. `backend/app/schemas/notificacao.py` — Pydantic v2 schemas (compact).
3. `backend/app/models/notificacao.py` — SQLAlchemy 2.0 model (compact) — maybe merge into one file presentation.
4. `backend/app/api/v1/notificacoes.py` — SSE + polling + ack endpoints (compact).
5. `backend/tests/test_notificacoes_push.py` — pytest tests for schemas/endpoints.

That's a lot. Let me be judicious: the primary artifact is the JS. The guidelines demand Python typing/Pydantic/SQLAlchemy/pytest compliance — I'll include a consolidated backend contract file and tests, but keep them tight. Maybe combine schemas+model+endpoints into one listing per file but concise.

Actually, let me reconsider scope. The instruction: "crie backend/app/static/js/notificacoes_push.js com suporte a Web Notifications API: exibição de lembrete de teleconsulta 15 minutos antes, aviso de paciente em sala e confirmação de presença." The diretrizes are general project guidelines. The best answer: deliver the JS file thoroughly, then provide the minimal backend contract (schemas + endpoints) and pytest tests so the component is verifiable, as the guidelines demand test coverage. I'll keep backend code focused on the notification contract.

Let me draft the JS carefully.

Key design decisions for JS:

1. **Permission**: request only on explicit user action. Provide `MedIANotificacoes.solicitarPermissao()` and auto-bind to elements with `[data-media-notific-permissao]`.

2. **Transport**: SSE primary; polling fallback if EventSource fails or unsupported. Reconnect with backoff.

3. **Reminder scheduling**: 
   - Fetch agenda on start and every `cicloReavaliacaoAgendaMs`.
   - For each teleconsulta with `inicio` in future and `inicio - now <= janelaAgendaMs`, schedule `setTimeout` at `inicio - antecedencia`. Store timer ids; clear on re-fetch to avoid duplicates; dedupe by teleconsulta id in shown-set.
   - Also guard: if `inicio - now < antecedencia` and not yet shown and `now < inicio`, show immediately (page loaded inside the 15-min window).

4. **Sanitization**: remove CPF (11 digits, possibly formatted `###.###.###-##`) and CNS (15 digits `### #### #### ####`) patterns from title/body before display. Replace with `[identificador protegido]`.

5. **Dedupe/persist**: `sessionStorage` array of ids; cap size.

6. **Ack**: fire-and-forget POST with keepalive.

7. **Click routing**: focus + `window.location.assign(url)` if same-origin; validate same-origin to avoid open redirect (security touch).

8. **Toasts**: container appended to body, `role="status"` `aria-live="polite"`, auto-dismiss, close button.

9. **Service worker**: optional; if `usarServiceWorker` and SW supported and registration succeeds, use `registration.showNotification`. Else `new Notification`. Wrap in try/catch.

10. **Visibility**: when page hidden, prefer system notifications; when visible, toasts + system (configurable). Keep simple: always attempt system notification if permission granted; also show toast when page visible.

11. **Logging**: namespaced `console.debug` guarded by flag.

12. **i18n/pt-BR**: messages in Portuguese, formatted dates via Intl.

13. **Strict typing in JS**: JSDoc types for editor support — nice touch aligning with "tipagem estrita" spirit. I'll add JSDoc typedefs.

Now the backend contract:

`backend/app/schemas/notificacao.py`:

```python
from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class TipoNotificacao(StrEnum):
    LEMBRETE_TELECONSULTA = "LEMBRETE_TELECONSULTA"
    PACIENTE_EM_SALA = "PACIENTE_EM_SALA"
    CONFIRMACAO_PRESENCA = "CONFIRMACAO_PRESENCA"


class TeleconsultaAgenda(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inicio: datetime  # ISO 8601 com fuso
    paciente_label: str = Field(..., examples=["Paciente M. S."])
    url_sala: str | None = None


class NotificacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tipo: TipoNotificacao
    titulo: str = Field(max_length=120)
    corpo: str = Field(max_length=280)
    ocorrido_em: datetime
    url_destino: str | None = None
    requer_interacao: bool = False
    tag: str | None = None

    @field_validator("titulo", "corpo")
    @classmethod
    def validar_sem_identificador(cls, v: str) -> str:
        # LGPD: nunca expor CNS/CPF integral em notificações
        ...
```

Hmm, validators for CPF/CNS leakage — good compliance touch.

`backend/app/models/notificacao.py` — SQLAlchemy 2.0:

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Notificacao(Base):
    __tablename__ = "notificacao"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(40), index=True)
    titulo: Mapped[str] = mapped_column(String(120))
    corpo: Mapped[str] = mapped_column(String(280))
    ocorrido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    lida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    url_destino: Mapped[str | None] = mapped_column(String(512))
    requer_interacao: Mapped[bool] = mapped_column(Boolean, default=False)
    tag: Mapped[str | None] = mapped_column(String(80))
```

`backend/app/api/v1/notificacoes.py` — FastAPI endpoints:

- `GET /api/v1/notificacoes/pendentes` → list[NotificacaoOut] (unread)
- `POST /api/v1/notificacoes/{id}/ack` → 204
- `GET /api/v1/notificacoes/stream` → SSE (text/event-stream) — using `sse-starlette`'s `EventSourceResponse` or manual StreamingResponse. I'll use a simple async generator with `StreamingResponse`, media_type "text/event-stream". Keep it simple; note auth dependency placeholders.
- `GET /api/v1/teleconsultas/proximas` → list[TeleconsultaAgenda]

For SSE, I'll write an async generator polling the DB every few seconds for new notifications for the current user, yielding `data: {json}\n\n`. Use `anyio` sleep. Keep concise.

pytest tests: `backend/tests/test_notificacoes_push.py`:
- Test schema validation (CPF leak blocked, valid payload passes, enum values).
- Test endpoints with httpx AsyncClient + dependency overrides (in-memory fake). To keep it runnable without full app, I'll write tests against the router with dependency_overrides and a fake session/repository. Simpler: test schemas + a pure function `montar_mensagem_lembrete` maybe. But guidelines want endpoint coverage. I'll write tests using FastAPI TestClient with dependency overrides for `get_db` and `get_usuario_atual`, using sqlite in-memory with SQLAlchemy. That's a fair amount of code but standard.

Given response size, I'll write compact but complete tests: schema tests + endpoint tests (