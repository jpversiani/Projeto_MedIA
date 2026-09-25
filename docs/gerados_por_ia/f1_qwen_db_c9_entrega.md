Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Implement `backend/app/repositories/auditoria_telemedicina.py` with a class `AuditoriaTelemedicinaRepository` for logging teleconsultation events (connection, disconnection, patient confidentiality agreement acceptance, secure timestamping) using SQLAlchemy 2.0.
   - **Constraints:** Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), full compliance with automated test coverage using pytest.
   - **Output Requirement:** Provide complete, executable code. Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File Path:** `backend/app/repositories/auditoria_telemedicina.py`
   - **Class:** `AuditoriaTelemedicinaRepository`
   - **Features:**
     - Log connection events
     - Log disconnection events
     - Log patient confidentiality agreement acceptance (LGPD/CFM)
     - Secure timestamping
     - SQLAlchemy 2.0 ORM
     - Pydantic v2 for data validation
     - SUS/APS standards: CIAP-2, CID-10, SOAP, CNS/CPF
   - **Testing:** Need to provide pytest tests covering the repository.
   - **Architecture:** Python 3.12, strict typing, SQLAlchemy 2.0 patterns.

3.  **Design Database Model (SQLAlchemy 2.0):**
   - Need a table for audit logs: `telemedicina_auditoria`
   - Fields:
     - `id`: UUID/Integer primary key
     - `session_id`: String (teleconsultation session ID)
     - `patient_cns`: String (CNS - Carteira Nacional de Saúde)
     - `patient_cpf`: String (CPF)
     - `doctor_crm`: String (CRM)
     - `event_type`: Enum (CONNECTION, DISCONNECTION, CONSENT_ACCEPTED, etc.)
     - `event_data`: JSON/Text (for SOAP, CIAP-2, CID-10, etc.)
     - `timestamp`: DateTime (secure, UTC, with timezone)
     - `ip_address`: String
     - `user_agent`: String
     - `created_at`: DateTime (auto)
   - Let's use SQLAlchemy 2.0 declarative style with `Mapped`, `mapped_column`, `MappedAsDataclass` or standard `DeclarativeBase`.
   - I'll use `DeclarativeBase` for clarity and compatibility.
   - Event types: `CONNECTION`, `DISCONNECTION`, `CONSENT_ACCEPTED`, `CONSULTATION_START`, `CONSULTATION_END`, `DOCUMENTATION` (for SOAP/CID-10/CIAP-2)
   - Actually, the prompt specifically asks for: connection, disconnection, consent acceptance, secure timestamp. I'll focus on these but include fields for SUS/APS standards as requested.

   Let's define the model:
   ```python
   from sqlalchemy import String, Text, DateTime, Enum, func, ForeignKey
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   from datetime import datetime, timezone
   import enum
   import uuid

   class EventType(str, enum.Enum):
       CONNECTION = "CONNECTION"
       DISCONNECTION = "DISCONNECTION"
       CONSENT_ACCEPTED = "CONSENT_ACCEPTED"
       CONSULTATION_EVENT = "CONSULTATION_EVENT" # For SOAP/CID-10/CIAP-2

   class Base(DeclarativeBase):
       pass

   class TelemedicinaAuditoria(Base):
       __tablename__ = "telemedicina_auditoria"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
       patient_cns: Mapped[str | None] = mapped_column(String(15), nullable=True)
       patient_cpf: Mapped[str | None] = mapped_column(String(14), nullable=True)
       doctor_crm: Mapped[str | None] = mapped_column(String(20), nullable=True)
       event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
       event_data: Mapped[str | None] = mapped_column(Text, nullable=True) # JSON string for SOAP, CIAP-2, CID-10, etc.
       ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
       user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
       timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
   ```

4.  **Design Pydantic Schemas (v2):**
   - Need schemas for validation and DTOs.
   - `AuditoriaTelemedicinaCreate` (for input)
   - `AuditoriaTelemedicinaRead` (for output)
   - Use `pydantic` v2 patterns: `BaseModel`, `Field`, `ConfigDict`, `model_validator`, etc.
   - Strict typing: `type: ignore` if needed, but prefer proper types.

   ```python
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from datetime import datetime
   from typing import Optional
   import json

   class AuditoriaTelemedicinaCreate(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True)

       session_id: str = Field(..., min_length=1, max_length=36)
       patient_cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       patient_cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       doctor_crm: Optional[str] = Field(None, min_length=1)
       event_type: str = Field(..., pattern=r"^(CONNECTION|DISCONNECTION|CONSENT_ACCEPTED|CONSULTATION_EVENT)$")
       event_data: Optional[dict] = None
       ip_address: Optional[str] = None
       user_agent: Optional[str] = None

       @field_validator("event_data", mode="before")
       @classmethod
       def validate_event_data(cls, v):
           if v is None:
               return None
           if isinstance(v, dict):
               return json.dumps(v)
           return v

   class AuditoriaTelemedicinaRead(BaseModel):
       id: uuid.UUID
       session_id: str
       patient_cns: Optional[str]
       patient_cpf: Optional[str]
       doctor_crm: Optional[str]
       event_type: str
       event_data: Optional[dict]
       ip_address: Optional[str]
       user_agent: Optional[str]
       timestamp: datetime
       created_at: datetime

       model_config = ConfigDict(from_attributes=True)

       @field_validator("event_data", mode="before")
       @classmethod
       def parse_event_data(cls, v):
           if v is None:
               return None
           if isinstance(v, str):
               return json.loads(v)
           return v
   ```

5.  **Design Repository Class:**
   - `AuditoriaTelemedicinaRepository`
   - Methods:
     - `__init__(self, session: AsyncSession)`
     - `log_connection(self, session_id, patient_cns, patient_cpf, doctor_crm, ip_address, user_agent)`
     - `log_disconnection(self, session_id, ...)`
     - `log_consent_accepted(self, session_id, patient_cns, patient_cpf, ...)`
     - `log_consultation_event(self, session_id, patient_cns, patient_cpf, doctor_crm, event_data, ...)` (for SOAP/CID-10/CIAP-2)
     - `get_by_session(self, session_id)`
     - `get_by_date_range(self, start, end)`
   - Use SQLAlchemy 2.0 async patterns (`async with`, `session.execute`, `session.commit`).
   - Secure timestamping: Use `datetime.now(timezone.utc)` explicitly.
   - Strict typing: Use `asyncio`, `sqlalchemy.ext.asyncio.AsyncSession`, `sqlalchemy.orm.Session` if sync, but prompt says SQLAlchemy 2.0, I'll assume async as it's modern, but I'll make it compatible or explicitly async. I'll use `AsyncSession` for modern FastAPI/SQLAlchemy 2.0 stack. I'll also provide sync alternative or stick to async as it's standard. I'll use `AsyncSession` but note it. Actually, I'll make it generic or explicitly async. Let's stick to `AsyncSession` for modern stack, but I'll add type hints properly.

   Let's draft the repository:
   ```python
   import asyncio
   import json
   import uuid
   from datetime import datetime, timezone
   from typing import Optional, List
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, func
   from sqlalchemy.orm import Session

   # Assuming the model is defined in the same file or imported. I'll put it here for completeness.
   # ... (model code) ...

   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def log_event(self, event: AuditoriaTelemedicinaCreate) -> TelemedicinaAuditoria:
           # Secure timestamp
           now_utc = datetime.now(timezone.utc)
           db_obj = TelemedicinaAuditoria(
               session_id=event.session_id,
               patient_cns=event.patient_cns,
               patient_cpf=event.patient_cpf,
               doctor_crm=event.doctor_crm,
               event_type=event.event_type,
               event_data=event.event_data,
               ip_address=event.ip_address,
               user_agent=event.user_agent,
               timestamp=now_utc,
               created_at=now_utc
           )
           self.session.add(db_obj)
           await self.session.flush()
           await self.session.refresh(db_obj)
           return db_obj

       async def log_connection(self, session_id: str, patient_cns: Optional[str], patient_cpf: Optional[str],
                                doctor_crm: Optional[str], ip_address: Optional[str], user_agent: Optional[str]) -> TelemedicinaAuditoria:
           event = AuditoriaTelemedicinaCreate(
               session_id=session_id,
               patient_cns=patient_cns,
               patient_cpf=patient_cpf,
               doctor_crm=doctor_crm,
               event_type="CONNECTION",
               ip_address=ip_address,
               user_agent=user_agent
           )
           return await self.log_event(event)

       async def log_disconnection(self, session_id: str, patient_cns: Optional[str], patient_cpf: Optional[str],
                                   doctor_crm: Optional[str], ip_address: Optional[str], user_agent: Optional[str]) -> TelemedicinaAuditoria:
           event = AuditoriaTelemedicinaCreate(
               session_id=session_id,
               patient_cns=patient_cns,
               patient_cpf=patient_cpf,
               doctor_crm=doctor_crm,
               event_type="DISCONNECTION",
               ip_address=ip_address,
               user_agent=user_agent
           )
           return await self.log_event(event)

       async def log_consent_accepted(self, session_id: str, patient_cns: Optional[str], patient_cpf: Optional[str],
                                      doctor_crm: Optional[str], ip_address: Optional[str], user_agent: Optional[str]) -> TelemedicinaAuditoria:
           event = AuditoriaTelemedicinaCreate(
               session_id=session_id,
               patient_cns=patient_cns,
               patient_cpf=patient_cpf,
               doctor_crm=doctor_crm,
               event_type="CONSENT_ACCEPTED",
               ip_address=ip_address,
               user_agent=user_agent
           )
           return await self.log_event(event)

       async def log_consultation_event(self, session_id: str, patient_cns: Optional[str], patient_cpf: Optional[str],
                                        doctor_crm: Optional[str], event_data: dict, ip_address: Optional[str], user_agent: Optional[str]) -> TelemedicinaAuditoria:
           # Supports SOAP, CIAP-2, CID-10
           event = AuditoriaTelemedicinaCreate(
               session_id=session_id,
               patient_cns=patient_cns,
               patient_cpf=patient_cpf,
               doctor_crm=doctor_crm,
               event_type="CONSULTATION_EVENT",
               event_data=event_data,
               ip_address=ip_address,
               user_agent=user_agent
           )
           return await self.log_event(event)

       async def get_by_session(self, session_id: str) -> List[TelemedicinaAuditoria]:
           stmt = select(TelemedicinaAuditoria).where(TelemedicinaAuditoria.session_id == session_id).order_by(TelemedicinaAuditoria.timestamp)
           result = await self.session.execute(stmt)
           return list(result.scalars().all())

       async def get_by_date_range(self, start: datetime, end: datetime) -> List[TelemedicinaAuditoria]:
           stmt = select(TelemedicinaAuditoria).where(
               TelemedicinaAuditoria.timestamp >= start,
               TelemedicinaAuditoria.timestamp <= end
           ).order_by(TelemedicinaAuditoria.timestamp)
           result = await self.session.execute(stmt)
           return list(result.scalars().all())
   ```

6.  **Refine & Align with Requirements:**
   - **Python 3.12, strict typing:** Use `from __future__ import annotations` or modern typing. I'll use `typing` module properly. Add type hints to all methods.
   - **Pydantic v2:** Used `model_config`, `Field`, `field_validator`. Good.
   - **SQLAlchemy 2.0:** Used `DeclarativeBase`, `Mapped`, `mapped_column`, `select`, `AsyncSession`. Good.
   - **SUS/APS Standards:** Added fields for CIAP-2, CID-10, SOAP in `event_data` dict structure. I should document this or add a helper to structure it. I'll add a Pydantic model for the consultation event data to enforce structure.
   - **Secure Timestamping:** Explicit UTC with timezone.
   - **LGPD/CFM Consent:** Handled via `CONSENT_ACCEPTED` event type.
   - **Tests:** Need pytest tests covering all methods, validation, and edge cases.

   Let's enhance the Pydantic schema for consultation events to align with SUS/APS:
   ```python
   class ConsultaEventos(BaseModel):
       # SOAP
       subjetivo: Optional[str] = None
       objetivo: Optional[str] = None
       avaliacoes: Optional[str] = None
       plano: Optional[str] = None
       # CID-10 / CIAP-2
       codigos_cid10: Optional[list[str]] = None
       codigos_ciap2: Optional[list[str]] = None
       # Outros
       duracao_minutos: Optional[int] = None
       observacoes_lgpd: Optional[str] = None
   ```
   I'll integrate this into the `event_data` validation or use it directly. Actually, keeping `event_data` as `dict` is fine, but I'll add a specific schema for it to enforce structure.

   Let's restructure the code to be clean, complete, and ready for testing. I'll put everything in one file as requested, but structure it logically.

   **File Structure in Output:**
   - `backend/app/repositories/auditoria_telemedicina.py` (Model, Schemas, Repository)
   - `backend/app/tests/test_auditoria_telemedicina.py` (Pytest tests)

   I'll ensure strict typing, SQLAlchemy 2.0 async patterns, Pydantic v2, and comprehensive tests.

   **Self-Correction/Verification during thought:**
   - *SQLAlchemy 2.0 Mapped syntax:* Requires `from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase`. Correct.
   - *Pydantic v2:* `model_config = ConfigDict(from_attributes=True)` is correct for ORM mode. `field_validator` with `mode="before"` is correct.
   - *AsyncSession:* I'll use `AsyncSession` but note that it can be adapted. I'll stick to async as it's standard for modern Python 3.12 + FastAPI.
   - *Secure Timestamp:* `datetime.now(timezone.utc)` is correct. I'll also add a method to generate secure UUIDs if needed, but `uuid.uuid4()` is fine.
   - *SUS/APS:* I'll add a helper function or Pydantic model to structure the SOAP/CID-10/CIAP-2 data properly.
   - *Tests:* Need to mock `AsyncSession` or use `pytest-asyncio` with an in-memory SQLite DB. I'll use `pytest-asyncio` and `sqlalchemy.ext.asyncio.create_async_engine` with `AsyncSession` for real DB testing in tests. This is more robust.

   Let's draft the complete code carefully.

   **Structure of `auditoria_telemedicina.py`:**
   - Imports
   - Pydantic Schemas (Create, Read, ConsultaEventos)
   - SQLAlchemy Model (TelemedicinaAuditoria)
   - Repository Class (AuditoriaTelemedicinaRepository)
   - Helper/Constants (Event types, etc.)

   **Structure of `test_auditoria_telemedicina.py`:**
   - Fixtures (engine, session, repo)
   - Tests for validation
   - Tests for CRUD/Logging
   - Tests for SUS/APS data structure
   - Tests for timestamp security
   - Use `pytest-asyncio`

   I'll write it out now, ensuring all constraints are met.
   *Self-Correction/Refinement during drafting:*
   - SQLAlchemy 2.0 `Mapped` syntax requires `from __future__ import annotations` or explicit string annotations in older