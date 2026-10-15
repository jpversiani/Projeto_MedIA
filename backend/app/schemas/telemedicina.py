"""
Schemas Pydantic v2 para o módulo de Telemedicina do MedIA.
Compatível com e-SUS APS, CIAP-2, CID-10 e validação de documentos.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StatusTeleconsulta(str, Enum):
    AGENDADA = "agendada"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class TeleconsultaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    paciente_cpf: str = Field(..., description="CPF do paciente (11 dígitos)")
    medico_crm: str = Field(..., description="CRM do médico (6 dígitos)")
    data_hora: datetime = Field(..., description="Data e hora da teleconsulta")
    ciap2: str | None = Field(None, description="Código CIAP-2 para APS")
    cid10: str | None = Field(None, description="Código CID-10")

    @field_validator("paciente_cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        clean = "".join(filter(str.isdigit, v))
        if len(clean) != 11:
            raise ValueError("CPF deve conter exatamente 11 dígitos")
        return clean

    @field_validator("medico_crm")
    @classmethod
    def validate_crm(cls, v: str) -> str:
        clean = "".join(filter(str.isdigit, v))
        if len(clean) != 6:
            raise ValueError("CRM deve conter exatamente 6 dígitos")
        return clean


class TeleconsultaCreate(TeleconsultaBase):
    pass


class TeleconsultaStatus(BaseModel):
    status: str = Field(..., description="Status da teleconsulta")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in [s.value for s in StatusTeleconsulta]:
            raise ValueError("Status inválido")
        return v


class Teleconsulta(TeleconsultaBase):
    id: int
    status: str
    link_sala: str | None = None
