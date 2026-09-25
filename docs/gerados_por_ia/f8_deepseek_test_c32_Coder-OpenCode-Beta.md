We need to create backend/tests/test_mensageria_preventiva.py for the MedIA project. The task: "TAREFA: Testes de Regras de Busca Ativa e Prevenção de Spam Clínico (C32)" - Tests for Active Search Rules and Clinical Spam Prevention (C32). We need to create tests that:

1) valida filtro de pacientes com consultas de hipertensão vencidas - validate filter of patients with overdue hypertension appointments.
2) assegura que lembretes respeitam janela de tolerância de horário - ensure reminders respect time tolerance window.
3) valida idempotência no disparo de notificações - validate idempotency in sending notifications.

We need to follow architecture guidelines: Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0. Patterns: SUS/APS (CIAP-2, CID-10, SOAP method, identification by CNS/CPF). Maintain full compliance and test coverage with pytest.

We need to produce a complete test file. We need to infer the structure of the project. Since we don't have the actual codebase, we'll need to create tests that are plausible, using mocks/factories, and maybe define some fixtures. We should assume there are models/services for patients, appointments, notifications, etc. We'll write tests that validate the behavior.

We need to be careful: The task says "Cree backend/tests/test_mensageria_preventiva.py" - create that file. We'll provide the full code.

We need to include imports, fixtures, test functions. We'll use pytest, maybe with SQLAlchemy in-memory SQLite, Pydantic models, etc. We'll need to mock or create fake data.

Let's design the tests:

1) Filter patients with overdue hypertension appointments. We need a function that queries patients with appointments for hypertension (maybe diagnosis code I10-I15 or CIAP-2 code for hypertension) that are overdue (appointment date < today) and not completed/cancelled? We'll write a test that creates some patients with appointments, some overdue, some not, and asserts the filter returns only overdue hypertension ones.

2) Reminders respect time tolerance window. There's likely a rule that reminders should only be sent within a certain window before the appointment (e.g., 24-48 hours before, or maybe after overdue? Actually "janela de tolerância de horário" could mean that reminders should not be sent outside allowed hours, e.g., not at night, or within a specific time before appointment. We need to interpret. The phrase "lembretes respeitam janela de tolerância de horário" - reminders respect time tolerance window. Could be that if an appointment is scheduled at a certain time, the reminder should be sent within a window (e.g., between 24h and 1h before). Or it could be about not sending reminders outside business hours. We'll need to define a plausible function that checks if the current time is within a tolerance window relative to appointment time. We'll test that reminders are only sent when within the window.

3) Idempotency in sending notifications. This means that if the same notification is triggered multiple times, it should not be sent more than once. We'll test that calling the send function twice for the same patient/appointment does not create duplicate notifications.

We need to write tests that are self-contained. We'll need to create some domain models. Since we don't have the actual code, we'll create minimal Pydantic models and SQLAlchemy models within the test file? Or we can use mocks. Better to create a test that uses mocks to simulate the service functions. But the task says "Cree backend/tests/test_mensageria_preventiva.py" - it's a test file, so we can define fixtures and use mocks.

We should also consider the architecture: "Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF)." So we should include these in the test data: e.g., patients have CNS/CPF, diagnoses use CID-10 codes, CIAP-2 codes for reasons, SOAP method for notes. We'll incorporate that.

Let's outline the test file:

- Imports: pytest, datetime, timedelta, from sqlalchemy import create_engine, etc. But we might not need actual DB if we use mocks. However, to test filters, we might need a query. We can create a fake repository or use SQLAlchemy with in-memory SQLite. Let's do that for realism.

We'll define SQLAlchemy models: Patient, Appointment, Notification, maybe ReminderRule. But we can also use Pydantic for schemas. The test file can define these models locally, but that might be too much. Alternatively, we can use mocks of the service functions. The task is to test rules, not to implement them. So we can mock the service layer and test the logic.

But to test "filtro de pacientes com consultas de hipertensão vencidas", we need to test the actual filter logic. If we mock the service, we're not testing the filter. So we need to implement the filter in the test? No, we need to test the existing filter. Since we don't have the existing code, we'll need to assume there is a function like `get_patients_with_overdue_hypertension_appointments(session)` and we'll test it by creating a session with data. But we need to define the model. We can define minimal models in the test file to support the test. That's acceptable for a test file, though it's not ideal. But the instruction says "Cree backend/tests/test_mensageria_preventiva.py" - we can include test-specific models.

Alternatively, we can use mocks to simulate the database and test the service logic by patching. But that's less robust.

Given the constraints, I'll create a test file that defines minimal SQLAlchemy models (Patient, Appointment, Notification) and uses an in-memory SQLite database. The models will include fields for CNS/CPF, diagnosis codes, appointment dates, status, etc. Then we'll write tests for the three requirements.

We'll also need to define some helper functions that might be part of the service, but we can implement them in the test file as "production code" for the purpose of testing? Actually, the test should import from the actual backend modules. Since we don't have them, we can't. So we need to create a test that is self-contained, but that doesn't test actual code. That's not ideal. The instruction likely expects us to write tests that would be run against a real implementation, but we don't have it. We need to make reasonable assumptions and write tests that would pass if the implementation follows the described rules.

Maybe we can create a "conftest.py" or use mocks to simulate the service. But the task specifically says "Cree backend/tests/test_mensageria_preventiva.py" - so we just need to provide that file. It can contain tests that use mocks and patch the actual service functions. But we need to know the function names. We can invent them.

Let's think: The project MedIA likely has a module for "mensageria preventiva" (preventive messaging). There might be functions like:

- `buscar_pacientes_hipertension_vencidos(db)` - returns list of patients with overdue hypertension appointments.
- `enviar_recordatorio(paciente, cita, hora_actual)` - sends reminder if within tolerance window.
- `enviar_notificacion(paciente, cita)` - sends notification, but idempotent.

We can write tests that mock these functions and assert they are called correctly. But that doesn't test the logic. Alternatively, we can write tests that use a fake implementation of these functions within the test file, but then we're testing our own fake, not the real code. That's not useful.

Given the ambiguity, I'll write tests that are more like unit tests for the service logic, assuming the service functions are implemented in a module `backend.app.services.mensageria` or similar. We'll use `pytest` with `unittest.mock` to patch the dependencies. We'll test the behavior by calling the service functions and checking the results. We'll need to define the service functions in the test? No, we'll import them. But since we don't have them, we can't. We can use `pytest.importorskip` to skip if not available? That's not good.

Maybe the best approach is to create a test file that defines the expected behavior using mocks and also includes some "contract" tests that would fail if the implementation doesn't meet the rules. But we need to write actual test code.

Let's re-read the task: "Para el Proyecto MedIA, cree backend/tests/test_mensageria_preventiva.py: 1) valida filtro de pacientes con consultas de hipertensión vencidas; 2) asegura que los recordatorios respetan ventana de tolerancia de horario; 3) valida idempotencia en el disparo de notificaciones."

So we need to create a test file that validates these three things. We can write tests that use mocks to simulate the data and assert that the service functions behave correctly. We'll need to define the service functions as mocks? Actually, we can use `unittest.mock` to patch the service functions and assert they are called with correct arguments. But that doesn't validate the logic.

Alternatively, we can write tests that use a fake repository and a fake notification sender, and test the "rules" by implementing them in the test? That seems wrong.

Given the context, I think the intended solution is to write tests that would be used to verify the implementation of these rules. The test file should contain test cases that, given certain inputs (patients, appointments, times), assert the output of the functions. Since we don't have the actual functions, we need to assume they exist and are importable. We'll write the tests with imports like:

```python
from backend.app.services.mensageria import (
    get_patients_with_overdue_hypertension_appointments,
    send_reminder,
    send_notification,
)
```

But if those don't exist, the tests will fail. However, the task is to create the test file, not the implementation. So it's okay if the tests are written against a hypothetical API. The test file will be used later when the implementation is done.

We'll also need to define fixtures for database session, sample data, etc. We'll use SQLAlchemy in-memory SQLite for the database. We'll define models in the test file? No, we should import models from the app. But again, we don't have them. We can use `pytest` fixtures that create a test database and use the actual models. But we don't know the models.

Maybe we can create a "conftest.py" that provides fixtures, but the task only asks for the test file. We can include everything in the test file.

Let's decide: We'll write a test file that is self-contained, defining minimal SQLAlchemy models and service functions (as part of the test file) to demonstrate the tests. But that would be testing our own code, not the project's. However, the task is to create tests, not implementation. It's common to write tests that define the expected behavior, and then the implementation is written to pass them. So we can write tests that use a "contract" approach: we define the expected behavior in the tests, and the implementation must match. We can use mocks to simulate the database and the notification sender, and we can write tests that call functions that we expect to exist. If they don't exist, the tests will fail, but that's okay because the implementation hasn't been done yet.

Given the instruction "Ejecute con precisión conforme a las directrices" - we need to produce a precise test file. I'll write a test file that uses `pytest` and `unittest.mock` to test the three rules. I'll assume the existence of a service module with functions:

- `get_patients_with_overdue_hypertension_appointments(db_session)` -> returns list of patients.
- `should_send_reminder(appointment_time, current_time, tolerance_window)` -> bool.
- `send_notification(patient, appointment, db_session)` -> sends and records notification.

But to test idempotency, we need to check that if `send_notification` is called twice, only one notification is created. We can use a mock for the notification sender and assert it's called once.

Let's design the tests:

1) Test filter: We'll create a mock database session with a query that returns patients. We'll patch the session's query to return a list of patients with appointments. We'll assert that the function returns only those with overdue hypertension appointments.

We can use SQLAlchemy's `create_mock_engine`? Better to use `unittest.mock.MagicMock` for the session. We'll create a list of Patient objects (Pydantic models or simple objects) with appointments. We'll patch the session's `query` method to return a mock that filters. But that's complex.

Alternatively, we can use an in-memory SQLite database with actual SQLAlchemy models. We'll define the models in the test file. This is more robust and tests the query logic. Let's do that.

We'll define:

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
```

Define `Base`, `Patient`, `Appointment`, `Notification`.

Patient: id, cns, cpf, name, etc.
Appointment: id, patient_id, scheduled_at (DateTime), status (String), diagnosis_code (String) for CID-10, ciap2_code (String), is_hypertension (maybe derived from diagnosis_code).
Notification: id, patient_id, appointment_id, sent_at, type.

We'll create a function `get_patients_with_overdue_hypertension_appointments(session)` that queries appointments with diagnosis_code in hypertension codes (e.g., I10-I15) and scheduled_at < now and status == 'scheduled' (or not completed). We'll implement this function in the test file? No, we need to test the actual function. But we can define it in the test file as a helper? That would be testing our helper, not the app's.

Given the constraints, I'll write the tests using mocks for the service functions, and also include a test that uses an in-memory DB to test the query logic if we assume the function is implemented. But we need to decide.

Maybe the best is to write tests that use `unittest.mock.patch` to patch the service functions and assert they are called with the right arguments. For example:

- Test 1: Patch `get_patients_with_overdue_hypertension_appointments` to return a known list. Then call a higher-level function that uses it? That doesn't test the filter.

Actually, the task says "valida filtro de pacientes con consultas de hipertensión vencidas" - we need to validate the filter itself. So we need to test the function that does the filtering. We can write a test that creates a database with sample data and calls the function, asserting the result. That requires the function to exist. We'll assume it exists and import it. If it doesn't, the test will fail, but that's okay.

Let's write the test file with imports from `backend.app.services.mensageria` and `backend.app.models` etc. We'll also include a `conftest`? No.

I'll create a test file that is self-contained with minimal models and functions, but I'll clearly mark that these are "fixtures" for the test. Actually, the test file should test the actual code, not define it. But since we don't have the actual code, we can't. The task is to create the test file, so we can write it in a way that it would work with the actual code if it follows the described patterns.

Let's assume the project has the following structure:

- `backend/app/models/patient.py` with `Patient` model.
- `backend/app/models/appointment.py` with `Appointment` model.
- `backend/app/models/notification.py` with `Notification` model.
- `backend/app/services/mensageria.py` with functions.

We'll write tests that import these. We'll also use `pytest` fixtures to create a test database.

I'll write the test file with:

```python
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models import Base, Patient, Appointment, Notification
from backend.app.services.mensageria import (
    get_patients_with_overdue_hypertension_appointments,
    send_reminder,
    send_notification,
)
```

But we need to define the models. We can't import from `backend.app.models` if it doesn't exist. However, the test file is part of the project, so it's expected that those modules exist. We'll write the tests assuming they do.

We'll also need to define a fixture for the database session:

```python
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

Then we'll create sample data.

For test 1:

```python
def test_filtro_pacientes_hipertension_vencidos(db_session):
    # Create patients
    p1 = Patient(cns="123456789012345", cpf="12345678901", name="Paciente 1")
    p2 = Patient(cns="234567890123456", cpf="23456789012", name="Paciente 2")
    p3 = Patient(cns="345678901234567", cpf="34567890123", name="Paciente 3")
    db_session.add_all([p1, p2, p3])
    db_session.commit()

    # Create appointments
    now = datetime.utcnow()
    # Overdue hypertension
    a1 = Appointment(patient=p1, scheduled_at=now - timedelta(days=30), status="scheduled", diagnosis_code="I10")
    # Future hypertension
    a2 = Appointment(patient=p2, scheduled_at=now + timedelta(days=30), status="scheduled", diagnosis_code="I10")
    # Overdue non-hypertension
    a3 = Appointment(patient=p3, scheduled_at=now - timedelta(days=30), status="scheduled", diagnosis_code="J00")
    db_session.add_all([a1, a2, a3])
    db_session.commit()

    result = get_patients_with_overdue_