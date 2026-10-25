"""Testes da persistência de receitas e atestados (T2).

Antes, ``MotorPrescricaoCFM`` guardava os documentos num dicionário em memória.
Ao reiniciar o processo, todo QR Code/link de validação passava a responder
**404** e a farmácia não conseguia conferir a receita. Estes testes fingem o
restart limpando o dicionário e conferem que o documento continua validável.

Também cobrem o outro lado do mesmo fluxo: a validação pública não pode exigir
Bearer token, porque quem lê o QR Code numa farmácia não tem conta no sistema.
"""

import pytest

from app.models.documento_clinico import DocumentoClinicoEmitido
from app.services import prescricao_digital_cfm
from app.services.prescricao_digital_cfm import _REPOSITORIO_DOCUMENTOS_CFM


def _payload_prescricao(cpf="12345678901"):
    return {
        "paciente_nome": "Mariana Souza Alencar",
        "paciente_cpf": cpf,
        "medico_nome": "Dra. Francelli Neves Versiani",
        "medico_crm": "78421",
        "medico_uf": "MG",
        "tipo": "SIMPLES",
        "itens": [
            {
                "farmaco": "Escitalopram",
                "concentracao": "10mg",
                "posologia": "Tomar 1 comprimido ao dia",
                "quantidade_total": "1 caixa",
            }
        ],
    }


@pytest.fixture
def documento_emitido(client, db_session):
    """Emite uma receita pela API e devolve o código de validação."""
    resposta = client.post("/api/v1/prescricao/emitir", json=_payload_prescricao())
    assert resposta.status_code == 201, resposta.text
    codigo = resposta.json()["codigo_validacao"]

    yield codigo

    db_session.query(DocumentoClinicoEmitido).filter(
        DocumentoClinicoEmitido.codigo_validacao == codigo
    ).delete()
    db_session.commit()


def test_documento_fica_persistido_no_banco(db_session, documento_emitido):
    registro = (
        db_session.query(DocumentoClinicoEmitido)
        .filter(DocumentoClinicoEmitido.codigo_validacao == documento_emitido)
        .first()
    )
    assert registro is not None
    assert registro.tipo_documento == "RECEITA_DIGITAL"
    assert registro.paciente_nome == "Mariana Souza Alencar"
    assert len(registro.hash_integridade_sha256) == 64
    assert registro.payload_json["itens"][0]["farmaco"] == "Escitalopram"
    # A visão pública não expõe o CPF inteiro.
    assert "12345678901" not in str(registro.dados_consulta_publica)


def test_validacao_sobrevive_a_restart(client, documento_emitido):
    """Simula reinício do processo: a memória some, o banco permanece."""
    _REPOSITORIO_DOCUMENTOS_CFM.clear()

    resposta = client.get(f"/api/v1/prescricao/validar/{documento_emitido}")
    assert resposta.status_code == 200, resposta.text
    dados = resposta.json()
    assert dados["status"] == "VALIDA"
    assert dados["paciente_cpf_mascarado"] == "***.456.789-**"

    # O PDF também continua disponível (é gerado a partir do payload salvo).
    pdf = client.get(f"/api/v1/prescricao/{documento_emitido}/pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF-")


def test_html_de_validacao_sobrevive_a_restart(client, documento_emitido):
    _REPOSITORIO_DOCUMENTOS_CFM.clear()

    resposta = client.get(f"/api/v1/prescricao/validar-html/{documento_emitido}")
    assert resposta.status_code == 200
    assert "Mariana Souza Alencar" in resposta.text


def test_validacao_publica_nao_exige_token(client, documento_emitido, monkeypatch):
    """Farmácia sem conta no sistema precisa conseguir conferir o QR Code."""
    from app.core import rbac

    class _SettingsProtegidas:
        require_auth = True

    monkeypatch.setattr(rbac, "settings", _SettingsProtegidas())

    resposta = client.get(f"/api/v1/prescricao/validar/{documento_emitido}")
    assert resposta.status_code == 200, resposta.text


def test_emissao_continua_exigindo_token(client, monkeypatch):
    """O outro lado: emitir receita sem autenticação deve ser barrado."""
    from app.core import rbac

    class _SettingsProtegidas:
        require_auth = True

    monkeypatch.setattr(rbac, "settings", _SettingsProtegidas())

    resposta = client.post("/api/v1/prescricao/emitir", json=_payload_prescricao())
    assert resposta.status_code in (401, 403)


def test_atestado_omite_cid_a_pedido_do_paciente(client, db_session):
    resposta = client.post(
        "/api/v1/prescricao/atestado/emitir",
        json={
            "paciente_nome": "Carlos Roberto Prado",
            "paciente_cpf": "98765432100",
            "medico_nome": "Dra. Francelli Neves Versiani",
            "medico_crm": "78421",
            "medico_uf": "MG",
            "dias_afastamento": 5,
        },
    )
    assert resposta.status_code == 201, resposta.text
    codigo = resposta.json()["codigo_validacao"]

    try:
        validacao = client.get(f"/api/v1/prescricao/validar/{codigo}")
        assert validacao.status_code == 200
        assert validacao.json()["cid10"] == "Omitido a pedido do paciente"
    finally:
        db_session.query(DocumentoClinicoEmitido).filter(
            DocumentoClinicoEmitido.codigo_validacao == codigo
        ).delete()
        db_session.commit()


def test_motor_puro_sem_sessao_usa_memoria():
    """Caminho legado: sem `db`, o motor continua funcionando em memória."""
    _REPOSITORIO_DOCUMENTOS_CFM.clear()
    doc = prescricao_digital_cfm.MotorPrescricaoCFM.emitir_prescricao(
        paciente_nome="Paciente Sem Banco",
        paciente_cpf="11122233344",
        medico_nome="Dr. Teste",
        medico_crm="12345",
        medico_uf="MG",
        medico_rqe=None,
        itens=[{"farmaco": "Dipirona", "posologia": "1 cp"}],
    )
    assert prescricao_digital_cfm.MotorPrescricaoCFM.validar_documento_publico(
        doc.codigo_validacao
    ) is not None
