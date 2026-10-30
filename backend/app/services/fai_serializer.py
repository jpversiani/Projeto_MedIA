"""
FAI (Ficha de Atendimento Individual) Serializer.
Estrutura e serialização compatível com prontuário clínico e exportação de fichas individuais.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FAIHeader(BaseModel):
    ficha_id: str | None = None
    data_geracao: datetime = Field(default_factory=datetime.now)
    tipo_ficha: str = "ATENCAO_INDIVIDUAL"
    versao: str = "5.3.0"


class FAIPatient(BaseModel):
    cns: str | None = None
    cpf: str | None = None
    nome_completo: str | None = None
    data_nascimento: str | None = None
    sexo: str | None = "M"


class FAIProfessional(BaseModel):
    cns: str | None = None
    cpf: str | None = None
    nome_completo: str | None = None
    cbo: str | None = "225142"


class FAIProblem(BaseModel):
    tipo_codigo: str
    codigo: str
    descricao: str | None = None


class FAI(BaseModel):
    header: FAIHeader = Field(default_factory=FAIHeader)
    paciente: FAIPatient | None = None
    profissional: FAIProfessional | None = None
    problemas: list[FAIProblem] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "FAI":
        return cls(**data)


def create_fa_i(data: dict) -> FAI:
    """Factory method to create a FAI instance from raw dictionary."""
    return FAI(**data)
