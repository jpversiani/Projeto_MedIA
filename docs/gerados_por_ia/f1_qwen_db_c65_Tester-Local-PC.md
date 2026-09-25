Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Implement `backend/app/repositories/auditoria_telemedicina.py` with a class `AuditoriaTelemedicinaRepository` for logging teleconsultation events (connection, disconnection, consent acceptance, secure timestamping) using SQLAlchemy 2.0.
   - **Constraints:** Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), full compliance with automated tests using pytest.
   - **Output Requirement:** Provide complete, executable code. Specify file paths in code blocks.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/auditoria_telemedicina.py`
   - **Class:** `AuditoriaTelemedicinaRepository`
   - **Features:**
     - Log connection events
     - Log disconnection events
     - Log consent acceptance (LGPD/CFM)
     - Secure timestamping
     - Use SQLAlchemy 2.0 (async preferred, but I'll stick to sync or provide async if needed; I'll use async as it's modern, but I'll make sure it's compatible with standard SQLAlchemy 2.0 patterns)
     - Pydantic v2 for models/validation
     - SUS/APS standards: CIAP-2, CID-10, SOAP, CNS/CPF
     - Pytest coverage
   - **Architecture/Standards:** Python 3.12, strict typing, SQLAlchemy 2.0, Pydantic v2, pytest.

3.  **Design the Solution:**
   - **Database Models (SQLAlchemy 2.0):** Need a table for audit logs. Let's call it `TelemedicinaAuditoria`.
     - Fields: id, session_id, patient_cns, patient_cpf, professional_cpf, event_type, event_timestamp, ip_address, user_agent, consent_accepted (bool), consent_timestamp, soap_notes (optional), ciap2_codes (JSON/array), cid10_codes (JSON/array), metadata (JSON), created_at, updated_at.
     - Actually, to keep it focused on the repository task, I'll define the ORM model in the same file or assume it's imported. The prompt says "implemente backend/app/repositories/auditoria_telemedicina.py com a classe AuditoriaTelemedicinaRepository". I'll include the SQLAlchemy model definition in the same file for completeness, or import it. I'll define it locally to make it self-contained and executable.
   - **Pydantic Models:** For input validation and output serialization.
     - `TelemedicinaAuditoriaEvent` (Pydantic v2)
     - `TelemedicinaAuditoriaLog` (Pydantic v2)
   - **Repository Class:** `AuditoriaTelemedicinaRepository`
     - Constructor: takes a database session (async or sync). I'll use `AsyncSession` as it's standard for modern FastAPI/SQLAlchemy 2.0 apps, but I'll make it type-annotated properly.
     - Methods:
       - `registrar_conexao(session_id, patient_cns, patient_cpf, professional_cpf, ip_address, user_agent, db)`
       - `registrar_desconexao(session_id, ip_address, user_agent, db)`
       - `registrar_aceite_termos(session_id, patient_cns, patient_cpf, db)`
       - `obter_logs(session_id, db)`
       - Helper for secure timestamping (use `datetime.now(timezone.utc)` with precision, maybe hash or sign? The prompt says "carimbo de data/hora seguro". I'll use UTC with timezone, and optionally add a cryptographic hash of the timestamp + session_id for integrity, or just emphasize timezone-aware UTC timestamps. I'll stick to standard secure timestamping practices: UTC, high precision, immutable record).
   - **SUS/APS Standards:** Include CIAP-2, CID-10, SOAP, CNS/CPF in the model/Pydantic schemas.
   - **Pytest:** Provide a complete test file `tests/test_auditoria_telemedicina.py` that covers all repository methods, uses pytest, async fixtures, and validates the requirements.

4.  **Draft - Code Structure (Mental Refinement):**
   *File 1: `backend/app/repositories/auditoria_telemedicina.py`*
   - Imports: `datetime`, `uuid`, `enum`, `json`, `sqlalchemy`, `pydantic`, `typing`
   - Define `EventType` enum: CONNECTION, DISCONNECTION, CONSENT_ACCEPTED, SOAP_NOTE, etc.
   - Define SQLAlchemy model `TelemedicinaAuditoriaLog`
   - Define Pydantic schemas `AuditoriaEventInput`, `AuditoriaEventOutput`
   - Define `AuditoriaTelemedicinaRepository` class
     - `__init__(self, session: AsyncSession)`
     - `async def registrar_evento(self, event_type: EventType, ...)`
     - `async def registrar_conexao(self, ...)`
     - `async def registrar_desconexao(self, ...)`
     - `async def registrar_aceite_termos(self, ...)`
     - `async def obter_logs(self, session_id: str) -> list`
     - Secure timestamp: `datetime.now(timezone.utc).replace(microsecond=0)` or keep microseconds for precision. I'll use `datetime.now(timezone.utc)` and add a note about secure timestamping (NTP sync, UTC, immutable).
   *File 2: `tests/test_auditoria_telemedicina.py`*
   - Imports: `pytest`, `pytest_asyncio`, `sqlalchemy`, `async_session_factory`
   - Fixtures: `db_session`, `repo`
   - Tests: `test_registrar_conexao`, `test_registrar_desconexao`, `test_registrar_aceite_termos`, `test_obter_logs`, `test_validacao_pydantic`, `test_carimbo_temporal_seguro`
   - Use `pytest-asyncio` for async tests.

5.  **Detailed Implementation (Mental to Code):**
   Let's write out the code carefully, ensuring strict typing, Pydantic v2, SQLAlchemy 2.0, and SUS/APS compliance.

   *SQLAlchemy Model:*
   ```python
   from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, Enum as SAEnum, ForeignKey
   from sqlalchemy.orm import DeclarativeBase
   from datetime import datetime, timezone
   import uuid

   class Base(DeclarativeBase):
       pass

   class TelemedicinaAuditoriaLog(Base):
       __tablename__ = "auditoria_telemedicina"

       id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
       session_id = Column(String(36), nullable=False, index=True)
       patient_cns = Column(String(15), nullable=True) # CNS format
       patient_cpf = Column(String(14), nullable=True) # CPF format
       professional_cpf = Column(String(14), nullable=True)
       event_type = Column(SAEnum("CONEXAO", "DESCONECAO", "ACEITE_TERMOS", "SOAP", name="event_type_enum"), nullable=False)
       event_timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
       ip_address = Column(String(45), nullable=True)
       user_agent = Column(Text, nullable=True)
       consent_accepted = Column(Boolean, default=False)
       consent_timestamp = Column(DateTime(timezone=True), nullable=True)
       soap_notes = Column(Text, nullable=True)
       ciap2_codes = Column(JSON, nullable=True)
       cid10_codes = Column(JSON, nullable=True)
       metadata_json = Column(JSON, nullable=True)
       created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
       updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
   ```
   *Pydantic Models:*
   ```python
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from datetime import datetime

   class EventType(str, Enum):
       CONEXAO = "CONEXAO"
       DESCONECAO = "DESCONECAO"
       ACEITE_TERMOS = "ACEITE_TERMOS"
       SOAP = "SOAP"

   class AuditoriaEventInput(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True)
       session_id: str = Field(..., min_length=1, max_length=36)
       patient_cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       patient_cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       professional_cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       event_type: EventType
       ip_address: Optional[str] = None
       user_agent: Optional[str] = None
       consent_accepted: Optional[bool] = None
       soap_notes: Optional[str] = None
       ciap2_codes: Optional[List[str]] = None
       cid10_codes: Optional[List[str]] = None
       metadata: Optional[Dict[str, Any]] = None

       @field_validator("patient_cpf", "professional_cpf")
       @classmethod
       def validate_cpf(cls, v):
           if v is not None:
               # Basic CPF validation logic could go here, but pattern is enough for now
               pass
           return v
   ```
   *Repository:*
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select
   from typing import List
   import hashlib
   import hmac

   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def _secure_timestamp(self) -> datetime:
           # Secure timestamping: UTC, high precision, immutable record
           return datetime.now(timezone.utc).replace(microsecond=0)

       async def registrar_conexao(self, input_data: AuditoriaEventInput) -> None:
           input_data.event_type = EventType.CONEXAO
           await self._registrar_evento(input_data)

       async def registrar_desconexao(self, input_data: AuditoriaEventInput) -> None:
           input_data.event_type = EventType.DESCONECAO
           await self._registrar_evento(input_data)

       async def registrar_aceite_termos(self, input_data: AuditoriaEventInput) -> None:
           input_data.event_type = EventType.ACEITE_TERMOS
           input_data.consent_accepted = True
           input_data.consent_timestamp = await self._secure_timestamp()
           await self._registrar_evento(input_data)

       async def _registrar_evento(self, input_data: AuditoriaEventInput) -> None:
           ts = await self._secure_timestamp()
           # Create integrity hash for secure timestamping
           integrity_hash = hmac.new(
               b"secret_key_placeholder", # In prod, use env var or KMS
               f"{input_data.session_id}{ts.isoformat()}".encode(),
               hashlib.sha256
           ).hexdigest()

           log = TelemedicinaAuditoriaLog(
               session_id=input_data.session_id,
               patient_cns=input_data.patient_cns,
               patient_cpf=input_data.patient_cpf,
               professional_cpf=input_data.professional_cpf,
               event_type=input_data.event_type.value,
               event_timestamp=ts,
               ip_address=input_data.ip_address,
               user_agent=input_data.user_agent,
               consent_accepted=input_data.consent_accepted,
               consent_timestamp=input_data.consent_timestamp,
               soap_notes=input_data.soap_notes,
               ciap2_codes=input_data.ciap2_codes,
               cid10_codes=input_data.cid10_codes,
               metadata_json=input_data.metadata,
               created_at=ts,
               updated_at=ts
           )
           # Add integrity hash to metadata or a dedicated column if needed.
           # For simplicity, I'll store it in metadata_json or a dedicated field.
           # Let's add a dedicated column to the model for integrity_hash.
           log.integrity_hash = integrity_hash

           self.session.add(log)
           await self.session.flush()

       async def obter_logs(self, session_id: str) -> List[TelemedicinaAuditoriaLog]:
           stmt = select(TelemedicinaAuditoriaLog).where(TelemedicinaAuditoriaLog.session_id == session_id).order_by(TelemedicinaAuditoriaLog.event_timestamp)
           result = await self.session.execute(stmt)
           return list(result.scalars().all())
   ```
   Wait, I need to add `integrity_hash` to the SQLAlchemy model. Let's update the model definition.
   Also, I should make sure the code is complete and self-contained. I'll combine everything into the requested file path.

   Let's refine the SQLAlchemy model to include `integrity_hash`:
   ```python
   integrity_hash = Column(String(64), nullable=False)
   ```

   Now, Pytest file. I'll write a comprehensive test suite using `pytest-asyncio`, `sqlalchemy.ext.asyncio`, and `aiosqlite` for in-memory testing.

   *Test Structure:*
   - Fixtures: `async_engine`, `async_session_factory`, `db_session`, `repo`
   - Tests:
     - `test_registrar_conexao`
     - `test_registrar_desconexao`
     - `test_registrar_aceite_termos`
     - `test_obter_logs`
     - `test_validacao_pydantic_cpf_cns`
     - `test_carimbo_temporal_utc`
   - Use `pytest.mark.asyncio`
   - Ensure strict typing and coverage.

   Let's draft the test file carefully.

   ```python
   import pytest
   import pytest_asyncio
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   from sqlalchemy.pool import StaticPool
   from datetime import datetime, timezone
   from backend.app.repositories.auditoria_telemedicina import (
       Base,
       TelemedicinaAuditoriaLog,
       AuditoriaTelemedicinaRepository,
       AuditoriaEventInput,
       EventType
   )

   @pytest_asyncio.fixture
   async def async_engine():
       engine = create_async_engine(
           "sqlite+aiosqlite:///:memory:",
           connect_args={"check_same_thread": False},
           poolclass=StaticPool
       )
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
       yield engine
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.drop_all)
       await engine.dispose()

   @pytest_asyncio.fixture
   async def async_session_factory(async_engine):
       return async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

   @pytest_asyncio.fixture
   async def db_session(async_session_factory):
       async with async_session_factory() as session:
           yield session

   @pytest_asyncio.fixture
   async def repo(db_session):
       return AuditoriaTelemedicinaRepository(session=db_session)

   @pytest.mark.asyncio
   async def test_registrar_conexao(repo):
       input_data = AuditoriaEventInput(
           session_id="sess-123",
           patient_cns="123456789012345",
           patient_cpf="12345678901",
           professional_cpf="98765432100",
           event_type=EventType.CONEXAO,
           ip_address="192.168.1.1",
           user_agent="Mozilla/5.0"
       )
       await repo.registrar_conexao(input_data)
       logs = await repo.obter_logs("sess-123")
       assert len(logs) == 1
       assert logs[0].event_type == "CONEXAO"
       assert logs[0].patient_cns == "123456789012345"
       assert logs[0].event_timestamp.tzinfo is not None

   @pytest.mark.asyncio
   async def test_registrar_desconexao(repo):
       input_data = AuditoriaEventInput(
           session_id="sess-456",
           event_type=EventType.DESCONECAO,
           ip_address="10.0.0.1"
       )
       await repo.registrar_desconexao(input_data)
       logs = await repo.obter_logs("sess-456")
       assert len(logs) == 1
       assert logs[0].event_type == "DESCONECAO"

   @pytest.mark.asyncio
   async def test_registrar_aceite_termos(repo):
       input_data = AuditoriaEventInput(
           session_id="sess-789",
           patient_cpf="11122233344",
           event_type=EventType.ACEITE_TERMOS
       )
       await repo.registrar_aceite_termos(input_data)
       logs = await repo.obter_logs("sess-789")
       assert len(logs) == 1
       assert logs[0].consent_accepted is True
       assert logs[0].consent_timestamp is not None
       assert logs[0].consent_timestamp.tzinfo is not None

   @pytest.mark.asyncio
   async def test_obter_logs_ordenacao(repo):
       for i in range(3):
           input_data = AuditoriaEventInput(
               session_id="sess-ord",
               event_type=EventType.CONEXAO,
               ip_address=f"192.168.1.{i}"
           )
           await repo.registrar_conexao(input_data)
       logs = await repo.obter_logs("sess-ord")
       assert len(logs) == 3
       # Verify order by timestamp
       for i in range(len(logs) - 1):
           assert logs[i].event_timestamp <= logs[i+1].event_timestamp

   @pytest.mark.asyncio