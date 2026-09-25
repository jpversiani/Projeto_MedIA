"""Testes dos endpoints REST do Prontuário do Cidadão (PEC e-SUS APS)."""

CNS_TESTE = "116809660000001"  # CNS definitivo válido (prefixo 1)
CNS_EVOLUCOES = "211680966000008"  # CNS definitivo válido (prefixo 2)


def _criar_cidadao(client, cns: str, cpf: str, alergias: str | None = None) -> int:
    """Cria um cidadão de teste e devolve o id."""
    payload = {
        "nome_completo": "Cidadão Prontuário Teste",
        "cpf": cpf,
        "cns": cns,
        "data_nascimento": "1975-03-10",
        "sexo": "M",
    }
    if alergias is not None:
        payload["alergias"] = alergias
    response = client.post("/api/v1/cidadaos/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_resumo_rejeita_cns_malformado(client):
    """CNS fora do formato de 15 dígitos deve gerar erro de validação (422)."""
    response = client.get("/api/v1/prontuario/1234")
    assert response.status_code == 422


def test_resumo_cns_nao_encontrado(client):
    """CNS bem formado porém inexistente deve retornar 404."""
    response = client.get("/api/v1/prontuario/998450013720001")
    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"]


def test_ciclo_completo_alergias_e_problemas(client):
    """Fluxo completo: registro de alergia e problema com validações de duplicidade."""
    _criar_cidadao(client, CNS_TESTE, "55566677788")

    # Registro de alergia (201)
    response = client.post(
        f"/api/v1/prontuario/{CNS_TESTE}/alergia", json={"descricao": "Penicilina"}
    )
    assert response.status_code == 201, response.text
    corpo = response.json()
    assert corpo["descricao"] == "Penicilina"
    assert corpo["alergias"] == ["Penicilina"]

    # Alergia duplicada (422)
    response = client.post(
        f"/api/v1/prontuario/{CNS_TESTE}/alergia", json={"descricao": "penicilina"}
    )
    assert response.status_code == 422

    # Alergia muito curta (422 de validação do schema)
    response = client.post(
        f"/api/v1/prontuario/{CNS_TESTE}/alergia", json={"descricao": "A"}
    )
    assert response.status_code == 422

    # Registro de problema CIAP-2 (201)
    response = client.post(
        f"/api/v1/prontuario/{CNS_TESTE}/problema",
        json={
            "tipo_codigo": "CIAP2",
            "codigo": "K86",
            "descricao": "Hipertensão arterial sem complicações",
        },
    )
    assert response.status_code == 201, response.text
    problema = response.json()
    assert problema["codigo"] == "K86"
    assert problema["situacao"] == "ATIVO"
    assert problema["data_registro"] is not None

    # Problema duplicado, mesmo com caixa diferente (422)
    response = client.post(
        f"/api/v1/prontuario/{CNS_TESTE}/problema",
        json={
            "tipo_codigo": "CIAP2",
            "codigo": "k86",
            "descricao": "Hipertensão arterial sem complicações",
        },
    )
    assert response.status_code == 422

    # Código fora do padrão oficial da terminologia (422)
    response = client.post(
        f"/api/v1/prontuario/{CNS_TESTE}/problema",
        json={
            "tipo_codigo": "CID10",
            "codigo": "I1000",
            "descricao": "Código CID-10 malformado",
        },
    )
    assert response.status_code == 422

    # Tipo de código fora do padrão SUS (422)
    response = client.post(
        f"/api/v1/prontuario/{CNS_TESTE}/problema",
        json={
            "tipo_codigo": "CID9",
            "codigo": "I10",
            "descricao": "Terminologia não suportada",
        },
    )
    assert response.status_code == 422

    # Resumo deve trazer o problema ativo e a alergia registrada
    response = client.get(f"/api/v1/prontuario/{CNS_TESTE}")
    assert response.status_code == 200
    resumo = response.json()
    assert resumo["cidadao"]["cns"] == CNS_TESTE
    assert resumo["alergias"] == ["Penicilina"]
    assert len(resumo["problemas_ativos"]) == 1
    ativo = resumo["problemas_ativos"][0]
    assert ativo["tipo_codigo"] == "CIAP2"
    assert ativo["codigo"] == "K86"
    assert ativo["origem"] == "PRONTUARIO"
    assert resumo["total_atendimentos"] == 0
    assert resumo["data_ultimo_atendimento"] is None


def test_evolucoes_paginado_e_medicamentos_em_uso(client):
    """Evoluções paginadas (SOAP) e medicamentos em uso derivados das prescrições."""
    cidadao_id = _criar_cidadao(client, CNS_EVOLUCOES, "77788899900")

    prescricao = (
        "Losartana Potássica 50mg - 30 comprimidos\n"
        "Metformina 850mg - 60 comprimidos"
    )
    for _ in range(2):
        response = client.post(
            "/api/v1/atendimentos/",
            json={
                "cidadao_id": cidadao_id,
                "profissional_id": 1,
                "estabelecimento_id": 1,
                "plano_prescricoes": prescricao,
                "problemas": [
                    {
                        "tipo_codigo": "CID10",
                        "codigo": "I10",
                        "descricao": "Hipertensão essencial (primária)",
                        "situacao": "ATIVO",
                    }
                ],
            },
        )
        assert response.status_code == 201, response.text

    # Resumo: medicamentos em uso sem duplicidade + episódio ativo do atendimento
    response = client.get(f"/api/v1/prontuario/{CNS_EVOLUCOES}")
    assert response.status_code == 200
    resumo = response.json()
    assert resumo["total_atendimentos"] == 2
    nomes = {m["nome"] for m in resumo["medicamentos_em_uso"]}
    assert nomes == {"Losartana Potássica 50mg", "Metformina 850mg"}
    assert resumo["data_ultimo_atendimento"] is not None
    origens_atendimento = [
        p for p in resumo["problemas_ativos"] if p["origem"] == "ATENDIMENTO"
    ]
    assert any(p["codigo"] == "I10" for p in origens_atendimento)

    # Paginação: página única com 1 item e total 2
    response = client.get(f"/api/v1/prontuario/{CNS_EVOLUCOES}/evolucoes?skip=0&limit=1")
    assert response.status_code == 200
    pagina = response.json()
    assert pagina["total"] == 2
    assert pagina["skip"] == 0
    assert pagina["limit"] == 1
    assert len(pagina["itens"]) == 1
    assert pagina["itens"][0]["plano_prescricoes"] == prescricao
    assert len(pagina["itens"][0]["problemas"]) == 1

    # Segunda página traz a outra evolução
    response = client.get(f"/api/v1/prontuario/{CNS_EVOLUCOES}/evolucoes?skip=1&limit=1")
    assert response.status_code == 200
    pagina2 = response.json()
    assert len(pagina2["itens"]) == 1
    assert pagina2["itens"][0]["id"] != pagina["itens"][0]["id"]

    # Limite inválido (0 ou acima do máximo) deve gerar 422
    assert client.get(f"/api/v1/prontuario/{CNS_EVOLUCOES}/evolucoes?limit=0").status_code == 422
    assert client.get(f"/api/v1/prontuario/{CNS_EVOLUCOES}/evolucoes?limit=101").status_code == 422

    # Evoluções de CNS inexistente retornam 404
    assert client.get("/api/v1/prontuario/998450013720001/evolucoes").status_code == 404