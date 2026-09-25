import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, engine, get_db
from sqlalchemy.orm import sessionmaker

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


def test_criar_agendamento_sucesso(client):
    payload = {
        "paciente_cpf": "12345678901",
        "medico_crm": "123456",
        "data_hora": datetime.now(timezone.utc).isoformat(),
        "ciap2": "R74",
        "cid10": "J00"
    }
    response = client.post("/api/v1/telemedicina/agendamentos", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "codigo_sala" in data
    assert data["paciente_cpf"] == "12345678901"
    assert data["status"] == "AGENDADA"


def test_consultar_sala_virtual(client):
    payload = {
        "paciente_cpf": "98765432100",
        "medico_crm": "654321",
        "data_hora": datetime.now(timezone.utc).isoformat(),
    }
    create_res = client.post("/api/v1/telemedicina/agendamentos", json=payload)
    assert create_res.status_code == 201
    codigo_sala = create_res.json()["codigo_sala"]

    res = client.get(f"/api/v1/telemedicina/salas/{codigo_sala}")
    assert res.status_code == 200
    data = res.json()
    assert data["codigo"] == codigo_sala
    assert data["paciente_cpf"] == "98765432100"


def test_transicao_fluxo_chamada(client):
    payload = {
        "paciente_cpf": "11122233344",
        "medico_crm": "112233",
        "data_hora": datetime.now(timezone.utc).isoformat(),
    }
    create_res = client.post("/api/v1/telemedicina/agendamentos", json=payload)
    consulta_id = create_res.json()["id"]

    # Iniciar chamada
    init_res = client.post("/api/v1/telemedicina/iniciar-chamada", json={"teleconsulta_id": consulta_id})
    assert init_res.status_code == 200
    assert init_res.json()["status"] == "EM_ANDAMENTO"

    # Finalizar chamada com SOAP
    soap = {
        "subjetivo": "Paciente relata tosse seca há 3 dias",
        "objetivo": "Afebril, murmúrio vesicular universalmente audível",
        "avaliacao": "Infecção de vias aéreas superiores",
        "plano": "Hidratação oral e sintomáticos",
    }
    fin_res = client.post(
        "/api/v1/telemedicina/finalizar-chamada",
        json={"teleconsulta_id": consulta_id, "dados_soap": soap}
    )
    assert fin_res.status_code == 200
    assert fin_res.json()["status"] == "CONCLUIDA"


def test_validacao_cpf_invalido(client):
    payload = {
        "paciente_cpf": "123",  # Inválido (< 11 dígitos)
        "medico_crm": "123456",
        "data_hora": datetime.now(timezone.utc).isoformat(),
    }
    response = client.post("/api/v1/telemedicina/agendamentos", json=payload)
    assert response.status_code == 422
