Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/offline_cache_repo.py` for a project called "MedIA".
   - **Functionality:** Manage a local queue of pending mutations (outbox pattern), synchronization status (PENDENTE, ENVIADO, CONFLITO), and integrity using SQLAlchemy 2.0.
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards compliance (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Full compliance and coverage with automated tests using pytest.
   - **Output Requirement:** Provide complete, executable code. Specify file paths at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/offline_cache_repo.py`
   - **Core Features:**
     - Outbox pattern for local mutations queue.
     - Status enum: `PENDENTE`, `ENVIADO`, `CONFLITO`.
     - SQLAlchemy 2.0 models & repository pattern.
     - Pydantic v2 for data validation/serialization.
     - SUS/APS standards: CIAP-2, CID-10, SOAP, CNS/CPF.
     - Pytest coverage.
   - **Implicit Needs:**
     - Database session management.
     - Transaction handling.
     - Error handling for conflicts.
     - Type hints throughout.
     - Clear structure.

3.  **Design Components:**
   - **Enums:** `SyncStatus` (PENDENTE, ENVIADO, CONFLITO)
   - **Pydantic Models:**
     - `OfflineMutation` (for API/input validation)
     - `MutationRecord` (for DB model, but SQLAlchemy handles this)
     - Actually, I'll create Pydantic models for request/response and SQLAlchemy models for DB.
   - **SQLAlchemy Model:** `OfflineCacheMutation`
     - Fields: id, patient_cns (optional), patient_cpf, mutation_type, payload (JSON), status, created_at, updated_at, sync_error (optional)
     - Constraints: Check constraints for status, unique constraints if needed.
   - **Repository Class:** `OfflineCacheRepository`
     - Methods: `add_mutation`, `get_pending_mutations`, `mark_as_sent`, `mark_as_conflict`, `get_by_id`, `clear_sent`
     - Use SQLAlchemy 2.0 style (`select`, `session.execute`, etc.)
   - **SUS/APS Compliance:**
     - Validate CNS/CPF format.
     - Support CIAP-2, CID-10 codes in payload.
     - SOAP method tracking.
   - **Pytest:**
     - Test fixtures for DB session.
     - Tests for CRUD, status transitions, validation, conflict handling.

4.  **Draft Code - `offline_cache_repo.py`:**
   *(Mental Refinement during drafting)*
   - Need to import `enum`, `json`, `uuid`, `datetime`, `sqlalchemy`, `pydantic`, `typing`.
   - Define `SyncStatus` enum.
   - Define Pydantic models for input/output.
   - Define SQLAlchemy model `OfflineCacheMutation`.
   - Define `OfflineCacheRepository` class.
   - Add validation for CNS/CPF (Brazilian health system IDs).
   - Ensure strict typing.
   - Handle transactions properly.

   Let's write it out carefully.

   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations
   import json
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Any, Optional, Sequence

   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy import (
       Column,
       DateTime,
       Enum as SAEnum,
       ForeignKey,
       Integer,
       JSON,
       String,
       Text,
       func,
       select,
       update,
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

   # --- Enums ---
   class SyncStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   # --- Pydantic Models ---
   class OfflineMutationPayload(BaseModel):
       model_config = ConfigDict(extra="forbid")
       patient_cns: Optional[str] = Field(None, description="Cartão Nacional de Saúde (CNS)")
       patient_cpf: Optional[str] = Field(None, description="Cadastro de Pessoas Físicas (CPF)")
       ciap2_code: Optional[str] = Field(None, description="CIAP-2 code")
       cid10_code: Optional[str] = Field(None, description="CID-10 code")
       soap_method: str = Field(..., description="Método SOAP (S-O-A-P)")
       clinical_data: dict[str, Any] = Field(default_factory=dict)

       @field_validator("patient_cns")
       @classmethod
       def validate_cns(cls, v: Optional[str]) -> Optional[str]:
           if v is not None and len(v) != 17:
               raise ValueError("CNS deve ter exatamente 17 dígitos.")
           return v

       @field_validator("patient_cpf")
       @classmethod
       def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
           if v is not None and len(v) != 14:
               raise ValueError("CPF deve ter exatamente 14 dígitos (com pontos e traço).")
           return v

   class MutationResponse(BaseModel):
       id: str
       status: SyncStatus
       created_at: datetime
       updated_at: datetime
       payload: dict[str, Any]

   # --- SQLAlchemy Model ---
   class Base(DeclarativeBase):
       pass

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutations"

       id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
       patient_cns: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
       patient_cpf: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
       mutation_type: Mapped[str] = mapped_column(String(50), nullable=False)
       payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
       status: Mapped[SyncStatus] = mapped_column(SAEnum(SyncStatus), default=SyncStatus.PENDENTE, nullable=False)
       sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

       __table_args__ = (
           # Integrity constraints
           {"sqlite_autoincrement": True},
       )

   # --- Repository ---
   class OfflineCacheRepository:
       def __init__(self, session: Session) -> None:
           self.session = session

       def add_mutation(self, mutation_type: str, payload: OfflineMutationPayload) -> MutationResponse:
           mutation = OfflineCacheMutation(
               mutation_type=mutation_type,
               patient_cns=payload.patient_cns,
               patient_cpf=payload.patient_cpf,
               payload=payload.model_dump(),
               status=SyncStatus.PENDENTE,
           )
           self.session.add(mutation)
           self.session.flush()
           return self._to_response(mutation)

       def get_pending_mutations(self, limit: int = 100) -> Sequence[MutationResponse]:
           stmt = select(OfflineCacheMutation).where(
               OfflineCacheMutation.status == SyncStatus.PENDENTE
           ).order_by(OfflineCacheMutation.created_at.asc()).limit(limit)
           result = self.session.execute(stmt)
           return [self._to_response(m) for m in result.scalars().all()]

       def mark_as_sent(self, mutation_id: str) -> bool:
           stmt = (
               update(OfflineCacheMutation)
               .where(OfflineCacheMutation.id == mutation_id)
               .values(status=SyncStatus.ENVIADO, updated_at=datetime.now(timezone.utc))
           )
           result = self.session.execute(stmt)
           self.session.flush()
           return result.rowcount > 0

       def mark_as_conflict(self, mutation_id: str, error: str) -> bool:
           stmt = (
               update(OfflineCacheMutation)
               .where(OfflineCacheMutation.id == mutation_id)
               .values(status=SyncStatus.CONFLITO, sync_error=error, updated_at=datetime.now(timezone.utc))
           )
           result = self.session.execute(stmt)
           self.session.flush()
           return result.rowcount > 0

       def get_by_id(self, mutation_id: str) -> Optional[MutationResponse]:
           stmt = select(OfflineCacheMutation).where(OfflineCacheMutation.id == mutation_id)
           result = self.session.execute(stmt)
           mutation = result.scalar_one_or_none()
           return self._to_response(mutation) if mutation else None

       def clear_sent_mutations(self, older_than_days: int = 7) -> int:
           cutoff = datetime.now(timezone.utc).replace(tzinfo=None)
           from datetime import timedelta
           cutoff_dt = cutoff - timedelta(days=older_than_days)
           stmt = (
               delete(OfflineCacheMutation)
               .where(
                   OfflineCacheMutation.status == SyncStatus.ENVIADO,
                   OfflineCacheMutation.updated_at < cutoff_dt
               )
           )
           result = self.session.execute(stmt)
           self.session.flush()
           return result.rowcount

       @staticmethod
       def _to_response(mutation: OfflineCacheMutation) -> MutationResponse:
           return MutationResponse(
               id=mutation.id,
               status=mutation.status,
               created_at=mutation.created_at,
               updated_at=mutation.updated_at,
               payload=mutation.payload,
           )
   ```

   Wait, I need to import `delete` from sqlalchemy. Also, `delete` is in `sqlalchemy`. Let's fix imports.
   Also, `sync_error` should be validated or handled properly.
   The `clear_sent_mutations` uses `delete` which needs to be imported.
   Let's adjust imports: `from sqlalchemy import delete, ...`
   Also, need to ensure strict typing and Pydantic v2 compatibility.
   I'll add `from sqlalchemy import delete` to imports.
   I'll also add a method to get mutations by status for completeness.
   I should also add a method to retry conflicts.

   Let's refine the repository class to be more robust and add missing imports.

   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations
   import json
   import uuid
   from datetime import datetime, timedelta, timezone
   from enum import Enum
   from typing import Any, Optional, Sequence

   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy import (
       Column,
       DateTime,
       Enum as SAEnum,
       Integer,
       JSON,
       String,
       Text,
       delete,
       func,
       select,
       update,
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

   # ... (rest of the code)
   ```

   Actually, `Column` and `Integer` aren't used in the mapped_column style, but it's fine. I'll clean up imports.
   I'll also add a `retry_conflict` method.
   I need to make sure the code is complete and executable.

   Let's structure it properly.

   **Pytest File:** `backend/tests/test_offline_cache_repo.py`
   - Fixtures: `db_session`, `repo`
   - Tests: `test_add_mutation`, `test_get_pending`, `test_mark_as_sent`, `test_mark_as_conflict`, `test_validate_cns_cpf`, `test_clear_sent`, `test_retry_conflict`
   - Use `pytest-asyncio`? The prompt doesn't specify async, so I'll stick to sync SQLAlchemy for simplicity, but note that it can be adapted. I'll use `pytest` with `sqlalchemy` in-memory SQLite for tests.

   Let's draft the test file.

   ```python
   # Arquivo: backend/tests/test_offline_cache_repo.py
   import pytest
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker

   from app.repositories.offline_cache_repo import (
       Base,
       OfflineCacheMutation,
       OfflineCacheRepository,
       OfflineMutationPayload,
       SyncStatus,
   )

   @pytest.fixture
   def engine():
       return create_engine("sqlite:///:memory:", echo=False)

   @pytest.fixture
   def session_factory(engine):
       return sessionmaker(bind=engine)

   @pytest.fixture
   def db_session(session_factory):
       session = session_factory()
       Base.metadata.create_all(engine)
       yield session
       session.rollback()
       session.close()

   @pytest.fixture
   def repo(db_session):
       return OfflineCacheRepository(db_session)

   class TestOfflineCacheRepository:
       def test_add_mutation(self, repo):
           payload = OfflineMutationPayload(
               patient_cns="701010101010101",
               patient_cpf="123.456.789-00",
               ciap2_code="A00",
               cid10_code="J06.9",
               soap_method="S",
               clinical_data={"complaint": "Dor de cabeça"},
           )
           mutation = repo.add_mutation("CONSULTA", payload)
           assert mutation.status == SyncStatus.PENDENTE
           assert mutation.id is not None
           assert mutation.payload["soap_method"] == "S"

       def test_get_pending_mutations(self, repo):
           payload = OfflineMutationPayload(
               patient_cns="701010101010101",
               patient_cpf="123.456.789-00",
               ciap2_code="A00",
               cid10_code="J06.9",
               soap_method="O",
               clinical_data={},
           )
           repo.add_mutation("CONSULTA", payload)
           pending = repo.get_pending_mutations()
           assert len(pending) == 1
           assert pending[0].status == SyncStatus.PENDENTE

       def test_mark_as_sent(self, repo):
           payload = OfflineMutationPayload(
               patient_cns="701010101010101",
               patient_cpf="123.456.789-00",
               ciap2_code="A00",
               cid10_code="J06.9",
               soap_method="A",
               clinical_data={},
           )
           mutation = repo.add_mutation("CONSULTA", payload)
           assert repo.mark_as_sent(mutation.id)
           updated = repo.get_by_id(mutation.id)
           assert updated.status == SyncStatus.ENVIADO

       def test_mark_as_conflict(self, repo):
           payload = OfflineMutationPayload(
               patient_cns="701010101010101",
               patient_cpf="123.456.789-00",
               ciap2_code="A00",
               cid10_code="J06.9",
               soap_method="P",
               clinical_data={},
           )
           mutation = repo.add_mutation("CONSULTA", payload)
           assert repo.mark_as_conflict(mutation.id, "Erro de rede")
           updated = repo.get_by_id(mutation.id)
           assert updated.status == SyncStatus.CONFLITO
           assert updated.payload.get("sync_error") is None # sync_error is stored in DB, not payload
           # Actually, I should check DB directly or add sync_error to response. Let's fix response to include sync_error.
   ```

   I notice a flaw: `MutationResponse` doesn't include `sync_error`. I should add it or access it differently. I'll update `MutationResponse` to include `sync_error` and `mutation_type`.
   Also, `sync_error` is stored in the DB model, not in the JSON payload. I'll update the Pydantic model and the `_to_response` method.

   Let's refine the code carefully.

   **Revised `offline_cache_repo.py`:**
   - Add `sync_error` to `MutationResponse`.
   - Add `mutation_type` to `MutationResponse`.
   - Fix imports.
   - Ensure strict typing.
   - Add `retry_conflict` method.
   - Ensure SUS/APS compliance in validation/comments.

   **Revised `test_offline_cache_repo.py`:**
   - Update tests to match new response model.
   - Add test for validation errors.
   - Add test for conflict retry.
   - Ensure coverage.

   Let's write out the final code blocks carefully.

   *Self-Correction/Verification during thought:*
   - `SyncStatus` enum: `str, Enum` is correct for Pydantic v2.
   - `mapped_column` is SQLAlchemy 2.0 style.
   - `field_validator` is Pydantic v2.
   - CNS validation: 17 digits. CPF validation: 14 chars (with formatting). I'll keep it simple but note it's a placeholder for real validation.
   - SUS/APS: I'll add comments and ensure the payload structure supports CIAP-2, CID-10, SOAP.
   - Repository methods: `add_mutation`, `get_pending_mutations`, `mark_as_sent`, `mark_as_conflict`, `get_by_id`, `clear_sent_mutations`, `retry_conflict`.
   - I'll add `retry_conflict`