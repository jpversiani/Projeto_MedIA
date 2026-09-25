We need to create a test file for the MedIA project, specifically backend/tests/test_farmacia_dispensacao.py. The task is to validate three things: 1) prescriptions with tampered hash are rejected; 2) duplicate dispensing of same prescription is prevented; 3) partial dispensing records remaining balance.

We need to understand the context: MedIA is a project likely with backend using FastAPI, SQLAlchemy 2.0, Pydantic v2. The test file should be in backend/tests. We need to write tests that verify these behaviors. We need to assume the existence of models, services, etc. Since we are only asked to create the test file, we need to write tests that are plausible and can be run if the application is set up. We should include fixtures, mocks, or use a test database.

We need to ensure the tests are comprehensive and follow the architecture guidelines: Python 3.12, strict typing, Pydantic v2, SQLAlchemy 2.0, SUS/APS patterns, CIAP-2, CID-10, SOAP, CNS/CPF identification.

We'll write tests using pytest, likely with a test database (SQLite in-memory or postgres). We'll need to import models and services. Since we don't have the actual code, we'll have to make reasonable assumptions about the structure. We'll create tests that mock the necessary components or use a real test DB with schema creation.

We should write the test file with clear docstrings and comments. We'll use pytest fixtures for session, client, etc.

We need to cover:

1) Test that a prescription with tampered hash is rejected. This implies there is a hash validation mechanism. We'll need to create a prescription record with a hash, then tamper with it (e.g., change a field) and verify that the validation fails.

2) Test that duplicate dispensing of same prescription is prevented. This implies there is a unique constraint or business rule that prevents multiple dispensations for the same prescription (maybe only one full dispensing, or no more than the prescribed quantity). We'll test that attempting to dispense again raises an error.

3) Test that partial dispensing records remaining balance. This implies that when a prescription is partially dispensed, the system records the remaining quantity to be dispensed later.

We'll need to design tests that interact with the service layer. We'll assume there is a service class like FarmaciaService or DispensacaoService with methods like dispensar(prescricao_id, quantidade, ...). We'll also need models: Prescricao, Dispensacao, maybe Medicamento, etc.

Since we don't have the actual code, we'll write tests that are self-contained and use mocks or in-memory SQLite with actual models if they exist. But we can't import non-existent modules. The instruction says "Crie backend/tests/test_farmacia_dispensacao.py" - we are to create the file. It's okay to write tests that assume the existence of certain modules; they will be run in the actual project. We'll write the tests in a way that they can be adapted.

We'll include imports from the app modules. We'll use pytest fixtures to set up a test database and client.

We'll also need to ensure the tests are isolated and use transactions.

Let's outline the test file:

- Imports: pytest, sqlalchemy, fastapi.testclient, etc.
- Fixtures: db_session, client, etc.
- Helper functions to create prescriptions, etc.
- Test functions.

We'll write code that is plausible and follows best practices.

We'll also include type hints.

We'll use Pydantic v2 for schemas, but tests may not need them directly.

Let's write the file.

We'll start with a docstring explaining the purpose.

We'll define a fixture for the database session using SQLAlchemy's create_engine with SQLite in-memory, and create tables from Base metadata.

We'll need to import Base from the app's models. We'll assume there is a module backend.app.models or similar. We'll use a try-except to handle import errors? No, we should write the tests assuming the project structure.

We'll also need to import the service class. We'll assume it's in backend.app.services.farmacia.

We'll write tests that use the service directly.

For hash validation, we'll need to know how hash is generated. We'll assume there is a function to compute hash from prescription data. We'll test that if we change a field, the hash doesn't match.

For duplicate dispensing, we'll test that after a full dispensing, another attempt raises an exception.

For partial dispensing, we'll test that after partial, the remaining quantity is updated.

We'll also need to consider the business rules: maybe a prescription has a quantity and a dispensed quantity. We'll track that.

Let's write the code.

We'll include comments in Portuguese? The task is in Portuguese, but code can be in English. We'll use English for code, but comments can be in Portuguese if needed. We'll keep it professional.

We'll also include a test for the hash validation specifically: create a prescription, compute hash, then modify a field and try to validate; expect rejection.

We'll need to mock the hash function or use the actual one. We'll assume there is a function `calcular_hash_prescricao` in the service.

We'll write tests that are independent.

Let's produce the final answer with the code block.```python
# Arquivo: backend/tests/test_farmacia_dispensacao.py
"""
Testes de integridade da dispensação e validação hash (C10).

Cobre:
1. Rejeição de receitas com hash adulterado.
2. Impedimento de dispensação duplicada da mesma receita.
3. Registro de saldo remanescente em baixa parcial.

Segue os padrões do Projeto MedIA:
- Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0.
- Padrões SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF).
- Cobertura de testes automatizados com pytest.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Importações do projeto (ajuste os caminhos conforme a estrutura real)
from backend.app.models.base import Base
from backend.app.models.farmacia import Dispensacao, Prescricao, Medicamento
from backend.app.services.farmacia import FarmaciaService, HashInvalidoError, DispensacaoDuplicadaError
from backend.app.schemas.farmacia import DispensacaoCreate, PrescricaoCreate


@pytest.fixture
def db_session() -> Session:
    """
    Cria um banco de dados SQLite em memória para cada teste.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def farmacia_service(db_session: Session) -> FarmaciaService:
    """
    Instancia o serviço de farmácia com a sessão de teste.
    """
    return FarmaciaService(db=db_session)


def _criar_prescricao(db: Session, **kwargs) -> Prescricao:
    """
    Cria uma prescrição válida no banco de teste.
    """
    dados = {
        "cns_paciente": "123456789012345",
        "cpf_paciente": "12345678901",
        "cid10": "J00",
        "ciap2": "R74",
        "medicamento": "Amoxicilina 500mg",
        "quantidade_prescrita": 10,
        "posologia": "Tomar 1 comprimido de 8 em 8 horas por 7 dias",
    }
    dados.update(kwargs)
    prescricao = Prescricao(**dados)
    db.add(prescricao)
    db.commit()
    db.refresh(prescricao)
    return prescricao


def _criar_medicamento(db: Session, **kwargs) -> Medicamento:
    """
    Cria um medicamento no banco de teste.
    """
    dados = {
        "nome": "Amoxicilina 500mg",
        "codigo_barras": "7891234567890",
        "estoque": 100,
    }
    dados.update(kwargs)
    medicamento = Medicamento(**dados)
    db.add(medicamento)
    db.commit()
    db.refresh(medicamento)
    return medicamento


def _calcular_hash(prescricao: Prescricao) -> str:
    """
    Calcula o hash de uma prescrição (função auxiliar para testes).
    """
    from backend.app.services.farmacia import calcular_hash_prescricao
    return calcular_hash_prescricao(prescricao)


# -----------------------------------------------------------------------------
# 1. Receitas com hash adulterado são rejeitadas
# -----------------------------------------------------------------------------

def test_rejeita_receita_com_hash_adulterado(db_session: Session, farmacia_service: FarmaciaService):
    """
    Deve lançar HashInvalidoError quando o hash da prescrição não confere
    com os dados atuais.
    """
    # Cria prescrição e calcula hash original
    prescricao = _criar_prescricao(db_session)
    hash_original = _calcular_hash(prescricao)
    prescricao.hash = hash_original
    db_session.commit()

    # Adultera um campo da prescrição (simula alteração indevida)
    prescricao.quantidade_prescrita = 99
    db_session.commit()

    # Tenta dispensar com hash adulterado
    with pytest.raises(HashInvalidoError):
        farmacia_service.dispensar(
            prescricao_id=prescricao.id,
            quantidade=1,
            hash_recebido=hash_original,  # hash antigo, não confere com os dados atuais
        )


def test_aceita_receita_com_hash_valido(db_session: Session, farmacia_service: FarmaciaService):
    """
    Deve permitir a dispensação quando o hash confere com os dados.
    """
    prescricao = _criar_prescricao(db_session)
    hash_correto = _calcular_hash(prescricao)
    prescricao.hash = hash_correto
    db_session.commit()

    # Deve dispensar sem erro
    dispensacao = farmacia_service.dispensar(
        prescricao_id=prescricao.id,
        quantidade=2,
        hash_recebido=hash_correto,
    )
    assert dispensacao.id is not None
    assert dispensacao.quantidade == 2


# -----------------------------------------------------------------------------
# 2. Dispensação duplicada da mesma receita é impedida
# -----------------------------------------------------------------------------

def test_impede_dispensacao_duplicada_total(db_session: Session, farmacia_service: FarmaciaService):
    """
    Após uma dispensação total, nova tentativa deve lançar DispensacaoDuplicadaError.
    """
    prescricao = _criar_prescricao(db_session, quantidade_prescrita=5)
    hash_correto = _calcular_hash(prescricao)
    prescricao.hash = hash_correto
    db_session.commit()

    # Dispensação total
    farmacia_service.dispensar(
        prescricao_id=prescricao.id,
        quantidade=5,
        hash_recebido=hash_correto,
    )

    # Nova tentativa (mesma receita, mesmo hash)
    with pytest.raises(DispensacaoDuplicadaError):
        farmacia_service.dispensar(
            prescricao_id=prescricao.id,
            quantidade=1,
            hash_recebido=hash_correto,
        )


def test_permite_dispensacao_parcial_sequencial(db_session: Session, farmacia_service: FarmaciaService):
    """
    Dispensações parciais são permitidas enquanto houver saldo.
    """
    prescricao = _criar_prescricao(db_session, quantidade_prescrita=10)
    hash_correto = _calcular_hash(prescricao)
    prescricao.hash = hash_correto
    db_session.commit()

    # Primeira dispensação parcial
    farmacia_service.dispensar(
        prescricao_id=prescricao.id,
        quantidade=4,
        hash_recebido=hash_correto,
    )

    # Segunda dispensação parcial (saldo restante = 6)
    farmacia_service.dispensar(
        prescricao_id=prescricao.id,
        quantidade=6,
        hash_recebido=hash_correto,
    )

    # Verifica que o saldo é zero
    db_session.refresh(prescricao)
    assert prescricao.quantidade_dispensada == 10
    assert prescricao.saldo_restante == 0


# -----------------------------------------------------------------------------
# 3. Baixa parcial registra saldo remanescente
# -----------------------------------------------------------------------------

def test_baixa_parcial_registra_saldo_remanescente(db_session: Session, farmacia_service: FarmaciaService):
    """
    Após uma dispensação parcial, o saldo remanescente deve ser atualizado.
    """
    prescricao = _criar_prescricao(db_session, quantidade_prescrita=10)
    hash_correto = _calcular_hash(prescricao)
    prescricao.hash = hash_correto
    db_session.commit()

    # Dispensação parcial de 3 unidades
    farmacia_service.dispensar(
        prescricao_id=prescricao.id,
        quantidade=3,
        hash_recebido=hash_correto,
    )

    db_session.refresh(prescricao)
    assert prescricao.quantidade_dispensada == 3
    assert prescricao.saldo_restante == 7

    # Nova dispensação parcial de 2 unidades
    farmacia_service.dispensar(
        prescricao_id=prescricao.id,
        quantidade=2,
        hash_recebido=hash_correto,
    )

    db_session.refresh(prescricao)
    assert prescricao.quantidade_dispensada == 5
    assert prescricao.saldo_restante == 5


def test_baixa_parcial_nao_permite_quantidade_maior_que_saldo(
    db_session: Session, farmacia_service: FarmaciaService
):
    """
    Deve lançar erro se a quantidade dispensada exceder o saldo restante.
    """
    prescricao = _criar_prescricao(db_session, quantidade_prescrita=5)
    hash_correto = _calcular_hash(prescricao)
    prescricao.hash = hash_correto
    db_session.commit()

    # Tenta dispensar mais do que o prescrito
    with pytest.raises(ValueError, match="Quantidade excede o saldo restante"):
        farmacia_service.dispensar(
            prescricao_id=prescricao.id,
            quantidade=6,
            hash_recebido=hash_correto,
        )


# -----------------------------------------------------------------------------
# Testes adicionais de integridade (opcionais)
# -----------------------------------------------------------------------------

def test_dispensacao_gera_registro_com_hash_integridade(
    db_session: Session, farmacia_service: FarmaciaService
):
    """
    A dispensação deve gerar um registro com hash próprio de integridade.
    """
    prescricao = _criar_prescricao(db_session, quantidade_prescrita=5)
    hash_correto = _calcular_hash(prescricao)
    prescricao.hash = hash_correto
    db_session.commit()

    dispensacao = farmacia_service.dispensar(
        prescricao_id=prescricao.id,
        quantidade=2,
        hash_recebido=hash_correto,
    )

    assert dispensacao.hash_integridade is not None
    assert len(dispensacao.hash_integridade) == 64  # SHA-256


def test_dispensacao_atualiza_estoque_medicamento(
    db_session: Session, farmacia_service: FarmaciaService
):
    """
    A dispensação deve reduzir o estoque do medicamento correspondente.
    """
    medicamento = _criar_medicamento(db_session, estoque=50)
    prescricao = _criar_prescricao(
        db_session,
        medicamento_id=medicamento.id,
        quantidade_prescrita=10,
    )
    hash_correto = _calcular_hash(prescricao)
    prescricao.hash = hash_correto
    db_session.commit()

    farmacia_service.dispensar(
        prescricao_id=prescricao.id,
        quantidade=3,
        hash_recebido=hash_correto,
    )

    db_session.refresh(medicamento)
    assert medicamento.estoque == 47
```