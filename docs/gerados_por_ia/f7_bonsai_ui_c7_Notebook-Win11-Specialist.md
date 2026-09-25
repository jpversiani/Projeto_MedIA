# Dashboard Executivo Interativo - Projeto MedIA

## Estrutura do Projeto

```
media_dashboard/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── analytics.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── dashboard.py
│   │   └── static/
│   │       └── dashboard_analytics.html
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_models.py
│   │   ├── test_schemas.py
│   │   └── test_dashboard.py
│   └── requirements.txt
├── pytest.ini
└── README.md
```

---

## Arquivo: `backend/app/config.py`

```python
# Arquivo: backend/app/config.py
"""
Configuração do projeto MedIA Dashboard.
Padrões SUS/APS: CIAP-2, CID-10, método SOAP, identificação por CNS/CPF.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuração do ambiente do sistema."""

    # Aplicação
    APP_NAME: str = "MedIA Dashboard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Banco de Dados (SQLite para desenvolvimento)
    DATABASE_URL: str = "sqlite:///media_dashboard.db"
    DATABASE_SYNC: bool = True

    # Identificação SUS/APS
    CIAP_CODE: str = "0001"  # Código de CIAP (Centro de Integração de Atualizações)
    CID_CODE: str = "0001"    # Código de CID (Código de Identificação do Estado)
    STATE_CODE: str = "SP"    # Código do estado (ex: SP, RJ, MG, etc.)

    # Identificação de Pacientes
    IDENTIFICATION_TYPES: list[str] = ["CNS", "CPF"]

    # Limite de dados para dashboard
    DASHBOARD_DATE_RANGE_DAYS: int = 30
    DASHBOARD_HEATMAP_DAYS: int = 7

    # API
    API_PREFIX: str = "/api/v1"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

---

## Arquivo: `backend/app/database.py`

```python
# Arquivo: backend/app/database.py
"""
Configuração do banco de dados com SQLAlchemy 2.0.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker as sync_sessionmaker
from typing import AsyncGenerator, Generator

from .config import settings


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos do banco de dados."""


def get_sync_engine() -> create_engine:
    """Cria o motor de banco de dados síncrono."""
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )
    return engine


def get_sync_session_factory() -> sync_sessionmaker:
    """Fábrica de sessões síncronas."""
    engine = get_sync_engine()
    return sync_sessionmaker(bind=engine, expire_on_commit=False)


def get_sync_session() -> Generator[sessionmaker, None, None]:
    """Context manager para sessões síncronas."""
    session = get_sync_session_factory()()
    try:
        yield session
    finally:
        session.close()


async def get_async_engine():
    """Cria o motor de banco de dados assíncrono."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )
    return engine


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager para sessões assíncronas."""
    engine = await get_async_engine()
    async_session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Inicializa o banco de dados e cria todas as tabelas."""
    engine = get_sync_engine()
    Base.metadata.create_all(bind=engine)
    print(f"[DB] Banco de dados inicializado: {settings.DATABASE_URL}")
```

---

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos do banco de dados com SQLAlchemy 2.0.
Padrões SUS/APS: CIAP-2, CID-10, método SOAP, identificação por CNS/CPF.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    Enum,
    ForeignKey,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import Base


class IdentificationType(str):
    """Tipos de identificação de paciente conforme SUS/APS."""
    CNS = "CNS"
    CPF = "CPF"


class AppointmentStatus(str):
    """Status de agendamento conforme método SOAP."""
    SCHEDULED = "agendado"
    IN_PROGRESS = "em_progreso"
    COMPLETED = "completo"
    CANCELLED = "cancelado"
    NO_SHOW = "não_assistido"


class AppointmentPriority(str):
    """Prioridade de agendamento conforme SUS."""
    URGENT = "urgente"
    NON_URGENT = "não_urgente"
    ROUTINE = "rotino"


class Patient(Base):
    """
    Modelo de Paciente.
    Identificação por CNS/CPF conforme padrão SUS.
    """
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    identification_type = Column(
        Enum(IdentificationType),
        nullable=False,
        default=IdentificationType.CNS,
        index=True,
    )
    identification_number = Column(String(20), nullable=False, index=True)
    # Identificação única por CNS/CPF
    __table_args__ = (
        UniqueConstraint("identification_type", "identification_number", name="uq_patient_id"),
    )
    full_name = Column(String(100), nullable=False)
    gender = Column(String(10), nullable=False, default="M")
    date_of_birth = Column(DateTime, nullable=False)
    contact_phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    insurance_code = Column(String(20), nullable=True)  # Código de cobertura SUS/UBS
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    records = relationship("MedicalRecord", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, id={self.identification_number}, name={self.full_name})>"


class Appointment(Base):
    """
    Modelo de Agendamento.
    Método SOAP: Scheduling, Observation, Assessment, Plan.
    """
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(
        Integer, ForeignKey("patients.id"), nullable=False, index=True
    )
    appointment_date = Column(DateTime, nullable=False, index=True)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(
        Enum(AppointmentStatus),
        nullable=False,
        default=AppointmentStatus.SCHEDULED,
    )
    priority = Column(
        Enum(AppointmentPriority),
        nullable=False,
        default=AppointmentPriority.ROUTINE,
    )
    appointment_type = Column(String(50), nullable=False)  # Ex: consulta, consulta_urgente, etc.
    doctor_id = Column(String(50), nullable=True)  # ID do médico
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    patient = relationship("Patient", back_populates="appointments")

    def __repr__(self) -> str:
        return (
            f"<Appointment(id={self.id}, patient={self.patient_id}, "
            f"date={self.appointment_date}, status={self.status})>"
        )


class MedicalRecord(Base):
    """
    Modelo de Registro Médico.
    Método SOAP: Scheduling, Observation, Assessment, Plan.
    CID-10: Código de diagnóstico.
    """
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(
        Integer, ForeignKey("patients.id"), nullable=False, index=True
    )
    appointment_id = Column(
        Integer, ForeignKey("appointments.id"), nullable=False, index=True
    )
    appointment_date = Column(DateTime, nullable=False, index=True)
    diagnosis_code = Column(String(10), nullable=False)  # CID-10
    diagnosis_description = Column(String(200), nullable=True)
    symptoms = Column(Text, nullable=True)
    examination_notes = Column(Text, nullable=True)  # Observação SOAP
    assessment_notes = Column(Text, nullable=True)  # Avaliação SOAP
    treatment_plan = Column(Text, nullable=True)  # Plano SOAP
    medications = Column(Text, nullable=True)  # Medicamentos prescritos
    follow_up_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    patient = relationship("Patient", back_populates="records")
    appointment = relationship("Appointment", back_populates="records")

    def __repr__(self) -> str:
        return f"<MedicalRecord(id={self.id}, patient={self.patient_id}, diagnosis={self.diagnosis_code})>"


class AppointmentRecord(Base):
    """
    Modelo de registro de consulta (SOAP).
    Cada consulta gera um registro com SOAP completo.
    """
    __tablename__ = "appointment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(
        Integer, ForeignKey("appointments.id"), nullable=False, index=True
    )
    soap_scheduling = Column(Text, nullable=True)  # Scheduling SOAP
    soap_observation = Column(Text, nullable=True)  # Observation SOAP
    soap_assessment = Column(Text, nullable=True)  # Assessment SOAP
    soap_plan = Column(Text, nullable=True)  # Plan SOAP
    appointment_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    appointment = relationship("Appointment", back_populates="records")

    def __repr__(self) -> str:
        return f"<AppointmentRecord(id={self.id}, appointment={self.appointment_id})>"


class HeatmapData(Base):
    """
    Modelo para dados de heatmap de horários de pico.
    Armazena contagem de agendamentos por hora e data.
    """
    __tablename__ = "heatmap_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    hour = Column(Integer, nullable=False)
    count = Column(Integer, nullable=False, default=0)
    __table_args__ = (
        UniqueConstraint("date", "hour", name="uq_heatmap"),
    )

    def __repr__(self) -> str:
        return f"<HeatmapData(date={self.date}, hour={self.hour}, count={self.count})>"
```

---

## Arquivo: `backend/app/schemas.py`

```python
# Arquivo: backend/app/schemas.py
"""
Esquemas Pydantic v2 para validação de dados.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


# --- Esquemas de Identificação SUS/APS ---

class Identification(BaseModel):
    """Identificação do paciente conforme SUS/APS."""
    model_config = ConfigDict(frozen=True)

    identification_type: str = Field(
        description="Tipo de identificação: CNS ou CPF",
        pattern="^(CNS|CPF)$",
    )
    identification_number: str = Field(
        description="Número de identificação",
        min_length=1,
        max_length=20,
    )


class PatientCreate(BaseModel):
    """Esquema para criação de paciente."""
    model_config = ConfigDict(frozen=False)

    identification_type: str = Field(
        description="Tipo de identificação: CNS ou CPF",
        pattern="^(CNS|CPF)$",
    )
    identification_number: str = Field(
        description="Número de identificação",
        min_length=1,
        max_length=20,
    )
    full_name: str = Field(
        description="Nome completo do paciente",
        min_length=2,
        max_length=100,
    )
    gender: str = Field(description="Sexo", pattern="^(M|F)$")
    date_of_birth: datetime
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    insurance_code: Optional[str] = None


class PatientUpdate(BaseModel):
    """Esquema para atualização de paciente."""
    model_config = ConfigDict(frozen=False)

    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    gender: Optional[str] = Field(None, pattern="^(M|F)$")
    date_of_birth: Optional[datetime] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    insurance_code: Optional[str] = None


class PatientResponse(BaseModel):
    """Esquema de resposta para paciente."""
    model_config = ConfigDict(from_attributes=True, frozen=False)

    id: int
    identification_type: str
    identification_number: str
    full_name: str
    gender: str
    date_of_birth: datetime
    contact_phone: Optional[str]
    address: Optional[str]
    insurance_code: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Esquemas de Agendamento ---

class AppointmentCreate(BaseModel):
    """Esquema para criação de agendamento."""
    model_config = ConfigDict(frozen=False)

    patient_id: int
    appointment_date: datetime
    scheduled_time: datetime
    priority: str = Field(
        description="Prioridade: urgente, não_urgente, rotina",
        pattern="^(urgente|não_urgente|rotino)$",
    )
    appointment_type: str = Field(
       