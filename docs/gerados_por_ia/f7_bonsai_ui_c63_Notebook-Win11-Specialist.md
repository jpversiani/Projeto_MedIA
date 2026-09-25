# Dashboard Executivo Interativo - Projeto MedIA

## Estrutura do Projeto

```
media/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── telemedicina.py
│   │   │   └── dashboard.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── analytics.py
│   │   ├── static/
│   │   │   └── dashboard_analytics.html
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── sus_patterns.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_schemas.py
│   │   ├── test_api.py
│   │   └── test_dashboard.py
│   ├── requirements.txt
│   └── pyproject.toml
└── README.md
```

---

## 1. `backend/requirements.txt`

```text
# Arquivo: backend/requirements.txt
fastapi==0.115.0
uvicorn==0.30.6
sqlalchemy==2.0.35
asyncpg==0.29.0
pydantic==2.9.2
pydantic-settings==2.5.2
alembic==1.13.1
python-multipart==0.0.9
chartjs==0.4.0
python-dotenv==1.0.0
pytest==8.3.2
pytest-asyncio==0.23.5
httpx==0.27.0
```

---

## 2. `backend/pyproject.toml`

```toml
# Arquivo: backend/pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "media-backend"
version = "1.0.0"
description = "Backend do Projeto MedIA com Dashboard Executivo"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.30.6",
    "sqlalchemy>=2.0.35",
    "asyncpg>=0.29.0",
    "pydantic>=2.9.2",
    "pydantic-settings>=2.5.2",
    "alembic>=1.13.1",
    "python-multipart>=0.0.9",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.2",
    "pytest-asyncio>=0.23.5",
    "httpx>=0.27.0",
]

[tool.pytest.ini_options]
testpaths = ["backend/tests"]
asyncio_mode = "auto"
```

---

## 3. `backend/app/config.py`

```python
# Arquivo: backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuração do projeto MedIA com padrões SUS/APS."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://media_user:media_pass@localhost:5432/media_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # API
    APP_NAME: str = "MedIA - Sistema de Telemedicina"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["*"]

    # SUS/APS Patterns
    SUS_CICLO: str = "CICLO"
    SUS_CICLO_2: str = "CICLO2"
    SUS_CID_10: str = "CID-10"
    SUS_CNS: str = "CNS"
    SUS_CPF: str = "CPF"
    SUS_SOAP: str = "SOAP"

    # Dashboard
    DASHBOARD_DAYS: int = 30
    DASHBOARD_HOUR_BINS: int = 24

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
```

---

## 4. `backend/app/database.py`

```python
# Arquivo: backend/app/database.py
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
)


async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos SQLAlchemy."""


async def get_db():
    """Dependência assíncrona para sessão de banco."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
```

---

## 5. `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class SusPatient(Base):
    """
    Modelo SUS/APS: Identificação por CNS/CPF.
    Padrão: Identificação por CNS/CPF conforme APs.
    """
    __tablename__ = "sus_patient"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cns = Column(String(15), unique=True, nullable=False, index=True)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    data_nascimento = Column(DateTime, nullable=False)
    gender = Column(String(1), nullable=False)  # M/F
    telefone = Column(String(11), nullable=True)
    email = Column(String(100), nullable=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)

    # Relação com consultas
    consultas = relationship("Consultation", back_populates="patient")

    def __repr__(self) -> str:
        return f"<SusPatient(cns={self.cns}, nome={self.nome})>"


class Consultation(Base):
    """
    Modelo SOAP: Sinalização, Observação, Abstração, Procedimento.
    Padrão SUS/APS: Método SOAP para registro de consultas.
    """
    __tablename__ = "consultation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("sus_patient.id"), nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    appointment_hour = Column(Integer, nullable=False)  # 0-23
    status = Column(String(20), default="AGENDADA")  # AGENDADA, REALIZADA, CANCELADA
    soap_sinalization = Column(Text, nullable=True)
    soap_observations = Column(Text, nullable=True)
    soap_abstraction = Column(Text, nullable=True)
    soap_procedure = Column(Text, nullable=True)
    icd10_diagnosis = Column(String(20), nullable=True)  # CID-10
    ciap2_code = Column(String(20), nullable=True)  # CIAP-2
    duration_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relação com patient
    patient = relationship("SusPatient", back_populates="consultations")

    def __repr__(self) -> str:
        return f"<Consultation(id={self.id}, patient={self.patient_id}, date={self.appointment_date})>"


class Appointment(Base):
    """
    Modelo de agendamento com heatmap de horários de pico.
    """
    __tablename__ = "appointment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("sus_patient.id"), nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    appointment_hour = Column(Integer, nullable=False)
    appointment_slot = Column(String(20), nullable=False)
    status = Column(String(20), default="AGENDADA")
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("SusPatient", back_populates="consultations")

    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, patient={self.patient_id}, date={self.appointment_date})>"


class TelemedicineRecord(Base):
    """
    Modelo de registro de telemedicina.
    """
    __tablename__ = "telemedicine_record"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("sus_patient.id"), nullable=False)
    consultation_id = Column(UUID(as_uuid=True), ForeignKey("consultation.id"), nullable=True)
    video_url = Column(String(500), nullable=True)
    recording_url = Column(String(500), nullable=True)
    doctor_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("SusPatient", back_populates="consultations")
    consultation = relationship("Consultation", back_populates="telemedicine_records")

    def __repr__(self) -> str:
        return f"<TelemedicineRecord(id={self.id}, patient={self.patient_id})>"


class KPIData(Base):
    """
    Modelo para KPIs em tempo real.
    """
    __tablename__ = "kpi_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<KPIData(metric={self.metric_name}, value={self.value})>"
```

---

## 6. `backend/app/schemas.py`

```python
# Arquivo: backend/app/schemas.py
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


# ==================== SUS/APS Patterns ====================

class SusPatientCreate(BaseModel):
    """Schema de criação de paciente com padrões SUS/APS."""
    cns: str = Field(..., min_length=1, max_length=15, description="CNS do paciente")
    cpf: str = Field(..., min_length=14, max_length=14, description="CPF do paciente")
    nome: str = Field(..., min_length=1, max_length=100, description="Nome completo")
    data_nascimento: datetime = Field(..., description="Data de nascimento")
    gender: str = Field(..., pattern="^(M|F)$", description="Gênero (M/F)")
    telefone: Optional[str] = Field(None, max_length=11)
    email: Optional[str] = Field(None, max_length=100)


class SusPatientUpdate(BaseModel):
    """Schema de atualização de paciente."""
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    telefone: Optional[str] = Field(None, max_length=11)
    email: Optional[str] = Field(None, max_length=100)


class SusPatientResponse(BaseModel):
    """Schema de resposta de paciente."""
    id: str
    cns: str
    cpf: str
    nome: str
    data_nascimento: datetime
    gender: str
    telefone: Optional[str]
    email: Optional[str]
    data_criacao: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Consultation/SOAP ====================

class ConsultationCreate(BaseModel):
    """Schema de criação de consulta com método SOAP."""
    patient_id: str
    appointment_date: datetime
    appointment_hour: int = Field(..., ge=0, le=23)
    soap_signalization: Optional[str] = None
    soap_observations: Optional[str] = None
    soap_abstraction: Optional[str] = None
    soap_procedure: Optional[str] = None
    icd10_diagnosis: Optional[str] = None  # CID-10
    ciap2_code: Optional[str] = None  # CIAP-2
    duration_minutes: Optional[int] = None


class ConsultationResponse(BaseModel):
    """Schema de resposta de consulta."""
    id: str
    patient_id: str
    appointment_date: datetime
    appointment_hour: int
    status: str
    soap_signalization: Optional[str]
    soap_observations: Optional[str]
    soap_abstraction: Optional[str]
    soap_procedure: Optional[str]
    icd10_diagnosis: Optional[str]
    ciap2_code: Optional[str]
    duration_minutes: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Telemedicine ====================

class TelemedicineRecordCreate(BaseModel):
    """Schema de criação de registro de telemedicina."""
    patient_id: str
    consultation_id: Optional[str] = None
    video_url: Optional[str] = None
    recording_url: Optional[str] = None
    doctor_notes: Optional[str] = None


class TelemedicineRecordResponse(BaseModel):
    """Schema de resposta de registro de telemedicina."""
    id: str
    patient_id: str
    consultation_id: Optional[str]
    video_url: Optional[str]
    recording_url: Optional[str]
    doctor_notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== KPIs ====================

class KPIResponse(BaseModel):
    """Schema de KPI."""
    id: str
    metric_name: str
    value: float
    timestamp: datetime
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class KPIsResponse(BaseModel):
    """Schema de lista de KPIs."""
    metrics: List[KPIResponse]
    updated_at: datetime


# ==================== Dashboard Analytics ====================

class HourlyDataPoint(BaseModel):
    """Ponto de dados para heatmap de horários."""
    hour: int
    value: float
    label: str


class DailyDataPoint(BaseModel):
    """Ponto de dados para gráfico de linha."""
    date: datetime
    value: float
    label: str


class KPICard(BaseModel):
    """Card de KPI para o dashboard."""
    id: str
    title: str
    value: float
    unit: str
    description: str
    trend: str  # "Aumentando", "Estável", "Diminuindo"
