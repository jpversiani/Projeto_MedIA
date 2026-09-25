Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for a project called "MedIA".
   - **Features:** Campaign repository with models and methods for:
     - Tracking sent messages
     - Confirmation status by patient
     - Audit log for data protection
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification
     - Full compliance and automated test coverage with pytest
   - **Output Requirement:** Provide complete, executable code. Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/campanhas_repo.py`
   - **Models (Pydantic v2):** Need schemas for Campaign, MessageLog, PatientConfirmation, AuditLog.
   - **Database Models (SQLAlchemy 2.0):** Need ORM models mapping to the above.
   - **Repository Methods:** CRUD for campaigns, track messages, update confirmation status, log audit events.
   - **Standards:** Include fields for CIAP-2, CID-10, SOAP notes, CNS/CPF.
   - **Testing:** Provide pytest tests covering the repository methods.
   - **Compliance:** Data protection (LGPD) considerations in audit logs, encryption/hashing hints, strict typing.

3.  **Design Database Models (SQLAlchemy 2.0):**
   - `Campanha`: id, nome, descricao, status, cid10, ciap2, soap_note, created_at, updated_at
   - `MensagemEnviada`: id, campanha_id, paciente_cpf, paciente_cns, status_envio, mensagem, enviado_em, confirmado_por_paciente, confirmado_em
   - `AuditLog`: id, campanha_id, acao, detalhes, usuario, timestamp, ip_address, hash_dados (for LGPD compliance)
   - Use `Mapped`, `mapped_column`, `relationship`, `ForeignKey`, `DateTime`, `String`, `Boolean`, `Enum`, etc.

4.  **Design Pydantic Schemas (v2):**
   - `CampanhaCreate`, `CampanhaUpdate`, `CampanhaRead`
   - `MensagemCreate`, `MensagemUpdate`, `MensagemRead`
   - `AuditLogCreate`, `AuditLogRead`
   - Use `BaseModel`, `Field`, `ConfigDict`, `computed_field` if needed.

5.  **Design Repository Class:**
   - `class CampanhasRepository:`
   - Methods: `create_campanha`, `get_campanha`, `update_campanha`, `delete_campanha`
   - `enviar_mensagem`, `atualizar_confirmacao_paciente`
   - `registrar_auditoria`, `obter_logs_auditoria`
   - Use dependency injection pattern for `Session` (common in FastAPI/SQLAlchemy apps). I'll design it to accept a `Session` or use a context manager, but for a repository file, I'll make it accept a `Session` in methods or use a class-level session manager. Actually, standard practice is to pass `session` to methods or use `__init__(self, session: Session)`. I'll go with method-level session injection for testability, or a class that takes a session. Let's use a class that accepts a session in `__init__` or just static methods with session parameter. I'll stick to instance methods with `session` passed explicitly for clarity and testability.

   Wait, the prompt says "código completo e executável". I should provide a self-contained file that can be run/tested. I'll include a `Base` declarative base, models, schemas, repository class, and a test file. But the prompt specifically asks for `backend/app/repositories/campanhas_repo.py`. I'll provide that file, and then the test file separately as requested ("cobertura de testes automatizados com pytest").

   Let's structure `campanhas_repo.py`:
   - Imports
   - SQLAlchemy Models
   - Pydantic Schemas
   - Repository Class
   - Helper functions (if needed)
   - I'll make it compatible with SQLAlchemy 2.0 declarative style.

6.  **Draft - SQLAlchemy Models:**
   ```python
   from datetime import datetime
   from enum import Enum
   from typing import Optional, List
   from sqlalchemy import (
       String, Text, Boolean, DateTime, ForeignKey, Enum as SAEnum,
       Index, UniqueConstraint
   )
   from sqlalchemy.orm import (
       DeclarativeBase, Mapped, mapped_column, relationship, Session
   )
   from sqlalchemy.sql import func

   class Base(DeclarativeBase):
       pass

   class CampanhaStatus(str, Enum):
       RASCUNHO = "rascunho"
       ATIVA = "ativa"
       PAUSADA = "pausada"
       CONCLUIDA = "concluida"

   class MensagemStatus(str, Enum):
       PENDENTE = "pendente"
       ENVIADA = "enviada"
       FALHA = "falha"
       CONFIRMADA = "confirmada"

   class Campanha(Base):
       __tablename__ = "campanhas"

       id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
       nome: Mapped[str] = mapped_column(String(255), nullable=False)
       descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       status: Mapped[CampanhaStatus] = mapped_column(SAEnum(CampanhaStatus), default=CampanhaStatus.RASCUNHO)
       cid10: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
       ciap2: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
       soap_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

       mensagens: Mapped[List["Mensagem"]] = relationship(back_populates="campanha", cascade="all, delete-orphan")
       logs_auditoria: Mapped[List["AuditLog"]] = relationship(back_populates="campanha", cascade="all, delete-orphan")

   class Mensagem(Base):
       __tablename__ = "mensagens"
       __table_args__ = (UniqueConstraint("campanha_id", "paciente_cpf"),)

       id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id", ondelete="CASCADE"))
       paciente_cpf: Mapped[str] = mapped_column(String(14), nullable=False)
       paciente_cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       status: Mapped[MensagemStatus] = mapped_column(SAEnum(MensagemStatus), default=MensagemStatus.PENDENTE)
       conteudo: Mapped[str] = mapped_column(Text, nullable=False)
       enviado_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
       confirmado_por_paciente: Mapped[bool] = mapped_column(Boolean, default=False)
       confirmado_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

       campanha: Mapped["Campanha"] = relationship(back_populates="mensagens")

   class AuditLog(Base):
       __tablename__ = "logs_auditoria"

       id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id", ondelete="SET NULL"))
       acao: Mapped[str] = mapped_column(String(50), nullable=False)
       detalhes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       usuario: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
       timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
       hash_dados: Mapped[Optional[str]] = mapped_column(String(64), nullable=True) # SHA-256 for LGPD

       campanha: Mapped["Campanha"] = relationship(back_populates="logs_auditoria")
   ```

7.  **Draft - Pydantic Schemas:**
   ```python
   from pydantic import BaseModel, Field, ConfigDict, EmailStr
   from typing import Optional, List
   from datetime import datetime
   from enum import Enum

   class CampanhaStatusEnum(str, Enum):
       RASCUNHO = "rascunho"
       ATIVA = "ativa"
       PAUSADA = "pausada"
       CONCLUIDA = "concluida"

   class CampanhaBase(BaseModel):
       nome: str = Field(..., min_length=1, max_length=255)
       descricao: Optional[str] = None
       cid10: Optional[str] = Field(None, pattern=r"^[A-Z][0-9][0-9A-Z]$")
       ciap2: Optional[str] = Field(None, pattern=r"^[A-Z][0-9][0-9A-Z]$")
       soap_note: Optional[str] = None

   class CampanhaCreate(CampanhaBase):
       pass

   class CampanhaUpdate(CampanhaBase):
       status: Optional[CampanhaStatusEnum] = None

   class CampanhaRead(CampanhaBase):
       model_config = ConfigDict(from_attributes=True)
       id: int
       status: CampanhaStatusEnum
       created_at: datetime
       updated_at: datetime

   class MensagemStatusEnum(str, Enum):
       PENDENTE = "pendente"
       ENVIADA = "enviada"
       FALHA = "falha"
       CONFIRMADA = "confirmada"

   class MensagemBase(BaseModel):
       paciente_cpf: str = Field(..., pattern=r"^\d{11}$")
       paciente_cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       conteudo: str = Field(..., min_length=1)

   class MensagemCreate(MensagemBase):
       campanha_id: int

   class MensagemUpdate(BaseModel):
       status: Optional[MensagemStatusEnum] = None
       confirmado_por_paciente: Optional[bool] = None

   class MensagemRead(MensagemBase):
       model_config = ConfigDict(from_attributes=True)
       id: int
       campanha_id: int
       status: MensagemStatusEnum
       enviado_em: Optional[datetime]
       confirmado_por_paciente: bool
       confirmado_em: Optional[datetime]

   class AuditLogBase(BaseModel):
       campanha_id: Optional[int] = None
       acao: str = Field(..., min_length=1, max_length=50)
       detalhes: Optional[str] = None
       usuario: Optional[str] = None
       ip_address: Optional[str] = None

   class AuditLogCreate(AuditLogBase):
       hash_dados: Optional[str] = Field(None, pattern=r"^[a-fA-F0-9]{64}$")

   class AuditLogRead(AuditLogBase):
       model_config = ConfigDict(from_attributes=True)
       id: int
       timestamp: datetime
       hash_dados: Optional[str]
   ```

8.  **Draft - Repository Class:**
   Need to handle DB session, transactions, and methods.
   ```python
   from sqlalchemy.orm import Session
   from sqlalchemy import select, update, delete
   from typing import List, Optional
   import hashlib
   from contextlib import contextmanager

   class CampanhasRepository:
       def __init__(self, session: Session):
           self.session = session

       def _hash_sensitive_data(self, data: str) -> str:
           return hashlib.sha256(data.encode("utf-8")).hexdigest()

       # Campanhas
       def criar_campanha(self, schema: CampanhaCreate) -> CampanhaRead:
           db_campanha = Campanha(**schema.model_dump())
           self.session.add(db_campanha)
           self.session.flush()
           self.session.refresh(db_campanha)
           self.registrar_auditoria(
               campanha_id=db_campanha.id,
               acao="CRIAR_CAMPAHNA",
               detalhes=f"Campanha '{db_campanha.nome}' criada.",
               hash_dados=self._hash_sensitive_data(db_campanha.nome)
           )
           return CampanhaRead.model_validate(db_campanha)

       def buscar_campanha(self, campanha_id: int) -> Optional[CampanhaRead]:
           stmt = select(Campanha).where(Campanha.id == campanha_id)
           db_campanha = self.session.execute(stmt).scalar_one_or_none()
           return CampanhaRead.model_validate(db_campanha) if db_campanha else None

       def atualizar_campanha(self, campanha_id: int, schema: CampanhaUpdate) -> Optional[CampanhaRead]:
           stmt = select(Campanha).where(Campanha.id == campanha_id)
           db_campanha = self.session.execute(stmt).scalar_one_or_none()
           if not db_campanha:
               return None
           for key, value in schema.model_dump(exclude_unset=True).items():
               setattr(db_campanha, key, value)
           self.session.flush()
           self.session.refresh(db_campanha)
           self.registrar_auditoria(
               campanha_id=campanha_id,
               acao="ATUALIZAR_CAMPAHNA",
               detalhes=f"Campanha '{db_campanha.nome}' atualizada.",
               hash_dados=self._hash_sensitive_data(db_campanha.nome)
           )
           return CampanhaRead.model_validate(db_campanha)

       # Mensagens
       def registrar_envio_mensagem(self, schema: MensagemCreate) -> MensagemRead:
           db_msg = Mensagem(
               campanha_id=schema.campanha_id,
               paciente_cpf=schema.paciente_cpf,
               paciente_cns=schema.paciente_cns,
               conteudo=schema.conteudo,
               status=MensagemStatus.ENVIADA,
               enviado_em=datetime.utcnow()
           )
           self.session.add(db_msg)
           self.session.flush()
           self.session.refresh(db_msg)
           self.registrar_auditoria(
               campanha_id=schema.campanha_id,
               acao="ENVIAR_MENSAGEM",
               detalhes=f"Mensagem enviada para CPF {schema.paciente_cpf}",
               hash_dados=self._hash_sensitive_data(schema.paciente_cpf)
           )
           return MensagemRead.model_validate(db_msg)

       def atualizar_confirmacao_paciente(self, mensagem_id: int, confirmado: bool) -> Optional[MensagemRead]:
           stmt = select(Mensagem).where(Mensagem.id == mensagem_id)
           db_msg = self.session.execute(stmt).scalar_one_or_none()
           if not db_msg:
               return None
           db_msg.confirmado_por_paciente = confirmado
           db_msg.confirmado_em = datetime.utcnow()
           if confirmado:
               db_msg.status = MensagemStatus.CONFIRMADA
           self.session.flush()
           self.session.refresh(db_msg)
           self.registrar_auditoria(
               campanha_id=db_msg.campanha_id,
               acao="CONFIRMAR_MENSAGEM",
               detalhes=f"Confirmação de CPF {db_msg.paciente_cpf} atualizada para {confirmado}",
               hash_dados=self._hash_sensitive_data(db_msg.paciente_cpf)
           )
           return MensagemRead.model_validate(db_msg)

       # Auditoria
       def registrar_auditoria(self, campanha_id: Optional[int], acao: str, detalhes: Optional[str], hash_dados: Optional[str]) -> AuditLogRead:
           log = AuditLog(
               campanha_id=campanha_id,
               acao=acao,
               detalhes=detalhes,
               timestamp=datetime.utcnow(),
               hash_dados=hash_dados
           )
           self.session.add(log)
           self.session.flush()
           self.session.refresh(log)
           return AuditLogRead.model_validate(log)

       def listar_logs_auditoria(self, campanha_id: Optional[int] = None) -> List[AuditLogRead]:
           stmt = select(AuditLog)
           if campanha_id:
               stmt = stmt.where(AuditLog.campanha_id == campanha_id)
           stmt = stmt.order_by(AuditLog.timestamp.desc())
           logs = self.session.execute(stmt).scalars().all()
           return [AuditLogRead.model_validate(log) for log in logs]
   ```

9.  **Review & Refine (Self-Correction/Verification):**
   - *Python 3.12 & Strict Typing:* Used `Mapped`, `mapped_column`, type hints everywhere. Pydantic v2 uses `model_config = ConfigDict(from_attributes=True)`. Good.
   - *SQLAlchemy 2.0:* Used `select`, `scalar_one_or_none`, `scalars()`, `flush()`, `refresh()`. Good.
   - *SUS/APS Standards:* Included `cid10`, `ciap2`, `soap_note`, `paciente_cpf`, `paciente_cns`. Added regex patterns for CPF (11 digits) and CNS (15 digits). Good.
   - *Data Protection (LGPD):* Added `hash_dados` field, `_hash_sensitive_data` method, audit logs for all sensitive operations. Good.
   - *Repository Pattern:* Encapsulated DB operations. Good.
   - *Testing:* Need to provide a complete pytest file. I'll create `tests/test_campanhas_repo.py` with fixtures for DB session, test cases for all methods,