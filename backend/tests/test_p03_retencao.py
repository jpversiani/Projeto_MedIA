"""Testes da política de retenção e anonimização (P0.3 / LGPD Art. 16).

O que precisa ficar provado:

* o **plano** nunca altera nada;
* o que já cumpriu finalidade é expurgado (refresh token, cópia offline, link);
* o que identifica pessoa é **anonimizado** preservando a linha estatística;
* dado recente **não** é tocado;
* registro **clínico** nunca é apagado — a guarda de 20 anos do prontuário não é
  violada por um cron;
* executar sem confirmação falha alto e não altera nada;
* a execução deixa rastro na trilha de auditoria e é idempotente.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.models.atendimento_offline import AtendimentoOffline, StatusSincronizacao
from app.models.cidadao import Cidadao
from app.models.mensageria import AlertaBuscaAtiva, MensagemPreventiva
from app.models.telemedicina import SalaVirtual, StatusTeleconsulta
from app.models.usuario import AuditTrail, RefreshToken
from app.services.retencao_dados import (
    MARCADOR_ANONIMIZACAO,
    ExecucaoNaoConfirmada,
    ServicoRetencao,
)

AGORA = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)


def _dias_atras(dias: int) -> datetime:
    return AGORA - timedelta(days=dias)


# ----------------------------------------------------------------------
# Construtores auxiliares
# ----------------------------------------------------------------------
def _mensagem(db, *, dias: int, telefone="38999887766", status="ENVIADO"):
    # O banco da suíte é único para toda a sessão (StaticPool): a chave de
    # idempotência precisa ser única por teste, não por valor de campo.
    mensagem = MensagemPreventiva(
        chave_idempotencia=f"msg-{uuid4().hex[:12]}",
        tipo_alerta="BUSCA_ATIVA_VACINAL",
        canal="WHATSAPP",
        telefone=telefone,
        nome_destinatario="Maria da Silva",
        cns="898001160000000",
        cpf="12345678901",
        texto="Compareça à UBS para vacinação.",
        status=status,
        criado_em=_dias_atras(dias),
    )
    db.add(mensagem)
    db.commit()
    db.refresh(mensagem)
    return mensagem


def _alerta(db, *, dias: int):
    alerta = AlertaBuscaAtiva(
        chave_idempotencia=f"alerta-{uuid4().hex[:12]}",
        tipo="BUSCA_ATIVA_CRONICO",
        nome="João Pereira",
        cns="898001160000001",
        cpf="98765432100",
        prioridade="ALTA",
        ciap2="T90",
        cid10="E11",
        descricao="Diabético sem consulta há 8 meses",
        data_alerta=_dias_atras(dias),
    )
    db.add(alerta)
    db.commit()
    db.refresh(alerta)
    return alerta


def _refresh_token(db, *, expira_dias: int, revogado_dias=None):
    token = RefreshToken(
        jti=f"jti-{uuid4().hex[:12]}",
        usuario_id=1,
        expires_at=_dias_atras(expira_dias),
        revoked_at=_dias_atras(revogado_dias) if revogado_dias is not None else None,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def _sala(db, *, expira_dias: int, status=StatusTeleconsulta.AGENDADA):
    sala = SalaVirtual(
        codigo_sala=f"sala_ret_{uuid4().hex[:12]}",
        url_video="https://video.exemplo/sala",
        status=status,
        data_criacao=_dias_atras(expira_dias + 1),
        data_expiracao=_dias_atras(expira_dias),
    )
    db.add(sala)
    db.commit()
    db.refresh(sala)
    return sala


def _offline(db, *, dias: int, status=StatusSincronizacao.RECEBIDO, sufixo="a"):
    registro = AtendimentoOffline(
        id_local=f"{uuid4().hex[:8]}-{uuid4().hex[:8]}-{uuid4().hex[:8]}",
        cns_cidadao="898001160000002",
        cpf_cidadao="11122233344",
        data_hora_atendimento=_dias_atras(dias),
        subjetivo="Dor de cabeça",
        status=status,
        criado_em=_dias_atras(dias),
        recebido_em=_dias_atras(dias),
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


# ----------------------------------------------------------------------
# Plano
# ----------------------------------------------------------------------
def test_plano_relata_sem_alterar_nada(db_session):
    mensagem = _mensagem(db_session, dias=800)
    token = _refresh_token(db_session, expira_dias=90)

    plano = ServicoRetencao().plano(db_session, agora=AGORA)
    por_regra = {item.regra: item for item in plano}

    assert por_regra["mensagens_preventivas_antigas"].afetados == 1
    assert por_regra["refresh_tokens_expirados"].afetados == 1
    assert all(item.executado is False for item in plano)

    # Nada foi alterado pelo plano.
    db_session.refresh(mensagem)
    db_session.refresh(token)
    assert mensagem.telefone == "38999887766"
    assert db_session.query(RefreshToken).filter(RefreshToken.id == token.id).count() == 1


def test_plano_traz_base_legal_em_todas_as_regras(db_session):
    plano = ServicoRetencao().plano(db_session, agora=AGORA)
    assert plano, "a política não pode ser vazia"
    for regra in plano:
        assert regra.base_legal, f"regra {regra.regra} sem base legal"
        assert regra.acao in {"EXPURGAR", "ENCERRAR", "ANONIMIZAR", "REVISAR"}


# ----------------------------------------------------------------------
# Anonimização
# ----------------------------------------------------------------------
def test_anonimiza_mensagem_antiga_preservando_a_linha(db_session):
    mensagem = _mensagem(db_session, dias=400)
    mensagem_id = mensagem.id

    ServicoRetencao().executar(db_session, agora=AGORA, confirmar=True)

    db_session.expire_all()
    atualizada = (
        db_session.query(MensagemPreventiva)
        .filter(MensagemPreventiva.id == mensagem_id)
        .one()
    )
    assert atualizada.telefone == MARCADOR_ANONIMIZACAO
    assert atualizada.nome_destinatario == MARCADOR_ANONIMIZACAO
    assert atualizada.cns is None
    assert atualizada.cpf is None
    # A linha continua existindo: o histórico de campanha ainda é útil.
    assert atualizada.tipo_alerta == "BUSCA_ATIVA_VACINAL"
    assert atualizada.texto.startswith("Compareça")


def test_nao_toca_mensagem_recente(db_session):
    recente = _mensagem(db_session, dias=30, telefone="38988887777")

    ServicoRetencao().executar(db_session, agora=AGORA, confirmar=True)

    db_session.refresh(recente)
    assert recente.telefone == "38988887777"
    assert recente.nome_destinatario == "Maria da Silva"


def test_anonimiza_alerta_antigo(db_session):
    alerta = _alerta(db_session, dias=800)
    alerta_id = alerta.id

    ServicoRetencao().executar(db_session, agora=AGORA, confirmar=True)

    db_session.expire_all()
    atualizado = (
        db_session.query(AlertaBuscaAtiva)
        .filter(AlertaBuscaAtiva.id == alerta_id)
        .one()
    )
    assert atualizado.nome == MARCADOR_ANONIMIZACAO
    assert atualizado.cns is None and atualizado.cpf is None
    # Indicador epidemiológico continua válido sem identificar ninguém.
    assert atualizado.ciap2 == "T90" and atualizado.cid10 == "E11"


# ----------------------------------------------------------------------
# Expurgo e encerramento
# ----------------------------------------------------------------------
def test_expurga_refresh_token_expirado_e_preserva_o_valido(db_session):
    expirado = _refresh_token(db_session, expira_dias=90)
    expirado_id = expirado.id
    valido = _refresh_token(db_session, expira_dias=-5)  # expira no futuro
    valido_id = valido.id

    ServicoRetencao().executar(db_session, agora=AGORA, confirmar=True)

    restantes = {t.id for t in db_session.query(RefreshToken).all()}
    assert expirado_id not in restantes
    assert valido_id in restantes


def test_expurga_refresh_token_revogado(db_session):
    revogado = _refresh_token(db_session, expira_dias=60, revogado_dias=45)
    revogado_id = revogado.id

    ServicoRetencao().executar(db_session, agora=AGORA, confirmar=True)

    assert (
        db_session.query(RefreshToken).filter(RefreshToken.id == revogado_id).count() == 0
    )


def test_encerra_sala_com_link_expirado_sem_apagar_a_sala(db_session):
    sala = _sala(db_session, expira_dias=30)
    sala_id = sala.id

    ServicoRetencao().executar(db_session, agora=AGORA, confirmar=True)

    db_session.expire_all()
    atualizada = db_session.query(SalaVirtual).filter(SalaVirtual.id == sala_id).one()
    # A linha permanece: `teleconsultas.sala_virtual_id` aponta para ela.
    assert atualizada.status == StatusTeleconsulta.CONCLUIDA
    assert atualizada.url_video is None


def test_nao_encerra_sala_ainda_valida(db_session):
    sala = _sala(db_session, expira_dias=-3)  # expira no futuro

    ServicoRetencao().executar(db_session, agora=AGORA, confirmar=True)

    db_session.refresh(sala)
    assert sala.status == StatusTeleconsulta.AGENDADA
    assert sala.url_video is not None


def test_expurga_copia_offline_ja_sincronizada(db_session):
    sincronizado = _offline(db_session, dias=120, status=StatusSincronizacao.RECEBIDO)
    sincronizado_id = sincronizado.id
    pendente = _offline(db_session, dias=120, status=StatusSincronizacao.PENDENTE, sufixo="b")
    pendente_id = pendente.id

    ServicoRetencao().executar(db_session, agora=AGORA, confirmar=True)

    ids = {r.id for r in db_session.query(AtendimentoOffline).all()}
    assert sincronizado_id not in ids
    # Ainda não subiu para o prontuário: apagar seria perda de dado clínico.
    assert pendente_id in ids


# ----------------------------------------------------------------------
# Registro clínico protegido
# ----------------------------------------------------------------------
def test_prontuario_nunca_e_apagado_nem_anonimizado(db_session):
    # CPF/CNS exclusivos deste teste: o banco da suíte é compartilhado e
    # `test_prontuario.py` usa 55566677788 — reutilizar aquele CPF fazia o POST
    # dele falhar com 400 (registro duplicado) por causa da ordem de execução.
    cidadao = Cidadao(
        cns="898001160000777",
        cpf="11122233399",
        nome_completo="Paciente Histórico",
        data_nascimento=datetime(1950, 1, 1).date(),
        sexo="F",
        telefone="38977776666",
    )
    db_session.add(cidadao)
    db_session.commit()
    db_session.refresh(cidadao)
    cidadao_id = cidadao.id

    # O cadastro está "sem movimento" há mais de 20 anos.
    cidadao.created_at = _dias_atras(365 * 25)
    db_session.commit()

    plano = ServicoRetencao().plano(db_session, agora=AGORA)
    revisao = {item.regra: item for item in plano}["cidadaos_sem_movimento_20_anos"]
    assert revisao.acao == "REVISAR"
    assert revisao.afetados >= 1

    ServicoRetencao().executar(db_session, agora=AGORA, confirmar=True)

    db_session.expire_all()
    atual = db_session.query(Cidadao).filter(Cidadao.id == cidadao_id).one()
    assert atual.nome_completo == "Paciente Histórico"
    assert atual.cpf == "11122233399"
    assert atual.telefone == "38977776666"


def test_trilha_de_auditoria_e_apenas_relatada(db_session):
    antigo = AuditTrail(
        usuario_id=None,
        acao="LOGIN_SUCESSO",
        recurso_tipo="Usuario",
        recurso_id="1",
        timestamp=_dias_atras(365 * 6),
        hash_anterior=None,
        hash_integridade="x" * 64,
    )
    db_session.add(antigo)
    db_session.commit()
    antigo_id = antigo.id

    ServicoRetencao().executar(db_session, agora=AGORA, confirmar=True)

    assert db_session.query(AuditTrail).filter(AuditTrail.id == antigo_id).count() == 1


# ----------------------------------------------------------------------
# Segurança de execução
# ----------------------------------------------------------------------
def test_executar_sem_confirmacao_nao_altera_nada(db_session):
    mensagem = _mensagem(db_session, dias=800)

    with pytest.raises(ExecucaoNaoConfirmada):
        ServicoRetencao().executar(db_session, agora=AGORA, confirmar=False)

    db_session.refresh(mensagem)
    assert mensagem.telefone == "38999887766"


def test_execucao_e_idempotente(db_session):
    _mensagem(db_session, dias=800)
    servico = ServicoRetencao()

    primeiro = servico.executar(db_session, agora=AGORA, confirmar=True)
    segundo = servico.executar(db_session, agora=AGORA, confirmar=True)

    assert primeiro["total_afetado"] >= 1
    assert segundo["total_afetado"] == 0


def test_execucao_deixa_rastro_na_auditoria(db_session):
    _mensagem(db_session, dias=800)

    ServicoRetencao().executar(
        db_session, agora=AGORA, confirmar=True, usuario_id=None, ip_origem="127.0.0.1"
    )

    evento = (
        db_session.query(AuditTrail)
        .filter(AuditTrail.acao == "EXECUTAR_RETENCAO_DADOS")
        .order_by(AuditTrail.id.desc())
        .first()
    )
    assert evento is not None
    assert "total_afetado" in (evento.detalhes_json or "")


def test_pode_restringir_a_execucao_a_uma_regra(db_session):
    _mensagem(db_session, dias=800)
    token = _refresh_token(db_session, expira_dias=90)
    token_id = token.id

    relatorio = ServicoRetencao().executar(
        db_session,
        agora=AGORA,
        regras=["mensagens_preventivas_antigas"],
        confirmar=True,
    )

    executadas = {item["regra"] for item in relatorio["regras"]}
    assert executadas == {"mensagens_preventivas_antigas"}
    # O token não foi tocado porque a regra não foi selecionada.
    assert db_session.query(RefreshToken).filter(RefreshToken.id == token_id).count() == 1


# ----------------------------------------------------------------------
# API
# ----------------------------------------------------------------------
def test_api_plano_de_retencao(client, db_session):
    _mensagem(db_session, dias=800)

    resposta = client.get("/api/v1/conformidade/retencao")
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert "regras" in corpo and corpo["regras"]
    assert corpo["total_afetavel"] >= 1
    assert "não altera dados" in corpo["aviso"]


def test_api_executar_sem_confirmar_retorna_400(client, db_session):
    _mensagem(db_session, dias=800)

    resposta = client.post(
        "/api/v1/conformidade/retencao/executar", json={"confirmar": False}
    )
    assert resposta.status_code == 400
    assert "confirmar" in resposta.json()["detail"].lower()
