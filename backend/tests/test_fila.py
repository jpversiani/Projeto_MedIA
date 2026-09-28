"""
Testes de integridade da FILA DE ATENDIMENTO & ACOLHIMENTO do MedIA.

Cobrem: listagem com filtro de status, criação com cálculo de IMC,
validações de existência (404), atualização de status e ordenação.
"""
import pytest

from app.models.cidadao import Cidadao
from app.models.estabelecimento import Estabelecimento
from app.models.fila import FilaAcolhimento


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _seed_cidadao(db_session, cpf="12345678900"):
    """Retorna um cidadão do seed (criado pelo conftest)."""
    cidadao = db_session.query(Cidadao).filter(Cidadao.cpf == cpf).first()
    assert cidadao is not None, "Cidadão de seed não encontrado"
    return cidadao


def _est_id(db_session):
    return db_session.query(Estabelecimento).first().id


# ------------------------------------------------------------------
# 1. Listagem e filtro
# ------------------------------------------------------------------
def test_listar_fila_vazia_retorna_lista(client):
    resp = client.get("/api/v1/fila/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_listar_fila_status_todos_nao_filtra(client, db_session):
    cidadao = _seed_cidadao(db_session)
    est = _est_id(db_session)
    db_session.add(FilaAcolhimento(cidadao_id=cidadao.id, estabelecimento_id=est, status="FINALIZADO"))
    db_session.commit()

    resp = client.get("/api/v1/fila/?status=TODOS")
    assert resp.status_code == 200
    assert any(item["status"] == "FINALIZADO" for item in resp.json())


def test_listar_fila_filtro_status_aguardando(client, db_session):
    cidadao = _seed_cidadao(db_session)
    est = _est_id(db_session)
    db_session.add(
        FilaAcolhimento(cidadao_id=cidadao.id, estabelecimento_id=est, status="AGUARDANDO_ATENDIMENTO")
    )
    db_session.commit()

    resp = client.get("/api/v1/fila/?status=AGUARDANDO_ATENDIMENTO")
    assert resp.status_code == 200
    assert all(i["status"] == "AGUARDANDO_ATENDIMENTO" for i in resp.json())


# ------------------------------------------------------------------
# 2. Criação / Acolhimento
# ------------------------------------------------------------------
def test_acolher_cidadao_calcula_imc(client, db_session):
    cidadao = _seed_cidadao(db_session)
    est = _est_id(db_session)

    payload = {
        "cidadao_id": cidadao.id,
        "estabelecimento_id": est,
        "peso_kg": 90.0,
        "altura_cm": 180.0,
        "classificacao_risco": "AMARELO",
    }
    resp = client.post("/api/v1/fila/", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "AGUARDANDO_ATENDIMENTO"
    assert body["imc"] == pytest.approx(27.78, abs=0.01)


def test_acolher_cidadao_inexistente_retorna_404(client, db_session):
    est = _est_id(db_session)
    resp = client.post(
        "/api/v1/fila/",
        json={"cidadao_id": 999999, "estabelecimento_id": est},
    )
    assert resp.status_code == 404


def test_acolher_cidadao_sem_altura_nao_calcula_imc(client, db_session):
    cidadao = _seed_cidadao(db_session)
    est = _est_id(db_session)
    resp = client.post(
        "/api/v1/fila/",
        json={"cidadao_id": cidadao.id, "estabelecimento_id": est, "peso_kg": 70.0},
    )
    assert resp.status_code == 201
    assert resp.json()["imc"] is None


# ------------------------------------------------------------------
# 3. Consulta e Atualização
# ------------------------------------------------------------------
def test_obter_item_inexistente_retorna_404(client):
    resp = client.get("/api/v1/fila/999999")
    assert resp.status_code == 404


def test_obter_item_existente(client, db_session):
    cidadao = _seed_cidadao(db_session)
    est = _est_id(db_session)
    item = FilaAcolhimento(cidadao_id=cidadao.id, estabelecimento_id=est)
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    resp = client.get(f"/api/v1/fila/{item.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == item.id


def test_atualizar_status_fila(client, db_session):
    cidadao = _seed_cidadao(db_session)
    est = _est_id(db_session)
    item = FilaAcolhimento(cidadao_id=cidadao.id, estabelecimento_id=est)
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    resp = client.put(f"/api/v1/fila/{item.id}", json={"status": "EM_ATENDIMENTO"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "EM_ATENDIMENTO"


def test_atualizar_item_inexistente_retorna_404(client):
    resp = client.put("/api/v1/fila/999999", json={"status": "FINALIZADO"})
    assert resp.status_code == 404


# ------------------------------------------------------------------
# 4. Ordenação (contrato de priorização)
# ------------------------------------------------------------------
def test_fila_ordenada_por_data_de_entrada(client, db_session):
    """Ordem cronológica por data_hora_entrada (FIFO) é o contrato atual."""
    from datetime import datetime, timedelta, timezone

    cidadao = _seed_cidadao(db_session)
    est = _est_id(db_session)
    base = datetime.now(timezone.utc)
    for i, minutos in enumerate([0, -30, -10]):  # entradas fora de ordem
        db_session.add(
            FilaAcolhimento(
                cidadao_id=cidadao.id,
                estabelecimento_id=est,
                data_hora_entrada=base + timedelta(minutes=minutos),
            )
        )
    db_session.commit()

    resp = client.get("/api/v1/fila/")
    assert resp.status_code == 200
    datas = [i["data_hora_entrada"] for i in resp.json()]
    assert datas == sorted(datas), "A fila deve sair ordenada por data_hora_entrada (FIFO)"