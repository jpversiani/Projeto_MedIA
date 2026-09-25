Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for the MedIA project.
   - **Requirements:**
     - Models and methods for recording: tracking sent messages, patient confirmation status, data protection audit log.
     - Context: MedIA is for private care and health plans (TISS ANS 4.01 / DMED Receita Federal), Primary Care / Family Health clinical method.
     - Constraints: No mandatory SUS/SISAB or IoT peripheral code. Clean Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0. Production code only in `backend/app/`, tests only in `backend/tests/`. Preserve 100% of the test suite (green).
     - Output: Complete, executable code. Specify file paths clearly.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/campanhas_repo.py`
   - **Domain:** Health Campaigns (Campanhas de Saúde)
   - **Key Features:**
     - Message sending tracking
     - Patient confirmation status
     - Data protection audit log
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0
   - **Architecture/Constraints:** Strict typing, production code in `backend/app/`, no SUS/IoT code, maintain test compatibility.

3.  **Design Models (Pydantic v2 & SQLAlchemy 2.0):**
   - Need SQLAlchemy models for the database.
   - Need Pydantic schemas for validation/serialization.
   - Key entities:
     - `Campanha` (Campaign)
     - `DisparoCampanha` (Campaign Dispatch/Sending)
     - `ConfirmacaoPaciente` (Patient Confirmation)
     - `LogAuditoriaProtecaoDados` (Data Protection Audit Log)
   - Let's define them carefully with SQLAlchemy 2.0 syntax (declarative base, mapped columns, relationships).
   - Pydantic v2 schemas will mirror these for API/input validation.

   *SQLAlchemy Models:*
   ```python
   from datetime import datetime
   from typing import Optional
   from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Integer, Enum as SAEnum
   from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
   import enum

   class Base(DeclarativeBase):
       pass

   class StatusDisparo(str, enum.Enum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       FALHA = "falha"
       CONFIRMADO = "confirmado"
       NAO_CONFIRMADO = "nao_confirmado"

   class TipoAcesso(str, enum.Enum):
       AUTENTICADO = "autenticado"
       ANONIMO = "anonimo"
       SISTEMA = "sistema"

   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[int] = mapped_column(primary_key=True)
       nome: Mapped[str] = mapped_column(String(255))
       descricao: Mapped[Optional[str]] = mapped_column(Text)
       status: Mapped[StatusDisparo] = mapped_column(SAEnum(StatusDisparo), default=StatusDisparo.PENDENTE)
       criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

       disparos = relationship("DisparoCampanha", back_populates="campanha", cascade="all, delete-orphan")
       confirmacoes = relationship("ConfirmacaoPaciente", back_populates="campanha", cascade="all, delete-orphan")
       logs = relationship("LogAuditoriaProtecaoDados", back_populates="campanha", cascade="all, delete-orphan")

   class DisparoCampanha(Base):
       __tablename__ = "disparos_campanhas"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"))
       paciente_id: Mapped[str] = mapped_column(String(50)) # Could be UUID or CPF masked
       canal: Mapped[str] = mapped_column(String(50)) # SMS, Email, App, etc.
       status: Mapped[StatusDisparo] = mapped_column(SAEnum(StatusDisparo), default=StatusDisparo.PENDENTE)
       mensagem_hash: Mapped[Optional[str]] = mapped_column(String(64)) # SHA-256 for integrity
       enviado_em: Mapped[Optional[datetime]] = mapped_column(DateTime)
       falha_razao: Mapped[Optional[str]] = mapped_column(String(500))

       campanha = relationship("Campanha", back_populates="disparos")

   class ConfirmacaoPaciente(Base):
       __tablename__ = "confirmacoes_pacientes"
       id: Mapped[int] = mapped_column(primary_key=True)
       disparo_id: Mapped[int] = mapped_column(ForeignKey("disparos_campanhas.id"))
       paciente_id: Mapped[str] = mapped_column(String(50))
       confirmado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       metodo_confirmacao: Mapped[str] = mapped_column(String(50)) # Link, PIN, App, etc.
       ip_origem: Mapped[Optional[str]] = mapped_column(String(45))
       user_agent: Mapped[Optional[str]] = mapped_column(String(255))

       disparo = relationship("DisparoCampanha", back_populates="confirmacoes")

   class LogAuditoriaProtecaoDados(Base):
       __tablename__ = "logs_auditoria_protecao_dados"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"))
       acao: Mapped[str] = mapped_column(String(100)) # LEITURA, EXPORTACAO, DESCARTAR, ACESSO
       entidade_alvo: Mapped[str] = mapped_column(String(100)) # PACIENTE, CAMPAHNA, SISTEMA
       entidade_id: Mapped[Optional[str]] = mapped_column(String(50))
       responsavel: Mapped[Optional[str]] = mapped_column(String(100))
       ip_origem: Mapped[Optional[str]] = mapped_column(String(45))
       timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       detalhes: Mapped[Optional[str]] = mapped_column(Text)

       campanha = relationship("Campanha", back_populates="logs")
   ```

   *Pydantic v2 Schemas:*
   ```python
   from pydantic import BaseModel, Field, ConfigDict
   from typing import Optional
   from datetime import datetime

   class CampanhaBase(BaseModel):
       nome: str = Field(..., min_length=1, max_length=255)
       descricao: Optional[str] = None

   class CampanhaCreate(CampanhaBase):
       pass

   class CampanhaRead(CampanhaBase):
       model_config = ConfigDict(from_attributes=True)
       id: int
       status: str
       criado_em: datetime
       atualizado_em: datetime

   class DisparoCampanhaBase(BaseModel):
       paciente_id: str = Field(..., min_length=1, max_length=50)
       canal: str = Field(..., min_length=1, max_length=50)
       status: str = Field(default="pendente")
       mensagem_hash: Optional[str] = None

   class DisparoCampanhaCreate(DisparoCampanhaBase):
       campanha_id: int

   class DisparoCampanhaRead(DisparoCampanhaBase):
       model_config = ConfigDict(from_attributes=True)
       id: int
       campanha_id: int
       enviado_em: Optional[datetime] = None
       falha_razao: Optional[str] = None

   class ConfirmacaoPacienteBase(BaseModel):
       paciente_id: str
       metodo_confirmacao: str
       ip_origem: Optional[str] = None
       user_agent: Optional[str] = None

   class ConfirmacaoPacienteCreate(ConfirmacaoPacienteBase):
       disparo_id: int

   class ConfirmacaoPacienteRead(ConfirmacaoPacienteBase):
       model_config = ConfigDict(from_attributes=True)
       id: int
       disparo_id: int
       confirmado_em: datetime

   class LogAuditoriaBase(BaseModel):
       acao: str
       entidade_alvo: str
       entidade_id: Optional[str] = None
       responsavel: Optional[str] = None
       ip_origem: Optional[str] = None
       detalhes: Optional[str] = None

   class LogAuditoriaCreate(LogAuditoriaBase):
       campanha_id: int

   class LogAuditoriaRead(LogAuditoriaBase):
       model_config = ConfigDict(from_attributes=True)
       id: int
       campanha_id: int
       timestamp: datetime
   ```

4.  **Design Repository Methods:**
   - Need async methods for CRUD and specific tracking/audit operations.
   - Use SQLAlchemy 2.0 async session pattern.
   - Methods needed:
     - `criar_campanha`
     - `registrar_disparo`
     - `atualizar_status_disparo`
     - `registrar_confirmacao_paciente`
     - `registrar_log_auditoria`
     - `obter_historico_campanha` (for tracking)
   - I'll structure it as a class `CampanhasRepository` with async methods.
   - I'll use `AsyncSession` from `sqlalchemy.ext.asyncio`.

   *Repository Implementation Draft:*
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, update, func
   from typing import List, Optional
   from datetime import datetime
   import uuid

   class CampanhasRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def criar_campanha(self, schema: CampanhaCreate) -> CampanhaRead:
           nova = Campanha(
               nome=schema.nome,
               descricao=schema.descricao,
               status=StatusDisparo.PENDENTE,
               criado_em=datetime.utcnow(),
               atualizado_em=datetime.utcnow()
           )
           self.session.add(nova)
           await self.session.flush()
           await self.session.refresh(nova)
           return self._map_campanha_to_read(nova)

       async def registrar_disparo(self, schema: DisparoCampanhaCreate) -> DisparoCampanhaRead:
           novo = DisparoCampanha(
               campanha_id=schema.campanha_id,
               paciente_id=schema.paciente_id,
               canal=schema.canal,
               status=StatusDisparo.PENDENTE,
               mensagem_hash=schema.mensagem_hash or uuid.uuid4().hex,
               enviado_em=datetime.utcnow()
           )
           self.session.add(novo)
           await self.session.flush()
           await self.session.refresh(novo)
           return self._map_disparo_to_read(novo)

       async def atualizar_status_disparo(self, disparo_id: int, status: StatusDisparo, falha_razao: Optional[str] = None) -> None:
           stmt = (
               update(DisparoCampanha)
               .where(DisparoCampanha.id == disparo_id)
               .values(status=status, enviado_em=datetime.utcnow(), falha_razao=falha_razao)
           )
           await self.session.execute(stmt)

       async def registrar_confirmacao_paciente(self, schema: ConfirmacaoPacienteCreate) -> ConfirmacaoPacienteRead:
           nova = ConfirmacaoPaciente(
               disparo_id=schema.disparo_id,
               paciente_id=schema.paciente_id,
               metodo_confirmacao=schema.metodo_confirmacao,
               ip_origem=schema.ip_origem,
               user_agent=schema.user_agent,
               confirmado_em=datetime.utcnow()
           )
           self.session.add(nova)
           await self.session.flush()
           await self.session.refresh(nova)
           return self._map_confirmacao_to_read(nova)

       async def registrar_log_auditoria(self, schema: LogAuditoriaCreate) -> LogAuditoriaRead:
           novo = LogAuditoriaProtecaoDados(
               campanha_id=schema.campanha_id,
               acao=schema.acao,
               entidade_alvo=schema.entidade_alvo,
               entidade_id=schema.entidade_id,
               responsavel=schema.responsavel,
               ip_origem=schema.ip_origem,
               timestamp=datetime.utcnow(),
               detalhes=schema.detalhes
           )
           self.session.add(novo)
           await self.session.flush()
           await self.session.refresh(novo)
           return self._map_log_to_read(novo)

       async def obter_historico_campanha(self, campanha_id: int) -> dict:
           stmt_disparos = select(DisparoCampanha).where(DisparoCampanha.campanha_id == campanha_id)
           result_disparos = await self.session.execute(stmt_disparos)
           disparos = result_disparos.scalars().all()

           stmt_confirmacoes = select(ConfirmacaoPaciente).where(ConfirmacaoPaciente.disparo_id.in_([d.id for d in disparos]))
           result_confirmacoes = await self.session.execute(stmt_confirmacoes)
           confirmacoes = result_confirmacoes.scalars().all()

           stmt_logs = select(LogAuditoriaProtecaoDados).where(LogAuditoriaProtecaoDados.campanha_id == campanha_id)
           result_logs = await self.session.execute(stmt_logs)
           logs = result_logs.scalars().all()

           return {
               "campanha_id": campanha_id,
               "disparos": [self._map_disparo_to_read(d) for d in disparos],
               "confirmacoes": [self._map_confirmacao_to_read(c) for c in confirmacoes],
               "logs_auditoria": [self._map_log_to_read(l) for l in logs]
           }

       # Helper mappers to convert SQLAlchemy models to Pydantic schemas
       @staticmethod
       def _map_campanha_to_read(model: Campanha) -> CampanhaRead:
           return CampanhaRead(
               id=model.id,
               nome=model.nome,
               descricao=model.descricao,
               status=model.status.value,
               criado_em=model.criado_em,
               atualizado_em=model.atualizado_em
           )
       @staticmethod
       def _map_disparo_to_read(model: DisparoCampanha) -> DisparoCampanhaRead:
           return DisparoCampanhaRead(
               id=model.id,
               campanha_id=model.campanha_id,
               paciente_id=model.paciente_id,
               canal=model.canal,
               status=model.status.value,
               mensagem_hash=model.mensagem_hash,
               enviado_em=model.enviado_em,
               falha_razao=model.falha_razao
           )
       @staticmethod
       def _map_confirmacao_to_read(model: ConfirmacaoPaciente) -> ConfirmacaoPacienteRead:
           return ConfirmacaoPacienteRead(
               id=model.id,
               disparo_id=model.disparo_id,
               paciente_id=model.paciente_id,
               metodo_confirmacao=model.metodo_confirmacao,
               ip_origem=model.ip_origem,
               user_agent=model.user_agent,
               confirmado_em=model.confirmado_em
           )
       @staticmethod
       def _map_log_to_read(model: LogAuditoriaProtecaoDados) -> LogAuditoriaRead:
           return LogAuditoriaRead(
               id=model.id,
               campanha_id=model.campanha_id,
               acao=model.acao,
               entidade_alvo=model.entidade_alvo,
               entidade_id=model.entidade_id,
               responsavel=model.responsavel,
               ip_origem=model.ip_origem,
               timestamp=model.timestamp,
               detalhes=model.detalhes
           )
   ```

5.  **Refine & Check Constraints:**
   - *Python 3.12, strict typing:* Used `Mapped`, `mapped_column`, type hints everywhere. Pydantic v2 `ConfigDict(from_attributes=True)`.
   - *SQLAlchemy 2.0:* Used `select`, `update`, `AsyncSession`, `DeclarativeBase`, `mapped_column`.
   - *Domain:* Tracks sent messages, confirmation status, audit log. Matches requirements.
   - *No SUS/IoT:* Explicitly avoided.
   - *File path:* `backend/app/repositories/campanhas_repo.py`
   - *Test compatibility:* The repository is self-contained. I should ensure it doesn't break existing tests by keeping imports standard and avoiding side effects. I'll add necessary imports and ensure the code is ready to be dropped in.
   - *Pydantic v2:* Used `Field`, `ConfigDict`, `from_attributes`.
   - *Audit/Compliance:* Added fields for IP, user agent, hash, responsible party, action type, target entity. Matches LGPD/DMED/ANS requirements implicitly through structure.
   - *Structure:* I'll organize the file logically: Imports -> Enums -> SQLAlchemy Models -> Pydantic Schemas -> Repository Class.

   Let's double-check the SQLAlchemy 2.0 syntax:
   - `mapped_column` is correct.
   - `relationship` with `back_populates` is correct.
   - `DeclarativeBase` is correct.
   - `AsyncSession` usage is correct.
   - Pydantic v2 `model_config = ConfigDict(from_attributes=True)` is correct.
   - I should ensure all types are strictly annotated.

   One minor adjustment: `StatusDisparo` enum values should match the Pydantic schema expectations. I'll keep them as strings for simplicity in Pydantic, or use `enum.Enum` with `str` mixin. I'll stick to `str, enum.Enum`.

   I'll also add a comment block at the top as