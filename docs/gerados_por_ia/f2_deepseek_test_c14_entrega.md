We need to create a test file for the MedIA project. The task is to create backend/tests/test_farmacia_dispensacao.py validating three things: 1) prescriptions with adulterated hash are rejected; 2) duplicate dispensing of same prescription is prevented; 3) partial dispensing records remaining balance.

We need to follow architecture guidelines: Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0, SUS/APS patterns (CIAP-2, CID-10, SOAP, CNS/CPF). We need to provide complete executable code. We need to infer the context: likely there is a backend with models for prescriptions, dispensing, etc. We need to write tests that assume certain models/services exist. Since we are only asked to create the test file, we need to write tests that will pass given the implementation. But we don't have the implementation. We need to design tests that are plausible and follow the guidelines. We can create fixtures and mock dependencies. However, the instruction says "Crie backend/tests/test_farmacia_dispensacao.py validando que..." So we need to create the test file. We can assume that the project has certain modules: maybe backend/app/models, backend/app/services, etc. We need to write tests that import from those modules. Since we don't know the exact structure, we can define the tests in a way that they will work if the implementation follows the described patterns. We can also include comments explaining assumptions.

We need to provide the full code for the test file. We'll write a pytest test file with fixtures for database session, models, etc. We'll use SQLAlchemy in-memory SQLite for tests. We'll define minimal models if needed? But the task is to test existing functionality. We can create tests that use the actual models from the app. To make it executable, we need to ensure imports are correct. Since we don't have the actual code, we can either:

1. Write tests that import from the app and assume the app is structured in a certain way. We'll include comments that these are placeholders and need to be adjusted to actual project structure.

2. Alternatively, we can create a self-contained test file that defines minimal models and services to demonstrate the tests. But the task says "Para o Projeto MedIA, cree backend/tests/test_farmacia_dispensacao.py" - it's for the project, so we should write tests that would be used in that project. We need to make reasonable assumptions.

Given the instructions, we should produce a test file that is as complete as possible, with clear structure. We'll use pytest fixtures, SQLAlchemy in-memory database, and test the three scenarios. We'll also include type hints and Pydantic v2 usage.

Let's outline:

- Imports: pytest, sqlalchemy, pydantic, datetime, decimal, etc.
- Fixtures: db_session (in-memory SQLite), maybe create tables.
- We need to define models? Actually, if the app has models, we can import them. But to make the test file executable, we might need to define them. However, the instruction says "Código em Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0." So we should use those.

We can write tests that use the service layer functions (e.g., dispense_medication, validate_prescription_hash). We'll assume there are functions like `validate_prescription_hash(prescription_id, hash_value)` and `dispense_prescription(...)`.

Alternatively, we can test at the API level using FastAPI TestClient. But the task says "test_farmacia_dispensacao.py" - likely unit/integration tests.

Let's design a test file that:

- Uses a fixture to create an in-memory SQLite database and a session.
- Uses a fixture to create a sample prescription with a known hash.
- Test 1: "test_receipt_with_adulterated_hash_rejected" - create a prescription, then try to validate with wrong hash, expect rejection (e.g., raises ValueError or returns False).
- Test 2: "test_duplicate_dispensation_prevented" - dispense a prescription once, then try again, expect error.
- Test 3: "test_partial_dispensation_records_remaining_balance" - dispense partial quantity, check remaining balance.

We need to define the models: Prescription, Dispensation. We'll keep it simple.

We'll also include Pydantic schemas for request/response.

We'll write the test file with clear comments.

Let's proceed.

We'll create a file `backend/tests/test_farmacia_dispensacao.py`. We'll include:

- Imports: from datetime import datetime, date; from decimal import Decimal; import pytest; from sqlalchemy import create_engine, Column, Integer, String, Date, Numeric, ForeignKey, DateTime, Boolean; from sqlalchemy.orm import declarative_base, sessionmaker, relationship; from pydantic import BaseModel, Field, ValidationError; etc.

But if we define models in the test file, it's not testing the actual app. However, we can argue that the test file is self-contained for demonstration. But the instruction says "Para o Projeto MedIA" - it should be part of the project. We can write tests that import from the app's models and services. To make it executable, we need to either include the app code or assume it exists. Since we are only asked to create the test file, we can write it with imports from the app, and note that the app must have those modules. But the user expects a complete code block. We can provide a test file that is ready to run if the app is structured as expected.

Given the constraints, I'll write a test file that imports from `backend.app.models` and `backend.app.services` (or similar). I'll include comments that these imports need to be adjusted to actual project structure. But to make it "executable" in the sense of being syntactically correct, we can also include fallback definitions if imports fail? That's messy.

Better: We'll write the test file using the actual project structure as we infer. We'll assume the project has:

- backend/app/models.py with Base, Prescription, Dispensation
- backend/app/schemas.py with Pydantic models
- backend/app/services/farmacia.py with functions

We'll write tests that import from these. We'll also include a conftest.py? But the task only asks for the test file. We can include fixtures within the test file.

We'll also use `pytest` fixtures with `tmp_path` for SQLite file? Or in-memory.

Let's craft the test file.

We need to ensure strict typing: use type hints, `Optional`, `List`, etc.

We'll use SQLAlchemy 2.0 style: `Mapped`, `mapped_column`, `DeclarativeBase`.

Let's write:

```python
# backend/tests/test_farmacia_dispensacao.py
"""
Testes de integridade da dispensação e validação hash (C14).

Cubre:
1. Rechazo de receitas con hash adulterado.
2. Prevenção de dispensação duplicada.
3. Registro de saldo remanente em baixa parcial.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Generator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Importações do projeto (ajustar caminhos conforme estrutura real)
from app.models import Base, Prescription, Dispensation  # type: ignore
from app.schemas import PrescriptionCreate, DispensationCreate  # type: ignore
from app.services.farmacia import (
    validate_prescription_hash,
    dispense_prescription,
    get_remaining_balance,
)
```

But we need to define the models and services? Since we don't have them, we can either mock them or define them in the test file. The instruction says "Cree backend/tests/test_farmacia_dispensacao.py" - it's just the test file. We can include the models and services as part of the test file for completeness? That would be unusual. But we can create a "test" that uses the actual app code. To make it executable, we need to ensure the app code exists. Since we are the AI, we can assume the app code is as we define. But the user might expect the test file only. We can provide the test file with imports that reference the app, and also provide the app code? The instruction says "Execute com precisão conforme as diretrizes." It doesn't say to create the whole project. It says create the test file. So we should only create the test file. But to make it executable, we need to ensure the imports work. We can include a note that the test file assumes the existence of certain modules. Alternatively, we can write the test file to be self-contained by defining minimal models and services within the test file, but that would not test the actual project. However, the task is to validate the behavior, not necessarily to test the actual implementation. It says "validando que: 1) receitas com hash adulterado são rejeitadas; ..." So we need to write tests that validate these behaviors. If the actual implementation doesn't exist, the tests will fail. But we are to create the test file as part of the project. So we must assume the implementation exists.

Given the ambiguity, I'll write the test file with imports from the app, and include a comment that the test file should be placed in the project and the imports should match the actual structure. I'll also include a `conftest.py`? No, just the test file.

To be safe, I'll write the test file with a fixture that creates an in-memory database and tables using the app's Base. I'll also create sample data using the app's models. I'll use the service functions. If the service functions don't exist, the tests will fail, but that's expected if the implementation is incomplete. The user asked to create the test file, not the implementation.

Let's proceed with that.

We'll need to define the expected behavior:

1. `validate_prescription_hash(prescription_id, hash)` returns True if hash matches, False otherwise. Or raises an exception. We'll test that it returns False or raises.

2. `dispense_prescription(prescription_id, quantity, ...)` creates a Dispensation record. If a previous dispensation exists for the same prescription, it should raise an error (e.g., `DuplicateDispensationError`).

3. `get_remaining_balance(prescription_id)` returns the remaining quantity after partial dispensation.

We'll write tests accordingly.

We'll also use Pydantic v2 for schemas.

Let's write the test file now.

We'll include:

- `pytest.fixture` for `db_session` that creates an in-memory SQLite database, creates tables, yields a session, and tears down.
- `pytest.fixture` for `sample_prescription` that creates a Prescription record with a known hash.
- Test functions.

We'll also need to handle the fact that the service functions might require a session. We'll pass the session.

Let's define the models in the test file? No, we'll import from app.models. But to make the test file self-contained for the purpose of this answer, we can include the model definitions in the test file as a fallback? That would be confusing.

I think the best approach is to write the test file as it would appear in the project, with imports from the app. We'll also include a `conftest.py`? The task only asks for the test file. So we'll just provide the test file.

Let's write it.

We'll use `pytest` and `sqlalchemy`.

We'll also include type hints.

Now, let's produce the final answer with the code block.```python
# backend/tests/test_farmacia_dispensacao.py
"""
Testes de Integridade da Dispensação e Validação Hash (C14)

Cubre:
1. Rechazo de receitas con hash adulterado.
2. Prevenção de dispensação duplicada.
3. Registro de saldo remanente em baixa parcial.

Requisitos de arquitectura:
- Python 3.12, tipagem estricta com Pydantic v2 e SQLAlchemy 2.0.
- Padrões SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF).
- Cobertura de testes automatizados com pytest.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Generator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Importações do projeto (ajustar caminhos conforme estrutura real)
# ---------------------------------------------------------------------------
from app.models import Base, Prescription, Dispensation  # type: ignore
from app.schemas import PrescriptionCreate, DispensationCreate  # type: ignore
from app.services.farmacia import (
    validate_prescription_hash,
    dispense_prescription,
    get_remaining_balance,
)
from app.core.exceptions import DuplicateDispensationError  # type: ignore

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """
    Crea una base de datos SQLite en memoria y una sesión de SQLAlchemy.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, future=True, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def sample_prescription(db_session: Session) -> Prescription:
    """
    Crea una receta médica de ejemplo con hash conocido.
    """
    prescription = Prescription(
        patient_cns="123456789012345",
        patient_cpf="12345678901",
        doctor_cpf="98765432101",
        diagnosis_cid10="J00.0",
        diagnosis_ci ap2="A01",
        soap_subjective="Paciente presenta dolor de garganta",
        soap_objective="Faringe eritematosa",
        soap_assessment="Faringitis aguda",
        soap_plan="Prescribir amoxicilina 500mg cada 8h por 7 días",
        medication_code="AMOX500",
        medication_name="Amoxicilina 500mg",
        quantity=30,
        hash_value="abc123hash",
        created_at=datetime.now(),
    )
    db_session.add(prescription)
    db_session.commit()
    db_session.refresh(prescription)
    return prescription


# ---------------------------------------------------------------------------
# Test 1: Receitas com hash adulterado são rejeitadas
# ---------------------------------------------------------------------------

def test_receipt_with_adulterated_hash_rejected(
    db_session: Session, sample_prescription: Prescription
) -> None:
    """
    Verifica que uma receta com hash adulterado não passa a validação.
    """
    # Hash correto
    assert validate_prescription_hash(sample_prescription.id, "abc123hash") is True

    # Hash adulterado
    assert validate_prescription_hash(sample_prescription.id, "hash_incorrecto") is False

    # Hash vazio / nulo
    assert validate_prescription_hash(sample_prescription.id, "") is False


# ---------------------------------------------------------------------------
# Test 2: Dispensação duplicada da mesma receita é impedida
# ---------------------------------------------------------------------------

def test_duplicate_dispensation_prevented(
    db_session: Session, sample_prescription: Prescription
) -> None:
    """
    Verifica que não é possível dispensar duas vezes a mesma receita.
    """
    # Primera dispensación (completa)
    dispense_prescription(
        db_session,
        prescription_id=sample_prescription.id,
        quantity=30,
        dispensed_at=datetime.now(),
    )

    # Segunda dispensación deve falhar
    with pytest.raises(DuplicateDispensationError):
        dispense_prescription(
            db_session,
            prescription_id=sample_prescription.id,
            quantity=10,
            dispensed_at=datetime.now(),
        )


# ---------------------------------------------------------------------------
# Test 3: Baixa parcial registra saldo remanente
# ---------------------------------------------------------------------------

def test_partial_dispensation_records_remaining_balance(
    db_session: Session, sample_prescription: Prescription
) -> None:
    """
    Verifica que após uma dispensação parcial, o saldo remanente é correto.
    """
    # Dispensação parcial: 10 unidades de 30
    dispense_prescription(
        db_session,
        prescription_id=sample_prescription.id,
        quantity=10,
        dispensed_at=datetime.now(),
    )

    # Saldo remanente deve ser 20
    remaining = get_remaining_balance(db_session, sample_prescription.id)
    assert remaining == Decimal("20")

    # Verificar que a dispensação foi registrada
    dispensations = db_session.scalars(
        select(Dispensation).where(Dispensation.prescription_id == sample_prescription.id)
    ).all()
    assert len(dispensations) == 1
    assert dispensations[0].quantity == 10
```