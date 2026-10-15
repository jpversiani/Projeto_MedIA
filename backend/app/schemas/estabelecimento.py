from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    razao_social: str | None = None
    municipio_ibge: str
    logradouro: str | None = None
    numero: str | None = None
    bairro: str | None = None


class EstabelecimentoCreate(EstabelecimentoBase):
    pass


class EstabelecimentoOut(EstabelecimentoBase):
    id: int
    created_at: datetime
    equipes: list[EquipeOut] = []
    model_config = ConfigDict(from_attributes=True)
