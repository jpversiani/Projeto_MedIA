"""SQLAlchemy models for telemedicina database schema."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Patient(Base):
    """Patient model representing a telemedicina patient."""
    __tablename__ = "patients"

    id: Optional[int] = Column(Integer, primary_key=True, index=True)
    cnf: str = Column(String(20), unique=True, index=True, nullable=False, description="Conselho Nacional de Saúde identifier")
    cip: Optional[str] = Column(String(20), nullable=True, description="Cartão de Identidade do Paciente")
    name: str = Column(String(100), nullable=False)
    gender: str = Column(String(10), nullable=True)
    birth_date: Optional[datetime] = Column(DateTime, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.now)

    # Relationships
    telemedicina_sessions: list = relationship("TelemedicinaSession", back_populates="patient")


class Room(Base):
    """Room model for telemedicina sessions."""
    __tablename__ = "rooms"

    id: Optional[int] = Column(Integer, primary_key=True, index=True)
    code: str = Column(String(50), unique=True, index=True, nullable=False, description="Room code")
    name: str = Column(String(100), nullable=False)
    max_participants: int = Column(Integer, default=10)
    created_at: datetime = Column(DateTime, default=datetime.now)

    # Relationships
    sessions: list = relationship("TelemedicinaSession", back_populates="room")


class TelemedicinaSession(Base):
    """Telemedicina session model."""
    __tablename__ = "telemedicina_sessions"

    id: Optional[int] = Column(Integer, primary_key=True, index=True)
    room_code: str = Column(String(50), unique=True, index=True, nullable=False, description="Room code")
    patient_id: Optional[int] = Column(Integer, ForeignKey("patients.id"), nullable=True)
    provider_id: Optional[int] = Column(Integer, ForeignKey("patients.id"), nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.now)
    ended_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Relationships
    room: Room = relationship("Room", back_populates="sessions")
    patient: Patient = relationship("Patient", back_populates="telemedicina_sessions")
    provider: Patient = relationship("Patient", back_populates="telemedicina_sessions")


class MedicalRecord(Base):
    """Medical record model for telemedicina patient records."""
    __tablename__ = "medical_records"

    id: Optional[int] = Column(Integer, primary_key=True, index=True)
    patient_cnf: str = Column(String(20), unique=True, index=True, nullable=False, description="Patient CPF")
    clinical_data: str = Column(Text, nullable=False, description="Structured clinical data")
    recorded_at: datetime = Column(DateTime, default=datetime.now)

    # Relationships
    session: Optional[TelemedicinaSession] = relationship("TelemedicinaSession", back_populates="medical_record")
