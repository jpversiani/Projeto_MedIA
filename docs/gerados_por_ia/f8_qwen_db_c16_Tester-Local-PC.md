Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for a "Health Campaigns Repository and Send History" (C16) for the "MedIA" project.
   - **Requirements:**
     - Track sent messages, confirmation status by patient, and data protection audit log.
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification.
     - Full compliance and automated test coverage with pytest.
     - Provide complete, executable code.
     - Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/campanhas_repo.py`
   - **Domain:** Health campaigns, message dispatch history, patient confirmation, data protection audit.
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0 (async or sync? Usually async is preferred in modern FastAPI, but I'll stick to sync or provide async with `AsyncSession` if needed. I'll use `sqlalchemy.orm` and `sqlalchemy.ext.asyncio` if needed, but I'll stick to standard SQLAlchemy 2.0 with `Session` for simplicity and clarity, or explicitly use `AsyncSession` if it's for FastAPI. I'll assume standard SQLAlchemy 2.0 with `Session` for repository pattern, but I'll make it compatible with both or explicitly use `AsyncSession` as it's common in modern stacks. Actually, I'll use `sqlalchemy.orm.Session` for simplicity, but I'll note it's easily adaptable. Wait, the prompt says "SQLAlchemy 2.0", so I'll use the modern declarative style with `Mapped`, `mapped_column`, etc.)
   - **Standards:** CIAP-2 (Classificação Internacional de Atenção Primária), CID-10 (ICD-10), SOAP (Subjective, Objective, Assessment, Plan), CNS (Cartão Nacional de Saúde), CPF (Cadastro de Pessoas Físicas).
   - **Testing:** pytest coverage, full compliance. I need to provide the repository code AND a test file. The prompt says "Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo". So I'll provide both `campanhas_repo.py` and `test_campanhas_repo.py`.

3.  **Design Data Models (Pydantic + SQLAlchemy):**
   - **Campaign (Campanha):** ID, name, description, start_date, end_date, status, target_population (CIAP-2/CID-10 codes), created_at, updated_at.
   - **Dispatch (Disparo/Envio):** ID, campaign_id, patient_cns, patient_cpf, message_content, status (sent, delivered, confirmed, failed), sent_at, confirmed_at, soap_notes (optional but relevant to SUS), created_at.
   - **AuditLog (Log de Auditoria LGPD):** ID, entity_type, entity_id, action, user_id, ip_address, timestamp, justification (for data protection compliance).
   - **Pydantic Schemas:** CreateRequest, DispatchCreate, DispatchResponse, AuditLogCreate, AuditLogResponse, PatientConfirmation.
   - **SQLAlchemy Models:** Map to tables. Use `Mapped` and `mapped_column` (SQLAlchemy 2.0 style).

   Let's refine the models to strictly follow SUS/APS standards:
   - `Campanha`: `id`, `nome`, `descricao`, `codigos_ciap2` (list), `codigos_cid10` (list), `status`, `data_inicio`, `data_fim`, `criado_em`, `atualizado_em`
   - `Disparo`: `id`, `campanha_id`, `cns_paciente` (str, 15 digits), `cpf_paciente` (str, 11 digits), `conteudo_mensagem`, `status_envio` (enum), `data_envio`, `data_confirmacao`, `notas_soap` (dict/JSON), `criado_em`
   - `LogAuditoriaLGPD`: `id`, `entidade_tipo`, `entidade_id`, `acao`, `usuario_id`, `ip_origem`, `justificativa_lgpd`, `data_hora`, `criado_em`

   Pydantic v2 schemas will validate CNS/CPF formats, CIAP-2/CID-10 codes, SOAP structure, and statuses.

4.  **Repository Implementation:**
   - Need methods for:
     - `criar_campanha`
     - `listar_campanhas`
     - `registrar_disparo`
     - `atualizar_status_disparo`
     - `confirmar_paciente`
     - `registrar_auditoria_lgpd`
     - `obter_historico_campanha`
   - Use SQLAlchemy 2.0 async or sync? I'll use `AsyncSession` as it's standard for modern FastAPI backends, but I'll make it clear. Actually, I'll stick to synchronous `Session` for broader compatibility unless specified, but I'll add type hints properly. I'll use `sqlalchemy.ext.asyncio.AsyncSession` to be modern, but I'll also provide sync if needed. Let's stick to `AsyncSession` as it's common, but I'll make it generic with `Session` type hint or just use `AsyncSession` explicitly. I'll use `AsyncSession` for async support.
   - Wait, the prompt says "SQLAlchemy 2.0". I'll use the modern `Mapped` syntax.
   - I'll structure the repository with dependency injection in mind, but keep it self-contained.

   Let's draft the SQLAlchemy models:
   ```python
   from sqlalchemy import String, Text, DateTime, Boolean, Enum, JSON, ForeignKey
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
   from sqlalchemy.sql import func
   import enum

   class Base(DeclarativeBase):
       pass

   class StatusDisparo(str, enum.Enum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       ENTREGUE = "entregue"
       CONFIRMADO = "confirmado"
       FALHA = "falha"

   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[int] = mapped_column(primary_key=True)
       nome: Mapped[str] = mapped_column(String(100))
       descricao: Mapped[str] = mapped_column(Text)
       codigos_ciap2: Mapped[list[str]] = mapped_column(JSON)
       codigos_cid10: Mapped[list[str]] = mapped_column(JSON)
       status: Mapped[str] = mapped_column(String(20), default="ativa")
       data_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
       data_fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))
       criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

   class Disparo(Base):
       __tablename__ = "disparos"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"))
       cns_paciente: Mapped[str] = mapped_column(String(15))
       cpf_paciente: Mapped[str] = mapped_column(String(14))
       conteudo_mensagem: Mapped[str] = mapped_column(Text)
       status_envio: Mapped[StatusDisparo] = mapped_column(Enum(StatusDisparo), default=StatusDisparo.PENDENTE)
       data_envio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
       data_confirmacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
       notas_soap: Mapped[dict] = mapped_column(JSON, nullable=True)
       criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

   class LogAuditoriaLGPD(Base):
       __tablename__ = "logs_auditoria_lgpd"
       id: Mapped[int] = mapped_column(primary_key=True)
       entidade_tipo: Mapped[str] = mapped_column(String(50))
       entidade_id: Mapped[int] = mapped_column(Integer)
       acao: Mapped[str] = mapped_column(String(50))
       usuario_id: Mapped[int] = mapped_column(Integer, nullable=True)
       ip_origem: Mapped[str] = mapped_column(String(45), nullable=True)
       justificativa_lgpd: Mapped[str] = mapped_column(Text)
       data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
   ```
   Wait, `Integer` needs import. I'll fix imports.

   Pydantic schemas:
   - Need validation for CNS (15 digits), CPF (11 digits), CIAP-2/CID-10 codes, SOAP structure.
   - I'll use `@field_validator` from pydantic.v2.

   Repository class:
   - `CampanhasRepository`
   - Methods using `AsyncSession` or `Session`. I'll use `AsyncSession` for modern async apps, but I'll type it as `AsyncSession` from `sqlalchemy.ext.asyncio`.
   - I'll implement CRUD and specific business logic.

   Let's draft the repository carefully.

5.  **Draft Code (Mental Refinement):**
   I'll structure it properly with imports, models, schemas, and repository.
   I need to ensure strict typing, Pydantic v2, SQLAlchemy 2.0.
   I'll add validation for CNS/CPF, CIAP-2/CID-10, SOAP.
   I'll add audit logging integration.
   I'll write comprehensive pytest tests.

   Structure:
   ```python
   # Arquivo: backend/app/repositories/campanhas_repo.py
   import enum
   from datetime import datetime, timezone
   from typing import Optional, List, Dict, Any
   from uuid import uuid4

   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from pydantic.v2 import EmailStr # Not needed
   from sqlalchemy import String, Text, DateTime, Boolean, Enum, JSON, ForeignKey, Integer
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, update, delete
   from sqlalchemy.sql import func
   import re

   # Base
   class Base(DeclarativeBase):
       pass

   # Enums
   class StatusDisparo(str, enum.Enum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       ENTREGUE = "entregue"
       CONFIRMADO = "confirmado"
       FALHA = "falha"

   # Models
   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[int] = mapped_column(primary_key=True)
       nome: Mapped[str] = mapped_column(String(100))
       descricao: Mapped[str] = mapped_column(Text)
       codigos_ciap2: Mapped[list[str]] = mapped_column(JSON)
       codigos_cid10: Mapped[list[str]] = mapped_column(JSON)
       status: Mapped[str] = mapped_column(String(20), default="ativa")
       data_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
       data_fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))
       criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

   class Disparo(Base):
       __tablename__ = "disparos"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"))
       cns_paciente: Mapped[str] = mapped_column(String(15))
       cpf_paciente: Mapped[str] = mapped_column(String(14))
       conteudo_mensagem: Mapped[str] = mapped_column(Text)
       status_envio: Mapped[StatusDisparo] = mapped_column(Enum(StatusDisparo), default=StatusDisparo.PENDENTE)
       data_envio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
       data_confirmacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
       notas_soap: Mapped[dict] = mapped_column(JSON, nullable=True)
       criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

   class LogAuditoriaLGPD(Base):
       __tablename__ = "logs_auditoria_lgpd"
       id: Mapped[int] = mapped_column(primary_key=True)
       entidade_tipo: Mapped[str] = mapped_column(String(50))
       entidade_id: Mapped[int] = mapped_column(Integer)
       acao: Mapped[str] = mapped_column(String(50))
       usuario_id: Mapped[int] = mapped_column(Integer, nullable=True)
       ip_origem: Mapped[str] = mapped_column(String(45), nullable=True)
       justificativa_lgpd: Mapped[str] = mapped_column(Text)
       data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
   ```

   Pydantic Schemas:
   Need to validate CNS (15 digits), CPF (11 digits), CIAP-2/CID-10 (alphanumeric, usually 1-4 chars for CIAP-2, 1 letter + 2 digits for CID-10), SOAP (S, O, A, P keys).
   I'll add validators.

   Repository:
   ```python
   class CampanhasRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def criar_campanha(self, schema: CampanhaCreate) -> Campanha:
           # audit log
           await self._registrar_auditoria("CAMPAIGN", None, "CREATE", schema.criado_por, schema.ip_origem, "Criação de campanha de saúde pública")
           campanha = Campanha(**schema.model_dump())
           self.session.add(campanha)
           await self.session.flush()
           return campanha

       async def registrar_disparo(self, campanha_id: int, schema: DisparoCreate) -> Disparo:
           # check campaign exists
           # insert
           # audit
           ...
   ```
   I'll make it complete and robust.

   Let's write the full code carefully. I'll ensure all imports are correct, types are strict, and it follows SQLAlchemy 2.0 and Pydantic v2 standards.

   I'll also create the test file `test_campanhas_repo.py` with pytest, using `pytest-asyncio`, `sqlalchemy.ext.asyncio.sessionmaker`, and in-memory SQLite for testing.

   Key considerations for tests:
   - Async fixtures
   - Database session management
   - Validation tests (CNS, CPF, CIAP-2, CID-10, SOAP)
   - Repository logic tests (CRUD, status updates, audit logs)
   - Coverage markers

   Let's draft the repository file first.

   **Repository File Structure:**
   - Imports
   - Base
   - Enums
   - SQLAlchemy Models
   - Pydantic Schemas (with validators)
   - Repository Class
   - Helper functions (CNS/CPF validation, CIAP/CID validation, SOAP validation)

   **Test File Structure:**
   - Imports
   - Fixtures (async engine, session, repo)
   - Test classes/functions
   - Validation tests
   - CRUD tests
   - Audit log tests
   - Status update tests

   I'll write it out carefully.
   *Self-Correction/Refinement during thought:*
   - Pydantic v2 uses `pydantic` directly, not `pydantic.v2`. I'll use `pydantic`.
   - SQLAlchemy 2.0 uses `Mapped` and `mapped_column`. I'll use them.
   - CNS validation: 15 digits, check digit algorithm is complex, but I'll implement a basic regex and mention it's for format validation, or implement a simplified checksum if needed. I'll stick to regex `^\d{15}$` for brevity but add a comment about SUS validation. Actually, I'll implement a proper CNS check digit validator to be thorough.
   - CPF validation: standard algorithm.
   - CIAP-2 codes: typically 1-4 alphanumeric characters (e.g., A00, B12, C3).
   - CID-10 codes: 1 letter + 2 digits (e.g., A00, B34.2). I'll allow `^\w{1,4}$` for CIAP and `^\w{3}(\.\w{1,2})?$` for CID.
   - SOAP: dict with keys S, O, A, P.
   - I'll make sure the code is production-ready.

   Let's write the code. 
   I'll structure it carefully to avoid syntax errors and ensure compatibility.
   I'll use `sqlalchemy.ext.asyncio.AsyncSession` for the repository.
   I'll add type hints strictly.
   I'll include the test file as requested.

   *Code Generation Plan:*
   1. `backend/app/repositories/campanhas_repo.py`
      - Imports
      - Base
      - Enums
      - Models
      - Schemas (with validators)
      - Repository
   2. `tests/test_campanhas_repo.py`
      - Fixtures
      - Tests
   I'll ensure both are complete and executable.

   Let's draft carefully. 
   *Self-Correction/Verification during drafting