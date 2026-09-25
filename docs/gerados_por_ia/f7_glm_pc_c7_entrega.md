The user wants me to create a FastAPI analytics module for a healthcare system (ClinicCare-inspired), specifically:

1. `backend/app/api/v1/analytics.py` with routes:
   - `GET /analytics/heatmap` - 7x24 matrix of demand density by weekday and hour
   - `GET /analytics/kpis` - no-show rate, average wait time, APS resolutivity rate

Architecture guidelines:
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- LGPD compliance (Brazilian data protection law - "conformidade total" likely refers to LGPD given SUS context)
- Automated test coverage with pytest

Let me design this properly:

**Domain model assumptions** (I need to define the SQLAlchemy models since this is a new module, but I should assume existing models or create them):

Given it's a clinic system (ClinicCare), typical entities:
- `Patient` (Paciente): id, cns, cpf, name, birth_date, etc.
- `Appointment` (Agendamento/Consulta): id, patient_id, professional_id, scheduled_at (datetime), started_at, ended_at, status (agendada, confirmada, realizada, faltou/no-show, cancelada), created_at
- `Encounter` (Atendimento): SOAP notes, CIAP-2 codes, CID-10

For the heatmap: aggregate appointments by weekday (0-6) and hour (0-23), counting scheduled appointments (demand density).

For KPIs:
- No-show rate: appointments with status "faltou" / total appointments that should have occurred (realizadas + faltou)
- Average wait time: average of (started_at - scheduled_at) in minutes for realized appointments
- APS resolutivity rate: percentage of encounters resolved at primary care without referral (no referral to specialty/hospital). This could be modeled as encounters where `encaminhamento` is False or `resolvido_na_aps` flag, or based on CIAP-2 codes without referral.

Let me structure the code:

```
backend/app/
├── api/v1/
│   ├── __init__.py
│   ├── analytics.py
│   └── deps.py (assumed existing - get_db, auth)
├── models/
│   ├── __init__.py
│   ├── patient.py
│   ├── appointment.py
│   └── encounter.py
├── schemas/
│   ├── analytics.py
├── services/
│   └── analytics_service.py
└── core/
    ├── security.py (auth deps)
```

Since the task says "crie backend/app/api/v1/analytics.py", the main deliverable is that file, but to make it complete and testable, I should provide:
1. The analytics router file
2. Pydantic schemas (schemas/analytics.py)
3. Service layer (services/analytics_service.py) - good separation
4. SQLAlchemy models needed (or assume they exist - I'll define them to be self-contained but note they may already exist)
5. Tests with pytest

Let me think about LGPD compliance:
- No PII in responses (aggregated data only)
- Minimum aggregation threshold (k-anonymity): suppress cells with < 3 patients to prevent re-identification
- Audit logging
- CNS/CPF never exposed in analytics responses

Let me write the code:

**Models** (SQLAlchemy 2.0 style with Mapped, mapped_column):

```python
# backend/app/models/appointment.py
import enum
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Enum, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class AppointmentStatus(str, enum.Enum):
    AGENDADA = "agendada"
    CONFIRMADA = "confirmada"
    REALIZADA = "realizada"
    FALTOU = "faltou"  # no-show
    CANCELADA = "cancelada"

class Appointment(Base):
    __tablename__ = "appointments"
    
    id: Mapped[uuid.UUID] = mapped_column(...)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"))
    professional_id: Mapped[uuid.UUID]
    unit_id (UBS - unidade básica de saúde)
    scheduled_at: Mapped[datetime]
    started_at: Mapped[datetime | None]
    ended_at: Mapped[datetime | None]
    status: Mapped[AppointmentStatus]
    created_at
```

**Encounter** for resolutivity:
```python
class Encounter(Base):
    __tablename__ = "encounters"
    id
    appointment_id
    patient_id
    professional_id
    ciap2_code: Mapped[str | None]  # CIAP-2 (3 chars, e.g., "A01")
    cid10_code: Mapped[str | None]
    subjective, objective, assessment, plan (SOAP)
    referred_out: Mapped[bool]  # encaminhamento para fora da APS
    resolved_at_aps: Mapped[bool]  # resolutividade
```

Actually for resolutivity, the standard measure in APS is: proportion of encounters that did NOT result in referral to another level of care (contra-referência/encaminhamento). So `resolutividade = atendimentos sem encaminhamento / total de atendimentos`.

**Schemas** (Pydantic v2):

```python
class HeatmapCell(BaseModel):
    weekday: int  # 0=Monday (ISO) or 0=Sunday? Let's use ISO: 1=Monday..7=Sunday
    hour: int  # 0-23
    demand: int  # count of appointments
    patient_count: int  # distinct patients (k-anonymity)
    density: float  # normalized 0-1

class HeatmapResponse(BaseModel):
    matrix: list[list[HeatmapCell]]  # 7x24
    total_demand: int
    peak: HeatmapCell | None
    period: DateRange

class KPIResponse(BaseModel):
    no_show_rate: float
    avg_wait_minutes: float
    aps_resolutivity_rate: float
    sample sizes, confidence, period
```

**Service layer** with SQL aggregation:

Heatmap query:
```sql
SELECT EXTRACT(ISODOW FROM scheduled_at) as weekday,
       EXTRACT(HOUR FROM scheduled_at) as hour,
       COUNT(*) as demand,
       COUNT(DISTINCT patient_id) as patients
FROM appointments
WHERE scheduled_at BETWEEN :start AND :end
  AND status != 'cancelada'
GROUP BY 1, 2
```

But to be DB-agnostic and testable with SQLite, I could use `func.extract` which works in SQLite too. Actually `EXTRACT(ISODOW ...)` doesn't work in SQLite. SQLite has `strftime('%w', ...)` for weekday (0=Sunday). Hmm.

For portability, I could compute in Python after fetching minimal rows, or use `func.extract('dow', ...)` which works in PostgreSQL. For tests with SQLite, `extract` on datetime columns... SQLite doesn't support EXTRACT. 

Options:
1. Use PostgreSQL-specific SQL and test with PostgreSQL (testcontainers) — heavier.
2. Fetch rows (scheduled_at, patient_id) for period and aggregate in Python — simple, portable, fine for reasonable data volumes; can note optimization path.
3. Use dialect-agnostic expressions.

Given "cobertura de testes automatizados com pytest", option 2 (Python aggregation) is most portable and testable. But for production scale, SQL aggregation is better. I can do a hybrid: use SQL aggregation with `func.extract` for PostgreSQL, but that breaks SQLite tests.

Alternative: SQLAlchemy 2.0 with `func.strftime` is SQLite-only. Let me just do Python-side aggregation over a lean query selecting only needed columns. For a clinic (thousands of appointments per month), this is fine. I'll add a comment noting the SQL-aggregation optimization path. Actually, let me reconsider — a cleaner approach that's still portable: query with `select(Appointment.scheduled_at, Appointment.patient_id)` filtered by period and status, then aggregate in Python with `statistics`/dict. That's clean and testable.

Hmm, but a "senior" implementation would push aggregation to the DB. Let me think about what's best for the answer quality. The task emphasizes strict typing, Pydantic v2, SQLAlchemy 2.0, pytest coverage. Python-side aggregation over a filtered, column-projected query is defensible and keeps tests simple with SQLite (via aiosqlite or sync sqlite). I'll do Python-side aggregation but structure the service so it's clean.

Actually, I can do DB-side aggregation in a portable way using SQLAlchemy expressions that compile per-dialect... There isn't a built-in portable "isodow". I'll go with Python aggregation. For KPIs, I can do DB-side aggregation with `func.count`, `func.avg`, `case` — those are portable! 

KPI queries:
- No-show: `COUNT(*) FILTER` is PG-specific; use `func.sum(case((Appointment.status == FALTOU, 1), else_=0))` — portable.
- Avg wait: `func.avg(func.julianday(...))` is SQLite; `EXTRACT(EPOCH FROM (started_at - scheduled_at))/60` is PG. Not portable. So compute wait in Python from selected rows, or store `wait_minutes` column. Hmm.

Simplest portable: select (scheduled_at, started_at) for realized appointments in period, compute in Python. Fine.

Actually, let me reconsider: maybe define the models with a computed `wait_minutes` column? No, that's denormalization. Python-side is fine.

Decision: Service layer does:
1. Heatmap: query projected columns (scheduled_at, patient_id) → aggregate in Python.
2. KPIs: 
   - Query counts via SQL aggregate (portable `case`/`func.count`) for no-show.
   - Query (scheduled_at, started_at) pairs for wait time → Python.
   - Query counts for resolutivity via SQL aggregate on Encounter.referred_out.

Or just do everything in Python from projected rows. Cleaner to read. But showing SQL aggregation skills is nice. I'll mix: use SQL for counts (portable), Python for time math.

Hmm, actually for simplicity and consistency, let me do a single service with clear methods, each doing its own query. Let me write it.

**Auth/RBAC**: Analytics endpoints should require authenticated professional with role like "gestor"/"admin"/"coordenacao" (telemetry is sensitive aggregated data). I'll assume a `deps.py` with `get_current_user` / `require_roles`. I'll create a minimal `deps.py` in the answer or assume it exists. To make the answer self-contained but not bloated, I'll include a small `api/v1/deps.py` with `get_db` and `CurrentUser` dependency, noting it may already exist in the project.

**LGPD compliance**:
- Aggregated-only responses; k-anonymity threshold (min 3 distinct patients per cell) — cells below threshold are suppressed (demand shown as 0 or flagged `suppressed=True`).
- No PII (no CNS/CPF in responses).
- Audit log entry on access (I can add a simple audit hook or comment). I'll include an audit dependency that logs access without PII.
- Period limits (max 365 days) to limit re-identification risk over tiny windows? Actually small windows increase identifiability; enforce minimum? Typically you restrict max range and enforce k-anonymity. I'll enforce max 366 days and default last 90 days.

**Date handling**: Query params `start_date`, `end_date` (ISO dates), `unit_id` optional filter (UBS), `professional_id` optional. Validate end >= start.

**Weekday convention**: ISO 8601: 1=Monday ... 7=Sunday. I'll use that and document it. Matrix indexed [weekday-1][hour].

**Density normalization**: density = demand / max_demand in matrix (0..1), rounded.

**KPI definitions** (document in docstrings):
- Taxa de absenteísmo (no-show): faltou / (realizadas + faltou) — cancellations excluded. Also could include "absenteísmo" broadly as faltou+canceladas_sem_aviso; keep it simple: no_show = FALTOU / (REALIZADA + FALTOU).
- Tempo médio de espera: mean(started_at - scheduled_at) in minutes for REALIZADA with both timestamps; only non-negative waits; maybe cap outliers? Keep simple, report count of samples.
- Resolutividade na APS: encounters without referral (encaminhado_fora=False) / total encounters in period. Use `referred_out` boolean. Also could count `ciap2_code` presence. Keep: resolutividade = 1 - referral_rate.

Response includes sample sizes (n) and period, plus `generated_at`.

**Pydantic v2 strict typing**: use `model_config = ConfigDict(frozen=True)`, `Field(ge=..., le=...)`, `Decimal` or float with rounding. Use `float` rounded to 4 decimals or percentages 0-100. I'll use ratios 0..1 with 4 decimals? For SUS dashboards, percentages are common. I'll return both? Keep ratio 0..1 and `percentage` fields maybe. I'll return floats 0..1 rounded, and document.

**Router**:

```python
router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(..., db: Session = Depends(get_db), user = Depends(require_roles("admin","gestor","coordenador"))) -> HeatmapResponse:
    ...
```

Sync or async? SQLAlchemy 2.0 — could be sync with `Session` or async with `AsyncSession`. FastAPI commonly async. For tests simplicity, sync Session is easier with SQLite. But modern stack: async. Hmm. I'll go sync (`Session`) for portability and simplicity of tests — many production codebases use sync SQLAlchemy with FastAPI. Actually with Python 3.12 + SQLAlchemy 2.0, async is trendy. But sync keeps the answer tighter and tests simpler. I'll use sync sessions and note it. Actually, let me use async? The DB layer choice affects deps and tests. Sync is safer for correctness in an answer. I'll go sync.

**Tests** (pytest):
- fixtures: in-memory SQLite engine, create tables, session, override get_db, seed data, TestClient.
- Tests:
  - heatmap returns 7x24 matrix, correct counts for seeded data, peak detection, suppression below k threshold, date validation errors (422), auth required (401/403).
  - kpis: no-show rate correct, wait time correct, resolutivity correct, empty period → zeros/None handling.
  - LGPD: no PII fields in response.

Let me now write all files.

File structure I'll deliver:

1. `backend/app/models/appointment.py` — Appointment + AppointmentStatus (assuming patients model exists; I'll include minimal Patient model too for tests)
2. `backend/app/models/encounter.py` — Encounter (SOAP, CIAP-2, CID-10)
3. `backend/app/schemas/analytics.py` — Pydantic v2 schemas
4. `backend/app/services/analytics_service.py` — business logic
5. `backend/app/api/v1/analytics.py` — the router (main deliverable)
6. `backend/app/api/v1/deps.py` — get_db + auth deps (minimal, noted as possibly existing)
7. `backend/tests/test_analytics.py` — pytest suite
8. Maybe `backend/app/core/audit.py` — small audit logger. Could fold into deps. I'll include a lightweight audit function inside deps or a small module.

Let me be careful about length — this is a code-heavy task, so a long answer is appropriate, but I should keep prose minimal and code focused. Use headers per file path, code blocks. The user speaks Portuguese — I should respond in Portuguese! The task is in Portuguese. Yes, respond in Portuguese (code comments/docstrings in Portuguese too, which fits SUS context).

Now let me write the actual code carefully.

### Models

```python
# backend/app/models/appointment.py
"""Modelo de Agendamento (Consulta) — padrão SUS/APS."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AppointmentStatus(str, enum.Enum):
    AGENDADA = "agendada"
    CONFIRMADA = "confirmada"
    REALIZADA = "realizada"
    FALTOU = "faltou"          # no-show / absenteísmo
    CANCELADA_PACIENTE = "cancelada_paciente"
    CANCELADA_UNIDADE = "cancelada_unidade"
```

UUID type portability: `UUID(as_uuid=True)` from postgresql dialect doesn't work on SQLite. For tests with SQLite, use `Char(36)` storage or SQLAlchemy's `Uuid` type (SQLAlchemy 2.0 has `sqlalchemy.Uuid` portable type!). Yes — SQLAlchemy 2.0 added `sqlalchemy.Uuid` generic type that works across backends. Use `Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)`. 

```python
from sqlalchemy import Uuid
```

Actually `sqlalchemy.Uuid` exists in 2.0. Good.

```python
class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_scheduled", "scheduled_at"),
        Index("ix_appointments_unit_scheduled", "unit_id", "scheduled_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    professional_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    unit_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)  # UBS/ESF
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, native_enum=False, length=32), nullable=False, default=Appointment