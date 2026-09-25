# Dashboard de Monitoramento de Remessas do SISAB (C20)

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── api.py
│   ├── dependencies.py
│   ├── static/
│   │   └── monitor_sisab.html
│   └── config.py
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_models.py
│   └── conftest.py
├── requirements.txt
└── pyproject.toml
```

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para remessas do SISAB (C20).
Padrões SUS/APS: CIAP-2, CID-10, SOAP, CNS/CPF.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
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
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarativa para modelos SQLAlchemy 2.0."""


class RemittanceStatus(str, Enum):
    """Estados da remessa conforme padrão SUS/APS."""
    GERADA = "gerada"
    ENVIADA = "enviada"
    RECEBIDA = "recebida"
    REJAGADA = "rejeitada"
    ERRO = "erro"
    RETRANSMISA = "retransmissão"
    CONCLUDA = "concluda"


class RemittanceMethod(str, Enum):
    """Métodos de remessa SISAB."""
    C20 = "c20"
    C21 = "c21"
    C22 = "c22"
    C23 = "c23"
    C24 = "c24"
    C25 = "c25"


class RemittanceType(str, Enum):
    """Tipos de remessas."""
    SALARIO = "salario"
    ALIMENTO = "alimentacao"
    MEDICINA = "medicina"
    OUTROS = "outros"


class Remittance(Base):
    """
    Modelo de remessa SISAB com padrão SUS/APS.
    Identificação por CNS/CPF e método SOAP.
    """

    __tablename__ = "remessas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cnpj: Mapped[str] = mapped_column(String(14), nullable=False, index=True)
    cnpj_formatado: Mapped[str] = mapped_column(String(17), nullable=False)
    cnpj_verificado: Mapped[bool] = mapped_column(Boolean, default=True)

    # Identificação SUS/APS
    cns: Mapped[str] = mapped_column(String(11), nullable=False, index=True)
    cns_formatado: Mapped[str] = mapped_column(String(11), nullable=False)
    cpf: Mapped[str] = mapped_column(String(11), nullable=False, index=True)
    cpf_formatado: Mapped[str] = mapped_column(String(11), nullable=False)

    # Dados da remessa
    valor: Mapped[Decimal] = mapped_column(Float, nullable=False)
    valor_formado: Mapped[str] = mapped_column(String(20), nullable=False)
    moeda: Mapped[str] = mapped_column(String(3), default="BRL")

    # Método de remessa
    metodo: Mapped[RemittanceMethod] = mapped_column(
        SAEnum(RemittanceMethod), nullable=False, default=RemittanceMethod.C20
    )
    tipo_remessa: Mapped[RemittanceType] = mapped_column(
        SAEnum(RemittanceType), nullable=False, default=RemittanceType.SALARIO
    )

    # Estado e timestamps
    status: Mapped[RemittanceStatus] = mapped_column(
        SAEnum(RemittanceStatus), nullable=False, default=RemittanceStatus.GERADA
    )
    status_historico: Mapped[str] = mapped_column(Text, nullable=True)

    # Dados SOAP/CID-10
    cid_10: Mapped[str] = mapped_column(String(10), nullable=False)
    cid_10_formatado: Mapped[str] = mapped_column(String(10), nullable=False)
    soap_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    soap_status: Mapped[str] = mapped_column(String(10), nullable=True)
    soap_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Dados de envio
    data_emissao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    data_envio: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    data_rececao: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    data_rejeicao: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Dados de erro
    erro: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    erro_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mensagem_error: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Batch de retransmissão
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    batch_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadados
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Relações
    batches: Mapped[list["BatchStatus"]] = mapped_column(
        relationship("BatchStatus", back_populates="remessas", lazy="dynamic")
    )

    def __repr__(self) -> str:
        return f"<Remittance(id={self.id}, cnpj={self.cnpj}, valor={self.valor}, status={self.status})>"


class BatchStatus(Base):
    """
    Modelo para rastreamento de batches de retransmissão.
    """

    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    batch_name: Mapped[str] = mapped_column(String(100), nullable=False)
    batch_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[RemittanceStatus] = mapped_column(
        SAEnum(RemittanceStatus), nullable=False, default=RemittanceStatus.GERADA
    )
    remessa_ids: Mapped[list[uuid.UUID]] = mapped_column(
        Text, nullable=False, default="[]"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)

    remessas: Mapped[list[Remittance]] = mapped_column(
        relationship("Remittance", back_populates="batches", lazy="dynamic")
    )

    def __repr__(self) -> str:
        return f"<Batch(id={self.id}, name={self.batch_name}, status={self.status})>"


class RemittanceHistory(Base):
    """
    Modelo de histórico de estados das remessas.
    Mantém audit trail conforme padrão SUS/APS.
    """

    __tablename__ = "remessas_historico"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    remessa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    status: Mapped[RemittanceStatus] = mapped_column(
        SAEnum(RemittanceStatus), nullable=False
    )
    status_historico: Mapped[str] = mapped_column(Text, nullable=False)
    mensagem: Mapped[str] = mapped_column(String(500), nullable=True)
    data_evento: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )

    remessa: Mapped[Remittance] = mapped_column(
        relationship("Remittance", back_populates="historia")
    )

    def __repr__(self) -> str:
        return f"<History(id={self.id}, remessa={self.remessa_id}, status={self.status})>"


class BatchRetransmission(Base):
    """
    Modelo para rastreamento de retransmissões de batches com erro.
    """

    __tablename__ = "batch_retransmissao"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    remessa_ids: Mapped[list[uuid.UUID]] = mapped_column(
        Text, nullable=False, default="[]"
    )
    status: Mapped[RemittanceStatus] = mapped_column(
        SAEnum(RemittanceStatus), nullable=False, default=RemittanceStatus.GERADA
    )
    erro: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mensagem_error: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    data_tentativa: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    max_tentativas: Mapped[int] = mapped_column(Integer, default=5)
    tentativas: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    batch: Mapped[BatchStatus] = mapped_column(
        relationship("BatchStatus", back_populates="retransmissao")
    )

    def __repr__(self) -> str:
        return f"<BatchRetransmission(id={self.id}, batch={self.batch_id}, status={self.status})>"


class BatchRetransmission.retransmissao:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchStatus.retransmissao:
    """Relação inversa para BatchStatus."""
    pass


class BatchStatus.retransmissao:
    """Relação inversa para BatchStatus."""
    pass


class Remittance.historia:
    """Relação inversa para Remittance."""
    pass


class Remittance.history:
    """Relação inversa para Remittance."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetransmission.batch:
    """Relação inversa para BatchRetransmission."""
    pass


class BatchRetrans