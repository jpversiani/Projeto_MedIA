# Projeto MedIA - Interface Web de Consulta e Baixa de Prescrição (C26)

## Estrutura do Projeto

```
media/
├── backend/
│   ├── __init__.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── static/
│   │   │   ├── farmacia_dispensacao.html
│   │   │   └── style.css
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   └── test_api.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── dispensacao.py
│   ├── requirements.txt
│   └── config.py
└── README.md
```

---

## Arquivo: `backend/app/__init__.py`

```python
# Arquivo: backend/app/__init__.py
"""
Pacote app do projeto MedIA.
Interface Web de Consulta e Baixa de Prescrição (C26) para atendentes de farmácia da UBS.
Padrões: SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF).
"""
```

---

## Arquivo: `backend/app/database.py`

```python
# Arquivo: backend/app/database.py
"""
Configuração da base de dados com SQLAlchemy 2.0.
Suporte a PostgreSQL e SQLite para desenvolvimento.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./media_db.sqlite"
)

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)

Base = declarative_base()


def get_db() -> Session:
    """Yield a database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Inicializa todas as tabelas na base de dados."""
    Base.metadata.create_all(bind=engine)
```

---

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para o sistema MedIA.
Conformidade com padrões SUS/APS:
- CIAP-2: Código de Identificação de Attribuição de Profissão
- CID-10: Código Internacional de Diagnóstico
- SOAP: Método de comunicação
- Identificação por CNS/CPF
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey,
    Enum, Numeric, Float, Index, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from .database import Base


class CNS(Enum):
    """Identificador do Sistema Nacional de Cadastro."""
    CPF = "CPF"
    CNPJ = "CNPJ"
    CPF_MF = "CPF_MF"
    CPF_JUR = "CPF_JUR"
    CPF_MF_JUR = "CPF_MF_JUR"


class CID10(Enum):
    """Código Internacional de Diagnóstico 10."""
    # Exemplos comuns
    CARDIOVASCULAR = "I21.9"
    DIABETES = "E11.9"
    HIPERTENSIA = "I10.0"
    ASTMA = "J41.9"
    HIPOTENSIA = "I50.0"
    DEPRESSAO = "F41.3"
    ANXIOSIDADE = "F41.1"
    DIALSEIS = "I20.9"
    OBEZESIA = "E50.9"
    DEMENTO = "F02.0"
    OTR = "F99.9"


class Patient(Base):
    """
    Modelo de Paciente/Patente.
    Identificação por CNS (CPF/CNPJ).
    """
    __tablename__ = "patient"

    id = Column(Integer, primary_key=True, index=True)
    CNS = Column(String(14), unique=True, nullable=False, index=True)
    CNS_TYPE = Column(Enum(CNS), nullable=False, default=CNS.CPF)
    full_name = Column(String(120), nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(1), nullable=True)  # M/F
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    prescriptions = relationship("Prescription", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "CNS": self.CNS,
            "CNS_TYPE": self.CNS_TYPE.value,
            "full_name": self.full_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Prescription(Base):
    """
    Modelo de Prescrição Digital.
    Suporte a leitura via código de barras / hash.
    """
    __tablename__ = "prescription"

    id = Column(Integer, primary_key=True, index=True)
    hash_code = Column(String(64), unique=True, nullable=False, index=True)
    barcode_code = Column(String(50), nullable=True, index=True)
    patient_cns = Column(String(14), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=True)
    doctor_cns = Column(String(14), nullable=True, index=True)
    doctor_name = Column(String(120), nullable=True)
    prescription_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="ativo")
    # Status: ativo, consumido, expirado, cancelado, rejeitado
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relação com itens da receita
    items = relationship("PrescriptionItem", back_populates="prescription")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "hash_code": self.hash_code,
            "barcode_code": self.barcode_code,
            "patient_cns": self.patient_cns,
            "patient_id": self.patient_id,
            "doctor_cns": self.doctor_cns,
            "doctor_name": self.doctor_name,
            "prescription_date": self.prescription_date.isoformat() if self.prescription_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PrescriptionItem(Base):
    """
    Modelo de item da receita.
    Conformidade com CID-10 e CIAP-2.
    """
    __tablename__ = "prescription_item"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescription.id"), nullable=False)
    drug_name = Column(String(120), nullable=False)
    drug_code = Column(String(50), nullable=True)  # CID-10 / Nomenclatura
    dosage = Column(Numeric(10, 2), nullable=True)
    frequency = Column(String(50), nullable=True)  # q.d., 3x/d., etc.
    duration = Column(String(50), nullable=True)  # 7 dias, 30 dias, etc.
    instructions = Column(Text, nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    prescription = relationship("Prescription", back_populates="items")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "prescription_id": self.prescription_id,
            "drug_name": self.drug_name,
            "drug_code": self.drug_code,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "duration": self.duration,
            "instructions": self.instructions,
            "quantity": self.quantity,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DispensingRecord(Base):
    """
    Registro de dispensação (C26).
    Audit trail completo.
    """
    __tablename__ = "dispensing_record"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescription.id"), nullable=False)
    patient_cns = Column(String(14), nullable=False)
    patient_name = Column(String(120), nullable=False)
    dispenser_cns = Column(String(14), nullable=False)  # Atenente da farmácia
    dispenser_name = Column(String(120), nullable=False)
    dispensing_date = Column(DateTime, nullable=False)
    quantity_dispensed = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="completa")
    # Status: completa, parcial, rejeitada, cancelada
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    prescription = relationship("Prescription", back_populates="dispensing_records")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "prescription_id": self.prescription_id,
            "patient_cns": self.patient_cns,
            "patient_name": self.patient_name,
            "dispenser_cns": self.dispenser_cns,
            "dispenser_name": self.dispenser_name,
            "dispensing_date": self.dispensing_date.isoformat() if self.dispensing_date else None,
            "quantity_dispensed": self.quantity_dispensed,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PrescriptionStatus(Base):
    """
    Status da receita conforme SUS/APS.
    """
    __tablename__ = "prescription_status"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    description = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "description": self.description,
            "is_active": self.is_active,
        }


class DispensingStatus(Base):
    """
    Status de dispensação conforme C26.
    """
    __tablename__ = "dispensing_status"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    description = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "description": self.description,
            "is_active": self.is_active,
        }
```

---

## Arquivo: `backend/app/schemas.py`

```python
# Arquivo: backend/app/schemas.py
"""
Esquemas Pydantic v2 para validação de dados.
Conformidade com tipos do SUS/APS.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum

from .models import CNS, CID10


# --- Enums ---

class PrescriptionStatusEnum(str, Enum):
    """Status da receita."""
    ATIVO = "ativo"
    CONSUMIDO = "consumido"
    EXPIRADO = "expirado"
    CANCELADO = "cancelado"
    REJETADO = "rejeitado"


class DispensingStatusEnum(str, Enum):
    """Status de dispensação."""
    COMPLETA = "completa"
    PARCIAL = "parcial"
    REJETADA = "rejeitada"
    CANCELADA = "cancelada"


class PatientCreate(BaseModel):
    """Esquema para criação de paciente."""
    CNS: str = Field(..., min_length=11, max_length=14, description="CPF ou CNPJ")
    CNS_TYPE: CNS = Field(default=CNS.CPF)
    full_name: str = Field(..., min_length=2, max_length=120)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(None, pattern="^[MF]$")
    address: Optional[str] = None
    phone: Optional[str] = Field(None, pattern="^\+?[0-9\s\-()]{10,20}$")
    email: Optional[str] = Field(None, max_length=120)

    @field_validator("CNS")
    @classmethod
    def validate_cns(cls, v: str) -> str:
        if CNS.CPF.value in v.upper():
            if len(v) != 11:
                raise ValueError("CPF deve ter exatamente 11 dígitos")
        elif CNS.CNPJ.value in v.upper():
            if len(v) != 14:
                raise ValueError("CNPJ deve ter exatamente 14 dígitos")
        return v.upper()


class PrescriptionCreate(BaseModel):
    """Esquema para criação de receita."""
    patient_cns: str = Field(..., min_length=11, max_length=14)
    doctor_cns: Optional[str] = Field(None, min_length=11, max_length=14)
    doctor_name: Optional[str] = Field(None, max_length=120)
    prescription_date: datetime = Field(..., description="Data da receita")
    expiry_date: datetime = Field(..., description="Data de vencimento")
    notes: Optional[str] = None
    items: List["PrescriptionItemCreate"] = Field(..., min_items=1)

    @field_validator("prescription_date")
    @classmethod