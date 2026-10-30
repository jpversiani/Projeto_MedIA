from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class CidadaoBase(BaseModel):
    cns: str | None = Field(None, description="Cartão Nacional de Saúde (15 dígitos)")
    cpf: str | None = Field(None, description="CPF (11 dígitos sem formatação)")
    nome_completo: str
    nome_social: str | None = None
    nome_mae: str | None = None
    data_nascimento: date
    sexo: str = Field("M", description="'M', 'F' ou 'I'")
    raca_cor: str = "Parda"
    telefone: str | None = None
    email: str | None = None
    cep: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    municipio_ibge: str | None = None
    hipertenso: bool = False
    diabetico: bool = False
    gestante: bool = False
    fumante: bool = False
    alergias: str | None = None


class CidadaoCreate(CidadaoBase):
    pass


class CidadaoUpdate(BaseModel):
    telefone: str | None = None
    email: str | None = None
    cep: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    bairro: str | None = None
    hipertenso: bool | None = None
    diabetico: bool | None = None
    gestante: bool | None = None
    fumante: bool | None = None
    alergias: str | None = None


class CidadaoOut(CidadaoBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
