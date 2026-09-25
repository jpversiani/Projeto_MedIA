Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Implement `backend/app/repositories/auditoria_telemedicina.py` with a class `AuditoriaTelemedicinaRepository` for logging teleconsultation events (connection, disconnection, privacy policy acceptance, secure timestamping) using SQLAlchemy 2.0.
   - **Constraints:** Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), full compliance with automated pytest tests.
   - **Output Requirement:** Provide complete, executable code for each file, with file path comments.

2.  **Deconstruct Requirements:**
   - **Repository Class:** `AuditoriaTelemedicinaRepository`
   - **Events to Log:** Connection, Disconnection, Privacy Policy Acceptance (LGPD/CFM)
   - **Features:** Secure timestamping, SQLAlchemy 2.0 ORM, Pydantic v2 models for validation/input/output
   - **Standards:** SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF) - need to incorporate these into the model/schema
   - **Testing:** Must be testable with pytest (I should provide the repository code, but the prompt says "Execute com precisão conforme as diretrizes" and emphasizes testing coverage. I'll provide the repository and a corresponding test file to ensure completeness, as requested by "cobertura de testes automatizados com pytest").

3.  **Design the Data Model (SQLAlchemy 2.0):**
   - Need a table for audit logs.
   - Fields:
     - `id`: UUID or Integer (PK)
     - `event_type`: Enum (CONNECTION, DISCONNECTION, CONSENT_ACCEPTANCE)
     - `patient_cns`: String (CNS - Carteira Nacional de Saúde)
     - `patient_cpf`: String (CPF)
     - `provider_cpf`: String (CPF do médico/profissional)
     - `consultation_id`: UUID/Integer (FK to teleconsultation)
     - `diagnosis_ciap2`: String (CIAP-2)
     - `diagnosis_cid10`: String (CID-10)
     - `soap_method`: String (SOAP format)
     - `timestamp_utc`: DateTime (secure, UTC)
     - `metadata`: JSON (for extra event details)
     - `created_at`: DateTime (auto)
     - `updated_at`: DateTime (auto)
   - Use SQLAlchemy 2.0 declarative style.
   - Use Pydantic v2 for request/response schemas.

4.  **Design Pydantic Schemas:**
   - `AuditoriaTelemedicinaCreateSchema`: For creating logs
   - `AuditoriaTelemedicinaReadSchema`: For reading/logs
   - Use `BaseModel` from `pydantic`
   - Validate CNS/CPF formats (optional but good practice, or just use string with length constraints)
   - Use `Enum` for event types

5.  **Design Repository Class:**
   - `AuditoriaTelemedicinaRepository`
   - Methods:
     - `__init__(self, session: AsyncSession)`
     - `create_log(self, event_type: EventType, patient_cns: str, patient_cpf: str, provider_cpf: str, consultation_id: UUID, diagnosis_ciap2: str | None, diagnosis_cid10: str | None, soap_method: str | None, metadata: dict | None) -> AuditLog`
     - `get_logs_by_consultation(self, consultation_id: UUID) -> list[AuditLog]`
     - `get_logs_by_patient(self, patient_cns: str) -> list[AuditLog]`
   - Use async SQLAlchemy 2.0 (`AsyncSession`)
   - Secure timestamp: Use `datetime.now(timezone.utc)` or `func.now()`
   - Handle transactions properly.

6.  **Refine & Align with Standards:**
   - SUS/APS: CIAP-2, CID-10, SOAP, CNS, CPF are already in the model.
   - LGPD/CFM: Consent acceptance event type, metadata for consent details.
   - Secure timestamp: Ensure UTC, timezone-aware, immutable after creation.
   - Pydantic v2: Use `model_config`, `Field`, `ConfigDict`, `ComputedField` if needed.
   - SQLAlchemy 2.0: Use `Mapped`, `mapped_column`, `MappedAsDataclass` or standard declarative. I'll use standard declarative with `Mapped` and `mapped_column` for modern SQLAlchemy 2.0 style.

   Let's draft the SQLAlchemy model:
   ```python
   from sqlalchemy import String, Text, DateTime, Enum, JSON, ForeignKey
   from sqlalchemy.orm import Mapped, mapped_column, relationship
   from sqlalchemy.sql import func
   from datetime import datetime, timezone
   import uuid
   from enum import Enum as PyEnum

   class EventType(PyEnum):
       CONNECTION = "CONNECTION"
       DISCONNECTION = "DISCONNECTION"
       CONSENT_ACCEPTANCE = "CONSENT_ACCEPTANCE"

   class AuditLog(Base):
       __tablename__ = "auditoria_telemedicina"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
       patient_cns: Mapped[str] = mapped_column(String(47), nullable=False) # CNS length
       patient_cpf: Mapped[str] = mapped_column(String(14), nullable=False) # CPF format
       provider_cpf: Mapped[str] = mapped_column(String(14), nullable=False)
       consultation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teleconsultas.id"), nullable=False)
       diagnosis_ciap2: Mapped[str | None] = mapped_column(String(4), nullable=True) # CIAP-2
       diagnosis_cid10: Mapped[str | None] = mapped_column(String(7), nullable=True) # CID-10
       soap_method: Mapped[str | None] = mapped_column(Text, nullable=True)
       metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
       timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
   ```

   Wait, SQLAlchemy 2.0 recommends using `Mapped` and `mapped_column` with type hints. I'll stick to that.
   Need to import `Base` from the project's base module, but since I'm providing a standalone file, I'll assume a standard `Base` or define it minimally. I'll add a comment about importing from `backend/app/database/base.py`.

   Pydantic schemas:
   ```python
   from pydantic import BaseModel, Field, ConfigDict
   from datetime import datetime
   from typing import Optional, Dict, Any
   from enum import Enum as PyEnum

   class EventTypeEnum(str, PyEnum):
       CONNECTION = "CONNECTION"
       DISCONNECTION = "DISCONNECTION"
       CONSENT_ACCEPTANCE = "CONSENT_ACCEPTANCE"

   class AuditoriaTelemedicinaCreateSchema(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       event_type: EventTypeEnum
       patient_cns: str = Field(..., min_length=15, max_length=47)
       patient_cpf: str = Field(..., pattern=r"^\d{11}$")
       provider_cpf: str = Field(..., pattern=r"^\d{11}$")
       consultation_id: str = Field(..., pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
       diagnosis_ciap2: Optional[str] = Field(None, max_length=4)
       diagnosis_cid10: Optional[str] = Field(None, max_length=7)
       soap_method: Optional[str] = None
       metadata: Optional[Dict[str, Any]] = None

   class AuditoriaTelemedicinaReadSchema(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: str
       event_type: EventTypeEnum
       patient_cns: str
       patient_cpf: str
       provider_cpf: str
       consultation_id: str
       diagnosis_ciap2: Optional[str]
       diagnosis_cid10: Optional[str]
       soap_method: Optional[str]
       metadata: Optional[Dict[str, Any]]
       timestamp_utc: datetime
       created_at: datetime
       updated_at: datetime
   ```

   Repository class:
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select
   from typing import List, Optional
   import uuid
   from datetime import datetime, timezone

   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def create_log(self, schema: AuditoriaTelemedicinaCreateSchema) -> AuditLog:
           now_utc = datetime.now(timezone.utc)
           log = AuditLog(
               event_type=schema.event_type,
               patient_cns=schema.patient_cns,
               patient_cpf=schema.patient_cpf,
               provider_cpf=schema.provider_cpf,
               consultation_id=uuid.UUID(schema.consultation_id),
               diagnosis_ciap2=schema.diagnosis_ciap2,
               diagnosis_cid10=schema.diagnosis_cid10,
               soap_method=schema.soap_method,
               metadata=schema.metadata,
               timestamp_utc=now_utc,
               created_at=now_utc,
               updated_at=now_utc
           )
           self.session.add(log)
           await self.session.flush()
           await self.session.refresh(log)
           return log

       async def get_logs_by_consultation(self, consultation_id: uuid.UUID) -> List[AuditLog]:
           stmt = select(AuditLog).where(AuditLog.consultation_id == consultation_id).order_by(AuditLog.timestamp_utc)
           result = await self.session.execute(stmt)
           return list(result.scalars().all())

       async def get_logs_by_patient(self, patient_cns: str) -> List[AuditLog]:
           stmt = select(AuditLog).where(AuditLog.patient_cns == patient_cns).order_by(AuditLog.timestamp_utc)
           result = await self.session.execute(stmt)
           return list(result.scalars().all())
   ```

   Need to ensure SQLAlchemy 2.0 compatibility. `Mapped` and `mapped_column` are correct. I'll add the necessary imports and base class assumption.
   Also, need to handle the secure timestamp requirement properly. Using `datetime.now(timezone.utc)` is fine, but for DB-level security, `server_default=func.now()` is good. I'll keep both.

   Let's structure the file properly with all necessary imports, type hints, and comments. I'll also add a test file to satisfy the "cobertura de testes automatizados com pytest" requirement, as it's explicitly mentioned.

   Test file structure:
   - Mock async session
   - Test create_log
   - Test get_logs_by_consultation
   - Test get_logs_by_patient
   - Test validation (Pydantic)
   - Use `pytest-asyncio`

   I'll write the repository file first, then the test file.

   Check constraints:
   - Python 3.12: Use `|` for union types, `from __future__ import annotations` if needed, but standard is fine.
   - Pydantic v2: `model_config = ConfigDict(from_attributes=True)` is correct.
   - SQLAlchemy 2.0: `Mapped`, `mapped_column`, `AsyncSession`, `select`, `execute` are correct.
   - SUS/APS: CIAP-2, CID-10, SOAP, CNS, CPF included.
   - LGPD/CFM: Consent acceptance event, metadata for consent details.
   - Secure timestamp: UTC, timezone-aware, immutable after creation (handled by DB default and logic).

   One detail: `timestamp_utc` should be secure. I'll add a comment about cryptographic signing or HMAC if needed, but for standard audit logs, UTC + DB server time + immutable creation is standard. I'll ensure it's strictly UTC and timezone-aware.

   Let's draft the complete repository file.

   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   from __future__ import annotations

   import uuid
   from datetime import datetime, timezone
   from enum import Enum as PyEnum
   from typing import List, Optional, Dict, Any

   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from sqlalchemy import String, Text, DateTime, Enum, JSON, ForeignKey, select
   from sqlalchemy.orm import Mapped, mapped_column
   from sqlalchemy.ext.asyncio import AsyncSession

   # Importação assumida da base do projeto
   # from backend.app.database.base import Base

   class EventType(PyEnum):
       CONNECTION = "CONNECTION"
       DISCONNECTION = "DISCONNECTION"
       CONSENT_ACCEPTANCE = "CONSENT_ACCEPTANCE"

   class AuditLog(Base):
       __tablename__ = "auditoria_telemedicina"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
       patient_cns: Mapped[str] = mapped_column(String(47), nullable=False)
       patient_cpf: Mapped[str] = mapped_column(String(14), nullable=False)
       provider_cpf: Mapped[str] = mapped_column(String(14), nullable=False)
       consultation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teleconsultas.id"), nullable=False)
       diagnosis_ciap2: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
       diagnosis_cid10: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
       soap_method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
       timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=None, nullable=False)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=None, nullable=False)
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=None, nullable=False)

   class AuditoriaTelemedicinaCreateSchema(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       event_type: EventType
       patient_cns: str = Field(..., min_length=15, max_length=47)
       patient_cpf: str = Field(..., pattern=r"^\d{11}$")
       provider_cpf: str = Field(..., pattern=r"^\d{11}$")
       consultation_id: str = Field(..., pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
       diagnosis_ciap2: Optional[str] = Field(None, max_length=4)
       diagnosis_cid10: Optional[str] = Field(None, max_length=7)
       soap_method: Optional[str] = None
       metadata: Optional[Dict[str, Any]] = None

       @field_validator("patient_cpf", "provider_cpf")
       @classmethod
       def validate_cpf(cls, v: str) -> str:
           if not v.isdigit():
               raise ValueError("CPF deve conter apenas dígitos")
           return v

   class AuditoriaTelemedicinaReadSchema(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: str
       event_type: EventType
       patient_cns: str
       patient_cpf: str
       provider_cpf: str
       consultation_id: str
       diagnosis_ciap2: Optional[str]
       diagnosis_cid10: Optional[str]
       soap_method: Optional[str]
       metadata: Optional[Dict[str, Any]]
       timestamp_utc: datetime
       created_at: datetime
       updated_at: datetime

   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def create_log(self, schema: AuditoriaTelemedicinaCreateSchema) -> AuditLog:
           now_utc = datetime.now(timezone.utc)
           log = AuditLog(
               event_type=schema.event_type,
               patient_cns=schema.patient_cns,
               patient_cpf=schema.patient_cpf,
               provider_cpf=schema.provider_cpf,
               consultation_id=uuid.UUID(schema.consultation_id),
               diagnosis_ciap2=schema.diagnosis_ciap2,
               diagnosis_cid10=schema.diagnosis_cid10,
               soap_method=schema.soap_method,
               metadata=schema.metadata,
               timestamp_utc=now_utc,
               created_at=now_utc,
               updated_at=now_utc,
           )
           self.session.add(log)
           await self.session.flush()
           await self.session.refresh(log)
           return log

       async def get_logs_by_consultation(self, consultation_id: uuid.UUID) -> List[AuditLog]:
           stmt = select(AuditLog).where(AuditLog.consultation_id == consultation_id).order_by(AuditLog.timestamp_utc)
           result = await self.session.execute(stmt)
           return list(result.scalars().all())

       async def get_logs_by_patient(self, patient_cns: str) -> List[AuditLog]:
           stmt = select(AuditLog).where(AuditLog.patient_cns == patient_cns).order_by(AuditLog.timestamp_utc)
           result = await self.session.execute(stmt)
           return list(result.scalars().all())
   ```

   Wait, `server