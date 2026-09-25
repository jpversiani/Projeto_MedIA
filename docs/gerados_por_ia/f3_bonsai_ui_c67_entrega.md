# Painel Visual da Triagem e Monitor de Fila APS (C67)

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
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── triagem.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── queue_service.py
│   │   └── static/
│   │       └── painel_triagem.html
│   ├── alembic/
│   │   ├── env.py
│   │   └── scripts/
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_models.py
│       ├── test_schemas.py
│       ├── test_routers.py
│       └── test_queue_service.py
├── requirements.txt
└── pytest.ini
```

---

## 1. `requirements.txt`

```text
# Arquivo: requirements.txt
fastapi==0.115.0
uvicorn==0.30.6
sqlalchemy==2.0.35
alembic==1.13.1
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1
pytest==8.3.3
pytest-asyncio==0.23.9
httpx==0.27.0
```

---

## 2. `pytest.ini`

```ini
# Arquivo: pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    asyncio: marks tests as async (skip if async not supported)
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
    DATABASE_URL: str = "postgresql://media:media@localhost:5432/media_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Aplicação
    APP_NAME: str = "MedIA - Sistema de Triagem e Monitor de Fila APS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "media-secret-key-change-in-production"

    # SUS/APS
    CIAP_CODE: str = "0000000000"  # Código CIAP do hospital
    CID_CODE: str = "0000000000"  # Código CID do hospital
    SUS_REGION: str = "01"  # Região SUS
    SUS_UF: str = "SP"  # Estado

    # Identificação
    IDENTIFICATION_METHOD: str = "SOAP"  # Método SOAP (Sistema de Identificação)
    IDENTITY_TYPE: str = "CNS"  # CNS ou CPF

    # Fila
    MAX_QUEUE_SIZE: int = 100
    CALL_INTERVAL: int = 5  # Intervalo entre chamadas sonoras (segundos)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

---

## 4. `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class IdentidadeCNS(Enum):
    """Identificação por CNS (Cadastro Nacional de Segurança)."""
    CNS = "CNS"


class IdentidadeCPF(Enum):
    """Identificação por CPF."""
    CPF = "CPF"


class TipoCidade(Enum):
    """Tipo de cidade conforme SUS."""
    URBANA = "URBANA"
    RURAL = "RURAL"
    INDÍGENO = "INDIGENO"
    REMOTO = "REMOTO"


class TipoAtendimento(Enum):
    """Tipo de atendimento conforme SUS."""
    URGENTE = "URGENTE"
    URGENTE_Muito = "URGENTE_Muito"
    URGENTE_Muito_Muito = "URGENTE_Muito_Muito"
    URGENTE_Muito_Muito_Muito = "URGENTE_Muito_Muito_Muito"
    URGENTE_Muito_Muito_Muito_Muito = "URGENTE_Muito_Muito_Muito_Muito"
    URGENTE_Muito_Muito_Muito_Muito_Muito = "URGENTE_Muito_Muito_Muito_Muito_Muito"
    URGENTE_Muito_Muito_Muito_Muito_Muito_Muito = "URGENTE_Muito_Muito_Muito_Muito_Muito_Muito"
    URGENTE_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito = "URGENTE_Muito_Muito_Muito_Muito_Muito_Muito_Muito"
    URGENTE_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito = "URGENTE_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito"
    URGENTE_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito = "URGENTE_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito"
    URGENTE_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito = "URGENTE_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito"
    URGENTE_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito = "URGENTE_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito_Muito