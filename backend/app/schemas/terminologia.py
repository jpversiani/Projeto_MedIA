from pydantic import BaseModel, ConfigDict
from typing import Optional

class CIAP2Out(BaseModel):
    id: int
    codigo: str
    descricao: str
    capitulo: Optional[str] = None
    ativo: bool
    model_config = ConfigDict(from_attributes=True)

class CID10Out(BaseModel):
    id: int
    codigo: str
    descricao: str
    ativo: bool
    model_config = ConfigDict(from_attributes=True)
