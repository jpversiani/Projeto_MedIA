Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/offline_cache_repo.py` for a project called "MedIA".
   - **Features:** Manage a local queue of pending mutations (outbox pattern), synchronization status (PENDENTE, ENVIADO, CONFLITO), integrity with SQLAlchemy 2.0.
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards compliance (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Full compliance and coverage with automated pytest tests.
   - **Output Requirement:** Provide complete, executable code. Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/offline_cache_repo.py`
   - **Core Functionality:**
     - Outbox pattern: Store local mutations (creates, updates, deletes) with status tracking.
     - Statuses: `PENDENTE` (Pending), `ENVIADO` (Sent), `CONFLITO` (Conflict).
     - SQLAlchemy 2.0 models & queries.
     - Pydantic v2 for data validation/serialization.
     - SUS/APS context: Need to incorporate relevant fields/concepts (CIAP-2, CID-10, SOAP, CNS/CPF) into the model or at least ensure the structure supports them.
     - Test coverage: Provide pytest tests.
   - **Constraints:** Python 3.12, strict typing, SQLAlchemy 2.0, Pydantic v2.

3.  **Design the Solution:**
   - **Database Model (`OfflineCacheMutation`):**
     - `id`: UUID
     - `entity_type`: str (e.g., "patient", "consultation", "diagnosis")
     - `entity_id`: str (UUID or string ID)
     - `mutation_type`: str (CREATE, UPDATE, DELETE)
     - `payload`: JSON (Pydantic model or dict)
     - `status`: Enum (PENDENTE, ENVIADO, CONFLITO)
     - `created_at`: datetime
     - `updated_at`: datetime
     - `error_message`: Optional[str]
     - `retry_count`: int
     - `metadata`: Optional[dict] (could store CNS/CPF, CIAP-2, CID-10, SOAP notes)
   - **Pydantic Models:**
     - `OfflineCacheMutationCreate`
     - `OfflineCacheMutationUpdate`
     - `OfflineCacheMutationResponse`
   - **Repository Class (`OfflineCacheRepository`):**
     - `__init__(self, session: AsyncSession)`
     - `add_mutation(...)`: Create pending mutation
     - `get_pending_mutations(...)`: Fetch mutations to sync
     - `mark_sent(...)`: Update status to ENVIADO
     - `mark_conflict(...)`: Update status to CONFLITO
     - `get_by_id(...)`: Fetch specific mutation
     - `cleanup(...)`: Remove sent mutations (optional but good practice)
   - **SUS/APS Integration:**
     - Add fields to `metadata` or specific columns for `cns`, `cpf`, `ciap2_codes`, `cid10_codes`, `soap_note`.
     - Ensure the model supports these natively or via JSON. I'll add explicit columns for critical SUS identifiers to ensure integrity and indexing.
     - `cns`: Optional[str]
     - `cpf`: Optional[str]
     - `ciap2_codes`: JSON list
     - `cid10_codes`: JSON list
     - `soap_note`: JSON (structured SOAP)
   - **SQLAlchemy 2.0 Implementation:**
     - Use `Mapped`, `mapped_column`, `Column`, `Enum`, `JSON`, `UUID`, `DateTime`, `Boolean`, `Integer`, `String`.
     - Use `DeclarativeBase` or `AsyncSession`.
     - Strict typing with `mypy`-compatible annotations.
   - **Pydantic v2:**
     - Use `BaseModel`, `Field`, `ConfigDict`, `model_validator`.
     - Strict mode.
   - **Testing:**
     - pytest-asyncio
     - Mock or use in-memory SQLite for tests.
     - Test all repository methods.
     - Test status transitions.
     - Test SUS/APS fields.
     - Test error handling/conflict marking.

4.  **Draft the Code (Mental Refinement):**

   *Model Definition:*
   ```python
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from uuid import UUID, uuid4
   from sqlalchemy import String, JSON, DateTime, Integer, Enum as SAEnum, func
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   from sqlalchemy.dialects.postgresql import UUID as PG_UUID
   import uuid

   class MutationStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class MutationType(str, Enum):
       CREATE = "CREATE"
       UPDATE = "UPDATE"
       DELETE = "DELETE"

   class Base(DeclarativeBase):
       pass

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutations"

       id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
       entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
       entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
       mutation_type: Mapped[MutationType] = mapped_column(SAEnum(MutationType), nullable=False)
       status: Mapped[MutationStatus] = mapped_column(SAEnum(MutationStatus), default=MutationStatus.PENDENTE, nullable=False)

       # SUS/APS specific fields
       cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       cpf: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
       ciap2_codes: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
       cid10_codes: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
       soap_note: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

       payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
       error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
       retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
   ```

   *Pydantic Models:*
   ```python
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from datetime import datetime

   class OfflineCacheMutationCreate(BaseModel):
       model_config = ConfigDict(strict=True, from_attributes=True)
       entity_type: str = Field(..., min_length=1, max_length=50)
       entity_id: str = Field(..., min_length=1, max_length=100)
       mutation_type: MutationType
       cns: Optional[str] = None
       cpf: Optional[str] = None
       ciap2_codes: Optional[List[str]] = None
       cid10_codes: Optional[List[str]] = None
       soap_note: Optional[Dict[str, Any]] = None
       payload: Dict[str, Any] = Field(..., min_length=1)

       @field_validator('cns')
       @classmethod
       def validate_cns(cls, v):
           if v is not None and len(v) != 15:
               raise ValueError('CNS must be 15 digits')
           return v

       @field_validator('cpf')
       @classmethod
       def validate_cpf(cls, v):
           if v is not None and len(v) != 14:
               raise ValueError('CPF must be 14 digits')
           return v

   class OfflineCacheMutationResponse(BaseModel):
       model_config = ConfigDict(strict=True, from_attributes=True)
       id: UUID
       entity_type: str
       entity_id: str
       mutation_type: MutationType
       status: MutationStatus
       cns: Optional[str] = None
       cpf: Optional[str] = None
       ciap2_codes: Optional[List[str]] = None
       cid10_codes: Optional[List[str]] = None
       soap_note: Optional[Dict[str, Any]] = None
       payload: Dict[str, Any]
       error_message: Optional[str] = None
       retry_count: int
       created_at: datetime
       updated_at: datetime
   ```

   *Repository Class:*
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, update, delete
   from sqlalchemy.orm import selectinload
   from typing import List, Optional
   import asyncio

   class OfflineCacheRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def add_mutation(self, data: OfflineCacheMutationCreate) -> OfflineCacheMutationResponse:
           mutation = OfflineCacheMutation(
               entity_type=data.entity_type,
               entity_id=data.entity_id,
               mutation_type=data.mutation_type,
               status=MutationStatus.PENDENTE,
               cns=data.cns,
               cpf=data.cpf,
               ciap2_codes=data.ciap2_codes,
               cid10_codes=data.cid10_codes,
               soap_note=data.soap_note,
               payload=data.payload,
           )
           self.session.add(mutation)
           await self.session.commit()
           await self.session.refresh(mutation)
           return OfflineCacheMutationResponse.model_validate(mutation)

       async def get_pending_mutations(self, limit: int = 100) -> List[OfflineCacheMutationResponse]:
           stmt = select(OfflineCacheMutation).where(
               OfflineCacheMutation.status == MutationStatus.PENDENTE
           ).order_by(OfflineCacheMutation.created_at.asc()).limit(limit)
           result = await self.session.execute(stmt)
           mutations = result.scalars().all()
           return [OfflineCacheMutationResponse.model_validate(m) for m in mutations]

       async def mark_sent(self, mutation_id: UUID) -> bool:
           stmt = update(OfflineCacheMutation).where(
               OfflineCacheMutation.id == mutation_id,
               OfflineCacheMutation.status == MutationStatus.PENDENTE
           ).values(status=MutationStatus.ENVIADO, updated_at=datetime.now(timezone.utc))
           result = await self.session.execute(stmt)
           await self.session.commit()
           return result.rowcount > 0

       async def mark_conflict(self, mutation_id: UUID, error_msg: str) -> bool:
           stmt = update(OfflineCacheMutation).where(
               OfflineCacheMutation.id == mutation_id
           ).values(
               status=MutationStatus.CONFLITO,
               error_message=error_msg,
               retry_count=OfflineCacheMutation.retry_count + 1,
               updated_at=datetime.now(timezone.utc)
           )
           result = await self.session.execute(stmt)
           await self.session.commit()
           return result.rowcount > 0

       async def get_by_id(self, mutation_id: UUID) -> Optional[OfflineCacheMutationResponse]:
           stmt = select(OfflineCacheMutation).where(OfflineCacheMutation.id == mutation_id)
           result = await self.session.execute(stmt)
           mutation = result.scalar_one_or_none()
           return OfflineCacheMutationResponse.model_validate(mutation) if mutation else None

       async def cleanup_sent(self, max_age_days: int = 7) -> int:
           cutoff = datetime.now(timezone.utc).replace(tzinfo=None)
           # SQLAlchemy 2.0 datetime comparison
           from datetime import timedelta
           cutoff_dt = datetime.now(timezone.utc) - timedelta(days=max_age_days)
           stmt = delete(OfflineCacheMutation).where(
               OfflineCacheMutation.status == MutationStatus.ENVIADO,
               OfflineCacheMutation.updated_at < cutoff_dt
           )
           result = await self.session.execute(stmt)
           await self.session.commit()
           return result.rowcount
   ```

   *Wait, need to fix datetime timezone handling in SQLAlchemy.*
   SQLAlchemy's `DateTime(timezone=True)` expects aware datetimes. `datetime.now(timezone.utc)` is fine.
   For `updated_at` onupdate, it's better to use `func.now()` or a Python callable that returns aware datetime. I'll stick with `default=lambda: datetime.now(timezone.utc)` and `onupdate=lambda: datetime.now(timezone.utc)`.

   *Refining Repository for SQLAlchemy 2.0 best practices:*
   Use `select` and `update` correctly. Ensure type hints match.
   Add `__init__.py` imports if needed, but the prompt asks for the specific file.

   *Testing Strategy:*
   - Use `pytest-asyncio`
   - Use `sqlalchemy.ext.asyncio.create_async_engine` with SQLite for testing.
   - Create tables before tests.
   - Test `add_mutation`, `get_pending_mutations`, `mark_sent`, `mark_conflict`, `cleanup_sent`.
   - Test Pydantic validation (CNS/CPF length).
   - Test SUS/APS fields.
   - Ensure strict typing and coverage.

   Let's draft the test file structure. The prompt says "Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo". I'll provide:
   1. `backend/app/repositories/offline_cache_repo.py`
   2. `backend/app/repositories/tests/test_offline_cache_repo.py`

   *Self-Correction/Verification during drafting:*
   - SQLAlchemy 2.0 uses `Mapped` and `mapped_column`. I need to import them correctly.
   - Pydantic v2 uses `model_config = ConfigDict(strict=True)`.
   - The prompt mentions "integridade com SQLAlchemy 2.0". I should add unique constraints or indexes if relevant, but for an outbox, it's fine as is. I'll add a composite index on `(status, created_at)` for performance.
   - SUS/APS standards: CIAP-2, CID-10, SOAP, CNS/CPF. I've added them as columns/JSON. I'll ensure the Pydantic models validate them properly.
   - I need to make sure the code is fully executable and type-safe.
   - I'll add `__all__` and proper imports.
   - For the test, I'll use `pytest-asyncio` and `asyncio.run` or `pytest.mark.asyncio`. I'll provide a complete test file.

   Let's structure the repository file carefully.

   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations
   from datetime import datetime, timezone, timedelta
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from uuid import UUID, uuid4

   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from sqlalchemy import String, JSON, DateTime, Integer, Enum as SAEnum, Index, select, update, delete, func
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

   # ... (definitions)
   ```

   Wait, `Index` needs to be imported from `sqlalchemy`.
   I'll add `__table_args__` to the model for indexing.

   Let's refine the model:
   ```python
   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutations"
       __table_args__ = (
           Index("ix_offline_cache_status_created", "status", "created_at"),
       )
       # ... columns
   ```

   Pydantic models: I'll keep them strict. Add validators for CNS/CPF format if needed, but length is enough for now. I'll add a simple regex for CPF/CNS if appropriate, but the prompt says "identificação por CNS/CPF", so I'll just ensure they are stored correctly. I'll add a validator to strip whitespace.

   Repository methods: I'll ensure they handle async properly and use SQLAlchemy 2.0 syntax.

   Test file: I'll create a comprehensive pytest suite.

   Let's write it out carefully.

   *Structure of the response:*
   - File 1: `backend/app/repositories/offline_cache_repo.py`
   - File 2: `backend/app/repositories/tests/test_offline_cache_repo.py`
   - Instructions for running tests.

   *Self-Correction/Check during thought:*
   - SQLAlchemy 2.0 `DateTime(timezone=True)` requires aware datetimes. `datetime.now(timezone.utc)` is correct.
   - `onupdate` in SQLAlchemy 2.0 can be a callable. I'll use `default=func.now()` for better DB-level consistency, but Python callable is fine too. I'll stick to Python callable for strict typing control, or use `func.now()`. Actually, `func.now()` is standard. I'll use `default=func.now()` and `onupdate=func.now()`.
   - Pydantic v2 `ConfigDict(strict=True)` is correct.
   - I need to make sure the test uses `pytest-asyncio` and sets up the async engine/session correctly.
   - I'll add `pytest.ini` or `pyproject.toml` config hints if necessary, but the prompt just asks for the code.
   - I'll ensure all imports are correct.
   - I'll add type hints everywhere.
   - I'll make sure the outbox pattern is clearly implemented.

   Let's draft the code carefully.

   *Repository Code:*
   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations

   from datetime import datetime, timezone, timedelta
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from uuid import UUID, uuid