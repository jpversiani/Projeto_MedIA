"""Schemas Pydantic v2 do Copiloto Clínico (C22) — Projeto MedIA.

Contrato consumido pelo widget de front-end
``backend/app/static/js/copiloto_sidebar.js`` (Painel Lateral do Copiloto
na tela de teleatendimento do médico — Home Office).

Padrões SUS/APS:
  - Identificação do cidadão por CNS (fallback CPF);
  - Motivo de contato/avaliação codificado em CIAP-2 e CID-10;
  - Registro clínico pelo método SOAP (S·O·A·P);
  - Dosagens usuais conforme RENAME/Forma Nacional e PCDT do Ministério da
    Saúde (referência explícita em cada sugestão).

Conformidade LGPD/CFM:
  - Nenhuma sugestão da IA é aplicada sem aceite explícito do médico
    (CFM Resolução 2.314/2022); cada aceite gera registro de auditoria.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class TipoAlerta(StrEnum):
    """Classificação dos alertas clínicos exibidos no painel (piscantes)."""

    ALERGIA = "alergia"
    RISCO = "risco"
    INTERACAO_MEDICAMENTOSA = "interacao_medicamentosa"
    DOSE_MAXIMA_EXCEDIDA = "dose_maxima_excedida"
    RED_FLAG_CLINICA = "red_flag_clinica"


class SeveridadeAlerta(StrEnum):
    """Severidade assistencial; `critico`/`alto` disparam o estado piscante."""

    CRITICO = "critico"
    ALTO = "alto"
    MODERADO = "moderado"
    INFO = "info"


class PrioridadeExame(StrEnum):
    ROTINA = "rotina"
    URGENTE = "urgente"


class OrigemAceite(StrEnum):
    """Rastreabilidade do uso da sugestão (auditoria CFM 2.314/2022)."""

    IA_ACEITA = "IA_ACEITA"  # sugerido pela IA e aceito sem edições
    IA_EDITADA = "IA_EDITADA"  # sugerido pela IA e revisado/ajustado pelo médico
    MANUAL = "MANUAL"  # redigido pelo médico, sem conteúdo da IA


class AlertaClinicoOut(BaseModel):
    """Alerta de risco/alergia exibido de forma piscante no painel lateral."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: str = Field(..., description="Identificador estável do alerta (hash/contexto)")
    tipo: TipoAlerta
    severidade: SeveridadeAlerta
    titulo: str = Field(..., min_length=1, max_length=120)
    descricao: str = Field(..., min_length=1, max_length=600)
    conduta_recomendada: str = Field(..., min_length=1, max_length=600)
    substancia: str | None = Field(None, max_length=200, description="DCB da substância (alergia/interação)")
    cid10: str | None = Field(None, max_length=10)
    ciap2: str | None = Field(None, max_length=10)
    fonte: str = Field(..., max_length=120, description="Origem: 'RMCA', 'e-SUS APS', 'RENAME 2022', ...")
    criado_em: datetime = Field(default_factory=_agora_utc)


class ExameComplementarOut(BaseModel):
    """Sugestão de exame complementar disponível no SUS (Sisreg/APS)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(..., min_length=1)
    nome: str = Field(..., min_length=1, max_length=200)
    justificativa: str = Field(..., min_length=1, max_length=600)
    prioridade: PrioridadeExame = PrioridadeExame.ROTINA
    cid10: str | None = Field(None, max_length=10)
    ciap2: str | None = Field(None, max_length=10)
    disponivel_sus: bool = Field(True, description="Disponível na rede SUS/APS")


class DosagemSUSOut(BaseModel):
    """Dosagem usual do SUS (RENAME/PCDT) sugerida para o problema ativo."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(..., min_length=1)
    medicamento: str = Field(..., min_length=1, max_length=200, description="DCB (Denominação Comum Brasileira)")
    apresentacao: str = Field(..., min_length=1, max_length=200, description="Ex.: 'comprimido 500 mg'")
    posologia: str = Field(..., min_length=1, max_length=400, description="Ex.: '500 mg via oral, 8/8 h, por 5 dias'")
    cid10: str | None = Field(None, max_length=10)
    ciap2: str | None = Field(None, max_length=10)
    referencia: str = Field(..., min_length=1, max_length=200, description="Ex.: 'RENAME 2022', 'PCDT MS'")


class SugestaoSOAPOut(BaseModel):
    """Rascunho SOAP sugerido pela IA (sempre opcional; decisão final é do médico)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    subjetivo: str = Field(..., max_length=2000)
    objetivo: str = Field(..., max_length=2000)
    avaliacao: str = Field(..., max_length=2000)
    plano: str = Field(..., max_length=4000)
    cid10_sugerido: str | None = Field(None, max_length=10)
    ciap2_sugerido: str | None = Field(None, max_length=10)
    confianca: float = Field(..., ge=0.0, le=1.0, description="Confiança do modelo (0..1)")
    modelo: str = Field(..., max_length=120, description="Identificação do motor (rastreabilidade)")
    gerado_em: datetime = Field(default_factory=_agora_utc)


class SugestoesCopilotoOut(BaseModel):
    """Agregado consumido pelo botão 'Preencher SOAP com Sugestão da IA'."""

    model_config = ConfigDict(from_attributes=True)

    atendimento_id: int
    soap: SugestaoSOAPOut
    exames_complementares: tuple[ExameComplementarOut, ...] = Field(default_factory=tuple)
    dosagens_sus: tuple[DosagemSUSOut, ...] = Field(default_factory=tuple)


class AceiteSOAPIn(BaseModel):
    """Payload do aceite do rascunho SOAP sugerido pela IA (auditoria)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    subjetivo: str = Field(..., min_length=1, max_length=2000)
    objetivo: str = Field(..., min_length=1, max_length=2000)
    avaliacao: str = Field(..., min_length=1, max_length=2000)
    plano: str = Field(..., min_length=1, max_length=4000)
    cid10: str | None = Field(None, max_length=10)
    ciap2: str | None = Field(None, max_length=10)
    origem: OrigemAceite = OrigemAceite.IA_ACEITA
    profissional_id: int | None = Field(None, ge=1)

    @field_validator("cid10", "ciap2")
    @classmethod
    def _normalizar_codigo(cls, v: str | None) -> str | None:
        return v.strip().upper() if v else None


class AuditoriaCopilotoOut(BaseModel):
    """Registro de auditoria do aceite da sugestão da IA."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    atendimento_id: int
    profissional_id: int | None
    origem: OrigemAceite
    campos_preenchidos: tuple[str, ...] = Field(default_factory=tuple)
    cid10: str | None
    ciap2: str | None
    registrado_em: datetime


class EventoWS(StrEnum):
    """Tipos de evento transmitidos pelo WebSocket do copiloto."""

    SNAPSHOT_ALERTAS = "snapshot_alertas"
    ALERTA_NOVO = "alerta_novo"
    SOAP_ACEITO = "soap_aceito"
    PONG = "pong"


class EventoCopilotoWS(BaseModel):
    """Envelope das mensagens WS (cabeçalho `tipo` + carga `dados`)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    tipo: EventoWS
    atendimento_id: int
    dados: dict[str, object] = Field(default_factory=dict)
    enviado_em: datetime = Field(default_factory=_agora_utc)


TipoAlertaLiteral = Literal[
    "alergia",
    "risco",
    "interacao_medicamentosa",
    "dose_maxima_excedida",
    "red_flag_clinica",
]
