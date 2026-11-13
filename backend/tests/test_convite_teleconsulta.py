"""Testes do convite assinado do paciente (Fase 2 — telemedicina plena).

Fixam o que antes não existia: o paciente entra na teleconsulta **sem conta**,
por um link que é a própria credencial — um convite assinado, amarrado a UMA
sala, com TTL e revogação. Antes o link era ``?sala=<codigo>`` puro (permanente,
sem token) e, com a autenticação ligada, o paciente nem conseguia entrar.

Propriedades de segurança verificadas:
* convite válido entra como PACIENTE;
* convite de outra sala é recusado (escopo);
* convite revogado / expirado / adulterado / desconhecido é recusado;
* convite nunca vale como access token de usuário (tipo distinto);
* finalizar a consulta revoga o convite (link morre);
* o link gerado pela API carrega o convite.
"""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import sessionmaker
from starlette.websockets import WebSocketDisconnect

from app.api.v1 import telemedicina_ws as ws_mod
from app.models.telemedicina import (
    ConviteTeleconsulta,
    SalaVirtual,
    StatusTeleconsulta,
    Teleconsulta,
)
from app.services.auth_service import decode_access_token
from app.services.convite_teleconsulta import (
    TIPO_CONVITE,
    expiracao_sala,
    gerar_convite_paciente,
    revogar_convites_da_teleconsulta,
    validar_convite,
)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------
@pytest.fixture
def consulta(db_session):
    """Sala + teleconsulta vinculadas, exclusivas destes testes."""
    sala = SalaVirtual(
        codigo_sala="sala-convite-teste", status=StatusTeleconsulta.AGENDADA
    )
    db_session.add(sala)
    db_session.commit()
    db_session.refresh(sala)
    teleconsulta = Teleconsulta(
        sala_virtual_id=sala.id, status=StatusTeleconsulta.AGENDADA
    )
    db_session.add(teleconsulta)
    db_session.commit()
    db_session.refresh(teleconsulta)

    yield {"db": db_session, "sala": sala, "teleconsulta": teleconsulta}

    db_session.query(ConviteTeleconsulta).filter(
        ConviteTeleconsulta.teleconsulta_id == teleconsulta.id
    ).delete()
    db_session.query(Teleconsulta).filter(Teleconsulta.id == teleconsulta.id).delete()
    db_session.query(SalaVirtual).filter(SalaVirtual.id == sala.id).delete()
    db_session.commit()


@pytest.fixture
def ws_protegido(db_session, monkeypatch, consulta):
    """Handler WS apontado para o banco hermético, com autenticação ligada."""
    fabrica = sessionmaker(bind=db_session.get_bind(), autocommit=False, autoflush=False)
    monkeypatch.setattr(ws_mod, "SessionLocal", fabrica)

    class _SettingsProtegidas:
        require_auth = True
        ice_servers = [{"urls": "stun:stun.l.google.com:19302"}]
        WS_SALA_MAX_PARTICIPANTES = 2
        WS_TIMEOUT_OCIOSO_SEGUNDOS = 900

    monkeypatch.setattr(ws_mod, "settings", _SettingsProtegidas())
    return consulta


def _url(codigo, token=None, papel="paciente"):
    base = f"/api/v1/ws/telemedicina/sala/{codigo}?papel={papel}"
    return f"{base}&token={token}" if token else base


def _recusa(client, url):
    """Conecta, lê o envelope de erro e devolve (mensagem, código de fechamento)."""
    with client.websocket_connect(url) as ws:
        mensagem = ws.receive_json()
        try:
            while True:
                ws.receive_json()
        except WebSocketDisconnect as erro:
            return mensagem, erro.code
    return mensagem, None


# ----------------------------------------------------------------------
# Serviço: emissão / validação / revogação
# ----------------------------------------------------------------------
def test_convite_emitido_e_valido(consulta):
    db, sala, t = consulta["db"], consulta["sala"], consulta["teleconsulta"]
    token = gerar_convite_paciente(db, t.id, sala.codigo_sala, "Paciente Teste")
    payload = validar_convite(db, token, sala.codigo_sala)
    assert payload is not None
    assert payload["papel"] == "PACIENTE"
    assert payload["sala"] == sala.codigo_sala
    assert payload["tipo"] == TIPO_CONVITE
    assert payload["nome"] == "Paciente Teste"
    # jti persistido para revogação.
    assert (
        db.query(ConviteTeleconsulta).filter_by(jti=payload["jti"]).first() is not None
    )


def test_convite_nao_vale_como_access_token(consulta):
    db, sala, t = consulta["db"], consulta["sala"], consulta["teleconsulta"]
    token = gerar_convite_paciente(db, t.id, sala.codigo_sala)
    # O tipo é distinto: um convite nunca autentica como usuário do sistema.
    assert decode_access_token(token) is None


def test_convite_de_outra_sala_e_recusado(consulta):
    db, sala, t = consulta["db"], consulta["sala"], consulta["teleconsulta"]
    token = gerar_convite_paciente(db, t.id, sala.codigo_sala)
    assert validar_convite(db, token, "sala-alheia") is None


def test_convite_revogado_e_recusado(consulta):
    db, sala, t = consulta["db"], consulta["sala"], consulta["teleconsulta"]
    token = gerar_convite_paciente(db, t.id, sala.codigo_sala)
    assert validar_convite(db, token, sala.codigo_sala) is not None
    quantidade = revogar_convites_da_teleconsulta(db, t.id)
    assert quantidade == 1
    assert validar_convite(db, token, sala.codigo_sala) is None


def test_convite_expirado_e_recusado(consulta):
    db, sala, t = consulta["db"], consulta["sala"], consulta["teleconsulta"]
    token = gerar_convite_paciente(db, t.id, sala.codigo_sala, ttl_horas=-1)
    assert validar_convite(db, token, sala.codigo_sala) is None


def test_convite_adulterado_e_recusado(consulta):
    db, sala, t = consulta["db"], consulta["sala"], consulta["teleconsulta"]
    token = gerar_convite_paciente(db, t.id, sala.codigo_sala)
    assert validar_convite(db, token + "x", sala.codigo_sala) is None


def test_expiracao_sala_usa_inicio_mais_graca():
    inicio = datetime(2026, 11, 13, 10, 0, tzinfo=timezone.utc)
    assert expiracao_sala(inicio) == inicio + timedelta(hours=24)
    # Sem início, conta a partir de agora (nunca None).
    assert expiracao_sala(None) > datetime.now(timezone.utc)


# ----------------------------------------------------------------------
# WebSocket: o paciente entra com o convite, sem conta
# ----------------------------------------------------------------------
def test_paciente_entra_com_convite(client, ws_protegido):
    db, sala, t = ws_protegido["db"], ws_protegido["sala"], ws_protegido["teleconsulta"]
    token = gerar_convite_paciente(db, t.id, sala.codigo_sala, "Paciente Sem Conta")
    with client.websocket_connect(_url(sala.codigo_sala, token)) as ws:
        mensagem = ws.receive_json()
        assert mensagem["tipo"] == "sala_ingressada"
        assert mensagem["payload"]["seu_papel"] == "paciente"


def test_sem_token_e_recusado(client, ws_protegido):
    sala = ws_protegido["sala"]
    mensagem, codigo = _recusa(client, _url(sala.codigo_sala))
    assert mensagem["tipo"] == "erro"
    assert codigo == 4401


def test_convite_de_outra_sala_e_recusado_no_ws(client, ws_protegido):
    db, sala, t = ws_protegido["db"], ws_protegido["sala"], ws_protegido["teleconsulta"]
    # Convite válido, mas para outra sala: não pode abrir esta.
    token = gerar_convite_paciente(db, t.id, "sala-alheia")
    mensagem, codigo = _recusa(client, _url(sala.codigo_sala, token))
    assert mensagem["tipo"] == "erro"
    assert codigo == 4401


def test_convite_revogado_e_recusado_no_ws(client, ws_protegido):
    db, sala, t = ws_protegido["db"], ws_protegido["sala"], ws_protegido["teleconsulta"]
    token = gerar_convite_paciente(db, t.id, sala.codigo_sala)
    revogar_convites_da_teleconsulta(db, t.id)
    mensagem, codigo = _recusa(client, _url(sala.codigo_sala, token))
    assert mensagem["tipo"] == "erro"
    assert codigo == 4401


# ----------------------------------------------------------------------
# Rotas: link carrega convite; finalizar revoga
# ----------------------------------------------------------------------
def _criar_teleconsulta_api(client):
    resp = client.post(
        "/api/v1/telemedicina/agendamentos",
        json={
            "paciente_cpf": "12345678909",
            "medico_crm": "123456",
            "data_hora": "2026-11-13T10:00:00",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_link_paciente_carrega_convite(client, db_session):
    dados = _criar_teleconsulta_api(client)
    codigo_sala = dados["codigo_sala"]
    resp = client.get(
        f"/api/v1/telemedicina/link-paciente/{codigo_sala}?paciente_nome=Fulano"
    )
    assert resp.status_code == 200
    url = resp.json()["url_acesso_paciente"]
    assert f"sala={codigo_sala}" in url
    assert "convite=" in url
    # O convite do link é válido para a sala.
    token = url.split("convite=")[1]
    assert validar_convite(db_session, token, codigo_sala) is not None


def test_finalizar_chamada_revoga_convite(client, db_session):
    dados = _criar_teleconsulta_api(client)
    codigo_sala, teleconsulta_id = dados["codigo_sala"], dados["id"]
    link = client.get(f"/api/v1/telemedicina/link-paciente/{codigo_sala}").json()
    token = link["url_acesso_paciente"].split("convite=")[1]
    assert validar_convite(db_session, token, codigo_sala) is not None

    resp = client.post(
        "/api/v1/telemedicina/finalizar-chamada",
        json={"teleconsulta_id": teleconsulta_id},
    )
    assert resp.status_code == 200
    # Depois de finalizar, o link do paciente morre (convite revogado).
    assert validar_convite(db_session, token, codigo_sala) is None


def test_agendamento_preenche_expiracao_da_sala(client, db_session):
    dados = _criar_teleconsulta_api(client)
    sala = (
        db_session.query(SalaVirtual)
        .filter(SalaVirtual.codigo_sala == dados["codigo_sala"])
        .first()
    )
    assert sala.data_expiracao is not None