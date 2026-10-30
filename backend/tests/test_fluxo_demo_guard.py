"""Guarda contra dados de paciente fictício no fluxo de atendimento.

A jornada de demonstração ("Mariana Souza Alencar") era criada em todo boot e
o botão "Finalizar" do cockpit usava um id fixo, emitindo documentos clínicos
para esse paciente. Agora a jornada só existe em desenvolvimento e a
finalização usa o atendimento realmente aberto.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.models.documento_clinico import DocumentoClinicoEmitido
from app.services.fluxo_atendimento_service import fluxo_service


def test_suite_nao_carrega_jornada_de_paciente_ficticio():
    # A suíte cria jornadas reais via API; o que não pode existir é a jornada
    # de demonstração (paciente fictício) criada no boot.
    assert "CONS-2026-9812" not in fluxo_service._jornadas
    assert all(
        jornada.get("paciente_nome") != "Mariana Souza Alencar"
        for jornada in fluxo_service._jornadas.values()
    )
    assert fluxo_service._demo_ativo is False


def test_finalizar_consulta_inexistente_retorna_404_sem_emitir_documento(
    client, db_session
):
    antes = db_session.query(DocumentoClinicoEmitido).count()

    resposta = client.post(
        "/api/v1/fluxo-atendimento/pos-consulta/finalizar",
        json={
            "consulta_id": "CONS-2026-9812",
            "emitir_recibo_dmed": True,
            "lancar_livro_caixa": True,
        },
    )

    assert resposta.status_code == 404, resposta.text
    assert "não localizada" in resposta.json()["detail"]
    assert db_session.query(DocumentoClinicoEmitido).count() == antes


def test_frontend_nao_hardcoda_consulta_de_demonstracao():
    raiz = Path(__file__).resolve().parents[1]
    app_js = (raiz / "app" / "static" / "app.js").read_text(encoding="utf-8")

    trecho = app_js.split("window.finalizarAtendimentoComFluxo", 1)[1][:1200]

    assert "CONS-2026-9812" not in trecho
    assert "consultaAtiva" in trecho
    # Números de documento fictícios não podem aparecer como fallback.
    assert not re.search(r'"CFM-[0-9A-F]{4}', trecho)
    assert "DMED-2026" not in trecho


def test_formulario_de_prescricao_nao_vem_preenchido_com_paciente_ficticio():
    """O modal de receita chegava com "Mariana Souza Alencar"/CPF inventado.

    Um clique em "Emitir" sem tocar nos campos gerava documento clínico real
    para uma pessoa que não existe — e o PDF ia para a farmácia.
    """
    raiz = Path(__file__).resolve().parents[1]
    html = (raiz / "app" / "static" / "index.html").read_text(encoding="utf-8")
    app_js = (raiz / "app" / "static" / "app.js").read_text(encoding="utf-8")

    # Recorte do formulário de prescrição (o cabeçalho do prontuário tem outro
    # placeholder de demonstração, tratado separadamente).
    bloco = html.split('id="modal-prescricao-digital"', 1)[1]
    bloco = bloco.split('id="lista-medicamentos-container"', 1)[0]

    assert 'id="presc-paciente-nome" value=' not in bloco
    assert 'id="presc-paciente-cpf" value=' not in bloco
    assert "Mariana Souza Alencar" not in bloco
    assert "12345678901" not in bloco

    bloco_atestado = html.split('id="modal-atestado-digital"', 1)[1][:4000]
    assert 'id="atestado-paciente-nome" value=' not in bloco_atestado
    assert 'id="atestado-paciente-cpf" value=' not in bloco_atestado
    assert "Mariana Souza Alencar" not in bloco_atestado

    assert '|| "Mariana Souza Alencar"' not in app_js
    assert '|| "12345678901"' not in app_js


def test_emissao_de_receita_exige_paciente_identificado(client):
    """Sem CPF/nome válidos a API recusa — não inventa paciente."""
    resposta = client.post(
        "/api/v1/prescricao/emitir",
        json={
            "paciente_nome": "Paciente Sem CPF",
            "paciente_cpf": "123",
            "medico_nome": "Dra. Francelli Neves Versiani",
            "medico_crm": "78421",
            "medico_uf": "MG",
            "itens": [{"farmaco": "Dipirona", "posologia": "1 cp"}],
        },
    )
    assert resposta.status_code == 422
