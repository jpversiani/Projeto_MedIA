Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/remessas_sisab_repo.py` for the MedIA project.
   - **Purpose:** Persist transmission batches (lotes), send status (GERADO, ENVIADO, PROCESSADO, REJEITADO), and SISAB return logs.
   - **Architecture Guidelines:**
     - Python 3.12
     - Strict typing with Pydantic v2 and SQLAlchemy 2.0
     - SUS/APS standards compliance (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
     - Full compliance with automated testing coverage using pytest
   - **Output Requirement:** Provide complete, executable code. Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/remessas_sisab_repo.py`
   - **Domain:** SISAB (Sistema de Informação em Saúde para o Sistema Único de Saúde) - specifically for export batches (remessas/lotes).
   - **Entities/Models:**
     - `SisabBatch` (Lote de transmissão)
     - `SisabBatchStatus` (Status: GERADO, ENVIADO, PROCESSADO, REJEITADO)
     - `SisabReturnLog` (Logs de retorno do SISAB)
   - **Pydantic v2:** Use for data validation/serialization (schemas).
   - **SQLAlchemy 2.0:** Use for ORM models, async/sync session handling (I'll assume async as it's modern, but I'll make it compatible or explicitly use `sqlalchemy.orm` with `Session` or `AsyncSession`. I'll stick to standard SQLAlchemy 2.0 style with `sessionmaker` and `Session` for simplicity, but I'll note it's compatible with async if needed. Actually, I'll use `sqlalchemy.orm` with `Session` as it's standard, but I'll make it clear. I'll use `sqlalchemy` 2.0 declarative style.)
   - **SUS/APS Standards:** CIAP-2, CID-10, SOAP method, CNS/CPF. These should be reflected in the model fields or validation.
   - **Testing:** Provide pytest tests covering the repository, models, and Pydantic schemas.

3.  **Design the Repository (`remessas_sisab_repo.py`):**
   - **Imports:** `sqlalchemy`, `sqlalchemy.orm`, `pydantic`, `enum`, `datetime`, `uuid`, `typing`, `logging`.
   - **Enums:** `SisabBatchStatus` (GERADO, ENVIADO, PROCESSADO, REJEITADO)
   - **Pydantic Schemas:**
     - `SisabBatchCreate`
     - `SisabBatchUpdate`
     - `SisabReturnLogCreate`
     - `SisabBatchResponse`
     - `SisabReturnLogResponse`
   - **SQLAlchemy Models:**
     - `SisabBatch` (id, lote_id, data_criacao, status, cns_origem, cpf_origem, descricao, xml_content, created_at, updated_at)
     - `SisabReturnLog` (id, lote_id, data_retorno, codigo_retorno, descricao_retorno, xml_retorno, created_at)
   - **Repository Class:** `SisabBatchRepository`
     - Methods: `create_batch`, `update_status`, `get_batch`, `get_batches_by_status`, `create_return_log`, `get_return_logs`, `delete_batch`, etc.
     - Use dependency injection pattern for `Session` (standard in FastAPI/SQLAlchemy).
   - **SUS/APS Compliance:** Add fields for CIAP-2, CID-10, SOAP method, CNS/CPF in the models/schemas. Add validation in Pydantic.

4.  **Draft the Code (Mental Refinement):**
   Let's structure it carefully.

   ```python
   # Arquivo: backend/app/repositories/remessas_sisab_repo.py
   from __future__ import annotations
   import enum
   import logging
   from datetime import datetime, timezone
   from typing import Optional, Sequence
   from uuid import UUID, uuid4

   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy import String, Text, DateTime, Enum as SAEnum, ForeignKey, func
   from sqlalchemy.orm import (
       DeclarativeBase,
       Mapped,
       mapped_column,
       Session,
       relationship,
       select,
   )

   # ... define enums, models, schemas, repository ...
   ```

   *Enums:*
   ```python
   class SisabBatchStatus(str, enum.Enum):
       GERADO = "GERADO"
       ENVIADO = "ENVIADO"
       PROCESSADO = "PROCESSADO"
       REJEITADO = "REJEITADO"
   ```

   *SQLAlchemy Base:*
   ```python
   class Base(DeclarativeBase):
       pass
   ```

   *SQLAlchemy Models:*
   ```python
   class SisabBatchModel(Base):
       __tablename__ = "sisab_batches"

       id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
       lote_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
       data_criacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       status: Mapped[SisabBatchStatus] = mapped_column(SAEnum(SisabBatchStatus), default=SisabBatchStatus.GERADO)
       cns_origem: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       cpf_origem: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
       metodo_sus: Mapped[str] = mapped_column(String(20), default="SOAP")
       ciap2_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON string or comma-separated
       cid10_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       xml_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc))

       logs: Mapped[list["SisabReturnLogModel"]] = relationship(back_populates="batch", cascade="all, delete-orphan")
   ```

   *Return Log Model:*
   ```python
   class SisabReturnLogModel(Base):
       __tablename__ = "sisab_return_logs"

       id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
       lote_id: Mapped[UUID] = mapped_column(ForeignKey("sisab_batches.id"), index=True)
       data_retorno: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       codigo_retorno: Mapped[str] = mapped_column(String(10))
       descricao_retorno: Mapped[str] = mapped_column(String(255))
       xml_retorno: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

       batch: Mapped["SisabBatchModel"] = relationship(back_populates="logs")
   ```

   *Pydantic Schemas:*
   Need to handle validation for CNS/CPF, CIAP-2, CID-10.
   CNS: 15 digits. CPF: 11 digits. CIAP-2: alphanumeric. CID-10: alphanumeric.
   I'll add simple validators.

   ```python
   class SisabBatchCreate(BaseModel):
       lote_id: str = Field(..., min_length=1, max_length=36)
       cns_origem: Optional[str] = None
       cpf_origem: Optional[str] = None
       metodo_sus: str = "SOAP"
       ciap2_codes: Optional[str] = None
       cid10_codes: Optional[str] = None
       xml_content: Optional[str] = None

       @field_validator("cns_origem")
       @classmethod
       def validate_cns(cls, v: Optional[str]) -> Optional[str]:
           if v and not v.isdigit() or len(v) != 15:
               raise ValueError("CNS deve conter exatamente 15 dígitos numéricos.")
           return v

       @field_validator("cpf_origem")
       @classmethod
       def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
           if v and (not v.isdigit() or len(v) != 11):
               raise ValueError("CPF deve conter exatamente 11 dígitos numéricos.")
           return v
   ```

   Similar for Update and Response schemas. I'll keep it concise but complete.

   *Repository Class:*
   Standard async/sync? I'll use sync `Session` for simplicity but note it's compatible. Actually, FastAPI usually uses async, but I'll stick to sync `Session` as it's standard in SQLAlchemy 2.0 examples unless specified. I'll make it accept `Session` in `__init__` or use a context manager. I'll use a class with methods that take `session: Session` as a parameter, which is standard for testing.

   ```python
   class SisabBatchRepository:
       def __init__(self, session: Session):
           self.session = session

       async def create_batch(self, data: SisabBatchCreate) -> SisabBatchModel:
           # ...
   ```
   Wait, the prompt says "Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0". It doesn't specify async/sync. I'll use sync for simplicity but add type hints. Actually, I'll make it fully type-hinted and use `Session` from `sqlalchemy.orm`.

   Let's draft the repository methods carefully:
   - `create_batch`
   - `update_status`
   - `get_batch`
   - `get_batches_by_status`
   - `create_return_log`
   - `get_return_logs`
   - `delete_batch`

   I'll implement them with proper SQLAlchemy 2.0 syntax (`select`, `session.execute`, etc.).

5.  **Draft the Test File (`test_remessas_sisab_repo.py`):**
   - Use `pytest`, `pytest-asyncio` (if async) or standard `pytest`. I'll stick to sync for simplicity, but I'll make it clear. Actually, I'll use `pytest` with `sqlalchemy` in-memory SQLite for testing.
   - Need to test:
     - Pydantic validation (CNS, CPF)
     - Repository CRUD operations
     - Status transitions
     - Return logs persistence
     - SUS/APS field constraints
   - I'll provide a complete `conftest.py` or inline fixtures.

   Structure:
   ```python
   # Arquivo: backend/app/tests/test_remessas_sisab_repo.py
   import pytest
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from backend.app.repositories.remessas_sisab_repo import (
       Base,
       SisabBatchRepository,
       SisabBatchCreate,
       SisabBatchStatus,
       SisabReturnLogCreate,
   )

   # ... fixtures ...
   # ... tests ...
   ```

6.  **Refine & Self-Correction/Verification:**
   - *Check guidelines:* Python 3.12, strict typing, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP, CNS/CPF), pytest coverage.
   - *Pydantic v2:* Uses `field_validator`, `ConfigDict`, `model_validator` if needed. I'll use `field_validator`.
   - *SQLAlchemy 2.0:* Uses `Mapped`, `mapped_column`, `select`, `session.execute`. Correct.
   - *SUS/APS:* Added fields for CNS, CPF, CIAP-2, CID-10, SOAP. Added validation.
   - *Repository:* Should handle transactions properly. I'll add a `commit` method or assume the caller handles it. I'll make methods return the ORM model and let the caller commit, or add a `save`/`commit` helper. Standard practice: repository methods take a session, perform operations, and return results. I'll explicitly handle commits inside methods for simplicity, or document it. I'll add a `commit()` method to the repo.
   - *Testing:* I'll write comprehensive tests covering validation, CRUD, status updates, and log persistence. I'll use `pytest` with `tmp_path` or in-memory SQLite.
   - *Code Structure:* I'll put everything in one block as requested, but clearly separated. The prompt asks for `backend/app/repositories/remessas_sisab_repo.py`. I'll also provide the test file as it's required for "cobertura de testes automatizados com pytest".

   Let's draft carefully.

   *Self-Correction/Improvement during drafting:*
   - Pydantic v2 validation for CNS/CPF: I'll use regex or simple length/type checks. CNS is 15 digits. CPF is 11 digits. I'll add proper validators.
   - SQLAlchemy 2.0: I'll use `session.execute(select(...)).scalars().first()` pattern.
   - I'll make the repository methods `async` compatible but use sync `Session` for simplicity, or explicitly use `async_session`. Actually, I'll stick to sync `Session` as it's standard and easier to test without `pytest-asyncio` complexity, but I'll add type hints. I'll note it's compatible with async.
   - I'll ensure all imports are correct.
   - I'll add docstrings and type hints strictly.
   - I'll structure the test file to be runnable with `pytest`.

   Let's write it out carefully.

   *Structure of `remessas_sisab_repo.py`:*
   - Imports
   - Enums
   - Base
   - ORM Models
   - Pydantic Schemas
   - Repository Class
   - Helper functions (if any)

   *Structure of `test_remessas_sisab_repo.py`:*
   - Imports
   - Fixtures (engine, session, repo)
   - Tests for Pydantic validation
   - Tests for Repository CRUD
   - Tests for Status & Logs
   - Tests for SUS/APS constraints

   I'll make sure the code is complete and executable.

   *Key considerations for SUS/APS:*
   - CIAP-2: Código Internacional de Doenças em Atenção Primária (alphanumeric, usually 2-4 chars).
   - CID-10: Alphanumeric, 2-7 chars.
   - SOAP: Standard method for SISAB web services.
   - CNS/CPF: Identification.
   I'll add these to the schema and models.

   Let's draft. 
   I will carefully check SQLAlchemy 2.0 syntax:
   ```python
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, Session, select
   from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, func
   ```
   Correct.

   Pydantic v2:
   ```python
   from pydantic import BaseModel, Field, field_validator, ConfigDict
   ```
   Correct.

   Repository methods will use `session.execute()` and `session.commit()`.

   I'll write the code now. 
   I'll ensure strict typing: `from typing import Optional, Sequence, List, Dict, Any`
   I'll add `@dataclass` or just use Pydantic for schemas.
   I'll make sure the test file is complete.

   One thing: The prompt says "Execute com precisão conforme as diretrizes." and "Forneça o código completo e executável."
   I'll provide both files in one response, clearly marked.

   Let's generate. 
   *Self-Correction/Verification during thought:*
   - Pydantic v2 `field_validator` needs `@field_validator("field_name")`.
   - SQLAlchemy 2.0 `mapped_column` requires `default=` or `server_default=`.
   - I'll use `datetime.now(timezone.utc)` for defaults.
   - I'll add a `commit()` method to the repo to manage transactions safely.
   - I'll ensure the test file uses `pytest` and `sqlalchemy` in-memory DB.
   - I'll add comments explaining SUS/APS compliance.
   - I'll make sure type hints are strict.

   All good. Proceeding. 
   Output matches the response. 
   Structure:
   1. `backend/app/repositories/remessas_sisab_repo.py`
   2. `backend/app/tests/test_remessas_sisab_repo.py`
   Both complete, typed, compliant.✅
   I will now generate the response. 
   *Output Generation* (matches the final response)
   - Includes strict typing, Pydantic v2, SQLAlchemy 2.0
   - SUS/APS fields & validation
   - Repository with CRUD & status management
   - Comprehensive pytest suite
   - Clear file paths as requested.✅
   Ready. 
   [Output Generation] -> *Proceeds*
Aqui está a implementação completa e executável, seguindo rigorosamente as diretrizes de arquitetura, tipagem estrita, padrões do SUS/APS e cobertura de testes com pytest.

```python
# Arquivo: backend/app/repositories/remessas_sisab_repo.py
from __future__ import annotations

import enum
import logging
from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ConfigDict
from sqlalchemy import String, Text, DateTime, Enum as SAEnum, ForeignKey, func, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    Session,
    relationship,
