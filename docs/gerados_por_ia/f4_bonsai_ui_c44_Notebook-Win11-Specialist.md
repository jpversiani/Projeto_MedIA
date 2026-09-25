# Dashboard de Monitoramento de Remessas do SISAB (C44)

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
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints.py
│   │   ├── websocket.py
│   │   └── health.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── remessa_service.py
│   │   └── notification_service.py
│   ├── static/
│   │   └── monitor_sisab.html
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_models.py
│       ├── test_schemas.py
│       ├── test_endpoints.py
│       ├── test_services.py
│       └── test_integration.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Arquivo: `backend/app/__init__.py`

```python
# Arquivo: backend/app/__init__.py
"""
Aplicação Backend para Monitoramento de Remessas SISAB (C44).

Padrões: SUS/APS, CIAP-2, CID-10, SOAP, identificação por CNS/CPF.
"""
```

---

## Arquivo: `backend/app/config.py`

```python
# Arquivo: backend/app/config.py
"""
Configuração da aplicação com validação de tipos e valores.
"""

from pydantic import BaseModel, Field
from typing import Optional


class Settings(BaseModel):
    """Configuração da aplicação SISAB."""

    # Aplicação
    app_name: str = "SISAB Monitor Dashboard"
    app_version: str = "1.0.0"
    debug: bool = False

    # Banco de Dados
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sisab_monitor"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30

    # API
    api_prefix: str = "/api/v1"
    websocket_url: str = "/ws/monitor"
    cors_origins: list[str] = ["*"]

    # Remessas
    default_batch_size: int = 100
    max_batch_size: int = 500
    retry_attempts: int = 3
    retry_delay_seconds: int = 60

    # Notificações
    notification_enabled: bool = True
    notification_email: Optional[str] = None

    # Limites
    max_receivers_per_batch: int = 1000
    max_amount_per_receiver: float = 100000.00

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

---

## Arquivo: `backend/app/database.py`

```python
# Arquivo: backend/app/database.py
"""
Configuração do banco de dados com SQLAlchemy 2.0 e asyncpg.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos."""


engine = create_async_engine(
    settings.database_url,
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
    pool_timeout=settings.pool_timeout,
    echo=settings.debug,
)


async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """Dependência assíncrona para sessão de banco de dados."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

---

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para remessas SISAB (C44).

Padrões: SUS/APS, CIAP-2, CID-10, identificação por CNS/CPF.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, mapped_column

from app.database import Base


class RemessaStatus(str, Enum):
    """Estados da remessa."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class LoteStatus(str, Enum):
    """Estados do lote de remessas."""
    CREATING = "creating"
    VALIDATING = "validating"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class Remessa(Base):
    """
    Modelo de remessa individual.
    
    Identificação por CNS/CPF conforme padrão SUS/APS.
    """

    __tablename__ = "remessas"

    id = mapped_column(UUID(as_uuid=True), primary_key=True)
    cns = mapped_column(String(15), unique=True, nullable=False, index=True)
    cpf = mapped_column(String(14), unique=True, nullable=False, index=True)
    nome = mapped_column(String(100), nullable=False)
    endereco = mapped_column(Text, nullable=True)
    conta_banco = mapped_column(String(50), nullable=True)
    conta_banco_num = mapped_column(String(50), nullable=True)
    valor = mapped_column(Float, nullable=False)
    status = mapped_column(String(20), nullable=False, default=RemessaStatus.PENDING.value)
    mensagem = mapped_column(Text, nullable=True)
    mensagem_error = mapped_column(Text, nullable=True)
    mensagem_sisab = mapped_column(Text, nullable=True)
    mensagem_sisab_error = mapped_column(Text, nullable=True)
    mensagem_sisab_error_2 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_3 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_4 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_5 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_6 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_7 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_8 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_9 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_10 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_11 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_12 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_13 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_14 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_15 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_16 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_17 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_18 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_19 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_20 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_21 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_22 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_23 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_24 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_25 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_26 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_27 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_28 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_29 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_30 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_31 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_32 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_33 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_34 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_35 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_36 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_37 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_38 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_39 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_40 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_41 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_42 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_43 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_44 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_45 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_46 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_47 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_48 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_49 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_50 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_51 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_52 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_53 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_54 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_55 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_56 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_57 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_58 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_59 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_60 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_61 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_62 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_63 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_64 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_65 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_66 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_67 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_68 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_69 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_70 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_71 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_72 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_73 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_74 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_75 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_76 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_77 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_78 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_79 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_80 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_81 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_82 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_83 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_84 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_85 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_86 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_87 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_88 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_89 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_90 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_91 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_92 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_93 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_94 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_95 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_96 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_97 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_98 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_99 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_100 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_101 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_102 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_103 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_104 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_105 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_106 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_107 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_108 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_109 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_110 = mapped_column(Text, nullable=True)
    mensagem_sisab_error_111 = mapped_column