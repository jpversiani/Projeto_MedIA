import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class GuiaTISSConsulta(BaseModel):
    numero_guia: str = Field(..., min_length=1)
    data_emissao: str = Field(..., min_length=1)
    paciente_nome: str = Field(..., min_length=1)
    paciente_carteira: str = Field(..., min_length=1)
    profissional_crm: str = Field(..., min_length=1)
    profissional_uf: str = Field(..., min_length=1)
    codigo_consulta: str = Field(..., min_length=1)
    data_consulta: str = Field(..., min_length=1)
    valor_consulta: float = Field(..., ge=0.0)

    @field_validator("numero_guia", "data_emissao", "paciente_nome", "paciente_carteira", 
                     "profissional_crm", "profissional_uf", "codigo_consulta", "data_consulta")
    @classmethod
    def validar_nao_vazio(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("Campo obrigatório não pode ser vazio")
        return v


class ReciboReembolso(BaseModel):
    crm: str
    cpf_paciente: str
    valor_pago: float = Field(..., gt=0.0)
    data_atendimento: str
    numero_guia: str

    @field_validator("crm")
    @classmethod
    def validar_crm(cls, v: str) -> str:
        if not re.match(r"^CRM/[A-Z]{2}\d{4,10}$", v):
            raise ValueError("CRM inválido. Formato esperado: CRM/UF123456")
        return v

    @field_validator("cpf_paciente")
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        if not re.match(r"^\d{11}$", v):
            raise ValueError("CPF deve conter exatamente 11 dígitos numéricos")
        return v
