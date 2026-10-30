from pydantic import BaseModel, ConfigDict

class CIAP2Out(BaseModel):
    id: int
    codigo: str
    descricao: str
    capitulo: str | None = None
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
    capitulo: str | None = None
    capitulo_numero: str | None = None
    cid10_equivalente: str | None = None
    sinonimos: list[str] = []
    definicao: str | None = None
    padrao_oms: str | None = "ICD-11 MMS"

    model_config = ConfigDict(from_attributes=True)


class CID11ConversaoOut(BaseModel):
    origem: str
    codigo_origem: str
    destino: str
    codigo_destino: str | None = None
    codigo_cid11: str | None = None
    codigo_cid10: str | None = None
    titulo: str | None = None
    titulo_cid11: str | None = None
    capitulo: str | None = None
    equivalencia_direta: bool | None = True
    observacao: str | None = None

