"""
Testes unitários e de integração para o serviço e API da CID-11 (OMS - ICD-11 MMS).
Verifica:
1. Catálogo clínico de entidades da CID-11
2. Busca inteligente por código, texto e sinônimos
3. Conversor Dual-Coding CID-10 <-> CID-11
4. Endpoints REST da API FastAPI
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.cid11_service import CID11Service, ItemCID11, cid11_service

client = TestClient(app)


def test_cid11_service_catalogo_carregado():
    """Garante que o catálogo da CID-11 possui entidades clínicas essenciais cadastradas."""
    assert cid11_service.total_codigos() >= 20
    capitulos = cid11_service.listar_capitulos()
    assert len(capitulos) >= 5
    # Verifica presença de capítulos chave (ex: 05, 06, 11, 12)
    nums = [c["numero"] for c in capitulos]
    assert "05" in nums  # Endócrino
    assert "06" in nums  # Saúde mental
    assert "11" in nums  # Circulatório


def test_cid11_service_busca_por_codigo():
    """Testa busca direta pelo código MMS da CID-11."""
    res_ba00 = cid11_service.buscar("BA00")
    assert len(res_ba00) >= 1
    assert res_ba00[0]["codigo"] == "BA00"
    assert "Hipertensão" in res_ba00[0]["titulo"]
    assert res_ba00[0]["cid10_equivalente"] == "I10"


def test_cid11_service_busca_por_sinonimo():
    """Testa busca usando termos médicos usuais e abreviações."""
    # DM2
    res_dm2 = cid11_service.buscar("DM2")
    assert any(item["codigo"] == "5A11" for item in res_dm2)

    # TAG (Transtorno de Ansiedade Generalizada)
    res_tag = cid11_service.buscar("TAG")
    assert any(item["codigo"] == "6B00" for item in res_tag)

    # Burnout
    res_burnout = cid11_service.buscar("Burnout")
    assert any(item["codigo"] == "QD85" for item in res_burnout)


def test_cid11_service_busca_sem_acento():
    """Garante busca tolerante a termos sem acentuação (ex: hipertensao -> Hipertensão)."""
    res = cid11_service.buscar("hipertensao")
    assert any(item["codigo"] == "BA00" for item in res)

    res_dep = cid11_service.buscar("depressao")
    assert any(item["codigo"] == "6A70" for item in res_dep)



def test_cid11_service_busca_por_capitulo():
    """Testa filtro por capítulo."""
    res = cid11_service.buscar(capitulo="06")
    assert len(res) > 0
    for item in res:
        assert item["capitulo_numero"] == "06"


def test_cid11_conversao_cid10_para_cid11():
    """Testa o mapeador cruzado de CID-10 para CID-11."""
    # Hipertensão I10 -> BA00
    conv = cid11_service.converter_cid10_para_cid11("I10")
    assert conv is not None
    assert conv["codigo_cid11"] == "BA00"
    assert conv["equivalencia_direta"] is True

    # Diabetes E11 -> 5A11
    conv_dm = cid11_service.converter_cid10_para_cid11("E11")
    assert conv_dm is not None
    assert conv_dm["codigo_cid11"] == "5A11"

    # Prefixo com subcódigo I10.9
    conv_prefix = cid11_service.converter_cid10_para_cid11("I10.9")
    assert conv_prefix is not None
    assert conv_prefix["codigo_cid11"] == "BA00"
    assert conv_prefix["equivalencia_direta"] is False


def test_cid11_conversao_cid11_para_cid10():
    """Testa conversão inversa CID-11 para CID-10 (essencial para faturamento e guias TISS)."""
    # 6B00 (Ansiedade) -> F41.1
    conv = cid11_service.converter_cid11_para_cid10("6B00")
    assert conv is not None
    assert conv["codigo_cid10"] == "F41.1"

    # CA23 (Asma) -> J45
    conv_asma = cid11_service.converter_cid11_para_cid10("CA23")
    assert conv_asma is not None
    assert conv_asma["codigo_cid10"] == "J45"


def test_api_buscar_cid11():
    """Testa endpoint GET /api/v1/terminologias/cid11."""
    resp = client.get("/api/v1/terminologias/cid11?busca=ansiedade")
    assert resp.status_code == 200
    dados = resp.json()
    assert isinstance(dados, list)
    assert len(dados) >= 1
    assert any("6B00" in d["codigo"] for d in dados)


def test_api_detalhe_cid11_existente():
    """Testa GET /api/v1/terminologias/cid11/{codigo}."""
    resp = client.get("/api/v1/terminologias/cid11/BA00")
    assert resp.status_code == 200
    dados = resp.json()
    assert dados["codigo"] == "BA00"
    assert "Hipertensão" in dados["titulo"]
    assert dados["cid10_equivalente"] == "I10"


def test_api_detalhe_cid11_inexistente():
    """Testa 404 para código inexistente."""
    resp = client.get("/api/v1/terminologias/cid11/CODIGO_INVALIDO")
    assert resp.status_code == 404


def test_api_converter_codigo_dual_coding():
    """Testa GET /api/v1/terminologias/cid11/converter/{codigo}."""
    # CID-10 -> CID-11
    resp1 = client.get("/api/v1/terminologias/cid11/converter/I10")
    assert resp1.status_code == 200
    assert resp1.json()["codigo_cid11"] == "BA00"

    # CID-11 -> CID-10
    resp2 = client.get("/api/v1/terminologias/cid11/converter/5A11")
    assert resp2.status_code == 200
    assert resp2.json()["codigo_cid10"] == "E11"


def test_api_listar_capitulos_cid11():
    """Testa GET /api/v1/terminologias/cid11/capitulos."""
    resp = client.get("/api/v1/terminologias/cid11/capitulos")
    assert resp.status_code == 200
    dados = resp.json()
    assert "capitulos" in dados
    assert dados["total_capitulos"] >= 5
