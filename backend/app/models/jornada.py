"""Jornada do fluxo de atendimento persistida.

O motor de fluxo (`fluxo_atendimento_service`) mantinha tudo em memória:
`criar_agendamento` gravava num dicionário do processo e `finalizar` lia dali.
Consequências reais:

1. **Reiniciar o servidor apagava todas as consultas em andamento** — o médico
   perdia o atendimento aberto no meio.
- Com mais de um worker, cada processo via uma lista diferente.
- **Não havia tenant**: `paciente_id` era sorteado (`uuid4`), não havia
   `cidadao_id`, `estabelecimento_id` nem `profissional_id`. Em ambiente
   multi-clínica, um médico podia finalizar a consulta de outro.
- Finalizar uma consulta criada pela agenda retornava 404, porque a agenda grava
  em ``agendamentos`` e o fluxo nunca lia de lá.

Esta tabela guarda o estado da jornada (JSON) e os vínculos de identidade
reais. O serviço mantém um cache em memória para performance, mas toda mutação
é gravada e toda leitura ausente no cache é hidratada do banco.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.crypto import CampoProtegido, JsonProtegido
from app.core.database import Base


class EtapaJornada(str, enum.Enum):
    """Etapas do ciclo de vida do atendimento."""

    AGENDADA = "AGENDADA"
    PRE_CONSULTA = "PRE_CONSULTA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    FINALIZADA = "FINALIZADA"


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class JornadaAtendimento(Base):
    """Estado completo de uma consulta do fluxo, sobrevivente a restart."""

    __tablename__ = "jornadas_atendimento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Identificador usado pelo frontend (``CONS-AAAA-XXXXXXXX``) ou o código do
    # agendamento da agenda (``AGD-...``), quando a consulta nasce lá.
    consulta_id: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, index=True
    )

    # Vínculos reais (antes eram sorteados/ausentes).
    cidadao_id: Mapped[int | None] = mapped_column(
        ForeignKey("cidadaos.id"), nullable=True, index=True
    )
    profissional_id: Mapped[int | None] = mapped_column(
        ForeignKey("profissionais.id"), nullable=True, index=True
    )
    estabelecimento_id: Mapped[int | None] = mapped_column(
        ForeignKey("estabelecimentos.id"), nullable=True, index=True
    )
    agendamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("agendamentos.id"), nullable=True, index=True
    )

    # Colunas espelhadas para consulta/relatório sem abrir o JSON.
    paciente_nome: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    paciente_cpf: Mapped[str | None] = mapped_column(CampoProtegido, nullable=True)
    medico_nome: Mapped[str] = mapped_column(String(200), nullable=False)
    medico_crm: Mapped[str | None] = mapped_column(String(20), nullable=True)
    modalidade: Mapped[str] = mapped_column(String(20), nullable=False)
    etapa: Mapped[str] = mapped_column(
        String(20), default=EtapaJornada.AGENDADA.value, nullable=False, index=True
    )
    valor_honorarios: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Estado completo (SOAP, diagnósticos, prescrições, TCLE, pacote pós-consulta).
    dados_json: Mapped[dict] = mapped_column(
        # CPF/CNS do paciente dentro do JSON também são cifrados; o resto
        # (etapas, checklist, anamnese) segue legível para relatórios.
        JsonProtegido(campos=("paciente_cpf", "paciente_cns")),
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_agora_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_agora_utc, onupdate=_agora_utc
    )

    def __repr__(self) -> str:
        return (
            f"<JornadaAtendimento(consulta_id={self.consulta_id}, "
            f"etapa={self.etapa})>"
        )
