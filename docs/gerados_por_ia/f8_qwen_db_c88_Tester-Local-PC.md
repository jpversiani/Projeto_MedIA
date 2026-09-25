Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for a "Health Campaigns Repository and Dispatch History (C88)" project.
   - **Requirements:**
     - Models and methods for logging: tracked sent messages, patient confirmation status, data protection audit log.
     - Architecture Guidelines: Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS Standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification.
     - Full compliance and coverage with automated tests using pytest.
     - Provide complete, executable code. Specify file paths in code blocks.
   - **Key Components Needed:**
     - SQLAlchemy 2.0 models for campaigns, dispatches, confirmations, audit logs.
     - Pydantic v2 schemas for request/response validation.
     - Repository class/methods for CRUD and specific tracking operations.
     - Pytest tests covering the repository.
     - Adherence to SUS/APS standards (CIAP-2, CID-10, SOAP, CNS/CPF).

2.  **Deconstruct Requirements & Plan Structure:**
   - **File 1:** `backend/app/repositories/campanhas_repo.py` - Contains SQLAlchemy models, Pydantic schemas, and the repository class.
   - **File 2:** `backend/app/repositories/test_campanhas_repo.py` - Contains pytest tests.
   - **Models Needed:**
     - `Campanha` (Campaign): ID, name, description, status, dates, etc.
     - `Disparo` (Dispatch/Sent Message): ID, campaign_id, patient_cns/cpf, message_content, status, sent_at, etc.
     - `ConfirmacaoPaciente` (Patient Confirmation): ID, disparo_id, confirmed_at, method (SMS, WhatsApp, etc.), status.
     - `LogAuditoriaProtecaoDados` (Data Protection Audit Log): ID, entity_type, entity_id, action, user_id, timestamp, ip_address, compliance_status.
   - **SUS/APS Standards Integration:**
     - CIAP-2 codes for health conditions.
     - CID-10 codes for diagnoses.
     - SOAP method for clinical notes (optional but can be referenced in schemas/models).
     - CNS (Cartão Nacional de Saúde) and CPF validation.
   - **Pydantic v2 Schemas:** For input/output validation.
   - **Repository Class:** Async/Sync? I'll use SQLAlchemy 2.0 async style as it's modern, but I'll make it compatible. Actually, I'll stick to synchronous for simplicity unless specified, but SQLAlchemy 2.0 supports both. I'll use synchronous for broader compatibility, but add type hints. I'll explicitly use `sqlalchemy.orm` and `sqlalchemy.ext.asyncio` if needed, but I'll stick to sync for the repo to keep it straightforward, or provide async as it's standard now. I'll use sync for simplicity but note it's SQLAlchemy 2.0 style. Actually, I'll use `sqlalchemy.orm` with `Session` and type hints.
   - **Testing:** pytest with `pytest-asyncio` or sync. I'll use sync for simplicity, but ensure it's comprehensive. I'll mock the database or use `pytest` with `sqlalchemy` in-memory SQLite.

3.  **Draft - `backend/app/repositories/campanhas_repo.py`:**
   - Imports: `uuid`, `datetime`, `enum`, `sqlalchemy`, `pydantic`, `typing`.
   - Enums: `CampanhaStatus`, `DisparoStatus`, `CanalComunicacao`, `AcaoAuditoria`, `StatusConformidade`.
   - Models:
     - `Campanha`: `id`, `nome`, `descricao`, `codigo_ciap2`, `codigo_cid10`, `status`, `data_criacao`, `data_atualizacao`.
     - `Disparo`: `id`, `campanha_id`, `cns`, `cpf`, `canal`, `conteudo`, `status`, `data_envio`, `data_atualizacao`.
     - `ConfirmacaoPaciente`: `id`, `disparo_id`, `confirmado_em`, `metodo`, `status`.
     - `LogAuditoriaProtecaoDados`: `id`, `entidade_tipo`, `entidade_id`, `acao`, `usuario_id`, `data_hora`, `ip_address`, `status_conformidade`.
   - Schemas (Pydantic v2):
     - `CampanhaCreate`, `CampanhaUpdate`, `CampanhaRead`.
     - `DisparoCreate`, `DisparoUpdate`, `DisparoRead`.
     - `ConfirmacaoPacienteCreate`, `ConfirmacaoPacienteRead`.
     - `LogAuditoriaCreate`, `LogAuditoriaRead`.
   - Repository Class: `CampanhasRepository`
     - Methods: `criar_campanha`, `obter_campanha`, `atualizar_campanha`, `excluir_campanha`, `registrar_disparo`, `obter_disparos_por_campanha`, `registrar_confirmacao`, `obter_confirmacoes_por_disparo`, `registrar_log_auditoria`, `obter_logs_auditoria`, `obter_relatorio_campanha`.
     - Use SQLAlchemy 2.0 syntax: `select`, `insert`, `update`, `delete`, `session.execute()`.
     - Strict typing with Pydantic v2.
     - Validate CNS/CPF format (basic regex or checksum simulation for brevity, but I'll add a validation function).
     - CIAP-2/CID-10 validation (basic format check).
     - SOAP method reference in docstrings/comments.

   Let's write it out carefully.

   *Self-Correction/Refinement during drafting:*
   - SQLAlchemy 2.0 uses `Mapped` and `mapped_column`. I'll use that.
   - Pydantic v2 uses `ConfigDict`, `Field`, `model_validator`.
   - CNS validation: 15 digits, checksum. I'll add a simple validator.
   - CPF validation: 11 digits, checksum. I'll add a simple validator.
   - CIAP-2: 2-3 letters + 1-2 digits. CID-10: 1 letter + 1-2 digits.
   - I'll keep validators simple but functional.
   - Repository will take a `Session` or use a provided session factory. I'll make it accept a `Session` in methods or use a class-level session for simplicity in tests. Actually, dependency injection is better, but for a single file, I'll pass `session` to methods or use a context manager. I'll design it to accept a `Session` instance.

   Structure:
   ```python
   # Arquivo: backend/app/repositories/campanhas_repo.py
   import uuid
   from datetime import datetime
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy import select, insert, update, delete, func
   from sqlalchemy.orm import Session, Mapped, mapped_column
   from sqlalchemy import String, Text, DateTime, Enum as SAEnum, Boolean, ForeignKey
   import re

   # Enums
   class CampanhaStatus(str, Enum):
       RASCUNHO = "rascunho"
       ATIVA = "ativa"
       PAUSADA = "pausada"
       CONCLUIDA = "concluida"

   class DisparoStatus(str, Enum):
       AGUARDANDO = "aguardando"
       ENVIADO = "enviado"
       FALHA = "falha"
       CONFIRMADO = "confirmado"

   class CanalComunicacao(str, Enum):
       SMS = "sms"
       WHATSAPP = "whatsapp"
       EMAIL = "email"
       TELEFONE = "telefone"

   class AcaoAuditoria(str, Enum):
       CRIACAO = "criacao"
       ATUALIZACAO = "atualizacao"
       EXCLUSAO = "exclusao"
       ACESSO = "acesso"
       EXPORTACAO = "exportacao"

   class StatusConformidade(str, Enum):
       CONFORME = "conforme"
       NAO_CONFORME = "nao_conforme"
       PENDENTE = "pendente"

   # Models (SQLAlchemy 2.0)
   class CampanhaModel(Base):
       __tablename__ = "campanhas"
       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       nome: Mapped[str] = mapped_column(String(255), nullable=False)
       descricao: Mapped[Optional[str]] = mapped_column(Text)
       codigo_ciap2: Mapped[Optional[str]] = mapped_column(String(10))
       codigo_cid10: Mapped[Optional[str]] = mapped_column(String(10))
       status: Mapped[CampanhaStatus] = mapped_column(SAEnum(CampanhaStatus), default=CampanhaStatus.RASCUNHO)
       data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       data_atualizacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

   # ... similar for others ...
   ```

   Wait, I need to import `Base` from somewhere. I'll assume a base module or define it inline for completeness. I'll define `Base = declarative_base()` at the top.

   Let's refine the models and schemas carefully. I'll make sure it's strictly typed and follows SQLAlchemy 2.0 conventions.

   *Pydantic Schemas:*
   ```python
   class CampanhaBase(BaseModel):
       nome: str = Field(..., min_length=1, max_length=255)
       descricao: Optional[str] = None
       codigo_ciap2: Optional[str] = None
       codigo_cid10: Optional[str] = None

       @field_validator("codigo_ciap2")
       @classmethod
       def validate_ciap2(cls, v):
           if v and not re.match(r"^[A-Z]{2,3}\d{1,2}$", v):
               raise ValueError("Código CIAP-2 inválido. Formato esperado: 2-3 letras + 1-2 dígitos.")
           return v

       @field_validator("codigo_cid10")
       @classmethod
       def validate_cid10(cls, v):
           if v and not re.match(r"^[A-Z]\d{1,2}$", v):
               raise ValueError("Código CID-10 inválido. Formato esperado: 1 letra + 1-2 dígitos.")
           return v

   class CampanhaCreate(CampanhaBase):
       pass

   class CampanhaRead(CampanhaBase):
       model_config = ConfigDict(from_attributes=True)
       id: uuid.UUID
       status: CampanhaStatus
       data_criacao: datetime
       data_atualizacao: datetime
   ```

   *Repository Class:*
   I'll create `CampanhasRepository` with methods that take a `Session` as the first argument, or use a class-level session for simplicity in the test. Actually, it's better to pass `session` to methods or use a context manager. I'll design it to accept `session: Session` in each method for explicit dependency injection, which is standard.

   Methods needed:
   - `criar_campanha(session, dto: CampanhaCreate) -> CampanhaRead`
   - `obter_campanha(session, campanha_id: uuid.UUID) -> Optional[CampanhaRead]`
   - `registrar_disparo(session, campanha_id: uuid.UUID, cns: str, cpf: str, canal: CanalComunicacao, conteudo: str) -> DisparoRead`
   - `obter_disparos_por_campanha(session, campanha_id: uuid.UUID) -> List[DisparoRead]`
   - `registrar_confirmacao(session, disparo_id: uuid.UUID, metodo: str) -> ConfirmacaoPacienteRead`
   - `obter_confirmacoes_por_disparo(session, disparo_id: uuid.UUID) -> List[ConfirmacaoPacienteRead]`
   - `registrar_log_auditoria(session, entidade_tipo: str, entidade_id: uuid.UUID, acao: AcaoAuditoria, usuario_id: str, ip_address: str) -> LogAuditoriaRead`
   - `obter_logs_auditoria(session, entidade_tipo: str, entidade_id: uuid.UUID) -> List[LogAuditoriaRead]`
   - `obter_relatorio_campanha(session, campanha_id: uuid.UUID) -> Dict[str, Any]`

   I'll add CNS/CPF validation in the repository or schemas. I'll add it to the `DisparoCreate` schema.

   *CNS/CPF Validation:*
   ```python
   @field_validator("cns")
   @classmethod
   def validate_cns(cls, v):
       if v and not re.match(r"^\d{15}$", v):
           raise ValueError("CNS inválido. Deve conter 15 dígitos.")
       # Checksum validation omitted for brevity but noted
       return v
   ```
   Actually, I'll implement basic checksums or just regex for simplicity, but mention it's for demonstration. I'll stick to regex for brevity but ensure it's clear.

   *Repository Implementation:*
   I'll use SQLAlchemy 2.0 `select`, `insert`, `update`, `delete`. I'll make sure to handle sessions properly.

   Let's draft the full file carefully.

4.  **Draft - `backend/app/repositories/test_campanhas_repo.py`:**
   - Use `pytest`, `sqlalchemy`, `pytest-asyncio` (or sync). I'll use sync for simplicity.
   - Create an in-memory SQLite database.
   - Create tables.
   - Test each repository method.
   - Test validation errors.
   - Test audit log tracking.
   - Test confirmation status updates.
   - Use `pytest` fixtures for session and database.

   Structure:
   ```python
   # Arquivo: backend/app/repositories/test_campanhas_repo.py
   import pytest
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from backend.app.repositories.campanhas_repo import (
       Base, CampanhasRepository, CampanhaCreate, DisparoCreate,
       CampanhaStatus, DisparoStatus, CanalComunicacao, AcaoAuditoria, StatusConformidade
   )
   # ... tests ...
   ```

   I'll write comprehensive tests covering:
   - CRUD campaigns
   - Dispatch registration and tracking
   - Patient confirmation
   - Audit logging
   - Validation errors (CIAP-2, CID-10, CNS, CPF)
   - Report generation

5.  **Refine & Self-Correction/Verification:**
   - *Python 3.12 & Pydantic v2:* Use `from pydantic import BaseModel, Field, field_validator, ConfigDict`. Use `model_config = ConfigDict(from_attributes=True)`.
   - *SQLAlchemy 2.0:* Use `Mapped`, `mapped_column`, `select`, `insert`, `update`, `delete`. Ensure `Base` is defined.
   - *SUS/APS Standards:* CIAP-2, CID-10, SOAP, CNS/CPF. I'll add docstrings/comments referencing SOAP method and SUS standards. I'll add a `metodo_soap` field to models if relevant, or just document it. Actually, SOAP is a clinical documentation method, not necessarily a DB field, but I can add `nota_clinica_soap` to `Campanha` or `Disparo` for context. I'll add it to `Campanha` as `nota_clinica_soap: Mapped[Optional[str]]`.
   - *Strict Typing:* All functions/methods have type hints. Pydantic schemas are strictly typed.
   - *Repository Pattern:* Methods are explicit, use SQLAlchemy 2.0 syntax.
   - *Tests:* Comprehensive, use `pytest`, cover happy path, edge cases, validation.
   - *File Paths:* Clearly marked.
   - *Executable:* Code should run as-is if dependencies are installed. I'll add a `if __name__ == "__main__":` block for DB setup/demo, but it's optional. I'll focus on the repo and tests.

   Let's write the code carefully.

   *Structure Check:*
   - `backend/app/repositories/campanhas_repo.py`
   - `backend/app/repositories/test_campanhas_repo.py`
   - I'll make sure imports are correct.
   - I'll use `sqlalchemy.orm.declarative_base()` for `Base`.
   - I'll ensure Pydantic v2 compatibility (`from_attributes=True` instead of `orm_mode`).
   - I'll add CNS/CPF validation with checksums (simplified but functional).
   - I'll add CIAP-2/CID-10 validation.
   - I'll add SOAP note field.
   - I'll ensure strict typing.

   *Code Generation (Mental Walkthrough):*
   ```python
   # Arquivo: backend/app/repositories/campanhas_repo.py
   import uuid
   from datetime import datetime
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy import (
       select, insert, update, delete, func, String, Text, DateTime,
       Enum as SAEnum, Boolean, ForeignKey, CheckConstraint
   )
   from sqlalchemy.orm import Session, Mapped, mapped_column, declarative_base
   import re

   Base = declarative_base()

   # Enums...
   # Models...
   # Schemas...
   # Repository...
   ```

   I'll implement CNS/CPF validation properly. CNS checksum algorithm is complex, but I'll use a simplified version or just regex for brevity, but I'll note it. Actually, I'll implement a basic checksum for CPF and a placeholder for CNS, or just use regex to keep it concise but functional.