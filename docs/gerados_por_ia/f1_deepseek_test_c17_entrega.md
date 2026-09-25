We need to create a test file for the MedIA project. The task is to create backend/tests/test_telemedicina_lifecycle.py with pytest tests validating:
1) creation of room with expiration;
2) rejection of duplicate rooms;
3) consultation status cycle (AGENDADA -> EM_ANDAMENTO -> CONCLUIDA).

We need to follow the architecture: Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0. Patterns of SUS/APS (CIAP-2, CID-10, SOAP method, identification by CNS/CPF). Maintain full compliance and test coverage.

We need to write tests. But we need to know the actual implementation to test. Since we are only given the task, we need to infer the likely structure. Possibly there is an existing codebase with models, services, etc. We need to write tests that validate the lifecycle. Since we don't have the actual code, we need to design tests that would work with a typical implementation. However, the instruction says "Crie backend/tests/test_telemedicina_lifecycle.py" - so we are creating the test file. We need to ensure it's runnable and passes given the existing code. But we don't have the code. We need to make reasonable assumptions.

We can create tests that use mocks or fakes, but the task says "testes pytest validando" - so they should be actual tests. We need to write tests that would pass if the implementation is correct. Since we don't have the implementation, we can write tests that define the expected behavior and then the implementation would need to satisfy them. But the user is asking us to create the test file, not the implementation. So we can write tests that are self-contained, perhaps using in-memory SQLite and Pydantic models, and test the lifecycle logic.

But the task says "Para o Projeto MedIA, crie backend/tests/test_telemedicina_lifecycle.py" - so we are part of the project. We need to write tests that align with the existing architecture. Since we don't have the existing code, we need to make educated guesses. However, we can also write tests that are independent of the actual implementation by using dependency injection or by testing the service layer with mocks. But the instruction says "testes pytest validando" - they should be meaningful.

Maybe the best approach is to write tests that use a real database (SQLite in-memory) and define minimal models and services within the test file? But that would be testing the test code, not the actual project. That's not good.

Alternatively, we can assume that the project has a structure like:
- backend/app/models/telemedicina.py with SQLAlchemy models for Sala (Room) and Consulta (Appointment/Consultation).
- backend/app/schemas/telemedicina.py with Pydantic schemas.
- backend/app/services/telemedicina.py with business logic.

We can write tests that import from these modules. But we don't know the exact names. We need to be generic.

Given the task, I think the expectation is to write a test file that tests the lifecycle of a telemedicine room. The tests should cover:
1) creation of room with expiration: likely a function like create_sala() that sets an expiration time (e.g., now + 30 minutes) and stores it.
2) rejection of duplicate rooms: maybe a room is unique per consultation or per patient/doctor pair, so trying to create another active room for the same consultation raises an error.
3) consultation status cycle: a consultation has statuses AGENDADA, EM_ANDAMENTO, CONCLUIDA. The service should allow transitions in that order.

We need to write tests that validate these behaviors. Since we don't have the implementation, we can write tests that use the actual service functions if they exist. But we need to know the function names and signatures. We can infer from common patterns.

Maybe we can write tests that are based on the expected API endpoints? But the task says "testes de conexão WebSocket e ciclo de vida da sala" but the actual tests listed are about room creation, duplicate rejection, and status cycle. No WebSocket connection tests are mentioned. The title says "Testes de Conexão WebSocket e Ciclo de Vida da Sala (C17)" but the instructions only list three items. So we'll focus on those.

Given the ambiguity, I'll write tests that are self-contained and use a simple in-memory SQLite database with SQLAlchemy models defined in the test file? That would not test the actual project. But the instruction says "Crie backend/tests/test_telemedicina_lifecycle.py" - it doesn't say we need to test existing code. It says "testes pytest validando" - so we are creating tests that validate the behavior. If the project doesn't have the implementation yet, these tests would fail. But the user is asking us to create the tests, not the implementation. So we should write tests that are correct and would pass if the implementation is correct.

Given the context of the project (MedIA, SUS/APS), it's likely a real project with existing code. The user wants us to add tests for this specific functionality. So we need to write tests that import from the project's modules. Since we don't have the code, we need to make reasonable assumptions about the structure.

I'll assume a typical structure:
- backend/app/models/telemedicina.py contains SQLAlchemy models: SalaTelemedicina (or Room) and Consulta (or Appointment).
- backend/app/services/telemedicina.py contains functions like criar_sala(), obter_sala(), etc.
- backend/app/schemas/telemedicina.py contains Pydantic schemas.

But to avoid import errors, we can write tests that use the `pytest` framework with fixtures that set up a test database using SQLAlchemy's `create_engine` and `sessionmaker`. We can define the models in the test file? That would be redundant.

Alternatively, we can write tests that use `unittest.mock` to mock the service functions and test the logic of the test itself? That doesn't make sense.

Maybe the best is to write tests that are integration tests with a real database, and we need to ensure the models exist. Since we don't have them, we can create a minimal set of models in the test file that represent the domain, and then test the lifecycle logic. But that would be testing our own models, not the project's.

Given the instruction "Execute com precisão conforme as diretrizes", I think we need to produce a test file that is ready to run in the project. The user expects us to know the project structure. Since we don't, we can make reasonable assumptions and write the tests accordingly, with clear imports that would need to be adjusted.

Let's think: The task is from a series of tasks (C17). It's likely part of a larger project where the code already exists. The user wants us to add tests. So we should write tests that import from the actual modules. We can infer the module names from the task: "telemedicina" is the domain. So likely there is a module `backend/app/services/telemedicina.py` or `backend/app/api/v1/telemedicina.py`. The tests are for the lifecycle, so they would test the service layer.

I'll write tests that use a fixture to create a test database (SQLite in-memory) and use the actual models and services. I'll assume the following:

- Models are in `backend/app/models/telemedicina.py` with classes `SalaTelemedicina` and `Consulta`.
- Services are in `backend/app/services/telemedicina.py` with functions:
  - `criar_sala(db, consulta_id, ...)` -> creates a room with expiration.
  - `criar_sala` should raise an error if a room already exists for that consultation (duplicate).
  - `atualizar_status_consulta(db, consulta_id, novo_status)` -> updates status with validation.

But we don't know the exact names. To be safe, we can write tests that are more generic and use the actual project's API. However, without the code, it's impossible.

Maybe the user expects us to write the tests as part of a TDD approach, and the tests will be used to drive the implementation. In that case, we can write tests that define the expected behavior, and the implementation will be created later. The tests should be runnable and fail initially. That's acceptable.

Given that, we can write tests that use a simple in-memory database and define the models and services within the test file? No, that would not be testing the project.

Let's re-read the task: "TAREFA: Testes de Conexão WebSocket e Ciclo de Vida da Sala (C17) ... Para o Projeto MedIA, crie backend/tests/test_telemedicina_lifecycle.py com testes pytest validando: 1) criação de sala com expiração; 2) rejeição de salas duplicadas; 3) ciclo de status da consulta (AGENDADA -> EM_ANDAMENTO -> CONCLUIDA)."

It says "crie backend/tests/test_telemedicina_lifecycle.py" - so we are creating the test file. It doesn't say we need to create the implementation. So we just need to write the test file. The tests should be valid and pass when the implementation is correct. Since we don't have the implementation, we need to write tests that are self-contained and don't depend on external code? But then they wouldn't be testing the project.

Maybe the project already has the implementation, and we are just adding tests. In that case, we need to know the exact API. Since we don't, we can write tests that are based on common patterns and hope they match. But that's risky.

Given the constraints, I'll write tests that are self-contained by defining minimal models and services within the test file, but using the same patterns (Pydantic v2, SQLAlchemy 2.0). This way, the tests are runnable and demonstrate the expected behavior. The user can then adapt them to the actual project. However, the instruction says "Manter conformidade total e cobertura de testes automatizados com pytest." - so we need to ensure the tests are valid.

I'll create a test file that:
- Uses SQLAlchemy 2.0 with an in-memory SQLite database.
- Defines SQLAlchemy models for `SalaTelemedicina` and `Consulta` with the necessary fields (including expiration, status).
- Defines Pydantic schemas for validation.
- Defines service functions (or use the models directly) to test the lifecycle.
- Tests the three scenarios.

But this would be a lot of code in the test file, and it would be testing our own implementation, not the project's. That's not ideal.

Alternatively, we can write tests that use `unittest.mock` to mock the database and service functions, and test the logic of the service functions by mocking the dependencies. But again, we need to know the service functions.

Maybe the best approach is to write tests that are integration tests with a real database, and we assume the models and services are already defined. We'll use `pytest` fixtures to create a test database and use the actual models. We'll import from the project's modules. Since we don't know the exact names, we'll use `from app.models.telemedicina import ...` etc. If the imports fail, the user will need to adjust.

Given the task, I think the user expects us to produce a test file that is ready to run in the project. They will have the implementation. So we should write tests that import from the actual modules. We can make reasonable assumptions about the structure.

Let's define a plausible structure:

- `backend/app/models/telemedicina.py`:
  - `class Consulta(Base)` with fields: id, paciente_nome, status (enum: AGENDADA, EM_ANDAMENTO, CONCLUIDA), created_at, etc.
  - `class SalaTelemedicina(Base)` with fields: id, consulta_id (FK), expira_em (datetime), created_at, etc.

- `backend/app/schemas/telemedicina.py`:
  - Pydantic models for request/response.

- `backend/app/services/telemedicina.py`:
  - `def criar_sala(db: Session, consulta_id: int, expiracao_minutos: int = 30) -> SalaTelemedicina`
  - `def obter_sala_por_consulta(db: Session, consulta_id: int) -> Optional[SalaTelemedicina]`
  - `def atualizar_status_consulta(db: Session, consulta_id: int, novo_status: str) -> Consulta`

We can write tests that use these functions.

But we need to be careful: the task says "criação de sala com expiração" - so the test should verify that the room has an expiration time in the future. "rejeição de salas duplicadas" - test that creating a room for a consultation that already has an active room raises an error. "ciclo de status da consulta" - test that the status transitions are allowed.

Let's write the tests.

We'll need a fixture that creates a test database and a session. We'll use `pytest` with `tmp_path` or in-memory SQLite.

We'll also need to create the tables. We can use `Base.metadata.create_all`.

We'll need to handle the fact that the models might have relationships. We'll keep it simple.

Let's write the test file.

I'll include imports, fixtures, and tests.

We'll assume the models are in `app.models.telemedicina` and services in `app.services.telemedicina`. We'll use `from sqlalchemy.orm import Session` etc.

But to be safe, we can write the tests in a way that they can be run even if the actual modules don't exist yet? No, they would fail on import. But that's okay for TDD.

Given the instruction, I'll write the tests with the assumption that the project structure is as described. I'll include comments to indicate where to adjust if needed.

Let's craft the code.

We'll need to define the status enum. We can use Python's `enum.Enum` or `str, Enum`.

We'll need to handle the expiration: the service should set `expira_em` to `datetime.utcnow() + timedelta(minutes=expiracao_minutos)`.

For duplicate rooms: the service should check if a room already exists for the consultation and raise an error (e.g., `ValueError` or a custom exception).

For status cycle: the service should validate that the new status is allowed given the current status. For example, from AGENDADA can go to EM_ANDAMENTO, from EM_ANDAMENTO to CONCLUIDA. It should reject invalid transitions.

Let's write the tests.

We'll need to create a `Consulta` object first, then create a room for it, then try to create another room and expect an error, then update statuses.

We'll also need to test that the room expiration is in the future.

Let's write the test file.

I'll use `pytest` fixtures:

```python
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

# Import models and services
from app.models.telemedicina import Base, Consulta, SalaTelemedicina
from app.services.telemedicina import criar_sala, obter_sala_por_consulta, atualizar_status_consulta
```

But we don't know if these imports exist. To make the test file runnable, we can define the models and services within the test file? That would be redundant but ensures the tests pass. However, the task says "Para o Projeto MedIA" - so it's part of the project. I think we should import from the project.

Given the risk, I'll write the tests using imports from the project, and add a comment that the imports should be adjusted to match the actual structure. But the user asked for "código completo e executável" - so it should be runnable. If the imports fail, it's not runnable.

Maybe we can use `pytest.importorskip` to skip if modules not found? That would not test anything.

Alternatively, we can write the tests in a way that they don't depend on the actual implementation by using dependency injection. For example, we can define a `create_sala` function that takes a session and a consulta_id, and we can test it with a real database. But we need to define that function somewhere.

Given the ambiguity, I'll write the test file with a self-contained implementation of the models and services, but clearly marked as test helpers. This way, the tests are runnable and demonstrate the expected behavior. The user can then adapt them to the actual project by replacing the test helpers with imports from the project.

But the instruction says "Crie backend/tests/test_telemedicina_lifecycle.py" - it doesn't say we can't include helper code. However, it's unusual to have production code in test files.

Let's think again: The user is an agent that is supposed to generate code. The task is to create a test file. The test file should be part of the project. If the project already has the implementation, the test file should import from it. If not, the test file would fail. Since the user didn't provide the implementation, we need to make a decision.

I'll write the test file assuming the project has the following structure (which is common for such projects):

- `backend/app/models/telemedicina.py` with `Base`, `Consulta`, `SalaTelemedicina`.
- `backend/app/services/telemedicina.py` with `criar_sala`, `atualizar_status_consulta`.

I'll write the tests using these imports. If the imports are wrong, the user can adjust. The tests will be correct in terms of logic.

To make the tests more robust, we can use `pytest` fixtures that create a test database and session. We'll need to ensure the tables are created.

Let's write the code.

We'll need to define the status enum. We can use `enum.Enum`.

We'll need to define the models with SQLAlchemy 2.0 style (Mapped, mapped_column).

Let's write:

```python
# backend/tests/test_telemedicina_lifecycle.py
"""Testes do ciclo de vida da sala de telemedicina."""

from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

# Importações do projeto (ajustar conforme