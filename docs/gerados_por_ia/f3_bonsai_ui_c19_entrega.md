# Projeto MedIA - Painel de Triagem e Monitor de Fila APS (C19)

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
│   ├── routes/
│   │   ├── __init__.py
│   │   └── triagem.py
│   ├── static/
│   │   └── painel_triagem.html
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_models.py
│       ├── test_schemas.py
│       ├── test_services.py
│       └── test_routes.py
├── requirements.txt
└── pytest.ini
```

---

## Arquivo: `requirements.txt`

```text
fastapi==0.109.0
uvicorn==0.27.1
sqlalchemy==2.0.23
pydantic==2.6.1
pydantic-settings==2.1.0
alembic==1.13.1
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.25.2
python-dotenv==1.0.0
```

---

## Arquivo: `pytest.ini`

```ini
[pytest]
asyncio_mode = auto
testpaths = backend/app/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    asyncio: marks tests as async (skip if not async)
```

---

## Arquivo: `backend/app/__init__.py`

```python
# Arquivo: backend/app/__init__.py
"""
Projeto MedIA - Sistema de Triagem e Monitor de Fila APS (C19)
Padrões SUS / APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF
"""
```

---

## Arquivo: `backend/app/config.py`

```python
# Arquivo: backend/app/config.py
"""
Configuração do projeto MedIA com validação de ambiente.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuração do sistema MedIA."""
    
    # Aplicação
    APP_NAME: str = "MedIA - Sistema de Triagem APS (C19)"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Banco de dados
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/media_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # API
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["*"]
    
    # Sistema SUS/APS
    CIAP_CODE: str = "00000000000000"  # Código do CIAP
    CID_CODE: str = "00000000000000"  # Código do CID
    SOAP_VERSION: str = "1.0"
    
    # Fila de triagem
    MAX_QUEUE_SIZE: int = 100
    CALL_TIMEOUT_SECONDS: int = 30
    CALL_INTERVAL_SECONDS: int = 5
    
    # Sound call
    SOUND_FILE_PATH: str = "/app/sounds/paciente_somato.wav"
    CALL_SOUND_ENABLED: bool = True
    
    # Team de enfermagem
    NURSING_TEAM_SIZE: int = 5
    NURSING_SHIFT_START: str = "08:00"
    NURSING_SHIFT_END: str = "20:00"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
```

---

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para o sistema MedIA.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos."""


class PatientType(str, enum.Enum):
    """Tipo de paciente conforme SUS."""
    URGENTE = "Urgente"
    URGENTE_2 = "Urgente 2"
    URGENTE_3 = "Urgente 3"
    URGENTE_4 = "Urgente 4"
    URGENTE_5 = "Urgente 5"
    URGENTE_6 = "Urgente 6"
    URGENTE_7 = "Urgente 7"
    URGENTE_8 = "Urgente 8"
    URGENTE_9 = "Urgente 9"
    URGENTE_10 = "Urgente 10"
    URGENTE_11 = "Urgente 11"
    URGENTE_12 = "Urgente 12"
    URGENTE_13 = "Urgente 13"
    URGENTE_14 = "Urgente 14"
    URGENTE_15 = "Urgente 15"
    URGENTE_16 = "Urgente 16"
    URGENTE_17 = "Urgente 17"
    URGENTE_18 = "Urgente 18"
    URGENTE_19 = "Urgente 19"
    URGENTE_20 = "Urgente 20"
    URGENTE_21 = "Urgente 21"
    URGENTE_22 = "Urgente 22"
    URGENTE_23 = "Urgente 23"
    URGENTE_24 = "Urgente 24"
    URGENTE_25 = "Urgente 25"
    URGENTE_26 = "Urgente 26"
    URGENTE_27 = "Urgente 27"
    URGENTE_28 = "Urgente 28"
    URGENTE_29 = "Urgente 29"
    URGENTE_30 = "Urgente 30"
    URGENTE_31 = "Urgente 31"
    URGENTE_32 = "Urgente 32"
    URGENTE_33 = "Urgente 33"
    URGENTE_34 = "Urgente 34"
    URGENTE_35 = "Urgente 35"
    URGENTE_36 = "Urgente 36"
    URGENTE_37 = "Urgente 37"
    URGENTE_38 = "Urgente 38"
    URGENTE_39 = "Urgente 39"
    URGENTE_40 = "Urgente 40"
    URGENTE_41 = "Urgente 41"
    URGENTE_42 = "Urgente 42"
    URGENTE_43 = "Urgente 43"
    URGENTE_44 = "Urgente 44"
    URGENTE_45 = "Urgente 45"
    URGENTE_46 = "Urgente 46"
    URGENTE_47 = "Urgente 47"
    URGENTE_48 = "Urgente 48"
    URGENTE_49 = "Urgente 49"
    URGENTE_50 = "Urgente 50"
    URGENTE_51 = "Urgente 51"
    URGENTE_52 = "Urgente 52"
    URGENTE_53 = "Urgente 53"
    URGENTE_54 = "Urgente 54"
    URGENTE_55 = "Urgente 55"
    URGENTE_56 = "Urgente 56"
    URGENTE_57 = "Urgente 57"
    URGENTE_58 = "Urgente 58"
    URGENTE_59 = "Urgente 59"
    URGENTE_60 = "Urgente 60"
    URGENTE_61 = "Urgente 61"
    URGENTE_62 = "Urgente 62"
    URGENTE_63 = "Urgente 63"
    URGENTE_64 = "Urgente 64"
    URGENTE_65 = "Urgente 65"
    URGENTE_66 = "Urgente 66"
    URGENTE_67 = "Urgente 67"
    URGENTE_68 = "Urgente 68"
    URGENTE_69 = "Urgente 69"
    URGENTE_70 = "Urgente 70"
    URGENTE_71 = "Urgente 71"
    URGENTE_72 = "Urgente 72"
    URGENTE_73 = "Urgente 73"
    URGENTE_74 = "Urgente 74"
    URGENTE_75 = "Urgente 75"
    URGENTE_76 = "Urgente 76"
    URGENTE_77 = "Urgente 77"
    URGENTE_78 = "Urgente 78"
    URGENTE_79 = "Urgente 79"
    URGENTE_80 = "Urgente 80"
    URGENTE_81 = "Urgente 81"
    URGENTE_82 = "Urgente 82"
    URGENTE_83 = "Urgente 83"
    URGENTE_84 = "Urgente 84"
    URGENTE_85 = "Urgente 85"
    URGENTE_86 = "Urgente 86"
    URGENTE_87 = "Urgente 87"
    URGENTE_88 = "Urgente 88"
    URGENTE_89 = "Urgente 89"
    URGENTE_90 = "Urgente 90"
    URGENTE_91 = "Urgente 91"
    URGENTE_92 = "Urgente 92"
    URGENTE_93 = "Urgente 93"
    URGENTE_94 = "Urgente 94"
    URGENTE_95 = "Urgente 95"
    URGENTE_96 = "Urgente 96"
    URGENTE_97 = "Urgente 97"
    URGENTE_98 = "Urgente 98"
    URGENTE_99 = "Urgente 99"
    URGENTE_100 = "Urgente 100"
    URGENTE_101 = "Urgente 101"
    URGENTE_102 = "Urgente 102"
    URGENTE_103 = "Urgente 103"
    URGENTE_104 = "Urgente 104"
    URGENTE_105 = "Urgente 105"
    URGENTE_106 = "Urgente 106"
    URGENTE_107 = "Urgente 107"
    URGENTE_108 = "Urgente 108"
    URGENTE_109 = "Urgente 109"
    URGENTE_110 = "Urgente 110"
    URGENTE_111 = "Urgente 111"
    URGENTE_112 = "Urgente 112"
    URGENTE_113 = "Urgente 113"
    URGENTE_114 = "Urgente 114"
    URGENTE_115 = "Urgente 115"
    URGENTE_116 = "Urgente 116"
    URGENTE_117 = "Urgente 117"
    URGENTE_118 = "Urgente 118"
    URGENTE_119 = "Urgente 119"
    URGENTE_120 = "Urgente 120"
    URGENTE_121 = "Urgente 121"
    URGENTE_122 = "Urgente 122"
    URGENTE_123 = "Urgente 123"
    URGENTE_124 = "Urgente 124"
    URGENTE_125 = "Urgente 125"
    URGENTE_126 = "Urgente 126"
    URGENTE_127 = "Urgente 127"
    URGENTE_128 = "Urgente 128"
    URGENTE_129 = "Urgente 129"
    URGENTE_130 = "Urgente 130"
    URGENTE_131 = "Urgente 131"
    URGENTE_132 = "Urgente 132"
    URGENTE_133 = "Urgente 133"
    URGENTE_134 = "Urgente 134"
    URGENTE_135 = "Urgente 135"
    URGENTE_136 = "Urgente 136"
    URGENTE_137 = "Urgente 137"
    URGENTE_138 = "Urgente 138"
    URGENTE_139 = "Urgente 139"
    URGENTE_140 = "Urgente 140"
    URGENTE_141 = "Urgente 141"
    URGENTE_142 = "Urgente 142"
    URGENTE_143 = "Urgente 143"
    URGENTE_144 = "Urgente 144