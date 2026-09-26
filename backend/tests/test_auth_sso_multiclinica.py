"""
Suíte de Testes Automatizados para Autenticação, SSO (Google/Microsoft), Multi-Tenancy e Trilha de Auditoria (LGPD).
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.usuario import Usuario, VinculoClinica, PapelUsuarioEnum, AuditTrail
from app.models.estabelecimento import Estabelecimento
from app.services.auth_service import hash_password, verify_password, generate_totp_secret, verify_totp_token, get_totp_token

client = TestClient(app)


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


def test_login_demo_medico_titular():
    res = client.post("/api/v1/auth/login", json={
        "email": "dr.versiani@media-saude.com.br",
        "demo_role": "medico_titular"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["usuario"]["nome"] == "Dr. João Paulo Versiani"
    assert data["usuario"]["clinica_ativa"]["papel"] == "MEDICO"
    assert len(data["usuario"]["vinculos"]) >= 1


def test_sso_google_and_microsoft_endpoints():
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


def test_multi_tenancy_switch_clinic():
    # Login as medico
    login_res = client.post("/api/v1/auth/login", json={
        "email": "dr.versiani@media-saude.com.br",
        "demo_role": "medico_titular"
    })
    token = login_res.json()["access_token"]
    vinculos = login_res.json()["usuario"]["vinculos"]

    if len(vinculos) >= 2:
        target_clinica = vinculos[1]["estabelecimento_id"]
        res_switch = client.post(
            "/api/v1/auth/switch-clinic",
            headers={"Authorization": f"Bearer {token}"},
            json={"estabelecimento_id": target_clinica}
        )
        assert res_switch.status_code == 200
        assert res_switch.json()["usuario"]["clinica_ativa"]["estabelecimento_id"] == target_clinica


def test_audit_trail_immutable():
    login_res = client.post("/api/v1/auth/login", json={
        "email": "dr.versiani@media-saude.com.br",
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
