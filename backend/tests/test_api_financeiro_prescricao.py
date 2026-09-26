import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_gerar_pix_cobranca():
    payload = {
        "chave_pix": "12345678901",
        "nome_beneficiario": "Dr. Joao Paulo Versiani",
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


def test_api_livro_caixa_demonstrativo():
    response = client.get("/api/v1/financeiro-medico/livro-caixa/demonstrativo?mes_ano=09/2026")
    assert response.status_code == 200
    data = response.json()
    assert "receitas" in data
    assert "despesas" in data
    assert "apuracao_fiscal" in data
    assert data["receitas"]["total_bruto"] > 0


def test_api_emitir_prescricao_e_validar():
    payload = {
        "paciente_nome": "Beatriz Viana",
        "paciente_cpf": "99988877766",
        "medico_nome": "Dr. João Paulo Versiani",
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


def test_api_emitir_atestado():
    payload = {
        "paciente_nome": "Carlos Pereira",
        "paciente_cpf": "11122233344",
        "medico_nome": "Dr. João Paulo Versiani",
        "medico_crm": "78421",
        "medico_uf": "MG",
        "dias_afastamento": 2
    }
    res = client.post("/api/v1/prescricao/atestado/emitir", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["codigo_validacao"].startswith("ATE-")
    assert data["dias_afastamento"] == 2
