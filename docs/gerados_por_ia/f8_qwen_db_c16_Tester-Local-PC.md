Here's a thinking process:

1.  **Analyze User Input:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for a "Health Campaigns and Dispatch History Repository (C16)" for the MedIA project.
   - **Requirements:**
     - Track sent messages, patient confirmation status, and data protection audit logs.
     - Architecture guidelines: Private care/insurance (TISS ANS 4.01 / DMED Receita Federal), Primary Care/Family Health methodology.
     - No mandatory SUS/SISAB or IoT code.
     - Clean Python 3.12, strict Pydantic v2 typing, SQLAlchemy 2.0.
     - Production code only in `backend/app/`, tests only in `backend/tests/`.
     - Preserve 100% green test suite.
     - Provide complete, executable code. Specify file paths in code blocks.
   - **Implicit Needs:** Since I need to provide a complete, executable solution that preserves a test suite, I should also create the corresponding test file (`backend/tests/test_campanhas_repo.py`) and possibly necessary supporting files (models, schemas, base setup) if they don't exist, but the prompt specifically asks for `backend/app/repositories/campanhas_repo.py`. I'll focus on that but ensure it's self-contained enough to be tested. I'll also provide the test file to satisfy the "preserve 100% green test suite" requirement.

2.  **Deconstruct Requirements for `campanhas_repo.py`:**
   - **Domain:** Health Campaigns (Campanhas de Saúde) & Dispatch History (Histórico de Disparos)
   - **Key Features:**
     - Track sent messages (disparos/mensagens enviadas)
     - Patient confirmation status (status de confirmação pelo paciente)
     - Data protection audit log (log de auditoria de proteção de dados - LGPD)
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0
   - **Architecture:** Repository pattern, strict typing, production-ready.

3.  **Design Data Models (SQLAlchemy 2.0):**
   - `Campanha` (Campaign): id, name, description, status, created_at, updated_at
   - `Disparo` (Dispatch/Send): id, campanha_id, paciente_id, mensagem, status_envio, criado_em
   - `ConfirmacaoPaciente` (Patient Confirmation): id, disparo_id, confirmado, confirmado_em, metadados
   - `LogAuditoriaLGPD` (Audit Log): id, entidade_tipo, entidade_id, acao, detalhes, realizado_por, criado_em
   - Relationships: Campaign -> Dispatches -> Confirmations. Audit log can be linked to any entity.

4.  **Design Pydantic Schemas (v2):**
   - `CampanhaCreate`, `CampanhaRead`
   - `DisparoCreate`, `DisparoRead`
   - `ConfirmacaoPacienteCreate`, `ConfirmacaoPacienteRead`
   - `LogAuditoriaLGPDCreate`, `LogAuditoriaLGPDRead`
   - Use `ConfigDict` for strict typing, `model_validator` if needed.

5.  **Design Repository Class (`CampanhasRepository`):**
   - Constructor takes a SQLAlchemy async session (or sync, but async is modern). I'll use `AsyncSession` for modern stack, but will make it compatible. Actually, SQLAlchemy 2.0 often uses `Session` or `AsyncSession`. I'll stick to `AsyncSession` as it's standard for modern FastAPI/Python 3.12, but I'll type it properly.
   - Methods:
     - `criar_campanha(campanha: CampanhaCreate) -> Campanha`
     - `obter_campanha(campanha_id: UUID) -> Optional[Campanha]`
     - `registrar_disparo(disparo: DisparoCreate) -> Disparo`
     - `obter_disparos_por_campanha(campanha_id: UUID) -> List[Disparo]`
     - `atualizar_status_confirmacao(confirmacao: ConfirmacaoPacienteCreate) -> ConfirmacaoPaciente`
     - `registrar_log_auditoria(lgpd: LogAuditoriaLGPDCreate) -> LogAuditoriaLGPD`
     - `obter_logs_auditoria(entidade_tipo: str, entidade_id: UUID) -> List[LogAuditoriaLGPD]`
   - All methods should be type-hinted and use Pydantic models for input/output.
   - Use SQLAlchemy 2.0 syntax: `select()`, `insert()`, `update()`, `session.execute()`, `session.commit()`.

6.  **Draft Code (Mental Refinement):**
   I'll structure the file with imports, models, schemas, and repository class. I'll ensure strict typing and Pydantic v2 compliance.

   *Models:*
   ```python
   from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum as SAEnum
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
   from sqlalchemy.dialects.postgresql import UUID
   import uuid
   from datetime import datetime
   from enum import Enum as PyEnum

   class Base(DeclarativeBase):
       pass

   class StatusCampanha(PyEnum):
       RASCUNHO = "rascunho"
       ATIVA = "ativa"
       PAUSADA = "pausada"
       CONCLUIDA = "concluida"

   class StatusEnvio(PyEnum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       FALHA = "falha"
       LIDO = "lido"

   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       nome: Mapped[str] = mapped_column(String(255), nullable=False)
       descricao: Mapped[str] = mapped_column(Text, nullable=True)
       status: Mapped[StatusCampanha] = mapped_column(SAEnum(StatusCampanha), default=StatusCampanha.RASCUNHO)
       criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
       disparos: Mapped[list["Disparo"]] = relationship(back_populates="campanha", cascade="all, delete-orphan")

   class Disparo(Base):
       __tablename__ = "disparos"
       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       campanha_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campanhas.id"), nullable=False)
       paciente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
       mensagem: Mapped[str] = mapped_column(Text, nullable=False)
       status_envio: Mapped[StatusEnvio] = mapped_column(SAEnum(StatusEnvio), default=StatusEnvio.PENDENTE)
       criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       campanha: Mapped["Campanha"] = relationship(back_populates="disparos")
       confirmacao: Mapped["ConfirmacaoPaciente"] = relationship(back_populates="disparo", uselist=False, cascade="all, delete-orphan")

   class ConfirmacaoPaciente(Base):
       __tablename__ = "confirmacoes_paciente"
       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       disparo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("disparos.id"), nullable=False)
       confirmado: Mapped[bool] = mapped_column(Boolean, default=False)
       confirmado_em: Mapped[datetime] = mapped_column(DateTime, nullable=True)
       metadados: Mapped[str] = mapped_column(Text, nullable=True)
       disparo: Mapped["Disparo"] = relationship(back_populates="confirmacao")

   class LogAuditoriaLGPD(Base):
       __tablename__ = "logs_auditoria_lgpd"
       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       entidade_tipo: Mapped[str] = mapped_column(String(50), nullable=False) # 'CAMPAHNA', 'DISPARO', 'PACIENTE'
       entidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
       acao: Mapped[str] = mapped_column(String(100), nullable=False) # 'CRIAR', 'ACESSAR', 'MODIFICAR', 'EXCLUIR'
       detalhes: Mapped[str] = mapped_column(Text, nullable=True)
       realizado_por: Mapped[str] = mapped_column(String(255), nullable=False)
       criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
   ```

   *Schemas (Pydantic v2):*
   ```python
   from pydantic import BaseModel, ConfigDict, Field, field_validator
   from datetime import datetime
   from typing import Optional
   import uuid

   class CampanhaCreate(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True)
       nome: str = Field(..., min_length=1, max_length=255)
       descricao: Optional[str] = None

   class CampanhaRead(CampanhaCreate):
       id: uuid.UUID
       status: str
       criado_em: datetime
       atualizado_em: datetime

   class DisparoCreate(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True)
       campanha_id: uuid.UUID
       paciente_id: uuid.UUID
       mensagem: str = Field(..., min_length=1)

   class DisparoRead(DisparoCreate):
       id: uuid.UUID
       status_envio: str
       criado_em: datetime

   class ConfirmacaoPacienteCreate(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True)
       disparo_id: uuid.UUID
       confirmado: bool = False
       metadados: Optional[str] = None

   class ConfirmacaoPacienteRead(ConfirmacaoPacienteCreate):
       id: uuid.UUID
       confirmado_em: Optional[datetime] = None

   class LogAuditoriaLGPDCreate(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True)
       entidade_tipo: str = Field(..., min_length=1, max_length=50)
       entidade_id: uuid.UUID
       acao: str = Field(..., min_length=1, max_length=100)
       detalhes: Optional[str] = None
       realizado_por: str = Field(..., min_length=1, max_length=255)

   class LogAuditoriaLGPDRead(LogAuditoriaLGPDCreate):
       id: uuid.UUID
       criado_em: datetime
   ```

   *Repository:*
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, update
   from typing import List, Optional
   import uuid
   from datetime import datetime

   class CampanhasRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def criar_campanha(self, data: CampanhaCreate) -> CampanhaRead:
           campanha = Campanha(nome=data.nome, descricao=data.descricao)
           self.session.add(campanha)
           await self.session.flush()
           await self.session.refresh(campanha)
           return CampanhaRead.model_validate(campanha)

       async def obter_campanha(self, campanha_id: uuid.UUID) -> Optional[CampanhaRead]:
           stmt = select(Campanha).where(Campanha.id == campanha_id)
           result = await self.session.execute(stmt)
           campanha = result.scalar_one_or_none()
           return CampanhaRead.model_validate(campanha) if campanha else None

       async def registrar_disparo(self, data: DisparoCreate) -> DisparoRead:
           disparo = Disparo(campanha_id=data.campanha_id, paciente_id=data.paciente_id, mensagem=data.mensagem)
           self.session.add(disparo)
           await self.session.flush()
           await self.session.refresh(disparo)
           return DisparoRead.model_validate(disparo)

       async def obter_disparos_por_campanha(self, campanha_id: uuid.UUID) -> List[DisparoRead]:
           stmt = select(Disparo).where(Disparo.campanha_id == campanha_id)
           result = await self.session.execute(stmt)
           return [DisparoRead.model_validate(d) for d in result.scalars().all()]

       async def atualizar_status_confirmacao(self, data: ConfirmacaoPacienteCreate) -> ConfirmacaoPacienteRead:
           stmt = (
               update(ConfirmacaoPaciente)
               .where(ConfirmacaoPaciente.disparo_id == data.disparo_id)
               .values(confirmado=data.confirmado, confirmado_em=datetime.utcnow(), metadados=data.metadados)
           )
           await self.session.execute(stmt)
           # Fetch updated record
           stmt_get = select(ConfirmacaoPaciente).where(ConfirmacaoPaciente.disparo_id == data.disparo_id)
           result = await self.session.execute(stmt_get)
           confirmacao = result.scalar_one_or_none()
           return ConfirmacaoPacienteRead.model_validate(confirmacao)

       async def registrar_log_auditoria(self, data: LogAuditoriaLGPDCreate) -> LogAuditoriaLGPDRead:
           log = LogAuditoriaLGPD(
               entidade_tipo=data.entidade_tipo,
               entidade_id=data.entidade_id,
               acao=data.acao,
               detalhes=data.detalhes,
               realizado_por=data.realizado_por
           )
           self.session.add(log)
           await self.session.flush()
           await self.session.refresh(log)
           return LogAuditoriaLGPDRead.model_validate(log)

       async def obter_logs_auditoria(self, entidade_tipo: str, entidade_id: uuid.UUID) -> List[LogAuditoriaLGPDRead]:
           stmt = select(LogAuditoriaLGPD).where(
               LogAuditoriaLGPD.entidade_tipo == entidade_tipo,
               LogAuditoriaLGPD.entidade_id == entidade_id
           ).order_by(LogAuditoriaLGPD.criado_em.desc())
           result = await self.session.execute(stmt)
           return [LogAuditoriaLGPDRead.model_validate(l) for l in result.scalars().all()]
   ```

7.  **Check against Requirements:**
   - *Python 3.12, strict Pydantic v2, SQLAlchemy 2.0:* Yes. Used `Mapped`, `mapped_column`, `select()`, `update()`, Pydantic `ConfigDict`, `Field`, `model_validate`.
   - *Track sent messages, confirmation status, audit log:* Yes, covered by `Disparo`, `ConfirmacaoPaciente`, `LogAuditoriaLGPD` models and repo methods.
   - *Architecture guidelines:* MedIA context, TISS/DMED mentioned in comments/docstrings. No SUS/SISAB or IoT.
   - *Production code in `backend/app/`, tests in `backend/tests/`:* I'll provide the repo file and a corresponding test file to ensure it's executable and preserves a green suite.
   - *Complete & executable:* I'll structure the response with both files. I'll make sure imports are correct and the code is self-contained. I'll add necessary docstrings and type hints.

   *Self-Correction/Refinement during thought:*
   - SQLAlchemy 2.0 `mapped_column` requires `sqlalchemy.orm`. I used it correctly.
   - Pydantic v2 `ConfigDict` is correct.
   - The repository uses `AsyncSession`. I should note that or make it compatible with sync if needed, but async is standard for Python 3.12/FastAPI. I'll stick to async but add a comment.
   - I need to ensure the test file actually runs and passes. I'll use `pytest`, `pytest-asyncio`, and `sqlalchemy.ext.asyncio.InMemoryBackend` (or `aiosqlite`/`sqlite` for simplicity in tests). Actually, for a clean test suite, I'll use `pytest-asyncio` with an in-memory SQLite database via `sqlalchemy.ext.asyncio.sessionmaker` and `AsyncSession`.
   - I'll create a minimal test file that sets up an async engine, creates tables, and tests the repository methods. This ensures the "preserve 100% green test suite" requirement is met.
   - I'll add proper docstrings referencing MedIA, TISS ANS 4.01, DMED, LGPD.
   - I'll ensure strict typing: `from typing import List, Optional, AsyncIterator` etc.
   - I'll check Pydantic v2 syntax: `model_config = ConfigDict(...)` is correct. `Field(...)` is correct. `model_validate()` is correct.
   - I'll check SQLAlchemy 2.0 syntax: `select()`, `update()`, `mapped_column`, `relationship` are correct.
   - I'll make sure the code is production-ready: error handling, type hints, docstrings, LGPD compliance comments.

   Let's draft the test file mentally to ensure compatibility:
   ```python
   import pytest
   import asyncio
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   from app.repositories.campanhas_repo import CampanhasRepository, CampanhaCreate, DisparoCreate, ConfirmacaoPacienteCreate, LogAuditoriaLGPDCreate
   from app.models.base import Base # I'll need to define Base in the repo file or import it. I'll put Base in the same file for simplicity, or import it. The prompt says `backend/app/repositories/campanhas_repo.py`, so I'll put models there.
   ```
   Actually, it's better to keep models and schemas in the same file for this specific task, or import them. I'll keep them in the same file as requested.

   I will structure the response with two files:
   1