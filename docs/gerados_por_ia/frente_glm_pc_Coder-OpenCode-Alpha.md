The user wants me to create a Telemedicine API for a system called MedIA. They want:

1. File: `backend/app/api/v1/telemedicina.py` with FastAPI routes:
   - POST /agendamentos (schedule teleconsultation)
   - GET /salas/{sala_id} (get room info)
   - POST /iniciar-chamada (start call)
   - POST /finalizar-chamada (finish call)

2. Requirements:
   - Schedule teleconsultation
   - Generate unique room link
   - Update call status (AGUARDANDO, EM_CHAMADA, FINALIZADA)
   - Link to SOAP medical record
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS compatibility (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Telemedicine practical: video rooms, remote SOAP evolution, digital prescription
   - Testability with pytest

Since this is a complete implementation, I should provide:
1. The main API file `backend/app/api/v1/telemedicina.py`
2. Supporting files that would be needed:
   - Models (SQLAlchemy)
   - Schemas (Pydantic v2)
   - Service layer
   - Tests (pytest)

Let me design this properly:

**Architecture:**
- `backend/app/models/telemedicina.py` - SQLAlchemy models
- `backend/app/schemas/telemedicina.py` - Pydantic schemas
- `backend/app/services/telemedicina_service.py` - Business logic
- `backend/app/api/v1/telemedicina.py` - API routes
- `backend/tests/test_telemedicina.py` - Tests

**Models:**

1. `AgendamentoTeleconsulta` - teleconsultation scheduling
   - id, paciente_id, profissional_id, data_hora, status, motivo, cid10_code, ciap2_code
   
2. `SalaAtendimento` - room
   - id, agendamento_id, codigo_sala (unique link token), status (AGUARDANDO, EM_CHAMADA, FINALIZADA), iniciada_em, finalizada_em

3. `ProntuarioSOAP` - SOAP record
   - id, sala_id, subjetivo, objetivo, avaliacao, plano, cid10, ciap2, profissional_id, paciente_id

**Status enum:**
```python
class StatusChamada(str, Enum):
    AGUARDANDO = "AGUARDANDO"
    EM_CHAMADA = "EM_CHAMADA"
    FINALIZADA = "FINALIZADA"
```

**Endpoints:**

1. `POST /agendamentos` - Create teleconsultation schedule
   - Input: paciente (CNS/CPF), profissional_id, data_hora, motivo, cid10?, ciap2?
   - Output: agendamento with generated room

2. `GET /salas/{sala_id}` - Get room info by ID or code
   - Output: room details, status, link

3. `POST /iniciar-chamada` - Start call
   - Input: sala_id
   - Updates status to EM_CHAMADA

4. `POST /finalizar-chamada` - Finish call
   - Input: sala_id, SOAP data (subjetivo, objetivo, avaliacao, plano, cid10, ciap2)
   - Updates status to FINALIZADA, creates SOAP record

Let me write the code:

**backend/app/models/telemedicina.py:**

```python
# Arquivo: backend/app/models/telemedicina.py
"""Modelos SQLAlchemy 2.0 para o módulo de Telemedicina do MedIA."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.profissional import Profissional

from app.db.base import Base


class StatusChamada(str, enum.Enum):
    """Estados possíveis de uma sala de teleatendimento."""
    AGUARDANDO = "AGUARDANDO"
    EM_CHAMADA = "EM_CHAMADA"
    FINALIZADA = "FINALIZADA"


class AgendamentoTeleconsulta(Base):
    __tablename__ = "agendamentos_teleconsulta"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paciente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pacientes.id"), nullable=False, index=True)
    profissional_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profissionais.id"), nullable=False, index=True)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    motivo: Mapped[str] = mapped_column(String(255), nullable=False)
    cid10: Mapped[str | None] = mapped_column(String(8), nullable=True)  # CID-10
    ciap2: Mapped[str | None] = mapped_column(String(5), nullable=True)  # CIAP-2
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sala: Mapped[SalaAtendimento | None] = relationship(back_populates="agendamento", uselist=False, cascade="all, delete-orphan")


class SalaAtendimento(Base):
    __tablename__ = "salas_atendimento"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agendamento_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agendamentos_teleconsulta.id"), unique=True, nullable=False)
    codigo_sala: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    status: Mapped[StatusChamada] = mapped_column(Enum(StatusChamada, name="status_chamada"), default=StatusChamada.AGUARDANDO, nullable=False)
    iniciada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finalizada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    agendamento: Mapped[AgendamentoTeleconsulta] = relationship(back_populates="sala")
    prontuario: Mapped[ProntuarioSOAP | None] = relationship(back_populates="sala", uselist=False, cascade="all, delete-orphan")


class ProntuarioSOAP(Base):
    __tablename__ = "prontuarios_soap"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sala_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("salas_atendimento.id"), unique=True, nullable=False)
    paciente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pacientes.id"), nullable=False, index=True)
    profissional_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profissionais.id"), nullable=False, index=True)
    subjetivo: Mapped[str] = mapped_column(Text, nullable=False)
    objetivo: Mapped[str] = mapped_column(Text, nullable=False)
    avaliacao: Mapped[str] = mapped_column(Text, nullable=False)
    plano: Mapped[str] = mapped_column(Text, nullable=False)
    cid10: Mapped[str | None] = mapped_column(String(8), nullable=True)
    ciap2: Mapped[str | None] = mapped_column(String(5), nullable=True)
    prescricao_digital: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sala: Mapped[SalaAtendimento] = relationship(back_populates="prontuario")
```

Hmm, but I don't know the exact structure of the existing project. Since the task says "Crie o arquivo: backend/app/api/v1/telemedicina.py", I should focus on that file but provide supporting files to make it complete and executable. I'll make reasonable assumptions about the project structure and document them.

Let me think about what's needed for a complete, executable solution:

1. `backend/app/models/telemedicina.py` - models
2. `backend/app/schemas/telemedicina.py` - Pydantic schemas
3. `backend/app/services/telemedicina_service.py` - service layer (business logic)
4. `backend/app/api/v1/telemedicina.py` - the main API router
5. `backend/tests/test_telemedicina.py` - pytest tests
6. Maybe `backend/app/db/session.py` - database setup (or assume exists)

For the router prefix, typically it would be mounted as `/api/v1/telemedicina` so routes become `/api/v1/telemedicina/agendamentos` etc. The task says routes: POST /agendamentos, GET /salas/{sala_id}, POST /iniciar-chamada, POST /finalizar-chamada. So within the router, those are the paths.

Let me design the schemas:

```python
# backend/app/schemas/telemedicina.py
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StatusChamada(str, Enum):
    AGUARDANDO = "AGUARDANDO"
    EM_CHAMADA = "EM_CHAMADA"
    FINALIZADA = "FINALIZADA"


class IdentificacaoPaciente(BaseModel):
    """Identificação do paciente por CNS ou CPF (DIRETRIZ 3)."""
    model_config = ConfigDict(str_strip_whitespace=True)

    cns: str | None = Field(default=None, pattern=r"^\d{15}$", description="Cartão Nacional de Saúde (15 dígitos)")
    cpf: str | None = Field(default=None, pattern=r"^\d{11}$", description="CPF (11 dígitos)")

    @model_validator(mode="after")
    def exige_cns_ou_cpf(self) -> "IdentificacaoPaciente":
        if not self.cns and not self.cpf:
            raise ValueError("Informe CNS ou CPF do paciente")
        return self


class AgendamentoCreate(BaseModel):
    paciente: IdentificacaoPaciente
    profissional_id: uuid.UUID
    data_hora: datetime
    motivo: str = Field(min_length=3, max_length=255)
    cid10: str | None = Field(default=None, pattern=r"^[A-TV-Z][0-9]{2}(\.[0-9]{1,2})?$")
    ciap2: str | None = Field(default=None, pattern=r"^[A-Z][0-9]{2}$")
    observacoes: str | None = None


class ProntuarioSOAPCreate(BaseModel):
    subjetivo: str = Field(min_length=1)
    objetivo: str = Field(min_length=1)
    avaliacao: str = Field(min_length=1)
    plano: str = Field(min_length=1)
    cid10: str | None = ...
    ciap2: str | None = ...
    prescricao_digital: str | None = ...


class FinalizarChamadaRequest(BaseModel):
    sala_id: uuid.UUID
    prontuario: ProntuarioSOAPCreate


class IniciarChamadaRequest(BaseModel):
    sala_id: uuid.UUID


class SalaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    codigo_sala: str
    link_atendimento: str
    status: StatusChamada
    ...
```

For the service layer, I'll create a `TelemedicinaService` class with methods:
- `criar_agendamento(dados) -> Agendamento`
- `obter_sala(sala_id) -> Sala`
- `iniciar_chamada(sala_id) -> Sala`
- `finalizar_chamada(sala_id, prontuario) -> ProntuarioSOAP`

The unique link generation: use `secrets.token_urlsafe(16)` or a UUID-based code. Something like `https://tele.mediabrasil.gov.br/sala/{codigo}` — but better to make base URL configurable via settings.

For tests, use pytest with SQLite in-memory (with StaticPool) or use httpx AsyncClient with ASGITransport. Since SQLAlchemy UUID with PostgreSQL dialect might not work on SQLite... I could use `sqlalchemy.Uuid` type which is dialect-agnostic (SQLAlchemy 2.0 has `Uuid` type). Let me use `sa.Uuid` instead of postgresql UUID to make tests easier with SQLite.

Actually in SQLAlchemy 2.0, there's `sqlalchemy.Uuid` which works across dialects. Let me use that.

```python
from sqlalchemy import Uuid
id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
```

That works with SQLite for tests.

For the API file, I need dependency injection:
- `get_db` - database session dependency
- Maybe `get_current_user` for auth — I'll include a placeholder dependency that can be swapped, or keep it simple with an optional auth dependency. To keep it executable, I'll define a simple dependency structure but note it should integrate with the project's auth. Actually, let me include a lightweight auth dependency stub that reads a JWT-ish header but defaults to allowing, or better: define `Depends(get_db)` and a `profissional_atual` dependency that's clearly marked for integration.

Hmm, to keep it truly executable, maybe I should provide minimal versions of the infrastructure files too:
- `backend/app/db/session.py` (engine, SessionLocal, get_db)
- `backend/app/db/base.py` (Base declarative)
- `backend/app/main.py` (app factory including router)

That makes it fully runnable. Let me include those as minimal supporting files.

Let me also think about business rules:
1. POST /agendamentos: validate data_hora is in future, resolve paciente by CNS/CPF (create if not exists? or error?). For simplicity: look up paciente by CNS/CPF; if not found, raise 404. Actually for a complete flow, maybe accept paciente_id directly OR identification. Let me support both: `paciente_id` optional, or `paciente: {cns/cpf}`. Hmm, keep it simpler: the request has `paciente_cns` or `paciente_cpf` and the service resolves. But if the patient doesn't exist in the system... In a real SUS system, the patient would be registered first (cadastro). I'll resolve and 404 if not found, with a clear message. Actually, to make tests self-contained, maybe auto-create a minimal patient record? That adds complexity. Let me look up and 404 if not found — cleaner. But then tests need patient fixtures. I'll create the Paciente model minimally too... 

Hmm, this is getting big. Let me scope: the task focuses on telemedicina.py. I'll create:

1. `backend/app/models/telemedicina.py` — full models (Agendamento, Sala, ProntuarioSOAP)
2. `backend/app/schemas/telemedicina.py` — full schemas
3. `backend/app/services/telemedicina_service.py` — service with business logic
4. `backend/app/api/v1/telemedicina.py` — the router (main deliverable)
5. `backend/app/api/deps.py` — dependencies (get_db, auth stub)
6. `backend/app/db/base.py` + `backend/app/db/session.py` — minimal infra
7. `backend/app/main.py` — app wiring
8. `backend/tests/test_telemedicina.py` — pytest tests with SQLite in-memory

For patient lookup: I'll include a minimal `Paciente` model in a `pacientes.py` model file with cns, cpf, nome. The service resolves paciente by CNS/CPF. If not found → 404 with message "Paciente não encontrado no cadastro. Realize o cadastro antes de agendar." That's realistic for SUS.

Actually wait — maybe simpler and more robust: allow the agendamento request to carry `paciente_id` OR identification (cns/cpf). The service resolves. Tests create a patient fixture directly in DB.

Let me now write everything carefully.

**Enums:**

```python
class StatusChamada(str, enum.Enum):
    AGUARDANDO = "AGUARDANDO"
    EM_CHAMADA = "EM_CHAMADA"
    FINALIZADA = "FINALIZADA"
```

**Room code generation:**

```python
import secrets
def gerar_codigo_sala() -> str:
    return f"TELE-{secrets.token_hex(8).upper()}"  # e.g., TELE-A1B2C3D4E5F6A7B8
```

Link: `{settings.TELEMEDICINA_BASE_URL}/sala/{codigo_sala}` — configurable. Default `https://teleatendimento.mediagov.local/sala`.

**Service methods:**

```python
class TelemedicinaService:
    def __init__(self, db: Session):
        self.db = db

    def criar_agendamento(self, dados: AgendamentoCreate) -> AgendamentoTeleconsulta:
        # valida data futura
        # resolve paciente
        # valida profissional existe
        # cria agendamento + sala com código único
        ...

    def obter_sala(self, sala_id: uuid.UUID) -> SalaAtendimento: ...

    def iniciar_chamada(self, sala_id: uuid.UUID) -> SalaAtendimento:
        # AGUARDANDO -> EM_CHAMADA
        ...

    def finalizar_chamada(self, sala_id: uuid.UUID, prontuario: ProntuarioSOAPCreate) -> ProntuarioSOAP:
        # EM_CHAMADA -> FINALIZADA + cria SOAP
        ...
```

Error handling: custom exceptions mapped to HTTPException in the router, or raise HTTPException in service. Cleaner: domain exceptions in service, router translates. Let me define:

```python
class TelemedicinaError(Exception): ...
class SalaNaoEncontradaError(TelemedicinaError): ...
class TransicaoStatusInvalidaError(TelemedicinaError): ...
class PacienteNaoEncontradoError(TelemedicinaError): ...
class ProfissionalNaoEncontradoError(TelemedicinaError): ...
class DataInvalidaError(TelemedicinaError): ...
