"""Testes da Agenda Médica — persistência, vínculo com o paciente e check-in.

Estes testes foram reescritos. A versão anterior usava um `TestClient` criado no
nível do módulo (ignorando as fixtures do `conftest.py`) e dependia do seed em
memória `_AGENDA_MEMORIA`, que era povoado no import do módulo. Isso significava
que a suíte podia tocar o banco de desenvolvimento e que os testes passavam por
causa de dados fictícios injetados no código, não por o fluxo funcionar.

Agora cada teste cria seus próprios dados pela API e verifica o comportamento
real: persistência no banco, vínculo com o cidadão e ligação com a fila.
"""
from datetime import date

from app.models.agendamento import Agendamento
from app.models.cidadao import Cidadao
from app.models.fila import FilaAcolhimento


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _cidadao_id(db_session) -> int:
    """Cidadão do seed criado pelo conftest."""
    cidadao = db_session.query(Cidadao).filter(Cidadao.cpf == "12345678900").first()
    assert cidadao is not None, "Cidadão de seed não encontrado"
    return cidadao.id


def _criar_agendamento(client, cidadao_id, **overrides):
    payload = {
        "cidadao_id": cidadao_id,
        "tipo": "PRESENCIAL",
        "horario": "09:00",
        "especialidade": "Clínica Médica",
        "motivo_queixa": "Consulta de rotina",
        "valor_consulta": 300.0,
    }
    payload.update(overrides)
    resposta = client.post("/api/v1/agenda/novo", json=payload)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


# ---------------------------------------------------------------------------
# 1. Listagem
# ---------------------------------------------------------------------------
def test_listar_agenda_vazia_retorna_estrutura(client, db_session):
    """Agenda sem consultas no dia devolve a estrutura, com total zero.

    Antes, este endpoint sempre devolvia ao menos 5 consultas porque o seed em
    memória era injetado no import — era impossível representar uma agenda vazia.
    """
    db_session.query(Agendamento).delete()
    db_session.commit()

    resposta = client.get("/api/v1/agenda/")
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["total"] == 0
    assert dados["consultas"] == []
    assert "data_referencia" in dados


def test_listar_agenda_com_filtro_de_tipo(client, db_session):
    db_session.query(Agendamento).delete()
    db_session.commit()
    cid = _cidadao_id(db_session)

    _criar_agendamento(client, cid, tipo="PRESENCIAL", horario="08:00")
    _criar_agendamento(client, cid, tipo="TELEMEDICINA", horario="10:00")

    todas = client.get("/api/v1/agenda/").json()
    assert todas["total"] == 2
    assert todas["total_presencial"] == 1
    assert todas["total_telemedicina"] == 1

    so_tele = client.get("/api/v1/agenda/?tipo=TELEMEDICINA").json()
    assert so_tele["total"] == 1
    assert so_tele["consultas"][0]["tipo"] == "TELEMEDICINA"
    assert so_tele["consultas"][0]["codigo_sala_telemedicina"].startswith("sala_")

    so_pres = client.get("/api/v1/agenda/?tipo=PRESENCIAL").json()
    assert so_pres["total"] == 1
    assert so_pres["consultas"][0]["codigo_sala_telemedicina"] is None


def test_agenda_ordena_por_horario(client, db_session):
    db_session.query(Agendamento).delete()
    db_session.commit()
    cid = _cidadao_id(db_session)

    for h in ["14:00", "08:30", "11:15"]:
        _criar_agendamento(client, cid, horario=h)

    horarios = [c["horario"] for c in client.get("/api/v1/agenda/").json()["consultas"]]
    assert horarios == sorted(horarios)


def test_data_invalida_retorna_422(client):
    resposta = client.get("/api/v1/agenda/?data=31-12-2026")
    assert resposta.status_code == 422


# ---------------------------------------------------------------------------
# 2. Criação — vínculo com o paciente
# ---------------------------------------------------------------------------
def test_criar_agendamento_vincula_cidadao(client, db_session):
    """O agendamento precisa apontar para um cidadão cadastrado.

    Este é o vínculo que faltava: sem `cidadao_id`, era impossível abrir o
    prontuário de quem estava na sala de espera.
    """
    cid = _cidadao_id(db_session)
    criado = _criar_agendamento(client, cid, tipo="TELEMEDICINA", horario="16:30")

    assert criado["cidadao_id"] == cid
    assert criado["codigo"].startswith("AG-")
    assert criado["status"] == "AGENDADO"
    assert criado["codigo_sala_telemedicina"].startswith("sala_")
    assert criado["paciente_nome"], "o nome do paciente deve vir do cadastro"

    no_banco = db_session.query(Agendamento).filter(Agendamento.id == criado["id"]).first()
    assert no_banco is not None
    assert no_banco.cidadao_id == cid


def test_criar_agendamento_resolve_cpf_para_cidadao(client, db_session):
    """CPF em texto livre é resolvido para o cidadão, nunca guardado solto."""
    resposta = client.post(
        "/api/v1/agenda/novo",
        json={"paciente_cpf": "123.456.789-00", "tipo": "PRESENCIAL", "horario": "09:00"},
    )
    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["cidadao_id"] == _cidadao_id(db_session)


def test_criar_agendamento_cpf_inexistente_retorna_404(client):
    resposta = client.post(
        "/api/v1/agenda/novo",
        json={"paciente_cpf": "00000000000", "tipo": "PRESENCIAL", "horario": "09:00"},
    )
    assert resposta.status_code == 404
    assert "cadastr" in resposta.json()["detail"].lower()


def test_criar_agendamento_sem_paciente_retorna_422(client):
    resposta = client.post(
        "/api/v1/agenda/novo", json={"tipo": "PRESENCIAL", "horario": "09:00"}
    )
    assert resposta.status_code == 422


def test_horario_invalido_retorna_422(client, db_session):
    cid = _cidadao_id(db_session)
    resposta = client.post(
        "/api/v1/agenda/novo",
        json={"cidadao_id": cid, "tipo": "PRESENCIAL", "horario": "25:99"},
    )
    assert resposta.status_code == 422
    assert "hor" in resposta.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 3. Status
# ---------------------------------------------------------------------------
def test_atualizar_status_por_codigo(client, db_session):
    db_session.query(Agendamento).delete()
    db_session.commit()
    criado = _criar_agendamento(client, _cidadao_id(db_session))

    resposta = client.patch(f"/api/v1/agenda/{criado['codigo']}/status?novo_status=EM_CONSULTA")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "EM_CONSULTA"


def test_atualizar_status_por_id(client, db_session):
    db_session.query(Agendamento).delete()
    db_session.commit()
    criado = _criar_agendamento(client, _cidadao_id(db_session))

    resposta = client.patch(f"/api/v1/agenda/{criado['id']}/status?novo_status=CONCLUIDO")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "CONCLUIDO"


def test_status_invalido_retorna_422(client, db_session):
    criado = _criar_agendamento(client, _cidadao_id(db_session))
    resposta = client.patch(f"/api/v1/agenda/{criado['codigo']}/status?novo_status=INVENTADO")
    assert resposta.status_code == 422


def test_agendamento_inexistente_retorna_404(client):
    resposta = client.patch("/api/v1/agenda/AG-NAOEXISTE/status?novo_status=EM_CONSULTA")
    assert resposta.status_code == 404


# ---------------------------------------------------------------------------
# 4. Check-in — liga a agenda à fila de acolhimento
# ---------------------------------------------------------------------------
def test_checkin_coloca_paciente_na_fila(client, db_session):
    """O check-in é o elo que faltava entre agendar e atender.

    Sem ele, o paciente agendado nunca chegava à fila e o médico não tinha como
    chamá-lo.
    """
    db_session.query(Agendamento).delete()
    db_session.query(FilaAcolhimento).delete()
    db_session.commit()
    cid = _cidadao_id(db_session)
    criado = _criar_agendamento(client, cid, tipo="PRESENCIAL")

    resposta = client.post(f"/api/v1/agenda/{criado['codigo']}/checkin?classificacao_risco=AMARELO")
    assert resposta.status_code == 201, resposta.text
    dados = resposta.json()

    assert dados["agendamento_id"] == criado["id"]
    assert dados["cidadao_id"] == cid
    assert dados["status_agendamento"] == "SALA_DE_ESPERA"

    entrada = db_session.query(FilaAcolhimento).filter(FilaAcolhimento.id == dados["fila_id"]).first()
    assert entrada is not None
    assert entrada.cidadao_id == cid
    assert entrada.classificacao_risco == "AMARELO"
    assert entrada.tipo_demanda == "AGENDADA"

    # O paciente aparece na fila de espera
    fila = client.get("/api/v1/fila/?status=AGUARDANDO_ATENDIMENTO").json()
    assert any(item["cidadao_id"] == cid for item in fila)


def test_checkin_e_idempotente(client, db_session):
    """Repetir o check-in não duplica o paciente na fila."""
    db_session.query(Agendamento).delete()
    db_session.query(FilaAcolhimento).delete()
    db_session.commit()
    criado = _criar_agendamento(client, _cidadao_id(db_session))

    primeiro = client.post(f"/api/v1/agenda/{criado['codigo']}/checkin")
    segundo = client.post(f"/api/v1/agenda/{criado['codigo']}/checkin")

    assert primeiro.status_code == 201
    assert segundo.status_code == 201
    assert primeiro.json()["fila_id"] == segundo.json()["fila_id"]
    assert db_session.query(FilaAcolhimento).count() == 1


def test_checkin_de_agendamento_cancelado_e_recusado(client, db_session):
    db_session.query(Agendamento).delete()
    db_session.commit()
    criado = _criar_agendamento(client, _cidadao_id(db_session))
    client.patch(f"/api/v1/agenda/{criado['codigo']}/status?novo_status=CANCELADO")

    resposta = client.post(f"/api/v1/agenda/{criado['codigo']}/checkin")
    assert resposta.status_code == 409


def test_checkin_com_risco_invalido_retorna_422(client, db_session):
    criado = _criar_agendamento(client, _cidadao_id(db_session))
    resposta = client.post(f"/api/v1/agenda/{criado['codigo']}/checkin?classificacao_risco=ROXO")
    assert resposta.status_code == 422


# ---------------------------------------------------------------------------
# 5. Histórico por paciente
# ---------------------------------------------------------------------------
def test_historico_de_agendamentos_do_cidadao(client, db_session):
    """Consulta só possível porque o agendamento passou a ter `cidadao_id`."""
    db_session.query(Agendamento).delete()
    db_session.commit()
    cid = _cidadao_id(db_session)

    _criar_agendamento(client, cid, horario="08:00")
    _criar_agendamento(client, cid, horario="09:00")

    resposta = client.get(f"/api/v1/agenda/cidadao/{cid}")
    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_historico_de_cidadao_inexistente_retorna_404(client):
    resposta = client.get("/api/v1/agenda/cidadao/999999")
    assert resposta.status_code == 404


# ---------------------------------------------------------------------------
# 6. Persistência
# ---------------------------------------------------------------------------
def test_agendamento_sobrevive_a_nova_sessao(client, db_session):
    """O agendamento está no banco, não em memória.

    Antes, a agenda era um dicionário de módulo: reiniciar o processo apagava
    tudo. Este teste verifica que o registro é durável e legível por outra
    sessão do banco.
    """
    db_session.query(Agendamento).delete()
    db_session.commit()
    criado = _criar_agendamento(client, _cidadao_id(db_session))
    codigo = criado["codigo"]

    # Sessão nova, como faria outro worker do uvicorn.
    db_session.expire_all()
    do_banco = db_session.query(Agendamento).filter(Agendamento.codigo == codigo).first()
    assert do_banco is not None, "agendamento não persistiu"
    assert do_banco.data_consulta == date.today()
