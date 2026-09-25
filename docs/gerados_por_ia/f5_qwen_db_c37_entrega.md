Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/offline_cache_repo.py` for the "MedIA" project.
   - **Functionality:** Manage a local queue of pending mutations (Outbox pattern), synchronization status (PENDENTE, ENVIADO, CONFLITO), and integrity with SQLAlchemy 2.0.
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards compliance (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Full compliance and coverage with automated pytest tests.
   - **Output Requirement:** Provide complete, executable code. Specify file paths in code blocks.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/offline_cache_repo.py`
   - **Core Features:**
     - Outbox pattern for local mutations queue.
     - Status management: `PENDENTE`, `ENVIADO`, `CONFLITO`.
     - SQLAlchemy 2.0 models & queries.
     - Pydantic v2 for data validation/serialization.
     - SUS/APS standards: CIAP-2, CID-10, SOAP, CNS/CPF.
     - Type hints throughout.
     - Pytest coverage (I need to provide the test file as well, or at least ensure the code is testable and provide tests).
   - **Architecture/Standards:**
     - Need to model mutations that can contain clinical data (SOAP, CID-10, CIAP-2, CNS/CPF).
     - Use SQLAlchemy 2.0 declarative style.
     - Use Pydantic v2 for DTOs.
     - Implement repository pattern methods: `add_mutation`, `get_pending`, `mark_sent`, `mark_conflict`, `get_by_id`, etc.
     - Handle integrity (constraints, unique keys, status transitions).

3.  **Design Decisions:**
   - **Database Models:**
     - `OfflineCacheMutation`: Represents a pending mutation.
     - Fields: `id` (UUID), `entity_type` (str), `entity_id` (str), `mutation_type` (CREATE/UPDATE/DELETE), `payload` (JSON), `status` (Enum), `created_at`, `updated_at`, `sync_version` (for conflict detection), `cns` (optional), `cpf` (optional), `cid10` (optional), `ciap2` (optional), `soap_notes` (JSON/str).
     - Actually, to keep it clean and aligned with SUS/APS, I'll add specific fields for clinical context, but keep the payload generic for flexibility. Or I can make the payload a Pydantic model that includes these fields. Let's stick to a generic `payload` JSONB field but add indexes/constraints for CNS/CPF/CID-10 if needed. Actually, the prompt says "Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF)". This likely means the mutations should support or reference these standards. I'll add explicit fields or a structured payload schema.
     - Let's define a Pydantic model `ClinicalMutationPayload` that includes `cns`, `cpf`, `cid10`, `ciap2`, `soap_method`.
     - Status Enum: `MutationStatus` with `PENDENTE`, `ENVIADO`, `CONFLITO`.
   - **Repository:**
     - `OfflineCacheRepository` class with async methods (since SQLAlchemy 2.0 is often used with async, but I'll make it sync/async agnostic or explicitly async as it's modern). I'll use `AsyncSession` for modern stack, but provide sync if needed. I'll stick to `AsyncSession` as it's standard for SQLAlchemy 2.0 in modern backends. I'll also provide a sync wrapper if necessary, but async is fine.
     - Methods: `create_mutation`, `get_pending_mutations`, `mark_as_sent`, `mark_as_conflict`, `get_mutation_by_id`, `delete_mutation`.
     - Integrity: Use DB constraints, unique indexes on `(entity_type, entity_id, sync_version)`, check constraints on status.
   - **Pydantic v2:**
     - Define schemas for request/response.
   - **Testing:**
     - Provide `tests/test_offline_cache_repo.py` with pytest, using `pytest-asyncio`, `aiosqlite` or `pytest-postgresql`/`testcontainers`. I'll use `pytest-asyncio` with an in-memory SQLite for simplicity and reliability in the provided code, or mock the session. Actually, providing a complete test with `pytest-asyncio` and `aiosqlite` is better. I'll use `pytest` with `asyncio` and a temporary SQLite database.

4.  **Drafting - `offline_cache_repo.py`:**
   - Imports: `uuid`, `datetime`, `enum`, `json`, `typing`, `sqlalchemy`, `pydantic`, `pydantic.json_schema`.
   - Define `MutationStatus` enum.
   - Define Pydantic models: `ClinicalContext`, `MutationPayload`, `MutationOut`.
   - Define SQLAlchemy model: `OfflineCacheMutation`.
   - Define Repository class with async methods.
   - Add type hints, docstrings.
   - Ensure SUS/APS fields are present.

   Let's write it out carefully.

   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Any, Optional, Sequence
   import json

   from pydantic import BaseModel, Field, ConfigDict
   from sqlalchemy import (
       String,
       Text,
       JSON,
       Enum as SAEnum,
       UniqueConstraint,
       CheckConstraint,
       select,
       func,
       update,
   )
   from sqlalchemy.dialects.postgresql import JSONB
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
   from sqlalchemy.ext.asyncio import AsyncSession

   # --- Enums & Constants ---
   class MutationStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class MutationType(str, Enum):
       CREATE = "CREATE"
       UPDATE = "UPDATE"
       DELETE = "DELETE"

   # --- Pydantic v2 Schemas ---
   class ClinicalContext(BaseModel):
       cns: Optional[str] = Field(None, pattern=r"^\d{15}$", description="CNS do paciente")
       cpf: Optional[str] = Field(None, pattern=r"^\d{11}$", description="CPF do paciente")
       cid10: Optional[str] = Field(None, description="CID-10 principal")
       ciap2: Optional[str] = Field(None, description="CIAP-2 principal")
       soap_method: Optional[str] = Field(None, description="Método SOAP (Subjetivo, Objetivo, Avaliação, Plano)")

   class MutationPayload(BaseModel):
       entity_type: str
       entity_id: str
       mutation_type: MutationType
       clinical_context: Optional[ClinicalContext] = None
       raw_data: dict[str, Any] = Field(default_factory=dict)
       sync_version: int = 1

   class MutationOut(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: uuid.UUID
       entity_type: str
       entity_id: str
       mutation_type: MutationType
       status: MutationStatus
       payload: dict[str, Any]
       clinical_context: Optional[ClinicalContext] = None
       created_at: datetime
       updated_at: datetime
       sync_version: int

   # --- SQLAlchemy 2.0 Model ---
   class Base(DeclarativeBase):
       pass

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutations"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
       entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
       mutation_type: Mapped[MutationType] = mapped_column(SAEnum(MutationType), nullable=False)
       status: Mapped[MutationStatus] = mapped_column(SAEnum(MutationStatus), default=MutationStatus.PENDENTE, nullable=False)
       payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
       clinical_context: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
       sync_version: Mapped[int] = mapped_column(default=1, nullable=False)
       created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)
       updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

       __table_args__ = (
           UniqueConstraint("entity_type", "entity_id", "sync_version", name="uq_entity_sync"),
           CheckConstraint("status IN ('PENDENTE', 'ENVIADO', 'CONFLITO')", name="chk_status"),
       )

   # --- Repository ---
   class OfflineCacheRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def create_mutation(self, payload: MutationPayload) -> OfflineCacheMutation:
           clinical_ctx = payload.clinical_context.model_dump() if payload.clinical_context else None
           mutation = OfflineCacheMutation(
               entity_type=payload.entity_type,
               entity_id=payload.entity_id,
               mutation_type=payload.mutation_type,
               status=MutationStatus.PENDENTE,
               payload=payload.model_dump(),
               clinical_context=clinical_ctx,
               sync_version=payload.sync_version,
           )
           self.session.add(mutation)
           await self.session.flush()
           await self.session.refresh(mutation)
           return mutation

       async def get_pending_mutations(self, limit: int = 100) -> Sequence[OfflineCacheMutation]:
           stmt = select(OfflineCacheMutation).where(
               OfflineCacheMutation.status == MutationStatus.PENDENTE
           ).order_by(OfflineCacheMutation.created_at.asc()).limit(limit)
           result = await self.session.execute(stmt)
           return list(result.scalars().all())

       async def get_mutation_by_id(self, mutation_id: uuid.UUID) -> Optional[OfflineCacheMutation]:
           stmt = select(OfflineCacheMutation).where(OfflineCacheMutation.id == mutation_id)
           result = await self.session.execute(stmt)
           return result.scalar_one_or_none()

       async def mark_as_sent(self, mutation_id: uuid.UUID) -> Optional[OfflineCacheMutation]:
           stmt = (
               update(OfflineCacheMutation)
               .where(
                   OfflineCacheMutation.id == mutation_id,
                   OfflineCacheMutation.status == MutationStatus.PENDENTE,
               )
               .values(status=MutationStatus.ENVIADO, updated_at=datetime.now(timezone.utc))
           )
           await self.session.execute(stmt)
           await self.session.flush()
           return await self.get_mutation_by_id(mutation_id)

       async def mark_as_conflict(self, mutation_id: uuid.UUID, new_version: int) -> Optional[OfflineCacheMutation]:
           stmt = (
               update(OfflineCacheMutation)
               .where(
                   OfflineCacheMutation.id == mutation_id,
                   OfflineCacheMutation.status == MutationStatus.PENDENTE,
               )
               .values(status=MutationStatus.CONFLITO, sync_version=new_version, updated_at=datetime.now(timezone.utc))
           )
           await self.session.execute(stmt)
           await self.session.flush()
           return await self.get_mutation_by_id(mutation_id)

       async def delete_mutation(self, mutation_id: uuid.UUID) -> bool:
           stmt = select(OfflineCacheMutation).where(OfflineCacheMutation.id == mutation_id)
           result = await self.session.execute(stmt)
           mutation = result.scalar_one_or_none()
           if mutation:
               await self.session.delete(mutation)
               await self.session.flush()
               return True
           return False

       async def get_conflict_mutations(self) -> Sequence[OfflineCacheMutation]:
           stmt = select(OfflineCacheMutation).where(
               OfflineCacheMutation.status == MutationStatus.CONFLITO
           ).order_by(OfflineCacheMutation.updated_at.desc())
           result = await self.session.execute(stmt)
           return list(result.scalars().all())
   ```

5.  **Drafting - `tests/test_offline_cache_repo.py`:**
   - Need to set up async test environment.
   - Use `pytest-asyncio`.
   - Use `aiosqlite` or `pytest-postgresql`. I'll use `aiosqlite` with a temporary SQLite file for simplicity and zero external dependencies besides standard test libs. Actually, `pytest-asyncio` + `aiosqlite` is standard.
   - I'll create a fixture that sets up an in-memory SQLite database with the tables.
   - Write tests for: create, get pending, mark sent, mark conflict, delete, integrity constraints.
   - Ensure Pydantic v2 validation is tested.
   - Ensure SUS/APS fields are validated.

   Let's structure the test file carefully.

   ```python
   # Arquivo: backend/app/tests/test_offline_cache_repo.py
   import pytest
   import pytest_asyncio
   import asyncio
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   from sqlalchemy.orm import sessionmaker
   from uuid import uuid4
   from pydantic import ValidationError
   import os

   from app.repositories.offline_cache_repo import (
       Base,
       OfflineCacheMutation,
       OfflineCacheRepository,
       MutationPayload,
       MutationType,
       MutationStatus,
       ClinicalContext,
   )

   # Configuração do banco em memória para testes
   DATABASE_URL = "sqlite+aiosqlite:///:memory:"

   @pytest_asyncio.fixture
   async def engine():
       engine = create_async_engine(DATABASE_URL, echo=False)
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
       yield engine
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.drop_all)
       await engine.dispose()

   @pytest_asyncio.fixture
   async def session(engine):
       async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
       async with async_session() as s:
           yield s

   @pytest_asyncio.fixture
   async def repo(session):
       return OfflineCacheRepository(session)

   @pytest_asyncio.fixture
   async def valid_payload():
       return MutationPayload(
           entity_type="CONSULTA",
           entity_id="123e4567-e89b-12d3-a456-426614174000",
           mutation_type=MutationType.CREATE,
           clinical_context=ClinicalContext(
               cns="123456789012345",
               cpf="12345678901",
               cid10="J06.9",
               ciap2="R18",
               soap_method="Subjetivo: Dor abdominal. Objetivo: Abdome doloroso. Avaliação: Gastroenterite. Plano: Exames e repouso."
           ),
           raw_data={"diagnostico": "Gastroenterite"},
           sync_version=1
       )

   class TestOfflineCacheRepository:
       @pytest.mark.asyncio
       async def test_create_mutation(self, repo, valid_payload):
           mutation = await repo.create_mutation(valid_payload)
           assert mutation.id is not None
           assert mutation.status == MutationStatus.PENDENTE
           assert mutation.entity_type == "CONSULTA"
           assert mutation.clinical_context is not None
           assert mutation.clinical_context["cid10"] == "J06.9"

       @pytest.mark.asyncio
       async def test_get_pending_mutations(self, repo, valid_payload):
           await repo.create_mutation(valid_payload)
           pending = await repo.get_pending_mutations()
           assert len(pending) == 1
           assert pending[0].status == MutationStatus.PENDENTE

       @pytest.mark.asyncio
       async def test_mark_as_sent(self, repo, valid_payload):
           mutation = await repo.create_mutation(valid_payload)
           updated = await repo.mark_as_sent(mutation.id)
           assert updated.status == MutationStatus.ENVIADO
           assert updated.updated_at > mutation.created_at

       @pytest.mark.asyncio
       async def test_mark_as_conflict(self, repo, valid_payload):
           mutation = await repo.create_mutation(valid_payload)
           updated = await repo.mark_as_conflict(mutation.id, new_version=2)
           assert updated.status == MutationStatus.CONFLITO
           assert updated.sync_version == 2

       @pytest.mark.asyncio
       async def test_delete_mutation(self, repo, valid_payload):
           mutation = await repo.create_mutation(valid_payload)
           deleted = await repo.delete_mutation(mutation.id)
           assert deleted is True
           pending = await repo.get_pending_mutations()
           assert len(pending) == 0

       @pytest.mark.asyncio
       async def test_get_conflict_mutations(self, repo, valid_payload):
           mutation = await repo.create_mutation(valid_payload)
           await repo.mark_as_conflict(mutation.id, new_version=2)
           conflicts = await repo.get_conflict_mutations()
           assert len(conflicts) == 1
           assert conflicts[0].id == mutation.id

       @pytest.mark.asyncio
       async def test_pydantic_validation_cns(self):
           with pytest.raises(ValidationError):
               MutationPayload(
                   entity_type="CONSULTA",
                   entity_id="123",
                   mutation_type=MutationType.CREATE,
                   clinical_context=ClinicalContext(cns="123")
               )

       @pytest.mark.asyncio
       async def test_pydantic_validation_cpf(self):
           with pytest.raises(ValidationError):
              