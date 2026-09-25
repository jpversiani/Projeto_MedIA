# Dashboard de Monitoramento de Remessas do SISAB (C4)

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
│   ├── api/
│   │   ├── __init__.py
│   │   └── sisab.py
│   ├── static/
│   │   └── monitor_sisab.html
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_models.py
│       ├── test_schemas.py
│       ├── test_services.py
│       └── test_api.py
├── requirements.txt
└── pytest.ini
```

---

## Arquivo: `backend/requirements.txt`

```text
fastapi==0.109.0
uvicorn==0.27.1
sqlalchemy==2.0.23
pydantic==2.6.1
pydantic-settings==2.1.0
alembic==1.13.1
pytest==7.4.3
pytest-asyncio==0.23.5
httpx==0.27.0
python-dotenv==1.0.0
```

---

## Arquivo: `backend/pytest.ini`

```ini
[pytest]
asyncio_mode = auto
testpaths = backend/app/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    asyncio: marks tests as async (deselect with '-m "not asyncio"')
    integration: marks tests as integration tests
```

---

## Arquivo: `backend/app/config.py`

```python
# Arquivo: backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuração do sistema SISAB - C4."""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./sisab_c4.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # API
    API_TITLE: str = "SISAB C4 - Dashboard de Remessas"
    API_VERSION: str = "v1"
    API_DESCRIPTION: str = (
        "API para monitoramento de remessas de remessas do SUS/C4. "
        "Suporte a CIAP-2, CID-10, SOAP e identificação por CNS/CPF."
    )
    API_VERSION_PREFIX: str = "/api/v1"

    # SISAB C4
    SISAB_C4_API_URL: str = "https://sisab.c4.gov.br/api"
    SISAB_C4_API_KEY: Optional[str] = None
    SISAB_C4_TIMEOUT: int = 30

    # Dashboard
    REFRESH_INTERVAL_MS: int = 5000
    MAX_BATCH_SIZE: int = 1000

    # Sus/APS Patterns
    SUS_CNPJ_PATTERN: str = r"^\d{8}\.\d{9}[-\s]?\d{2}$"
    SUS_CPF_PATTERN: str = r"^\d{3}[-\s]?\d{2}[-\s]?\d{2}[-\s]?\d{2}$"
    SUS_CNS_PATTERN: str = r"^\d{11}$"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

---

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para o sistema SISAB C4.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, CNS/CPF.
"""
from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    UniqueConstraint,
    check,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    validates,
)
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos."""


class RemessaStatus(str, enum.Enum):
    """Status da remessa no sistema SISAB C4."""
    GERADA = "gerada"
    ENVIADA = "enviada"
    ENVIADA_COM_ERRO = "enviada_com erro"
    RETRANSMITA = "retransmitida"
    REJADA = "rejada"
    PENDING = "pendente"


class RemessaType(str, enum.Enum):
    """Tipo de remessa no SUS/C4."""
    CIAP_2 = "CIAP-2"
    CID_10 = "CID-10"
    SOAP = "SOAP"
    CUSTOM = "custom"


class Remessa(Base):
    """
    Modelo de Remessa no SISAB C4.
    Suporte a CIAP-2, CID-10, SOAP e identificação por CNS/CPF.
    """
    __tablename__ = "remessas"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="ID da remessa"
    )
    cnpj_sus: Mapped[Optional[str]] = mapped_column(
        String(14), nullable=True, comment="CNPJ do SUS"
    )
    cpf_sus: Mapped[Optional[str]] = mapped_column(
        String(11), nullable=True, comment="CPF do SUS"
    )
    cns_sus: Mapped[Optional[str]] = mapped_column(
        String(11), nullable=True, comment="CNS do SUS"
    )
    tipo_remessa: Mapped[RemessaType] = mapped_column(
        Enum(RemessaType), nullable=False, default=RemessaType.CIAP_2,
        comment="Tipo de remessa (CIAP-2, CID-10, SOAP)"
    )
    status: Mapped[RemessaStatus] = mapped_column(
        Enum(RemessaStatus), nullable=False, default=RemessaStatus.PENDING,
        comment="Status da remessa"
    )
    valor: Mapped[Decimal] = mapped_column(
        Float, nullable=False, comment="Valor da remessa",
        check=check(Decimal >= 0)
    )
    data_emissao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), comment="Data de emissão"
    )
    data_envio: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Data de envio"
    )
    data_retransmissao: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Data de retransmissão"
    )
    erro: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Descrição do erro"
    )
    mensagem: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Mensagem da remessa"
    )
    payload: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Payload da remessa"
    )
    lotes: Mapped[list["RemessaLote"]] = mapped_column(
        relationship("RemessaLote", back_populates="remessa", cascade="all, delete-orphan")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), comment="Criação"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now(),
        comment="Atualização"
    )

    __table_args__ = (
        Index("ix_remessas_status", status),
        Index("ix_remessas_data_emissao", data_emissao),
        Index("ix_remessas_cnpj", cnpj_sus),
        Index("ix_remessas_cpf", cpf_sus),
        Index("ix_remessas_cns", cns_sus),
        Index("ix_remessas_tipo", tipo_remessa),
        UniqueConstraint("cnpj_sus", "cpf_sus", "cns_sus", name="uq_remessa_sus"),
    )

    def __repr__(self) -> str:
        return (
            f"<Remessa(id={self.id}, status={self.status.value}, "
            f"valor={self.valor}, tipo={self.tipo_remessa.value})>"
        )


class RemessaLote(Base):
    """
    Lote de remessa para retransmissão.
    Agrupa remessas com erro para retransmissão em lote.
    """
    __tablename__ = "remessas_lotes"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="ID do lote"
    )
    remessa_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("remessas.id"), nullable=False, comment="ID da remessa"
    )
    remessa: Mapped["Remessa"] = mapped_column(
        relationship("Remessa", back_populates="lotes")
    )
    status: Mapped[RemessaStatus] = mapped_column(
        Enum(RemessaStatus), nullable=False, default=RemessaStatus.PENDING,
        comment="Status do lote"
    )
    erro: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Erro do lote"
    )
    mensagem: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Mensagem do lote"
    )
    payload: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Payload do lote"
    )
    data_retransmissao: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Data de retransmissão"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), comment="Criação"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now(),
        comment="Atualização"
    )

    __table_args__ = (
        Index("ix_remessas_lotes_remessa", remessa_id),
        Index("ix_remessas_lotes_status", status),
    )

    def __repr__(self) -> str:
        return (
            f"<RemessaLote(id={self.id}, remessa_id={self.remessa_id}, "
            f"status={self.status.value})>"
        )


class RemessaHistorico(Base):
    """
    Histórico de remessas para rastreamento.
    Mantém registro de todas as operações.
    """
    __tablename__ = "remessas_historico"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="ID histórico"
    )
    remessa_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("remessas.id"), nullable=False, comment="ID da remessa"
    )
    remessa: Mapped["Remessa"] = mapped_column(
        relationship("Remessa", back_populates="lotes")
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Ação realizada"
    )
    mensagem: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Mensagem da ação"
    )
    payload: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Payload da ação"
    )
    data_acao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), comment="Data da ação"
    )

    __table_args__ = (
        Index("ix_remessas_historico_remessa", remessa_id),
        Index("ix_remessas_historico_data", data_acao),
    )

    def __repr__(self) -> str:
        return (
            f"<RemessaHistorico(id={self.id}, remessa_id={self.remessa_id}, "
            f"action={self.action})>"
        )
```

---

## Arquivo: `backend/app/schemas.py`

```python
# Arquivo: backend/app/schemas.py
"""
Esquemas Pydantic v2 para validação de dados.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, CNS/CPF.
"""
from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, Text, Enum, Integer

from app.models import Remessa, RemessaLote, RemessaStatus, RemessaType


# --- Padrões de validação SUS/APS ---
SUS_CNPJ_PATTERN = re.compile(r"^\d{8}\.\d{9}[-\s]?\d{2}$")
SUS_CPF_PATTERN = re.compile(r"^\d{3}[-\s]?\d{2}[-\s]?\d{2}[-\s]?\d{2}$")
SUS_CNS_PATTERN = re.compile(r"^\d{11}$")


class RemessaCreate(BaseModel):
    """Esquema para criação de remessa."""
    model_config = ConfigDict(from_attributes=True)

    cnpj_sus: Optional[str] = Field(
        None,
        max_length=14,
        description="CNPJ do SUS"
    )
    cpf_sus: Optional[str] = Field(
        None,
        max_length=11,
        description="CPF do SUS"
    )
    cns_sus: Optional[str] = Field(
        None,
        max_length=11,
        description="CNS do SUS"
    )
    tipo_remessa: RemessaType = Field(
        RemessaType.CIAP_2,
        description="Tipo de remessa (CIAP-2, CID-10, SOAP)"
    )
    valor: Decimal = Field(
        gt=0,
        description="Valor da remessa"
    )
    mensagem: Optional[str] = Field(
        None,
        max_length=4096,
        description="Mensagem da remessa"
    )
    payload: Optional[str] = Field(
        None,
        max_length=8192,
        description="Payload da remessa"
    )

    @field_validator("cnpj_sus")
    @classmethod
    def validate_cnpj(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not SUS_CNPJ_PATTERN.match(v):
            raise ValueError("CNPJ inválido. Formato: XXX.XXXX.XXXX-XX")
        return v

    @field_validator("cpf_sus")
    @classmethod
    def validate_cpf(cls, v: Optional[str]) -> Optional