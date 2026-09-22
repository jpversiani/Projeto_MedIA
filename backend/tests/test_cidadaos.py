def test_listar_cidadaos_com_seed(client):
    response = client.get("/api/v1/cidadaos/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("Sebastião" in c["nome_completo"] for c in data)

def test_criar_cidadao_valido(client):
    payload = {
        "nome_completo": "Maria Francisca de Oliveira",
        "cpf": "98765432199",
        "cns": "898000987654321",
        "data_nascimento": "1980-10-25",
        "sexo": "F",
        "raca_cor": "Branca",
        "telefone": "38988776655",
        "hipertenso": True,
        "diabetico": True,
        "alergias": "Penicilina"
    }
    response = client.post("/api/v1/cidadaos/", json=payload)
    assert response.status_code == 201
    criado = response.json()
    assert criado["nome_completo"] == payload["nome_completo"]
    assert criado["hipertenso"] is True
    assert criado["id"] is not None

def test_evitar_cpf_duplicado(client):
    payload = {
        "nome_completo": "Duplicado Teste",
        "cpf": "98765432199", # mesmo CPF do teste anterior
        "data_nascimento": "1990-01-01",
        "sexo": "M"
    }
    response = client.post("/api/v1/cidadaos/", json=payload)
    assert response.status_code == 400
    assert "CPF já cadastrado" in response.json()["detail"]
