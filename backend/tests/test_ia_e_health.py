from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_healthcheck_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "uptime_segundos" in data

def test_gerar_soap_ia_endpoint():
    payload = {
        "texto_bruto": "Paciente refere dor de cabeça pulsátil há 2 dias, náusea e fotofobia. PA 120x80 mmHg. Prescrito dipirona 1g.",
        "paciente_nome": "Maria Santos"
    }
    response = client.post("/api/v1/copiloto/ia/gerar-soap", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "subjetivo_hda" in data
    assert "avaliacao_raciocinio" in data
    assert "plano_prescricao" in data
    assert data["motor_utilizado"] is not None

def test_diagnostico_diferencial_ia_endpoint():
    payload = {
        "sintomas": "Febre alta, tosse produtiva e dispneia"
    }
    response = client.post("/api/v1/copiloto/ia/diagnostico-diferencial", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "cid10" in data[0]
    assert "descricao" in data[0]
