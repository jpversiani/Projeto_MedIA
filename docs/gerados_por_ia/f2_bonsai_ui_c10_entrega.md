# Interface Web de Consulta e Baixa de Prescrição (C10)

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── prescription.py
│   │   ├── patient.py
│   │   └── medication.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── prescription.py
│   │   └── patient.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── prescriptions.py
│   ├── static/
│   │   └── farmacia_dispensacao.html
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_prescription.py
│   └── test_api.py
├── requirements.txt
└── pytest.ini
```

---

## Arquivo: `backend/app/models/patient.py`

```python
# Arquivo: backend/app/models/patient.py
"""
Modelo de Paciente conforme padrões SUS/APS.
Identificação por CNS (Cadastro Nacional de Sistemas) ou CPF.
"""

from sqlalchemy import Column, Integer, String, UniqueConstraint, Index
from sqlalchemy.orm import DeclarativeBase
from datetime import date


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos SQLAlchemy."""


class Patient(Base):
    """
    Modelo Paciente conforme padrões SUS/APS.
    
    Atributos:
    - id: Identificador único do paciente
    - cns: Código Nacional de Sistemas (identificador SUS)
    - cpf: CPF do paciente
    - nome: Nome completo do paciente
    - data_nascimento: Data de nascimento
    - gender: Gênero
    - address: Endereço do paciente
    - phone: Número de telefone
    - email: Endereço de e-mail
    - created_at: Timestamp de criação
    - updated_at: Timestamp de atualização
    """
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cns = Column(String(15), unique=True, nullable=False, index=True)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    data_nascimento = Column(date, nullable=False)
    gender = Column(String(1), nullable=False)  # M/F
    address = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint("cns", name="uq_patient_cns"),
        UniqueConstraint("cpf", name="uq_patient_cpf"),
        Index("ix_patient_cns", "cns"),
        Index("ix_patient_cpf", "cpf"),
    )

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, cns={self.cns}, nome={self.nome})>"
```

---

## Arquivo: `backend/app/models/medication.py`

```python
# Arquivo: backend/app/models/medication.py
"""
Modelo de Medicamento conforme padrões SUS/APS.
Identificação por CID-10 (Código de Identificação dos Medicamentos).
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos SQLAlchemy."""


class Medication(Base):
    """
    Modelo Medicamento conforme padrões SUS/APS.
    
    Atributos:
    - id: Identificador único do medicamento
    - cid_10: Código de Identificação dos Medicamentos (CID-10)
    - nome: Nome do medicamento
    - categoria: Categoria do medicamento (ex: analgésico, antihistâmico)
    - forma: Forma de administração (ex: oral, injeção, injeção subcutânea)
    - dose: Dose recomendada
    - unidade: Unidade de medida (ex: mg, mL, g)
    - description: Descrição do medicamento
    - created_at: Timestamp de criação
    - updated_at: Timestamp de atualização
    """
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cid_10 = Column(String(10), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    categoria = Column(String(50), nullable=False)
    forma = Column(String(50), nullable=False)
    dose = Column(String(50), nullable=False)
    unidade = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint("cid_10", name="uq_medication_cid_10"),
        Index("ix_medication_cid_10", "cid_10"),
    )

    def __repr__(self) -> str:
        return f"<Medication(id={self.id}, cid_10={self.cid_10}, nome={self.nome})>"
```

---

## Arquivo: `backend/app/models/prescription.py`

```python
# Arquivo: backend/app/models/prescription.py
"""
Modelo de Prescrição conforme padrões SUS/APS.
Método SOAP (Sintoma, Observação, Avaliação, Plano).
Identificação por CNS/CPF do paciente.
"""

from sqlalchemy import (
    Column, Integer, String, ForeignKey, Text, DateTime, Enum,
    func, Index, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos SQLAlchemy."""


class Prescription(Base):
    """
    Modelo Prescrição conforme padrões SUS/APS.
    
    Atributos:
    - id: Identificador único da receita
    - patient_id: Referência ao paciente
    - cns: Código Nacional de Sistemas do paciente
    - cpf: CPF do paciente
    - hash: Hash da receita para leitura via leitor de código de barras
    - SOAP: Conteúdo SOAP (Sintoma, Observação, Avaliação, Plano)
    - status: Status da receita (em_proceso, dispensada, encerrada)
    - date_prescription: Data da receita
    - date_dispensed: Data de dispensação
    - date_expiration: Data de validade
    - created_at: Timestamp de criação
    - updated_at: Timestamp de atualização
    - dispensing_count: Contagem de dispensações
    - medication_id: Referência ao medicamento dispensado
    - dosage: Dose dispensada
    - frequency: Frequência de administração
    - duration: Duração da receita
    - notes: Notas adicionais
    """
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    cns = Column(String(15), nullable=False, index=True)
    cpf = Column(String(14), nullable=False, index=True)
    hash = Column(String(64), unique=True, nullable=False, index=True)
    soap = Column(Text, nullable=False)
    status = Column(Enum("em_proceso", "dispensada", "encerrada", name="prescription_status"),
                  default="em_proceso", nullable=False)
    date_prescription = Column(DateTime, nullable=False)
    date_dispensed = Column(DateTime, nullable=True)
    date_expiration = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    dispensing_count = Column(Integer, default=0, nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=True)
    dosage = Column(String(50), nullable=False)
    frequency = Column(String(50), nullable=False)
    duration = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("hash", name="uq_prescription_hash"),
        Index("ix_prescription_cns", "cns"),
        Index("ix_prescription_cpf", "cpf"),
        Index("ix_prescription_status", "status"),
        Index("ix_prescription_date_prescription", "date_prescription"),
    )

    # Relacionamentos
    patient = relationship("Patient", back_populates="prescriptions")
    medication = relationship("Medication", back_populates="prescriptions")

    def __repr__(self) -> str:
        return f"<Prescription(id={self.id}, hash={self.hash}, status={self.status})>"
```

---

## Arquivo: `backend/app/schemas/patient.py`

```python
# Arquivo: backend/app/schemas/patient.py
"""
Esquemas Pydantic v2 para validação de dados do paciente.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional


class PatientCreate(BaseModel):
    """Esquema para criação de paciente."""
    cns: str = Field(..., min_length=1, max_length=15, description="Código Nacional de Sistemas")
    cpf: str = Field(..., min_length=14, max_length=14, description="CPF do paciente")
    nome: str = Field(..., min_length=1, max_length=100, description="Nome completo")
    data_nascimento: date = Field(..., description="Data de nascimento")
    gender: str = Field(..., min_length=1, max_length=1, description="Gênero (M/F)")
    address: Optional[str] = Field(None, max_length=255, description="Endereço")
    phone: Optional[str] = Field(None, max_length=20, description="Telefone")
    email: Optional[str] = Field(None, max_length=100, description="E-mail")

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        """Validação do CPF."""
        if len(v) != 14:
            raise ValueError("CPF deve ter exatamente 14 dígitos")
        return v.strip()

    @field_validator("cns")
    @classmethod
    def validate_cns(cls, v: str) -> str:
        """Validação do CNS."""
        if len(v) != 15:
            raise ValueError("CNS deve ter exatamente 15 dígitos")
        return v.strip()


class PatientRead(BaseModel):
    """Esquema para leitura de paciente."""
    id: int
    cns: str
    cpf: str
    nome: str
    data_nascimento: date
    gender: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PatientUpdate(BaseModel):
    """Esquema para atualização de paciente."""
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    data_nascimento: Optional[date] = None
    gender: Optional[str] = Field(None, min_length=1, max_length=1)
    address: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
```

---

## Arquivo: `backend/app/schemas/prescription.py`

```python
# Arquivo: backend/app/schemas/prescription.py
"""
Esquemas Pydantic v2 para validação de dados da receita.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class PrescriptionCreate(BaseModel):
    """Esquema para criação de receita."""
    patient_id: int
    cns: str
    cpf: str
    soap: str = Field(..., min_length=1, max_length=10000, description="Conteúdo SOAP")
    medication_id: Optional[int] = None
    dosage: str = Field(..., min_length=1, max_length=50, description="Dose recomendada")
    frequency: str = Field(..., min_length=1, max_length=50, description="Frequência de administração")
    duration: str = Field(..., min_length=1, max_length=50, description="Duração da receita")
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("cns")
    @classmethod
    def validate_cns(cls, v: str) -> str:
        """Validação do CNS."""
        if len(v) != 15:
            raise ValueError("CNS deve ter exatamente 15 dígitos")
        return v.strip()

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        """Validação do CPF."""
        if len(v) != 14:
            raise ValueError("CPF deve ter exatamente 14 dígitos")
        return v.strip()


class PrescriptionRead(BaseModel):
    """Esquema para leitura de receita."""
    id: int
    patient_id: int
    cns: str
    cpf: str
    hash: str
    soap: str
    status: str
    date_prescription: datetime
    date_dispensed: Optional[datetime] = None
    date_expiration: datetime
    created_at: datetime
    updated_at: datetime
    dispensing_count: int
    medication_id: Optional[int] = None
    dosage: str
    frequency: str
    duration: str
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class PrescriptionDispense(BaseModel):
    """Esquema para dispensação de receita."""
    prescription_id: int
    dispensing_count: int = Field(..., ge=1, description="Contagem de dispensação")
    dosage: str = Field(..., min_length=1, max_length=50, description="Dose dispensada")
    frequency: str = Field(..., min_length=1, max_length=50, description="Frequência dispensada")
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("dosage")
    @classmethod
    def validate_dosage(cls, v: str) -> str:
        """Validação da dose dispensada."""
        if not v:
            raise ValueError("Dose não pode ser vazia")
        return v.strip()

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        """Validação da frequência dispensada."""
        if not v:
            raise ValueError("Frequência não pode ser vazia")
        return v.strip()


class PrescriptionSearch(BaseModel):
    """Esquema para busca de receita."""
    cns: Optional[str] = Field