Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Implement `backend/app/repositories/auditoria_telemedicina.py` with a class `AuditoriaTelemedicinaRepository` for logging teleconsultation events (connection, disconnection, privacy policy acceptance, secure timestamping) using SQLAlchemy 2.0.
   - **Context:** Project MedIA, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), Python 3.12, strict typing with Pydantic v2, SQLAlchemy 2.0, full compliance with automated pytest tests.
   - **Output Requirement:** Provide complete, executable code. Specify file paths in comments or block headers.

2.  **Key Requirements Analysis:**
   - **Repository Class:** `AuditoriaTelemedicinaRepository`
   - **Events to Log:** Connection, Disconnection, Privacy Policy Acceptance (LGPD/CFM)
   - **Secure Timestamping:** Needs to be robust (UTC, timezone-aware, possibly using `datetime.now(timezone.utc)`)
   - **Database:** SQLAlchemy 2.0 (async or sync? Usually async is preferred in modern FastAPI, but I'll stick to sync for simplicity unless specified, or provide async as it's standard. I'll use `sqlalchemy.orm` with `Session` for standard ORM, but I'll make it compatible with both or explicitly use `AsyncSession` if it's a modern stack. Given the prompt says "SQLAlchemy 2.0", I'll use the modern declarative style with `Mapped`, `mapped_column`, etc.)
   - **Pydantic v2:** For request/response models or validation. I'll define Pydantic models for the audit events.
   - **SUS/APS Standards:** CIAP-2, CID-10, SOAP, CNS/CPF. These should be part of the audit log schema or related models.
   - **Testing:** Must be pytest-compliant. I'll provide the repository code and a corresponding test file structure, but the prompt specifically asks for the repository file. I'll focus on the repository but ensure it's testable.
   - **Strict Typing:** Python 3.12, type hints everywhere.

3.  **Design Decisions:**
   - **Database Model:** `TelemedicinaAuditoriaLog` table with columns:
     - `id` (UUID)
     - `consulta_id` (UUID, FK to teleconsultation)
     - `paciente_cns` (str)
     - `paciente_cpf` (str, optional)
     - `evento_tipo` (enum: CONNECTION, DISCONNECTION, PRIVACY_ACCEPTANCE)
     - `evento_detalhes` (JSON/text)
     - `carimbo_tempo` (datetime, UTC)
     - `ip_origem` (str, optional)
     - `agente` (str, e.g., doctor/patient ID)
     - `created_at` (datetime)
   - **Pydantic Models:** `AuditoriaEventoCreate` for input validation.
   - **Repository:** `AuditoriaTelemedicinaRepository` with methods like `registrar_conexao`, `registrar_desconexao`, `registrar_aceite_termos`, `registrar_evento`.
   - **Secure Timestamp:** Use `datetime.now(timezone.utc)` and ensure timezone awareness.
   - **SQLAlchemy 2.0:** Use `Mapped`, `mapped_column`, `DeclarativeBase`, `sessionmaker` or dependency injection pattern. I'll use a standard async/sync compatible approach with `Session` but explicitly type it. I'll assume sync for simplicity but note it can be adapted. Actually, modern FastAPI uses async, so I'll use `AsyncSession` but keep it generic enough. I'll stick to `Session` for broader compatibility unless specified, but I'll add type hints properly.
   - **SUS/APS Integration:** Add fields for `metodo_sus` (SOAP), `classificacao_ciap2`, `classificacao_cid10` to the audit log or related consultation model. I'll add them to the audit log for completeness.

4.  **Drafting the Code (Mental Refinement):**
   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   from __future__ import annotations
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Any, Optional
   from uuid import UUID

   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import String, Text, DateTime, Enum as SAEnum, ForeignKey
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, Session, relationship
   import sqlalchemy as sa

   # --- Models ---
   class EventoAuditoriaTipo(str, Enum):
       CONEXAO = "CONEXAO"
       DESCONEXAO = "DESCONEXAO"
       ACEITE_TERMOS = "ACEITE_TERMOS"

   class AuditoriaEventoCreate(BaseModel):
       consulta_id: UUID
       paciente_cns: str = Field(..., pattern=r"^\d{15}$")
       paciente_cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       evento_tipo: EventoAuditoriaTipo
       detalhes: Optional[dict[str, Any]] = None
       ip_origem: Optional[str] = None
       agente_id: str
       metodo_sus: str = Field(default="SOAP", pattern=r"^(SOAP|CIAP-2|CID-10)$")
       classificacao_ciap2: Optional[str] = None
       classificacao_cid10: Optional[str] = None

       @field_validator("metodo_sus")
       @classmethod
       def validar_metodo_sus(cls, v: str) -> str:
           if v not in ("SOAP", "CIAP-2", "CID-10"):
               raise ValueError("Método SUS/APS inválido. Use SOAP, CIAP-2 ou CID-10.")
           return v

   # --- SQLAlchemy Model ---
   class Base(DeclarativeBase):
       pass

   class TelemedicinaAuditoriaLog(Base):
       __tablename__ = "telemedicina_auditoria_log"

       id: Mapped[UUID] = mapped_column(primary_key=True, default=lambda: __import__("uuid").uuid4())
       consulta_id: Mapped[UUID] = mapped_column(ForeignKey("teleconsultas.id", ondelete="CASCADE"))
       paciente_cns: Mapped[str] = mapped_column(String(15))
       paciente_cpf: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
       evento_tipo: Mapped[EventoAuditoriaTipo] = mapped_column(SAEnum(EventoAuditoriaTipo, name="evento_auditoria_tipo"))
       detalhes: Mapped[Optional[dict]] = mapped_column(Text, nullable=True)
       carimbo_tempo: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       ip_origem: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
       agente_id: Mapped[str] = mapped_column(String(36))
       metodo_sus: Mapped[str] = mapped_column(String(10), default="SOAP")
       classificacao_ciap2: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
       classificacao_cid10: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

   # --- Repository ---
   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: Session):
           self.session = session

       def _criar_log(self, evento: AuditoriaEventoCreate) -> TelemedicinaAuditoriaLog:
           log = TelemedicinaAuditoriaLog(
               consulta_id=evento.consulta_id,
               paciente_cns=evento.paciente_cns,
               paciente_cpf=evento.paciente_cpf,
               evento_tipo=evento.evento_tipo,
               detalhes=evento.detalhes,
               carimbo_tempo=datetime.now(timezone.utc),
               ip_origem=evento.ip_origem,
               agente_id=evento.agente_id,
               metodo_sus=evento.metodo_sus,
               classificacao_ciap2=evento.classificacao_ciap2,
               classificacao_cid10=evento.classificacao_cid10,
           )
           self.session.add(log)
           self.session.flush()
           return log

       def registrar_conexao(self, evento: AuditoriaEventoCreate) -> TelemedicinaAuditoriaLog:
           evento.evento_tipo = EventoAuditoriaTipo.CONEXAO
           return self._criar_log(evento)

       def registrar_desconexao(self, evento: AuditoriaEventoCreate) -> TelemedicinaAuditoriaLog:
           evento.evento_tipo = EventoAuditoriaTipo.DESCONEXAO
           return self._criar_log(evento)

       def registrar_aceite_termos(self, evento: AuditoriaEventoCreate) -> TelemedicinaAuditoriaLog:
           evento.evento_tipo = EventoAuditoriaTipo.ACEITE_TERMOS
           return self._criar_log(evento)

       def commit(self) -> None:
           self.session.commit()

       def rollback(self) -> None:
           self.session.rollback()
   ```

5.  **Refinement & Compliance Check:**
   - *Python 3.12 & Strict Typing:* Used `from __future__ import annotations`, explicit type hints, `Mapped`, `mapped_column`.
   - *Pydantic v2:* Used `BaseModel`, `Field`, `field_validator`, `pattern`.
   - *SQLAlchemy 2.0:* Used `DeclarativeBase`, `Mapped`, `mapped_column`, `ForeignKey`, `SAEnum`.
   - *Secure Timestamp:* `datetime.now(timezone.utc)` explicitly set. Added `timezone=True` to `DateTime`.
   - *SUS/APS Standards:* Added `metodo_sus`, `classificacao_ciap2`, `classificacao_cid10` fields. Validated in Pydantic.
   - *LGPD/CFM:* `ACEITE_TERMOS` event type, CNS/CPF validation.
   - *Repository Pattern:* `AuditoriaTelemedicinaRepository` with methods for each event type.
   - *Testability:* The repository is dependency-injected with `Session`, making it easy to mock in pytest. I should also provide a pytest test file to satisfy "cobertura de testes automatizados com pytest". The prompt says "Manter conformidade total e cobertura de testes automatizados com pytest." I'll add a test file.
   - *File Path:* `backend/app/repositories/auditoria_telemedicina.py`
   - *Structure:* I'll organize it cleanly. I'll also add async support note if needed, but keep it sync for simplicity unless specified. Actually, modern stacks prefer async, but I'll stick to sync `Session` as it's standard for SQLAlchemy 2.0 examples. I'll make it clear.

   Let's adjust the Pydantic model to be more aligned with v2 best practices and ensure all types are correct. I'll also add a `__init__.py` reference if needed, but not required.
   I'll add a comprehensive pytest test file to ensure compliance.

   Key improvements during drafting:
   - Use `uuid4` properly without `__import__`.
   - Ensure `datetime` imports are correct.
   - Add proper docstrings and type hints.
   - Make sure the repository methods return the created model.
   - Add a test file `tests/test_auditoria_telemedicina.py`.

   Let's write out the full code carefully.

   **Repository Code Structure:**
   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   from __future__ import annotations
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Any, Optional
   from uuid import UUID, uuid4

   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import String, Text, DateTime, Enum as SAEnum, ForeignKey
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, Session

   # ... (models and repo)
   ```

   **Test Code Structure:**
   ```python
   # Arquivo: tests/test_auditoria_telemedicina.py
   import pytest
   from unittest.mock import MagicMock, patch
   from datetime import datetime, timezone
   from uuid import uuid4
   from backend.app.repositories.auditoria_telemedicina import (
       AuditoriaTelemedicinaRepository,
       AuditoriaEventoCreate,
       EventoAuditoriaTipo,
       TelemedicinaAuditoriaLog,
   )

   # ... (tests)
   ```

   I need to ensure the test uses `pytest` correctly, mocks the session, and validates Pydantic, SQLAlchemy, and business logic.

   Let's draft the test carefully:
   - Test Pydantic validation (CNS pattern, CPF pattern, method validation)
   - Test repository methods (connection, disconnection, acceptance)
   - Test secure timestamp (UTC)
   - Test session interaction (add, flush, commit/rollback)

   I'll write it out now. I'll make sure all imports are correct and the code is production-ready.

   One detail: `SAEnum` in SQLAlchemy 2.0 is `sqlalchemy.Enum`. I'll use `sqlalchemy.Enum`.
   Also, `mapped_column` is correct for SA 2.0.
   I'll add `__init__.py` if needed, but not required.
   I'll ensure the code is strictly typed and follows PEP 484/586.

   Let's construct the final response.
   I will provide:
   1. `backend/app/repositories/auditoria_telemedicina.py`
   2. `tests/test_auditoria_telemedicina.py`
   Both with clear paths and comments.
   I'll double-check SQLAlchemy 2.0 syntax: `Mapped`, `mapped_column`, `DeclarativeBase`, `sessionmaker` (not used here, repo takes session), `Enum` from `sqlalchemy`.
   Pydantic v2: `BaseModel`, `Field`, `field_validator`, `pattern`.
   Python 3.12: `from __future__ import annotations`, type hints.
   SUS/APS: CIAP-2, CID-10, SOAP, CNS/CPF.
   LGPD/CFM: ACEITE_TERMOS, secure timestamp.
   All constraints met.

   One minor adjustment: `sqlalchemy.Enum` is preferred over `SAEnum`. I'll import it directly.
   I'll also add a `__init__.py` reference if needed, but not necessary.
   I'll make sure the test file is complete and runnable.

   Let's write it out carefully. 
   Structure:
   - Repository file
   - Test file
   - Brief explanation of design choices (optional but helpful)
   - Ensure strict compliance.
   All good. Proceeding. 
   Self-Correction/Verification during thought:
   - `sqlalchemy.Enum` vs `sqlalchemy.dialects.postgresql.ENUM`? I'll use standard `sqlalchemy.Enum` for DB agnosticism, but note it.
   - `datetime.now(timezone.utc)` is correct for secure timestamp.
   - Pydantic v2 `field_validator` is correct.
   - `Mapped` and `mapped_column` are SA 2.0.
   - The repository should handle session lifecycle? Usually, the service layer handles commit/rollback, but I'll keep `commit()` and `rollback()` in the repo for simplicity as requested, or remove them and let the caller handle it. I'll keep them but mark them as optional or standard. Actually, it's better to let the caller handle commit/rollback, but I'll leave them for convenience. I'll add a note.
   - I'll ensure the test uses `pytest` fixtures properly.
   - I'll add `# Arquivo: ...` as requested.

   Final check of the prompt: "registro de eventos de conexão, desconexão, aceite de termos de sigilo do paciente (LGPD / Resolução CFM) e carimbo de data/hora seguro com SQLAlchemy 2.0."
   All covered.

   I will generate the response now. 
   Output matches the refined code.✅
   Structure:
   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   ...
   ```
   ```python
   # Arquivo: tests/test_auditoria_telemedicina.py
   ...
   ```
   Ready. 
   Output Generation. 
   *(Self-Correction/Refinement during drafting)*: 
   I should make sure the SQLAlchemy model uses `sqlalchemy.Enum` correctly. In SA 2.0, it's `sqlalchemy.Enum`. I'll import it as `Enum as SAE`.
   I'll also add `__init__.py` if needed, but not required.
   I'll ensure the Pydantic model uses `model_validator` or `field_validator` correctly. `field_validator` is fine.
   I'll add type hints for all methods.
   I'll make sure the test covers all requirements.
   All good.
   Proceeds. 
   Output Generation. 
   [Done] 
   *Output Generation* (matches the final response)
   - Repository file with strict typing, Pydantic v2, SA 2.0, SUS/APS fields, LGPD/CFM events, secure UTC timestamp.
   - Test file with pytest, mocking, validation checks, and coverage of all methods.
   - Clear file path comments.
   - Ready. 
   *(Self-Correction/Note during thought)*: I should ensure the `carimbo_tempo` is explicitly set to UTC in the model and repository to avoid naive datetime issues. I'll use `datetime.now(timezone.utc)` in both model default and repo creation for safety. Actually, model default is enough, but I'll set it explicitly in the repo for audit clarity.
   I'll also add `__init__.py` reference if needed, but not required.
   All constraints met. Output matches response. 
  