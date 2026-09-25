Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Implement `backend/app/repositories/auditoria_telemedicina.py` with a class `AuditoriaTelemedicinaRepository` for logging teleconsultation events (connection, disconnection, privacy terms acceptance, secure timestamping) using SQLAlchemy 2.0.
   - **Guidelines:** Python 3.12, strict typing with Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), full compliance with automated tests via pytest.
   - **Output Requirement:** Provide complete, executable code. Specify file paths at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/auditoria_telemedicina.py`
   - **Class:** `AuditoriaTelemedicinaRepository`
   - **Features:**
     - Log connection events
     - Log disconnection events
     - Log privacy terms acceptance (LGPD/CFM)
     - Secure timestamping
     - SQLAlchemy 2.0 ORM
     - Pydantic v2 for data models/validation
     - SUS/APS standards: CIAP-2, CID-10, SOAP, CNS/CPF
     - Pytest coverage
   - **Architecture/Standards:** Python 3.12, strict typing, SUS/APS compliance.

3.  **Identify Key Components Needed:**
   - **Database Models (SQLAlchemy 2.0):** Need a table/model for audit logs. Let's call it `TelemedicinaAuditLog`.
     - Fields: id, session_id, patient_cns, patient_cpf, doctor_crm, event_type (connection, disconnection, terms_accepted), event_data (JSON), created_at (timestamp), ip_address, user_agent, signature_hash (for secure timestamping/integrity).
   - **Pydantic Models:** For validation of input/output.
     - `TelemedicinaAuditLogCreate` (input)
     - `TelemedicinaAuditLogRead` (output)
   - **Repository Class:** `AuditoriaTelemedicinaRepository`
     - Methods: `log_connection`, `log_disconnection`, `log_terms_acceptance`, `get_session_logs`, `verify_integrity`
     - Uses SQLAlchemy async/sync? The prompt doesn't specify, but modern apps often use async. I'll stick to sync for simplicity unless specified, but I'll make it compatible with both or explicitly use `sqlalchemy.orm.Session`. I'll use sync for broader compatibility, but add type hints. Actually, I'll use `sqlalchemy.ext.asyncio` if needed, but the prompt says "SQLAlchemy 2.0", so I'll stick to standard `Session` with type hints. I'll make it async-ready or just use standard `Session` with explicit type hints. Let's use standard `Session` for simplicity, but I'll note it can be adapted. Actually, I'll use `sqlalchemy.orm.Session` and type hints.
   - **Secure Timestamping:** Use cryptographic hashing (HMAC or SHA-256) with a secret key to ensure integrity. I'll implement a method to generate a secure timestamp/hash.
   - **SUS/APS Standards:** Include fields for CIAP-2, CID-10, SOAP method, CNS, CPF in the audit log or related models. I'll add them to the `event_data` JSON or as explicit columns. Explicit columns are better for querying. Let's add them to the model.
   - **Pytest:** Need a test file `tests/test_auditoria_telemedicina.py` with comprehensive coverage.

4.  **Design Database Model (SQLAlchemy 2.0):**
   ```python
   from sqlalchemy import Column, Integer, String, DateTime, Enum, JSON, ForeignKey, Text
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
   from datetime import datetime
   import enum

   class Base(DeclarativeBase):
       pass

   class EventType(str, enum.Enum):
       CONNECTION = "connection"
       DISCONNECTION = "disconnection"
       TERMS_ACCEPTANCE = "terms_acceptance"

   class TelemedicinaAuditLog(Base):
       __tablename__ = "telemedicina_audit_logs"

       id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
       session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
       patient_cns: Mapped[str | None] = mapped_column(String(15), nullable=True)
       patient_cpf: Mapped[str | None] = mapped_column(String(14), nullable=True)
       doctor_crm: Mapped[str | None] = mapped_column(String(20), nullable=True)
       event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
       ciap2_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
       cid10_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
       soap_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
       event_data: Mapped[dict] = mapped_column(JSON, nullable=True)
       ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
       user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
       signature_hash: Mapped[str] = mapped_column(String(64), nullable=False)
       created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
   ```
   Wait, `mapped_column` is SQLAlchemy 2.0 style. I'll use it correctly.
   Also, need to handle `ciap2_code`, `cid10_code`, `soap_method` as per SUS/APS standards.

5.  **Design Pydantic Models:**
   ```python
   from pydantic import BaseModel, Field, ConfigDict
   from datetime import datetime
   from typing import Optional
   from enum import Enum

   class EventTypeEnum(str, Enum):
       CONNECTION = "connection"
       DISCONNECTION = "disconnection"
       TERMS_ACCEPTANCE = "terms_acceptance"

   class TelemedicinaAuditLogCreate(BaseModel):
       session_id: str
       patient_cns: Optional[str] = None
       patient_cpf: Optional[str] = None
       doctor_crm: Optional[str] = None
       event_type: EventTypeEnum
       ciap2_code: Optional[str] = None
       cid10_code: Optional[str] = None
       soap_method: Optional[str] = None
       event_data: Optional[dict] = None
       ip_address: Optional[str] = None
       user_agent: Optional[str] = None

   class TelemedicinaAuditLogRead(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: int
       session_id: str
       patient_cns: Optional[str]
       patient_cpf: Optional[str]
       doctor_crm: Optional[str]
       event_type: EventTypeEnum
       ciap2_code: Optional[str]
       cid10_code: Optional[str]
       soap_method: Optional[str]
       event_data: Optional[dict]
       ip_address: Optional[str]
       user_agent: Optional[str]
       signature_hash: str
       created_at: datetime
   ```

6.  **Design Repository Class:**
   Needs to handle DB session injection. I'll use a standard `Session` from `sqlalchemy.orm`.
   Secure timestamping: I'll create a method that generates a hash based on session_id, event_type, timestamp, and a secret key (or just uses a deterministic hash for integrity verification). Actually, "carimbo de data/hora seguro" usually implies a trusted timestamp or cryptographic hash. I'll implement a simple HMAC-based integrity check/hash generation for the log entry.
   ```python
   import hashlib
   import hmac
   from sqlalchemy.orm import Session
   from datetime import datetime
   from typing import List, Optional
   from .models import TelemedicinaAuditLog, EventType
   from .schemas import TelemedicinaAuditLogCreate, TelemedicinaAuditLogRead

   class AuditoriaTelemedicinaRepository:
       def __init__(self, db_session: Session, secret_key: str = "default_secret_key_for_audit"):
           self.db_session = db_session
           self.secret_key = secret_key

       def _generate_secure_timestamp_hash(self, session_id: str, event_type: str, created_at: datetime) -> str:
           # Secure timestamp/hash generation
           data = f"{session_id}:{event_type}:{created_at.isoformat()}"
           return hmac.new(self.secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()

       def log_connection(self, create_data: TelemedicinaAuditLogCreate) -> TelemedicinaAuditLogRead:
           create_data.event_type = EventTypeEnum.CONNECTION
           log_entry = self._create_log_entry(create_data)
           return self._read_from_model(log_entry)

       def log_disconnection(self, create_data: TelemedicinaAuditLogCreate) -> TelemedicinaAuditLogRead:
           create_data.event_type = EventTypeEnum.DISCONNECTION
           log_entry = self._create_log_entry(create_data)
           return self._read_from_model(log_entry)

       def log_terms_acceptance(self, create_data: TelemedicinaAuditLogCreate) -> TelemedicinaAuditLogRead:
           create_data.event_type = EventTypeEnum.TERMS_ACCEPTANCE
           log_entry = self._create_log_entry(create_data)
           return self._read_from_model(log_entry)

       def _create_log_entry(self, create_data: TelemedicinaAuditLogCreate) -> TelemedicinaAuditLog:
           now = datetime.utcnow()
           signature_hash = self._generate_secure_timestamp_hash(
               create_data.session_id,
               create_data.event_type.value,
               now
           )
           db_entry = TelemedicinaAuditLog(
               session_id=create_data.session_id,
               patient_cns=create_data.patient_cns,
               patient_cpf=create_data.patient_cpf,
               doctor_crm=create_data.doctor_crm,
               event_type=create_data.event_type,
               ciap2_code=create_data.ciap2_code,
               cid10_code=create_data.cid10_code,
               soap_method=create_data.soap_method,
               event_data=create_data.event_data,
               ip_address=create_data.ip_address,
               user_agent=create_data.user_agent,
               signature_hash=signature_hash,
               created_at=now
           )
           self.db_session.add(db_entry)
           self.db_session.flush()
           return db_entry

       def _read_from_model(self, model: TelemedicinaAuditLog) -> TelemedicinaAuditLogRead:
           return TelemedicinaAuditLogRead.model_validate(model)

       def get_session_logs(self, session_id: str) -> List[TelemedicinaAuditLogRead]:
           logs = self.db_session.query(TelemedicinaAuditLog).filter(
               TelemedicinaAuditLog.session_id == session_id
           ).order_by(TelemedicinaAuditLog.created_at).all()
           return [self._read_from_model(log) for log in logs]

       def verify_integrity(self, log_id: int) -> bool:
           log = self.db_session.query(TelemedicinaAuditLog).filter(TelemedicinaAuditLog.id == log_id).first()
           if not log:
               return False
           expected_hash = self._generate_secure_timestamp_hash(
               log.session_id, log.event_type.value, log.created_at
           )
           return hmac.compare_digest(expected_hash, log.signature_hash)
   ```
   Wait, I need to import `EventType` from the model. I'll adjust imports. Also, Pydantic v2 uses `model_validate`. I'll make sure types are correct.
   I should also add type hints strictly as requested. Python 3.12 supports `X | Y` syntax.
   Let's refine the repository to be more robust and strictly typed.

   Also, the prompt mentions "carimbo de data/hora seguro". In Brazil, this often refers to `RFC 3161` or similar, but for a repository, a cryptographic hash with a secret key or a trusted timestamp service is common. I'll stick to HMAC-SHA256 for simplicity but note it can be swapped for a TSP. I'll add a method to verify it.

   I need to create the model file as well? The prompt says "implemente backend/app/repositories/auditoria_telemedicina.py". I'll include the model and schemas in the same file or assume they exist. To make it self-contained and executable, I'll put everything in one file or clearly structure it. I'll put the model and schemas in the same file for completeness, or just define them inline. Actually, it's better to keep them separate in a real project, but for this task, I'll include them in the same file or provide them as needed. I'll stick to defining them in the same file to ensure it's executable.

   Let's structure `backend/app/repositories/auditoria_telemedicina.py`:
   - Imports
   - SQLAlchemy Model
   - Pydantic Schemas
   - Repository Class
   - I'll also provide `tests/test_auditoria_telemedicina.py`

   Wait, the prompt says "implemente backend/app/repositories/auditoria_telemedicina.py com a classe AuditoriaTelemedicinaRepository". I'll focus on that file. I'll include necessary models/schemas in it or import them. To be safe, I'll define them in the same file.

   Let's draft the file carefully.

   **File: `backend/app/repositories/auditoria_telemedicina.py`**
   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   from __future__ import annotations

   import hashlib
   import hmac
   from datetime import datetime
   from enum import Enum
   from typing import List, Optional

   from pydantic import BaseModel, ConfigDict, Field
   from sqlalchemy import Column, DateTime, Enum as SAEnum, Integer, JSON, String
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

   # --- SQLAlchemy 2.0 Model ---
   class Base(DeclarativeBase):
       pass

   class EventType(str, Enum):
       CONNECTION = "connection"
       DISCONNECTION = "disconnection"
       TERMS_ACCEPTANCE = "terms_acceptance"

   class TelemedicinaAuditLog(Base):
       __tablename__ = "telemedicina_audit_logs"

       id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
       session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
       patient_cns: Mapped[str | None] = mapped_column(String(15), nullable=True)
       patient_cpf: Mapped[str | None] = mapped_column(String(14), nullable=True)
       doctor_crm: Mapped[str | None] = mapped_column(String(20), nullable=True)
       event_type: Mapped[EventType] = mapped_column(SAEnum(EventType), nullable=False)
       ciap2_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
       cid10_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
       soap_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
       event_data: Mapped[dict] = mapped_column(JSON, nullable=True)
       ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
       user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
       signature_hash: Mapped[str] = mapped_column(String(64), nullable=False)
       created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

   # --- Pydantic v2 Schemas ---
   class EventTypeEnum(str, Enum):
       CONNECTION = "connection"
       DISCONNECTION = "disconnection"
       TERMS_ACCEPTANCE = "terms_acceptance"

   class TelemedicinaAuditLogCreate(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True)
       session_id: str = Field(..., min_length=1, max_length=36)
       patient_cns: str | None = Field(None, pattern=r"^\d{15}$")
       patient_cpf: str | None = Field(None, pattern=r"^\d{11}$")
       doctor_crm: str | None = None
       event_type: EventTypeEnum
       ciap2_code: str | None = Field(None, pattern=r"^[A-Z0-9]{1,10}$")
       cid10_code: str | None = Field(None, pattern=r"^[A-Z]\d{2}$")
       soap_method: str | None = Field(None, pattern=r"^(S|O|A|P|SOAP)$")
       event_data: dict | None = None
       ip_address: str | None = None
       user_agent: str | None = None

   class TelemedicinaAuditLogRead(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: int
       session_id: str
       patient_cns: str | None
       patient_cpf: str | None
       doctor_crm: str | None
       event_type: EventTypeEnum
       ciap2_code: str | None
       cid10_code: str | None
       soap_method: str | None
       event_data: dict | None
       ip_address: str | None
       user_agent: str | None
       signature_hash: str
       created_at: datetime

   # --- Repository ---
   class AuditoriaTelemedicinaRepository:
       def __init__(self, db_session: Session, secret_key: str = "media_audit_secret_key_2024") -> None:
           self.db_session = db_session
           self.secret_key = secret_key

       def _generate_secure_timestamp_hash(self, session_id: str, event_type: str, created_at: datetime) -> str:
           """Gera hash criptográfico para carimbo de data/hora seguro (integridade)."""
           data = f"{session_id}:{event_type}:{created_at.isoformat()}"
           return hmac.new(self