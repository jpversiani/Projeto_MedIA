"""Livro caixa persistido (P0-6).

O demonstrativo financeiro devolvia dados *hardcoded* — cinco consultas e três
despesas, com nomes e CPFs de pacientes fictícios e um faturamento que nunca
existiu. Além de inútil para trabalhar, era risco de LGPD (dados inventados de
titulares) e de compliance fiscal (o livro caixa é documento escritural).

Estes testes provam que os números vêm do banco, que competências são
respeitadas e que reenvio não duplica receita.
"""

from __future__ import annotations

from datetime import date

from app.models.financeiro import LancamentoLivroCaixa, TipoLancamento


def _receita(**overrides) -> dict:
    dados = {
        "tipo": "RECEITA",
        "data_competencia": "1990-04-10",
        "descricao": "Consulta presencial",
        "valor": 350.0,
        "paciente_nome": "Paciente Real Um",
        "paciente_cpf": "12345678900",
        "modalidade": "PRESENCIAL",
        "numero_recibo": "REC-100",
        "metodo_pagamento": "PIX",
    }
    dados.update(overrides)
    return dados


def _despesa(**overrides) -> dict:
    dados = {
        "tipo": "DESPESA",
        "data_competencia": "1990-04-05",
        "descricao": "Internet do consultório",
        "valor": 200.0,
        "categoria": "TELECOMUNICACOES",
        "dedutivel": True,
    }
    dados.update(overrides)
    return dados


def _criar(client, payload: dict) -> dict:
    resposta = client.post("/api/v1/financeiro-medico/lancamentos", json=payload)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def _demonstrativo(client, mes_ano: str) -> dict:
    resposta = client.get(
        f"/api/v1/financeiro-medico/livro-caixa/demonstrativo?mes_ano={mes_ano}"
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def test_demonstrativo_reflete_os_lancamentos_persistidos(client, db_session):
    _criar(client, _receita(valor=350.0))
    _criar(
        client,
        _receita(
            valor=450.0,
            modalidade="TELEMEDICINA",
            paciente_nome="Paciente Dois",
            paciente_cpf=None,
            numero_recibo="REC-101",
        ),
    )
    _criar(client, _despesa(valor=200.0))
    _criar(
        client,
        _despesa(
            valor=100.0,
            descricao="Curso não dedutível",
            categoria="OUTROS",
            dedutivel=False,
        ),
    )

    data = _demonstrativo(client, "04/1990")

    assert data["receitas"]["total_bruto"] == 800.0
    assert data["receitas"]["consultorio_presencial"] == 350.0
    assert data["receitas"]["home_office_telemedicina"] == 450.0
    assert data["receitas"]["quantidade_consultas"] == 2
    assert data["receitas"]["percentual_telemedicina"] == 56.2

    assert data["despesas"]["total_despesas"] == 300.0
    assert data["despesas"]["dedutiveis_carne_leao"] == 200.0
    assert data["despesas"]["nao_dedutiveis"] == 100.0

    assert data["apuracao_fiscal"]["base_carne_leao"] == 600.0
    assert data["apuracao_fiscal"]["codigo_darf"] == "0190"
    assert data["apuracao_fiscal"]["imposto_a_recolher_darf"] == 0.0

    assert data["cobertura"]["quantidade_lancamentos"] == 4
    assert data["cobertura"]["possui_lancamentos"] is True

    lancamentos_da_competencia = (
        db_session.query(LancamentoLivroCaixa)
        .filter(
            LancamentoLivroCaixa.data_competencia >= date(1990, 4, 1),
            LancamentoLivroCaixa.data_competencia < date(1990, 5, 1),
        )
        .count()
    )
    assert lancamentos_da_competencia == 4


def test_competencia_separa_meses(client):
    _criar(client, _receita(data_competencia="1990-05-10", valor=999.0))

    maio = _demonstrativo(client, "05/1990")
    junho = _demonstrativo(client, "06/1990")

    assert maio["receitas"]["total_bruto"] == 999.0
    assert junho["receitas"]["total_bruto"] == 0.0
    assert junho["cobertura"]["possui_lancamentos"] is False


def test_sem_lancamentos_o_demonstrativo_e_zerado_e_explicito(client):
    data = _demonstrativo(client, "07/1991")

    assert data["receitas"] == {
        "total_bruto": 0.0,
        "consultorio_presencial": 0.0,
        "home_office_telemedicina": 0.0,
        "quantidade_consultas": 0,
        "percentual_telemedicina": 0.0,
    }
    assert data["despesas"]["total_despesas"] == 0.0
    assert data["apuracao_fiscal"]["imposto_a_recolher_darf"] == 0.0
    assert data["resultado_liquido_medico"] == 0.0
    assert data["cobertura"]["quantidade_lancamentos"] == 0


def test_listagem_de_lancamentos_da_competencia(client):
    receita = _criar(client, _receita(data_competencia="1990-08-10"))
    _criar(client, _despesa(data_competencia="1990-08-05"))

    resposta = client.get(
        "/api/v1/financeiro-medico/lancamentos?mes_ano=08/1990&tipo=RECEITA"
    )
    assert resposta.status_code == 200, resposta.text
    dados = resposta.json()

    assert len(dados) == 1
    assert dados[0]["id"] == receita["id"]
    assert dados[0]["tipo"] == "RECEITA"
    assert dados[0]["origem"] == "MANUAL"


def test_chave_de_idempotencia_nao_duplica_receita(client, db_session):
    payload = _receita(chave_idempotencia="consulta:CONS-TESTE-1")

    primeiro = _criar(client, payload)
    segundo = _criar(client, payload)

    assert primeiro["id"] == segundo["id"]
    assert (
        db_session.query(LancamentoLivroCaixa)
        .filter(LancamentoLivroCaixa.chave_idempotencia == "consulta:CONS-TESTE-1")
        .count()
        == 1
    )


def test_receita_exige_paciente_e_modalidade(client):
    sem_paciente = client.post(
        "/api/v1/financeiro-medico/lancamentos",
        json=_receita(paciente_nome=None),
    )
    sem_modalidade = client.post(
        "/api/v1/financeiro-medico/lancamentos",
        json=_receita(modalidade=None),
    )

    assert sem_paciente.status_code == 422
    assert "paciente" in sem_paciente.json()["detail"].lower()
    assert sem_modalidade.status_code == 422
    assert "modalidade" in sem_modalidade.json()["detail"].lower()


def test_despesa_exige_categoria(client):
    resposta = client.post(
        "/api/v1/financeiro-medico/lancamentos",
        json=_despesa(categoria=None),
    )
    assert resposta.status_code == 422
    assert "categoria" in resposta.json()["detail"].lower()


def test_competencia_invalida_retorna_422(client):
    for invalida in ("13/2026", "2026", "abc/def", "00/2026"):
        resposta = client.get(
            f"/api/v1/financeiro-medico/livro-caixa/demonstrativo?mes_ano={invalida}"
        )
        assert resposta.status_code == 422, (invalida, resposta.text)


def test_valor_nao_positivo_e_recusado(client):
    resposta = client.post(
        "/api/v1/financeiro-medico/lancamentos",
        json=_receita(valor=0),
    )
    assert resposta.status_code == 422


# ---------------------------------------------------------------------------
# Integração com a finalização da consulta + guarda do frontend
# ---------------------------------------------------------------------------


def test_finalizar_consulta_escritura_honorario_no_livro_caixa(client, db_session):
    from datetime import datetime

    from app.services.fluxo_atendimento_service import fluxo_service

    consulta = client.post(
        "/api/v1/fluxo-atendimento/novo-agendamento",
        json={
            "paciente_nome": "Paciente do Livro Caixa",
            "paciente_cpf": "52998224725",
            "paciente_telefone": "(38) 99999-1111",
            "medico_id": 1,
            "medico_nome": "Dra. Francelli Neves Versiani",
            "medico_crm": "78421",
            "modalidade": "TELEMEDICINA",
            "data_hora": datetime.now().isoformat(timespec="minutes"),
            "valor_honorarios": 600.0,
        },
    )
    assert consulta.status_code == 200, consulta.text
    consulta_id = consulta.json()["consulta_id"]

    pacote = client.post(
        "/api/v1/fluxo-atendimento/pos-consulta/finalizar",
        json={
            "consulta_id": consulta_id,
            "emitir_recibo_dmed": True,
            "lancar_livro_caixa": True,
        },
    )
    assert pacote.status_code == 200, pacote.text
    livro_caixa_id = pacote.json()["livro_caixa_id"]
    assert livro_caixa_id and livro_caixa_id.startswith("LC-")

    registros = (
        db_session.query(LancamentoLivroCaixa)
        .filter(
            LancamentoLivroCaixa.chave_idempotencia == f"consulta:{consulta_id}"
        )
        .all()
    )
    assert len(registros) == 1
    assert float(registros[0].valor) == 600.0
    assert registros[0].origem == "FLUXO_ATENDIMENTO"
    assert registros[0].modalidade == "TELEMEDICINA"

    # O DARF informado é o do mês (real), não 15% inventados sobre a consulta.
    assert pacote.json()["darf_carnê_leão_prevista"] >= 0

    fluxo_service._jornadas.pop(consulta_id, None)


def test_frontend_nao_exibe_lancamentos_ficticios():
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[1]
    app_js = (raiz / "app" / "static" / "app.js").read_text(encoding="utf-8")

    # Recorte do bloco de honorários (outras abas têm sua própria guarda).
    inicio = app_js.index("// Lançamentos do livro caixa carregados da API")
    fim = app_js.index("function abrirModalReciboDMED", inicio)
    bloco = app_js[inicio:fim]

    # Recibos e pacientes inventados que ficavam fixos na tabela de honorários.
    for marca in ("REC-2026-081", "REC-2026-085", "Roberto Carlos Fagundes"):
        assert marca not in bloco

    # A tela precisa consumir a API real.
    assert "/api/v1/financeiro-medico/lancamentos" in bloco
    assert "/api/v1/financeiro-medico/livro-caixa/demonstrativo" in bloco

    html = (raiz / "app" / "static" / "index.html").read_text(encoding="utf-8")
    assert "R$ 1.780,00" not in html
