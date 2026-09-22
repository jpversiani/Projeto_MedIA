from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class EquipeBase(BaseModel):
    ine: str
    nome: str
    tipo_equipe: str = "eSF"

class EquipeCreate(EquipeBase):
    estabelecimento_id: int

class EquipeOut(EquipeBase):
    id: int
    estabelecimento_id: int
    model_config = ConfigDict(from_attributes=True)

class EstabelecimentoBase(BaseModel):
    cnes: str
    nome_fantasia: str
    razao_social: Optional[str] = None
    municipio_ibge: str
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None

class EstabelecimentoCreate(EstabelecimentoBase):
    pass

class EstabelecimentoOut(EstabelecimentoBase):
    id: int
    created_at: datetime
    equipes: List[EquipeOut] = []
    model_config = ConfigDict(from_attributes=True)
