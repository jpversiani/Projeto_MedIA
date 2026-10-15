"""Testes para a Aba de Acolhimento no Cockpit (T1 do Handoff).

Garante que o HTML, JS e o endpoint de check-in funcionem perfeitamente integrados.
"""
from datetime import date, time
from pathlib import Path

from app.models.agendamento import Agendamento, StatusAgendamento, TipoAtendimento
from app.models.cidadao import Cidadao
from app.models.fila import FilaAcolhimento

STATIC_DIR = Path(__file__).resolve().parents[1] / "app" / "static"


def test_html_possui_elementos_obrigatorios_de_acolhimento():
    """index.html deve conter o menu, a seção e os 4 IDs exigidos por fila_espera.js."""
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    assert 'id="btn-menu-acolhimento"' in html
    assert 'id="aba-acolhimento"' in html
    assert 'id="fila-espera-lista"' in html
    assert 'id="fila-espera-contador"' in html
    assert 'id="fila-espera-chamada"' in html
    assert 'id="fila-espera-atualizacao"' in html
    assert 'id="fila-espera-som"' in html
    assert "fila_espera.js" in html


def test_app_js_suporta_aba_acolhimento():
    """app.js deve registrar 'acolhimento' no array de abas e definir a função carregarAcolhimento."""
    js = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert '"acolhimento"' in js
    assert "carregarAcolhimento" in js
    assert "realizarCheckinRapido" in js


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
