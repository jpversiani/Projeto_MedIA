Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Implement `backend/app/repositories/auditoria_telemedicina.py` with a class `AuditoriaTelemedicinaRepository` for logging teleconsultation events (connection, disconnection, patient confidentiality agreement acceptance, secure timestamping) using SQLAlchemy 2.0.
   - **Guidelines:** Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), full compliance with automated pytest coverage.
   - **Output Requirement:** Provide complete, executable code. Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/auditoria_telemedicina.py`
   - **Class:** `AuditoriaTelemedicinaRepository`
   - **Features:**
     - Log connection events
     - Log disconnection events
     - Log patient confidentiality agreement acceptance (LGPD/CFM)
     - Secure timestamping
     - Use SQLAlchemy 2.0 (async or sync? I'll assume async as it's common in modern FastAPI apps, but I'll make it compatible with both or explicitly use `sqlalchemy.orm` with `AsyncSession` or `Session`. I'll stick to `AsyncSession` for modern stack, but will provide clear type hints and async/await patterns. Actually, I'll use `Session` for simplicity unless specified, but I'll note it. I'll go with `AsyncSession` as it's standard for FastAPI, but I'll make it work with standard SQLAlchemy 2.0 patterns.)
     - Pydantic v2 models for data validation
     - SUS/APS standards: CIAP-2, CID-10, SOAP, CNS/CPF
     - Pytest coverage (I'll provide the repository code, but the prompt says "Manter conformidade total e cobertura de testes automatizados com pytest." I should probably include the test file as well, or at least structure the code to be easily testable. I'll provide both the repository and a comprehensive test file to satisfy the "tester" role and coverage requirement.)
   - **Architecture:** Python 3.12, strict typing, Pydantic v2, SQLAlchemy 2.0.

3.  **Design the Repository:**
   - **Database Models (SQLAlchemy 2.0):**
     - `TelemedicinaAuditoriaEvent` table
     - Fields: id, session_id, patient_cns, patient_cpf, doctor_crm, event_type (connection, disconnection, agreement_accepted), event_data (JSON), timestamp (UTC, secure), created_at, updated_at
     - Enum for event types
     - Indexes for performance
   - **Pydantic Models:**
     - `TelemedicinaAuditoriaEventCreate` (for input)
     - `TelemedicinaAuditoriaEventRead` (for output)
   - **Repository Class:**
     - `__init__(self, session: AsyncSession)`
     - `log_connection(self, ...)`
     - `log_disconnection(self, ...)`
     - `log_agreement_acceptance(self, ...)`
     - `get_events(self, ...)`
     - Use `datetime.now(timezone.utc)` for secure timestamps
     - Use `uuid` for session IDs
     - Strict typing throughout

4.  **Draft the Code (Mental Refinement):**
   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from sqlalchemy import String, Text, DateTime, Enum as SAEnum, JSON, Index
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   from sqlalchemy.ext.asyncio import AsyncSession

   # --- SQLAlchemy Models ---
   class Base(DeclarativeBase):
       pass

   class EventType(str, Enum):
       CONNECTION = "connection"
       DISCONNECTION = "disconnection"
       AGREEMENT_ACCEPTANCE = "agreement_acceptance"

   class TelemedicinaAuditoriaEvent(Base):
       __tablename__ = "telemedicina_auditoria_events"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       session_id: Mapped[str] = mapped_column(String(36), index=True)
       patient_cns: Mapped[Optional[str]] = mapped_column(String(15), index=True)
       patient_cpf: Mapped[Optional[str]] = mapped_column(String(14), index=True)
       doctor_crm: Mapped[Optional[str]] = mapped_column(String(20))
       event_type: Mapped[EventType] = mapped_column(SAEnum(EventType), nullable=False)
       event_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
       timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

       __table_args__ = (
           Index("ix_auditoria_session_timestamp", "session_id", "timestamp"),
           Index("ix_auditoria_patient_cns", "patient_cns"),
           Index("ix_auditoria_patient_cpf", "patient_cpf"),
       )

   # --- Pydantic Models ---
   class AuditoriaEventBase(BaseModel):
       session_id: str = Field(..., pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
       patient_cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       patient_cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       doctor_crm: Optional[str] = None
       event_data: Dict[str, Any] = Field(default_factory=dict)

   class AuditoriaEventCreate(AuditoriaEventBase):
       event_type: EventType

   class AuditoriaEventRead(AuditoriaEventBase):
       id: uuid.UUID
       event_type: EventType
       timestamp: datetime
       created_at: datetime
       updated_at: datetime

       model_config = ConfigDict(from_attributes=True)

   # --- Repository ---
   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def log_connection(self, session_id: str, patient_cns: Optional[str] = None, patient_cpf: Optional[str] = None, doctor_crm: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> AuditoriaEventRead:
           event = TelemedicinaAuditoriaEvent(
               session_id=session_id,
               patient_cns=patient_cns,
               patient_cpf=patient_cpf,
               doctor_crm=doctor_crm,
               event_type=EventType.CONNECTION,
               event_data=metadata or {}
           )
           await self._persist(event)
           return self._to_pydantic(event)

       async def log_disconnection(self, session_id: str, reason: Optional[str] = None, duration_seconds: Optional[int] = None) -> AuditoriaEventRead:
           event = TelemedicinaAuditoriaEvent(
               session_id=session_id,
               event_type=EventType.DISCONNECTION,
               event_data={"reason": reason, "duration_seconds": duration_seconds}
           )
           await self._persist(event)
           return self._to_pydantic(event)

       async def log_agreement_acceptance(self, session_id: str, patient_cns: Optional[str] = None, patient_cpf: Optional[str] = None, method: str = "LGPD_CFM", version: str = "1.0") -> AuditoriaEventRead:
           event = TelemedicinaAuditoriaEvent(
               session_id=session_id,
               patient_cns=patient_cns,
               patient_cpf=patient_cpf,
               event_type=EventType.AGREEMENT_ACCEPTANCE,
               event_data={"method": method, "version": version, "accepted_at": datetime.now(timezone.utc).isoformat()}
           )
           await self._persist(event)
           return self._to_pydantic(event)

       async def _persist(self, event: TelemedicinaAuditoriaEvent):
           self.session.add(event)
           await self.session.commit()
           await self.session.refresh(event)

       def _to_pydantic(self, event: TelemedicinaAuditoriaEvent) -> AuditoriaEventRead:
           return AuditoriaEventRead(
               id=event.id,
               session_id=event.session_id,
               patient_cns=event.patient_cns,
               patient_cpf=event.patient_cpf,
               doctor_crm=event.doctor_crm,
               event_type=event.event_type,
               event_data=event.event_data,
               timestamp=event.timestamp,
               created_at=event.created_at,
               updated_at=event.updated_at
           )

       async def get_events_by_session(self, session_id: str) -> List[AuditoriaEventRead]:
           from sqlalchemy import select
           stmt = select(TelemedicinaAuditoriaEvent).where(TelemedicinaAuditoriaEvent.session_id == session_id).order_by(TelemedicinaAuditoriaEvent.timestamp)
           result = await self.session.execute(stmt)
           events = result.scalars().all()
           return [self._to_pydantic(e) for e in events]
   ```

5.  **Check Against Requirements:**
   - ✅ File path specified
   - ✅ Class `AuditoriaTelemedicinaRepository`
   - ✅ Logs connection, disconnection, agreement acceptance
   - ✅ Secure timestamping (UTC, timezone-aware)
   - ✅ SQLAlchemy 2.0 (DeclarativeBase, mapped_column, async)
   - ✅ Pydantic v2 (BaseModel, ConfigDict, from_attributes, Field validation)
   - ✅ Python 3.12 strict typing
   - ✅ SUS/APS standards mentioned in event_data or fields? I should explicitly add fields for CIAP-2, CID-10, SOAP method, CNS/CPF as per guidelines. The prompt says "Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF)." I'll add these to the event_data or as explicit columns if they are core to the audit. Actually, audit logs usually capture the consultation context. I'll add `ciap2_code`, `cid10_code`, `soap_method` to the model or event_data. Let's add them as optional columns for better indexing/querying, or keep them in `event_data` but validate them. I'll add them as explicit fields to align with SUS/APS standards strictly.
   - ✅ Pytest coverage: I need to provide the test file as well to satisfy "Manter conformidade total e cobertura de testes automatizados com pytest."

   Let's refine the model to include SUS/APS fields explicitly:
   ```python
   ciap2_code: Mapped[Optional[str]] = mapped_column(String(10))
   cid10_code: Mapped[Optional[str]] = mapped_column(String(10))
   soap_method: Mapped[Optional[str]] = mapped_column(String(50))
   ```
   And update Pydantic models accordingly.

   Also, secure timestamping: I'll use `datetime.now(timezone.utc)` and ensure it's timezone-aware. I'll add a validator or just rely on SQLAlchemy's default. I'll make it explicit.

   Let's adjust the repository to include these fields in the log methods or as part of the consultation context. Actually, the audit event is for connection/disconnection/agreement. The consultation details (CIAP-2, CID-10, SOAP) might be logged in a separate consultation event, but the prompt says "Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF)." I'll include them in the `event_data` or as explicit columns. I'll add them as explicit columns for strict compliance.

   Revised Model:
   ```python
   class TelemedicinaAuditoriaEvent(Base):
       __tablename__ = "telemedicina_auditoria_events"
       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       session_id: Mapped[str] = mapped_column(String(36), index=True)
       patient_cns: Mapped[Optional[str]] = mapped_column(String(15), index=True)
       patient_cpf: Mapped[Optional[str]] = mapped_column(String(14), index=True)
       doctor_crm: Mapped[Optional[str]] = mapped_column(String(20))
       event_type: Mapped[EventType] = mapped_column(SAEnum(EventType), nullable=False)
       ciap2_code: Mapped[Optional[str]] = mapped_column(String(10))
       cid10_code: Mapped[Optional[str]] = mapped_column(String(10))
       soap_method: Mapped[Optional[str]] = mapped_column(String(50))
       event_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
       timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
       # ... indexes
   ```

   I'll update the Pydantic models and repository methods to accept these.

   Now, for Pytest coverage: I'll create `tests/test_auditoria_telemedicina.py` with comprehensive tests using `pytest-asyncio`, `pytest-cov`, and mocking/fixture for `AsyncSession`. I'll use `pytest-asyncio` and `sqlalchemy.ext.asyncio` testing utilities or mock the session. Since it's a repository, I'll use `pytest-asyncio` and a real SQLite async database via `pytest-asyncio` and `sqlalchemy.ext.asyncio.create_async_engine` with `async_sessionmaker` for integration tests, or mock for unit tests. I'll provide a robust test suite.

   Let's structure the test file:
   - Fixtures for async session
   - Tests for each log method
   - Tests for validation (Pydantic)
   - Tests for timestamp security (UTC)
   - Tests for SUS/APS fields
   - Coverage markers

   I'll write the code carefully.

6.  **Code Construction (Mental to Text):**
   I'll draft the repository file first, ensuring all guidelines are met.
   Then I'll draft the test file.
   I'll make sure type hints are strict, Pydantic v2 is used correctly, SQLAlchemy 2.0 is modern, and Python 3.12 features are utilized (like `match` if needed, but not necessary here).

   *Self-Correction/Refinement during drafting:*
   - SQLAlchemy 2.0 uses `Mapped` and `mapped_column`. I'll use them.
   - Pydantic v2 uses `model_config = ConfigDict(from_attributes=True)`.
   - Secure timestamp: I'll explicitly set `server_default` and `default` to `func.now()` or lambda. I'll stick to lambda for Python-side control, but add `server_default=func.now()` for DB consistency.
   - I'll add `import sqlalchemy as sa` for `func`.
   - For the repository, I'll make methods `async` as it's standard for SQLAlchemy 2.0 async.
   - I'll ensure strict typing: `from typing import Optional, List, Dict, Any, Union`
   - I'll add docstrings and type hints.
   - I'll include the test file to satisfy the "tester" role and coverage requirement.

   Let's write it out carefully.

   **Repository Structure:**
   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from sqlalchemy import String, Text, DateTime, Enum as SAEnum, JSON, Index, func
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   from sqlalchemy.ext.asyncio import AsyncSession

   class Base(DeclarativeBase):
       pass

   class EventType(str, Enum):
       CONNECTION = "connection"
       DISCONNECTION = "disconnection"
       AGREEMENT_ACCEPTANCE = "agreement_acceptance"

   class TelemedicinaAuditoriaEvent(Base):
       __tablename__ = "telemedicina_auditoria_events"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       session_id: Mapped[str] = mapped_column(String(36), index=True)
       patient_cns: Mapped[Optional[str]] = mapped_column(String(15), index=True)
       patient_cpf: Mapped[Optional[str]] = mapped_column(String(14), index=True)
       doctor_crm: Mapped[Optional[str]] = mapped_column(String(20))
       event_type: Mapped[EventType] = mapped_column(SAEnum(EventType), nullable=False)
       ciap2_code: Mapped[Optional[str]] = mapped_column(String(10))
       cid10_code: Mapped[Optional[str]] = mapped_column(String(10))
       soap_method: Mapped[Optional[str]] = mapped_column(String(50))
       event_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
       timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime