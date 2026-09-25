"""Modelo de persistência dos atendimentos registrados em contingência offline (C29).

Atendimentos capturados no PEC enquanto a UBS estava sem conexão são
persistidos aqui ao serem sincronizados, garantindo rastreabilidade
(identificação por CNS/CPF), terminologia SUS/APS (CIAP-2/CID-10) e a
estrutura clínica pelo método SOAP.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StatusSincronizacao(str, enum.Enum):
    """Ciclo de vida do registro de contingência no servidor."""

    PENDENTE = "PENDENTE"      # registrado localmente, aguardando upload
    RECEBIDO = "RECEBIDO"      # confirmado pelo servidor (upload concluído)
    CONFLITO = "CONFLITO"      # divergência detectada (ex.: id_local duplicado com payload distinto)


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class AtendimentoOffline(Base):
    """Atendimento SOAP registrado offline e recebido pelo servidor."""

    __tablename__ = "atendimentos_offline"
    __table_args__ = (
        UniqueConstraint("id_local", name="uq_atendimento_offline_id_local"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Idempotência: UUID v4 gerado no cliente no momento do registro offline.
    id_local: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Identificação do cidadão conforme padrões SUS (CNS obrigatório; CPF opcional).
    cns_cidadao: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    cpf_cidadao: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)

    # Identificação do profissional (CNS) e do estabelecimento (CNES, 7 dígitos).
    profissional_cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    cnes_estabelecimento: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)

    # Momento em que o atendimento ocorreu na UBS (gerado no cliente).
    data_hora_atendimento: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Método SOAP (padrão APS).
    subjetivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objetivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avaliacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plano: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Terminologias SUS/APS: CIAP-2 (motivo de contato/problema) e CID-10 (diagnóstico).
    ciap2: Mapped[Optional[str]] = mapped_column(String(3), nullable=True, index=True)
    cid10: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, index=True)

    # Controle da sincronização.
    status: Mapped[StatusSincronizacao] = mapped_column(
        SAEnum(StatusSincronizacao, name="status_sincronizacao_enum"),
        nullable=False,
        default=StatusSincronizacao.RECEBIDO,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_agora_utc
    )
    recebido_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_agora_utc, onupdate=_agora_utc
    )

    def __repr__(self) -> str:  # pragma: no cover - representação técnica
        return f"AtendimentoOffline(id={self.id}, id_local='{self.id_local}', status={self.status.value})"


class SyncState(Base):
    """Estado do último timestamp de sincronização por dispositivo offline."""

    __tablename__ = "sync_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    last_sync_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_agora_utc
    )

