"""
Testes automatizados para a persistência e consulta do TCLE
em conformidade com a Resolução CFM nº 2.314/2022 e LGPD (Lei 13.709/2018).
"""

from app.models.telemedicina import ConsentimentoTCLE


def test_tcle_registro_persistente_no_banco(client):
    """Testa o registro do TCLE garantindo que é gravado no banco de dados."""
    cpf_teste = "987.654.321-09"
    payload = {
        "paciente_nome": "Carlos Drummond de Andrade",
        "paciente_cpf": cpf_teste,
        "metodo": "ELETRONICO_WEB",
    }

    # 1. Antes de registrar, consulta de status deve indicar NÃO REGISTRADO
    res_status_antes = client.get(f"/api/v1/telemedicina/tcle/status/{cpf_teste}")
    assert res_status_antes.status_code == 200
    dados_antes = res_status_antes.json()
    assert dados_antes["tem_consentimento"] is False
    assert dados_antes["status"] == "NAO_REGISTRADO"

    # 2. Registra o consentimento
    res_reg = client.post(
        "/api/v1/telemedicina/tcle/registrar",
        json=payload,
        headers={"User-Agent": "Pytest/CFM-Auditor"},
    )
    assert res_reg.status_code == 200
    dados_reg = res_reg.json()
    assert dados_reg["status"] == "VALIDADO_CFM_2314"
    assert dados_reg["paciente_cpf"] == "98765432109"
    assert "hash_tcle" in dados_reg
    assert len(dados_reg["hash_tcle"]) == 64  # SHA-256
    assert "ip_origem" in dados_reg

    # 3. Após registrar, consulta de status deve indicar VALIDADO_CFM_2314
    res_status_depois = client.get(f"/api/v1/telemedicina/tcle/status/{cpf_teste}")
    assert res_status_depois.status_code == 200
    dados_depois = res_status_depois.json()
    assert dados_depois["tem_consentimento"] is True
    assert dados_depois["hash_tcle"] == dados_reg["hash_tcle"]
    assert dados_depois["status"] == "VALIDADO_CFM_2314"
    assert dados_depois["versao_termo"] == "CFM_2314_2022_V1"


def test_tcle_registro_com_texto_integral_personalizado(client):
    """Testa registro de TCLE com texto fornecido diretamente."""
    cpf_teste = "11122233344"
    texto_especifico = "Termo específico de teleconsulta com riscos de ausência de palpação física."
    payload = {
        "paciente_nome": "Ana Lins dos Guimarães Peixoto",
        "paciente_cpf": cpf_teste,
        "metodo": "ASSINATURA_DIGITAL",
        "texto_integral": texto_especifico,
    }

    res = client.post("/api/v1/telemedicina/tcle/registrar", json=payload)
    assert res.status_code == 200
    dados = res.json()
    assert dados["paciente_cpf"] == "11122233344"
    assert dados["metodo_aceite"] == "ASSINATURA_DIGITAL"
    assert dados["status"] == "VALIDADO_CFM_2314"

    # Confere status
    res_status = client.get(f"/api/v1/telemedicina/tcle/status/{cpf_teste}")
    assert res_status.status_code == 200
    assert res_status.json()["tem_consentimento"] is True
