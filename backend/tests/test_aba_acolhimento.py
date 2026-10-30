"""Testes do check-in da agenda para a fila de acolhimento.

Contexto do merge: o branch T4 trazia uma implementação alternativa da aba de
acolhimento (``static/js/fila_espera.js``, 21 KB) que duplicava a que o main já
usa (``app.js#carregarAcolhimento`` + a seção ``#aba-acolhimento`` do
``index.html``). Duas implementações concorrentes renderizariam a mesma fila
duas vezes, então a do main foi mantida e a alternativa não foi adotada.

Os testes de UI que exigiam a implementação descartada foram removidos; o
contrato de backend que a tela usa (check-in -> fila) continua verificado aqui.
Pendência registrada: decidir se a aba ganha o controle de som/alerta sonoro do
T4 (exige teste em navegador, que a suíte não tem).
"""
from datetime import date, time

from app.models.agendamento import Agendamento, StatusAgendamento, TipoAtendimento
from app.models.cidadao import Cidadao
from app.models.fila import FilaAcolhimento


def test_fluxo_checkin_agenda_na_fila(client, db_session):
    """Testa o endpoint de check-in que o botão da tela de acolhimento aciona."""
    # Cria cidadão exclusivo
    cidadao = Cidadao(
        nome_completo="Cidadão Teste Acolhimento",
        cpf="99988877766",
        cns="700000000000099",
        data_nascimento=date(1990, 1, 1),
        sexo="M",
    )
    db_session.add(cidadao)
    db_session.commit()
    db_session.refresh(cidadao)

    # Cria agendamento
    agendamento = Agendamento(
        codigo="AG-TESTE-001",
        cidadao_id=cidadao.id,
        tipo=TipoAtendimento.PRESENCIAL,
        status=StatusAgendamento.AGENDADO,
        estabelecimento_id=1,
        data_consulta=date.today(),
        horario=time(10, 0),
    )
    db_session.add(agendamento)
    db_session.commit()
    db_session.refresh(agendamento)

    # Executa check-in com risco AMARELO
    res = client.post(
        f"/api/v1/agenda/{agendamento.id}/checkin?classificacao_risco=AMARELO&motivo_acolhimento=Febre"
    )
    assert res.status_code == 201
    dados = res.json()
    assert dados["agendamento_id"] == agendamento.id
    assert dados["status_agendamento"] == "SALA_DE_ESPERA"

    # Confirma que o cidadão está na fila
    fila_item = db_session.query(FilaAcolhimento).filter_by(id=dados["fila_id"]).first()
    assert fila_item is not None
    assert fila_item.classificacao_risco == "AMARELO"
    assert fila_item.status == "AGUARDANDO_ATENDIMENTO"
