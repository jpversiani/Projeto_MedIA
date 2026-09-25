The user wants me to create a FastAPI analytics module for a healthcare system (ClinicCare-inspired, SUS/APS Brazilian public health system context). Let me analyze the requirements:

1. **File to create**: `backend/app/api/v1/analytics.py`
2. **Routes needed**:
   - `GET /analytics/heatmap` - 7x24 matrix of demand density by weekday and hour
   - `GET /analytics/kpis` - no-show rate, average wait time, APS resolutivity rate

3. **Architecture guidelines**:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Since this is a coder agent task, I should deliver:
1. The main analytics API file
2. Supporting schemas (Pydantic v2)
3. Possibly repository/service layer
4. Tests with pytest
5. Maybe models if needed

Let me think about the domain:

**SUS/APS context (Atenção Primária à Saúde)**:
- APS = Atenção Primária à Saúde (Primary Health Care in Brazil)
- CIAP-2 = Classificação Internacional de Atenção Primária (reason for encounter, diagnoses in primary care)
- CID-10 = ICD-10
- SOAP = Subjective, Objective, Assessment, Plan (clinical record method)
- CNS = Cartão Nacional de Saúde (National Health Card)
- CPF = Cadastro de Pessoas Físicas
- e-SUS APS is the Brazilian primary care information system

**Heatmap**: 7 days × 24 hours matrix of appointment density. Data source: appointments (agendamentos). Each cell = count of appointments for that weekday/hour. Could also include no-show breakdown.

**KPIs**:
- Taxa de absenteísmo/no-show: percentage of appointments marked as "faltou" (no-show) out of completed/expected appointments
- Tempo médio de espera: average wait time — could be time between scheduled time and actual care start (tempo de espera na unidade), or time between scheduling and appointment. In APS context, usually it's the waiting time in the waiting room (chegada → atendimento) or time from request (demanda) to consultation. I'll implement both interpretations or pick the most common: minutes between scheduled start and actual start (atraso) — actually "tempo de espera" in SUS often refers to wait time for scheduling (tempo de espera para consulta). Let me implement it as average minutes between `chegada_em` (arrival/check-in) and `iniciou_em` (care started) when available, falling back to scheduled vs started. Hmm, to keep it robust, I'll compute wait time as minutes from scheduled datetime to actual start datetime (positive part), which is the classic "waiting time" metric. Actually let me think about what fields an Appointment model would have:

Typical Appointment model fields:
- id
- paciente_id (FK)
- profissional_id (FK)
- unidade_id (FK - UBS)
- data_hora_inicio (scheduled start)
- data_hora_fim (scheduled end)
- status: enum (AGENDADO, CONFIRMADO, ATENDIDO, FALTOU (no-show), CANCELADO_PACIENTE, CANCELADO_UNIDADE, REAGENDADO)
- chegada_em (check-in timestamp, nullable)
- inicio_atendimento_em (actual start, nullable)
- fim_atendimento_em (nullable)
- motivo / queixa (CIAP-2 code for reason for encounter)
- canal_agendamento (e.g., AGENDEJA, PRESENCIAL, TELEFONE)
- created_at, updated_at

For resolutividade na APS: percentage of encounters resolved in primary care without referral to specialized care (não houve encaminhamento). So we need Encounter/Atendimento model with fields like:
- id
- agendamento_id
- paciente_id
- profissional_id
- cid10_principal (nullable)
- ciap2_principal (nullable)
- metodo SOAP: subjetiva, objetiva, avaliacao, plano (text fields)
- encaminhado_para (nullable - especialidade / CETS)
- resolutivo (bool) or derived from encaminhamento
- conduta: enum (ALTA_RESOLVIDO, ENCAMINHAMENTO_ESPECIALISTA, ENCAMINHAMENTO_URGENCIA, RETORNO_AGENDADO, etc.)

Resolutividade = atendimentos com conduta de alta/resolução local / total atendimentos (excluindo cancelados?). Standard definition: proportion of consultations resolved without referral to other points of care.

Let me design the architecture:

```
backend/app/
├── api/v1/
│   ├── analytics.py          # main deliverable
├── schemas/
│   └── analytics.py          # Pydantic v2 schemas
├── repositories/
│   └── analytics.py          # SQLAlchemy 2.0 queries
├── services/
│   └── analytics.py          # business logic
├── models/
│   ├── agendamento.py
│   └── atendimento.py
```

Since the task says "crie backend/app/api/v1/analytics.py contendo rotas FastAPI", the main file is the router. But to be complete and testable, I should provide the supporting layers. However, I need to be careful about scope — the task focuses on the analytics router. I'll deliver:

1. `backend/app/api/v1/analytics.py` — router with the two endpoints
2. `backend/app/schemas/analytics.py` — Pydantic v2 response models
3. `backend/app/repositories/analytics.py` — SQLAlchemy 2.0 data access (or embed queries in service)
4. `backend/app/services/analytics.py` — KPI computation logic
5. `backend/tests/api/v1/test_analytics.py` — pytest tests
6. Maybe conftest with fixtures

Actually, to keep the response manageable but complete, I could structure it as:
- Router (analytics.py) — depends on service
- Service (analytics.py) — depends on repository/session
- Schemas (analytics.py)
- Repository (analytics.py) — SQLAlchemy 2.0 style queries
- Tests

Let me think about whether to include models. The task says "Heatmap de Agendamentos" — so there's an existing Agendamento model presumably. Since this is inspired by ClinicCare (a fictional/existing project), I'll assume models exist but I need to define them for tests. I'll create minimal model definitions in the test fixtures or assume they exist. Better approach: define the models I depend on in the repository with imports from `app.models`, and provide the models in the deliverable too (or at least reference them). To make tests self-contained, I'll create the models in the test setup or provide them.

Hmm, let me be pragmatic: I'll deliver a complete vertical slice:

1. `backend/app/models/agendamento.py` — SQLAlchemy 2.0 model (if not existing, define it; I'll note it may already exist)
2. `backend/app/models/atendimento.py` — clinical encounter model
3. `backend/app/schemas/analytics.py`
4. `backend/app/repositories/analytics.py`
5. `backend/app/services/analytics.py`
6. `backend/app/api/v1/analytics.py`
7. `backend/tests/...` tests

Actually, that's a lot. Let me reconsider. The instruction: "crie backend/app/api/v1/analytics.py contendo rotas FastAPI de telemetria clínica". The primary deliverable is the router file. But "Manter conformidade total e cobertura de testes automatizados com pytest" means tests are required.

I'll structure the answer as a vertical slice with clear file boundaries. To avoid duplicating existing models, I'll assume the project has `app.models.agendamento.Agendamento` and `app.models.atendimento.Atendimento` — but since I can't verify, I'll define them in the deliverable as part of the slice, with a note that if they already exist, adapt imports.

Let me design each piece carefully.

### Models (SQLAlchemy 2.0, typed)

```python
# backend/app/models/agendamento.py
import enum
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

class StatusAgendamento(str, enum.Enum):
    AGENDADO = "AGENDADO"
    CONFIRMADO = "CONFIRMADO"
    ATENDIDO = "ATENDIDO"
    FALTOU = "FALTOU"          # no-show
    CANCELADO_PACIENTE = "CANCELADO_PACIENTE"
    CANCELADO_UNIDADE = "CANCELADO_UNIDADE"
    REAGENDADO = "REAGENDADO"

class Agendamento(Base):
    __tablename__ = "agendamentos"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id"))
    profissional_id: Mapped[int] = mapped_column(ForeignKey("profissionais.id"))
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"))  # UBS
    inicio_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fim_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[StatusAgendamento] = mapped_column(Enum(StatusAgendamento, name="status_agendamento"))
    chegada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # check-in
    inicio_atendimento_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canal: Mapped[str] = ...
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Wait — for heatmap we need weekday and hour of the scheduled start. Weekday: ISO 1=Monday..7=Sunday. Hour: 0-23.

For no-show: status == FALTOU. Denominator: appointments that reached a "definitive" state: ATENDIDO + FALTOU (i.e., expected consultations that occurred or not). Cancelled by patient/unit typically excluded from no-show calc.

For wait time: for ATENDIDO appointments with chegada_em and inicio_atendimento_em: wait = inicio_atendimento_em - chegada_em. If chegada_em is null, fallback to inicio_atendimento_em - inicio_em (delay vs scheduled). I'll compute average of wait minutes using chegada→início when present, else scheduled→início. Hmm, mixing definitions is statistically iffy. Better: define "tempo médio de espera" as minutes between scheduled start (inicio_em) and actual care start (inicio_atendimento_em), counting only positive delays? Or between arrival and start?

In APS/e-SUS context, "tempo de espera" commonly reported is waiting time in the unit (from check-in to being seen). I'll implement: primary = chegada_em → inicio_atendimento_em; fallback (when no check-in recorded) = inicio_em → inicio_atendimento_em, flagged in response metadata. Actually simpler and cleaner: compute both and expose:
- `tempo_medio_espera_min`: average wait (chegada→início when available; otherwise agendado→início)
- plus counts of samples.

Hmm, let me keep it well-defined: I'll compute wait as the interval between the "reference start" and actual start, where reference = chegada_em if present else inicio_em. And document it. Also expose `p50`/`p90`? That could be nice (percentis). Let me include p50 and p90 for quality. Use SQL percentile_cont or compute in Python. For portability across SQLite (tests) and Postgres, computing percentiles in SQL differs; SQLite lacks percentile_cont without extension. Since tests will use SQLite, I'll compute aggregates mostly in SQL where portable (avg, count, case) and percentiles in Python from fetched values. Actually for wait times, fetching all values could be heavy; but with a date filter it's bounded. Alternatively compute avg in SQL and percentiles in Python only if needed. Let me do: SQL for counts/avg; Python for percentiles over fetched wait minutes (bounded by period). That's fine.

For resolutividade: Atendimento (encounter) model:

```python
class CondutaEncaminhamento(str, enum.Enum):
    RESOLVIDO_APS = "RESOLVIDO_APS"          # alta/resolução na APS
    ENCAMINHADO_ESPECIALISTA = "ENCAMINHADO_ESPECIALISTA"
    ENCAMINHADO_URGENCIA = "ENCAMINHADO_URGENCIA"
    RETORNO_APS = "RETORNO_APS"              # retorno agendado na APS — still APS care
    ...

class Atendimento(Base):
    __tablename__ = "atendimentos"
    id, agendamento_id (FK unique), paciente_id, profissional_id, unidade_id
    cid10_principal: Mapped[str | None] = mapped_column(String(4))   # CID-10
    ciap2_principal: Mapped[str | None] = mapped_column(String(5))   # CIAP-2 (3 letras + 2 dígitos, e.g., "A01"? Actually CIAP-2 codes are like "A01"? CIAP-2: letter (chapter) + 2 digits, e.g., K29? Hmm CIAP codes: chapter letter + 2 digits, e.g., "A01"? Let me recall: CIAP-2 codes like "K29" (hipertensão não especificada? no that's K86?). CIAP-2: e.g., A01, K29... Actually CIAP-2 code format: one letter (A–Z, chapter) + two digits. Examples: K29 = "Hypertension, unspecified"? I believe K29 is "Blood pressure high" hmm. Anyway format: letter + 2 digits = 3 chars. e.g., "S27"? I'll use String(3) with regex ^[A-Z]\d{2}$.
    subjetiva/objetiva/avaliacao/plano: Text (SOAP)
    conduta: enum
    encaminhamento_especialidade: str | None
```

Resolutividade = (atendimentos com conduta RESOLVIDO_APS or RETORNO_APS?) / total atendimentos válidos. Definition: proportion of encounters whose outcome did not require referral outside APS. So numerator: conduta in (RESOLVIDO_APS, RETORNO_APS) — retorno agendado is still resolved within APS flow? Hmm. Strictly, "resolutividade" = resolved without referral to another point of the network. A scheduled return within APS is still APS care. I'll count RESOLVIDO_APS and RETORNO_APS as resolutivos; ENCAMINHADO_* as não resolutivos. Also possibly "INTERCORRENCIA"? Keep enum small: RESOLVIDO_APS, RETORNO_APS, ENCAMINHAMENTO_ESPECIALISTA, ENCAMINHAMENTO_URGENCIA, OBITO? Too much. Keep 4 + maybe ALTA? RESOLVIDO_APS covers alta.

Denominator: atendimentos realizados (i.e., linked to appointments with status ATENDIDO, or simply all Atendimento records in period). I'll use Atendimento records in period (an Atendimento exists only when care happened).

Also KPIs should support filters: unidade_id, profissional_id, periodo (data_inicio, data_fim). And maybe equipe (INE)? Keep: unidade_id, profissional_id, data_inicio, data_fim.

### Schemas (Pydantic v2)

```python
# schemas/analytics.py
from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field, computed_field

class DiaSemana(int, Enum):
    SEGUNDA = 1 ... DOMINGO = 7

class HeatmapCelula(BaseModel):
    dia_semana: DiaSemana  # 1..7 ISO
    hora: int = Field(ge=0, le=23)
    total: int = Field(ge=0)
    atendidos: int
    faltas: int
    cancelados: int
    taxa_absenteismo: float | None  # per cell? maybe
    densidade: float  # normalized 0..1 relative to max cell

class HeatmapResponse(BaseModel):
    periodo: PeriodoInfo
    filtros: ...
    matriz: list[HeatmapCelula]  # 168 cells
    total_agendamentos: int
    pico: PicoInfo  # dia/hora com maior densidade
    gerado_em: datetime

class KpisResponse(BaseModel):
    periodo: ...
    absenteismo: TaxaAbsenteismo
    espera: TempoEspera
    resolutividade: TaxaResolutividade
```

Let me define:

```python
class TaxaAbsenteismo(BaseModel):
    total_esperados: int      # ATENDIDO + FALTOU
    faltas: int
    taxa: float               # 0..1 or percent? I'll use percent 0-100 with 2 decimals? Or fraction. I'll use fraction with 4 decimals and also percent field? Keep "taxa" as percent (0-100). Hmm. In Brazilian health dashboards, "taxa de absenteísmo" usually shown as %. I'll return `taxa_percentual: float` and maybe `taxa` fraction. Choose: `taxa: float = Field(..., ge=0, le=1, description="proporção")` plus `percentual` computed. Simpler: return percent with description. I'll go with fraction (0..1) named `taxa` and a computed `percentual`. Actually to avoid confusion, single field `taxa_percentual` (0–100). Let me do both: `taxa` (0–1) and `taxa_percentual` computed_field = taxa*100. Fine.
```

Wait, computed_field in Pydantic v2: `@computed_field` decorator on property. Yes.

```python
class TempoEspera(BaseModel):
    amostra: int                       # nº de atendimentos com dado de espera
    media_min: float
    mediana_min: float | None
    p90_min: float | None
    unidade: Literal["minutos"] = "minutos"

class TaxaResolutividade(BaseModel):
    total_atendimentos: int
    resolutivos: int
    encaminhamentos: int
    taxa: float
    taxa_percent