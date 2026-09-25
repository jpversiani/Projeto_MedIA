# Arquivo: backend/app/models.py
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    Integer,
    String,
    Float,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos do projeto MedIA."""


class IdentificaçãoType(str, Enum):
    """Tipos de identificação conforme SUS/APS."""
    CNS = "CNS"
    CPF = "CPF"
    CNPJ = "CNPJ"


class CID10Category(str, Enum):
    """Categorias do CID-10 (ICD-10)."""
    A = "A"  # Doenças e condições
    B = "B"  # Lesões e traumas
    C = "C"  # Doenças infectivas e parasitas
    D = "D"  # Doenças endocrinas
    E = "E"  # Doenças maternas e neonatais
    F = "F"  # Doenças cardiovasculares
    G = "G"  # Doenças respiratórias
    H = "H"  # Doenças digestivas
    I = "I"  # Doenças hematológicas
    J = "J"  # Doenças imunes
    K = "K"  # Doenças neoplásticas
    L = "L"  # Doenças do sistema nervoso
    M = "M"  # Doenças do sistema renal
    N = "N"  # Doenças do sistema pulmonar
    P = "P"  # Doenças do sistema renal
    Q = "Q"  # Doenças do sistema digestivo
    R = "R"  # Doenças do sistema respiratório
    S = "S"  # Doenças do sistema imunológico
    T = "T"  # Doenças do sistema muscular
    U = "U"  # Doenças do sistema digestivo
    V = "V"  # Doenças do sistema renal
    W = "W"  # Doenças do sistema imunológico
    X = "X"  # Doenças do sistema digestivo
    Y = "Y"  # Doenças do sistema imunológico
    Z = "Z"  # Doenças do sistema digestivo


class SOAPEvent(Base):
    """
    Evento SOAP (Significado, Observação, Anotação, Plano).
    Padrão de registro de eventos clínicos conforme SUS/APS.
    """
    __tablename__ = "soap_events"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.id"), nullable=False
    )
    identification_method: Mapped[IdentificaçãoType] = mapped_column(
        SAEnum(IdentificaçãoType), nullable=False
    )
    identification_value: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    soap_significance: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    soap_observations: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    soap_notes: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    soap_plan: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    appointment_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relações
    patient: Mapped["Patient"] = relationship(
        back_populates="soap_events"
    )

    # Índices para performance
    __table_args__ = (
        Index("ix_soap_patient_date", "patient_id", "appointment_date"),
        Index("ix_soap_identification", "identification_method", "identification_value"),
        Index("ix_soap_date", "appointment_date"),
    )


class Patient(Base):
    """
    Modelo de Patiento conforme padrões SUS/APS.
    Identificação por CNS/CPF/CNPJ.
    """
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    identification_method: Mapped[IdentificaçãoType] = mapped_column(
        SAEnum(IdentificaçãoType), nullable=False
    )
    identification_value: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    date_of_birth: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    insurance_provider: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Integer, nullable=False, server_default=1
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relações
    soap_events: Mapped[list["SOAPEvent"]] = relationship(
        back_populates="patient"
    )

    # Índices para performance
    __table_args__ = (
        UniqueConstraint(
            "identification_method", "identification_value", name="uq_patient_id"
        ),
        Index("ix_patient_identification", "identification_method", "identification_value"),
        Index("ix_patient_date_of_birth", "date_of_birth"),
    )


class Diagnosis(Base):
    """
    Diagnóstico conforme CID-10.
    """
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    cid10_code: Mapped[str] = mapped_column(
        String(10), nullable=False, unique=True
    )
    cid10_description: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    category: Mapped[CID10Category] = mapped_column(
        SAEnum(CID10Category), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Índices
    __table_args__ = (
        Index("ix_diagnosis_cid10", "cid10_code"),
        Index("ix_diagnosis_category", "category"),
    )


class Appointment(Base):
    """
    Agendamento de consulta conforme padrões SUS/APS.
    """
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.id"), nullable=False
    )
    appointment_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    appointment_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="scheduled"
    )
    doctor_name: Mapped[str] = mapped_column(String(100), nullable=False)
    diagnosis_cid10: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relações
    patient: Mapped["Patient"] = relationship(
        back_populates="appointments"
    )

    # Índices
    __table_args__ = (
        Index("ix_appointment_date", "appointment_date"),
        Index("ix_appointment_time", "appointment_time"),
        Index("ix_appointment_patient_date", "patient_id", "appointment_date"),
        Index("ix_appointment_status", "status"),
    )


class KPIData(Base):
    """
    Dados de KPI em tempo real para o dashboard executivo.
    """
    __tablename__ = "kpi_data"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    kpi_name: Mapped[str] = mapped_column(String(100), nullable=False)
    kpi_value: Mapped[float] = mapped_column(Float, nullable=False)
    kpi_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    appointment_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Índices
    __table_args__ = (
        Index("ix_kpi_date", "appointment_date"),
        Index("ix_kpi_name_date", "kpi_name", "appointment_date"),
    )
