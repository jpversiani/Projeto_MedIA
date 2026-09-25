Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Implement `backend/app/repositories/auditoria_telemedicina.py` with a class `AuditoriaTelemedicinaRepository` for logging teleconsultation events (connection, disconnection, patient confidentiality agreement acceptance, secure timestamping) using SQLAlchemy 2.0.
   - **Constraints:** Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), full compliance and automated test coverage with pytest.
   - **Output Requirement:** Provide complete, executable code. Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/auditoria_telemedicina.py`
   - **Class:** `AuditoriaTelemedicinaRepository`
   - **Features:**
     - Log connection events
     - Log disconnection events
     - Log patient confidentiality agreement acceptance (LGPD/CFM)
     - Secure timestamping
     - Use SQLAlchemy 2.0
   - **Standards:** SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF)
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0, pytest
   - **Testing:** Provide pytest tests covering the repository.

3.  **Design Database Model (SQLAlchemy 2.0):**
   Need a table for audit logs. Let's call it `auditoria_telemedicina`.
   Columns:
   - `id`: UUID/Integer primary key
   - `tipo_evento`: Enum (CONEXAO, DESCONECAO, ACEITE_TERMO_SIGILO)
   - `paciente_cns`: String (optional, CNS is 15 digits)
   - `paciente_cpf`: String (optional, CPF is 11 digits)
   - `medico_cpf`: String (optional)
   - `data_hora`: DateTime (with timezone, secure timestamp)
   - `ip_origem`: String
   - `user_agent`: String
   - `metodo_soap`: String (optional, SOAP method)
   - `codigo_ciap2`: String (optional, CIAP-2 code)
   - `codigo_cid10`: String (optional, CID-10 code)
   - `descricao`: String (optional, extra details)
   - `created_at`: DateTime (auto)
   - `updated_at`: DateTime (auto)

   Let's define an Enum for event types.
   Use SQLAlchemy 2.0 declarative style.
   Use `UUID` or `String` for IDs. I'll use `String` with `UUID` format or just `Integer` for simplicity, but `UUID` is better for audit logs. I'll stick to `String` primary key with `UUID` generation, or `Integer` auto-increment. Let's use `Integer` for simplicity, but I'll add a `uuid` column if needed. Actually, SQLAlchemy 2.0 recommends `Mapped` syntax.

   ```python
   from sqlalchemy import Column, Integer, String, DateTime, Enum, Text
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
   from sqlalchemy.sql import func
   import enum
   import uuid
   from datetime import datetime, timezone
   ```

   Model:
   ```python
   class AuditoriaTelemedicinaBase(DeclarativeBase):
       pass

   class EventoTelemedicinaTipo(enum.Enum):
       CONEXAO = "CONEXAO"
       DESCONECAO = "DESCONECAO"
       ACEITE_TERMO_SIGILO = "ACEITE_TERMO_SIGILO"

   class AuditoriaTelemedicina(AuditoriaTelemedicinaBase):
       __tablename__ = "auditoria_telemedicina"

       id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
       tipo_evento: Mapped[EventoTelemedicinaTipo] = mapped_column(Enum(EventoTelemedicinaTipo))
       paciente_cns: Mapped[str | None] = mapped_column(String(15), nullable=True)
       paciente_cpf: Mapped[str | None] = mapped_column(String(11), nullable=True)
       medico_cpf: Mapped[str | None] = mapped_column(String(11), nullable=True)
       data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       ip_origem: Mapped[str] = mapped_column(String(45))
       user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
       metodo_soap: Mapped[str | None] = mapped_column(String(50), nullable=True)
       codigo_ciap2: Mapped[str | None] = mapped_column(String(4), nullable=True)
       codigo_cid10: Mapped[str | None] = mapped_column(String(4), nullable=True)
       descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
   ```

4.  **Design Pydantic Schemas (v2):**
   Need schemas for input validation and output.
   ```python
   from pydantic import BaseModel, Field, ConfigDict
   from datetime import datetime
   from typing import Optional
   from enum import Enum as PydanticEnum

   class EventoTelemedicinaTipoPydantic(PydanticEnum):
       CONEXAO = "CONEXAO"
       DESCONECAO = "DESCONECAO"
       ACEITE_TERMO_SIGILO = "ACEITE_TERMO_SIGILO"

   class AuditoriaTelemedicinaCreate(BaseModel):
       tipo_evento: EventoTelemedicinaTipoPydantic
       paciente_cns: Optional[str] = None
       paciente_cpf: Optional[str] = None
       medico_cpf: Optional[str] = None
       ip_origem: str
       user_agent: Optional[str] = None
       metodo_soap: Optional[str] = None
       codigo_ciap2: Optional[str] = None
       codigo_cid10: Optional[str] = None
       descricao: Optional[str] = None

   class AuditoriaTelemedicinaResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: int
       tipo_evento: EventoTelemedicinaTipoPydantic
       paciente_cns: Optional[str] = None
       paciente_cpf: Optional[str] = None
       medico_cpf: Optional[str] = None
       data_hora: datetime
       ip_origem: str
       user_agent: Optional[str] = None
       metodo_soap: Optional[str] = None
       codigo_ciap2: Optional[str] = None
       codigo_cid10: Optional[str] = None
       descricao: Optional[str] = None
       created_at: datetime
       updated_at: datetime
   ```

5.  **Design Repository Class:**
   Needs to interact with SQLAlchemy session.
   Methods:
   - `__init__(self, session: AsyncSession)`
   - `registrar_conexao(self, ...)`
   - `registrar_desconexao(self, ...)`
   - `registrar_aceite_termo(self, ...)`
   - `registrar_evento(self, ...)` (core method)
   - `buscar_por_paciente(self, paciente_cns: str)`
   - `buscar_por_medico(self, medico_cpf: str)`
   - `buscar_por_data_range(self, start: datetime, end: datetime)`

   Use `async` for modern SQLAlchemy 2.0.
   Secure timestamp: Use `datetime.now(timezone.utc)` or let DB handle it. I'll use Python's `datetime.now(timezone.utc)` for consistency and security, but also keep DB default.

   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, delete
   from datetime import datetime
   from typing import List
   import uuid

   class AuditoriaTelemedicinaRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def registrar_evento(self, evento: AuditoriaTelemedicinaCreate) -> AuditoriaTelemedicina:
           # Map pydantic to sqlalchemy model
           db_evento = AuditoriaTelemedicina(
               tipo_evento=evento.tipo_evento,
               paciente_cns=evento.paciente_cns,
               paciente_cpf=evento.paciente_cpf,
               medico_cpf=evento.medico_cpf,
               data_hora=datetime.now(timezone.utc),
               ip_origem=evento.ip_origem,
               user_agent=evento.user_agent,
               metodo_soap=evento.metodo_soap,
               codigo_ciap2=evento.codigo_ciap2,
               codigo_cid10=evento.codigo_cid10,
               descricao=evento.descricao,
           )
           self.session.add(db_evento)
           await self.session.flush()
           await self.session.refresh(db_evento)
           return db_evento

       async def registrar_conexao(self, paciente_cns: str, paciente_cpf: str, medico_cpf: str, ip_origem: str, user_agent: str | None = None) -> AuditoriaTelemedicina:
           evento = AuditoriaTelemedicinaCreate(
               tipo_evento=EventoTelemedicinaTipoPydantic.CONEXAO,
               paciente_cns=paciente_cns,
               paciente_cpf=paciente_cpf,
               medico_cpf=medico_cpf,
               ip_origem=ip_origem,
               user_agent=user_agent,
           )
           return await self.registrar_evento(evento)

       async def registrar_desconexao(self, paciente_cns: str, paciente_cpf: str, medico_cpf: str, ip_origem: str, user_agent: str | None = None) -> AuditoriaTelemedicina:
           evento = AuditoriaTelemedicinaCreate(
               tipo_evento=EventoTelemedicinaTipoPydantic.DESCONEXAO,
               paciente_cns=paciente_cns,
               paciente_cpf=paciente_cpf,
               medico_cpf=medico_cpf,
               ip_origem=ip_origem,
               user_agent=user_agent,
           )
           return await self.registrar_evento(evento)

       async def registrar_aceite_termo(self, paciente_cns: str, paciente_cpf: str, medico_cpf: str, ip_origem: str, user_agent: str | None = None) -> AuditoriaTelemedicina:
           evento = AuditoriaTelemedicinaCreate(
               tipo_evento=EventoTelemedicinaTipoPydantic.ACEITE_TERMO_SIGILO,
               paciente_cns=paciente_cns,
               paciente_cpf=paciente_cpf,
               medico_cpf=medico_cpf,
               ip_origem=ip_origem,
               user_agent=user_agent,
           )
           return await self.registrar_evento(evento)

       async def buscar_por_paciente(self, paciente_cns: str) -> List[AuditoriaTelemedicina]:
           stmt = select(AuditoriaTelemedicina).where(AuditoriaTelemedicina.paciente_cns == paciente_cns).order_by(AuditoriaTelemedicina.data_hora.desc())
           result = await self.session.execute(stmt)
           return list(result.scalars().all())

       async def buscar_por_medico(self, medico_cpf: str) -> List[AuditoriaTelemedicina]:
           stmt = select(AuditoriaTelemedicina).where(AuditoriaTelemedicina.medico_cpf == medico_cpf).order_by(AuditoriaTelemedicina.data_hora.desc())
           result = await self.session.execute(stmt)
           return list(result.scalars().all())

       async def buscar_por_data_range(self, start: datetime, end: datetime) -> List[AuditoriaTelemedicina]:
           stmt = select(AuditoriaTelemedicina).where(
               AuditoriaTelemedicina.data_hora >= start,
               AuditoriaTelemedicina.data_hora <= end
           ).order_by(AuditoriaTelemedicina.data_hora.desc())
           result = await self.session.execute(stmt)
           return list(result.scalars().all())
   ```

6.  **Refine & Check Constraints:**
   - Python 3.12: Use `from __future__ import annotations` or standard type hints. I'll use standard `str | None` syntax (Python 3.10+).
   - Pydantic v2: Used `ConfigDict`, `from_attributes=True`.
   - SQLAlchemy 2.0: Used `Mapped`, `mapped_column`, `AsyncSession`, `select`, `execute`.
   - SUS/APS standards: Included CIAP-2, CID-10, SOAP, CNS/CPF fields.
   - Secure timestamp: Used `datetime.now(timezone.utc)` explicitly.
   - Need to ensure the code is complete and executable. I'll add necessary imports and structure it properly.
   - I should also provide the pytest file as requested ("cobertura de testes automatizados com pytest").

   Let's structure the repository file carefully.
   I'll add type hints properly.
   I'll make sure the Pydantic enum matches the SQLAlchemy enum.
   I'll add a `__init__.py` or just focus on the requested file.
   I'll create `tests/test_auditoria_telemedicina.py` for pytest coverage.

   Check SQLAlchemy 2.0 Enum handling: `Enum(EventoTelemedicinaTipo)` works, but sometimes it's better to use `sa.Enum` or `String`. I'll stick to `Enum` but ensure it's imported correctly. Actually, SQLAlchemy 2.0 recommends `sqlalchemy.Enum` or just `String` for enums to avoid dialect issues. I'll use `String` with a check constraint or just `Enum` from `sqlalchemy.dialects.postgresql` if needed, but standard `Enum` is fine. I'll use `sqlalchemy.Enum` explicitly.

   Let's refine the model:
   ```python
   from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, CheckConstraint
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
   from sqlalchemy.sql import func
   import enum
   from datetime import datetime, timezone
   from typing import Optional
   ```
   Actually, `Mapped` syntax is preferred in 2.0.
   I'll define the enum as a Python `enum.Enum` and pass it to `sqlalchemy.Enum`.

   One detail: `data_hora` should be secure. I'll explicitly set it in the repo, not rely on `server_default`.

   Let's draft the complete `backend/app/repositories/auditoria_telemedicina.py`:

   ```python
   # Arquivo: backend/app/repositories/auditoria_telemedicina.py
   from __future__ import annotations

   from datetime import datetime, timezone
   from enum import Enum as PydanticEnum
   from typing import List, Optional

   from pydantic import BaseModel, ConfigDict, Field
   from sqlalchemy import Enum as SqlAlchemyEnum, String, Text, DateTime
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
   from sqlalchemy.sql import func, select

   # --- SQLAlchemy Base ---
   class Base(DeclarativeBase):
       pass

   # --- Enums ---
   class EventoTelemedicinaTipoEnum(PydanticEnum):
       CONEXAO = "CONEXAO"
       DESCONECAO = "DESCONECAO"
       ACEITE_TERMO_SIGILO = "ACEITE_TERMO_SIGILO"

   # --- SQLAlchemy Model ---
   class AuditoriaTelemedicina(Base):
       __tablename__ = "auditoria_telemedicina"

       id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
       tipo_evento: Mapped[EventoTelemedicinaTipoEnum] = mapped_column(SqlAlchemyEnum(EventoTelemedicinaTipoEnum))
       paciente_cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       paciente_cpf: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
       medico_cpf: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
       data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True))
       ip_origem: Mapped[str] = mapped_column(String(45))
       user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
       metodo_soap: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
       codigo_ciap2: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
       codigo_cid10: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
       descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

   # --- Pydantic Schemas ---
   class AuditoriaTelemedicinaCreate(BaseModel):
       tipo_evento: EventoTelemedicinaTipoEnum
       paciente_cns: Optional[str] = None
       paciente_cpf: Optional[str] = None
       medico_cpf: Optional[str] = None
       ip_origem: str
       user_agent: Optional[str] = None
       metodo_soap: Optional[str] = None
       codigo_ciap2: Optional[str] = None
       codigo_cid10: Optional[str] = None
       descricao: Optional[str] = None

   class AuditoriaTelemedicinaResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: int
       tipo_evento: EventoTelemedicinaTipoEnum
       paciente_cns: Optional[str] = None
       paciente_cpf: Optional[str] = None
       medico_cpf: Optional[str] = None