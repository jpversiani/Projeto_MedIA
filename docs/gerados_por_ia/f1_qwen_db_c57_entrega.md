Here's a thinking process:

1.  **Understand User Goal:** The user wants me to act as a software engineer/tester and implement a specific file: `backend/app/repositories/auditoria_telemedicina.py` containing a class `AuditoriaTelemedicinaRepository`. This repository should handle logging events for teleconsultations (connection, disconnection, acceptance of confidentiality terms/LGPD/CFM), and include secure timestamping using SQLAlchemy 2.0. The project is called "MedIA".

2.  **Key Requirements:**
   - File path: `backend/app/repositories/auditoria_telemedicina.py`
   - Class: `AuditoriaTelemedicinaRepository`
   - Functionality: Log connection/disconnection events, acceptance of confidentiality terms (LGPD/CFM), secure timestamps.
   - Tech Stack: Python 3.12, strict typing with Pydantic v2, SQLAlchemy 2.0.
   - Standards: SUS/APS (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
   - Compliance: Full compliance with automated test coverage using pytest.
   - Output: Complete, executable code for the specified file.

3.  **Deconstruct Requirements & Plan Implementation:**
   - **Database Model (SQLAlchemy 2.0):** Need a table/model for audit logs. Fields should include:
     - `id` (UUID or Integer)
     - `teleconsulta_id` (FK to teleconsultation)
     - `patient_cns` (CNS - Carteira Nacional de Saúde)
     - `patient_cpf` (CPF)
     - `event_type` (connection, disconnection, terms_accepted, etc.)
     - `event_data` (JSON for additional details like SOAP notes, CIAP-2, CID-10, timestamps)
     - `timestamp` (UTC, secure/immutable)
     - `ip_address`, `user_agent`, `session_id` (for security/audit trail)
     - `signature` (optional but good for "secure timestamping" - could use a hash or just rely on DB constraints + UTC)
   - **Pydantic Models:** Need request/response models for validation.
   - **Repository Class:** `AuditoriaTelemedicinaRepository` with methods to:
     - `log_connection`
     - `log_disconnection`
     - `log_terms_acceptance`
     - `get_logs` (for querying)
     - Use SQLAlchemy 2.0 async/sync? I'll stick to sync for simplicity unless specified, but I'll make it compatible with modern SQLAlchemy 2.0 patterns (using `Session` or `AsyncSession`). I'll use `AsyncSession` as it's common in modern FastAPI apps, but I'll make it clear. Actually, I'll use standard `Session` for broader compatibility, but I'll note it. Wait, the prompt says "SQLAlchemy 2.0", so I'll use the modern declarative style with `Mapped`, `mapped_column`, etc.
   - **SUS/APS Standards:** Include fields for CIAP-2, CID-10, SOAP method, CNS/CPF in the event data or as direct columns.
   - **Secure Timestamping:** Use `datetime.now(timezone.utc)` with `server_default` or `onupdate` in SQLAlchemy. I'll add a cryptographic hash/signature field if needed, but typically "secure timestamping" in this context means immutable, timezone-aware UTC timestamps with DB constraints. I'll implement a hash-based integrity check or just emphasize UTC + DB constraints + Pydantic validation.
   - **Testing:** The prompt says "Manter conformidade total e cobertura de testes automatizados com pytest." I should provide the repository code, but I'll also include a test file structure or mention how it's tested. The prompt asks for the code for the specific file, but I can add a test file if needed. I'll focus on the requested file first, but ensure it's testable.

4.  **Draft - Database Model (SQLAlchemy 2.0):**
   ```python
   from datetime import datetime, timezone
   from typing import Optional
   from uuid import uuid4
   from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, func
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   import enum

   class Base(DeclarativeBase):
       pass

   class AuditoriaTelemedicinaEventType(str, enum.Enum):
       CONEXAO = "conexao"
       DESCONECAO = "desconexao"
       ACEITE_TERMOS_SIGILO = "aceite_termos_sigilo"
       REGISTRO_SOA = "registro_soa"
       REGISTRO_CIAP_CID = "registro_ciap_cid"

   class AuditoriaTelemedicina(Base):
       __tablename__ = "auditoria_telemedicina"

       id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
       teleconsulta_id: Mapped[str] = mapped_column(String(36), ForeignKey("teleconsultas.id", ondelete="CASCADE"))
       paciente_cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       paciente_cpf: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
       evento: Mapped[AuditoriaTelemedicinaEventType] = mapped_column(Enum(AuditoriaTelemedicinaEventType))
       dados_evento: Mapped[Optional[dict]] = mapped_column(Text, nullable=True) # JSON stored as text
       ip_origem: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
       user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
       carimbo_seguro: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
       hash_integridade: Mapped[str] = mapped_column(String(64), nullable=False) # SHA-256 of event data + timestamp
   ```
   Wait, SQLAlchemy 2.0 uses `mapped_column` and `Mapped`. I need to import correctly. Also, `server_default=func.now()` is fine. For "secure timestamping", I'll compute a hash of the timestamp + event data to ensure immutability.

5.  **Draft - Pydantic Models:**
   ```python
   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from typing import Optional, Dict, Any
   from datetime import datetime
   import hashlib
   import json

   class AuditoriaTelemedicinaBase(BaseModel):
       teleconsulta_id: str
       paciente_cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       paciente_cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       evento: AuditoriaTelemedicinaEventType
       dados_evento: Optional[Dict[str, Any]] = None
       ip_origem: Optional[str] = None
       user_agent: Optional[str] = None

       model_config = ConfigDict(from_attributes=True)

       @field_validator("dados_evento")
       @classmethod
       def validate_dados_evento(cls, v):
           if v is not None:
               # Ensure CIAP-2, CID-10, SOAP are optional but structured if present
               pass
           return v

       def compute_hash(self) -> str:
           data = json.dumps(self.model_dump(), sort_keys=True, default=str)
           return hashlib.sha256(data.encode()).hexdigest()
   ```
   Actually, Pydantic v2 uses `model_config = ConfigDict(from_attributes=True)`. I'll keep it simple.

6.  **Draft - Repository Class:**
   Need methods to interact with the DB. I'll use SQLAlchemy 2.0 async patterns as it's standard for modern Python backends, but I'll make it sync-compatible or explicitly use `AsyncSession`. I'll stick to `AsyncSession` for modern FastAPI apps, but I'll add a note. Actually, I'll use `Session` for simplicity and broader compatibility, but I'll write it in a way that's clearly SQLAlchemy 2.0.
   Wait, the prompt says "SQLAlchemy 2.0". I'll use `AsyncSession` as it's the recommended pattern for async frameworks, but I'll make the repository generic enough. I'll use `Session` for simplicity in the example, but I'll add type hints properly.

   Let's structure the repository:
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, insert
   from typing import List, Optional
   import asyncio

   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def log_event(self, event: AuditoriaTelemedicinaBase) -> AuditoriaTelemedicina:
           # compute hash
           # insert
           # commit
           pass
   ```
   Actually, I should make it sync or async? I'll provide async as it's standard, but I'll make sure it's clear. I'll use `AsyncSession` and `async def`.

   Let's refine the repository with proper SQLAlchemy 2.0 syntax:
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, insert
   from typing import List, Optional
   from datetime import datetime, timezone
   import json
   import hashlib

   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def log_event(self, event: AuditoriaTelemedicinaBase) -> AuditoriaTelemedicina:
           # Compute secure hash
           data_str = json.dumps(event.model_dump(mode="json", exclude_unset=True), sort_keys=True, default=str)
           secure_hash = hashlib.sha256(data_str.encode("utf-8")).hexdigest()

           # Create DB model instance
           db_event = AuditoriaTelemedicina(
               teleconsulta_id=event.teleconsulta_id,
               paciente_cns=event.paciente_cns,
               paciente_cpf=event.paciente_cpf,
               evento=event.evento,
               dados_evento=event.dados_evento,
               ip_origem=event.ip_origem,
               user_agent=event.user_agent,
               carimbo_seguro=datetime.now(timezone.utc),
               hash_integridade=secure_hash
           )

           self.session.add(db_event)
           await self.session.commit()
           await self.session.refresh(db_event)
           return db_event
   ```
   Wait, I need to handle the specific events: connection, disconnection, terms acceptance. I'll add convenience methods.
   Also, I need to ensure the Pydantic models and SQLAlchemy models are properly defined in the same file or imported. The prompt says "implemente backend/app/repositories/auditoria_telemedicina.py com a classe AuditoriaTelemedicinaRepository". I'll put everything in one file for completeness, or structure it logically.

   Let's structure the file properly:
   - Imports
   - Enums
   - SQLAlchemy Model
   - Pydantic Models
   - Repository Class
   - Type hints, docstrings, compliance notes.

   I'll add methods for the specific events:
   - `log_conexao`
   - `log_desconexao`
   - `log_aceite_termos_sigilo`
   - `log_registro_clinico` (for SOAP, CIAP-2, CID-10)

   I'll also add a method to query logs.

   Let's draft carefully.

   **Structure:**
   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   from __future__ import annotations
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, Dict, Any, List
   from uuid import uuid4
   import hashlib
   import json

   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy import String, Text, DateTime, Enum as SAEnum, ForeignKey, func, select
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   from sqlalchemy.ext.asyncio import AsyncSession

   # --- Enums & Constants ---
   class AuditoriaTelemedicinaEventType(str, Enum):
       CONEXAO = "conexao"
       DESCONECAO = "desconexao"
       ACEITE_TERMOS_SIGILO = "aceite_termos_sigilo"
       REGISTRO_SOA = "registro_soa"
       REGISTRO_CIAP_CID = "registro_ciap_cid"

   # --- SQLAlchemy 2.0 Model ---
   class Base(DeclarativeBase):
       pass

   class AuditoriaTelemedicina(Base):
       __tablename__ = "auditoria_telemedicina"

       id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
       teleconsulta_id: Mapped[str] = mapped_column(String(36), ForeignKey("teleconsultas.id", ondelete="CASCADE"))
       paciente_cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       paciente_cpf: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
       evento: Mapped[AuditoriaTelemedicinaEventType] = mapped_column(SAEnum(AuditoriaTelemedicinaEventType))
       dados_evento: Mapped[Optional[Dict[str, Any]]] = mapped_column(Text, nullable=True)
       ip_origem: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
       user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
       carimbo_seguro: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
       hash_integridade: Mapped[str] = mapped_column(String(64), nullable=False)

   # --- Pydantic v2 Models ---
   class AuditoriaTelemedicinaBase(BaseModel):
       teleconsulta_id: str
       paciente_cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       paciente_cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       evento: AuditoriaTelemedicinaEventType
       dados_evento: Optional[Dict[str, Any]] = None
       ip_origem: Optional[str] = None
       user_agent: Optional[str] = None

       model_config = ConfigDict(from_attributes=True)

       @field_validator("dados_evento")
       @classmethod
       def validate_dados_evento(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
           if v is not None:
               # Validação básica para padrões SUS/APS
               if "metodo_soa" in v and v["metodo_soa"] not in ["subjetivo", "objetivo", "análise", "plano"]:
                   raise ValueError("Método SOAP deve conter: subjetivo, objetivo, análise, plano")
           return v

       def compute_hash(self) -> str:
           data_str = json.dumps(self.model_dump(mode="json", exclude_unset=True), sort_keys=True, default=str)
           return hashlib.sha256(data_str.encode("utf-8")).hexdigest()

   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def log_event(self, event: AuditoriaTelemedicinaBase) -> AuditoriaTelemedicina:
           secure_hash = event.compute_hash()
           db_event = AuditoriaTelemedicina(
               teleconsulta_id=event.teleconsulta_id,
               paciente_cns=event.paciente_cns,
               paciente_cpf=event.paciente_cpf,
               evento=event.evento,
               dados_evento=event.dados_evento,
               ip_origem=event.ip_origem,
               user_agent=event.user_agent,
               carimbo_seguro=datetime.now(timezone.utc),
               hash_integridade=secure_hash
           )
           self.session.add(db_event)
           await self.session.commit()
           await self.session.refresh(db_event)
           return db_event

       # Convenience methods for SUS/APS standards
       async def log_conexao(self, teleconsulta_id: str, paciente_cns: Optional[str] = None, paciente_cpf: Optional[str] = None, ip: Optional[str] = None, ua: Optional[str] = None) -> AuditoriaTelemedicina:
           return await self.log_event(AuditoriaTelemedicinaBase(
               teleconsulta_id=teleconsulta_id,
               paciente_cns=paciente_cns,
               paciente_cpf=paciente_cpf,
               evento=AuditoriaTelemedicinaEventType.CONEXAO,
               ip_origem=ip,
               user_agent=ua
           ))

       async def log_desconexao(self, teleconsulta_id: str, paciente_cns: Optional[str] = None, paciente_cpf: Optional[str] = None, ip: Optional[str] = None, ua: Optional[str] = None) -> AuditoriaTelemedicina:
           return await self.log_event(AuditoriaTelemedicinaBase(
               teleconsulta_id=teleconsulta_id,
               paciente_cns=paciente_cns,
               paciente_cpf=paciente_cpf,
               evento=AuditoriaTelemedicinaEventType.DESCONEXAO,
               ip_origem=ip,
               user_agent=ua
           ))

       async def log_aceite_termos_sigilo(self, teleconsulta_id: str, paciente_cns: str, paciente_cpf: str) -> AuditoriaTelemedicina:
           return await self.log_event(AuditoriaTelemedicinaBase(
               teleconsulta_id=teleconsulta_id,
               paciente_cns=paciente_cns,
               paciente_cpf=paciente_cpf,
               evento=AuditoriaTelemedicinaEventType.ACEITE_TERMOS_SIGILO,
               dados_evento={"termo": "LGPD/CFM_2023", "versao": "1.0", "status": "aceito"}
           ))

       async def log_registro_clinico(self, teleconsulta_id: str, paciente_cns: str, paciente_cpf: str, soa: Dict[str, str], ciap2: List[str], cid10: List[str]) -> AuditoriaTelemedicina:
           return await self.log_event(AuditoriaTelemedicinaBase(
               teleconsulta_id