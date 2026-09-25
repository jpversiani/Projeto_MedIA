Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/convenios_repo.py` for a project called "MedIA".
   - **Domain:** Repository of Health Plans/Operators (Convênios), TISS Guides (Guias TISS), and Financial Receipts (Lançamentos Financeiros).
   - **Requirements:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification.
     - Full compliance and automated test coverage with pytest.
     - Provide complete, executable code.
     - Specify file paths clearly.
   - **Key Entities to Model:**
     - Operadoras/Planos de Saúde (Health Operators/Plans)
     - Guias TISS (TISS Guides) with status: GERADA, ENVIADA, FATURADA, GLOSADA
     - Recibos Particulares (Private Receipts)
     - References to CIAP-2, CID-10, SOAP, CNS/CPF
   - **Architecture/Standards:**
     - SQLAlchemy 2.0 (declarative, async/sync? I'll use sync for simplicity but note it can be adapted, or use async if preferred. I'll stick to sync for broader compatibility, but SQLAlchemy 2.0 style is key).
     - Pydantic v2 for DTOs/validations.
     - Strict typing.
     - pytest coverage.

2.  **Deconstruct Requirements & Plan Structure:**
   - I need to create:
     - `backend/app/repositories/convenios_repo.py` (main file requested)
     - Models (SQLAlchemy 2.0)
     - Pydantic schemas (v2)
     - Repository functions/queries
     - Pytest tests
   - Since the prompt asks for `backend/app/repositories/convenios_repo.py`, I'll focus on that, but I should also provide the necessary models/schemas if they aren't assumed to exist, or structure it so it's self-contained for testing. I'll create a complete module with models, schemas, repository, and tests in a logical way, but I'll clearly mark the main file as requested. Actually, the prompt says "crie backend/app/repositories/convenios_repo.py: modelos e consultas SQLAlchemy 2.0...". I'll put everything in that file for simplicity, or split logically but clearly indicate paths. I'll stick to one main file for the repo, and provide tests separately.
   - Let's define the entities:
     - `OperadoraSaude`: id, nome, cnpj, contato, status
     - `PlanoSaude`: id, operadora_id, nome, codigo_ans, tipo (ambulatorial, hospitalar, etc.)
     - `GuiaTISS`: id, plano_id, paciente_cns, paciente_cpf, data_emissao, status (enum), ciap2_codes (JSON/list), cid10_codes (JSON/list), soap_data (JSON), xml_tiss (text), created_at, updated_at
     - `LancamentoFinanceiro`: id, guia_id, tipo (particular, convenio), valor, descricao, status, data_lancamento
   - I'll use SQLAlchemy 2.0 declarative style with `Mapped`, `mapped_column`, `relationship`.
   - I'll use Pydantic v2 for DTOs.
   - I'll implement repository functions using SQLAlchemy 2.0 session patterns.
   - I'll write comprehensive pytest tests.

3.  **Draft - `backend/app/repositories/convenios_repo.py`:**
   - Imports: `uuid`, `datetime`, `enum`, `list`, `dict`, `Optional`, `Any`, `Session` from sqlalchemy, `Column`, `String`, `Integer`, `Float`, `DateTime`, `Boolean`, `Enum`, `Text`, `JSON`, `relationship`, `mapped_column`, `Mapped`, `DeclarativeBase`, `select`, `update`, `delete`, `insert`, `sessionmaker`, `create_engine` (for testing), `pydantic` models.
   - Define Enums: `GuiaStatus`, `LancamentoTipo`, `LancamentoStatus`
   - Define Base class: `class Base(DeclarativeBase): pass`
   - Define Models:
     - `Operadora`
     - `Plano`
     - `GuiaTISS`
     - `LancamentoFinanceiro`
   - Define Pydantic Schemas (v2):
     - `OperadoraCreate`, `OperadoraRead`
     - `PlanoCreate`, `PlanoRead`
     - `GuiaTISSCreate`, `GuiaTISSRead`
     - `LancamentoFinanceiroCreate`, `LancamentoFinanceiroRead`
   - Define Repository class/functions:
     - `ConveniosRepository` with methods like `create_operadora`, `get_operadora`, `create_plano`, `get_plano`, `create_guia`, `update_guia_status`, `get_guias_by_status`, `create_lancamento`, `get_lancamentos`, etc.
     - Use SQLAlchemy 2.0 syntax: `session.execute(select(...))`, `session.execute(update(...))`, etc.
   - Ensure strict typing and Pydantic v2 compliance.
   - Add comments for SUS/APS standards (CIAP-2, CID-10, SOAP, CNS/CPF).

   Let's write it out carefully.

   *Self-Correction/Refinement during drafting:*
   - SQLAlchemy 2.0 uses `mapped_column` instead of `Column`. I'll use `Mapped` and `mapped_column`.
   - Pydantic v2 uses `model_config = ConfigDict(from_attributes=True)` for ORM compatibility.
   - I'll make the repository methods async or sync? The prompt doesn't specify, but sync is fine for examples. I'll use sync for simplicity but note it's compatible with async. Actually, I'll stick to sync to keep it straightforward, but I'll make sure it's SQLAlchemy 2.0 style.
   - I need to ensure the code is complete and executable. I'll include a test database setup in the pytest file.
   - I'll structure the repo file with clear sections: Enums, Models, Schemas, Repository.
   - I'll add validation for CNS/CPF in Pydantic schemas.
   - I'll ensure CIAP-2, CID-10, SOAP are represented as JSON/arrays in the model, with Pydantic validation.

   Let's draft the code mentally first, then write it out.

   **Models:**
   ```python
   class Operadora(Base):
       __tablename__ = "operadoras"
       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
       cnpj: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
       contato_email: Mapped[str] = mapped_column(String(255))
       status: Mapped[bool] = mapped_column(Boolean, default=True)
       planos: Mapped[list["Plano"]] = relationship(back_populates="operadora", cascade="all, delete-orphan")

   class Plano(Base):
       __tablename__ = "planos"
       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       operadora_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("operadoras.id"))
       nome: Mapped[str] = mapped_column(String(100), nullable=False)
       codigo_ans: Mapped[str] = mapped_column(String(6), unique=True, nullable=False)
       tipo: Mapped[str] = mapped_column(String(20)) # ambulatorial, hospitalar, etc.
       operadora: Mapped["Operadora"] = relationship(back_populates="planos")
       guias: Mapped[list["GuiaTISS"]] = relationship(back_populates="plano", cascade="all, delete-orphan")

   class GuiaTISS(Base):
       __tablename__ = "guias_tiss"
       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       plano_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("planos.id"))
       paciente_cns: Mapped[str] = mapped_column(String(15))
       paciente_cpf: Mapped[str] = mapped_column(String(11))
       data_emissao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       status: Mapped[GuiaStatus] = mapped_column(Enum(GuiaStatus), default=GuiaStatus.GERADA)
       ciap2_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
       cid10_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
       soap_data: Mapped[dict] = mapped_column(JSON, default=dict)
       xml_tiss: Mapped[str] = mapped_column(Text)
       plano: Mapped["Plano"] = relationship(back_populates="guias")
       lancamentos: Mapped[list["LancamentoFinanceiro"]] = relationship(back_populates="guia", cascade="all, delete-orphan")

   class LancamentoFinanceiro(Base):
       __tablename__ = "lancamentos_financeiros"
       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       guia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("guias_tiss.id"))
       tipo: Mapped[LancamentoTipo] = mapped_column(Enum(LancamentoTipo))
       valor: Mapped[float] = mapped_column(Float, nullable=False)
       descricao: Mapped[str] = mapped_column(String(255))
       status: Mapped[LancamentoStatus] = mapped_column(Enum(LancamentoStatus), default=LancamentoStatus.PENDENTE)
       data_lancamento: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       guia: Mapped["GuiaTISS"] = relationship(back_populates="lancamentos")
   ```

   **Pydantic Schemas (v2):**
   Need to validate CNS (15 digits) and CPF (11 digits). I'll use `field_validator`.
   CIAP-2 and CID-10 validation: CIAP-2 is typically 1-3 letters + 1-2 digits. CID-10 is 1 letter + 2 digits. I'll add basic regex validators.
   SOAP: Subjective, Objective, Assessment, Plan. I'll validate structure.

   **Repository:**
   Standard CRUD + status updates + financial controls.
   I'll use `session.execute(select(...))` pattern.

   **Tests:**
   Use `pytest`, `sqlalchemy`, `tempfile` for SQLite in-memory or file-based.
   Test models, schemas, repo methods.
   Ensure coverage.

   Let's write it out carefully, ensuring all constraints are met.
   I'll structure the response with clear file paths.
   I'll make sure the code is Python 3.12 compatible, uses strict typing, Pydantic v2, SQLAlchemy 2.0.
   I'll add comments for SUS/APS standards.
   I'll provide the repo file and the test file.

   *Self-Correction/Verification during thought:*
   - SQLAlchemy 2.0 `mapped_column` requires `from sqlalchemy.orm import mapped_column`.
   - `Enum` in SQLAlchemy 2.0: `mapped_column(Enum(...))` is fine, but sometimes `TypeDecorator` or `String` is safer for portability. I'll stick to `Enum` but note it. Actually, SQLAlchemy 2.0 recommends `Enum` from `sqlalchemy`.
   - Pydantic v2: `model_config = ConfigDict(from_attributes=True)` is correct.
   - CNS validation: 15 digits. CPF: 11 digits.
   - CIAP-2: `[A-Z]{1,3}\d{1,2}`
   - CID-10: `[A-Z]\d{2}`
   - SOAP: dict with keys `s`, `o`, `a`, `p`.
   - I'll implement these validators.
   - Repository will be a class with methods taking `Session`.
   - I'll write comprehensive tests.

   Let's draft the code. 
   I'll structure it as:
   1. `backend/app/repositories/convenios_repo.py`
   2. `backend/tests/test_convenios_repo.py`
   I'll ensure it's complete and executable.
   I'll use `typing` module for strict types.
   I'll add type hints everywhere.
   I'll make sure the code runs with `pytest`.

   *Code Structure Generation:*
   (Mental walkthrough of the code to ensure correctness)
   - Imports: `uuid`, `datetime`, `enum`, `typing`, `sqlalchemy`, `pydantic`, `pytest`, `sqlalchemy.orm`, `sqlalchemy.ext.asyncio` (optional, but I'll stick to sync for simplicity unless specified. I'll use sync).
   - Enums: `GuiaStatus`, `LancamentoTipo`, `LancamentoStatus`
   - Base: `DeclarativeBase`
   - Models: as above
   - Schemas: Pydantic v2 with validators
   - Repo: `class ConveniosRepository:`
   - Tests: `pytest` with `sessionmaker`, `create_engine`, `Base.metadata.create_all`
   - All strict typing.
   - Comments for SUS/APS.
   - Ready.

   I will now generate the response. 
   I'll make sure to explicitly state the file paths as requested.
   I'll ensure the code is self-contained and executable.
   I'll add necessary imports and configuration.
   I'll verify Pydantic v2 syntax (`model_config`, `field_validator`, `ConfigDict`).
   I'll verify SQLAlchemy 2.0 syntax (`mapped_column`, `Mapped`, `select`, `session.execute`).
   I'll verify Python 3.12 compatibility (no deprecated features).
   All good. Proceed. 
   Output matches the response. 
   Structure:
   - `backend/app/repositories/convenios_repo.py`
   - `backend/tests/test_convenios_repo.py`
   - Instructions for running.
   - Clear comments.
   - Strict typing.
   - Pydantic v2.
   - SQLAlchemy 2.0.
   - SUS/APS standards noted.
   - pytest coverage.
   Done. 
   Generating. 
   *[Self-Correction/Refinement during generation prep]*
   - I should make sure the repository methods are properly typed and use SQLAlchemy 2.0 patterns.
   - I'll add `session.commit()` and `session.refresh()` where needed.
   - I'll use `typing.Annotated` if needed, but standard types are fine.
   - I'll ensure the test file sets up a real DB session for each test.
   - I'll add coverage markers.
   - All set. 
   Output matches the final response. 
   Proceeds. 
   [Output Generation] -> *See response.* 
   *(Note: I'll carefully format the code blocks with the exact paths as requested.)*
   *(I'll also ensure the Pydantic schemas validate CNS/CPF/CIAP-2/CID-10/SOAP as requested.)*
   *(I'll make sure the repository uses SQLAlchemy 2.0 `select`/`execute` pattern.)*
   *(I'll add pytest tests with proper fixtures.)*
   *(All constraints met.)*
Aqui está a implementação completa, seguindo rigorosamente as diretrizes: Python 3.12, tipagem estrita, Pydantic v2, SQLAlchemy 2.0, conformidade com padrões SUS/APS e cobertura de testes com pytest.

### 1. Arquivo Principal: Repositório, Modelos e Schemas
```python
# Arquivo: backend/app/repositories/convenios_repo.py
"""
Repositório de Convênios, Guias TISS e Lançamentos Financeiros.
Conformidade SUS/APS: CIAP-2, CID-10, SOAP, CNS/CPF.
Stack: Python 3.12, SQLAlchemy 2.0, Pydantic v2.
"""

from __future__ import annotations

import uuid
import re
import enum
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    func,
    select,
    update,
    delete,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    Session,
)

# =============================================================================
# Enums de Domínio
# =============================================================================
class GuiaStatus(enum.Enum):
    GERADA = "GERADA"
    ENVIADA = "ENVIADA"
    FATURADA = "FATURADA"
    GLOSADA = "GLOSADA"

class LancamentoTipo(enum.Enum):
    PARTICULAR = "PARTICULAR"
    CONVENIO = "CONVENIO"
    REEMBOLSO = "REEMBOLSO"

class LancamentoStatus(enum.Enum):
    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    REJEITADO = "REJEITADO"
    ESTORRADO = "ESTORRADO"

# =============================================================================
# Base SQLAlchemy 2.0
# =============================================================================
class Base(DeclarativeBase):
    pass

# =============================================================================
# Modelos ORM (SQLAlchemy 2.0)
# =============================================================================
class Operadora(Base):
    __tablename__ = "operadoras"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    contato_email