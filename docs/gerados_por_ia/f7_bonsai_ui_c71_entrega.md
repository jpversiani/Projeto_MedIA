# Dashboard Executivo Interativo - Projeto MedIA

## Estrutura do Projeto

```
media/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routes.py
│   │   ├── services.py
│   │   ├── static/
│   │   │   ├── dashboard_analytics.html
│   │   │   ├── style.css
│   │   │   └── dashboard.js
│   │   └── config.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_models.py
│   │   ├── test_schemas.py
│   │   ├── test_routes.py
│   │   └── test_services.py
│   ├── requirements.txt
│   └── pytest.ini
└── README.md
```

---

## 1. Configuração do Projeto

```python
# backend/app/config.py
"""
Configuração do projeto MedIA.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, CNS/CPF.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuração do projeto com suporte a ambientes."""
    
    # Aplicação
    APP_NAME: str = "MedIA"
    DEBUG: bool = False
    TESTING: bool = False
    
    # Base de Dados (SQLite para desenvolvimento, PostgreSQL para produção)
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///media.db"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    
    # Sus/APS - Padrões de Identificação
    SUS_CNPJ: str = "0000000000000000"  # CNPJ do SUS
    SUS_CNPJ_MUNICIPAL: str = "0000000000000000"  # CNPJ do município
    
    # CID-10 - Classificação Internacional de Doenças
    CID10_VERSION: str = "2022"
    
    # SOAP - Método de Registro
    SOAP_VERSION: str = "2.0"
    
    # Identificação por CNS/CPF
    CNS_PREFIX: str = "12345"  # Prefixo de CNS para geração de IDs
    CPF_PREFIX: str = "123456789"  # Prefixo de CPF para geração de IDs
    
    # Dashboards
    DASHBOARD_KPI_COUNT: int = 6
    DASHBOARD_HEATMAP_DAYS: int = 30
    DASHBOARD_LINE_CHART_DAYS: int = 30
    
    # Limites de paginação
    PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Cache
    CACHE_TTL: int = 300  # 5 minutos
    
    @classmethod
    def get(cls, key: str) -> str:
        """Obter configuração por chave."""
        return getattr(cls, key, "")
    
    @classmethod
    def get_int(cls, key: str) -> int:
        """Obter configuração inteira."""
        return int(getattr(cls, key, 0))
    
    @classmethod
    def get_bool(cls, key: str) -> bool:
        """Obter configuração booleana."""
        return bool(getattr(cls, key, False))


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///media_dev.db"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///media_test.db"
    DEBUG = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "postgresql://user:pass@localhost:5432/media_prod"
    TESTING = False


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
```

```python
# backend/app/__init__.py
"""
Aplicação MedIA - Backend com padrões SUS/APS.
"""

from .config import config_map
from .models import db
from .main import create_app


def create_app(config_name: str = "development") -> object:
    """
    Factory de aplicação com padrão SUS/APS.
    
    Args:
        config_name: Nome do ambiente (development, testing, production)
    
    Returns:
        Aplicação Flask configurada
    """
    from .main import app
    
    config = config_map.get(config_name, config_map["development"])
    app.config.from_object(config)
    
    # Inicializar modelos
    from .models import (
        Patient,
        MedicalRecord,
        Appointment,
        Diagnosis,
        Treatment,
        Medication,
        LaboratoryResult,
        Vitals,
        Hospital,
        Doctor,
        Ward,
        Room,
        MedicationPrescription,
        EmergencyRecord,
        PatientContact,
        InsuranceRecord,
        MedicalDevice,
        MedicalProcedure,
        HospitalDepartment,
        MedicalStaff,
        PatientAllergy,
        MedicalNote,
        ClinicalTrial,
        ResearchRecord,
        QualityAssessment,
        PatientFeedback,
        StaffTraining,
        EquipmentMaintenance,
        InventoryRecord,
        FinancialRecord,
        AuditLog,
        ComplianceRecord,
        RiskAssessment,
        CarePlan,
        FollowUpRecord,
        DischargeRecord,
        TransferRecord,
        EmergencyResponse,
        DisasterPreparedness,
        CommunityHealth,
        PublicHealth,
        Epidemiology,
        HealthEquity,
        SocialDeterminants,
        MentalHealth,
        Rehabilitation,
        PalliativeCare,
        GeriatricCare,
        PediatricCare,
        MaternalCare,
        OccupationalHealth,
        EnvironmentalHealth,
        OccupationalInjury,
        WorkplaceSafety,
        OccupationalHealth,
        OccupationalHealth,
    )
    
    return app
```

```python
# backend/app/models.py
"""
Modelos SQLAlchemy 2.0 com padrões SUS/APS.
Identificação por CNS/CPF, CID-10, SOAP.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum as SAEnum, Numeric, LargeBinary,
    Index, UniqueConstraint, CheckConstraint,
    event, func, JSON, Text, LargeBinary,
    Index, UniqueConstraint, CheckConstraint,
    Index, UniqueConstraint, CheckConstraint,
    Index, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import (
    declarative_base, relationship, sessionmaker,
    Mapped, mapped_column, validates, validated
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import text

Base = declarative_base()


# ============================================================================
# ENUMERACIONES SUS/APS
# ============================================================================

class CID10Category(Enum):
    """Categorias CID-10 (ICD-10)."""
    A = "A"  # Doenças e condições
    B = "B"  # Doenças infecciosas, parasitas, parasitoses
    C = "C"  # Doenças neoplásticas
    D = "D"  # Doenças do sistema cardiovascular
    E = "E"  # Doenças endocrinas
    F = "F"  # Doenças do sistema respiratório
    G = "G"  # Doenças do sistema digestivo
    H = "H"  # Doenças do sistema renal
    I = "I"  # Doenças do sistema imunológico e alérgicos
    J = "J"  # Doenças do sistema hematológico
    K = "K"  # Doenças do sistema musculoesqueletico e articulares
    L = "L"  # Doenças do sistema nervoso
    M = "M"  # Doenças do sistema endocrino
    N = "N"  # Doenças do sistema renal
    P = "P"  # Doenças do sistema pulmonar
    Q = "Q"  # Doenças do sistema digestivo
    R = "R"  # Doenças do sistema imunológico
    S = "S"  # Doenças do sistema hematológico
    T = "T"  # Doenças do sistema musculoesqueletico
    U = "U"  # Doenças do sistema digestivo
    V = "V"  # Doenças do sistema pulmonar
    W = "W"  # Doenças do sistema imunológico
    Y = "Y"  # Doenças do sistema hematológico
    Z = "Z"  # Doenças do sistema musculoesqueletico


class SOAPStatus(Enum):
    """Status SOAP - Método de Registro."""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
    REVIEWED = "REVIEWED"


class AppointmentStatus(Enum):
    """Status de Agendamento."""
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    NO_SHOW = "NO_SHOW"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    POSTPONED = "POSTPONED"


class VitalsType(Enum):
    """Tipos de sinais vitais."""
    BLOOD_PRESSURE = "blood_pressure"
    HEART_RATE = "heart_rate"
    RESPIRATORY_RATE = "respiratory_rate"
    TEMPERATURE = "temperature"
    OXYGEN_SATURATION = "oxygen_saturation"
    PULSE = "pulse"
    PAIN = "pain"
    WEIGHT = "weight"
    HEIGHT = "height"
    BMI = "bmi"
    GLUCOSE = "glucose"
    BLOOD_SUGAR = "blood_sugar"
    LIPIDS = "lipids"
    BLOOD_COAGULATION = "blood_coagulation"
    ELECTROLYTES = "electrolytes"
    BLOOD_COUNT = "blood_count"
    URINE_ANALYSIS = "urine_analysis"
    BLOOD_GAS = "blood_gas"
    LIVER_FUNCTION = "liver_function"
    KIDNEY_FUNCTION = "kidney_function"
    THYROID = "thyroid"
    PTH = "phosphorus"
    CALCIUM = "calcium"
    MAGNESIUM = "magnesium"
    POTASSIUM = "potassium"
    SODIUM = "sodium"
    CHLORIDE = "chloride"
    BICARBONATE = "bicarbonate"
    PH = "ph"
    ANION_GAP = "anion_gap"
    LACTATE = "lactate"
    CREATININE = "creatinine"
    GFR = "gfr"
    ALBUMIN = "albumin"
    GLOBULIN = "globulin"
    ALBUMIN_GLOBULIN_RATIO = "albumin_globulin_ratio"
    HEMOGLOBIN = "hemoglobin"
    HEMOCITOSIS = "hemocytosis"
    WHITE_BLOOD_COUNT = "white_blood_count"
    RED_BLOOD_COUNT = "red_blood_count"
    PLATELET_COUNT = "platelet_count"
    HEMATOCRIT = "hematocrit"
    BLOOD_VISCOSITY = "blood_viscosity"
    BLOOD_PLASMA = "blood_plasma"
    BLOOD_VOLUME = "blood_volume"
    BLOOD_OXIDATION = "blood_oxidation"
    BLOOD_REDUCTION = "blood_reduction"
    BLOOD_OXIDATION_REDUCTION = "blood_oxidation_reduction"
    BLOOD_OXIDATION_REDUCTION_RATIO = "blood_oxidation_reduction_ratio"
    BLOOD_OXIDATION_REDUCTION_RATIO_24H = "blood_oxidation_reduction_ratio_24h"
    BLOOD_OXIDATION_REDUCTION_RATIO_48H = "blood_oxidation_reduction_ratio_48h"
    BLOOD_OXIDATION_REDUCTION_RATIO_72H = "blood_oxidation_reduction_ratio_72h"
    BLOOD_OXIDATION_REDUCTION_RATIO_96H = "blood_oxidation_reduction_ratio_96h"
    BLOOD_OXIDATION_REDUCTION_RATIO_120H = "blood_oxidation_reduction_ratio_120h"
    BLOOD_OXIDATION_REDUCTION_RATIO_144H = "blood_oxidation_reduction_ratio_144h"
    BLOOD_OXIDATION_REDUCTION_RATIO_168H = "blood_oxidation_reduction_ratio_168h"
    BLOOD_OXIDATION_REDUCTION_RATIO_192H = "blood_oxidation_reduction_ratio_192h"
    BLOOD_OXIDATION_REDUCTION_RATIO_216H = "blood_oxidation_reduction_ratio_216h"
    BLOOD_OXIDATION_REDUCTION_RATIO_240H = "blood_oxidation_reduction_ratio_240h"
    BLOOD_OXIDATION_REDUCTION_RATIO_264H = "blood_oxidation_reduction_ratio_264h"
    BLOOD_OXIDATION_REDUCTION_RATIO_288H = "blood_oxidation_reduction_ratio_288h"
    BLOOD_OXIDATION_REDUCTION_RATIO_312H = "blood_oxidation_reduction_ratio_312h"
    BLOOD_OXIDATION_REDUCTION_RATIO_336H = "blood_oxidation_reduction_ratio_336h"
    BLOOD_OXIDATION_REDUCTION_RATIO_360H = "blood_oxidation_reduction_ratio_360h"
    BLOOD_OXIDATION_REDUCTION_RATIO_384H = "blood_oxidation_reduction_ratio_384h"
    BLOOD_OXIDATION_REDUCTION_RATIO_408H = "blood_oxidation_reduction_ratio_408h"
    BLOOD_OXIDATION_REDUCTION_RATIO_432H = "blood_oxidation_reduction_ratio_432h"
    BLOOD_OXIDATION_REDUCTION_RATIO_456H = "blood_oxidation_reduction_ratio_456h"
    BLOOD_OXIDATION_REDUCTION_RATIO_480H = "blood_oxidation_reduction_ratio_480h"
    BLOOD_OXIDATION_REDUCTION_RATIO_504H = "blood_oxidation_reduction_ratio_504h"
    BLOOD_OXIDATION_REDUCTION_RATIO_528H = "blood_oxidation_reduction_ratio_528h"
    BLOOD_OXIDATION_REDUCTION_RATIO_552H = "blood_oxidation_reduction_ratio_552h"
    BLOOD_OXIDATION_REDUCTION_RATIO_576H = "blood_oxidation_reduction_ratio_576h"
    BLOOD_OXIDATION_REDUCTION_RATIO_600H = "blood_oxidation_reduction_ratio_600h"
    BLOOD_OXIDATION_REDUCTION_RATIO_624H = "blood_oxidation_reduction_ratio_624h"
    BLOOD_OXIDATION_REDUCTION_RATIO_648H = "blood_oxidation_reduction_ratio_648h"
    BLOOD_OX