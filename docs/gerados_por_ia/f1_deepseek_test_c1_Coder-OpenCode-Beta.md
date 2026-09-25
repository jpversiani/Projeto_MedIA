Vamos criar o arquivo de testes conforme solicitado. Precisamos entender o projeto MedIA. O arquivo é backend/tests/test_telemedicina_lifecycle.py. Vamos supor que o Projeto MedIA tem uma aplicação FastAPI com rotas de telemedicina. Precisamos escrever testes para:

1) criação de sala com expiração;
2) rejeição de salas duplicadas;
3) ciclo de status da consulta (AGENDADA -> EM_ANDAMENTO -> CONCLUIDA).

Vamos verificar a estrutura existente? Não temos acesso. Precisamos criar testes que sejam plausíveis. Mas o usuário pede para criar testes pytest validando esses comportamentos. Devemos fornecer código completo. Provavelmente precisamos importar os módulos do backend. Mas como não temos o código, podemos criar testes que utilizem a API via TestClient do FastAPI, ou testar diretamente as funções de serviço.

Precisamos usar boas práticas: Pydantic v2, SQLAlchemy 2.0. Como são testes, podemos usar um banco de dados SQLite em memória, talvez. Vamos supor que existe um app FastAPI em backend/app/main.py, com rotas em backend/app/api/v1/telemedicina.py. Vamos criar testes que:

- Usam TestClient para chamar endpoints.
- Criam uma sala (POST /telemedicina/salas) e verificam expiração.
- Tentam criar duplicata e verificam rejeição.
- Atualizam status da consulta.

Vamos verificar se existem endpoints específicos. Como não temos, podemos fazer testes em nível de serviço, mas o pedido diz "testes de conexão WebSocket e ciclo de vida da sala". No título: "Testes de Conexão WebSocket e Ciclo de Vida da Sala (C1)". Portanto, deve incluir WebSocket? A tarefa apenas lista 3 itens: criação com expiração, duplicatas, ciclo de status. Não menciona WebSocket diretamente, mas o título fala. Talvez o teste 1 envolva criação de sala e expiração; 2 rejeição; 3 ciclo de status. Não há WebSocket. Mas o título pode ser genérico. Vou focar nos 3 itens.

Vamos criar um arquivo de teste com fixtures, talvez um banco de testes. Precisamos garantir que é executável. Como não conhecemos o modelo, podemos definir schemas e serviços fictícios? Mas seria melhor usar a estrutura real. No entanto, a instrução diz "crie backend/tests/test_telemedicina_lifecycle.py com testes pytest validando..." Então devemos fornecer código que provavelmente será executado no contexto do projeto. Precisamos fazer suposições razoáveis.

Vou supor que o projeto tem:

- Um modelo SQLAlchemy `Consulta` com campos: id, paciente_id, medico_id, status (enum com AGENDADA, EM_ANDAMENTO, CONCLUIDA), data_hora_inicio, data_hora_fim, etc.
- Uma sala de telemedicina é uma entidade com `token`, `expira_em`, `consulta_id` etc.

Mas não temos detalhes. Vamos criar testes que interagem com a API via TestClient, usando um banco de testes. Para isso, precisamos da aplicação FastAPI. Vamos importar `from fastapi.testclient import TestClient` e `from backend.app.main import app`. Mas isso pode falhar se o caminho não estiver correto. No projeto, geralmente a raiz é backend/, então `from app.main import app` pode funcionar se estiver no diretório raiz. Para robustez, vamos usar imports relativos ao contexto do teste: `from app.database import SessionLocal, Base, engine` etc. Mas como não temos o arquivo, é arriscado.

Uma alternativa é projetar os testes para serem executados com o pytest diretamente, sem depender de implementação existente, mas isso não valida nada. O objetivo é validar funcionalidades reais. Portanto, precisamos escrever testes que acessem funções/classes que existem no projeto.

Como não temos o código, não posso gerar testes fiéis. Talvez eu possa fornecer um esqueleto com mocks, mas o usuário pede para executar com precisão. Vou assumir que o projeto segue padrões comuns: há um CRUD de salas em `backend/app/services/telemedicina_service.py` com funções `criar_sala`, `obter_sala`, etc. Vou criar testes que usam essas funções com um banco de teste.

Ou, melhor, posso fornecer um arquivo de teste que define as funcionalidades de teste usando `pytest` juntamente com `unittest.mock`. Mas seria artificial.

Vou reler a tarefa: "TAREFA: Testes de Conexão WebSocket e Ciclo de Vida da Sala (C1)" e os itens não mencionam WebSocket. Talvez "Conexão WebSocket" esteja implícito na criação de sala? Não sei.

Como agente, devo fornecer código que atenda às diretrizes. Vou escrever um arquivo de teste completo, mas comentarei que assume a existência de determinados módulos. Posso usar uma estrutura de teste com fixture de banco de dados, usando SQLAlchemy com SQLite em memória. Crio modelos fictícios? Mas isso não testaria a aplicação real.

A melhor abordagem é escrever testes que usem a API via TestClient, e configurar o banco de dados para testes. Vou incluir instruções de como rodar. No arquivo, importo `from backend.app.main import app`? Se a estrutura é `backend/` como raiz do projeto, `backend/app/main.py` teria `app`. Em `backend/tests/` os imports podiam ser `from app.main import app` (se `backend` for o projeto). Normalmente, quando se executa `pytest` de dentro de `backend/`, o diretório atual é `backend`, então `app` é um pacote.

Então:

```python
from app.main import app
from fastapi.testclient import TestClient
```

Mas cuidado: `app` pode ser uma instância de FastAPI. Vamos assumir.

Precisamos de um banco de dados de teste. Podemos usar `dependency_overrides` para substituir a dependência do banco. Ou criar uma fixture que cria as tabelas em SQLite.

Vou fazer algo assim:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import Consulta, Sala  # assumindo que existem
```

Mas precisamos conhecer os modelos. Talvez não existam. Vou criar modelos minimalistas no próprio teste? Isso não ajudaria.

Outra ideia: escrever testes de integração que usam chamadas HTTP para a API, e para o banco usar um SQLite temporário. Mas se o app não estiver configurado para aceitar override, precisa de hooks.

Vou fornecer um código que define a fixture `client` usando `TestClient` e usando um banco PostgreSQL ou SQLite real? Usar SQLite em memória é fácil. Mas o app pode ter configurações que exigem PostgreSQL. Para testes, muitos projetos usam SQLite.

Vou criar um arquivo que faz o seguinte:

- Define `engine` e `TestingSessionLocal` para SQLite em memoria.
- Cria as tabelas `Base.metadata.create_all`.
- Override da dependência `get_db`.

Assim, os testes podem acessar os modelos diretamente ou via API.

Vou precisar dos modelos e schemas. Como não os conheço, vou definir modelos baseados nas suposições. Mas o teste deve ser executado no projeto MedIA real; se os modelos não baterem, falhará. Talvez o ideal seja criar um teste que use os modelos existentes, assumindo nomes. Vou fazer suposições e documentar.

Vou criar um arquivo de teste que:

1. Testa criação de sala com expiração:
   - Envia POST para `/api/v1/telemedicina/salas` com dados de consulta.
   - Verifica que retorna `token` e `expira_em` no futuro.
   - Verifica que a sala foi criada no banco com expiração correta.

2. Rejeição de salas duplicadas:
   - Tenta criar outra sala para a mesma consulta, esperando 409.

3. Ciclo de status da consulta:
   - Cria consulta com status AGENDADA.
   - Atualiza para EM_ANDAMENTO.
   - Atualiza para CONCLUIDA.
   - Verifica cada transição.

Vou supor endpoints:
- POST /telemedicina/salas (criar sala)
- GET /telemedicina/salas/{id} (obter sala)
- PATCH /telemedicina/consultas/{id}/status (atualizar status)
- GET /telemedicina/consultas/{id}

Mas não sei. Vou definir rotas comuns.

Na falta de código real, vou fornecer testes que podem ser adaptados. O usuário pede "Execute com precisão conforme as diretrizes." Acho que ele quer que eu escreva o código da melhor forma possível, assumindo a estrutura típica.

Vou incluir no arquivo um comentário explicando que ele deve ser adaptado se necessário.

Vamos escrever o código.

Estrutura do arquivo:

```python
"""
Testes de ciclo de vida da sala de telemedicina.
Cobre criação com expiração, rejeição de duplicidade e ciclo de status.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importar app e modelos reais
from app.main import app
from app.core.database import Base, get_db
from app.models.telemedicina import Consulta, SalaTelemedicina
from app.schemas.telemedicina import ...
```

Isso pode falhar. Para evitar, vou usar um approach que não dependa de importações de módulos que podem não existir, mas sim de um mock da camada de serviço. Mas o pedido é criar testes para validar funcionalidades reais. Hmm.

Talvez eu possa criar testes unitários dos serviços, mockando a sessão de banco. Mas seria menos integrado.

Vou optar por uma abordagem de testes de integração usando TestClient e um banco fictício criado via models definidos no próprio teste? Não.

Vou escrever um arquivo que define fixtures e testes, mas usando `pytest-mock` para mockar as funções de serviço, e assim não precisar de banco real. Mas isso não testaria integração.

A tarefa diz "crie backend/tests/test_telemedicina_lifecycle.py com testes pytest validando: 1) criação de sala com expiração; ...". Isso deve ser um arquivo de teste que será executado pelo pytest. Deve ser robusto.

Vamos supor que o projeto MedIA tem uma estrutura semelhante a:

```
backend/
  app/
    main.py
    api/
      v1/
        telemedicina.py
    models/
    schemas/
    services/
    core/
  tests/
```

Então faz sentido escrever:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app
```

Mas não conheço `app.database`. Talvez seja `app.core.database`. Vou usar `app.database` como padrão.

Preciso de um banco de teste. Vou fazer:

```python
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
```

Preciso importar `get_db` de onde? De `app.database`. Se não existir, falha.

Outra abordagem: não usar banco, apenas testar via HTTP mockando o serviço. Mas é menos valioso.

Acho que o mais seguro é escrever um teste que usa a API real, mas com um banco SQLite. Vou assumir que o app está configurado para usar PostgreSQL, mas podemos sobrescrever. Vou incluir no código `from app.db.session import Base, get_db` ou algo assim.

Como não tenho certeza, vou fornecer um código com imports flexíveis? Não existe isso em Python.

Talvez o usuário espera que eu procure a estrutura do projeto e crie o teste de acordo. Como não tenho acesso, devo fornecer um template que provavelmente precisa de ajustes. Mas a instrução pede para "Execute com precisão", então devo fazer o melhor possível.

Vou criar um arquivo de teste que não depende de nenhum código específico além de `pytest`, e testa as lógicas usando mocks e testes unitários de funções que eu mesmo defino? Mas não valida o projeto.

Decisão: Vou escrever um arquivo de teste que usa `pytest` e `unittest.mock` para testar funções de serviço `criar_sala`, `rejeitar_duplicada`, `transicionar_status`. Vou importá-los de `app.services.telemedicina`. Se não existirem, o teste falhará na importação, mas o usuário pode ajustar. Vou dar exemplos com a estrutura esperada.

Vou fazer um arquivo:

```python
from datetime import datetime, timedelta
import pytest
from unittest.mock import MagicMock, patch
from app.services.telemedicina import criar_sala, atualizar_status_consulta
from app.models.enums import StatusConsulta
```

Mas novamente, dependo de imports.

Talvez seja melhor criar um teste que valide os endpoints da API, pois são mais estáveis.

Vou escolher criar testes de integração com FastAPI TestClient, e usar `dependency_overrides` com um banco simulado. Para isso, preciso saber o nome da função de dependência. Em FastAPI, é comum:

```python
from app.database import SessionLocal, engine, Base, get_db
```

Vou assumir que está assim.

Agora, vou precisar definir os models para o teste? Não, a tabela será criada a partir dos models existentes. Se os models existirem, funcionará. Mas se o banco SQLite não suportar os tipos específicos do PostgreSQL, pode falhar. Mas podemos usar `sqlite://` com `StaticPool` para resolver.

Vou incluir no código:

```python
import os
os.environ["DATABASE_URL"] = "sqlite://"
```

Antes de importar o app, para que a configuração use SQLite. Mas o app pode ler de `.env`. Complicated.

Vou escrever um código mais genérico:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configuração do banco de teste
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Importar app e Base após config
import app.main
from app.database import Base, get_db  # Ajuste conforme estrutura real
```

Isso é razoável.

Agora, vamos definir os testes.

Para testar criação de sala com expiração:
- Precisamos ter uma consulta existente. Vamos criar um paciente e médico? Sim, mas isso pode complicar. Podemos simplesmente criar uma consulta diretamente via ORM.
- Vamos usar `TestingSessionLocal` para inserir dados no banco antes de chamar a API.

Mas o teste deve ser isolado. Vamos usar fixtures que criam os dados.

Vou criar uma fixture `db_session` que cria as tabelas e fornece uma sessão.

```python
@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
```

Mas se usarmos `dependency_overrides` global, o banco será recriado a cada teste? Pode ser melhor criar em fixture.

Vou fazer assim:

```python
@pytest.fixture(scope="function")
def client(db_session):
    # Override da dependência
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
```

No entanto, `db_session` precisa ser uma sessão com escopo. Vou criar uma função que cria uma nova sessão por teste.

Vamos estruturar:

```python
@pytest.fixture()
def db_engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db_session(db_engine):
    TestSession = sessionmaker(bind=db_engine)
    session = TestSession()
    yield session
    session.close()
```

Mas o override deve usar essa sessão. Vamos criar uma factory:

```python
@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

Ok.

Agora, precisamos inserir dados de paciente, médico, consulta. Vou supor models: `Paciente`, `Medico`, `Consulta`. Vou criar esses registros.

Vou usar `db_session` para adicionar.

Vou escrever helpers:

```python
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.consulta import Consulta
from app.models.sala import SalaTelemedicina
from app.models.enums import StatusConsulta
```

Vou usar essas importações. Se os modelos forem diferentes, ajuste.

Vou criar um fixture para criar uma consulta com status AGENDADA:

```python
@pytest.fixture()
def consulta_agendada(db_session):
    paciente = Paciente(nome="João", cpf="12345678900", ...)
    medico = Medico(nome="Dr. Ana", crm="12345", ...)
    db_session.add(paciente)
    db_session.add(medico)
    db_session.flush()
    consulta = Consulta(
        paciente_id=paciente.id,
        medico_id=medico.id,
        status=StatusConsulta.AGENDADA,
        data_inicio=datetime.now(timezone.utc) + timedelta(hours=1),
        data_fim=None,
    )
    db_session.add(consulta)
    db_session.commit()
    db_session.refresh(consulta)
    return consulta
```

Mas isso pode falhar se os campos não forem esses. Vou simplificar: em vez de criar entidades, usar sempre o mesmo `consulta_id` que já existe? Não, precisamos de dados consistentes.

Talvez os endpoints de sala recebam `consulta_id` e criem a sala. Para testar duplicata, precisamos que a consulta exista. Podemos criar a consulta diretamente via API também. Mas seria mais simples se o endpoint de sala criar a consulta? Não, geralmente a consulta é criada antes.

Vou supor que o endpoint de criação de sala recebe `consulta_id` e que a consulta já existe. Então no teste, criamos a consulta via banco.

Vou fazer assim.

Precisamos dos schemas de entrada/saída. Vou usar os schemas reais se existirem, mas como não sei, vou usar dicionários diretamente.

Criação de sala:

POST `/telemedicina/salas` com JSON `{"consulta_id": consulta.id, "validade_minutos": 30}` (ou similar). Verificar resposta 201 com `token`, `expira_em`, `consulta_id`.

Duplicada: chamar novamente com mesmo `consulta_id`, esperar 409.

Ciclo de status: PATCH `/telemedicina/consultas/{id}/status` com `{"status": "EM_ANDAMENTO"}` e depois `{"status": "CONCLUIDA"}`. Verificar resposta 200 e que status atualizou.

Mas não sei se os endpoints existem. Vou criar os testes assumindo que existem.

Vou incluir no arquivo uma seção de "Configuração" que ajusta os imports de acordo com a estrutura real do projeto.

Ok, vou produzir o código. Vou colocar comentários para ajudar na adaptação.

No final, o arquivo deve ser completo e executável se o projeto tiver a estrutura esperada.

Vou escrever o arquivo agora.```python
# Arquivo: backend/tests/test_telemedicina_lifecycle.py
"""
Testes de ciclo de vida da sala de telemedicina e consulta.

Cobre:
  1. Criação de sala com expiração
  2. Rejeição de salas duplicadas
  3. Ciclo de status da consulta (AGENDADA → EM_ANDAMENTO → CONCLUIDA)
"""

import os
from datetime import datetime, timedelta, timezone

os.environ["DATABASE_URL"] = "sqlite://"  # Força SQLite para testes antes de importar o app

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ajuste os imports abaixo conforme a estrutura real do projeto MedIA
from app.main import app
from app.core.database import Base, get_db  # Ex.: app.database, app.db, app.core.database
from app.models.telemedicina import Consulta, SalaTelemedicina  # Modelos reais
from app.models.enums import StatusConsulta  # Enum com AGENDADA, EM_ANDAMENTO, CONCLUIDA


# -----------------------------------------------------------------------------
# Configuração do banco de testes
# -----------------------------------------------------------------------------
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Cria as tabelas e fornece uma sessão isolada para cada teste."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Cliente de teste com dependência de banco sobrescrita."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


# -----------------------------------------------------------------------------
# Helpers para criar dados de apoio
# -----------------------------------------------------------------------------
def _criar_consulta_agendada(db_session) -> Consulta:
    """Cria uma consulta no banco com status AGENDADA (existente)."""
    consulta = Consulta(
        paciente_nome="Paciente Teste",
        paciente_cns="12345678901234",  # exemplo de CNS
        paciente_cpf="12345678900",
        medico_nome="Dr. Teste",
        medico_crm="12345",
        data_inicio=datetime.now(timezone.utc) + timedelta(hours=1),
        data_fim=None,
        status=StatusConsulta.AGENDADA,
    )
    db_session.add(consulta)
    db_session.commit()
    db_session.refresh(consulta)
    return consulta


# -----------------------------------------------------------------------------
# 1) Criação de sala com expiração
# -----------------------------------------------------------------------------
def test_criar_sala_com_expiracao(client, db_session):
    consulta = _criar_consulta_agendada(db_session)

    payload = {
        "consulta_id": consulta.id,
        "validade_minutos": 30,
    }

    response = client.post("/api/v1/telemedicina/salas", json=payload)

    assert response.status_code == 201, f"Erro ao criar sala: {response.text}"
    data = response.json()

    assert "token" in data
    assert "expira_em" in data
    assert data["consulta_id"] == consulta.id

    # Verifica expiração: deve estar no futuro, próximo de validade_minutos
    expira_em = datetime.fromisoformat(data["expira_em"])
    agora = datetime.now(timezone.utc)
    assert expira_em > agora, "A expiração deve estar no futuro"

    limite = agora + timedelta(minutes=31)
    assert expira_em <= limite, "A expiração não respeita o tempo de validade informado"

    # Verifica se a sala foi persistida corretamente
    sala_db = db_session.query(SalaTelemedicina).filter_by(consulta_id=consulta.id).first()
    assert sala_db is not None
    assert sala_db.token == data["token"]
    assert sala_db.expira_em == expira_em


# -----------------------------------------------------------------------------
# 2) Rejeição de salas duplicadas
# -----------------------------------------------------------------------------
def test_rejeitar_sala_duplicada(client, db_session):
    consulta = _criar_consulta_agendada(db_session)

    payload = {
        "consulta_id": consulta.id,
        "validade_minutos": 30,
    }

    # Primeira criação: deve funcionar
    response = client.post("/api/v1/telemedicina/salas", json=payload)
    assert response.status_code == 201

    # Segunda criação para a mesma consulta: deve ser rejeitada
    response = client.post("/api/v1/telemedicina/salas", json=payload)
    assert response.status_code == 409, f"Esperado status 409, obtido {response.status_code}"
    assert "já existe" in response.json().get("detail", "").lower() or "duplic" in response.json().get("detail", "").lower()


# -----------------------------------------------------------------------------
# 3) Ciclo de status da consulta (AGENDADA → EM_ANDAMENTO → CONCLUIDA)
# -----------------------------------------------------------------------------
def test_ciclo_status_consulta(client, db_session):
    consulta = _criar_consulta_agendada(db_session)
    consulta_id = consulta.id

    # Estado inicial
    assert consulta.status == StatusConsulta.AGENDADA

    # Transição para EM_ANDAMENTO
    response = client.patch(
        f"/api/v1/telemedicina/consultas/{consulta_id}/status",
        json={"status": "EM_ANDAMENTO"},
    )
    assert response.status_code == 200, f"Falha ao iniciar consulta: {response.text}"
    assert response.json()["status"] == "EM_ANDAMENTO"

    db_session.refresh(consulta)
    assert consulta.status == StatusConsulta.EM_ANDAMENTO

    # Transição para CONCLUIDA
    response = client.patch(
        f"/api/v1/telemedicina/consultas/{consulta_id}/status",
        json={"status": "CONCLUIDA"},
    )
    assert response.status_code == 200, f"Falha ao concluir consulta: {response.text}"
    assert response.json()["status"] == "CONCLUIDA"

    db_session.refresh(consulta)
    assert consulta.status == StatusConsulta.CONCLUIDA

    # Verifica que data_fim é preenchida
    assert consulta.data_fim is not None
```