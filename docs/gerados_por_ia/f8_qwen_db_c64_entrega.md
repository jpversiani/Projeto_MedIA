Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for a project called "MedIA".
   - **Features:** Campaign repository for health campaigns and sending history. Track sent messages, patient confirmation status, and data protection audit logs.
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification.
     - Full compliance and automated test coverage with pytest.
   - **Output Requirement:** Provide complete, executable code. Specify file paths at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/campanhas_repo.py`
   - **Domain:** Health campaigns, message dispatch history, patient confirmation, data protection audit logs.
   - **Standards:** CIAP-2 (Classificação Internacional de Assistência Primária), CID-10 (ICD-10), SOAP (Subjective, Objective, Assessment, Plan), CNS (Cartão Nacional de Saúde), CPF (Cadastro de Pessoas Físicas).
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0 (async/sync? I'll assume async for modern apps, but I'll make it compatible or specify. I'll use SQLAlchemy 2.0 with async session pattern, but keep it standard. I'll provide both models and repository methods).
   - **Testing:** Pytest coverage required. I'll need to provide the repo code and a corresponding test file.

3.  **Design Database Models (SQLAlchemy 2.0):**
   - `Campanha` (Campaign): id, name, description, start_date, end_date, status, created_at, updated_at
   - `MensagemDisparo` (MessageDispatch): id, campanha_id, paciente_cpf, paciente_cns, message_content, status (sent, delivered, confirmed, failed), sent_at, confirmed_at, cid10_codes (list/JSON), ciap2_codes (list/JSON), soap_notes (JSON/text), created_at
   - `LogAuditoriaLGPD` (LGPD Audit Log): id, campanha_id, mensagem_disparo_id, action (view, export, delete, consent_granted, consent_revoked), performed_by, performed_at, ip_address, user_agent, details (JSON)
   - I'll use SQLAlchemy 2.0 declarative syntax. I'll define enums for statuses.

4.  **Design Pydantic Schemas (v2):**
   - `CampanhaCreate`, `CampanhaRead`, `CampanhaUpdate`
   - `MensagemDisparoCreate`, `MensagemDisparoRead`, `MensagemDisparoUpdate`
   - `LogAuditoriaLGPDCreate`, `LogAuditoriaLGPDRead`
   - Use `ConfigDict`, `Field`, `model_validator`, `computed_field` as needed.
   - Strict typing: `str`, `int`, `datetime`, `list[str]`, `Optional`, `Enum`.

5.  **Design Repository Methods:**
   - CRUD for campaigns
   - CRUD for message dispatches
   - Track message status updates
   - Record patient confirmation
   - Audit logging for LGPD compliance
   - Methods should be async (standard for modern FastAPI/SQLAlchemy 2.0)
   - Use `AsyncSession`
   - Implement filtering by CPF/CNS, CID-10, CIAP-2, SOAP notes, date ranges, status.

6.  **Draft Code - `backend/app/repositories/campanhas_repo.py`:**
   *(Mental Refinement during drafting)*
   - Need imports: `sqlalchemy`, `pydantic`, `enum`, `datetime`, `uuid`, `typing`, `asyncpg` (or just standard `sqlalchemy.ext.asyncio`)
   - I'll use `sqlalchemy.orm.mapped_column`, `sqlalchemy.ForeignKey`, `sqlalchemy.Enum`, `sqlalchemy.JSON`, `sqlalchemy.Text`
   - I'll define enums: `CampanhaStatus`, `MensagemStatus`, `AcaoAuditoria`
   - I'll make sure Pydantic v2 uses `model_config = ConfigDict(from_attributes=True)`
   - Repository class will take `AsyncSession` in methods or as init. I'll use method-level session injection for flexibility.
   - I'll add type hints strictly.
   - I'll include docstrings and comments.

   Let's write it out carefully.

   ```python
   # Arquivo: backend/app/repositories/campanhas_repo.py
   from __future__ import annotations
   import enum
   from datetime import datetime, timezone
   from typing import Optional, Sequence
   from uuid import UUID

   from pydantic import BaseModel, ConfigDict, Field, field_validator
   from sqlalchemy import (
       String,
       Text,
       DateTime,
       Enum,
       JSON,
       ForeignKey,
       select,
       update,
       func,
   )
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

   # ... (define base, enums, models, schemas, repo)
   ```

   I need to be careful with SQLAlchemy 2.0 syntax. `DeclarativeBase` is correct. `mapped_column` is correct.
   I'll define the models first, then Pydantic schemas, then the repository.

   **Models:**
   - `Base`
   - `Campanha`
   - `MensagemDisparo`
   - `LogAuditoriaLGPD`

   **Schemas:**
   - `CampanhaCreate`, `CampanhaRead`
   - `MensagemDisparoCreate`, `MensagemDisparoRead`
   - `LogAuditoriaLGPDCreate`, `LogAuditoriaLGPDRead`

   **Repository:**
   - `CampanhasRepository`
   - Methods: `criar_campanha`, `obter_campanha`, `atualizar_status_campanha`, `registrar_disparo`, `atualizar_status_disparo`, `confirmar_paciente`, `registrar_auditoria_lgpd`, `listar_disparos_por_campanha`, `filtrar_por_cid10_ciap2`, `obter_log_auditoria`

   I'll ensure strict typing and Pydantic v2 compliance. I'll use `datetime.now(timezone.utc)` for timestamps.

   **Testing Requirements:**
   - The prompt says "Manter conformidade total e cobertura de testes automatizados com pytest."
   - I need to provide the test file as well. I'll create `backend/app/tests/test_campanhas_repo.py` with comprehensive pytest tests using `pytest-asyncio`, `pytest-mock`, and `pytest-asyncio` fixtures for async session. I'll use `in-memory SQLite` for testing.

   Let's structure the response carefully. I'll provide:
   1. `backend/app/repositories/campanhas_repo.py`
   2. `backend/app/tests/test_campanhas_repo.py`
   I'll make sure both are complete and executable.

   **Detailed Implementation Plan:**

   *campanhas_repo.py:*
   - Imports
   - Enums (CampanhaStatus, MensagemStatus, AcaoAuditoria)
   - Base class
   - ORM Models (Campanha, MensagemDisparo, LogAuditoriaLGPD)
   - Pydantic Schemas (Create/Read for each)
   - Repository class with async methods
   - Strict typing, docstrings, comments

   *test_campanhas_repo.py:*
   - Imports (pytest, asyncio, mock, sqlalchemy, etc.)
   - Fixtures: `async_engine`, `async_session`, `db_session`
   - Test classes/functions for each repo method
   - Assertions for status updates, confirmation, audit logs, filtering
   - Use `pytest-asyncio` mode

   I'll write the code now, ensuring it matches all constraints.

   *Self-Correction/Refinement during thought:*
   - SQLAlchemy 2.0 uses `mapped_column` and `ForeignKey`. I'll use that.
   - Pydantic v2 uses `model_config = ConfigDict(from_attributes=True)`.
   - I'll use `uuid` for primary keys.
   - I'll make sure the repository methods are properly typed and async.
   - For testing, I'll use `pytest-asyncio` and `sqlalchemy.ext.asyncio.sessionmaker`. I'll provide a complete test setup.
   - I'll add comments explaining SUS/APS standards integration (CID-10, CIAP-2, SOAP, CNS/CPF).
   - I'll ensure the code is production-ready and follows best practices.

   Let's draft it carefully. 
   I'll structure the output exactly as requested.
   I'll make sure the code is complete and executable.
   I'll add necessary imports and type hints.
   I'll handle the async session properly in tests.
   I'll ensure Pydantic v2 and SQLAlchemy 2.0 syntax is correct.
   I'll include LGPD audit tracking explicitly.
   I'll include SUS/APS fields explicitly.

   Proceeding to generate. 
   Structure:
   ```python
   # Arquivo: backend/app/repositories/campanhas_repo.py
   ... code ...
   ```
   ```python
   # Arquivo: backend/app/tests/test_campanhas_repo.py
   ... code ...
   ```
   I'll make sure the code is self-contained and follows all constraints.
   I'll double-check SQLAlchemy 2.0 syntax: `Mapped`, `mapped_column`, `ForeignKey`, `select`, `update`, `AsyncSession`.
   I'll double-check Pydantic v2: `BaseModel`, `ConfigDict`, `Field`, `model_validator`, `computed_field`.
   I'll ensure strict typing: `Optional`, `Sequence`, `list`, `dict`, `str`, `int`, `datetime`, `UUID`.
   I'll add comments for SUS/APS standards.
   I'll write comprehensive pytest tests.
   All good. Generating. 
   *Self-Correction/Verification during drafting:*
   - SQLAlchemy 2.0 `mapped_column` requires `sqlalchemy>=2.0.0`. I'll assume it's installed.
   - Pydantic v2 `ConfigDict` is correct.
   - I'll use `sqlalchemy.Enum` with `native_enum=False` for better cross-DB compatibility, or just let it default. I'll specify `name="campanha_status"` etc.
   - I'll make sure the repository methods handle transactions properly (though in async, the caller usually manages commit/rollback, but I'll add `await session.commit()` and `await session.flush()` as appropriate).
   - I'll add `@asynccontextmanager` or just standard async methods. Standard is fine.
   - I'll ensure the test file uses `pytest-asyncio` correctly with `asyncio_mode = "auto"` or explicit fixtures. I'll provide a standard async test setup.
   - I'll make sure the code is complete and ready to run.

   Let's write it out. 
   *Output Generation matches the response.* 
   I will carefully construct the code blocks now. 
   All constraints met. Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards, LGPD audit, pytest coverage. Strict typing. Complete and executable. File paths specified.✅
   Proceeds. 
   [Output Generation] -> *See response.* 
   *(Self-Correction/Note during thought)*: I should make sure the SQLAlchemy models use `Mapped` and `mapped_column` correctly. I'll use `sqlalchemy.orm.Mapped` and `sqlalchemy.orm.mapped_column`. I'll also ensure Pydantic schemas use `from_attributes=True`. I'll add proper type hints. I'll make the repository methods async. I'll provide a complete test suite. All good. 
   Output matches the final response. 
   [Done.] 
   *Output Generation* (matches the final response)
   ```python
   # Arquivo: backend/app/repositories/campanhas_repo.py
   ...
   ```
   ```python
   # Arquivo: backend/app/tests/test_campanhas_repo.py
   ...
   ```
   All constraints satisfied. Ready. 
   *Proceeds.*
Aqui está a implementação completa, seguindo rigorosamente as diretrizes de arquitetura, tipagem estrita, padrões SUS/APS, conformidade LGPD e cobertura de testes com pytest.

```python
# Arquivo: backend/app/repositories/campanhas_repo.py
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Enum,
    JSON,
    ForeignKey,
    select,
    update,
    func,
    and_,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase


# ---------------------------------------------------------------------------
# Enums & Padrões SUS/APS
# ---------------------------------------------------------------------------
class CampanhaStatus(str, enum.Enum):
    RASCUNHO = "rascunho"
    ATIVA = "ativa"
    PAUSADA = "pausada"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class MensagemStatus(str, enum.Enum):
    AGUARDANDO_ENVIO = "aguardando_envio"
    ENVIADA = "enviada"
    ENTREGUE = "entregue"
    CONFIRMADA = "confirmada"
    FALHA = "falha"


class AcaoAuditoria(str, enum.Enum):
    CONSENTIMENTO_CONCEDIDO = "consentimento_concedido"
    CONSENTIMENTO_REVOGADO = "consentimento_revogado"
    DADOS_EXPORTADOS = "dados_exportados"
    DADOS_EXCLUIDOS = "dados_excluidos"
    ACESSO_REALIZADO = "acesso_realizado"
    AUDITORIA_REALIZADA = "auditoria_realizada"


# ---------------------------------------------------------------------------
# Base & Modelos ORM (SQLAlchemy 2.0)
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


class Campanha(Base):
    __tablename__ = "campanhas"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[CampanhaStatus] = mapped_column(
        Enum(CampanhaStatus, name="campanha_status_enum"), default=CampanhaStatus.RASCUNHO
    )
    data_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    data_fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    disparos: Mapped[list[MensagemDisparo]] = relationship(back_populates="campanha", cascade="all, delete-orphan")
    logs: Mapped[list[LogAuditoriaLGPD]] = relationship(back_populates="campanha", cascade="all, delete-orphan")


class MensagemDisparo(Base):
    __tablename__ = "mensagens_disparo"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    campanha_id: Mapped[UUID] = mapped_column(ForeignKey("campanhas.id", ondelete="CASCADE"), index=True)
    
    # Identificação SUS/APS
    paciente_cpf: Mapped[str] = mapped_column(String(14), index=True)
    paciente_cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    
    conteudo: Mapped[str] = mapped_column(Text)
    status: Mapped[MensagemStatus] = mapped_column(
        Enum(MensagemStatus, name="mensagem_status_enum"), default=MensagemStatus.AGUARDANDO_ENVIO
    )
    
    # Padrões Clínicos SUS/APS
    codigos_cid10: Mapped[list[str]] = mapped_column(JSON, default=list)
    codigos_ciap2: Mapped[list[str]] = mapped_column(JSON, default=list)
    notas_soap: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    enviado_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmado_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    campanha: Mapped[Campanha] = relationship(back_populates="disparos")
    logs: Mapped[list[LogAuditoriaLGPD]] = relationship(back_populates="mensagem", cascade="all, delete-orphan")


class LogAuditoriaLGPD(Base):
    __tablename__ = "logs_auditoria_lgpd"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    campanha_id: Mapped[UUID] = mapped_column(ForeignKey("campanhas.id", ondelete="SET NULL"), nullable=True)
    mensagem_disparo_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("mensagens_disparo.id", ondelete="SET NULL"), nullable=True)
    
    acao: Mapped[AcaoAuditoria] = mapped_column(Enum(AcaoAuditoria, name="acao_auditoria_enum"))
    agente: Mapped[str] = mapped_column(String(100))
    ip_origem: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)