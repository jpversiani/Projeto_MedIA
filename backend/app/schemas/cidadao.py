from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date, datetime

class CidadaoBase(BaseModel):
    cns: Optional[str] = Field(None, description="Cartão Nacional de Saúde (15 dígitos)")
    cpf: Optional[str] = Field(None, description="CPF (11 dígitos sem formatação)")
    nome_completo: str
    nome_social: Optional[str] = None
    nome_mae: Optional[str] = None
    data_nascimento: date
    sexo: str = Field("M", description="'M', 'F' ou 'I'")
    raca_cor: str = "Parda"
    telefone: Optional[str] = None
    email: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    municipio_ibge: Optional[str] = None
    hipertenso: bool = False
    diabetico: bool = False
    gestante: bool = False
    fumante: bool = False
    alergias: Optional[str] = None

class CidadaoCreate(CidadaoBase):
    pass

class CidadaoUpdate(BaseModel):
    telefone: Optional[str] = None
    email: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    hipertenso: Optional[bool] = None
    diabetico: Optional[bool] = None
    gestante: Optional[bool] = None
    fumante: Optional[bool] = None
    alergias: Optional[str] = None

class CidadaoOut(CidadaoBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
