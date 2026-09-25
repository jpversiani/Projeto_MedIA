"""Schemas Pydantic v2 do componente C29 — contingência e sincronização offline.

O contrato espelha o payload gravado pelo frontend (``offline_sync_indicator.js``)
no IndexedDB: identificação por CNS/CPF, registro clínico pelo método SOAP e
problemas codificados em CIAP-2/CID-10 (padrões SUS/APS).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Optional

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    field_validator,
    model_validator,
)

from app.models.atendimento_offline import StatusSincronizacao
from app.services.validadores import (
    normalizar_cid10,
    normalizar_ciap2,
    normalizar_cnes,
    normalizar_cns,
    normalizar_cpf,
)

# ---------------------------------------------------------------------------
# Tipos de domínio (tipagem estrita reutilizável)
# ---------------------------------------------------------------------------

CNS = Annotated[str, AfterValidator(normalizar_cns)]
"""CNS validado e normalizado (15 dígitos)."""

CPF = Annotated[Optional[str], AfterValidator(normalizar_cpf)]
"""CPF opcional validado e normalizado (11 dígitos)."""

CIAP2 = Annotated[str, AfterValidator(normalizar_ciap2)]
"""Código CIAP-2 validado (letra + 2 dígitos)."""

CID10 = Annotated[str, AfterValidator(normalizar_cid10)]
"""Código CID-10 validado (categoria + extensão opcional)."""

CNES = Annotated[str, AfterValidator(normalizar_cnes)]
"""CNES do estabelecimento validado (7 dígitos)."""

# ---------------------------------------------------------------------------
# Registro clínico (método SOAP)
# ---------------------------------------------------------------------------


class RegistroSOAP(BaseModel):
    """Quatro domínios do método SOAP exigidos pelo padrão APS."""

    model_config = ConfigDict(str_strip_whitespace=True)

    subjetivo: Optional[str] = Field(None, max_length=10_000, description="S — queixas e história relatada")
    objetivo: Optional[str] = Field(None, max_length=10_000, description="O — exame físico e achados")
    avaliacao: Optional[str] = Field(None, max_length=10_000, description="A — raciocínio clínico")
    plano: Optional[str] = Field(None, max_length=10_000, description="P — conduta e prescrições")

    @model_validator(mode="after")
    def _exigir_pelo_menos_um_dominio(self) -> "RegistroSOAP":
        if not any(
            (dominio or "").strip()
            for dominio in (self.subjetivo, self.objetivo, self.avaliacao, self.plano)
        ):
            raise ValueError(
                "O registro SOAP deve conter ao menos um domínio preenchido "
                "(subjetivo, objetivo, avaliacao ou plano)."
            )
        return self


# ---------------------------------------------------------------------------
# Sincronização offline
# ---------------------------------------------------------------------------


class AtendimentoOfflineCreate(BaseModel):
    """Payload de um atendimento registrado offline, enviado no upload."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id_local: uuid.UUID = Field(
        description="UUID v4 gerado no cliente; garante idempotência do upload."
    )
    cns_cidadao: CNS
    cpf_cidadao: CPF = None
    profissional_cns: Optional[CNS] = None
    cnes_estabelecimento: Optional[CNES] = None

    data_hora_atendimento: datetime = Field(
        description="Momento do atendimento na UBS, com fuso horário explícito."
    )

    soap: RegistroSOAP
    ciap2: Optional[CIAP2] = None
    cid10: Optional[CID10] = None

    @field_validator("data_hora_atendimento")
    @classmethod
    def _exigir_fuso_horario(cls, valor: datetime) -> datetime:
        if valor.tzinfo is None or valor.tzinfo.utcoffset(valor) is None:
            raise ValueError(
                "data_hora_atendimento deve ser um instante com fuso horário explícito (ISO-8601)."
            )
        return valor


class AtendimentoOfflineOut(BaseModel):
    """Representação persistida de um atendimento de contingência."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    id_local: uuid.UUID
    cns_cidadao: str
    cpf_cidadao: Optional[str] = None
    profissional_cns: Optional[str] = None
    cnes_estabelecimento: Optional[str] = None
    data_hora_atendimento: datetime
    subjetivo: Optional[str] = None
    objetivo: Optional[str] = None
    avaliacao: Optional[str] = None
    plano: Optional[str] = None
    ciap2: Optional[str] = None
    cid10: Optional[str] = None
    status: StatusSincronizacao
    criado_em: datetime
    recebido_em: datetime


class LoteSincronizacaoRequest(BaseModel):
    """Lote de atendimentos aguardando upload enviado pelo cliente offline."""

    model_config = ConfigDict(extra="forbid")

    itens: list[AtendimentoOfflineCreate] = Field(min_length=1, max_length=500)


class ItemDuplicado(BaseModel):
    """Item já recebido anteriormente (idempotência por ``id_local``)."""

    id_local: uuid.UUID
    motivo: str = "Atendimento já sincronizado anteriormente (id_local existente)."


class LoteSincronizacaoResponse(BaseModel):
    """Resultado do upload do lote de contingência."""

    recebidos: list[uuid.UUID] = Field(default_factory=list)
    duplicados: list[ItemDuplicado] = Field(default_factory=list)
    total_recebidos: NonNegativeInt = 0
    total_duplicados: NonNegativeInt = 0


class StatusSincronizacaoOut(BaseModel):
    """Painel resumido do servidor para auditoria da contingência."""

    total_recebidos: NonNegativeInt = 0
    ultimo_recebimento: Optional[datetime] = None
