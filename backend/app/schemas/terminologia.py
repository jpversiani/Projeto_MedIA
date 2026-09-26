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


class CID11Out(BaseModel):
    codigo: str
    titulo: str
    capitulo: Optional[str] = None
    capitulo_numero: Optional[str] = None
    cid10_equivalente: Optional[str] = None
    sinonimos: list[str] = []
    definicao: Optional[str] = None
    padrao_oms: Optional[str] = "ICD-11 MMS"
    model_config = ConfigDict(from_attributes=True)


class CID11ConversaoOut(BaseModel):
    origem: str
    codigo_origem: str
    destino: str
    codigo_destino: Optional[str] = None
    codigo_cid11: Optional[str] = None
    codigo_cid10: Optional[str] = None
    titulo: Optional[str] = None
    titulo_cid11: Optional[str] = None
    capitulo: Optional[str] = None
    equivalencia_direta: Optional[bool] = True
    observacao: Optional[str] = None

