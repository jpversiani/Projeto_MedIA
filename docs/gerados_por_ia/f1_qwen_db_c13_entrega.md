Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Implement `backend/app/repositories/auditoria_telemedicina.py` with a class `AuditoriaTelemedicinaRepository` for logging teleconsultation events (connection, disconnection, patient confidentiality agreement acceptance, secure timestamping) using SQLAlchemy 2.0.
   - **Context:** Project MedIA, Brazilian SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), LGPD/CFM compliance.
   - **Requirements:** Python 3.12, strict typing with Pydantic v2, SQLAlchemy 2.0, full test coverage with pytest, complete executable code.

2.  **Key Components to Implement:**
   - **Database Model:** SQLAlchemy 2.0 declarative model for audit logs.
   - **Repository Class:** `AuditoriaTelemedicinaRepository` with methods for logging events.
   - **Pydantic Models:** For request/response validation (though the task focuses on the repository, I'll include necessary Pydantic schemas for type hints).
   - **Secure Timestamping:** Use UTC, timezone-aware datetimes, possibly cryptographic hashing or integrity checks (though standard DB timestamps are usually sufficient, I'll ensure strict UTC handling and maybe add a hash for tamper-evidence if needed, but keep it practical).
   - **SUS/APS Standards:** Include fields for CNS, CPF, CIAP-2, CID-10, SOAP method.
   - **LGPD/CFM Compliance:** Explicit fields for patient confidentiality agreement acceptance (timestamp, IP, user agent).
   - **Testing:** Comprehensive pytest suite covering all repository methods, edge cases, and database interactions.

3.  **Design Decisions:**
   - **Database Model (`TelemedicinaAuditoriaLog`):**
     - `id`: UUID primary key
     - `session_id`: UUID (teleconsultation session)
     - `patient_cns`: Optional[str] (Conselho Nacional de Saúde)
     - `patient_cpf`: Optional[str] (masked or hashed for LGPD? I'll store raw but note it should be encrypted in prod. For now, string.)
     - `event_type`: Enum (CONNECTION, DISCONNECTION, CONSENT_ACCEPTANCE, etc.)
     - `event_data`: JSONB (flexible for CIAP-2, CID-10, SOAP, IP, User-Agent, etc.)
     - `timestamp_utc`: DateTime (timezone-aware, UTC)
     - `created_at`: DateTime (auto)
     - `updated_at`: DateTime (auto)
     - `integrity_hash`: String (for tamper detection - optional but good for "secure timestamping")
   - **Repository Methods:**
     - `log_connection(session_id, patient_cns, patient_cpf, ip_address, user_agent)`
     - `log_disconnection(session_id, duration_seconds, reason)`
     - `log_consent_acceptance(session_id, patient_cns, patient_cpf, ip_address, user_agent, timestamp_utc)`
     - `get_session_logs(session_id)`
     - `get_logs_by_patient(patient_cns, patient_cpf)`
     - Helper to generate secure timestamp/hash
   - **Pydantic Models:** For type hints in repository methods.
   - **Testing:** Use `pytest`, `pytest-asyncio` (if async, but I'll stick to sync for simplicity unless specified, but SQLAlchemy 2.0 supports both. I'll use sync for straightforward testing, or async if preferred. The prompt says SQLAlchemy 2.0, doesn't specify async. I'll use sync for broader compatibility, but add async support if needed. Actually, I'll stick to sync for simplicity and reliability in testing.)
   - **Database Setup:** Use SQLite in-memory for testing, PostgreSQL for prod (via config). I'll provide a base engine/session factory.

4.  **Implementation Details (Mental Draft):**
   - *Model:*
     ```python
     from sqlalchemy import Column, String, DateTime, Enum, JSON, BigInteger, func
     from sqlalchemy.orm import DeclarativeBase
     import enum
     import uuid
     from datetime import datetime, timezone

     class EventType(str, enum.Enum):
         CONNECTION = "CONNECTION"
         DISCONNECTION = "DISCONNECTION"
         CONSENT_ACCEPTANCE = "CONSENT_ACCEPTANCE"
         SOAP_UPDATE = "SOAP_UPDATE"
         CID_UPDATE = "CID_UPDATE"
         CIAP_UPDATE = "CIAP_UPDATE"

     class Base(DeclarativeBase):
         pass

     class TelemedicinaAuditoriaLog(Base):
         __tablename__ = "telemedicina_auditoria_logs"
         id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
         session_id = Column(String(36), nullable=False, index=True)
         patient_cns = Column(String(15), nullable=True, index=True)
         patient_cpf = Column(String(14), nullable=True, index=True)
         event_type = Column(Enum(EventType), nullable=False)
         event_data = Column(JSON, nullable=True)
         timestamp_utc = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
         created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
         updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
         integrity_hash = Column(String(64), nullable=False)
     ```
   - *Repository:*
     Need to inject `Session` or use a session factory. I'll use a class-based approach with dependency injection pattern or accept a session in methods. For simplicity and testability, I'll make it accept a `Session` in `__init__` or use a classmethod/factory. Actually, standard repository pattern in SQLAlchemy 2.0 often uses a session passed to methods or injected. I'll use a class that takes a `Session` in `__init__`.
     Methods will validate inputs, create model instances, add to session, commit.
     Secure timestamping: I'll use `datetime.now(timezone.utc)` and generate an HMAC or SHA256 hash of the log data + timestamp for integrity.
     LGPD/CFM: Explicit fields for consent, IP, User-Agent stored in `event_data`.
     SUS/APS: CIAP-2, CID-10, SOAP stored in `event_data`.

   - *Pydantic Models:*
     ```python
     from pydantic import BaseModel, Field, field_validator
     from datetime import datetime
     import re

     class ConsentAcceptanceData(BaseModel):
         ip_address: str
         user_agent: str
         timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

     class ConnectionData(BaseModel):
         ip_address: str
         user_agent: str

     class DisconnectionData(BaseModel):
         duration_seconds: float
         reason: str

     class ClinicalData(BaseModel):
         ciap2_codes: list[str] = Field(default_factory=list)
         cid10_codes: list[str] = Field(default_factory=list)
         soap_method: str = Field(default="SOAP")
     ```
   - *Repository Class:*
     ```python
     class AuditoriaTelemedicinaRepository:
         def __init__(self, session: Session):
             self.session = session

         def _generate_integrity_hash(self, data: dict, timestamp: datetime) -> str:
             import hashlib
             import hmac
             import os
             key = os.environ.get("AUDIT_KEY", "default_secret_key_for_dev").encode()
             content = f"{timestamp.isoformat()}|{json.dumps(data, sort_keys=True)}".encode()
             return hmac.new(key, content, hashlib.sha256).hexdigest()

         def log_consent_acceptance(self, session_id: str, patient_cns: str | None, patient_cpf: str | None, consent_data: ConsentAcceptanceData) -> None:
             # validate, create model, add, commit
             ...
     ```
   - *Testing:*
     Need `pytest`, `sqlalchemy`, `pytest-mock` or just use `sessionmaker` with SQLite.
     I'll create a test file `tests/test_auditoria_telemedicina_repository.py` with fixtures for DB session, and test each method.
     Ensure strict typing, coverage, edge cases (invalid CPF/CNS, timezone handling, hash verification).

5.  **Refine & Structure Output:**
   - I'll provide two files:
     1. `backend/app/repositories/auditoria_telemedicina.py` (Repository + Models + Pydantic schemas)
     2. `tests/test_auditoria_telemedicina_repository.py` (Comprehensive pytest suite)
   - I'll ensure Python 3.12 syntax (type hints, `|` union, `match` if needed, but not necessary here).
   - I'll add comments explaining SUS/APS, LGPD/CFM compliance.
   - I'll make sure the code is executable and follows SQLAlchemy 2.0 best practices (using `session.execute`, `session.add`, `session.commit`, `select` for queries).
   - I'll handle timezone strictly with `datetime.now(timezone.utc)`.
   - I'll add integrity hash for tamper-evidence.
   - I'll include proper error handling (e.g., `sqlalchemy.exc.SQLAlchemyError`).

   Let's draft the code carefully.

   *Self-Correction/Verification during drafting:*
   - SQLAlchemy 2.0 uses `session.execute(select(...))` and `session.commit()`.
   - Pydantic v2 uses `model_dump()` instead of `dict()`.
   - Type hints: `str | None` is Python 3.10+. I'll use it.
   - For testing, I'll use `pytest` with `pytest-asyncio`? The prompt doesn't specify async. I'll stick to sync for simplicity and reliability, but note it can be adapted. Actually, SQLAlchemy 2.0 is often used with async in modern stacks, but sync is fine. I'll use sync to keep tests straightforward.
   - I need to ensure the repository is fully typed and follows the repository pattern.
   - I'll add a `get_logs` method using SQLAlchemy 2.0 `select`.
   - I'll ensure LGPD compliance by noting that CPF/CNS should be encrypted in production, but for the repo, I'll store them as provided with validation.
   - I'll add CIAP-2, CID-10, SOAP fields in `event_data` as per SUS/APS standards.
   - I'll make sure the code is complete and ready to run.

   Structure:
   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   ... code ...
   ```
   ```python
   # Arquivo: tests/test_auditoria_telemedicina_repository.py
   ... code ...
   ```

   Let's write it out carefully.
   *Key considerations for the repository:*
   - Use `Session` from `sqlalchemy.orm`
   - Use `UUID` for IDs
   - Strict UTC timestamps
   - Pydantic v2 for validation
   - SQLAlchemy 2.0 for DB operations
   - SUS/APS fields in JSONB
   - LGPD/CFM consent tracking
   - Integrity hash for tamper detection
   - Comprehensive tests

   I'll now generate the code. 
   I'll make sure to include all necessary imports, type hints, and follow PEP 8.
   I'll add comments explaining compliance aspects.
   I'll ensure the test file uses `pytest` fixtures, covers all methods, and validates edge cases.
   I'll use `sqlite:///:memory:` for testing.
   I'll handle session lifecycle properly in tests.
   I'll use `pytest`'s `caplog` or assertions for hash verification.
   I'll make sure the code is executable as-is (with minor DB config adjustments if needed, but I'll provide a complete setup).

   Let's draft. 
   *Self-Correction/Refinement during thought:*
   - The prompt says "carimbo de data/hora seguro" (secure timestamp). I'll implement a cryptographic hash of the log content + timestamp using HMAC-SHA256. I'll store it and provide a verification method.
   - I'll add a `verify_integrity` method to the repository.
   - I'll ensure Pydantic v2 compatibility (`model_dump()`, `Field`, `field_validator`).
   - I'll use `sqlalchemy.orm.Session` explicitly.
   - I'll add type hints for all methods.
   - I'll make the repository class accept a `Session` in `__init__` for DI.
   - I'll add a `__aenter__`/`__aexit__`? No, keep it simple.
   - I'll ensure the test file is complete and runnable.

   All set. Generating. 
   Output will contain two code blocks with clear paths.
   I'll double-check SQLAlchemy 2.0 syntax: `session.execute(select(...))`, `session.add()`, `session.commit()`, `session.rollback()`.
   Pydantic v2: `BaseModel`, `Field`, `model_dump()`, `field_validator`.
   Python 3.12: `str | None`, `list[str]`, `datetime.now(timezone.utc)`.
   SUS/APS: CIAP-2, CID-10, SOAP, CNS, CPF.
   LGPD/CFM: Consent timestamp, IP, User-Agent, explicit acceptance.
   Secure timestamp: HMAC integrity hash.
   Tests: Fixtures, parameterized tests, edge cases, coverage.
   Ready.✅
   Output matches the response. 
   Proceeds. 
   [Output Generation] -> *See response.* 
   *Self-Correction/Verification during output generation prep:*
   - I need to make sure the repository doesn't hardcode DB credentials. I'll use a `Session` passed in.
   - I'll add a `create_engine` and `SessionLocal` example in comments if needed, but the prompt asks for the repository file specifically.
   - I'll ensure the test file includes `pytest` imports and fixtures.
   - I'll add `# Arquivo: ...` as requested.
   - I'll make sure the code is strictly typed and executable.
   - All good.✅
   Output matches the final response. 
   [Done.] 
   *Output Generation* (matches the final response)
   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   ...
   ```
   ```python
   # Arquivo: tests/test_auditoria_telemedicina_repository.py
   ...
   ```
   All constraints met. Proceeds. 
   [Final Check of the Prompt]: "Execute com precisão conforme as diretrizes." -> I will provide the complete code with strict typing, SQLAlchemy 2.0, Pydantic v2, SUS/APS compliance, LGPD/CFM compliance, secure timestamps, and full pytest coverage. I'll add necessary comments for clarity. All good. 
   Output matches response.✅
Aqui está a implementação completa e executável, seguindo rigorosamente as diretrizes: Python 3.12, tipagem estrita, Pydantic v2, SQLAlchemy 2.0, conformidade SUS/APS, LGPD/CFM e carimbo de data/hora seguro com integridade criptográfica.

```python
# Arquivo: backend/app/repositories/auditoria_telemedicina.py
from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, ClassVar

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Enum as SAEnum, JSON, String, DateTime, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
import enum


# ---------------------------------------------------------------------------
# Pydantic v2 Schemas (Validação Estrita)
# ---------------------------------------------------------------------------
class ConsentAcceptanceData(BaseModel):
    ip_address: str
    user_agent: str
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        if not v or len(v) > 45:
            raise ValueError("IP inválido ou ausente")
        return v


class ConnectionData(BaseModel):
    ip_address: str
    user_agent: str

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        if not v or len(v) > 45:
            raise ValueError("IP inválido ou ausente")
        return v


class DisconnectionData(BaseModel):
    duration_seconds: float
    reason: str

    @field_validator("duration_seconds")
    @classmethod
    def validate_duration(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Duração não pode ser negativa")
        return v


class ClinicalData(BaseModel):
    ciap2_codes: list[str] = Field(default_factory=list, description="CIAP-2 (Classificação Internacional de Atenção Primária)")
    cid10_codes: list[str] = Field(default_factory=list, description="CID-10 (Classificação Internacional de Doenças)")
    soap_method: str = Field(default="SOAP", description="Método de registro clínico (SOAP)")

    @field_validator("soap_method")
    @classmethod
    def validate_soap(cls, v: str) -> str:
        if v.upper() not in ("SOAP", "SOAP-PLUS", "SOAP-EXTENDED"):
            raise ValueError("Método SOAP não suportado")
        return v.upper()


# ---------------------------------------------------------------------------
# SQLAlchemy 2.0 Model
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


class EventType(str, enum.Enum):
    CONNECTION = "CONNECTION"
    DISCONNECTION = "DISCONNECTION"
    CONSENT_ACCEPTANCE = "CONSENT_ACCEPTANCE"
    CLINICAL_UPDATE = "CLINICAL_UPDATE"


class TelemedicinaAuditoriaLog(Base):
    __tablename__ = "telemedicina_auditoria_logs"

    id: Mapped[str] = mapped_column(String(