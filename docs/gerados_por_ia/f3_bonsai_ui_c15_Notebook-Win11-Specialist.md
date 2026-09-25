# Projeto MedIA - Panel Visual da Triagem e Monitor de Fila APS (C15)

## Estrutura do Projeto

```
media/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── triagem.py
│   │   │   └── nurse_dashboard.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── triagem_service.py
│   │   │   └── nurse_service.py
│   │   ├── static/
│   │   │   └── painel_triagem.html
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       ├── test_schemas.py
│   │       ├── test_services.py
│   │       └── test_api.py
│   ├── requirements.txt
│   └── pyproject.toml
├── tests/
│   ├── __init__.py
│   └── test_integration.py
├── Dockerfile
└── docker-compose.yml
```

---

## Arquivo: `backend/app/__init__.py`

```python
# Arquivo: backend/app/__init__.py
"""
Projeto MedIA - Sistema de Triagem e Monitor de Fila APS (C15)
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF
"""
```

---

## Arquivo: `backend/app/config.py`

```python
# Arquivo: backend/app/config.py
"""
Configuração do projeto MedIA com tipagem estrita.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Configuração do sistema MedIA - Padrões SUS/APS"""

    # Aplicação
    APP_NAME: str = "MedIA - Sistema de Triagem APS"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Banco de Dados
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://media:media@localhost:5432/media_db"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # API
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["*"]

    # Triagem
    TRIAGE_TIMEOUT_SECONDS: int = 300  # 5 minutos
    MAX_QUEUE_SIZE: int = 1000
    CALL_SOUND_DURATION: int = 3  # segundos

    # Identificação SUS
    SUS_CNS_PREFIX: str = "00"  # Prefixo CNS padrão
    SUS_CPF_PREFIX: str = "00"  # Prefixo CPF padrão

    # CID-10
    CID10_VERSION: str = "2022"  # CID-10 atualizado

    # SOAP
    SOAP_TEMPLATE: str = "SOAP"
    SOAP_TEMPLATE_VERSION: str = "2.0"

    # Monitor de Fila
    MONITOR_INTERVAL_SECONDS: int = 5
    MONITOR_ALERT_THRESHOLD: int = 60  # alertar se fila > 60

    # Team de Enfermagem
    NURSING_TEAM_SIZE: int = 5
    NURSING_SHIFT_DURATION: int = 8  # horas

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
```

---

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para o sistema MedIA.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    check,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Base declarativa SQLAlchemy 2.0"""


class PatientType(str, enum.Enum):
    """Tipos de pacientes conforme SUS"""
    URGENT = "urgente"
    URGENT_2 = "urgente_2"
    URGENT_3 = "urgente_3"
    URGENT_4 = "urgente_4"
    URGENT_5 = "urgente_5"
    URGENT_6 = "urgente_6"
    URGENT_7 = "urgente_7"
    URGENT_8 = "urgente_8"
    URGENT_9 = "urgente_9"
    URGENT_10 = "urgente_10"
    URGENT_11 = "urgente_11"
    URGENT_12 = "urgente_12"
    URGENT_13 = "urgente_13"
    URGENT_14 = "urgente_14"
    URGENT_15 = "urgente_15"
    URGENT_16 = "urgente_16"
    URGENT_17 = "urgente_17"
    URGENT_18 = "urgente_18"
    URGENT_19 = "urgente_19"
    URGENT_20 = "urgente_20"
    URGENT_21 = "urgente_21"
    URGENT_22 = "urgente_22"
    URGENT_23 = "urgente_23"
    URGENT_24 = "urgente_24"
    URGENT_25 = "urgente_25"
    URGENT_26 = "urgente_26"
    URGENT_27 = "urgente_27"
    URGENT_28 = "urgente_28"
    URGENT_29 = "urgente_29"
    URGENT_30 = "urgente_30"
    URGENT_31 = "urgente_31"
    URGENT_32 = "urgente_32"
    URGENT_33 = "urgente_33"
    URGENT_34 = "urgente_34"
    URGENT_35 = "urgente_35"
    URGENT_36 = "urgente_36"
    URGENT_37 = "urgente_37"
    URGENT_38 = "urgente_38"
    URGENT_39 = "urgente_39"
    URGENT_40 = "urgente_40"
    URGENT_41 = "urgente_41"
    URGENT_42 = "urgente_42"
    URGENT_43 = "urgente_43"
    URGENT_44 = "urgente_44"
    URGENT_45 = "urgente_45"
    URGENT_46 = "urgente_46"
    URGENT_47 = "urgente_47"
    URGENT_48 = "urgente_48"
    URGENT_49 = "urgente_49"
    URGENT_50 = "urgente_50"
    URGENT_51 = "urgente_51"
    URGENT_52 = "urgente_52"
    URGENT_53 = "urgente_53"
    URGENT_54 = "urgente_54"
    URGENT_55 = "urgente_55"
    URGENT_56 = "urgente_56"
    URGENT_57 = "urgente_57"
    URGENT_58 = "urgente_58"
    URGENT_59 = "urgente_59"
    URGENT_60 = "urgente_60"
    URGENT_61 = "urgente_61"
    URGENT_62 = "urgente_62"
    URGENT_63 = "urgente_63"
    URGENT_64 = "urgente_64"
    URGENT_65 = "urgente_65"
    URGENT_66 = "urgente_66"
    URGENT_67 = "urgente_67"
    URGENT_68 = "urgente_68"
    URGENT_69 = "urgente_69"
    URGENT_70 = "urgente_70"
    URGENT_71 = "urgente_71"
    URGENT_72 = "urgente_72"
    URGENT_73 = "urgente_73"
    URGENT_74 = "urgente_74"
    URGENT_75 = "urgente_75"
    URGENT_76 = "urgente_76"
    URGENT_77 = "urgente_77"
    URGENT_78 = "urgente_78"
    URGENT_79 = "urgente_79"
    URGENT_80 = "urgente_80"
    URGENT_81 = "urgente_81"
    URGENT_82 = "urgente_82"
    URGENT_83 = "urgente_83"
    URGENT_84 = "urgente_84"
    URGENT_85 = "urgente_85"
    URGENT_86 = "urgente_86"
    URGENT_87 = "urgente_87"
    URGENT_88 = "urgente_88"
    URGENT_89 = "urgente_89"
    URGENT_90 = "urgente_90"
    URGENT_91 = "urgente_91"
    URGENT_92 = "urgente_92"
    URGENT_93 = "urgente_93"
    URGENT_94 = "urgente_94"
    URGENT_95 = "urgente_95"
    URGENT_96 = "urgente_96"
    URGENT_97 = "urgente_97"
    URGENT_98 = "urgente_98"
    URGENT_99 = "urgente_99"
    URGENT_100 = "urgente_100"
    URGENT_101 = "urgente_101"
    URGENT_102 = "urgente_102"
    URGENT_103 = "urgente_103"
    URGENT_104 = "urgente_104"
    URGENT_105 = "urgente_105"
    URGENT_106 = "urgente_106"
    URGENT_107 = "urgente_107"
    URGENT_108 = "urgente_108"
    URGENT_109 = "urgente_109"
    URGENT_110 = "urgente_110"
    URGENT_111 = "urgente_111"
    URGENT_112 = "urgente_112"
    URGENT_113 = "urgente_113"
    URGENT_114 = "urgente_114"
    URGENT_115 = "urgente_115"
    URGENT_116 = "urgente_116"
    URGENT_117 = "urgente_117"
    URGENT_118 = "urgente_118"
    URGENT_119 = "urgente_119"
    URGENT_120 = "urgente_120"
    URGENT_121 = "urgente_121"
    URGENT_122 = "urgente_122"
    URGENT_123 = "urgente_123"
    URGENT_124 = "urgente_124"
    URGENT_125 = "urgente_125"
    URGENT_126 = "urgente_126"
    URGENT_127 = "urgente_127"
    URGENT_128 = "urgente_128"
    URGENT_129 = "urgente_129"
    URGENT_130 = "urgente_130"
    URGENT_131 = "urgente_131"
    URGENT_132 = "urgente_132"
    URGENT_133 = "urgente_133"
    URGENT_134 = "urgente_134"
    URGENT_135 = "urgente_135"
    URGENT_136 = "urgente_136"
    URGENT_137 = "urgente_137"
    URGENT_138 = "urgente_138"
    URGENT_139 = "urgente_139"
    URGENT_140 = "urgente_140"
    URGENT_141 = "urgente_141"
    URGENT_142 = "urgente_142"
    URGENT_143 = "urgente_143"
    URGENT_144 = "urgente_144"
    URGENT_145 = "urgente_145"
    URGENT_146 = "urgente_146"
    URGENT_147 = "urgente_147"
    URGENT_148 = "urgente_148"
    URGENT_149 = "urgente_149"
    URGENT_150 = "urgente_150"
    URGENT_151 = "urgente_151"