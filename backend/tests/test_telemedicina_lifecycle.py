from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, ConfigDict

class StatusConsulta(str, Enum):
    AGENDADA = "AGENDADA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"

class TelemedicinaRoom(Base):
    __tablename__ = "telemedicina_rooms"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consultas: Mapped[List["Consulta"]] = relationship(back_populates="room")

class Consulta(Base):
    __tablename__ = "consultas"
    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("telemedicina_rooms.id"))
    status: Mapped[StatusConsulta] = mapped_column(SAEnum(StatusConsulta), default=StatusConsulta.AGENDADA)
    room: Mapped["TelemedicinaRoom"] = relationship(back_populates="consultas")
