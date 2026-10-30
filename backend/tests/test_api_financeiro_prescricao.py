import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_gerar_pix_cobranca():
    payload = {
        "chave_pix": "12345678901",
        "nome_beneficiario": "Dra. Francelli Neves Versiani",
        "cidade_beneficiario": "Montes Claros",
        "valor": 350.00,
        "descricao": "Consulta Telemedicina"
    }
    response = client.post("/api/v1/financeiro-medico/pix/gerar-cobranca", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "pix_copia_e_cola" in data
    assert "crc16" in data
    assert data["valor"] == "350.00"


def test_api_livro_caixa_demonstrativo(client):
    """O demonstrativo não pode inventar faturamento.

    Antes esta rota devolvia cinco consultas e três despesas *hardcoded*, e o
    teste antigo (`total_bruto > 0`) apenas blindava o mock. Agora, sem
    lançamentos na competência, todos os totais vêm zerados.
    """
    response = client.get("/api/v1/financeiro-medico/livro-caixa/demonstrativo?mes_ano=01/1990")
    assert response.status_code == 200
    data = response.json()

    assert data["competencia"] == "01/1990"
    assert data["receitas"]["total_bruto"] == 0
    assert data["receitas"]["quantidade_consultas"] == 0
    assert data["despesas"]["total_despesas"] == 0
    assert data["apuracao_fiscal"]["imposto_a_recolher_darf"] == 0
    assert data["cobertura"]["possui_lancamentos"] is False


def test_api_emitir_prescricao_e_validar(client):
    payload = {
        "paciente_nome": "Beatriz Viana",
        "paciente_cpf": "99988877766",
        "medico_nome": "Dra. Francelli Neves Versiani",
        "medico_crm": "78421",
        "medico_uf": "MG",
        "tipo": "SIMPLES",
        "itens": [
            {
                "farmaco": "Dipirona Monoidratada",
                "concentracao": "500mg",
                "posologia": "1 cp se dor ou febre",
                "quantidade_total": "1 cartela"
            }
        ]
    }
    res = client.post("/api/v1/prescricao/emitir", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["codigo_validacao"].startswith("CFM-")

    # Validar publicamente
    res_val = client.get(f"/api/v1/prescricao/validar/{data['codigo_validacao']}")
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["status"] == "VALIDA"
    assert val_data["paciente_nome"] == "Beatriz Viana"


def test_api_emitir_atestado(client):
    payload = {
        "paciente_nome": "Carlos Pereira",
        "paciente_cpf": "11122233344",
        "medico_nome": "Dra. Francelli Neves Versiani",
        "medico_crm": "78421",
        "medico_uf": "MG",
        "dias_afastamento": 2
    }
    res = client.post("/api/v1/prescricao/atestado/emitir", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["codigo_validacao"].startswith("ATE-")
    assert data["dias_afastamento"] == 2
