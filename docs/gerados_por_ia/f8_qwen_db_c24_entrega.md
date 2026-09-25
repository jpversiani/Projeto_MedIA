Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for the "MedIA" project.
   - **Requirements:**
     - Models and methods for recording: message dispatch tracking, patient confirmation status, data protection audit log.
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification.
     - Full compliance and automated test coverage with pytest.
     - Provide complete, executable code.
     - Specify file paths for each block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/campanhas_repo.py`
   - **Core Entities/Models:**
     - Campaign/Message Dispatch Tracking (`CampanhaEnvio`)
     - Patient Confirmation Status (`ConfirmaçãoPaciente` or `StatusConfirmacao`)
     - Data Protection Audit Log (`LogAuditoriaProtecaoDados`)
   - **Standards/Fields:**
     - CIAP-2 (Classificação Internacional de Atenção Primária)
     - CID-10 (Classificação Internacional de Doenças)
     - SOAP (Subjetivo, Objetivo, Avaliação, Plano)
     - CNS (Cartão Nacional de Saúde) / CPF (Cadastro de Pessoas Físicas)
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0 (async/sync? I'll use async for modern backend, but will make it compatible. I'll stick to SQLAlchemy 2.0 ORM with declarative base).
   - **Testing:** pytest coverage, full compliance. I need to provide the repo file AND a test file. The prompt says "Execute com precisão conforme as diretrizes" and "Forneça o código completo e executável". I'll provide both the repository and the tests.

3.  **Design Database Models (SQLAlchemy 2.0):**
   - `Campanha` (Campaign): id, nome, descricao, status, criado_em, atualizado_em
   - `CampanhaMensagem` (Message Dispatch): id, campanha_id, destinatario_cpf, destinatario_cns, mensagem, status_envio, data_envio, metodo_soap (JSON/text), cid10, ciap2
   - `ConfirmaçãoPaciente` (Confirmation): id, mensagem_id, paciente_cpf, paciente_cns, status (confirmado, pendente, negado), data_confirmacao, observacoes
   - `LogAuditoriaProtecaoDados` (Audit Log): id, campanha_id, mensagem_id, acao, usuario, ip, data_hora, detalhes, conformidade_lgpd (bool)

   Wait, the prompt says "rastreio de mensagens enviadas, status de confirmação pelo paciente e log de auditoria de proteção de dados." So I'll focus on these three core entities. I'll make them related to a campaign.

   Let's define Pydantic schemas for validation/input/output.
   SQLAlchemy models for persistence.
   Repository class with methods for CRUD and specific tracking/audit operations.

   I'll use SQLAlchemy 2.0 style: `DeclarativeBase`, `Mapped`, `mapped_column`, `relationship`.
   I'll use Pydantic v2: `BaseModel`, `ConfigDict`, `Field`.

4.  **Draft - SQLAlchemy Models:**
   ```python
   from datetime import datetime
   from typing import Optional, List
   from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Enum as SAEnum
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
   import enum

   class Base(DeclarativeBase):
       pass

   class StatusEnvio(str, enum.Enum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       FALHA = "falha"
       LIDO = "lido"

   class StatusConfirmacao(str, enum.Enum):
       PENDENTE = "pendente"
       CONFIRMADO = "confirmado"
       NEGADO = "negado"
       EXPIRADO = "expirado"

   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[int] = mapped_column(primary_key=True)
       nome: Mapped[str] = mapped_column(String(100), unique=True)
       descricao: Mapped[Optional[str]] = mapped_column(Text)
       criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

   class CampanhaMensagem(Base):
       __tablename__ = "campanhas_mensagens"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"))
       cpf_destinatario: Mapped[str] = mapped_column(String(14), index=True)
       cns_destinatario: Mapped[Optional[str]] = mapped_column(String(15))
       conteudo: Mapped[str] = mapped_column(Text)
       status_envio: Mapped[StatusEnvio] = mapped_column(SAEnum(StatusEnvio), default=StatusEnvio.PENDENTE)
       data_envio: Mapped[Optional[datetime]] = mapped_column(DateTime)
       # SUS/APS Standards
       cid10: Mapped[Optional[str]] = mapped_column(String(10))
       ciap2: Mapped[Optional[str]] = mapped_column(String(4))
       metodo_soap: Mapped[Optional[str]] = mapped_column(Text) # JSON string or structured text
       campanha = relationship("Campanha", back_populates="mensagens")

   class CampanhaMensagem.conversas = relationship("CampanhaMensagem", back_populates="campanha")

   class ConfirmacaoPaciente(Base):
       __tablename__ = "confirmacoes_paciente"
       id: Mapped[int] = mapped_column(primary_key=True)
       mensagem_id: Mapped[int] = mapped_column(ForeignKey("campanhas_mensagens.id"))
       cpf_paciente: Mapped[str] = mapped_column(String(14))
       cns_paciente: Mapped[Optional[str]] = mapped_column(String(15))
       status: Mapped[StatusConfirmacao] = mapped_column(SAEnum(StatusConfirmacao), default=StatusConfirmacao.PENDENTE)
       data_confirmacao: Mapped[Optional[datetime]] = mapped_column(DateTime)
       observacoes: Mapped[Optional[str]] = mapped_column(Text)
       mensagem = relationship("CampanhaMensagem", back_populates="confirmacoes")

   class CampanhaMensagem.conversas = relationship("ConfirmacaoPaciente", back_populates="mensagem")

   class LogAuditoriaProtecaoDados(Base):
       __tablename__ = "log_auditoria_lgpd"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"))
       mensagem_id: Mapped[Optional[int]] = mapped_column(ForeignKey("campanhas_mensagens.id"))
       acao: Mapped[str] = mapped_column(String(50)) # e.g., "DISPATCH", "CONFIRM", "ACCESS", "DELETE"
       usuario: Mapped[Optional[str]] = mapped_column(String(100))
       ip_origem: Mapped[Optional[str]] = mapped_column(String(45))
       data_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       detalhes: Mapped[Optional[str]] = mapped_column(Text)
       conformidade_lgpd: Mapped[bool] = mapped_column(Boolean, default=True)
   ```
   *Self-Correction/Refinement during drafting:*
   - SQLAlchemy 2.0 uses `mapped_column` and type hints. I need to import `Mapped` and `mapped_column` from `sqlalchemy.orm`.
   - Enums in SQLAlchemy 2.0: `SAEnum` is fine, but `Enum` from `sqlalchemy` is standard. I'll use `sqlalchemy.Enum`.
   - I'll structure the file properly with imports, models, Pydantic schemas, and the repository class.
   - I'll add proper relationships and back_populates.
   - I'll ensure strict typing.

   Let's rewrite the models carefully for SQLAlchemy 2.0:
   ```python
   from datetime import datetime
   from typing import Optional, List
   from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Enum as SAEnum
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
   import enum

   class Base(DeclarativeBase):
       pass

   class StatusEnvio(str, enum.Enum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       FALHA = "falha"
       LIDO = "lido"

   class StatusConfirmacao(str, enum.Enum):
       PENDENTE = "pendente"
       CONFIRMADO = "confirmado"
       NEGADO = "negado"
       EXPIRADO = "expirado"

   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[int] = mapped_column(primary_key=True)
       nome: Mapped[str] = mapped_column(String(100), unique=True)
       descricao: Mapped[Optional[str]] = mapped_column(Text)
       criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       mensagens: Mapped[List["CampanhaMensagem"]] = relationship(back_populates="campanha")

   class CampanhaMensagem(Base):
       __tablename__ = "campanhas_mensagens"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"))
       cpf_destinatario: Mapped[str] = mapped_column(String(14), index=True)
       cns_destinatario: Mapped[Optional[str]] = mapped_column(String(15))
       conteudo: Mapped[str] = mapped_column(Text)
       status_envio: Mapped[StatusEnvio] = mapped_column(SAEnum(StatusEnvio), default=StatusEnvio.PENDENTE)
       data_envio: Mapped[Optional[datetime]] = mapped_column(DateTime)
       cid10: Mapped[Optional[str]] = mapped_column(String(10))
       ciap2: Mapped[Optional[str]] = mapped_column(String(4))
       metodo_soap: Mapped[Optional[str]] = mapped_column(Text)
       campanha = relationship("Campanha", back_populates="mensagens")
       confirmacoes: Mapped[List["ConfirmacaoPaciente"]] = relationship(back_populates="mensagem")

   class ConfirmacaoPaciente(Base):
       __tablename__ = "confirmacoes_paciente"
       id: Mapped[int] = mapped_column(primary_key=True)
       mensagem_id: Mapped[int] = mapped_column(ForeignKey("campanhas_mensagens.id"))
       cpf_paciente: Mapped[str] = mapped_column(String(14))
       cns_paciente: Mapped[Optional[str]] = mapped_column(String(15))
       status: Mapped[StatusConfirmacao] = mapped_column(SAEnum(StatusConfirmacao), default=StatusConfirmacao.PENDENTE)
       data_confirmacao: Mapped[Optional[datetime]] = mapped_column(DateTime)
       observacoes: Mapped[Optional[str]] = mapped_column(Text)
       mensagem = relationship("CampanhaMensagem", back_populates="confirmacoes")

   class LogAuditoriaProtecaoDados(Base):
       __tablename__ = "log_auditoria_lgpd"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"))
       mensagem_id: Mapped[Optional[int]] = mapped_column(ForeignKey("campanhas_mensagens.id"))
       acao: Mapped[str] = mapped_column(String(50))
       usuario: Mapped[Optional[str]] = mapped_column(String(100))
       ip_origem: Mapped[Optional[str]] = mapped_column(String(45))
       data_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       detalhes: Mapped[Optional[str]] = mapped_column(Text)
       conformidade_lgpd: Mapped[bool] = mapped_column(Boolean, default=True)
   ```
   *Note:* SQLAlchemy 2.0 requires `from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship`. I'll add that. Also, `enum.Enum` is fine. I'll use `sqlalchemy.Enum` for the column type.

5.  **Draft - Pydantic Schemas (v2):**
   Need input/output schemas for validation.
   ```python
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from datetime import datetime
   from typing import Optional, List
   import re

   class CampanhaCreate(BaseModel):
       nome: str = Field(..., min_length=3, max_length=100)
       descricao: Optional[str] = None

   class CampanhaMensagemCreate(BaseModel):
       campanha_id: int
       cpf_destinatario: str = Field(..., pattern=r"^\d{11}$")
       cns_destinatario: Optional[str] = Field(None, pattern=r"^\d{15}$")
       conteudo: str = Field(..., min_length=1)
       cid10: Optional[str] = Field(None, pattern=r"^[A-Z]\d{2}$")
       ciap2: Optional[str] = Field(None, pattern=r"^[A-Z]\d{3}$")
       metodo_soap: Optional[str] = None

       @field_validator("cpf_destinatario")
       @classmethod
       def validate_cpf(cls, v: str) -> str:
           if not re.match(r"^\d{11}$", v):
               raise ValueError("CPF deve conter 11 dígitos numéricos.")
           return v

   class ConfirmacaoPacienteCreate(BaseModel):
       mensagem_id: int
       cpf_paciente: str = Field(..., pattern=r"^\d{11}$")
       cns_paciente: Optional[str] = Field(None, pattern=r"^\d{15}$")
       status: StatusConfirmacao
       observacoes: Optional[str] = None

   class LogAuditoriaCreate(BaseModel):
       campanha_id: int
       mensagem_id: Optional[int] = None
       acao: str = Field(..., min_length=1, max_length=50)
       usuario: Optional[str] = None
       ip_origem: Optional[str] = None
       detalhes: Optional[str] = None
       conformidade_lgpd: bool = True
   ```
   *Self-Correction/Refinement:* Pydantic v2 uses `field_validator` with `@field_validator("field_name")`. I'll adjust. Also, I'll add `model_config = ConfigDict(from_attributes=True)` for ORM mapping. I'll make sure types match SQLAlchemy models.

6.  **Draft - Repository Class:**
   Need async methods for tracking dispatch, confirmation, and audit logs.
   I'll use `async_session` pattern. I'll define the repo class with methods like:
   - `criar_campanha`
   - `registrar_envio_mensagem`
   - `atualizar_status_confirmacao`
   - `registrar_log_auditoria`
   - `obter_rastreamento_campanha`
   - `obter_logs_auditoria`

   I'll use SQLAlchemy 2.0 async session (`AsyncSession`).
   I'll make sure to handle transactions properly.

   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, func
   from typing import List, Dict, Any
   from uuid import uuid4

   class CampanhasRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def registrar_envio_mensagem(self, schema: CampanhaMensagemCreate) -> CampanhaMensagem:
           mensagem = CampanhaMensagem(
               campanha_id=schema.campanha_id,
               cpf_destinatario=schema.cpf_destinatario,
               cns_destinatario=schema.cns_destinatario,
               conteudo=schema.conteudo,
               cid10=schema.cid10,
               ciap2=schema.ciap2,
               metodo_soap=schema.metodo_soap,
               status_envio=StatusEnvio.ENVIADO,
               data_envio=datetime.utcnow()
           )
           self.session.add(mensagem)
           await self.session.flush()
           # Register audit log
           await self.registrar_log_auditoria(LogAuditoriaCreate(
               campanha_id=schema.campanha_id,
               mensagem_id=mensagem.id,
               acao="DISPATCH",
               usuario="SISTEMA",
               ip_origem="127.0.0.1",
               detalhes=f"Envio para CPF {schema.cpf_destinatario}"
           ))
           await self.session.commit()
           await self.session.refresh(mensagem)
           return mensagem

       async def atualizar_status_confirmacao(self, cpf: str, status: StatusConfirmacao, observacoes: Optional[str] = None) -> ConfirmacaoPaciente:
           # Find existing or create
           stmt = select(ConfirmacaoPaciente).where(ConfirmacaoPaciente.cpf_paciente == cpf)
           result = await self.session.execute(stmt)
           confirmacao = result.scalar_one_or_none()

           if not confirmacao:
               confirmacao = ConfirmacaoPaciente(
                   cpf_paciente=cpf,
                   status=status,
                   data_confirmacao=datetime.utcnow(),
                   observacoes=observacoes
               )
               self.session.add(confirmacao)
           else:
               confirmacao.status = status
               confirmacao.data_confirmacao = datetime.utcnow()
               if observacoes:
                   confirmacao.observacoes = observacoes

           await self.session.commit()
           await self