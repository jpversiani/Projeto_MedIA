"""
Testes automatizados com Pytest para o Módulo de Telemedicina do MedIA.
Valida regras de negócio, Pydantic v2, validação de CRM/CPF e transições de status.
"""
from datetime import datetime

import pytest

from app.schemas.telemedicina import Teleconsulta, TeleconsultaCreate, TeleconsultaStatus


def test_teleconsulta_create_valid() -> None:
    data_hora = datetime.now()
    teleconsulta = TeleconsultaCreate(
        paciente_cpf="12345678901",
        medico_crm="123456",
        data_hora=data_hora,
        ciap2="A01",
        cid10="J00",
    )
    assert teleconsulta.paciente_cpf == "12345678901"
    assert teleconsulta.medico_crm == "123456"
    assert teleconsulta.data_hora == data_hora
    assert teleconsulta.ciap2 == "A01"
    assert teleconsulta.cid10 == "J00"


def test_teleconsulta_create_invalid_cpf() -> None:
    with pytest.raises(ValueError) as excinfo:
        TeleconsultaCreate(
            paciente_cpf="123",
            medico_crm="123456",
            data_hora=datetime.now(),
        )
    assert "CPF deve conter exatamente 11 dígitos" in str(excinfo.value)


def test_teleconsulta_create_invalid_crm() -> None:
    with pytest.raises(ValueError) as excinfo:
        TeleconsultaCreate(
            paciente_cpf="12345678901",
            medico_crm="123",
            data_hora=datetime.now(),
        )
    assert "CRM deve conter exatamente 6 dígitos" in str(excinfo.value)


def test_teleconsulta_status_valid() -> None:
    status = TeleconsultaStatus(status="agendada")
    assert status.status == "agendada"


def test_teleconsulta_status_invalid() -> None:
    with pytest.raises(ValueError) as excinfo:
        TeleconsultaStatus(status="invalid_status")
    assert "Status inválido" in str(excinfo.value)


def test_teleconsulta_model() -> None:
    data_hora = datetime.now()
    teleconsulta = Teleconsulta(
        id=1,
        paciente_cpf="12345678901",
        medico_crm="123456",
        data_hora=data_hora,
        status="agendada",
    )
    assert teleconsulta.id == 1
    assert teleconsulta.paciente_cpf == "12345678901"
    assert teleconsulta.medico_crm == "123456"
    assert teleconsulta.data_hora == data_hora
    assert teleconsulta.status == "agendada"
