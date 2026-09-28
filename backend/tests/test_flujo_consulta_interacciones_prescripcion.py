"""Fluxo completo da consulta médica — Estágio 3: Interacciones medicamentosas en la prescripción.

LACUNA DE SEGURIDAD CONOCIDA:
``POST /prescricao/emitir`` (``app.api.v1.prescricao_cfm``) NO invoca el
``VerificadorFarmacologico`` (``app.services.interacoes_medicamentosas``).
La checagem de interacciones solo se usa en el flujo de la farmacia.

Este archivo:
1. Verifica que el motor de interacciones detecta el par fluoxetina+tramadol
   como GRAVE (síndrome serotoninérgica) — regresión ya cubierta en
   ``test_interacoes_medicamentosas.py``, aquí se reafirma a nivel de servicio.
2. EXPONE la laguna: una prescripción con fluoxetina+tramadol emitida vía
   POST /prescricao/emitir se acepta con 201 y status "VALIDA" sin ninguna
   alerta farmacológica en la respuesta.
3. Verifica que el flujo de la farmacia (que SÍ usa el verificador) rechaza
   la dispensación de una combinación contraindicada (varfarina+ibuprofeno),
   demostrando que el motor funciona pero no está conectado a la prescripción.
"""

from __future__ import annotations

import pytest

from app.services.interacoes_medicamentosas import VerificadorFarmacologico

CPF_PACIENTE: str = "55566677788"
CRM_MEDICO: str = "78421"
UF_MEDICO: str = "MG"


def _payload_prescripcion(itens: list[dict]) -> dict:
    """Payload mínimo válido para POST /prescricao/emitir."""
    return {
        "paciente_nome": "Paciente Interacciones",
        "paciente_cpf": CPF_PACIENTE,
        "medico_nome": "Dr. João Paulo Versiani",
        "medico_crm": CRM_MEDICO,
        "medico_uf": UF_MEDICO,
        "medico_rqe": "39412",
        "tipo": "SIMPLES",
        "itens": itens,
        "instrucoes_gerais": "Tomar según indicación médica.",
    }


def _item(farmaco: str, posologia: str = "1 comprimido cada 12 horas") -> dict:
    return {
        "farmaco": farmaco,
        "concentracao": "20mg" if "fluoxetina" in farmaco.lower() else "50mg",
        "forma_farmaceutica": "comprimido",
        "posologia": posologia,
        "quantidade_total": "30 comprimidos",
        "via_administracao": "Oral",
    }


# ---------------------------------------------------------------------------
# 1. El motor de interacciones detecta el par GRAVE (síndrome serotoninérgica)
# ---------------------------------------------------------------------------

def test_verificador_detecta_fluoxetina_tramadol_grave():
    """El motor detecta fluoxetina+tramadol como GRAVE (síndrome serotoninérgica)."""
    rel = VerificadorFarmacologico.checar_interacoes_e_alergias(
        medicamentos_prescritos=["Fluoxetina 20mg", "Tramadol 50mg"],
        alergias_paciente=[],
    )
    assert len(rel.interacoes_detectadas) == 1
    alerta = rel.interacoes_detectadas[0]
    assert alerta.gravidade == "GRAVE"
    assert "serotoninérgica" in alerta.mecanismo.lower()
    assert "fluoxetina" in alerta.medicamento_a
    assert "tramadol" in alerta.medicamento_b


# ---------------------------------------------------------------------------
# 2. LACUNA: POST /prescricao/emitir NO invoca el verificador farmacológico
# ---------------------------------------------------------------------------

def test_prescripcion_fluoxetina_tramadol_no_es_bloqueada(client):
    """LACUNA DE SEGURIDAD: la prescripción con fluoxetina+tramadol se emite sin alerta.

    Una prescripción con la combinación GRAVE (riesgo de síndrome
    serotoninérgica potencialmente fatal) debería ser bloqueada o al menos
    alertada por POST /prescricao/emitir. Hoy el endpoint NO consulta el
    VerificadorFarmacologico: la respuesta es 201 con status "VALIDA" y
    NO contiene ningún campo de alerta farmacológica.

    Este test documenta la laguna (no debe fallar la suite). Si se conecta
    el verificador al endpoint, este test deberá esperar 409/422 o un campo
    de alertas en la respuesta.
    """
    response = client.post(
        "/api/v1/prescricao/emitir",
        json=_payload_prescripcion(
            [_item("Fluoxetina 20mg"), _item("Tramadol 50mg")]
        ),
    )
    assert response.status_code == 201, response.text
    cuerpo = response.json()
    assert cuerpo["status"] == "VALIDA"
    assert cuerpo["tipo"] == "SIMPLES"
    assert len(cuerpo["hash_integridade"]) == 64

    # La respuesta NO expone ninguna alerta farmacológica
    assert "alertas" not in cuerpo
    assert "interacciones" not in cuerpo
    assert "aprobado_para_dispensacion" not in cuerpo


def test_prescripcion_fluoxetina_tramadol_es_valida_publicamente(client):
    """La prescripción GRAVE queda registrada como VALIDA en el validador público.

    Consecuencia directa de la laguna: la farmacia que consulte el código de
    validación verá "VALIDA" sin ninguna advertencia de interacción.
    """
    response = client.post(
        "/api/v1/prescricao/emitir",
        json=_payload_prescripcion(
            [_item("Fluoxetina 20mg"), _item("Tramadol 50mg")]
        ),
    )
    assert response.status_code == 201
    codigo = response.json()["codigo_validacao"]

    validacion = client.get(f"/api/v1/prescricao/validar/{codigo}")
    assert validacion.status_code == 200
    datos = validacion.json()
    assert datos["status"] == "VALIDA"
    assert datos["tipo_receita"] == "SIMPLES"
    # Sin advertencia de interacción en los datos de consulta de farmacia
    assert "interacciones" not in datos
    assert "advertencias" not in datos


def test_prescripcion_segura_sin_interacciones_se_emite_normal(client):
    """Control: una prescripción sin interacciones se emite con 201 (comportamiento esperado)."""
    response = client.post(
        "/api/v1/prescricao/emitir",
        json=_payload_prescripcion(
            [_item("Paracetamol 750mg"), _item("Loratadina 10mg")]
        ),
    )
    assert response.status_code == 201
    assert response.json()["status"] == "VALIDA"


# ---------------------------------------------------------------------------
# 3. El flujo de la farmacia SÍ usa el verificador (contraste)
# ---------------------------------------------------------------------------

def test_verificador_bloquea_contraindicacion_varfarina_ibuprofeno():
    """El motor marca varfarina+ibuprofeno como CONTRAINDICADO (no dispensable).

    Demuestra que el motor funciona correctamente: la laguna está en la
    conexión con POST /prescricao/emitir, no en la detección.
    """
    rel = VerificadorFarmacologico.checar_interacoes_e_alergias(
        medicamentos_prescritos=["Varfarina 5mg", "Ibuprofeno 600mg"],
        alergias_paciente=[],
    )
    assert len(rel.interacoes_detectadas) == 1
    assert rel.interacoes_detectadas[0].gravidade == "CONTRAINDICADO"
    assert rel.aprovado_para_dispensacao is False


def test_verificador_alerta_alergia_cruzada_penicilina():
    """El motor alerta alergia cruzada (amoxicilina + alergia a penicilina)."""
    rel = VerificadorFarmacologico.checar_interacoes_e_alergias(
        medicamentos_prescritos=["Amoxicilina 500mg"],
        alergias_paciente=["Alergia grave a Penicilina"],
    )
    assert len(rel.alertas_alergia) >= 1
    assert rel.aprovado_para_dispensacao is False