"""SQLAlchemy models for telemedicina database schema."""  # noqa: N999

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class Patient(Base):
    """Patient model representing a telemedicina patient."""
    __tablename__ = "patients"

    id: int | None = Column(Integer, primary_key=True, index=True)
    cnf: str = Column(String(20), unique=True, index=True, nullable=False, description="Conselho Nacional de Saúde identifier")
    cip: str | None = Column(String(20), nullable=True, description="Cartão de Identidade do Paciente")
    name: str = Column(String(100), nullable=False)
    gender: str | None = Column(String(10), nullable=True)
    birth_date: datetime | None = Column(DateTime, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.now)

    # Relationships
    telemedicina_sessions: list = relationship("TelemedicinaSession", back_populates="patient")


class Room(Base):
    """Room model for telemedicina sessions."""
    __tablename__ = "rooms"

    id: int | None = Column(Integer, primary_key=True, index=True)
    code: str = Column(String(50), unique=True, index=True, nullable=False, description="Room code")
    name: str = Column(String(100), nullable=False)
    max_participants: int = Column(Integer, default=10)
    created_at: datetime = Column(DateTime, default=datetime.now)

    # Relationships
    sessions: list = relationship("TelemedicinaSession", back_populates="room")


class TelemedicinaSession(Base):
    """Telemedicina session model."""
    __tablename__ = "telemedicina_sessions"

    id: int | None = Column(Integer, primary_key=True, index=True)
    room_code: str = Column(String(50), unique=True, index=True, nullable=False, description="Room code")
    patient_id: int | None = Column(Integer, ForeignKey("patients.id"), nullable=True)
    provider_id: int | None = Column(Integer, ForeignKey("patients.id"), nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.now)
    ended_at: datetime | None = Column(DateTime, nullable=True)

    # Relationships
    room: Room = relationship("Room", back_populates="sessions")
    patient: Patient = relationship("Patient", back_populates="telemedicina_sessions")
    provider: Patient = relationship("Patient", back_populates="telemedicina_sessions")


class MedicalRecord(Base):
    """Medical record model for telemedicina patient records."""
    __tablename__ = "medical_records"

    id: int | None = Column(Integer, primary_key=True, index=True)
    patient_cnf: str = Column(String(20), unique=True, index=True, nullable=False, description="Patient CPF")
    clinical_data: str = Column(Text, nullable=False, description="Structured clinical data")
    recorded_at: datetime = Column(DateTime, default=datetime.now)

    # Relationships
    session: TelemedicinaSession | None = relationship("TelemedicinaSession", back_populates="medical_record")
