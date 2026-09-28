"""
Testes de integridade da camada de AUTENTICAÇÃO do MedIA.

Cobrem: login demo/local, credenciais inválidas, MFA, SSO (Google/Microsoft),
portador de token (válido/inválido/expirado/ausente), multi-tenancy
(switch-clinic) e trilha de auditoria (LGPD/CFM).
"""
import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.services.auth_service import (
    SECRET_KEY,
    ALGORITHM,
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.usuario import Usuario, VinculoClinica, PapelUsuarioEnum
from app.models.estabelecimento import Estabelecimento


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _make_token(usuario: Usuario, vinculo: VinculoClinica = None, exp_delta_min: int = 60) -> str:
    """Emite um JWT controlado (para simular expiração/conteúdo adulterado)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario.id),
        "email": usuario.email,
        "nome": usuario.nome,
        "is_superuser": usuario.is_superuser,
        "clinica_id": vinculo.estabelecimento_id if vinculo else None,
        "papel": vinculo.papel.value if vinculo else "VISITANTE",
        "profissional_id": vinculo.profissional_id if vinculo else None,
        "iat": int((now - timedelta(minutes=1)).timestamp()),
        "exp": int((now + timedelta(minutes=exp_delta_min)).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ------------------------------------------------------------------
# 1. Login demo / local
# ------------------------------------------------------------------
def test_login_demo_role_medico_retorna_token(client):
    resp = client.post("/api/v1/auth/login", json={"demo_role": "medico_titular"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["usuario"]["email"] == "dr.versiani@media-saude.com.br"


def test_login_demo_role_secretaria_papel_recepcao(client):
    resp = client.post("/api/v1/auth/login", json={"demo_role": "secretaria"})
    assert resp.status_code == 200, resp.text
    usuario = resp.json()["usuario"]
    # A secretaria deve ter vínculo de RECEPCAO (não MEDICO)
    assert usuario["vinculos"], "Secretária deveria possuir vínculo de clínica"
    assert all(v["papel"] == "RECEPCAO" for v in usuario["vinculos"])


def test_login_credenciais_invalidas_retorna_401(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "inexistente@media-saude.com.br", "password": "senha-errada"},
    )
    assert resp.status_code == 401
    assert "Credenciais inválidas" in resp.json()["detail"]


def test_login_email_invalido_retorna_422(client):
    """Validação de EmailStr deve rejeitar e-mail malformado antes da lógica."""
    resp = client.post("/api/v1/auth/login", json={"email": "nao-e-email", "password": "x"})
    assert resp.status_code == 422


def test_login_senha_correta_apos_hash(client, db_session):
    usuario = Usuario(
        email="local.teste@media-saude.com.br",
        nome="Usuário Local",
        sso_provider="local",
        hashed_password=hash_password("Segredo#123"),
        is_active=True,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": usuario.email, "password": "Segredo#123"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["access_token"]


# ------------------------------------------------------------------
# 2. MFA (TOTP)
# ------------------------------------------------------------------
def test_login_mfa_exigido_sem_codigo_retorna_400(client, db_session):
    from app.services.auth_service import generate_totp_secret

    usuario = Usuario(
        email="mfa.ativo@media-saude.com.br",
        nome="Usuário MFA",
        sso_provider="local",
        hashed_password=hash_password("Senha#123"),
        mfa_enabled=True,
        mfa_secret=generate_totp_secret(),
        is_active=True,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": usuario.email, "password": "Senha#123"},
    )
    assert resp.status_code == 400
    assert "MFA" in resp.json()["detail"]


def test_login_mfa_codigo_valido_retorna_200(client, db_session):
    from app.services.auth_service import generate_totp_secret, get_totp_token

    secret = generate_totp_secret()
    usuario = Usuario(
        email="mfa.ok@media-saude.com.br",
        nome="Usuário MFA OK",
        sso_provider="local",
        hashed_password=hash_password("Senha#123"),
        mfa_enabled=True,
        mfa_secret=secret,
        is_active=True,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)

    resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": usuario.email,
            "password": "Senha#123",
            "mfa_code": get_totp_token(secret),
        },
    )
    assert resp.status_code == 200, resp.text


# ------------------------------------------------------------------
# 3. Portador do Token (/me)
# ------------------------------------------------------------------
def test_me_sem_token_retorna_401(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_header_malformado_retorna_401(client):
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Token abc"})
    assert resp.status_code == 401


def test_me_token_adulterado_retorna_401(client):
    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer abc.def.ghi"}
    )
    assert resp.status_code == 401


def test_me_token_expirado_retorna_401(client, db_session):
    """LACUNA CRÍTICA: decode_access_token deve rejeitar 'exp' no passado."""
    usuario = Usuario(
        email="expirado@media-saude.com.br",
        nome="Usuário Expirado",
        sso_provider="local",
        is_active=True,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)

    token = _make_token(usuario, exp_delta_min=-10)  # já expirado
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert "expirad" in resp.json()["detail"].lower()


def test_me_token_valido_retorna_perfil(client):
    login = client.post("/api/v1/auth/login", json={"demo_role": "medico_titular"})
    token = login.json()["access_token"]
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == "dr.versiani@media-saude.com.br"


def test_me_token_usuario_inativo_retorna_404(client, db_session):
    usuario = Usuario(
        email="inativo@media-saude.com.br",
        nome="Usuário Inativo",
        sso_provider="local",
        is_active=False,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)

    token = _make_token(usuario)
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


# ------------------------------------------------------------------
# 4. SSO (Google / Microsoft)
# ------------------------------------------------------------------
@pytest.mark.parametrize("provider", ["google", "microsoft"])
def test_sso_url_retorna_auth_url(client, provider):
    resp = client.get(f"/api/v1/auth/sso/{provider}/url")
    assert resp.status_code == 200
    assert resp.json()["provider"] == provider
    assert resp.json()["auth_url"].startswith("https://")


@pytest.mark.parametrize("provider", ["google", "microsoft"])
def test_sso_callback_provisiona_usuario_e_token(client, provider):
    resp = client.post(
        f"/api/v1/auth/sso/{provider}/callback", json={"id_token": f"sub-teste-{provider}"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["access_token"]


# ------------------------------------------------------------------
# 5. Multi-Tenancy (switch-clinic)
# ------------------------------------------------------------------
def test_switch_clinic_vinculo_valido_emite_novo_token(client, db_session):
    login = client.post("/api/v1/auth/login", json={"demo_role": "admin"})
    token = login.json()["access_token"]
    est_id = db_session.query(Estabelecimento).first().id

    resp = client.post(
        "/api/v1/auth/switch-clinic",
        json={"estabelecimento_id": est_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["usuario"]["clinica_ativa"]["estabelecimento_id"] == est_id


def test_switch_clinic_sem_vinculo_retorna_403(client, db_session):
    login = client.post("/api/v1/auth/login", json={"demo_role": "medico_titular"})
    token = login.json()["access_token"]

    est_inexistente = 999999
    resp = client.post(
        "/api/v1/auth/switch-clinic",
        json={"estabelecimento_id": est_inexistente},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_switch_clinic_sem_token_retorna_401(client):
    resp = client.post("/api/v1/auth/switch-clinic", json={"estabelecimento_id": 1})
    assert resp.status_code == 401


# ------------------------------------------------------------------
# 6. Trilha de auditoria (LGPD / CFM)
# ------------------------------------------------------------------
def test_audit_trail_requer_autenticacao(client):
    resp = client.get("/api/v1/auth/audit-trail")
    assert resp.status_code == 401


def test_audit_trail_registra_login(client):
    login = client.post("/api/v1/auth/login", json={"demo_role": "admin"})
    token = login.json()["access_token"]
    resp = client.get(
        "/api/v1/auth/audit-trail",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    acoes = [e["acao"] for e in resp.json()]
    assert "LOGIN_SUCESSO" in acoes


# ------------------------------------------------------------------
# 7. Utilitários de senha
# ------------------------------------------------------------------
def test_hash_e_verify_password_roundtrip():
    h = hash_password("MedIA#2026")
    assert h != "MedIA#2026"
    assert verify_password("MedIA#2026", h) is True
    assert verify_password("errada", h) is False


def test_verify_password_hash_invalido_retorna_false():
    assert verify_password("qualquer", "sem-separador") is False
    assert verify_password("qualquer", "") is False