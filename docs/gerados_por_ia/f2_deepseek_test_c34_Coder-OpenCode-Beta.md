We need to create a test file for the "MedIA" project, specifically backend/tests/test_farmacia_dispensacao.py. The task: validate that 1) prescriptions with altered hash are rejected; 2) duplicate dispensing of same prescription is prevented; 3) partial dispensing records remaining balance.

We need to write pytest tests for these scenarios. We should assume there are models/services for prescriptions, dispensing, etc. We'll need to mock or use a test database. We'll need to follow architecture: Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS patterns.

We need to provide the full code for the test file. Since we don't have actual implementation, we'll create tests that assume certain interfaces/functions exist. We'll design tests that check these behaviors.

Let's outline:

- The tests will use fixtures to set up a test database (maybe in-memory SQLite) and create a prescription record with a hash.
- Test 1: altered hash -> rejection when attempting to dispense. Likely the service that validates hash before dispensing will raise an error or return a failure.
- Test 2: duplicate dispensing -> second attempt to dispense same prescription is prevented.
- Test 3: partial dispensing -> record remaining quantity.

We'll need to define mock models or use the actual models if we know them, but given the abstract task, we'll write tests that target a service class (e.g., DispensacaoService) with methods like dispensar(prescricao_id, quantidade, hash_recebido?). We'll also need to set up models: Prescricao, Dispensacao, etc.

Since it's a test file, we can import from app models and services. But we need to ensure the code is runnable. To be safe, we'll write tests that define the necessary fixtures and use mocks where appropriate. We'll assume there's a module structure.

We'll also need to use pytest and maybe pytest-asyncio if async. But we'll keep it sync to simplify.

Let's define:

- Use SQLAlchemy in-memory SQLite for testing.
- Create tables from models.
- Create a Prescricao object with a hash (e.g., SHA256 of some contents).
- For altered hash: we tamper with the hash stored in DB or the hash provided at time of dispensing.

We need to understand the semantics: "receitas com hash adulterado são rejeitadas" - meaning prescriptions with altered hash are rejected. So likely the system stores a hash of the prescription data to ensure integrity. At dispensing, the system might recompute hash from the prescription data and compare, or it might store a hash that is verified. So the test: we create a prescription, then modify some field (like medication dosage) and try to dispense, expecting rejection. Alternatively, the hash itself is stored and at dispensing we provide the hash, but if it's different from stored, rejection.

We'll define a service that takes prescription_id and quantity and optionally a hash? To test hash validation, we could test that a function verifies the hash of a prescription before allowing dispensing.

I'll design tests as per common patterns:

- We have a Prescricao model with fields: id, cns, cpf, data_prescricao, medicamento, dosagem, quantidade_total, hash_integridade, data_criacao, etc.
- We have a Dispensacao model with id, prescricao_id, quantidade, saldo_remanescente, data_dispensacao, etc.
- The service function `realizar_dispensacao(prescricao_id, quantidade_dispensada, hash_recebido)` will:
  - Load the prescription by id.
  - Verify that hash_recebido matches the prescription's hash_integridade (or recompute hash from prescription fields). If not, raise `HashInvalidoError`.
  - Check if the prescription has already been fully dispensed (e.g., total dispensed >= quantidade_total) or if it is locked, and reject duplicate dispensing.
  - If partial dispensing, create a Dispensacao record, update the remaining quantity.

For duplicate prevention: If a prescription is marked as "dispensed" (fully or partially) and the system prevents multiple dispensations for the same prescription (i.e., only one dispensing event allowed per prescription). But partial dispensing means you can have multiple events? The task says "dispensação duplicada de mesma receita é impedida" - duplicate dispensing (i.e., the same prescription cannot be dispensed more than once, perhaps meaning cannot exceed total quantity or cannot have duplicate dispensation of same quantity). We need to interpret: if a prescription has total quantity 10, and you dispense 6, then later you want to dispense 6 again, that should be prevented because total would exceed available. Or if you try to dispense after full dispensation, prevented. Alternatively, the system may only allow one dispensing event per prescription (like a single dispensing transaction). The third test says "baixa parcial registra saldo remanescente" - partial dispensing records remaining balance, so clearly multiple dispensing events allowed (partial quantities). Thus "dispensação duplicada" probably means attempting to dispense the same prescription again after it has already been fully dispensed (i.e., remaining balance zero), or attempting to dispense more than the remaining quantity, or attempting to dispense a duplicate event that would exceed total.

Better: The test likely wants to verify that the system checks if the prescription has been fully dispensed or if there is remaining quantity. So a duplicate dispensing (i.e., trying to dispense when no remaining quantity) is prevented.

We'll implement tests accordingly.

Now the instruction is to create the test file. We'll need to provide full code. We'll write it with fixtures to set up a test database and create a prescription. We'll mock the service or use a real one if we assume the project structure.

Given we don't have the actual implementation, we'll write tests that will initially fail but are correct for the specification. We'll include comments explaining.

We'll also ensure we use Pydantic v2 models for schemas, SQLAlchemy for ORM.

We'll use `pytest` and `pytest-asyncio` if we choose async, but let's keep sync to simplify.

We'll also need to handle database rollback after each test to avoid interference.

I'll produce a test file with:

- Imports: pytest, sqlalchemy, datetime, decimal, uuid, etc.
- Fixtures: in-memory SQLite engine, session, setup/teardown, create_test_prescription.
- Tests:
  - test_hash_adulterado_rejeitado
  - test_dispensacao_duplicada_impedida
  - test_baixa_parcial_registra_saldo_remanescente

We'll define custom exceptions.

To make the code runnable without actual implementation, we'll need to import from the app modules. But since they don't exist yet, we could create dummy classes? No, the instruction is to create the test file, presumably for an existing project. So we should write tests that target expected endpoints/services.

We'll assume the project has the following structure:

- backend/app/models/prescricao.py: Prescricao model
- backend/app/models/dispensacao.py: Dispensacao model
- backend/app/services/farmacia.py: service functions
- backend/app/schemas/farmacia.py: Pydantic schemas
- backend/app/core/security.py: hash functions

We'll write tests that import from these.

To make it easy, we'll create fixtures that create a test database and a Prescricao record. Then call the service.

We'll also need to ensure we handle `HashInvalidoError` and `DispensacaoDuplicadaError`.

Let's draft the code.

Also the task says "Execute com precisão conforme as diretrizes." So we need to produce the code block with the file path.

Now, let's write the test file content.```python
# Arquivo: backend/tests/test_farmacia_dispensacao.py
"""
Testes de integridade da dispensação e validação hash (C34).

Cobertura:
1) Receitas com hash adulterado são rejeitadas;
2) Dispensação duplicada de mesma receita é impedida;
3) Baixa parcial registra saldo remanescente.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Importações da aplicação (ajuste conforme estrutura real do projeto)
from app.models.prescricao import Prescricao
from app.models.dispensacao import Dispensacao
from app.services.farmacia import (
    realizar_dispensacao,
    HashInvalidoError,
    DispensacaoDuplicadaError,
)
from app.schemas.farmacia import DispensacaoCreate


# =========================================================
# Fixtures de banco de dados em memória (SQLite)
# =========================================================
@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Cria as tabelas a partir dos modelos
    from app.core.database import Base
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def prescricao_valida(db_session: Session) -> Prescricao:
    """Cria uma prescrição válida com hash integro."""
    prescricao = Prescricao(
        id=uuid4(),
        cns="123456789012345",
        cpf="12345678901",
        data_prescricao=datetime.now().date(),
        medicamento="Amoxicilina",
        dosagem="500mg",
        quantidade_total=Decimal("10"),
        hash_integridade="hash_integridade_original",  # simulado
    )
    db_session.add(prescricao)
    db_session.commit()
    db_session.refresh(prescricao)
    return prescricao


# =========================================================
# Testes
# =========================================================

def test_hash_adulterado_rejeitado(db_session: Session, prescricao_valida: Prescricao):
    """
    C34-1: Receita com hash adulterado deve ser rejeitada.
    Simula envio de hash diferente do armazenado.
    """
    # Hash recebido (do aplicativo/mobile) alterado
    hash_recebido = "hash_adulterado_xyz"

    with pytest.raises(HashInvalidoError):
        realizar_dispensacao(
            db=db_session,
            prescricao_id=str(prescricao_valida.id),
            quantidade=Decimal("2"),
            hash_recebido=hash_recebido,
        )


def test_dispensacao_duplicada_impedida(db_session: Session, prescricao_valida: Prescricao):
    """
    C34-2: Não é possível dispensar duas vezes a mesma receita quando o
    saldo remanescente é zero (dispensação completa já realizada).
    """
    # Primeira dispensação: quantidade total
    quantidade_total = prescricao_valida.quantidade_total
    realizar_dispensacao(
        db=db_session,
        prescricao_id=str(prescricao_valida.id),
        quantidade=quantidade_total,
        hash_recebido="hash_integridade_original",
    )

    # Tentativa de segunda dispensação (mesma receita, mesmo hash)
    with pytest.raises(DispensacaoDuplicadaError):
        realizar_dispensacao(
            db=db_session,
            prescricao_id=str(prescricao_valida.id),
            quantidade=Decimal("1"),  # qualquer quantidade
            hash_recebido="hash_integridade_original",
        )


def test_baixa_parcial_registra_saldo_remanescente(db_session: Session, prescricao_valida: Prescricao):
    """
    C34-3: Dispensação parcial deve registrar saldo remanescente
    e permitir novas dispensações até o esgotamento.
    """
    # Dispensar 6 de 10 unidades
    primeira_dose = Decimal("6")
    realizar_dispensacao(
        db=db_session,
        prescricao_id=str(prescricao_valida.id),
        quantidade=primeira_dose,
        hash_recebido="hash_integridade_original",
    )

    # Verifica saldo remanescente registrado
    dispensacao = db_session.query(Dispensacao).filter_by(prescricao_id=prescricao_valida.id).one()
    saldo_esperado = prescricao_valida.quantidade_total - primeira_dose
    assert dispensacao.saldo_remanescente == saldo_esperado
    assert dispensacao.quantidade_dispensada == primeira_dose

    # Nova dispensação parcial até esgotar
    segunda_dose = Decimal("4")
    realizar_dispensacao(
        db=db_session,
        prescricao_id=str(prescricao_valida.id),
        quantidade=segunda_dose,
        hash_recebido="hash_integridade_original",
    )

    # Após esgotar, o saldo deve ser zero
    ultima_dispensacao = (
        db_session.query(Dispensacao)
        .filter_by(prescricao_id=prescricao_valida.id)
        .order_by(Dispensacao.data_dispensacao.desc())
        .first()
    )
    assert ultima_dispensacao.saldo_remanescente == Decimal("0")
```