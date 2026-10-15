"""
Suíte de Testes Automatizados para Autenticação, SSO (Google/Microsoft), Multi-Tenancy e Trilha de Auditoria (LGPD).
"""

from app.models.estabelecimento import Estabelecimento
from app.models.usuario import VinculoClinica
from app.services.auth_service import (
    generate_totp_secret,
    get_totp_token,
    hash_password,
    verify_password,
    verify_totp_token,
)

# NOTA: o cliente HTTP vem da fixture `client` do conftest.py, que sobrescreve
# `get_db` para o banco SQLite em memória já populado por `seed_database`.
# Um `TestClient(app)` criado no escopo do módulo usaria o `get_db` real e
# gravaria no `backend/esus.db` de desenvolvimento, tornando a suíte dependente
# de estado residual entre execuções.


def test_password_hashing():
    pwd = "SenhaSeguraMedIA2026!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("SenhaErrada", hashed) is False


def test_totp_mfa_rfc6238():
    secret = generate_totp_secret()
    assert len(secret) >= 16
    token = get_totp_token(secret)
    assert len(token) == 6
    assert token.isdigit()
    assert verify_totp_token(secret, token) is True
    assert verify_totp_token(secret, "000000") is False


def test_login_demo_medico_titular(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "dra.francelli@media-saude.com.br",
        "demo_role": "medico_titular"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["usuario"]["nome"] == "Dra. Francelli Neves Versiani"
    assert data["usuario"]["clinica_ativa"]["papel"] == "MEDICO"
    assert len(data["usuario"]["vinculos"]) >= 1


def test_login_demo_reconcilia_vinculos_de_usuario_existente(client, db_session):
    """Regressão: o login demo precisa reconciliar vínculos mesmo para usuário já existente.

    Antes, os vínculos só eram criados na primeira criação do usuário. Um usuário
    pré-existente ficava sem `clinica_ativa` e o Workspace Switcher quebrava.
    """
    db_session.query(VinculoClinica).filter(
        VinculoClinica.usuario_id == 1
    ).delete(synchronize_session=False)
    db_session.commit()

    res = client.post("/api/v1/auth/login", json={"demo_role": "medico_titular"})
    assert res.status_code == 200
    assert res.json()["usuario"]["clinica_ativa"] is not None


def test_sso_google_and_microsoft_endpoints(client):
    # 1. URL generation
    res_g_url = client.get("/api/v1/auth/sso/google/url")
    assert res_g_url.status_code == 200
    assert "accounts.google.com" in res_g_url.json()["auth_url"]

    res_m_url = client.get("/api/v1/auth/sso/microsoft/url")
    assert res_m_url.status_code == 200
    assert "login.microsoftonline.com" in res_m_url.json()["auth_url"]

    # 2. Callbacks
    res_g = client.post("/api/v1/auth/sso/google/callback", json={
        "provider": "google",
        "id_token": "token_mock_google_test"
    })
    assert res_g.status_code == 200
    assert res_g.json()["usuario"]["sso_provider"] == "google"

    res_m = client.post("/api/v1/auth/sso/microsoft/callback", json={
        "provider": "microsoft",
        "id_token": "token_mock_ms_test"
    })
    assert res_m.status_code == 200
    assert res_m.json()["usuario"]["sso_provider"] == "microsoft"


def test_multi_tenancy_switch_clinic(client, db_session):
    """Alternância de clínica ativa emitindo novo JWT com o escopo da unidade alvo."""
    # Garante uma segunda unidade para exercitar de fato a troca de contexto.
    segunda = db_session.query(Estabelecimento).filter(
        Estabelecimento.cnes == "3180116"
    ).first()
    if not segunda:
        segunda = Estabelecimento(
            cnes="3180116",
            nome_fantasia="Consultório Particular MedIA - Montes Claros",
            razao_social="MedIA Serviços de Saúde LTDA",
            municipio_ibge="3143302",
            logradouro="Av. Brasil",
            numero="1500",
            bairro="Centro"
        )
        db_session.add(segunda)
        db_session.commit()
        db_session.refresh(segunda)

    login_res = client.post("/api/v1/auth/login", json={
        "email": "dra.francelli@media-saude.com.br",
        "demo_role": "medico_titular"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    vinculos = login_res.json()["usuario"]["vinculos"]
    assert len(vinculos) >= 2, "o login demo deveria vincular o médico às duas unidades"

    target_clinica = segunda.id
    res_switch = client.post(
        "/api/v1/auth/switch-clinic",
        headers={"Authorization": f"Bearer {token}"},
        json={"estabelecimento_id": target_clinica}
    )
    assert res_switch.status_code == 200
    assert res_switch.json()["usuario"]["clinica_ativa"]["estabelecimento_id"] == target_clinica


def test_switch_clinic_negado_para_unidade_sem_vinculo(client, db_session):
    """Um usuário não pode entrar no contexto de uma unidade da qual não é vinculado.

    A unidade é criada DEPOIS do login de propósito: o login demo reconcilia os
    vínculos com todas as clínicas existentes, então só uma clínica criada
    depois disso permanece realmente fora do escopo do usuário.
    """
    login_res = client.post("/api/v1/auth/login", json={"demo_role": "medico_titular"})
    token = login_res.json()["access_token"]

    alheia = Estabelecimento(
        cnes="9999999",
        nome_fantasia="Unidade de Terceiros",
        razao_social="Outro CNPJ",
        municipio_ibge="3106200",
        logradouro="Rua X",
        numero="1",
        bairro="Y"
    )
    db_session.add(alheia)
    db_session.commit()
    db_session.refresh(alheia)

    res = client.post(
        "/api/v1/auth/switch-clinic",
        headers={"Authorization": f"Bearer {token}"},
        json={"estabelecimento_id": alheia.id}
    )
    assert res.status_code == 403


def test_audit_trail_immutable(client):
    login_res = client.post("/api/v1/auth/login", json={
        "email": "dra.francelli@media-saude.com.br",
        "demo_role": "medico_titular"
    })
    token = login_res.json()["access_token"]

    res_audit = client.get(
        "/api/v1/auth/audit-trail?limit=10",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_audit.status_code == 200
    logs = res_audit.json()
    assert len(logs) > 0
    primeiro = logs[0]
    assert "hash_integridade" in primeiro
    assert len(primeiro["hash_integridade"]) == 64 # SHA-256 hex
