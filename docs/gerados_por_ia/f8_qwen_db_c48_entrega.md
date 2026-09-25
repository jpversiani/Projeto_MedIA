Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for a project called "MedIA".
   - **Features:** Campaign repository with models and methods for:
     - Tracking sent messages
     - Confirmation status by patient
     - Data protection audit log
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
     - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
     - Full compliance and automated test coverage with pytest
   - **Output Requirement:** Provide complete, executable code. Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/campanhas_repo.py`
   - **Models (Pydantic v2):** Need schemas for campaigns, message tracking, confirmation status, audit log.
   - **Database Models (SQLAlchemy 2.0):** Need ORM models corresponding to the Pydantic schemas.
   - **Repository Methods:** CRUD for campaigns, send message, update confirmation status, log audit.
   - **SUS/APS Standards:** Fields for CIAP-2, CID-10, SOAP notes, CNS/CPF.
   - **Testing:** Provide pytest tests covering all repository methods and models.
   - **Compliance:** Data protection (LGPD) considerations in audit log.

3.  **Design Database Models (SQLAlchemy 2.0):**
   - `Campanha` (Campaign): id, name, description, status, created_at, updated_at, target_cpf/cns (maybe not, campaigns target groups), message_template, ciap2_codes, cid10_codes, soap_notes (JSON/text), created_by.
   - `MensagemEnviada` (SentMessage): id, campanha_id, paciente_cpf, paciente_cns, status (sent, delivered, read, failed), sent_at, confirmation_status (confirmed, pending, rejected), confirmation_at, message_id (external provider ref).
   - `AuditoriaProtecaoDados` (DataProtectionAudit): id, campanha_id, mensagem_id, action (view, export, delete, modify), performed_by, timestamp, ip_address, justification, compliance_status (compliant, violation).

   Let's refine based on SUS/APS standards:
   - Campaigns in SUS often relate to specific health conditions (CID-10, CIAP-2), target populations (CNS/CPF ranges), and follow SOAP methodology for notes.
   - I'll add fields like `condicao_saude` (CID-10), `codigo_ciap2`, `metodo_observacao` (SOAP), `publico_alvo_cpf/cns`.
   - For simplicity and strict typing, I'll use SQLAlchemy 2.0 declarative style with `Mapped` and `mapped_column`.

4.  **Design Pydantic Schemas (v2):**
   - `CampanhaCreate`, `CampanhaUpdate`, `CampanhaRead`
   - `MensagemEnvio`, `MensagemStatusUpdate`, `MensagemRead`
   - `AuditoriaCreate`, `AuditoriaRead`
   - Use `ConfigDict`, `Field`, `model_validator`, `computed_field` as needed.
   - Strict typing: `str`, `int`, `float`, `datetime`, `enum`, `UUID`, `Optional`, `List`.

5.  **Design Repository Class:**
   - `class CampanhasRepository:`
   - Methods: `create_campaign`, `get_campaign`, `update_campaign`, `send_message`, `update_message_status`, `log_audit`, `get_audit_logs`, `get_campaign_messages`.
   - Use async SQLAlchemy (SQLAlchemy 2.0 async session).
   - Handle transactions, error handling, validation.

6.  **Address SUS/APS Standards:**
   - CID-10: `cid10_codes: List[str]`
   - CIAP-2: `ciap2_codes: List[str]`
   - SOAP: `soap_notes: dict` or `str` (I'll use `dict` with keys `S`, `O`, `A`, `P`)
   - CNS/CPF: `target_cpf: Optional[str]`, `target_cns: Optional[str]` (or list)
   - I'll add validation for CPF/CNS format if possible, but keep it simple for now.

7.  **Address Data Protection (LGPD):**
   - Audit log must track: action, user, timestamp, IP, justification, compliance status.
   - Add `consent_given: bool` to campaign/message if needed, but audit log covers it.

8.  **Draft Code (Mental Refinement):**
   I'll structure the file with:
   - Imports
   - Enums (Status, AuditAction, etc.)
   - SQLAlchemy Models
   - Pydantic Schemas
   - Repository Class
   - Test file (pytest)

   Let's write it out carefully.

   *SQLAlchemy Models:*
   ```python
   from sqlalchemy import String, Text, DateTime, Boolean, Enum, ForeignKey, Integer
   from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
   from sqlalchemy.sql import func
   import enum
   import uuid

   class Base(DeclarativeBase):
       pass

   class CampanhaStatus(str, enum.Enum):
       RASCUNHO = "rascunho"
       ATIVA = "ativa"
       PAUSADA = "pausada"
       CONCLUIDA = "concluida"

   class MensagemStatus(str, enum.Enum):
       ENVIADO = "enviado"
       ENTREGUE = "entregue"
       LIDO = "lido"
       FALHA = "falha"

   class ConfirmacaoStatus(str, enum.Enum):
       PENDENTE = "pendente"
       CONFIRMADO = "confirmado"
       REJEITADO = "rejeitado"

   class AuditoriaAcao(str, enum.Enum):
       CRIAR = "criar"
       ATUALIZAR = "atualizar"
       EXCLUIR = "excluir"
       EXPORTAR = "exportar"
       ACESSAR = "acessar"
       MODIFICAR = "modificar"

   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       nome: Mapped[str] = mapped_column(String(255), nullable=False)
       descricao: Mapped[str] = mapped_column(Text, nullable=True)
       status: Mapped[CampanhaStatus] = mapped_column(Enum(CampanhaStatus), default=CampanhaStatus.RASCUNHO)
       cid10_codes: Mapped[list[str]] = mapped_column(Text, nullable=True) # JSON string in DB
       ciap2_codes: Mapped[list[str]] = mapped_column(Text, nullable=True)
       soap_notes: Mapped[dict] = mapped_column(Text, nullable=True) # JSON string
       publico_alvo_cpf: Mapped[str] = mapped_column(String(14), nullable=True)
       publico_alvo_cns: Mapped[str] = mapped_column(String(15), nullable=True)
       template_mensagem: Mapped[str] = mapped_column(Text, nullable=False)
       criado_por: Mapped[str] = mapped_column(String(100), nullable=False)
       criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
       mensagens = relationship("MensagemEnviada", back_populates="campanha", cascade="all, delete-orphan")
       auditorias = relationship("AuditoriaProtecaoDados", back_populates="campanha", cascade="all, delete-orphan")

   class MensagemEnviada(Base):
       __tablename__ = "mensagens_enviadas"
       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       campanha_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campanhas.id"), nullable=False)
       paciente_cpf: Mapped[str] = mapped_column(String(14), nullable=False)
       paciente_cns: Mapped[str] = mapped_column(String(15), nullable=True)
       status: Mapped[MensagemStatus] = mapped_column(Enum(MensagemStatus), default=MensagemStatus.ENVIADO)
       confirmation_status: Mapped[ConfirmacaoStatus] = mapped_column(Enum(ConfirmacaoStatus), default=ConfirmacaoStatus.PENDENTE)
       mensagem_id_externo: Mapped[str] = mapped_column(String(255), nullable=True)
       enviado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       confirmado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
       campanha = relationship("Campanha", back_populates="mensagens")
       auditorias = relationship("AuditoriaProtecaoDados", back_populates="mensagem", cascade="all, delete-orphan")

   class AuditoriaProtecaoDados(Base):
       __tablename__ = "auditoria_protecao_dados"
       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       campanha_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campanhas.id"), nullable=True)
       mensagem_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mensagens_enviadas.id"), nullable=True)
       acao: Mapped[AuditoriaAcao] = mapped_column(Enum(AuditoriaAcao), nullable=False)
       realizado_por: Mapped[str] = mapped_column(String(100), nullable=False)
       timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
       justificativa: Mapped[str] = mapped_column(Text, nullable=True)
       status_conformidade: Mapped[bool] = mapped_column(Boolean, default=True)
       campanha = relationship("Campanha", back_populates="auditorias")
       mensagem = relationship("MensagemEnviada", back_populates="auditorias")
   ```

   *Pydantic Schemas:*
   Need to handle JSON serialization for lists/dicts. I'll use `Json` type or `str` with validation. Pydantic v2 handles `list[str]` and `dict` fine, but SQLAlchemy needs JSON type. I'll use `JSON` from `sqlalchemy` or just store as text and parse. For simplicity in this repo file, I'll keep it as `Text` and use `json` module in repo, or use `SQLAlchemy`'s `JSON` type. I'll stick to `Text` and handle JSON in repo for clarity, or use `sqlalchemy.JSON`. Let's use `sqlalchemy.JSON` for `cid10_codes`, `ciap2_codes`, `soap_notes`.

   Actually, Pydantic v2 + SQLAlchemy 2.0 works well with `Mapped[list[str]]` and `Mapped[dict]` if using `JSON` type. I'll import `JSON` from `sqlalchemy`.

   Let's draft schemas:
   ```python
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from datetime import datetime
   import uuid
   import re

   class CampanhaBase(BaseModel):
       nome: str = Field(..., min_length=1, max_length=255)
       descricao: str | None = None
       cid10_codes: list[str] = Field(default_factory=list)
       ciap2_codes: list[str] = Field(default_factory=list)
       soap_notes: dict[str, str] = Field(default_factory=dict)
       publico_alvo_cpf: str | None = None
       publico_alvo_cns: str | None = None
       template_mensagem: str = Field(..., min_length=1)
       criado_por: str = Field(..., min_length=1)

       @field_validator("publico_alvo_cpf")
       @classmethod
       def validate_cpf(cls, v):
           if v is None: return v
           v = re.sub(r'\D', '', v)
           if len(v) != 11: raise ValueError("CPF deve ter 11 dígitos")
           return v

       @field_validator("publico_alvo_cns")
       @classmethod
       def validate_cns(cls, v):
           if v is None: return v
           v = re.sub(r'\D', '', v)
           if len(v) != 15: raise ValueError("CNS deve ter 15 dígitos")
           return v

   class CampanhaCreate(CampanhaBase):
       pass

   class CampanhaUpdate(BaseModel):
       nome: str | None = None
       descricao: str | None = None
       status: CampanhaStatus | None = None
       cid10_codes: list[str] | None = None
       ciap2_codes: list[str] | None = None
       soap_notes: dict[str, str] | None = None
       template_mensagem: str | None = None

   class CampanhaRead(CampanhaBase):
       model_config = ConfigDict(from_attributes=True)
       id: uuid.UUID
       status: CampanhaStatus
       criado_em: datetime
       atualizado_em: datetime | None = None

   class MensagemEnvio(BaseModel):
       campanha_id: uuid.UUID
       paciente_cpf: str
       paciente_cns: str | None = None
       mensagem_id_externo: str | None = None

       @field_validator("paciente_cpf")
       @classmethod
       def validate_cpf(cls, v):
           if v is None: return v
           v = re.sub(r'\D', '', v)
           if len(v) != 11: raise ValueError("CPF deve ter 11 dígitos")
           return v

   class MensagemStatusUpdate(BaseModel):
       status: MensagemStatus | None = None
       confirmation_status: ConfirmacaoStatus | None = None
       confirmado_em: datetime | None = None

   class MensagemRead(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: uuid.UUID
       campanha_id: uuid.UUID
       paciente_cpf: str
       paciente_cns: str | None = None
       status: MensagemStatus
       confirmation_status: ConfirmacaoStatus
       mensagem_id_externo: str | None = None
       enviado_em: datetime
       confirmado_em: datetime | None = None

   class AuditoriaCreate(BaseModel):
       campanha_id: uuid.UUID | None = None
       mensagem_id: uuid.UUID | None = None
       acao: AuditoriaAcao
       realizado_por: str
       ip_address: str | None = None
       justificativa: str | None = None
       status_conformidade: bool = True

   class AuditoriaRead(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: uuid.UUID
       campanha_id: uuid.UUID | None = None
       mensagem_id: uuid.UUID | None = None
       acao: AuditoriaAcao
       realizado_por: str
       timestamp: datetime
       ip_address: str | None = None
       justificativa: str | None = None
       status_conformidade: bool
   ```

   *Repository Class:*
   Need async methods. I'll use `AsyncSession` from `sqlalchemy.ext.asyncio`.
   I'll add type hints, docstrings, and error handling.
   I'll also add a method to log audit automatically when creating/updating campaigns or messages.

   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, update, delete
   from sqlalchemy.exc import IntegrityError, SQLAlchemyError
   import asyncio
   import json

   class CampanhasRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def create_campaign(self, schema: CampanhaCreate) -> CampanhaRead:
           # Log audit
           await self.log_audit(AuditoriaCreate(acao=AuditoriaAcao.CRIAR, realizado_por=schema.criado_por, campanha_id=None))
           campaign = Campanha(
               nome=schema.nome,
               descricao=schema.descricao,
               status=CampanhaStatus.RASCUNHO,
               cid10_codes=schema.cid10_codes,
               ciap2_codes=schema.ciap2_codes,
               soap_notes=schema.soap_notes,
               publico_alvo_cpf=schema.publico_alvo_cpf,
               publico_alvo_cns=schema.publico_alvo_cns,
               template_mensagem=schema.template_mensagem,
               criado_por=schema.criado_por,
           )
           self.session.add(campaign)
           await self.session.flush()
           await self.session.refresh(campaign)
           return CampanhaRead.model_validate(campaign)

       async def get_campaign(self, campaign_id: uuid.UUID) -> CampanhaRead | None:
           stmt = select(Campanha).where(Campanha.id == campaign_id)
           result = await self.session.execute(stmt)
           campaign = result.scalar_one_or_none()
           if not campaign:
               return None
           await self.log_audit(AuditoriaCreate(acao=AuditoriaAcao.ACESSAR, realizado_por="sistema", campanha_id=campaign_id))
           return CampanhaRead.model_validate(campaign)

       async def update_campaign(self, campaign_id: uuid.UUID, schema: CampanhaUpdate) -> CampanhaRead:
           stmt = select(Campanha).where(Campanha.id == campaign_id)
           result = await self.session.execute(stmt)
           campaign = result.scalar_one_or_none()
           if not campaign:
               raise ValueError("Campanha não encontrada")

           update_data = schema.model_dump(exclude_unset=True)
           for key, value in update_data.items():
               setattr(campaign, key, value)

           await self.session.flush()