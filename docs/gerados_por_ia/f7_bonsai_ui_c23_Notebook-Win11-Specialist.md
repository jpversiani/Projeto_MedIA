# Dashboard Executivo Interativo - Projeto MedIA

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── telemedicina.py
│   └── static/
│       ├── dashboard_analytics.html
│       └── style.css
├── tests/
│   ├── __init__.py
│   └── test_dashboard.py
├── requirements.txt
└── pytest.ini
```

---

## Arquivo: `backend/app/database.py`

```python
# Arquivo: backend/app/database.py
"""
Configuração de banco de dados com SQLAlchemy 2.0.
Suporte para PostgreSQL e SQLite (modo desenvolvimento).
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from typing import Optional
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./media.db"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

ScopedSession = scoped_session(SessionLocal)
Base = declarative_base()


def get_db() -> Session:
    """Dependência FastAPI para session do banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Inicializa todas as tabelas no banco de dados."""
    Base.metadata.create_all(bind=engine)
```

---

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 com tipagem estrita.
Padrões SUS/APS: CIAP-2, CID-10, método SOAP, identificação por CNS/CPF.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text,
    ForeignKey, Enum, Index, UniqueConstraint,
    func, event
)
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class ProviderType(str, Enum):
    """Tipos de profissionais da SUS/APS."""
    DOCTOR = "D"
    NURSE = "N"
    TECHNICIAN = "T"
    PHARMACIST = "P"
    OTHER = "O"


class Provider(Base):
    """
    Modelo de Profissional (CNS/CPF).
    Identificação por CNS (SUS) ou CPF (APs).
    """
    __tablename__ = "providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    cns = Column(String(11), unique=True, nullable=False, index=True)
    cpf = Column(String(14), unique=True, nullable=True, index=True)
    full_name = Column(String(255), nullable=False)
    profession = Column(Enum(ProviderType), nullable=False)
    provider_type = Column(String(50), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    appointments = relationship("Appointment", back_populates="provider")
    consultations = relationship("Consultation", back_populates="provider")

    def __repr__(self) -> str:
        return f"<Provider(id={self.id}, cns={self.cns}, name={self.full_name})>"


class Consultation(Base):
    """
    Consulta médica com método SOAP.
    CID-10 para diagnóstico, CIAP-2 para classificação.
    """
    __tablename__ = "consultations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    patient_cpf = Column(String(14), nullable=False, index=True)
    patient_name = Column(String(255), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)
    provider = relationship("Provider", back_populates="consultations")

    # Método SOAP
    subject = Column(String(500), nullable=True)
    objective = Column(Text, nullable=True)
    assessment = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)

    # CID-10 e CIAP-2
    cid10_code = Column(String(10), nullable=True, index=True)
    ciap2_code = Column(String(10), nullable=True, index=True)
    diagnosis = Column(String(500), nullable=True)
    treatment = Column(Text, nullable=True)

    # Horário da consulta
    consultation_time = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=True)

    # Status
    status = Column(String(20), default="AGENDADA")
    is_completed = Column(Boolean, default=False)

    # Notas adicionais
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Consultation(id={self.id}, patient={self.patient_cpf}, time={self.consultation_time})>"


class Appointment(Base):
    """
    Agendamento de consulta.
    Suporte para consulta em tempo real e histórico.
    """
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    patient_cpf = Column(String(14), nullable=False, index=True)
    patient_name = Column(String(255), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)
    provider = relationship("Provider", back_populates="appointments")

    appointment_time = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default="AGENDADA")
    notes = Column(Text, nullable=True)

    consultation = relationship("Consultation", back_populates="appointment", uselist=False)

    created_at = Column(DateTime, default=func.now())

    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, patient={self.patient_cpf}, time={self.appointment_time})>"


class Patient(Base):
    """
    Modelo de paciente com identificação por CPF.
    """
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(1), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    consultations = relationship("Consultation", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, cpf={self.cpf}, name={self.full_name})>"


class HealthRecord(Base):
    """
    Registro de saúde com histórico de consultas.
    Suporte para análise de KPIs e heatmap.
    """
    __tablename__ = "health_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    patient_cpf = Column(String(14), unique=True, nullable=False, index=True)
    patient_name = Column(String(255), nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(1), nullable=True)
    region = Column(String(50), nullable=True)
    insurance_type = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    consultations = relationship("Consultation", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")

    def __repr__(self -> str):
        return f"<HealthRecord(id={self.id}, patient={self.patient_cpf})>"


class ServiceType(Base):
    """
    Tipo de serviço com CID-10 e CIAP-2.
    """
    __tablename__ = "service_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    cid10_code = Column(String(10), nullable=False, unique=True)
    ciap2_code = Column(String(10), nullable=False, unique=True)
    service_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)

    consultations = relationship("Consultation", back_populates="service")

    def __repr__(self) -> str:
        return f"<ServiceType(id={self.id}, cid10={self.cid10_code}, name={self.service_name})>"


class AppointmentRecord(Base):
    """
    Registro de agendamento para análise de heatmap.
    """
    __tablename__ = "appointment_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    patient_cpf = Column(String(14), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)
    appointment_time = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default="AGENDADA")
    consultation_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self) -> str:
        return f"<AppointmentRecord(id={self.id}, time={self.appointment_time})>"
```

---

## Arquivo: `backend/app/schemas.py`

```python
# Arquivo: backend/app/schemas.py
"""
Esquemas Pydantic v2 com tipagem estrita.
Validação de dados para API REST.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


# ==========================================
# Esquemas de Consultação (SOAP)
# ==========================================

class ConsultationCreate(BaseModel):
    """Esquema para criação de consulta."""
    patient_cpf: str = Field(..., min_length=11, max_length=14)
    patient_name: str = Field(..., min_length=1, max_length=255)
    provider_id: UUID
    subject: Optional[str] = Field(None, max_length=500)
    objective: Optional[str] = Field(None, max_length=2000)
    assessment: Optional[str] = Field(None, max_length=2000)
    plan: Optional[str] = Field(None, max_length=2000)
    cid10_code: Optional[str] = Field(None, max_length=10)
    ciap2_code: Optional[str] = Field(None, max_length=10)
    diagnosis: Optional[str] = Field(None, max_length=500)
    treatment: Optional[str] = Field(None, max_length=2000)
    consultation_time: datetime
    duration_minutes: Optional[int] = Field(None, ge=0, le=1440)
    status: str = Field("AGENDADA", max_length=20)
    notes: Optional[str] = Field(None, max_length=2000)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    @field_validator("patient_cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        """Validação básica de CPF."""
        if len(v) != 14:
            raise ValueError("CPF deve ter exatamente 14 dígitos")
        return v.upper()


class ConsultationUpdate(BaseModel):
    """Esquema para atualização de consulta."""
    subject: Optional[str] = Field(None, max_length=500)
    objective: Optional[str] = Field(None, max_length=2000)
    assessment: Optional[str] = Field(None, max_length=2000)
    plan: Optional[str] = Field(None, max_length=2000)
    cid10_code: Optional[str] = Field(None, max_length=10)
    ciap2_code: Optional[str] = Field(None, max_length=10)
    diagnosis: Optional[str] = Field(None, max_length=500)
    treatment: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=2000)


class ConsultationResponse(BaseModel):
    """Esquema de resposta de consulta."""
    id: UUID
    patient_cpf: str
    patient_name: str
    provider_id: UUID
    subject: Optional[str]
    objective: Optional[str]
    assessment: Optional[str]
    plan: Optional[str]
    cid10_code: Optional[str]
    ciap2_code: Optional[str]
    diagnosis: Optional[str]
    treatment: Optional[str]
    consultation_time: datetime
    duration_minutes: Optional[int]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Esquemas de Agendamento
# ==========================================

class AppointmentCreate(BaseModel):
    """Esquema para criação de agendamento."""
    patient_cpf: str = Field(..., min_length=11, max_length=14)
    patient_name: str = Field(..., min_length=1, max_length=255)
    provider_id: UUID
    appointment_time: datetime
    status: str = Field("AGENDADA", max_length=20)
    notes: Optional[str] = Field(None, max_length=2000)


class AppointmentResponse(BaseModel):
    """Esquema de resposta de ag