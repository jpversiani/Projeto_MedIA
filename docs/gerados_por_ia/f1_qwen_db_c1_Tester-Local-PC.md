Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Implement `backend/app/repositories/auditoria_telemedicina.py` with a class `AuditoriaTelemedicinaRepository` for logging teleconsultation events (connection, disconnection, patient confidentiality agreement acceptance, secure timestamping) using SQLAlchemy 2.0.
   - **Context:** MedIA project for private/insurance teleconsultations (TISS ANS 4.01 / DMED Receita Federal), Primary Care/Family Health methodology.
   - **Constraints:**
     - No SUS/SISAB or IoT peripheral code.
     - Python 3.12, strict typing, Pydantic v2, SQLAlchemy 2.0.
     - Production code only in `backend/app/`, tests in `backend/tests/`.
     - Preserve 100% green test suite (implies I should provide tests too, or at least ensure the implementation is testable and matches expected patterns).
     - Provide complete, executable code.
     - Specify file paths in code blocks.

2.  **Analyze Requirements for `AuditoriaTelemedicinaRepository`:**
   - **Events to log:** Connection, Disconnection, Patient confidentiality agreement acceptance (LGPD/CFM), Secure timestamp.
   - **Tech Stack:** SQLAlchemy 2.0 (async/sync? Usually async is preferred in modern FastAPI, but I'll stick to sync or async based on common patterns. I'll use async SQLAlchemy 2.0 as it's standard for modern Python backends, but I'll make it clear. Actually, I'll use `async` with `Session` from `sqlalchemy.ext.asyncio` as it's standard, but I'll also provide sync if needed. I'll stick to async for modern stack, but ensure it's clear. Wait, the prompt says "SQLAlchemy 2.0", doesn't specify sync/async. I'll use async as it's standard for FastAPI, but I'll make the repository interface clear.)
   - **Pydantic v2:** For request/response models or data transfer.
   - **Strict Typing:** Use `typing` module, type hints.
   - **Secure Timestamp:** Use `datetime.now(timezone.utc)` or `datetime.utcnow()` (deprecated in 3.12, so `datetime.now(timezone.utc)` is correct).
   - **Database Model:** Need an `AuditoriaTelemedicina` model/table.
   - **Repository Methods:** `log_connection`, `log_disconnection`, `log_confidentiality_acceptance`, `get_secure_timestamp`, etc.

3.  **Design the Database Model (`backend/app/models/auditoria_telemedicina.py`):**
   - Table: `auditoria_telemedicina`
   - Columns:
     - `id`: UUID or int (PK)
     - `consulta_id`: UUID (FK to teleconsultas)
     - `paciente_id`: UUID (FK to pacientes)
     - `medico_id`: UUID (FK to medicos)
     - `evento`: Enum (CONEXAO, DESCONEXAO, ACEITE_SIGILO)
     - `detalhes`: JSON/Text (optional metadata)
     - `carimbo_hora_utc`: DateTime (timezone-aware)
     - `ip_origem`: String (optional)
     - `created_at`: DateTime
   - I'll define this model in `backend/app/models/auditoria_telemedicina.py`.

4.  **Design the Repository (`backend/app/repositories/auditoria_telemedicina.py`):**
   - Class: `AuditoriaTelemedicinaRepository`
   - Constructor: Takes `AsyncSession` (or `Session`)
   - Methods:
     - `async log_connection(self, consulta_id, paciente_id, medico_id, ip_origem: str = None) -> None`
     - `async log_disconnection(self, consulta_id, paciente_id, medico_id, duracao_segundos: int = None) -> None`
     - `async log_confidentiality_acceptance(self, consulta_id, paciente_id, medico_id, versao_termo: str = "1.0") -> None`
     - `async get_secure_timestamp(self) -> datetime`
     - Helper to create event records.
   - Use SQLAlchemy 2.0 syntax: `insert()`, `select()`, `session.execute()`, `session.commit()`.
   - Pydantic v2: Maybe define a `AuditoriaEvento` model for type hints, but the prompt says "tipagem estrita Pydantic v2". I'll use Pydantic for data validation/serialization if needed, but for DB operations, SQLAlchemy models are standard. I'll add Pydantic models for DTOs if necessary, or just use strict typing on the repository methods.

5.  **Refine Implementation Details:**
   - **Secure Timestamp:** `datetime.now(timezone.utc)` is correct. I'll make it a method that returns it, or just use it directly. The prompt says "carimbo de data/hora seguro com SQLAlchemy 2.0", so I'll ensure the DB model uses `server_default=func.now()` or sets it explicitly in Python with timezone awareness.
   - **Pydantic v2:** I'll create a Pydantic model for the audit event DTO to satisfy the requirement, even if it's just for type hints or response serialization.
   - **SQLAlchemy 2.0:** Use `Insert`, `Select`, `session.execute()`, `session.commit()`.
   - **Strict Typing:** Use `from typing import ...`, `Enum`, `UUID`, `datetime`, `Optional`, `AsyncSession`.
   - **Structure:**
     ```python
     # backend/app/models/auditoria_telemedicina.py
     # backend/app/repositories/auditoria_telemedicina.py
     # backend/tests/test_auditoria_telemedicina.py
     ```

   Let's draft the model first:
   ```python
   from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, func
   from sqlalchemy.dialects.postgresql import UUID
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
   from datetime import datetime, timezone
   import uuid

   class Base(DeclarativeBase):
       pass

   class AuditoriaTelemedicinaStatus(str, Enum):
       CONEXAO = "CONEXAO"
       DESCONEXAO = "DESCONEXAO"
       ACEITE_SIGILO = "ACEITE_SIGILO"

   class AuditoriaTelemedicina(Base):
       __tablename__ = "auditoria_telemedicina"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       consulta_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teleconsultas.id"))
       paciente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pacientes.id"))
       medico_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("medicos.id"))
       evento: Mapped[AuditoriaTelemedicinaStatus] = mapped_column(Enum(AuditoriaTelemedicinaStatus))
       detalhes: Mapped[dict | None] = mapped_column(Text, nullable=True) # JSON stored as text
       carimbo_hora_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       ip_origem: Mapped[str | None] = mapped_column(String(45), nullable=True)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
   ```
   Wait, SQLAlchemy 2.0 uses `Mapped` and `mapped_column`. I'll stick to that. For JSON, I'll use `JSON` type or `Text`. I'll use `Text` for simplicity, or `JSON` if available. I'll stick to `Text` and note it's JSON.

   Now the repository:
   ```python
   # backend/app/repositories/auditoria_telemedicina.py
   from typing import AsyncSession, Optional, Dict, Any
   from uuid import UUID
   from datetime import datetime, timezone
   from sqlalchemy import insert, select, func
   from sqlalchemy.orm import Session
   from app.models.auditoria_telemedicina import AuditoriaTelemedicina, AuditoriaTelemedicinaStatus
   from pydantic import BaseModel, Field, field_validator
   import uuid

   class AuditoriaEventoDTO(BaseModel):
       consulta_id: UUID
       paciente_id: UUID
       medico_id: UUID
       evento: AuditoriaTelemedicinaStatus
       detalhes: Optional[Dict[str, Any]] = None
       ip_origem: Optional[str] = None
       carimbo_hora_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

       @field_validator('carimbo_hora_utc', mode='before')
       @classmethod
       def ensure_utc_timezone(cls, v):
           if v is None:
               return datetime.now(timezone.utc)
           if v.tzinfo is None:
               return v.replace(tzinfo=timezone.utc)
           return v

   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def log_connection(self, consulta_id: UUID, paciente_id: UUID, medico_id: UUID, ip_origem: Optional[str] = None) -> None:
           evento = AuditoriaEventoDTO(
               consulta_id=consulta_id,
               paciente_id=paciente_id,
               medico_id=medico_id,
               evento=AuditoriaTelemedicinaStatus.CONEXAO,
               ip_origem=ip_origem
           )
           await self._persist_event(evento)

       async def log_disconnection(self, consulta_id: UUID, paciente_id: UUID, medico_id: UUID, duracao_segundos: Optional[int] = None) -> None:
           detalhes = {"duracao_segundos": duracao_segundos} if duracao_segundos is not None else None
           evento = AuditoriaEventoDTO(
               consulta_id=consulta_id,
               paciente_id=paciente_id,
               medico_id=medico_id,
               evento=AuditoriaTelemedicinaStatus.DESCONEXAO,
               detalhes=detalhes
           )
           await self._persist_event(evento)

       async def log_confidentiality_acceptance(self, consulta_id: UUID, paciente_id: UUID, medico_id: UUID, versao_termo: str = "1.0") -> None:
           detalhes = {"versao_termo": versao_termo, "conformidade": "LGPD / CFM"}
           evento = AuditoriaEventoDTO(
               consulta_id=consulta_id,
               paciente_id=paciente_id,
               medico_id=medico_id,
               evento=AuditoriaTelemedicinaStatus.ACEITE_SIGILO,
               detalhes=detalhes
           )
           await self._persist_event(evento)

       async def _persist_event(self, evento: AuditoriaEventoDTO) -> None:
           stmt = insert(AuditoriaTelemedicina).values(
               id=uuid.uuid4(),
               consulta_id=evento.consulta_id,
               paciente_id=evento.paciente_id,
               medico_id=evento.medico_id,
               evento=evento.evento,
               detalhes=evento.detalhes,
               ip_origem=evento.ip_origem,
               carimbo_hora_utc=evento.carimbo_hora_utc
           )
           await self.session.execute(stmt)
           await self.session.commit()

       async def get_secure_timestamp(self) -> datetime:
           return datetime.now(timezone.utc)
   ```

   Wait, I need to make sure it's strictly typed and uses Pydantic v2 correctly. The `field_validator` is correct for v2. I'll adjust imports and types to be precise. Also, SQLAlchemy 2.0 recommends `session.execute()` and `session.commit()`. For async, it's `await session.execute()` and `await session.commit()`.

   I should also consider that the prompt says "carimbo de data/hora seguro com SQLAlchemy 2.0". This might imply using `server_default=func.now()` or explicitly setting it. I'll explicitly set it in Python with `timezone.utc` for security and consistency, which is standard practice.

   Let's refine the repository to be more robust and strictly typed:
   - Use `typing` properly.
   - Ensure Pydantic v2 compatibility.
   - Add docstrings.
   - Handle potential errors? The prompt says "código de produção apenas", so I'll keep it clean and production-ready.

   Now, I need to provide the test suite as well, since it says "Preservar 100% da suíte de testes verde." I'll create a test file that mocks the session and tests the repository methods.

   Test file structure:
   ```python
   # backend/tests/test_auditoria_telemedicina.py
   import pytest
   from unittest.mock import AsyncMock, MagicMock
   from uuid import uuid4
   from datetime import datetime, timezone
   from app.repositories.auditoria_telemedicina import AuditoriaTelemedicinaRepository, AuditoriaEventoDTO
   from app.models.auditoria_telemedicina import AuditoriaTelemedicinaStatus

   @pytest.fixture
   def mock_session():
       session = AsyncMock()
       session.execute = AsyncMock()
       session.commit = AsyncMock()
       return session

   @pytest.fixture
   def repository(mock_session):
       return AuditoriaTelemedicinaRepository(session=mock_session)

   @pytest.mark.asyncio
   async def test_log_connection(repository, mock_session):
       consulta_id = uuid4()
       paciente_id = uuid4()
       medico_id = uuid4()
       ip = "192.168.1.1"

       await repository.log_connection(consulta_id, paciente_id, medico_id, ip)

       mock_session.execute.assert_called_once()
       mock_session.commit.assert_called_once()
       # Verify the statement contains correct values
       call_args = mock_session.execute.call_args[0][0]
       assert call_args._values["evento"] == AuditoriaTelemedicinaStatus.CONEXAO
       assert call_args._values["ip_origem"] == ip

   # ... other tests
   ```

   I need to make sure the tests are robust and match SQLAlchemy 2.0's `insert()` behavior. `insert()` returns an `Insert` object. Checking `_values` might be implementation-specific. Better to just verify that `execute` and `commit` were called, and maybe use a more reliable assertion or just trust the mock. For production-grade tests, I'll use `pytest-asyncio` and mock the session properly. I'll also add tests for `log_disconnection`, `log_confidentiality_acceptance`, and `get_secure_timestamp`.

   Let's adjust the test to be more standard and reliable:
   ```python
   import pytest
   from unittest.mock import AsyncMock, call
   from uuid import uuid4
   from datetime import datetime, timezone
   from app.repositories.auditoria_telemedicina import AuditoriaTelemedicinaRepository
   from app.models.auditoria_telemedicina import AuditoriaTelemedicinaStatus

   @pytest.fixture
   def mock_session():
       session = AsyncMock()
       session.execute = AsyncMock()
       session.commit = AsyncMock()
       return session

   @pytest.fixture
   def repository(mock_session):
       return AuditoriaTelemedicinaRepository(session=mock_session)

   @pytest.mark.asyncio
   async def test_log_connection_calls_execute_and_commit(repository, mock_session):
       consulta_id = uuid4()
       paciente_id = uuid4()
       medico_id = uuid4()
       ip = "10.0.0.1"

       await repository.log_connection(consulta_id, paciente_id, medico_id, ip)

       mock_session.execute.assert_called_once()
       mock_session.commit.assert_called_once()

   @pytest.mark.asyncio
   async def test_log_disconnection_calls_execute_and_commit(repository, mock_session):
       consulta_id = uuid4()
       paciente_id = uuid4()
       medico_id = uuid4()
       duracao = 300

       await repository.log_disconnection(consulta_id, paciente_id, medico_id, duracao)

       mock_session.execute.assert_called_once()
       mock_session.commit.assert_called_once()

   @pytest.mark.asyncio
   async def test_log_confidentiality_acceptance_calls_execute_and_commit(repository, mock_session):
       consulta_id = uuid4()
       paciente_id = uuid4()
       medico_id = uuid4()

       await repository.log_confidentiality_acceptance(consulta_id, paciente_id, medico_id, "2.1")

       mock_session.execute.assert_called_once()
       mock_session.commit.assert_called_once()

   @pytest.mark.asyncio
   async def test_get_secure_timestamp_returns_utc(repository):
       ts = await repository.get_secure_timestamp()
       assert ts.tzinfo is not None
       assert ts.tzinfo == timezone.utc
   ```

   This looks solid. Now, I need to ensure the model and repository are correctly structured and follow all constraints.

   Let's review constraints:
   - Python 3.12, strict typing, Pydantic v2, SQLAlchemy 2.0.
   - No SUS/SISAB or IoT.
   - Production code in `backend/app/`, tests in `backend/tests/`.
   - Complete and executable.
   - Specify file paths.

   I'll structure the response with three files:
   1. `backend/app/models/auditoria_telemedicina.py` (Model)
   2. `backend/app/repositories/auditoria_telemedicina.py` (Repository)
   3. `backend/tests/test_auditoria_telemedicina.py` (Tests)

   I'll make sure the code is self-contained, uses correct imports, and follows modern Python/SQLAlchemy/Pydantic standards.

   One detail: SQLAlchemy 2.0 `insert()` returns an `Insert` object. To verify values in tests, I can use `call_args[0][0]._select_args` or just rely on the fact that it's a mock. For simplicity and reliability in tests, I'll just assert `execute` and `commit` were called. I'll also add a test that verifies the Pydantic model validation works correctly.

   Let's refine the repository to be strictly typed and production-ready:
   - Use `typing` module.
   - Use `datetime.now(timezone.utc)` for secure timestamp.
  