"""Testes da API de Dispensação Farmacêutica e Baixa de Receita (C10)."""

from __future__ import annotations

from datetime import date, timedelta
import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.farmacia import Receita, ReceitaItem

OUTRO_HASH = "b" * 64

def _payload(receita: Receita, **overrides) -> dict:
    base = {
        "qr_code_hash": receita.codigo_hash,
        "tipo_baixa": "TOTAL",
        "farmaceutico_nome": "Farmacêutica Ana Souza",
        "farmaceutico_cns": "123456789012345",
        "unidade_cnes": "3180115",
    }
    return {**base, **overrides}


@pytest.fixture
def receita(db_session: Session) -> Receita:
    receita = Receita(
        codigo_hash=uuid.uuid4().hex,
        cns_paciente="123456789012345",
        prescritor_nome="Dra. Francelli Neves Versiani",
        prescritor_cns="987654321098765",
        prescritor_registro="CRM/MG 12345",
        unidade_cnes="3180115",
        data_validade=date.today() + timedelta(days=30),
        itens=[
            ReceitaItem(
                medicamento="Losartana 50mg",
                dosagem="50mg",
                posologia="1 comprimido ao dia",
                quantidade_prescrita=30,
            ),
            ReceitaItem(
                medicamento="Metformina 850mg",
                dosagem="850mg",
                posologia="2 comprimidos ao dia",
                quantidade_prescrita=60,
            ),
        ],
    )
    db_session.add(receita)
    db_session.commit()
    db_session.refresh(receita)
    return receita


def test_consultar_dispensacao_por_hash(client, receita):
    res = client.post("/api/v1/farmacia/dispensacao/consultar", json={"qr_code_hash": receita.codigo_hash})
    assert res.status_code == 200
    corpo = res.json()
    assert corpo["qr_code_hash"] == receita.codigo_hash
    assert corpo["cns_paciente"] == "123456789012345"
    assert len(corpo["medicamentos"]) == 2
    assert corpo["medicamentos"][0]["saldo_remanescente"] == 30


def test_consultar_hash_invalido_retorna_404(client):
    res = client.post("/api/v1/farmacia/dispensacao/consultar", json={"qr_code_hash": OUTRO_HASH})
    assert res.status_code == 404


def test_confirmar_baixa_total(client, receita):
    res = client.post("/api/v1/farmacia/dispensacao/confirmar", json=_payload(receita))
    assert res.status_code == 201
    corpo = res.json()
    assert corpo["tipo_baixa"] == "TOTAL"
    assert corpo["status_receita"] == "DISPENSADA"
    assert all(item["saldo_remanescente"] == 0 for item in corpo["itens"])


def test_confirmar_baixa_fracionada(client, receita):
    item_id = receita.itens[0].id
    payload = _payload(
        receita,
        tipo_baixa="FRACIONADA",
        itens=[{"receita_item_id": item_id, "quantidade": 10, "lote": "L2026A"}],
    )
    res = client.post("/api/v1/farmacia/dispensacao/confirmar", json=payload)
    assert res.status_code == 201
    corpo = res.json()
    assert corpo["status_receita"] == "PARCIALMENTE_DISPENSADA"
    assert corpo["itens"][0]["saldo_remanescente"] == 20


def test_confirmar_fracionada_sem_itens_retorna_400(client, receita):
    payload = _payload(receita, tipo_baixa="FRACIONADA", itens=[])
    res = client.post("/api/v1/farmacia/dispensacao/confirmar", json=payload)
    assert res.status_code == 400


def test_confirmar_quantidade_acima_do_saldo_retorna_400(client, receita):
    item_id = receita.itens[1].id
    payload = _payload(
        receita,
        tipo_baixa="FRACIONADA",
        itens=[{"receita_item_id": item_id, "quantidade": 999}],
    )
    res = client.post("/api/v1/farmacia/dispensacao/confirmar", json=payload)
    assert res.status_code == 400


def test_confirmar_receita_cancelada_retorna_409(client, receita, db_session):
    receita.status = "CANCELADA"
    db_session.commit()
    res = client.post("/api/v1/farmacia/dispensacao/confirmar", json=_payload(receita))
    assert res.status_code == 409


def test_consultar_receita_vencida_retorna_409(client, receita, db_session):
    receita.data_validade = date.today() - timedelta(days=1)
    db_session.commit()
    res = client.post("/api/v1/farmacia/dispensacao/consultar", json={"qr_code_hash": receita.codigo_hash})
    assert res.status_code == 409


def test_confirmar_receita_vencida_retorna_409(client, receita, db_session):
    receita.data_validade = date.today() - timedelta(days=1)
    db_session.commit()
    res = client.post("/api/v1/farmacia/dispensacao/confirmar", json=_payload(receita))
    assert res.status_code == 409


def test_confirmar_receita_ja_dispensada_retorna_409(client, receita):
    assert client.post("/api/v1/farmacia/dispensacao/confirmar", json=_payload(receita)).status_code == 201
    res = client.post("/api/v1/farmacia/dispensacao/confirmar", json=_payload(receita))
    assert res.status_code == 409


def test_confirmar_itens_duplicados_acima_do_saldo_retorna_400(client, receita):
    item_id = receita.itens[0].id
    payload = _payload(
        receita,
        tipo_baixa="FRACIONADA",
        itens=[
            {"receita_item_id": item_id, "quantidade": 20},
            {"receita_item_id": item_id, "quantidade": 20},
        ],
    )
    res = client.post("/api/v1/farmacia/dispensacao/confirmar", json=payload)
    assert res.status_code == 400


def test_confirmar_idempotencia_duplicada_retorna_409(client, receita):
    payload = _payload(receita, chave_idempotencia="op-123")
    assert client.post("/api/v1/farmacia/dispensacao/confirmar", json=payload).status_code == 201
    res = client.post("/api/v1/farmacia/dispensacao/confirmar", json=payload)
    assert res.status_code == 409
