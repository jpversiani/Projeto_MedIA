"""Integração Prescrição Digital → Farmácia (P0-5).

Antes desta correção a emissão gravava apenas em ``documentos_clinicos``:
nenhuma ``Receita`` era criada, então a farmácia respondia **404 para toda
receita emitida** — mesmo a receita impressa, com QR Code, era inutilizável.

Estes testes cobrem o caminho real: emitir → consultar → dispensar.
"""

from __future__ import annotations

import json

import pytest

from app.models.cidadao import Cidadao
from app.models.documento_clinico import DocumentoClinicoEmitido
from app.models.farmacia import (
    STATUS_DISPENSADA,
    STATUS_PARCIALMENTE_DISPENSADA,
    Receita,
)
from app.services.farmacia_bridge import (
    calcular_hash_receita,
    montar_conteudo_canonico,
)

CNS_PRESCRITOR = "700123456789012"
CNES_UNIDADE = "3180115"
CNS_FARMACEUTICO = "700987654321098"


def _payload(**overrides) -> dict:
    dados = {
        "paciente_nome": "Beatriz Viana",
        "paciente_cpf": "99988877766",
        "paciente_cns": "898000123456780",
        "medico_nome": "Dra. Francelli Neves Versiani",
        "medico_crm": "78421",
        "medico_uf": "MG",
        "medico_cns": CNS_PRESCRITOR,
        "unidade_cnes": CNES_UNIDADE,
        "tipo": "SIMPLES",
        "itens": [
            {
                "farmaco": "Dipirona Monoidratada",
                "concentracao": "500mg",
                "forma_farmaceutica": "comprimido",
                "posologia": "1 cp se dor ou febre",
                "quantidade_total": "1 cartela",
            }
        ],
    }
    dados.update(overrides)
    return dados


def _emitir(client, **overrides) -> dict:
    resposta = client.post("/api/v1/prescricao/emitir", json=_payload(**overrides))
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def _consultar(client, valor: str) -> dict:
    resposta = client.post(
        "/api/v1/farmacia/dispensacao/consultar", json={"qr_code_hash": valor}
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def _dispensar(client, valor: str, *, tipo: str = "TOTAL", itens=None, chave=None) -> dict:
    corpo = {
        "qr_code_hash": valor,
        "tipo_baixa": tipo,
        "farmaceutico_nome": "Farmacêutico de Teste",
        "farmaceutico_cns": CNS_FARMACEUTICO,
        "unidade_cnes": CNES_UNIDADE,
        "observacoes": "Baixa registrada no teste de integração",
    }
    if itens is not None:
        corpo["itens"] = itens
    if chave is not None:
        corpo["chave_idempotencia"] = chave
    resposta = client.post("/api/v1/farmacia/dispensacao/confirmar", json=corpo)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


# ---------------------------------------------------------------------------
# Emissão cria a receita dispensável
# ---------------------------------------------------------------------------


def test_emissao_cria_receita_dispensavel(client, db_session):
    corpo = _emitir(client)

    assert corpo["farmacia_integrada"] is True
    assert corpo["farmacia_pendencias"] == []
    assert corpo["receita_id"] is not None
    assert len(corpo["qr_code_hash"]) == 64

    receita = db_session.get(Receita, corpo["receita_id"])
    assert receita is not None
    assert receita.codigo_hash == corpo["qr_code_hash"]
    assert receita.cns_paciente == "898000123456780"
    assert receita.prescritor_cns == CNS_PRESCRITOR
    assert receita.prescritor_registro == "78421-MG"
    assert receita.unidade_cnes == CNES_UNIDADE
    assert receita.status == "EMITIDA"

    assert len(receita.itens) == 1
    item = receita.itens[0]
    assert item.medicamento == "Dipirona Monoidratada"
    assert item.dosagem == "500mg comprimido"
    # Texto livre do contrato ("1 cartela") vira inteiro para a farmácia.
    assert item.quantidade_prescrita == 1
    assert item.saldo_remanescente == 1


def test_hash_do_qr_e_recalculavel_a_partir_do_conteudo(client, db_session):
    corpo = _emitir(client)
    receita = db_session.get(Receita, corpo["receita_id"])

    conteudo = montar_conteudo_canonico(
        codigo_validacao=corpo["codigo_validacao"],
        cns_paciente=receita.cns_paciente,
        cpf_paciente=receita.cpf_paciente,
        prescritor_cns=receita.prescritor_cns,
        prescritor_registro=receita.prescritor_registro,
        unidade_cnes=receita.unidade_cnes,
        data_emissao=receita.data_emissao,
        itens=[
            {
                "medicamento": item.medicamento,
                "dosagem": item.dosagem,
                "posologia": item.posologia,
                "quantidade_prescrita": item.quantidade_prescrita,
            }
            for item in receita.itens
        ],
    )

    assert calcular_hash_receita(conteudo) == receita.codigo_hash

    # Qualquer adulteração do conteúdo clínico muda o hash.
    adulterado = json.loads(json.dumps(conteudo))
    adulterado["itens"][0]["quantidade_prescrita"] = 99
    assert calcular_hash_receita(adulterado) != receita.codigo_hash


def test_cns_do_paciente_e_resolvido_pelo_cpf_cadastrado(client, db_session):
    cidadao = db_session.query(Cidadao).filter(Cidadao.cpf == "12345678900").first()
    assert cidadao is not None and cidadao.cns

    corpo = _emitir(
        client,
        paciente_cpf=cidadao.cpf,
        paciente_cns=None,
        paciente_nome=cidadao.nome_completo,
    )

    assert corpo["farmacia_integrada"] is True
    receita = db_session.get(Receita, corpo["receita_id"])
    assert receita.cns_paciente == cidadao.cns


def test_emissao_sem_identificacao_avisa_a_pendencia_em_vez_de_sumir(client):
    corpo = _emitir(
        client,
        paciente_cpf="00011122233",
        paciente_cns=None,
        medico_cns=None,
        unidade_cnes=None,
    )

    # O documento clínico não pode falhar por cadastro incompleto...
    assert corpo["codigo_validacao"].startswith("CFM-")
    assert corpo["farmacia_integrada"] is False
    assert corpo["qr_code_hash"] is None

    # ...mas a pendência precisa ser explícita.
    pendencias = " ".join(corpo["farmacia_pendencias"])
    assert "CNS do paciente" in pendencias
    assert "CNS do prescritor" in pendencias
    assert "CNES da unidade" in pendencias

    # E a farmácia continua sem a receita, agora de forma rastreável.
    resposta = client.post(
        "/api/v1/farmacia/dispensacao/consultar",
        json={"qr_code_hash": corpo["codigo_validacao"]},
    )
    assert resposta.status_code == 404


# ---------------------------------------------------------------------------
# Farmácia consulta e dispensa
# ---------------------------------------------------------------------------


def test_farmacia_consulta_receita_emitida(client):
    corpo = _emitir(client)

    consulta = _consultar(client, corpo["qr_code_hash"])
    assert consulta["receita_id"] == corpo["receita_id"]
    assert consulta["cns_paciente"] == "898000123456780"
    assert consulta["prescritor_registro"] == "78421-MG"
    assert consulta["status"] == "EMITIDA"
    assert len(consulta["medicamentos"]) == 1
    assert consulta["medicamentos"][0]["saldo_remanescente"] == 1


def test_farmacia_consulta_pelo_codigo_impresso_no_qr(client):
    """O QR do PDF carrega o código público, não o hash bruto."""
    corpo = _emitir(client)

    consulta = _consultar(client, corpo["codigo_validacao"])
    assert consulta["receita_id"] == corpo["receita_id"]

    # E também funciona se a farmácia enviar a URL completa do validador.
    url = f"https://app.media-saude.com.br/api/v1/prescricao/validar-html/{corpo['codigo_validacao']}"
    assert _consultar(client, url)["receita_id"] == corpo["receita_id"]


def test_dispensacao_total_encerra_a_receita(client, db_session):
    corpo = _emitir(client)

    baixa = _dispensar(client, corpo["qr_code_hash"], chave="baixa-total-1")
    assert baixa["receita_id"] == corpo["receita_id"]
    assert baixa["status_receita"] == STATUS_DISPENSADA
    assert baixa["itens"][0]["saldo_remanescente"] == 0

    receita = db_session.get(Receita, corpo["receita_id"])
    db_session.refresh(receita)
    assert receita.status == STATUS_DISPENSADA
    assert receita.dispensacoes[0].chave_idempotencia == "baixa-total-1"

    # Segunda tentativa é recusada (não há saldo).
    repetida = client.post(
        "/api/v1/farmacia/dispensacao/consultar",
        json={"qr_code_hash": corpo["qr_code_hash"]},
    )
    assert repetida.status_code == 409


def test_dispensacao_fracionada_preserva_saldo(client, db_session):
    corpo = _emitir(
        client,
        itens=[
            {
                "farmaco": "Losartana Potássica",
                "concentracao": "50mg",
                "posologia": "1 cp pela manhã",
                "quantidade_total": "30 comprimidos",
            },
            {
                "farmaco": "Hidroclorotiazida",
                "concentracao": "25mg",
                "posologia": "1 cp pela manhã",
                "quantidade_total": "30 comprimidos",
            },
        ],
    )

    consulta = _consultar(client, corpo["qr_code_hash"])
    primeiro_item = consulta["medicamentos"][0]
    assert primeiro_item["quantidade_prescrita"] == 30

    baixa = _dispensar(
        client,
        corpo["qr_code_hash"],
        tipo="FRACIONADA",
        itens=[{"receita_item_id": primeiro_item["item_id"], "quantidade": 10}],
    )

    assert baixa["status_receita"] == STATUS_PARCIALMENTE_DISPENSADA
    por_item = {item["item_id"]: item for item in baixa["itens"]}
    assert por_item[primeiro_item["item_id"]]["saldo_remanescente"] == 20

    receita = db_session.get(Receita, corpo["receita_id"])
    db_session.refresh(receita)
    assert receita.status == STATUS_PARCIALMENTE_DISPENSADA


@pytest.mark.parametrize("tipo", ["SIMPLES", "ANTIBIOTICO", "CONTROLE_ESPECIAL"])
def test_validade_da_receita_varia_por_tipo(client, db_session, tipo):
    corpo = _emitir(client, tipo=tipo)
    receita = db_session.get(Receita, corpo["receita_id"])
    dias = (receita.data_validade - receita.data_emissao.date()).days
    assert dias == (10 if tipo == "ANTIBIOTICO" else 30)


def test_documento_clinico_guarda_o_hash_do_qr(client, db_session):
    corpo = _emitir(client)

    documento = (
        db_session.query(DocumentoClinicoEmitido)
        .filter(
            DocumentoClinicoEmitido.codigo_validacao == corpo["codigo_validacao"]
        )
        .one()
    )
    assert documento.dados_consulta_publica["qr_code_hash"] == corpo["qr_code_hash"]
    assert documento.payload_json["qr_code_hash"] == corpo["qr_code_hash"]
    assert documento.payload_json["receita_id"] == corpo["receita_id"]
