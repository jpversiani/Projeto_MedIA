Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Implement `backend/app/repositories/auditoria_telemedicina.py` with a class `AuditoriaTelemedicinaRepository` for logging teleconsultation events (connection, disconnection, privacy terms acceptance, secure timestamping) using SQLAlchemy 2.0.
   - **Guidelines:** Python 3.12, strict typing with Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), full compliance with automated pytest coverage.
   - **Output Requirement:** Provide complete, executable code. Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/auditoria_telemedicina.py`
   - **Class:** `AuditoriaTelemedicinaRepository`
   - **Features:**
     - Log connection events
     - Log disconnection events
     - Log privacy terms acceptance (LGPD/CFM)
     - Secure timestamping (UTC, timezone-aware)
     - SQLAlchemy 2.0 ORM/Async? (I'll assume sync for simplicity unless specified, but I'll make it compatible with both or explicitly use sync as it's standard for repositories unless async is requested. I'll stick to sync SQLAlchemy 2.0 for clarity, but note it can be adapted. Actually, modern apps often use async, but I'll provide a robust sync version with clear session management, or better, design it to accept a session dependency.)
     - Pydantic v2 for models/DTOs
     - SUS/APS standards: CIAP-2, CID-10, SOAP, CNS, CPF
     - Pytest coverage (I'll provide the repository code and a comprehensive test file)
   - **Constraints:** Python 3.12, strict typing, SQLAlchemy 2.0, Pydantic v2.

3.  **Design the Repository & Models:**
   - **Database Models (SQLAlchemy 2.0):**
     - `TelemedicinaAuditoriaEvent` table
     - Fields: `id` (UUID), `patient_cns` (str), `patient_cpf` (str), `event_type` (enum: CONNECTION, DISCONNECTION, TERMS_ACCEPTANCE), `event_data` (JSON), `created_at` (datetime, UTC), `updated_at` (datetime, UTC)
     - Need indexes for CNS/CPF and event_type.
   - **Pydantic Models (v2):**
     - `TelemedicinaAuditoriaEventCreate` (for input)
     - `TelemedicinaAuditoriaEventRead` (for output)
   - **Repository Class:**
     - `__init__(self, session: Session)`
     - `log_connection(self, patient_cns: str, patient_cpf: str, metadata: dict) -> TelemedicinaAuditoriaEventRead`
     - `log_disconnection(self, patient_cns: str, patient_cpf: str, metadata: dict) -> TelemedicinaAuditoriaEventRead`
     - `log_terms_acceptance(self, patient_cns: str, patient_cpf: str, terms_version: str, ip_address: str) -> TelemedicinaAuditoriaEventRead`
     - Helper to get secure UTC timestamp.
     - Use SQLAlchemy 2.0 syntax (`select`, `insert`, `update`, `session.execute`, etc.)

4.  **Draft the Code (Mental Refinement):**
   *Imports:* `uuid`, `datetime`, `timezone`, `enum`, `json`, `typing`, `sqlalchemy`, `pydantic`
   *Enums:* `EventType(str, Enum)`
   *Models:*
   ```python
   from pydantic import BaseModel, Field, ConfigDict
   from datetime import datetime
   from typing import Optional
   from enum import Enum

   class EventType(str, Enum):
       CONNECTION = "CONNECTION"
       DISCONNECTION = "DISCONNECTION"
       TERMS_ACCEPTANCE = "TERMS_ACCEPTANCE"

   class AuditoriaEventCreate(BaseModel):
       patient_cns: str = Field(..., pattern=r"^\d{15}$")
       patient_cpf: str = Field(..., pattern=r"^\d{11}$")
       event_type: EventType
       metadata: dict = Field(default_factory=dict)

   class AuditoriaEventRead(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: str
       patient_cns: str
       patient_cpf: str
       event_type: str
       metadata: dict
       created_at: datetime
   ```
   *SQLAlchemy Model:*
   ```python
   from sqlalchemy import Column, String, DateTime, Enum, JSON, Index, func
   from sqlalchemy.orm import DeclarativeBase

   class Base(DeclarativeBase):
       pass

   class TelemedicinaAuditoriaEvent(Base):
       __tablename__ = "telemedicina_auditoria_events"
       id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
       patient_cns = Column(String(15), nullable=False, index=True)
       patient_cpf = Column(String(11), nullable=False, index=True)
       event_type = Column(Enum(EventType), nullable=False)
       metadata = Column(JSON, nullable=False, default=dict)
       created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
       updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
   ```
   *Repository:*
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession # Wait, guidelines don't specify async. I'll use sync Session for simplicity but note it. Actually, I'll use `sqlalchemy.orm.Session` as it's standard.
   from sqlalchemy import select, insert, update
   from datetime import datetime, timezone

   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: Session):
           self.session = session

       def _get_secure_utc_now(self) -> datetime:
           return datetime.now(timezone.utc)

       def log_connection(self, patient_cns: str, patient_cpf: str, metadata: dict) -> AuditoriaEventRead:
           event = TelemedicinaAuditoriaEvent(
               patient_cns=patient_cns,
               patient_cpf=patient_cpf,
               event_type=EventType.CONNECTION,
               metadata=metadata,
               created_at=self._get_secure_utc_now(),
               updated_at=self._get_secure_utc_now()
           )
           self.session.add(event)
           self.session.flush()
           return AuditoriaEventRead.model_validate(event)

       def log_disconnection(self, patient_cns: str, patient_cpf: str, metadata: dict) -> AuditoriaEventRead:
           event = TelemedicinaAuditoriaEvent(
               patient_cns=patient_cns,
               patient_cpf=patient_cpf,
               event_type=EventType.DISCONNECTION,
               metadata=metadata,
               created_at=self._get_secure_utc_now(),
               updated_at=self._get_secure_utc_now()
           )
           self.session.add(event)
           self.session.flush()
           return AuditoriaEventRead.model_validate(event)

       def log_terms_acceptance(self, patient_cns: str, patient_cpf: str, terms_version: str, ip_address: str) -> AuditoriaEventRead:
           metadata = {"terms_version": terms_version, "ip_address": ip_address}
           event = TelemedicinaAuditoriaEvent(
               patient_cns=patient_cns,
               patient_cpf=patient_cpf,
               event_type=EventType.TERMS_ACCEPTANCE,
               metadata=metadata,
               created_at=self._get_secure_utc_now(),
               updated_at=self._get_secure_utc_now()
           )
           self.session.add(event)
           self.session.flush()
           return AuditoriaEventRead.model_validate(event)
   ```
   *Wait*, I need to ensure SQLAlchemy 2.0 best practices. Using `session.add()` and `session.flush()` is fine. I'll add type hints properly. I'll also make the repository accept an async or sync session, but I'll stick to sync for clarity, or better, use `sqlalchemy.orm.Session` as per standard. I'll explicitly type it.

   Let's refine the SQLAlchemy model to be fully compliant with 2.0:
   - Use `Mapped` and `mapped_column` for modern SQLAlchemy 2.0 style.
   - Use `uuid` for primary key.
   - Ensure timezone-aware datetimes.

   *Modern SQLAlchemy 2.0 Model:*
   ```python
   from sqlalchemy import String, DateTime, Enum, JSON, Index, func
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   import uuid
   from datetime import datetime, timezone

   class Base(DeclarativeBase):
       pass

   class TelemedicinaAuditoriaEvent(Base):
       __tablename__ = "telemedicina_auditoria_events"

       id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
       patient_cns: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
       patient_cpf: Mapped[str] = mapped_column(String(11), nullable=False, index=True)
       event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
       metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
   ```

   *Repository with SQLAlchemy 2.0 syntax:*
   I'll use `session.add()` and `session.flush()` as it's standard. I'll also add a method to query by patient for completeness, though not strictly requested, it's good practice. I'll stick to the requested methods.

   Let's ensure Pydantic v2 compatibility: `model_config = ConfigDict(from_attributes=True)` is correct.

   *Pytest Coverage:*
   I need to provide a test file `tests/test_auditoria_telemedicina.py` that covers:
   - Connection logging
   - Disconnection logging
   - Terms acceptance logging
   - Secure timestamp verification (UTC)
   - Data validation (CNS/CPF patterns)
   - SQLAlchemy session mocking or in-memory SQLite
   I'll use `pytest` with `sqlalchemy` in-memory SQLite for testing.

   Structure of test:
   - `@pytest.fixture` for `session`
   - `@pytest.fixture` for `repo`
   - Tests for each method
   - Assertions on UTC timestamps
   - Assertions on DB records

   Let's draft the test file mentally:
   ```python
   import pytest
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from backend.app.repositories.auditoria_telemedicina import (
       Base,
       AuditoriaTelemedicinaRepository,
       EventType,
       AuditoriaEventCreate
   )
   from datetime import datetime, timezone
   import uuid

   @pytest.fixture
   def engine():
       return create_engine("sqlite:///:memory:")

   @pytest.fixture
   def session(engine):
       Base.metadata.create_all(engine)
       SessionLocal = sessionmaker(bind=engine)
       sess = SessionLocal()
       yield sess
       sess.close()

   @pytest.fixture
   def repo(session):
       return AuditoriaTelemedicinaRepository(session)

   def test_log_connection(repo, session):
       event = repo.log_connection("123456789012345", "12345678901", {"consult_id": "abc"})
       assert event.event_type == EventType.CONNECTION
       assert event.created_at.tzinfo == timezone.utc
       # verify in db
       stmt = select(TelemedicinaAuditoriaEvent).where(TelemedicinaAuditoriaEvent.patient_cns == "123456789012345")
       result = session.execute(stmt).scalar_one()
       assert result.event_type == EventType.CONNECTION
   ```
   I need to import `select` and `TelemedicinaAuditoriaEvent` in the test.

   Let's refine the repository code to be production-ready, strictly typed, and compliant with SQLAlchemy 2.0 and Pydantic v2. I'll also add proper docstrings and type hints.

   *Key considerations for SUS/APS standards:*
   - CNS (Cartão Nacional de Saúde) is 15 digits.
   - CPF is 11 digits.
   - I'll add validation in Pydantic for these.
   - I'll mention CIAP-2, CID-10, SOAP in comments/docstrings as context, but the repository focuses on audit logs. The prompt says "Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF)" - this likely means the audit events should support these fields in metadata or be structured to accommodate them. I'll add optional fields for `ciap2_code`, `cid10_code`, `soap_notes` to the metadata or as explicit columns if needed. But keeping it flexible with JSON metadata is better for audit logs. I'll explicitly document that metadata supports these SUS standards.

   Let's structure the repository carefully.

   *File 1: `backend/app/repositories/auditoria_telemedicina.py`*
   - Imports
   - Enums
   - Pydantic Models
   - SQLAlchemy Model
   - Repository Class
   - Helper functions if needed

   *File 2: `tests/test_auditoria_telemedicina.py`*
   - Pytest fixtures
   - Test cases
   - Coverage assertions

   I will write the code now, ensuring strict typing, SQLAlchemy 2.0 syntax (`Mapped`, `mapped_column`), Pydantic v2 (`model_config`, `Field`), and comprehensive tests.

   *Self-Correction/Refinement during thought:*
   - SQLAlchemy 2.0 recommends `mapped_column` but `Column` still works. I'll use `mapped_column` for modern compliance.
   - Pydantic v2: `ConfigDict` is correct. `from_attributes=True` is correct.
   - Timestamps: Must be timezone-aware UTC. I'll enforce this in the repo and validate in tests.
   - CNS/CPF validation: I'll use Pydantic's `field_validator` or regex pattern.
   - I'll make sure the repository doesn't commit automatically, leaving transaction management to the caller (standard practice).
   - I'll add type hints for all methods.
   - I'll ensure the code is executable and follows the exact path requested.

   Let's draft carefully. 
   Structure:
   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   ... code ...
   ```
   ```python
   # Arquivo: tests/test_auditoria_telemedicina.py
   ... code ...
   ```

   I will now generate the response. 
   Checkpoints:
   - Python 3.12 compatible? Yes, uses modern typing.
   - Pydantic v2? Yes.
   - SQLAlchemy 2.0? Yes, uses `Mapped`, `mapped_column`, `session.add`, `session.flush`, `select`.
   - SUS/APS standards? CNS/CPF validation, metadata structure for CIAP-2/CID-10/SOAP documented and supported.
   - Secure timestamp? UTC timezone-aware, enforced.
   - Pytest coverage? Comprehensive tests provided.
   - Complete & executable? Yes.

   One detail: `mapped_column` requires SQLAlchemy >= 2.0.14. I'll assume modern version. I'll also add `__init__.py` if needed, but not required.
   I'll make sure the test uses `pytest` and `sqlalchemy` properly.
   I'll add `field_validator` for CNS/CPF in Pydantic.
   I'll ensure the repository handles the SUS standards gracefully in metadata.

   Let's write it out. 
   *Self-Correction/Verification during drafting:*
   - `mapped_column` syntax: `id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))`
   - Pydantic v2: `from pydantic import BaseModel, Field, field_validator, ConfigDict`
   - Validation: `@field_validator('patient_cns') @classmethod ...`
   - I'll keep it clean.
   - Test: I'll use `pytest` with `caplog` or direct assertions. I'll verify UTC timezone explicitly.
   - I'll add comments explaining SUS/APS integration points.

   All good. Proceeding. 
   Output matches the response. 
   Structure of response:
   - Brief intro
   - Code block 1: Repository
   - Code block 2: Tests
   - Instructions to run
   - Compliance notes.✅
   Ready. 
   *Output Generation* (matches the final response)
   - Checks: Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS, pytest, strict typing, secure timestamps, complete code. All met.✅
   - Path specified correctly.✅
   - Executable.✅
   - Ready. 
   [Proceeds]
Aqui está a implementação completa e executável, seguindo rigorosamente as diretrizes: Python 3.12, tipagem estrita, Pydantic v2, SQLAlchemy 2.0, conformidade SUS/APS e cobertura de testes com pytest.

```python
# Arquivo: backend/app/repositories/auditoria_telemedicina.py
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import String, DateTime, Enum as SAEnum, JSON, Index, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session


# ---------------------------------------------------------------------------
# 1. Modelos de Domínio (Pydantic v2