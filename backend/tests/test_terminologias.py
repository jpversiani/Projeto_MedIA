def test_buscar_ciap2_por_codigo_ou_termo(client):
    # Buscar por código K86 (Hipertensão)
    res = client.get("/api/v1/terminologias/ciap2?busca=K86")
    assert res.status_code == 200
    itens = res.json()
    assert len(itens) >= 1
    assert itens[0]["codigo"] == "K86"

    # Buscar por termo 'tosse'
    res_termo = client.get("/api/v1/terminologias/ciap2?busca=tosse")
    assert res_termo.status_code == 200
    itens_termo = res_termo.json()
    assert len(itens_termo) >= 1
    assert itens_termo[0]["codigo"] == "R05"

def test_buscar_cid10(client):
    res = client.get("/api/v1/terminologias/cid10?busca=I10")
    assert res.status_code == 200
    itens = res.json()
    assert len(itens) >= 1
    assert "Hipertensão" in itens[0]["descricao"]
