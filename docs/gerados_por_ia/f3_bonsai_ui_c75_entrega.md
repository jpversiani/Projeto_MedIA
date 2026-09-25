# Backend MedIA - Panel Visual de Triagem e Monitor de Fila APS (C75)

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── schemas.py
│   ├── services.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── triagem.py
│   ├── static/
│   │   └── painel_triagem.html
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       ├── test_schemas.py
│       ├── test_services.py
│       └── test_api.py
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## Arquivo: `backend/requirements.txt`

```text
fastapi==0.115.0
uvicorn==0.30.6
pydantic==2.9.2
pydantic-settings==2.5.2
sqlalchemy==2.0.35
alembic==1.13.1
psycopg2-binary==2.9.9
pytest==8.3.3
pytest-asyncio==0.23.8
httpx==0.27.0
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
markers =
    asyncio: marks tests as async (deselect with '-m "not asyncio"')
```

---

## Arquivo: `backend/app/__init__.py`

```python
# Arquivo: backend/app/__init__.py
"""
Projeto MedIA - Sistema de Medição e Tratamento de Fila APS (C75)
Padrões SUS / APS: CIAP-2, CID-10, SOAP, CNS/CPF
"""
```

---

## Arquivo: `backend/app/config.py`

```python
# Arquivo: backend/app/config.py
"""
Configuração do projeto MedIA com validação de tipos estrita.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, CNS/CPF
"""

from pydantic_settings import BaseSettings
from typing import Optional
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    """Configuração do sistema MedIA - Padrões SUS/APS"""

    # Identificação SUS/APS
    APP_NAME: str = "MedIA - Sistema de Fila APS (C75)"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    SUS_INSTITUTION_CODE: str = "1234567890"  # Código do SUS
    REGION: str = "01"  # Região do SUS
    STATE: str = "SP"  # Estado do SUS

    # Banco de Dados
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/media_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # API
    API_PREFIX: str = "/api/v1"
    API_VERSION: str = "v1"
    CORS_ORIGINS: list[str] = ["*"]

    # Sistema de Fila
    MAX_QUEUE_SIZE: int = 1000
    CALL_INTERVAL_SECONDS: int = 30  # Intervalo entre chamadas sonoras
    CALL_VOLUME: int = 80  # Volume da chamada (0-100)

    # Identificação SUS
    IDENTIFICATION_METHOD: str = "cns"  # CNS ou CPF
    IDENTIFICATION_LENGTH: int = 11  # CNS: 11 dígitos

    # CID-10
    CID10_VERSION: str = "2023"
    CID10_CODE_LENGTH: int = 5  # CID-10: 5 dígitos

    # SOAP
    SOAP_TEMPLATE: str = "SOAP_STD"
    SOAP_REQUIRED_FIELDS: list[str] = ["patient_id", "diagnosis", "symptoms", "treatment"]

    # Medida
    MEASURE_UNIT: str = "cm"
    MEASURE_PRECISION: int = 2  # Decimais

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "str_strip_whitespace": True,
        "extra": "forbid",
    }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

---

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 - Padrões SUS/APS
- Identificação por CNS/CPF
- CID-10 para diagnósticos
- Método SOAP para registro
- CIAP-2 para classificação de urgência
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Enum as SAEnum,
    Float,
    Integer,
    String,
    Text,
    DateTime,
    UniqueConstraint,
    Index,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos do sistema MedIA."""


class PatientType(str, enum.Enum):
    """Tipos de identificação SUS"""
    CNS = "cns"
    CPF = "cpf"


class UrgencyLevel(str, enum.Enum):
    """
    Classificação de urgência CIAP-2 (Classificação de Intensidade de Agudização)
    - 1: Crítico / Emergência
    - 2: Urgente / Alta Prioridade
    - 3: Moderado / Média Prioridade
    - 4: Baixo / Baixa Prioridade
    - 5: Não Urgente / Routine
    """
    CRITICAL = "1"
    URGENT = "2"
    MODERATE = "3"
    LOW = "4"
    NON_URGENT = "5"


class Patient(Base):
    """
    Modelo do Paciente - Identificação por CNS/CPF (SUS)
    Conformidade: Identificação única por CNS ou CPF
    """

    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_type: Mapped[PatientType] = mapped_column(
        Enum(PatientType), nullable=False, default=PatientType.CNS
    )
    identification: Mapped[str] = mapped_column(
        String(11), nullable=False, unique=True, index=True
    )
    # CPF: 11 dígitos, CNS: 11 dígitos
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    gender: Mapped[str] = mapped_column(String(1), nullable=False)  # M/F
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    date_of_birth: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relações
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    diagnoses: Mapped[list["Diagnosis"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, identification={self.identification})>"


class Appointment(Base):
    """
    Modelo de Agendamento - Método SOAP
    Conformidade: SOAP (Subjective, Objective, Assessment, Plan)
    """

    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False
    )
    appointment_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="consultation"
    )
    scheduled_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="scheduled"
    )
    # Status: scheduled, in_progress, completed, cancelled, no_show
    current_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="scheduled"
    )
    triage_level: Mapped[UrgencyLevel] = mapped_column(
        Enum(UrgencyLevel), nullable=False, default=UrgencyLevel.MODERATE
    )
    ciap2_classification: Mapped[str] = mapped_column(
        String(10), nullable=False, default="02"  # CIAP-2: 01-05
    )
    soap_subjective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    soap_objective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    soap_assessment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    soap_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigned_nurse: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    assigned_doctor: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relações
    patient: Mapped["Patient"] = relationship(back_populates="appointments")
    diagnoses: Mapped[list["Diagnosis"]] = relationship(
        back_populates="appointment", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, patient={self.patient_id}, status={self.current_status})>"


class Diagnosis(Base):
    """
    Modelo de Diagnóstico - CID-10
    Conformidade: CID-10 (Classificação Internacional de Doenças)
    """

    __tablename__ = "diagnoses"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False
    )
    cid10_code: Mapped[str] = mapped_column(
        String(5), nullable=False, index=True
    )
    cid10_description: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    icd10_code: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )
    icd10_description: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    severity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relações
    appointment: Mapped["Appointment"] = relationship(back_populates="diagnoses")

    def __repr__(self) -> str:
        return f"<Diagnosis(id={self.id}, cid10={self.cid10_code})>"


class Nurse(Base):
    """
    Modelo da Equipe de Enfermeiros
    """

    __tablename__ = "nurses"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    registration_number: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True
    )
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    assigned_appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="assigned_nurse", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Nurse(id={self.id}, name={self.name})>"


class AppointmentQueue(Base):
    """
    Modelo de Fila de Agendamento - Monitor de Fila APS (C75)
    """

    __tablename__ = "appointment_queue"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_wait_time_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    is_called: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    call_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relações
    appointment: Mapped["Appointment"] = relationship(back_populates="queue")

    def __repr__(self) -> str:
        return (
            f"<Queue(id={self.id}, position={self.position}, "
            f"wait={self.estimated_wait_time_seconds}s, called={self.is_called})>"
        )


class CallLog(Base):
    """
    Modelo de Log de Chamadas - Monitor de Fila APS (C75)
    """

    __tablename__ = "call_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),