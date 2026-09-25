Here's a thinking process:

1.  **Understand User Goal:** The user wants me to create a specific file for a project called "MedIA": `backend/app/repositories/offline_cache_repo.py`. This file should manage a local queue of pending mutations (outbox pattern), synchronization status (PENDENTE, ENVIADO, CONFLITO), and ensure integrity using SQLAlchemy 2.0.

2.  **Analyze Constraints & Guidelines:**
   - **Project Context:** MedIA - private care & insurance (TISS ANS 4.01 / DMED Receita Federal), Primary Care / Family Health clinical method.
   - **Exclusions:** Do NOT generate code for mandatory SUS/SISAB submission or IoT peripherals.
   - **Tech Stack:** Python 3.12, strict typing with Pydantic v2, SQLAlchemy 2.0.
   - **Directory Structure:** Production code only in `backend/app/`, tests only in `backend/tests/`.
   - **Testing:** Preserve 100% of the test suite (green). I need to ensure the code is well-structured and testable, but I won't generate tests unless necessary, though I should keep the API clean for testing.
   - **Output Format:** Provide complete, executable code. Specify the file path at the top of each code block.

3.  **Key Requirements for `offline_cache_repo.py`:**
   - Outbox pattern implementation for local mutations.
   - Status management: `PENDENTE`, `ENVIADO`, `CONFLITO`.
   - SQLAlchemy 2.0 models & queries.
   - Pydantic v2 for data validation/serialization.
   - Strict typing (Python 3.12).
   - Integrity handling (transactions, conflict resolution).
   - Context: Healthcare data (needs to be robust, but I'll keep it generic enough to fit the outbox pattern).

4.  **Design the Solution:**
   - **Database Model:** `OfflineCacheMutation` table with fields: `id`, `entity_type`, `entity_id`, `mutation_type` (CREATE, UPDATE, DELETE), `payload` (JSON), `status` (enum), `created_at`, `updated_at`, `error_message`, `retry_count`.
   - **Pydantic Models:** `MutationPayload`, `MutationStatus`, `OfflineCacheMutationCreate`, `OfflineCacheMutationResponse`.
   - **Repository Class:** `OfflineCacheRepository` with methods:
     - `enqueue_mutation`: Add to local queue with status `PENDENTE`.
     - `get_pending_mutations`: Fetch mutations to sync.
     - `mark_as_sent`: Update status to `ENVIADO` (or delete after successful sync).
     - `mark_as_conflict`: Update status to `CONFLITO` with error details.
     - `retry_conflicts`: Get conflicts for retry.
     - `purge_sent`: Clean up old sent mutations.
   - **Integrity:** Use SQLAlchemy sessions, explicit transactions, optimistic locking or retry logic.
   - **Status Enum:** `MutationStatus` with `PENDENTE`, `ENVIADO`, `CONFLITO`.

5.  **Draft the Code (Mental Refinement):**
   I'll structure it carefully with SQLAlchemy 2.0 declarative base, Pydantic v2 models, and type hints.

   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations
   import json
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, Sequence
   from uuid import UUID, uuid4

   from pydantic import BaseModel, Field, ConfigDict
   from sqlalchemy import String, Text, DateTime, Integer, Enum as SAEnum, func
   from sqlalchemy.orm import Mapped, mapped_column, Session, DeclarativeBase
   from sqlalchemy import select

   # ... define base, models, enums, repository ...
   ```

   Let's flesh out the details:
   - `MutationStatus` enum (Pydantic + SQLAlchemy compatible). I'll use `str` enum for DB compatibility.
   - `OfflineCacheMutation` model: `id` (UUID), `entity_type` (str), `entity_id` (str), `mutation_type` (str), `payload` (JSON/Text), `status` (str), `retry_count` (int), `error_message` (Optional[str]), `created_at`, `updated_at`.
   - Repository methods will take a `Session` as argument (standard for repositories in SQLAlchemy 2.0).
   - I'll add explicit transaction handling comments and use `session.commit()` appropriately.
   - Pydantic models for input/output validation.

   Wait, the prompt says "status de sincronização (PENDENTE, ENVIADO, CONFLITO)". I'll map these exactly.
   I need to ensure it's production-ready, clean, and strictly typed.

   Let's write it out carefully.

   Structure:
   - Imports
   - Enums
   - Pydantic Models
   - SQLAlchemy Model
   - Repository Class
   - Type aliases if needed

   Key considerations for SQLAlchemy 2.0:
   - Use `DeclarativeBase`
   - Use `mapped_column`
   - Use `select` instead of `session.query`
   - Use `session.execute`
   - Explicit type hints for `Mapped`

   Let's draft:

   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations

   import json
   from datetime import datetime, timezone
   from enum import Enum as PydanticEnum
   from typing import Optional, Sequence
   from uuid import UUID, uuid4

   from pydantic import BaseModel, Field, ConfigDict
   from sqlalchemy import String, Text, DateTime, Integer, func
   from sqlalchemy.orm import Mapped, mapped_column, Session, DeclarativeBase
   from sqlalchemy import select

   # ...
   ```

   I'll define the Pydantic enum carefully to match SQLAlchemy's string enum behavior. Actually, SQLAlchemy 2.0 supports `Enum` from `sqlalchemy` but it's better to use `str` and validate with Pydantic, or use `sqlalchemy.Enum` with `native_enum=False` for cross-DB compatibility. I'll stick to `String` for status to avoid DB enum migration headaches, and validate via Pydantic.

   Let's refine the model:
   ```python
   class MutationStatus(str, PydanticEnum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class OfflineCacheMutationBase(BaseModel):
       entity_type: str = Field(..., min_length=1, max_length=64)
       entity_id: str = Field(..., min_length=1, max_length=64)
       mutation_type: str = Field(..., pattern="^(CREATE|UPDATE|DELETE)$")
       payload: dict = Field(..., description="JSON serializable payload")
       status: MutationStatus = MutationStatus.PENDENTE
       retry_count: int = Field(default=0, ge=0)
       error_message: Optional[str] = None

   class OfflineCacheMutationCreate(OfflineCacheMutationBase):
       pass

   class OfflineCacheMutationResponse(OfflineCacheMutationBase):
       id: UUID
       created_at: datetime
       updated_at: datetime
       model_config = ConfigDict(from_attributes=True)
   ```

   SQLAlchemy Model:
   ```python
   class Base(DeclarativeBase):
       pass

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutations"

       id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
       entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
       entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
       mutation_type: Mapped[str] = mapped_column(String(16), nullable=False)
       payload: Mapped[str] = mapped_column(Text, nullable=False)
       status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDENTE")
       retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
       error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
   ```

   Repository:
   ```python
   class OfflineCacheRepository:
       def __init__(self, session: Session) -> None:
           self.session = session

       def enqueue_mutation(self, payload: OfflineCacheMutationCreate) -> OfflineCacheMutationResponse:
           mutation = OfflineCacheMutation(
               id=uuid4(),
               entity_type=payload.entity_type,
               entity_id=payload.entity_id,
               mutation_type=payload.mutation_type,
               payload=json.dumps(payload.payload),
               status=payload.status.value,
               retry_count=payload.retry_count,
               error_message=payload.error_message,
           )
           self.session.add(mutation)
           self.session.flush()
           return OfflineCacheMutationResponse.model_validate(mutation)

       def get_pending_mutations(self, limit: int = 100) -> Sequence[OfflineCacheMutationResponse]:
           stmt = select(OfflineCacheMutation).where(
               OfflineCacheMutation.status == "PENDENTE"
           ).order_by(OfflineCacheMutation.created_at.asc()).limit(limit)
           result = self.session.execute(stmt)
           return [OfflineCacheMutationResponse.model_validate(m) for m in result.scalars().all()]

       def mark_as_sent(self, mutation_id: UUID) -> bool:
           stmt = select(OfflineCacheMutation).where(OfflineCacheMutation.id == mutation_id)
           mutation = self.session.execute(stmt).scalar_one_or_none()
           if not mutation:
               return False
           mutation.status = "ENVIADO"
           mutation.updated_at = datetime.now(timezone.utc)
           self.session.flush()
           return True

       def mark_as_conflict(self, mutation_id: UUID, error_message: str) -> OfflineCacheMutationResponse:
           stmt = select(OfflineCacheMutation).where(OfflineCacheMutation.id == mutation_id)
           mutation = self.session.execute(stmt).scalar_one_or_none()
           if not mutation:
               raise ValueError(f"Mutação {mutation_id} não encontrada.")
           mutation.status = "CONFLITO"
           mutation.error_message = error_message
           mutation.retry_count += 1
           mutation.updated_at = datetime.now(timezone.utc)
           self.session.flush()
           return OfflineCacheMutationResponse.model_validate(mutation)

       def get_conflict_mutations(self, limit: int = 50) -> Sequence[OfflineCacheMutationResponse]:
           stmt = select(OfflineCacheMutation).where(
               OfflineCacheMutation.status == "CONFLITO"
           ).order_by(OfflineCacheMutation.retry_count.desc()).limit(limit)
           result = self.session.execute(stmt)
           return [OfflineCacheMutationResponse.model_validate(m) for m in result.scalars().all()]

       def purge_sent_mutations(self, older_than: datetime) -> int:
           stmt = select(OfflineCacheMutation).where(
               OfflineCacheMutation.status == "ENVIADO",
               OfflineCacheMutation.updated_at < older_than
           )
           mutations = self.session.execute(stmt).scalars().all()
           for m in mutations:
               self.session.delete(m)
           self.session.flush()
           return len(mutations)
   ```

   Wait, I need to ensure strict typing and Pydantic v2 compatibility. `from_attributes=True` is correct for Pydantic v2. I should also add proper docstrings and type hints. The `datetime.now(timezone.utc)` lambda is fine, but SQLAlchemy 2.0 recommends `func.now()` or `server_default`. I'll use `server_default=func.now()` for better DB consistency, but keep `default` for Python-side fallback. Actually, `default=datetime.now(timezone.utc)` is fine for ORM-level.

   Let's adjust the model to be more robust:
   - Use `sqlalchemy.Enum`? The prompt says "status de sincronização (PENDENTE, ENVIADO, CONFLITO)". I'll stick to `String` for simplicity and cross-DB compatibility, but I'll add a check in Pydantic.
   - I'll add a method to commit the transaction explicitly or rely on the caller. Usually, repositories don't commit, they just flush. I'll keep `flush()` and let the caller commit.
   - I should ensure the code is complete and executable. I'll add a `__all__` and proper structure.

   Let's refine the repository to be more production-ready:
   - Add `sync_pending_mutations` as a batch operation? The prompt says "gerencia fila local de mutações pendentes (outbox pattern)". I'll keep individual methods but add a batch sync helper if needed. Actually, the outbox pattern usually involves a worker that picks up pending items, processes them, and updates status. I'll provide the core CRUD/status methods as requested.
   - I'll add explicit transaction boundaries comments.
   - I'll ensure Pydantic v2 uses `model_config = ConfigDict(from_attributes=True)`.
   - I'll add type hints for all methods.

   One thing: `mutation_type` should probably be an enum too, but I'll keep it as string for simplicity, or define `MutationType` enum. I'll stick to string with pattern validation.

   Let's write out the full file carefully.

   Structure:
   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   """
   Repositório de Cache Offline para o padrão Outbox.
   Gerencia fila local de mutações pendentes, status de sincronização e integridade.
   """
   from __future__ import annotations

   import json
   from datetime import datetime, timezone
   from enum import Enum as PydanticEnum
   from typing import Optional, Sequence
   from uuid import UUID, uuid4

   from pydantic import BaseModel, ConfigDict, Field, field_validator
   from sqlalchemy import String, Text, DateTime, Integer, func, select
   from sqlalchemy.orm import Mapped, mapped_column, Session, DeclarativeBase

   # ... (enums, models, base, repository) ...
   ```

   I'll add a `MutationType` enum for better typing.
   I'll ensure all Pydantic models use `model_config = ConfigDict(from_attributes=True)`.
   I'll add proper error handling and type hints.
   I'll make sure it's strictly Python 3.12 compatible.

   Let's draft it completely.

   *Self-Correction/Verification during drafting:*
   - `sqlalchemy.Enum` can cause issues across databases. I'll use `String` and validate via Pydantic.
   - `datetime.now(timezone.utc)` in `default` is evaluated at import time in some SQLAlchemy versions. Better to use `default=lambda: datetime.now(timezone.utc)` or `server_default=func.now()`. I'll use `server_default=func.now()` and `default=datetime.now(timezone.utc)`.
   - Pydantic v2 `from_attributes` is correct.
   - I should ensure the repository methods don't commit automatically to allow transactional control by the caller (standard practice).
   - I'll add a `sync_batch` method that demonstrates the outbox pattern workflow (fetch pending -> process -> update status).
   - I'll make sure the code is self-contained and ready for import.

   Let's write it out carefully. 
   I'll structure it logically:
   1. Imports & Constants
   2. Pydantic Models (Enums, DTOs)
   3. SQLAlchemy Model
   4. Repository Class
   5. Type hints & docstrings throughout.

   All constraints met: Python 3.12, Pydantic v2, SQLAlchemy 2.0, strict typing, outbox pattern, status management, integrity handling, healthcare context noted but not over-engineered (no SUS/IoT).

   Code generation starts now. 
   I will double-check SQLAlchemy 2.0 syntax: `select(Model).where(...)`, `session.execute(stmt).scalars().all()`, `mapped_column`, `DeclarativeBase`. All correct.
   Pydantic v2: `ConfigDict(from_attributes=True)`, `field_validator`, `model_validate`. All correct.
   Type hints: `Sequence`, `Optional`, `UUID`, `datetime`. All correct.
   I'll add a `__all__` export list.
   I'll ensure the file path comment is at the top.
   Ready.✅
   Output matches the response. 
   Proceeds. 
   [Output Generation] -> *See response.* 
   Self-Correction/Refinement during thought: 
   - I should make sure the `payload` field in Pydantic is validated as a dict, and in SQLAlchemy it's stored as JSON string. I'll handle serialization/deserialization in the repository or use a custom type. For simplicity and strictness, I'll keep it as `dict` in Pydantic and `str` (JSON) in SQLAlchemy, converting in the repo methods.
   - I'll add a `field_validator` for `payload` to ensure it's serializable.
   - I'll ensure the repository methods are async-compatible? The prompt doesn't specify async, so sync is fine. I'll stick to sync for simplicity and strict SQLAlchemy 2.0 ORM usage.
   - I'll add explicit transaction management comments.
   - All good.
   Output matches the final code. 
   Proceeds. 
   [Done.] 
   *Output Generation* (matches the final response)
   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   ...
   ```
   All constraints verified. Ready. 
   *Self-Correction/Note during generation prep*: 
   I need to make sure the Pydantic model uses `model_config = ConfigDict(from_attributes=True)` correctly. In Pydantic v2, it's `model_config = ConfigDict(from_attributes=True)`. Correct.
   I'll add a `sync_pending_mutations` method that demonstrates the outbox pattern workflow (fetch, process, update status) to fully satisfy "gerencia fila local de mutações pendentes (outbox pattern)".
   I'll ensure strict typing everywhere