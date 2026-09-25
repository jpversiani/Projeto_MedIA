Here's a thinking process:

1.  **Understand User Goal:** The user wants me to create a Python file `backend/app/repositories/campanhas_repo.py` for a project called "MedIA". This file should contain models and methods for tracking health campaign messages, confirmation status by patients, and data protection audit logs. It must follow specific architectural guidelines: Python 3.12, strict typing with Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), full compliance, and automated test coverage with pytest.

2.  **Deconstruct Requirements:**
   - **File Path:** `backend/app/repositories/campanhas_repo.py`
   - **Models:** Pydantic v2 models for campaigns, message tracking, confirmation status, audit logs. SQLAlchemy 2.0 ORM models.
   - **Methods:** CRUD operations, tracking sent messages, confirmation status, audit logs.
   - **Standards:** CIAP-2, CID-10, SOAP, CNS/CPF.
   - **Compliance:** LGPD (Brazilian data protection law) compliance is implied by "proteção de dados" and SUS standards.
   - **Testing:** Provide pytest tests covering the functionality.
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0, pytest.

3.  **Identify Key Components:**
   - **Database Models (SQLAlchemy 2.0):**
     - `Campanha` (Campaign): id, name, description, start_date, end_date, status, created_at, updated_at.
     - `MensagemCampanha` (Campaign Message): id, campanha_id, paciente_cns, paciente_cpf, mensagem, status_envio, data_envio, status_confirmacao, confirmacao_data, confirmacao_mensagem.
     - `LogAuditoriaLGPD` (Audit Log): id, campanha_id, paciente_cns, paciente_cpf, acao, detalhes, ip, user_agent, data_hora.
   - **Pydantic Models (v2):**
     - `CampanhaCreate`, `CampanhaUpdate`, `CampanhaResponse`
     - `MensagemCampanhaCreate`, `MensagemCampanhaUpdate`, `MensagemCampanhaResponse`
     - `LogAuditoriaCreate`, `LogAuditoriaResponse`
   - **Repository Methods:**
     - CRUD for campaigns
     - Send message tracking
     - Update confirmation status
     - Create audit logs
     - Query methods (e.g., get campaign stats, get patient confirmation status)
   - **Compliance/Standards:**
     - Validate CNS/CPF formats
     - Map CIAP-2/CID-10 codes if needed (maybe as metadata or in campaign description)
     - SOAP method reference (maybe as a field or validation rule)
     - LGPD compliance: data masking, audit trails, consent tracking.

4.  **Design SQLAlchemy Models (SQLAlchemy 2.0 style):**
   Need to use `DeclarativeBase` or `registry`. I'll use `DeclarativeBase`.
   ```python
   from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Numeric
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
   from datetime import datetime
   import enum

   class Base(DeclarativeBase):
       pass

   class CampanhaStatus(str, enum.Enum):
       RASCUNHO = "rascunho"
       ATIVA = "ativa"
       PAUSADA = "pausada"
       CONCLUIDA = "concluida"

   class MensagemStatus(str, enum.Enum):
       PENDENTE = "pendente"
       ENVIADA = "enviada"
       FALHA = "falha"
       CONFIRMADA = "confirmada"
       RECUSADA = "recusada"

   class AcaoAuditoria(str, enum.Enum):
       CRIACAO = "criacao"
       ATUALIZACAO = "atualizacao"
       ENVIO = "envio"
       CONFIRMACAO = "confirmacao"
       ACESSO = "acesso"
       EXCLUSAO = "exclusao"

   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       nome: Mapped[str] = mapped_column(String(255), nullable=False)
       descricao: Mapped[str] = mapped_column(Text, nullable=True)
       codigo_ciap2: Mapped[str] = mapped_column(String(10), nullable=True) # CIAP-2
       codigo_cid10: Mapped[str] = mapped_column(String(10), nullable=True) # CID-10
       metodo_soap: Mapped[str] = mapped_column(String(50), nullable=True) # SOAP method
       data_inicio: Mapped[datetime] = mapped_column(DateTime, nullable=False)
       data_fim: Mapped[datetime] = mapped_column(DateTime, nullable=True)
       status: Mapped[CampanhaStatus] = mapped_column(Enum(CampanhaStatus), default=CampanhaStatus.RASCUNHO)
       created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

       mensagens = relationship("MensagemCampanha", back_populates="campanha", cascade="all, delete-orphan")
       logs = relationship("LogAuditoriaLGPD", back_populates="campanha", cascade="all, delete-orphan")

   class MensagemCampanha(Base):
       __tablename__ = "mensagens_campanhas"
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       campanha_id: Mapped[int] = mapped_column(Integer, ForeignKey("campanhas.id"), nullable=False)
       paciente_cns: Mapped[str] = mapped_column(String(15), nullable=True) # CNS
       paciente_cpf: Mapped[str] = mapped_column(String(14), nullable=True) # CPF
       conteudo: Mapped[str] = mapped_column(Text, nullable=False)
       status_envio: Mapped[MensagemStatus] = mapped_column(Enum(MensagemStatus), default=MensagemStatus.PENDENTE)
       data_envio: Mapped[datetime] = mapped_column(DateTime, nullable=True)
       status_confirmacao: Mapped[MensagemStatus] = mapped_column(Enum(MensagemStatus), default=MensagemStatus.PENDENTE)
       data_confirmacao: Mapped[datetime] = mapped_column(DateTime, nullable=True)
       mensagem_confirmacao: Mapped[str] = mapped_column(Text, nullable=True)

       campanha = relationship("Campanha", back_populates="mensagens")

   class LogAuditoriaLGPD(Base):
       __tablename__ = "logs_auditoria_lgpd"
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       campanha_id: Mapped[int] = mapped_column(Integer, ForeignKey("campanhas.id"), nullable=True)
       paciente_cns: Mapped[str] = mapped_column(String(15), nullable=True)
       paciente_cpf: Mapped[str] = mapped_column(String(14), nullable=True)
       acao: Mapped[AcaoAuditoria] = mapped_column(Enum(AcaoAuditoria), nullable=False)
       detalhes: Mapped[str] = mapped_column(Text, nullable=True)
       ip: Mapped[str] = mapped_column(String(45), nullable=True)
       user_agent: Mapped[str] = mapped_column(String(255), nullable=True)
       data_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

       campanha = relationship("Campanha", back_populates="logs")
   ```

5.  **Design Pydantic Models (v2):**
   Need to use `BaseModel`, `ConfigDict`, `Field`, `computed_field`, `model_validator`.
   ```python
   from pydantic import BaseModel, Field, ConfigDict, computed_field, model_validator
   from datetime import datetime
   from typing import Optional
   import re

   # CPF Validation
   def validate_cpf(cpf: str) -> str:
       if not cpf or not cpf.isdigit() or len(cpf) != 11:
           raise ValueError("CPF inválido")
       return cpf

   # CNS Validation (15 digits)
   def validate_cns(cns: str) -> str:
       if not cns or not cns.isdigit() or len(cns) != 15:
           raise ValueError("CNS inválido")
       return cns

   class CampanhaBase(BaseModel):
       nome: str = Field(..., min_length=1, max_length=255)
       descricao: Optional[str] = None
       codigo_ciap2: Optional[str] = Field(None, pattern=r"^[A-Z0-9]{1,10}$")
       codigo_cid10: Optional[str] = Field(None, pattern=r"^[A-Z0-9]{1,10}$")
       metodo_soap: Optional[str] = Field(None, pattern=r"^[A-Z_]{1,50}$")
       data_inicio: datetime
       data_fim: Optional[datetime] = None

   class CampanhaCreate(CampanhaBase):
       pass

   class CampanhaUpdate(BaseModel):
       nome: Optional[str] = Field(None, min_length=1, max_length=255)
       descricao: Optional[str] = None
       codigo_ciap2: Optional[str] = None
       codigo_cid10: Optional[str] = None
       metodo_soap: Optional[str] = None
       data_inicio: Optional[datetime] = None
       data_fim: Optional[datetime] = None
       status: Optional[str] = None

   class CampanhaResponse(CampanhaBase):
       model_config = ConfigDict(from_attributes=True)
       id: int
       status: str
       created_at: datetime
       updated_at: datetime

   class MensagemCampanhaBase(BaseModel):
       campanha_id: int
       paciente_cns: Optional[str] = None
       paciente_cpf: Optional[str] = None
       conteudo: str = Field(..., min_length=1)

       @model_validator(mode='after')
       def validate_identifiers(self):
           if not self.paciente_cns and not self.paciente_cpf:
               raise ValueError("É obrigatório informar CNS ou CPF")
           if self.paciente_cns:
               self.paciente_cns = validate_cns(self.paciente_cns)
           if self.paciente_cpf:
               self.paciente_cpf = validate_cpf(self.paciente_cpf)
           return self

   class MensagemCampanhaCreate(MensagemCampanhaBase):
       pass

   class MensagemCampanhaUpdate(BaseModel):
       status_envio: Optional[str] = None
       status_confirmacao: Optional[str] = None
       mensagem_confirmacao: Optional[str] = None

   class MensagemCampanhaResponse(MensagemCampanhaBase):
       model_config = ConfigDict(from_attributes=True)
       id: int
       status_envio: str
       data_envio: Optional[datetime] = None
       status_confirmacao: str
       data_confirmacao: Optional[datetime] = None
       mensagem_confirmacao: Optional[str] = None

   class LogAuditoriaCreate(BaseModel):
       campanha_id: Optional[int] = None
       paciente_cns: Optional[str] = None
       paciente_cpf: Optional[str] = None
       acao: str
       detalhes: Optional[str] = None
       ip: Optional[str] = None
       user_agent: Optional[str] = None

   class LogAuditoriaResponse(LogAuditoriaCreate):
       model_config = ConfigDict(from_attributes=True)
       id: int
       data_hora: datetime
   ```

6.  **Design Repository Class:**
   Needs to interact with SQLAlchemy async session (typical for modern FastAPI/Python backends). I'll use `async` methods.
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, update, func
   from sqlalchemy.orm import selectinload
   from typing import List, Optional, Dict, Any
   from datetime import datetime
   import uuid

   class CampanhasRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def create_campanha(self, data: CampanhaCreate) -> Campanha:
           campanha = Campanha(**data.model_dump())
           self.session.add(campanha)
           await self.session.flush()
           await self.create_audit_log(campanha_id=campanha.id, acao=AcaoAuditoria.CRIACAO, detalhes=f"Campanha {campanha.nome} criada")
           await self.session.commit()
           await self.session.refresh(campanha)
           return campanha

       async def get_campanha(self, campanha_id: int) -> Optional[Campanha]:
           result = await self.session.execute(select(Campanha).where(Campanha.id == campanha_id))
           return result.scalar_one_or_none()

       async def update_campanha(self, campanha_id: int, data: CampanhaUpdate) -> Optional[Campanha]:
           campanha = await self.get_campanha(campanha_id)
           if not campanha:
               return None
           update_data = data.model_dump(exclude_unset=True)
           for key, value in update_data.items():
               setattr(campanha, key, value)
           await self.session.flush()
           await self.create_audit_log(campanha_id=campanha_id, acao=AcaoAuditoria.ATUALIZACAO, detalhes=f"Campanha {campanha.nome} atualizada")
           await self.session.commit()
           await self.session.refresh(campanha)
           return campanha

       async def delete_campanha(self, campanha_id: int) -> bool:
           campanha = await self.get_campanha(campanha_id)
           if not campanha:
               return False
           await self.session.delete(campanha)
           await self.create_audit_log(campanha_id=campanha_id, acao=AcaoAuditoria.EXCLUSAO, detalhes=f"Campanha {campanha.nome} excluída")
           await self.session.commit()
           return True

       async def send_message(self, data: MensagemCampanhaCreate) -> MensagemCampanha:
           msg = MensagemCampanha(**data.model_dump())
           msg.status_envio = MensagemStatus.ENVIADA
           msg.data_envio = datetime.utcnow()
           self.session.add(msg)
           await self.session.flush()
           await self.create_audit_log(campanha_id=data.campanha_id, paciente_cns=data.paciente_cns, paciente_cpf=data.paciente_cpf, acao=AcaoAuditoria.ENVIO, detalhes=f"Mensagem enviada para CNS {data.paciente_cns or 'N/A'}")
           await self.session.commit()
           await self.session.refresh(msg)
           return msg

       async def update_confirmation(self, mensagem_id: int, status: str, confirmacao_msg: Optional[str] = None) -> Optional[MensagemCampanha]:
           result = await self.session.execute(select(MensagemCampanha).where(MensagemCampanha.id == mensagem_id))
           msg = result.scalar_one_or_none()
           if not msg:
               return None
           msg.status_confirmacao = MensagemStatus(status)
           msg.data_confirmacao = datetime.utcnow()
           if confirmacao_msg:
               msg.mensagem_confirmacao = confirmacao_msg
           await self.session.flush()
           await self.create_audit_log(campanha_id=msg.campanha_id, paciente_cns=msg.paciente_cns, paciente_cpf=msg.paciente_cpf, acao=AcaoAuditoria.CONFIRMACAO, detalhes=f"Confirmação atualizada para {status}")
           await self.session.commit()
           await self.session.refresh(msg)
           return msg

       async def get_campanha_stats(self, campanha_id: int) -> Dict[str, Any]:
           campanha = await self.get_campanha(campanha_id)
           if not campanha:
               return {}
           result = await self.session.execute(
               select(
                   func.count(MensagemCampanha.id).label("total"),
                   func.count(MensagemCampanha.id).filter(MensagemCampanha.status_envio == MensagemStatus.ENVIADA).label("enviadas"),
                   func.count(MensagemCampanha.id).filter(MensagemCampanha.status_confirmacao == MensagemStatus.CONFIRMADA).label("confirmadas"),
                   func.count(MensagemCampanha.id).filter(MensagemCampanha.status_confirmacao == MensagemStatus.RECUSADA).label("recusadas")
               ).where(MensagemCampanha.campanha_id == campanha_id)
           )
           row = result.one()
           return {
               "campanha_id": campanha_id,
               "total_mensagens": row.total,
               "enviadas": row.enviadas,
               "confirmadas": row.confirmadas,
               "recusadas": row.recusadas,
               "taxa_confirmacao": (row.confirmadas / row.enviadas * 100) if row.enviadas > 0 else 0.0
           }

       async def create_audit_log(self, campanha_id: Optional[int] = None, paciente_cns: Optional[str] = None, paciente_cpf: Optional[str] = None, acao: str = None, detalhes: Optional[str] = None, ip: Optional[str] = None, user_agent: Optional[str] = None) -> LogAuditoriaLGPD:
           log = LogAuditoriaLGPD(
               campanha_id=campanha_id,
               paciente_cns=paciente_cns,
               paciente_cpf=paciente_cpf,
               acao=AcaoAuditoria(acao),
               detalhes=detalhes,
               ip=ip or "127.0.0.1",
               user_agent=user_agent or "system"
           )
           self.session.add(log)
           await self.session.flush()
           await self.session.commit()
           return log