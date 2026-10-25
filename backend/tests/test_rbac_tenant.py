"""Testes de autorização por papel (RBAC) e de isolamento entre clínicas.

Antes destas mudanças a API exigia apenas *autenticação*: qualquer usuário
autenticado — inclusive uma recepcionista ou um paciente — podia ler
prontuário, emitir receita, exportar TISS e listar a fila de OUTRA unidade.

Os testes ligam ``settings.REQUIRE_AUTH`` (o mesmo interruptor que governa a
autenticação em produção) e exercitam o RBAC de ponta a ponta, com tokens
reais emitidos por ``create_access_token``.
"""

from datetime import date, time

import pytest

from app.core.config import settings
from app.models.agendamento import Agendamento, StatusAgendamento, TipoAtendimento
from app.models.estabelecimento import Estabelecimento
from app.models.fila import FilaAcolhimento
from app.models.usuario import PapelUsuarioEnum, Usuario, VinculoClinica
from app.services.auth_service import create_access_token


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------
@pytest.fixture
def rbac_ligado(monkeypatch):
    """Liga a autorização exatamente como em produção.

    ``Settings`` é um modelo pydantic *frozen* (não aceita atribuição), então o
    interruptor é trocado no objeto de configuração lido pelo módulo de RBAC —
    que só consulta ``require_auth``.
    """
    from app.core import rbac

    class _SettingsProtegidas:
        require_auth = True

    monkeypatch.setattr(rbac, "settings", _SettingsProtegidas())
    yield


@pytest.fixture
def cenario(db_session):
    """Duas unidades + tokens de papéis diferentes, com limpeza ao final."""
    principal = db_session.query(Estabelecimento).order_by(Estabelecimento.id).first()
    assert principal is not None, "o seed da suíte precisa criar uma unidade"

    outra = Estabelecimento(
        cnes="8888888",
        nome_fantasia="Unidade Teste RBAC (segundo tenant)",
        municipio_ibge=principal.municipio_ibge,
    )
    db_session.add(outra)
    db_session.commit()
    db_session.refresh(outra)

    usuarios_criados = []
    filas_criadas = []

    def _token(papel: PapelUsuarioEnum, estabelecimento_id, *, superusuario=False, com_vinculo=True):
        usuario = Usuario(
            email=f"rbac.{papel.value.lower()}.{estabelecimento_id}.{len(usuarios_criados)}@teste.local",
            nome=f"Usuário Teste {papel.value}",
            is_active=True,
            is_superuser=superusuario,
        )
        db_session.add(usuario)
        db_session.commit()
        db_session.refresh(usuario)
        usuarios_criados.append(usuario)

        vinculo = None
        if com_vinculo:
            vinculo = VinculoClinica(
                usuario_id=usuario.id,
                estabelecimento_id=estabelecimento_id,
                papel=papel,
                is_default=True,
            )
            db_session.add(vinculo)
            db_session.commit()
            db_session.refresh(vinculo)
        return create_access_token(usuario, vinculo)

    def _item_fila(estabelecimento_id, risco="VERDE", cidadao_id=1):
        item = FilaAcolhimento(
            cidadao_id=cidadao_id,
            estabelecimento_id=estabelecimento_id,
            classificacao_risco=risco,
            status="AGUARDANDO_ATENDIMENTO",
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        filas_criadas.append(item)
        return item

    agendamentos_criados = []

    def _agendamento(estabelecimento_id, *, codigo):
        agendamento = Agendamento(
            codigo=codigo,
            cidadao_id=1,
            estabelecimento_id=estabelecimento_id,
            tipo=TipoAtendimento.PRESENCIAL.value,
            status=StatusAgendamento.AGENDADO.value,
            data_consulta=date.today(),
            horario=time(9, 0),
        )
        db_session.add(agendamento)
        db_session.commit()
        db_session.refresh(agendamento)
        agendamentos_criados.append(agendamento)
        return agendamento

    class Cenario:
        pass

    ctx = Cenario()
    ctx.principal = principal
    ctx.outra = outra
    ctx.token = _token
    ctx.item_fila = _item_fila
    ctx.agendamento = _agendamento

    try:
        yield ctx
    finally:
        from app.models.usuario import AuditTrail

        for agendamento in agendamentos_criados:
            db_session.query(Agendamento).filter(Agendamento.id == agendamento.id).delete()
        for item in filas_criadas:
            db_session.query(FilaAcolhimento).filter(FilaAcolhimento.id == item.id).delete()
        db_session.query(AuditTrail).filter(AuditTrail.usuario_id.in_([u.id for u in usuarios_criados])).delete(
            synchronize_session=False
        )
        for usuario in usuarios_criados:
            db_session.query(VinculoClinica).filter(VinculoClinica.usuario_id == usuario.id).delete()
            db_session.query(Usuario).filter(Usuario.id == usuario.id).delete()
        db_session.query(Estabelecimento).filter(Estabelecimento.id == outra.id).delete()
        db_session.commit()


def _h(token):
    return {"Authorization": f"Bearer {token}"}


PRONTUARIO_URL = "/api/v1/prontuario/898000123456789"


# ----------------------------------------------------------------------
# 1. Autenticação continua obrigatória
# ----------------------------------------------------------------------
def test_rota_clinica_sem_token_responde_401(rbac_ligado, client):
    for url in ("/api/v1/cidadaos/", "/api/v1/fila/", "/api/v1/analytics/kpis"):
        assert client.get(url).status_code == 401, url


# ----------------------------------------------------------------------
# 2. RBAC por papel
# ----------------------------------------------------------------------
def test_recepcao_nao_acessa_prontuario(rbac_ligado, client, cenario):
    """Recepcionista não lê prontuário (dado clínico sensível)."""
    token = cenario.token(PapelUsuarioEnum.RECEPCAO, cenario.principal.id)
    resp = client.get(PRONTUARIO_URL, headers=_h(token))
    assert resp.status_code == 403, resp.text
    assert "MEDICO" in resp.text


def test_medico_acessa_prontuario(rbac_ligado, client, cenario):
    token = cenario.token(PapelUsuarioEnum.MEDICO, cenario.principal.id)
    resp = client.get(PRONTUARIO_URL, headers=_h(token))
    assert resp.status_code != 403, resp.text


def test_recepcao_pode_listar_cidadaos(rbac_ligado, client, cenario):
    """A recepção precisa do cadastro para agendar e fazer check-in."""
    token = cenario.token(PapelUsuarioEnum.RECEPCAO, cenario.principal.id)
    resp = client.get("/api/v1/cidadaos/", headers=_h(token))
    assert resp.status_code == 200, resp.text


def test_recepcao_nao_acessa_indicadores(rbac_ligado, client, cenario):
    token = cenario.token(PapelUsuarioEnum.RECEPCAO, cenario.principal.id)
    assert client.get("/api/v1/analytics/kpis", headers=_h(token)).status_code == 403


def test_recepcao_pode_consultar_terminologias(rbac_ligado, client, cenario):
    token = cenario.token(PapelUsuarioEnum.RECEPCAO, cenario.principal.id)
    assert client.get("/api/v1/terminologias/cid10", headers=_h(token)).status_code == 200


def test_farmaceutico_nao_acessa_prontuario_mas_acessa_farmacia(rbac_ligado, client, cenario):
    token = cenario.token(PapelUsuarioEnum.FARMACEUTICO, cenario.principal.id)
    assert client.get(PRONTUARIO_URL, headers=_h(token)).status_code == 403
    resp = client.post("/api/v1/farmacia/dispensacao/consultar", json={}, headers=_h(token))
    assert resp.status_code != 403, resp.text


def test_paciente_nao_acessa_area_clinica(rbac_ligado, client, cenario):
    token = cenario.token(PapelUsuarioEnum.PACIENTE, cenario.principal.id)
    assert client.get(PRONTUARIO_URL, headers=_h(token)).status_code == 403
    assert client.get("/api/v1/cidadaos/", headers=_h(token)).status_code == 403


# ----------------------------------------------------------------------
# 3. Isolamento entre tenants
# ----------------------------------------------------------------------
def test_fila_nao_vaza_entre_unidades(rbac_ligado, client, cenario):
    """A fila de uma unidade não aparece para o usuário de outra."""
    da_principal = cenario.item_fila(cenario.principal.id, risco="VERMELHO")
    da_outra = cenario.item_fila(cenario.outra.id, risco="VERMELHO")

    token = cenario.token(PapelUsuarioEnum.MEDICO, cenario.principal.id)
    resp = client.get("/api/v1/fila/?status=TODOS", headers=_h(token))
    assert resp.status_code == 200, resp.text

    ids = {item["id"] for item in resp.json()}
    assert da_principal.id in ids
    assert da_outra.id not in ids


def test_fila_bloqueia_escrita_cruzada(rbac_ligado, client, cenario):
    """Não se acolhe paciente na unidade do vizinho."""
    token = cenario.token(PapelUsuarioEnum.MEDICO, cenario.principal.id)
    resp = client.post(
        "/api/v1/fila/",
        json={"cidadao_id": 1, "estabelecimento_id": cenario.outra.id, "classificacao_risco": "VERDE"},
        headers=_h(token),
    )
    assert resp.status_code == 403, resp.text


def test_fila_bloqueia_leitura_de_item_de_outra_unidade(rbac_ligado, client, cenario):
    item = cenario.item_fila(cenario.outra.id)
    token = cenario.token(PapelUsuarioEnum.MEDICO, cenario.principal.id)
    assert client.get(f"/api/v1/fila/{item.id}", headers=_h(token)).status_code == 403


def test_superusuario_ve_todas_as_unidades(rbac_ligado, client, cenario):
    da_principal = cenario.item_fila(cenario.principal.id, risco="AZUL")
    da_outra = cenario.item_fila(cenario.outra.id, risco="AZUL")

    token = cenario.token(
        PapelUsuarioEnum.ADMIN, cenario.principal.id, superusuario=True
    )
    resp = client.get("/api/v1/fila/?status=TODOS", headers=_h(token))
    assert resp.status_code == 200, resp.text
    ids = {item["id"] for item in resp.json()}
    assert {da_principal.id, da_outra.id}.issubset(ids)


def test_token_sem_clinica_ativa_e_recusado(rbac_ligado, client, cenario):
    """Sem clínica ativa não há como aplicar escopo de tenant."""
    token = cenario.token(PapelUsuarioEnum.MEDICO, cenario.principal.id, com_vinculo=False)
    resp = client.get("/api/v1/fila/", headers=_h(token))
    assert resp.status_code == 400, resp.text


def test_agenda_nao_vaza_entre_unidades(rbac_ligado, client, cenario):
    """A agenda do dia de uma unidade não aparece para a outra."""
    da_principal = cenario.agendamento(cenario.principal.id, codigo="AG-TEST1")
    da_outra = cenario.agendamento(cenario.outra.id, codigo="AG-TEST2")

    token = cenario.token(PapelUsuarioEnum.MEDICO, cenario.principal.id)
    resp = client.get("/api/v1/agenda/", headers=_h(token))
    assert resp.status_code == 200, resp.text

    codigos = {c["codigo"] for c in resp.json()["consultas"]}
    assert da_principal.codigo in codigos
    assert da_outra.codigo not in codigos


def test_agenda_bloqueia_agendamento_em_outra_unidade(rbac_ligado, client, cenario):
    token = cenario.token(PapelUsuarioEnum.MEDICO, cenario.principal.id)
    resp = client.post(
        "/api/v1/agenda/novo",
        json={
            "cidadao_id": 1,
            "estabelecimento_id": cenario.outra.id,
            "data_consulta": date.today().isoformat(),
            "horario": "10:00",
        },
        headers=_h(token),
    )
    assert resp.status_code == 403, resp.text


def test_token_de_clinica_sem_vinculo_e_recusado(rbac_ligado, client, cenario, db_session):
    """Token aponta para unidade onde o usuário não tem vínculo."""
    from app.core.rbac import get_contexto_clinico  # noqa: F401  (documenta a origem do 403)

    token = cenario.token(PapelUsuarioEnum.MEDICO, cenario.principal.id)
    # Remove o vínculo do usuário: o token continua válido, mas o vínculo não.
    from app.services.auth_service import decode_access_token

    payload = decode_access_token(token)
    db_session.query(VinculoClinica).filter(
        VinculoClinica.usuario_id == int(payload["sub"])
    ).delete()
    db_session.commit()

    assert client.get("/api/v1/fila/", headers=_h(token)).status_code == 403
