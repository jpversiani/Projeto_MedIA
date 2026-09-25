Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for a "Health Campaigns Repository and Send History" (C16).
   - **Requirements:**
     - Track sent messages, confirmation status by patient, and data protection audit logs.
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification.
     - Full compliance and automated test coverage with pytest.
     - Provide complete, executable code.
     - Specify file paths in code blocks.

2.  **Deconstruct Requirements & Architecture:**
   - **Domain:** Health campaigns (Campanhas de Saúde)
   - **Entities/Models needed:**
     - Campaign (Campanha)
     - Message/Send (Disparo/Mensagem)
     - Patient Confirmation (Confirmação do Paciente)
     - Audit Log (Log de Auditoria LGPD)
   - **Standards/Fields:**
     - CIAP-2 (Classificação Internacional de Atenção Primária)
     - CID-10 (Classificação Internacional de Doenças)
     - SOAP (Subjective, Objective, Assessment, Plan)
     - CNS (Cartão Nacional de Saúde) / CPF (Cadastro de Pessoas Físicas)
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0 (async/sync? I'll use sync for simplicity but note it's compatible with async, or use `sqlalchemy.orm` with `Mapped` and `mapped_column` for SQLAlchemy 2.0 style).
   - **Testing:** pytest coverage, strict typing, Pydantic models for validation.

3.  **Design Database Models (SQLAlchemy 2.0 style):**
   I'll use declarative base with `Mapped` and `mapped_column` (SQLAlchemy 2.0 recommended style).
   - `Campanha`: id, nome, descricao, status, data_criacao, data_atualizacao, cid10_referencia, ciap2_referencia
   - `Disparo`: id, campanha_id, paciente_cns, paciente_cpf, mensagem, status_envio, data_envio, data_confirmacao, confirmacao_paciente (bool), detalhes_confirmacao
   - `LogAuditoriaLGPD`: id, entidade_tipo (enum: CAMPAHA, DISPARO, PACIENTE), entidade_id, acao (enum: CRIAR, LER, ATUALIZAR, EXCLUIR, EXPORTAR), usuario_id, ip_origem, justificativa, data_hora

   Wait, the prompt says "rastreio de mensagens enviadas, status de confirmação pelo paciente e log de auditoria de proteção de dados." So I need models for Campaign, Send/Message, Confirmation, and Audit Log. I can combine Send and Confirmation into one model or keep them separate. Let's keep them separate for clarity, or combine as `Disparo` with confirmation fields. I'll go with `Disparo` having confirmation fields.

   Let's define Pydantic schemas for validation:
   - `CampanhaCreate`, `CampanhaRead`
   - `DisparoCreate`, `DisparoRead`
   - `LogAuditoriaCreate`, `LogAuditoriaRead`

   I'll use SQLAlchemy 2.0 syntax: `Mapped`, `mapped_column`, `relationship`, `DeclarativeBase`.

4.  **Draft Code Structure (Mental):**
   ```python
   # backend/app/repositories/campanhas_repo.py
   from __future__ import annotations
   from datetime import datetime
   from enum import Enum
   from typing import Optional, List
   from uuid import uuid4, UUID

   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum, Boolean, func
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
   import re

   # Base
   class Base(DeclarativeBase):
       pass

   # Enums
   class CampanhaStatus(str, Enum):
       RASCUNHO = "rascunho"
       ATIVA = "ativa"
       PAUSADA = "pausada"
       CONCLUIDA = "concluida"

   class DisparoStatus(str, Enum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       FALHA = "falha"
       CONFIRMADO = "confirmado"
       RECUSADO = "recusado"

   class AcaoAuditoria(str, Enum):
       CRIAR = "criar"
       LER = "ler"
       ATUALIZAR = "atualizar"
       EXCLUIR = "excluir"
       EXPORTAR = "exportar"

   # Pydantic Models
   class CampanhaBase(BaseModel):
       nome: str = Field(..., min_length=3, max_length=100)
       descricao: str = Field(..., max_length=500)
       cid10_referencia: str = Field(..., pattern=r'^[A-Z][0-9][0-9A-Z]{0,2}$')
       ciap2_referencia: str = Field(..., pattern=r'^[A-Z][0-9]{2,4}$')
       status: CampanhaStatus = CampanhaStatus.RASCUNHO

       @field_validator('cid10_referencia')
       @classmethod
       def validate_cid10(cls, v):
           # Basic CID-10 validation: Letter + 2 digits, optionally followed by a decimal and more digits
           if not re.match(r'^[A-Z][0-9][0-9A-Z]{0,2}(\.[0-9]{1,2})?$', v):
               raise ValueError('Formato CID-10 inválido')
           return v.upper()

       @field_validator('ciap2_referencia')
       @classmethod
       def validate_ciap2(cls, v):
           if not re.match(r'^[A-Z][0-9]{2,4}$', v):
               raise ValueError('Formato CIAP-2 inválido')
           return v.upper()

   class CampanhaCreate(CampanhaBase):
       pass

   class CampanhaRead(CampanhaBase):
       id: UUID
       data_criacao: datetime
       data_atualizacao: datetime
       model_config = ConfigDict(from_attributes=True)

   class DisparoBase(BaseModel):
       campanha_id: UUID
       paciente_cns: str = Field(..., min_length=15, max_length=15)
       paciente_cpf: str = Field(..., min_length=11, max_length=14)
       mensagem: str = Field(..., max_length=1000)
       status: DisparoStatus = DisparoStatus.PENDENTE
       detalhes_confirmação: Optional[str] = None

       @field_validator('paciente_cns')
       @classmethod
       def validate_cns(cls, v):
           if not re.match(r'^\d{15}$', v):
               raise ValueError('CNS inválido')
           return v

       @field_validator('paciente_cpf')
       @classmethod
       def validate_cpf(cls, v):
           v = v.replace('.', '').replace('-', '')
           if not re.match(r'^\d{11}$', v):
               raise ValueError('CPF inválido')
           return v

   class DisparoCreate(DisparoBase):
       pass

   class DisparoRead(DisparoBase):
       id: UUID
       data_envio: Optional[datetime] = None
       data_confirmacao: Optional[datetime] = None
       confirmacao_paciente: Optional[bool] = None
       model_config = ConfigDict(from_attributes=True)

   class LogAuditoriaBase(BaseModel):
       entidade_tipo: str
       entidade_id: UUID
       acao: AcaoAuditoria
       usuario_id: Optional[UUID] = None
       ip_origem: Optional[str] = None
       justificativa: Optional[str] = None

   class LogAuditoriaCreate(LogAuditoriaBase):
       pass

   class LogAuditoriaRead(LogAuditoriaBase):
       id: UUID
       data_hora: datetime
       model_config = ConfigDict(from_attributes=True)

   # SQLAlchemy Models
   class CampaignModel(Base):
       __tablename__ = "campanhas"
       id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
       nome: Mapped[str] = mapped_column(String(100))
       descricao: Mapped[str] = mapped_column(Text)
       status: Mapped[CampanhaStatus] = mapped_column(SAEnum(CampanhaStatus), default=CampanhaStatus.RASCUNHO)
       cid10_referencia: Mapped[str] = mapped_column(String(10))
       ciap2_referencia: Mapped[str] = mapped_column(String(10))
       data_criacao: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
       data_atualizacao: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
       disparos: Mapped[List["DisparoModel"]] = relationship(back_populates="campanha", lazy="selectin")

   class DisparoModel(Base):
       __tablename__ = "disparos"
       id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
       campanha_id: Mapped[UUID] = mapped_column(ForeignKey("campanhas.id"))
       paciente_cns: Mapped[str] = mapped_column(String(15))
       paciente_cpf: Mapped[str] = mapped_column(String(14))
       mensagem: Mapped[str] = mapped_column(Text)
       status: Mapped[DisparoStatus] = mapped_column(SAEnum(DisparoStatus), default=DisparoStatus.PENDENTE)
       data_envio: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
       data_confirmacao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
       confirmacao_paciente: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
       detalhes_confirmacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       campanha: Mapped["CampaignModel"] = relationship(back_populates="disparos")
       logs: Mapped[List["LogAuditoriaModel"]] = relationship(back_populates="entidade", lazy="selectin")

   class LogAuditoriaModel(Base):
       __tablename__ = "logs_auditoria"
       id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
       entidade_tipo: Mapped[str] = mapped_column(String(50))
       entidade_id: Mapped[UUID] = mapped_column(ForeignKey("disparos.id", ondelete="CASCADE"))
       acao: Mapped[AcaoAuditoria] = mapped_column(SAEnum(AcaoAuditoria))
       usuario_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
       ip_origem: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
       justificativa: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       data_hora: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
       entidade: Mapped["DisparoModel"] = relationship(back_populates="logs")

   # Repository Class
   class CampanhasRepository:
       def __init__(self, session: Session):
           self.session = session

       # Campaigns
       def create_campanha(self, data: CampanhaCreate) -> CampanhaRead:
           db_campanha = CampaignModel(**data.model_dump())
           self.session.add(db_campanha)
           self.session.flush()
           self._log_auditoria("CAMPAHA", db_campanha.id, AcaoAuditoria.CRIAR)
           self.session.commit()
           self.session.refresh(db_campanha)
           return CampanhaRead.model_validate(db_campanha)

       def get_campanha(self, campanha_id: UUID) -> Optional[CampanhaRead]:
           db_campanha = self.session.get(CampaignModel, campanha_id)
           if not db_campanha:
               return None
           return CampanhaRead.model_validate(db_campanha)

       # Disparos
       def criar_disparo(self, data: DisparoCreate) -> DisparoRead:
           db_disparo = DisparoModel(**data.model_dump())
           self.session.add(db_disparo)
           self.session.flush()
           self._log_auditoria("DISPARO", db_disparo.id, AcaoAuditoria.CRIAR)
           self.session.commit()
           self.session.refresh(db_disparo)
           return DisparoRead.model_validate(db_disparo)

       def atualizar_status_disparo(self, disparo_id: UUID, novo_status: DisparoStatus, confirmacao: Optional[bool] = None, detalhes: Optional[str] = None) -> Optional[DisparoRead]:
           db_disparo = self.session.get(DisparoModel, disparo_id)
           if not db_disparo:
               return None
           db_disparo.status = novo_status
           if confirmacao is not None:
               db_disparo.confirmacao_paciente = confirmacao
               db_disparo.data_confirmacao = datetime.utcnow()
               db_disparo.detalhes_confirmacao = detalhes
           if novo_status == DisparoStatus.ENVIADO:
               db_disparo.data_envio = datetime.utcnow()
           self.session.commit()
           self.session.refresh(db_disparo)
           self._log_auditoria("DISPARO", disparo_id, AcaoAuditoria.ATUALIZAR, justificativa=f"Status alterado para {novo_status.value}")
           return DisparoRead.model_validate(db_disparo)

       def listar_disparos_por_campanha(self, campanha_id: UUID) -> List[DisparoRead]:
           db_disparos = self.session.query(DisparoModel).filter_by(campanha_id=campanha_id).all()
           return [DisparoRead.model_validate(d) for d in db_disparos]

       # Auditoria
       def _log_auditoria(self, entidade_tipo: str, entidade_id: UUID, acao: AcaoAuditoria, usuario_id: Optional[UUID] = None, ip_origem: Optional[str] = None, justificativa: Optional[str] = None):
           log = LogAuditoriaModel(
               entidade_tipo=entidade_tipo,
               entidade_id=entidade_id,
               acao=acao,
               usuario_id=usuario_id,
               ip_origem=ip_origem,
               justificativa=justificativa
           )
           self.session.add(log)
           self.session.flush()

       def get_logs_auditoria(self, entidade_id: UUID) -> List[LogAuditoriaRead]:
           logs = self.session.query(LogAuditoriaModel).filter_by(entidade_id=entidade_id).order_by(LogAuditoriaModel.data_hora.desc()).all()
           return [LogAuditoriaRead.model_validate(l) for l in logs]
   ```

5.  **Refine & Check Requirements:**
   - Python 3.12, strict typing: Used `from __future__ import annotations`, type hints everywhere.
   - Pydantic v2: Used `BaseModel`, `Field`, `field_validator`, `ConfigDict`, `model_dump`, `model_validate`.
   - SQLAlchemy 2.0: Used `DeclarativeBase`, `Mapped`, `mapped_column`, `relationship`, `ForeignKey`, `func.now()`.
   - SUS/APS standards: CID-10, CIAP-2 validation in Pydantic. SOAP method? The prompt says "método SOAP". I should add a field or method related to SOAP clinical notes. I'll add `notas_soap` to Campaign or Disparo. Let's add it to Campaign as it's a health campaign context. Actually, SOAP is a clinical documentation method. I'll add `notas_soap` to `CampanhaBase` or create a separate model. To keep it focused on campaigns/dispatches, I'll add `notas_soap` as a JSON/text field in Campaign, or just document it. I'll add `notas_soap: str = ""` to `CampanhaBase` with validation.
   - CNS/CPF: Validated in Pydantic.
   - Audit log: Covered.
   - Test coverage: I need to provide pytest tests. The prompt says "Manter conformidade total e cobertura de testes automatizados com pytest." I should provide the test file as well, or at least ensure the code is testable. I'll create `tests/test_campanhas_repo.py` with comprehensive tests.
   - File path: `backend/app/repositories/campanhas_repo.py`

   Let's adjust the SOAP requirement. I'll add a `notas_soap` field to the campaign model and validate it. SOAP stands for Subjective, Objective, Assessment, Plan. I'll add a validator or just a field. I'll make it a structured JSON or text. For simplicity, I'll add `notas_soap: str = ""` and document it. Actually, I can add a Pydantic model for SOAP notes.

   Let's refine the Pydantic models to include SOAP structure:
   ```python
   class NotasSOAP(BaseModel):
       subjetiva: str
       objetiva: str
       avaliacao: str
       plano: str
   ```
   And add `notas_soap: Optional[NotasSOAP] = None` to `CampanhaBase`.

   Wait, the prompt says "Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF)." This implies these should be present in the data models. I'll ensure they are.

   Let's structure the code carefully. I'll also add type hints for SQLAlchemy relationships to avoid forward reference issues in Python 3.12. I'll use `TYPE_CHECK