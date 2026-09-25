Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/offline_cache_repo.py` for a project called "MedIA".
   - **Core Functionality:** Manage a local queue of pending mutations (outbox pattern), synchronization status (PENDENTE, ENVIADO, CONFLITO), and integrity using SQLAlchemy 2.0.
   - **Architecture Guidelines:**
     - MedIA is for private care and insurance (TISS ANS 4.01 / DMED Receita Federal), focusing on Primary Care / Family Health clinical methods.
     - Do NOT generate code for mandatory SUS/SISAB or IoT peripheral sending.
     - Clean Python 3.12 code, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - Production code strictly in `backend/app/`, tests strictly in `backend/tests/`.
     - Preserve 100% of the test suite (green).
   - **Output Requirement:** Provide complete, executable code. Specify file paths at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/offline_cache_repo.py`
   - **Pattern:** Outbox pattern for offline cache synchronization.
   - **Statuses:** `PENDENTE`, `ENVIADO`, `CONFLITO`
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0
   - **Domain Context:** MedIA (Primary Care/Family Health), but the repo itself is generic for offline mutations. I should keep it focused on the cache/mutation management, not domain-specific medical logic, but maybe add comments/context if needed.
   - **Integrity:** Need to ensure data integrity (transactions, constraints, maybe checksums or versioning).
   - **Testing:** The prompt says "Preservar 100% da suíte de testes verde." This implies I should either provide tests or ensure the code is testable and follows patterns that won't break existing tests. Since I'm generating the file, I'll also provide a corresponding test file to ensure it's green, or at least structure it so it's ready for testing. I'll create a test file as well to be safe, but the prompt specifically asks for `backend/app/repositories/offline_cache_repo.py`. I'll focus on that, but I'll make sure it's robust.

3.  **Design the Repository (`offline_cache_repo.py`):**
   - **Models:** Need a SQLAlchemy model for the outbox/cache entries.
     - Fields: `id`, `entity_type`, `entity_id`, `mutation_type` (CREATE, UPDATE, DELETE), `payload` (JSON), `status` (enum), `created_at`, `updated_at`, `sync_error` (optional), `version` (for integrity/conflict resolution).
     - Status Enum: `PENDENTE`, `ENVIADO`, `CONFLITO`
   - **Pydantic Schemas:** For validation of mutations/payloads.
   - **Repository Class:** Methods to:
     - `enqueue_mutation(entity_type, entity_id, mutation_type, payload)`
     - `get_pending_mutations(limit)`
     - `mark_as_sent(mutation_id)`
     - `mark_as_conflict(mutation_id, error_msg)`
     - `get_by_id(mutation_id)`
     - `purge_sent(limit)`
     - Use SQLAlchemy 2.0 async or sync? I'll use sync for simplicity unless specified, but async is common in modern FastAPI. I'll stick to sync SQLAlchemy 2.0 for broader compatibility, but I'll make it easily adaptable. Actually, I'll use `Session` from `sqlalchemy.orm`.
   - **Integrity:** Use database constraints (unique on entity_type+entity_id+mutation_type+version?), or application-level versioning. I'll add a `version` field and use optimistic locking or just track it. For integrity, I'll ensure transactions are used and add a `checksum` field for payload integrity.
   - **Typing:** Strict Python 3.12 type hints.
   - **Pydantic v2:** Use `BaseModel`, `ConfigDict`, `Field`, `Enum` (or `str` with `Literal`), `model_validator` if needed.

   Let's draft the structure:
   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations
   import json
   from datetime import datetime
   from enum import Enum
   from typing import Optional, Sequence
   from uuid import uuid4

   from pydantic import BaseModel, Field, ConfigDict, field_validator
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
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship

   # ... Define models, enums, schemas, repository class ...
   ```

   Wait, SQLAlchemy 2.0 uses `Mapped` and `mapped_column` for declarative base. I'll use the modern style.
   Let's define the status enum:
   ```python
   class MutationStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"
   ```

   Model:
   ```python
   class Base(DeclarativeBase):
       pass

   class OfflineCacheEntry(Base):
       __tablename__ = "offline_cache_entries"

       id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
       entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
       entity_id: Mapped[str] = mapped_column(String(50), nullable=False)
       mutation_type: Mapped[str] = mapped_column(String(10), nullable=False) # CREATE, UPDATE, DELETE
       payload: Mapped[dict] = mapped_column(JSON, nullable=False)
       status: Mapped[MutationStatus] = mapped_column(SAEnum(MutationStatus), default=MutationStatus.PENDENTE, nullable=False)
       version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
       checksum: Mapped[str] = mapped_column(String(64), nullable=False)
       created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
       updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
       sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

       __table_args__ = (
           # Integrity constraint: prevent duplicate mutations for same entity/version
           # Actually, outbox usually allows retries, so maybe unique on (entity_type, entity_id, mutation_type, version) is too strict.
           # Better: unique constraint on (entity_type, entity_id) for the latest version, or just rely on application logic.
           # I'll add a unique index on (entity_type, entity_id, mutation_type) to prevent duplicates, but allow version increments.
           # Actually, outbox pattern typically doesn't need strict unique constraints on entity_id because mutations are sequential.
           # I'll skip complex constraints and rely on DB transactions and app logic for integrity.
       )
   ```
   Actually, for integrity, I'll compute a SHA-256 checksum of the payload and store it. I'll also add a `sequence_number` for ordering.

   Let's refine the model with SQLAlchemy 2.0 style:
   ```python
   from sqlalchemy import String, Integer, Text, DateTime, JSON, Enum, func, UniqueConstraint
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, Session
   from datetime import datetime
   from uuid import uuid4
   import hashlib
   from enum import Enum as PyEnum

   class MutationStatus(str, PyEnum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class Base(DeclarativeBase):
       pass

   class OfflineCacheEntry(Base):
       __tablename__ = "offline_cache_entries"

       id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
       entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
       entity_id: Mapped[str] = mapped_column(String(50), nullable=False)
       mutation_type: Mapped[str] = mapped_column(String(10), nullable=False)
       payload: Mapped[dict] = mapped_column(JSON, nullable=False)
       status: Mapped[MutationStatus] = mapped_column(Enum(MutationStatus), default=MutationStatus.PENDENTE, nullable=False)
       version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
       checksum: Mapped[str] = mapped_column(String(64), nullable=False)
       sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=lambda: 0) # Will be set by repo
       created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
       updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
       sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)

       __table_args__ = (
           UniqueConstraint("entity_type", "entity_id", "mutation_type", name="uq_entity_mutation"),
       )
   ```
   Wait, `UniqueConstraint` on entity_type, entity_id, mutation_type might block retries. Outbox pattern usually allows the same mutation to be retried until success. I'll remove the unique constraint and rely on `id` as primary key. Integrity will be handled via checksum and versioning.

   Let's adjust:
   ```python
   class OfflineCacheEntry(Base):
       __tablename__ = "offline_cache_entries"
       # ... fields ...
   ```

   Pydantic Schemas:
   ```python
   class MutationPayloadSchema(BaseModel):
       model_config = ConfigDict(extra="forbid")
       entity_type: str = Field(..., min_length=1, max_length=50)
       entity_id: str = Field(..., min_length=1, max_length=50)
       mutation_type: str = Field(..., pattern="^(CREATE|UPDATE|DELETE)$")
       payload: dict = Field(..., min_size=1)

       @field_validator("payload")
       @classmethod
       def validate_payload(cls, v: dict) -> dict:
           # Basic integrity check: ensure payload is JSON serializable
           import json
           try:
               json.dumps(v)
           except (TypeError, ValueError) as e:
               raise ValueError(f"Payload must be JSON serializable: {e}")
           return v
   ```

   Repository Class:
   ```python
   class OfflineCacheRepository:
       def __init__(self, session: Session):
           self.session = session

       def enqueue_mutation(self, entity_type: str, entity_id: str, mutation_type: str, payload: dict) -> OfflineCacheEntry:
           # Validate
           # Compute checksum
           # Create entry
           # Commit
           pass

       def get_pending_mutations(self, limit: int = 100) -> Sequence[OfflineCacheEntry]:
           pass

       def mark_as_sent(self, mutation_id: str) -> bool:
           pass

       def mark_as_conflict(self, mutation_id: str, error_msg: str) -> bool:
           pass

       def get_by_id(self, mutation_id: str) -> OfflineCacheEntry | None:
           pass

       def purge_sent_mutations(self, older_than_days: int = 30) -> int:
           pass
   ```

   I need to implement these methods carefully with SQLAlchemy 2.0 syntax.
   Checksum: `hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()`
   Sequence: Use a DB sequence or just `func.now()` + random, or rely on `created_at` for ordering. I'll use `created_at` for ordering pending mutations.

   Let's write it out carefully.

   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations

   import hashlib
   import json
   from datetime import datetime, timedelta
   from enum import Enum
   from typing import Optional, Sequence

   from pydantic import BaseModel, ConfigDict, Field, field_validator
   from sqlalchemy import (
       String,
       Integer,
       Text,
       DateTime,
       JSON,
       Enum as SAEnum,
       func,
       select,
       update,
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

   class MutationStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class Base(DeclarativeBase):
       pass

   class OfflineCacheEntry(Base):
       __tablename__ = "offline_cache_entries"

       id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
       entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
       entity_id: Mapped[str] = mapped_column(String(50), nullable=False)
       mutation_type: Mapped[str] = mapped_column(String(10), nullable=False)
       payload: Mapped[dict] = mapped_column(JSON, nullable=False)
       status: Mapped[MutationStatus] = mapped_column(SAEnum(MutationStatus), default=MutationStatus.PENDENTE, nullable=False)
       version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
       checksum: Mapped[str] = mapped_column(String(64), nullable=False)
       created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
       updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
       sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)

   # ... Pydantic schemas ...
   # ... Repository ...
   ```

   Wait, `uuid4` needs import. I'll add it.
   Also, SQLAlchemy 2.0 `mapped_column` requires `from sqlalchemy.orm import mapped_column`.
   I need to be careful with `Enum` import conflict. I'll use `Enum as PyEnum` or just `enum.Enum`.

   Let's refine the repository implementation:

   ```python
   class OfflineCacheRepository:
       def __init__(self, session: Session) -> None:
           self.session = session

       def _compute_checksum(self, payload: dict) -> str:
           return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()

       def enqueue_mutation(self, entity_type: str, entity_id: str, mutation_type: str, payload: dict) -> OfflineCacheEntry:
           checksum = self._compute_checksum(payload)
           entry = OfflineCacheEntry(
               entity_type=entity_type,
               entity_id=entity_id,
               mutation_type=mutation_type,
               payload=payload,
               status=MutationStatus.PENDENTE,
               version=1,
               checksum=checksum,
           )
           self.session.add(entry)
           self.session.flush()
           return entry

       def get_pending_mutations(self, limit: int = 100) -> Sequence[OfflineCacheEntry]:
           stmt = (
               select(OfflineCacheEntry)
               .where(OfflineCacheEntry.status == MutationStatus.PENDENTE)
               .order_by(OfflineCacheEntry.created_at.asc())
               .limit(limit)
           )
           return self.session.scalars(stmt).all()

       def mark_as_sent(self, mutation_id: str) -> bool:
           stmt = (
               update(OfflineCacheEntry)
               .where(OfflineCacheEntry.id == mutation_id)
               .values(status=MutationStatus.ENVIADO, updated_at=func.now())
           )
           result = self.session.execute(stmt)
           self.session.flush()
           return result.rowcount > 0

       def mark_as_conflict(self, mutation_id: str, error_msg: str) -> bool:
           stmt = (
               update(OfflineCacheEntry)
               .where(OfflineCacheEntry.id == mutation_id)
               .values(
                   status=MutationStatus.CONFLITO,
                   sync_error=error_msg,
                   version=OfflineCacheEntry.version + 1,
                   updated_at=func.now(),
               )
           )
           result = self.session.execute(stmt)
           self.session.flush()
           return result.rowcount > 0

       def get_by_id(self, mutation_id: str) -> OfflineCacheEntry | None:
           return self.session.get(OfflineCacheEntry, mutation_id)

       def purge_sent_mutations(self, older_than_days: int = 30) -> int:
           cutoff = datetime.now() - timedelta(days=older_than_days)
           stmt = select(OfflineCacheEntry).where(
               OfflineCacheEntry.status == MutationStatus.ENVIADO,
               OfflineCacheEntry.updated_at < cutoff
           )
           entries = self.session.scalars(stmt).all()
           for entry in entries:
               self.session.delete(entry)
           self.session.flush()
           return len(entries)
   ```

   This looks solid. I need to add Pydantic validation schemas as requested ("tipagem estrita Pydantic v2"). I'll add them to the same file or import them. I'll keep them in the same file for completeness.

   Let's add the Pydantic models:
   ```python
   class MutationPayloadSchema(BaseModel):
       model_config = ConfigDict(extra="forbid")
       entity_type: str = Field(..., min_length=1, max_length=50)
       entity_id: str = Field(..., min_length=1, max_length=50)
       mutation_type: str = Field(..., pattern="^(CREATE|UPDATE|DELETE)$")
       payload: