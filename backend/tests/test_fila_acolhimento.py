def test_acolhimento_e_calculo_imc(client):
    # Cidadão ID 1 já foi inserido pelo seed
    payload = {
        "cidadao_id": 1,
        "estabelecimento_id": 1,
        "classificacao_risco": "AMARELO",
        "tipo_demanda": "ESPONTANEA",
        "motivo_acolhimento": "Pico hipertensivo e cefaleia occipital",
        "pressao_sistolica": 160,
        "pressao_diastolica": 100,
        "frequencia_cardiaca": 88,
        "temperatura": 36.8,
        "peso_kg": 80.0,
        "altura_cm": 175.0
    }
    response = client.post("/api/v1/fila/", json=payload)
    assert response.status_code == 201
    item = response.json()
    assert item["classificacao_risco"] == "AMARELO"
    assert item["status"] == "AGUARDANDO_ATENDIMENTO"
    # IMC = 80 / (1.75^2) = 26.12
    assert item["imc"] is not None
    assert round(item["imc"], 1) == 26.1

def test_listar_fila_aguardando(client):
    response = client.get("/api/v1/fila/?status=AGUARDANDO_ATENDIMENTO")
    assert response.status_code == 200
    lista = response.json()
    assert len(lista) >= 1
    assert lista[0]["cidadao"] is not None
