"""WebSocket do copiloto clínico: snapshot, keepalive e autorização.

Cobre o defeito que derrubava a conexão com ``NameError`` (o retorno de
``_obter_atendimento`` era descartado e uma variável inexistente era usada) e a
ausência de autenticação no handshake.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.config import Settings, settings
from app.models.usuario import PapelUsuarioEnum, Usuario
from app.services.auth_service import create_access_token


def _criar_atendimento(client: TestClient) -> int:
    resposta = client.post(
        "/api/v1/atendimentos/",
        json={
            "cidadao_id": 1,
            "profissional_id": 1,
            "estabelecimento_id": 1,
            "subjetivo_motivo": "Cefaleia occipital há 2 dias",
            "subjetivo_notas": "Sem febre, sem vômitos.",
            "objetivo_exame_fisico": "PA 140/90, afebril, neurológico sem déficits.",
            "avaliacao_notas": "Cefaleia tensional.",
            "plano_conduta": "Analgésico e retorno se piora.",
            "problemas": [],
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


def _token(db_session, clinica_id: int | None = None) -> str:
    usuario = db_session.query(Usuario).first()
    if usuario is None:
        usuario = Usuario(
            email="ws.teste@media-saude.com.br",
            nome="Usuário WS",
            sso_provider="local",
            hashed_password="nao-usado-neste-teste",
            is_active=True,
        )
        db_session.add(usuario)
        db_session.commit()
        db_session.refresh(usuario)
    vinculo = None
    if clinica_id is not None:
        vinculo = SimpleNamespace(
            estabelecimento_id=clinica_id,
            papel=PapelUsuarioEnum.MEDICO,
            profissional_id=None,
        )
    return create_access_token(usuario, vinculo)


def _forcar_auth(monkeypatch) -> None:
    monkeypatch.setattr(
        Settings, "require_auth", property(lambda self: True), raising=True
    )


def test_ws_envia_snapshot_e_responde_pong(client):
    atendimento_id = _criar_atendimento(client)

    with client.websocket_connect(f"/api/v1/copiloto/ws/{atendimento_id}") as ws:
        snapshot = ws.receive_json()
        assert snapshot["tipo"] == "snapshot_alertas"
        assert snapshot["atendimento_id"] == atendimento_id
        assert isinstance(snapshot["dados"]["alertas"], list)

        ws.send_text("ping")
        pong = ws.receive_json()
        assert pong["tipo"] == "pong"
        assert pong["atendimento_id"] == atendimento_id


def test_ws_atendimento_inexistente_fecha_com_4404(client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/api/v1/copiloto/ws/999999") as ws:
            ws.receive_json()

    assert exc.value.code == 4404


def test_ws_sem_token_e_recusado_quando_auth_obrigatoria(client, monkeypatch):
    atendimento_id = _criar_atendimento(client)
    _forcar_auth(monkeypatch)

    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/api/v1/copiloto/ws/{atendimento_id}") as ws:
            ws.receive_json()

    assert exc.value.code == 4401


def test_ws_com_token_valido_conecta(client, db_session, monkeypatch):
    atendimento_id = _criar_atendimento(client)
    token = _token(db_session, clinica_id=1)
    _forcar_auth(monkeypatch)

    with client.websocket_connect(
        f"/api/v1/copiloto/ws/{atendimento_id}?token={token}"
    ) as ws:
        snapshot = ws.receive_json()
        assert snapshot["tipo"] == "snapshot_alertas"


def test_ws_token_de_outro_estabelecimento_e_recusado(
    client, db_session, monkeypatch
):
    atendimento_id = _criar_atendimento(client)
    token = _token(db_session, clinica_id=999)
    _forcar_auth(monkeypatch)

    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            f"/api/v1/copiloto/ws/{atendimento_id}?token={token}"
        ) as ws:
            ws.receive_json()

    assert exc.value.code == 4401


def test_ws_token_invalido_e_recusado(client, monkeypatch):
    atendimento_id = _criar_atendimento(client)
    _forcar_auth(monkeypatch)

    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            f"/api/v1/copiloto/ws/{atendimento_id}?token=nao-e-um-jwt"
        ) as ws:
            ws.receive_json()

    assert exc.value.code == 4401


def test_settings_de_producao_exigem_auth():
    """Trava a regra: fora de desenvolvimento, autenticação é obrigatória."""
    producao = Settings(
        ENVIRONMENT="production", JWT_SECRET_KEY="k" * 64, REQUIRE_AUTH=False
    )
    assert producao.require_auth is True
    assert Settings(ENVIRONMENT="development").require_auth is False
