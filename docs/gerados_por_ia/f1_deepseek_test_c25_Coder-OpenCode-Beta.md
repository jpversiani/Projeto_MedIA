We need to create a test file for the MedIA project. The task: create backend/tests/test_telemedicina_lifecycle.py with pytest tests validating: 1) creation of room with expiration; 2) rejection of duplicate rooms; 3) consultation status cycle (AGENDADA -> EM_ANDAMENTO -> CONCLUIDA).

We need to understand the architecture. The project is MedIA, likely a telemedicine system. We need to write tests that validate these behaviors. We need to infer the models, services, etc. Since we are only asked to create the test file, we need to assume the existing code structure. We should write tests that are plausible and follow the guidelines: Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS patterns, CIAP-2, CID-10, SOAP, CNS/CPF.

We need to create tests that likely use fixtures, maybe a test database, and test the lifecycle. We need to ensure the tests are comprehensive.

Let's think about the domain: Telemedicine rooms. There is likely a model for TelemedicineRoom (or SalaTelemedicina) with fields like id, status (AGENDADA, EM_ANDAMENTO, CONCLUIDA, etc.), expiration time, maybe a unique constraint on something (like a room code or a consultation id). Duplicate rooms: maybe cannot create two rooms for the same consultation or same patient/doctor/time.

We need to write tests that validate these behaviors. Since we don't have the actual code, we need to write tests that would pass given the expected implementation. We can use mocks or actual database with SQLAlchemy. The instructions say "crie backend/tests/test_telemedicina_lifecycle.py" - so we need to produce the file content.

We should structure the tests with pytest, using fixtures for database session, maybe using a test client or service functions. We'll assume there is a service layer (e.g., TelemedicinaService) with methods like create_room, get_room, update_status, etc.

We need to be precise. Let's outline the test file:

- Imports: pytest, datetime, timedelta, maybe from sqlalchemy, from app models, services.
- Fixtures: db_session (in-memory SQLite or test database), maybe a user/patient/doctor fixture.
- Tests:
  1. test_create_room_with_expiration: create a room, assert it has an expiration time (e.g., now + 30 minutes), and that the room is created with status AGENDADA.
  2. test_reject_duplicate_rooms: attempt to create a second room for the same consultation (or same unique key) and expect an exception (e.g., IntegrityError or ValueError).
  3. test_consultation_status_cycle: create a room, then update status to EM_ANDAMENTO, then to CONCLUIDA, and assert each transition is valid.

We need to decide on the exact API. Let's assume the service is something like:

```python
from app.services.telemedicina import TelemedicinaService
from app.models.telemedicina import TelemedicinaRoom, StatusConsulta
```

We'll need to create a room with parameters: patient_cns, doctor_cpf, consultation_id, etc. We'll use Pydantic schemas for input.

Since we don't have the actual code, we can write tests that are self-contained by defining minimal models and services in the test file? But the instruction says "crie backend/tests/test_telemedicina_lifecycle.py" - it's a test file for the project, so it should import from the project's modules. However, we don't have the project code. In a real scenario, we would have the code. As an AI, we need to produce a test file that is plausible and would work with the described architecture. We can make reasonable assumptions and write tests that are robust.

We can also use mocks to avoid needing the actual database. But the task says "testes pytest validando" - so we need actual tests that validate behavior. We can use a test database with SQLAlchemy and create tables.

Let's design the test file with the following structure:

- Use pytest fixtures to set up an in-memory SQLite database, create tables, and provide a session.
- Define a service class (or use the actual service) that interacts with the session.
- Since we don't have the actual service, we can write the tests to use a service that we define in the test file? That would be weird. Better to assume the service exists and import it. But if the service doesn't exist, the tests will fail. The task is to create the test file, not the implementation. So we need to write tests that would pass if the implementation is correct. We can write tests that are clear and follow the requirements.

Perhaps we can write tests using the repository pattern or directly using the model and session. For example, to test creation with expiration, we can create a TelemedicinaRoom object, add to session, commit, and assert expiration is set. To test duplicate rejection, we can rely on a unique constraint in the model. To test status cycle, we can update the status and validate allowed transitions.

We need to ensure the tests are meaningful and cover the requirements.

Let's define a minimal model in the test file? No, that would not test the actual project. But since we are asked to create the test file, we can assume the project has these models. We'll write the tests using imports that are likely to exist. We can also add comments indicating the expected structure.

Given the lack of actual code, I'll produce a test file that is well-structured, uses fixtures, and tests the described behaviors. I'll make reasonable assumptions about the model and service.

Let's think about the domain specifics:

- "criação de sala com expiração" - a room should have an expiration time, likely a datetime field `expires_at`. The test should create a room and assert that `expires_at` is set to a future time (e.g., now + 30 minutes). We can also test that the room is initially active.

- "rejeição de salas duplicadas" - duplicate rooms: likely there is a unique constraint on a field like `consultation_id` (or `agendamento_id`). So creating a second room for the same consultation should raise an IntegrityError or a custom exception. We'll test that.

- "ciclo de status da consulta (AGENDADA -> EM_ANDAMENTO -> CONCLUIDA)" - the status field should follow this sequence. We'll test that we can transition from AGENDADA to EM_ANDAMENTO, then to CONCLUIDA, and that invalid transitions (e.g., from CONCLUIDA to EM_ANDAMENTO) are rejected.

We need to implement the tests with proper setup and teardown.

Let's write the test file:

```python
# Arquivo: backend/tests/test_telemedicina_lifecycle.py
"""
Testes de ciclo de vida da sala de telemedicina.

Cobre:
- Criação de sala com expiração.
- Rejeição de salas duplicadas.
- Ciclo de status da consulta (AGENDADA -> EM_ANDAMENTO -> CONCLUIDA).
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError

# Assumindo que os modelos e serviços estão em app
from app.models.telemedicina import TelemedicinaRoom, StatusConsulta
from app.services.telemedicina import TelemedicinaService
from app.schemas.telemedicina import TelemedicinaRoomCreate
from app.database import Base, get_db  # ou similar

# Fixtures para banco de dados em memória
@pytest.fixture
def db_session():
    # Configuração do banco de dados SQLite em memória
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def service(db_session):
    return TelemedicinaService(db_session)

# Testes
def test_create_room_with_expiration(service):
    """Deve criar uma sala com data de expiração futura."""
    # Dados mínimos para criação
    data = TelemedicinaRoomCreate(
        consulta_id="consulta-123",
        paciente_cns="898003486440001",
        medico_cpf="12345678900",
        especialidade="CLINICA_GERAL",
        unidade_saude="UBS CENTRO",
    )
    room = service.create_room(data)
    assert room.id is not None
    assert room.status == StatusConsulta.AGENDADA
    assert room.expires_at is not None
    assert room.expires_at > datetime.now(timezone.utc)
    # Verifica se a expiração é aproximadamente 30 minutos (ou o configurado)
    expected_expiration = datetime.now(timezone.utc) + timedelta(minutes=30)
    assert abs((room.expires_at - expected_expiration).total_seconds()) < 60

def test_reject_duplicate_rooms(service):
    """Não deve permitir criar duas salas para a mesma consulta."""
    data = TelemedicinaRoomCreate(
        consulta_id="consulta-456",
        paciente_cns="898003486440001",
        medico_cpf="12345678900",
        especialidade="CLINICA_GERAL",
        unidade_saude="UBS CENTRO",
    )
    service.create_room(data)
    with pytest.raises(IntegrityError):
        service.create_room(data)  # Deve violar a constraint única

def test_consultation_status_cycle(service):
    """Deve seguir o ciclo AGENDADA -> EM_ANDAMENTO -> CONCLUIDA."""
    data = TelemedicinaRoomCreate(
        consulta_id="consulta-789",
        paciente_cns="898003486440001",
        medico_cpf="12345678900",
        especialidade="CLINICA_GERAL",
        unidade_saude="UBS CENTRO",
    )
    room = service.create_room(data)
    assert room.status == StatusConsulta.AGENDADA

    # Transição para EM_ANDAMENTO
    room = service.update_status(room.id, StatusConsulta.EM_ANDAMENTO)
    assert room.status == StatusConsulta.EM_ANDAMENTO

    # Transição para CONCLUIDA
    room = service.update_status(room.id, StatusConsulta.CONCLUIDA)
    assert room.status == StatusConsulta.CONCLUIDA

    # Transição inválida: de CONCLUIDA para EM_ANDAMENTO deve falhar
    with pytest.raises(ValueError):
        service.update_status(room.id, StatusConsulta.EM_ANDAMENTO)
```

But we need to be careful: the service methods may not exist. We can also write tests using the model directly. However, the task says "testes de conexão WebSocket e ciclo de vida da sala" - the title mentions WebSocket, but the instructions only mention the three tests. Maybe we should also include WebSocket connection tests? The title says "C25" and "Testes de Conexão WebSocket e Ciclo de Vida da Sala". But the instructions explicitly list three items: 1) criação de sala com expiração; 2) rejeição de salas duplicadas; 3) ciclo de status da consulta. So we focus on those.

We need to ensure the test file is complete and executable. We'll include necessary imports and fixtures. We'll also add a conftest.py? The task only asks for this file. We can include everything in one file.

Let's refine the test file to be more robust and not rely on unknown service methods. We can use the SQLAlchemy session directly to test the model constraints and status transitions. But the requirement is to test the lifecycle, which likely involves service logic. We can write tests that use the service, but we need to define the service in the test file? No, we can assume it exists. However, to make the test file self-contained and runnable, we might need to provide mocks or stubs. But the task is to create the test file for the project, so it should import from the project's modules. Since we don't have the actual modules, we can write the tests in a way that they would work if the modules exist. We can also use `unittest.mock` to patch the service if needed.

Alternatively, we can write tests that directly test the model and its methods. For example, the model might have a method `can_transition_to` or the service handles it. We'll assume the service has `create_room` and `update_status`.

Let's also consider the "expiração" - maybe the room has a `expires_at` field that is set automatically. We can test that.

We need to include the necessary imports for SQLAlchemy, Pydantic, etc. We'll also need to set up the database. We'll use `pytest` fixtures.

Let's write a more complete version with comments explaining assumptions.

We should also consider that the project uses Pydantic v2 and SQLAlchemy 2.0. So we'll use `Mapped` and `mapped_column` in models, but in tests we don't need to define models.

We'll write the test file with the following structure:

- Module docstring.
- Imports.
- Fixtures: `db_session`, `service`.
- Tests.

We'll also include a test for the expiration being set to a specific duration (e.g., 30 minutes). We can use `freezegun` to freeze time, but that's an extra dependency. We'll just check that it's in the future.

For duplicate rooms, we need to ensure the unique constraint is on `consulta_id`. We'll assume that.

For status cycle, we need to ensure the service validates transitions. We'll test that invalid transitions raise an exception.

Let's write the final code.

But wait: the task says "Testes de Conexão WebSocket e Ciclo de Vida da Sala". Maybe there is also a WebSocket connection test? The instructions only list three items, but the title mentions WebSocket. Perhaps the "Conexão WebSocket" is part of the room lifecycle? Maybe the room has a WebSocket connection that needs to be tested? However, the explicit instructions are clear: "crie backend/tests/test_telemedicina_lifecycle.py com testes pytest validando: 1) criação de sala com expiração; 2) rejeição de salas duplicadas; 3) ciclo de status da consulta". So we'll stick to those.

Let's produce the file.

We need to be careful with the import paths. We'll assume the project structure is:

- backend/app/models/telemedicina.py
- backend/app/services/telemedicina.py
- backend/app/schemas/telemedicina.py
- backend/app/database.py

We'll import accordingly.

We'll also include a `pytest.ini`? Not needed.

Let's write the code.```python
# Arquivo: backend/tests/test_telemedicina_lifecycle.py
"""
Testes de ciclo de vida da sala de telemedicina.

Cobre:
- Criação de sala com expiração.
- Rejeição de salas duplicadas.
- Ciclo de status da consulta (AGENDADA -> EM_ANDAMENTO -> CONCLUIDA).
"""

import pytest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Assumindo a estrutura do projeto MedIA
from app.database import Base
from app.models.telemedicina import TelemedicinaRoom, StatusConsulta
from app.schemas.telemedicina import TelemedicinaRoomCreate
from app.services.telemedicina import TelemedicinaService


@pytest.fixture
def db_session():
    """
    Cria um banco de dados SQLite em memória para os testes.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False
    )
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def service(db_session):
    """
    Instancia o serviço de telemedicina com a sessão de teste.
    """
    return TelemedicinaService(db_session)


def test_create_room_with_expiration(service):
    """
    Deve criar uma sala com data de expiração futura e status inicial AGENDADA.
    """
    data = TelemedicinaRoomCreate(
        consulta_id="consulta-123",
        paciente_cns="898003486440001",
        medico_cpf="12345678900",
        especialidade="CLINICA_GERAL",
        unidade_saude="UBS CENTRO",
    )

    room = service.create_room(data)

    assert room.id is not None
    assert room.status == StatusConsulta.AGENDADA
    assert room.expires_at is not None
    assert room.expires_at > datetime.now(timezone.utc)

    # Verifica se a expiração é aproximadamente 30 minutos (configurável)
    expected_expiration = datetime.now(timezone.utc) + timedelta(minutes=30)
    assert abs((room.expires_at - expected_expiration).total_seconds()) < 60


def test_reject_duplicate_rooms(service):
    """
    Não deve permitir criar duas salas para a mesma consulta.
    """
    data = TelemedicinaRoomCreate(
        consulta_id="consulta-456",
        paciente_cns="898003486440001",
        medico_cpf="12345678900",
        especialidade="CLINICA_GERAL",
        unidade_saude="UBS CENTRO",
    )

    service.create_room(data)

    with pytest.raises(IntegrityError):
        service.create_room(data)  # Deve violar a constraint única


def test_consultation_status_cycle(service):
    """
    Deve seguir o ciclo AGENDADA -> EM_ANDAMENTO -> CONCLUIDA.
    Transições inválidas devem ser rejeitadas