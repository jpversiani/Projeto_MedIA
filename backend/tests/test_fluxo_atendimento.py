"""
Testes automatizados da máquina de estados do Fluxo Clínico e Perfis de Usuários.
MedIA Practice & Telemedicina OS.
"""

import pytest
from app.schemas.fluxo_atendimento import EtapaFluxoEnum, ModalidadeAtendimentoEnum


def test_obter_matriz_perfis(client):
    """Testa consulta da matriz de papéis (Médico, Recepção, Paciente, Admin, Farmacêutico)."""
    resp = client.get("/api/v1/fluxo-atendimento/perfis")
    assert resp.status_code == 200
    dados = resp.json()
    assert "perfis" in dados
    perfis = dados["perfis"]
    assert "MEDICO" in perfis
    assert "RECEPCAO" in perfis
    assert "PACIENTE" in perfis
    assert "ADMIN" in perfis
    assert "FARMACEUTICO" in perfis
    assert len(perfis["MEDICO"]["pre_consulta"]) > 0
    assert len(perfis["MEDICO"]["intra_consulta"]) > 0
    assert len(perfis["MEDICO"]["pos_consulta"]) > 0


def test_ciclo_completo_jornada_medica(client):
    """Testa o ciclo de vida completo de uma consulta médica (Agendamento -> Pré -> Intra -> Pós)."""
    # 1. Criar Agendamento
    payload_novo = {
        "paciente_nome": "Carolina Mendes Ribeiro",
        "paciente_cpf": "123.456.789-00",
        "paciente_telefone": "(31) 99887-6655",
        "medico_nome": "Dr. Lucas Bittencourt",
        "medico_crm": "CRM-MG 54.321",
        "especialidade": "Cardiologia",
        "modalidade": "TELEMEDICINA",
        "valor_honorarios": 400.00
    }
    resp_novo = client.post("/api/v1/fluxo-atendimento/novo-agendamento", json=payload_novo)
    assert resp_novo.status_code == 200
    dados_novo = resp_novo.json()
    consulta_id = dados_novo["consulta_id"]
    assert dados_novo["etapa_atual"] == "AGENDADA"
    assert dados_novo["checklist_pre"]["tcle_confirmado"] is False

    # 2. Registrar Pré-Consulta (Pre-Anamnese & TCLE eletrônico)
    payload_pre = {
        "pre_anamnese": {
            "motivo_consulta": "Palpitações ocasionais e elevação tensional noturna.",
            "sintomas_principais": ["Palpitação", "Cefaleia occipital"],
            "medicamentos_em_uso": ["Losartana 50mg"],
            "alergias_conhecidas": ["Nenhuma"],
            "pressao_arterial_recente": "142/92 mmHg"
        },
        "tcle_aceito": True,
        "pagamento_confirmado": True
    }
    resp_pre = client.post(f"/api/v1/fluxo-atendimento/{consulta_id}/pre-consulta", json=payload_pre)
    assert resp_pre.status_code == 200
    dados_pre = resp_pre.json()
    assert dados_pre["etapa_atual"] == "PRE_CONSULTA"
    assert dados_pre["checklist_pre"]["tcle_confirmado"] is True
    assert dados_pre["checklist_pre"]["pagamento_confirmado"] is True
    assert dados_pre["tcle_aceito"] is True

    # 3. Iniciar Atendimento Médico (Intra-Consulta com Carimbo Temporal CFM)
    resp_ini = client.post(f"/api/v1/fluxo-atendimento/{consulta_id}/iniciar")
    assert resp_ini.status_code == 200
    dados_ini = resp_ini.json()
    assert dados_ini["etapa_atual"] == "EM_ATENDIMENTO"
    assert dados_ini["data_hora_inicio"] is not None

    # 4. Salvar Evolução Intra-Consulta (SOAP, CID-11 Dual-Coding, Prescrição)
    payload_intra = {
        "consulta_id": consulta_id,
        "soap_subjetivo": "Paciente refere episódios de palpitações associados a estresse profissional.",
        "soap_objetivo": "PA: 140/90 mmHg, FC: 78 bpm. Ausculta cardíaca em 2T sem sopros.",
        "soap_avaliacao": "Hipertensão arterial estágio 1 não controlada e palpitações sinusais.",
        "soap_plano": "Otimização de anti-hipertensivo, MAPA 24h e ecocardiograma transtorácico.",
        "diagnosticos": [
            {
                "cid11_codigo": "BA00",
                "cid11_titulo": "Hipertensão essencial",
                "cid10_codigo": "I10"
            }
        ],
        "prescricoes": [
            {
                "nome_farmaco": "Losartana Potássica",
                "dosagem": "50 mg",
                "forma_farmaceutica": "Comprimido",
                "posologia": "Tomar 1 comprimido 12/12 horas",
                "duracao_dias": 60,
                "quantidade": "2 caixas",
                "tipo_receita": "SIMPLES"
            }
        ],
        "exames": [
            {"descricao_exame": "MAPA 24 Horas", "justificativa_clinica": "Avaliação de pico pressórico noturno"}
        ],
        "atestado": {
            "dias_afastamento": 1,
            "motivo_manifesto": "Comparecimento a consulta médica e realização de propedêutica",
            "incluir_cid": False
        }
    }
    resp_intra = client.post("/api/v1/fluxo-atendimento/intra-consulta/salvar", json=payload_intra)
    assert resp_intra.status_code == 200
    dados_intra = resp_intra.json()
    assert len(dados_intra["checklist_pre"]) > 0

    # 5. Finalizar Atendimento e Gerar Pacote Pós-Consulta
    payload_pos = {
        "consulta_id": consulta_id,
        "emitir_recibo_dmed": True,
        "lancar_livro_caixa": True,
        "dias_retorno_sugerido": 45,
        "canal_despacho_paciente": "WHATSAPP"
    }
    resp_pos = client.post("/api/v1/fluxo-atendimento/pos-consulta/finalizar", json=payload_pos)
    assert resp_pos.status_code == 200
    pacote = resp_pos.json()

    assert pacote["status"] == "FINALIZADA"
    assert pacote["codigo_verificador_receita"] is not None
    assert "CFM-" in pacote["codigo_verificador_receita"]
    assert pacote["codigo_verificador_atestado"] is not None
    assert "ATE-" in pacote["codigo_verificador_atestado"]
    assert "DMED-" in pacote["recibo_dmed_numero"]
    assert pacote["livro_caixa_id"] is not None
    # DARF é o do mês, calculado sobre o livro caixa real. Com uma única
    # consulta de R$ 400 (abaixo da faixa de isenção), o valor correto é 0,00 —
    # o código antigo inventava 15% do honorário e o teste exigia `> 0`.
    assert pacote["darf_carnê_leão_prevista"] >= 0
    assert pacote["darf_carnê_leão_prevista"] == 0.0
    assert "whatsapp" in pacote["link_whatsapp_despacho"].lower()
    assert "portal_paciente" in pacote["link_paciente_portal"].lower()


def test_jornada_inexistente_retorna_404(client):
    """Garante que IDs inexistentes geram HTTP 404 apropriado."""
    resp = client.get("/api/v1/fluxo-atendimento/CONS-NAO-EXISTE/jornada")
    assert resp.status_code == 404


def test_jornada_telemedicina_usa_codigo_real_da_sala(client, db_session):
    """TM-5: a `sala_virtual_url` usa o código REAL da sala, em `/static/`.

    Antes a URL era montada com o `consulta_id` (um id de jornada, não um
    código de sala) e no host errado (sem `/static/`): o link enviado ao
    paciente apontava para uma sala inexistente no WebSocket. Agora o link
    usa o `codigo_sala_telemedicina` persistido no agendamento da agenda.
    """
    from app.models.cidadao import Cidadao

    cidadao = db_session.query(Cidadao).filter(Cidadao.cpf == "12345678900").first()
    assert cidadao is not None

    resp_ag = client.post(
        "/api/v1/agenda/novo",
        json={
            "cidadao_id": cidadao.id,
            "tipo": "TELEMEDICINA",
            "horario": "11:00",
            "especialidade": "Clínica Médica",
            "motivo_queixa": "Retorno por telemedicina",
        },
    )
    assert resp_ag.status_code == 201, resp_ag.text
    agendamento = resp_ag.json()
    codigo_sala = agendamento["codigo_sala_telemedicina"]
    assert codigo_sala, "agendamento de telemedicina deve ter código de sala"

    resp_jornada = client.post(
        "/api/v1/fluxo-atendimento/novo-agendamento",
        json={
            "paciente_nome": "Paciente Sala Real",
            "paciente_cpf": "12345678900",
            "modalidade": "TELEMEDICINA",
            "agendamento_codigo": agendamento["codigo"],
        },
    )
    assert resp_jornada.status_code == 200
    jornada = resp_jornada.json()
    url = jornada["sala_virtual_url"]
    assert url is not None
    assert "/static/telemedicina_paciente.html" in url
    # O parâmetro `sala` é o código real da sala, nunca o id da jornada.
    assert url.endswith(f"?sala={codigo_sala}")
    assert f"sala={jornada['consulta_id']}" not in url


def test_jornada_sem_sala_nao_inventa_link(client):
    """Sem código de sala real a `sala_virtual_url` fica ``None``.

    O código antigo montava a URL com o `consulta_id`, gerando um link que
    abria uma sala inexistente — pior que nenhum link.
    """
    resp = client.post(
        "/api/v1/fluxo-atendimento/novo-agendamento",
        json={
            "paciente_nome": "Paciente Sem Sala",
            "paciente_cpf": "98765432100",
            "modalidade": "TELEMEDICINA",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["sala_virtual_url"] is None
