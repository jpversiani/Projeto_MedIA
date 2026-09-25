"""Modelo da lista de problemas do Prontuário do Cidadão (PEC e-SUS APS).

Registra condições de saúde (problemas) do cidadão de forma continuada na
APS, codificadas por CIAP-2 ou CID-10, com situação de controle (ATIVO,
RESOLVIDO ou RASTREAMENTO), conforme o modelo da Lista de Problemas do
Prontuário Eletrônico do Cidadão.

Projeto MedIA — SUS/APS (Python 3.12, SQLAlchemy 2.0 tipado).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cidadao import Cidadao


class ProntuarioProblema(Base):
    """Problema/condição de saúde da Lista de Problemas do cidadão.

    Diferente de ``AtendimentoProblema`` (episódios vinculados a um
    atendimento SOAP específico), este registro pertence ao prontuário do
    cidadão e acompanha a evolução cronica da condição na APS.
    """

    __tablename__ = "prontuario_problemas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cidadao_id: Mapped[int] = mapped_column(
        ForeignKey("cidadaos.id"), nullable=False, index=True
    )

    # Codificação SUS: 'CIAP2' ou 'CID10' (ex.: K86, I10)
    tipo_codigo: Mapped[str] = mapped_column(String(10), nullable=False)
    codigo: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(String(300), nullable=False)

    # ATIVO, RESOLVIDO ou RASTREAMENTO
    situacao: Mapped[str] = mapped_column(String(30), default="ATIVO", nullable=False)

    data_registro: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    cidadao: Mapped["Cidadao"] = relationship("Cidadao")