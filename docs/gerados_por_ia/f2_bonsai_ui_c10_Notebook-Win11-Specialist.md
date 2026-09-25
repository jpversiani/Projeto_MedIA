# Interface Web de Consulta e Baixa de Prescrição (C10)

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── static/
│   │   └── farmacia_dispensacao.html
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── telemedicina.py
│   │   │   └── farmacia_dispensacao.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── patient.py
│   │   ├── prescription.py
│   │   └── dispensation.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── patient.py
│   │   ├── prescription.py
│   │   └── dispensation.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── prescription_service.py
│   │   └── dispensation_service.py
│   ├── main.py
│   └── config.py
├── tests/
│   ├── __init__.py
│   ├── test_prescription.py
│   ├── test_dispensation.py
│   └── test_barcode.py
├── requirements.txt
└── pytest.ini
```

---

## 1. Configuração do Projeto

```python
# backend/app/config.py
"""
Configuração de aplicação com tipagem estrita.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, CNS/CPF.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuração da aplicação MEDIA."""

    # Aplicação
    APP_NAME: str = "MEDIA - Sistema de Telemedicina e Farmácia"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Base de Dados
    DATABASE_URL: str = "sqlite:///media.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # API
    API_PREFIX: str = "/api/v1"
    API_TITLE: str = "API MEDIA - Telemedicina e Farmácia"
    API_DESCRIPTION: str = "Interface de consulta e baixa de prescrição"
    API_VERSION: str = "1.0.0"

    # SUS/APS
    SUS_CNPJ: str = "11.222.222/0001-00"
    SUS_CNPJ_MEDICINA: str = "11.222.222/0001-00"
    SUS_CNPJ_FARMACIA: str = "11.222.222/0002-00"

    # CID-10
    CID10_CODE: str = "I10"  # Exemplo: Códigos CID-10

    # SOAP
    SOAP_FORMAT: str = "SOAP"
    SOAP_VERSION: str = "1.1"

    # CNS/CPF
    CNS_MAX_LENGTH: int = 11
    CPF_MAX_LENGTH: int = 11

    # Prescrição
    PRESCRIPTION_DEFAULT_DURATION_DAYS: int = 30
    PRESCRIPTION_DEFAULT_RECIPIENT: str = "CNS"

    # Farmácia
    FARMACIA_NOME: str = "Farmácia UBS"
    FARMACIA_CNPJ: str = "11.222.222/0002-00"
    FARMACIA_CNPJ_MEDICINA: str = "11.222.222/0002-00"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

---

## 2. Esquemas Pydantic v2

```python
# backend/app/schemas/patient.py
"""
Esquemas Pydantic v2 para identificação SUS/APS.
Padrões: CNS (Código Nacional de Saúde) e CPF.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class PatientIdentification(BaseModel):
    """
    Identificação do paciente conforme SUS/APS.
    Suporta CNS (Código Nacional de Saúde) e CPF.
    """

    identifier_type: str = Field(
        ...,
        description="Tipo de identificação: 'CNS' ou 'CPF'",
        pattern="^(CNS|CPF)$",
        examples=["CNS", "CPF"],
    )
    identifier_value: str = Field(
        ...,
        description="Valor da identificação (CNS ou CPF)",
        min_length=1,
        max_length=11,
    )

    @field_validator("identifier_value")
    @classmethod
    def validate_identifier_length(cls, v: str) -> str:
        """Valida o comprimento da identificação."""
        if v.strip() != v:
            raise ValueError("Identificador não pode conter espaços")
        return v.strip()

    @model_validator(mode="after")
    def validate_identifier_format(self) -> "PatientIdentification":
        """Valida o formato da identificação conforme SUS/APS."""
        if self.identifier_type == "CNS":
            if not self.identifier_value.isdigit():
                raise ValueError("CNS deve conter apenas dígitos")
            if len(self.identifier_value) != 11:
                raise ValueError("CNS deve conter exatamente 11 dígitos")
        elif self.identifier_type == "CPF":
            if not self.identifier_value.isdigit():
                raise ValueError("CPF deve conter apenas dígitos")
            if len(self.identifier_value) != 11:
                raise ValueError("CPF deve conter exatamente 11 dígitos")
        return self


class PatientInfo(BaseModel):
    """
    Informações do paciente conforme padrões SUS/APS.
    """

    identifier: PatientIdentification
    name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: Optional[str] = Field(
        None,
        description="Data de nascimento do paciente",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    gender: Optional[str] = Field(
        None,
        description="Gênero do paciente",
        pattern="^(M|F|O)$",
    )
    address: Optional[str] = Field(
        None,
        description="Endereço do paciente",
        max_length=255,
    )
    phone: Optional[str] = Field(
        None,
        description="Telefone do paciente",
        max_length=20,
    )
    email: Optional[str] = Field(
        None,
        description="E-mail do paciente",
        max_length=255,
    )
    medical_history: Optional[str] = Field(
        None,
        description="Histórico médico do paciente",
        max_length=1000,
    )
    allergies: Optional[str] = Field(
        None,
        description="Alergias do paciente",
        max_length=500,
    )
    current_medications: Optional[str] = Field(
        None,
        description="Medicamentos atuais do paciente",
        max_length=1000,
    )
    notes: Optional[str] = Field(
        None,
        description="Notas adicionais do paciente",
        max_length=1000,
    )


class PatientCreate(BaseModel):
    """Esquema para criação de paciente."""

    identifier: PatientIdentification
    name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    gender: Optional[str] = Field(
        None,
        pattern="^(M|F|O)$",
    )
    address: Optional[str] = Field(
        None,
        max_length=255,
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
    )
    email: Optional[str] = Field(
        None,
        max_length=255,
    )
    medical_history: Optional[str] = Field(
        None,
        max_length=1000,
    )
    allergies: Optional[str] = Field(
        None,
        max_length=500,
    )
    current_medications: Optional[str] = Field(
        None,
        max_length=1000,
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
    )


class PatientUpdate(BaseModel):
    """Esquema para atualização de paciente."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
    )
    date_of_birth: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    gender: Optional[str] = Field(
        None,
        pattern="^(M|F|O)$",
    )
    address: Optional[str] = Field(
        None,
        max_length=255,
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
    )
    email: Optional[str] = Field(
        None,
        max_length=255,
    )
    medical_history: Optional[str] = Field(
        None,
        max_length=1000,
    )
    allergies: Optional[str] = Field(
        None,
        max_length=500,
    )
    current_medications: Optional[str] = Field(
        None,
        max_length=1000,
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
    )


class PatientRead(BaseModel):
    """Esquema para leitura de paciente."""

    id: int
    identifier: PatientIdentification
    name: str
    date_of_birth: Optional[str]
    gender: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    medical_history: Optional[str]
    allergies: Optional[str]
    current_medications: Optional[str]
    notes: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class PatientList(BaseModel):
    """Esquema para lista de pacientes."""

    patients: list[PatientRead]
    total: int
    page: int
    per_page: int
    total_pages: int


class PatientSearch(BaseModel):
    """Esquema para busca de paciente."""

    search_term: Optional[str] = Field(
        None,
        description="Termo de busca",
        max_length=100,
    )
    identifier_type: Optional[str] = Field(
        None,
        description="Tipo de identificação",
        pattern="^(CNS|CPF)$",
    )
    identifier_value: Optional[str] = Field(
        None,
        description="Valor da identificação",
        max_length=11,
    )
    name: Optional[str] = Field(
        None,
        description="Nome do paciente",
        max_length=100,
    )
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class PatientCreateResponse(BaseModel):
    """Resposta para criação de paciente."""

    patient: PatientRead
    message: str = "Paciente criado com sucesso"


class PatientUpdateResponse(BaseModel):
    """Resposta para atualização de paciente."""

    patient: PatientRead
    message: str = "Paciente atualizado com sucesso"


class PatientDeleteResponse(BaseModel):
    """Resposta para deleção de paciente."""

    message: str = "Paciente deletado com sucesso"
```

```python
# backend/app/schemas/prescription.py
"""
Esquemas Pydantic v2 para prescrição conforme SOAP/SUS.
Padrões: SOAP, CID-10, CIAP-2.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class Drug(BaseModel):
    """
    Medicamento conforme padrões SOAP/SUS.
    """

    name: str = Field(..., description="Nome do medicamento", max_length=200)
    generic_name: Optional[str] = Field(
        None,
        description="Nome genérico do medicamento",
        max_length=200,
    )
    brand_name: Optional[str] = Field(
        None,
        description="Nome da marca do medicamento",
        max_length=200,
    )
    dosage: str = Field(..., description="Dosagem do medicamento", max_length=100)
    route: str = Field(..., description="Via de administração", max_length=50)
    frequency: str = Field(..., description="Frequência de administração", max_length=100)
    duration_days: int = Field(
        ...,
        description="Duração da prescrição em dias",
        ge=1,
        le=365,
    )
    instructions: Optional[str] = Field(
        None,
        description="Instruções de uso",
        max_length=500,
    )
    contraindications: Optional[str] = Field(
        None,
        description="Contraindicações",
        max_length=500,
    )
    warnings: Optional[str] = Field(
        None,
        description="Alertas",
        max_length=500,
    )
    manufacturer: Optional[str] = Field(
        None,
        description="Fabricante",
        max_length=200,
    )
    nmp_code: Optional[str] = Field(
        None,
        description="Código NMP",
        max_length=50,
    )
    ciap2_code: Optional[str] = Field(
        None,
        description="Código CIAP-2",
        max_length=50,
    )
    cid10_code: Optional[str] = Field(
        None,
        description="Código CID-10",
        max_length=50,
    )
    quantity: int = Field(
        ...,
        description="Quantidade do medicamento",
        ge=1,
    )
    unit: str = Field(..., description="Unidade do medicamento", max_length=50)
    cost_per_unit: Optional[float] = Field(
        None,
        description="Custo por unidade",
        ge=0,
    )
    notes: Optional[str] = Field(
        None,
        description="Notas adicionais",
        max_length=500,
    )


class Prescription(BaseModel):
    """
    Prescrição conforme padrões SOAP/SUS.
    """

    id: Optional[int] = Field(
        None,
        description="ID da prescrição",
    )
    prescription_code: str = Field(
        ...,
        description="Código da prescrição",
        max_length=100,
    )
    patient_identifier: str = Field(
        ...,
        description="Identificador do paciente (CNS/