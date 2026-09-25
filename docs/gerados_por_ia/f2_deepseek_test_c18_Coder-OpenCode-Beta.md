We need to create a test file for the MedIA project. The task: create backend/tests/test_farmacia_dispensacao.py validating three things: 1) prescriptions with tampered hash are rejected; 2) duplicate dispensing of same prescription is prevented; 3) partial dispensing records remaining balance.

We need to understand the project structure. It's a backend with Python 3.12, Pydantic v2, SQLAlchemy 2.0. We need to write tests. Likely there are existing models and services for farmácia (pharmacy) and dispensação. We need to infer the architecture.

We should create a test file that uses pytest, possibly with fixtures for database session, etc. We need to ensure tests are comprehensive.

Let's think about what the test file should contain. We'll need to import relevant modules. Since we don't have the actual code, we need to make reasonable assumptions. The task says "Crie backend/tests/test_farmacia_dispensacao.py" - so we need to create that file. We'll write tests that would pass given the described functionality. We'll need to mock or use actual models.

We should define test cases:

1. Test that a prescription with tampered hash is rejected. This implies there is a validation function that checks hash integrity. We'll need to simulate a prescription with a hash that doesn't match its content. We'll create a prescription object (maybe via factory) and then tamper with it, then call the service/endpoint that validates and expect an error.

2. Test that duplicate dispensing of same prescription is prevented. There should be a unique constraint or logic to prevent re-dispensing the same prescription. We'll attempt to dispense twice and expect an error on the second.

3. Test partial dispensing records remaining balance. When a prescription has a quantity, and we dispense partially, the remaining balance should be recorded. We'll test that after a partial dispensing, the prescription's remaining quantity is updated correctly.

We need to write tests that are executable. Since we don't have the actual code, we'll need to create a test file that imports from the project's modules. We'll assume there are models like Prescription, Dispensation, etc. We'll also need to set up a test database (SQLite in-memory) and use SQLAlchemy.

We'll write tests using pytest fixtures. We'll need to create the database schema, create a session, and use factories or direct ORM objects.

Let's outline the test file:

- Imports: pytest, sqlalchemy, pydantic, datetime, decimal, etc.
- Import models and services from the backend package.
- Define fixtures: db_session, client (if testing API), etc.

But since we don't know the exact structure, we need to make it generic. Perhaps we can write tests that are self-contained, using a minimal in-memory SQLite database with the necessary tables. However, the task says "Para o Projeto MedIA, crie backend/tests/test_farmacia_dispensacao.py" - so we need to create the file in the context of the project. We'll assume the project has a structure like:

backend/
  app/
    models/
      farmacia.py
    services/
      farmacia.py
    schemas/
      farmacia.py
  tests/
    conftest.py
    test_farmacia_dispensacao.py

We'll write the test file assuming the existence of these modules. We'll need to import from app.models, app.services, etc.

We should also consider that the tests might be run with pytest. We'll use pytest fixtures.

Let's design the tests:

Test 1: test_receita_hash_adulterado_rejeitado
- Create a prescription with a valid hash.
- Tamper with the hash (e.g., change a character).
- Call the validation function (maybe `validate_prescription_hash` or `dispense` service) and expect an exception (e.g., `HashMismatchError` or `ValidationError`).
- Alternatively, if it's an API endpoint, we can use TestClient to POST to /dispensar and expect 400.

Test 2: test_dispensacao_duplicada_impedida
- Create a prescription.
- Dispense it once successfully.
- Attempt to dispense again and expect an error (e.g., `DuplicateDispensationError` or a database IntegrityError).

Test 3: test_baixa_parcial_registra_saldo
- Create a prescription with quantity 10.
- Dispense 4 units.
- Check that the remaining balance is 6 (or that the prescription's dispensed quantity is 4 and remaining is 6).

We'll need to define the models. Let's assume:

- `Prescription` model: id, patient_cns, prescription_hash, medication, quantity, dispensed_quantity, created_at, etc.
- `Dispensation` model: id, prescription_id, quantity, created_at, etc.

We'll also need a service function like `dispense_prescription(prescription_id, quantity)` that handles validation and updates.

Given the lack of actual code, we'll write tests that are clear and follow the described behavior. We'll use mocks where necessary, but ideally we want to test the actual implementation. Since we don't have it, we'll write tests that would pass if the implementation is correct. We'll also include comments.

We need to ensure the test file is complete and executable. We'll include necessary imports and fixtures.

Let's write the file. We'll use SQLAlchemy 2.0 style with Declarative Base. We'll create a test database using SQLite in-memory. We'll define the models in the test file? That would be weird. Better to import from the app. But we don't have the app code. We'll assume the app has these models. We'll write the test file with imports that would work if the app exists.

Alternatively, we can create a minimal setup in the test file itself, defining the models and services, to demonstrate the tests. But the task says "Para o Projeto MedIA" - so we should write tests for the project, not a standalone. However, since we are an AI generating code, we need to produce a file that is plausible and can be run in the project context.

I'll write the test file with imports from `backend.app.models.farmacia` and `backend.app.services.farmacia`. I'll also include a conftest.py? The task only asks for the test file. But we can include fixtures within the test file.

Let's structure:

```python
# Arquivo: backend/tests/test_farmacia_dispensacao.py
"""
Testes de integridade da dispensação e validação hash (C18).
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from backend.app.models.farmacia import Prescription, Dispensation
from backend.app.services.farmacia import dispense_prescription, validate_prescription_hash
from backend.app.core.exceptions import HashMismatchError, DuplicateDispensationError
```

But we need to define the database session fixture. We'll create an engine and session.

We'll also need to create tables. We'll use `Base.metadata.create_all(engine)`.

Let's assume the models are defined with SQLAlchemy. We'll need to import Base from somewhere.

We'll write:

```python
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()
```

But we need to import Base. We'll assume it's in `backend.app.database`.

Now, for the tests:

Test 1:

```python
def test_receita_hash_adulterado_rejeitado(db_session):
    # Cria uma receita válida
    receita = Prescription(
        patient_cns="123456789012345",
        medication="Amoxicilina 500mg",
        quantity=10,
        prescription_hash="hash_valido",
    )
    db_session.add(receita)
    db_session.commit()

    # Adultera o hash
    receita.prescription_hash = "hash_adulterado"

    # A validação deve falhar
    with pytest.raises(HashMismatchError):
        validate_prescription_hash(receita)
```

But we need to know how the hash is computed. Maybe the hash is computed from the prescription data. So we need to create a prescription with a valid hash. We could compute it using a function. We'll assume there is a function `compute_prescription_hash(prescription_data)`.

Let's adjust:

```python
from backend.app.services.farmacia import compute_prescription_hash

def test_receita_hash_adulterado_rejeitado(db_session):
    receita_data = {
        "patient_cns": "123456789012345",
        "medication": "Amoxicilina 500mg",
        "quantity": 10,
    }
    hash_valido = compute_prescription_hash(receita_data)
    receita = Prescription(
        patient_cns=receita_data["patient_cns"],
        medication=receita_data["medication"],
        quantity=receita_data["quantity"],
        prescription_hash=hash_valido,
    )
    db_session.add(receita)
    db_session.commit()

    # Adultera o hash
    receita.prescription_hash = "hash_adulterado"

    with pytest.raises(HashMismatchError):
        validate_prescription_hash(receita)
```

Test 2:

```python
def test_dispensacao_duplicada_impedida(db_session):
    receita = Prescription(
        patient_cns="123456789012345",
        medication="Amoxicilina 500mg",
        quantity=10,
        prescription_hash="hash_valido",
    )
    db_session.add(receita)
    db_session.commit()

    # Primeira dispensação
    dispense_prescription(db_session, receita.id, quantity=5)

    # Segunda dispensação deve falhar
    with pytest.raises(DuplicateDispensationError):
        dispense_prescription(db_session, receita.id, quantity=5)
```

But we need to ensure that the service checks if the prescription has already been fully dispensed or if there is any dispensation. The requirement says "dispensação duplicada de mesma receita é impedida" - meaning the same prescription cannot be dispensed more than once? Or cannot be dispensed twice for the same quantity? Usually a prescription can be partially dispensed multiple times until the total quantity is reached. But the requirement says "dispensação duplicada de mesma receita é impedida" - could mean that you cannot dispense the same prescription twice for the same medication? Or that you cannot create a duplicate dispensation record for the same prescription? Let's interpret: "dispensação duplicada de mesma receita é impedida" - duplicate dispensing of the same prescription is prevented. This likely means that a prescription cannot be dispensed more than once in total? But that would conflict with partial dispensing. Actually, partial dispensing means you can dispense part of the quantity and later dispense the rest. So duplicate dispensing might mean that you cannot dispense the same prescription again after it has been fully dispensed, or you cannot create two dispensation records for the same prescription at the same time? The requirement also says "baixa parcial registra saldo remanescente" - partial dispensing records remaining balance. So partial dispensing is allowed. Therefore, duplicate dispensing likely means that you cannot dispense the same prescription twice for the same quantity? Or that you cannot have two active dispensations for the same prescription? Let's think.

In pharmacy, a prescription can be filled partially, and the remaining balance is tracked. You can have multiple dispensations for the same prescription as long as the total dispensed does not exceed the prescribed quantity. So "dispensação duplicada" might mean that you cannot dispense the same prescription again if it has already been fully dispensed, or if the remaining balance is zero. Or it could mean that you cannot have two dispensation records for the same prescription with the same date/time? That seems odd.

Given the context, I think the test should verify that if you try to dispense a prescription that has already been fully dispensed (i.e., remaining quantity is zero), it is rejected. Or if you try to dispense more than the remaining quantity, it is rejected. But the requirement says "dispensação duplicada de mesma receita é impedida" - duplicate dispensing of same prescription is prevented. This could be interpreted as: you cannot dispense the same prescription more than once (i.e., a prescription can only be dispensed once). But then partial dispensing would be impossible. Unless "dispensação" refers to the act of dispensing the entire prescription, and "baixa parcial" is a separate operation that records partial dispensing. Hmm.

Let's re-read: "1) receitas com hash adulterado são rejeitadas; 2) dispensação duplicada de mesma receita é impedida; 3) baixa parcial registra saldo remanescente." So there are three distinct tests. The second is about duplicate dispensing being prevented. The third is about partial dispensing recording remaining balance. So they are separate. So duplicate dispensing likely means that you cannot dispense the same prescription twice in a way that would exceed the total quantity or that the prescription has already been fully dispensed. But the phrase "duplicada" suggests a duplicate record, not exceeding quantity. Perhaps the system has a rule that a prescription can only be dispensed once (i.e., one dispensation per prescription). But then partial dispensing would be a separate concept: you can record a partial dispensing (baixa parcial) which updates the remaining balance, but you cannot create a new dispensation for the same prescription. That seems contradictory.

Maybe the intended meaning: A prescription has a unique hash. When dispensing, the system checks if that prescription hash has already been used for a dispensation. If so, it rejects the duplicate. This prevents the same prescription from being filled twice (e.g., at different pharmacies). So "dispensação duplicada" means using the same prescription hash to dispense again. This is a common anti-fraud measure. So the test would be: create a prescription, dispense it, then try to dispense again using the same prescription hash, and expect an error. This aligns with the hash validation: the hash is used to identify the prescription uniquely. So duplicate dispensing is prevented by checking if a dispensation already exists for that prescription hash.

Thus, in the test, we should have a prescription with a unique hash. After dispensing, we attempt to dispense again (maybe by calling the service with the same prescription id or hash) and expect an error.

We'll implement that.

Test 3: partial dispensing records remaining balance. So we create a prescription with quantity 10, dispense 4, then check that the remaining balance is 6. This implies that the prescription model has a field like `remaining_quantity` or `dispensed_quantity`. We'll check that.

Now, we need to write the test file. Since we don't have the actual implementation, we'll write tests that are clear and use the expected API. We'll also include a conftest.py? The task only asks for the test file, but we can include fixtures in the test file.

We'll also need to handle the case where the service functions are not defined. But we are writing the tests, so we'll assume they exist.

Let's write the file with proper imports and fixtures.

We'll also need to consider that the project uses Pydantic v2 and SQLAlchemy 2.0. We'll use type hints.

I'll write the test file with the following structure:

- Module docstring.
- Imports.
- Fixtures: `db_session` (creates in-memory SQLite, creates tables, yields session).
- Helper functions: `create_prescription` (maybe).
- Tests.

We'll also need to import the models and services. Since we don't know the exact paths, we'll use relative imports? Actually, the test file is in `backend/tests/`, so we can import from `backend.app...` or from `app...` depending on the project structure. Usually, tests are run from the backend directory, so we can use `from app.models.farmacia import ...`. We'll use that.

Let's assume the project structure:

backend/
  app/
    __init__.py
    models/
      __init__.py
      farmacia.py
    services/
      __init__.py
      farmacia.py
    core/
      exceptions.py
    database.py
  tests/
    conftest.py
    test_farmacia_dispensacao.py

We'll write the test file accordingly.

Now, let's write the code.

We'll need to define the models in the test? No, we'll import them. But to make the test file self-contained and runnable even without the actual app, we could define minimal models in the test file. However, the task says "Para o Projeto MedIA" - so we should write tests for the project. I'll write tests that import from the app, and include comments explaining the expected behavior.

If the actual app doesn't have these exact models, the tests will fail. But that's okay; the task is to create the test file.

Let's proceed.

We'll write:

```python
# Arquivo: backend/tests/test_farmacia_dispensacao.py
"""
Testes de integridade da dispensação e validação hash (C18).

Cobre:
- Rejeição de receitas com hash adulterado.
- Prevenção de dispensação duplicada da mesma receita.
- Registro de saldo remanescente em baixa parcial.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.database import Base
from app.models.farmacia import Prescription, Dispensation
from app.services.farmacia import (
    compute_prescription_hash,
    validate_prescription_hash,
    dispense_prescription,
)
from app.core.exceptions import (
    HashMismatchError,
    DuplicateDispensationError,
    InsufficientBalanceError,
)
```

But we need to ensure that the imports are correct. We'll assume these modules exist.

Now, fixtures:

```python
@pytest.fixture
def db_session():
    """Cria uma sessão de banco de dados em memória para os testes."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Testing