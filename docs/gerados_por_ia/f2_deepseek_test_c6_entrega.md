We need to create a test file for the MedIA project. The task is to create backend/tests/test_farmacia_dispensacao.py with tests for:

1) Receipts with adulterated hash are rejected.
2) Duplicate dispensing of same receipt is prevented.
3) Partial dispensing records remaining balance.

We need to follow architecture guidelines: Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0, SUS/APS patterns (CIAP-2, CID-10, SOAP, CNS/CPF), full compliance and automated test coverage with pytest.

We need to produce complete executable code. We'll need to infer the structure of the project. Since we don't have the actual codebase, we need to create a test file that likely tests existing models/services. We should assume there are models like Receipt, Dispensation, etc. We'll write tests using pytest, likely with a test database (SQLite in-memory or similar). We'll need to mock or use fixtures.

We should define the test file with appropriate imports. Since we don't know exact module paths, we'll assume a typical structure: backend/app/models, backend/app/services, etc. We'll write tests that import from these.

We need to ensure the tests are meaningful and cover the requirements. We'll create fixtures for database session, sample data, etc.

Let's design the test file:

- Use pytest fixtures to set up a test database (SQLAlchemy in-memory SQLite).
- Create tables.
- Create sample receipt with hash.
- Test 1: Create a receipt with a valid hash, then try to validate with altered hash, expect rejection. Or test a service function that verifies hash.
- Test 2: Attempt to dispense same receipt twice, expect second attempt to raise an error.
- Test 3: Dispense partial quantity, then check remaining balance.

We need to define what "receipt" and "dispensation" mean. In a pharmacy context, a prescription (receita) has items with quantities. Dispensation is the act of giving medication. We'll model a simple scenario.

We'll need to create models or use existing ones. Since we don't have them, we'll write tests that assume certain models and services exist. We'll need to make reasonable assumptions.

Let's outline:

- Model: Receipt (id, hash, patient_cns, doctor_cpf, items relationship, etc.)
- Model: ReceiptItem (id, receipt_id, medication_code, quantity_prescribed, quantity_dispensed, etc.)
- Model: Dispensation (id, receipt_id, timestamp, quantity, etc.)

But the task says "dispensação duplicada de mesma receita é impedida" - duplicate dispensing of same receipt is prevented. That could mean that a receipt can only be dispensed once (full dispensing) or that you cannot dispense more than prescribed. We'll interpret as: a receipt cannot be fully dispensed more than once, or a dispensation cannot be created if the receipt has already been fully dispensed.

"baixa parcial registra saldo remanescente" - partial dispensing records remaining balance. So a receipt can be partially dispensed, and the remaining quantity is tracked.

We'll create tests that use a service function like `dispense_medication(receipt_id, quantity)`.

We'll need to define a hash validation function. Maybe the receipt has a hash that is computed from its contents, and we need to verify integrity.

Let's write the test file with clear structure.

We'll include type hints, use Pydantic for schemas if needed, but tests can use SQLAlchemy models directly.

We'll need to ensure the tests are executable. Since we don't have the actual project, we'll create a self-contained test file that defines minimal models and services within the test file? But the instruction says "create backend/tests/test_farmacia_dispensacao.py" - it's a test file, not the implementation. So we should write tests that import from the actual app. However, without the app, the tests won't run. But the task is to create the test file as part of the project. We'll assume the project structure exists and we are writing tests for it. We'll use imports like `from app.models import Receipt, Dispensation` etc.

We'll also need to handle the hash validation. We'll assume there's a function `validate_receipt_hash(receipt, hash)` or `verify_receipt_integrity(receipt)`.

Let's write the test file with comments explaining assumptions.

We'll use pytest fixtures:

- `db_session` fixture: creates in-memory SQLite database, creates tables, yields session.
- `sample_receipt` fixture: creates a receipt with items and a valid hash.

We'll need to compute hash. We'll use a simple hash function like SHA256 of the receipt data.

But to test "adulterated hash", we can create a receipt with a valid hash, then modify the hash in the database or in the object, and call the validation function, expecting it to fail.

Alternatively, we can test that when creating a receipt, the hash is computed and stored; if someone changes the data, the hash no longer matches.

Let's design:

- Model Receipt has a `hash` column.
- There's a function `compute_receipt_hash(receipt)` that computes hash from the receipt's contents (e.g., patient CNS, items, quantities).
- There's a function `verify_receipt_hash(receipt)` that checks if receipt.hash equals computed hash.

Test 1: Create a receipt, compute hash, set it, then modify a field (e.g., quantity), call verify, expect False. Or call a service that rejects if hash invalid.

We'll write tests that call service functions.

Let's define service functions:

- `dispense_medication(session, receipt_id, quantity)` - creates a Dispensation record, updates remaining balance, raises error if duplicate full dispensing or if quantity exceeds remaining.

We'll need to model remaining balance. We can have a `remaining_quantity` field on ReceiptItem, or compute from dispensation records.

Simpler: Each ReceiptItem has `quantity_prescribed`. Dispensations have `quantity_dispensed`. Remaining = prescribed - sum(dispensed). We'll enforce that total dispensed cannot exceed prescribed.

Duplicate dispensing of same receipt: If a receipt is fully dispensed (all items remaining = 0), then any further dispensation is prevented. Or if there's a rule that a receipt can only be dispensed once (i.e., one dispensation per receipt). The phrase "dispensação duplicada de mesma receita é impedida" suggests that you cannot dispense the same receipt twice. But partial dispensing implies multiple dispensations might be allowed. So "duplicate" likely means you cannot dispense more than the prescribed quantity, or you cannot create a dispensation if the receipt is already fully dispensed. We'll implement that.

Test 2: Create a receipt with one item quantity 10. Dispense 10. Then attempt to dispense again (even 1), expect error.

Test 3: Create a receipt with quantity 10. Dispense 4. Check that remaining balance is 6. Then dispense 6, check remaining 0.

We'll also test hash rejection.

Now, let's write the code.

We'll need to include necessary imports. We'll assume SQLAlchemy 2.0 style with Mapped and mapped_column.

We'll define models in a conftest? But the test file should be self-contained? Usually tests import from app. We'll write the test file with imports from app.models and app.services. We'll also include a conftest.py? The task only asks for the test file. We'll include fixtures in the test file itself.

To make it executable, we'll need to define the models and services within the test file? That would be unusual. But since we don't have the actual app, we can create a test file that defines minimal models and services to demonstrate the tests. However, the instruction says "Código em Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0." So the test file should also follow these. We'll use SQLAlchemy 2.0 and Pydantic for schemas if needed.

I think the best approach is to write a test file that assumes the existence of the app modules, and we'll provide the necessary imports. We'll also include a comment that the tests are designed for the MedIA project.

Let's craft the test file.

We'll need to handle the hash. We'll use hashlib.

Let's define a simple model:

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Integer
```

We'll define Base.

But if we import from app, we don't need to define. However, to make the test file runnable in isolation, we could define the models in a conftest or in the test file. But the task is to create a test file, not the implementation. The test file should test the implementation. So we should write tests that import from the app. We'll assume the app has these models and services.

Let's write the test file with imports like:

```python
from app.models import Receipt, ReceiptItem, Dispensation
from app.services.farmacia import dispense_medication, verify_receipt_hash
```

We'll also need a database fixture. We'll use `pytest` and `sqlalchemy`.

We'll create a fixture that creates an in-memory SQLite database, creates tables, and provides a session.

We'll need to ensure the models are imported so that metadata is populated.

Let's write:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Receipt, ReceiptItem, Dispensation
from app.services.farmacia import dispense_medication, verify_receipt_hash, compute_receipt_hash
```

But we don't know if these exist. We'll write the test file as if they do.

We'll also need to create sample data.

Let's define a fixture `db_session`:

```python
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
```

Then a fixture `sample_receipt` that creates a receipt with items and a valid hash.

We'll need to compute hash. We'll define a helper function in the test file to compute hash based on the receipt data. But the service should have its own. We'll call `compute_receipt_hash` from the service.

Let's assume `compute_receipt_hash` takes a receipt object and returns a string.

We'll create a receipt:

```python
receipt = Receipt(
    patient_cns="1234567890123",
    doctor_cpf="12345678901",
    items=[
        ReceiptItem(medication_code="ABC", quantity_prescribed=10),
    ]
)
receipt.hash = compute_receipt_hash(receipt)
session.add(receipt)
session.commit()
```

Then test 1:

```python
def test_receipt_with_adulterated_hash_is_rejected(db_session, sample_receipt):
    # Tamper with the receipt data
    sample_receipt.items[0].quantity_prescribed = 20
    db_session.commit()
    # The hash should no longer match
    assert verify_receipt_hash(sample_receipt) is False
```

But we need to ensure that the service rejects it. Maybe there's a function `validate_receipt_integrity` that raises an exception. We'll test that.

Alternatively, we can test that when trying to dispense with an invalid hash, it raises an error.

Let's design:

- `verify_receipt_hash(receipt)` returns bool.
- `dispense_medication(session, receipt_id, quantity)` first checks hash, raises `InvalidReceiptHashError` if invalid.

Then test 1: create receipt, tamper, call dispense, expect exception.

But the requirement says "receitas com hash adulterado são rejeitadas" - receipts with adulterated hash are rejected. So we should test that the system rejects them.

We'll write:

```python
def test_receipt_with_adulterated_hash_is_rejected(db_session, sample_receipt):
    sample_receipt.items[0].quantity_prescribed = 20
    db_session.commit()
    with pytest.raises(InvalidReceiptHashError):
        dispense_medication(db_session, sample_receipt.id, 1)
```

We'll need to define the exception class. We'll import it.

Test 2:

```python
def test_duplicate_dispensation_of_same_receipt_is_prevented(db_session, sample_receipt):
    # First dispense full quantity
    dispense_medication(db_session, sample_receipt.id, 10)
    # Second attempt should raise
    with pytest.raises(DuplicateDispensationError):
        dispense_medication(db_session, sample_receipt.id, 1)
```

Test 3:

```python
def test_partial_dispensation_records_remaining_balance(db_session, sample_receipt):
    dispense_medication(db_session, sample_receipt.id, 4)
    # Check remaining balance
    receipt = db_session.get(Receipt, sample_receipt.id)
    assert receipt.items[0].remaining_quantity == 6
    # Dispense the rest
    dispense_medication(db_session, sample_receipt.id, 6)
    assert receipt.items[0].remaining_quantity == 0
```

We need to ensure `remaining_quantity` is a property or column. We'll assume it's a column updated by the service.

Now, we need to write the test file with proper imports and fixtures. Since we don't have the actual app, we'll include comments that the imports are from the MedIA project.

We'll also include type hints.

Let's write the complete test file.

We'll need to handle the case where the sample_receipt fixture creates the receipt and commits. We'll also need to ensure the hash is computed.

We'll define the fixture:

```python
@pytest.fixture
def sample_receipt(db_session):
    receipt = Receipt(
        patient_cns="1234567890123",
        doctor_cpf="12345678901",
        items=[
            ReceiptItem(medication_code="ABC", quantity_prescribed=10),
        ]
    )
    receipt.hash = compute_receipt_hash(receipt)
    db_session.add(receipt)
    db_session.commit()
    db_session.refresh(receipt)
    return receipt
```

Now, we need to import `compute_receipt_hash` from the service.

We'll also need to define the exception classes. We'll import them.

Let's write the file.

We should also include a conftest? The task only asks for the test file. We'll put everything in the test file.

We'll also need to ensure the test database is set up. We'll use SQLite in-memory.

Now, let's produce the final answer with the code block.

We'll include a header comment with the file path.

We'll write the code with proper Python 3.12 syntax, type hints.

Let's craft it.```python
# Arquivo: backend/tests/test_farmacia_dispensacao.py
"""
Testes de Integridade da Dispensação e Validação Hash (C6)

Cobertura:
1. Receitas com hash adulterado são rejeitadas.
2. Dispensação duplicada de mesma receita é impedida.
3. Baixa parcial registra saldo remanescente.

Conformidade:
- Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0.
- Padrões SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF).
- pytest para automação de testes.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Importações do domínio MedIA (assumindo estrutura padrão do projeto)
from app.models import Base, Receipt, ReceiptItem  # type: ignore
from app.services.farmacia import (  # type: ignore
    DuplicateDispensationError,
    InvalidReceiptHashError,
    compute_receipt_hash,
    dispense_medication,
    verify_receipt_hash,
)


@pytest.fixture
def db_session() -> Session:
    """Cria uma sessão de banco de dados SQLite em memória para testes."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    session = testing_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_receipt(db_session: Session) -> Receipt:
    """Cria uma receita válida com hash íntegro e um item de 10 unidades."""
    receipt = Receipt(
        patient_cns="1234567890123",  # CNS válido (formato 15 dígitos)
        doctor_cpf="12345678901",     # CPF válido (formato 11 dígitos)
        items=[
            ReceiptItem(
                medication_code="ABC",
                quantity_prescribed=10,
            )
        ],
    )
    receipt.hash = compute_receipt_hash(receipt)
    db_session.add(receipt)
    db_session.commit()
    db_session.refresh(receipt)
    return receipt


def test_receipt_with_adulterated_hash_is_rejected(
    db_session: Session, sample_receipt: Receipt
) -> None:
    """
    Verifica que uma receita cujo hash foi adulterado (dados modificados)
    é rejeitada pelo serviço de dispensação.
    """
    # Adulterar a receita: alterar a quantidade prescrita
    sample_receipt.items[0].quantity_prescribed = 20
    db_session.commit()

    # O hash não deve corresponder aos dados atuais
    assert verify_receipt_hash(sample_receipt) is False

    # A dispensação deve ser bloqueada com exceção específica
    with pytest.raises(InvalidReceiptHashError):
        dispense_medication(db_session, sample_receipt.id, 1)


def test_duplicate_dispensation_of_same_receipt_is_prevented(
    db_session: Session, sample_receipt: Rece