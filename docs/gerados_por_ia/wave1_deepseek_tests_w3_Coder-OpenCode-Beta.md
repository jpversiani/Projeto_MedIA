Vamos criar o arquivo de testes. Precisamos garantir que os testes sejam autônomos, ou seja, não dependam de um banco de dados real ou de serviços externos. Vamos usar dependências mockadas ou in-memory. Como a aplicação usa SQLAlchemy, podemos usar um banco SQLite em memória para os testes. Também precisamos garantir que o TestClient funcione com a app.

Primeiro, vamos analisar a estrutura do projeto. O arquivo principal é app.main:app. Vamos supor que a aplicação está configurada com um banco de dados e rotas. Para os testes, podemos sobrescrever a dependência de banco de dados com um banco em memória.

Vamos criar o arquivo backend/tests/test_api_telemedicina.py. Precisamos importar a app, criar um TestClient, e configurar um banco de dados temporário. Vamos usar pytest fixtures.

Como não temos o código da aplicação, vamos assumir que as rotas existem conforme descrito. Vamos escrever testes que façam chamadas HTTP e verifiquem respostas.

Para o teste de CPF inválido, esperamos erro 422. Para o fluxo SOAP, vamos simular as chamadas.

Vamos também garantir que os testes rodem de forma autônoma, ou seja, sem precisar de um servidor externo. Usaremos o TestClient que já cuida disso.

Vamos criar o arquivo com as fixtures e os testes.

Precisamos também garantir que o banco de dados seja criado e dropado entre testes. Usaremos SQLite em memória.

Vamos escrever o código.```python
# Arquivo: backend/tests/test_api_telemedicina.py
"""
Testes de integração para a API de Telemedicina do Projeto MedIA.

Estes testes utilizam pytest e TestClient do FastAPI, com um banco de dados
SQLite em memória para garantir autonomia e isolamento.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db  # Ajuste conforme a estrutura real


# Fixture para criar um banco de dados em memória e sobrescrever a dependência
@pytest.fixture(scope="function")
def client():
    # Configuração do banco em memória
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Cria as tabelas
    Base.metadata.create_all(bind=engine)

    # Sobrescreve a dependência get_db para usar o banco de teste
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # Limpa as tabelas após o teste
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


# Teste 1: Criar agendamento com sucesso
def test_criar_agendamento_sucesso(client):
    payload = {
        "paciente_cpf": "12345678901",  # CPF válido (apenas para teste)
        "paciente_nome": "Maria da Silva",
        "data_hora": "2025-04-10T14:30:00",
        "especialidade": "Clínico Geral",
        "medico_crm": "123456",
        "observacoes": "Paciente com sintomas de gripe"
    }
    response = client.post("/api/v1/telemedicina/agendamentos", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["paciente_cpf"] == payload["paciente_cpf"]
    assert data["status"] == "agendado"


# Teste 2: Consultar sala virtual
def test_consultar_sala_virtual(client):
    # Primeiro, criar um agendamento para obter um código de sala
    payload = {
        "paciente_cpf": "12345678901",
        "paciente_nome": "João Souza",
        "data_hora": "2025-04-11T10:00:00",
        "especialidade": "Cardiologia",
        "medico_crm": "654321",
        "observacoes": ""
    }
    create_resp = client.post("/api/v1/telemedicina/agendamentos", json=payload)
    assert create_resp.status_code == 201
    agendamento_id = create_resp.json()["id"]

    # Obter o código da sala (assumindo que o agendamento retorna um código)
    # Se não retornar, podemos buscar via GET /agendamentos/{id}
    # Vamos supor que o agendamento tenha um campo "codigo_sala"
    # Para simplificar, vamos buscar o agendamento e extrair o código
    get_resp = client.get(f"/api/v1/telemedicina/agendamentos/{agendamento_id}")
    assert get_resp.status_code == 200
    codigo_sala = get_resp.json().get("codigo_sala")
    assert codigo_sala is not None

    # Consultar a sala virtual
    response = client.get(f"/api/v1/telemedicina/salas/{codigo_sala}")
    assert response.status_code == 200
    data = response.json()
    assert data["codigo"] == codigo_sala
    assert "url" in data  # ou outro campo esperado


# Teste 3: Transição de fluxo de chamada com SOAP
def test_transicao_fluxo_chamada(client):
    # Criar um agendamento
    payload = {
        "paciente_cpf": "12345678901",
        "paciente_nome": "Ana Pereira",
        "data_hora": "2025-04-12T09:00:00",
        "especialidade": "Pediatria",
        "medico_crm": "111222",
        "observacoes": ""
    }
    create_resp = client.post("/api/v1/telemedicina/agendamentos", json=payload)
    assert create_resp.status_code == 201
    agendamento_id = create_resp.json()["id"]

    # Iniciar chamada (SOAP)
    start_payload = {
        "agendamento_id": agendamento_id,
        "tipo": "inicio",
        "dados_soap": {
            "subjetivo": "Paciente relata dor de cabeça",
            "objetivo": "PA 120/80, FC 80",
            "avaliacao": "Provável enxaqueca",
            "plano": "Prescrição de analgésico"
        }
    }
    start_resp = client.post("/api/v1/telemedicina/chamadas/iniciar", json=start_payload)
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "em_andamento"

    # Encerrar chamada (SOAP)
    end_payload = {
        "agendamento_id": agendamento_id,
        "tipo": "encerramento",
        "dados_soap": {
            "subjetivo": "Paciente relata melhora",
            "objetivo": "PA 120/80, FC 80",
            "avaliacao": "Evolução favorável",
            "plano": "Alta com orientações"
        }
    }
    end_resp = client.post("/api/v1/telemedicina/chamadas/encerrar", json=end_payload)
    assert end_resp.status_code == 200
    assert end_resp.json()["status"] == "encerrada"


# Teste 4: Validação de CPF inválido
def test_validacao_cpf_invalido(client):
    payload = {
        "paciente_cpf": "123",  # CPF inválido
        "paciente_nome": "Teste",
        "data_hora": "2025-04-13T15:00:00",
        "especialidade": "Dermatologia",
        "medico_crm": "999888",
        "observacoes": ""
    }
    response = client.post("/api/v1/telemedicina/agendamentos", json=payload)
    assert response.status_code == 422
    # Verifica se o erro contém detalhes sobre o campo CPF
    errors = response.json()["detail"]
    assert any("CPF" in error["msg"] for error in errors)
```