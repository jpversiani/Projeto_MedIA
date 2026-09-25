Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/offline_cache_repo.py` for a project called "MedIA".
   - **Features:** Manage a local queue of pending mutations (outbox pattern), synchronization status (PENDENTE, ENVIADO, CONFLITO), integrity with SQLAlchemy 2.0.
   - **Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Full compliance and automated test coverage with pytest.
     - Provide complete, executable code.
     - Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/offline_cache_repo.py`
   - **Core Functionality:** Outbox pattern for offline cache, mutation queue, sync status management.
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0, pytest.
   - **Domain Context:** Brazilian Unified Health System (SUS) / Primary Care (APS) standards: CIAP-2 (classification of health problems), CID-10 (ICD-10), SOAP (Subjective, Objective, Assessment, Plan) notes, CNS (National Health Card number), CPF (Taxpayer Registry).
   - **Testing:** Need comprehensive pytest tests covering all functionality.

3.  **Design the Solution:**
   - **Database Model (SQLAlchemy 2.0):**
     - Table: `offline_cache_mutation`
     - Fields: `id` (UUID), `patient_cns` (str), `patient_cpf` (str), `mutation_type` (enum: CREATE, UPDATE, DELETE), `entity_type` (str: e.g., CONSULTATION, DIAGNOSIS), `payload` (JSON), `status` (enum: PENDENTE, ENVIADO, CONFLITO), `created_at`, `updated_at`, `error_message` (nullable).
     - Use SQLAlchemy 2.0 style: `Mapped`, `mapped_column`, `MappedAsDict` (optional but good for Pydantic integration), `Enum`, `JSON`, `TIMESTAMP`.
   - **Pydantic Models:**
     - `OfflineCacheMutationCreate` (for input)
     - `OfflineCacheMutationStatus` (for output/status)
     - `OfflineCacheMutationResponse` (for full record)
   - **Repository Class:**
     - `OfflineCacheRepository`
     - Methods:
       - `add_mutation(session, mutation_data)` -> adds to queue with status PENDENTE
       - `get_pending_mutations(session, limit)` -> fetches pending mutations
       - `mark_as_sent(session, mutation_id)` -> updates status to ENVIADO
       - `mark_as_conflict(session, mutation_id, error_msg)` -> updates status to CONFLITO
       - `get_mutation_by_id(session, mutation_id)`
       - `cleanup_sent_mutations(session, older_than_days)` -> optional but good for integrity
   - **SUS/APS Context Integration:**
     - Validate CNS/CPF format (basic regex or use a library, but I'll implement basic validation for completeness).
     - Support SOAP note structure in payload.
     - Support CIAP-2/CID-10 codes in payload.
   - **Testing (pytest):**
     - Mock database session or use SQLite in-memory.
     - Test CRUD operations, status transitions, validation, SUS/APS fields.
     - Use `pytest-asyncio` if needed, but I'll keep it sync for simplicity unless specified. I'll stick to sync SQLAlchemy for now, but note it's compatible with async if needed. Actually, SQLAlchemy 2.0 is often used with async, but I'll provide sync for simplicity and clarity, as the prompt doesn't specify async. I'll use `sqlalchemy.orm.Session`.

4.  **Draft Code (Mental Refinement):**

   *File: backend/app/repositories/offline_cache_repo.py*
   ```python
   from __future__ import annotations
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import (
       String, Text, Enum as SAEnum, JSON, TIMESTAMP, func, select, update, delete
   )
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, Session
   import re

   # --- Enums ---
   class MutationStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class MutationType(str, Enum):
       CREATE = "CREATE"
       UPDATE = "UPDATE"
       DELETE = "DELETE"

   # --- Pydantic Models ---
   class OfflineCacheMutationCreate(BaseModel):
       patient_cns: str = Field(..., min_length=15, max_length=15)
       patient_cpf: Optional[str] = Field(None, min_length=11, max_length=14)
       mutation_type: MutationType
       entity_type: str = Field(..., pattern=r"^[A-Z_]+$")
       payload: Dict[str, Any] = Field(default_factory=dict)
       # Optional SUS/APS fields for quick access
       ciap2_codes: Optional[List[str]] = None
       cid10_codes: Optional[List[str]] = None
       soap_note: Optional[Dict[str, str]] = None

       @field_validator("patient_cns")
       @classmethod
       def validate_cns(cls, v: str) -> str:
           # Basic CNS validation (15 digits, starts with 7, 8, or 9)
           if not re.match(r"^[789]\d{14}$", v):
               raise ValueError("CNS inválido. Deve ter 15 dígitos e começar com 7, 8 ou 9.")
           return v

       @field_validator("patient_cpf")
       @classmethod
       def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
           if v is None:
               return v
           cleaned = re.sub(r"[^\d]", "", v)
           if len(cleaned) != 11 or not cleaned.isdigit():
               raise ValueError("CPF inválido. Deve conter 11 dígitos.")
           return cleaned

   class OfflineCacheMutationResponse(BaseModel):
       id: uuid.UUID
       patient_cns: str
       patient_cpf: Optional[str]
       mutation_type: MutationType
       entity_type: str
       payload: Dict[str, Any]
       status: MutationStatus
       ciap2_codes: Optional[List[str]]
       cid10_codes: Optional[List[str]]
       soap_note: Optional[Dict[str, str]]
       created_at: datetime
       updated_at: datetime
       error_message: Optional[str]

       model_config = {"from_attributes": True}

   # --- SQLAlchemy Model ---
   class Base(DeclarativeBase):
       pass

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutation"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       patient_cns: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
       patient_cpf: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
       mutation_type: Mapped[MutationType] = mapped_column(SAEnum(MutationType), nullable=False)
       entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
       payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
       status: Mapped[MutationStatus] = mapped_column(SAEnum(MutationStatus), nullable=False, default=MutationStatus.PENDENTE)
       ciap2_codes: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
       cid10_codes: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
       soap_note: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, nullable=True)
       created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
       updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
       error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

   # --- Repository ---
   class OfflineCacheRepository:
       def __init__(self, session_factory):
           self.session_factory = session_factory

       def _get_session(self) -> Session:
           return self.session_factory()

       def add_mutation(self, mutation_data: OfflineCacheMutationCreate) -> OfflineCacheMutationResponse:
           session = self._get_session()
           try:
               mutation = OfflineCacheMutation(
                   patient_cns=mutation_data.patient_cns,
                   patient_cpf=mutation_data.patient_cpf,
                   mutation_type=mutation_data.mutation_type,
                   entity_type=mutation_data.entity_type,
                   payload=mutation_data.payload,
                   ciap2_codes=mutation_data.ciap2_codes,
                   cid10_codes=mutation_data.cid10_codes,
                   soap_note=mutation_data.soap_note,
                   status=MutationStatus.PENDENTE,
               )
               session.add(mutation)
               session.commit()
               session.refresh(mutation)
               return OfflineCacheMutationResponse.model_validate(mutation)
           except Exception as e:
               session.rollback()
               raise e
           finally:
               session.close()

       def get_pending_mutations(self, limit: int = 100) -> List[OfflineCacheMutationResponse]:
           session = self._get_session()
           try:
               stmt = select(OfflineCacheMutation).where(
                   OfflineCacheMutation.status == MutationStatus.PENDENTE
               ).order_by(OfflineCacheMutation.created_at.asc()).limit(limit)
               results = session.execute(stmt).scalars().all()
               return [OfflineCacheMutationResponse.model_validate(m) for m in results]
           finally:
               session.close()

       def mark_as_sent(self, mutation_id: uuid.UUID) -> Optional[OfflineCacheMutationResponse]:
           session = self._get_session()
           try:
               stmt = update(OfflineCacheMutation).where(
                   OfflineCacheMutation.id == mutation_id
               ).values(status=MutationStatus.ENVIADO, updated_at=datetime.now(timezone.utc))
               session.execute(stmt)
               session.commit()
               stmt_get = select(OfflineCacheMutation).where(OfflineCacheMutation.id == mutation_id)
               mutation = session.execute(stmt_get).scalar_one_or_none()
               return OfflineCacheMutationResponse.model_validate(mutation) if mutation else None
           except Exception as e:
               session.rollback()
               raise e
           finally:
               session.close()

       def mark_as_conflict(self, mutation_id: uuid.UUID, error_message: str) -> Optional[OfflineCacheMutationResponse]:
           session = self._get_session()
           try:
               stmt = update(OfflineCacheMutation).where(
                   OfflineCacheMutation.id == mutation_id
               ).values(status=MutationStatus.CONFLITO, error_message=error_message, updated_at=datetime.now(timezone.utc))
               session.execute(stmt)
               session.commit()
               stmt_get = select(OfflineCacheMutation).where(OfflineCacheMutation.id == mutation_id)
               mutation = session.execute(stmt_get).scalar_one_or_none()
               return OfflineCacheMutationResponse.model_validate(mutation) if mutation else None
           except Exception as e:
               session.rollback()
               raise e
           finally:
               session.close()

       def get_mutation_by_id(self, mutation_id: uuid.UUID) -> Optional[OfflineCacheMutationResponse]:
           session = self._get_session()
           try:
               stmt = select(OfflineCacheMutation).where(OfflineCacheMutation.id == mutation_id)
               mutation = session.execute(stmt).scalar_one_or_none()
               return OfflineCacheMutationResponse.model_validate(mutation) if mutation else None
           finally:
               session.close()

       def cleanup_sent_mutations(self, older_than_days: int = 30) -> int:
           session = self._get_session()
           try:
               cutoff = datetime.now(timezone.utc).replace(day=1) # Simplified for demo, ideally use timedelta
               from datetime import timedelta
               cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
               stmt = delete(OfflineCacheMutation).where(
                   OfflineCacheMutation.status == MutationStatus.ENVIADO,
                   OfflineCacheMutation.updated_at < cutoff
               )
               result = session.execute(stmt)
               session.commit()
               return result.rowcount
           finally:
               session.close()
   ```

   *Wait, I need to fix the `cleanup_sent_mutations` logic.* `datetime.now(timezone.utc).replace(day=1)` is wrong. I'll fix it properly.
   Also, SQLAlchemy 2.0 prefers `func.now()` for timestamps, but Python-side defaults are fine for this context. I'll stick to Python-side for simplicity but note it. Actually, `default=lambda: datetime.now(timezone.utc)` is fine.

   Let's refine the repository to be more robust and follow best practices. I'll also add proper type hints and ensure Pydantic v2 compatibility.

   *File: backend/app/repositories/offline_cache_repo.py* (Revised)
   I'll structure it carefully.

   Now, the test file: `backend/app/repositories/test_offline_cache_repo.py`
   Need to use `pytest`, `sqlalchemy`, `pytest-mock` or `unittest.mock`, and in-memory SQLite.
   I'll create a fixture for the database session.

   ```python
   import pytest
   import uuid
   from datetime import datetime, timezone, timedelta
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from backend.app.repositories.offline_cache_repo import (
       Base,
       OfflineCacheRepository,
       OfflineCacheMutationCreate,
       MutationType,
       MutationStatus,
       OfflineCacheMutationResponse,
   )

   @pytest.fixture
   def engine():
       engine = create_engine("sqlite:///:memory:", echo=False)
       Base.metadata.create_all(engine)
       yield engine
       Base.metadata.drop_all(engine)

   @pytest.fixture
   def session_factory(engine):
       SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
       return SessionLocal

   @pytest.fixture
   def repo(session_factory):
       return OfflineCacheRepository(session_factory)

   @pytest.fixture
   def valid_mutation_data():
       return OfflineCacheMutationCreate(
           patient_cns="700000000000000",
           patient_cpf="12345678909",
           mutation_type=MutationType.CREATE,
           entity_type="CONSULTATION",
           payload={"subjective": "Dor abdominal", "objective": "Sinais vitais estáveis"},
           ciap2_codes=["A01"],
           cid10_codes=["K30"],
           soap_note={"S": "Queixa principal", "O": "Exame físico", "A": "Hipótese diagnóstica", "P": "Conduta"}
       )

   # Tests...
   ```

   I'll write comprehensive tests covering:
   - Add mutation (PENDENTE)
   - Get pending mutations
   - Mark as sent
   - Mark as conflict
   - Validation (CNS/CPF)
   - Cleanup
   - Error handling

   Let's draft the full test file.

   *Self-Correction/Refinement during thought:*
   - SQLAlchemy 2.0 `TIMESTAMP` timezone handling: `TIMESTAMP(timezone=True)` is correct.
   - Pydantic v2 `from_attributes` is correct.
   - CNS validation regex: `^[789]\d{14}$` is standard for Brazil.
   - CPF validation: I'll keep it simple but functional.
   - I should ensure the code is fully executable and follows the prompt's exact file path requirement.
   - I'll add comments explaining SUS/APS integration points.
   - I'll make sure the repository handles transactions properly.
   - I'll use `sqlalchemy.ext.asyncio`? The prompt doesn't specify async, so sync is safer. I'll stick to sync but note it's easily adaptable.
   - I'll structure the code clearly.

   Let's write out the complete solution.

   Structure:
   1. `backend/app/repositories/offline_cache_repo.py`
   2. `backend/app/repositories/test_offline_cache_repo.py`

   I'll carefully check SQLAlchemy 2.0 syntax:
   - `Mapped`, `mapped_column`
   - `select`, `update`, `delete`
   - `Session`
   - All good.

   Pydantic v2:
   - `field_validator`
   - `model_config = {"from_attributes": True}`
   - All good.

   SUS/APS:
   - CNS/CPF validation
   - CIAP-2/CID-10 fields
   - SOAP note structure
   - All good.

   I'll now generate the response.
   I need to make sure the code is complete, executable, and follows the exact path format requested.
   I'll add necessary imports and ensure it runs with `pytest`.
   I'll also add a `__init__.py` note if needed, but not required.
   I'll structure the output clearly.
   Let's write it out. 
   *Self-Correction/Verification during drafting:*
   - `cleanup_sent_mutations` uses `timedelta` but I imported it inside. I'll move it to top.
   - `datetime.now(timezone.utc)` is fine.
   - I'll add proper docstrings.
   - I'll ensure the test file uses `pytest` correctly and can be run standalone.
   - I'll add a note about running tests: `pytest backend/app/repositories/test_offline_cache_repo.py -v`
   - The prompt says "Execute com precisão conforme as diretrizes