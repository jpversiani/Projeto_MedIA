Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/offline_cache_repo.py` for a project called "MedIA".
   - **Functionality:** Manage a local queue of pending mutations (outbox pattern), synchronization status (PENDENTE, ENVIADO, CONFLITO), and integrity using SQLAlchemy 2.0.
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards compliance (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Full compliance and coverage with automated tests using pytest.
   - **Output Requirement:** Provide complete, executable code. Specify file paths at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/offline_cache_repo.py`
   - **Core Features:**
     - Outbox pattern for pending mutations.
     - Status enum: `PENDENTE`, `ENVIADO`, `CONFLITO`.
     - SQLAlchemy 2.0 ORM models & queries.
     - Pydantic v2 for data validation/serialization.
     - SQLite/PostgreSQL support (dialect-agnostic where possible, but explicit in setup).
     - SUS/APS standards: CIAP-2, CID-10, SOAP, CNS/CPF. This implies the models should reflect these concepts, or at least the context should support them. I'll design the mutation model to include fields relevant to these standards.
     - Test coverage with pytest.
   - **Constraints:** Python 3.12, strict typing, SQLAlchemy 2.0, Pydantic v2.

3.  **Design Decisions:**
   - **Model:** `OfflineCacheMutation`
     - `id`: UUID
     - `entity_type`: str (e.g., 'patient', 'consultation', 'diagnosis')
     - `entity_id`: str
     - `mutation_type`: str (CREATE, UPDATE, DELETE)
     - `payload`: JSON (stores the actual data, validated via Pydantic)
     - `status`: Enum (PENDENTE, ENVIADO, CONFLITO)
     - `priority`: int (default 0)
     - `created_at`, `updated_at`: datetime
     - `error_message`: Optional[str]
     - `retry_count`: int
     - `metadata`: Optional[dict] (for SUS/APS specific fields like CIAP-2, CID-10, SOAP, CNS/CPF)
   - **Enum:** `MutationStatus` with values `PENDENTE`, `ENVIADO`, `CONFLITO`
   - **Pydantic Models:** `MutationPayloadSchema`, `MutationStatusSchema`, etc.
   - **Repository Class:** `OfflineCacheRepository`
     - Methods: `add_mutation`, `get_pending_mutations`, `mark_as_sent`, `mark_as_conflict`, `get_by_id`, `clear_sent`, `get_integrity_report`
     - Use SQLAlchemy 2.0 async/sync? I'll stick to sync for simplicity but note it's compatible with async. I'll use `Session` from `sqlalchemy.orm`.
     - Integrity checks: Ensure no duplicate pending mutations for the same entity+type, validate payload schema, check status transitions.
   - **SUS/APS Compliance:** I'll add specific fields/methods to handle CNS/CPF validation, CIAP-2/CID-10 codes, and SOAP notes in the payload/metadata. I'll create a Pydantic model that enforces these standards.

4.  **Draft Code Structure (Mental):**
   ```python
   # backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations
   import uuid
   from datetime import datetime
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import (
       Column, String, Text, DateTime, Enum as SAEnum, JSON, Integer, Boolean,
       create_engine, func, select, update, delete
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker
   import json

   # Enums
   class MutationStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   # Pydantic Models for SUS/APS
   class SusApsMetadata(BaseModel):
       cns: Optional[str] = None
       cpf: Optional[str] = None
       ciap2_codes: Optional[List[str]] = None
       cid10_codes: Optional[List[str]] = None
       soap_note: Optional[str] = None

       @field_validator('cns')
       @classmethod
       def validate_cns(cls, v):
           if v and len(v) != 15:
               raise ValueError("CNS deve ter 15 dígitos")
           return v

       @field_validator('cpf')
       @classmethod
       def validate_cpf(cls, v):
           if v and len(v) != 14:
               raise ValueError("CPF deve ter 14 dígitos (com formatação)")
           return v

   # SQLAlchemy Base
   class Base(DeclarativeBase):
       pass

   # ORM Model
   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutations"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
       entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
       mutation_type: Mapped[str] = mapped_column(String(10), nullable=False) # CREATE, UPDATE, DELETE
       payload: Mapped[dict] = mapped_column(JSON, nullable=False)
       status: Mapped[MutationStatus] = mapped_column(SAEnum(MutationStatus), default=MutationStatus.PENDENTE)
       priority: Mapped[int] = mapped_column(Integer, default=0)
       created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
       error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       retry_count: Mapped[int] = mapped_column(Integer, default=0)
       metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

   # Repository
   class OfflineCacheRepository:
       def __init__(self, engine):
           self.engine = engine
           self.session_factory = sessionmaker(bind=self.engine)

       def add_mutation(self, entity_type: str, entity_id: str, mutation_type: str, payload: dict, metadata: Optional[dict] = None) -> OfflineCacheMutation:
           # validation & insert logic
           ...

       def get_pending_mutations(self, limit: int = 100) -> List[OfflineCacheMutation]:
           ...

       def mark_as_sent(self, mutation_id: uuid.UUID) -> bool:
           ...

       def mark_as_conflict(self, mutation_id: uuid.UUID, error: str) -> bool:
           ...

       def get_by_id(self, mutation_id: uuid.UUID) -> Optional[OfflineCacheMutation]:
           ...

       def clear_sent_mutations(self, older_than: datetime) -> int:
           ...

       def get_integrity_report(self) -> dict:
           ...
   ```

5.  **Refine & Implement (Mental to Code):**
   I need to ensure strict typing, SQLAlchemy 2.0 syntax, Pydantic v2 compliance, and SUS/APS standards integration. I'll also add a Pydantic model for the payload that validates CNS/CPF, CIAP-2, CID-10, and SOAP format.

   Let's structure the code properly:
   - Imports
   - Enums
   - Pydantic models (Payload, Metadata)
   - SQLAlchemy Base & Model
   - Repository class with methods
   - Helper functions for DB setup (for testing)
   - I'll also include a `__init__.py` or just focus on the requested file.

   I'll make sure the repository uses SQLAlchemy 2.0 style (`select`, `update`, `session.execute`, etc.).
   I'll add type hints everywhere.
   I'll handle SUS/APS validation in Pydantic.

   Let's draft it carefully.

   *Self-Correction/Verification during drafting:*
   - SQLAlchemy 2.0 uses `mapped_column` instead of `Column`. I'll use that.
   - Pydantic v2 uses `@field_validator` instead of `@validator`.
   - I need to ensure the code is executable. I'll include a minimal DB setup function for SQLite/Postgres.
   - The prompt asks for "Repositório Local com Suporte a Cache Offline SQLite/Postgres (C53)". I'll make the engine configurable.
   - I'll add comprehensive docstrings and type hints.
   - I'll ensure SUS/APS fields are properly typed and validated.

   Structure:
   ```python
   # Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from pydantic import BaseModel, Field, field_validator, ValidationError
   from sqlalchemy import (
       String, Text, DateTime, Enum as SAEnum, JSON, Integer, select, update, delete, func
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker
   import json

   # ... (definitions) ...
   ```

   I'll implement the repository methods carefully.
   `add_mutation`: validates payload/metadata, creates record.
   `get_pending_mutations`: selects where status='PENDENTE', orders by priority/created_at.
   `mark_as_sent`: updates status to 'ENVIADO', updated_at.
   `mark_as_conflict`: updates status to 'CONFLITO', sets error_message, increments retry_count.
   `clear_sent_mutations`: deletes where status='ENVIADO' and created_at < threshold.
   `get_integrity_report`: counts by status, checks for duplicates, validates payload schema.

   I'll also add a Pydantic model for the mutation payload that enforces SUS/APS standards:
   ```python
   class SusApsPayloadSchema(BaseModel):
       patient_cns: Optional[str] = None
       patient_cpf: Optional[str] = None
       ciap2_codes: Optional[List[str]] = None
       cid10_codes: Optional[List[str]] = None
       soap_note: Optional[str] = None
       # Add other generic fields if needed, but keep it focused on SUS/APS
   ```
   Actually, the payload should be flexible but validated against SUS/APS standards when applicable. I'll make it a generic dict but add a validator that checks for required SUS/APS fields if they are present. Or better, I'll create a specific `MutationPayload` Pydantic model that enforces these standards.

   Let's stick to a clean design: The repository handles the outbox. The payload is stored as JSON. I'll provide a Pydantic model for validation when adding mutations.

   I'll write the complete code now.

   *Checklist:*
   - Python 3.12, strict typing? Yes.
   - Pydantic v2? Yes.
   - SQLAlchemy 2.0? Yes.
   - Outbox pattern? Yes (pending queue, status transitions).
   - Status: PENDENTE, ENVIADO, CONFLITO? Yes.
   - Integrity? Yes (validation, duplicate checks, retry limits, report).
   - SUS/APS standards? Yes (CNS/CPF validation, CIAP-2/CID-10, SOAP in payload/metadata).
   - SQLite/Postgres support? Yes (dialect-agnostic engine).
   - Complete & executable? Yes, includes setup & example usage.
   - File path specified? Yes.

   I'll generate the code now. I'll make sure it's production-ready and well-documented. I'll also add a `__init__.py` reference if needed, but the prompt asks specifically for `offline_cache_repo.py`.

   One detail: SQLAlchemy 2.0 `mapped_column` requires `sqlalchemy>=2.0.0`. I'll assume that.
   I'll use `datetime.now(timezone.utc)` for modern datetime handling.
   I'll ensure type hints are precise.

   Let's write it out carefully. 
   Structure of the file:
   1. Imports
   2. Enums
   3. Pydantic Models (Payload, Metadata)
   4. SQLAlchemy Base & Model
   5. Repository Class
   6. DB Setup Helper (for testing/execution)
   7. Main block (optional, but good for executability)

   I'll make sure the code is self-contained and runnable. I'll add comments explaining SUS/APS compliance.
   I'll also ensure the repository methods are async-compatible in signature but use sync for simplicity, or I'll stick to sync as requested. The prompt doesn't specify async, so sync is fine. I'll note it's compatible with async.

   Proceed. 
   *Self-Correction/Refinement during thought:*
   - I should make sure the Pydantic models strictly validate SUS/APS formats.
   - CNS: 15 digits. CPF: 11 digits (usually stored without dots, but I'll accept formatted and strip).
   - CIAP-2: 2-3 chars + 1-2 digits (e.g., A00, A00.0)
   - CID-10: 1 char + 3 digits (e.g., A00.0)
   - SOAP: structured text or JSON. I'll keep it as string but validate length/format if needed.
   - I'll add these validators to the Pydantic models.
   - The repository will use these validators when adding mutations.
   - I'll ensure the code is fully type-hinted and follows PEP 484/586.

   Let's draft. 
   *Code Generation starts...* (mental simulation complete, output matches the final response)
   I will structure it carefully. All requirements met. I'll output the code block with the specified path. I'll also include a minimal test example in comments or a separate section if needed, but the prompt says "Execute com precisão conforme as diretrizes" and "Forneça o código completo e executável". I'll make it runnable as a standalone script with SQLite. I'll add pytest tests in a separate block or within the same file? The prompt says "Manter conformidade total e cobertura de testes automatizados com pytest." I should probably provide the tests too, or at least ensure the code is testable. I'll add a `tests/` block or include tests in the response. The prompt says "Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo". I'll provide `offline_cache_repo.py` and `test_offline_cache_repo.py`.

   Actually, I'll focus on the main file as requested, but I'll make sure it's fully testable. I'll add the test file as well to satisfy "cobertura de testes automatizados com pytest".

   Let's produce the response. 
   Structure:
   - `backend/app/repositories/offline_cache_repo.py`
   - `tests/test_offline_cache_repo.py`
   Both with proper paths and complete code.
   I'll ensure strict typing, Pydantic v2, SQLAlchemy 2.0, SUS/APS compliance, outbox pattern, status enum, integrity checks.
   Ready. 
   Output matches the final response. 
   *Self-Correction/Verification during output generation prep:*
   - Check SQLAlchemy 2.0 syntax: `select`, `session.execute`, `mapped_column`, `DeclarativeBase`. Correct.
   - Check Pydantic v2: `BaseModel`, `field_validator`, `ValidationError`. Correct.
   - Check SUS/APS: CNS/CPF validators, CIAP-2/CID-10 patterns, SOAP note field. Correct.
   - Check Outbox: pending queue, status transitions, retry logic, integrity report. Correct.
   - Check Python 3.12: `from __future__ import annotations`, modern typing. Correct.
   - I'll make sure the code is executable by including a `if __name__ == "__main__":` block that demonstrates setup and usage.
   - I'll add pytest tests in a separate block.
   - All good. Proceeds. 
   Output generation. 
   [Done] 
   *Output Generation* (matches the final response)
   - File 1: `backend/app/repositories/offline_cache_repo.py`
   - File 2: `tests/test_offline_cache_repo.py`
   - Both complete, typed, compliant.✅
   - I'll carefully format the code blocks.✅
   - I'll ensure all constraints are met.✅
   - Ready. 
   [Output Generation] -> *Proceeds*
Aqui está a implementação completa e executável, seguindo rigorosamente as diretrizes de arquitetura, tipagem estrita, padrões SUS/APS e padrões de teste.

```python
# Arquivo: backend/app/repositories/offline_cache_repo.py
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ValidationError
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Enum as SAEnum,
    JSON,
    Integer,
    select,
    update,
    delete,
    func,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker
import json
import re


# ---------------------------------------------------------------------------
# Enums & Pydantic Models (SUS/APS Compliance)
# ---------------------------------------------------------------------------

class MutationStatus(str, Enum):
    PENDENTE = "PENDENTE"
    ENVIADO = "ENVIADO"
    CONFLITO = "CONFLITO