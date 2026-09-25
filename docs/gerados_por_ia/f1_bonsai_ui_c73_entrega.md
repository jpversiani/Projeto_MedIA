# Painel Visual de Chamada de Teleconsulta - MedIA

## Arquitetura Completa

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para Telemedicina - Padrão SUS/APS
- CIAP-2: Código de Identificação de Attribuição de Proficiência
- CID-10: Código Internacional de Diagnóstico
- Método SOAP: Estrutura de registro de consulta
- Identificação por CNS/CPF
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    check,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class ConsultationStatus(str, Enum):
    """Padrão SOAP - Status da consulta"""
    AGENDADA = "AGENDADA"
    IN PROGRESSO = "EM PROGRESSO"
    COMPLETA = "COMPLETA"
    CANCELADA = "CANCELADA"
    REVISADA = "REVISADA"


class ConsultationType(str, Enum):
    """Tipos de consulta conforme SUS"""
    CONSULTA_GENERAL = "CONSULTA_GENERAL"
    CONSULTA_EMERGENCIA = "CONSULTA_EMERGENCIA"
    CONSULTA_RAPIDA = "CONSULTA_RAPIDA"
    CONSULTA_ESPECIALISTA = "CONSULTA_ESPECIALISTA"


class PatientType(str, Enum):
    """Identificação do paciente"""
    PACIENTE = "PACIENTE"
    DOCTOR = "DOCTOR"
    ASSISTENTE = "ASSISTENTE"


class Teleconsultation(Base):
    """
    Registro de Teleconsulta - Padrão SOAP + SUS
    Identificação por CNS/CPF do paciente e do atendente
    """

    __tablename__ = "teleconsultations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_cnp: Mapped[str] = mapped_column(
        String(11), nullable=False, index=True,
        comment="CNPJ do paciente"
    )
    patient_cpf: Mapped[str] = mapped_column(
        String(11), nullable=False, index=True,
        comment="CPF do paciente"
    )
    patient_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Nome completo do paciente"
    )
    patient_type: Mapped[PatientType] = mapped_column(
        Enum(PatientType), nullable=False, default=PatientType.PACIENTE
    )
    patient_cnp: Mapped[str] = mapped_column(
        String(11), nullable=False,
        comment="CNPJ do atendente"
    )
    patient_cpf: Mapped[str] = mapped_column(
        String(11), nullable=False,
        comment="CPF do atendente"
    )
    patient_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Nome completo do atendente"
    )
    patient_type: Mapped[PatientType] = mapped_column(
        Enum(PatientType), nullable=False, default=PatientType.PACIENTE
    )
    consultation_type: Mapped[ConsultationType] = mapped_column(
        Enum(ConsultationType), nullable=False, default=ConsultationType.CONSULTA_GENERAL
    )
    status: Mapped[ConsultationStatus] = mapped_column(
        Enum(ConsultationStatus), nullable=False, default=ConsultationStatus.AGENDADA
    )
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Data agendada"
    )
    actual_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Data real da consulta"
    )
    actual_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Horário real da consulta"
    )
    duration_minutes: Mapped[Optional[Decimal]] = mapped_column(
        Decimal(5, 2), nullable=True,
        comment="Duração em minutos"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Notas da consulta"
    )
    diagnosis_cid10: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True,
        comment="CID-10 do diagnóstico"
    )
    diagnosis_description: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="Descrição do diagnóstico"
    )
    treatment_plan: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Plano de tratamento"
    )
    prescription: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Prescrição"
    )
    prescription_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Data da prescrição"
    )
    prescription_number: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="Número da prescrição"
    )
    video_session_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="ID da sessão de vídeo"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Hora de fechamento"
    )

    # Relações
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="consultation", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<Teleconsultation(id={self.id}, patient_cpf={self.patient_cpf}, "
            f"status={self.status})>"
        )


class ChatMessage(Base):
    """
    Mensagens do chat de teleconsulta
    """

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teleconsultations.id"), nullable=False
    )
    sender_type: Mapped[PatientType] = mapped_column(
        Enum(PatientType), nullable=False,
        comment="Tipo do emissor (PACIENTE/DOCTOR)"
    )
    sender_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Nome do emissor"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Conteúdo da mensagem"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    read: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="Se a mensagem foi lida"
    )

    # Relações
    consultation: Mapped["Teleconsultation"] = relationship(
        back_populates="chat_messages"
    )

    def __repr__(self) -> str:
        return (
            f"<ChatMessage(id={self.id}, sender={self.sender_type}, "
            f"timestamp={self.timestamp})>"
        )


class Patient(Base):
    """
    Modelo do paciente - Padrão SUS
    """

    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cnp: Mapped[str] = mapped_column(
        String(11), unique=True, nullable=False, index=True,
        comment="CNPJ do paciente"
    )
    cpf: Mapped[str] = mapped_column(
        String(11), unique=True, nullable=False, index=True,
        comment="CPF do paciente"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Nome completo"
    )
    date_of_birth: Mapped[Optional[date]] = mapped_column(
        date, nullable=True,
        comment="Data de nascimento"
    )
    gender: Mapped[Optional[str]] = mapped_column(
        String(1), nullable=True,
        comment="Gênero (M/F)"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        comment="Telefone"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="E-mail"
    )
    address: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="Endereço"
    )
    medical_history: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Histórico médico"
    )
    allergies: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="Alergias"
    )
    medications: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Medicamentos atuais"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relações
    consultations: Mapped[list["Teleconsultation"]] = relationship(
        back_populates="patient", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, cpf={self.cpf})>"


class Doctor(Base):
    """
    Modelo do doctor - Padrão SUS + CIAP-2
    """

    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cnp: Mapped[str] = mapped_column(
        String(11), unique=True, nullable=False, index=True,
        comment="CNPJ do doctor"
    )
    cpf: Mapped[str] = mapped_column(
        String(11), unique=True, nullable=False, index=True,
        comment="CPF do doctor"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Nome completo"
    )
    date_of_birth: Mapped[Optional[date]] = mapped_column(
        date, nullable=True,
        comment="Data de nascimento"
    )
    gender: Mapped[Optional[str]] = mapped_column(
        String(1), nullable=True,
        comment="Gênero (M/F)"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        comment="Telefone"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="E-mail"
    )
    ciap2_code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True,
        comment="Código CIAP-2"
    )
    specialty: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Especialidade"
    )
    license_number: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="Número de licença"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relações
    consultations: Mapped[list["Teleconsultation"]] = relationship(
        back_populates="doctor", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Doctor(id={self.id}, ciap2={self.ciap2_code})>"


class TeleconsultationService:
    """
    Serviço de Teleconsulta - Padrão SOAP + SUS
    """

    def __init__(self, session):
        self.session = session

    def create_teleconsultation(
        self,
        patient_cnp: str,
        patient_cpf: str,
        patient_name: str,
        doctor_cnp: str,
        doctor_cpf: str,
        doctor_name: str,
        consultation_type: ConsultationType = ConsultationType.CONSULTA_GENERAL,
        scheduled_date: Optional[datetime] = None,
    ) -> Teleconsultation:
        """
        Cria uma nova teleconsulta conforme padrão SOAP
        """
        consultation = Teleconsultation(
            patient_cnp=patient_cnp,
            patient_cpf=patient_cpf,
            patient_name=patient_name,
            doctor_cnp=doctor_cnp,
            doctor_cpf=doctor_cpf,
            doctor_name=doctor_name,
            consultation_type=consultation_type,
            scheduled_date=scheduled_date,
        )
        self.session.add(consultation)
        self.session.flush()
        return consultation

    def update_chat_message(
        self,
        consultation_id: uuid.UUID,
        sender_type: PatientType,
        sender_name: str,
        content: str,
    ) -> ChatMessage:
        """
        Adiciona uma mensagem de