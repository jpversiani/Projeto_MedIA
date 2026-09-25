import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.convenios import GuiaStatus, LancamentoStatus, LancamentoTipo
from app.repositories.convenios_repo import ConveniosRepository
from app.services.tiss_generator import TISSGenerator

# Setup test DB in memory
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def test_tiss_generator_xml():
    xml = TISSGenerator.gerar_guia_consulta_xml(
        numero_guia="TISS-TEST-001",
        operadora_registro_ans="305685",
        paciente_nome="Maria Silva",
        numero_carteira="0011223344",
        paciente_cpf="12345678901",
        cid10="I10",
        ciap2="K86",
        procedimento_tuss="10101012",
        valor_procedimento=180.0,
    )
    assert "TISS-TEST-001" in xml
    assert "305685" in xml
    assert "Maria Silva" in xml
    assert "10101012" in xml
    assert "180.00" in xml
    assert "padroes/tiss/schemas" in xml
    assert "<ans:hash>" in xml

def test_tiss_generator_dmed_recibo():
    recibo = TISSGenerator.gerar_recibo_dmed(
        numero_recibo="REC-2026-001",
        prestador_nome="Clínica MedIA",
        prestador_cpf_cnpj="12345678000100",
        paciente_nome="João Pedro",
        paciente_cpf="98765432100",
        valor=250.0,
    )
    assert recibo["recibo_numero"] == "REC-2026-001"
    assert recibo["dmed_dedutivel"] is True
    assert "autenticacao_eletronica" in recibo
    assert recibo["servico"]["valor_total"] == 250.0

def test_convenios_repo_and_workflow(db_session):
    # 1. Cria operadora
    operadora = ConveniosRepository.criar_operadora(
        db=db_session,
        nome="Bradesco Saúde",
        registro_ans="005711",
        cnpj="92693118000160",
    )
    assert operadora.id is not None
    assert operadora.nome == "Bradesco Saúde"

    # 2. Cria plano
    plano = ConveniosRepository.criar_plano(
        db=db_session,
        operadora_id=operadora.id,
        nome="Top Nacional",
        codigo_plano="TOP-01",
    )
    assert plano.id is not None

    # 3. Emite Guia TISS
    guia = ConveniosRepository.emitir_guia_consulta_tiss(
        db=db_session,
        plano_id=plano.id,
        paciente_nome="Carlos Eduardo",
        numero_carteira="9988776655",
        paciente_cpf="11122233344",
        ciap2="T90",
        cid10="E11",
        valor=200.0,
    )
    assert guia.id is not None
    assert guia.status == GuiaStatus.GERADA
    assert guia.valor_total == 200.0
    assert len(guia.lancamentos) == 1
    assert guia.lancamentos[0].status == LancamentoStatus.PENDENTE

    # 4. Atualiza status para PAGA
    guia_paga = ConveniosRepository.atualizar_status_guia(
        db=db_session,
        guia_id=guia.id,
        novo_status=GuiaStatus.PAGA,
    )
    assert guia_paga.status == GuiaStatus.PAGA
    assert guia_paga.lancamentos[0].status == LancamentoStatus.PAGO

    # 5. Emite Recibo DMED Particular
    recibo = ConveniosRepository.registrar_recibo_particular_dmed(
        db=db_session,
        paciente_nome="Ana Clara",
        paciente_cpf="55566677788",
        valor=300.0,
    )
    assert recibo.id is not None
    assert recibo.tipo == LancamentoTipo.PARTICULAR
    assert recibo.status == LancamentoStatus.PAGO
    assert recibo.recibo_numero.startswith("REC-")

def test_api_convenios_endpoints(client):
    # 1. Post Operadora
    resp_op = client.post(
        "/api/v1/convenios/operadoras",
        json={
            "nome": "Amil Assistência Médica",
            "registro_ans": "326305",
            "cnpj": "29309127000179",
            "contato_email": "tiss@amil.com.br",
        },
    )
    assert resp_op.status_code == 201
    op_data = resp_op.json()
    op_id = op_data["id"]

    # 2. Get Operadoras
    resp_ops = client.get("/api/v1/convenios/operadoras")
    assert resp_ops.status_code == 200
    assert any(o["id"] == op_id for o in resp_ops.json())

    # 3. Post Plano
    resp_pl = client.post(
        "/api/v1/convenios/planos",
        json={
            "operadora_id": op_id,
            "nome": "Amil Blue 300",
            "codigo_plano": "ABLUE-300",
            "tipo": "AMBULATORIAL",
        },
    )
    assert resp_pl.status_code == 201
    pl_id = resp_pl.json()["id"]

    # 4. Post Guia Consulta TISS
    resp_guia = client.post(
        "/api/v1/convenios/guias/consulta",
        json={
            "plano_id": pl_id,
            "paciente_nome": "Juliana Silveira",
            "numero_carteira": "1234567890",
            "paciente_cpf": "12312312300",
            "ciap2": "W78",
            "cid10": "O20.0",
            "procedimento_tuss": "10101012",
            "valor": 175.50,
        },
    )
    assert resp_guia.status_code == 201
    guia_data = resp_guia.json()
    guia_id = guia_data["id"]
    assert guia_data["paciente_nome"] == "Juliana Silveira"
    assert "xml_tiss" in guia_data

    # 5. Patch Guia Status
    resp_patch = client.patch(
        f"/api/v1/convenios/guias/{guia_id}/status",
        json={"status": "PAGA"},
    )
    assert resp_patch.status_code == 200
    assert resp_patch.json()["status"] == "PAGA"

    # 6. Post DMED Recibo
    resp_dmed = client.post(
        "/api/v1/convenios/dmed/recibo",
        json={
            "paciente_nome": "Marcos Vinicius",
            "paciente_cpf": "99988877711",
            "valor": 220.0,
            "descricao": "Consulta Pediátrica Particular",
        },
    )
    assert resp_dmed.status_code == 200
    dmed_data = resp_dmed.json()
    assert "recibo_numero" in dmed_data
    assert dmed_data["dados_fiscais_dmed"]["dmed_dedutivel"] is True
