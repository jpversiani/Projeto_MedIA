"""Fluxo completo da consulta médica — Estágio 2: Prontuario SOAP (PEC e-SUS APS).

Complementa ``test_prontuario.py`` con el flujo SOAP completo:
- Resumen del prontuario (problemas activos, alergias, medicamentos en uso)
- Evoluciones paginadas (método SOAP)
- Registro de alergias y problemas CIAP-2/CID-10
- CASO NEGATIVO: SOAP incompleto/rechazado (422 por validación del schema)
- Validación de CNS malformado (422)

Los endpoints de evolución SOAP (POST /atendimentos/) NO validan la
completitud del método SOAP (S/O/A/P): un atendimiento con solo el motivo
subjetivo se acepta con 201. El test documenta esta laguna de calidad
clínica sin romper la suite.

NOTA: la BD es compartida en sesión (StaticPool) con el resto de la suíte.
Cada test usa CNS/CPF ÚNICOS para evitar colisiones de unicidad.
"""

from __future__ import annotations

import itertools

import pytest

CNS_INEXISTENTE: str = "998450013720001"

# Generadores de identificadores únicos por test (evitan colisiones en la BD
# compartida de sesión: CPF y CNS son UNIQUE en el modelo Cidadao).
_cns_counter = itertools.count(1)
_cpf_counter = itertools.count(1)


def _cns_unico() -> str:
    """CNS definitivo de 15 dígitos (prefijo 1) único por llamada."""
    n = next(_cns_counter)
    return f"1168096600000{n:03d}"[-15:]


def _cpf_unico() -> str:
    """CPF de 11 dígitos único por llamada."""
    n = next(_cpf_counter)
    return f"1{n:09d}"[-11:]


def _crear_cidadao(client, cns: str, cpf: str, alergias: str | None = None) -> int:
    """Crea un ciudadano de prueba y devuelve su id."""
    payload = {
        "nome_completo": "Paciente SOAP Flujo",
        "cpf": cpf,
        "cns": cns,
        "data_nascimento": "1975-03-10",
        "sexo": "M",
    }
    if alergias is not None:
        payload["alergias"] = alergias
    response = client.post("/api/v1/cidadaos/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _crear_atendimento_soap(client, cidadao_id: int, **campos) -> dict:
    """Crea un atendimiento SOAP y devuelve el JSON de respuesta."""
    payload = {
        "cidadao_id": cidadao_id,
        "profissional_id": 1,
        "estabelecimento_id": 1,
        "problemas": [],
    }
    payload.update(campos)
    response = client.post("/api/v1/atendimentos/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Resumen del prontuario
# ---------------------------------------------------------------------------

def test_resumen_prontuario_con_alergias_problemas_y_medicamentos(client):
    """GET /prontuario/{cns}: resumen con alergias, problemas y medicamentos."""
    cns = _cns_unico()
    cidadao_id = _crear_cidadao(
        client, cns, _cpf_unico(), alergias="Penicilina; Dipirona"
    )

    # Problema CIAP-2 en la Lista de Problemas
    response = client.post(
        f"/api/v1/prontuario/{cns}/problema",
        json={
            "tipo_codigo": "CIAP2",
            "codigo": "K86",
            "descricao": "Hipertensión arterial sin complicaciones",
        },
    )
    assert response.status_code == 201, response.text

    # Atendimiento SOAP con prescripción y problema CID-10
    _crear_atendimento_soap(
        client,
        cidadao_id,
        plano_prescricoes="Losartana Potássica 50mg - 30 comprimidos",
        problemas=[
            {
                "tipo_codigo": "CID10",
                "codigo": "I10",
                "descricao": "Hipertensión esencial (primaria)",
                "situacao": "ATIVO",
            }
        ],
    )

    response = client.get(f"/api/v1/prontuario/{cns}")
    assert response.status_code == 200
    resumo = response.json()
    assert resumo["cidadao"]["cns"] == cns
    assert set(resumo["alergias"]) == {"Penicilina", "Dipirona"}
    assert resumo["total_atendimentos"] == 1
    assert resumo["data_ultimo_atendimento"] is not None

    codigos = {(p["tipo_codigo"], p["codigo"]) for p in resumo["problemas_ativos"]}
    assert ("CIAP2", "K86") in codigos
    assert ("CID10", "I10") in codigos
    origenes = {p["origem"] for p in resumo["problemas_ativos"]}
    assert origenes == {"PRONTUARIO", "ATENDIMENTO"}

    nombres_medicamentos = {m["nome"] for m in resumo["medicamentos_em_uso"]}
    assert nombres_medicamentos == {"Losartana Potássica 50mg"}


def test_resumo_rechaza_cns_malformado(client):
    """CNS fuera del formato de 15 dígitos debe generar 422."""
    response = client.get("/api/v1/prontuario/1234")
    assert response.status_code == 422


def test_resumo_cns_inexistente_devuelve_404(client):
    """CNS bien formado pero inexistente debe devolver 404."""
    response = client.get(f"/api/v1/prontuario/{CNS_INEXISTENTE}")
    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Evoluciones SOAP paginadas
# ---------------------------------------------------------------------------

def test_evoluciones_soap_paginadas_y_ordenadas(client):
    """GET /prontuario/{cns}/evolucoes: paginación por offset, más reciente primero."""
    cns = _cns_unico()
    cidadao_id = _crear_cidadao(client, cns, _cpf_unico())

    for i in range(3):
        _crear_atendimento_soap(
            client,
            cidadao_id,
            subjetivo_motivo=f"Motivo de consulta {i}",
            plano_conduta=f"Conduta {i}",
        )

    response = client.get(f"/api/v1/prontuario/{cns}/evolucoes?skip=0&limit=2")
    assert response.status_code == 200
    pagina = response.json()
    assert pagina["total"] == 3
    assert pagina["skip"] == 0
    assert pagina["limit"] == 2
    assert len(pagina["itens"]) == 2

    # Orden: más reciente primero (data_hora_inicio desc)
    fechas = [item["data_hora_inicio"] for item in pagina["itens"]]
    assert fechas == sorted(fechas, reverse=True)

    # Segunda página
    response2 = client.get(f"/api/v1/prontuario/{cns}/evolucoes?skip=2&limit=2")
    assert response2.status_code == 200
    assert len(response2.json()["itens"]) == 1


def test_evoluciones_limite_invalido_rechazado(client):
    """limit=0 o limit>100 deben generar 422 (validación del query)."""
    cns = _cns_unico()
    cidadao_id = _crear_cidadao(client, cns, _cpf_unico())
    _crear_atendimento_soap(client, cidadao_id)

    assert client.get(f"/api/v1/prontuario/{cns}/evolucoes?limit=0").status_code == 422
    assert client.get(f"/api/v1/prontuario/{cns}/evolucoes?limit=101").status_code == 422


def test_evoluciones_cns_inexistente_devuelve_404(client):
    """Evoluciones de un CNS inexistente deben devolver 404."""
    response = client.get(f"/api/v1/prontuario/{CNS_INEXISTENTE}/evolucoes")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Registro de alergias y problemas (CIAP-2 / CID-10)
# ---------------------------------------------------------------------------

def test_registrar_alergia_y_duplicado_rechazado(client):
    """POST /prontuario/{cns}/alergia: 201 y duplicado (case-insensitive) 422."""
    cns = _cns_unico()
    _crear_cidadao(client, cns, _cpf_unico())

    response = client.post(
        f"/api/v1/prontuario/{cns}/alergia", json={"descricao": "Penicilina"}
    )
    assert response.status_code == 201
    assert response.json()["alergias"] == ["Penicilina"]

    # Duplicado con diferente capitalización → 422
    response = client.post(
        f"/api/v1/prontuario/{cns}/alergia", json={"descricao": "penicilina"}
    )
    assert response.status_code == 422

    # Descripción demasiado corta → 422 (validación del schema)
    response = client.post(
        f"/api/v1/prontuario/{cns}/alergia", json={"descricao": "A"}
    )
    assert response.status_code == 422


def test_registrar_problema_ciap2_y_cid10(client):
    """POST /prontuario/{cns}/problema: CIAP-2 y CID-10 aceptados (201)."""
    cns = _cns_unico()
    _crear_cidadao(client, cns, _cpf_unico())

    response = client.post(
        f"/api/v1/prontuario/{cns}/problema",
        json={
            "tipo_codigo": "CIAP2",
            "codigo": "K86",
            "descricao": "Hipertensión arterial",
        },
    )
    assert response.status_code == 201
    assert response.json()["codigo"] == "K86"
    assert response.json()["situacao"] == "ATIVO"

    response = client.post(
        f"/api/v1/prontuario/{cns}/problema",
        json={
            "tipo_codigo": "CID10",
            "codigo": "I10",
            "descricao": "Hipertensión esencial",
        },
    )
    assert response.status_code == 201
    assert response.json()["codigo"] == "I10"


def test_registrar_problema_duplicado_rechazado(client):
    """Problema duplicado (mismo código, no resuelto) debe dar 422."""
    cns = _cns_unico()
    _crear_cidadao(client, cns, _cpf_unico())

    payload = {
        "tipo_codigo": "CIAP2",
        "codigo": "K86",
        "descricao": "Hipertensión arterial",
    }
    assert client.post(f"/api/v1/prontuario/{cns}/problema", json=payload).status_code == 201
    # Duplicado con diferente capitalización → 422
    payload_dup = dict(payload, codigo="k86")
    assert client.post(f"/api/v1/prontuario/{cns}/problema", json=payload_dup).status_code == 422


def test_registrar_problema_codigo_malformado_rechazado(client):
    """Código fuera del patrón oficial de la terminología debe dar 422."""
    cns = _cns_unico()
    _crear_cidadao(client, cns, _cpf_unico())

    # CID-10 malformado (I1000 no es válido)
    response = client.post(
        f"/api/v1/prontuario/{cns}/problema",
        json={
            "tipo_codigo": "CID10",
            "codigo": "I1000",
            "descricao": "Código malformado",
        },
    )
    assert response.status_code == 422

    # Terminología no soportada
    response = client.post(
        f"/api/v1/prontuario/{cns}/problema",
        json={
            "tipo_codigo": "CID9",
            "codigo": "I10",
            "descricao": "Terminología no soportada",
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# CASO NEGATIVO: SOAP incompleto / rechazado
# ---------------------------------------------------------------------------

def test_atendimento_soap_incompleto_es_aceptado(client):
    """LAGUNA DE CALIDAD CLÍNICA: SOAP incompleto NO es rechazado.

    El método SOAP exige las 4 secciones (Subjetivo, Objetivo, Avaliação,
    Plano). El endpoint POST /atendimentos/ acepta un atendimiento con solo
    el motivo subjetivo (201) sin validar la completitud del SOAP.

    Este test documenta el comportamiento actual. Si se implementa la
    validación de completitud SOAP, este test deberá esperar 422.
    """
    cns = _cns_unico()
    cidadao_id = _crear_cidadao(client, cns, _cpf_unico())

    payload = {
        "cidadao_id": cidadao_id,
        "profissional_id": 1,
        "estabelecimento_id": 1,
        "subjetivo_motivo": "Paciente refiere dolor de cabeza",
        # objetivo_exame_fisico, avaliacao_notas, plano_conduta ausentes
        "problemas": [],
    }
    response = client.post("/api/v1/atendimentos/", json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["subjetivo_motivo"] == "Paciente refiere dolor de cabeza"
    assert response.json()["objetivo_exame_fisico"] is None
    assert response.json()["avaliacao_notas"] is None
    assert response.json()["plano_conduta"] is None


def test_atendimento_soap_cidadao_inexistente_devuelve_404(client):
    """Atendimiento SOAP de un ciudadano inexistente debe dar 404."""
    response = client.post(
        "/api/v1/atendimentos/",
        json={
            "cidadao_id": 999999,
            "profissional_id": 1,
            "estabelecimento_id": 1,
            "problemas": [],
        },
    )
    assert response.status_code == 404