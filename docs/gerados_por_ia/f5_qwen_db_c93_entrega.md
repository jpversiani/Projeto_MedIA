Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/offline_cache_repo.py` for a project called "MedIA".
   - **Functionality:** Manage a local queue of pending mutations (outbox pattern), synchronization status (PENDENTE, ENVIADO, CONFLITO), and integrity using SQLAlchemy 2.0.
   - **Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards compliance (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Full compliance and automated test coverage with pytest.
     - Provide complete, executable code.
     - Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/offline_cache_repo.py`
   - **Core Features:**
     - Outbox pattern implementation for local mutations.
     - Status management: `PENDENTE`, `ENVIADO`, `CONFLITO`.
     - SQLAlchemy 2.0 ORM models and queries.
     - Pydantic v2 models for data validation/serialization.
     - Strict typing (Python 3.12).
     - SUS/APS context: CIAP-2, CID-10, SOAP, CNS/CPF.
     - Pytest coverage (I need to provide the test file as well, or at least ensure the code is testable and mention/test coverage).
   - **Architecture/Standards:**
     - Need models for mutations/cache entries.
     - Need enums for status.
     - Need repository class with methods to add, update, sync, handle conflicts, etc.
     - Need Pydantic schemas for input/output.
     - Need to integrate SUS/APS concepts (maybe as fields in the mutation model or validation rules).

3.  **Design Components:**
   - **Enums:** `SyncStatus` (PENDENTE, ENVIADO, CONFLITO)
   - **Pydantic Models:**
     - `MutationPayload` (for creating mutations)
     - `MutationResponse` (for returning mutations)
     - `SyncResult` (for sync operation results)
   - **SQLAlchemy 2.0 Model:**
     - `OfflineCacheMutation` table
     - Fields: id, patient_cns, patient_cpf, mutation_type, payload (JSON), status, created_at, updated_at, sync_error, version
     - Indexes for status and patient identifiers
   - **Repository Class:** `OfflineCacheRepository`
     - `__init__(self, session: AsyncSession)`
     - `add_mutation(self, payload: MutationPayload) -> MutationResponse`
     - `get_pending_mutations(self, limit: int = 100) -> list[MutationResponse]`
     - `mark_as_sent(self, mutation_id: UUID) -> None`
     - `mark_as_conflict(self, mutation_id: UUID, error: str) -> None`
     - `sync_batch(self, mutations: list[MutationResponse]) -> SyncResult`
     - `get_by_patient(self, cns: str | None, cpf: str | None) -> list[MutationResponse]`
     - Integrity checks (e.g., validate CNS/CPF format, SOAP/CID-10/CIAP-2 structure if applicable)
   - **SUS/APS Integration:**
     - CNS validation (15 digits, checksum)
     - CPF validation (11 digits, checksum)
     - SOAP/CID-10/CIAP-2 structure validation in payload
     - I'll add validation functions or Pydantic validators for these.

4.  **Draft Code (Mental Refinement):**
   Let's structure the file carefully.

   *Imports:*
   ```python
   from __future__ import annotations
   import json
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Any, Optional

   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy import (
       Column,
       DateTime,
       Enum as SAEnum,
       ForeignKey,
       Index,
       JSON,
       String,
       Text,
       UUID,
       func,
       select,
   )
   from sqlalchemy.dialects.postgresql import JSONB
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
   from sqlalchemy.ext.asyncio import AsyncSession
   ```

   *Enums:*
   ```python
   class SyncStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"
   ```

   *Pydantic Models:*
   ```python
   class MutationPayload(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True)
       patient_cns: Optional[str] = Field(None, min_length=15, max_length=15)
       patient_cpf: Optional[str] = Field(None, min_length=11, max_length=11)
       mutation_type: str = Field(..., pattern=r"^(CREATE|UPDATE|DELETE)$")
       clinical_data: dict[str, Any] = Field(default_factory=dict)
       # SUS/APS fields
       ciap2_codes: list[str] = Field(default_factory=list)
       cid10_codes: list[str] = Field(default_factory=list)
       soap_note: Optional[str] = None

       @field_validator("patient_cns")
       @classmethod
       def validate_cns(cls, v: Optional[str]) -> Optional[str]:
           if v is None:
               return v
           # Simplified CNS validation (15 digits, checksum logic omitted for brevity but noted)
           if not v.isdigit() or len(v) != 15:
               raise ValueError("CNS deve ter 15 dígitos numéricos")
           return v

       @field_validator("patient_cpf")
       @classmethod
       def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
           if v is None:
               return v
           if not v.isdigit() or len(v) != 11:
               raise ValueError("CPF deve ter 11 dígitos numéricos")
           return v
   ```

   *SQLAlchemy Model:*
   ```python
   class Base(DeclarativeBase):
       pass

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutations"

       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       patient_cns: Mapped[Optional[str]] = mapped_column(String(15), index=True)
       patient_cpf: Mapped[Optional[str]] = mapped_column(String(11), index=True)
       mutation_type: Mapped[str] = mapped_column(String(10))
       clinical_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
       ciap2_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
       cid10_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
       soap_note: Mapped[Optional[str]] = mapped_column(Text)
       status: Mapped[SyncStatus] = mapped_column(SAEnum(SyncStatus), default=SyncStatus.PENDENTE)
       sync_error: Mapped[Optional[str]] = mapped_column(Text)
       version: Mapped[int] = mapped_column(default=1)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

       __table_args__ = (
           Index("ix_offline_cache_status", "status"),
           Index("ix_offline_cache_patient", "patient_cns", "patient_cpf"),
       )
   ```

   *Repository Class:*
   ```python
   class OfflineCacheRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def add_mutation(self, payload: MutationPayload) -> MutationResponse:
           # ... implementation
   ```

   Wait, I need to define `MutationResponse` and `SyncResult` first.
   Let's adjust the Pydantic models to be complete.

   ```python
   class MutationResponse(BaseModel):
       id: uuid.UUID
       patient_cns: Optional[str]
       patient_cpf: Optional[str]
       mutation_type: str
       clinical_data: dict[str, Any]
       ciap2_codes: list[str]
       cid10_codes: list[str]
       soap_note: Optional[str]
       status: SyncStatus
       sync_error: Optional[str]
       version: int
       created_at: datetime
       updated_at: datetime

       model_config = ConfigDict(from_attributes=True)

   class SyncResult(BaseModel):
       success_count: int = 0
       conflict_count: int = 0
       errors: list[str] = Field(default_factory=list)
   ```

   Now, implement repository methods with SQLAlchemy 2.0 syntax.
   Need to handle async session properly.
   Add integrity checks: CNS/CPF mutual exclusivity (at least one required), SOAP/CID-10/CIAP-2 validation (simplified regex/format checks), versioning for optimistic concurrency.

   Let's draft the repository methods carefully:

   ```python
   class OfflineCacheRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def add_mutation(self, payload: MutationPayload) -> MutationResponse:
           # Integrity: CNS or CPF required
           if not payload.patient_cns and not payload.patient_cpf:
               raise ValueError("É obrigatório informar CNS ou CPF do paciente.")

           # SUS/APS: Validate SOAP/CID-10/CIAP-2 structure if present
           if payload.soap_note:
               # Simplified validation for SOAP structure (S, O, A, P sections)
               soap_sections = ["S", "O", "A", "P"]
               if not all(section in payload.soap_note.upper() for section in soap_sections):
                   raise ValueError("SOAP note deve conter as seções S, O, A, P.")

           mutation = OfflineCacheMutation(
               patient_cns=payload.patient_cns,
               patient_cpf=payload.patient_cpf,
               mutation_type=payload.mutation_type,
               clinical_data=payload.clinical_data,
               ciap2_codes=payload.ciap2_codes,
               cid10_codes=payload.cid10_codes,
               soap_note=payload.soap_note,
           )
           self.session.add(mutation)
           await self.session.flush()
           await self.session.refresh(mutation)
           return MutationResponse.model_validate(mutation)

       async def get_pending_mutations(self, limit: int = 100) -> list[MutationResponse]:
           stmt = (
               select(OfflineCacheMutation)
               .where(OfflineCacheMutation.status == SyncStatus.PENDENTE)
               .order_by(OfflineCacheMutation.created_at.asc())
               .limit(limit)
           )
           result = await self.session.execute(stmt)
           mutations = result.scalars().all()
           return [MutationResponse.model_validate(m) for m in mutations]

       async def mark_as_sent(self, mutation_id: uuid.UUID) -> None:
           stmt = (
               update(OfflineCacheMutation)
               .where(OfflineCacheMutation.id == mutation_id)
               .values(status=SyncStatus.ENVIADO, updated_at=func.now(timezone=True))
           )
           await self.session.execute(stmt)
           await self.session.commit()

       async def mark_as_conflict(self, mutation_id: uuid.UUID, error: str) -> None:
           stmt = (
               update(OfflineCacheMutation)
               .where(OfflineCacheMutation.id == mutation_id)
               .values(status=SyncStatus.CONFLITO, sync_error=error, updated_at=func.now(timezone=True))
           )
           await self.session.execute(stmt)
           await self.session.commit()

       async def sync_batch(self, mutations: list[MutationResponse]) -> SyncResult:
           result = SyncResult()
           for mutation in mutations:
               try:
                   # Simulate sync logic (in real app, this would call remote API)
                   # For now, just mark as sent
                   await self.mark_as_sent(mutation.id)
                   result.success_count += 1
               except Exception as e:
                   await self.mark_as_conflict(mutation.id, str(e))
                   result.conflict_count += 1
                   result.errors.append(f"Mutation {mutation.id}: {str(e)}")
           return result

       async def get_by_patient(self, cns: Optional[str] = None, cpf: Optional[str] = None) -> list[MutationResponse]:
           conditions = [OfflineCacheMutation.status == SyncStatus.PENDENTE]
           if cns:
               conditions.append(OfflineCacheMutation.patient_cns == cns)
           if cpf:
               conditions.append(OfflineCacheMutation.patient_cpf == cpf)

           stmt = select(OfflineCacheMutation).where(*conditions).order_by(OfflineCacheMutation.created_at.desc())
           res = await self.session.execute(stmt)
           mutations = res.scalars().all()
           return [MutationResponse.model_validate(m) for m in mutations]
   ```

   Wait, I need to import `update` from sqlalchemy. Also, `func.now(timezone=True)` might need adjustment for SQLAlchemy 2.0. `func.now()` is fine, or `func.current_timestamp()`. I'll use `func.now()`.

   Let's fix imports and ensure SQLAlchemy 2.0 compatibility:
   ```python
   from sqlalchemy import update, func, select
   ```

   Also, need to handle timezone properly. `datetime.now(timezone.utc)` is fine for defaults. For `onupdate`, `func.now()` returns UTC in PostgreSQL. I'll stick with `func.now()`.

   Now, I need to add Pytest tests as requested ("cobertura de testes automatizados com pytest"). I'll create a separate test file or include it in the response. The prompt says "Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo". I'll provide both the repo file and the test file.

   Let's structure the test file: `backend/app/tests/repositories/test_offline_cache_repo.py`

   Tests should cover:
   - Adding mutation with valid CNS/CPF
   - Validation errors (missing CNS/CPF, invalid format)
   - SOAP/CID-10/CIAP-2 validation
   - Pending mutations retrieval
   - Mark as sent/conflict
   - Sync batch
   - Get by patient

   I'll use `pytest-asyncio` and `pytest` with `asyncio` fixtures. I'll mock the database session or use an in-memory SQLite database for tests. Since it's SQLAlchemy 2.0, I'll use `pytest-asyncio` and `sqlalchemy.ext.asyncio` with `create_async_engine` and `async_sessionmaker`.

   Actually, for simplicity and reliability in the response, I'll provide a test file that uses `pytest-asyncio` and a mock session or a real async engine with `autocommit=False` and `expire_on_commit=False`. I'll make it robust.

   Let's draft the test file carefully.

   ```python
   import pytest
   import asyncio
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   from sqlalchemy.orm import sessionmaker
   from backend.app.repositories.offline_cache_repo import (
       OfflineCacheRepository,
       MutationPayload,
       SyncStatus,
       OfflineCacheMutation,
       Base,
   )

   @pytest.fixture(scope="module")
   def event_loop():
       loop = asyncio.new_event_loop()
       yield loop
       loop.close()

   @pytest.fixture(scope="module")
   async def engine():
       engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
       yield engine
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.drop_all)
       await engine.dispose()

   @pytest.fixture
   async def session(engine):
       async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
       async with async_session() as sess:
           yield sess

   @pytest.fixture
   def repo(session):
       return OfflineCacheRepository(session)
   ```

   Wait, `aiosqlite` might not be installed by default. I'll note it in requirements or use `pytest-asyncio` standard approach. I'll stick to standard async testing patterns.

   Let's write the test cases:

   ```python
   class TestOfflineCacheRepository:
       @pytest.mark.asyncio
       async def test_add_mutation_valid_cns(self, repo):
           payload = MutationPayload(
               patient_cns="123456789012345",
               mutation_type="CREATE",
               clinical_data={"diagnosis": "CID-10: A00.0"},
               cid10_codes=["A00.0"],
               soap_note="S: Queixa principal\nO: Exame físico\nA: Hipótese diagnóstica\nP: Conduta"
           )
           result = await repo.add_mutation(payload)
           assert result.status == SyncStatus.PENDENTE
           assert result.patient_cns == "123456789012345"
           assert result.mutation_type == "CREATE"

       @pytest.mark.asyncio
       async def test_add_mutation_valid_cpf(self, repo):
           payload = MutationPayload(
               patient_cpf="12345678901",
               mutation_type="UPDATE",
               clinical_data={"lab": "Hemograma"},
               ciap2_codes=["R73"],
           )
           result = await repo.add_mutation(payload)
           assert result.patient_cpf == "12345678901"

       @pytest.mark.asyncio
      