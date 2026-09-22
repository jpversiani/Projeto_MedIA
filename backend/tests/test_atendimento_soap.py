def test_atendimento_soap_com_ciap2_e_cid10(client):
    # Criar um acolhimento inicial
    resp_fila = client.post("/api/v1/fila/", json={
        "cidadao_id": 1,
        "estabelecimento_id": 1,
        "classificacao_risco": "VERDE",
        "motivo_acolhimento": "Consulta de rotina hipertensão",
        "pressao_sistolica": 130,
        "pressao_diastolica": 85
    })
    fila_id = resp_fila.json()["id"]

    # Registrar Atendimento Clínico SOAP
    payload_soap = {
        "cidadao_id": 1,
        "profissional_id": 1,
        "estabelecimento_id": 1,
        "fila_id": fila_id,
        "subjetivo_motivo": "Acompanhamento de HAS",
        "subjetivo_notas": "Paciente relata boa adesão à medicação, sem queixas no momento.",
        "objetivo_exame_fisico": "BEG, eupneico, ACV RCR em 2T sem sopros, AP MVF sem RA.",
        "avaliacao_notas": "Hipertensão controlada em monoterapia.",
        "plano_conduta": "Manter Losartana 50mg 1x ao dia. Retorno em 3 meses.",
        "plano_prescricoes": "Losartana Potássica 50mg - 30 comprimidos",
        "problemas": [
            {
                "tipo_codigo": "CIAP2",
                "codigo": "K86",
                "descricao": "Hipertensão arterial sem complicações",
                "situacao": "ATIVO"
            },
            {
                "tipo_codigo": "CID10",
                "codigo": "I10",
                "descricao": "Hipertensão essencial (primária)",
                "situacao": "ATIVO"
            }
        ]
    }

    response = client.post("/api/v1/atendimentos/", json=payload_soap)
    assert response.status_code == 201
    atend = response.json()
    assert atend["id"] is not None
    assert len(atend["problemas"]) == 2
    assert atend["problemas"][0]["codigo"] in ["K86", "I10"]

    # Verificar se a fila foi atualizada para FINALIZADO
    resp_fila_check = client.get(f"/api/v1/fila/{fila_id}")
    assert resp_fila_check.json()["status"] == "FINALIZADO"

    # Verificar se o histórico do cidadão agora inclui o atendimento
    resp_hist = client.get("/api/v1/cidadaos/1/historico")
    assert resp_hist.status_code == 200
    historico = resp_hist.json()
    assert len(historico) >= 1
    assert historico[0]["subjetivo_motivo"] == "Acompanhamento de HAS"

    # Testar exportação oficial FAI (Layout e-SUS APS de Dados e Interface)
    resp_fai = client.get(f"/api/v1/atendimentos/{atend['id']}/exportar-fai")
    assert resp_fai.status_code == 200
    fai = resp_fai.json()
    assert fai["cabecalho"]["tipoDadoSerializado"] == 7
    assert fai["cabecalho"]["cnesDadoSerializado"] == "3180115"
    assert "K86" in fai["fichaAtendimentoIndividualMaster"]["atendimentosIndividuais"][0]["problemaCondicaoAvaliada"]["ciap2"]

