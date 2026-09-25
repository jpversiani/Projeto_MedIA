We need to create a test file for the MedIA project. The task is to create backend/tests/test_telemedicina_lifecycle.py with pytest tests validating:

1) criação de sala com expiração (creation of room with expiration)
2) rejeição de salas duplicadas (rejection of duplicate rooms)
3) ciclo de status da consulta (AGENDADA -> EM_ANDAMENTO -> CONCLUIDA) (appointment status cycle)

We need to infer the domain models and services. The project is "MedIA" with telemedicine. We need to write tests that likely use SQLAlchemy models and Pydantic schemas. Since we don't have the actual codebase, we must assume typical structure. The instructions say "Crie backend/tests/test_telemedicina_lifecycle.py" with tests. We need to provide complete executable code. We should include necessary imports, fixtures, and test functions.

We need to consider the architecture: Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS patterns (CIAP-2, CID-10, SOAP, CNS/CPF). But the tests are focused on telemedicine lifecycle.

We should create a test file that can run against the actual codebase. Since we don't have the code, we need to make reasonable assumptions about the models and services. Alternatively, we can write tests that use mocks or in-memory SQLite to test the logic. The task says "crie backend/tests/test_telemedicina_lifecycle.py" - we need to provide the file content.

We should define fixtures for database session, models, etc. We need to ensure the tests are self-contained or rely on existing app modules. Since we don't have the app, we can create a minimal set of models and services within the test file? But the instruction says "Para o Projeto MedIA, crie backend/tests/test_telemedicina_lifecycle.py" - meaning we are adding a test file to an existing project. We should write tests that import from the app's modules. However, without knowing the exact module paths, we need to guess.

Maybe we can create a test file that uses the app's models and services, but we need to provide the code that would work if the project has those modules. To be safe, we can write tests that use SQLAlchemy in-memory SQLite and define the necessary models and services inline? But that would not test the actual project code. The task likely expects us to write tests that validate the behavior of the existing code. Since we don't have the code, we need to infer the API.

Let's think about typical telemedicine lifecycle:

- A "sala" (room) is created for a telemedicine consultation. It has an expiration time (e.g., 30 minutes). It should be associated with a consultation (consulta).
- Duplicate rooms: probably cannot create a room for the same consultation or same patient/doctor at the same time? Or maybe cannot create a room with the same identifier? We need to define what "duplicate" means. Likely, a room is unique per consultation ID, or per appointment ID. So creating a room for an appointment that already has a room should raise an error.
- Status cycle: AGENDADA -> EM_ANDAMENTO -> CONCLUIDA. This is the status of the consultation (consulta). The room creation might change status to EM_ANDAMENTO? Or the status changes are separate.

We need to write tests that validate these behaviors. We can create fixtures that set up a database, create an appointment (consulta) with status AGENDADA, then create a room, check expiration, try duplicate, then update status to EM_ANDAMENTO and CONCLUIDA.

We need to decide on the model names. Let's assume:

- Model `Consulta` (appointment) with fields: id, paciente_id, medico_id, status (enum), data_hora, etc.
- Model `SalaTelemedicina` (room) with fields: id, consulta_id (unique), token, expira_em (datetime), criada_em, etc.

Services: maybe `TelemedicinaService` with methods `criar_sala(consulta_id)`, `obter_sala(consulta_id)`, `atualizar_status_consulta(consulta_id, novo_status)`.

We can write tests using these assumed interfaces. But to make the tests executable, we need to define the models and services within the test file or import from the app. Since the task is to create the test file, we can include minimal implementations of the models and services in the test file as part of the test setup? That would be unusual but acceptable if the project doesn't have them yet? However, the instruction says "Para o Projeto MedIA, crie backend/tests/test_telemedicina_lifecycle.py" - it's a test file for the project. The project likely already has the models and services. We should write tests that import from the app's modules.

Given the lack of context, I'll write a test file that assumes the existence of modules:

- `backend.app.models.telemedicina` (or `backend.app.models`) with `Consulta`, `SalaTelemedicina`, `StatusConsulta` enum.
- `backend.app.services.telemedicina` with `TelemedicinaService`.

But we need to provide the code. The user expects a complete code block. We can write the test file with imports that may need adjustment. To make it more robust, we can use `pytest` fixtures that create an in-memory SQLite database and use SQLAlchemy's `create_engine` and `sessionmaker`. We can also use `pytest` to auto-discover models.

Alternatively, we can write tests that use `unittest.mock` to mock the service methods. But that would not test the actual behavior.

Given the instruction "Execute com precisão conforme as diretrizes", we need to produce a test file that is plausible and follows best practices. I'll write a test file that:

- Defines a fixture for the database session using SQLite in-memory.
- Creates tables from the models (imported from the app).
- Uses the service to perform operations.
- Tests the three scenarios.

I'll also include type hints and Pydantic v2 usage if needed.

Let's outline the test file:

```python
# Arquivo: backend/tests/test_telemedicina_lifecycle.py
"""
Testes de conexão WebSocket e ciclo de vida da sala (C21).
Valida criação de sala com expiração, rejeição de duplicidade e ciclo de status.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importações do projeto (ajustar conforme estrutura real)
from backend.app.models import Base, Consulta, SalaTelemedicina, StatusConsulta
from backend.app.services.telemedicina import TelemedicinaService
from backend.app.schemas.telemedicina import SalaCreate, ConsultaStatusUpdate
```

But we need to be careful: if the project doesn't have these exact paths, the test will fail. However, the task is to create the test file; the user will integrate it. We can add comments indicating that paths may need adjustment.

To make the test file self-contained and runnable without the actual project, we could define minimal models and services inside the test file. But that would not test the project's code. The instruction says "Para o Projeto MedIA" - so it's for the project. I think it's better to write tests that import from the project, assuming the project has those modules. We can also provide a fallback: if imports fail, we can define minimal models? That would be messy.

Maybe we can write tests that use the `app` package from the backend. The project structure likely has `backend/app/...`. We'll assume that.

Let's design the tests:

1. Test creation of room with expiration:
   - Create a consulta with status AGENDADA.
   - Call service.criar_sala(consulta_id).
   - Assert that a SalaTelemedicina is created with expira_em in the future (e.g., now + 30 minutes).
   - Assert that the room is associated with the consulta.

2. Test rejection of duplicate rooms:
   - Create a consulta.
   - Create a room for it.
   - Attempt to create another room for the same consulta.
   - Expect an exception (e.g., ValueError, DuplicateRoomError).

3. Test status cycle:
   - Create a consulta with status AGENDADA.
   - Update status to EM_ANDAMENTO (maybe via service or directly).
   - Assert status is EM_ANDAMENTO.
   - Update status to CONCLUIDA.
   - Assert status is CONCLUIDA.

We also need to test that invalid transitions are rejected? The task says "ciclo de status da consulta (AGENDADA -> EM_ANDAMENTO -> CONCLUIDA)" - just the happy path.

We'll need to define the `StatusConsulta` enum with those values.

Let's write the test file with clear structure. We'll include a fixture `db_session` that creates an in-memory SQLite database, creates tables, and yields a session. We'll also have a fixture `service` that uses the session.

We'll need to handle timezone-aware datetimes.

Now, let's write the code. We'll include type hints and use Pydantic v2 if needed for schemas.

We'll also add a `conftest.py`? No, we can put everything in one file.

Let's produce the final answer with the code block.```python
# Arquivo: backend/tests/test_telemedicina_lifecycle.py
"""
Testes de conexão WebSocket e ciclo de vida da sala (C21).

Valida:
1) Criação de sala com expiração.
2) Rejeição de salas duplicadas.
3) Ciclo de status da consulta (AGENDADA -> EM_ANDAMENTO -> CONCLUIDA).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Importações do projeto (ajuste os caminhos conforme a estrutura real do MedIA)
from backend.app.models import Base, Consulta, SalaTelemedicina, StatusConsulta
from backend.app.services.telemedicina import TelemedicinaService
from backend.app.schemas.telemedicina import SalaCreate, ConsultaStatusUpdate


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """
    Cria uma sessão de banco de dados SQLite em memória para os testes.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def service(db_session: Session) -> TelemedicinaService:
    """
    Instancia o serviço de telemedicina com a sessão de teste.
    """
    return TelemedicinaService(db_session)


def _criar_consulta(
    db_session: Session,
    status: StatusConsulta = StatusConsulta.AGENDADA,
) -> Consulta:
    """
    Helper para criar uma consulta no banco de teste.
    """
    consulta = Consulta(
        paciente_id="12345678901",  # CPF fictício
        medico_id="cns1234567890",  # CNS fictício
        data_hora=datetime.now(timezone.utc) + timedelta(hours=1),
        status=status,
    )
    db_session.add(consulta)
    db_session.commit()
    db_session.refresh(consulta)
    return consulta


# ---------------------------------------------------------------------------
# 1) Criação de sala com expiração
# ---------------------------------------------------------------------------
def test_criar_sala_com_expiracao(db_session: Session, service: TelemedicinaService) -> None:
    """
    Deve criar uma sala de telemedicina associada à consulta,
    com data de expiração futura (padrão: 30 minutos).
    """
    consulta = _criar_consulta(db_session)

    sala = service.criar_sala(consulta.id)

    assert sala is not None
    assert sala.consulta_id == consulta.id
    assert sala.expira_em > datetime.now(timezone.utc)
    assert sala.expira_em <= datetime.now(timezone.utc) + timedelta(minutes=31)

    # Verifica persistência no banco
    sala_db = db_session.get(SalaTelemedicina, sala.id)
    assert sala_db is not None
    assert sala_db.consulta_id == consulta.id


# ---------------------------------------------------------------------------
# 2) Rejeição de salas duplicadas
# ---------------------------------------------------------------------------
def test_rejeitar_sala_duplicada(db_session: Session, service: TelemedicinaService) -> None:
    """
    Não deve permitir criar mais de uma sala para a mesma consulta.
    """
    consulta = _criar_consulta(db_session)

    service.criar_sala(consulta.id)

    with pytest.raises(ValueError, match="já possui sala"):
        service.criar_sala(consulta.id)

    # Garante que apenas uma sala existe
    salas = db_session.query(SalaTelemedicina).filter_by(consulta_id=consulta.id).all()
    assert len(salas) == 1


# ---------------------------------------------------------------------------
# 3) Ciclo de status da consulta
# ---------------------------------------------------------------------------
def test_ciclo_status_consulta(db_session: Session, service: TelemedicinaService) -> None:
    """
    Deve permitir a transição AGENDADA -> EM_ANDAMENTO -> CONCLUIDA.
    """
    consulta = _criar_consulta(db_session, status=StatusConsulta.AGENDADA)

    # AGENDADA -> EM_ANDAMENTO
    consulta_atualizada = service.atualizar_status_consulta(
        consulta.id, StatusConsulta.EM_ANDAMENTO
    )
    assert consulta_atualizada.status == StatusConsulta.EM_ANDAMENTO

    # EM_ANDAMENTO -> CONCLUIDA
    consulta_atualizada = service.atualizar_status_consulta(
        consulta.id, StatusConsulta.CONCLUIDA
    )
    assert consulta_atualizada.status == StatusConsulta.CONCLUIDA

    # Verifica persistência
    consulta_db = db_session.get(Consulta, consulta.id)
    assert consulta_db.status == StatusConsulta.CONCLUIDA


def test_transicao_invalida_status(db_session: Session, service: TelemedicinaService) -> None:
    """
    Deve rejeitar transições inválidas (ex.: AGENDADA -> CONCLUIDA diretamente).
    """
    consulta = _criar_consulta(db_session, status=StatusConsulta.AGENDADA)

    with pytest.raises(ValueError, match="transição inválida"):
        service.atualizar_status_consulta(consulta.id, StatusConsulta.CONCLUIDA)
```