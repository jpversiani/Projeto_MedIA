We need to create a test file for the MedIA project. The task is to create backend/tests/test_farmacia_dispensacao.py that validates three things:

1. Receitas with tampered hash are rejected.
2. Duplicate dispensing of the same prescription is prevented.
3. Partial dispensing records remaining balance.

We need to write tests that cover these scenarios. We should assume there is an existing backend structure with models and services for farmácia (pharmacy) and dispensação (dispensing). We need to write tests that use pytest, likely with fixtures, mocking, or actual database setup.

We need to understand the domain: "receitas" (prescriptions) have hashes, "dispensação" (dispensing) records, and there is a balance concept. The tests should verify the behavior.

We'll write tests using pytest and likely using SQLAlchemy in-memory SQLite or test database. We'll need to import models and services. Since we don't have the actual code, we'll make reasonable assumptions about the structure.

We'll create a test file that:

- Sets up a test database (maybe using pytest fixtures with SQLAlchemy).
- Creates instances of models (Receita, Dispensacao, etc.) as needed.
- Tests the validation logic.

We'll need to mock or use actual functions that perform the validation. Since we don't have the actual implementation, we'll write tests that assume certain functions exist, like `validate_receita_hash`, `dispensar_medicamento`, etc. We'll write tests that would pass if the implementation is correct.

We'll also need to consider that the tests should be self-contained and runnable. We'll use pytest fixtures to set up the database and session.

Let's outline the test file:

- Imports: pytest, sqlalchemy, models, services, etc.
- Fixtures: `db_session` (in-memory SQLite), `receita` (a valid prescription), `dispensacao_service` (instance of service).
- Test functions:
  - `test_receita_hash_adulterado_rejeitado`: create a receita with a valid hash, then tamper with it (e.g., change a field) and attempt to validate; expect rejection.
  - `test_dispensacao_duplicada_impedida`: create a receita, dispense it once, then attempt to dispense again; expect error.
  - `test_baixa_parcial_registra_saldo_remanescente`: create a receita with quantity, dispense partial quantity, check that remaining balance is recorded.

We'll need to define the models and services. Since we don't have them, we'll write tests that assume the existence of certain classes and methods. We'll also need to define the schema for the models. We'll make reasonable assumptions:

- `Receita` model: has fields like `id`, `hash`, `medicamento`, `quantidade_prescrita`, `cns_paciente`, etc.
- `Dispensacao` model: has fields like `id`, `receita_id`, `quantidade_dispensada`, `data`, `saldo_remanescente`, etc.
- Service functions: `validar_receita(receita)`, `dispensar(receita_id, quantidade)`.

We'll write tests that use these.

We'll also need to set up the database schema. We'll use SQLAlchemy's `create_all` on the test engine.

Let's write the test file. We'll include comments and docstrings.

We'll also need to handle the hash validation: likely the hash is computed from the receita's fields. So we'll create a function to compute hash, and then tamper with a field and recompute? Actually, the test should check that if the hash doesn't match the content, it's rejected. So we'll create a receita with a hash, then modify a field (e.g., change the medication name) without updating the hash, and then call validation; it should fail.

For duplicate dispensing: we'll dispense once, then try again; the service should raise an error.

For partial dispensing: we'll dispense a quantity less than the prescribed, and check that the remaining balance is stored.

We'll need to ensure the database is clean between tests.

Let's write the code.

We'll assume the models are in `backend/app/models` and services in `backend/app/services`. We'll import them.

We'll also need to set up a test configuration.

We'll use pytest fixtures with `scope="function"` to create a new session per test.

We'll use SQLAlchemy's `create_engine("sqlite://")` for in-memory.

We'll also need to define the models if they don't exist? Actually, we are writing tests, so we assume they exist. We'll import them.

We'll write the tests with proper assertions.

Let's produce the final answer.```python:backend/tests/test_farmacia_dispensacao.py
"""
Testes de integridade da dispensação e validação hash (C26).

Cobertura:
1. Receitas com hash adulterado são rejeitadas.
2. Dispensação duplicada de mesma receita é impedida.
3. Baixa parcial registra saldo remanescente.

Execução:
    pytest backend/tests/test_farmacia_dispensacao.py -v
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importações do projeto (ajuste os caminhos conforme a estrutura real)
from backend.app.models import Base, Receita, Dispensacao
from backend.app.services.farmacia import (
    validar_receita,
    dispensar_medicamento,
    obter_saldo_remanescente,
)
from backend.app.core.security import gerar_hash_receita


@pytest.fixture(scope="function")
def db_session():
    """Cria um banco de dados SQLite em memória e fornece uma sessão limpa."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def receita_valida(db_session):
    """Cria uma receita válida com hash correto."""
    receita = Receita(
        cns_paciente="123456789012345",
        cpf_paciente="12345678901",
        medicamento="Amoxicilina 500mg",
        quantidade_prescrita=10,
        posologia="1 comprimido de 8 em 8 horas por 7 dias",
        data_prescricao="2025-03-01",
    )
    # Gera o hash a partir dos dados da receita
    receita.hash = gerar_hash_receita(receita)
    db_session.add(receita)
    db_session.commit()
    db_session.refresh(receita)
    return receita


def test_receita_hash_adulterado_rejeitado(db_session, receita_valida):
    """
    Verifica que uma receita com hash adulterado é rejeitada.
    """
    # Adultera um campo da receita sem atualizar o hash
    receita_valida.medicamento = "Amoxicilina 1g"
    db_session.commit()

    # A validação deve falhar
    with pytest.raises(ValueError, match="Hash da receita inválido"):
        validar_receita(receita_valida)


def test_dispensacao_duplicada_impedida(db_session, receita_valida):
    """
    Verifica que uma segunda dispensação da mesma receita é impedida.
    """
    # Primeira dispensação (quantidade total)
    dispensar_medicamento(
        db_session,
        receita_id=receita_valida.id,
        quantidade=receita_valida.quantidade_prescrita,
    )

    # Segunda tentativa deve falhar
    with pytest.raises(ValueError, match="Receita já dispensada"):
        dispensar_medicamento(
            db_session,
            receita_id=receita_valida.id,
            quantidade=1,
        )


def test_baixa_parcial_registra_saldo_remanescente(db_session, receita_valida):
    """
    Verifica que uma dispensação parcial registra o saldo remanescente.
    """
    quantidade_parcial = 4
    dispensar_medicamento(
        db_session,
        receita_id=receita_valida.id,
        quantidade=quantidade_parcial,
    )

    # O saldo remanescente deve ser a diferença
    saldo = obter_saldo_remanescente(db_session, receita_valida.id)
    assert saldo == receita_valida.quantidade_prescrita - quantidade_parcial

    # A dispensação deve ter sido registrada com o saldo correto
    dispensacao = (
        db_session.query(Dispensacao)
        .filter(Dispensacao.receita_id == receita_valida.id)
        .one()
    )
    assert dispensacao.quantidade_dispensada == quantidade_parcial
    assert dispensacao.saldo_remanescente == saldo
```