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

from backend.app.schemas.sisab import FichaAtendimento, LoteSISAB
from backend.app.services.sisab_export import (
    validar_ficha,
    validar_lote,
    gerar_payload,
)

@pytest.fixture
def ficha_valida():
    return FichaAtendimento(
        cns="123456789012345",  # 15 digits
        cnes="1234567",          # 7 digits
        ciap2="A01",
        cid10=None,
        data_atendimento="2024-01-01",
        ...
    )

def validar_ficha(ficha: dict) -> bool:
    # returns True if valid, raises ValidationError if invalid

soma = sum(int(d) * (15 - i) for i, d in enumerate(cns[:14]))
resto = soma % 11
if resto == 0:
    dv = 0
else:
    dv = 11 - resto

CNS_VALIDO = "123456789012348"
CNS_INVALIDO = "123456789012345"
CNES_VALIDO = "1234567"
CNES_INVALIDO = "123456"

def test_ficha_sem_ciap_e_cid_é_invalida():
    ficha = {
        "cns": CNS_VALIDO,
        "cnes": CNES_VALIDO,
        # sem ciap2 e sem cid10
    }
    with pytest.raises(ValidationError):
        validar_ficha(ficha)

def test_lote_com_cns_invalido_é_rejeitado():
    lote = {
        "fichas": [
            {"cns": CNS_INVALIDO, "cnes": CNES_VALIDO, "ciap2": "A01"},
        ]
    }
    with pytest.raises(ValidationError):
        validar_lote(lote)

def test_gerar_payload_consistente():
    ficha = {
        "cns": CNS_VALIDO,
        "cnes": CNES_VALIDO,
        "ciap2": "A01",
        "cid10": None,
        "data_atendimento": "2024-01-01",
    }
    payload = gerar_payload(ficha)
    assert payload["cns"] == CNS_VALIDO
    assert payload["cnes"] == CNES_VALIDO
    assert payload["ciap2"] == "A01"
    assert "cid10" in payload
