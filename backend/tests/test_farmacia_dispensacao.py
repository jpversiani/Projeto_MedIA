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
