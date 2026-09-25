The user wants me to create a FastAPI analytics module for a healthcare system (inspired by ClinicCare), with:

1. `backend/app/api/v1/analytics.py` containing:
   - `GET /analytics/heatmap` - 7x24 matrix of demand density by weekday and hour
   - `GET /analytics/kpis` - no-show rate, average wait time, resolutivity rate in Primary Health Care (APS)

Requirements:
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

I need to create:
1. The analytics API router
2. Pydantic schemas for responses
3. SQLAlchemy queries (2.0 style)
4. Tests with pytest

Let me think about the domain model. Since this is inspired by ClinicCare (a Brazilian health system), I'll assume there are existing models like:
- `Appointment` (Agendamento/Consulta) with fields like: scheduled_at (datetime), status (agendada, confirmada, realizada, faltou/no-show, cancelada), patient_id, professional_id, etc.
- `Encounter` (Atendimento) with SOAP notes, CIAP-2 codes, CID-10
- `Patient` with CNS/CPF

Since I'm creating the analytics module, I should probably also define or reference the models. To be safe and self-contained, I'll create:
- The analytics router with service layer
- Schemas in `backend/app/schemas/analytics.py`
- Service in `backend/app/services/analytics_service.py` (or keep queries in the router with a service layer)
- Tests in `backend/tests/test_analytics.py`

Let me design carefully:

**Heatmap endpoint:**
- Query: appointments grouped by weekday (0-6, ISO) and hour (0-23)
- Response: 7x24 matrix with counts, plus metadata (total, peak day/hour)
- Filters: date range (start_date, end_date), professional_id, unit_id (UBS/unidade de saúde), status filter maybe
- Should count scheduled demand (agendamentos) — density of demand

**KPIs endpoint:**
- Taxa de absenteísmo (no-show rate): faltou / (realizadas + faltou) — typically no-show / total scheduled excluding cancellations
- Tempo médio de espera: average difference between scheduled_at and started_at (or checked_in_at) for completed appointments
- Taxa de resolutividade na APS: proportion of encounters resolved at primary care without referral (encounter without encaminhamento/referência) — e.g., encounters with CIAP-2 resolved vs total; commonly: (consultas resolvidas / total de consultas). We can compute: encounters where `outcome == 'resolvido'` or no referral created.

Let me define the models I'll reference. Since the task says "crie backend/app/api/v1/analytics.py", the main deliverable is that file, but for it to work and be testable, I need supporting files. I'll create a complete, coherent set:

1. `backend/app/models/appointment.py` — SQLAlchemy 2.0 models (Appointment, Encounter) — but wait, maybe these already exist in the project. The instruction says "Inspirado no ClinicCare" — ClinicCare is presumably an existing codebase. Since I don't have it, I'll create the models as part of the solution but note they may be adapted. Actually, to be safe, I'll create a self-contained module with models, schemas, service, router, and tests. I'll structure it well.

Let me write:

```
backend/app/
├── api/v1/analytics.py
├── schemas/analytics.py
├── services/analytics_service.py
├── models/appointment.py (referenced)
└── tests/test_analytics.py
```

Actually, let me think about what's most useful: The user asked specifically for the analytics.py file with the routes. But "cobertura de testes automatizados com pytest" means I need tests. And "tipagem estrita com Pydantic v2 e SQLAlchemy 2.0" means I need schemas and models. I'll deliver a complete vertical slice.

Let me design the models (SQLAlchemy 2.0 with Mapped/mapped_column):

```python
class AppointmentStatus(str, enum.Enum):
    AGENDADA = "agendada"
    CONFIRMADA = "confirmada"
    REALIZADA = "realizada"
    FALTOU = "faltou"          # no-show
    CANCELADA_PACIENTE = "cancelada_paciente"
    CANCELADA_SERVICO = "cancelada_servico"
```

Appointment:
- id: UUID
- patient_id: FK
- professional_id: FK
- unit_id (unidade de saúde / UBS)
- scheduled_at: datetime (timezone-aware)
- started_at: datetime | None (when consultation actually started — for wait time)
- finished_at: datetime | None
- status: enum
- created_at, updated_at

Encounter (Atendimento — SOAP):
- id
- appointment_id: FK
- patient_id
- professional_id
- subjective, objective, assessment, plan (SOAP)
- ciap2_code: str(3) — CIAP-2 codes are 3 chars (letter + 2 digits)
- cid10_code: str(4) — CID-10 like "A90" or "J45.0"
- outcome: enum — RESOLVIDO (resolvido na APS), ENCAMINHADO (referenciado), RETORNO_AGENDADO, etc.
- created_at

Patient:
- id, cns (CNS validated), cpf, name, birth_date

For CNS/CPF identification — I should include validators for CNS (15 digits with checksum) and CPF (11 digits with checksum). That's part of "conformidade" — SUS standards. I can include a `schemas/health_identifiers.py` with CNS/CPF validation using Pydantic v2 `field_validator` or Annotated types. The heatmap/KPIs endpoints don't strictly need CNS, but the guidelines mention identification by CNS/CPF, so I'll include the validators in the models/schemas where patients are referenced, and maybe allow filtering KPIs by patient CNS? Hmm, that could be a nice touch: KPIs per patient? Actually KPIs are population-level. But I could add optional `patient_cns` filter to show individual metrics. Let me keep it focused: filters by unit, professional, date range. But I'll include CNS/CPF validation utilities since guidelines demand SUS compliance — used in Patient model and maybe in a small endpoint? No — stick to the two endpoints requested. I'll include the identifier validators in the models file (Patient) and a dedicated validators module used by tests.

Actually, let me reconsider scope. The task: "crie backend/app/api/v1/analytics.py contendo rotas FastAPI de telemetria clínica: GET /analytics/heatmap ... GET /analytics/kpis". So the core deliverable is analytics.py. To make it complete and testable I'll provide:

1. `backend/app/core/validators.py` — CNS/CPF validators (SUS compliance)
2. `backend/app/models/` — appointment.py, encounter.py, patient.py (SQLAlchemy 2.0)
3. `backend/app/schemas/analytics.py` — Pydantic v2 strict schemas
4. `backend/app/services/analytics_service.py` — query logic
5. `backend/app/api/v1/analytics.py` — router
6. `backend/app/api/v1/router.py` — aggregator (maybe skip)
7. `backend/tests/conftest.py` — fixtures with SQLite in-memory (or better, use real engine; SQLite for tests is fine, but datetime with timezone... SQLite stores naive datetimes; I'll handle carefully)
8. `backend/tests/test_analytics.py` — comprehensive tests

Let me think about the heatmap computation:

```sql
SELECT 
  EXTRACT(ISODOW FROM scheduled_at) as weekday,  -- 1=Monday..7=Sunday
  EXTRACT(HOUR FROM scheduled_at) as hour,
  COUNT(*) as total
FROM appointments
WHERE scheduled_at BETWEEN :start AND :end
  AND status NOT IN ('cancelada_paciente', 'cancelada_servico')  -- demand = effective demand
GROUP BY weekday, hour
```

But for portability (SQLite tests), I'd rather do the grouping in Python after fetching rows, or use `func.extract` which works in SQLite for ISO weekday? SQLite's strftime('%w') gives 0=Sunday. To keep it DB-agnostic and testable, I'll fetch appointments in the window and aggregate in Python. For production scale that's not ideal, but for clarity and testability it's acceptable; alternatively I can write a dialect-aware SQL. Hmm. Let me think: SQLAlchemy 2.0 with `func.extract('isodow', ...)` works on PostgreSQL; SQLite doesn't support isodow. Since tests will likely run on SQLite (common practice), I'll aggregate in Python from a lightweight column fetch (only scheduled_at and status). That's clean and deterministic. I'll note in docstring that for large volumes one can push down to SQL with dialect functions; but keep Python aggregation for portability. Actually, a middle ground: use SQL aggregation with `func.strftime` fallback... too complex. Python aggregation it is — but I'll select only needed columns via `select(Appointment.scheduled_at, Appointment.status)` for efficiency.

Wait — but for KPIs, wait time needs started_at - scheduled_at. Also Python-side or SQL-side. Python-side is fine.

Heatmap response schema:

```python
class HeatmapCell(BaseModel):
    weekday: int  # 1..7 (ISO, segunda=1)
    hour: int     # 0..23
    total: int
    density: float  # normalized 0..1 relative to max cell

class HeatmapResponse(BaseModel):
    period_start: date
    period_end: date
    cells: list[HeatmapCell]  # 168 cells (7x24), always complete matrix
    total_appointments: int
    peak: HeatmapCell | None
    generated_at: datetime
```

Always return full 168 cells (zeros included) — that's a proper matrix for heatmap rendering.

KPIs response:

```python
class KpiValue(BaseModel):
    # maybe generic
class KpisResponse(BaseModel):
    period_start: date
    period_end: date
    no_show_rate: float | None       # 0..1
    no_show_total: int
    eligible_total: int              # realizadas + faltou
    avg_wait_minutes: float | None
    wait_sample_size: int
    resolutivity_rate: float | None
    resolved_total: int
    encounter_total: int
    generated_at: datetime
```

No-show rate definition (SUS/e-SUS AB style): absenteísmo = faltas / (consultas realizadas + faltas). Cancellations excluded. I'll document that.

Wait time: média de (started_at - scheduled_at) em minutos, para consultas realizadas com started_at preenchido. Could also use check-in time; I'll use started_at and document.

Resolutividade na APS: proporção de atendimentos com desfecho "resolvido na APS" (sem necessidade de encaminhamento) sobre o total de atendimentos com desfecho registrado. I'll define EncounterOutcome enum: RESOLVIDO_NA_APS, ENCAMINHADO_REDE, RETORNO_PROGRAMADO, OBITO(?), etc. Keep: RESOLVIDO_NA_APS = "resolvido_na_aps", ENCAMINHADO = "encaminhado", RETORNO = "retorno_programado", EVASAO? Keep simple: three outcomes + maybe "outro". Resolutivity = resolved / total with outcome recorded.

Filters for both endpoints:
- `start_date`, `end_date` (date, default last 30 days)
- `unit_id` (UUID | None) — unidade de saúde (UBS)
- `professional_id` (UUID | None)
- For heatmap maybe `include_cancelled: bool = False`

Validation: end_date >= start_date, max range (e.g., 366 days) to prevent abuse.

Auth: The task doesn't mention auth explicitly, but "conformidade total" for health data suggests at least role-based dependency. ClinicCare-inspired... I'll add a dependency stub `get_current_user` requiring an authenticated professional with role in (ADMIN, GESTOR, PROFISSIONAL) — but that adds complexity to tests. Hmm. I could include a simple dependency that's overridable in tests. Let me include a lightweight auth dependency in the router via `Depends(require_roles(...))` but define it in a way tests can override with `app.dependency_overrides`. That demonstrates LGPD-aware access control. I'll create `backend/app/api/deps.py` with `get_current_user` returning a `CurrentUser` pydantic model, and the analytics router requiring roles. In tests, override it. That's realistic and shows compliance (LGPD: minimum necessary access).

Actually, to keep the answer focused but complete, I'll include deps.py with a simple token-less stub? No — better: define `require_any_role` factory that depends on `get_current_user`, and in tests override `get_current_user`. The real `get_current_user` would decode JWT — I'll implement a minimal JWT-based one? That's scope creep. I'll implement `get_current_user` as a dependency that decodes a bearer token using `jose`/`jwt`... The task is about analytics, not auth. I'll make `get_current_user` raise 401 unless overridden, with a comment that it's wired to the project's auth module; tests override it. Hmm, but then the module isn't self-sufficient. Alternative: skip auth entirely and note it. The guidelines say "Manter conformidade total" — LGPD compliance for health telemetry implies access control. I'll include a minimal, functional bearer-token dependency using `itsdangerous`? No.

Decision: include `backend/app/api/deps.py` with:
- `CurrentUser` schema (id, role, unit_id)
- `get_current_user` — decodes JWT via `python-jose`? To avoid extra deps, I can implement HMAC-signed token verification with `hmac`/`hashlib` stdlib... overkill.

Simplest compliant approach: `get_current_user` reads `Authorization: Bearer <token>` and validates via the project's `security.decode_token` — I'll write a tiny `security.py` using stdlib `hmac` + `json` + `base64` (a JWT-like HS256 implementation in ~30 lines, no deps). Actually implementing HS256 JWT with stdlib is easy: header.payload.signature with base64url and hmac-sha256. That's ~40 lines and fully functional. That shows craftsmanship and keeps zero extra dependencies beyond fastapi/pydantic/sqlalchemy/pytest/httpx. I think that's a nice touch but adds length. The answer is already going to be long. Let me weigh: The user asked for analytics routes with tests. Auth is secondary. I'll include a compact `deps.py` with JWT HS256 verification using stdlib (compact), or... 

Alternative: Use FastAPI's `Security` with an API key header? For a clinical telemetry API, role-based is better.

Let me just do a compact stdlib JWT verifier in `app/core/security.py` (~35 lines) and `deps.py` with `get_current_user` + `require_roles`. Tests will create real tokens by signing with the same secret — that also tests auth integration. Good.

Hmm, actually, let me reconsider the overall length budget. This is a "coder agent" task; the user expects production-quality code. A complete vertical slice with tests will be long (maybe 700-900 lines total). That's acceptable for this kind of request. I'll organize the answer with file headers and concise explanations.

Let me now write the code carefully.

### File: backend/app/core/validators.py (SUS identifiers)

CNS validation: 15 digits. Algorithm for CNS starting with 1, 2, 7, 8, 9:
- Must be 15 digits, all numeric.
- If starts with 1,2: use mod 11 with weights 15,14,...,2 (peso de 15 a 2), sum = Σ digit*weight; rest = sum % 11; dv = 11 - rest; if dv == 11 → dv = 0; if dv == 10 → invalid (or format: when dv=10, sum is adjusted... actually the classic algorithm: if rest == 0 → valid? Let me recall precisely.

Classic CNS validation:
```
pesos = [15,14,13,12,11,10,9,8,7,6,5,4,3,2]
soma = Σ cns[i] * pesos[i] for i in 0..13
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0
if dv == 10: invalid (some implementations: soma += 2 and recompute? No—)
```
Hmm, the well-known algorithm: For CNS (15 digits) starting with 1, 2, 7, 8 or 9:
```
soma = 0
for i in range(15): soma += int(cns[i]) * (15 - i)
resto = soma % 11
if resto != 0: return False
```
Wait, there are two variants. Let me recall the canonical one from fNIRS/gov implementations:

The common Python implementation:
```python
def valida_cns(cns):
    cns = ''.join(filter(str.isdigit, cns))
    if len(cns) != 15: return False
    if re.match(r'[1-9]', cns[0]) is None: ... 
```
Actually valid CNS first char: 1, 2, 7, 8, 9 (7,8,9 for provisórios). The checksum: 
```
peso = 15
soma = 0
for i in range(15):
    soma += int(cns[i]) * peso
    peso -= 1
resto = soma % 11
dv = 11 - resto
valid = (dv == 11 and int(cns[14]) == 0) or (dv != 10 and int(cns[14]) == dv) ... 
```
Hmm no. Let me get it right. The standard algorithm (from Cartão Nacional de Saúde documentation):

For CNS with first digit 1 or 2 (definitive):
- Take first 14 digits, multiply by weights 15 down to 2.
- soma = Σ
- resto = soma % 11