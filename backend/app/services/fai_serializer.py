"""
FAI (Ficha de Atendimento Individual) Serializer.
Estrutura e serialização compatível com prontuário clínico e exportação de fichas individuais.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class FAIHeader(BaseModel):
    ficha_id: Optional[str] = None
    data_geracao: datetime = Field(default_factory=datetime.utcnow)
    tipo_ficha: str = "ATENCAO_INDIVIDUAL"
    versao: str = "5.3.0"

class FAIPatient(BaseModel):
    cns: Optional[str] = None
    cpf: Optional[str] = None
    nome_completo: Optional[str] = None
    data_nascimento: Optional[str] = None
    sexo: Optional[str] = "M"

class FAIProfessional(BaseModel):
    cns: Optional[str] = None
    cpf: Optional[str] = None
    nome_completo: Optional[str] = None
    cbo: Optional[str] = "225142"

class FAIProblem(BaseModel):
    tipo_codigo: str
    codigo: str
    descricao: Optional[str] = None

class FAI(BaseModel):
    header: FAIHeader = Field(default_factory=FAIHeader)
    paciente: Optional[FAIPatient] = None
    profissional: Optional[FAIProfessional] = None
    problemas: List[FAIProblem] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "FAI":
        return cls(**data)

def create_fa_i(data: dict) -> FAI:
    """Factory method to create a FAI instance from raw dictionary."""
    return FAI(**data)
