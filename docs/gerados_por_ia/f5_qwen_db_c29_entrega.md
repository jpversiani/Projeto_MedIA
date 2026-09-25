Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/offline_cache_repo.py` for the MedIA project.
   - **Functionality:** Manage a local queue of pending mutations (outbox pattern), synchronization status (PENDENTE, ENVIADO, CONFLITO), and integrity using SQLAlchemy 2.0.
   - **Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards compliance (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Full compliance and coverage with automated pytest tests.
     - Provide complete, executable code. Specify file paths in code blocks.
   - **Key Concepts:** Outbox pattern, SQLite/Postgres support, offline cache, sync status, SQLAlchemy 2.0 models & queries, Pydantic v2 for data validation, pytest for testing.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/offline_cache_repo.py`
   - **Core Components:**
     - SQLAlchemy 2.0 Model for `OfflineCacheMutation` (or similar)
     - Enums for sync status: `PENDENTE`, `ENVIADO`, `CONFLITO`
     - Repository class with methods to:
       - Add mutation to queue
       - Get pending mutations
       - Update status (mark as sent, mark as conflict)
       - Handle integrity (maybe checksums, timestamps, unique constraints)
     - Pydantic v2 schemas for request/response/validation
     - Support for both SQLite and Postgres (via SQLAlchemy's dialect abstraction)
     - SUS/APS context: fields like `cns`, `cpf`, `cid10`, `ciap2`, `soap_method`, etc.
   - **Testing:** pytest suite covering all repository methods, status transitions, integrity checks, and both DB backends (or at least one with dialect flexibility).

3.  **Design Decisions:**
   - **Model:** `OfflineCacheEntry` with fields:
     - `id`: UUID
     - `entity_type`: str (e.g., "patient", "consultation")
     - `entity_id`: str
     - `mutation_type`: str (CREATE, UPDATE, DELETE)
     - `payload`: JSON (Pydantic model or dict)
     - `sync_status`: Enum (PENDENTE, ENVIADO, CONFLITO)
     - `cns`: Optional[str]
     - `cpf`: Optional[str]
     - `cid10`: Optional[str]
     - `ciap2`: Optional[str]
     - `soap_method`: Optional[str]
     - `created_at`: datetime
     - `updated_at`: datetime
     - `checksum`: str (for integrity)
     - `retry_count`: int
   - **Enum:** `SyncStatus` with values `PENDENTE`, `ENVIADO`, `CONFLITO`
   - **Pydantic Schemas:** `OfflineCachePayload`, `OfflineCacheMutationIn`, `OfflineCacheMutationOut`
   - **Repository Class:** `OfflineCacheRepository` with async methods (SQLAlchemy 2.0 async session is standard)
   - **Integrity:** Checksum of payload + metadata, unique constraint on (entity_type, entity_id, mutation_type, created_at) or similar, retry limit handling
   - **DB Support:** Use `create_async_engine` with dialect parameter, but the repo itself should be dialect-agnostic. I'll provide a factory or config hint, but focus on the repo code.
   - **Testing:** Use `pytest-asyncio`, `aiosqlite` for SQLite, `pytest-postgresql` or mock for Postgres. I'll use SQLite for simplicity in tests but ensure dialect independence.

4.  **Draft Code (Mental Refinement):**

   *Imports:*
   ```python
   from __future__ import annotations
   import hashlib
   import json
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, Sequence
   import uuid
   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import Column, String, Text, DateTime, Integer, Enum as SAEnum, UniqueConstraint, CheckConstraint
   from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
   ```

   *Wait, SQLAlchemy 2.0 uses `mapped_column` and `Mapped`.* Let's stick to modern SQLAlchemy 2.0 syntax.

   *Model Definition:*
   ```python
   class Base(DeclarativeBase):
       pass

   class SyncStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutations"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
       entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
       mutation_type: Mapped[str] = mapped_column(String(10), nullable=False) # CREATE, UPDATE, DELETE
       payload: Mapped[dict] = mapped_column(Text, nullable=False)
       sync_status: Mapped[SyncStatus] = mapped_column(SAEnum(SyncStatus), default=SyncStatus.PENDENTE)
       cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       cpf: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
       cid10: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
       ciap2: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
       soap_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
       checksum: Mapped[str] = mapped_column(String(64), nullable=False)
       retry_count: Mapped[int] = mapped_column(Integer, default=0)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

       __table_args__ = (
           UniqueConstraint("entity_type", "entity_id", "mutation_type", "created_at", name="uix_mutation"),
           CheckConstraint("retry_count >= 0", name="chk_retry_count"),
       )
   ```

   *Pydantic Schemas:*
   ```python
   class OfflineCacheMutationPayload(BaseModel):
       entity_type: str
       entity_id: str
       mutation_type: str
       payload: dict
       cns: Optional[str] = None
       cpf: Optional[str] = None
       cid10: Optional[str] = None
       ciap2: Optional[str] = None
       soap_method: Optional[str] = None

       @field_validator("mutation_type")
       @classmethod
       def validate_mutation_type(cls, v):
           if v.upper() not in ("CREATE", "UPDATE", "DELETE"):
               raise ValueError("mutation_type must be CREATE, UPDATE or DELETE")
           return v.upper()

   class OfflineCacheMutationOut(BaseModel):
       id: uuid.UUID
       entity_type: str
       entity_id: str
       mutation_type: str
       payload: dict
       sync_status: SyncStatus
       cns: Optional[str]
       cpf: Optional[str]
       cid10: Optional[str]
       ciap2: Optional[str]
       soap_method: Optional[str]
       checksum: str
       retry_count: int
       created_at: datetime
       updated_at: datetime

       model_config = {"from_attributes": True}
   ```

   *Repository Class:*
   Need async methods:
   - `add_mutation(session, payload: OfflineCacheMutationPayload) -> OfflineCacheMutationOut`
   - `get_pending_mutations(session, limit: int = 100) -> Sequence[OfflineCacheMutationOut]`
   - `mark_as_sent(session, mutation_id: uuid.UUID) -> None`
   - `mark_as_conflict(session, mutation_id: uuid.UUID) -> None`
   - `get_by_id(session, mutation_id: uuid.UUID) -> Optional[OfflineCacheMutationOut]`
   - `update_retry_count(session, mutation_id: uuid.UUID) -> None` (or handle in mark_as_conflict)
   - Integrity check: verify checksum matches payload

   Let's implement carefully with SQLAlchemy 2.0 async syntax.

   ```python
   class OfflineCacheRepository:
       @staticmethod
       async def add_mutation(session: AsyncSession, payload: OfflineCacheMutationPayload) -> OfflineCacheMutationOut:
           # Generate checksum
           checksum_input = json.dumps({
               "entity_type": payload.entity_type,
               "entity_id": payload.entity_id,
               "mutation_type": payload.mutation_type,
               "payload": payload.payload,
               "cns": payload.cns,
               "cpf": payload.cpf,
               "cid10": payload.cid10,
               "ciap2": payload.ciap2,
               "soap_method": payload.soap_method,
           }, sort_keys=True)
           checksum = hashlib.sha256(checksum_input.encode()).hexdigest()

           mutation = OfflineCacheMutation(
               entity_type=payload.entity_type,
               entity_id=payload.entity_id,
               mutation_type=payload.mutation_type,
               payload=payload.payload,
               cns=payload.cns,
               cpf=payload.cpf,
               cid10=payload.cid10,
               ciap2=payload.ciap2,
               soap_method=payload.soap_method,
               checksum=checksum,
           )
           session.add(mutation)
           await session.commit()
           await session.refresh(mutation)
           return OfflineCacheMutationOut.model_validate(mutation)

       @staticmethod
       async def get_pending_mutations(session: AsyncSession, limit: int = 100) -> Sequence[OfflineCacheMutationOut]:
           stmt = select(OfflineCacheMutation).where(
               OfflineCacheMutation.sync_status == SyncStatus.PENDENTE
           ).order_by(OfflineCacheMutation.created_at.asc()).limit(limit)
           result = await session.execute(stmt)
           mutations = result.scalars().all()
           return [OfflineCacheMutationOut.model_validate(m) for m in mutations]

       @staticmethod
       async def mark_as_sent(session: AsyncSession, mutation_id: uuid.UUID) -> None:
           stmt = update(OfflineCacheMutation).where(
               OfflineCacheMutation.id == mutation_id
           ).values(sync_status=SyncStatus.ENVIADO)
           await session.execute(stmt)
           await session.commit()

       @staticmethod
       async def mark_as_conflict(session: AsyncSession, mutation_id: uuid.UUID) -> None:
           stmt = update(OfflineCacheMutation).where(
               OfflineCacheMutation.id == mutation_id
           ).values(
               sync_status=SyncStatus.CONFLITO,
               retry_count=OfflineCacheMutation.retry_count + 1
           )
           await session.execute(stmt)
           await session.commit()

       @staticmethod
       async def verify_integrity(session: AsyncSession, mutation_id: uuid.UUID) -> bool:
           stmt = select(OfflineCacheMutation).where(OfflineCacheMutation.id == mutation_id)
           result = await session.execute(stmt)
           mutation = result.scalar_one_or_none()
           if not mutation:
               return False

           checksum_input = json.dumps({
               "entity_type": mutation.entity_type,
               "entity_id": mutation.entity_id,
               "mutation_type": mutation.mutation_type,
               "payload": mutation.payload,
               "cns": mutation.cns,
               "cpf": mutation.cpf,
               "cid10": mutation.cid10,
               "ciap2": mutation.ciap2,
               "soap_method": mutation.soap_method,
           }, sort_keys=True)
           expected_checksum = hashlib.sha256(checksum_input.encode()).hexdigest()
           return mutation.checksum == expected_checksum
   ```

   *Wait*, I need to import `select`, `update` from sqlalchemy. Also, `Sequence` from typing. I'll add them.

   Let's structure the file properly with all imports, models, schemas, and repository. I'll also add a helper to create the engine for testing, but the prompt asks specifically for the repo file. I'll keep it focused.

   I should also consider the SUS/APS standards. The fields `cns`, `cpf`, `cid10`, `ciap2`, `soap_method` are already there. I'll add validation for CNS/CPF formats if needed, but Pydantic v2 can handle it. I'll add a simple regex validator for CPF/CNS to be thorough.

   CNS format: 15 digits, sometimes with mask. CPF: 11 digits.
   I'll keep it simple but add a note or basic validator.

   Let's refine the Pydantic models with validators:
   ```python
   @field_validator("cpf")
   @classmethod
   def validate_cpf(cls, v):
       if v is not None:
           if not v.isdigit() or len(v) != 11:
               raise ValueError("CPF must be 11 digits")
       return v

   @field_validator("cns")
   @classmethod
   def validate_cns(cls, v):
       if v is not None:
           if not v.isdigit() or len(v) != 15:
               raise ValueError("CNS must be 15 digits")
       return v
   ```

   Now, the repository class. I'll make it a class with `@classmethod` or instance methods. I'll use instance methods for better testability, but static is fine too. I'll stick to static for simplicity, or provide an `__init__` that takes a session factory. Actually, standard repo pattern uses session injection. I'll keep it as `async def method(session, ...)`.

   I need to add `from sqlalchemy import select, update` and `from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column`.

   Let's assemble the complete file.

   *Structure of `backend/app/repositories/offline_cache_repo.py`:*
   - Imports
   - Enums
   - SQLAlchemy Model
   - Pydantic Schemas
   - Repository Class
   - (Optional) Engine factory for testing, but I'll put it in a separate comment or just rely on pytest fixtures. The prompt says "código completo e executável", so I'll include a minimal test file as well, or at least ensure the repo is self-contained. I'll provide the repo file and a pytest file.

   Wait, the prompt says: "Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo". I'll provide:
   1. `backend/app/repositories/offline_cache_repo.py`
   2. `backend/app/repositories/__init__.py` (if needed)
   3. `tests/test_offline_cache_repo.py`

   I'll focus on the main repo file and the test file.

   Let's draft the repo file carefully.

   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations

   import hashlib
   import json
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, Sequence

   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import select, update
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

   # ... (rest of code)
   ```

   I need to make sure SQLAlchemy 2.0 syntax is correct. `mapped_column` is correct. `DeclarativeBase` is correct. `AsyncSession` is correct.

   Let's add the model:
   ```python
   class Base(DeclarativeBase):
       pass

   class SyncStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutations"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
       entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
       mutation_type: Mapped[str] = mapped_column(String(10), nullable=False)
       payload: Mapped[dict] = mapped_column(Text, nullable=False)
       sync_status: Mapped[SyncStatus] = mapped_column(SAEnum(SyncStatus), default=SyncStatus.PENDENTE)
       cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       cpf: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
       cid10: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
       ciap2: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
       soap_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
       checksum: Mapped[str] = mapped_column(String(64), nullable=False)
       retry_count: Mapped[int] = mapped_column(Integer, default=0)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

       __table_args__ = (
           UniqueConstraint("entity_type", "entity_id", "mutation_type", "created_at", name="uix_mutation"),
           CheckConstraint("retry_count >= 0", name="chk_retry_count"),
       )
   ```
   I need to import `String`, `Text`, `DateTime`, `Integer`, `Enum as SAEnum`, `UniqueConstraint`, `