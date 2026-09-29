from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_emitir_prescricao_e_download_pdf():
    # 1. Emitir prescrição
    payload = {
        "paciente_nome": "Mariana Souza Alencar",
        "paciente_cpf": "12345678901",
        "medico_nome": "Dr. João Paulo Versiani",
        "medico_crm": "78421",
        "medico_uf": "MG",
        "tipo": "SIMPLES",
        "itens": [
            {
                "farmaco": "Escitalopram",
                "concentracao": "10mg",
                "posologia": "Tomar 1 cp ao dia",
                "quantidade_total": "1 cx",
            }
        ],
        "instrucoes_gerais": "Uso contínuo.",
    }
    res = client.post("/api/v1/prescricao/emitir", json=payload)
    assert res.status_code == 201
    dados = res.json()
    codigo = dados["codigo_validacao"]
    assert "CFM-" in codigo
    assert "url_pdf" in dados
    assert "url_validacao_publica" in dados

    # 2. Baixar PDF
    res_pdf = client.get(f"/api/v1/prescricao/{codigo}/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF-")

    # 3. Validar HTML
    res_html = client.get(f"/api/v1/prescricao/validar-html/{codigo}")
    assert res_html.status_code == 200
    assert "Mariana Souza Alencar" in res_html.text
    assert "DOCUMENTO MÉDICO VÁLIDO" in res_html.text


def test_emitir_atestado_e_download_pdf():
    # 1. Emitir atestado
    payload = {
        "paciente_nome": "Carlos Roberto Prado",
        "paciente_cpf": "98765432100",
        "medico_nome": "Dr. João Paulo Versiani",
        "medico_crm": "78421",
        "medico_uf": "MG",
        "dias_afastamento": 5,
        "cid10": "J06.9",
    }
    res = client.post("/api/v1/prescricao/atestado/emitir", json=payload)
    assert res.status_code == 201
    dados = res.json()
    codigo = dados["codigo_validacao"]
    assert "ATE-" in codigo

    # 2. Baixar PDF Atestado
    res_pdf = client.get(f"/api/v1/prescricao/atestado/{codigo}/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF-")

    # 3. Validar HTML Atestado
    res_html = client.get(f"/api/v1/prescricao/validar-html/{codigo}")
    assert res_html.status_code == 200
    assert "Carlos Roberto Prado" in res_html.text
    assert "Atestado Médico Digital" in res_html.text
