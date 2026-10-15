"""Regressões de segurança introduzidas na evolução para a v1.

Cada teste documenta um defeito que existia no código e que não pode voltar.
A suíte é hermética: `conftest.py` define ENVIRONMENT=test, usa SQLite em
memória e desliga migração/seed no startup.
"""
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings


# ----------------------------------------------------------------------
# 1. Chave de assinatura do JWT
# ----------------------------------------------------------------------
def test_chave_padrao_nao_e_usada_em_producao():
    """Sem JWT_SECRET_KEY, produção deve recusar a configuração."""
    s = Settings(ENVIRONMENT="production")
    with pytest.raises(RuntimeError) as exc:
        s.validar_ambiente()
    assert "JWT_SECRET_KEY" in str(exc.value)


def test_alias_secret_key_legado_e_aceito():
    """O `.env.example` documentava SECRET_KEY; o código lia JWT_SECRET_KEY.

    Esse descasamento fazia a chave do operador ser silenciosamente ignorada.
    """
    s = Settings(ENVIRONMENT="production", SECRET_KEY="x" * 64)
    assert s.effective_secret_key == "x" * 64


def test_chave_padrao_so_esta_disponivel_em_desenvolvimento():
    dev = Settings(ENVIRONMENT="development")
    assert dev.effective_secret_key  # funciona localmente
    with pytest.raises(RuntimeError):
        Settings(ENVIRONMENT="production").effective_secret_key


# ----------------------------------------------------------------------
# 2. Configuração insegura em produção
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "overrides",
    [
        {"AUTO_SEED_DEMO_DATA": True},
        {"DEMO_LOGIN_ENABLED": True},
        {"SSO_ENABLED": True},
    ],
)
def test_producao_recusa_flags_de_demonstracao(overrides):
    base = {"ENVIRONMENT": "production", "JWT_SECRET_KEY": "k" * 64}
    base.update(overrides)
    with pytest.raises(RuntimeError):
        Settings(**base).validar_ambiente()


def test_producao_com_configuracao_segura_passa():
    s = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="k" * 64,
        AUTO_SEED_DEMO_DATA=False,
        DEMO_LOGIN_ENABLED=False,
        SSO_ENABLED=False,
    )
    s.validar_ambiente()  # não deve levantar


# ----------------------------------------------------------------------
# 2b. Leitura do .env
# ----------------------------------------------------------------------
@pytest.fixture
def env_file():
    """Cria um `.env` temporário ao lado dos testes e o remove ao final.

    Não usamos `tmp_path` nem `tempfile.mkdtemp`: ambos criam diretórios no
    `%TEMP%` do sistema (que pode não ser gravável em container/sandbox).
    """
    caminho = os.path.join(os.path.dirname(__file__), f".env.test.{uuid.uuid4().hex}")
    yield caminho
    if os.path.exists(caminho):
        os.remove(caminho)


def _escrever_env(caminho: str, conteudo: str) -> str:
    with open(caminho, "w", encoding="utf-8") as fh:
        fh.write(conteudo)
    return caminho


def test_valores_em_branco_no_env_caem_no_padrao(env_file):
    """`cp .env.example .env` entrega placeholders vazios.

    Sem normalização, `DATABASE_URL=` vazio quebrava `create_engine` e
    `CORS_ORIGINS=` desligava todo o CORS silenciosamente.
    """
    env = _escrever_env(
        env_file,
        "DATABASE_URL=\nCORS_ORIGINS=\nLOG_LEVEL=\nENVIRONMENT=\n"
        "JWT_SECRET_KEY=\nGEMINI_API_KEY=\n",
    )
    s = Settings(_env_file=env)

    assert s.DATABASE_URL.startswith("sqlite:///")  # não fica vazio
    assert s.cors_origins_list == ["http://localhost:8000", "http://127.0.0.1:8000"]
    assert s.JWT_SECRET_KEY is None  # em branco = não definido
    assert s.GEMINI_API_KEY is None
    assert s.LOG_LEVEL == "info"
    # `ENVIRONMENT` é "test" porque o conftest.py a define no ambiente, e
    # variáveis de ambiente têm precedência sobre o arquivo. O que importa é
    # que o valor em branco do arquivo não sobrepõe nem invalida nada.
    assert s.ENVIRONMENT in ("development", "test")


def test_valor_explicito_no_env_tem_precedencia(env_file):
    env = _escrever_env(env_file, "CORS_ORIGINS=https://app.exemplo.com.br\n")
    s = Settings(_env_file=env)
    assert s.cors_origins_list == ["https://app.exemplo.com.br"]


def test_sqlite_padrao_e_anotado_em_backend():
    """O SQLite padrão não pode depender do diretório de trabalho.

    `start.sh` faz `cd backend`, o README manda rodar de `backend/`, mas o
    pytest roda da raiz — com `sqlite:///./esus.db` eram DUAS bases.
    """
    s = Settings(DATABASE_URL="")
    caminho = s.DATABASE_URL.replace("sqlite:///", "").replace("/", os.sep)
    assert os.path.isabs(caminho), f"DATABASE_URL relativo ao CWD: {s.DATABASE_URL}"
    assert caminho.endswith(os.path.join("backend", "esus.db"))


# ----------------------------------------------------------------------
# 3. Autenticação obrigatória nas rotas clínicas
# ----------------------------------------------------------------------
ROTAS_CLINICAS = [
    ("GET", "/api/v1/cidadaos/"),
    ("GET", "/api/v1/prontuario/898000123456789"),
    ("GET", "/api/v1/agenda/"),
    ("GET", "/api/v1/analytics/kpis"),
    ("GET", "/api/v1/fila/"),
    ("GET", "/api/v1/terminologias/cid10"),
    ("POST", "/api/v1/farmacia/dispensacao/confirmar"),
    ("GET", "/api/v1/financeiro-medico/livro-caixa/demonstrativo"),
    ("POST", "/api/v1/sincronizacao/atendimentos"),
    ("GET", "/api/v1/sincronizacao/status"),
]


@pytest.mark.parametrize("metodo,url", ROTAS_CLINICAS)
def test_rota_clinica_exige_bearer_token(metodo, url, client, db_session):
    """Nenhuma rota clínica pode responder a um chamador anônimo.

    Antes, `curl /api/v1/cidadaos/` listava pacientes e
    `curl -X POST /api/v1/prescricao/emitir` emitia uma receita, sem token.
    """
    from fastapi import FastAPI
    from app.api.v1.router import build_clinical_router

    # App isolada com o router clínico protegido, reaproveitando a sessão
    # de teste (mesmo esquema em memória) via `client`.
    app_protegido = FastAPI()
    app_protegido.include_router(
        build_clinical_router(require_auth=True), prefix="/api/v1"
    )
    app_protegido.dependency_overrides = client.app.dependency_overrides

    with TestClient(app_protegido) as c:
        resp = c.request(metodo, url)

    assert resp.status_code == 401, f"{metodo} {url} respondeu {resp.status_code}"


def test_rotas_clinicas_abrem_sem_token_em_desenvolvimento(client):
    """Em desenvolvimento a v1 continua utilizável sem token (teste local)."""
    resp = client.get("/api/v1/cidadaos/")
    assert resp.status_code in (200, 404)


def test_login_demo_funciona_em_desenvolvimento(client):
    """O login de demonstração continua disponível para testar a v1 localmente."""
    resp = client.post("/api/v1/auth/login", json={"demo_role": "medico_titular"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_token_invalido_e_recusado(client):
    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer token.inventado.assinado"}
    )
    assert resp.status_code in (401, 404)


# ----------------------------------------------------------------------
# 4. Isolamento entre tenants na trilha de auditoria
# ----------------------------------------------------------------------
def test_trilha_auditoria_nao_vaza_entre_clinicas(client, db_session):
    """Um usuário só enxerga os eventos da clínica ativa do seu token.

    Antes, `GET /auth/audit-trail` devolvia os eventos de TODAS as unidades
    para qualquer usuário autenticado.
    """
    from app.models.usuario import AuditTrail

    outro = AuditTrail(
        usuario_id=999,
        estabelecimento_id=424242,  # clínica de outro tenant
        acao="ACESSAR_PRONTUARIO",
        recurso_tipo="Cidadao",
        recurso_id="1",
        hash_integridade="f" * 64,
    )
    db_session.add(outro)
    db_session.commit()

    login = client.post("/api/v1/auth/login", json={"demo_role": "medico_titular"})
    token = login.json()["access_token"]
    clinica_id = login.json()["usuario"]["clinica_ativa"]["estabelecimento_id"]

    resp = client.get(
        "/api/v1/auth/audit-trail?limit=200", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    for evento in resp.json():
        if evento["estabelecimento_id"] is not None:
            assert evento["estabelecimento_id"] == clinica_id


# ----------------------------------------------------------------------
# 5. Superfície de API documentada
# ----------------------------------------------------------------------
def test_openapi_declara_esquema_de_autenticacao():
    """O OpenAPI precisa declarar `securitySchemes`; estava vazio."""
    from app.main import app

    comps = app.openapi().get("components", {})
    assert "securitySchemes" in comps, (
        "OpenAPI sem securitySchemes: clientes e gateways não conseguem "
        "descobrir como se autenticar."
    )
