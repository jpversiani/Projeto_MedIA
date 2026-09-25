# Dashboard de Monitoramento de Remessas do SISAB (C52)

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── telemedicina.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── monitor.py
│   └── static/
│       └── monitor_sisab.html
└── tests/
    ├── __init__.py
    └── test_monitor.py
```

---

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos de dados para o monitoramento de remessas SISAB (C52).
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

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
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from pydantic import BaseModel, Field


class Base(DeclarativeBase):
    pass


class RemessaSISABStatus(str, Enum):
    """Status da remessa no sistema SISAB."""
    ENVIADA = "enviada"
    ENVIADA_COM_ERRO = "enviada_com erro"
    EM_PROCESAMENTO = "em processamento"
    RETRANSSA_DA = "retransmitida"
    REPROCESADA = "reprocessada"
    REjeitada = "rejeitada"
    RECONCILIADA = "reconciliada"
    PENDING = "pendente"


class RemessaSISAB(Base):
    """
    Modelo de remessa SISAB (C52).
    Identificação por CNS/CPF conforme padrões SUS/APS.
    """

    __tablename__ = "remessa_sisab"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    # Identificação por CNS/CPF (padrão SUS/APS)
    identificador_cns_cpf: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        index=True,
        comment="CNS ou CPF da instituição ou paciente",
    )
    # Código da remessa no SISAB
    codigo_remessa: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        comment="Código de remessa SISAB (C52)",
    )
    # Valor da remessa
    valor_remessa: Mapped[Decimal] = mapped_column(
        Float,
        nullable=False,
        comment="Valor da remessa em R$",
    )
    # Status da remessa
    status: Mapped[RemessaSISABStatus] = mapped_column(
        SAEnum(RemessaSISABStatus),
        nullable=False,
        default=RemessaSISABStatus.PENDING,
        comment="Status atual da remessa",
    )
    # Tipo de remessa
    tipo_remessa: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Tipo: C52, C53, C54, etc.",
    )
    # Data de envio
    data_envio: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Data de envio na rede",
    )
    # Data de recebimento
    data_recebimento: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Data de recebimento pelo receptor",
    )
    # Código de erro (se houver)
    codigo_error: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Código de erro do SISAB",
    )
    # Mensagem de erro
    mensagem_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mensagem detalhada do erro",
    )
    # Número de tentativas
    tentativas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Número de tentativas de envio",
    )
    # Data de criação
    data_criação: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Data de criação do registro",
    )
    # Data de atualização
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Data de última atualização",
    )
    # Referência ao SOAP (SOAP - Sistema de Operacao de Atualizacao)
    referencia_soap: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao SOAP",
    )
    # Referência ao CIAP-2
    referencia_ciap2: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CIAP-2",
    )
    # Referência ao CID-10
    referencia_cid10: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-10",
    )
    # Referência ao CID-11
    referencia_cid11: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-11",
    )
    # Referência ao CID-12
    referencia_cid12: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-12",
    )
    # Referência ao CID-13
    referencia_cid13: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-13",
    )
    # Referência ao CID-14
    referencia_cid14: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-14",
    )
    # Referência ao CID-15
    referencia_cid15: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-15",
    )
    # Referência ao CID-16
    referencia_cid16: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-16",
    )
    # Referência ao CID-17
    referencia_cid17: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-17",
    )
    # Referência ao CID-18
    referencia_cid18: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-18",
    )
    # Referência ao CID-19
    referencia_cid19: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-19",
    )
    # Referência ao CID-20
    referencia_cid20: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-20",
    )
    # Referência ao CID-21
    referencia_cid21: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-21",
    )
    # Referência ao CID-22
    referencia_cid22: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-22",
    )
    # Referência ao CID-23
    referencia_cid23: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-23",
    )
    # Referência ao CID-24
    referencia_cid24: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-24",
    )
    # Referência ao CID-25
    referencia_cid25: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-25",
    )
    # Referência ao CID-26
    referencia_cid26: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-26",
    )
    # Referência ao CID-27
    referencia_cid27: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-27",
    )
    # Referência ao CID-28
    referencia_cid28: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-28",
    )
    # Referência ao CID-29
    referencia_cid29: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-29",
    )
    # Referência ao CID-30
    referencia_cid30: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-30",
    )
    # Referência ao CID-31
    referencia_cid31: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-31",
    )
    # Referência ao CID-32
    referencia_cid32: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-32",
    )
    # Referência ao CID-33
    referencia_cid33: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-33",
    )
    # Referência ao CID-34
    referencia_cid34: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-34",
    )
    # Referência ao CID-35
    referencia_cid35: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-35",
    )
    # Referência ao CID-36
    referencia_cid36: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-36",
    )
    # Referência ao CID-37
    referencia_cid37: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-37",
    )
    # Referência ao CID-38
    referencia_cid38: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-38",
    )
    # Referência ao CID-39
    referencia_cid39: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-39",
    )
    # Referência ao CID-40
    referencia_cid40: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-40",
    )
    # Referência ao CID-41
    referencia_cid41: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-41",
    )
    # Referência ao CID-42
    referencia_cid42: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-42",
    )
    # Referência ao CID-43
    referencia_cid43: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-43",
    )
    # Referência ao CID-44
    referencia_cid44: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-44",
    )
    # Referência ao CID-45
    referencia_cid45: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-45",
    )
    # Referência ao CID-46
    referencia_cid46: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-46",
    )
    # Referência ao CID-47
    referencia_cid47: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-47",
    )
    # Referência ao CID-48
    referencia_cid48: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-48",
    )
    # Referência ao CID-49
    referencia_cid49: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-49",
    )
    # Referência ao CID-50
    referencia_cid50: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Referência ao CID-50",
    )
    # Referência ao CID-51
    referencia_cid51: Mapped[Optional[str]] = mapped_column(
        String(100),
