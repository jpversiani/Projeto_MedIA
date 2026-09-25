Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/offline_cache_repo.py` for a project called "MedIA".
   - **Functionality:** Manage a local queue of pending mutations (outbox pattern), synchronization status (PENDENTE, ENVIADO, CONFLITO), and integrity using SQLAlchemy 2.0.
   - **Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - Follow SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Maintain full compliance and automated test coverage with pytest.
     - Provide complete, executable code.
     - Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/offline_cache_repo.py`
   - **Core Features:**
     - Outbox pattern for pending mutations.
     - Synchronization status: `PENDENTE`, `ENVIADO`, `CONFLITO`.
     - Data integrity (constraints, transactions, validation).
     - SQLAlchemy 2.0 ORM models & queries.
     - Pydantic v2 for data validation/serialization.
     - Python 3.12 type hints.
     - SUS/APS context: CIAP-2, CID-10, SOAP, CNS/CPF.
     - Pytest coverage.
   - **Architecture/Standards:**
     - Need models for `OfflineCacheMutation` (or similar).
     - Enums for status.
     - Pydantic schemas for request/response.
     - Repository class with methods: `add_mutation`, `get_pending`, `mark_sent`, `mark_conflict`, `get_by_id`, `delete_sent`, etc.
     - Database session management (dependency injection friendly).
     - Constraints: unique constraints, check constraints for status, foreign keys if needed (maybe to a `Patient` or `Visit` table, but keep it self-contained for now).
     - SUS/APS fields: `cns`, `cpf`, `cid10`, `ciap2`, `soap_note`.
     - Pytest: comprehensive tests covering CRUD, status transitions, constraints, Pydantic validation, SQLAlchemy async/sync (I'll use sync for simplicity but note async compatibility, or stick to sync as it's standard for repos unless specified otherwise. I'll use sync SQLAlchemy 2.0).

3.  **Design Components:**
   - **Enums:** `SyncStatus` (PENDENTE, ENVIADO, CONFLITO)
   - **Pydantic Models:**
     - `OfflineCacheMutationCreate` (for input)
     - `OfflineCacheMutationRead` (for output)
   - **SQLAlchemy Model:** `OfflineCacheMutation`
     - `id` (UUID)
     - `entity_type` (str)
     - `entity_id` (str)
     - `mutation_type` (str: CREATE, UPDATE, DELETE)
     - `payload` (JSON)
     - `status` (SyncStatus)
     - `cns` (str, optional)
     - `cpf` (str, optional)
     - `cid10` (str, optional)
     - `ciap2` (str, optional)
     - `soap_note` (str, optional)
     - `created_at`, `updated_at`, `synced_at`
     - Constraints: unique on `(entity_type, entity_id, mutation_type)`? Or just rely on outbox pattern. Actually, outbox usually has a unique `id` and maybe a `version` or `sequence`. I'll add a `sequence` or `id` as primary key. Let's use `id` as UUID primary key. Add check constraint for status.
   - **Repository Class:** `OfflineCacheRepository`
     - Methods: `add_mutation`, `get_pending_mutations`, `mark_as_sent`, `mark_as_conflict`, `get_mutation_by_id`, `delete_mutation`, `get_status_summary`
     - Use `Session` from SQLAlchemy 2.0.
     - Strict typing.
   - **Pytest:**
     - Fixtures for DB session, repo.
     - Tests for: add mutation, get pending, mark sent/conflict, validation, constraints, status transitions, SUS/APS fields.
     - Use `pytest-asyncio`? I'll stick to sync for simplicity unless async is required. The prompt doesn't specify async, so sync is fine. I'll use `pytest` with `sqlalchemy` in-memory SQLite for tests.

4.  **Draft Code (Mental Refinement):**
   *File: `backend/app/repositories/offline_cache_repo.py`*
   ```python
   from __future__ import annotations
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import (
       String, Text, Enum as SAEnum, JSON, CheckConstraint, UniqueConstraint,
       func, select, update, delete
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
   from sqlalchemy.dialects.postgresql import JSONB
   import json

   # --- Enums & Pydantic Schemas ---
   class SyncStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class MutationType(str, Enum):
       CREATE = "CREATE"
       UPDATE = "UPDATE"
       DELETE = "DELETE"

   class OfflineCacheMutationCreate(BaseModel):
       entity_type: str = Field(..., min_length=1, max_length=50)
       entity_id: str = Field(..., min_length=1, max_length=100)
       mutation_type: MutationType
       payload: Dict[str, Any] = Field(default_factory=dict)
       cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       cid10: Optional[str] = Field(None, pattern=r"^[A-Z]\d{2}$")
       ciap2: Optional[str] = Field(None, pattern=r"^[A-Z]\d{2}$")
       soap_note: Optional[str] = None

       @field_validator("payload")
       @classmethod
       def validate_payload(cls, v: Dict[str, Any]) -> Dict[str, Any]:
           if not isinstance(v, dict):
               raise ValueError("Payload must be a dictionary")
           return v

   class OfflineCacheMutationRead(BaseModel):
       id: str
       entity_type: str
       entity_id: str
       mutation_type: str
       payload: Dict[str, Any]
       status: str
       cns: Optional[str] = None
       cpf: Optional[str] = None
       cid10: Optional[str] = None
       ciap2: Optional[str] = None
       soap_note: Optional[str] = None
       created_at: str
       updated_at: str
       synced_at: Optional[str] = None

       model_config = {"from_attributes": True}

   # --- SQLAlchemy Model ---
   class Base(DeclarativeBase):
       pass

   class OfflineCacheMutationModel(Base):
       __tablename__ = "offline_cache_mutations"

       id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
       entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
       entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
       mutation_type: Mapped[str] = mapped_column(SAEnum(MutationType), nullable=False)
       payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
       status: Mapped[str] = mapped_column(SAEnum(SyncStatus), nullable=False, default=SyncStatus.PENDENTE)
       cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       cpf: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
       cid10: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
       ciap2: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
       soap_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

       created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
       updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
       synced_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

       __table_args__ = (
           CheckConstraint("status IN ('PENDENTE', 'ENVIADO', 'CONFLITO')", name="ck_sync_status"),
           UniqueConstraint("entity_type", "entity_id", "mutation_type", name="uq_entity_mutation"),
       )

   # --- Repository ---
   class OfflineCacheRepository:
       def __init__(self, session: Session):
           self.session = session

       def add_mutation(self, data: OfflineCacheMutationCreate) -> OfflineCacheMutationRead:
           mutation = OfflineCacheMutationModel(
               id=str(uuid.uuid4()),
               entity_type=data.entity_type,
               entity_id=data.entity_id,
               mutation_type=data.mutation_type,
               payload=data.payload,
               status=SyncStatus.PENDENTE,
               cns=data.cns,
               cpf=data.cpf,
               cid10=data.cid10,
               ciap2=data.ciap2,
               soap_note=data.soap_note,
           )
           self.session.add(mutation)
           self.session.flush()
           return self._to_read(mutation)

       def get_pending_mutations(self, limit: int = 100) -> List[OfflineCacheMutationRead]:
           stmt = select(OfflineCacheMutationModel).where(
               OfflineCacheMutationModel.status == SyncStatus.PENDENTE
           ).order_by(OfflineCacheMutationModel.created_at.asc()).limit(limit)
           results = self.session.execute(stmt).scalars().all()
           return [self._to_read(r) for r in results]

       def mark_as_sent(self, mutation_id: str) -> Optional[OfflineCacheMutationRead]:
           stmt = update(OfflineCacheMutationModel).where(
               OfflineCacheMutationModel.id == mutation_id,
               OfflineCacheMutationModel.status == SyncStatus.PENDENTE
           ).values(status=SyncStatus.ENVIADO, synced_at=datetime.now(timezone.utc))
           self.session.execute(stmt)
           return self.get_mutation_by_id(mutation_id)

       def mark_as_conflict(self, mutation_id: str, payload: Optional[Dict[str, Any]] = None) -> Optional[OfflineCacheMutationRead]:
           stmt = update(OfflineCacheMutationModel).where(
               OfflineCacheMutationModel.id == mutation_id,
               OfflineCacheMutationModel.status == SyncStatus.ENVIADO
           ).values(status=SyncStatus.CONFLITO, synced_at=datetime.now(timezone.utc))
           if payload:
               stmt = stmt.values(payload=payload)
           self.session.execute(stmt)
           return self.get_mutation_by_id(mutation_id)

       def get_mutation_by_id(self, mutation_id: str) -> Optional[OfflineCacheMutationRead]:
           stmt = select(OfflineCacheMutationModel).where(OfflineCacheMutationModel.id == mutation_id)
           result = self.session.execute(stmt).scalar_one_or_none()
           return self._to_read(result) if result else None

       def delete_mutation(self, mutation_id: str) -> bool:
           stmt = delete(OfflineCacheMutationModel).where(OfflineCacheMutationModel.id == mutation_id)
           result = self.session.execute(stmt)
           self.session.flush()
           return result.rowcount > 0

       def get_status_summary(self) -> Dict[str, int]:
           stmt = select(OfflineCacheMutationModel.status, func.count(OfflineCacheMutationModel.id))
           stmt = stmt.group_by(OfflineCacheMutationModel.status)
           results = self.session.execute(stmt).all()
           return {status: count for status, count in results}

       @staticmethod
       def _to_read(model: OfflineCacheMutationModel) -> OfflineCacheMutationRead:
           return OfflineCacheMutationRead(
               id=model.id,
               entity_type=model.entity_type,
               entity_id=model.entity_id,
               mutation_type=model.mutation_type,
               payload=model.payload,
               status=model.status,
               cns=model.cns,
               cpf=model.cpf,
               cid10=model.cid10,
               ciap2=model.ciap2,
               soap_note=model.soap_note,
               created_at=model.created_at.isoformat(),
               updated_at=model.updated_at.isoformat(),
               synced_at=model.synced_at.isoformat() if model.synced_at else None,
           )
   ```

   *Wait*, I need to ensure strict typing and Pydantic v2 compatibility. The `model_config = {"from_attributes": True}` is correct for Pydantic v2. I'll use `model_config = ConfigDict(from_attributes=True)` for better practice.
   Also, SQLAlchemy 2.0 uses `mapped_column` and `Mapped`. I'll adjust imports accordingly.
   I should add proper type hints for methods.
   I'll also add a `delete_sent_mutations` method to clean up sent records, which is common in outbox patterns.
   Let's refine the repository class with strict typing and better structure.

   *File: `backend/app/repositories/offline_cache_repo.py`* (Refined)
   I'll structure it carefully. I'll also add comments explaining SUS/APS compliance.

   Now, the Pytest file: `backend/app/tests/test_offline_cache_repo.py`
   Need to cover:
   - DB setup (SQLite in-memory)
   - Repository instantiation
   - Add mutation & validation
   - Get pending
   - Mark sent/conflict
   - Constraints (unique, check)
   - Status summary
   - SUS/APS fields validation
   - Edge cases (empty payload, invalid CNS/CPF/CID10/CIAP2)

   I'll write the test file carefully.

   *Structure of Test File:*
   ```python
   import pytest
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from backend.app.repositories.offline_cache_repo import (
       Base, OfflineCacheRepository, OfflineCacheMutationCreate, SyncStatus, MutationType
   )

   @pytest.fixture
   def engine():
       return create_engine("sqlite:///:memory:", echo=False)

   @pytest.fixture
   def session(engine):
       Base.metadata.create_all(engine)
       SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
       sess = SessionLocal()
       yield sess
       sess.close()

   @pytest.fixture
   def repo(session):
       return OfflineCacheRepository(session)

   # ... tests ...
   ```

   I need to make sure the code is complete, executable, and follows all guidelines. I'll add proper imports, type hints, and comments. I'll also ensure Pydantic v2 uses `ConfigDict` and `field_validator`. SQLAlchemy 2.0 uses `mapped_column` and `Mapped`. I'll adjust accordingly.

   Let's draft the complete code carefully.

   *Self-Correction/Verification during drafting:*
   - Pydantic v2: `model_config = ConfigDict(from_attributes=True)` is correct.
   - SQLAlchemy 2.0: `Mapped`, `mapped_column`, `select`, `update`, `delete` are correct.
   - Enums: `str, Enum` is fine. SQLAlchemy `SAEnum` works.
   - Constraints: `CheckConstraint` and `UniqueConstraint` are correct.
   - SUS/APS: Added fields `cns`, `cpf`, `cid10`, `ciap2`, `soap_note` with validation patterns.
   - Outbox pattern: `add_mutation` (PENDENTE), `mark_as_sent` (ENVIADO), `mark_as_conflict` (CONFLITO), `delete_mutation` (cleanup).
   - Type hints: Strict typing throughout.
   - Tests: Comprehensive coverage.

   I'll write out the full code blocks now. I'll make sure to include the file path comment at the top of each block as requested.
   I'll also add a `delete_sent_mutations` method to the repo for completeness, as outbox patterns typically clean up sent records.
   I'll ensure the code is Python 3.12 compatible (uses `from __future__ import annotations` or just standard typing, but I'll stick to standard typing for clarity, or use `from __future__ import annotations` for forward references if needed. Actually, standard typing is fine for 3.12).
   I'll use `typing.Optional`, `typing.List`, `typing.Dict`, `typing.Any`.
   I'll make sure the Pydantic models use `field_validator` correctly.
   I'll add proper docstrings.

   Let's construct the final response.
   Structure:
   1. `backend/app/repositories/offline_cache_repo.py`
   2. `backend/app/tests/test_offline_cache_repo.py`
   Both with complete, executable code.
   I'll double-check SQLAlchemy 2.0 syntax: `mapped_column`, `Mapped`, `select`, `update`, `delete`, `session.execute()`, `session.flush()`, `session.commit()` (tests will handle commits).
   I'll add `session.commit()` in repo methods where needed, or assume caller handles it. Usually, repos don't commit, but for outbox, it's safer to commit or let caller handle. I'll leave commit to caller but add `flush()` to ensure IDs are available. Actually, outbox pattern usually commits immediately to persist the mutation. I'll add `self.session.commit()` after `add_mutation` and status updates for robustness, or document it. I'll stick to `flush()` and let caller commit, but I'll add a note. Actually, for outbox, immediate commit is standard. I'll add `self.session.commit()` after mutations to ensure durability.

   Wait, the prompt says "gerencia fila local de mutações