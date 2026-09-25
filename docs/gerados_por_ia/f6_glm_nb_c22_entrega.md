Let me analyze this task carefully.

The task is to create a JavaScript file: `backend/app/static/js/copiloto_sidebar.js` — a widget for the doctor's telehealth screen (Home Office) that displays in real-time:
1. Blinking alerts for risk/allergy
2. Button "Preencher SOAP com Sugestão da IA" (Fill SOAP with AI Suggestion)
3. Suggestions for complementary exams and usual SUS dosages

The architecture guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest test coverage.

However, the actual file requested is a JavaScript file (frontend widget). The guidelines mention Python backend standards, but the deliverable is JS. I should create the JavaScript widget that consumes backend API endpoints (which would be Python/Pydantic-based). I should probably also provide the supporting backend pieces (Pydantic schemas, SQLAlchemy models, FastAPI endpoints) and pytest tests to satisfy the "conformidade total e cobertura de testes automatizados com pytest" requirement — since the task says to maintain full compliance and test coverage.

Given the instruction says "crie backend/app/static/js/copiloto_sidebar.js" — the main deliverable is the JS file. But the guidelines emphasize Python typing, Pydantic v2, SQLAlchemy 2.0, and pytest coverage. A reasonable interpretation: deliver the JS widget as the primary artifact, plus the backend contract it depends on (Pydantic schemas + FastAPI router + SQLAlchemy models) and pytest tests, so the whole feature is compliant and testable.

Let me design this properly for a Brazilian SUS/APS telehealth context:

**Domain concepts:**
- CNS (Cartão Nacional de Saúde) — 15 digits, validation algorithm exists
- CPF — 11 digits with check digits
- CIAP-2 — International Classification of Primary Care, used in APS (Atenção Primária à Saúde) in Brazil via e-SUS APS
- CID-10 — ICD-10
- SOAP — Subjective, Objective, Assessment, Plan
- SUS dosages — standard dosing per Ministério da Saúde / Formulário Terapêutico Nacional (FTN)
- Allergies — Alergias (medicamentosas, alimentares)
- Risk alerts — e.g., chronic conditions (diabetes, hipertensão), high-risk pregnancy, drug interactions

**JS Widget design:**
- A sidebar widget (copiloto) that:
  - Polls or uses WebSocket/SSE for real-time updates
  - Renders blinking risk/allergy alerts (CSS animation)
  - Has a button "Preencher SOAP com Sugestão da IA" that fetches AI suggestion and dispatches an event (or calls a callback) to populate SOAP fields
  - Shows suggested complementary exams (solicitações) and usual SUS dosages (prescrição)
- Accessibility: ARIA live regions, prefers-reduced-motion support
- Security: no innerHTML with untrusted data — use DOM APIs / textContent, escape everything
- Config: API base URL, consultation ID, professional token (JWT) — CNS of professional
- CNS validation in JS too (client-side sanity check)
- Polling with exponential backoff, visibility API to pause when tab hidden
- Event-driven integration: dispatches CustomEvent `copiloto:soap-suggestion` that the main telehealth app listens to, to fill SOAP fields
- i18n: pt-BR labels
- LGPD considerations: no logging of sensitive data (patient data), consent, minimal data

**Backend contract (Pydantic v2 schemas):**
- `CNS` validated type (Annotated with field_validator or custom type)
- `CPF` validated type
- `AlertaClinico` model: tipo (ALERGIA, RISCO, INTERACAO), severidade, descricao, cid10/ciap2 optional, substancia
- `SugestaoExame` model: exame, codigo_sus/SIGTAP maybe, justificativa, urgencia
- `SugestaoDosagem` model: medicamento, dosagem, via, frequencia, duracao, observacao (FTN reference)
- `SugestaoSOAP` model: subjetivo, objetivo, avaliacao (with cid10/ciap2), plano
- `CopilotoResponse`: paciente (cns, nome redacted?), alertas, sugestao_soap, exames, dosagens, gerado_em, versao_modelo

**SQLAlchemy 2.0 models:**
- `AlertaClinicoORM`, `SugestaoCopilotoORM` — with Mapped[...] typed mappings
- Maybe audit table `CopilotoAuditLog` for LGPD traceability

**FastAPI endpoint:**
- `GET /api/v1/teleatendimento/{consulta_id}/copiloto` returns CopilotoResponse
- `POST /api/v1/teleatendimento/{consulta_id}/copiloto/aplicar-soap` records that the doctor used the suggestion (audit)

**pytest tests:**
- Test CNS/CPF validators
- Test API endpoint with mocked service
- Test severity ordering, alert serialization
- Maybe JS tests? The guidelines say pytest — so Python tests. But I could also include a note about JS testing with Jest... The instruction says "cobertura de testes automatizados com pytest" — so pytest for the Python parts.

Given the deliverable is primarily the JS file, I should focus most effort there, but include the backend contract files to make it complete and testable. Let me structure the answer:

1. `backend/app/static/js/copiloto_sidebar.js` — the main widget (IIFE or ES module, no dependencies, vanilla JS)
2. `backend/app/static/css/copiloto_sidebar.css` — styles including blink animation (or embed styles via JS injection? Better separate CSS file, but the task only asks for JS. I can inject a <style> from JS to keep it self-contained — that's a common widget pattern. Actually, injecting styles from JS makes the widget self-contained, which is good for a widget. I'll do that with a guard.)
3. Backend: `backend/app/schemas/copiloto.py` (Pydantic v2), `backend/app/models/copiloto.py` (SQLAlchemy 2.0), `backend/app/api/v1/endpoints/copiloto.py` (FastAPI), maybe `backend/app/services/copiloto_service.py`
4. Tests: `backend/tests/test_copiloto.py` (pytest)

Let me be careful about the JS file quality — it's the core deliverable.

**JS Widget detailed design:**

```javascript
/**
 * MedIA — Copiloto Clínico (C22)
 * Painel lateral para tela de teleatendimento do médico (Home Office).
 * ...
 */
```

Features:
- `CopilotoSidebar` class with config: `{ apiBaseUrl, consultaId, token, profissionalCns, pollIntervalMs, locale }`
- CNS validation function (client-side, mirrors backend)
- Fetch with Authorization Bearer token, AbortController, timeout
- Real-time: try WebSocket first? Or SSE? To keep it dependency-free and robust, I'll implement polling with adaptive interval + optional SSE endpoint if configured. Let me implement polling with `setInterval` + visibility handling + exponential backoff on errors. Maybe support SSE via EventSource if `sseUrl` provided. I'll include both: prefer SSE, fallback to polling. Actually to keep code manageable, I'll do polling with backoff, and note SSE hook. Hmm, "em tempo real" — polling every N seconds is acceptable for a copilot; but let me add SSE support since it's cleaner for real-time. I'll implement: if `config.sseUrl` set → EventSource; else polling.

- Rendering:
  - Header: "Copiloto Clínico" + status indicator (conectado/atualizando/offline) + last update time
  - Alerts section: blinking for high severity (CSS class `copiloto-alerta--critico` with `animation: copiloto-piscar 1s steps(2) infinite`), respecting `prefers-reduced-motion` (then use static highlight instead)
  - SOAP suggestion card: preview of S/O/A/P truncated + button "Preencher SOAP com Sugestão da IA"
  - Exams section: list with urgency badges
  - Dosages section: medication cards with dosagem/via/frequência/duração + source "FTN/MS"
  - Footer: disclaimer "Sugestões geradas por IA. A decisão final é do profissional." + model version
- On button click: fetch full suggestion (or use loaded data), dispatch `CustomEvent('copiloto:soap-aplicar', { detail: { soap, consultaId } })` on `document`, and also call optional callback `onApplySoap`. Also POST audit endpoint `aplicar-soap` to register usage (LGPD/audit). The main app listens and fills the SOAP textareas.
- Security: build DOM via `createElement`/`textContent` only; sanitize; CSP-friendly (no inline handlers, no eval). Injected style tag is static content (safe).
- Accessibility: `role="log"`/`aria-live="polite"` for updates, `aria-live="assertive"` for critical alerts, focus management, buttons with aria-labels, contrast.
- LGPD: don't log patient identifiers to console; mask patient name (first name + initial) maybe; the widget displays minimal patient info.
- Error states: offline banner, retry button.
- Data contract mirrors Pydantic schemas (camelCase? No — keep snake_case to match Pydantic JSON; Pydantic by default serializes field names as-is; I'll use snake_case in JS parsing, or configure alias generator to camelCase in backend. Simpler: keep snake_case in both. I'll parse snake_case.)

Let me write the CNS validation algorithm:
CNS: 15 digits. Valid if starts with 1, 7, 8, 9 (provisional 7/8/9? Actually definitive cards start with 1 or 7 or 8 or 9; older ones 1 and 2? Let me recall: CNS definitive: starts with 1, 7, 8 or 9. CNS provisório: starts with 2? Hmm. Actually: Cartão Nacional de Saúde definitivo begins with 1, 7, 8 or 9. The provisórios begin with 2? Let me recall the standard validation:

CNS validation (15 digits):
- Must have 15 digits
- First digit must be 1, 7, 8, or 9 (some implementations accept 2 for provisório? The official algorithm: numbers starting with 1 or 7 or 8 or 9 are definitive; there are also temporary ones starting with 2? Actually the common algorithm found in many implementations: first digit in {1,7,8,9}. Some also accept {2}? Let me think — the classic algorithm:

```
if length != 15 -> invalid
if first char not in '1789' -> invalid (some versions allow 2? no)
soma = sum over i of digit[i] * (15 - i)
if soma % 11 == 0 -> valid
```

Yes, the standard: peso = 15 - posição (posição 1..15), sum must be divisible by 11. And first digit must be 1, 7, 8 or 9. I'll implement that. (Some implementations also accept starting with 2 for CNS provisório? I've seen "2" in some validators... The widely used JS validator: first digit must be 1, 7, 8, or 9. I'll go with that and mirror it in Pydantic.)

CPF validation: standard check digits.

Now the Pydantic schemas:

```python
from __future__ import annotations
import re
from datetime import datetime
from enum import Enum
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator
```

CNS type:
```python
CnsStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=15, max_length=15)]

class CNS(RootModel[str]) ... 
```
Better: use Annotated with a custom `AfterValidator`:

```python
def _validar_cns(v: str) -> str:
    ...
CNS = Annotated[CnsStr, AfterValidator(_validar_cns)]
```

Similarly CPF.

Enums:
```python
class TipoAlerta(str, Enum):
    ALERGIA_MEDICAMENTOSA = "ALERGIA_MEDICAMENTOSA"
    ALERGIA_ALIMENTAR = "ALERGIA_ALIMENTAR"
    RISCO_CARDIOVASCULAR = ...
    INTERACAO_MEDICAMENTOSA = ...
    GESTACAO_ALTO_RISCO = ...
    OUTRO = "OUTRO"

class Severidade(str, Enum):
    INFO = "INFO"; MODERADA = "MODERADA"; ALTA = "ALTA"; CRITICA = "CRITICA"
```

Models with `model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)`.

`AlertaClinico(BaseModel)`: id, tipo, severidade, titulo, descricao, substancia: str|None, cid10: optional pattern, ciap2: optional pattern (e.g., `[A-Z][0-9]{2}`), criado_em.

`SugestaoExame`: exame, codigo_sigtap: optional, justificativa, urgencia: ROTINA|PRIORITARIA|URGENTE.

`SugestaoDosagem`: medicamento, apresentacao, dosagem, via (enum: ORAL, IV, IM, TOPICA, INALATORIA, OFTALMOLOGICA, SUBLINGUAL, RETAL), frequencia, duracao, observacao, referencia (default "FTN/MS").

`SugestaoSOAP`: subjetivo, objetivo, avaliacao, cid10_sugerido, ciap2_sugerido, plano, confianca: float ge=0 le=1.

`CopilotoResponse`: consulta_id (UUID), paciente_cns: CNS, paciente_nome_reduzido, alertas: list, sugestao_soap: SugestaoSOAP|None, exames_sugeridos: list, dosagens_sugeridas: list, gerado_em: datetime, versao_modelo: str, disclaimer.

SQLAlchemy 2.0 models (typed):
```python
class Base(DeclarativeBase): pass

class AlertaClinicoORM(Base):
    __tablename__ = "copiloto_alertas"
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consulta_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teleatendimento_consultas.id"), index=True)
    ...
```
Hmm, referencing another table might not exist; I'll keep consulta_id as UUID column with index, no FK to avoid coupling, or FK to a consultas table — safer to keep generic. I'll use `mapped_column(Uuid, index=True)` (SQLAlchemy 2.0 has `Uuid` type cross-db). Use `sqlalchemy.Uuid`.

Tables:
- `copiloto_alertas` — alerts per consultation
- `copiloto_sugestoes` — AI suggestion JSON per consultation (store SOAP suggestion + exams + dosages as JSON columns? For SQLAlchemy 2.0 typed: `Mapped[dict[str, Any]] = mapped_column(JSONB)`) — but JSONB is postgres-specific; use `JSON` generic. I'll use `mapped_column(JSON)` with `default=dict`.
- `copiloto_auditoria` — audit of SOAP application: consulta_id, profissional_cns (CNS of doctor), timestamp, hash of suggestion applied, versao_modelo. LGPD audit trail.

Service: `CopilotoService` that reads alerts + latest suggestion, assembles response. For tests, mock the AI gateway.

Endpoint:
```python
router = APIRouter(prefix="/api/v1/teleatendimento", tags=["copiloto"])

@router.get("/{consulta_id}/copiloto", response_model=CopilotoResponse)
async def obter_copiloto(consulta_id: UUID, ..., service: CopilotoService = Depends(get_copiloto_service), _: ProfissionalToken = Depends(require_profissional)) -> CopilotoResponse: ...
```

Auth dependency: I'll define a simple `require_profissional` that validates JWT and returns `ProfissionalContext` (cns, cpf, uf, cbo). Keep it minimal but typed.

Tests (pytest):
- `test_validador_cns_aceita_numero_valido`, `test_validador_cns_rejeita_invalido`
- `test_validador_cpf`
- `test_severidade_ordem` maybe
- API tests with `TestClient` and dependency overrides: fake service returning a valid `CopilotoResponse`; assert JSON structure, alert ordering (CRITICA first), 401 without token, 404 for unknown consulta.
- Audit endpoint test: POST aplicar-soap returns 204/200 and records audit row (use in-memory SQLite with SQLAlchemy session).

For SQLite compatibility, use `sqlalchemy.Uuid` and `JSON` — fine.

Now, the JS file — let me write it thoroughly. I'll write it as an ES module? Or UMD-ish IIFE that auto-initializes from a global config? For a widget included in a Django/FastAPI-served page, an IIFE exposing `window.MedIACopiloto` with `init(config)` is practical, plus auto-init if `#copiloto-sidebar` exists and `window.MEDIA_CONFIG` present. I'll write an IIFE (no modules to avoid build step), strict mode, ES2017+ (async/await fine).

Key parts:

```javascript
(function (window, document) {
  'use strict';

  const VERSAO_WIDGET = '1.0.0';
  const EVENTO_APLICAR_SOAP = 'media:copiloto:aplicar-soap';
  const EVENTO_ALERTA_CRITICO = 'media:copiloto:alerta-critico';

  // ---------- Utilidades ----------
  const SEVERIDADE_ORDEM = { CRITICA: 0, ALTA: 1, MODERADA: 2, INFO: 3 };
  const URGENCIA_ORDEM = { URGENTE: 0, PRIORITARIA: 1, ROTINA: 2 };

  function validarCNS(cns) { ... }
  function normalizarDigitos(v) { return String(v ?? '').replace(/\D+/g, ''); }
  ...
```

CNS algorithm:
```javascript
function validarCNS(valor) {
  const cns = normalizarDigitos(valor);
  if (cns.length !== 15) return