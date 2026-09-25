"""Modelos de persistência da Mensageria e Alertas Preventivos (C32).

Registra, conforme o modelo do e-SUS APS (PEC):

1. ``MensagemPreventiva`` — lembretes automáticos de teleconsulta e mensagens
   de busca ativa (canais WhatsApp/SMS), com chave de idempotência para evitar
   envios duplicados e trilha de status (PENDENTE, ENVIADO, FALHA);
2. ``AlertaBuscaAtiva`` — alertas de busca ativa comunitária gerados pelo
   serviço de saúde para crianças com vacinas atrasadas (calendário do PNI,
   CIAP-2 ``A96`` / CID-10 ``Z23``) e para diabéticos sem acompanhamento há
   mais de 90 dias (CIAP-2 ``T90`` / CID-10 ``E11.9``).

Identificação do cidadão por CNS/CPF; código do cidadão opcional
(``cidadao_id``) quando o registro existir no cadastro do PEC.

Projeto MedIA — SUS/APS (Python 3.12, SQLAlchemy 2.0 tipado). Timestamps
armazenados em UTC sem fuso (``datetime.utcnow``) por convenção do projeto.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

if TYPE_CHECKING:  # pragma: no cover - apenas tipagem estática
    from datetime import datetime as _Datetime


def _utc_naive() -> _Datetime:
    """Retorna o instante atual em UTC, sem informação de fuso (SQLite)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class MensagemPreventiva(Base):
    """Mensagem preventiva enviada por WhatsApp/SMS (mock de gateway)."""

    __tablename__ = "mensagens_preventivas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chave_idempotencia: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True, index=True
    )

    # LEMBRETE_TELECONSULTA, BUSCA_ATIVA_VACINAL ou BUSCA_ATIVA_CRONICO
    tipo_alerta: Mapped[str] = mapped_column(String(40), nullable=False, index=True)

    # WHATSAPP ou SMS
    canal: Mapped[str] = mapped_column(String(20), nullable=False)
    telefone: Mapped[str] = mapped_column(String(20), nullable=False)
    nome_destinatario: Mapped[str] = mapped_column(String(200), nullable=False)

    cns: Mapped[str | None] = mapped_column(String(15), nullable=True, index=True)
    cpf: Mapped[str | None] = mapped_column(String(11), nullable=True, index=True)
    cidadao_id: Mapped[int | None] = mapped_column(
        ForeignKey("cidadaos.id"), nullable=True, index=True
    )
    teleconsulta_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )

    texto: Mapped[str] = mapped_column(Text, nullable=False)
    # PENDENTE, ENVIADO ou FALHA
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDENTE")
    erro: Mapped[str | None] = mapped_column(String(300), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utc_naive
    )
    enviado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AlertaBuscaAtiva(Base):
    """Alerta de busca ativa comunitária (vacinal ou crônico) para a UBS."""

    __tablename__ = "alertas_busca_ativa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chave_idempotencia: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True, index=True
    )

    # BUSCA_ATIVA_VACINAL ou BUSCA_ATIVA_CRONICO
    tipo: Mapped[str] = mapped_column(String(40), nullable=False, index=True)

    cidadao_id: Mapped[int | None] = mapped_column(
        ForeignKey("cidadaos.id"), nullable=True, index=True
    )
    cns: Mapped[str | None] = mapped_column(String(15), nullable=True, index=True)
    cpf: Mapped[str | None] = mapped_column(String(11), nullable=True, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)

    # ALTA, MEDIA ou BAIXA
    prioridade: Mapped[str] = mapped_column(String(20), nullable=False)

    # CIAP-2 da conduta (A96 imunização; T90 diabetes) e CID-10 associado
    ciap2: Mapped[str] = mapped_column(String(5), nullable=False)
    cid10: Mapped[str] = mapped_column(String(10), nullable=False)

    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    detalhe: Mapped[str | None] = mapped_column(Text, nullable=True)

    data_alerta: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utc_naive
    )
    resolvido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (Index("ix_alertas_busca_ativa_tipo_prioridade", "tipo", "prioridade"),)


__all__ = ["AlertaBuscaAtiva", "MensagemPreventiva"]
