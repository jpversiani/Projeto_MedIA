# Projeto MedIA - Interface Farmacia Dispensação (C90)

## Estrutura do Projeto

```
media/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── patient.py
│   │   │   ├── prescription.py
│   │   │   ├── medication.py
│   │   │   └── dispensation.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── patient.py
│   │   │   ├── prescription.py
│   │   │   ├── medication.py
│   │   │   └── dispensation.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── prescriptions.py
│   │   │   │   ├── dispensation.py
│   │   │   │   └── health_records.py
│   │   │   └── health_records.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── prescription_service.py
│   │   │   ├── dispensation_service.py
│   │   │   └── health_record_service.py
│   │   ├── static/
│   │   │   └── farmacia_dispensacao.html
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_prescription.py
│   │       ├── test_dispensation.py
│   │       ├── test_health_records.py
│   │       └── conftest.py
│   ├── requirements.txt
│   └── pytest.ini
├── tests/
│   ├── __init__.py
│   └── test_integration.py
├── docker-compose.yml
└── README.md
```

---

## 1. Configuração do Backend

```python
# backend/app/config.py
"""
Configuração do backend MedIA - SUS/APS Compliant
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuração do projeto MedIA com suporte a SUS/APS"""

    # Aplicação
    APP_NAME: str = "MedIA - Sistema de Consultas e Baixa de Prescrições"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENV: str = "development"

    # Banco de Dados PostgreSQL
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/media_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    # API
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["*"]

    # SUS/APS - Identificação
    SUS_CNPJ: str = "11.222.222/0001-00"
    SUS_CNPJ_MUNICIPAL: str = "11.222.222/0001-00"

    # Hash de Prescrição (CID-10 / SUS)
    PRESCRIPTION_HASH_LENGTH: int = 16
    PRESCRIPTION_HASH_ALGORITHM: str = "sha256"

    # Medicamentos - CID-10
    CID10_PREFIX: str = "CID10"

    # Susceptibilidade dos dados
    DATA_RETENTION_DAYS: int = 365 * 5  # 5 anos conforme SUS

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

```python
# backend/app/__init__.py
"""
Backend MedIA - Sistema de Consultas e Baixa de Prescrições
SUS/APS Compliant - CIAP-2, CID-10, SOAP, CNS/CPF
"""
```

```python
# backend/app/main.py
"""
Entrada principal do Backend MedIA
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

from app.config import settings
from app.api.v1 import prescriptions, dispensation, health_records

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle do application com inicialização do banco de dados"""
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,
    )
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema de Consultas e Baixa de Prescrições - SUS/APS Compliant",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar rotas
app.include_router(prescriptions.router, prefix=settings.API_PREFIX)
app.include_router(dispensation.router, prefix=settings.API_PREFIX)
app.include_router(health_records.router, prefix=settings.API_PREFIX)

@app.get("/health")
async def health_check():
    """Endpoint de saúde do serviço"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "susp_compliant": True,
        "aps_compliant": True,
    }
```

---

## 2. Modelos do Banco de Dados (SQLAlchemy 2.0)

```python
# backend/app/models/base.py
"""
Base do SQLAlchemy com suporte a timestamps e soft delete
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, UUID as PG_UUID

Base = declarative_base()


class TimestampMixin:
    """Mixin com timestamps de criação e atualização"""
    created_at: Column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin com soft delete"""
    is_deleted: Column(Boolean, default=False, nullable=False)
    deleted_at: Column(DateTime, nullable=True)


class UUIDMixin:
    """Mixin com UUID como primary key"""
    id: Column(PG_UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
```

```python
# backend/app/models/patient.py
"""
Modelo de Paciente - Identificação por CNS/CPF conforme SUS
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin


class Patient(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """
    Modelo de Paciente conforme SUS/APS
    Identificação: CNS (Código Nacional de Suscriptor) / CPF
    """
    __tablename__ = "patients"

    # Identificação SUS
    cns: Column(String(11), unique=True, nullable=False, index=True)
    cpf: Column(String(14), unique=True, nullable=False, index=True)
    cnpj: Column(String(14), nullable=True)  # Para empresas

    # Dados demográficos
    nome: Column(String(100), nullable=False)
    sobrenome: Column(String(100), nullable=False)
    data_nascimento: Column(DateTime, nullable=False)
    gender: Column(Enum("M", "F", "O", name="gender_enum"), nullable=False)
    address: Column(String(200), nullable=True)
    phone: Column(String(20), nullable=True)

    # Dados de consulta
    last_visit_date: Column(DateTime, nullable=True)
    last_visit_cnpj: Column(String(14), nullable=True)
    last_visit_cnpj_municipal: Column(String(14), nullable=True)

    # Relações
    prescriptions: relationship(
        "Prescription",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Patient(cns={self.cns}, cpf={self.cpf}, nome={self.nome})>"


class PatientType(Enum):
    """Tipos de pacientes conforme SUS"""
    INDIVIDUAL = "individual"
    ENTIDADE = "entity"
    ORGANIZACIONAL = "organizational"
```

```python
# backend/app/models/prescription.py
"""
Modelo de Prescrição conforme SUS/APS
- CID-10 para identificação de medicamentos
- Método SOAP para registro
- Hash de prescrição para leitura via código de barras
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Numeric, Float
from sqlalchemy.dialects.postgresql import UUID, UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin


class PrescriptionStatus(Enum):
    """Status da prescrição conforme SUS"""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    DISPENSING = "dispensing"
    DISPENSED = "dispensed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Prescription(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """
    Modelo de Prescrição conforme SUS/APS
    - Identificação por Hash (leitura via código de barras)
    - CID-10 para medicamentos
    - Método SOAP para registro
    - Referência a CNS/CPF do paciente
    """
    __tablename__ = "prescriptions"

    # Identificação
    prescription_hash: Column(String(64), unique=True, nullable=False, index=True)
    prescription_code: Column(String(50), nullable=False, index=True)
    cnpj_prescriptor: Column(String(14), nullable=False)  # CNPJ do prescriptor
    cnpj_prescriptor_municipal: Column(String(14), nullable=False)

    # Referência ao paciente
    patient_cns: Column(String(11), nullable=False, index=True)
    patient_cpf: Column(String(14), nullable=False, index=True)
    patient_name: Column(String(100), nullable=False)  # Snapshot do nome do paciente

    # Dados da consulta
    consultation_date: Column(DateTime, nullable=False)
    consultation_cnpj: Column(String(14), nullable=False)
    consultation_cnpj_municipal: Column(String(14), nullable=False)
    consultation_notes: Column(Text, nullable=True)

    # Status e validade
    status: Column(Enum(PrescriptionStatus, name="prescription_status_enum"), nullable=False)
    validity_from: Column(DateTime, nullable=False)
    validity_to: Column(DateTime, nullable=False)
    prescription_type: Column(Enum("inpatient", "outpatient", "emergency", name="prescription_type_enum"), nullable=False)

    # Relações
    medications: relationship(
        "Medication",
        back_populates="prescription",
        cascade="all, delete-orphan",
    )
    dispensations: relationship(
        "Dispensation",
        back_populates="prescription",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Prescription(hash={self.prescription_hash[:8]}..., patient_cns={self.patient_cns})>"


class PrescriptionType(Enum):
    """Tipos de prescrição conforme SUS"""
    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"
    EMERGENCY = "emergency"
```

```python
# backend/app/models/medication.py
"""
Modelo de Medicamento conforme CID-10
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Numeric, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin


class DrugClass(Enum):
    """Classe de medicamentos conforme SUS"""
    ANTIBIOTIC = "antibiotic"
    ANTI-INFLAMMATORY = "anti-inflammatory"
    ANTI-DEPRESSANT = "anti-depressant"
    ANTI-HYPERTENSIVE = "anti-hypertensive"
    ANTIDIABETIC = "anti-diabetic"
    ANTICANCER = "anti-cancer"
    CARDIOVASCULAR = "cardiovascular"
    RESPIRATORY = "respiratory"
    NEUROLOGICAL = "neurological"
    PSYCHIATRIC = "psychiatric"
    PAIN_RELIEVER = "pain-reliever"
    OTHER = "other"


class Route(Enum):
    """Via de administração conforme SUS"""
    ORAL = "oral"
    INJECTED = "injected"
    TOPICAL = "topical"
    INHALATION = "inhalation"
    INTRAVENOUS = "intravenous"
    INTRAMUSCULAR = "intramuscular"
    SUBDERMAL = "subdermal"
    RECTAL = "rectal"
    INHALATION = "inhalation"
    INTRAVENOUS = "intravenous"


class Medication(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """
    Modelo de Medicamento conforme CID-10
    - CID-10: Código de identificação do medicamento
    - Classe de medicamento
    - Via de administração
    """
    __tablename__ = "medications"

    # Identificação CID-10
    cid10: Column(String(10), unique=True, nullable=False, index=True)
    cid10_short: Column(String(6), unique=True, nullable=False, index=True)  # CID10 truncado

    # Dados do medicamento
    name: Column(String(200), nullable=False)
    generic_name: Column(String(200), nullable=True)
    brand_name: Column(String(200), nullable=True)
    manufacturer: Column(String(100), nullable=True)

    # Classe e via
    drug_class: Column(Enum(DrugClass, name="drug_class_enum"), nullable=False)
    route: Column(Enum(Route, name="route_enum"), nullable=False)

    # Dose e unidade
    dose: Column(Numeric(10, 2), nullable=False)
    unit: Column(String(20), nullable=False)  # mg, g, mL, etc.
    max_dose: Column(Numeric(10, 2), nullable=True)
    min_dose: Column(Numeric