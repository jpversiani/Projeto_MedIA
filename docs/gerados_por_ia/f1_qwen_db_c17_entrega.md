Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Implement `backend/app/repositories/auditoria_telemedicina.py` with a class `AuditoriaTelemedicinaRepository` for logging teleconsultation events (connection, disconnection, patient confidentiality agreement acceptance, secure timestamping) using SQLAlchemy 2.0.
   - **Guidelines:** Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), full compliance with automated testing with pytest.
   - **Output Requirement:** Provide complete, executable code. Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/auditoria_telemedicina.py`
   - **Class:** `AuditoriaTelemedicinaRepository`
   - **Features:**
     - Log connection events
     - Log disconnection events
     - Log patient confidentiality agreement acceptance (LGPD/CFM)
     - Secure timestamping
     - Use SQLAlchemy 2.0 (async preferred given modern Python web stacks, but I'll stick to sync or async based on common patterns; I'll use async as it's standard for modern FastAPI/SQLAlchemy 2.0, but I'll make it clear)
     - Pydantic v2 for models/data transfer
     - SUS/APS standards: CIAP-2, CID-10, SOAP, CNS/CPF
     - Pytest coverage
   - **Architecture:** Repository pattern, likely interacting with a database session.

3.  **Design Database Model (SQLAlchemy 2.0):**
   Need a model for audit logs. Let's call it `TelemedicinaAuditLog`.
   Fields:
   - `id`: UUID or Integer (PK)
   - `session_id`: str (unique teleconsultation session)
   - `patient_cns`: str (CNS - Carteira Nacional de Saúde)
   - `patient_cpf`: str (CPF)
   - `doctor_cpf`: str (CPF of the doctor)
   - `event_type`: str (CONNECTION, DISCONNECTION, TERMS_ACCEPTANCE)
   - `event_data`: JSON (for additional context like SOAP notes, CIAP-2, CID-10, timestamps)
   - `created_at`: datetime (secure timestamp)
   - `ip_address`: str (optional but good for audit)
   - `user_agent`: str (optional)
   - `is_verified`: bool (for secure timestamping/signature)

   Let's refine based on SUS/APS standards:
   - `ciap2_codes`: JSON array (CIAP-2 classification)
   - `cid10_codes`: JSON array (CID-10 classification)
   - `soap_notes`: JSON (SOAP method documentation)
   - `secure_timestamp`: datetime (or string with signature)
   - `terms_accepted_at`: datetime (for LGPD/CFM)
   - `terms_version`: str

   Actually, the repository should handle logging these events. I'll create a Pydantic model for the event payload and a SQLAlchemy model for the DB.

   SQLAlchemy Model:
   ```python
   from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey
   from sqlalchemy.orm import DeclarativeBase
   import uuid

   class Base(DeclarativeBase):
       pass

   class TelemedicinaAuditLog(Base):
       __tablename__ = "telemedicina_audit_logs"
       id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
       session_id = Column(String(36), nullable=False, index=True)
       patient_cns = Column(String(15), nullable=True)
       patient_cpf = Column(String(14), nullable=True)
       doctor_cpf = Column(String(14), nullable=False)
       event_type = Column(String(50), nullable=False) # CONNECTION, DISCONNECTION, TERMS_ACCEPTANCE
       event_data = Column(JSON, default=dict)
       created_at = Column(DateTime, nullable=False, server_default=func.now())
       secure_timestamp = Column(DateTime, nullable=False)
       ip_address = Column(String(45), nullable=True)
       user_agent = Column(String(255), nullable=True)
       is_verified = Column(Boolean, default=False)
   ```

   Wait, SQLAlchemy 2.0 uses `mapped_column` and `Mapped`. I'll use the modern syntax.
   Also, need `func` for server_default.

   Let's stick to SQLAlchemy 2.0 declarative style:
   ```python
   from sqlalchemy import String, DateTime, Boolean, JSON, func
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   import uuid
   from datetime import datetime

   class Base(DeclarativeBase):
       pass

   class TelemedicinaAuditLog(Base):
       __tablename__ = "telemedicina_audit_logs"
       id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
       session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
       patient_cns: Mapped[str | None] = mapped_column(String(15), nullable=True)
       patient_cpf: Mapped[str | None] = mapped_column(String(14), nullable=True)
       doctor_cpf: Mapped[str] = mapped_column(String(14), nullable=False)
       event_type: Mapped[str] = mapped_column(String(50), nullable=False)
       event_data: Mapped[dict] = mapped_column(JSON, default=dict)
       created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
       secure_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
       ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
       user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
       is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
   ```

4.  **Design Pydantic Models (v2):**
   Need models for input validation and output.
   ```python
   from pydantic import BaseModel, Field, ConfigDict
   from datetime import datetime
   from typing import Optional, List, Dict, Any
   from enum import Enum

   class EventType(str, Enum):
       CONNECTION = "CONNECTION"
       DISCONNECTION = "DISCONNECTION"
       TERMS_ACCEPTANCE = "TERMS_ACCEPTANCE"

   class TelemedicinaAuditLogCreate(BaseModel):
       session_id: str = Field(..., min_length=1)
       patient_cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       patient_cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       doctor_cpf: str = Field(..., pattern=r"^\d{11}$")
       event_type: EventType
       event_data: Dict[str, Any] = Field(default_factory=dict)
       ip_address: Optional[str] = None
       user_agent: Optional[str] = None

   class TelemedicinaAuditLogResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: str
       session_id: str
       patient_cns: Optional[str]
       patient_cpf: Optional[str]
       doctor_cpf: str
       event_type: str
       event_data: Dict[str, Any]
       created_at: datetime
       secure_timestamp: datetime
       ip_address: Optional[str]
       user_agent: Optional[str]
       is_verified: bool
   ```

5.  **Design Repository Class:**
   Needs to interact with a SQLAlchemy session. I'll make it async to align with modern stacks, but I'll provide a sync alternative or just stick to async as it's standard. I'll use `AsyncSession` for SQLAlchemy 2.0.
   Methods:
   - `log_connection(session_id, patient_cns, patient_cpf, doctor_cpf, ip_address, user_agent)`
   - `log_disconnection(session_id, doctor_cpf, ip_address, user_agent)`
   - `log_terms_acceptance(session_id, patient_cns, patient_cpf, doctor_cpf, ip_address, user_agent, terms_version)`
   - `get_logs(session_id)`
   - `verify_timestamp(log_id)` (for secure timestamping)

   I'll implement a method to create the log entry with secure timestamping (using `datetime.utcnow()` or `datetime.now(timezone.utc)`). I'll use `datetime.now(timezone.utc)` for correctness.

   Secure timestamping: In real systems, this might involve a trusted time source or cryptographic signature. For this implementation, I'll simulate it by storing the UTC time and marking it as verified, or adding a simple HMAC-like signature field if needed. The prompt says "carimbo de data/hora seguro", so I'll add a `secure_timestamp` field and a method to "sign" or verify it, or just ensure it's immutable and stored with timezone awareness. I'll add a `secure_hash` field for cryptographic integrity simulation.

   Let's refine the repository:
   ```python
   import hashlib
   import hmac
   import secrets
   from datetime import datetime, timezone
   from typing import Optional, List
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select
   from app.models.telemedicina_audit import TelemedicinaAuditLog # Assuming model is here
   from app.schemas.telemedicina_audit import TelemedicinaAuditLogCreate, EventType
   from app.core.config import settings # For secret key

   class AuditoriaTelemedicinaRepository:
       def __init__(self, secret_key: str):
           self.secret_key = secret_key

       async def log_connection(self, session: AsyncSession, data: TelemedicinaAuditLogCreate) -> TelemedicinaAuditLog:
           # ...
   ```

   Actually, I should keep it self-contained in one file as requested, but import from standard places or define them inline for completeness. The prompt says "implemente backend/app/repositories/auditoria_telemedicina.py com a classe AuditoriaTelemedicinaRepository". I'll define the SQLAlchemy model and Pydantic schemas in the same file for simplicity and completeness, or assume they exist. I'll define them in the file to make it executable.

   Let's structure the file:
   - Imports
   - Pydantic models
   - SQLAlchemy model
   - Repository class
   - Helper functions for secure timestamping
   - Pytest tests (in a separate block or at the end? The prompt says "cobertura de testes automatizados com pytest", so I should provide the test file too. I'll create `tests/test_auditoria_telemedicina.py`)

   Secure Timestamping Implementation:
   I'll create a function that generates a cryptographically secure timestamp signature using HMAC-SHA256 with a secret key, session ID, and event type. This satisfies "carimbo de data/hora seguro".

   ```python
   def generate_secure_timestamp(session_id: str, event_type: str, secret_key: str) -> tuple[datetime, str]:
       now = datetime.now(timezone.utc)
       payload = f"{session_id}:{event_type}:{now.isoformat()}"
       signature = hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
       return now, signature
   ```

   Repository methods will use this.

6.  **Draft the Repository Code (`backend/app/repositories/auditoria_telemedicina.py`):**
   I'll write it carefully with SQLAlchemy 2.0 syntax, Pydantic v2, strict typing, and SUS/APS fields.

   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   import hashlib
   import hmac
   from datetime import datetime, timezone
   from typing import Optional, List, Dict, Any
   from enum import Enum

   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from sqlalchemy import String, DateTime, Boolean, JSON, func, select
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   from sqlalchemy.ext.asyncio import AsyncSession

   # --- Pydantic Models (v2) ---
   class EventType(str, Enum):
       CONNECTION = "CONNECTION"
       DISCONNECTION = "DISCONNECTION"
       TERMS_ACCEPTANCE = "TERMS_ACCEPTANCE"

   class TelemedicinaAuditLogCreate(BaseModel):
       session_id: str = Field(..., min_length=1)
       patient_cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       patient_cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       doctor_cpf: str = Field(..., pattern=r"^\d{11}$")
       event_type: EventType
       event_data: Dict[str, Any] = Field(default_factory=dict)
       ip_address: Optional[str] = None
       user_agent: Optional[str] = None

       @field_validator("event_data")
       @classmethod
       def validate_event_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
           # Validate SUS/APS fields if present
           if "ciap2_codes" in v:
               if not isinstance(v["ciap2_codes"], list):
                   raise ValueError("ciap2_codes deve ser uma lista")
           if "cid10_codes" in v:
               if not isinstance(v["cid10_codes"], list):
                   raise ValueError("cid10_codes deve ser uma lista")
           if "soap_notes" in v:
               if not isinstance(v["soap_notes"], dict):
                   raise ValueError("soap_notes deve ser um objeto JSON")
           return v

   class TelemedicinaAuditLogResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: str
       session_id: str
       patient_cns: Optional[str]
       patient_cpf: Optional[str]
       doctor_cpf: str
       event_type: str
       event_data: Dict[str, Any]
       created_at: datetime
       secure_timestamp: datetime
       secure_signature: str
       ip_address: Optional[str]
       user_agent: Optional[str]
       is_verified: bool

   # --- SQLAlchemy 2.0 Model ---
   class Base(DeclarativeBase):
       pass

   class TelemedicinaAuditLog(Base):
       __tablename__ = "telemedicina_audit_logs"

       id: Mapped[str] = mapped_column(String(36), primary_key=True)
       session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
       patient_cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       patient_cpf: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
       doctor_cpf: Mapped[str] = mapped_column(String(14), nullable=False)
       event_type: Mapped[str] = mapped_column(String(50), nullable=False)
       event_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
       created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
       secure_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
       secure_signature: Mapped[str] = mapped_column(String(64), nullable=False)
       ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
       user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
       is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

   # --- Helper for Secure Timestamping ---
   def _generate_secure_timestamp(session_id: str, event_type: str, secret_key: str) -> tuple[datetime, str]:
       now = datetime.now(timezone.utc)
       payload = f"{session_id}:{event_type}:{now.isoformat()}"
       signature = hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
       return now, signature

   # --- Repository ---
   class AuditoriaTelemedicinaRepository:
       def __init__(self, secret_key: str):
           self.secret_key = secret_key

       async def log_connection(self, session: AsyncSession, data: TelemedicinaAuditLogCreate) -> TelemedicinaAuditLog:
           secure_ts, sig = _generate_secure_timestamp(data.session_id, EventType.CONNECTION.value, self.secret_key)
           log = TelemedicinaAuditLog(
               id=data.session_id, # Using session_id as PK for simplicity, or generate UUID
               session_id=data.session_id,
               patient_cns=data.patient_cns,
               patient_cpf=data.patient_cpf,
               doctor_cpf=data.doctor_cpf,
               event_type=EventType.CONNECTION.value,
               event_data=data.event_data,
               secure_timestamp=secure_ts,
               secure_signature=sig,
               ip_address=data.ip_address,
               user_agent=data.user_agent,
               is_verified=True
           )
           session.add(log)
           await session.commit()
           await session.refresh(log)
           return log

       async def log_disconnection(self, session: AsyncSession, session_id: str, doctor_cpf: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> TelemedicinaAuditLog:
           # Fetch patient data if needed, or just log with available info
           secure_ts, sig = _generate_secure_timestamp(session_id, EventType.DISCONNECTION.value, self.secret_key)
           log = TelemedicinaAuditLog(
               id=f"{session_id}_disconnect",
               session_id=session_id,
               doctor_cpf=doctor_cpf,
               event_type=EventType.DISCONNECTION.value,
               event_data={"reason": "end_of_session"},
               secure_timestamp=secure_ts,
               secure_signature=sig,
               ip_address=ip_address,
               user_agent=user_agent,
               is_verified=True
           )
           session.add(log)
           await session.commit()
           await session.refresh(log)
           return log

       async def log_terms_acceptance(self, session: AsyncSession, session_id: str, patient_cns: str, patient_cpf: str, doctor_cpf: str