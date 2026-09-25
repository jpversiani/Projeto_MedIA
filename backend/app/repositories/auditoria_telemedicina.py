from sqlalchemy import String, Boolean, DateTime, JSON, Enum as SAEnum
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   from datetime import datetime, timezone
   import enum
   import uuid

   class EventoTipo(str, enum.Enum):
       CONEXAO = "conexao"
       DESCONEXAO = "desconexao"
       ACEITE_TERMO_SIGILO = "aceite_termo_sigilo"

   class Base(DeclarativeBase):
       pass

   class AuditoriaTelemedicina(Base):
       __tablename__ = "auditoria_telemedicina"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       tipo_evento: Mapped[EventoTipo] = mapped_column(SAEnum(EventoTipo), nullable=False)
       paciente_cns: Mapped[str | None] = mapped_column(String(15), nullable=True)
       paciente_cpf: Mapped[str | None] = mapped_column(String(14), nullable=True)
       medico_cpf: Mapped[str | None] = mapped_column(String(14), nullable=True)
       codigo_ciap2: Mapped[str | None] = mapped_column(String(10), nullable=True)
       codigo_cid10: Mapped[str | None] = mapped_column(String(10), nullable=True)
       metodo_soa: Mapped[str | None] = mapped_column(String(50), nullable=True)
       aceite_lgpd: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
       aceite_cfm: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
       detalhes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
       timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       ip_origem: Mapped[str | None] = mapped_column(String(45), nullable=True)
       user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
       status: Mapped[str | None] = mapped_column(String(20), nullable=True)

from pydantic import BaseModel, Field, ConfigDict
   from typing import Optional
   from datetime import datetime
   from enum import Enum

   class EventoTipoEnum(str, Enum):
       CONEXAO = "conexao"
       DESCONEXAO = "desconexao"
       ACEITE_TERMO_SIGILO = "aceite_termo_sigilo"

   class AuditoriaCreateSchema(BaseModel):
       tipo_evento: EventoTipoEnum
       paciente_cns: Optional[str] = None
       paciente_cpf: Optional[str] = None
       medico_cpf: Optional[str] = None
       codigo_ciap2: Optional[str] = None
       codigo_cid10: Optional[str] = None
       metodo_soa: Optional[str] = None
       aceite_lgpd: Optional[bool] = None
       aceite_cfm: Optional[bool] = None
       detalhes: Optional[dict] = None
       ip_origem: Optional[str] = None
       user_agent: Optional[str] = None
       status: Optional[str] = "SUCCESS"

       model_config = ConfigDict(from_attributes=True)

   class AuditoriaReadSchema(AuditoriaCreateSchema):
       id: uuid.UUID
       timestamp_utc: datetime

import uuid
   from datetime import datetime, timezone
   from typing import Optional, List
   from sqlalchemy import select, update
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy.orm import Mapped, mapped_column
   from app.models.base import Base # Assuming Base is defined elsewhere, but I'll define it locally or import it. I'll define it in the same file for completeness as requested.

import uuid
   from datetime import datetime, timezone
   from typing import Optional, List
   from enum import Enum
   from sqlalchemy import String, Boolean, DateTime, JSON, Enum as SAEnum, select
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   from pydantic import BaseModel, Field, ConfigDict

   # --- SQLAlchemy Model ---
   class Base(DeclarativeBase):
       pass

   class EventoTipo(str, Enum):
       CONEXAO = "conexao"
       DESCONEXAO = "desconexao"
       ACEITE_TERMO_SIGILO = "aceite_termo_sigilo"

   class AuditoriaTelemedicina(Base):
       __tablename__ = "auditoria_telemedicina"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       tipo_evento: Mapped[EventoTipo] = mapped_column(SAEnum(EventoTipo), nullable=False)
       paciente_cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       paciente_cpf: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
       medico_cpf: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
       codigo_ciap2: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
       codigo_cid10: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
       metodo_soa: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
       aceite_lgpd: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
       aceite_cfm: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
       detalhes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
       timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       ip_origem: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
       user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
       status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

class AuditoriaCreateSchema(BaseModel):
       tipo_evento: EventoTipo
       paciente_cns: Optional[str] = None
       paciente_cpf: Optional[str] = None
       medico_cpf: Optional[str] = None
       codigo_ciap2: Optional[str] = None
       codigo_cid10: Optional[str] = None
       metodo_soa: Optional[str] = None
       aceite_lgpd: Optional[bool] = None
       aceite_cfm: Optional[bool] = None
       detalhes: Optional[dict] = None
       ip_origem: Optional[str] = None
       user_agent: Optional[str] = None
       status: Optional[str] = "SUCCESS"

       model_config = ConfigDict(from_attributes=True)

   class AuditoriaReadSchema(AuditoriaCreateSchema):
       id: uuid.UUID
       timestamp_utc: datetime
