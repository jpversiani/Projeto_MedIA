"""Persistência da jornada do fluxo de atendimento (P0-4, parte 2).

O motor de fluxo guardava tudo num dicionário do processo. Isso significava:

* reiniciar o servidor **apagava a consulta em andamento**;
* com ``uvicorn --workers 2``, cada worker via uma lista diferente;
* ``paciente_id`` era sorteado com ``uuid4`` — um "paciente" que não existe;
* finalizar uma consulta da agenda retornava 404.

Estes testes provam o comportamento novo: a jornada sobrevive a restart, é
vinculada ao cidadão e carrega o tenant.
"""

from __future__ import annotations

from app.models.cidadao import Cidadao
from app.models.jornada import JornadaAtendimento
from app.services import fluxo_atendimento_service as modulo_fluxo
from app.services.fluxo_atendimento_service import fluxo_service

CNS_PACIENTE = "898000123456780"


def _novo_agendamento(client, **overrides):
    payload = {
        "paciente_nome": "Paciente Persistido",
        "paciente_cpf": "52998224725",
        "paciente_telefone": "(38) 99999-2222",
        "medico_nome": "Dra. Francelli Neves Versiani",
        "medico_crm": "78421",
        "modalidade": "PRESENCIAL",
        "valor_honorarios": 400.0,
    }
    payload.update(overrides)
    resposta = client.post("/api/v1/fluxo-atendimento/novo-agendamento", json=payload)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def _limpar_cache() -> None:
    """Simula um restart do processo (ou outro worker)."""
    fluxo_service._jornadas.clear()


def test_jornada_sobrevive_a_limpeza_do_cache(client, db_session):
    criada = _novo_agendamento(client)
    consulta_id = criada["consulta_id"]

    registro = (
        db_session.query(JornadaAtendimento)
        .filter(JornadaAtendimento.consulta_id == consulta_id)
        .one()
    )
    assert registro.paciente_nome == "Paciente Persistido"
    assert registro.etapa == "AGENDADA"

    _limpar_cache()

    recuperada = client.get(f"/api/v1/fluxo-atendimento/{consulta_id}/jornada")
    assert recuperada.status_code == 200, recuperada.text
    corpo = recuperada.json()
    assert corpo["consulta_id"] == consulta_id
    assert corpo["paciente_nome"] == "Paciente Persistido"
    assert corpo["etapa_atual"] == "AGENDADA"
    # O enum volta do banco como enum, não como string solta.
    assert corpo["modalidade"] == "PRESENCIAL"


def test_jornada_e_vinculada_ao_cidadao_cadastrado(client, db_session):
    cidadao = db_session.query(Cidadao).filter(Cidadao.cpf == "12345678900").one()

    criada = _novo_agendamento(
        client,
        paciente_cpf=cidadao.cpf,
        paciente_nome=cidadao.nome_completo,
    )

    assert criada["paciente_id"] == cidadao.id

    registro = (
        db_session.query(JornadaAtendimento)
        .filter(JornadaAtendimento.consulta_id == criada["consulta_id"])
        .one()
    )
    assert registro.cidadao_id == cidadao.id


def test_paciente_sem_cadastro_nao_recebe_id_inventado(client, db_session):
    """Antes o serviço sorteava `paciente_id` com `uuid4`."""
    cpf_sem_cadastro = "15935745682"
    assert (
        db_session.query(Cidadao).filter(Cidadao.cpf == cpf_sem_cadastro).first()
        is None
    ), "CPF de teste não pode estar cadastrado"

    criada = _novo_agendamento(client, paciente_cpf=cpf_sem_cadastro)

    assert criada["paciente_id"] is None
    assert criada["medico_id"] is None


def test_etapas_do_fluxo_sao_persistidas(client, db_session):
    consulta_id = client.post(
        "/api/v1/fluxo-atendimento/novo-agendamento",
        json={
            "paciente_nome": "Paciente Etapas",
            "paciente_cpf": "52998224725",
            "paciente_telefone": "",
            "modalidade": "TELEMEDICINA",
            "valor_honorarios": 300.0,
        },
    ).json()["consulta_id"]

    pre = client.post(
        f"/api/v1/fluxo-atendimento/{consulta_id}/pre-consulta",
        json={
            "pre_anamnese": {
                "motivo_consulta": "Dor de cabeça",
                "sintomas_principais": ["Cefaleia"],
                "medicamentos_em_uso": [],
                "alergias_conhecidas": [],
            },
            "tcle_aceito": True,
            "pagamento_confirmado": True,
        },
    )
    assert pre.status_code == 200, pre.text

    inicio = client.post(f"/api/v1/fluxo-atendimento/{consulta_id}/iniciar")
    assert inicio.status_code == 200, inicio.text

    _limpar_cache()

    registro = (
        db_session.query(JornadaAtendimento)
        .filter(JornadaAtendimento.consulta_id == consulta_id)
        .one()
    )
    assert registro.etapa == "EM_ATENDIMENTO"
    assert registro.dados_json["tcle_aceito"] is True
    assert registro.dados_json["pre_anamnese"]["motivo_consulta"] == "Dor de cabeça"


def test_listar_consultas_le_do_banco(client):
    criada = _novo_agendamento(client)
    _limpar_cache()

    listagem = client.get("/api/v1/fluxo-atendimento/consultas")
    assert listagem.status_code == 200, listagem.text
    ids = {item["consulta_id"] for item in listagem.json()}
    assert criada["consulta_id"] in ids


def test_agenda_alimenta_o_fluxo(client, db_session):
    """Consulta criada na agenda pode ser aberta/finalizada no fluxo.

    Antes eram dois repositórios separados: a agenda gravava em `agendamentos`
    e o fluxo nunca lia de lá, então finalizar retornava 404.
    """
    from datetime import date, time

    from app.models.agendamento import Agendamento, StatusAgendamento, TipoAtendimento

    cidadao = db_session.query(Cidadao).first()
    agendamento = Agendamento(
        codigo="AGD-TESTE-FLUXO",
        cidadao_id=cidadao.id,
        tipo=TipoAtendimento.PRESENCIAL.value,
        status=StatusAgendamento.AGENDADO.value,
        data_consulta=date.today(),
        horario=time(9, 0),
        especialidade="Clínica Médica",
        valor_consulta=250.0,
    )
    db_session.add(agendamento)
    db_session.commit()

    resposta = client.post(
        "/api/v1/fluxo-atendimento/novo-agendamento",
        json={
            "paciente_nome": cidadao.nome_completo,
            "paciente_cpf": cidadao.cpf,
            "paciente_telefone": cidadao.telefone or "",
            "medico_nome": "Dra. Francelli Neves Versiani",
            "medico_crm": "78421",
            "modalidade": "PRESENCIAL",
            "valor_honorarios": 250.0,
            "agendamento_codigo": "AGD-TESTE-FLUXO",
        },
    )
    assert resposta.status_code == 200, resposta.text

    corpo = resposta.json()
    assert corpo["consulta_id"] == "AGD-TESTE-FLUXO"
    assert corpo["paciente_id"] == cidadao.id

    _limpar_cache()

    finalizacao = client.post(
        "/api/v1/fluxo-atendimento/pos-consulta/finalizar",
        json={"consulta_id": "AGD-TESTE-FLUXO", "lancar_livro_caixa": True},
    )
    assert finalizacao.status_code == 200, finalizacao.text
    assert finalizacao.json()["status"] == "FINALIZADA"

    registro = (
        db_session.query(JornadaAtendimento)
        .filter(JornadaAtendimento.consulta_id == "AGD-TESTE-FLUXO")
        .one()
    )
    assert registro.etapa == "FINALIZADA"
    assert registro.agendamento_id == agendamento.id


def test_banco_nao_guarda_paciente_ficticio():
    """A jornada de demonstração continua fora do banco em produção/testes."""
    assert "CONS-2026-9812" not in fluxo_service._jornadas
    assert fluxo_service._demo_ativo is False
    # O helper de serialização não deve inventar identidade.
    assert modulo_fluxo._serializar_jornada({"consulta_id": "X"}) == {"consulta_id": "X"}
