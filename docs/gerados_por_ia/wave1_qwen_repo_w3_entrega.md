Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create a SQLAlchemy repository file `backend/app/repositories/telemedicina_repo.py` for a Telemedicine project (MedIA).
   - **Class:** `TelemedicinaRepository`
   - **Methods:**
     - `criar_agendamento(db, dados)`
     - `buscar_por_codigo_sala(db, codigo)`
     - `atualizar_status(db, teleconsulta_id, novo_status)`
     - `registrar_evolucao_soap(db, teleconsulta_id, dados_soap)`
   - **Requirements:**
     - Python 3.12 strict typing
     - Pydantic v2 for data validation (implied by "tipagem estrita com Pydantic v2")
     - SQLAlchemy 2.0 compatibility
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification
     - Exception handling
     - Full test coverage with pytest (implied by "Manter conformidade total e cobertura de testes automatizados com pytest")
     - Provide complete, executable code
     - Specify file path in comments or block header

2.  **Analyze Requirements & Constraints:**
   - **File Path:** `backend/app/repositories/telemedicina_repo.py`
   - **Database:** SQLAlchemy 2.0 style (async/sync? The prompt says `db` parameter, typically implies sync session in FastAPI/SQLAlchemy contexts, but I'll stick to sync for simplicity unless specified otherwise. I'll use `sqlalchemy.orm.Session` as `db`).
   - **Models:** I need to define or assume models for teleconsultations, appointments, SOAP notes, etc. Since it's a repository, I should define the necessary SQLAlchemy models or import them. I'll define them inline or assume they exist. To make it self-contained and executable, I'll define the models in the same file or clearly state dependencies. I'll create a minimal but complete setup with models, repository, and tests.
   - **Pydantic v2:** Use `pydantic` for input validation. I'll create Pydantic models for the input data.
   - **SUS/APS Standards:** CIAP-2, CID-10, SOAP, CNS/CPF. I'll include these fields in the models/schema.
   - **Exception Handling:** Use custom exceptions or standard SQLAlchemy exceptions (`sqlalchemy.exc.SQLAlchemyError`, `sqlalchemy.orm.exc.ObjectDeletedError`, etc.). I'll create a custom `TelemedicinaError` for clarity.
   - **Testing:** Provide pytest tests covering all methods, using `pytest`, `sqlalchemy`, `pytest-asyncio` (if async) or standard sync. I'll stick to sync for simplicity, but make it clear. I'll use `pytest` with an in-memory SQLite database for testing.

3.  **Design the Repository & Models:**
   - **Models (SQLAlchemy 2.0):**
     - `Teleconsulta` (Teleconsultation): id, codigo_sala, paciente_cpf, medico_cns, status, data_agendamento, created_at, updated_at
     - `EvolucaoSOAP` (SOAP Evolution): id, teleconsulta_id, motivo, observacoes, plano, created_at
     - `Agendamento` (Appointment): id, teleconsulta_id, data_hora, status, created_at
     - I'll keep it focused on the repository methods requested. The repository will interact with `Teleconsulta` and `EvolucaoSOAP` primarily.
   - **Pydantic Schemas:**
     - `AgendamentoCreate` (for `criar_agendamento`)
     - `EvolucaoSOAPCreate` (for `registrar_evolucao_soap`)
   - **Repository Methods:**
     - `criar_agendamento(db, dados)`: Creates an appointment/teleconsultation record.
     - `buscar_por_codigo_sala(db, codigo)`: Finds teleconsultations by room code.
     - `atualizar_status(db, teleconsulta_id, novo_status)`: Updates status with validation.
     - `registrar_evolucao_soap(db, teleconsulta_id, dados_soap)`: Creates SOAP note.
   - **Validation & Types:**
     - Use `typing` module: `Optional`, `List`, `Dict`, `Any`, `Union`, `TYPE_CHECKING`
     - Use `pydantic` v2: `BaseModel`, `Field`, `ConfigDict`
     - Use `sqlalchemy` 2.0: `Mapped`, `mapped_column`, `MappedAsDict` (optional), `Session`
     - Status enum: `AgendamentoStatus` (e.g., AGENDADO, EM_ANDAMENTO, CONCLUIDO, CANCELADO)

4.  **Draft the Code (Mental Refinement):**
   I'll structure the file as follows:
   - Imports
   - Enums/Constants (Status, CIAP-2/CID-10 validation if needed)
   - Pydantic Schemas
   - SQLAlchemy Models
   - Repository Class
   - Exception Classes
   - (Optional but requested) Pytest tests

   Let's write it out carefully.

   *Imports:*
   ```python
   from typing import Optional, List, Any, Dict
   from enum import Enum
   from datetime import datetime
   import re

   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy import String, Text, DateTime, Enum as SAEnum, ForeignKey, Integer
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, Session, relationship
   from sqlalchemy.exc import IntegrityError, SQLAlchemyError
   ```

   *Enums:*
   ```python
   class AgendamentoStatus(str, Enum):
       AGENDADO = "AGENDADO"
       EM_ANDAMENTO = "EM_ANDAMENTO"
       CONCLUIDO = "CONCLUIDO"
       CANCELADO = "CANCELADO"
       ATRASADO = "ATRASADO"
   ```

   *Pydantic Schemas:*
   ```python
   class AgendamentoCreate(BaseModel):
       codigo_sala: str = Field(..., min_length=1, max_length=50)
       paciente_cpf: str = Field(..., pattern=r'^\d{11}$')
       medico_cns: str = Field(..., pattern=r'^\d{15}$')
       data_agendamento: datetime = Field(...)
       motivo_cid10: str = Field(..., pattern=r'^[A-Z]\d{2}$')
       motivo_ciap2: Optional[str] = Field(default=None, pattern=r'^[A-Z]\d{2,3}$')

       model_config = ConfigDict(str_strip_whitespace=True)

       @field_validator('data_agendamento')
       @classmethod
       def validate_future_date(cls, v):
           if v < datetime.now():
               raise ValueError('A data de agendamento deve ser futura.')
           return v

   class EvolucaoSOAPCreate(BaseModel):
       motivo: str = Field(..., min_length=1)
       observacoes: str = Field(..., min_length=1)
       plano: str = Field(..., min_length=1)
   ```

   *SQLAlchemy Models:*
   ```python
   class Base(DeclarativeBase):
       pass

   class Teleconsulta(Base):
       __tablename__ = "teleconsultas"
       id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
       codigo_sala: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
       paciente_cpf: Mapped[str] = mapped_column(String(11), nullable=False)
       medico_cns: Mapped[str] = mapped_column(String(15), nullable=False)
       status: Mapped[AgendamentoStatus] = mapped_column(SAEnum(AgendamentoStatus), default=AgendamentoStatus.AGENDADO)
       data_agendamento: Mapped[datetime] = mapped_column(DateTime, nullable=False)
       motivo_cid10: Mapped[str] = mapped_column(String(4), nullable=False)
       motivo_ciap2: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
       created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

       evolucoes: Mapped[List["EvolucaoSOAP"]] = relationship(back_populates="teleconsulta", cascade="all, delete-orphan")

   class EvolucaoSOAP(Base):
       __tablename__ = "evolicoes_soap"
       id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
       teleconsulta_id: Mapped[int] = mapped_column(ForeignKey("teleconsultas.id"), nullable=False)
       motivo: Mapped[str] = mapped_column(Text, nullable=False)
       observacoes: Mapped[str] = mapped_column(Text, nullable=False)
       plano: Mapped[str] = mapped_column(Text, nullable=False)
       created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

       teleconsulta: Mapped["Teleconsulta"] = relationship(back_populates="evolicoes")
   ```
   *Wait*, I need to fix the relationship name mismatch. `evolicoes` vs `evolicoes`. I'll standardize to `evolicoes_soap`.
   Also, SQLAlchemy 2.0 uses `mapped_column` correctly. I'll adjust.

   *Repository Class:*
   ```python
   class TelemedicinaRepository:
       def __init__(self, db: Session):
           self.db = db

       def criar_agendamento(self, dados: AgendamentoCreate) -> Teleconsulta:
           try:
               teleconsulta = Teleconsulta(
                   codigo_sala=dados.codigo_sala,
                   paciente_cpf=dados.paciente_cpf,
                   medico_cns=dados.medico_cns,
                   data_agendamento=dados.data_agendamento,
                   motivo_cid10=dados.motivo_cid10,
                   motivo_ciap2=dados.motivo_ciap2,
                   status=AgendamentoStatus.AGENDADO,
               )
               self.db.add(teleconsulta)
               self.db.commit()
               self.db.refresh(teleconsulta)
               return teleconsulta
           except IntegrityError:
               self.db.rollback()
               raise TelemedicinaError("Já existe um agendamento com este código de sala.")
           except SQLAlchemyError as e:
               self.db.rollback()
               raise TelemedicinaError(f"Erro ao criar agendamento: {str(e)}")

       def buscar_por_codigo_sala(self, codigo: str) -> List[Teleconsulta]:
           try:
               return self.db.query(Teleconsulta).filter(Teleconsulta.codigo_sala == codigo).all()
           except SQLAlchemyError as e:
               raise TelemedicinaError(f"Erro ao buscar agendamento: {str(e)}")

       def atualizar_status(self, teleconsulta_id: int, novo_status: AgendamentoStatus) -> Teleconsulta:
           teleconsulta = self.db.query(Teleconsulta).get(teleconsulta_id) # SQLAlchemy 2.0 deprecated get, use select
           # Fix for SQLAlchemy 2.0:
           from sqlalchemy import select
           stmt = select(Teleconsulta).where(Teleconsulta.id == teleconsulta_id)
           teleconsulta = self.db.execute(stmt).scalar_one_or_none()
           if not teleconsulta:
               raise TelemedicinaError("Teleconsulta não encontrada.")
           teleconsulta.status = novo_status
           try:
               self.db.commit()
               self.db.refresh(teleconsulta)
               return teleconsulta
           except SQLAlchemyError as e:
               self.db.rollback()
               raise TelemedicinaError(f"Erro ao atualizar status: {str(e)}")

       def registrar_evolucao_soap(self, teleconsulta_id: int, dados_soap: EvolucaoSOAPCreate) -> EvolucaoSOAP:
           # Check if teleconsulta exists
           stmt = select(Teleconsulta).where(Teleconsulta.id == teleconsulta_id)
           teleconsulta = self.db.execute(stmt).scalar_one_or_none()
           if not teleconsulta:
               raise TelemedicinaError("Teleconsulta não encontrada.")
           if teleconsulta.status != AgendamentoStatus.EM_ANDAMENTO:
               raise TelemedicinaError("A teleconsulta deve estar em andamento para registrar evolução.")

           evolucao = EvolucaoSOAP(
               teleconsulta_id=teleconsulta_id,
               motivo=dados_soap.motivo,
               observacoes=dados_soap.observacoes,
               plano=dados_soap.plano,
           )
           self.db.add(evolucao)
           try:
               self.db.commit()
               self.db.refresh(evolucao)
               return evolucao
           except SQLAlchemyError as e:
               self.db.rollback()
               raise TelemedicinaError(f"Erro ao registrar evolução SOAP: {str(e)}")
   ```

   *Custom Exception:*
   ```python
   class TelemedicinaError(Exception):
       pass
   ```

   *Testing:*
   I need to provide pytest tests. I'll create a test file or include it in the same response. The prompt says "Manter conformidade total e cobertura de testes automatizados com pytest." I'll provide a complete test file `tests/test_telemedicina_repo.py` or inline it. I'll provide it as a separate block.

   Test structure:
   - Use `pytest`, `sqlalchemy`, `pytest-mock` or just standard `Session` with `create_engine`.
   - Use `pytest.fixture` for DB setup.
   - Test all 4 methods.
   - Test validation errors.
   - Test exception handling.

   Let's draft the test file mentally:
   ```python
   import pytest
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from datetime import datetime, timedelta
   from backend.app.repositories.telemedicina_repo import (
       Base, TelemedicinaRepository, AgendamentoCreate, EvolucaoSOAPCreate,
       AgendamentoStatus, TelemedicinaError
   )

   @pytest.fixture
   def engine():
       return create_engine("sqlite:///:memory:", echo=False)

   @pytest.fixture
   def session(engine):
       Base.metadata.create_all(engine)
       SessionLocal = sessionmaker(bind=engine)
       db = SessionLocal()
       yield db
       db.close()

   @pytest.fixture
   def repo(session):
       return TelemedicinaRepository(session)

   def test_criar_agendamento(repo, session):
       dados = AgendamentoCreate(
           codigo_sala="SALA001",
           paciente_cpf="12345678901",
           medico_cns="123456789012345",
           data_agendamento=datetime.now() + timedelta(days=1),
           motivo_cid10="J06.9",
           motivo_ciap2="A01"
       )
       result = repo.criar_agendamento(dados)
       assert result.codigo_sala == "SALA001"
       assert result.status == AgendamentoStatus.AGENDADO
       # Verify in DB
       from sqlalchemy import select
       stmt = select(Teleconsulta).where(Teleconsulta.id == result.id)
       db_obj = session.execute(stmt).scalar_one()
       assert db_obj.codigo_sala == "SALA001"

   def test_buscar_por_codigo_sala(repo, session):
       # create one first
       from backend.app.repositories.telemedicina_repo import Teleconsulta
       from sqlalchemy import select
       tele = Teleconsulta(
           codigo_sala="SALA002",
           paciente_cpf="11111111111",
           medico_cns="555555555555555",
           data_agendamento=datetime.now() + timedelta(days=1),
           motivo_cid10="J06.9"
       )
       session.add(tele)
       session.commit()

       results = repo.buscar_por_codigo_sala("SALA002")
       assert len(results) == 1
       assert results[0].codigo_sala == "SALA002"

   def test_atualizar_status(repo, session):
       # create one
       from backend.app.repositories.telemedicina_repo import Teleconsulta
       tele = Teleconsulta(
           codigo_sala="SALA003",
           paciente_cpf="22222222222",
           medico_cns="666666666666666",
           data_agendamento=datetime.now() + timedelta(days=1),
           motivo_cid10="J06.9",
           status=AgendamentoStatus.AGENDADO
       )
       session.add(tele)
       session.commit()

       updated = repo.atualizar_status(tele.id, AgendamentoStatus.EM_ANDAMENTO)
       assert updated.status == AgendamentoStatus.EM_ANDAMENTO

   def test_registrar_evolucao_soap(repo, session):
       # create one in EM_ANDAMENTO
       from backend.app.repositories.telemedicina_repo import Teleconsulta
       tele = Teleconsulta(
           codigo_sala="SALA004",
           paciente_cpf="33333333333",
           medico_cns="777777777777777",
           data_agendamento=datetime.now() + timedelta(days=1),
           motivo_cid10="J06.9",
           status=AgendamentoStatus.EM_ANDAMENTO
       )
       session.add(tele)
       session.commit()

       dados_soap = EvolucaoSOAPCreate(
           motivo="Dor de cabeça",
           observacoes="Paciente refere cefaleia há 2 dias",
           plano="Solicitar exames e retorno em 7 dias"
       )
       result = repo.registrar_evolucao_soap(tele.id, dados_soap)
       assert result.teleconsulta_id == tele.id
       assert result.motivo == "Dor de cabeça"

   def test_criar_agendamento_cpf_invalid():
       with pytest.raises(Exception): # Pydantic validation error
           AgendamentoCreate(
               codigo_sala="SALA001",
               paciente_cpf="123",
