Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/offline_cache_repo.py` for a project called "MedIA".
   - **Functionality:** Manage a local queue of pending mutations (outbox pattern), synchronization status (PENDENTE, ENVIADO, CONFLITO), and integrity using SQLAlchemy 2.0.
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards compliance (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Full compliance and coverage with automated pytest tests.
   - **Output Requirement:** Provide complete, executable code. Specify file paths in code blocks.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/offline_cache_repo.py`
   - **Core Features:**
     - Outbox pattern implementation (local queue for pending mutations)
     - Status management: `PENDENTE`, `ENVIADO`, `CONFLITO`
     - SQLAlchemy 2.0 ORM models & queries
     - Pydantic v2 for data validation/serialization
     - SUS/APS standards integration (CIAP-2, CID-10, SOAP, CNS/CPF)
     - Type hints (Python 3.12)
     - Pytest coverage (I'll provide the test file as well, as requested: "cobertura de testes automatizados com pytest")
   - **Constraints:** Complete, executable, strict typing, specific architecture.

3.  **Design the Solution:**
   - **Database Model (SQLAlchemy 2.0):**
     - Table: `offline_cache_mutation`
     - Fields: `id` (UUID), `entity_type` (str), `entity_id` (str), `payload` (JSON), `status` (Enum), `created_at`, `updated_at`, `error_message` (nullable), `sync_attempt_count` (int)
     - Status Enum: `PENDENTE`, `ENVIADO`, `CONFLITO`
   - **Pydantic Models:**
     - `OfflineCacheMutationCreate` (for input)
     - `OfflineCacheMutationResponse` (for output)
     - `SyncStatus` (enum)
   - **Repository Class:**
     - `OfflineCacheRepository`
     - Methods:
       - `add_mutation()`
       - `get_pending_mutations()`
       - `mark_as_sent()`
       - `mark_as_conflict()`
       - `get_by_id()`
       - `update_status()`
       - `cleanup_old_sent()` (optional but good practice)
     - Use SQLAlchemy 2.0 async/sync? I'll stick to sync for simplicity but note it can be adapted. Actually, modern apps often use async, but I'll provide sync with explicit session management or use a dependency injection pattern. I'll use a standard sync approach with `Session` for clarity, but ensure it's compatible with SQLAlchemy 2.0 syntax.
   - **SUS/APS Standards Integration:**
     - Validate CNS/CPF format in payload or as separate fields? I'll add validation for CNS/CPF in the Pydantic model or as a utility.
     - Support CIAP-2 and CID-10 codes in the payload.
     - SOAP method structure in payload.
     - I'll create a Pydantic model that enforces these standards.
   - **Testing (Pytest):**
     - Test setup with SQLite in-memory DB
     - Test each repository method
     - Test validation (CNS/CPF, CIAP-2, CID-10, SOAP)
     - Test status transitions
     - Ensure coverage

4.  **Draft - Code Structure:**

   *File 1: `backend/app/repositories/offline_cache_repo.py`*
   - Imports: SQLAlchemy 2.0, Pydantic v2, Enums, UUID, datetime, JSON, typing
   - Models: `OfflineCacheMutation` (SQLAlchemy), `MutationPayload` (Pydantic with SUS/APS validation)
   - Repository: `OfflineCacheRepository`
   - Helper: CNS/CPF validation, CIAP-2/CID-10 format checks

   *File 2: `backend/app/repositories/test_offline_cache_repo.py`*
   - Pytest fixtures (DB session)
   - Test cases for all repo methods
   - Validation tests
   - Status transition tests

5.  **Refine - Implementation Details (Mental Walkthrough):**

   *SQLAlchemy Model:*
   ```python
   from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum, ForeignKey
   from sqlalchemy.orm import DeclarativeBase
   from sqlalchemy.dialects.postgresql import UUID as PG_UUID
   import uuid
   from datetime import datetime
   from enum import Enum as PyEnum

   class Base(DeclarativeBase):
       pass

   class SyncStatus(PyEnum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutation"
       id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       entity_type = Column(String, nullable=False)
       entity_id = Column(String, nullable=False)
       payload = Column(JSON, nullable=False)
       status = Column(Enum(SyncStatus, name="sync_status_enum"), nullable=False, default=SyncStatus.PENDENTE)
       created_at = Column(DateTime, default=datetime.utcnow)
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
       error_message = Column(String, nullable=True)
       sync_attempt_count = Column(Integer, default=0)
   ```
   *Wait*, SQLAlchemy 2.0 prefers `sa.Enum` or `sqlalchemy.Enum`. I'll use `sqlalchemy.Enum`. Also, `PG_UUID` is fine, but I'll use `sa.Uuid` for SQLAlchemy 2.0 compatibility. Actually, `sa.Uuid` is available in 2.0. I'll stick to `sa.String` for UUID to avoid dialect issues, or use `sa.Uuid`. Let's use `sa.String` for simplicity and cross-dialect compatibility, or `sa.Uuid` with `uuid.UUID`. I'll use `sa.String` for UUID to keep it simple and robust.

   *Pydantic Models:*
   Need to enforce SUS/APS standards. I'll create a `MutationPayload` model that validates:
   - `cns` or `cpf` (with regex/validation)
   - `cid10_codes` (list of strings matching CID-10 pattern)
   - `ciap2_codes` (list of strings matching CIAP-2 pattern)
   - `soap_method` (dict with S, O, A, D)
   I'll add custom validators.

   *Repository:*
   ```python
   class OfflineCacheRepository:
       def __init__(self, session):
           self.session = session

       def add_mutation(self, entity_type: str, entity_id: str, payload: dict) -> OfflineCacheMutation:
           ...
       def get_pending_mutations(self, limit: int = 100) -> list[OfflineCacheMutation]:
           ...
       def mark_as_sent(self, mutation_id: uuid.UUID) -> None:
           ...
       def mark_as_conflict(self, mutation_id: uuid.UUID, error: str) -> None:
           ...
       ...
   ```

   *SUS/APS Validation:*
   CNS: 15 digits, starts with 7, 8, or 9. CPF: 11 digits, validation algorithm.
   CID-10: 1-2 letters + 1-3 digits (e.g., A00, J18.9)
   CIAP-2: 1 letter + 1-2 digits (e.g., A0, B12)
   SOAP: S, O, A, D keys present.
   I'll implement regex validators in Pydantic.

   *Testing:*
   Use `pytest`, `sqlalchemy`, `pytest-asyncio` (if async, but I'll stick to sync for simplicity unless specified). I'll use sync SQLAlchemy with `sessionmaker`.
   Fixtures: `db_engine`, `db_session`, `repo`.
   Tests: CRUD, status transitions, validation, conflict handling.

6.  **Write Code (Mental to Text):**

   I'll structure the response carefully.
   First, `backend/app/repositories/offline_cache_repo.py`
   Then, `backend/app/repositories/test_offline_cache_repo.py`

   Let's draft the repository file carefully with SQLAlchemy 2.0 syntax:
   ```python
   from __future__ import annotations
   import uuid
   from datetime import datetime
   from enum import Enum as PyEnum
   from typing import Any, Optional

   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy import (
       Column, String, Integer, DateTime, JSON, Enum as SAEnum,
       create_engine, select, update, delete
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
   import re

   # --- SQLAlchemy 2.0 Model ---
   class Base(DeclarativeBase):
       pass

   class SyncStatus(PyEnum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutation"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
       entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
       payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
       status: Mapped[SyncStatus] = mapped_column(SAEnum(SyncStatus, name="sync_status_enum"), default=SyncStatus.PENDENTE, nullable=False)
       created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
       error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
       sync_attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

   # --- Pydantic Models (SUS/APS Standards) ---
   class MutationPayload(BaseModel):
       model_config = ConfigDict(extra="forbid")

       cns: Optional[str] = Field(None, pattern=r"^[789]\d{14}$")
       cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       cid10_codes: list[str] = Field(default_factory=list, min_length=0)
       ciap2_codes: list[str] = Field(default_factory=list, min_length=0)
       soap_method: dict[str, str] = Field(default_factory=dict)

       @field_validator("cpf")
       @classmethod
       def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
           if v is None:
               return v
           # CPF validation algorithm
           if not re.match(r"^\d{11}$", v):
               raise ValueError("CPF deve ter 11 dígitos numéricos")
           # Simplified validation for demo (full algorithm omitted for brevity but structure is here)
           return v

       @field_validator("cid10_codes")
       @classmethod
       def validate_cid10(cls, v: list[str]) -> list[str]:
           pattern = re.compile(r"^[A-Z]\d{1,3}(\.\d{1,2})?$")
           for code in v:
               if not pattern.match(code):
                   raise ValueError(f"CID-10 inválido: {code}")
           return v

       @field_validator("ciap2_codes")
       @classmethod
       def validate_ciap2(cls, v: list[str]) -> list[str]:
           pattern = re.compile(r"^[A-Z]\d{1,2}$")
           for code in v:
               if not pattern.match(code):
                   raise ValueError(f"CIAP-2 inválido: {code}")
           return v

       @field_validator("soap_method")
       @classmethod
       def validate_soap(cls, v: dict[str, str]) -> dict[str, str]:
           required_keys = {"S", "O", "A", "D"}
           if not required_keys.issubset(v.keys()):
               raise ValueError("SOAP method deve conter as chaves S, O, A, D")
           return v

   # --- Repository ---
   class OfflineCacheRepository:
       def __init__(self, session: Session):
           self.session = session

       def add_mutation(self, entity_type: str, entity_id: str, payload: MutationPayload) -> OfflineCacheMutation:
           mutation = OfflineCacheMutation(
               entity_type=entity_type,
               entity_id=entity_id,
               payload=payload.model_dump(),
               status=SyncStatus.PENDENTE
           )
           self.session.add(mutation)
           self.session.flush()
           return mutation

       def get_pending_mutations(self, limit: int = 100) -> list[OfflineCacheMutation]:
           stmt = select(OfflineCacheMutation).where(
               OfflineCacheMutation.status == SyncStatus.PENDENTE
           ).order_by(OfflineCacheMutation.created_at.asc()).limit(limit)
           return list(self.session.scalars(stmt).all())

       def mark_as_sent(self, mutation_id: uuid.UUID) -> None:
           stmt = (
               update(OfflineCacheMutation)
               .where(OfflineCacheMutation.id == mutation_id)
               .values(status=SyncStatus.ENVIADO, updated_at=datetime.utcnow())
           )
           self.session.execute(stmt)
           self.session.flush()

       def mark_as_conflict(self, mutation_id: uuid.UUID, error_message: str) -> None:
           stmt = (
               update(OfflineCacheMutation)
               .where(OfflineCacheMutation.id == mutation_id)
               .values(
                   status=SyncStatus.CONFLITO,
                   error_message=error_message,
                   sync_attempt_count=OfflineCacheMutation.sync_attempt_count + 1,
                   updated_at=datetime.utcnow()
               )
           )
           self.session.execute(stmt)
           self.session.flush()

       def get_by_id(self, mutation_id: uuid.UUID) -> Optional[OfflineCacheMutation]:
           return self.session.get(OfflineCacheMutation, mutation_id)

       def cleanup_sent_mutations(self, older_than_days: int = 30) -> int:
           cutoff = datetime.utcnow().days - older_than_days # Wait, datetime subtraction
           # Better:
           from datetime import timedelta
           cutoff = datetime.utcnow() - timedelta(days=older_than_days)
           stmt = delete(OfflineCacheMutation).where(
               OfflineCacheMutation.status == SyncStatus.ENVIADO,
               OfflineCacheMutation.updated_at < cutoff
           )
           result = self.session.execute(stmt)
           self.session.flush()
           return result.rowcount
   ```
   *Self-Correction/Refinement during drafting:*
   - `datetime.utcnow()` is deprecated in Python 3.12+. I should use `datetime.now(datetime.timezone.utc)` or `datetime.now(tz=timezone.utc)`.
   - `mapped_column` syntax is correct for SQLAlchemy 2.0.
   - Pydantic v2 uses `field_validator` correctly.
   - I'll fix the datetime issue.
   - I'll add proper imports.
   - I'll ensure the repository handles transactions properly (caller usually manages commit/rollback, but I'll note it).
   - I'll make sure the code is complete and runnable.

   Let's fix the datetime:
   ```python
   from datetime import datetime, timedelta, timezone
   # ...
   now = datetime.now(timezone.utc)
   # ...
   ```

   Now, the test file. I'll write comprehensive pytest tests.
   Structure:
   - `conftest.py` or inline fixtures
   - Test DB setup (SQLite in-memory)
   - Test cases for each method
   - Validation tests
   - Status transition tests
   - Coverage requirements (I'll aim for >90% by testing edge cases)

   *Test File Draft:*
   ```python
   import pytest
   import uuid
   from datetime import datetime, timedelta, timezone
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker

   from backend.app.repositories.offline_cache_repo import (
       Base, SyncStatus, OfflineCacheMutation, OfflineCacheRepository, MutationPayload
   )

   @pytest.fixture
   def engine():
       return create_engine("sqlite:///:memory:")

   @pytest.fixture
   def session_factory(engine):
       Base.metadata.create_all(engine)
       return sessionmaker(bind=engine, expire_on_commit=False)

   @pytest.fixture
   def repo(session_factory):
       with session_factory() as session:
           yield OfflineCacheRepository(session)
           session.rollback() # Clean up after each test

   # Tests...
   ```
   I'll flesh out the tests carefully.

   *Key Test Cases:*
   1. `test_add_mutation_creates_pending_record`
   2. `test_get_pending_mutations_returns_only_pending`
   3. `test_mark_as_sent_updates_status`
   4. `test_mark_as_conflict_updates_status_and_error`
   5. `test_cleanup_sent_mutations_removes_old_records`
   6. `test_mutation_payload_validates_cpf`
   7. `test_mutation_payload_validates_cid10`
   8. `test_mutation_payload_validates_ciap2`
   9. `test_mutation_payload_validates_soap`
   10. `test_mutation_payload_validates_cns`
   11. `test_status_transitions`
   12. `test_get_by_id`

   I'll write them out properly with assertions.

   *Check SUS/APS Standards:*
   - CNS: 15 digits, starts with 7/8/9. Regex: