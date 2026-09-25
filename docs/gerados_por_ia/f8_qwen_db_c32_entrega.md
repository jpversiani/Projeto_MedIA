Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for a "Health Campaigns Repository and Send History" (C32).
   - **Requirements:**
     - Track sent messages, confirmation status by patient, and data protection audit logs.
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification.
     - Full compliance and automated test coverage with pytest.
     - Provide complete, executable code. Specify file paths in code blocks.
   - **Context:** Project MedIA (likely a health tech platform).

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/campanhas_repo.py`
   - **Models/Tables:**
     - Campaigns (Campanhas de Saúde)
     - Message Sends/History (Histórico de Disparos)
     - Patient Confirmation Status (Status de Confirmação)
     - Data Protection Audit Log (Log de Auditoria LGPD)
   - **Standards:** CIAP-2 (Classificação Internacional de Atenção Primária), CID-10 (ICD-10), SOAP (Subjective, Objective, Assessment, Plan), CNS (Cartão Nacional de Saúde), CPF (Cadastro de Pessoas Físicas).
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0, pytest.
   - **Architecture:** Repository pattern, strict typing, compliance focus.

3.  **Design Database Models (SQLAlchemy 2.0):**
   Need to define SQLAlchemy models that map to these concepts.
   - `Campanha`: id, nome, descricao, status, criado_em, atualizado_em, cid10_codes (JSON/List), ciap2_codes (JSON/List)
   - `DisparoCampanha`: id, campanha_id, paciente_cns, paciente_cpf, mensagem, status_envio, enviado_em, confirmado_em, confirmado_por_paciente (bool), metodo_soap (JSON/structured), criado_em
   - `LogAuditoriaLGPD`: id, disparo_id, acao, detalhes, usuario_sistema, ip, criado_em, conformidade_lgpd (bool)

   Wait, the prompt says "rastreio de mensagens enviadas, status de confirmação pelo paciente e log de auditoria de proteção de dados." So I need models for:
   - `Campanha`
   - `Disparo` (Message Send)
   - `ConfirmacaoPaciente` (Patient Confirmation)
   - `LogAuditoriaLGPD` (Audit Log)

   Let's refine the models to be more aligned with SUS/APS standards and the requirements:
   - `Campanha`: id, titulo, descricao, status, cid10_codes (list[str]), ciap2_codes (list[str]), created_at, updated_at
   - `Disparo`: id, campanha_id, paciente_cns (str), paciente_cpf (str), mensagem, status (enum: PENDING, SENT, FAILED, CONFIRMED), enviado_em, confirmado_em, criado_at
   - `ConfirmacaoPaciente`: id, disparo_id, paciente_cns, confirmado_em, metodo (enum: SMS, WHATSAPP, EMAIL), observacao_soap (str - maybe not needed here, but SOAP is for clinical notes. I'll add a `notas_soap` field to `Campanha` or `Disparo` if relevant, but the prompt says "método SOAP" as a standard. I'll add it to `Campanha` or `Disparo` as a JSON field for clinical context, or just note it in the schema. Actually, SOAP is typically for clinical encounters. I'll add `notas_soap` to `Campanha` or `Disparo` as a structured JSON field to comply with the requirement.)
   - `LogAuditoriaLGPD`: id, disparo_id, acao (enum: CREATE, READ, UPDATE, DELETE, EXPORT), detalhes, usuario_id, ip_address, criado_em, conformidade (bool)

   Let's stick to SQLAlchemy 2.0 declarative style with `Mapped`, `mapped_column`, `MappedAsDataclass` or standard `DeclarativeBase`. I'll use `DeclarativeBase` for clarity.

   Pydantic v2 models for request/response/validation.

4.  **Design Repository Methods:**
   - `criar_campanha`
   - `listar_campanhas`
   - `registrar_disparo`
   - `atualizar_status_disparo`
   - `registrar_confirmacao_paciente`
   - `registrar_log_auditoria`
   - `obter_historico_disparos`
   - `obter_relatorio_conformidade_lgpd`

   All methods should use SQLAlchemy 2.0 async or sync? I'll use sync for simplicity but note it can be async. The prompt doesn't specify async, so I'll stick to sync SQLAlchemy 2.0 with `Session`.

   I'll define Pydantic schemas for validation.

5.  **Structure the Code:**
   ```python
   # Arquivo: backend/app/repositories/campanhas_repo.py
   from __future__ import annotations
   from datetime import datetime
   from enum import Enum
   from typing import List, Optional
   from uuid import uuid4

   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy import (
       String, Text, DateTime, Boolean, ForeignKey, Enum as SAEnum, JSON
   )
   from sqlalchemy.orm import (
       DeclarativeBase, Mapped, mapped_column, relationship, Session
   )
   import enum

   # Base
   class Base(DeclarativeBase):
       pass

   # Enums
   class StatusCampanha(str, Enum):
       RASCUNHO = "rascunho"
       ATIVA = "ativa"
       PAUSADA = "pausada"
       CONCLUIDA = "concluida"

   class StatusDisparo(str, Enum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       FALHA = "falha"
       CONFIRMADO = "confirmado"

   class AcaoAuditoria(str, Enum):
       CREATE = "CREATE"
       READ = "READ"
       UPDATE = "UPDATE"
       DELETE = "DELETE"
       EXPORT = "EXPORT"

   # SQLAlchemy Models
   class CampanhaModel(Base):
       __tablename__ = "campanhas"
       id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
       titulo: Mapped[str] = mapped_column(String(255), nullable=False)
       descricao: Mapped[str] = mapped_column(Text, nullable=False)
       status: Mapped[StatusCampanha] = mapped_column(SAEnum(StatusCampanha), default=StatusCampanha.RASCUNHO)
       cid10_codes: Mapped[List[str]] = mapped_column(JSON, default=list)
       ciap2_codes: Mapped[List[str]] = mapped_column(JSON, default=list)
       notas_soap: Mapped[dict] = mapped_column(JSON, default=dict)
       criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

       disparos = relationship("DisparoModel", back_populates="campanha", cascade="all, delete-orphan")
       logs_auditoria = relationship("LogAuditoriaLGPDModel", back_populates="campanha", cascade="all, delete-orphan")

   class DisparoModel(Base):
       __tablename__ = "disparos_campanha"
       id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
       campanha_id: Mapped[str] = mapped_column(String(36), ForeignKey("campanhas.id"), nullable=False)
       paciente_cns: Mapped[str] = mapped_column(String(15), nullable=False)
       paciente_cpf: Mapped[str] = mapped_column(String(14), nullable=False)
       mensagem: Mapped[str] = mapped_column(Text, nullable=False)
       status: Mapped[StatusDisparo] = mapped_column(SAEnum(StatusDisparo), default=StatusDisparo.PENDENTE)
       enviado_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
       confirmado_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
       criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

       campanha = relationship("CampanhaModel", back_populates="disparos")
       confirmacoes = relationship("ConfirmacaoPacienteModel", back_populates="disparo", cascade="all, delete-orphan")
       logs_auditoria = relationship("LogAuditoriaLGPDModel", back_populates="disparo", cascade="all, delete-orphan")

   class ConfirmacaoPacienteModel(Base):
       __tablename__ = "confirmacoes_paciente"
       id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
       disparo_id: Mapped[str] = mapped_column(String(36), ForeignKey("disparos_campanha.id"), nullable=False)
       paciente_cns: Mapped[str] = mapped_column(String(15), nullable=False)
       confirmado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       canal: Mapped[str] = mapped_column(String(50), default="SMS")
       observacao: Mapped[str] = mapped_column(Text, nullable=True)

       disparo = relationship("DisparoModel", back_populates="confirmacoes")

   class LogAuditoriaLGPDModel(Base):
       __tablename__ = "logs_auditoria_lgpd"
       id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
       disparo_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("disparos_campanha.id"), nullable=True)
       campanha_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("campanhas.id"), nullable=True)
       acao: Mapped[AcaoAuditoria] = mapped_column(SAEnum(AcaoAuditoria), nullable=False)
       detalhes: Mapped[str] = mapped_column(Text, nullable=False)
       usuario_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
       ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
       criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       conformidade_lgpd: Mapped[bool] = mapped_column(Boolean, default=True)

       disparo = relationship("DisparoModel", back_populates="logs_auditoria")
       campanha = relationship("CampanhaModel", back_populates="logs_auditoria")

   # Pydantic Schemas
   class CampanhaCreate(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       titulo: str = Field(..., min_length=1, max_length=255)
       descricao: str = Field(..., min_length=1)
       cid10_codes: List[str] = Field(default_factory=list)
       ciap2_codes: List[str] = Field(default_factory=list)
       notas_soap: dict = Field(default_factory=dict)

       @field_validator("cid10_codes", "ciap2_codes")
       @classmethod
       def validate_codes(cls, v):
           # Basic validation for SUS standards
           for code in v:
               if not code.strip():
                   raise ValueError("Códigos não podem estar vazios.")
           return v

   class DisparoCreate(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       campanha_id: str
       paciente_cns: str = Field(..., pattern=r"^\d{15}$")
       paciente_cpf: str = Field(..., pattern=r"^\d{11}$")
       mensagem: str = Field(..., min_length=1)

   class ConfirmacaoCreate(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       disparo_id: str
       paciente_cns: str = Field(..., pattern=r"^\d{15}$")
       canal: str = Field(default="SMS")
       observacao: Optional[str] = None

   class AuditoriaLogCreate(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       disparo_id: Optional[str] = None
       campanha_id: Optional[str] = None
       acao: AcaoAuditoria
       detalhes: str
       usuario_id: Optional[str] = None
       ip_address: Optional[str] = None

   # Repository Class
   class CampanhasRepository:
       def __init__(self, session: Session):
           self.session = session

       def criar_campanha(self, schema: CampanhaCreate) -> CampanhaModel:
           self._log_auditoria(acao=AcaoAuditoria.CREATE, detalhes=f"Criação de campanha: {schema.titulo}")
           campanha = CampanhaModel(
               titulo=schema.titulo,
               descricao=schema.descricao,
               cid10_codes=schema.cid10_codes,
               ciap2_codes=schema.ciap2_codes,
               notas_soap=schema.notas_soap,
           )
           self.session.add(campanha)
           self.session.flush()
           return campanha

       def registrar_disparo(self, schema: DisparoCreate) -> DisparoModel:
           self._log_auditoria(acao=AcaoAuditoria.CREATE, detalhes=f"Registro de disparo para CNS: {schema.paciente_cns}")
           disparo = DisparoModel(
               campanha_id=schema.campanha_id,
               paciente_cns=schema.paciente_cns,
               paciente_cpf=schema.paciente_cpf,
               mensagem=schema.mensagem,
               status=StatusDisparo.PENDENTE,
           )
           self.session.add(disparo)
           self.session.flush()
           return disparo

       def atualizar_status_disparo(self, disparo_id: str, novo_status: StatusDisparo) -> DisparoModel:
           disparo = self.session.get(DisparoModel, disparo_id)
           if not disparo:
               raise ValueError("Disparo não encontrado.")
           disparo.status = novo_status
           if novo_status == StatusDisparo.ENVIADO:
               disparo.enviado_em = datetime.utcnow()
           self._log_auditoria(acao=AcaoAuditoria.UPDATE, detalhes=f"Status do disparo {disparo_id} alterado para {novo_status.value}")
           self.session.flush()
           return disparo

       def registrar_confirmacao(self, schema: ConfirmacaoCreate) -> ConfirmacaoPacienteModel:
           disparo = self.session.get(DisparoModel, schema.disparo_id)
           if not disparo:
               raise ValueError("Disparo não encontrado.")
           if disparo.status == StatusDisparo.CONFIRMADO:
               raise ValueError("Disparo já confirmado.")

           confirmacao = ConfirmacaoPacienteModel(
               disparo_id=schema.disparo_id,
               paciente_cns=schema.paciente_cns,
               canal=schema.canal,
               observacao=schema.observacao,
           )
           self.session.add(confirmacao)
           disparo.status = StatusDisparo.CONFIRMADO
           disparo.confirmado_em = datetime.utcnow()
           self._log_auditoria(acao=AcaoAuditoria.UPDATE, detalhes=f"Confirmação de paciente CNS {schema.paciente_cns} registrada para disparo {schema.disparo_id}")
           self.session.flush()
           return confirmacao

       def obter_historico_disparos(self, campanha_id: str) -> List[DisparoModel]:
           return self.session.query(DisparoModel).filter_by(campanha_id=campanha_id).all()

       def obter_logs_auditoria(self, disparo_id: Optional[str] = None, campanha_id: Optional[str] = None) -> List[LogAuditoriaLGPDModel]:
           query = self.session.query(LogAuditoriaLGPDModel)
           if disparo_id:
               query = query.filter_by(disparo_id=disparo_id)
           if campanha_id:
               query = query.filter_by(campanha_id=campanha_id)
           return query.all()

       def _log_auditoria(self, acao: AcaoAuditoria, detalhes: str):
           log = LogAuditoriaLGPDModel(
               acao=acao,
               detalhes=detalhes,
               ip_address="127.0.0.1", # Mock for repo layer
               conformidade_lgpd=True,
           )
           self.session.add(log)
           self.session.flush()
   ```

6.  **Add Pytest Tests:**
   Need comprehensive tests covering:
   - Campaign creation with validation
   - Message dispatch registration
   - Status updates
   - Patient confirmation
   - Audit logging
   - SUS/APS standards compliance (CID-10, CIAP-2, CNS, CPF, SOAP)
   - Data protection compliance (LGPD audit logs)

   I'll create a test file: `backend/app/repositories/test_campanhas_repo.py`
   Use `pytest`, `sqlalchemy`, `pytest-mock` or just in-memory SQLite.
   I'll use `pytest` with `sessionmaker` and `create_engine` for testing.

   Structure of tests:
   - `test_criar_campanha_valida`
   - `test_criar_campanha_invalida_cid10`
   - `test_registrar_disparo`
   - `test_atualizar_status_disparo`
   - `test_registrar_confirmacao_paciente`
   - `test_obter_historico_disparos`
   - `test_logs_auditoria_lgpd`
   - `test_valid