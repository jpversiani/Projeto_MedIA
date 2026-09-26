import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_listar_agenda_geral():
    response = client.get("/api/v1/agenda/")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "consultas" in data
    assert data["total"] >= 5
    assert data["total_presencial"] >= 1
    assert data["total_telemedicina"] >= 1


def test_filtrar_agenda_telemedicina():
    response = client.get("/api/v1/agenda/?tipo=TELEMEDICINA")
    assert response.status_code == 200
    data = response.json()
    for c in data["consultas"]:
        assert c["tipo"] == "TELEMEDICINA"
        assert c["codigo_sala_telemedicina"] is not None


def test_filtrar_agenda_presencial():
    response = client.get("/api/v1/agenda/?tipo=PRESENCIAL")
    assert response.status_code == 200
    data = response.json()
    for c in data["consultas"]:
        assert c["tipo"] == "PRESENCIAL"


def test_criar_agendamento_consulta_telemedicina():
    payload = {
        "paciente_nome": "Beatriz Viana",
        "paciente_cpf": "99988877766",
        "telefone_whatsapp": "38999998888",
        "email": "beatriz.viana@email.com",
        "tipo": "TELEMEDICINA",
        "horario": "16:30",
        "especialidade": "Dermatologia",
        "motivo_queixa": "Mancha solar na face",
        "valor_consulta": 350.00
    }
    response = client.post("/api/v1/agenda/novo", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("AG-")
    assert data["paciente_nome"] == "Beatriz Viana"
    assert data["status"] == "AGENDADO"
    assert data["codigo_sala_telemedicina"].startswith("sala_")


def test_atualizar_status_consulta():
    response = client.patch("/api/v1/agenda/AG-01/status?novo_status=EM_CONSULTA")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "EM_CONSULTA"
