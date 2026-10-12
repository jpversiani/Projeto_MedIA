"""Teste de integração do fluxo presencial de ponta a ponta.

Este é o teste que faltava. A auditoria do fluxo presencial mostrou que
nenhum teste encadeava agenda → fila → atendimento: cada módulo era testado
isoladamente, então a suíte passava mesmo com o fluxo quebrado em três pontos
(o agendamento não tinha `cidadao_id`, não havia check-in, e o Cockpit nunca
gravava o SOAP).

Aqui o caminho é exercitado inteiro, com as mesmas chamadas que o front-end
faz, e o resultado é verificado no banco:

    agenda → check-in → fila → atendimento SOAP → prontuário → histórico

Se qualquer elo se romper, este teste falha.
"""
from datetime import date

from app.models.agendamento import Agendamento
from app.models.atendimento import AtendimentoSOAP
from app.models.cidadao import Cidadao
from app.models.fila import FilaAcolhimento


def _cidadao(db_session) -> Cidadao:
    cidadao = db_session.query(Cidadao).filter(Cidadao.cpf == "12345678900").first()
    assert cidadao is not None
    return cidadao


def _estabelecimento_id(db_session) -> int:
    from app.models.estabelecimento import Estabelecimento

    return db_session.query(Estabelecimento).first().id


def _profissional_id(db_session) -> int:
    from app.models.profissional import Profissional

    return db_session.query(Profissional).first().id


def _cidadao_exclusivo(client, cpf: str, nome: str) -> int:
    """Cria (ou reutiliza) um cidadão só deste teste.

    A suíte compartilha um único banco em memória entre todos os arquivos, então
    apagar tabelas inteiras para "limpar" o cenário quebra outros testes que
    contam registros. Cada teste deste módulo usa um paciente próprio, e assim
    não interfere em ninguém.
    """
    existente = client.get(f"/api/v1/cidadaos/?busca={cpf}").json()
    if existente:
        return existente[0]["id"]

    resposta = client.post(
        "/api/v1/cidadaos/",
        json={
            "cns": "898" + cpf.zfill(12)[:12],
            "cpf": cpf,
            "nome_completo": nome,
            "data_nascimento": "1980-01-01",
            "sexo": "F",
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


def test_fluxo_presencial_completo(client, db_session):
    """Do agendamento ao prontuário, tudo persistido e encadeado."""
    cidadao_id = _cidadao_exclusivo(client, "55511122233", "Paciente Fluxo Presencial")
    est_id = _estabelecimento_id(db_session)
    prof_id = _profissional_id(db_session)

    # ------------------------------------------------------------------
    # 1. Recepção agenda a consulta
    # ------------------------------------------------------------------
    resposta = client.post(
        "/api/v1/agenda/novo",
        json={
            "cidadao_id": cidadao_id,
            "tipo": "PRESENCIAL",
            "horario": "09:00",
            "especialidade": "Clínica Médica",
            "motivo_queixa": "Cefaleia há 3 dias",
            "valor_consulta": 300.0,
            "profissional_id": prof_id,
            "estabelecimento_id": est_id,
        },
    )
    assert resposta.status_code == 201, resposta.text
    agendamento = resposta.json()
    assert agendamento["cidadao_id"] == cidadao_id
    assert agendamento["status"] == "AGENDADO"

    # ------------------------------------------------------------------
    # 2. Paciente chega e faz check-in — entra na fila de acolhimento
    # ------------------------------------------------------------------
    checkin = client.post(
        f"/api/v1/agenda/{agendamento['codigo']}/checkin?classificacao_risco=AMARELO"
    )
    assert checkin.status_code == 201, checkin.text
    dados_checkin = checkin.json()
    fila_id = dados_checkin["fila_id"]
    assert dados_checkin["status_agendamento"] == "SALA_DE_ESPERA"

    # O paciente aparece na fila, com o mesmo cidadão
    fila = client.get("/api/v1/fila/?status=AGUARDANDO_ATENDIMENTO").json()
    item_fila = next((i for i in fila if i["id"] == fila_id), None)
    assert item_fila is not None, "paciente não entrou na fila"
    assert item_fila["cidadao_id"] == cidadao_id

    # ------------------------------------------------------------------
    # 3. Médico atende e grava o SOAP
    # ------------------------------------------------------------------
    atendimento = client.post(
        "/api/v1/atendimentos/",
        json={
            "cidadao_id": cidadao_id,
            "profissional_id": prof_id,
            "estabelecimento_id": est_id,
            "fila_id": fila_id,
            "subjetivo_motivo": "Cefaleia occipital há 3 dias",
            "subjetivo_notas": "Sem febre. Nega trauma.",
            "objetivo_exame_fisico": "PA 138x90. Oroscopia sem alterações.",
            "avaliacao_notas": "Hipertensão arterial suspeita",
            "plano_prescricoes": "Losartana 50mg 1x/dia",
            "plano_exames": "Hemograma, creatinina",
            "problemas": [
                {
                    "tipo_codigo": "CIAP2",
                    "codigo": "K86",
                    "descricao": "Hipertensão arterial sem complicações",
                    "situacao": "ATIVO",
                }
            ],
        },
    )
    assert atendimento.status_code == 201, atendimento.text
    gravado = atendimento.json()
    atendimento_id = gravado["id"]
    assert gravado["cidadao_id"] == cidadao_id
    assert gravado["problemas"], "o problema CIAP-2 não foi gravado"

    # ------------------------------------------------------------------
    # 4. A fila foi finalizada pelo atendimento
    # ------------------------------------------------------------------
    db_session.expire_all()
    entrada = db_session.query(FilaAcolhimento).filter(FilaAcolhimento.id == fila_id).first()
    assert entrada.status is not None
    assert entrada.status == "FINALIZADO", (
        f"a fila deveria estar FINALIZADO, está {entrada.status}"
    )

    # ------------------------------------------------------------------
    # 5. O atendimento está no prontuário do paciente
    # ------------------------------------------------------------------
    historico = client.get(f"/api/v1/cidadaos/{cidadao_id}/historico")
    assert historico.status_code == 200
    ids = [a["id"] for a in historico.json()]
    assert atendimento_id in ids, "o atendimento não aparece no histórico do paciente"

    # ------------------------------------------------------------------
    # 6. O médico conclui o agendamento
    # ------------------------------------------------------------------
    conclusao = client.patch(
        f"/api/v1/agenda/{agendamento['codigo']}/status?novo_status=CONCLUIDO"
    )
    assert conclusao.status_code == 200
    assert conclusao.json()["status"] == "CONCLUIDO"

    # ------------------------------------------------------------------
    # 7. Tudo sobreviveu no banco
    # ------------------------------------------------------------------
    db_session.expire_all()
    assert db_session.query(AtendimentoSOAP).filter(
        AtendimentoSOAP.id == atendimento_id
    ).first() is not None
    assert db_session.query(Agendamento).filter(
        Agendamento.codigo == agendamento["codigo"]
    ).first() is not None


def test_agendamento_sem_cidadao_nao_permite_atendimento(client, db_session):
    """Um agendamento não vinculado a cidadão é recusado na origem.

    Antes o vínculo não existia: era possível agendar com um CPF em texto livre
    que não correspondia a ninguém, e o paciente nunca chegava ao prontuário.
    """
    resposta = client.post(
        "/api/v1/agenda/novo",
        json={
            "paciente_cpf": "00000000000",  # não cadastrado
            "tipo": "PRESENCIAL",
            "horario": "10:00",
        },
    )
    assert resposta.status_code == 404


def test_prontuario_exige_vinculo_com_cidadao(client, db_session):
    """Atendimento para cidadão inexistente é recusado."""
    est_id = _estabelecimento_id(db_session)
    prof_id = _profissional_id(db_session)

    resposta = client.post(
        "/api/v1/atendimentos/",
        json={
            "cidadao_id": 999999,
            "profissional_id": prof_id,
            "estabelecimento_id": est_id,
            "subjetivo_motivo": "Teste",
        },
    )
    assert resposta.status_code == 404


def test_historico_do_cidadao_mostra_agendamentos(client, db_session):
    """O histórico de agendamentos é recuperável pelo paciente."""
    cidadao_id = _cidadao_exclusivo(client, "55544433322", "Paciente Historico")

    client.post(
        "/api/v1/agenda/novo",
        json={"cidadao_id": cidadao_id, "tipo": "PRESENCIAL", "horario": "11:00"},
    )

    agendamentos = client.get(f"/api/v1/agenda/cidadao/{cidadao_id}")
    assert agendamentos.status_code == 200
    assert len(agendamentos.json()) >= 1
    assert agendamentos.json()[0]["data_consulta"] == date.today().isoformat()
