Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` with models and methods for:
     - Tracking sent messages
     - Patient confirmation status
     - Data protection audit log
   - **Project:** MedIA
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification
     - Full compliance and automated test coverage with pytest
   - **Output Requirement:** Provide complete, executable code. Specify file path for each file/block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/campanhas_repo.py`
   - **Models (Pydantic v2):** Need request/response schemas for campaigns, message tracking, confirmation status, audit logs.
   - **Database Models (SQLAlchemy 2.0):** Need ORM models corresponding to the Pydantic schemas.
   - **Repository Methods:** CRUD operations, tracking, status updates, audit logging.
   - **Standards Integration:** CIAP-2, CID-10, SOAP, CNS/CPF should be referenced/validated in the models.
   - **Testing:** Provide pytest tests covering the repository functionality.
   - **Compliance:** LGPD (Brazilian data protection law) considerations for audit logs.

3.  **Design - Database Models (SQLAlchemy 2.0):**
   - `Campanha`: ID, name, description, status, created_at, updated_at, ciap2_code, cid10_code
   - `MensagemCampanha`: ID, campanha_id, paciente_cns, paciente_cpf, message_content, status (sent, delivered, confirmed, failed), sent_at, confirmed_at, confirmation_status
   - `AuditoriaProtecaoDados`: ID, campanha_id, mensagem_id, action, user_id, timestamp, ip_address, details, compliance_status

   Let's refine with SQLAlchemy 2.0 syntax:
   ```python
   from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
   from datetime import datetime
   import enum

   class Base(DeclarativeBase):
       pass

   class CampanhaStatus(enum.Enum):
       DRAFT = "draft"
       ACTIVE = "active"
       PAUSED = "paused"
       COMPLETED = "completed"

   class MensagemStatus(enum.Enum):
       PENDING = "pending"
       SENT = "sent"
       DELIVERED = "delivered"
       CONFIRMED = "confirmed"
       FAILED = "failed"

   class AuditoriaAcao(enum.Enum):
       CREATE = "create"
       UPDATE = "update"
       DELETE = "delete"
       ACCESS = "access"
       EXPORT = "export"
       DATA_SUBJECT_REQUEST = "data_subject_request"

   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[int] = mapped_column(primary_key=True)
       nome: Mapped[str] = mapped_column(String(255), nullable=False)
       descricao: Mapped[str] = mapped_column(Text, nullable=True)
       ciap2_code: Mapped[str] = mapped_column(String(10), nullable=True) # CIAP-2 codes are typically short
       cid10_code: Mapped[str] = mapped_column(String(10), nullable=True) # CID-10 codes
       status: Mapped[CampanhaStatus] = mapped_column(Enum(CampanhaStatus), default=CampanhaStatus.DRAFT)
       created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

   class MensagemCampanha(Base):
       __tablename__ = "mensagens_campanhas"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"), nullable=False)
       paciente_cns: Mapped[str] = mapped_column(String(15), nullable=True) # CNS is 15 digits
       paciente_cpf: Mapped[str] = mapped_column(String(14), nullable=True) # CPF is 14 chars
       conteudo: Mapped[str] = mapped_column(Text, nullable=False)
       status: Mapped[MensagemStatus] = mapped_column(Enum(MensagemStatus), default=MensagemStatus.PENDING)
       metodo_soap: Mapped[str] = mapped_column(String(50), nullable=True) # SOAP method reference
       enviado_em: Mapped[datetime] = mapped_column(DateTime, nullable=True)
       confirmado_em: Mapped[datetime] = mapped_column(DateTime, nullable=True)
       status_confirmacao: Mapped[str] = mapped_column(String(50), nullable=True) # e.g., "read", "acknowledged", "declined"
       campanha = relationship("Campanha", back_populates="mensagens")

   class AuditoriaProtecaoDados(Base):
       __tablename__ = "auditoria_protecao_dados"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"), nullable=True)
       mensagem_id: Mapped[int] = mapped_column(ForeignKey("mensagens_campanhas.id"), nullable=True)
       acao: Mapped[AuditoriaAcao] = mapped_column(Enum(AuditoriaAcao), nullable=False)
       usuario_id: Mapped[str] = mapped_column(String(36), nullable=True) # UUID
       timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
       detalhes: Mapped[str] = mapped_column(Text, nullable=True)
       conformidade_lgpd: Mapped[bool] = mapped_column(Boolean, default=True)
   ```

4.  **Design - Pydantic Models (v2):**
   Need schemas for validation, serialization, and API contracts.
   - `CampanhaCreate`, `CampanhaRead`, `CampanhaUpdate`
   - `MensagemCampanhaCreate`, `MensagemCampanhaRead`, `MensagemStatusUpdate`
   - `AuditoriaLogCreate`, `AuditoriaLogRead`
   - Use `ConfigDict`, `field_validator`, `model_validator` for strict typing and validation.
   - Validate CNS/CPF formats, CIAP-2/CID-10 formats, SOAP method.

   Let's draft them:
   ```python
   from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
   from datetime import datetime
   from typing import Optional
   import re

   class CampanhaBase(BaseModel):
       nome: str = Field(..., min_length=1, max_length=255)
       descricao: Optional[str] = None
       ciap2_code: Optional[str] = Field(None, pattern=r"^[A-Z0-9]{1,10}$")
       cid10_code: Optional[str] = Field(None, pattern=r"^[A-Z0-9]{1,10}$")

   class CampanhaCreate(CampanhaBase):
       pass

   class CampanhaRead(CampanhaBase):
       model_config = ConfigDict(from_attributes=True)
       id: int
       status: str
       created_at: datetime
       updated_at: datetime

   class CampanhaUpdate(BaseModel):
       nome: Optional[str] = Field(None, min_length=1, max_length=255)
       descricao: Optional[str] = None
       ciap2_code: Optional[str] = Field(None, pattern=r"^[A-Z0-9]{1,10}$")
       cid10_code: Optional[str] = Field(None, pattern=r"^[A-Z0-9]{1,10}$")
       status: Optional[str] = None

   class MensagemCampanhaBase(BaseModel):
       campanha_id: int
       paciente_cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       paciente_cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       conteudo: str = Field(..., min_length=1)
       metodo_soap: Optional[str] = Field(None, pattern=r"^(GET|POST|PUT|DELETE|PATCH)$")

   class MensagemCampanhaCreate(MensagemCampanhaBase):
       pass

   class MensagemCampanhaRead(MensagemCampanhaBase):
       model_config = ConfigDict(from_attributes=True)
       id: int
       status: str
       enviado_em: Optional[datetime] = None
       confirmado_em: Optional[datetime] = None
       status_confirmacao: Optional[str] = None

   class MensagemStatusUpdate(BaseModel):
       status: str
       status_confirmacao: Optional[str] = None

   class AuditoriaLogBase(BaseModel):
       campanha_id: Optional[int] = None
       mensagem_id: Optional[int] = None
       acao: str
       usuario_id: Optional[str] = None
       ip_address: Optional[str] = Field(None, pattern=r"^\d{1,3}(\.\d{1,3}){3}$")
       detalhes: Optional[str] = None
       conformidade_lgpd: bool = True

   class AuditoriaLogCreate(AuditoriaLogBase):
       pass

   class AuditoriaLogRead(AuditoriaLogBase):
       model_config = ConfigDict(from_attributes=True)
       id: int
       timestamp: datetime
   ```

5.  **Design - Repository Class:**
   Need a class that interacts with SQLAlchemy session.
   Methods:
   - `create_campanha`
   - `get_campanha`
   - `update_campanha`
   - `delete_campanha`
   - `create_mensagem`
   - `update_mensagem_status`
   - `get_mensagens_by_campanha`
   - `log_auditoria`
   - `get_auditoria_logs`
   - `get_mensagens_nao_confirmadas`
   - `get_mensagens_confirmadas`

   I'll use `sqlalchemy.ext.asyncio` or sync? The prompt doesn't specify async/sync. I'll stick to sync SQLAlchemy 2.0 for simplicity, but make it easily adaptable. I'll use `Session` from `sqlalchemy.orm`.

   Let's draft the repository:
   ```python
   from sqlalchemy.orm import Session
   from sqlalchemy import select, update, delete
   from datetime import datetime
   from typing import List, Optional
   import uuid

   class CampanhasRepository:
       def __init__(self, session: Session):
           self.session = session

       # Campanhas
       def create_campanha(self, data: CampanhaCreate) -> Campanha:
           db_campanha = Campanha(**data.model_dump())
           self.session.add(db_campanha)
           self.session.flush()
           self.log_auditoria(
               campanha_id=db_campanha.id,
               acao=AuditoriaAcao.CREATE,
               detalhes=f"Campanha criada: {db_campanha.nome}"
           )
           self.session.commit()
           self.session.refresh(db_campanha)
           return db_campanha

       def get_campanha(self, campanha_id: int) -> Optional[Campanha]:
           stmt = select(Campanha).where(Campanha.id == campanha_id)
           return self.session.execute(stmt).scalar_one_or_none()

       def update_campanha(self, campanha_id: int, data: CampanhaUpdate) -> Optional[Campanha]:
           campanha = self.get_campanha(campanha_id)
           if not campanha:
               return None
           update_data = data.model_dump(exclude_unset=True)
           for key, value in update_data.items():
               setattr(campanha, key, value)
           campanha.updated_at = datetime.utcnow()
           self.session.add(campanha)
           self.session.commit()
           self.session.refresh(campanha)
           self.log_auditoria(
               campanha_id=campanha_id,
               acao=AuditoriaAcao.UPDATE,
               detalhes=f"Campanha atualizada: {campanha.nome}"
           )
           return campanha

       def delete_campanha(self, campanha_id: int) -> bool:
           campanha = self.get_campanha(campanha_id)
           if not campanha:
               return False
           self.session.delete(campanha)
           self.session.commit()
           self.log_auditoria(
               campanha_id=campanha_id,
               acao=AuditoriaAcao.DELETE,
               detalhes=f"Campanha deletada: {campanha.nome}"
           )
           return True

       # Mensagens
       def create_mensagem(self, data: MensagemCampanhaCreate) -> MensagemCampanha:
           db_mensagem = MensagemCampanha(**data.model_dump())
           self.session.add(db_mensagem)
           self.session.flush()
           self.log_auditoria(
               mensagem_id=db_mensagem.id,
               acao=AuditoriaAcao.CREATE,
               detalhes=f"Mensagem criada para CNS: {db_mensagem.paciente_cns}"
           )
           self.session.commit()
           self.session.refresh(db_mensagem)
           return db_mensagem

       def update_mensagem_status(self, mensagem_id: int, data: MensagemStatusUpdate) -> Optional[MensagemCampanha]:
           stmt = select(MensagemCampanha).where(MensagemCampanha.id == mensagem_id)
           mensagem = self.session.execute(stmt).scalar_one_or_none()
           if not mensagem:
               return None

           update_data = data.model_dump(exclude_unset=True)
           if "status" in update_data:
               mensagem.status = MensagemStatus(update_data["status"])
               if update_data["status"] == "SENT":
                   mensagem.enviado_em = datetime.utcnow()
           if "status_confirmacao" in update_data:
               mensagem.status_confirmacao = update_data["status_confirmacao"]
               if update_data["status_confirmacao"] == "CONFIRMED":
                   mensagem.confirmado_em = datetime.utcnow()

           self.session.add(mensagem)
           self.session.commit()
           self.session.refresh(mensagem)
           self.log_auditoria(
               mensagem_id=mensagem_id,
               acao=AuditoriaAcao.UPDATE,
               detalhes=f"Status atualizado para: {mensagem.status.value}"
           )
           return mensagem

       def get_mensagens_by_campanha(self, campanha_id: int) -> List[MensagemCampanha]:
           stmt = select(MensagemCampanha).where(MensagemCampanha.campanha_id == campanha_id)
           return list(self.session.execute(stmt).scalars().all())

       def get_mensagens_nao_confirmadas(self, campanha_id: int) -> List[MensagemCampanha]:
           stmt = (
               select(MensagemCampanha)
               .where(
                   MensagemCampanha.campanha_id == campanha_id,
                   MensagemCampanha.status == MensagemStatus.SENT,
                   MensagemCampanha.status_confirmacao.is_(None)
               )
           )
           return list(self.session.execute(stmt).scalars().all())

       # Auditoria
       def log_auditoria(self, campanha_id: Optional[int] = None, mensagem_id: Optional[int] = None,
                         acao: AuditoriaAcao = AuditoriaAcao.ACCESS, usuario_id: Optional[str] = None,
                         ip_address: Optional[str] = None, detalhes: Optional[str] = None) -> AuditoriaProtecaoDados:
           log = AuditoriaProtecaoDados(
               campanha_id=campanha_id,
               mensagem_id=mensagem_id,
               acao=acao,
               usuario_id=usuario_id or str(uuid.uuid4()),
               ip_address=ip_address,
               detalhes=detalhes,
               conformidade_lgpd=True
           )
           self.session.add(log)
           self.session.commit()
           self.session.refresh(log)
           return log

       def get_auditoria_logs(self, campanha_id: Optional[int] = None, mensagem_id: Optional[int] = None,
                              acao: Optional[AuditoriaAcao] = None, limit: int = 100) -> List[AuditoriaProtecaoDados]:
           conditions = []
           if campanha_id:
               conditions.append(AuditoriaProtecaoDados.campanha_id == campanha_id)
           if mensagem_id:
               conditions.append(AuditoriaProtecaoDados.mensagem_id == mensagem_id)
           if acao:
               conditions.append(AuditoriaProtecaoDados.acao == acao)

           stmt = select(AuditoriaProtecaoDados).where(*conditions).order_by(AuditoriaProtecaoDados.timestamp.desc()).limit(limit)
           return list(self.session.execute(stmt).scalars().all())
   ```

6.  **Design - Pytest Tests:**
   Need to test the repository with an in-memory SQLite database.
   - Setup: Create engine, session, tables.
   - Test cases:
     - Create/Read/Update/Delete Campanha
     - Create/Update Mensagem status
     - Audit log creation and retrieval
     - Validation errors (Pydantic)
     - CNS/CPF validation
     - CIAP-2/CID-10 validation
   - Use `pytest`, `sqlalchemy`, `pydantic`.

   Let's draft the test file: `tests/test_campanhas_repo.py`
   I'll structure it carefully.

   ```python
   import pytest
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from datetime import datetime
   from backend.app.repositories.campanhas_repo import (
       Base, CampanhasRepository, Campanha, MensagemCampanha, AuditoriaProtecaoDados,
       CampanhaCreate,