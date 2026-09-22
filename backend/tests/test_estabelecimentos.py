def test_listar_estabelecimentos(client):
    res = client.get("/api/v1/estabelecimentos")
    assert res.status_code == 200
    estabelecimentos = res.json()
    assert estabelecimentos[0]["cnes"] == "3180115"
    assert "CRISTO REI" in estabelecimentos[0]["nome_fantasia"]
    assert len(estabelecimentos[0]["equipes"]) >= 1

def test_listar_profissionais(client):
    res = client.get("/api/v1/profissionais")
    assert res.status_code == 200
    profs = res.json()
    assert len(profs) >= 2
    nomes = [p["nome"] for p in profs]
    assert any("Dra. Francelli Neves Versiani" in n for n in nomes)
