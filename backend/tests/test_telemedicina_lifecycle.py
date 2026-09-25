from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List

import pytest
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, UniqueConstraint, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Mapped, mapped_column
from sqlalchemy.exc import IntegrityError

Base = declarative_base()

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

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_criar_sala_telemedicina(db_session):
    agora = datetime.now(timezone.utc)
    exp = agora + timedelta(hours=1)
    sala = TelemedicinaRoom(name="SALA-101", expires_at=exp)
    db_session.add(sala)
    db_session.commit()
    assert sala.id is not None
    assert sala.name == "SALA-101"

def test_rejeitar_sala_duplicada(db_session):
    agora = datetime.now(timezone.utc)
    exp = agora + timedelta(hours=1)
    sala1 = TelemedicinaRoom(name="SALA-DUPLICADA", expires_at=exp)
    sala2 = TelemedicinaRoom(name="SALA-DUPLICADA", expires_at=exp)
    db_session.add(sala1)
    db_session.commit()
    db_session.add(sala2)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_ciclo_status_consulta(db_session):
    agora = datetime.now(timezone.utc)
    sala = TelemedicinaRoom(name="SALA-CONSULTA", expires_at=agora + timedelta(hours=1))
    db_session.add(sala)
    db_session.commit()

    consulta = Consulta(room_id=sala.id, status=StatusConsulta.AGENDADA)
    db_session.add(consulta)
    db_session.commit()
    assert consulta.status == StatusConsulta.AGENDADA

    consulta.status = StatusConsulta.EM_ANDAMENTO
    db_session.commit()
    assert consulta.status == StatusConsulta.EM_ANDAMENTO

    consulta.status = StatusConsulta.CONCLUIDA
    db_session.commit()
    assert consulta.status == StatusConsulta.CONCLUIDA
