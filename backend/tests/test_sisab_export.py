# Arquivo: backend/tests/test_sisab_export.py
"""
Testes de Validação Estrutural da Exportação SISAB (C36).

Cobertura:
1. Validação de preenchimento obrigatório de CIAP-2/CID-10.
2. Rejeição de lotes com CNS ou CNES inválido.
3. Geração de payload consistente.
"""

import pytest
from pydantic import ValidationError

from app.services.sisab_client import (
    FichaSISAB,
    LoteInvalidoError,
    LoteSISAB,
    TipoFicha,
)

CNS_VALIDO = "123456789012348"
CNS_INVALIDO = "123456789012345"
CNES_VALIDO = "1234567"
CIAP2_VALIDO = "A01"
CID10_VALIDO = "I10"


def test_ficha_sem_ciap_e_cid_é_invalida():
    with pytest.raises(ValidationError):
        FichaSISAB(
            cns=CNS_VALIDO,
            cnes=CNES_VALIDO,
            ciap2=None,
            cid10=None,
            data_atendimento="2024-01-01T00:00:00+00:00",
        )


def test_ficha_com_cns_invalido_é_rejeitada():
    with pytest.raises(ValidationError):
        FichaSISAB(
            cns=CNS_INVALIDO,
            cnes=CNES_VALIDO,
            ciap2=CIAP2_VALIDO,
            cid10=None,
            data_atendimento="2024-01-01T00:00:00+00:00",
        )


def test_ficha_com_cnes_invalido_é_rejeitada():
    with pytest.raises(ValidationError):
        FichaSISAB(
            cns=CNS_VALIDO,
            cnes="123456",
            ciap2=CIAP2_VALIDO,
            cid10=None,
            data_atendimento="2024-01-01T00:00:00+00:00",
        )


def test_ficha_com_ciap2_e_cid10():
    ficha = FichaSISAB(
        cns=CNS_VALIDO,
        cnes=CNES_VALIDO,
        ciap2=CIAP2_VALIDO,
        cid10=CID10_VALIDO,
        data_atendimento="2024-01-01T00:00:00+00:00",
    )
    assert ficha.ciap2 == "A01"
    assert ficha.cid10 == "I10"


def test_lote_com_ficha_valida():
    lote = LoteSISAB(
        lote_id="LOTE-001",
        cnes_origem=CNES_VALIDO,
        fichas=[
            FichaSISAB(
                cns=CNS_VALIDO,
                cnes=CNES_VALIDO,
                ciap2=CIAP2_VALIDO,
                cid10=None,
                data_atendimento="2024-01-01T00:00:00+00:00",
            )
        ],
    )
    assert lote.lote_id == "LOTE-001"
    assert lote.total_fichas == 1


def test_gerar_payload_consistente():
    ficha = FichaSISAB(
        cns=CNS_VALIDO,
        cnes=CNES_VALIDO,
        ciap2=CIAP2_VALIDO,
        cid10=None,
        data_atendimento="2024-01-01T00:00:00+00:00",
    )
    payload = ficha.model_dump(mode="json")
    assert payload["cns"] == CNS_VALIDO
    assert payload["cnes"] == CNES_VALIDO
    assert payload["ciap2"] == "A01"
    assert "cid10" in payload