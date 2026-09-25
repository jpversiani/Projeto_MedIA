Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Implement `backend/app/repositories/auditoria_telemedicina.py` with a class `AuditoriaTelemedicinaRepository`.
   - **Key Features:**
     - Log connection/disconnection events.
     - Log acceptance of confidentiality terms (LGPD/CFM Resolution).
     - Secure timestamping.
     - Use SQLAlchemy 2.0.
     - Python 3.12, strict typing with Pydantic v2.
     - Follow SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Maintain full compliance and automated test coverage with pytest.
   - **Output Requirement:** Provide complete, executable code. Specify file paths at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/auditoria_telemedicina.py`
   - **Class:** `AuditoriaTelemedicinaRepository`
   - **Database:** SQLAlchemy 2.0 (models, session management, async/sync? I'll assume sync for simplicity unless specified, but I'll make it compatible with modern practices. I'll use `sqlalchemy.orm` and `sqlalchemy.ext.asyncio` if needed, but the prompt doesn't specify async. I'll stick to sync SQLAlchemy 2.0 for clarity, but note that it can be adapted. Actually, I'll use `sqlalchemy` 2.0 style with `Session`.)
   - **Pydantic v2:** For data validation/serialization of events.
   - **Events:** Connection, Disconnection, Term Acceptance (LGPD/CFM).
   - **Timestamps:** Secure/fixed timestamps (maybe using `datetime.now(timezone.utc)` or allowing injection for testing).
   - **SUS/APS Standards:** CIAP-2, CID-10, SOAP, CNS/CPF. These should be fields in the audit model or related to the consultation context.
   - **Testing:** Provide pytest tests covering the repository.

3.  **Design the Database Model (SQLAlchemy 2.0):**
   Need a table for audit logs. Let's call it `auditoria_telemedicina`.
   Fields:
   - `id`: UUID or Integer (PK)
   - `tipo_evento`: Enum (CONEXAO, DESCONECAO, ACEITE_TERMOS)
   - `cns_paciente`: String (optional, for patient identification)
   - `cpf_paciente`: String (optional)
   - `cns_medico`: String (optional)
   - `cid10`: String (optional, diagnosis)
   - `ciap2`: String (optional, classification)
   - `metodo_sop`: String (optional, SOAP method)
   - `timestamp_utc`: DateTime (secure, timezone-aware)
   - `dados_adicionais`: JSON (for flexible event data)
   - `ip_origem`: String (optional)
   - `user_agent`: String (optional)
   - `aceite_lgpd`: Boolean (for term acceptance)
   - `versao_termo`: String (optional)

   Wait, the prompt says "registro de eventos de conexão, desconexão, aceite de termos de sigilo do paciente (LGPD / Resolução CFM) e carimbo de data/hora seguro". It also mentions SUS/APS standards (CIAP-2, CID-10, SOAP, CNS/CPF). I'll integrate these as fields in the audit model or as part of the consultation context.

   Let's define a Pydantic model for the event payload:
   ```python
   from pydantic import BaseModel, Field, ConfigDict
   from enum import Enum
   from datetime import datetime
   from typing import Optional, Dict, Any
   import uuid

   class EventoTipo(str, Enum):
       CONEXAO = "CONEXAO"
       DESCONECAO = "DESCONECAO"
       ACEITE_TERMOS = "ACEITE_TERMOS"

   class AuditoriaEventoPayload(BaseModel):
       model_config = ConfigDict(frozen=True)
       tipo: EventoTipo
       cns_paciente: Optional[str] = None
       cpf_paciente: Optional[str] = None
       cns_medico: Optional[str] = None
       cid10: Optional[str] = None
       ciap2: Optional[str] = None
       metodo_sop: Optional[str] = None
       ip_origem: Optional[str] = None
       user_agent: Optional[str] = None
       aceite_lgpd: Optional[bool] = None
       versao_termo: Optional[str] = None
       dados_adicionais: Optional[Dict[str, Any]] = None
   ```

   SQLAlchemy Model:
   ```python
   from sqlalchemy import Column, String, DateTime, Boolean, JSON, Enum as SAEnum, ForeignKey
   from sqlalchemy.orm import DeclarativeBase
   from sqlalchemy.dialects.postgresql import UUID
   import uuid
   from datetime import datetime, timezone

   class Base(DeclarativeBase):
       pass

   class AuditoriaTelemedicinaModel(Base):
       __tablename__ = "auditoria_telemedicina"

       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       tipo_evento = Column(SAEnum(EventoTipo), nullable=False)
       cns_paciente = Column(String(15), nullable=True)
       cpf_paciente = Column(String(14), nullable=True)
       cns_medico = Column(String(15), nullable=True)
       cid10 = Column(String(7), nullable=True)
       ciap2 = Column(String(4), nullable=True)
       metodo_sop = Column(String(50), nullable=True)
       timestamp_utc = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
       ip_origem = Column(String(45), nullable=True)
       user_agent = Column(String(255), nullable=True)
       aceite_lgpd = Column(Boolean, nullable=True)
       versao_termo = Column(String(20), nullable=True)
       dados_adicionais = Column(JSON, nullable=True)
   ```

   Wait, SQLAlchemy 2.0 prefers `Mapped` and `mapped_column`. Let's update to modern syntax:
   ```python
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   from sqlalchemy import String, DateTime, Boolean, JSON, Enum as SAEnum
   from sqlalchemy.dialects.postgresql import UUID
   import uuid
   from datetime import datetime, timezone

   class Base(DeclarativeBase):
       pass

   class AuditoriaTelemedicinaModel(Base):
       __tablename__ = "auditoria_telemedicina"

       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       tipo_evento: Mapped[EventoTipo] = mapped_column(SAEnum(EventoTipo), nullable=False)
       cns_paciente: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       cpf_paciente: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
       cns_medico: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       cid10: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
       ciap2: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
       metodo_sop: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
       timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
       ip_origem: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
       user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
       aceite_lgpd: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
       versao_termo: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
       dados_adicionais: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
   ```

   Actually, `default` in `mapped_column` for datetime should be `datetime.now(timezone.utc)` or `func.now()`. I'll use `datetime.now(timezone.utc)` for simplicity, but note that for production, `server_default` or `onupdate` might be better. I'll stick to `default=datetime.now(timezone.utc)`.

4.  **Design the Repository Class:**
   Needs to interact with SQLAlchemy session. I'll make it accept a session or use a dependency injection pattern. For simplicity and testability, I'll pass a `Session` to the constructor or methods. I'll use a class method or instance method with explicit session.
   Let's define it as:
   ```python
   from sqlalchemy.orm import Session
   from typing import List, Optional
   import uuid

   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: Session):
           self.session = session

       def registrar_evento(self, evento: AuditoriaEventoPayload) -> AuditoriaTelemedicinaModel:
           # Map payload to model
           model = AuditoriaTelemedicinaModel(
               tipo_evento=evento.tipo,
               cns_paciente=evento.cns_paciente,
               cpf_paciente=evento.cpf_paciente,
               cns_medico=evento.cns_medico,
               cid10=evento.cid10,
               ciap2=evento.ciap2,
               metodo_sop=evento.metodo_sop,
               timestamp_utc=evento.timestamp_utc if evento.timestamp_utc else datetime.now(timezone.utc),
               ip_origem=evento.ip_origem,
               user_agent=evento.user_agent,
               aceite_lgpd=evento.aceite_lgpd,
               versao_termo=evento.versao_termo,
               dados_adicionais=evento.dados_adicionais
           )
           self.session.add(model)
           self.session.commit()
           self.session.refresh(model)
           return model
   ```
   Wait, the payload should probably include the timestamp, or the repository should inject it securely. The prompt says "carimbo de data/hora seguro". I'll inject it in the repository to ensure security/consistency, ignoring any client-provided timestamp.
   Let's adjust the payload to not include timestamp, or keep it but override it. I'll override it in the repo for security.

   Also, I need to handle the SUS/APS standards. I'll add validation or constraints in the Pydantic model or repo.
   Let's refine the Pydantic model for strict typing and validation:
   ```python
   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from enum import Enum
   from datetime import datetime, timezone
   from typing import Optional, Dict, Any
   import uuid

   class EventoTipo(str, Enum):
       CONEXAO = "CONEXAO"
       DESCONECAO = "DESCONECAO"
       ACEITE_TERMOS = "ACEITE_TERMOS"

   class AuditoriaEventoPayload(BaseModel):
       model_config = ConfigDict(frozen=True)
       tipo: EventoTipo
       cns_paciente: Optional[str] = Field(None, pattern=r"^\d{15}$")
       cpf_paciente: Optional[str] = Field(None, pattern=r"^\d{11}$")
       cns_medico: Optional[str] = Field(None, pattern=r"^\d{15}$")
       cid10: Optional[str] = Field(None, pattern=r"^[A-Z]\d{2}$")
       ciap2: Optional[str] = Field(None, pattern=r"^[A-Z]\d{3}$")
       metodo_sop: Optional[str] = Field(None, pattern=r"^[A-Z]{4}$") # SOAP method? Actually SOAP is a method, maybe "SOAP" or "SUBJECTIVE", "OBJECTIVE", etc. I'll keep it flexible or use a specific enum. Let's stick to string for now, or define an enum for SOAP steps: ["SUBJECTIVE", "OBJECTIVE", "ASSESSMENT", "PLAN"].
       ip_origem: Optional[str] = Field(None, pattern=r"^\d{1,3}(\.\d{1,3}){3}$")
       user_agent: Optional[str] = None
       aceite_lgpd: Optional[bool] = None
       versao_termo: Optional[str] = None
       dados_adicionais: Optional[Dict[str, Any]] = None
   ```
   Actually, SOAP method in SUS/APS usually refers to the clinical method. I'll just keep it as a string field for flexibility, or add a validator. I'll keep it simple.

   Let's adjust the repository to handle session management properly. I'll make it accept a session factory or just a session. For testing, passing a session is fine.

   I'll also add a method to query logs, e.g., `obter_logs_por_paciente` or `obter_logs_por_evento`.

   Let's structure the repository properly:
   ```python:backend/app/repositories/auditoria_telemedicina.py
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, Dict, Any, List

   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from sqlalchemy.orm import Session
   from sqlalchemy import String, DateTime, Boolean, JSON, Enum as SAEnum
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

   # --- Pydantic Models ---
   class EventoTipo(str, Enum):
       CONEXAO = "CONEXAO"
       DESCONECAO = "DESCONECAO"
       ACEITE_TERMOS = "ACEITE_TERMOS"

   class AuditoriaEventoPayload(BaseModel):
       model_config = ConfigDict(frozen=True)
       tipo: EventoTipo
       cns_paciente: Optional[str] = Field(None, pattern=r"^\d{15}$")
       cpf_paciente: Optional[str] = Field(None, pattern=r"^\d{11}$")
       cns_medico: Optional[str] = Field(None, pattern=r"^\d{15}$")
       cid10: Optional[str] = Field(None, pattern=r"^[A-Z]\d{2}$")
       ciap2: Optional[str] = Field(None, pattern=r"^[A-Z]\d{3}$")
       metodo_sop: Optional[str] = Field(None, pattern=r"^[A-Z]{4}$")
       ip_origem: Optional[str] = Field(None, pattern=r"^\d{1,3}(\.\d{1,3}){3}$")
       user_agent: Optional[str] = None
       aceite_lgpd: Optional[bool] = None
       versao_termo: Optional[str] = None
       dados_adicionais: Optional[Dict[str, Any]] = None

   # --- SQLAlchemy Models ---
   class Base(DeclarativeBase):
       pass

   class AuditoriaTelemedicinaModel(Base):
       __tablename__ = "auditoria_telemedicina"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       tipo_evento: Mapped[EventoTipo] = mapped_column(SAEnum(EventoTipo), nullable=False)
       cns_paciente: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       cpf_paciente: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
       cns_medico: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       cid10: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
       ciap2: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
       metodo_sop: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
       timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
       ip_origem: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
       user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
       aceite_lgpd: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
       versao_termo: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
       dados_adicionais: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

   # --- Repository ---
   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: Session):
           self.session = session

       def registrar_evento(self, evento: AuditoriaEventoPayload) -> AuditoriaTelemedicinaModel:
           """Registra um evento de auditoria com carimbo de data/hora seguro (UTC)."""
           modelo = AuditoriaTelemedicinaModel(
               tipo_evento=evento.tipo,
               cns_paciente=evento.cns_paciente,
               cpf_paciente=evento.cpf_paciente,
               cns_medico=evento.cns_medico,
               cid10=evento.cid10,
               ciap2=evento.ciap2,
               metodo_sop=evento.metodo_sop,
               timestamp_utc=datetime.now(timezone.utc),  # Carimbo seguro no servidor
               ip_origem=evento.ip_origem,
               user_agent=evento.user_agent,
               aceite_lgpd=evento.aceite_lgpd,
               versao_termo=evento.versao_termo,
               dados_adicionais=evento.dados_adicionais
           )
           self.session.add(modelo)
           self.session.commit()
           self.session.refresh(modelo)
           return modelo

       def buscar_por_paciente(self, cns_paciente: str) -> List[AuditoriaTelemedicinaModel]:
           """Busca logs de auditoria por CNS do paciente."""
           return self.session.query(AuditoriaTelemedicinaModel).filter(
               AuditoriaTelemedicinaModel.cns_paciente == cns