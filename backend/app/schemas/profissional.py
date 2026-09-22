from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ProfissionalBase(BaseModel):
    cns: str
    cpf: str
    nome: str
    cbo: str
    cbo_descricao: Optional[str] = None

class ProfissionalCreate(ProfissionalBase):
    pass

class ProfissionalOut(ProfissionalBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
