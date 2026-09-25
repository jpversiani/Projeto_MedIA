Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/offline_cache_repo.py` for a project called "MedIA".
   - **Functionality:** Manage a local queue of pending mutations (outbox pattern), synchronization status (PENDENTE, ENVIADO, CONFLITO), and integrity using SQLAlchemy 2.0.
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards compliance (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Full compliance and coverage with automated pytest tests.
   - **Output Requirement:** Provide complete, executable code. Specify file paths at the beginning of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/offline_cache_repo.py`
   - **Core Features:**
     - Outbox pattern for local mutations queue.
     - Status tracking: `PENDENTE`, `ENVIADO`, `CONFLITO`.
     - SQLAlchemy 2.0 models & repository pattern.
     - Pydantic v2 for data validation/serialization.
     - SUS/APS standards: CIAP-2, CID-10, SOAP, CNS/CPF.
     - Pytest coverage (I need to provide the test file as well, or at least ensure the code is testable and mention tests, but the prompt says "Manter conformidade total e cobertura de testes automatizados com pytest." I should probably provide the test file too, or at least structure the code to be easily testable. I'll provide both the repo and a corresponding test file to be thorough).
   - **Tech Stack:** Python 3.12, SQLAlchemy 2.0, Pydantic v2, pytest.

3.  **Design the Repository (`offline_cache_repo.py`):**
   - **Models:**
     - `OfflineMutation` (SQLAlchemy): id, mutation_type, entity_type, entity_id, payload (JSON), status, created_at, updated_at, error_message, sync_attempt_count.
     - Status enum: `MutationStatus` (PENDENTE, ENVIADO, CONFLITO).
   - **Pydantic Schemas:**
     - `OfflineMutationCreate`, `OfflineMutationRead`, `OfflineMutationUpdate`.
   - **Repository Class:**
     - `OfflineCacheRepository`: methods for CRUD, status updates, batch operations, integrity checks.
     - Use `AsyncSession` or `Session`? I'll stick to synchronous for simplicity unless specified, but SQLAlchemy 2.0 supports both. I'll use `Session` but make it compatible with async if needed. Actually, modern apps prefer async, but I'll stick to sync for straightforwardness, or provide both. I'll use `Session` with type hints.
     - Methods: `add_mutation`, `get_pending_mutations`, `update_status`, `mark_as_sent`, `mark_as_conflict`, `get_mutation`, `cleanup_sent`, `verify_integrity`.
   - **SUS/APS Integration:**
     - The payload should support CNS/CPF, CID-10, CIAP-2, SOAP. I'll add validation/constraints in Pydantic or document it. I'll create a specific Pydantic model for the mutation payload that enforces these standards.
     - `PatientPayload` with `cns` (optional), `cpf` (optional), `cid10_codes` (list), `ciap2_codes` (list), `soap_note` (dict).
     - Actually, the outbox is generic, but I can add a `validate_sus_standards` method or use Pydantic validators.

4.  **Draft Code (Mental Refinement):**
   *File: `backend/app/repositories/offline_cache_repo.py`*
   ```python
   from __future__ import annotations
   import json
   from datetime import datetime
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from uuid import uuid4

   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy import (
       Column,
       String,
       Text,
       DateTime,
       Integer,
       Enum as SAEnum,
       JSON,
       func,
       select,
       update,
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
   from sqlalchemy.dialects.postgresql import JSONB

   # --- Enums ---
   class MutationStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   # --- Pydantic Models ---
   class PatientIdentifier(BaseModel):
       cns: Optional[str] = Field(None, pattern=r"^[0-9]{15}$", description="Cartão Nacional de Saúde")
       cpf: Optional[str] = Field(None, pattern=r"^\d{11}$", description="Cadastro de Pessoas Físicas")

       @field_validator("cns", "cpf")
       @classmethod
       def validate_identifier(cls, v: Optional[str]) -> Optional[str]:
           if v is not None:
               if not v.isdigit():
                   raise ValueError("Identificador deve conter apenas dígitos")
           return v

   class ClinicalData(BaseModel):
       cid10_codes: List[str] = Field(default_factory=list, description="CID-10 codes")
       ciap2_codes: List[str] = Field(default_factory=list, description="CIAP-2 codes")
       soap_note: Optional[Dict[str, str]] = Field(None, description="SOAP method note (S, O, A, P)")

       @field_validator("soap_note")
       @classmethod
       def validate_soap(cls, v: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
           if v is not None:
               allowed_keys = {"S", "O", "A", "P"}
               if not set(v.keys()).issubset(allowed_keys):
                   raise ValueError("SOAP note must only contain keys: S, O, A, P")
           return v

   class OfflineMutationPayload(BaseModel):
       patient: PatientIdentifier
       clinical: ClinicalData
       metadata: Dict[str, Any] = Field(default_factory=dict)

   class OfflineMutationCreate(BaseModel):
       mutation_type: str
       entity_type: str
       entity_id: str
       payload: OfflineMutationPayload
       status: MutationStatus = MutationStatus.PENDENTE

   class OfflineMutationRead(BaseModel):
       id: str
       mutation_type: str
       entity_type: str
       entity_id: str
       payload: OfflineMutationPayload
       status: MutationStatus
       created_at: datetime
       updated_at: datetime
       error_message: Optional[str] = None
       sync_attempt_count: int

       model_config = ConfigDict(from_attributes=True)

   # --- SQLAlchemy Model ---
   class Base(DeclarativeBase):
       pass

   class OfflineMutationModel(Base):
       __tablename__ = "offline_mutations"

       id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
       mutation_type: Mapped[str] = mapped_column(String(50), nullable=False)
       entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
       entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
       payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
       status: Mapped[MutationStatus] = mapped_column(SAEnum(MutationStatus), default=MutationStatus.PENDENTE, nullable=False)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
       error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       sync_attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

   # --- Repository ---
   class OfflineCacheRepository:
       def __init__(self, session: Session):
           self.session = session

       def add_mutation(self, data: OfflineMutationCreate) -> OfflineMutationRead:
           mutation = OfflineMutationModel(
               id=str(uuid4()),
               mutation_type=data.mutation_type,
               entity_type=data.entity_type,
               entity_id=data.entity_id,
               payload=data.payload.model_dump(),
               status=data.status,
           )
           self.session.add(mutation)
           self.session.flush()
           self.session.refresh(mutation)
           return OfflineMutationRead.model_validate(mutation)

       def get_pending_mutations(self, limit: int = 100) -> List[OfflineMutationRead]:
           stmt = select(OfflineMutationModel).where(
               OfflineMutationModel.status == MutationStatus.PENDENTE
           ).order_by(OfflineMutationModel.created_at.asc()).limit(limit)
           results = self.session.scalars(stmt).all()
           return [OfflineMutationRead.model_validate(m) for m in results]

       def update_status(self, mutation_id: str, new_status: MutationStatus, error: Optional[str] = None) -> Optional[OfflineMutationRead]:
           stmt = (
               update(OfflineMutationModel)
               .where(OfflineMutationModel.id == mutation_id)
               .values(status=new_status, error_message=error, updated_at=func.now())
           )
           self.session.execute(stmt)
           self.session.flush()
           stmt_get = select(OfflineMutationModel).where(OfflineMutationModel.id == mutation_id)
           result = self.session.scalar(stmt_get)
           if not result:
               return None
           return OfflineMutationRead.model_validate(result)

       def mark_as_sent(self, mutation_id: str) -> Optional[OfflineMutationRead]:
           return self.update_status(mutation_id, MutationStatus.ENVIADO)

       def mark_as_conflict(self, mutation_id: str, error: str) -> Optional[OfflineMutationRead]:
           stmt = (
               update(OfflineMutationModel)
               .where(OfflineMutationModel.id == mutation_id)
               .values(
                   status=MutationStatus.CONFLITO,
                   error_message=error,
                   sync_attempt_count=OfflineMutationModel.sync_attempt_count + 1,
                   updated_at=func.now()
               )
           )
           self.session.execute(stmt)
           self.session.flush()
           stmt_get = select(OfflineMutationModel).where(OfflineMutationModel.id == mutation_id)
           result = self.session.scalar(stmt_get)
           if not result:
               return None
           return OfflineMutationRead.model_validate(result)

       def get_mutation(self, mutation_id: str) -> Optional[OfflineMutationRead]:
           stmt = select(OfflineMutationModel).where(OfflineMutationModel.id == mutation_id)
           result = self.session.scalar(stmt)
           if not result:
               return None
           return OfflineMutationRead.model_validate(result)

       def cleanup_sent(self, max_age_days: int = 30) -> int:
           cutoff = datetime.now().timestamp() - (max_age_days * 86400)
           # SQLAlchemy 2.0 uses func.now() but for filtering we can use datetime
           from datetime import timedelta
           cutoff_date = datetime.now() - timedelta(days=max_age_days)
           stmt = select(OfflineMutationModel).where(
               OfflineMutationModel.status == MutationStatus.ENVIADO,
               OfflineMutationModel.updated_at < cutoff_date
           )
           results = self.session.scalars(stmt).all()
           for m in results:
               self.session.delete(m)
           self.session.flush()
           return len(results)

       def verify_integrity(self) -> Dict[str, Any]:
           # Check for orphaned mutations or invalid JSON payloads
           stmt = select(OfflineMutationModel)
           results = self.session.scalars(stmt).all()
           errors = []
           for m in results:
               try:
                   OfflineMutationPayload.model_validate(m.payload)
               except Exception as e:
                   errors.append({"id": m.id, "error": str(e)})
           return {
               "total_mutations": len(results),
               "pending": sum(1 for m in results if m.status == MutationStatus.PENDENTE),
               "sent": sum(1 for m in results if m.status == MutationStatus.ENVIADO),
               "conflict": sum(1 for m in results if m.status == MutationStatus.CONFLITO),
               "payload_errors": errors
           }
   ```

5.  **Review & Refine (Self-Correction/Improvement):**
   - *SQLAlchemy 2.0:* Used `mapped_column`, `select`, `update`, `func.now()`. Good.
   - *Pydantic v2:* Used `Field`, `field_validator`, `model_dump`, `model_validate`, `ConfigDict`. Good.
   - *SUS/APS Standards:* Added `PatientIdentifier` with CNS/CPF validation, `ClinicalData` with CID-10/CIAP-2 and SOAP validation. The payload schema enforces this.
   - *Outbox Pattern:* `add_mutation`, `get_pending_mutations`, `mark_as_sent`, `mark_as_conflict`, `cleanup_sent` cover the lifecycle.
   - *Integrity:* `verify_integrity` checks payload validity and counts statuses.
   - *Type Hints:* Strict typing throughout.
   - *Missing:* The prompt asks for "código completo e executável" and "cobertura de testes automatizados com pytest". I should provide the test file as well to fully satisfy the requirement. I'll create `backend/app/repositories/test_offline_cache_repo.py`.
   - *Test File Structure:* Use `pytest`, `tempfile` or `sqlite` for DB, create session, test CRUD, status updates, integrity, validation.
   - *Dependencies:* `sqlalchemy`, `pydantic`, `pytest`, `pytest-asyncio` (optional, but I'll stick to sync for simplicity unless async is needed. I'll use sync SQLAlchemy for tests).
   - *Database Setup for Tests:* Use `sqlite:///:memory:` for fast tests.

   Let's draft the test file mentally before writing:
   - Setup: `@pytest.fixture def session():` creates engine, creates tables, yields session, drops tables.
   - Test cases:
     - `test_add_mutation_validates_sus_standards`
     - `test_add_mutation_invalid_cpf`
     - `test_get_pending_mutations`
     - `test_update_status_to_sent`
     - `test_update_status_to_conflict_increments_attempts`
     - `test_cleanup_sent_removes_old_records`
     - `test_verify_integrity`
   - I'll make sure the test file is complete and runnable.

6.  **Final Code Construction:**
   I will structure the response with two files:
   1. `backend/app/repositories/offline_cache_repo.py`
   2. `backend/app/repositories/test_offline_cache_repo.py`

   I'll carefully check SQLAlchemy 2.0 syntax:
   - `mapped_column` requires `from sqlalchemy.orm import mapped_column`
   - `select`, `update` from `sqlalchemy`
   - `JSONB` from `sqlalchemy.dialects.postgresql` (but for SQLite compatibility in tests, I'll use `JSON` or handle dialects. Actually, `JSON` is fine for both, but I'll keep `JSONB` for PG as requested, and note that SQLite uses `JSON` fallback or just use `JSON` for portability. I'll stick to `JSON` for simplicity, or use `JSON` dialect-agnostic. Actually, SQLAlchemy 2.0 `JSON` works everywhere. I'll use `JSON`.)
   - Wait, the prompt says "SQLite/Postgres". I'll use `JSON` type which is standard.
   - I'll add proper imports.
   - I'll ensure Pydantic v2 syntax is correct (`model_config`, `field_validator`, `model_dump`, `model_validate`).
   - I'll add type hints strictly.
   - I'll make sure the outbox pattern is clear.

   Let's write it out carefully.

   *Self-Correction/Verification during drafting:*
   - `mapped_column` in SQLAlchemy 2.0 requires `from sqlalchemy.orm import mapped_column`.
   - `func.now()` works.
   - Pydantic v2 `field_validator` needs `@field_validator("field")` or `@field_validator("field", mode="before")`. I'll use `mode="after"` or just standard.
   - CNS validation: 15 digits. CPF: 11 digits.
   - SOAP: S, O, A, P keys.
   - I'll add a `Base` class for table creation.
   - For tests, I'll use `sqlite:///:memory:` and `Base.metadata.create_all(engine)`.
   - I'll ensure the code is production-ready and follows the prompt exactly.

   Structure:
   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   ... code ...

   # Arquivo: backend/app/repositories/test_offline_cache_repo.py
   ... code ...
   ```

   I will now generate the response. I'll make sure to include all necessary imports, strict typing, and comprehensive tests. I'll also add comments explaining the SUS/APS integration and outbox pattern.
   One detail: `JSONB` is PostgreSQL-specific. For cross-database support (SQLite/Postgres), I'll use `JSON` from `sqlalchemy`, which maps to `JSONB` on PG and `JSON` on SQLite automatically. I'll stick to `JSON`.
   I'll also add a `sync_mutation` method that simulates the outbox push, but the prompt says "gerencia fila local de mutações pendentes (outbox pattern)", so the repo handles the local queue. The sync process would be external, but I'll provide the necessary methods to fetch and update.

   Let's write it out. 
   I'll carefully check Pydantic v2 syntax: `model_config = ConfigDict(from_attributes=True)` is correct. `model_validate` is correct. `model_dump` is correct.
   SQLAlchemy 2.0: `select`, `update`, `func`, `mapped_column`, `Declarative