"""Testes da trilha de auditoria (LGPD Art. 11 / CFM 2.314/2022).

Cobrem três falhas que existiam antes:

1. o hash encadeado **não cobria** IP, User-Agent e detalhes — esses campos
   podiam ser alterados no banco sem quebrar a "prova criptográfica";
2. não havia como **verificar** a corrente (auditar a auditoria);
3. a leitura de prontuário **não gerava evento** algum.
"""

import pytest

from app.core.config import settings
from app.models.estabelecimento import Estabelecimento
from app.models.usuario import PapelUsuarioEnum, Usuario, VinculoClinica
from app.services.audit_service import AuditService, calcular_hash_auditoria
from app.services.auth_service import create_access_token


@pytest.fixture
def rbac_ligado(monkeypatch):
    from app.core import rbac

    class _SettingsProtegidas:
        require_auth = True

    monkeypatch.setattr(rbac, "settings", _SettingsProtegidas())
    yield


@pytest.fixture
def medico_token(db_session):
    estabelecimento = db_session.query(Estabelecimento).order_by(Estabelecimento.id).first()
    usuario = Usuario(
        email="auditoria.medico@teste.local",
        nome="Médico Auditoria",
        is_active=True,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)

    vinculo = VinculoClinica(
        usuario_id=usuario.id,
        estabelecimento_id=estabelecimento.id,
        papel=PapelUsuarioEnum.MEDICO,
        is_default=True,
    )
    db_session.add(vinculo)
    db_session.commit()

    token = create_access_token(usuario, vinculo)
    try:
        yield token, usuario, estabelecimento
    finally:
        db_session.rollback()
        db_session.query(VinculoClinica).filter(VinculoClinica.usuario_id == usuario.id).delete()
        db_session.query(Usuario).filter(Usuario.id == usuario.id).delete()
        db_session.commit()


def _h(token):
    return {"Authorization": f"Bearer {token}"}


# ----------------------------------------------------------------------
# 1. O hash protege os campos que antes ficavam de fora
# ----------------------------------------------------------------------
def test_hash_muda_quando_ip_muda():
    base = dict(
        usuario_id=1,
        estabelecimento_id=1,
        acao="ACESSAR_PRONTUARIO",
        recurso_tipo="Cidadao",
        recurso_id="7",
        timestamp=__import__("datetime").datetime(2026, 1, 1, 12, 0, 0),
        hash_anterior=None,
    )
    h1 = calcular_hash_auditoria(**base, ip_address="10.0.0.1")
    h2 = calcular_hash_auditoria(**base, ip_address="10.0.0.2")
    assert h1 != h2


def test_hash_muda_quando_detalhes_mudam():
    base = dict(
        usuario_id=1,
        estabelecimento_id=1,
        acao="ACESSAR_PRONTUARIO",
        recurso_tipo="Cidadao",
        recurso_id="7",
        timestamp=__import__("datetime").datetime(2026, 1, 1, 12, 0, 0),
        hash_anterior=None,
    )
    assert calcular_hash_auditoria(**base, detalhes_json='{"cns": "1"}') != calcular_hash_auditoria(
        **base, detalhes_json='{"cns": "2"}'
    )


def test_formato_legado_continua_verificavel():
    """Eventos gravados antes da correção precisam seguir verificáveis."""
    from datetime import datetime

    legado = calcular_hash_auditoria(
        usuario_id=1,
        estabelecimento_id=1,
        acao="LOGIN_SUCESSO",
        recurso_tipo="Usuario",
        recurso_id="1",
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
        hash_anterior=None,
        formato="legado",
    )
    canonico = calcular_hash_auditoria(
        usuario_id=1,
        estabelecimento_id=1,
        acao="LOGIN_SUCESSO",
        recurso_tipo="Usuario",
        recurso_id="1",
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
        hash_anterior=None,
        formato="canonico",
    )
    assert legado != canonico


# ----------------------------------------------------------------------
# 2. Verificação da corrente
# ----------------------------------------------------------------------
def test_cadeia_valida_apos_eventos(db_session):
    AuditService.registrar_evento(
        db_session, acao="TESTE_CADEIA", recurso_tipo="Teste", recurso_id="1",
        ip_address="10.0.0.1", user_agent="pytest", detalhes={"n": 1},
    )
    AuditService.registrar_evento(
        db_session, acao="TESTE_CADEIA", recurso_tipo="Teste", recurso_id="2",
        ip_address="10.0.0.2", detalhes={"n": 2},
    )
    ok, elo = AuditService.verificar_cadeia(db_session)
    assert ok is True, f"corrente quebrada no elo {elo}"


def test_verificacao_detecta_adulteracao_de_detalhes(db_session):
    registro = AuditService.registrar_evento(
        db_session, acao="TESTE_ADULTERACAO", recurso_tipo="Teste", recurso_id="9",
        detalhes={"valor": "original"},
    )
    original = registro.detalhes_json
    try:
        registro.detalhes_json = '{"valor": "adulterado"}'
        db_session.commit()

        ok, elo = AuditService.verificar_cadeia(db_session)
        assert ok is False
        assert elo == registro.id
    finally:
        registro.detalhes_json = original
        db_session.commit()


def test_verificacao_detecta_quebra_de_encadeamento(db_session):
    registro = AuditService.registrar_evento(
        db_session, acao="TESTE_ELO", recurso_tipo="Teste", recurso_id="10",
    )
    original = registro.hash_anterior
    try:
        registro.hash_anterior = "f" * 64
        db_session.commit()

        ok, elo = AuditService.verificar_cadeia(db_session)
        assert ok is False
        assert elo == registro.id
    finally:
        registro.hash_anterior = original
        db_session.commit()


# ----------------------------------------------------------------------
# 3. Leitura de prontuário gera evento auditável
# ----------------------------------------------------------------------
def test_leitura_de_prontuario_gera_evento(rbac_ligado, client, db_session, medico_token):
    token, usuario, estabelecimento = medico_token
    from app.models.usuario import AuditTrail

    antes = (
        db_session.query(AuditTrail)
        .filter(AuditTrail.acao == "ACESSAR_PRONTUARIO")
        .count()
    )

    resp = client.get("/api/v1/prontuario/898000123456789", headers=_h(token))
    assert resp.status_code == 200, resp.text

    eventos = (
        db_session.query(AuditTrail)
        .filter(
            AuditTrail.acao == "ACESSAR_PRONTUARIO",
            AuditTrail.usuario_id == usuario.id,
        )
        .all()
    )
    assert len(eventos) == antes + 1
    evento = eventos[-1]
    assert evento.estabelecimento_id == estabelecimento.id
    assert evento.ip_address is not None
    assert evento.detalhes_json is not None
    assert "898000123456789" in evento.detalhes_json
