"""Agendamento de consultas — presencial e telemedicina.

Este modelo substitui o dicionário `_AGENDA_MEMORIA` que existia em
`api/v1/agenda_medica.py`. Aquele armazenamento tinha três problemas que
inviabilizavam o fluxo clínico:

1. **Volátil.** Reiniciar o servidor apagava a agenda inteira e re-semeava
   cinco pacientes fictícios.
2. **Divergente entre workers.** Com `uvicorn --workers 2`, cada processo tinha
   a própria cópia; a recepção agendava no worker 1 e o médico não via nada no
   worker 2.
3. **Desconectado do paciente.** Não havia `cidadao_id` — o paciente era
   identificado por CPF em texto livre. Sem isso é impossível ligar um
   agendamento ao prontuário, ao atendimento SOAP ou à receita.

O vínculo com o cidadão é o ponto central: é ele que permite que o médico abra
o prontuário de quem está na sala de espera.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone as _tz
from enum import Enum

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import relationship

from app.core.database import Base


class TipoAtendimento(str, Enum):
    """Modalidade do atendimento agendado."""

    PRESENCIAL = "PRESENCIAL"
    TELEMEDICINA = "TELEMEDICINA"


class StatusAgendamento(str, Enum):
    """Ciclo de vida do agendamento na agenda."""

    AGENDADO = "AGENDADO"
    CONFIRMADO = "CONFIRMADO"
    SALA_DE_ESPERA = "SALA_DE_ESPERA"
    EM_CONSULTA = "EM_CONSULTA"
    CONCLUIDO = "CONCLUIDO"
    FALTOU = "FALTOU"
    CANCELADO = "CANCELADO"


class Agendamento(Base):
    __tablename__ = "agendamentos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, nullable=False, index=True)

    # Vínculo com o paciente — o que faltava no armazenamento em memória.
    cidadao_id = Column(Integer, ForeignKey("cidadaos.id"), nullable=False, index=True)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=True, index=True)
    estabelecimento_id = Column(Integer, ForeignKey("estabelecimentos.id"), nullable=True, index=True)

    tipo = Column(String(20), nullable=False, default=TipoAtendimento.PRESENCIAL.value, index=True)
    status = Column(String(20), nullable=False, default=StatusAgendamento.AGENDADO.value, index=True)

    data_consulta = Column(Date, nullable=False, index=True)
    horario = Column(Time, nullable=False)
    duracao_minutos = Column(Integer, default=30)

    especialidade = Column(String(120), nullable=True)
    motivo_queixa = Column(Text, nullable=True)

    valor_consulta = Column(Float, nullable=True)
    modalidade_pagamento = Column(String(40), nullable=True)

    # Telemedicina: código da sala, gerado apenas para atendimento remoto.
    codigo_sala_telemedicina = Column(String(64), nullable=True, index=True)

    # Vínculo com a fila de acolhimento, preenchido no check-in. É o que liga
    # "paciente agendado" a "paciente esperando atendimento".
    fila_id = Column(Integer, ForeignKey("fila_acolhimento.id"), nullable=True, index=True)

    observacoes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(_tz.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(_tz.utc),
        onupdate=lambda: datetime.now(_tz.utc),
    )

    cidadao = relationship("Cidadao", backref="agendamentos")
    profissional = relationship("Profissional", backref="agendamentos")
    estabelecimento = relationship("Estabelecimento", backref="agendamentos")
    fila = relationship("FilaAcolhimento", foreign_keys=[fila_id])
