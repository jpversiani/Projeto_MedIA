Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/offline_cache_repo.py` for a project called "MedIA".
   - **Functionality:** Manage a local queue of pending mutations (Outbox pattern), synchronization status (PENDENTE, ENVIADO, CONFLITO), and integrity using SQLAlchemy 2.0.
   - **Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - Follow SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Maintain full compliance and automated test coverage with pytest.
     - Provide complete, executable code.
     - Specify file path in each code block.
   - **Key Concepts:** Outbox pattern, SQLite/Postgres support, SQLAlchemy 2.0, Pydantic v2, strict typing, SUS/APS medical standards, pytest coverage.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/offline_cache_repo.py`
   - **Core Features:**
     - Model for pending mutations (Outbox table)
     - Enums for status: `PENDENTE`, `ENVIADO`, `CONFLITO`
     - CRUD operations for the outbox queue
     - Synchronization logic (mark as sent, handle conflicts)
     - Integrity constraints (e.g., unique mutation ID, status checks)
     - Support for SQLite and PostgreSQL via SQLAlchemy 2.0
   - **Standards Integration:**
     - CIAP-2 (Classificação Internacional de Atenção Primária)
     - CID-10 (Classificação Internacional de Doenças)
     - SOAP method (Subjetivo, Objetivo, Avaliação, Plano)
     - CNS/CPF identification (Brazilian health system identifiers)
   - **Tech Stack:**
     - Python 3.12
     - Pydantic v2 (for data validation/models)
     - SQLAlchemy 2.0 (ORM, async/sync support, type hints)
     - pytest (for testing)
   - **Output:** Complete code with tests, properly structured.

3.  **Design the Solution:**
   - **Database Model (SQLAlchemy 2.0):**
     - Table: `offline_cache_mutation`
     - Columns: `id` (UUID), `mutation_type` (enum), `payload` (JSON), `status` (enum), `created_at`, `updated_at`, `error_message`, `retry_count`, `source_id` (CNS/CPF), `clinical_context` (CID-10, CIAP-2, SOAP)
     - Use SQLAlchemy 2.0 declarative style with `Mapped`, `mapped_column`, `MappedAsDataclass` or standard `DeclarativeBase`
   - **Pydantic Models:**
     - `OfflineCacheMutationCreate`
     - `OfflineCacheMutationUpdate`
     - `OfflineCacheMutationResponse`
     - Enums: `MutationStatus`, `MutationType`
   - **Repository Class:**
     - `OfflineCacheRepository`
     - Methods: `add_mutation`, `get_pending_mutations`, `mark_as_sent`, `mark_as_conflict`, `get_by_id`, `cleanup_old_mutations`
     - Use async SQLAlchemy 2.0 for modern practices, but ensure it works with both SQLite and Postgres.
   - **Integrity & Standards:**
     - Validate CNS/CPF format
     - Validate CID-10 and CIAP-2 codes
     - Validate SOAP structure
     - Use Pydantic for validation
     - Database constraints: unique mutation ID, status check, retry limit
   - **Testing (pytest):**
     - Test async repository with in-memory SQLite
     - Test validation (CNS/CPF, CID-10, CIAP-2, SOAP)
     - Test status transitions
     - Test conflict handling
     - Test cleanup
     - Use `pytest-asyncio`

4.  **Draft the Code (Mental Refinement):**

   *File Structure:*
   ```
   backend/app/repositories/offline_cache_repo.py
   backend/app/repositories/tests/test_offline_cache_repo.py
   ```

   *Models & Enums (Pydantic + SQLAlchemy):*
   Need to define enums first. SQLAlchemy 2.0 supports `Enum` directly or via `sqlalchemy.Enum`. I'll use Python's `enum.Enum` and map it.

   *SQLAlchemy Model:*
   ```python
   from sqlalchemy import String, Text, DateTime, Enum, Integer, JSON, func
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   import uuid
   from datetime import datetime
   from enum import Enum as PyEnum

   class Base(DeclarativeBase):
       pass

   class MutationStatus(PyEnum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class MutationType(PyEnum):
       CREATE = "CREATE"
       UPDATE = "UPDATE"
       DELETE = "DELETE"

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutation"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       mutation_type: Mapped[MutationType] = mapped_column(Enum(MutationType, name="mutation_type"))
       payload: Mapped[dict] = mapped_column(JSON, nullable=False)
       status: Mapped[MutationStatus] = mapped_column(Enum(MutationStatus, name="mutation_status"), default=MutationStatus.PENDENTE)
       created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
       updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
       error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
       retry_count: Mapped[int] = mapped_column(Integer, default=0)
       source_id: Mapped[str] = mapped_column(String(20), nullable=False) # CNS/CPF
       clinical_context: Mapped[dict | None] = mapped_column(JSON, nullable=True) # CID-10, CIAP-2, SOAP
   ```

   *Pydantic Models:*
   ```python
   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from datetime import datetime
   import re

   class ClinicalContext(BaseModel):
       cid10: str | None = None
       ciap2: str | None = None
       soap: dict | None = None # {"S": str, "O": str, "A": str, "P": str}

       @field_validator("cid10")
       @classmethod
       def validate_cid10(cls, v):
           if v and not re.match(r"^[A-Z][0-9][0-9A-Z]{0,2}$", v):
               raise ValueError("CID-10 inválido")
           return v

       @field_validator("ciap2")
       @classmethod
       def validate_ciap2(cls, v):
           if v and not re.match(r"^[A-Z][0-9]{2}$", v):
               raise ValueError("CIAP-2 inválido")
           return v

       @field_validator("soap")
       @classmethod
       def validate_soap(cls, v):
           if v:
               required = {"S", "O", "A", "P"}
               if not required.issubset(v.keys()):
                   raise ValueError("SOAP deve conter S, O, A, P")
           return v

   class OfflineCacheMutationCreate(BaseModel):
       mutation_type: MutationType
       payload: dict
       source_id: str = Field(..., min_length=11, max_length=20)
       clinical_context: ClinicalContext | None = None

       @field_validator("source_id")
       @classmethod
       def validate_cns_cpf(cls, v):
           # Simplified validation for CNS (15 digits) or CPF (11 digits)
           if not re.match(r"^\d{11}$|^\d{15}$", v):
               raise ValueError("CNS ou CPF inválido")
           return v

   class OfflineCacheMutationResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: uuid.UUID
       mutation_type: MutationType
       payload: dict
       status: MutationStatus
       created_at: datetime
       updated_at: datetime
       error_message: str | None
       retry_count: int
       source_id: str
       clinical_context: dict | None
   ```

   *Repository Class:*
   Need async methods for SQLAlchemy 2.0.
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, update
   from typing import Sequence
   import asyncio

   class OfflineCacheRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def add_mutation(self, data: OfflineCacheMutationCreate) -> OfflineCacheMutation:
           mutation = OfflineCacheMutation(
               mutation_type=data.mutation_type,
               payload=data.payload,
               source_id=data.source_id,
               clinical_context=data.clinical_context.model_dump() if data.clinical_context else None
           )
           self.session.add(mutation)
           await self.session.commit()
           await self.session.refresh(mutation)
           return mutation

       async def get_pending_mutations(self, limit: int = 100) -> Sequence[OfflineCacheMutation]:
           stmt = select(OfflineCacheMutation).where(
               OfflineCacheMutation.status == MutationStatus.PENDENTE
           ).limit(limit)
           result = await self.session.execute(stmt)
           return result.scalars().all()

       async def mark_as_sent(self, mutation_id: uuid.UUID) -> bool:
           stmt = update(OfflineCacheMutation).where(
               OfflineCacheMutation.id == mutation_id,
               OfflineCacheMutation.status == MutationStatus.PENDENTE
           ).values(status=MutationStatus.ENVIADO)
           result = await self.session.execute(stmt)
           await self.session.commit()
           return result.rowcount > 0

       async def mark_as_conflict(self, mutation_id: uuid.UUID, error_msg: str) -> bool:
           stmt = update(OfflineCacheMutation).where(
               OfflineCacheMutation.id == mutation_id,
               OfflineCacheMutation.status == MutationStatus.PENDENTE
           ).values(
               status=MutationStatus.CONFLITO,
               error_message=error_msg,
               retry_count=OfflineCacheMutation.retry_count + 1
           )
           result = await self.session.execute(stmt)
           await self.session.commit()
           return result.rowcount > 0

       async def get_by_id(self, mutation_id: uuid.UUID) -> OfflineCacheMutation | None:
           stmt = select(OfflineCacheMutation).where(OfflineCacheMutation.id == mutation_id)
           result = await self.session.execute(stmt)
           return result.scalar_one_or_none()

       async def cleanup_old_mutations(self, days: int = 30) -> int:
           from datetime import timedelta
           cutoff = datetime.utcnow() - timedelta(days=days)
           stmt = update(OfflineCacheMutation).where(
               OfflineCacheMutation.status == MutationStatus.ENVIADO,
               OfflineCacheMutation.updated_at < cutoff
           ).values(status=MutationStatus.PENDENTE) # Or delete? Let's delete for simplicity
           # Actually, outbox pattern usually deletes or archives. I'll delete.
           stmt = OfflineCacheMutation.__table__.delete().where(
               OfflineCacheMutation.status == MutationStatus.ENVIADO,
               OfflineCacheMutation.updated_at < cutoff
           )
           result = await self.session.execute(stmt)
           await self.session.commit()
           return result.rowcount
   ```

   *Wait, need to adjust cleanup to actually delete or archive properly. Outbox pattern typically deletes sent records after a grace period. I'll keep it simple: delete sent records older than X days.*

   Let's refine the repository to be more robust and follow SQLAlchemy 2.0 best practices. I'll also add async context manager support or just keep it simple with explicit session management.

   *Testing Setup:*
   Need `pytest-asyncio`, `aiosqlite`, `pytest` fixtures.
   I'll create a test file that sets up an in-memory SQLite database, injects the session, and tests the repository.

   *Structure of Test File:*
   ```python
   import pytest
   import asyncio
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   from app.repositories.offline_cache_repo import (
       OfflineCacheRepository,
       OfflineCacheMutationCreate,
       MutationType,
       MutationStatus,
       ClinicalContext
   )
   from app.repositories.offline_cache_repo import Base

   @pytest.fixture
   async def engine():
       engine = create_async_engine("sqlite+aiosqlite:///:memory:")
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
       yield engine
       await engine.dispose()

   @pytest.fixture
   async def session(engine):
       async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
       async with async_session() as sess:
           yield sess

   @pytest.fixture
   def repo(session):
       return OfflineCacheRepository(session)

   # Tests...
   ```

   *Validation & Standards Check:*
   - CNS: 15 digits
   - CPF: 11 digits
   - CID-10: Regex `^[A-Z][0-9][0-9A-Z]{0,2}$` (simplified, real is more complex but acceptable for demo)
   - CIAP-2: Regex `^[A-Z][0-9]{2}$`
   - SOAP: dict with S, O, A, P
   - I'll make the validators more robust or note they are simplified for the context.

   *Integrity Constraints:*
   - DB level: unique constraint on `id` (primary key), check constraint on `retry_count < 5` (optional but good)
   - I'll add a check constraint in SQLAlchemy.

   Let's write the complete code carefully.

   *Self-Correction/Refinement during thought:*
   - SQLAlchemy 2.0 uses `Mapped` and `mapped_column`. I need to import them correctly.
   - Pydantic v2 uses `field_validator` and `model_validator`. I'll stick to `field_validator`.
   - The repository should handle async properly. I'll use `async_sessionmaker` in tests.
   - I should include the `__init__.py` or assume it's part of a package. The prompt asks for `backend/app/repositories/offline_cache_repo.py`.
   - I'll add type hints strictly.
   - I'll ensure the code is executable and follows Python 3.12 standards.
   - I'll add comments explaining SUS/APS integration points.
   - I'll make sure the outbox pattern is clear: mutations are queued locally, marked as sent after sync, conflicts are tracked, and old sent records are cleaned up.

   Let's draft the full file content.

   *File 1: `backend/app/repositories/offline_cache_repo.py`*
   - Imports
   - Enums
   - SQLAlchemy Model
   - Pydantic Models
   - Repository Class
   - Add constraints and indexes for performance/integrity.

   *File 2: `backend/app/repositories/tests/test_offline_cache_repo.py`*
   - Fixtures
   - Tests for CRUD, validation, status transitions, cleanup, integrity.

   I'll write them out carefully.

   *Key Considerations for SQLAlchemy 2.0:*
   - `DeclarativeBase`
   - `Mapped`, `mapped_column`
   - `AsyncSession`
   - `select`, `update`
   - Type hints: `Mapped[uuid.UUID]`, etc.
   - I'll use `sqlalchemy.Enum` with `native=False` for better cross-database compatibility (SQLite/Postgres).

   *Pydantic v2:*
   - `BaseModel`
   - `field_validator`
   - `ConfigDict`
   - `model_dump()`

   *SUS/APS Standards:*
   - I'll add explicit validation for CNS/CPF, CID-10, CIAP-2, SOAP.
   - I'll document how it maps to SUS workflows.

   *Testing:*
   - Use `pytest-asyncio`
   - In-memory SQLite
   - Cover all repository methods
   - Test validation errors
   - Test status transitions
   - Test cleanup

   Let's write it out. 
   I'll structure the response with clear file paths and complete code.
   I'll ensure strict typing, Python 3.12 compatibility, and pytest coverage.
   I'll add comments explaining the architecture and standards compliance.
   Ready.✅
   Output matches the response. 
   Self-Correction/Verification during drafting:
   - `sqlalchemy.Enum` in SQLite needs `native=False` or it might cause issues. I'll use `String` with check constraints or `Enum` with `native=False`. Actually, SQLAlchemy 2.0 handles `Enum` well, but for cross-database, `String` with `CheckConstraint` is safer. I'll stick to `Enum` but note it, or use `String` with validation. I'll use `String` for status/type to avoid dialect issues, but the prompt says SQLAlchemy 2.0, so `Enum` is fine. I'll use `sqlalchemy.Enum(..., name="...", native=False)` for safety.
   - Actually, SQLAlchemy 2.0 recommends `sqlalchemy.Enum` or Python `enum.Enum`. I'll use Python `enum.Enum` and map it.
   - I'll add `CheckConstraint` for retry_count < 5.
   - I'll ensure all type hints are correct.
   - I'll make sure the test file is complete and runnable.
   - I'll add `__init__.py` if needed, but not required by prompt.
   - I'll structure the code blocks clearly.

   All good. Proceeding. 
   Output Generation. 
   [Done] 
   *Self-Correction/Note during thought*: 
   I need to make sure the code is strictly Python 3.12 compatible. `from __future__ import annotations` is good practice.