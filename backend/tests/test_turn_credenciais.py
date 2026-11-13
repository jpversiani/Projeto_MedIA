"""Testes das credenciais efêmeras do TURN (Fase 2 — telemedicina em qualquer rede).

O coturn do compose usa ``use-auth-secret``: ele só autentica credenciais no
padrão REST API do TURN (username = timestamp de expiração, credential =
base64(HMAC-SHA1(secret, username))). Antes o ``ice_servers`` entregava um par
estático, que o coturn recusaria — a chamada não passava mídia atrás de NAT
simétrico mesmo com TURN "configurado".
"""
import base64
import hashlib
import hmac
import time

from app.core.config import TURN_CREDENTIAL_TTL_SEGUNDOS, Settings


def _settings(**kw) -> Settings:
    return Settings(_env_file=None, **kw)


def _turn(servidores):
    return next(x for x in servidores if "turn:" in x["urls"])


def test_turn_com_secret_gera_credencial_efemera_verificavel():
    s = _settings(TURN_URL="turn:turn.exemplo:3478", TURN_SECRET="segredo-turn")
    turn = _turn(s.ice_servers)
    username, credential = turn["username"], turn["credential"]

    # username é um timestamp de expiração futuro, dentro da janela de TTL.
    agora = int(time.time())
    assert agora < int(username) <= agora + TURN_CREDENTIAL_TTL_SEGUNDOS + 5

    # credential = base64(HMAC-SHA1(secret, username)): é exatamente o que o
    # coturn recalcula para autenticar. Conferimos de forma independente.
    esperado = base64.b64encode(
        hmac.new(b"segredo-turn", username.encode("utf-8"), hashlib.sha1).digest()
    ).decode("ascii")
    assert credential == esperado


def test_turn_sem_secret_usa_par_estatico():
    s = _settings(
        TURN_URL="turn:turn.exemplo:3478", TURN_USERNAME="user", TURN_CREDENTIAL="pass"
    )
    turn = _turn(s.ice_servers)
    assert turn["username"] == "user"
    assert turn["credential"] == "pass"


def test_sem_turn_url_nao_entrega_turn():
    s = _settings(TURN_SECRET="segredo-turn")
    assert all("turn:" not in x["urls"] for x in s.ice_servers)


def test_stun_sempre_presente():
    s = _settings()
    assert any("stun:" in x["urls"] for x in s.ice_servers)