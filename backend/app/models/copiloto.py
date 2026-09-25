"""Modelos SQLAlchemy 2.0 do Copiloto Clínico (C22) — Projeto MedIA.

``CopilotoAuditoria`` registra todo aceite de sugestão da IA pelo médico
(LGPD art. 20 — direito de explicação; CFM Resolução 2.314/2022 —
rastreabilidade da telemedicina e supervisão humana sobre a IA).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class CopilotoAuditoria(Base):
    """Auditoria do aceite da sugestão SOAP da IA em um atendimento.

    Cada linha documenta que o médico revisou e aceitou (ou editou) o
    rascunho SOAP gerado pelo copiloto, quais campos foram preenchidos
    e qual era a codificação CIAP-2/CID-10 sugerida.
    """

    __tablename__ = "copiloto_auditorias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    atendimento_id: Mapped[int] = mapped_column(
        ForeignKey("atendimentos_soap.id"), nullable=False, index=True
    )
    profissional_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("profissionais.id"), nullable=True
    )

    # Rastreabilidade da origem: IA_ACEITA, IA_EDITADA ou MANUAL
    origem: Mapped[str] = mapped_column(String(20), nullable=False, default="IA_ACEITA")
    campos_preenchidos: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # Conteúdo efetivamente registrado (texto integral para fins de auditoria)
    subjetivo: Mapped[str] = mapped_column(Text, nullable=False)
    objetivo: Mapped[str] = mapped_column(Text, nullable=False)
    avaliacao: Mapped[str] = mapped_column(Text, nullable=False)
    plano: Mapped[str] = mapped_column(Text, nullable=False)

    # Codificação SUS/APS
    cid10: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    ciap2: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Motor responsável pela sugestão (rastreabilidade do modelo)
    modelo: Mapped[str] = mapped_column(String(120), nullable=False, default="MedIA-CDS-1.0")

    registrado_em: Mapped[datetime] = mapped_column(
        DateTime, default=_agora_utc, nullable=False
    )

    atendimento = relationship("AtendimentoSOAP", backref="copiloto_auditorias")
