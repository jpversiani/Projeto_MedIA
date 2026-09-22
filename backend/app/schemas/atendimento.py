from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.cidadao import CidadaoOut
from app.schemas.profissional import ProfissionalOut

class ProblemaBase(BaseModel):
    tipo_codigo: str # 'CIAP2' ou 'CID10'
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
    fila_id: Optional[int] = None
    
    # SUBJETIVO
    subjetivo_motivo: Optional[str] = None
    subjetivo_notas: Optional[str] = None

    # OBJETIVO
    objetivo_exame_fisico: Optional[str] = None
    objetivo_antropometria_sinais: Optional[str] = None

    # AVALIAÇÃO
    avaliacao_notas: Optional[str] = None

    # PLANO
    plano_conduta: Optional[str] = None
    plano_prescricoes: Optional[str] = None
    plano_exames: Optional[str] = None
    plano_encaminhamentos: Optional[str] = None

class AtendimentoSOAPCreate(AtendimentoSOAPBase):
    problemas: List[ProblemaCreate] = []

class AtendimentoSOAPOut(AtendimentoSOAPBase):
    id: int
    data_hora_inicio: datetime
    data_hora_fim: Optional[datetime] = None
    status: str
    created_at: datetime
    cidadao: Optional[CidadaoOut] = None
    profissional: Optional[ProfissionalOut] = None
    problemas: List[ProblemaOut] = []
    model_config = ConfigDict(from_attributes=True)
