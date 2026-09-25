# Painel Visual da Triagem e Monitor de Fila APS (C35)

## Arquivo 1: Modelos de Dados (SQLAlchemy 2.0 + Pydantic v2)

```python
# backend/app/models/triage.py
"""
Modelos de dados para o sistema de triagem de C35.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from backend.app.models.base import Base


class TriagePriority(enum.Enum):
    """Prioridade de triagem conforme protocolo SUS/APS."""
    URGENT = "Urgente"          # 1 - Immediato
    HIGH = "Alta"              # 2 - Alta prioridade
    NORMAL = "Normal"          # 3 - Normal
    LOW = "Baixa"              # 4 - Baixa prioridade
    OBSERVATION = "Observação"  # 5 - Observação


class TriageStatus(enum.Enum):
    """Status do paciente na fila de triagem."""
    WAITING = "Em Fila"
    CALLING = "Chamando"
    ATTENDING = "Atendendo"
    COMPLETED = "Completado"
    DISCHARGED = "Desligado"
    DISCHARGED_NO_SHOW = "Desligado - Ausente"


class TriageMethod(enum.Enum):
    """Método de triagem: SOAP ou CIAP-2."""
    SOAP = "SOAP"
    CIAP_2 = "CIAP-2"


class Patient(Base):
    """
    Modelo do paciente com identificação por CNS/CPF.
    Conformidade SUS: identificação única por CNS ou CPF.
    """

    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cns: Mapped[Optional[str]] = mapped_column(
        String(11), unique=True, nullable=True, comment="Código Nacional de Saúde"
    )
    cpf: Mapped[Optional[str]] = mapped_column(
        String(11), unique=True, nullable=True, comment="Cadastro Nacional de Pessoas Físicas"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str] = mapped_column(String(1), nullable=False, comment="M/F")
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, cns={self.cns}, cpf={self.cpf}, name={self.name})>"


class Appointment(Base):
    """
    Agendamento de consulta com triagem.
    Padrão SOAP: Sinal, Observação, Avaliação, Plano.
    """

    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    appointment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    appointment_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    triage_priority: Mapped[TriagePriority] = mapped_column(
        Enum(TriagePriority), nullable=False, default=TriagePriority.NORMAL
    )
    triage_status: Mapped[TriageStatus] = mapped_column(
        Enum(TriageStatus), nullable=False, default=TriageStatus.WAITING
    )
    triage_method: Mapped[TriageMethod] = mapped_column(
        Enum(TriageMethod), nullable=False, default=TriageMethod.SOAP
    )
    soap_signal: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Sinal da SOAP"
    )
    soap_observations: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Observações da SOAP"
    )
    soap_assessment: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Avaliação da SOAP"
    )
    soap_plan: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Plano da SOAP"
    )
    ciap2_diagnosis: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="CID-10 da CIAP-2"
    )
    ciap2_severity: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Gravidade da CIAP-2"
    )
    triage_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    triage_performed_by: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="CNPJ do triageador"
    )
    wait_time_minutes: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Tempo de espera em minutos"
    )
    is_called: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Chamado para atender"
    )
    call_number: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Número da chamada"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return (
            f"<Appointment(id={self.id}, patient={self.patient_id}, "
            f"priority={self.triage_priority.value}, status={self.triage_status.value})>"
        )


class Nurse(Base):
    """
    Modelo da equipe de enfermagem.
    Identificação por CNPJ.
    """

    __tablename__ = "nurses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cnpj: Mapped[str] = mapped_column(
        String(14), unique=True, nullable=False, comment="CNPJ da equipe"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Enfermeira"
    )
    shift_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    shift_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<Nurse(id={self.id}, cnpj={self.cnpj}, name={self.name})>"


class TriageLog(Base):
    """
    Registro de cada ato de triagem.
    Audit trail conforme SUS.
    """

    __tablename__ = "triage_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    performed_by: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="CNPJ do triageador"
    )
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<TriageLog(id={self.id}, appointment={self.appointment_id})>"


class CallRecord(Base):
    """
    Registro de chamadas sonoras para pacientes na fila.
    """

    __tablename__ = "call_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    called_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    call_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="sent"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<CallRecord(id={self.id}, appointment={self.appointment_id})>"


class CallQueue(Base):
    """
    Fila de chamadas sonoras para pacientes.
    Ordenada por prioridade e tempo de espera.
    """

    __tablename__ = "call_queue"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    wait_time_minutes: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    is_called: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    called_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<CallQueue(id={self.id}, appointment={self.appointment_id})>"
```

## Arquivo 2: Pydantic Schemas

```python
# backend/app/schemas/triage.py
"""
Esquemas Pydantic v2 para serialização/deserialização.
Tipagem estrita conforme diretrizes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class PatientCreate(BaseModel):
    """Schema para criação de paciente."""

    cns: Optional[str] = Field(None, max_length=11, description="CNS do paciente")
    cpf: Optional[str] = Field(None, max_length=11, description="CPF do paciente")
    name: str = Field(..., min_length=1, max_length=100, description="Nome completo")
    gender: str = Field(..., pattern="^(M|F)$", description="M/F")
    age: int = Field(..., ge=0, le=150, description="Idade em anos")
    date_of_birth: Optional[datetime] = Field(None, description="Data de nascimento")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Telefone")


class PatientRead(BaseModel):
    """Schema para leitura de paciente."""

    id: str
    cns: Optional[str]
    cpf: Optional[str]
    name: str
    gender: str
    age: int
    date_of_birth: Optional[datetime]
    contact_phone: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentCreate(BaseModel):
    """Schema para criação de agendamento com triagem."""

    patient_id: str
    appointment_date: datetime
    appointment_time: Optional[datetime] = None
    triage_priority: str = Field(
        default="Normal",
        pattern="^(Urgente|Alta|Normal|Baixa|Observação)$",
    )
    triage_status: str = Field(
        default="Em Fila",
        pattern="^(Em Fila|Chamando|Atendendo|Completado|Desligado|Desligado - Ausente)$",
    )
    triage_method: str = Field(
        default="SOAP",
        pattern="^(SOAP|CIAP-2)$",
    )
    soap_signal: Optional[str] = None
    soap_observations: Optional[str] = None
    soap_assessment: Optional[str] = None
    soap_plan: Optional[str] = None
    ciap2_diagnosis: Optional[str] = Field(None, max_length=10)
    ciap2_severity: Optional[str] = Field(None, max_length=20)
    triage_performed_by: Optional[str] = Field(None, max_length=50)


class AppointmentRead(BaseModel):
    """Schema para leitura de agendamento."""

    id: str
    patient_id: str
    appointment_date: datetime
    appointment_time: Optional[datetime]
    triage_priority: str
    triage_status: str
    triage_method: str
    soap_signal: Optional[str]
    soap_observations: Optional[str]
    soap_assessment: Optional[str]
    soap_plan: Optional[str]
    ciap2_diagnosis: Optional[str]
    ciap2_severity: Optional[str]
    triage_performed_by: Optional[str]
    wait_time_minutes: Optional[float]
    is_called: bool
    call_number: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TriageStatusUpdate(BaseModel):
    """Schema para atualização do status de triagem."""

    appointment_id: str
    new_status: str = Field(
        pattern="^(Em Fila|Chamando|Atendendo|Completado|Desligado|Desligado - Ausente)$"
    )
    notes: Optional[str] = None


class CallRequest(BaseModel):
    """Schema para solicitar chamada sonora para um paciente."""

    appointment_id: str
    call_number: int = Field(..., gt=0)


class CallResponse(BaseModel):
    """Schema para resposta