We need to create a test file for the MedIA project. The task is to create backend/tests/test_mensageria_preventiva.py with tests for:

1. Validate filter of patients with overdue hypertension appointments.
2. Ensure reminders respect a time tolerance window.
3. Validate idempotency in notification dispatch.

We need to follow architecture guidelines: Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0, SUS/APS patterns (CIAP-2, CID-10, SOAP, CNS/CPF). We need to write pytest tests.

We need to infer the structure of the project. Since we are only asked to create the test file, we need to write tests that would work with the existing codebase. We should assume there are modules for models, services, etc. We need to design tests that are plausible and cover the requirements.

We should create tests that use fixtures, perhaps with in-memory SQLite or mocked dependencies. We need to ensure they are executable. Since we don't have the actual project code, we need to write tests that are self-contained enough or use mocks. But the instruction says "Crie backend/tests/test_mensageria_preventiva.py" - so we just need to create that file. We can write tests that import from the app's modules, but we don't know the exact names. We can make reasonable assumptions and write tests that would pass if the modules exist as expected. Alternatively, we can write tests that are more generic, using mocks to simulate the behavior. But the task says "valida filtro de pacientes com consultas de hipertensão vencidas" - so we need to test a function that filters patients. We need to know the function name. We can invent one, e.g., `get_patients_with_overdue_hypertension_appointments`. Similarly for reminder time window and idempotency.

Given the ambiguity, we should write tests that are clear and test the intended behavior, using mocks and fixtures to isolate the logic. We'll define the tests with descriptive names and use pytest. We'll also include type hints and Pydantic models if needed.

Let's outline the test file:

- Imports: pytest, datetime, maybe from app modules.
- We'll define fixtures: a mock session, sample patient data, etc.
- Test 1: `test_filtro_pacientes_hipertensao_vencidos` - creates a list of patients with appointments, some overdue, some not, and asserts the filter returns only overdue ones.
- Test 2: `test_lembretes_respeitam_janela_tolerancia` - tests that reminders are only sent within a time window (e.g., between 8:00 and 20:00, or within a specific tolerance around appointment time). We'll define a function `should_send_reminder(appointment_time, now)` and test various cases.
- Test 3: `test_idempotencia_disparo_notificacoes` - tests that sending a notification for the same appointment twice does not duplicate (e.g., using a unique constraint or checking if already sent).

We need to ensure the tests are meaningful. Since we don't have the actual implementation, we can write tests that would fail if the implementation is wrong, but we need to provide the test code. The user expects us to create the test file, not the implementation. So we can write tests that assume certain functions exist. We can also write tests that are self-contained by implementing small helper functions within the test file to simulate the logic, but that would be testing our own helpers, not the project. Better to write tests that import from the app's modules and use mocks to simulate database behavior.

Given the instruction "Crie backend/tests/test_mensageria_preventiva.py" - we should create a file that is ready to run with pytest, assuming the project structure. We'll use `pytest` and `unittest.mock` to mock dependencies.

Let's design:

- We'll assume there is a service module `backend.app.services.mensageria_preventiva` with functions:
  - `filtrar_pacientes_hipertensao_vencidos(session, data_referencia)` -> list[Paciente]
  - `enviar_lembrete(paciente, consulta, agora)` -> bool or None
  - `registrar_notificacao(session, paciente, consulta)` -> Notificacao

But we don't know. To make the tests robust, we can use mocks for the session and the models. We'll create fake data using Pydantic models or simple dataclasses.

Alternatively, we can write tests that directly test the logic by importing the functions and mocking the database query. For example, we can mock `session.query(...)` to return a list of patients.

Let's write the test file with clear structure. We'll include docstrings and comments in Portuguese.

We'll also need to ensure we use Python 3.12 and type hints.

Let's write:

```python
# Arquivo: backend/tests/test_mensageria_preventiva.py
"""
Testes para regras de busca ativa e prevenção de spam clínico (C8).
"""

from datetime import datetime, time, timedelta
from typing import List, Optional
from uuid import uuid4

import pytest
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Importações do projeto (ajustar conforme estrutura real)
from backend.app.models.paciente import Paciente
from backend.app.models.consulta import Consulta
from backend.app.services.mensageria_preventiva import (
    filtrar_pacientes_hipertensao_vencidos,
    enviar_lembrete,
    registrar_notificacao,
)
```

But we need to be careful: if the modules don't exist, the test file will fail to import. The user might expect us to create the test file only, not the implementation. However, the instruction says "Crie backend/tests/test_mensageria_preventiva.py" - so we just need to create that file. It's okay if it imports from modules that are assumed to exist. But to make the test file self-contained and runnable without the actual project, we could use mocks for the imports. But that would be weird.

Given the context, the user is asking us to create tests for a specific feature. They likely have a project structure in mind. We should write tests that are plausible and follow the guidelines. We can include comments that indicate the expected interfaces.

Let's create the test file with the following structure:

- Fixtures for sample data.
- Test for filtering overdue hypertension appointments.
- Test for reminder time window.
- Test for idempotency.

We'll use `unittest.mock` to mock the session and the query results. We'll also use Pydantic models to represent the data if needed.

Let's define some sample models in the test file to avoid dependency on actual models. But the instruction says "tipagem estrita com Pydantic v2 e SQLAlchemy 2.0" - so we should use Pydantic for data validation. We can create simple Pydantic models for test purposes.

However, the test should test the actual service functions. If we mock the session, we can test the filtering logic by providing a list of patients with appointments. The function `filtrar_pacientes_hipertensao_vencidos` likely queries the database. We can mock the query to return a list of tuples or objects.

Let's write the test file with mocks.

We'll also need to consider the time tolerance window. The requirement: "assegura que lembretes respeitam janela de tolerância de horário". This could mean that reminders are only sent during a certain time of day (e.g., not at night) or within a certain period before the appointment. We'll define a function `enviar_lembrete` that checks if the current time is within a tolerance window relative to the appointment time. For example, reminders should be sent only between 8:00 and 20:00, or only if the appointment is more than 24 hours away but less than 48 hours, etc. We'll pick a simple rule: reminders are sent only if the current time is between 8:00 and 20:00, and the appointment is within the next 24 hours. We'll test that.

For idempotency: `registrar_notificacao` should check if a notification already exists for the same patient and appointment before creating a new one. We'll test that calling it twice with the same data does not create a duplicate.

We'll write the tests using mocks for the session and the models.

Let's produce the final code.

We'll include:

- `test_filtro_pacientes_hipertensao_vencidos`: creates a mock session with a query that returns a list of patients. We'll use `unittest.mock.MagicMock` to simulate the session and the query. We'll assert that the function returns only patients with overdue hypertension appointments.

- `test_lembretes_respeitam_janela_tolerancia`: tests `enviar_lembrete` with different `agora` times and appointment times.

- `test_idempotencia_disparo_notificacoes`: tests `registrar_notificacao` with a mock session that has a query to check existing notifications.

We'll also add a fixture for a base patient and appointment.

Let's write the code.

We need to be careful with Pydantic v2: use `model_config` or `Field`. We'll use simple classes.

Let's write:

```python
from datetime import datetime, time, timedelta
from typing import List, Optional
from uuid import uuid4

import pytest
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
```

But we don't need to import Session if we use mocks.

We'll define sample models:

```python
class Paciente(BaseModel):
    id: int
    nome: str
    cns: str
    cpf: str
    hipertenso: bool = False

class Consulta(BaseModel):
    id: int
    paciente_id: int
    data_hora: datetime
    status: str = "agendada"
    tipo: str = "retorno"
```

But these are test models, not the actual models. The service functions might expect SQLAlchemy models. We can use mocks for those.

Alternatively, we can use `MagicMock` for the patient and appointment objects, setting attributes.

Let's do that: create simple objects using `types.SimpleNamespace` or `MagicMock`.

For the filter test, we'll create a list of mock patients with attributes like `id`, `hipertenso`, and a relationship to consultations. The function likely queries the database, so we'll mock the session's query to return a list of tuples (patient, consultation) or just patients with a `consultas` relationship.

We'll assume the function `filtrar_pacientes_hipertensao_vencidos` takes a session and a reference date, and returns a list of patients. It probably does a join between patients and consultations, filtering by diagnosis (hypertension) and appointment date < reference date.

We'll mock the session's `query` to return a list of patients that already have the overdue consultations. But then the function would just filter that list. That's okay.

Let's write:

```python
def test_filtro_pacientes_hipertensao_vencidos():
    # Cria pacientes mockados
    paciente_vencido = MagicMock()
    paciente_vencido.id = 1
    paciente_vencido.hipertenso = True
    paciente_vencido.consultas = [MagicMock(data_hora=datetime(2024,1,1,10,0), status="realizada")]

    paciente_nao_vencido = MagicMock()
    paciente_nao_vencido.id = 2
    paciente_nao_vencido.hipertenso = True
    paciente_nao_vencido.consultas = [MagicMock(data_hora=datetime(2024,6,1,10,0), status="agendada")]

    paciente_nao_hipertenso = MagicMock()
    paciente_nao_hipertenso.id = 3
    paciente_nao_hipertenso.hipertenso = False
    paciente_nao_hipertenso.consultas = [MagicMock(data_hora=datetime(2024,1,1,10,0), status="realizada")]

    session = MagicMock()
    session.query.return_value.join.return_value.filter.return_value.all.return_value = [
        paciente_vencido, paciente_nao_vencido, paciente_nao_hipertenso
    ]

    data_referencia = datetime(2024,6,1,0,0)
    resultado = filtrar_pacientes_hipertensao_vencidos(session, data_referencia)

    assert len(resultado) == 1
    assert resultado[0].id == 1
```

But this assumes the function uses `session.query(...).join(...).filter(...).all()`. We can mock that chain.

Alternatively, we can use `patch` to mock the function's internal query. But it's simpler to mock the session.

For the reminder time window test, we'll define a function `enviar_lembrete` that takes `agora` and `consulta_data_hora` and returns a boolean. We'll test various cases.

We'll write:

```python
def test_lembretes_respeitam_janela_tolerancia():
    # Caso 1: Dentro da janela (8h-20h e consulta em até 24h)
    assert enviar_lembrete(datetime(2024,6,1,9,0), datetime(2024,6,2,9,0)) is True
    # Caso 2: Fora do horário (madrugada)
    assert enviar_lembrete(datetime(2024,6,1,3,0), datetime(2024,6,2,9,0)) is False
    # Caso 3: Consulta muito distante (>24h)
    assert enviar_lembrete(datetime(2024,6,1,9,0), datetime(2024,6,3,9,0)) is False
    # Caso 4: Consulta já passou
    assert enviar_lembrete(datetime(2024,6,1,9,0), datetime(2024,5,31,9,0)) is False
```

But we need to define `enviar_lembrete` in the service. We'll assume it exists.

For idempotency, we'll test `registrar_notificacao`:

```python
def test_idempotencia_disparo_notificacoes():
    session = MagicMock()
    # Simula que já existe uma notificação para o paciente/consulta
    session.query.return_value.filter.return_value.first.return_value = MagicMock()
    resultado = registrar_notificacao(session, paciente_id=1, consulta_id=1)
    assert resultado is None  # ou não cria duplicata
    session.add.assert_not_called()
```

But we need to be more specific. The function might return the existing notification or None. We'll assert that `session.add` is not called.

Alternatively, we can test that calling twice creates only one record. We'll mock the session to have a list of notifications.

Let's write a more comprehensive test:

```python
def test_idempotencia_disparo_notificacoes():
    session = MagicMock()
    # Primeira chamada: não existe notificação, deve criar
    session.query.return_value.filter.return_value.first.return_value = None
    notificacao = registrar_notificacao(session, paciente_id=1, consulta_id=1)
    assert notificacao is not None
    session.add.assert_called_once()

    # Segunda chamada: já existe, não deve criar
    session.reset_mock()
    session.query.return_value.filter.return_value.first.return_value = MagicMock()
    notificacao = registrar_notificacao(session, paciente_id=1, consulta_id=1)
    assert notificacao is None
    session.add.assert_not_called()
```

This tests idempotency.

Now, we need to ensure the test file is complete and runnable. We'll include imports and maybe a `conftest.py`? No, just the test file.

We also need to consider that the service functions might not exist. But the task is to create the test file, so we assume they do.

Let's write the final code with proper docstrings and comments.

We'll also add a fixture for `session` to avoid repetition.

Let's produce the answer.```python
# Arquivo: backend/tests/test_mensageria_preventiva.py
"""
Testes para regras de busca ativa e prevenção de spam clínico (C8).

Cobre:
1. Filtro de pacientes com consultas de hipertensão vencidas.
2. Respeito à janela de tolerância de horário para envio de lembretes.
3. Idempotência no disparo de notificações.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

# Importações do projeto (ajustar conforme a estrutura real)
from backend.app.services.mensageria_preventiva import (
    enviar_lembrete,
    filtrar_pacientes_hipertensao_vencidos,
    registrar_notificacao,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def session_mock():
    """Cria uma sessão SQLAlchemy mockada."""
    return MagicMock()


@pytest.fixture
def paciente_hipertenso_vencido():
    """Paciente hipertenso com consulta vencida."""
    paciente = MagicMock()
    paciente.id = 1
    paciente.hipertenso = True
    consulta = MagicMock()
    consulta.data_hora = datetime(2024, 1, 15, 10, 0)
    consulta.status = "realizada"
    paciente.consultas = [consulta]
    return paciente


@pytest.fixture
def paciente_hipertenso_nao_vencido():
    """Paciente hipertenso com consulta futura."""
    paciente = MagicMock()
    paciente.id = 2
    paciente.hipertenso = True
    consulta = MagicMock()
    consulta.data_hora = datetime(2024, 12, 1, 10, 0)
    consulta.status = "agendada"
    paciente.consultas = [consulta]
    return paciente


@p