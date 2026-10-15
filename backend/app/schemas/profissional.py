from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProfissionalBase(BaseModel):
    cns: str
    cpf: str
    nome: str
    cbo: str
    cbo_descricao: str | None = None


class ProfissionalCreate(ProfissionalBase):
    pass


class ProfissionalOut(ProfissionalBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
