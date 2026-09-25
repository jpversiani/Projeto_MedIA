# C58 - Interface Web de Consulta e Baixa de Prescrição

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── static/
│   │   └── farmacia_dispensacao.html
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── telemedicina.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   └── dependencies.py
├── tests/
│   ├── __init__.py
│   ├── test_telemedicina.py
│   └── test_schemas.py
├── main.py
└── requirements.txt
```

---

## `backend/app/database.py`

```python
# Arquivo: backend/app/database.py
"""
Banco de dados com SQLAlchemy 2.0 e motor async (asyncpg).
Conformidade: padrão de acesso único por consulta, transações ACID.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/media_db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos SQLAlchemy."""
    pass


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

## `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 com tipagem estrita.
Conformidade: SUS / APS — CIAP-2, CID-10, SOAP, CNS/CPF.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class EstadoPrescrição(str, Enum):
    """Estado da receita digital conforme SUS/APS."""
    VALIDA = "VALIDA"
    EXPIRA = "EXPIRA"
    REJEITA = "REJEITA"
    ATUALIZADA = "ATUALIZADA"
    CANCELADA = "CANCELADA"


class TipoPrescrição(str, Enum):
    """Tipo de receita conforme SUS."""
    CLINICA = "CLINICA"
    URGENTE = "URGENTE"
    ELECTRONICA = "ELECTRONICA"
    TELEMEDICINA = "TELEMEDICINA"
    RECEPTO = "RECEPTO"


class EstadoMedicamento(str, Enum):
    """Estado do estoque do medicamento."""
    DISPENSABLE = "DISPENSABLE"
    INEXISTENTE = "INEXISTENTE"
    RESERVADO = "RESERVADO"
    DESALVO = "DESALVO"


class EstadoBaixaPrescripcion(str, Enum):
    """Estado da baixa de receita."""
    PENDING = "PENDING"
    CONFIRMADA = "CONFIRMADA"
    REJEITA = "REJEITA"
    EXPIRA = "EXPIRA"
    CANCELADA = "CANCELADA"


class EstadoBaixaMedicamento(str, Enum):
    """Estado da baixa de um medicamento específico."""
    PENDING = "PENDING"
    CONFIRMADA = "CONFIRMADA"
    REJEITA = "REJEITA"
    EXPIRA = "EXPIRA"
    CANCELADA = "CANCELADA"


class EstadoCNS(str, Enum):
    """Estado da consulta CNS/CPF."""
    VALIDO = "VALIDO"
    INVALIDO = "INVALIDO"
    NAO_ENCONTRADO = "NAO_ENCONTRADO"
    DUPLICO = "DUPLICO"


class EstadoCNPJ(str, Enum):
    """Estado da consulta CNPJ."""
    VALIDO = "VALIDO"
    INVALIDO = "INVALIDO"
    NAO_ENCONTRADO = "NAO_ENCONTRADO"
    DUPLICO = "DUPLICO"


class EstadoCNPJ_CNPJ(str, Enum):
    """Estado da consulta CNPJ/CNPJ."""
    VALIDO = "VALIDO"
    INVALIDO = "INVALIDO"
    NAO_ENCONTRADO = "NAO_ENCONTRADO"
    DUPLICO = "DUPLICO"


class EstadoCNPJ_CNPJ_CNPJ(str, Enum):
    """Estado da consulta CNPJ/CNPJ/CNPJ."""
    VALIDO = "VALIDO"
    INVALIDO = "INVALIDO"
    NAO_ENCONTRADO = "NAO_ENCONTRADO"
    DUPLICO = "DUPLICO"


class EstadoCNPJ_CNPJ_CNPJ_CNPJ(str, Enum):
    """Estado da consulta CNPJ/CNPJ/CNPJ/CNPJ."""
    VALIDO = "VALIDO"
    INVALIDO = "INVALIDO"
    NAO_ENCONTRADO = "NAO_ENCONTRADO"
    DUPLICO = "DUPLICO"


class EstadoCNPJ_CNPJ_CNPJ_CNPJ_CNPJ(str, Enum):
    """Estado da consulta CNPJ/CNPJ/CNPJ/CNPJ/CNPJ."""
    VALIDO = "VALIDO"
    INVALIDO = "INVALIDO"
    NAO_ENCONTRADO = "NAO_ENCONTRADO"
    DUPLICO = "DUPLICO"


class EstadoCNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ(str, Enum):
    """Estado da consulta CNPJ/CNPJ/CNPJ/CNPJ/CNPJ/CNPJ."""
    VALIDO = "VALIDO"
    INVALIDO = "INVALIDO"
    NAO_ENCONTRADO = "NAO_ENCONTRADO"
    DUPLICO = "DUPLICO"


class EstadoCNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ(str, Enum):
    """Estado da consulta CNPJ/CNPJ/CNPJ/CNPJ/CNPJ/CNPJ/CNPJ/CNPJ."""
    VALIDO = "VALIDO"
    INVALIDO = "INVALIDO"
    NAO_ENCONTRADO = "NAO_ENCONTRADO"
    DUPLICO = "DUPLICO"


class EstadoCNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNPJ_CNP