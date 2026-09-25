The user wants me to create a FastAPI analytics module for a healthcare system (ClinicCare-inspired), specifically:

1. `backend/app/api/v1/analytics.py` with routes:
   - `GET /analytics/heatmap` - 7x24 matrix of demand density by weekday and hour
   - `GET /analytics/kpis` - no-show rate, average wait time, APS (Primary Health Care) resolutivity rate

Architecture guidelines:
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

I need to create:
1. The analytics API router (`backend/app/api/v1/analytics.py`)
2. Supporting schemas (Pydantic v2)
3. Possibly repository/service layer
4. Tests with pytest

Let me think about the domain model. In a SUS context:
- Appointments (agendamentos) with: patient (CNS/CPF), professional, UBS/Unidade, scheduled datetime, status (agendado, confirmado, atendido, faltou/no-show, cancelado), CIAP-2 codes for reason for visit, CID-10 for diagnosis
- SOAP method: Subjective, Objective, Assessment, Plan
- APS resolutivity: percentage of consultations resolved at primary care level without referral to specialized care

For the heatmap:
- 7 days × 24 hours matrix
- Count of appointments per (weekday, hour) slot
- Normalized density

For KPIs:
- No-show rate: faltas / (faltas + atendimentos) or faltas / total agendamentos
- Average wait time: could be time between scheduled and actual attendance, or time between arrival and consultation
- APS resolutivity: consultations resolved at APS / total consultations (no referral generated)

Let me design the code structure:

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── analytics.py
│   ├── schemas/
│   │   ├── analytics.py
│   ├── models/
│   │   ├── appointment.py (assumed to exist)
│   ├── services/
│   │   ├── analytics_service.py
├── tests/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── test_analytics.py
```

Since this is a task focused on creating the analytics module, I should:
1. Create the Pydantic schemas for analytics responses
2. Create the service layer with SQL queries (SQLAlchemy 2.0 style)
3. Create the API router
4. Create comprehensive tests

Let me write the code with strict typing.

First, the models (I'll assume they exist but define what's needed for reference — actually, to make the code self-contained and testable, I should define the Appointment model or at least reference it clearly). The task says "crie backend/app/api/v1/analytics.py" — the main deliverable. But for full test coverage, I need the supporting pieces. Let me create:

1. `backend/app/schemas/analytics.py` — Pydantic v2 schemas
2. `backend/app/services/analytics_service.py` — business logic
3. `backend/app/api/v1/analytics.py` — routes
4. `backend/tests/api/v1/test_analytics.py` — pytest tests

Let me think about the SQLAlchemy 2.0 style:
- Use `select()` statements
- Use `Mapped` and `mapped_column` for models
- Async or sync? FastAPI commonly uses async with SQLAlchemy 2.0. Let me use async for modern style. Actually, for testability and simplicity, I could go either way. Let me use async SQLAlchemy 2.0 with `AsyncSession` since that's the modern FastAPI pattern.

Hmm, but tests with async require pytest-asyncio. That's fine.

Let me design the data model assumptions:

```python
class AppointmentStatus(str, enum.Enum):
    AGENDADO = "agendado"
    CONFIRMADO = "confirmado"
    ATENDIDO = "atendido"
    FALTOU = "faltou"  # no-show
    CANCELADO = "cancelado"
    CANCELADO_PACIENTE = "cancelado_paciente"
```

Appointment model fields:
- id: UUID
- patient_id: FK
- professional_id: FK
- unit_id (UBS): FK
- scheduled_at: datetime (data/hora agendada)
- checked_in_at: datetime | None (chegada)
- started_at: datetime | None (início do atendimento)
- ended_at: datetime | None
- status: AppointmentStatus
- ciap2_code: str | None (motivo da consulta, CIAP-2)
- cid10_code: str | None (diagnóstico)
- referred_out: bool (encaminhado para atenção especializada)
- resolved_at_aps: bool (resolvido na APS)
- soap fields: subjective, objective, assessment, plan

For the heatmap:
- Query appointments grouped by `extract(dow from scheduled_at)` and `extract(hour from scheduled_at)`
- In PostgreSQL, `extract(dow)` returns 0=Sunday...6=Saturday. In Brazil/SUS context, we want Monday-first: ISO weekday (1=Monday...7=Sunday). Use `extract(isodow)` in PostgreSQL.
- Build 7x24 matrix with counts and density (normalized 0-1 or percentage)

For KPIs:
- No-show rate: count(status = FALTOU) / count(status in (ATENDIDO, FALTOU)) — typically no-show rate is calculated over appointments that should have happened (attended + no-show), excluding cancellations made in advance.
- Average wait time: average of (started_at - scheduled_at) for attended appointments, or (started_at - checked_in_at). Let me define: tempo médio de espera = média entre chegada (check-in) e início do atendimento; fallback to scheduled_at if no check-in. Actually in APS context, "tempo de espera" often means time between scheduled time and actual care start. Let me compute both but expose the main one: espera = started_at - checked_in_at (sala de espera) — hmm. Let me think about what's most standard.

In SUS evaluation literature, "tempo médio de espera" for scheduling often refers to time between request/scheduling and the appointment date (lead time). But in daily operations, it's waiting room time. I'll implement: average of (started_at - checked_in_at) for consultations with check-in, and document it. Or make it configurable via query param `wait_mode`? That might overcomplicate. Let me keep it simple and well-documented: tempo de espera = diferença entre horário agendado e início efetivo do atendimento (started_at - scheduled_at), which captures both delays. Actually, let me do the waiting-room definition (checked_in_at → started_at) as primary since that's "tempo de espera" in the classic sense, with fallback to scheduled_at when check-in is absent. Hmm, mixing definitions is messy.

Let me define clearly:
- `tempo_medio_espera_min`: média de (COALESCE(checked_in_at, scheduled_at) → started_at) em minutos, para atendimentos com status ATENDIDO.

That's defensible: if patient checked in, wait = start - check-in; if not recorded, wait = start - scheduled.

- Taxa de resolutividade na APS: atendimentos resolvidos na APS (sem encaminhamento) / atendimentos concluídos (ATENDIDO). Using `resolved_at_aps` boolean flag or `referred_out` flag. resolutividade = 1 - taxa de encaminhamento. I'll use: among attended appointments with a recorded outcome, proportion where `referred_out = False` (or `resolved_at_aps = True`).

Filters: period (start_date, end_date), unit (UBS), professional. CNS/CPF identification — for LGPD compliance, analytics should be aggregated and not expose patient identifiers. I should mention anonymization/aggregation. Maybe support optional filter by patient CNS hash? For analytics endpoints, typically only aggregate data. I'll add filters: `data_inicio`, `data_fim`, `unidade_id`, `profissional_id`. And enforce LGPD: minimum aggregation threshold (k-anonymity) — e.g., suppress cells with count < 3? That's a nice compliance touch for heatmap. Maybe add a `k_min` parameter for minimum cell suppression. That's a nice compliance feature. Let me include it with default 1 (no suppression) or default 3? For LGPD, small cells could identify individuals. I'll add `k_anon_minimo` param default 1 but allow setting; document it. Hmm, keep it simple: default 1, range 1-10.

Auth: endpoints should require authentication. I'll assume a `get_current_user` dependency exists. To keep tests self-contained, I'll define the dependency in the router with a fallback... No — better to import from `app.api.deps`. But since I'm creating files, I need to define deps too or make tests override them. In tests, I'll override the dependency with `app.dependency_overrides`. That's the standard pattern. So I'll import `get_current_user` from `app.api.deps` and override in tests. But then `app/api/deps.py` must exist... I can create a minimal version or assume it exists. Since the task says "crie backend/app/api/v1/analytics.py", the project presumably exists (ClinicCare-inspired). I'll write the code assuming standard project structure but provide the essential supporting files I create, and note assumptions.

To make the answer complete and runnable, I'll provide:
1. `backend/app/schemas/analytics.py` (new)
2. `backend/app/services/analytics_service.py` (new)
3. `backend/app/api/v1/analytics.py` (main deliverable)
4. `backend/tests/api/v1/test_analytics.py` (new)
5. Maybe a conftest.py for tests with in-memory SQLite (aiosqlite) fixtures.

For the models, I'll assume `app.models.appointment.Appointment` exists with the fields. But to make tests pass, I need the model defined. I could include a minimal `app/models/appointment.py` in the answer for completeness, noting it may already exist. Hmm, the task is focused; but "cobertura de testes automatizados" requires runnable tests. I'll include the model file as a reference implementation (marked as such) so tests run.

Actually, let me reconsider: to keep the answer focused but complete, I'll structure it as:

- Brief architecture overview
- File 1: `backend/app/models/appointment.py` (reference — assumed existing; included for testability)
- File 2: `backend/app/schemas/analytics.py`
- File 3: `backend/app/services/analytics_service.py`
- File 4: `backend/app/api/v1/analytics.py` (main)
- File 5: `backend/app/api/deps.py` (minimal, assumed existing)
- File 6: `backend/tests/conftest.py`
- File 7: `backend/tests/api/v1/test_analytics.py`
- Maybe `backend/app/main.py` minimal for tests

That's a lot of code but the task demands full test coverage. Let me write it carefully.

Let me now write the actual code.

### Models (SQLAlchemy 2.0, typed)

```python
# backend/app/models/appointment.py
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AppointmentStatus(str, enum.Enum):
    AGENDADO = "agendado"
    CONFIRMADO = "confirmado"
    ATENDIDO = "atendido"
    FALTOU = "faltou"
    CANCELADO = "cancelado"


class Appointment(Base):
    __tablename__ = "agendamentos"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ...
```

Wait — for tests with SQLite, PGUUID won't work. Use `sqlalchemy.Uuid` (generic, SQLAlchemy 2.0 has `Uuid` type that works across dialects). Yes, SQLAlchemy 2.0 has `sqlalchemy.Uuid`. Use that.

For cross-database compatibility in tests (SQLite), avoid PostgreSQL-specific functions like `isodow`. I can compute weekday/hour in Python after fetching, or use `func.extract` which works in both (SQLite supports `strftime`). `extract('isodow', ...)` doesn't work in SQLite. Options:
1. Fetch all rows in period and aggregate in Python (fine for moderate volumes, but not scalable).
2. Use SQL with dialect-specific handling.
3. Use `func.strftime('%w', ...)` for SQLite and `extract` for PG — dialect branching is ugly.

Better approach: do the grouping in SQL with `func.extract("hour", col)` (works in both SQLite and PG) and for weekday use... SQLite: `extract('dow')`? SQLite doesn't support EXTRACT at all natively; SQLAlchemy compiles `extract` to `strftime` for SQLite? Let me recall: SQLAlchemy's `extract()` on SQLite compiles to `CAST(STRFTIME('%H', ...) AS INTEGER)`? Actually, SQLAlchemy has a compiler for SQLite that translates `extract` to strftime calls for known fields: 'month' → '%m', 'day' → '%d', 'year' → '%Y', 'hour' → '%H', 'minute' → '%M', 'second' → '%S', 'dow' → '%w' (day of week 0-6, Sunday=0), 'doy' → '%j'. Yes! SQLAlchemy's SQLite dialect supports extract for dow via `%w`. So `func.extract('dow', col)` works on both PG (0=Sunday) and SQLite (%w, 0=Sunday). 

So I'll use `dow` (0=Sunday..6=Saturday) and convert to ISO weekday (1=Monday..7=Sunday) in Python: `iso = 7 if dow == 0 else dow`. And hour via `extract('hour', ...)`.

Alternatively, to be safe and simple, I could aggregate in Python. But SQL aggregation is more "production-grade". I'll use SQL with extract and handle mapping in Python. For tests with SQLite this works.

Hmm, but there's a subtlety: SQLAlchemy stores DateTime in SQLite as strings; strftime works on those. extract('hour') → `%H` works. extract('dow') → `%w` works. Good.

### Schemas (Pydantic v2)

```python
# backend/app/schemas/analytics.py
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, field_validator, model_validator


class DiaSemana(int, Enum):
    SEGUNDA = 1
    TERCA = 2
    ...
    DOMINGO = 7


class HeatmapCelula(BaseModel):
    dia_semana: DiaSemana  # 1=segunda ... 7=domingo (ISO-8601)
    hora: Annotated[int, Field(ge=0, le=23)]
    total: NonNegativeInt
    densidade: Annotated[float, Field(ge=0.0, le=1.0)]


class HeatmapResponse(BaseModel):
    periodo_inicio: date
    periodo_fim: date
    total_agendamentos: NonNegativeInt
    matriz: list[list[HeatmapCelula]]  # 7 linhas x 24 colunas
    horarios_pico: list[HeatmapCelula]
    ...
```

Hmm, matrix as 7x24 nested lists of cells, or as flat list? A 7x24 matrix of objects is verbose but explicit. Alternative: `matriz: list[list[CellDTO]]` where each cell has `total` and `densidade`. 168 cells. Fine.

Or matrix of numbers (density) plus separate counts. Let me do: `matriz: list[list[CelulaHeatmap]]` with 7 rows (Monday..Sunday) × 24 columns (0..23h). Each cell: `dia_semana`, `hora`, `total`, `densidade`. Plus `horarios_pico`: top N cells.

KPIs schema:

```python
class KpisResponse(BaseModel):
    periodo_inicio: date
    periodo_fim: date
    total_agendamentos: int
    taxa_absenteismo: float  # 0-1 or percentage
    tempo_medio_espera_minutos: float | None
    taxa_resolutividade_aps: float
    # breakdown
    atendimentos: int
    faltas: int
    cancelamentos: int
    encaminhamentos: int
```

Percent vs fraction: I'll use percentage 0-100 with ge=0 le=100, and document. Or fraction 0-1. Percentages are more readable for SUS managers. Let me use percentage with 2 decimal rounding.

Also add per-unit or per-professional breakdown? Keep it focused. Maybe `kpis` supports optional grouping by unit? The task says just the three KPIs. Keep it clean but add breakdown counts for transparency.

### Service layer

```python
# backend/app/services/analytics_service.py
```

Functions:
- `get_heatmap(session, filtros) -> HeatmapOut`
- `get_kpis(session, filtros) -> KpisOut`

Using SQLAlchemy 2.0 `select` with `func.count`, `func.extract`, group by.

For heatmap:
```python
stmt = (
    select(
        func.extract("dow", Appointment.scheduled_at).label("dow"),
        func.extract("hour", Appointment.scheduled_at).label("hora"),
        func.count().label("total"),
    )
    .where(...)
    .group_by("dow", "hora")
)
```

Note: exclude CANCELADO from heatmap? Demand density should reflect demand — cancelled appointments are still demand signals but typically heatmap of "agendamentos" includes all scheduled; but cancellations inflate. I'll include all statuses by default but allow `incluir_cancelados: bool = False` filter — default excludes cancelled. Hmm, keep simpler: count all non-cancelled appointments (agendado, confirmado, atendido, faltou) as demand. Document it.

For KPIs:
```python
# counts by status
stmt = select(Appointment.status, func.count()).group_by(Appointment.status).where(...)
```

Wait time:
```python
espera_expr