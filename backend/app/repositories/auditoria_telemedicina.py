# Arquivo: backend/app/repositories/auditoria_telemedicina.py
   from __future__ import annotations
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, Sequence
   from pydantic import BaseModel, Field, ConfigDict
   from sqlalchemy import (
       Column, Integer, String, Text, DateTime, Enum as SAEnum,
       ForeignKey, Index, func, select, delete
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
   from sqlalchemy import event as sa_event

   # ... definitions ...

class Base(DeclarativeBase):
       pass

   class EventoTelemedicinaTipo(str, Enum):
       CONEXAO = "CONEXAO"
       DESCONEXAO = "DESCONEXAO"
       ACEITE_TERMOS = "ACEITE_TERMOS"
       REGISTRO_CLINICO = "REGISTRO_CLINICO"

   class AuditoriaTelemedicina(Base):
       __tablename__ = "auditoria_telemedicina"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

       event_type: Mapped[EventoTelemedicinaTipo] = mapped_column(SAEnum(EventoTelemedicinaTipo), nullable=False)
       patient_cpf: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
       patient_cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       doctor_cpf: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
       session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
       ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
       user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

       # LGPD / CFM
       agreement_version: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
       consent_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

       # SUS / APS
       cid10: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
       ciap2: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
       metodo_sop: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # SOAP

class AuditoriaTelemedicinaDTO(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: uuid.UUID
       created_at: datetime
       updated_at: Optional[datetime] = None
       event_type: EventoTelemedicinaTipo
       patient_cpf: Optional[str] = None
       patient_cns: Optional[str] = None
       doctor_cpf: Optional[str] = None
       session_id: Optional[str] = None
       ip_address: Optional[str] = None
       user_agent: Optional[str] = None
       agreement_version: Optional[str] = None
       consent_type: Optional[str] = None
       cid10: Optional[str] = None
       ciap2: Optional[str] = None
       metodo_sop: Optional[str] = None

class AuditoriaTelemedicinaRepository:
       def __init__(self, session: Session):
           self.session = session

       def _secure_timestamp(self) -> datetime:
           return datetime.now(timezone.utc)

       def registrar_evento(self, dto: AuditoriaTelemedicinaDTO) -> AuditoriaTelemedicina:
           # Map DTO to ORM
           orm_obj = AuditoriaTelemedicina(
               id=dto.id or uuid.uuid4(),
               created_at=dto.created_at or self._secure_timestamp(),
               updated_at=dto.updated_at or self._secure_timestamp(),
               event_type=dto.event_type,
               patient_cpf=dto.patient_cpf,
               patient_cns=dto.patient_cns,
               doctor_cpf=dto.doctor_cpf,
               session_id=dto.session_id,
               ip_address=dto.ip_address,
               user_agent=dto.user_agent,
               agreement_version=dto.agreement_version,
               consent_type=dto.consent_type,
               cid10=dto.cid10,
               ciap2=dto.ciap2,
               metodo_sop=dto.metodo_sop,
           )
           self.session.add(orm_obj)
           self.session.flush()
           self.session.refresh(orm_obj)
           return orm_obj

       # ... other methods ...
