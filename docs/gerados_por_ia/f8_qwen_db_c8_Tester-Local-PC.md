Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for a "Health Campaigns Repository and Send History" (C8).
   - **Requirements:**
     - Track sent messages, confirmation status by patient, and data protection audit log.
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification.
     - Full compliance and automated test coverage with pytest.
     - Provide complete, executable code.
     - Specify file paths in code blocks.
   - **Context:** Project MedIA (likely a health tech project).

2.  **Deconstruct Requirements:**
   - **Repository:** `backend/app/repositories/campanhas_repo.py`
   - **Models/Schema:** Pydantic v2 models for request/response/validation.
   - **Database:** SQLAlchemy 2.0 ORM models for campaigns, message history, confirmation status, audit log.
   - **Standards:** CIAP-2 (International Classification of Primary Care), CID-10 (ICD-10), SOAP (Subjective, Objective, Assessment, Plan), CNS (Unified Health System Card number), CPF (Brazilian tax ID).
   - **Testing:** Pytest coverage for all repository methods.
   - **Compliance:** LGPD (Brazilian Data Protection Law) considerations for audit logs.

3.  **Design Database Models (SQLAlchemy 2.0):**
   Need tables for:
   - `Campanha` (Campaign): id, name, description, start_date, end_date, status, created_at, updated_at
   - `MensagemCampanha` (Campaign Message): id, campanha_id, paciente_cpf, paciente_cns, status (sent, delivered, confirmed, failed), message_content, sent_at, confirmed_at, confirmation_method, created_at
   - `LogAuditoriaLGPD` (Audit Log): id, campanha_id, mensagem_id, action (send, confirm, view, delete, export), user_id, ip_address, timestamp, details, compliance_status
   - Need to incorporate SUS/APS fields: CIAP-2 code, CID-10 code, SOAP notes, CNS, CPF.

   Let's refine the models:
   ```python
   # Campaign
   class Campanha(Base):
       __tablename__ = "campanhas"
       id = Column(Integer, primary_key=True)
       nome = Column(String(255), nullable=False)
       descricao = Column(Text)
       codigo_ciap2 = Column(String(10)) # CIAP-2 code for primary care
       codigo_cid10 = Column(String(10)) # CID-10 code
       metodo_soap = Column(String(50)) # SOAP method type
       data_inicio = Column(DateTime, nullable=False)
       data_fim = Column(DateTime, nullable=False)
       status = Column(String(20), default="ativa")
       created_at = Column(DateTime, server_default=func.now())
       updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

   # Message/Send History
   class HistoricoDisparo(Base):
       __tablename__ = "historico_disparos"
       id = Column(Integer, primary_key=True)
       campanha_id = Column(Integer, ForeignKey("campanhas.id"), nullable=False)
       paciente_cpf = Column(String(14), nullable=False)
       paciente_cns = Column(String(15), nullable=False)
       status_envio = Column(String(20), default="pendente") # pendente, enviado, confirmado, falha
       mensagem = Column(Text, nullable=False)
       data_envio = Column(DateTime)
       data_confirmacao = Column(DateTime)
       metodo_confirmacao = Column(String(50)) # sms, whatsapp, email, etc.
       created_at = Column(DateTime, server_default=func.now())

   # Audit Log
   class LogAuditoria(Base):
       __tablename__ = "logs_auditoria"
       id = Column(Integer, primary_key=True)
       campanha_id = Column(Integer, ForeignKey("campanhas.id"))
       disparo_id = Column(Integer, ForeignKey("historico_disparos.id"))
       acao = Column(String(50), nullable=False) # enviar, confirmar, visualizar, exportar, excluir
       usuario_id = Column(String(50))
       ip_origem = Column(String(45))
       timestamp = Column(DateTime, server_default=func.now())
       detalhes = Column(Text)
       conformidade_lgpd = Column(String(20), default="conforme")
   ```

4.  **Design Pydantic Models (v2):**
   Need schemas for validation and API contracts.
   - `CampanhaCreate`, `CampanhaRead`
   - `HistoricoDisparoCreate`, `HistoricoDisparoRead`
   - `LogAuditoriaCreate`, `LogAuditoriaRead`
   - Use `ConfigDict`, `Field`, `validator`/`model_validator` for CPF/CNS validation.

   CPF validation: Standard algorithm or regex. I'll use a simple regex for brevity but note it's for demo. Actually, I'll implement a proper CPF/CNS validator using Pydantic v2's `model_validator`.
   CNS validation: 15 digits, checksum. I'll implement a basic validator.

   ```python
   from pydantic import BaseModel, Field, model_validator, ConfigDict
   from datetime import datetime
   from typing import Optional
   from enum import Enum

   class StatusCampanha(str, Enum):
       RASCUNHO = "rascunho"
       ATIVA = "ativa"
       PAUSADA = "pausada"
       CONCLUIDA = "concluida"

   class StatusDisparo(str, Enum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       CONFIRMADO = "confirmado"
       FALHA = "falha"

   class AcaoAuditoria(str, Enum):
       ENVIAR = "enviar"
       CONFIRMAR = "confirmar"
       VISUALIZAR = "visualizar"
       EXPORTAR = "exportar"
       EXCLUIR = "excluir"

   class CampanhaCreate(BaseModel):
       nome: str = Field(..., min_length=1, max_length=255)
       descricao: Optional[str] = None
       codigo_ciap2: Optional[str] = Field(None, pattern=r"^[A-Z0-9]{1,10}$")
       codigo_cid10: Optional[str] = Field(None, pattern=r"^[A-Z0-9]{1,10}$")
       metodo_soap: Optional[str] = Field(None, pattern=r"^(S|O|A|P|SOAP)$")
       data_inicio: datetime
       data_fim: datetime
       status: StatusCampanha = StatusCampanha.RASCUNHO

       model_config = ConfigDict(from_attributes=True)

   class CampanhaRead(CampanhaCreate):
       id: int
       created_at: datetime
       updated_at: datetime

   class HistoricoDisparoCreate(BaseModel):
       campanha_id: int
       paciente_cpf: str = Field(..., pattern=r"^\d{11}$")
       paciente_cns: str = Field(..., pattern=r"^\d{15}$")
       mensagem: str = Field(..., min_length=1)
       metodo_confirmacao: Optional[str] = None

       model_config = ConfigDict(from_attributes=True)

   class HistoricoDisparoRead(HistoricoDisparoCreate):
       id: int
       status_envio: StatusDisparo
       data_envio: Optional[datetime] = None
       data_confirmacao: Optional[datetime] = None
       created_at: datetime

   class LogAuditoriaCreate(BaseModel):
       campanha_id: Optional[int] = None
       disparo_id: Optional[int] = None
       acao: AcaoAuditoria
       usuario_id: str
       ip_origem: Optional[str] = None
       detalhes: Optional[str] = None

       model_config = ConfigDict(from_attributes=True)

   class LogAuditoriaRead(LogAuditoriaCreate):
       id: int
       timestamp: datetime
       conformidade_lgpd: str = "conforme"
   ```

5.  **Design Repository Class:**
   Need methods for:
   - Create campaign
   - Get campaign by ID
   - Send message (track history)
   - Update confirmation status
   - Get send history/pagination
   - Create audit log
   - Get audit logs
   - Use SQLAlchemy 2.0 async/sync? I'll use sync for simplicity but note it's compatible with async. I'll stick to sync `Session` for standard repo pattern, but make it type-hinted properly.

   Repository structure:
   ```python
   from sqlalchemy.orm import Session
   from sqlalchemy import select, func, update, delete
   from typing import List, Optional, Dict, Any
   from datetime import datetime
   import logging

   logger = logging.getLogger(__name__)

   class CampanhasRepository:
       def __init__(self, db: Session):
           self.db = db

       def criar_campanha(self, schema: CampanhaCreate) -> Campanha:
           ...
       def obter_campanha(self, campanha_id: int) -> Optional[Campanha]:
           ...
       def registrar_disparo(self, schema: HistoricoDisparoCreate) -> HistoricoDisparo:
           ...
       def atualizar_confirmacao(self, disparo_id: int, status: StatusDisparo, metodo: Optional[str] = None) -> HistoricoDisparo:
           ...
       def obter_historico_disparos(self, campanha_id: Optional[int] = None, paciente_cpf: Optional[str] = None, status: Optional[StatusDisparo] = None) -> List[HistoricoDisparo]:
           ...
       def registrar_log_auditoria(self, schema: LogAuditoriaCreate) -> LogAuditoria:
           ...
       def obter_logs_auditoria(self, campanha_id: Optional[int] = None, disparo_id: Optional[int] = None, acao: Optional[AcaoAuditoria] = None) -> List[LogAuditoria]:
           ...
   ```

   Implement methods with SQLAlchemy 2.0 syntax:
   ```python
   # Inside CampanhasRepository
   def criar_campanha(self, schema: CampanhaCreate) -> Campanha:
       campanha = Campanha(
           nome=schema.nome,
           descricao=schema.descricao,
           codigo_ciap2=schema.codigo_ciap2,
           codigo_cid10=schema.codigo_cid10,
           metodo_soap=schema.metodo_soap,
           data_inicio=schema.data_inicio,
           data_fim=schema.data_fim,
           status=schema.status.value
       )
       self.db.add(campanha)
       self.db.commit()
       self.db.refresh(campanha)
       return campanha

   def obter_campanha(self, campanha_id: int) -> Optional[Campanha]:
       stmt = select(Campanha).where(Campanha.id == campanha_id)
       return self.db.execute(stmt).scalar_one_or_none()

   def registrar_disparo(self, schema: HistoricoDisparoCreate) -> HistoricoDisparo:
       disparo = HistoricoDisparo(
           campanha_id=schema.campanha_id,
           paciente_cpf=schema.paciente_cpf,
           paciente_cns=schema.paciente_cns,
           mensagem=schema.mensagem,
           status_envio=StatusDisparo.PENDENTE.value,
           data_envio=datetime.utcnow()
       )
       self.db.add(disparo)
       self.db.commit()
       self.db.refresh(disparo)
       # Log audit
       self.registrar_log_auditoria(LogAuditoriaCreate(
           campanha_id=schema.campanha_id,
           disparo_id=disparo.id,
           acao=AcaoAuditoria.ENVIAR,
           usuario_id="sistema",
           detalhes=f"Disparo registrado para CPF {schema.paciente_cpf}"
       ))
       return disparo

   def atualizar_confirmacao(self, disparo_id: int, status: StatusDisparo, metodo: Optional[str] = None) -> HistoricoDisparo:
       stmt = update(HistoricoDisparo).where(HistoricoDisparo.id == disparo_id).values(
           status_envio=status.value,
           data_confirmacao=datetime.utcnow(),
           metodo_confirmacao=metodo
       )
       self.db.execute(stmt)
       self.db.commit()
       stmt_get = select(HistoricoDisparo).where(HistoricoDisparo.id == disparo_id)
       return self.db.execute(stmt_get).scalar_one()

   def obter_historico_disparos(self, campanha_id: Optional[int] = None, paciente_cpf: Optional[str] = None, status: Optional[StatusDisparo] = None) -> List[HistoricoDisparo]:
       stmt = select(HistoricoDisparo)
       if campanha_id:
           stmt = stmt.where(HistoricoDisparo.campanha_id == campanha_id)
       if paciente_cpf:
           stmt = stmt.where(HistoricoDisparo.paciente_cpf == paciente_cpf)
       if status:
           stmt = stmt.where(HistoricoDisparo.status_envio == status.value)
       stmt = stmt.order_by(HistoricoDisparo.data_envio.desc())
       return list(self.db.execute(stmt).scalars().all())

   def registrar_log_auditoria(self, schema: LogAuditoriaCreate) -> LogAuditoria:
       log = LogAuditoria(
           campanha_id=schema.campanha_id,
           disparo_id=schema.disparo_id,
           acao=schema.acao.value,
           usuario_id=schema.usuario_id,
           ip_origem=schema.ip_origem,
           detalhes=schema.detalhes,
           conformidade_lgpd="conforme"
       )
       self.db.add(log)
       self.db.commit()
       self.db.refresh(log)
       return log

   def obter_logs_auditoria(self, campanha_id: Optional[int] = None, disparo_id: Optional[int] = None, acao: Optional[AcaoAuditoria] = None) -> List[LogAuditoria]:
       stmt = select(LogAuditoria)
       if campanha_id:
           stmt = stmt.where(LogAuditoria.campanha_id == campanha_id)
       if disparo_id:
           stmt = stmt.where(LogAuditoria.disparo_id == disparo_id)
       if acao:
           stmt = stmt.where(LogAuditoria.acao == acao.value)
       stmt = stmt.order_by(LogAuditoria.timestamp.desc())
       return list(self.db.execute(stmt).scalars().all())
   ```

6.  **Add Pydantic Validators for CPF/CNS (LGPD/SUS compliance):**
   I'll add a `model_validator` to `HistoricoDisparoCreate` to validate CPF and CNS properly.
   CPF validation: 11 digits, check digits.
   CNS validation: 15 digits, checksum algorithm (standard SUS).
   I'll implement simplified but functional validators.

   ```python
   def validar_cpf(cpf: str) -> bool:
       cpf = cpf.replace('.', '').replace('-', '')
       if len(cpf) != 11 or not cpf.isdigit():
           return False
       if len(set(cpf)) == 1:
           return False
       add = lambda i, v: sum(int(cpf[i]) * v for i in range(len(cpf)))
       if add(0, range(10, 1, -1)) % 11 % 10 != int(cpf[9]):
           return False
       if add(0, range(11, 1, -1)) % 11 % 10 != int(cpf[10]):
           return False
       return True

   def validar_cns(cns: str) -> bool:
       if len(cns) != 15 or not cns.isdigit():
           return False
       # Simplified checksum for CNS (standard algorithm)
       weights = [2, 7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
       total = sum(int(cns[i]) * weights[i] for i in range(13))
       remainder = total % 11
       check = 11 - remainder if remainder > 1 else 0
       return check == int(cns[13])
   ```

   Add to Pydantic model:
   ```python
   @model_validator(mode='before')
   @classmethod
   def validar_identificacao_sus(cls, data):
       if isinstance(data, dict):
           cpf = data.get('paciente_cpf', '')
           cns = data.get('paciente_cns', '')
           if cpf and not validar_cpf(cpf):
               raise ValueError("CPF inválido")
           if cns and not validar_cns(cns):
               raise ValueError("CNS inválido")
       return data
   ```

7.  **Create Pytest Test Suite:**
   Need tests for:
   - Campaign CRUD
   - Disparo registration & confirmation
   - Audit log creation & retrieval
   - CPF/CNS validation
   - Use `pytest`, `sqlalchemy`, `pytest-mock` or `pytest-asyncio`? I'll stick to sync SQLAlchemy with `pytest` and `unittest.mock` or `pytest` fixtures with `SessionLocal`.
   I'll create a test file: `tests/test_campanhas_repo.py`
   Use `pytest` with `pytest-mock` or standard `unittest.mock`. I'll use `pytest` with `sqlalchemy` in-memory SQLite for testing.

   Test structure:
   ```python
   import pytest
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from datetime import datetime
   from backend.app.repositories.campanhas_repo import (
       CampanhasRepository, Campanha