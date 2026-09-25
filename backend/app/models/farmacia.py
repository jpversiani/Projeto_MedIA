"""Modelos de domínio da Dispensação Farmacêutica (C34 — SUS/APS).

Ciclo da receita digital na farmácia da APS: a receita emitida (com hash
de integridade lido do QR Code), seus itens prescritos e as baixas
(dispensações) totais ou fracionadas, com trilha de auditoria do
farmacêutico (CNS/CPF) e do estabelecimento dispensador (CNES).

Estados da receita: ``EMITIDA``, ``PARCIALMENTE_DISPENSADA``,
``DISPENSADA`` e ``CANCELADA``. O saldo remanescente de cada item é
derivable de ``quantidade_prescrita - quantidade_dispensada``.

Projeto MedIA — SUS/APS (Python 3.12, SQLAlchemy 2.0 tipado).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

STATUS_EMITIDA = "EMITIDA"
STATUS_PARCIALMENTE_DISPENSADA = "PARCIALMENTE_DISPENSADA"
STATUS_DISPENSADA = "DISPENSADA"
STATUS_CANCELADA = "CANCELADA"

TIPO_DISPENSACAO_TOTAL = "TOTAL"
TIPO_DISPENSACAO_FRACIONADA = "FRACIONADA"


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class Receita(Base):
    """Receita digital emitida na APS, identificada pelo hash do QR Code.

    O ``codigo_hash`` (SHA-256 em hex minúsculo) é o conteúdo escaneado do
    QR Code e deve ser recalculável a partir do conteúdo clínico registrado
    (cidadão, episódio CID-10/CIAP-2, prescritor, emissão e itens), permitindo
    à farmácia detectar adulteração antes da baixa.
    """

    __tablename__ = "receitas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    # Identificação SUS do paciente (CNS obrigatório; CPF complementar)
    cns_paciente: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    cpf_paciente: Mapped[str | None] = mapped_column(String(11), nullable=True)

    # Episódio clínico conforme terminologias SUS/APS (CID-10 e/ou CIAP-2)
    cid10: Mapped[str | None] = mapped_column(String(7), nullable=True)
    ciap2: Mapped[str | None] = mapped_column(String(3), nullable=True)

    # Prescritor (trilha de auditoria da emissão)
    prescritor_nome: Mapped[str] = mapped_column(String(200), nullable=False)
    prescritor_cns: Mapped[str] = mapped_column(String(15), nullable=False)
    prescritor_registro: Mapped[str] = mapped_column(String(30), nullable=False)

    # CNES da unidade emissora e vigência da prescrição
    unidade_cnes: Mapped[str] = mapped_column(String(7), nullable=False)
    data_emissao: Mapped[datetime] = mapped_column(
        DateTime, default=_agora_utc, nullable=False
    )
    data_validade: Mapped[date] = mapped_column(Date, nullable=False)

    # EMITIDA, PARCIALMENTE_DISPENSADA, DISPENSADA ou CANCELADA
    status: Mapped[str] = mapped_column(String(30), default=STATUS_EMITIDA, nullable=False)
    observacoes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_agora_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_agora_utc, onupdate=_agora_utc
    )

    itens: Mapped[list["ReceitaItem"]] = relationship(
        back_populates="receita",
        cascade="all, delete-orphan",
        order_by="ReceitaItem.id",
    )
    dispensacoes: Mapped[list["Dispensacao"]] = relationship(
        back_populates="receita",
        cascade="all, delete-orphan",
        order_by="Dispensacao.id",
    )

    def __repr__(self) -> str:
        return f"<Receita(id={self.id}, hash={self.codigo_hash[:8]}…, status={self.status})>"


class ReceitaItem(Base):
    """Item prescrito na receita: fármaco, dosagem e quantidade autorizada.

    ``quantidade_dispensada`` acumula as baixas fracionadas; o saldo
    remanescente é ``quantidade_prescrita - quantidade_dispensada``.
    """

    __tablename__ = "receita_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receita_id: Mapped[int] = mapped_column(
        ForeignKey("receitas.id"), nullable=False, index=True
    )

    medicamento: Mapped[str] = mapped_column(String(200), nullable=False)
    dosagem: Mapped[str] = mapped_column(String(100), nullable=False)
    posologia: Mapped[str] = mapped_column(String(300), nullable=False)
    quantidade_prescrita: Mapped[int] = mapped_column(Integer, nullable=False)
    quantidade_dispensada: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    receita: Mapped["Receita"] = relationship(back_populates="itens")
    baixas: Mapped[list["DispensacaoItem"]] = relationship(
        back_populates="receita_item", cascade="all, delete-orphan"
    )

    @property
    def saldo_remanescente(self) -> int:
        """Quantidade ainda não dispensada do item."""
        return self.quantidade_prescrita - self.quantidade_dispensada

    def __repr__(self) -> str:
        return (
            f"<ReceitaItem(id={self.id}, medicamento={self.medicamento}, "
            f"saldo={self.saldo_remanescente})>"
        )


class Dispensacao(Base):
    """Evento de baixa (dispensação) de uma receita na farmácia.

    ``tipo`` TOTAL encerra o saldo de todos os itens da receita;
    FRACIONADA registra baixa parcial, preservando o saldo remanescente.
    ``chave_idempotencia`` (opcional) evita duplicidade de registro da mesma
    operação em reenvio de rede no ponto de atendimento.
    """

    __tablename__ = "dispensacoes"
    __table_args__ = (
        UniqueConstraint("chave_idempotencia", name="uq_dispensacao_idempotencia"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receita_id: Mapped[int] = mapped_column(
        ForeignKey("receitas.id"), nullable=False, index=True
    )

    # TOTAL ou FRACIONADA
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)

    # Auditoria do farmacêutico dispensador (identificação SUS)
    farmaceutico_nome: Mapped[str] = mapped_column(String(200), nullable=False)
    farmaceutico_cns: Mapped[str] = mapped_column(String(15), nullable=False)
    farmaceutico_cpf: Mapped[str | None] = mapped_column(String(11), nullable=True)

    # CNES da farmácia/unidade dispensadora
    unidade_cnes: Mapped[str] = mapped_column(String(7), nullable=False)

    data_dispensacao: Mapped[datetime] = mapped_column(
        DateTime, default=_agora_utc, nullable=False
    )
    observacoes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    chave_idempotencia: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )

    receita: Mapped["Receita"] = relationship(back_populates="dispensacoes")
    itens: Mapped[list["DispensacaoItem"]] = relationship(
        back_populates="dispensacao",
        cascade="all, delete-orphan",
        order_by="DispensacaoItem.id",
    )

    def __repr__(self) -> str:
        return (
            f"<Dispensacao(id={self.id}, receita_id={self.receita_id}, "
            f"tipo={self.tipo})>"
        )


class DispensacaoItem(Base):
    """Baixa de um item da receita em um evento de dispensação."""

    __tablename__ = "dispensacao_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dispensacao_id: Mapped[int] = mapped_column(
        ForeignKey("dispensacoes.id"), nullable=False, index=True
    )
    receita_item_id: Mapped[int] = mapped_column(
        ForeignKey("receita_itens.id"), nullable=False, index=True
    )

    quantidade_dispensada: Mapped[int] = mapped_column(Integer, nullable=False)
    lote: Mapped[str | None] = mapped_column(String(30), nullable=True)
    validade_lote: Mapped[date | None] = mapped_column(Date, nullable=True)

    dispensacao: Mapped["Dispensacao"] = relationship(back_populates="itens")
    receita_item: Mapped["ReceitaItem"] = relationship(back_populates="baixas")

    def __repr__(self) -> str:
        return (
            f"<DispensacaoItem(id={self.id}, receita_item_id={self.receita_item_id}, "
            f"quantidade={self.quantidade_dispensada})>"
        )