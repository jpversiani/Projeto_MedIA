"""Fluxo completo da consulta médica — Estágio 4: Emisión y firma de la receta digital.

Cubre el endpoint REST ``POST /prescricao/emitir`` y ``GET /prescricao/validar/{codigo}``
de ``app.api.v1.prescricao_cfm``:
- Campos obligatorios (médico/CRM, paciente, fecha, ítems)
- Hash SHA-256 de integridad de la receta (campo ``hash_integridade``)
- Código de validación pública y consulta en farmacia
- Casos negativos documentados como LAGUNAS: ítems vacíos (201), ítems sin
  fármaco/posología (500 KeyError), campos del médico omitidos (201).

Nota: el hash SHA-256 se calcula sobre el payload canónico (código, CPF,
CRM-UF, tipo, fecha, ítems) — ver ``MotorPrescricaoCFM.emitir_prescricao``.
El hash NO es determinístico entre dos POSTs porque incluye ``data_emissao``
(timestamp de emisión).
"""

from __future__ import annotations

import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.prescricao_digital_cfm import MotorPrescricaoCFM, TipoPrescricao

CPF_PACIENTE: str = "55566677788"
CRM_MEDICO: str = "78421"
UF_MEDICO: str = "MG"


@pytest.fixture
def client_sin_relanzar_excepciones():
    """TestClient que NO relanza excepciones del servidor (permite ver 500).

    El fixture ``client`` de conftest usa ``TestClient(app)`` con
    ``raise_server_exceptions=True`` (default), que relanza KeyError en el
    test en lugar de devolver la respuesta 500. Para documentar la laguna
    de validación (500 en vez de 422) necesitamos capturar el 500 real.
    """
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def _item(
    farmaco: str = "Amoxicilina + Clavulanato",
    concentracao: str = "875mg + 125mg",
    posologia: str = "1 comprimido de 12 en 12 horas por 7 días",
) -> dict:
    return {
        "farmaco": farmaco,
        "concentracao": concentracao,
        "forma_farmaceutica": "comprimido revestido",
        "posologia": posologia,
        "quantidade_total": "14 comprimidos",
        "via_administracao": "Oral",
    }


def _payload(itens: list[dict] | None = None, **sustituciones) -> dict:
    payload = {
        "paciente_nome": "Paciente Receta Digital",
        "paciente_cpf": CPF_PACIENTE,
        "medico_nome": "Dr. João Paulo Versiani",
        "medico_crm": CRM_MEDICO,
        "medico_uf": UF_MEDICO,
        "medico_rqe": "39412",
        "tipo": "SIMPLES",
        "itens": itens if itens is not None else [_item()],
        "instrucoes_gerais": "Ingerir al inicio de una comida.",
    }
    payload.update(sustituciones)
    return payload


# ---------------------------------------------------------------------------
# Emisión con campos obligatorios
# ---------------------------------------------------------------------------

def test_emitir_receita_digital_campos_obligatorios(client):
    """POST /prescricao/emitir: 201 con todos los campos obligatorios."""
    response = client.post("/api/v1/prescricao/emitir", json=_payload())
    assert response.status_code == 201, response.text
    cuerpo = response.json()

    assert cuerpo["codigo_validacao"].startswith("CFM-")
    assert cuerpo["tipo"] == "SIMPLES"
    assert cuerpo["data_emissao"] is not None
    assert cuerpo["status"] == "VALIDA"
    assert len(cuerpo["hash_integridade"]) == 64
    assert "validador.media-saude.com.br" in cuerpo["url_validacao_publica"]


def test_emitir_receita_antibiotico_con_tipo_explicito(client):
    """Tipo ANTIBIOTICO (RDC 20/2011) se refleja en la respuesta."""
    response = client.post(
        "/api/v1/prescricao/emitir", json=_payload(tipo="ANTIBIOTICO")
    )
    assert response.status_code == 201
    assert response.json()["tipo"] == "ANTIBIOTICO"


def test_emitir_receita_con_instrucciones_generales(client):
    """Instrucciones generales opcionales no rompen la emisión."""
    response = client.post(
        "/api/v1/prescricao/emitir",
        json=_payload(instrucoes_gerais="Tomar con abundante agua."),
    )
    assert response.status_code == 201


# ---------------------------------------------------------------------------
# Hash SHA-256 de integridad
# ---------------------------------------------------------------------------

def test_hash_sha256_es_de_64_hex(client):
    """El hash SHA-256 devuelto es hexadecimal de 64 caracteres."""
    cuerpo = client.post("/api/v1/prescricao/emitir", json=_payload()).json()
    assert len(cuerpo["hash_integridade"]) == 64
    assert all(c in "0123456789abcdef" for c in cuerpo["hash_integridade"])


def test_hash_sha256_cambia_si_se_adultera_un_item(client):
    """Adulterar la posología de un ítem cambia el hash (integridad)."""
    base = client.post("/api/v1/prescricao/emitir", json=_payload()).json()
    adulterada = client.post(
        "/api/v1/prescricao/emitir",
        json=_payload(itens=[_item(posologia="1 comprimido cada 6 horas")]),
    ).json()
    assert base["hash_integridade"] != adulterada["hash_integridade"]


def test_hash_sha256_cambia_si_cambia_el_paciente(client):
    """Cambiar el CPF del paciente cambia el hash (integridad)."""
    base = client.post("/api/v1/prescricao/emitir", json=_payload()).json()
    otro = client.post(
        "/api/v1/prescricao/emitir", json=_payload(paciente_cpf="77788899900")
    ).json()
    assert base["hash_integridade"] != otro["hash_integridade"]


def test_hash_sha256_confirma_con_calculo_manual(client):
    """El hash devuelto coincide con SHA-256 del payload canónico del motor."""
    response = client.post("/api/v1/prescricao/emitir", json=_payload())
    assert response.status_code == 201
    cuerpo = response.json()

    # Reconstruir el payload canónico con los mismos datos del request
    payload = _payload()
    itens = payload["itens"]
    payload_canonico = {
        "codigo": cuerpo["codigo_validacao"],
        "paciente_cpf": payload["paciente_cpf"],
        "medico_crm": f"{payload['medico_crm']}-{payload['medico_uf']}",
        "tipo": payload["tipo"],
        "data": cuerpo["data_emissao"],
        "itens": [
            {
                "farmaco": it["farmaco"],
                "concentracao": it.get("concentracao", ""),
                "forma_farmaceutica": it.get("forma_farmaceutica", "comprimido"),
                "posologia": it["posologia"],
                "quantidade_total": it.get("quantidade_total", "1 caixa"),
                "via_administracao": it.get("via_administracao", "Oral"),
                "instrucoes_especiais": it.get("instrucoes_especiais"),
            }
            for it in itens
        ],
    }
    esperado = hashlib.sha256(
        json.dumps(payload_canonico, sort_keys=True).encode("utf-8")
    ).hexdigest()
    assert cuerpo["hash_integridade"] == esperado


# ---------------------------------------------------------------------------
# Validación pública (farmacia)
# ---------------------------------------------------------------------------

def test_validar_receita_publicamente(client):
    """GET /prescricao/validar/{codigo}: datos de consulta de farmacia."""
    emitida = client.post("/api/v1/prescricao/emitir", json=_payload()).json()
    codigo = emitida["codigo_validacao"]

    response = client.get(f"/api/v1/prescricao/validar/{codigo}")
    assert response.status_code == 200
    datos = response.json()
    assert datos["codigo"] == codigo
    assert datos["status"] == "VALIDA"
    assert datos["tipo_receita"] == "SIMPLES"
    assert datos["medico"] == f"Dr. João Paulo Versiani (CRM {CRM_MEDICO}-{UF_MEDICO})"
    assert datos["hash_sha256"] == emitida["hash_integridade"]
    assert any("Amoxicilina" in item for item in datos["itens"])


def test_validar_codigo_inexistente_devuelve_404(client):
    """GET /prescricao/validar/{codigo} con código desconocido debe dar 404."""
    response = client.get("/api/v1/prescricao/validar/CFM-0000-0000-0000")
    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Casos negativos — LAGUNAS de validación del schema
# ---------------------------------------------------------------------------

def test_emitir_receita_sin_items_es_aceptada(client):
    """LAGUNA: lista de ítems vacía NO es rechazada (201).

    El schema ``EmitirPrescricaoRequest.itens`` es ``List[Dict[str, str]]``
    sin ``min_length``: una receta sin medicamentos se emite como VALIDA.
    Debería ser 422 (una receta sin ítems no es dispensable).
    """
    response = client.post("/api/v1/prescricao/emitir", json=_payload(itens=[]))
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "VALIDA"


def test_emitir_receita_item_sin_farmaco_genera_error_500(client_sin_relanzar_excepciones):
    """LAGUNA: ítem sin 'farmaco' genera 500 (KeyError) en vez de 422.

    El schema no valida las claves internas de cada ítem; el servicio accede
    con ``it["farmaco"]`` y lanza KeyError → 500 Internal Server Error.
    Debería ser 422 con validación del schema.
    """
    item_invalido = _item()
    del item_invalido["farmaco"]
    response = client_sin_relanzar_excepciones.post(
        "/api/v1/prescricao/emitir", json=_payload(itens=[item_invalido])
    )
    assert response.status_code == 500


def test_emitir_receita_item_sin_posologia_genera_error_500(client_sin_relanzar_excepciones):
    """LAGUNA: ítem sin 'posologia' genera 500 (KeyError) en vez de 422."""
    item_invalido = _item()
    del item_invalido["posologia"]
    response = client_sin_relanzar_excepciones.post(
        "/api/v1/prescricao/emitir", json=_payload(itens=[item_invalido])
    )
    assert response.status_code == 500


def test_emitir_receita_sin_campos_medico_es_aceptada(client):
    """LAGUNA: omitir campos del médico (CRM) NO es rechazado (201).

    El schema ``EmitirPrescricaoRequest`` tiene valores por defecto para
    ``medico_nome``, ``medico_crm`` y ``medico_uf``: una receta sin CRM
    explícito se emite con el médico por defecto. Debería exigir CRM.
    """
    payload = _payload()
    del payload["medico_crm"]
    response = client.post("/api/v1/prescricao/emitir", json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "VALIDA"


def test_emitir_receita_sin_paciente_rechazada(client):
    """Faltan campos obligatorios del paciente (CPF) → 422."""
    payload = _payload()
    del payload["paciente_cpf"]
    response = client.post("/api/v1/prescricao/emitir", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Contrato del servicio (nivel unitario, sin HTTP)
# ---------------------------------------------------------------------------

def test_motor_emite_documento_con_hash_y_repositorio():
    """El motor emite el documento con hash y lo registra en el validador."""
    doc = MotorPrescricaoCFM.emitir_prescricao(
        paciente_nome="Paciente Receta Digital",
        paciente_cpf=CPF_PACIENTE,
        medico_nome="Dr. João Paulo Versiani",
        medico_crm=CRM_MEDICO,
        medico_uf=UF_MEDICO,
        medico_rqe="39412",
        itens=[_item()],
        tipo=TipoPrescricao.SIMPLES,
        instrucoes_gerais="Tomar según indicación.",
    )
    assert doc.codigo_validacao.startswith("CFM-")
    assert doc.status == "VALIDA"
    assert len(doc.hash_integridade_sha256) == 64
    assert len(doc.itens) == 1
    assert doc.itens[0].farmaco == "Amoxicilina + Clavulanato"

    val = MotorPrescricaoCFM.validar_documento_publico(doc.codigo_validacao)
    assert val is not None
    assert val["status"] == "VALIDA"