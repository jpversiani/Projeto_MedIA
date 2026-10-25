"""Testes de sessão: access token curto, refresh rotativo e revogação (P1).

Antes, o único token durava **24 horas**, não podia ser revogado e era guardado
em ``localStorage`` pelo frontend. Um token roubado dava um dia inteiro de
acesso a prontuários, sem forma de cortar a sessão. Estes testes fixam o
comportamento novo:

* access token de 15 minutos e ``expires_in`` coerente com ele;
* refresh token de 7 dias registrado no banco, com rotação a cada uso;
* reutilização de refresh já rotacionado derruba todas as sessões;
* logout revoga a sessão de verdade;
* ``access`` e ``refresh`` não são intercambiáveis.
"""

import pytest

from app.models.usuario import PapelUsuarioEnum, RefreshToken, Usuario, VinculoClinica
from app.models.estabelecimento import Estabelecimento
from app.services.auth_service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    hash_password,
    decode_token,
)


@pytest.fixture
def usuario_sessao(db_session):
    """Usuário próprio do teste, com senha e vínculo, para não colidir com o seed."""
    estabelecimento = db_session.query(Estabelecimento).order_by(Estabelecimento.id).first()
    usuario = Usuario(
        email="sessao.teste@media-sessao.com.br",
        nome="Usuário Sessão",
        hashed_password=hash_password("senha-forte-123"),
        is_active=True,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)

    db_session.add(
        VinculoClinica(
            usuario_id=usuario.id,
            estabelecimento_id=estabelecimento.id,
            papel=PapelUsuarioEnum.MEDICO,
            is_default=True,
        )
    )
    db_session.commit()

    yield usuario, estabelecimento

    db_session.rollback()
    db_session.query(RefreshToken).filter(RefreshToken.usuario_id == usuario.id).delete()
    db_session.query(VinculoClinica).filter(VinculoClinica.usuario_id == usuario.id).delete()
    db_session.query(Usuario).filter(Usuario.id == usuario.id).delete()
    db_session.commit()


def _login(client, usuario):
    resposta = client.post(
        "/api/v1/auth/login",
        json={"email": usuario.email, "password": "senha-forte-123"},
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def test_access_token_dura_15_minutos(client, usuario_sessao):
    usuario, _ = usuario_sessao
    dados = _login(client, usuario)

    assert ACCESS_TOKEN_EXPIRE_MINUTES == 15
    assert dados["expires_in"] == 900

    payload = decode_token(dados["access_token"], tipo_esperado="access")
    assert payload is not None
    # O `expires_in` do JSON precisa refletir o token real, não a documentação.
    assert payload["exp"] - payload["iat"] == 900


def test_login_grava_cookies_httponly(client, usuario_sessao):
    usuario, _ = usuario_sessao
    resposta = client.post(
        "/api/v1/auth/login",
        json={"email": usuario.email, "password": "senha-forte-123"},
    )
    assert resposta.status_code == 200

    cookies = resposta.headers.get_list("set-cookie")
    refresh_cookie = [c for c in cookies if "media_refresh=" in c]
    assert refresh_cookie, cookies
    assert "httponly" in refresh_cookie[0].lower()


def test_login_retorna_refresh_token(client, usuario_sessao):
    usuario, _ = usuario_sessao
    dados = _login(client, usuario)
    assert dados["refresh_token"]
    payload = decode_token(dados["refresh_token"], tipo_esperado="refresh")
    assert payload is not None
    assert payload["tipo"] == "refresh"


def test_refresh_renova_e_rotaciona(client, usuario_sessao, db_session):
    usuario, _ = usuario_sessao
    dados = _login(client, usuario)
    primeiro_refresh = dados["refresh_token"]
    primeiro_jti = decode_token(primeiro_refresh, tipo_esperado="refresh")["jti"]

    renovado = client.post("/api/v1/auth/refresh", json={"refresh_token": primeiro_refresh})
    assert renovado.status_code == 200, renovado.text
    corpo = renovado.json()
    assert corpo["access_token"] != dados["access_token"]
    assert corpo["refresh_token"] != primeiro_refresh
    assert corpo["expires_in"] == 900

    # O token anterior precisa ter sido revogado (rotação).
    antigo = db_session.query(RefreshToken).filter(RefreshToken.jti == primeiro_jti).first()
    assert antigo is not None
    assert antigo.revoked_at is not None
    assert antigo.substituido_por is not None


def test_refresh_reutilizado_derruba_a_sessao(client, usuario_sessao, db_session):
    usuario, _ = usuario_sessao
    dados = _login(client, usuario)
    primeiro_refresh = dados["refresh_token"]

    assert client.post(
        "/api/v1/auth/refresh", json={"refresh_token": primeiro_refresh}
    ).status_code == 200

    # Reutilizar o token rotacionado é sinal de roubo: recusa e revoga tudo.
    reuso = client.post("/api/v1/auth/refresh", json={"refresh_token": primeiro_refresh})
    assert reuso.status_code == 401

    ativos = (
        db_session.query(RefreshToken)
        .filter(
            RefreshToken.usuario_id == usuario.id,
            RefreshToken.revoked_at.is_(None),
        )
        .count()
    )
    assert ativos == 0


def test_logout_revoga_a_sessao(client, usuario_sessao, db_session):
    usuario, _ = usuario_sessao
    dados = _login(client, usuario)
    refresh = dados["refresh_token"]

    saida = client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
    assert saida.status_code == 200

    negado = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert negado.status_code == 401


def test_logout_sem_token_apenas_limpa_cookies(client):
    resposta = client.post("/api/v1/auth/logout")
    assert resposta.status_code == 200


def test_refresh_token_nao_serve_como_bearer(client, usuario_sessao):
    usuario, _ = usuario_sessao
    dados = _login(client, usuario)
    refresh = dados["refresh_token"]

    resposta = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh}"}
    )
    assert resposta.status_code == 401


def test_access_token_nao_serve_como_refresh(client, usuario_sessao):
    usuario, _ = usuario_sessao
    dados = _login(client, usuario)

    resposta = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": dados["access_token"]}
    )
    assert resposta.status_code == 401


def test_sessao_pode_ser_usada_por_cookie(client, usuario_sessao):
    """Sem Authorization: o navegador só manda o cookie HttpOnly."""
    usuario, _ = usuario_sessao
    _login(client, usuario)

    resposta = client.get("/api/v1/auth/me")
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["email"] == usuario.email


def test_logout_all_revoga_todas_as_sessoes(client, usuario_sessao, db_session):
    usuario, _ = usuario_sessao
    primeira = _login(client, usuario)
    segunda = client.post(
        "/api/v1/auth/login",
        json={"email": usuario.email, "password": "senha-forte-123"},
    ).json()

    resposta = client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {segunda['access_token']}"},
    )
    assert resposta.status_code == 200
    assert resposta.json()["revogadas"] >= 2

    for refresh in (primeira["refresh_token"], segunda["refresh_token"]):
        assert client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh}
        ).status_code == 401
