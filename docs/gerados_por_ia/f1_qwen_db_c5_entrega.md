Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Implement `backend/app/repositories/auditoria_telemedicina.py` with a class `AuditoriaTelemedicinaRepository` for logging teleconsultation events (connection, disconnection, patient confidentiality agreement acceptance, secure timestamping) using SQLAlchemy 2.0.
   - **Guidelines:** Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), full compliance with automated tests using pytest.
   - **Output Requirement:** Provide complete, executable code. Specify file paths at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/auditoria_telemedicina.py`
   - **Class:** `AuditoriaTelemedicinaRepository`
   - **Features:**
     - Log connection events
     - Log disconnection events
     - Log patient confidentiality agreement acceptance (LGPD/CFM)
     - Secure timestamping
     - Use SQLAlchemy 2.0 (async/sync? I'll assume async as it's modern, but I'll make it compatible or explicitly use `sqlalchemy.orm` with async session if needed. I'll stick to sync for simplicity unless specified, but modern Python 3.12 + FastAPI usually uses async. I'll provide async-compatible code or clearly state it. Actually, I'll use `sqlalchemy` 2.0 with `Session` and `AsyncSession` support, but I'll write it in a way that's standard for SQLAlchemy 2.0. I'll use `sqlalchemy.orm` with `DeclarativeBase`.)
     - Pydantic v2 models for data validation
     - SUS/APS standards: CIAP-2, CID-10, SOAP, CNS/CPF
     - Pytest coverage
   - **Architecture/Standards:**
     - Need models for audit logs
     - Need Pydantic schemas for input/output
     - Need repository class with methods for each event type
     - Need secure timestamping (UTC, timezone-aware, possibly cryptographic signing/hashing for integrity? The prompt says "carimbo de data/hora seguro", which usually means timezone-aware, immutable, and possibly hashed. I'll implement a method that generates a secure timestamp and optionally hashes the log entry for integrity, but keep it practical.)
     - SUS/APS fields: CNS, CPF, CIAP-2, CID-10, SOAP method

3.  **Design Decisions:**
   - **Database Models:** `TelemedicinaAuditoriaLog` with fields: `id`, `consultation_id`, `patient_cns`, `patient_cpf`, `doctor_id`, `event_type`, `event_data` (JSON), `timestamp_utc`, `ip_address`, `user_agent`, `confidentiality_accepted` (bool), `ciap2_codes`, `cid10_codes`, `soap_method`, `signature_hash` (for secure timestamping/integrity)
   - **Pydantic Models:** `AuditoriaLogCreate`, `AuditoriaLogResponse`
   - **Repository Class:** `AuditoriaTelemedicinaRepository` with methods:
     - `log_connection(session, ...)`
     - `log_disconnection(session, ...)`
     - `log_confidentiality_acceptance(session, ...)`
     - `create_secure_timestamp()` (returns UTC datetime with timezone)
     - `hash_log_entry()` (for integrity)
   - **SQLAlchemy 2.0:** Use `DeclarativeBase`, `Mapped`, `mapped_column`, `Column`, `String`, `DateTime`, `JSON`, `Boolean`, `Text`, `UUID`, etc.
   - **Testing:** `pytest` with `pytest-asyncio` (if async) or sync. I'll write sync for simplicity but note it can be adapted. Actually, I'll use `sqlalchemy.ext.asyncio` for modern stack, but to keep it straightforward and executable, I'll use sync SQLAlchemy 2.0 with `Session`. I'll make sure it's fully typed.
   - **Secure Timestamping:** I'll implement a method that generates a UTC timestamp and creates a cryptographic hash (SHA-256) of the log entry + timestamp for integrity verification. This satisfies "carimbo de data/hora seguro".
   - **SUS/APS Standards:** Include fields for CNS, CPF, CIAP-2, CID-10, SOAP method in the log data.

4.  **Draft Code - Mental Refinement:**
   Let's structure the file:
   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   from __future__ import annotations
   import hashlib
   import json
   from datetime import datetime, timezone
   from typing import Any, Dict, List, Optional
   from uuid import UUID, uuid4

   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import String, Text, DateTime, Boolean, JSON, func
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

   # ... models ...
   # ... pydantic schemas ...
   # ... repository class ...
   ```

   Wait, SQLAlchemy 2.0 uses `sqlalchemy.orm.DeclarativeBase` and `Mapped`. I'll define the ORM model inside the file or import it. Since the task says "implemente backend/app/repositories/auditoria_telemedicina.py com a classe AuditoriaTelemedicinaRepository", I'll include the ORM model in the same file for completeness, or assume it's in `models`. I'll define it in the same file to make it self-contained and executable.

   Let's define:
   - `Base` for SQLAlchemy
   - `TelemedicinaAuditoriaLog` ORM model
   - Pydantic schemas
   - Repository class

   Secure timestamp: I'll add a method that returns a timezone-aware UTC datetime and a hash of the log payload + timestamp for integrity.

   SUS/APS fields: I'll include them in the `event_data` JSON or as separate columns. Separate columns are better for querying. I'll add `ciap2_codes`, `cid10_codes`, `soap_method` as JSON/Text columns.

   Let's draft carefully.

   **ORM Model:**
   ```python
   class Base(DeclarativeBase):
       pass

   class TelemedicinaAuditoriaLog(Base):
       __tablename__ = "telemedicina_auditoria_log"

       id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
       consultation_id: Mapped[UUID] = mapped_column(String(36), index=True)
       patient_cns: Mapped[Optional[str]] = mapped_column(String(15), index=True)
       patient_cpf: Mapped[Optional[str]] = mapped_column(String(14), index=True)
       doctor_id: Mapped[UUID] = mapped_column(String(36), index=True)
       event_type: Mapped[str] = mapped_column(String(20)) # CONNECTION, DISCONNECTION, CONFIDENTIALITY_ACCEPTANCE
       event_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
       timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       ip_address: Mapped[Optional[str]] = mapped_column(String(45))
       user_agent: Mapped[Optional[str]] = mapped_column(String(255))
       confidentiality_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
       ciap2_codes: Mapped[List[str]] = mapped_column(JSON, default=list)
       cid10_codes: Mapped[List[str]] = mapped_column(JSON, default=list)
       soap_method: Mapped[Optional[str]] = mapped_column(String(50))
       signature_hash: Mapped[Optional[str]] = mapped_column(String(64)) # SHA-256
   ```

   **Pydantic Schemas:**
   ```python
   class AuditoriaLogCreate(BaseModel):
       consultation_id: UUID
       patient_cns: Optional[str] = None
       patient_cpf: Optional[str] = None
       doctor_id: UUID
       event_type: str
       event_data: Dict[str, Any] = Field(default_factory=dict)
       ip_address: Optional[str] = None
       user_agent: Optional[str] = None
       confidentiality_accepted: bool = False
       ciap2_codes: List[str] = Field(default_factory=list)
       cid10_codes: List[str] = Field(default_factory=list)
       soap_method: Optional[str] = None

       @field_validator("event_type")
       @classmethod
       def validate_event_type(cls, v: str) -> str:
           allowed = {"CONNECTION", "DISCONNECTION", "CONFIDENTIALITY_ACCEPTANCE"}
           if v.upper() not in allowed:
               raise ValueError(f"event_type must be one of {allowed}")
           return v.upper()

       @field_validator("patient_cpf")
       @classmethod
       def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
           if v:
               cleaned = v.replace(".", "").replace("-", "")
               if len(cleaned) != 11 or not cleaned.isdigit():
                   raise ValueError("CPF must be 11 digits")
           return v

       @field_validator("patient_cns")
       @classmethod
       def validate_cns(cls, v: Optional[str]) -> Optional[str]:
           if v:
               cleaned = v.replace("-", "")
               if len(cleaned) != 15 or not cleaned.isdigit():
                   raise ValueError("CNS must be 15 digits")
           return v
   ```

   **Repository Class:**
   ```python
   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: Session):
           self.session = session

       def create_secure_timestamp(self) -> datetime:
           return datetime.now(timezone.utc)

       def _compute_signature_hash(self, data: Dict[str, Any], timestamp: datetime) -> str:
           payload = json.dumps(data, sort_keys=True, default=str) + str(timestamp.isoformat())
           return hashlib.sha256(payload.encode("utf-8")).hexdigest()

       def log_connection(self, dto: AuditoriaLogCreate) -> TelemedicinaAuditoriaLog:
           now = self.create_secure_timestamp()
           log = TelemedicinaAuditoriaLog(
               consultation_id=dto.consultation_id,
               patient_cns=dto.patient_cns,
               patient_cpf=dto.patient_cpf,
               doctor_id=dto.doctor_id,
               event_type="CONNECTION",
               event_data=dto.event_data,
               timestamp_utc=now,
               ip_address=dto.ip_address,
               user_agent=dto.user_agent,
               confidentiality_accepted=dto.confidentiality_accepted,
               ciap2_codes=dto.ciap2_codes,
               cid10_codes=dto.cid10_codes,
               soap_method=dto.soap_method,
               signature_hash=self._compute_signature_hash(dto.model_dump(), now),
           )
           self.session.add(log)
           self.session.flush()
           return log

       def log_disconnection(self, dto: AuditoriaLogCreate) -> TelemedicinaAuditoriaLog:
           now = self.create_secure_timestamp()
           log = TelemedicinaAuditoriaLog(
               consultation_id=dto.consultation_id,
               patient_cns=dto.patient_cns,
               patient_cpf=dto.patient_cpf,
               doctor_id=dto.doctor_id,
               event_type="DISCONNECTION",
               event_data=dto.event_data,
               timestamp_utc=now,
               ip_address=dto.ip_address,
               user_agent=dto.user_agent,
               confidentiality_accepted=dto.confidentiality_accepted,
               ciap2_codes=dto.ciap2_codes,
               cid10_codes=dto.cid10_codes,
               soap_method=dto.soap_method,
               signature_hash=self._compute_signature_hash(dto.model_dump(), now),
           )
           self.session.add(log)
           self.session.flush()
           return log

       def log_confidentiality_acceptance(self, dto: AuditoriaLogCreate) -> TelemedicinaAuditoriaLog:
           if not dto.confidentiality_accepted:
               raise ValueError("Confidentiality acceptance must be True for this event.")
           now = self.create_secure_timestamp()
           log = TelemedicinaAuditoriaLog(
               consultation_id=dto.consultation_id,
               patient_cns=dto.patient_cns,
               patient_cpf=dto.patient_cpf,
               doctor_id=dto.doctor_id,
               event_type="CONFIDENTIALITY_ACCEPTANCE",
               event_data=dto.event_data,
               timestamp_utc=now,
               ip_address=dto.ip_address,
               user_agent=dto.user_agent,
               confidentiality_accepted=True,
               ciap2_codes=dto.ciap2_codes,
               cid10_codes=dto.cid10_codes,
               soap_method=dto.soap_method,
               signature_hash=self._compute_signature_hash(dto.model_dump(), now),
           )
           self.session.add(log)
           self.session.flush()
           return log
   ```

   Wait, the prompt says "carimbo de data/hora seguro". I should make sure the timestamp is immutable and cryptographically bound. The `_compute_signature_hash` does that. I'll also add a method to verify integrity.

   Let's add verification:
   ```python
       def verify_log_integrity(self, log: TelemedicinaAuditoriaLog) -> bool:
           expected_hash = self._compute_signature_hash(
               {k: v for k, v in log.__dict__.items() if k != "signature_hash"},
               log.timestamp_utc
           )
           return log.signature_hash == expected_hash
   ```

   Now, I need to provide the pytest tests. The prompt says "Manter conformidade total e cobertura de testes automatizados com pytest." I should provide a test file as well.

   **Test File:** `backend/app/tests/test_auditoria_telemedicina.py`
   I'll use `pytest`, `sqlalchemy`, `unittest.mock` or `pytest-asyncio` if needed. I'll stick to sync for simplicity but make it robust.

   ```python
   # Arquivo: backend/app/tests/test_auditoria_telemedicina.py
   import pytest
   from uuid import uuid4
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from app.repositories.auditoria_telemedicina import (
       Base,
       TelemedicinaAuditoriaLog,
       AuditoriaLogCreate,
       AuditoriaTelemedicinaRepository,
   )

   # In-memory SQLite for testing
   engine = create_engine("sqlite:///:memory:")
   Base.metadata.create_all(engine)
   SessionLocal = sessionmaker(bind=engine)

   @pytest.fixture
   def db_session():
       session = SessionLocal()
       try:
           yield session
       finally:
           session.close()

   @pytest.fixture
   def repo(db_session):
       return AuditoriaTelemedicinaRepository(session=db_session)

   @pytest.fixture
   def valid_dto():
       return AuditoriaLogCreate(
           consultation_id=uuid4(),
           patient_cns="987654321098765",
           patient_cpf="12345678909",
           doctor_id=uuid4(),
           event_type="CONNECTION",
           event_data={"platform": "web", "version": "1.0"},
           ip_address="192.168.1.1",
           user_agent="Mozilla/5.0",
           confidentiality_accepted=True,
           ciap2_codes=["A01"],
           cid10_codes=["J06.9"],
           soap_method="SOAP",
       )

   def test_create_secure_timestamp_is_utc(repo):
       ts = repo.create_secure_timestamp()
       assert ts.tzinfo is not None
       assert ts.tzname() == "UTC"

   def test_log_connection_creates_record(repo, db_session, valid_dto):
       log = repo.log_connection(valid_dto)
       db_session.flush()
       db_session.refresh(log)

       assert log.event_type == "CONNECTION"
       assert log.patient_cns == valid_dto.patient_cns
       assert log.patient_cpf == valid_dto.patient_cpf
       assert log.confidentiality_accepted is True
       assert log.signature_hash is not None
       assert repo.verify_log_integrity(log) is True

   def test_log_disconnection_creates_record(repo, db_session, valid_dto):
       valid_dto.event_type = "DISCONNECTION"
       log = repo.log_disconnection(valid_dto)
       db_session.flush()
       db_session.refresh(log)

       assert log.event_type == "DISCONNECTION"
       assert repo.verify_log_integrity(log) is True

   def test_log_confidentiality_acceptance_validates_true(repo, db_session):
       dto = AuditoriaLogCreate(
           consultation_id=uuid4(),
           doctor_id=uuid4(),
           event_type="CONFIDENTIALITY_ACCEPTANCE",
           confidentiality_accepted=True,
       )
       log = repo.log_confidentiality_acceptance(dto)
       db_session.flush()
       db_session.refresh(log)
       assert log.confidentiality_accepted is True

   def test_log_confidentiality_acceptance_rejects_false(repo):
       dto = AuditoriaLogCreate(
           consultation_id=uuid4(),
           doctor_id=uuid4(),
           event_type="CONFIDENTIALITY_ACCEPTANCE",
           confidentiality_accepted=False,
       )
       with pytest.raises(ValueError, match="Confidentiality acceptance must be True"):
           repo.log_confidentiality_acceptance(dto)

   def test_cpf_validation(repo):
       with pytest.raises(ValueError, match="CPF must be 11 digits"):
           AuditoriaLogCreate(
               consultation_id=uuid4(),
               doctor_id=uuid4(),
               event_type="CONNECTION",
               patient_cpf="123",
           )

   def test_cns_validation(repo):
       with pytest.raises(ValueError, match="CNS must be 15 digits"):
           AuditoriaLogCreate(
               consultation_id=uuid4(),
               doctor_id=uuid4(),
               event_type="CONNECTION",