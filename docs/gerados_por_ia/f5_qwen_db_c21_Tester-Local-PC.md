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
     - Outbox pattern implementation for offline mutations.
     - Status management: `PENDENTE`, `ENVIADO`, `CONFLITO`.
     - Data integrity handling.
     - SQLAlchemy 2.0 ORM models and queries.
     - Pydantic v2 for data validation/serialization.
     - Python 3.12 type hints.
     - SUS/APS context: CIAP-2, CID-10, SOAP, CNS/CPF. This implies the mutations might relate to patient records, clinical notes, or appointments. I'll design the model to support these fields.
     - Pytest coverage: Need to provide tests as well, though the prompt specifically asks for the repo file. I should include tests to fulfill "cobertura de testes automatizados com pytest". I'll create a separate test file or include it in the response as requested. The prompt says "Para cada arquivo criado ou modificado...", so I'll provide both the repo and the test file.

3.  **Design the SQLAlchemy Model:**
   - Table: `offline_cache_mutation`
   - Fields:
     - `id`: UUID or Integer (PK)
     - `mutation_type`: Enum (CREATE, UPDATE, DELETE)
     - `entity_type`: Enum (PATIENT, APPOINTMENT, CLINICAL_NOTE, etc.)
     - `entity_id`: String/UUID (FK reference)
     - `payload`: JSON (Pydantic model or dict)
     - `status`: Enum (PENDENTE, ENVIADO, CONFLITO)
     - `error_message`: Optional String
     - `created_at`: DateTime
     - `updated_at`: DateTime
     - `synced_at`: Optional DateTime
   - SUS/APS specific fields might be embedded in `payload`, but I can add specific columns for CNS/CPF, CID-10, CIAP-2, SOAP if needed. However, keeping it generic with JSON payload is better for an outbox pattern. I'll add specific columns for quick indexing/filtering if needed, or just rely on payload. Let's stick to a generic outbox model but include SUS/APS context in the Pydantic schemas and comments.

   Actually, the prompt says "Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF)". This likely means the mutations should support these fields. I'll add them as optional columns or ensure the Pydantic schema supports them.

   Let's design the model with explicit columns for clarity and performance:
   - `id`: UUID
   - `mutation_type`: String
   - `target_entity`: String
   - `target_id`: String
   - `patient_cns`: Optional[str]
   - `patient_cpf`: Optional[str]
   - `cid10_codes`: JSON (list)
   - `ciap2_codes`: JSON (list)
   - `soap_method`: JSON (dict)
   - `payload`: JSON
   - `status`: String (Enum)
   - `error_message`: Optional[str]
   - `created_at`: DateTime
   - `updated_at`: DateTime
   - `synced_at`: Optional[DateTime]

   Wait, SQLAlchemy 2.0 uses `Mapped` and `mapped_column`. I'll use that.
   Enums: `MutationStatus` (PENDENTE, ENVIADO, CONFLITO), `MutationType` (CREATE, UPDATE, DELETE).

4.  **Design Pydantic Schemas:**
   - `OfflineCacheMutationCreate`
   - `OfflineCacheMutationUpdate`
   - `OfflineCacheMutationRead`
   - All with Pydantic v2 features (`model_config`, `Field`, `ConfigDict`, `computed_field`, etc.)

5.  **Design Repository Class:**
   - `OfflineCacheRepository`
   - Methods:
     - `__init__(self, session: AsyncSession)`
     - `add_mutation(self, mutation: OfflineCacheMutationCreate) -> OfflineCacheMutationRead`
     - `get_pending_mutations(self, limit: int = 100) -> list[OfflineCacheMutationRead]`
     - `mark_as_sent(self, mutation_id: UUID) -> bool`
     - `mark_as_conflict(self, mutation_id: UUID, error: str) -> bool`
     - `get_by_status(self, status: MutationStatus) -> list[OfflineCacheMutationRead]`
     - `get_integrity_report(self) -> dict` (for integrity checks)
     - `clear_synced_mutations(self, before_date: datetime) -> int`
   - Use SQLAlchemy 2.0 async queries (`select`, `insert`, `update`, `delete`).
   - Handle transactions properly.

6.  **Incorporate SUS/APS Context:**
   - Add validation in Pydantic schemas for CNS/CPF format.
   - Add validation for CID-10/CIAP-2 codes.
   - Add comments explaining compliance.
   - Use `pydantic` validators (`@field_validator`).

7.  **Draft the Code (Mental Refinement):**
   *Imports:* `uuid`, `datetime`, `enum`, `typing`, `sqlalchemy`, `pydantic`, `pydantic.functional_validators`, `pydantic.functional_serializers`, `sqlalchemy.orm`, `sqlalchemy.ext.asyncio`, `sqlalchemy.dialects.postgresql`, etc.
   *Enums:* `MutationStatus`, `MutationType`
   *Pydantic Models:* `OfflineCacheMutationPayload`, `OfflineCacheMutationCreate`, `OfflineCacheMutationRead`
   *SQLAlchemy Model:* `OfflineCacheMutation`
   *Repository:* `OfflineCacheRepository`

   Let's write it out carefully.

   *Self-Correction/Verification during drafting:*
   - SQLAlchemy 2.0 requires `Mapped` and `mapped_column`. I'll use `sqlalchemy.orm.Mapped` and `sqlalchemy.orm.mapped_column`.
   - Pydantic v2 uses `model_config = ConfigDict(from_attributes=True)` for ORM mode.
   - CNS/CPF validation: CNS is 15 digits, CPF is 11 digits. I'll add regex validators.
   - CID-10/CIAP-2: Usually alphanumeric. I'll keep it flexible but add type hints.
   - Outbox pattern: The repo should handle adding to the queue, retrieving pending, and updating status. It should be async.
   - Integrity: Check for orphaned records, status consistency, or payload schema validation. I'll add a method to verify integrity.
   - Tests: I'll provide a comprehensive pytest file.

   Structure:
   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   ... code ...
   ```
   ```python
   # Arquivo: backend/tests/test_offline_cache_repo.py
   ... code ...
   ```

   Let's draft the repository file carefully.

   *Key SQLAlchemy 2.0 patterns:*
   ```python
   from sqlalchemy import select, update, delete, func
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   import uuid
   from datetime import datetime
   from enum import Enum
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from typing import Optional, List, Dict, Any
   ```

   *Model:*
   ```python
   class Base(DeclarativeBase):
       pass

   class MutationStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class MutationType(str, Enum):
       CREATE = "CREATE"
       UPDATE = "UPDATE"
       DELETE = "DELETE"

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutation"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       mutation_type: Mapped[MutationType] = mapped_column()
       entity_type: Mapped[str] = mapped_column() # e.g., "CLINICAL_NOTE", "APPOINTMENT"
       entity_id: Mapped[str] = mapped_column()
       patient_cns: Mapped[Optional[str]] = mapped_column(index=True)
       patient_cpf: Mapped[Optional[str]] = mapped_column(index=True)
       cid10_codes: Mapped[Optional[List[str]]] = mapped_column(server_default="[]")
       ciap2_codes: Mapped[Optional[List[str]]] = mapped_column(server_default="[]")
       soap_method: Mapped[Optional[Dict[str, Any]]] = mapped_column(server_default="{}")
       payload: Mapped[Dict[str, Any]] = mapped_column()
       status: Mapped[MutationStatus] = mapped_column(default=MutationStatus.PENDENTE)
       error_message: Mapped[Optional[str]] = mapped_column()
       created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, server_default=func.now())
       updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow)
       synced_at: Mapped[Optional[datetime]] = mapped_column()
   ```
   Wait, `server_default` for JSON in PostgreSQL is usually `'{}'::json` or `'[]'::json`. I'll use `default` and `server_default` carefully, or just rely on Pydantic defaults and let SQLAlchemy handle it. Actually, for async, `default` is fine. I'll use `default_factory` or just `default`.

   *Pydantic Schemas:*
   ```python
   class OfflineCacheMutationPayload(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: uuid.UUID
       mutation_type: MutationType
       entity_type: str
       entity_id: str
       patient_cns: Optional[str] = None
       patient_cpf: Optional[str] = None
       cid10_codes: List[str] = Field(default_factory=list)
       ciap2_codes: List[str] = Field(default_factory=list)
       soap_method: Optional[Dict[str, Any]] = None
       payload: Dict[str, Any]
       status: MutationStatus
       error_message: Optional[str] = None
       created_at: datetime
       updated_at: datetime
       synced_at: Optional[datetime] = None

       @field_validator('patient_cns')
       @classmethod
       def validate_cns(cls, v):
           if v and not v.isdigit() or len(v) != 15:
               raise ValueError('CNS deve ter 15 dígitos numéricos')
           return v

       @field_validator('patient_cpf')
       @classmethod
       def validate_cpf(cls, v):
           if v and not v.isdigit() or len(v) != 11:
               raise ValueError('CPF deve ter 11 dígitos numéricos')
           return v
   ```
   Actually, CPF validation is more complex (check digits), but for simplicity in this context, I'll keep it basic or use a regex. I'll stick to basic length/digit check for brevity, but note it. I'll add a proper CPF validator if needed, but it's fine.

   *Repository:*
   ```python
   class OfflineCacheRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def add_mutation(self, mutation: OfflineCacheMutationPayload) -> OfflineCacheMutationPayload:
           db_mutation = OfflineCacheMutation(**mutation.model_dump())
           self.session.add(db_mutation)
           await self.session.flush()
           await self.session.refresh(db_mutation)
           return OfflineCacheMutationPayload.model_validate(db_mutation)

       async def get_pending_mutations(self, limit: int = 100) -> List[OfflineCacheMutationPayload]:
           stmt = select(OfflineCacheMutation).where(
               OfflineCacheMutation.status == MutationStatus.PENDENTE
           ).order_by(OfflineCacheMutation.created_at.asc()).limit(limit)
           result = await self.session.execute(stmt)
           return [OfflineCacheMutationPayload.model_validate(row) for row in result.scalars().all()]

       async def mark_as_sent(self, mutation_id: uuid.UUID) -> bool:
           stmt = update(OfflineCacheMutation).where(
               OfflineCacheMutation.id == mutation_id,
               OfflineCacheMutation.status == MutationStatus.PENDENTE
           ).values(
               status=MutationStatus.ENVIADO,
               synced_at=datetime.utcnow()
           ).returning(OfflineCacheMutation.id)
           result = await self.session.execute(stmt)
           return result.scalar_one() is not None

       async def mark_as_conflict(self, mutation_id: uuid.UUID, error: str) -> bool:
           stmt = update(OfflineCacheMutation).where(
               OfflineCacheMutation.id == mutation_id,
               OfflineCacheMutation.status == MutationStatus.PENDENTE
           ).values(
               status=MutationStatus.CONFLITO,
               error_message=error
           ).returning(OfflineCacheMutation.id)
           result = await self.session.execute(stmt)
           return result.scalar_one() is not None

       async def get_integrity_report(self) -> Dict[str, Any]:
           # Integrity checks: orphaned records, status consistency, payload schema
           stmt = select(
               func.count(OfflineCacheMutation.id).label('total'),
               func.count(OfflineCacheMutation.id).filter(OfflineCacheMutation.status == MutationStatus.PENDENTE).label('pending'),
               func.count(OfflineCacheMutation.id).filter(OfflineCacheMutation.status == MutationStatus.ENVIADO).label('sent'),
               func.count(OfflineCacheMutation.id).filter(OfflineCacheMutation.status == MutationStatus.CONFLITO).label('conflict'),
               func.count(OfflineCacheMutation.id).filter(OfflineCacheMutation.payload.is_(None)).label('invalid_payload'),
               func.count(OfflineCacheMutation.id).filter(OfflineCacheMutation.patient_cns.is_(None) & OfflineCacheMutation.patient_cpf.is_(None)).label('missing_patient_id')
           )
           result = await self.session.execute(stmt)
           row = result.one()
           return {
               "total": row.total,
               "pending": row.pending,
               "sent": row.sent,
               "conflict": row.conflict,
               "invalid_payload": row.invalid_payload,
               "missing_patient_id": row.missing_patient_id,
               "integrity_ok": row.invalid_payload == 0 and row.missing_patient_id == 0
           }
   ```
   Wait, `func.count(...).filter(...)` syntax in SQLAlchemy 2.0 is `func.count(OfflineCacheMutation.id).filter(OfflineCacheMutation.status == ...)`. Actually, it's `func.count(OfflineCacheMutation.id).filter(OfflineCacheMutation.status == MutationStatus.PENDENTE)`. That's correct.
   Also, `payload.is_(None)` might not work as expected for JSON. I'll use `OfflineCacheMutation.payload == {}` or just skip that check. I'll simplify integrity report to focus on status and required fields.

   Let's refine the integrity report to be more robust and SQLAlchemy 2.0 compliant:
   ```python
   async def get_integrity_report(self) -> Dict[str, Any]:
       stmt = select(
           func.count(OfflineCacheMutation.id).label('total'),
           func.count(OfflineCacheMutation.id).filter(OfflineCacheMutation.status == MutationStatus.PENDENTE).label('pending'),
           func.count(OfflineCacheMutation.id).filter(OfflineCacheMutation.status == MutationStatus.ENVIADO).label('sent'),
           func.count(OfflineCacheMutation.id).filter(OfflineCacheMutation.status == MutationStatus.CONFLITO).label('conflict'),
           func.count(OfflineCacheMutation.id).filter(OfflineCacheMutation.payload == {}).label('empty_payload'),
           func.count(OfflineCacheMutation.id).filter(
               (OfflineCacheMutation.patient_cns == None) & (OfflineCacheMutation.patient_cpf == None)
           ).label('missing_patient_id')
       )
       result = await self.session.execute(stmt)
       row = result.one()
       return {
           "total": row.total,
           "pending": row.pending,
           "sent": row.sent,
           "conflict": row.conflict,
           "empty_payload": row.empty_payload,
           "missing_patient_id": row.missing_patient_id,
           "integrity_ok": row.empty_payload == 0 and row.missing_patient_id == 0
       }
   ```
   Actually, `payload == {}` might not index well. I'll just check `payload IS NULL` or skip. I'll keep it simple.

   Now, I need to ensure strict typing and Python 3.12 compatibility. I'll add `from __future__ import annotations` and use `typing` properly.

   Let's also add a method to clear synced mutations for cleanup (common in outbox patterns).
   ```python
   async def clear_synced_mutations(self, before_date: datetime) -> int:
       stmt = delete(OfflineCacheMutation).where(
           OfflineCacheMutation.status == MutationStatus.ENVIADO,
           OfflineCacheMutation.synced_at < before_date
       )
       result = await self.session.execute(stmt)
       await self.session.flush()
       return result.rowcount
   ```

   Now, the Pydantic schema needs to handle the `from_attributes` correctly. I'll use `model_validate` properly.

   Let's assemble the full repository file.

   *Self-Correction/Refinement during thought:*
   - SQLAlchemy 2.0 `func.now()` vs `datetime.utcnow