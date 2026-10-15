"""Fixtures compartilhadas da suíte de testes.

A suíte é HERMÉTICA: nada aqui toca o banco de desenvolvimento. O lifespan do
FastAPI (que aplica migrações e popula dados de demonstração) é desativado
nestes testes, e toda rota usa o SQLite em memória já populado por
`seed_database`. Sem estas variáveis, `TestClient(app)` executava o lifespan
contra o `settings.DATABASE_URL` real e a suíte gravava em `backend/esus.db`.
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Precisa vir ANTES de qualquer import de `app.*`: `app.core.config` lê estas
# variáveis no momento do import para construir o objeto `settings`.
os.environ["ENVIRONMENT"] = "test"
os.environ["AUTO_MIGRATE_ON_STARTUP"] = "false"
os.environ["AUTO_SEED_DEMO_DATA"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core import database as app_db
from app.core.database import Base, get_db
from app.main import app as fastapi_app
from app.seeds.init_data import seed_database

# Adicionar caminho do backend ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Garantir importação de todos os modelos
import app.models  # noqa: F401

# Banco de dados SQLite compartilhado em memória para a sessão de testes
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app_db.SessionLocal = TestingSessionLocal
app_db.engine = engine


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_database(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()
