"""Contrato da rota de sincronização offline (C29).

Estes testes cobrem o que a suíte anterior não cobria: o **endpoint real**
(`POST /api/v1/sincronizacao/atendimentos`), que respondia HTTP 500 porque o
serviço chamava um método inexistente. O `test_sync_offline.py` existente testa
uma reimplementação local do serviço e por isso não detectava o defeito.
"""

from __future__ import annotations

import uuid

import pytest

from app.models.atendimento_offline import AtendimentoOffline, StatusSincronizacao

# CNS válido pelo algoritmo DATASUS (soma ponderada múltipla de 11).
CNS_VALIDO = "898000123456780"


def _item(id_local: uuid.UUID | None = None) -> dict:
    return {
        "id_local": str(id_local or uuid.uuid4()),
        "cns_cidadao": CNS_VALIDO,
        "cpf_cidadao": None,
        "profissional_cns": None,
        "cnes_estabelecimento": None,
        "data_hora_atendimento": "2026-10-29T09:30:00-03:00",
        "soap": {
            "subjetivo": "Cefaleia há 3 dias, sem febre.",
            "objetivo": "PA 130/80 mmHg, afebril.",
            "avaliacao": "Cefaleia tensional.",
            "plano": "Analgésico e retorno se piora.",
        },
        "ciap2": "N01",
        "cid10": "G44.2",
    }


def _payload(*itens: dict) -> dict:
    return {"itens": list(itens)}


def test_upload_persiste_lote_e_responde_201(client, db_session):
    id_local = uuid.uuid4()

    response = client.post(
        "/api/v1/sincronizacao/atendimentos",
        json=_payload(_item(id_local)),
    )

    assert response.status_code == 201, response.text
    corpo = response.json()
    assert corpo["recebidos"] == [str(id_local)]
    assert corpo["duplicados"] == []
    assert corpo["total_recebidos"] == 1
    assert corpo["total_duplicados"] == 0

    registro = (
        db_session.query(AtendimentoOffline)
        .filter(AtendimentoOffline.id_local == str(id_local))
        .one()
    )
    assert registro.cns_cidadao == CNS_VALIDO
    assert registro.subjetivo == "Cefaleia há 3 dias, sem febre."
    assert registro.avaliacao == "Cefaleia tensional."
    assert registro.ciap2 == "N01"
    assert registro.cid10 == "G44.2"
    assert registro.status is StatusSincronizacao.RECEBIDO


def test_reenvio_do_mesmo_id_local_e_idempotente(client, db_session):
    id_local = uuid.uuid4()
    payload = _payload(_item(id_local))

    primeiro = client.post("/api/v1/sincronizacao/atendimentos", json=payload)
    segundo = client.post("/api/v1/sincronizacao/atendimentos", json=payload)

    assert primeiro.status_code == 201
    assert primeiro.json()["total_recebidos"] == 1

    assert segundo.status_code == 201, segundo.text
    corpo = segundo.json()
    assert corpo["total_recebidos"] == 0
    assert corpo["total_duplicados"] == 1
    assert corpo["duplicados"][0]["id_local"] == str(id_local)

    total = (
        db_session.query(AtendimentoOffline)
        .filter(AtendimentoOffline.id_local == str(id_local))
        .count()
    )
    assert total == 1


def test_id_local_repetido_dentro_do_mesmo_lote(client):
    id_local = uuid.uuid4()

    response = client.post(
        "/api/v1/sincronizacao/atendimentos",
        json=_payload(_item(id_local), _item(id_local)),
    )

    assert response.status_code == 201, response.text
    corpo = response.json()
    assert corpo["total_recebidos"] == 1
    assert corpo["total_duplicados"] == 1
    assert corpo["duplicados"][0]["id_local"] == str(id_local)


@pytest.mark.parametrize(
    "item_invalido",
    [
        pytest.param({**_item(), "cns_cidadao": "123"}, id="cns-invalido"),
        pytest.param(
            {**_item(), "data_hora_atendimento": "2026-10-29T09:30:00"},
            id="sem-fuso-horario",
        ),
        pytest.param(
            {k: v for k, v in _item().items() if k != "soap"}, id="sem-soap"
        ),
        pytest.param(
            {**_item(), "campo_desconhecido": "x"}, id="campo-extra"
        ),
        pytest.param(
            {**_item(), "id_local": "nao-e-uuid"}, id="uuid-invalido"
        ),
    ],
)
def test_payload_invalido_retorna_422(client, item_invalido):
    response = client.post(
        "/api/v1/sincronizacao/atendimentos",
        json=_payload(item_invalido),
    )
    assert response.status_code == 422, response.text


def test_lote_vazio_retorna_422(client):
    response = client.post("/api/v1/sincronizacao/atendimentos", json={"itens": []})
    assert response.status_code == 422


def test_status_geral_reflete_os_uploads(client):
    antes = client.get("/api/v1/sincronizacao/status")
    assert antes.status_code == 200, antes.text
    total_antes = antes.json()["total_recebidos"]

    id_local = uuid.uuid4()
    upload = client.post(
        "/api/v1/sincronizacao/atendimentos",
        json=_payload(_item(id_local)),
    )
    assert upload.status_code == 201

    depois = client.get("/api/v1/sincronizacao/status")
    assert depois.status_code == 200
    corpo = depois.json()
    assert corpo["total_recebidos"] == total_antes + 1
    assert corpo["ultimo_recebimento"] is not None
