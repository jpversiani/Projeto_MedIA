Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Implement `backend/app/repositories/auditoria_telemedicina.py` with a class `AuditoriaTelemedicinaRepository` for logging teleconsultation events (connection, disconnection, LGPD/CFM consent acceptance, secure timestamping) using SQLAlchemy 2.0.
   - **Guidelines:** Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), full compliance with automated pytest coverage.
   - **Output Requirement:** Provide complete, executable code for each file, with file path comments/headers.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/auditoria_telemedicina.py`
   - **Class:** `AuditoriaTelemedicinaRepository`
   - **Features:**
     - Log connection events
     - Log disconnection events
     - Log LGPD/CFM consent acceptance
     - Secure timestamping (UTC, timezone-aware)
     - SQLAlchemy 2.0 ORM models & repository pattern
     - Pydantic v2 for data validation/serialization
     - SUS/APS standards: CIAP-2, CID-10, SOAP, CNS/CPF
     - Type hints (Python 3.12)
     - Pytest coverage (I'll provide the test file as well, as requested "cobertura de testes automatizados com pytest")
   - **Architecture/Standards:** Follow typical MedIA project structure (though I'll focus on the requested file). I'll assume a standard FastAPI/SQLAlchemy setup context.

3.  **Design the SQLAlchemy Model:**
   Need a model for audit logs. Let's call it `TelemedicinaAuditoriaLog`.
   Fields:
   - `id`: UUID
   - `session_id`: str (teleconsultation session)
   - `patient_cns`: str (CNS)
   - `patient_cpf`: str (CPF)
   - `event_type`: str (CONNECTION, DISCONNECTION, CONSENT_ACCEPTED, etc.)
   - `event_data`: JSON (for flexible metadata like SOAP notes, CIAP-2, CID-10, timestamps, etc.)
   - `created_at`: datetime (UTC, timezone-aware)
   - `updated_at`: datetime (UTC)
   - `ip_address`: str (optional but good for audit)
   - `user_role`: str (patient, doctor, system)

   Let's refine based on SUS/APS standards:
   - `ciap2_codes`: JSON array (CIAP-2 codes)
   - `cid10_codes`: JSON array (CID-10 codes)
   - `soap_note`: JSON or text (SOAP method)
   - `consent_status`: bool or enum
   - `timestamp_utc`: datetime (secure)

   Actually, SQLAlchemy 2.0 recommends using `JSON` or `JSONB` for flexible data. I'll use `JSON` for `metadata` and specific columns for key audit fields.

   Model definition:
   ```python
   from sqlalchemy import String, DateTime, Boolean, Enum, JSON, ForeignKey
   from sqlalchemy.dialects.postgresql import UUID, JSONB
   from sqlalchemy.orm import Mapped, mapped_column, relationship
   from datetime import datetime, timezone
   import uuid

   class TelemedicinaAuditoriaLog(Base):
       __tablename__ = "telemedicina_auditoria_logs"

       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
       patient_cns: Mapped[str] = mapped_column(String(15), nullable=True, index=True)
       patient_cpf: Mapped[str] = mapped_column(String(14), nullable=True, index=True)
       event_type: Mapped[str] = mapped_column(Enum("CONNECTION", "DISCONNECTION", "CONSENT_ACCEPTED", "SOAP_NOTE_SAVED", "CIAP2_UPDATED", "CID10_UPDATED", name="event_type_enum"), nullable=False)
       metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
       ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
       user_role: Mapped[str] = mapped_column(String(20), nullable=False)
   ```

4.  **Design Pydantic Schemas:**
   Need Pydantic v2 models for request/response validation.
   - `AuditoriaTelemedicinaCreateSchema`
   - `AuditoriaTelemedicinaReadSchema`
   - Enums for event types

   ```python
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from enum import Enum
   from datetime import datetime
   from typing import Optional, Dict, Any
   import uuid

   class EventType(str, Enum):
       CONNECTION = "CONNECTION"
       DISCONNECTION = "DISCONNECTION"
       CONSENT_ACCEPTED = "CONSENT_ACCEPTED"
       SOAP_NOTE_SAVED = "SOAP_NOTE_SAVED"
       CIAP2_UPDATED = "CIAP2_UPDATED"
       CID10_UPDATED = "CID10_UPDATED"

   class AuditoriaTelemedicinaCreateSchema(BaseModel):
       session_id: str = Field(..., min_length=1, max_length=36)
       patient_cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       patient_cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       event_type: EventType
       metadata: Dict[str, Any] = Field(default_factory=dict)
       ip_address: Optional[str] = None
       user_role: str = Field(..., pattern=r"^(patient|doctor|system)$")

       model_config = ConfigDict(from_attributes=True)

   class AuditoriaTelemedicinaReadSchema(AuditoriaTelemedicinaCreateSchema):
       id: uuid.UUID
       created_at: datetime
       updated_at: datetime

       model_config = ConfigDict(from_attributes=True)
   ```

5.  **Design Repository Class:**
   `AuditoriaTelemedicinaRepository` using SQLAlchemy 2.0 async/sync? I'll assume async as it's modern, but I'll make it compatible with standard SQLAlchemy 2.0 patterns. I'll use `AsyncSession` for modern FastAPI apps, but I'll write it in a way that's clear. Actually, I'll stick to synchronous for simplicity unless specified, but async is better. I'll use `Session` as a dependency or pass it in. I'll design it to accept a `Session` instance.

   Methods:
   - `create_log(session: Session, data: AuditoriaTelemedicinaCreateSchema) -> AuditoriaTelemedicinaReadSchema`
   - `get_logs_by_session(session: Session, session_id: str) -> list[AuditoriaTelemedicinaReadSchema]`
   - `get_logs_by_patient(session: Session, cns: str | None, cpf: str | None) -> list[AuditoriaTelemedicinaReadSchema]`
   - `record_consent(session: Session, session_id: str, patient_cns: str, patient_cpf: str, ip_address: str | None) -> AuditoriaTelemedicinaReadSchema`
   - `record_connection(session: Session, session_id: str, patient_cns: str, patient_cpf: str, ip_address: str | None) -> AuditoriaTelemedicinaReadSchema`
   - `record_disconnection(session: Session, session_id: str, ip_address: str | None) -> AuditoriaTelemedicinaReadSchema`
   - `update_soap_ciap_cid(session: Session, session_id: str, soap: dict, ciap2: list[str], cid10: list[str]) -> AuditoriaTelemedicinaReadSchema`

   I'll implement secure timestamping explicitly using `datetime.now(timezone.utc)`.

   Repository implementation:
   ```python
   from sqlalchemy import select, update
   from sqlalchemy.orm import Session
   from datetime import datetime, timezone
   from typing import Optional, List
   import uuid

   class AuditoriaTelemedicinaRepository:
       def __init__(self, db_session: Session):
           self.db_session = db_session

       def _secure_timestamp(self) -> datetime:
           return datetime.now(timezone.utc)

       def create_log(self, data: AuditoriaTelemedicinaCreateSchema) -> AuditoriaTelemedicinaReadSchema:
           now = self._secure_timestamp()
           log = TelemedicinaAuditoriaLog(
               session_id=data.session_id,
               patient_cns=data.patient_cns,
               patient_cpf=data.patient_cpf,
               event_type=data.event_type.value,
               metadata=data.metadata,
               created_at=now,
               updated_at=now,
               ip_address=data.ip_address,
               user_role=data.user_role
           )
           self.db_session.add(log)
           self.db_session.flush()
           self.db_session.refresh(log)
           return AuditoriaTelemedicinaReadSchema.model_validate(log)

       # ... other methods ...
   ```

   I need to make sure the repository methods are robust and follow SQLAlchemy 2.0 best practices. I'll add methods for specific SUS/APS standards.

6.  **Design Pytest Tests:**
   Need comprehensive tests covering:
   - Connection/Disconnection logging
   - Consent acceptance (LGPD/CFM)
   - SOAP/CIAP-2/CID-10 updates
   - Secure timestamping (UTC)
   - Validation errors (Pydantic)
   - DB operations (using pytest-mock or testcontainers/fixtures)
   I'll use `pytest` with `sqlalchemy` in-memory SQLite for testing, or mock the session. I'll provide a complete test file `tests/test_auditoria_telemedicina.py`.

   Test structure:
   - `@pytest.fixture` for db session
   - Test cases for each repository method
   - Test Pydantic validation
   - Test timestamp timezone
   - Test SUS/APS fields

7.  **Refine & Assemble Code:**
   I'll structure the response with two files:
   - `backend/app/repositories/auditoria_telemedicina.py`
   - `tests/test_auditoria_telemedicina.py`

   Let's carefully write the repository file with all imports, models, schemas, and repository class. I'll ensure it's self-contained but follows the prompt's structure.

   *Self-Correction/Verification during thought:*
   - The prompt says "implemente backend/app/repositories/auditoria_telemedicina.py com a classe AuditoriaTelemedicinaRepository". It doesn't explicitly ask for the model/schema files, but I should include them in the same file or assume they exist. I'll put everything in one file for completeness, or clearly separate them with comments. I'll put the SQLAlchemy model and Pydantic schemas in the same file for simplicity, as it's a single repository file request.
   - SQLAlchemy 2.0 uses `Mapped` and `mapped_column`. I'll use that.
   - Pydantic v2 uses `model_config = ConfigDict(from_attributes=True)`.
   - Secure timestamp: `datetime.now(timezone.utc)` is standard. I'll add a comment about cryptographic signing if needed, but UTC is the baseline. I'll stick to UTC with timezone awareness.
   - SUS/APS: CIAP-2, CID-10, SOAP, CNS/CPF. I'll ensure these are in the metadata or specific columns.
   - Type hints: Python 3.12 compatible (`dict[str, Any]`, `list[str]`, etc.)
   - I'll add comprehensive pytest tests.

   Let's draft the code carefully.

   **File 1: `backend/app/repositories/auditoria_telemedicina.py`**
   - Imports
   - Enums
   - Pydantic Schemas
   - SQLAlchemy Model
   - Repository Class
   - All with strict typing and SQLAlchemy 2.0 patterns.

   **File 2: `tests/test_auditoria_telemedicina.py`**
   - Fixtures for DB
   - Tests for each method
   - Validation tests
   - Timestamp tests
   - Coverage focused.

   I'll write it out now, ensuring all constraints are met.
   *Checkpoints:*
   - Python 3.12 strict typing? Yes.
   - Pydantic v2? Yes.
   - SQLAlchemy 2.0? Yes.
   - SUS/APS standards? Yes (CIAP-2, CID-10, SOAP, CNS/CPF in schema/metadata).
   - Secure timestamp? Yes, UTC timezone-aware.
   - Pytest coverage? Yes, comprehensive tests provided.
   - File path comments? Yes.

   One detail: The prompt says "carimbo de data/hora seguro". In cybersecurity, "secure timestamp" often implies TSP (RFC 3161) or at least UTC with integrity. I'll implement UTC with timezone awareness and add a comment about TSP integration if needed, but for SQLAlchemy, `datetime.now(timezone.utc)` is standard. I'll also add a `checksum` or `signature` field if needed, but that might overcomplicate. I'll stick to UTC + `updated_at` tracking + metadata integrity. I'll explicitly mention UTC compliance and add a `verified_at` field if needed, but I'll keep it practical.

   I'll structure the repository to accept `Session` and provide methods that align with the task.

   Let's write it out. 
   I'll make sure the code is production-ready, follows PEP 8, uses type hints correctly, and includes the test file.
   I'll use `sqlalchemy.orm.Mapped` and `mapped_column` correctly.
   I'll use `pydantic.Field` with patterns for CNS/CPF.
   I'll ensure the repository methods are async-friendly or sync, I'll stick to sync for simplicity but note it's compatible with async. Actually, I'll use `Session` as a parameter.

   Draft structure:
   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   from __future__ import annotations
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, Dict, Any, List
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from sqlalchemy import String, DateTime, JSON, Enum as SAEnum
   from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, Session
   import re

   class Base(DeclarativeBase):
       pass

   class EventType(str, Enum):
       CONNECTION = "CONNECTION"
       DISCONNECTION = "DISCONNECTION"
       CONSENT_ACCEPTED = "CONSENT_ACCEPTED"
       SOAP_NOTE_SAVED = "SOAP_NOTE_SAVED"
       CIAP2_UPDATED = "CIAP2_UPDATED"
       CID10_UPDATED = "CID10_UPDATED"

   class AuditoriaTelemedicinaCreateSchema(BaseModel):
       session_id: str = Field(..., min_length=1, max_length=36)
       patient_cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       patient_cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       event_type: EventType
       metadata: Dict[str, Any] = Field(default_factory=dict)
       ip_address: Optional[str] = None
       user_role: str = Field(..., pattern=r"^(patient|doctor|system)$")
       model_config = ConfigDict(from_attributes=True)

   class AuditoriaTelemedicinaReadSchema(AuditoriaTelemedicinaCreateSchema):
       id: uuid.UUID
       created_at: datetime
       updated_at: datetime
       model_config = ConfigDict(from_attributes=True)

   class TelemedicinaAuditoriaLog(Base):
       __tablename__ = "telemedicina_auditoria_logs"
       id: Mapped[uuid.UUID] = mapped_column(PGGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
       patient_cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True, index=True)
       patient_cpf: Mapped[Optional[str]] = mapped_column(String(14), nullable=True, index=True)
       event_type: Mapped[str] = mapped_column(SAEnum(EventType, name="event_type_enum"), nullable=False)
       metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
       ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
       user_role: Mapped[str] = mapped_column(String(20), nullable=False)

   class AuditoriaTelemedicinaRepository:
       def __init__(self, db_session: Session):
           self.db_session = db_session

       def _secure_timestamp(self) -> datetime:
           return datetime.now(timezone.utc)

       def create_log(self, data: AuditoriaTelemedicinaCreateSchema) -> AuditoriaTelemedicinaReadSchema:
           now = self._secure_timestamp()
           log = TelemedicinaAuditoriaLog(
               session_id=data.session_id,
               patient_cns=data.patient_cns,
               patient_cpf=data.patient_cpf,
               event_type=data.event_type.value,
               metadata=data.metadata,
               created_at=now,
               updated_at=now,
               ip_address=data.ip_address,
               user_role=data.user_role
           )
           self.db_session.add(log)
