def test_copilot_gerar_soap_ivas(client):
    payload = {
        "relato_clinico": "Paciente com tosse produtiva e dor de garganta há 2 dias. Nega febre.",
        "pressao_aferida": "120/80"
    }
    res = client.post("/api/v1/copilot/gerar-soap", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "Sintomas respiratórios" in data["subjetivo_motivo"]
    assert "IVAS" in data["avaliacao_notas"]
    assert len(data["problemas_sugeridos"]) >= 2
    codigos = [p["codigo"] for p in data["problemas_sugeridos"]]
    assert "R74" in codigos
    assert "J00" in codigos

def test_copilot_bloqueio_alergia(client):
    # Cidadão ID 1 tem alergia a Dipirona cadastrada no seed
    payload = {
        "cidadao_id": 1,
        "relato_clinico": "Paciente hipertenso relatando forte dor de cabeça na nuca hoje.",
        "pressao_aferida": "160/100"
    }
    res = client.post("/api/v1/copilot/gerar-soap", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert any("BLOQUEIO DE SEGURANÇA" in alerta for alerta in data["alertas_seguranca"])
    assert "Dipirona" not in data["plano_prescricoes"]
    assert "Paracetamol" in data["plano_prescricoes"]
