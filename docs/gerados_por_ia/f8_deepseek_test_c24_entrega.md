We need to create backend/tests/test_mensageria_preventiva.py for the MedIA project. The task: 1) validate filter of patients with overdue hypertension appointments; 2) ensure reminders respect time tolerance window; 3) validate idempotency in notification dispatch.

We need to write tests. We need to infer the structure of the project. Since we don't have the actual code, we need to design tests that would work with typical implementation. We should create a test file that tests functions/classes related to "mensageria preventiva" (preventive messaging). Likely there are services for active search (busca ativa) and spam prevention.

We need to follow architecture: Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS patterns, CIAP-2, CID-10, SOAP, CNS/CPF. Tests should be pytest.

We need to write tests that validate:

1. Filter of patients with overdue hypertension appointments. This likely involves querying patients with hypertension (CID-10 I10-I15 or CIAP-2 K86?) and having appointments that are overdue (scheduled date < today) and not attended/cancelled. We need to test a function that returns such patients.

2. Reminders respect time tolerance window. This likely means that notifications/reminders should only be sent within a certain time window (e.g., not before 8am, not after 8pm, or within a specific tolerance around appointment time). We need to test that the logic correctly filters out reminders outside the window.

3. Idempotency in notification dispatch: sending the same notification multiple times should not result in duplicate sends. This likely involves a unique constraint or a check for existing notification records.

We need to write tests that are plausible. Since we don't have the actual code, we need to create tests that would pass if the implementation is correct. We can use mocks/fakes to simulate database and services.

We should structure the test file with pytest fixtures, using SQLAlchemy in-memory SQLite or mock repositories. We'll need to define models? But we are only writing tests, not implementation. However, tests need to import from the project. We can assume there are modules like `backend.app.services.mensageria` or similar. We'll need to create tests that import from those modules. Since we don't know exact names, we can make reasonable assumptions and write tests that would work if the modules exist. But the instruction says "crie backend/tests/test_mensageria_preventiva.py" - we are to create the test file. We can write tests that are self-contained with mocks, not depending on actual implementation details, but still testing the expected behavior.

We can define test functions that use monkeypatch or dependency injection to test the logic. For example, we can test a function `filtrar_pacientes_hipertensos_consulta_vencida` that takes a list of patients and returns those with overdue hypertension appointments. We can create sample data.

Alternatively, we can write tests that use SQLAlchemy models defined in the test file? But that would be redundant. Better to use mocks.

Given the task, we need to produce a test file that is comprehensive and follows best practices. We'll write tests that:

- Use pytest fixtures to create a test database (SQLite in-memory) with tables for patients, appointments, notifications.
- Define minimal models (or use existing models if we can import them). Since we don't know, we can define our own models in the test file? That might be acceptable for testing, but it's not ideal. However, the instruction says "Código em Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0." So we should use SQLAlchemy 2.0 style.

We can create a test that uses SQLAlchemy's declarative base to define temporary models for testing. But that would be testing our own models, not the project's. The task is to test the project's logic. We need to import the actual code. Since we don't have it, we can only write tests that assume certain interfaces. We can use `pytest.importorskip` to skip if modules not found? But the task expects us to create the test file, presumably for a project that exists. We should write tests that are likely to match the project's structure.

Let's think about the domain: "mensageria preventiva" likely includes services for "busca ativa" (active search) and "prevenção de spam clínico" (clinical spam prevention). The tests are for rules: filter patients with overdue hypertension appointments, respect time tolerance, idempotency.

We can create a test file that tests a service class, e.g., `MensageriaPreventivaService`, with methods:

- `buscar_pacientes_hipertensos_consulta_vencida()` -> list of patients
- `enviar_lembrete(paciente, consulta)` -> sends notification, respecting time window
- `enviar_lembrete` should be idempotent.

We'll write tests using mocks for the database session and notification sender.

We'll need to define sample data using Pydantic models? We can use simple dataclasses or dictionaries.

Given the instruction to use Pydantic v2, we can create Pydantic models for test data.

Let's outline the test file:

- Imports: pytest, datetime, timedelta, from sqlalchemy import create_engine, etc. But we might not need SQLAlchemy if we use mocks.

We can write unit tests that don't require a database, just test the logic functions. For example, a function `filtrar_consultas_vencidas(consultas, data_referencia)` that filters appointments where `data_hora < data_referencia` and status is 'agendada' or 'confirmada' and patient has hypertension. We can test that.

Similarly, a function `respeita_janela_tolerancia(horario_consulta, horario_atual, tolerancia)` that returns True if current time is within tolerance before appointment.

And a function `enviar_notificacao_idempotente(notificacao_id, enviar_func)` that checks if already sent.

But the task says "valida filtro de pacientes com consultas de hipertensão vencidas" - so we need to test the filter. "assegura que lembretes respeitam janela de tolerância de horário" - test the time window logic. "valida idempotência no disparo de notificações" - test idempotency.

We can write tests that directly test these three aspects.

Let's create a test file with:

- Fixtures for sample data (patients, appointments).
- Tests for filtering overdue hypertension appointments.
- Tests for time tolerance.
- Tests for idempotency.

We'll use Pydantic models for Patient and Appointment.

We'll also use a simple in-memory store for notifications to test idempotency.

We'll write the tests in a way that they can be run independently, without needing the actual project code. But the instruction says "Para o Projeto MedIA, crie backend/tests/test_mensageria_preventiva.py" - so we are creating the test file for the project. It's okay to write tests that assume the existence of certain functions/classes, but we need to provide the code. Since we are the coder, we can also create the implementation? The task only asks to create the test file. But to make tests pass, we might need to also create the implementation? The instruction says "Execute com precisão conforme as diretrizes." It doesn't ask to create implementation, only tests. However, tests that import non-existent modules will fail. We can write tests that are self-contained and don't import project modules, but that would not be testing the project. The task likely expects us to write tests for existing code. Since we don't have the code, we need to make reasonable assumptions and write tests that would pass if the code is correct. We can use `pytest` with `unittest.mock` to mock the service functions.

Maybe we can write tests that use `monkeypatch` to replace the service functions with our own logic? That would be testing the test itself, not the code.

Better approach: Write tests that define the expected behavior and use mocks to simulate the database and external services. We'll create a test class that uses a fake repository and a fake notification sender. We'll test the service methods by instantiating the service with these fakes. This way, the tests are independent of the actual implementation, but they validate the logic that the service should have. However, if the service doesn't exist, the tests will fail at import. We can use `pytest.importorskip` to skip if the module is not available. But the task says "crie backend/tests/test_mensageria_preventiva.py" - we are to create the file, not necessarily ensure it passes without the implementation. In a real project, the implementation would exist.

Given the constraints, I'll write a test file that imports from `backend.app.services.mensageria_preventiva` (or similar) and uses mocks for dependencies. I'll also include fallback definitions if the module doesn't exist? That would be messy.

Alternatively, we can write tests that are purely unit tests of pure functions that we define in the test file itself, but that would be testing our own code, not the project's. The task is to test the project's rules. So we need to test the project's code.

I think the best is to write tests that assume the existence of a service class with specific methods, and use mocks for the database session and notification sender. We'll write the tests in a way that they can be adapted to the actual implementation. We'll also include comments explaining the expected behavior.

Let's design:

- `backend/tests/test_mensageria_preventiva.py`

We'll have:

```python
import pytest
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
```

Define Pydantic models for test data:

```python
class Paciente(BaseModel):
    id: int
    nome: str
    cns: str
    cpf: str
    possui_hipertensao: bool = False

class Consulta(BaseModel):
    id: int
    paciente_id: int
    data_hora: datetime
    status: str  # 'agendada', 'confirmada', 'realizada', 'cancelada'
    tipo: str  # 'hipertensao' or other
```

Then we'll have a service class that we'll mock? Actually, we can test the service by creating a fake repository and passing it to the service. But we need the service class. We can import it:

```python
from backend.app.services.mensageria_preventiva import MensageriaPreventivaService
```

If that doesn't exist, the test will fail. But we can use `pytest.importorskip` to skip if not available. However, the task expects us to create the test file, not necessarily to make it pass without the implementation. In a real scenario, the implementation would be there.

Given the instruction "Execute com precisão conforme as diretrizes", I'll write the test file with the assumption that the service exists. I'll also include a `conftest.py`? No, just the test file.

Let's write tests:

1. Test filter of patients with overdue hypertension appointments.

We'll create a fake repository that returns a list of patients and consultations. We'll test that the service method `buscar_pacientes_hipertensos_consulta_vencida` returns only patients with hypertension and with at least one consultation that is overdue (data_hora < now) and status in ('agendada', 'confirmada').

We'll use `datetime.now(timezone.utc)` for reference.

2. Test time tolerance.

We'll test a method `enviar_lembrete` that checks if the current time is within a tolerance window before the appointment. For example, reminders should be sent only if the appointment is within 24 hours and not less than 1 hour before? Or a specific window. We'll define a constant `JANELA_TOLERANCIA` and test that reminders are sent when within window and not sent when outside.

We'll mock the notification sender to record calls.

3. Test idempotency.

We'll test that calling `enviar_lembrete` twice for the same consultation does not send duplicate notifications. We'll use a fake notification store that records sent notifications, and the service checks if a notification already exists for that consultation before sending.

We'll write tests using `unittest.mock` to mock the repository and sender.

Let's write the test file.

We need to be careful with timezone. Use `datetime.now(timezone.utc)`.

We'll define a fixture for the service with mocked dependencies.

We'll also define a fake repository class that implements the methods the service expects.

Let's write the code.

We'll include type hints.

We'll use `pytest` and `unittest.mock`.

We'll also include a test for the filter that ensures patients without hypertension are excluded, and patients with hypertension but no overdue consultations are excluded.

For time tolerance, we'll test that a reminder is sent when the current time is within the window, and not sent when outside. We'll also test that the reminder is sent only once (idempotency) even if called multiple times.

We'll combine idempotency with time tolerance.

Let's create the test file.

We'll need to define the service class? No, we'll import it. But to make the test file self-contained, we can define a dummy service class in the test file and use it? That would be testing our dummy, not the project. Better to import.

I'll write the test file with imports from `backend.app.services.mensageria_preventiva`. If the module doesn't exist, the test will error. But that's okay; the task is to create the test file for the project.

Let's also include a `pytest.importorskip` at the top to skip if the module is not available, but that might hide errors. I'll not use it.

We'll write the tests with clear names.

Let's produce the finalanswer.```python
# Arquivo: backend/tests/test_mensageria_preventiva.py
"""
Testes para as regras de busca ativa e prevenção de spam clínico (C24).

Cobre:
1. Filtro de pacientes com consultas de hipertensão vencidas.
2. Respeito à janela de tolerância de horário para envio de lembretes.
3. Idempotência no disparo de notificações.

Segue as diretrizes do Projeto MedIA:
- Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0.
- Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, CNS/CPF).
- Cobertura de testes automatizados com pytest.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Protocol
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# Modelos de dados de teste (Pydantic v2)
# -----------------------------------------------------------------------------


class Paciente(BaseModel):
    """Representa um paciente no domínio de teste."""

    id: int
    nome: str
    cns: str
    cpf: str
    possui_hipertensao: bool = False


class Consulta(BaseModel):
    """Representa uma consulta médica no domínio de teste."""

    id: int
    paciente_id: int
    data_hora: datetime
    status: str  # 'agendada', 'confirmada', 'realizada', 'cancelada'
    tipo: str = "hipertensao"  # usado para identificar consultas de hipertensão


class Notificacao(BaseModel):
    """Representa uma notificação já enviada (para controle de idempotência)."""

    id: int
    consulta_id: int
    paciente_id: int
    enviada_em: datetime


# -----------------------------------------------------------------------------
# Protocolos / contratos esperados do serviço de mensageria preventiva
# -----------------------------------------------------------------------------


class RepositorioPacientes(Protocol):
    """Interface mínima para o repositório de pacientes."""

    def listar_pacientes_hipertensos(self) -> List[Paciente]: ...

    def listar_consultas_por_paciente(self, paciente_id: int) -> List[Consulta]: ...


class RepositorioNotificacoes(Protocol):
    """Interface mínima para o repositório de notificações."""

    def existe_notificacao(self, consulta_id: int) -> bool: ...

    def registrar_notificacao(self, notificacao: Notificacao) -> None: ...


class ServicoMensageria(Protocol):
    """Contrato do serviço de mensageria preventiva."""

    def buscar_pacientes_hipertensos_consulta_vencida(
        self, data_referencia: Optional[datetime] = None
    ) -> List[Paciente]: ...

    def enviar_lembrete(
        self, paciente: Paciente, consulta: Consulta, agora: Optional[datetime] = None
    ) -> bool: ...


# -----------------------------------------------------------------------------
# Fakes e mocks para os testes
# -----------------------------------------------------------------------------


class FakeRepositorioPacientes:
    """Repositório fake com dados controlados."""

    def __init__(self, pacientes: List[Paciente], consultas: List[Consulta]):
        self._pacientes = pacientes
        self._consultas = consultas

    def listar_pacientes_hipertensos(self) -> List[Paciente]:
        return [p for p in self._pacientes if p.possui_hipertensao]

    def listar_consultas_por_paciente(self, paciente_id: int) -> List[Consulta]:
        return [c for c in self._consultas if c.paciente_id == paciente_id]


class FakeRepositorioNotificacoes:
    """Repositório fake de notificações para testar idempotência."""

    def __init__(self):
        self._notificacoes: List[Notificacao] = []
        self._next_id = 1

    def existe_notificacao(self, consulta_id: int) -> bool:
        return any(n.consulta_id == consulta_id for n in self._notificacoes)

    def registrar_notificacao(self, notificacao: Notificacao) -> None:
        self._notificacoes.append