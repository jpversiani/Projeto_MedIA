"""Livro Caixa do médico (Carnê-Leão / DMED) com persistência real.

Antes, ``GET /financeiro-medico/livro-caixa/demonstrativo`` devolvia uma lista
de cinco consultas e três despesas *hardcoded* no código da rota. O médico via
um faturamento de R$ 1.780,00 que nunca existiu, com nomes e CPFs de pacientes
fictícios, e não havia como lançar nada de verdade. Além de inútil para
trabalhar, isso é risco de LGPD (dados inventados de titulares) e de
compliance fiscal (livro caixa é documento escritural).

Esta tabela guarda receita e despesa no mesmo livro, discriminadas por
``tipo``. Cada lançamento carrega o tenant (``estabelecimento_id``) e o
profissional, para o demonstrativo ser escopado e nunca misturar consultórios.
"""

from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.crypto import CampoProtegido, JsonProtegido
from app.core.database import Base


class TipoLancamento(str, enum.Enum):
    """Natureza do lançamento no livro caixa."""

    RECEITA = "RECEITA"
    DESPESA = "DESPESA"


class ModalidadeConsulta(str, enum.Enum):
    """Segregação exigida na apuração (consultório x home office)."""

    PRESENCIAL = "PRESENCIAL"
    TELEMEDICINA = "TELEMEDICINA"


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class LancamentoLivroCaixa(Base):
    """Uma linha do livro caixa: honorário recebido ou despesa dedutível."""

    __tablename__ = "lancamentos_livro_caixa"
    __table_args__ = (
        # Reenvio da finalização da consulta não escritura o honorário duas vezes.
        UniqueConstraint("chave_idempotencia", name="uq_livro_caixa_idempotencia"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Tenant + profissional responsável (escopo do demonstrativo).
    estabelecimento_id: Mapped[int | None] = mapped_column(
        ForeignKey("estabelecimentos.id"), nullable=True, index=True
    )
    profissional_id: Mapped[int | None] = mapped_column(
        ForeignKey("profissionais.id"), nullable=True, index=True
    )

    tipo: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # Competência fiscal: o mês a que o lançamento pertence (não a data do
    # registro). Permite lançar uma nota atrasada na competência correta.
    data_competencia: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    descricao: Mapped[str] = mapped_column(String(300), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Receita
    paciente_nome: Mapped[str | None] = mapped_column(String(200), nullable=True)
    paciente_cpf: Mapped[str | None] = mapped_column(CampoProtegido, nullable=True)
    modalidade: Mapped[str | None] = mapped_column(String(15), nullable=True)
    numero_recibo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metodo_pagamento: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Despesa
    categoria: Mapped[str | None] = mapped_column(String(40), nullable=True)
    dedutivel: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Origem: MANUAL (digitado) ou FLUXO_ATENDIMENTO (finalização da consulta).
    origem: Mapped[str] = mapped_column(String(30), default="MANUAL", nullable=False)
    chave_idempotencia: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_agora_utc)

    def __repr__(self) -> str:
        return (
            f"<LancamentoLivroCaixa(id={self.id}, tipo={self.tipo}, "
            f"valor={self.valor}, competencia={self.data_competencia})>"
        )
