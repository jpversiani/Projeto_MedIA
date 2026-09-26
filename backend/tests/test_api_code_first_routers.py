import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_tiss_gerar_guia():
    payload = {
        "numero_guia_prestador": "GUIA-TEST-001",
        "registro_ans": "318011",
        "nome_operadora": "Bradesco Saúde",
        "numero_carteira": "9876543210123",
        "nome_beneficiario": "Maria Silva Santos",
        "codigo_cnes": "3180115",
        "nome_contratado": "Consultório Particular MedIA",
        "crm_medico": "78421",
        "uf_crm": "MG",
        "cbos": "225125",
        "data_atendimento": "2026-09-20",
        "codigo_tuss_procedimento": "10101012",
        "valor_procedimento": 150.00,
        "cid10_principal": "I10"
    }
    resp = client.post("/api/v1/tiss/gerar-guia-xml", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["valida"] is True
    assert "<ans:mensagemTISS" in data["xml_gerado"]


def test_api_dmed_exportar():
    payload = {
        "ano_calendario": 2025,
        "cnpj_prestador": "12345678000199",
        "nome_empresarial": "CLINICA MEDIA LTDA",
        "retificadora": False,
        "lancamentos": [
            {
                "cpf_responsavel_pagamento": "12345678909",
                "nome_responsavel_pagamento": "JOAO DA SILVA",
                "nome_beneficiario": "JOAO DA SILVA",
                "valor_pago": 300.00
            }
        ]
    }
    resp = client.post("/api/v1/dmed/exportar-arquivo-magnetico", json=payload)
    assert resp.status_code == 200
    assert "DMED|2025|12345678000199" in resp.text
    assert "ROP|12345678909|JOAO DA SILVA" in resp.text


def test_api_clinica_calculadoras():
    # Framingham
    payload_framingham = {
        "sexo": "M",
        "idade": 55,
        "colesterol_total": 240.0,
        "colesterol_hdl": 40.0,
        "pressao_sistolica": 140.0,
        "em_tratamento_has": True,
        "fumante": False,
        "diabetico": True
    }
    resp = client.post("/api/v1/clinica/framingham", json=payload_framingham)
    assert resp.status_code == 200
    assert "risco_percentual" in resp.json()

    # CKD-EPI
    resp_ckd = client.post("/api/v1/clinica/ckd-epi", json={"creatinina_serica": 1.1, "idade": 60, "sexo": "M"})
    assert resp_ckd.status_code == 200
    assert "egfr" in resp_ckd.json()

    # Interações
    resp_interacao = client.post("/api/v1/clinica/checar-interacoes", json={
        "medicamentos": ["Varfarina 5mg", "Ibuprofeno 400mg"],
        "alergias": ["Dipirona"]
    })
    assert resp_interacao.status_code == 200
    assert resp_interacao.json()["aprovado_para_dispensacao"] is False
