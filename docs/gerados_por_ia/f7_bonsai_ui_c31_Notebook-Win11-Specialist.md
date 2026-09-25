```python:backend/app/models.py
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para o sistema de Telemedicina.
Padrões SUS/APS: CIAP-2, CID-10, método SOAP, identificação por CNS/CPF.
"""
from __future__ import annotations

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    ForeignKey,
    Enum,
    UniqueConstraint,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    validates,
)
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    pass


class Patient(Base):
    """
    Modelo de Paciente com identificação por CNS/CPF.
    Padrão SUS: identificação única por CNS (Cadastro Nacional de Suscriptores).
    """
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cns: Mapped[str] = mapped_column(
        String(11), unique=True, nullable=False, index=True
    )
    cpf: Mapped[str] = mapped_column(
        String(11), unique=True, nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(
        Enum("M", "F", "O", name="gender"), nullable=False
    )
    insurance_type: Mapped[str] = mapped_column(
        Enum("SUS", "Privado", "MIS", name="insurance_type"), nullable=False
    )
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=datetime.utcnow, onupdate=datetime.utcnow
    )

    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )

    @validates("cns")
    def validate_cns(self, key: str, value: str) -> str:
        if len(value) != 11:
            raise ValueError("CNS deve ter exatamente 11 dígitos")
        if not value.isdigit():
            raise ValueError("CNS deve conter apenas dígitos")
        return value.upper()

    @validates("cpf")
    def validate_cpf(self, key: str, value: str) -> str:
        if len(value) != 11:
            raise ValueError("CPF deve ter exatamente 11 dígitos")
        if not value.isdigit():
            raise ValueError("CPF deve conter apenas dígitos")
        return value.upper()

    def __repr__(self) -> str:
        return f"<Patient(cns={self.cns}, cpf={self.cpf})>"


class Appointment(Base):
    """
    Modelo de Agendamento com método SOAP e CID-10.
    Padrão SOAP: Subjective, Objective, Assessment, Plan.
    """
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False
    )
    doctor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=True
    )
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    appointment_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "Agendada",
            "Em andamento",
            "Completada",
            "Cancelada",
            "Adiada",
            name="status",
        ),
        nullable=False,
        default="Agendada",
    )
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    diagnosis: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    icd10: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    ciap2: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    soap_subjective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    soap_objective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    soap_assessment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    soap_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=datetime.utcnow, onupdate=datetime.utcnow
    )

    patient: Mapped["Patient"] = relationship(back_populates="appointments")
    doctor: Mapped["Doctor"] = relationship(back_populates="appointments")

    @validates("appointment_time")
    def validate_appointment_time(self, key: str, value: datetime) -> datetime:
        if value < datetime.now():
            raise ValueError("Horário de agendamento não pode ser passado")
        return value

    @validates("duration_minutes")
    def validate_duration(self, key: str, value: int) -> int:
        if value < 1 or value > 180:
            raise ValueError("Duração deve estar entre 1 e 180 minutos")
        return value

    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, patient={self.patient_id}, status={self.status})>"


class Doctor(Base):
    """
    Modelo de Médico com identificação por CNS.
    """
    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cns: Mapped[str] = mapped_column(
        String(11), unique=True, nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    specialization: Mapped[str] = mapped_column(String(100), nullable=False)
    license_number: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=datetime.utcnow, onupdate=datetime.utcnow
    )

    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="doctor", cascade="all, delete-orphan"
    )

    @validates("cns")
    def validate_cns(self, key: str, value: str) -> str:
        if len(value) != 11:
            raise ValueError("CNS deve ter exatamente 11 dígitos")
        if not value.isdigit():
            raise ValueError("CNS deve conter apenas dígitos")
        return value.upper()

    def __repr__(self) -> str:
        return f"<Doctor(cns={self.cns}, specialization={self.specialization})>"


class ConsultationLog(Base):
    """
    Registro de consultas para análise de padrões e heatmap.
    """
    __tablename__ = "consultation_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False
    )
    hour: Mapped[int] = mapped_column(Integer, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "Agendada",
            "Em andamento",
            "Completada",
            "Cancelada",
            "Adiada",
            name="status",
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=datetime.utcnow
    )

    appointment: Mapped["Appointment"] = relationship(back_populates="consultation_logs")

    def __repr__(self) -> str:
        return f"<ConsultationLog(appointment={self.appointment_id}, hour={self.hour})>"


class Clinic(Base):
    """
    Modelo de Clínica com identificação SUS.
    """
    __tablename__ = "clinics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cns_clinic: Mapped[str] = mapped_column(
        String(11), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("SUS", "Privado", "MIS", name="type"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @validates("cns_clinic")
    def validate_cns_clinic(self, key: str, value: str) -> str:
        if len(value) != 11:
            raise ValueError("CNS da clínica deve ter exatamente 11 dígitos")
        if not value.isdigit():
            raise ValueError("CNS da clínica deve conter apenas dígitos")
        return value.upper()

    def __repr__(self) -> str:
        return f"<Clinic(cns={self.cns_clinic}, name={self.name})>"
```

```python:backend/app/schemas.py
# Arquivo: backend/app/schemas.py
"""
Esquemas Pydantic v2 para validação de dados.
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


class PatientBase(BaseModel):
    """Esquema base para Patient."""
    cns: str = Field(..., min_length=11, max_length=11)
    cpf: str = Field(..., min_length=11, max_length=11)
    full_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: str = Field(..., pattern="^(M|F|O)$")
    insurance_type: str = Field(..., pattern="^(SUS|Privado|MIS)$")
    phone: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PatientCreate(PlayerBase):
    """Esquema para criação de Patient."""
    pass


class PatientUpdate(BaseModel):
    """Esquema para atualização de Patient."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(M|F|O)$")
    insurance_type: Optional[str] = Field(None, pattern="^(SUS|Privado|MIS)$")
    phone: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PatientResponse(BaseModel):
    """Esquema de resposta para Patient."""
    id: UUID
    cns: str
    cpf: str
    full_name: str
    date_of_birth: date
    gender: str
    insurance_type: str
    phone: Optional[str]
    email: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentBase(BaseModel):
    """Esquema base para Appointment."""
    patient_id: UUID
    doctor_id: Optional[UUID] = None
    appointment_date: date
    appointment_time: datetime
    status: str = Field(..., pattern="^(Agendada|Em andamento|Completada|Cancelada|Adiada)$")
    reason: str = Field(..., min_length=1, max_length=200)
    diagnosis: Optional[str] = None
    icd10: Optional[str] = Field(None, pattern="^[0-9A-Z]{10}$")
    ciap2: Optional[str] = Field(None, pattern="^[0-9A-Z]{10}$")
    soap_subjective: Optional[str] = None
    soap_objective: Optional[str] = None
    soap_assessment: Optional[str] = None
    soap_plan: Optional[str] = None
    notes: Optional[str] = None
    duration_minutes: int = Field(..., ge=1, le=180)


class AppointmentCreate(AppointmentBase):
    """Esquema para criação de Appointment."""
    pass


class AppointmentUpdate(BaseModel):
    """Esquema para atualização de Appointment."""
    status: Optional[str] = Field(None, pattern="^(Agendada|Em andamento|Completada|Cancelada|Adiada)$")
    reason: Optional[str] = Field(None, min_length=1, max_length=200)
    diagnosis: Optional[str]