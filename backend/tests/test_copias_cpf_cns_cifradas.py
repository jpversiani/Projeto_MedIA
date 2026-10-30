"""P0-7b — cópias de CPF/CNS cifradas nas tabelas operacionais.

Antes, o cadastro mestre (`cidadaos`/`profissionais`) era cifrado, mas as
**cópias** do mesmo documento continuavam em texto claro em 11 tabelas
(receita, dispensação, guia TISS, financeiro, livro caixa, jornada,
contingência offline, mensageria e teleconsulta) — um dump parcial do banco
ainda expunha a identificação do paciente (LGPD art. 46).

O que estes testes garantem:

1. o **banco** guarda ciphertext nas 20 colunas de texto, no `xml_tiss` e nos
   campos de CPF/CNS embutidos nos JSONs (`payload_json`, `dados_json`);
2. o **ORM** devolve texto claro (contrato da API intacto), inclusive nos
   vizinhos do JSON (hash de integridade, itens, checklist);
3. comparar o texto claro com uma coluna cifrada **sem** índice cego falha
   alto (`ErroCriptografia`), em vez de devolver resultado vazio em silêncio;
4. busca parcial (`LIKE`/`startswith`) em campo cifrado também falha alto;
5. a política de retenção continua anonimizando CNS/CPF;
6. o inventário do modelo e o da migração `b6e8f24a91d7` não divergem.
"""

from __future__ import annotations

import importlib.util
import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import select, text

from app.core.database import Base
from app.core.crypto import (
    CampoProtegido,
    ErroCriptografia,
    JsonProtegido,
    PREFIXO,
    TextoProtegido,
)
from app.models.atendimento_offline import AtendimentoOffline
from app.models.cidadao import Cidadao
from app.models.convenios import GuiaTISS, LancamentoFinanceiro
from app.models.documento_clinico import DocumentoClinicoEmitido
from app.models.farmacia import Dispensacao, Receita
from app.models.financeiro import LancamentoLivroCaixa
from app.models.jornada import JornadaAtendimento
from app.models.mensageria import AlertaBuscaAtiva, MensagemPreventiva
from app.models.telemedicina import Teleconsulta

CPF = "52998224725"
CNS = "700123456789012"
CNS_PROFISSIONAL = "898000123456789"
XML_TISS = (
    '<?xml version="1.0"?><guiaTiss><cpf>52998224725</cpf>'
    "<cns>700123456789012</cns><cid>E11.9</cid></guiaTiss>"
)
MIGRACAO = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "b6e8f24a91d7_cifrar_copias_cpf_cns.py"
)


def _sucesso() -> str:
    return uuid.uuid4().hex


def _valor_bruto(db, sql: str, **params):
    """Lê direto do banco, sem passar pelo TypeDecorator."""
    return db.execute(text(sql), params).all()


# ---------------------------------------------------------------------------
# Persistência: banco cifra, ORM devolve claro
# ---------------------------------------------------------------------------
def test_receita_e_dispensacao_guardam_ciphertext(db_session):
    receita = Receita(
        codigo_hash=_sucesso(),
        cns_paciente=CNS,
        cpf_paciente=CPF,
        prescritor_nome="Dra. Teste",
        prescritor_cns=CNS_PROFISSIONAL,
        prescritor_registro="CRM-TESTE",
        unidade_cnes="3180115",
        data_validade=date(2030, 1, 1),
    )
    db_session.add(
        Dispensacao(
            receita=receita,
            tipo="TOTAL",
            farmaceutico_nome="Farm. Teste",
            farmaceutico_cns=CNS_PROFISSIONAL,
            farmaceutico_cpf=CPF,
            unidade_cnes="3180115",
        )
    )
    db_session.commit()
    db_session.expire_all()

    bruto = _valor_bruto(
        db_session,
        "SELECT cns_paciente, cpf_paciente, prescritor_cns FROM receitas "
        "WHERE codigo_hash = :h",
        h=receita.codigo_hash,
    )[0]
    assert all(str(v).startswith(PREFIXO) for v in bruto)
    assert CNS not in str(bruto[0]) and CPF not in str(bruto[0])
    assert CPF not in str(bruto[1])
    assert CNS_PROFISSIONAL not in str(bruto[2])

    dispensacao = db_session.query(Dispensacao).filter_by(receita_id=receita.id).one()
    assert dispensacao.farmaceutico_cns == CNS_PROFISSIONAL
    assert dispensacao.farmaceutico_cpf == CPF
    assert dispensacao.receita.cns_paciente == CNS
    assert dispensacao.receita.cpf_paciente == CPF


def test_documento_clinico_cifra_coluna_e_campo_do_payload_json(db_session):
    payload = {
        "paciente_cpf": CPF,
        "paciente_nome": "Paciente Cifrado",
        "hash_integridade_sha256": "f" * 64,
        "itens": [{"farmaco": "Metformina", "posologia": "850mg 2x/dia"}],
    }
    codigo = f"CFM-{_sucesso()[:12].upper()}"
    db_session.add(
        DocumentoClinicoEmitido(
            codigo_validacao=codigo,
            tipo_documento="PRESCRICAO",
            paciente_nome="Paciente Cifrado",
            paciente_cpf=CPF,
            medico_nome="Dr. Teste",
            medico_crm="123456",
            medico_uf="MG",
            hash_integridade_sha256="f" * 64,
            payload_json=payload,
        )
    )
    db_session.commit()
    db_session.expire_all()

    bruto_cpf, bruto_payload = _valor_bruto(
        db_session,
        "SELECT paciente_cpf, payload_json FROM documentos_clinicos "
        "WHERE codigo_validacao = :c",
        c=codigo,
    )[0]
    assert str(bruto_cpf).startswith(PREFIXO) and CPF not in str(bruto_cpf)

    objeto = json.loads(bruto_payload)
    assert objeto["paciente_cpf"].startswith(PREFIXO)
    assert CPF not in objeto["paciente_cpf"]
    # Os vizinhos do payload continuam legíveis: o hash de integridade precisa
    # ser recalculável e o PDF precisa ser regerável a partir deles.
    assert objeto["hash_integridade_sha256"] == "f" * 64
    assert objeto["itens"][0]["farmaco"] == "Metformina"
    assert objeto["paciente_nome"] == "Paciente Cifrado"

    registro = (
        db_session.query(DocumentoClinicoEmitido).filter_by(codigo_validacao=codigo).one()
    )
    assert registro.paciente_cpf == CPF
    assert registro.payload_json == payload


def test_xml_tiss_cifrado_no_banco_e_devolvido_inteiro(db_session):
    guia = GuiaTISS(
        numero_guia=f"GUIA-{_sucesso()[:12].upper()}",
        paciente_nome="Paciente Cifrado",
        xml_tiss=XML_TISS,
    )
    db_session.add(guia)
    db_session.commit()
    db_session.expire_all()

    bruto = _valor_bruto(
        db_session,
        "SELECT xml_tiss, paciente_cns, paciente_cpf FROM guias_tiss WHERE id = :id",
        id=guia.id,
    )[0]
    assert str(bruto[0]).startswith(PREFIXO)
    assert "52998224725" not in str(bruto[0])
    assert bruto[1] is None and bruto[2] is None

    registro = db_session.get(GuiaTISS, guia.id)
    assert registro.xml_tiss == XML_TISS
    assert "<cid>E11.9</cid>" in registro.xml_tiss


def test_jornada_dados_json_cifra_cpfs_e_preserva_o_resto(db_session):
    # Payload completo, como o serviço persiste (a listagem de jornadas hidrata
    # todas as linhas do banco e valida contra JornadaAtendimentoOut).
    dados = {
        "paciente_cpf": CPF,
        "paciente_cns": CNS,
        "paciente_telefone": "(31) 99999-0000",
        "especialidade": "Clínica Médica",
        "medico_crm": "CRM-MG 12345",
        "data_hora_agendamento": "2026-10-30 14:00",
        "valor_honorarios": 250.0,
        "etapa_atual": "EM_ATENDIMENTO",
        "checklist_pre": {
            "tcle_confirmado": True,
            "pagamento_confirmado": True,
            "pre_anamnese_preenchida": True,
            "historico_revisado_medico": False,
            "dispositivo_testado": True,
        },
        "tcle_aceito": True,
        "tcle_timestamp": "2026-10-30 13:55:00 UTC",
    }
    consulta_id = f"CONS-{_sucesso()[:16].upper()}"
    db_session.add(
        JornadaAtendimento(
            consulta_id=consulta_id,
            paciente_nome="Paciente Cifrado",
            paciente_cpf=CPF,
            medico_nome="Dr. Teste",
            modalidade="PRESENCIAL",
            dados_json=dados,
        )
    )
    db_session.commit()
    db_session.expire_all()

    bruto = _valor_bruto(
        db_session,
        "SELECT paciente_cpf, dados_json FROM jornadas_atendimento "
        "WHERE consulta_id = :c",
        c=consulta_id,
    )[0]
    assert str(bruto[0]).startswith(PREFIXO) and CPF not in str(bruto[0])
    objeto = json.loads(bruto[1])
    assert objeto["paciente_cpf"].startswith(PREFIXO)
    assert objeto["paciente_cns"].startswith(PREFIXO)
    assert objeto["etapa_atual"] == "EM_ATENDIMENTO"
    assert objeto["checklist_pre"]["tcle_confirmado"] is True
    assert objeto["especialidade"] == "Clínica Médica"
    assert objeto["valor_honorarios"] == 250.0

    registro = (
        db_session.query(JornadaAtendimento).filter_by(consulta_id=consulta_id).one()
    )
    assert registro.paciente_cpf == CPF
    assert registro.dados_json == dados


def test_lancamentos_financeiros_e_livro_caixa_cifrados(db_session):
    sufixo = _sucesso()[:8]
    nome_paciente = f"Paciente Cifrado {sufixo}"
    descricao = f"Consulta {sufixo}"
    db_session.add_all(
        [
            LancamentoFinanceiro(
                paciente_cpf=CPF,
                paciente_nome=nome_paciente,
                valor=150.0,
                cpf_cnpj_pagador=CPF,
            ),
            LancamentoLivroCaixa(
                tipo="RECEITA",
                data_competencia=date(2026, 1, 1),
                descricao=descricao,
                valor=150.0,
                paciente_cpf=CPF,
            ),
        ]
    )
    db_session.commit()
    db_session.expire_all()

    financeiro = _valor_bruto(
        db_session,
        "SELECT paciente_cpf, cpf_cnpj_pagador FROM lancamentos_financeiros "
        "WHERE paciente_nome = :n",
        n=nome_paciente,
    )[0]
    assert all(str(v).startswith(PREFIXO) for v in financeiro)
    assert CPF not in str(financeiro[0])

    caixa = _valor_bruto(
        db_session,
        "SELECT paciente_cpf FROM lancamentos_livro_caixa WHERE descricao = :d",
        d=descricao,
    )[0][0]
    assert str(caixa).startswith(PREFIXO) and CPF not in str(caixa)

    registro = (
        db_session.query(LancamentoFinanceiro)
        .filter_by(paciente_nome=nome_paciente)
        .one()
    )
    assert registro.paciente_cpf == CPF
    assert registro.cpf_cnpj_pagador == CPF
    livro = (
        db_session.query(LancamentoLivroCaixa).filter_by(descricao=descricao).one()
    )
    assert livro.paciente_cpf == CPF


def test_atendimento_offline_cifra_identificadores(db_session):
    registro = AtendimentoOffline(
        id_local=str(uuid.uuid4()),
        cns_cidadao=CNS,
        cpf_cidadao=CPF,
        profissional_cns=CNS_PROFISSIONAL,
        data_hora_atendimento=datetime.now(timezone.utc),
    )
    db_session.add(registro)
    db_session.commit()
    db_session.expire_all()

    bruto = _valor_bruto(
        db_session,
        "SELECT cns_cidadao, cpf_cidadao, profissional_cns FROM atendimentos_offline "
        "WHERE id_local = :i",
        i=registro.id_local,
    )[0]
    assert all(str(v).startswith(PREFIXO) for v in bruto)
    assert all(CNS not in str(v) and CPF not in str(v) for v in bruto)

    recarregado = (
        db_session.query(AtendimentoOffline)
        .filter_by(id_local=registro.id_local)
        .one()
    )
    assert recarregado.cns_cidadao == CNS
    assert recarregado.cpf_cidadao == CPF
    assert recarregado.profissional_cns == CNS_PROFISSIONAL


def test_mensageria_e_alertas_cifram_cns_e_cpf(db_session):
    sufixo = _sucesso()[:8]
    nome_destinatario = f"Paciente Cifrado {sufixo}"
    db_session.add_all(
        [
            MensagemPreventiva(
                chave_idempotencia=_sucesso(),
                tipo_alerta="LEMBRETE_TELECONSULTA",
                canal="WHATSAPP",
                telefone="31999990000",
                nome_destinatario=nome_destinatario,
                cns=CNS,
                cpf=CPF,
                texto="Lembrete de teleconsulta.",
            ),
            AlertaBuscaAtiva(
                chave_idempotencia=_sucesso(),
                tipo="BUSCA_ATIVA_CRONICO",
                nome=nome_destinatario,
                prioridade="MEDIA",
                ciap2="T90",
                cid10="E11.9",
                descricao="Diabético sem acompanhamento",
                cns=CNS,
                cpf=CPF,
            ),
        ]
    )
    db_session.commit()
    db_session.expire_all()

    mensagem = (
        db_session.query(MensagemPreventiva)
        .filter_by(nome_destinatario=nome_destinatario)
        .one()
    )
    alerta = db_session.query(AlertaBuscaAtiva).filter_by(nome=nome_destinatario).one()

    bruto = _valor_bruto(
        db_session,
        "SELECT cns, cpf FROM mensagens_preventivas WHERE id = :id",
        id=mensagem.id,
    )[0]
    assert all(str(v).startswith(PREFIXO) for v in bruto)
    assert CNS not in str(bruto[0]) and CPF not in str(bruto[1])

    bruto_alerta = _valor_bruto(
        db_session,
        "SELECT cns, cpf FROM alertas_busca_ativa WHERE id = :id",
        id=alerta.id,
    )[0]
    assert all(str(v).startswith(PREFIXO) for v in bruto_alerta)

    assert mensagem.cns == CNS and mensagem.cpf == CPF
    assert alerta.cns == CNS and alerta.cpf == CPF


def test_teleconsulta_cpf_cifrado(db_session):
    consulta = Teleconsulta(paciente_cpf=CPF)
    db_session.add(consulta)
    db_session.commit()
    db_session.expire_all()

    bruto = _valor_bruto(
        db_session,
        "SELECT paciente_cpf FROM teleconsultas WHERE id = :id",
        id=consulta.id,
    )[0][0]
    assert str(bruto).startswith(PREFIXO) and CPF not in str(bruto)

    assert db_session.get(Teleconsulta, consulta.id).paciente_cpf == CPF


def test_coluna_legada_sem_cifrar_continua_legivel(db_session):
    """Transição: linha anterior à migração não pode quebrar a leitura."""
    codigo = f"CFM-{_sucesso()[:12].upper()}"
    db_session.execute(
        text(
            "INSERT INTO documentos_clinicos (codigo_validacao, tipo_documento, "
            "paciente_nome, paciente_cpf, medico_nome, medico_crm, medico_uf, "
            "hash_integridade_sha256, data_emissao, status) VALUES "
            "(:c, 'PRESCRICAO', 'Paciente Legado', :cpf, 'Dr. Teste', '123456', "
            "'MG', :h, '2026-01-01 00:00:00', 'VALIDA')"
        ),
        {"c": codigo, "cpf": CPF, "h": "f" * 64},
    )
    db_session.commit()

    registro = (
        db_session.query(DocumentoClinicoEmitido).filter_by(codigo_validacao=codigo).one()
    )
    assert registro.paciente_cpf == CPF


# ---------------------------------------------------------------------------
# Comparador: falha alto em vez de resultado vazio
# ---------------------------------------------------------------------------
def test_comparar_coluna_cifrada_sem_indice_cego_falta_alto(db_session):
    """`WHERE cns_paciente = ?` casaria com zero linhas — é um erro, não uma busca.

    O ``operate`` do comparador dispara na **construção** da expressão, por
    isso a montagem inteira fica dentro do ``raises``.
    """
    with pytest.raises(ErroCriptografia, match="ndice cego"):
        select(Receita).where(Receita.cns_paciente == CNS)

    with pytest.raises(ErroCriptografia, match="ndice cego"):
        select(AtendimentoOffline).where(
            AtendimentoOffline.cns_cidadao.in_([CNS])
        )


def test_busca_parcial_em_campo_cifrado_falta_alto(db_session):
    """`LIKE`/`startswith` sobre ciphertext devolveria sempre vazio."""
    with pytest.raises(ErroCriptografia, match="Busca parcial"):
        select(Cidadao).where(Cidadao.cpf.like("%52998224725%"))

    with pytest.raises(ErroCriptografia, match="Busca parcial"):
        select(Teleconsulta).where(Teleconsulta.paciente_cpf.startswith("529"))


def test_igualdade_com_literal_de_tipo_errado_tambem_falta_alto(db_session):
    with pytest.raises(ErroCriptografia, match="texto"):
        select(Receita).where(Receita.cpf_paciente == 52998224725)


def test_igualdade_com_hash_e_is_null_continuam_normais(db_session):
    """O caminho com índice cego e o `IS NULL` não podem ser afetados."""
    com_hash = str(select(Cidadao).where(Cidadao.cpf == CPF))
    assert "cpf_hash" in com_hash

    nulo = select(AtendimentoOffline).where(AtendimentoOffline.cpf_cidadao.is_(None))
    assert "IS NULL" in str(nulo)

    igual_a_nada = select(Receita).where(Receita.cpf_paciente.isnot(None))
    assert "IS NOT NULL" in str(igual_a_nada)


# ---------------------------------------------------------------------------
# Retenção (LGPD art. 16): anonimização segue funcionando com o tipo cifrado
# ---------------------------------------------------------------------------
def test_retencao_anonimiza_cns_e_cpf_de_mensagens_e_alertas(db_session):
    from app.services.retencao_dados import ServicoRetencao

    mensagem = MensagemPreventiva(
        chave_idempotencia=_sucesso(),
        tipo_alerta="BUSCA_ATIVA_CRONICO",
        canal="SMS",
        telefone="31999990001",
        nome_destinatario="Paciente Antigo",
        cns=CNS,
        cpf=CPF,
        texto="Mensagem antiga.",
        criado_em=datetime(2020, 1, 1),
    )
    alerta = AlertaBuscaAtiva(
        chave_idempotencia=_sucesso(),
        tipo="BUSCA_ATIVA_VACINAL",
        nome="Paciente Antigo",
        prioridade="BAIXA",
        ciap2="A96",
        cid10="Z23",
        descricao="Vacina atrasada",
        cns=CNS,
        cpf=CPF,
        data_alerta=datetime(2020, 1, 1),
    )
    db_session.add_all([mensagem, alerta])
    db_session.commit()

    relatorio = ServicoRetencao().executar(
        db_session,
        confirmar=True,
        regras=(
            "mensagens_preventivas_antigas",
            "alertas_busca_ativa_antigos",
        ),
    )
    # Pode alcançar > 2 se o seed também tiver mensagens/alertas antigos.
    assert relatorio["total_afetado"] >= 2

    db_session.expire_all()
    reg_mensagem = db_session.get(MensagemPreventiva, mensagem.id)
    reg_alerta = db_session.get(AlertaBuscaAtiva, alerta.id)
    assert reg_mensagem.cns is None and reg_mensagem.cpf is None
    assert reg_alerta.cns is None and reg_alerta.cpf is None

    bruto = _valor_bruto(
        db_session,
        "SELECT cns, cpf FROM mensagens_preventivas WHERE id = :id",
        id=mensagem.id,
    )[0]
    assert tuple(bruto) == (None, None), (
        "sobrou ciphertext de CPF/CNS após anonimização"
    )


# ---------------------------------------------------------------------------
# Inventário: modelo e migração não podem divergir
# ---------------------------------------------------------------------------
def _carregar_migração():
    espec = importlib.util.spec_from_file_location("mig_p07b_copias", MIGRACAO)
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


def test_inventario_do_modelo_coincide_com_a_migrao():
    """Toda coluna cifrada do modelo está na migração — e vice-versa.

    Se alguém criar uma cópia de CPF num modelo sem lançar a migração de
    dados, esta comparação falha antes que o dado permaneça em texto claro.
    """
    mig = _carregar_migração()

    texto_modelo = {
        (tabela.name, nome)
        for tabela in Base.metadata.tables.values()
        for nome, coluna in tabela.c.items()
        if isinstance(coluna.type, CampoProtegido)
    }
    texto_migrao = {(t, c) for t, c, _m in mig.COLUNAS_TEXTO} | set(
        mig.COLUNAS_LONGAS
    )
    cadastro_mestre = {
        ("cidadaos", "cpf"),
        ("cidadaos", "cns"),
        ("profissionais", "cpf"),
        ("profissionais", "cns"),
    }
    # Tabelas novas que já NASCEM com a coluna cifrada (sem dado legado a
    # migrar: a própria criação da tabela usa CampoProtegido).
    nascidas_cifradas = {
        ("consentimentos_teleconsulta", "paciente_cpf"),
    }
    assert texto_modelo == texto_migrao | cadastro_mestre | nascidas_cifradas

    json_modelo = {
        (tabela.name, nome): tuple(sorted(coluna.type.campos))
        for tabela in Base.metadata.tables.values()
        for nome, coluna in tabela.c.items()
        if isinstance(coluna.type, JsonProtegido)
    }
    json_migrao = {
        (t, c): tuple(sorted(campos)) for t, c, campos in mig.COLUNAS_JSON
    }
    assert json_modelo == json_migrao
    assert json_modelo, "os payloads JSON protegidos sumiram do modelo"

    xml = Base.metadata.tables["guias_tiss"].c["xml_tiss"]
    assert isinstance(xml.type, TextoProtegido)
