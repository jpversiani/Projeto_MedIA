# Dashboard de Monitoramento de Remessas do SISAB (C60)

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── routes.py
│   ├── static/
│   │   └── monitor_sisab.html
│   └── tests/
│       ├── __init__.py
│       └── test_monitor.py
├── requirements.txt
└── pytest.ini
```

---

## Arquivo: `backend/app/models.py`

```python:backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para remessas do SISAB (C60).
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    Boolean,
    Enum as SAEnum,
    ForeignKey,
    Index,
    UniqueConstraint,
    check,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    validates,
)


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos SQLAlchemy."""


class RemessaStatus(str, enum.Enum):
    """Estados da remessa conforme padrão SUS/APS."""
    CRIADA = "criada"
    EM_PROCESSAMENTO = "em_processamento"
    ENVIADA = "enviada"
   Falha = "falha"
    RETRANSMITA = "retransmitida"
    EXPIRA = "expira"


class RemessaType(str, enum.Enum):
    """Tipos de remessas no sistema SISAB."""
    SALARIO = "salario"
    BônUS = "bônus"
    PRIO = "prio"
    VARSAL = "varsal"
    REIMB = "reimb"
    OUTRO = "outro"


class RemessaTypeMapping:
    """Mapeamento CID-10 para tipos de remessa SISAB."""
    CID10_MAP: dict[str, RemessaType] = {
        "10000000000000000001": RemessaType.SALARIO,
        "10000000000000000002": RemessaType.BônUS,
        "10000000000000000003": RemessaType.PRIO,
        "10000000000000000004": RemessaType.VARSAL,
        "10000000000000000005": RemessaType.REIMB,
    }


class Remessa(Base):
    """
    Modelo de Remessa SISAB (C60).
    Identificação por CNS/CPF conforme padrão SUS/APS.
    """
    __tablename__ = "remessas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Identificação por CNS/CPF (padrão SUS/APS)
    identificador_cns: Mapped[str] = mapped_column(
        String(14), unique=True, nullable=False, index=True
    )
    identificador_cpf: Mapped[str] = mapped_column(
        String(11), nullable=True, index=True
    )
    # Tipo de remessa (CID-10 / CIAP-2)
    tipo_remessa: Mapped[RemessaType] = mapped_column(
        SAEnum(RemessaType, name="remessa_type_enum", create_type=False),
        nullable=False,
    )
    cid10: Mapped[str] = mapped_column(
        String(19), nullable=False, index=True
    )
    # Dados da remessa
    valor: Mapped[Decimal] = mapped_column(
        Float, nullable=False, check=check("valor >= 0")
    )
    status: Mapped[RemessaStatus] = mapped_column(
        SAEnum(RemessaStatus, name="remessa_status_enum", create_type=False),
        nullable=False, default=RemessaStatus.CRIADA,
    )
    # Dados de envio
    data_emissao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    data_envio: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    data_retransmissao: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    # SOAP / CIAP-2
    soap_id: Mapped[str] = mapped_column(
        String(50), nullable=True, index=True
    )
    ciap2_id: Mapped[str] = mapped_column(
        String(50), nullable=True, index=True
    )
    # Log de retransmissão
    retransmissao_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, check=check("retransmissao_count >= 0")
    )
    mensagem_error: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    # Metadados
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relações
    batches: Mapped[list["Batch"]] = relationship(
        back_populates="remessas", lazy="dynamic"
    )

    @validates("identificador_cns")
    def validate_cns(self, key: str, value: str) -> str:
        """Valida formato CNS (14 dígitos)."""
        if len(value) != 14:
            raise ValueError("CNS deve ter exatamente 14 dígitos")
        if not value.isdigit():
            raise ValueError("CNS deve conter apenas dígitos")
        return value

    @validates("identificador_cpf")
    def validate_cpf(self, key: str, value: str) -> str:
        """Valida formato CPF (11 dígitos)."""
        if value is None:
            return value
        if len(value) != 11:
            raise ValueError("CPF deve ter exatamente 11 dígitos")
        if not value.isdigit():
            raise ValueError("CPF deve conter apenas dígitos")
        return value

    @validates("cid10")
    def validate_cid10(self, key: str, value: str) -> str:
        """Valida formato CID-10 (19 dígitos)."""
        if len(value) != 19:
            raise ValueError("CID-10 deve ter exatamente 19 dígitos")
        if not value.isdigit():
            raise ValueError("CID-10 deve conter apenas dígitos")
        return value

    def __repr__(self) -> str:
        return (
            f"<Remessa(id={self.id}, CNS={self.identificador_cns}, "
            f"tipo={self.tipo_remessa.value}, valor={self.valor}, "
            f"status={self.status.value})>"
        )


class Batch(Base):
    """
    Lote de remessas para envio via SOAP/CIAP-2.
    """
    __tablename__ = "lotes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome_lote: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    status: Mapped[RemessaStatus] = mapped_column(
        SAEnum(RemessaStatus, name="lote_status_enum", create_type=False),
        nullable=False, default=RemessaStatus.CRIADA,
    )
    data_criação: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    data_envio: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    mensagem_error: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    remessas: Mapped[list[Remessa]] = relationship(
        back_populates="batches", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return (
            f"<Batch(id={self.id}, nome={self.nome_lote}, "
            f"status={self.status.value}, remessas={len(self.remessas)})>"
        )
```

---

## Arquivo: `backend/app/schemas.py`

```python:backend/app/schemas.py
"""
Esquemas Pydantic v2 para validação de dados.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)
from sqlalchemy import inspect


class RemessaBase(BaseModel):
    """Dados base para criação de remessa."""

    identificador_cns: str = Field(
        ..., min_length=14, max_length=14, description="CNS (14 dígitos)"
    )
    identificador_cpf: Optional[str] = Field(
        None, min_length=11, max_length=11, description="CPF (11 dígitos)"
    )
    tipo_remessa: str = Field(
        ..., description="Tipo de remessa (salario, bônus, prio, varsal, reimb, outro)"
    )
    cid10: str = Field(
        ..., min_length=19, max_length=19, description="CID-10 (19 dígitos)"
    )
    valor: Decimal = Field(
        ..., gt=0, description="Valor da remessa em reais"
    )
    soap_id: Optional[str] = Field(
        None, max_length=50, description="ID SOAP"
    )
    ciap2_id: Optional[str] = Field(
        None, max_length=50, description="ID CIAP-2"
    )

    @field_validator("identificador_cns")
    @classmethod
    def validate_cns(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("CNS deve conter apenas dígitos")
        return v

    @field_validator("identificador_cpf")
    @classmethod
    def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v.isdigit() or len(v) != 11):
            raise ValueError("CPF deve conter apenas dígitos e ter 11 dígitos")
        return v

    @field_validator("cid10")
    @classmethod
    def validate_cid10(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("CID-10 deve conter apenas dígitos")
        return v

    @field_validator("tipo_remessa")
    @classmethod
    def validate_tipo(cls, v: str) -> str:
        validos = {"salario", "bônus", "prio", "varsal", "reimb", "outro"}
        if v.lower() not in validos:
            raise ValueError(f"Tipo de remessa inválido. Deve ser um de: {validos}")
        return v.lower()


class RemessaCreate(RemessaBase):
    """Esquema para criação de remessa."""
    pass


class RemessaUpdate(BaseModel):
    """Esquema para atualização de remessa."""

    status: Optional[str] = Field(
        None, description="Status da remessa"
    )
    mensagem_error: Optional[str] = Field(
        None, description="Mensagem de erro"
    )
    retransmissao_count: Optional[int] = Field(
        None, ge=0, description="Contagem de retransmissões"
    )


class RemessaResponse(RemessaBase):
    """Esquema de resposta para remessa."""

    id: UUID
    status: str
    data_emissao: datetime
    data_envio: Optional[datetime]
    data_retransmissao: Optional[datetime]
    retransmissao_count: int
    mensagem_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BatchCreate(BaseModel):
    """Esquema para criação de lote."""

    nome_lote: str = Field(..., min_length=1, max_length=100)
    remessas_ids: list[UUID] = Field(..., min_length=1)


class BatchUpdate(BaseModel):
    """Esquema para atualização de lote."""

    status: Optional[str] = None
    mensagem_error: Optional[str] = None


class BatchResponse(BaseModel):
    """Esquema de resposta para lote."""

    id: UUID
    nome_lote: str
    status: str
    data_criação: datetime
    data_envio: Optional[datetime]
    mensagem_error: Optional[str]
    remessas: list[RemessaResponse]

    model_config = {"from_attributes": True}


class RemessaListResponse(BaseModel):
    """Esquema para lista de remessas."""

    remessas: list[RemessaResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BatchListResponse(BaseModel):
    """Esquema para lista de lotes."""

    lotes: list[BatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RetransmitBatchRequest(BaseModel):
    """Esquema para retransmissão de lote."""

    batch_id: UUID
    motivo: str = Field(..., min_length=1, max_length=500)
    forçar: bool = Field(
        default=False, description="Forçar retransmissão mesmo com erro"
    )


class BatchRetransmitResponse(BaseModel):
    """Esquema de resposta para retransmissão."""

    batch_id: UUID
    status: str
    mensagem: str
    remessas_retransmitidas: int
    remessas_em_error: int
    timestamp: datetime


class MonthlySendGraph(BaseModel):
    """Estrutura para gráfico mensual de remessas."""

    mes: str
    total_remessas: int
    total_valor: Decimal
    status_criada: int
    status_enviada: int
    status_falha: int
