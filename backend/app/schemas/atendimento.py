from datetime import datetime

from app.schemas.cidadao import CidadaoOut
from app.schemas.profissional import ProfissionalOut
from pydantic import BaseModel, ConfigDict


class ProblemaBase(BaseModel):
    tipo_codigo: str  # 'CIAP2' ou 'CID10'
    codigo: str
    descricao: str
    situacao: str = "ATIVO"


class ProblemaCreate(ProblemaBase):
    pass


class ProblemaOut(ProblemaBase):
    id: int
    atendimento_id: int
    model_config = ConfigDict(from_attributes=True)


class AtendimentoSOAPBase(BaseModel):
    cidadao_id: int
    profissional_id: int
    estabelecimento_id: int
    fila_id: int | None = None

    # SUBJETIVO
    subjetivo_motivo: str | None = None
    subjetivo_notas: str | None = None

    # OBJETIVO
    objetivo_exame_fisico: str | None = None
    objetivo_antropometria_sinais: str | None = None

    # AVALIAÇÃO
    avaliacao_notas: str | None = None

    # PLANO
    plano_conduta: str | None = None
    plano_prescricoes: str | None = None
    plano_exames: str | None = None
    plano_encaminhamentos: str | None = None


class AtendimentoSOAPCreate(AtendimentoSOAPBase):
    problemas: list[ProblemaCreate] = []


class AtendimentoSOAPOut(AtendimentoSOAPBase):
    id: int
    data_hora_inicio: datetime
    data_hora_fim: datetime | None = None
    status: str
    created_at: datetime
    cidadao: CidadaoOut | None = None
    profissional: ProfissionalOut | None = None
    problemas: list[ProblemaOut] = []
    model_config = ConfigDict(from_attributes=True)
