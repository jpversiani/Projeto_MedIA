"""Fluxo completo da consulta médica — Estágio 1: Teleconsulta (CFM 2.314/2022).

Cubre os endpoints REST de ``app.api.v1.telemedicina``:
- POST /telemedicina/agendamentos (criação de sala + teleconsulta)
- GET  /telemedicina/salas/{codigo_sala}
- POST /telemedicina/iniciar-chamada
- POST /telemedicina/finalizar-chamada
- POST /telemedicina/tcle/gerar
- POST /telemedicina/tcle/registrar
- GET  /telemedicina/link-paciente/{codigo_sala}
- POST /telemedicina/converter-presencial

Incluye o caso negativo crítico: iniciar a chamada sem TCLE registrado
(a Resolução CFM 2.314/2022 exige consentimento prévio; hoje o endpoint
NÃO valida o TCLE — o teste documenta o comportamento atual).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

# CPFs de teste (11 dígitos, sem uso em outros testes de cidadãos)
CPF_PACIENTE: str = "33344455566"
CPF_PACIENTE_2: str = "44455566677"
# CRM de 6 dígitos exigido pelo schema TeleconsultaCreate (agendamentos)
CRM_AGENDA: str = "123456"
# CRM livre (5 dígitos) usado nos endpoints TCLE/conversão (sem validação)
CRM_MEDICO: str = "78421"
UF_MEDICO: str = "MG"


def _crear_agendamento(client, cpf: str = CPF_PACIENTE, crm: str = CRM_AGENDA) -> dict:
    """Crea un agendamiento de teleconsulta e devuelve el JSON de respuesta."""
    payload = {
        "paciente_cpf": cpf,
        "medico_crm": crm,
        "data_hora": datetime.now(timezone.utc).isoformat(),
        "ciap2": "R74",
        "cid10": "J00",
    }
    response = client.post("/api/v1/telemedicina/agendamentos", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Agendamiento y sala virtual
# ---------------------------------------------------------------------------

def test_agendar_teleconsulta_crea_sala_y_consulta(client):
    """POST /telemedicina/agendamentos: 201 con sala y teleconsulta AGENDADA."""
    datos = _crear_agendamento(client)
    assert datos["id"] > 0
    assert datos["codigo_sala"].startswith("sala_")
    assert datos["paciente_cpf"] == CPF_PACIENTE
    assert datos["medico_crm"] == CRM_AGENDA
    assert datos["status"] == "AGENDADA"
    assert datos["data_hora"] is not None


def test_agendar_teleconsulta_rechaza_cpf_invalido(client):
    """CPF com menos de 11 dígitos deve gerar 422 (validação do schema)."""
    payload = {
        "paciente_cpf": "123",
        "medico_crm": CRM_AGENDA,
        "data_hora": datetime.now(timezone.utc).isoformat(),
    }
    response = client.post("/api/v1/telemedicina/agendamentos", json=payload)
    assert response.status_code == 422


def test_agendar_teleconsulta_rechaza_crm_invalido(client):
    """CRM que não seja exatamente 6 dígitos deve gerar 422."""
    payload = {
        "paciente_cpf": CPF_PACIENTE,
        "medico_crm": "78421",  # 5 dígitos
        "data_hora": datetime.now(timezone.utc).isoformat(),
    }
    response = client.post("/api/v1/telemedicina/agendamentos", json=payload)
    assert response.status_code == 422


def test_consultar_sala_virtual_por_codigo(client):
    """GET /telemedicina/salas/{codigo}: devuelve la sala con su teleconsulta."""
    datos = _crear_agendamento(client, cpf=CPF_PACIENTE_2)
    codigo_sala = datos["codigo_sala"]

    response = client.get(f"/api/v1/telemedicina/salas/{codigo_sala}")
    assert response.status_code == 200
    sala = response.json()
    assert sala["codigo"] == codigo_sala
    assert sala["teleconsulta_id"] == datos["id"]
    assert sala["paciente_cpf"] == CPF_PACIENTE_2
    assert sala["status"] == "AGENDADA"


def test_consultar_sala_inexistente_devuelve_404(client):
    """GET /telemedicina/salas/{codigo} con código desconocido debe dar 404."""
    response = client.get("/api/v1/telemedicina/salas/sala_no_existe_000")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Ciclo de chamada: iniciar / finalizar
# ---------------------------------------------------------------------------

def test_iniciar_y_finalizar_chamada_con_soap(client):
    """Ciclo completo: iniciar (EM_ANDAMENTO) y finalizar (CONCLUIDA) con SOAP."""
    datos = _crear_agendamento(client)
    consulta_id = datos["id"]

    inicio = client.post(
        "/api/v1/telemedicina/iniciar-chamada", json={"teleconsulta_id": consulta_id}
    )
    assert inicio.status_code == 200
    assert inicio.json()["status"] == "EM_ANDAMENTO"

    soap = {
        "subjetivo": "Paciente relata tosse seca de 3 días de evolución",
        "objetivo": "Afebril, murmullo vesicular conservado",
        "avaliacao": "Infección de vías aéreas superiores",
        "plano": "Hidratación oral y sintomáticos",
    }
    fin = client.post(
        "/api/v1/telemedicina/finalizar-chamada",
        json={"teleconsulta_id": consulta_id, "dados_soap": soap},
    )
    assert fin.status_code == 200
    assert fin.json()["status"] == "CONCLUIDA"


def test_iniciar_chamada_inexistente_devuelve_404(client):
    """Iniciar chamada de uma teleconsulta inexistente deve dar 404."""
    response = client.post(
        "/api/v1/telemedicina/iniciar-chamada", json={"teleconsulta_id": 999999}
    )
    assert response.status_code == 404


def test_finalizar_chamada_inexistente_devuelve_404(client):
    """Finalizar chamada de uma teleconsulta inexistente deve dar 404."""
    response = client.post(
        "/api/v1/telemedicina/finalizar-chamada", json={"teleconsulta_id": 999999}
    )
    assert response.status_code == 404


def test_iniciar_chamada_sin_tcle_registrado(client):
    """CASO NEGATIVO CRÍTICO: iniciar a chamada sem TCLE registrado.

    A Resolução CFM 2.314/2022 (Art. 4º) exige consentimento livre e
    informado ANTES da teleconsulta. O endpoint /iniciar-chamada NÃO
    consulta nenhun registro de TCLE: a chamada se inicia igualmente.

    Este teste documenta a LACUNA de segurança atual (não deve falhar a
    suíte): se no futuro se implementa o bloqueo, este teste deverá ser
    atualizado para esperar 409/403.
    """
    datos = _crear_agendamento(client)
    consulta_id = datos["id"]

    # Não se registra nenhun TCLE para este paciente/consulta
    response = client.post(
        "/api/v1/telemedicina/iniciar-chamada", json={"teleconsulta_id": consulta_id}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "EM_ANDAMENTO"


# ---------------------------------------------------------------------------
# TCLE (consentimiento) — CFM 2.314/2022
# ---------------------------------------------------------------------------

def test_tcle_gerar_retorna_texto_y_hash_sha256(client):
    """POST /telemedicina/tcle/gerar: texto integral + hash SHA-256."""
    response = client.post(
        "/api/v1/telemedicina/tcle/gerar",
        json={
            "paciente_nome": "Paciente Flujo Consulta",
            "paciente_cpf": CPF_PACIENTE,
            "medico_nome": "Dr. João Paulo Versiani",
            "medico_crm": CRM_MEDICO,
            "medico_uf": UF_MEDICO,
            "medico_rqe": "39412",
            "especialidade": "Clínica Médica",
            "modalidade": "TELECONSULTA",
        },
    )
    assert response.status_code == 200
    tcle = response.json()
    assert tcle["norma_regulamentar"] == "CFM-2314/2022"
    assert "TERMO DE CONSENTIMENTO LIVRE E ESCLARECIDO" in tcle["texto_integral"]
    assert "CRM: 78421-MG" in tcle["texto_integral"]
    assert CPF_PACIENTE in tcle["texto_integral"]
    assert len(tcle["hash_integridade_sha256"]) == 64


def test_tcle_registrar_aceite_auditado(client):
    """POST /telemedicina/tcle/registrar: registro auditado com hash."""
    response = client.post(
        "/api/v1/telemedicina/tcle/registrar",
        json={
            "paciente_nome": "Paciente Flujo Consulta",
            "paciente_cpf": CPF_PACIENTE,
            "metodo": "ELETRONICO_WEB",
            "ip_origem": "127.0.0.1",
        },
    )
    assert response.status_code == 200
    registro = response.json()
    assert registro["consentimento_id"].startswith("TCLE-")
    assert registro["paciente_cpf"] == CPF_PACIENTE
    assert registro["metodo_aceite"] == "ELETRONICO_WEB"
    assert registro["status"] == "VALIDADO_CFM_2314"
    assert len(registro["hash_tcle"]) == 64


# ---------------------------------------------------------------------------
# Link del paciente
# ---------------------------------------------------------------------------

def test_link_paciente_genera_url_y_whatsapp(client):
    """GET /telemedicina/link-paciente/{codigo}: URL efímera + WhatsApp."""
    datos = _crear_agendamento(client)
    codigo_sala = datos["codigo_sala"]

    response = client.get(
        f"/api/v1/telemedicina/link-paciente/{codigo_sala}",
        params={
            "paciente_nome": "Paciente Flujo Consulta",
            "medico_nome": "Dr. João Paulo Versiani",
            "telefone": "38991234567",
        },
    )
    assert response.status_code == 200
    link = response.json()
    assert codigo_sala in link["url_acesso_paciente"]
    assert "telemedicina_paciente.html" in link["url_acesso_paciente"]
    assert "Paciente Flujo Consulta" in link["mensagem_formatada"]
    assert link["link_whatsapp_direto"].startswith("https://api.whatsapp.com/send?phone=55")


# ---------------------------------------------------------------------------
# Conversión a presencial (Art. 3º CFM)
# ---------------------------------------------------------------------------

def test_converter_presencial_registra_motivo_y_hash(client):
    """POST /telemedicina/converter-presencial: registro con motivo y hash.

    El endpoint emite el registro de conversión (Art. 3º CFM) con hash
    SHA-256 del relatorio. Nota: la teleconsulta se marca CANCELADA en BD
    pero la SalaVirtual conserva su status (AGENDADA) — laguna de
    consistencia documentada en el informe.
    """
    datos = _crear_agendamento(client)
    consulta_id = datos["id"]

    response = client.post(
        "/api/v1/telemedicina/converter-presencial",
        json={
            "teleconsulta_id": consulta_id,
            "paciente_nome": "Paciente Flujo Consulta",
            "motivo_clinico": "Dolor precordial con sudoración fría, sospecha de síndrome coronario agudo.",
            "medico_nome": "Dr. João Paulo Versiani",
            "medico_crm": CRM_MEDICO,
            "medico_uf": UF_MEDICO,
        },
    )
    assert response.status_code == 200
    resultado = response.json()
    assert resultado["status"] == "CONVERTIDA_PRESENCIAL"
    assert "ART. 3º CFM 2.314/2022" in resultado["relatorio"]
    assert len(resultado["hash_registro"]) == 64


def test_converter_presencial_teleconsulta_inexistente(client):
    """Convertir una teleconsulta inexistente: el registro se emite igualmente.

    El endpoint no valida la existencia de la teleconsulta (solo la cancela
    si existe). Documenta el comportamiento actual.
    """
    response = client.post(
        "/api/v1/telemedicina/converter-presencial",
        json={
            "teleconsulta_id": 999999,
            "paciente_nome": "Paciente Flujo Consulta",
            "motivo_clinico": "Motivo clínico de prueba.",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CONVERTIDA_PRESENCIAL"