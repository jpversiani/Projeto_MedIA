Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/offline_cache_repo.py` for a project called "MedIA".
   - **Functionality:** Manage a local queue of pending mutations (outbox pattern), synchronization status (PENDENTE, ENVIADO, CONFLITO), and integrity with SQLAlchemy 2.0.
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Full compliance and coverage with automated tests using pytest.
   - **Output Requirement:** Provide complete, executable code. Specify file paths at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/offline_cache_repo.py`
   - **Core Features:**
     - Outbox pattern implementation for offline cache.
     - Status management: PENDENTE, ENVIADO, CONFLITO.
     - SQLAlchemy 2.0 models & queries.
     - Pydantic v2 for data validation/serialization.
     - Integration with SUS/APS standards (CIAP-2, CID-10, SOAP, CNS/CPF).
     - Type hints (Python 3.12).
     - Pytest coverage (I need to provide the test file as well, or at least ensure the code is testable and mention/test coverage).
   - **Architecture/Standards:**
     - Need to define models for mutations/cache.
     - Need enums for status.
     - Need Pydantic schemas.
     - Need repository class with methods for CRUD, sync status updates, conflict handling.
     - Must align with SUS/APS data structures (e.g., patient CNS/CPF, diagnosis CID-10/CIAP-2, SOAP notes).

3.  **Design the Solution:**
   - **Models (SQLAlchemy 2.0):**
     - `OfflineCacheMutation`: Represents a pending mutation.
       - `id`: UUID
       - `entity_type`: str (e.g., 'patient', 'consultation', 'diagnosis')
       - `entity_id`: str
       - `payload`: JSON (Pydantic model serialized)
       - `status`: Enum (PENDENTE, ENVIADO, CONFLITO)
       - `created_at`, `updated_at`: datetime
       - `sync_error`: str (optional)
       - `priority`: int (for queue ordering)
     - `SyncLog`: (Optional but good for integrity) tracks sync attempts.
   - **Enums:**
     - `MutationStatus`: PENDENTE, ENVIADO, CONFLITO
   - **Pydantic Schemas:**
     - `OfflineCacheMutationCreate`
     - `OfflineCacheMutationRead`
     - `SyncStatusUpdate`
   - **Repository Class:**
     - `OfflineCacheRepository`
     - Methods:
       - `add_mutation(entity_type, entity_id, payload, priority=0)`
       - `get_pending_mutations(limit=100)`
       - `mark_as_sent(mutation_id)`
       - `mark_as_conflict(mutation_id, error_msg)`
       - `get_mutation_by_id(mutation_id)`
       - `clear_sent_mutations()`
       - `get_sync_status_summary()`
     - Use SQLAlchemy 2.0 async or sync? The prompt says SQLAlchemy 2.0, doesn't specify async. I'll use sync for simplicity but ensure it's compatible with modern practices. I'll stick to sync `Session` but note it can be adapted. Actually, I'll use `async` as it's common in modern FastAPI backends, but I'll make it sync for broader compatibility unless specified. I'll stick to sync `Session` for clarity, but use SQLAlchemy 2.0 syntax (`select`, `insert`, etc.).
   - **SUS/APS Integration:**
     - The payload should support CNS/CPF, CID-10, CIAP-2, SOAP.
     - I'll define Pydantic models for these standards to validate the payload.
     - `PatientInfo`: cns (str), cpf (str)
     - `Diagnosis`: cid10 (str), ciap2 (str)
     - `SOAPNote`: subjective, objective, assessment, plan
     - The mutation payload will be a union or dict, but I'll enforce structure via Pydantic.

4.  **Draft the Code (Mental Refinement):**
   Let's structure the file properly.

   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations
   import json
   from datetime import datetime
   from enum import Enum
   from typing import Any, Optional
   from uuid import UUID, uuid4

   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import (
       Column,
       DateTime,
       Enum as SAEnum,
       ForeignKey,
       Integer,
       JSON,
       String,
       Text,
       select,
       update,
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship

   # --- Enums & Pydantic Models (SUS/APS Standards) ---
   class MutationStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class PatientInfo(BaseModel):
       cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")

   class Diagnosis(BaseModel):
       cid10: Optional[str] = Field(None, pattern=r"^[A-Z]\d{2}(\.\d{1,2})?$")
       ciap2: Optional[str] = Field(None, pattern=r"^[A-Z]\d{2}(\.\d{1,2})?$")

   class SOAPNote(BaseModel):
       subjective: str
       objective: str
       assessment: str
       plan: str

   class OfflineCachePayload(BaseModel):
       patient: PatientInfo
       diagnoses: list[Diagnosis] = []
       soap: Optional[SOAPNote] = None
       metadata: dict[str, Any] = {}

       @field_validator("patient")
       @classmethod
       def validate_patient(cls, v):
           if not v.cns and not v.cpf:
               raise ValueError("Paciente deve informar CNS ou CPF")
           return v

   # --- SQLAlchemy 2.0 Models ---
   class Base(DeclarativeBase):
       pass

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutations"

       id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
       entity_type: Mapped[str] = mapped_column(String(50))
       entity_id: Mapped[str] = mapped_column(String(100))
       payload: Mapped[dict] = mapped_column(JSON)
       status: Mapped[MutationStatus] = mapped_column(SAEnum(MutationStatus), default=MutationStatus.PENDENTE)
       priority: Mapped[int] = mapped_column(Integer, default=0)
       sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

   # --- Repository ---
   class OfflineCacheRepository:
       def __init__(self, session: Session):
           self.session = session

       def add_mutation(self, entity_type: str, entity_id: str, payload: OfflineCachePayload, priority: int = 0) -> OfflineCacheMutation:
           mutation = OfflineCacheMutation(
               entity_type=entity_type,
               entity_id=entity_id,
               payload=payload.model_dump(),
               priority=priority,
           )
           self.session.add(mutation)
           self.session.flush()
           return mutation

       def get_pending_mutations(self, limit: int = 100) -> list[OfflineCacheMutation]:
           stmt = (
               select(OfflineCacheMutation)
               .where(OfflineCacheMutation.status == MutationStatus.PENDENTE)
               .order_by(OfflineCacheMutation.priority.desc(), OfflineCacheMutation.created_at.asc())
               .limit(limit)
           )
           return list(self.session.scalars(stmt).all())

       def mark_as_sent(self, mutation_id: UUID) -> bool:
           stmt = (
               update(OfflineCacheMutation)
               .where(OfflineCacheMutation.id == mutation_id)
               .values(status=MutationStatus.ENVIADO, updated_at=datetime.utcnow())
           )
           result = self.session.execute(stmt)
           self.session.commit()
           return result.rowcount > 0

       def mark_as_conflict(self, mutation_id: UUID, error_msg: str) -> bool:
           stmt = (
               update(OfflineCacheMutation)
               .where(OfflineCacheMutation.id == mutation_id)
               .values(status=MutationStatus.CONFLITO, sync_error=error_msg, updated_at=datetime.utcnow())
           )
           result = self.session.execute(stmt)
           self.session.commit()
           return result.rowcount > 0

       def get_mutation_by_id(self, mutation_id: UUID) -> Optional[OfflineCacheMutation]:
           return self.session.get(OfflineCacheMutation, mutation_id)

       def clear_sent_mutations(self, older_than_days: int = 7) -> int:
           cutoff = datetime.utcnow() - __import__("datetime").timedelta(days=older_than_days)
           stmt = select(OfflineCacheMutation).where(
               OfflineCacheMutation.status == MutationStatus.ENVIADO,
               OfflineCacheMutation.updated_at < cutoff
           )
           mutations = list(self.session.scalars(stmt).all())
           for m in mutations:
               self.session.delete(m)
           self.session.commit()
           return len(mutations)

       def get_sync_status_summary(self) -> dict[str, int]:
           stmt = select(OfflineCacheMutation.status, __import__("sqlalchemy").func.count(OfflineCacheMutation.id))
           stmt = stmt.group_by(OfflineCacheMutation.status)
           rows = self.session.execute(stmt).all()
           return {status: count for status, count in rows}
   ```

   Wait, I need to fix the `clear_sent_mutations` and `get_sync_status_summary` imports. I'll use proper imports at the top.
   Also, `datetime.utcnow()` is deprecated in Python 3.12. I should use `datetime.now(timezone.utc)` or `datetime.utcnow()` with a note, but better to use `datetime.now(timezone.utc)` and `timezone.utc`.
   Let's adjust imports and use modern datetime.

   Also, the prompt says "integração com SQLAlchemy 2.0" and "Pydantic v2". I'll ensure strict typing and modern syntax.
   I'll add a `SyncLog` model if needed, but the prompt focuses on the outbox queue. I'll stick to `OfflineCacheMutation`.
   I need to make sure the code is complete and executable. I'll add a `__main__` block or at least ensure it's ready for use.
   I should also provide the pytest file as requested: "Manter conformidade total e cobertura de testes automatizados com pytest." I'll create `tests/test_offline_cache_repo.py`.

   Let's refine the repository code carefully.

   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations

   import json
   from datetime import datetime, timedelta, timezone
   from enum import Enum
   from typing import Any, Optional
   from uuid import UUID, uuid4

   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import (
       DateTime,
       Enum as SAEnum,
       Integer,
       JSON,
       String,
       Text,
       func,
       select,
       update,
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

   # --- Enums & Pydantic Models (Padrões SUS/APS) ---
   class MutationStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class PatientInfo(BaseModel):
       cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")

       @field_validator("cns", "cpf")
       @classmethod
       def validate_not_both_none(cls, v):
           # Validation handled at class level
           return v

   class Diagnosis(BaseModel):
       cid10: Optional[str] = Field(None, pattern=r"^[A-Z]\d{2}(\.\d{1,2})?$")
       ciap2: Optional[str] = Field(None, pattern=r"^[A-Z]\d{2}(\.\d{1,2})?$")

   class SOAPNote(BaseModel):
       subjective: str
       objective: str
       assessment: str
       plan: str

   class OfflineCachePayload(BaseModel):
       patient: PatientInfo
       diagnoses: list[Diagnosis] = []
       soap: Optional[SOAPNote] = None
       metadata: dict[str, Any] = {}

       @field_validator("patient")
       @classmethod
       def validate_patient(cls, v):
           if not v.cns and not v.cpf:
               raise ValueError("Paciente deve informar CNS ou CPF")
           return v

   # --- SQLAlchemy 2.0 Models ---
   class Base(DeclarativeBase):
       pass

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutations"

       id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
       entity_type: Mapped[str] = mapped_column(String(50))
       entity_id: Mapped[str] = mapped_column(String(100))
       payload: Mapped[dict] = mapped_column(JSON)
       status: Mapped[MutationStatus] = mapped_column(SAEnum(MutationStatus), default=MutationStatus.PENDENTE)
       priority: Mapped[int] = mapped_column(Integer, default=0)
       sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
       updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

   # --- Repository ---
   class OfflineCacheRepository:
       def __init__(self, session: Session):
           self.session = session

       def add_mutation(self, entity_type: str, entity_id: str, payload: OfflineCachePayload, priority: int = 0) -> OfflineCacheMutation:
           mutation = OfflineCacheMutation(
               entity_type=entity_type,
               entity_id=entity_id,
               payload=payload.model_dump(),
               priority=priority,
           )
           self.session.add(mutation)
           self.session.flush()
           return mutation

       def get_pending_mutations(self, limit: int = 100) -> list[OfflineCacheMutation]:
           stmt = (
               select(OfflineCacheMutation)
               .where(OfflineCacheMutation.status == MutationStatus.PENDENTE)
               .order_by(OfflineCacheMutation.priority.desc(), OfflineCacheMutation.created_at.asc())
               .limit(limit)
           )
           return list(self.session.scalars(stmt).all())

       def mark_as_sent(self, mutation_id: UUID) -> bool:
           stmt = (
               update(OfflineCacheMutation)
               .where(OfflineCacheMutation.id == mutation_id)
               .values(status=MutationStatus.ENVIADO, updated_at=datetime.now(timezone.utc))
           )
           result = self.session.execute(stmt)
           self.session.commit()
           return result.rowcount > 0

       def mark_as_conflict(self, mutation_id: UUID, error_msg: str) -> bool:
           stmt = (
               update(OfflineCacheMutation)
               .where(OfflineCacheMutation.id == mutation_id)
               .values(status=MutationStatus.CONFLITO, sync_error=error_msg, updated_at=datetime.now(timezone.utc))
           )
           result = self.session.execute(stmt)
           self.session.commit()
           return result.rowcount > 0

       def get_mutation_by_id(self, mutation_id: UUID) -> Optional[OfflineCacheMutation]:
           return self.session.get(OfflineCacheMutation, mutation_id)

       def clear_sent_mutations(self, older_than_days: int = 7) -> int:
           cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
           stmt = select(OfflineCacheMutation).where(
               OfflineCacheMutation.status == MutationStatus.ENVIADO,
               OfflineCacheMutation.updated_at < cutoff
           )
           mutations = list(self.session.scalars(stmt).all())
           for m in mutations:
               self.session.delete(m)
           self.session.commit()
           return len(mutations)

       def get_sync_status_summary(self) -> dict[str, int]:
           stmt = select(OfflineCacheMutation.status, func.count(OfflineCacheMutation.id)).group_by(OfflineCacheMutation.status)
           rows = self.session.execute(stmt).all()
           return {status: count for status, count in rows}
   ```

   Now, I need to create the pytest file. The prompt says "Manter conformidade total e cobertura de testes automatizados com pytest." I'll provide a comprehensive test file.

   ```python
   # Arquivo: tests/test_offline_cache_repo.py
   import pytest
   from datetime import datetime, timezone
   from uuid import uuid4
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker

   from backend.app.repositories.offline_cache_repo import (
       Base,
       MutationStatus,
       OfflineCacheMutation,
       OfflineCachePayload,
       OfflineCacheRepository,
       PatientInfo,
       Diagnosis,
   )

   # Configuração de banco