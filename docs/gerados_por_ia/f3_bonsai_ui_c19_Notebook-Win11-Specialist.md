# Backend MedIA - Painel de Triagem e Monitor de Fila APS

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── triage.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── triage_service.py
│   ├── static/
│   │   └── painel_triagem.html
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       ├── test_schemas.py
│       ├── test_triage.py
│       └── conftest.py
├── requirements.txt
└── pytest.ini
```

---

## Arquivo: `backend/requirements.txt`

```text
fastapi==0.109.0
uvicorn==0.27.1
sqlalchemy==2.0.23
pydantic==2.5.2
pydantic-settings==2.1.0
alembic==1.13.1
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.25.2
python-dotenv==1.0.0
```

---

## Arquivo: `backend/pytest.ini`

```ini
[pytest]
asyncio_mode = auto
testpaths = backend/app/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
```

---

## Arquivo: `backend/app/__init__.py`

```python
"""
Projeto MedIA - Sistema de Triagem e Monitor de Fila APS
Padrões SUS / APS: CIAP-2, CID-10, SOAP, Identificação CNS/CPF
"""

__version__ = "1.0.0"
__author__ = "Engenheiro de Software MedIA"
```

---

## Arquivo: `backend/app/config.py`

```python
# Arquivo: backend/app/config.py
"""
Configuração do projeto MedIA com validação de tipos e padrões SUS/APS.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuração do sistema MedIA com padrões SUS/APS."""

    # Identificação do sistema
    app_name: str = "MedIA - Sistema de Triagem e Monitor de Fila"
    app_version: str = "1.0.0"

    # Banco de dados
    database_url: str = "postgresql://postgres:postgres@localhost:5432/media_db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False

    # API
    api_prefix: str = "/api/v1"
    debug: bool = False
    secret_key: str = "media-secret-key-change-in-production"

    # Triagem - Padrões SUS/APS
    ciap2_grades: list[int] = [1, 2, 3, 4, 5]  # Gradas de intensidade
    cid10_categories: list[str] = [
        "A00-A99", "B00-B99", "C00-C99", "D00-D99", "E00-E99",
        "F00-F99", "G00-G99", "H00-H99", "I00-I99", "J00-J99",
        "K00-K99", "L00-L99", "M00-M99", "N00-N99", "O00-O99",
        "P00-P99", "Q00-Q99", "R00-R99", "S00-S99", "T00-T99",
        "U00-U99", "V00-V99", "W00-W99", "Y00-Y99", "Z00-Z99"
    ]

    # Identificação de pacientes
    identification_methods: list[str] = ["CNS", "CPF", "CNPJ"]

    # Fila de espera
    max_queue_size: int = 100
    emergency_threshold: int = 30  # minutos

    # Audio
    audio_enabled: bool = True
    audio_volume: float = 0.7

    model_config = {"extra": "forbid"}


# Instância global
settings = Settings()
```

---

## Arquivo: `backend/app/database.py`

```python
# Arquivo: backend/app/database.py
"""
Configuração do banco de dados com SQLAlchemy 2.0 e padrões SUS/APS.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from app.config import settings


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos do projeto MedIA."""
    pass


# Configuração síncrona
engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependência assíncrona para sessão de banco de dados."""
    async with AsyncSession(bind=engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Inicializa o banco de dados com todas as tabelas."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Fecha a conexão do banco de dados."""
    await engine.dispose()
```

---

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 com padrões SUS/APS:
- CIAP-2 (Classificação de Intensidade de Agudos)
- CID-10 (Código Internacional de Diagnóstico)
- SOAP (Simptomas, Observações, Avaliação, Plano)
- Identificação por CNS/CPF
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float,
    ForeignKey, Enum as SAEnum, Index, UniqueConstraint,
    CheckConstraint, event
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class PatientIdentification(str, Enum):
    """Métodos de identificação de pacientes conforme SUS/APS."""
    CNS = "CNS"
    CPF = "CPF"
    CNPJ = "CNPJ"


class Ciap2Grade(Enum):
    """
    Classificação de Intensidade de Agudos (CIAP-2).
    Grade 1: Baixa intensidade
    Grade 5: Crítica/Immediata
    """
    GRADE_1 = 1
    GRADE_2 = 2
    GRADE_3 = 3
    GRADE_4 = 4
    GRADE_5 = 5


class PatientStatus(str, Enum):
    """Status do paciente na fila de espera."""
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISCHARGED = "discharged"
    ADMITTED = "admitted"
    EMERGENCY = "emergency"


class TriagePriority(str, Enum):
    """Prioridade de triagem conforme protocolo SUS."""
    PRIORITY_1 = "priority_1"  # Crítica
    PRIORITY_2 = "priority_2"  # Urgente
    PRIORITY_3 = "priority_3"  # Rápida
    PRIORITY_4 = "priority_4"  # Não urgente


class Patient(Base):
    """
    Modelo de Paciente com identificação por CNS/CPF.
    Conformidade SUS/APS: Identificação única por CNS/CPF.
    """

    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=base_uuid)
    identification = Column(String(11), unique=True, nullable=False, index=True)
    identification_type = Column(SAEnum(PatientIdentification), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    gender = Column(String(1), nullable=False)  # M/F
    age = Column(Integer, nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    phone = Column(String(15), nullable=True)
    email = Column(String(100), nullable=True)
    ciap2_grade = Column(SAEnum(Ciap2Grade), nullable=False)
    cid10_diagnosis = Column(String(10), nullable=False)
    soap_symptoms = Column(Text, nullable=False)
    soap_observations = Column(Text, nullable=False)
    soap_assessment = Column(Text, nullable=False)
    soap_plan = Column(Text, nullable=False)
    status = Column(SAEnum(PatientStatus), nullable=False, default=PatientStatus.WAITING)
    triage_priority = Column(SAEnum(TriagePriority), nullable=False)
    queue_position = Column(Integer, nullable=False, default=0)
    arrival_time = Column(DateTime, nullable=False)
    expected_completion = Column(DateTime, nullable=True)
    actual_completion = Column(DateTime, nullable=True)
    waiting_time = Column(Float, nullable=True)  # em minutos
    is_emergency = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relações
    appointments = relationship("Appointment", back_populates="patient")
    nurse_assignments = relationship("NurseAssignment", back_populates="patient")

    __table_args__ = (
        CheckConstraint("age >= 0", name="check_age_positive"),
        CheckConstraint("age <= 150", name="check_age_reasonable"),
        UniqueConstraint("identification", "identification_type", name="uq_patient_id"),
    )

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, id={self.identification}, status={self.status})>"


class Appointment(Base):
    """
    Modelo de Agendamento com padrão SOAP.
    """

    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=base_uuid)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    provider_name = Column(String(100), nullable=False)
    provider_specialty = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="appointments")

    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, patient={self.patient_id}, time={self.appointment_time})>"


class NurseAssignment(Base):
    """
    Modelo de Atribuição de Enfermeira ao Paciente.
    """

    __tablename__ = "nurse_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=base_uuid)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    nurse_name = Column(String(100), nullable=False)
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(SAEnum(PatientStatus), nullable=False)
    notes = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="nurse_assignments")

    def __repr__(self) -> str:
        return f"<NurseAssignment(id={self.id}, patient={self.patient_id}, nurse={self.nurse_name})>"


class TriageEvent(Base):
    """
    Evento de triagem registrado para auditoria.
    """

    __tablename__ = "triage_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=base_uuid)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # triage, reassessment, etc.
    performed_by = Column(String(100), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    details = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<TriageEvent(id={self.id}, patient={self.patient_id}, type={self.event_type})>"


from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

base_uuid = func.uuid_generate_v4()
```

---

## Arquivo: `backend/app/schemas.py`

```python
# Arquivo: backend/app/schemas.py
"""
Esquemas Pydantic v2 com tipagem estrita para o sistema MedIA.
Validação conforme padrões SUS/APS.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator, model_validator


class PatientIdentification(BaseModel):
    """Identificação do paciente conforme SUS/APS."""

    identification: str = Field(..., min_length=6, max_length=11)
    identification_type: str = Field(..., pattern="^(CNS|CPF|CNPJ)$")


class Ciap2Grade(BaseModel):
    """Classe CIAP-2 com validação de grau."""

    grade: int = Field(..., ge=1, le=5)
    description: str = Field(..., max_length=100)

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Grade CIAP-2 deve estar entre 1 e 5")
        return v


class PatientSOAP(BaseModel):
    """
    Padrão SOAP (Simptomas, Observações, Avaliação, Plano).
    Conformidade SUS/APS.
    """

    symptoms: str = Field(..., min_length=1, max_length=5000)
    observations: str = Field(..., min_length=1, max_length=5000)
    assessment: str = Field(..., min_length=1, max_length=5000)
    plan: str = Field(..., min_length=1, max_length=50