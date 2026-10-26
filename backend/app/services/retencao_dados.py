"""Política de retenção e anonimização de dados (LGPD Art. 15/16/18).

O problema que este módulo resolve: o sistema guardava tudo para sempre. CPF,
CNS, telefone e nome de paciente ficavam em tabelas operacionais mesmo depois de
a finalidade ter acabado — cópias de contingência já sincronizadas, mensagens de
WhatsApp de dois anos atrás, salas virtuais com link expirado, refresh tokens
mortos. Guardar além do necessário é risco desnecessário (LGPD Art. 15/16) e
aumenta o impacto de qualquer vazamento.

O que **não** é feito aqui, de propósito: o prontuário não é apagado nem
anonimizado automaticamente. A Resolução CFM nº 1.821/2007 e a nº 2.314/2022
exigem guarda mínima de **20 anos** do registro clínico, e a decisão de anonimizar
um registro clínico é jurídica, não automática. Por isso a regra de cidadãos é
somente **REVISAR**: ela informa quantos cadastros estão sem movimento há mais de
20 anos para que uma pessoa decida, com registro em auditoria.

Três tipos de ação:

* ``EXPURGAR``  — apaga a linha (dado operacional cuja finalidade terminou);
* ``ENCERRAR``  — mantém a linha por integridade referencial, mas inutiliza o
  dado (sala virtual sem link, por exemplo);
* ``ANONIMIZAR``— substitui os identificadores diretos, preservando a linha para
  estatística;
* ``REVISAR``   — apenas relata; nunca altera nada.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence

from sqlalchemy.orm import Session

from app.models.atendimento_offline import AtendimentoOffline, StatusSincronizacao
from app.models.cidadao import Cidadao
from app.models.mensageria import AlertaBuscaAtiva, MensagemPreventiva
from app.models.telemedicina import SalaVirtual, StatusTeleconsulta
from app.models.usuario import AuditTrail, RefreshToken

logger = logging.getLogger(__name__)

# Marcador gravado no lugar do dado pessoal. Não é reversível e deixa claro, para
# quem ler o banco, que a remoção foi intencional e não uma falha de carga.
MARCADOR_ANONIMIZACAO = "[anonimizado]"


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _como_utc(valor: datetime) -> datetime:
    """Normaliza para UTC *aware*.

    O SQLite devolve ``datetime`` sem ``tzinfo`` mesmo quando a coluna foi gravada
    com fuso. Comparar um ``datetime`` naive com um aware levanta ``TypeError`` —
    então tudo passa por aqui antes de qualquer conta.
    """
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


class ExecucaoNaoConfirmada(Exception):
    """``executar()`` foi chamado sem ``confirmar=True``.

    Existe porque a operação é destrutiva e irreversível: apagar por engano não
    tem desfazer. Quem chama (CLI ou endpoint) precisa dizer que sabe disso.
    """


@dataclass
class ResultadoRegra:
    """Quanto uma regra afetaria (ou afetou) — usado no plano e no relatório."""

    regra: str
    descricao: str
    acao: str
    base_legal: str
    retencao_dias: int
    afetados: int = 0
    executado: bool = False

    def como_dicionario(self) -> Dict[str, Any]:
        return {
            "regra": self.regra,
            "descricao": self.descricao,
            "acao": self.acao,
            "base_legal": self.base_legal,
            "retencao_dias": self.retencao_dias,
            "afetados": self.afetados,
            "executado": self.executado,
        }


@dataclass
class RegraRetencao:
    """Uma regra declarativa: qual tabela, por quanto tempo, e o que fazer."""

    identificador: str
    descricao: str
    acao: str
    base_legal: str
    retencao_dias: int
    contar: Any  # Callable[[Session, datetime], int]
    aplicar: Optional[Any] = None  # Callable[[Session, datetime], int]
    campos_anonimizados: Sequence[str] = field(default_factory=tuple)


# =========================================================================
# Regras
# =========================================================================
def _contar_refresh_tokens(db: Session, limite: datetime) -> int:
    return (
        db.query(RefreshToken)
        .filter(
            (RefreshToken.expires_at < limite)
            | (RefreshToken.revoked_at.isnot(None) & (RefreshToken.revoked_at < limite))
        )
        .count()
    )


def _expurgar_refresh_tokens(db: Session, limite: datetime) -> int:
    return (
        db.query(RefreshToken)
        .filter(
            (RefreshToken.expires_at < limite)
            | (RefreshToken.revoked_at.isnot(None) & (RefreshToken.revoked_at < limite))
        )
        .delete(synchronize_session=False)
    )


def _contar_salas_expiradas(db: Session, limite: datetime) -> int:
    return (
        db.query(SalaVirtual)
        .filter(
            SalaVirtual.data_expiracao.isnot(None),
            SalaVirtual.data_expiracao < limite,
            SalaVirtual.status.in_(
                [StatusTeleconsulta.AGENDADA, StatusTeleconsulta.EM_ANDAMENTO]
            ),
        )
        .count()
    )


def _encerrar_salas_expiradas(db: Session, limite: datetime) -> int:
    salas = (
        db.query(SalaVirtual)
        .filter(
            SalaVirtual.data_expiracao.isnot(None),
            SalaVirtual.data_expiracao < limite,
            SalaVirtual.status.in_(
                [StatusTeleconsulta.AGENDADA, StatusTeleconsulta.EM_ANDAMENTO]
            ),
        )
        .all()
    )
    for sala in salas:
        # Não apagamos a sala: `teleconsultas.sala_virtual_id` aponta para ela.
        # Inutilizar o link resolve o risco sem quebrar a integridade.
        sala.status = StatusTeleconsulta.CONCLUIDA
        sala.url_video = None
    return len(salas)


def _contar_offline_sincronizados(db: Session, limite: datetime) -> int:
    return (
        db.query(AtendimentoOffline)
        .filter(
            AtendimentoOffline.status == StatusSincronizacao.RECEBIDO,
            AtendimentoOffline.criado_em < limite,
        )
        .count()
    )


def _expurgar_offline_sincronizados(db: Session, limite: datetime) -> int:
    return (
        db.query(AtendimentoOffline)
        .filter(
            AtendimentoOffline.status == StatusSincronizacao.RECEBIDO,
            AtendimentoOffline.criado_em < limite,
        )
        .delete(synchronize_session=False)
    )


def _contar_mensagens_antigas(db: Session, limite: datetime) -> int:
    return (
        db.query(MensagemPreventiva)
        .filter(
            MensagemPreventiva.criado_em < limite,
            MensagemPreventiva.telefone != MARCADOR_ANONIMIZACAO,
        )
        .count()
    )


def _anonimizar_mensagens_antigas(db: Session, limite: datetime) -> int:
    mensagens = (
        db.query(MensagemPreventiva)
        .filter(
            MensagemPreventiva.criado_em < limite,
            MensagemPreventiva.telefone != MARCADOR_ANONIMIZACAO,
        )
        .all()
    )
    for mensagem in mensagens:
        # A linha fica: o histórico de campanha ("quantas mensagens enviamos em
        # janeiro") continua válido sem identificar ninguém.
        mensagem.telefone = MARCADOR_ANONIMIZACAO
        mensagem.nome_destinatario = MARCADOR_ANONIMIZACAO
        mensagem.cns = None
        mensagem.cpf = None
    return len(mensagens)


def _contar_alertas_antigos(db: Session, limite: datetime) -> int:
    return (
        db.query(AlertaBuscaAtiva)
        .filter(
            AlertaBuscaAtiva.data_alerta < limite,
            AlertaBuscaAtiva.nome != MARCADOR_ANONIMIZACAO,
        )
        .count()
    )


def _anonimizar_alertas_antigos(db: Session, limite: datetime) -> int:
    alertas = (
        db.query(AlertaBuscaAtiva)
        .filter(
            AlertaBuscaAtiva.data_alerta < limite,
            AlertaBuscaAtiva.nome != MARCADOR_ANONIMIZACAO,
        )
        .all()
    )
    for alerta in alertas:
        alerta.nome = MARCADOR_ANONIMIZACAO
        alerta.cns = None
        alerta.cpf = None
    return len(alertas)


def _candidatos_revisao_cidadaos(db: Session, limite: datetime) -> int:
    """Cadastros sem atendimento recente — apenas **relatório**, nunca apaga.

    A guarda de 20 anos do prontuário (CFM 1.821/2007) e a decisão sobre
    anonimizar registro clínico são humanas. Esta regra só dá o número.
    """
    from app.models.atendimento import AtendimentoSOAP

    total = 0
    for cidadao in db.query(Cidadao).all():
        ultimo = (
            db.query(AtendimentoSOAP)
            .filter(AtendimentoSOAP.cidadao_id == cidadao.id)
            .order_by(AtendimentoSOAP.data_hora_inicio.desc())
            .first()
        )
        referencia = (
            _como_utc(ultimo.data_hora_inicio)
            if ultimo and ultimo.data_hora_inicio
            else _como_utc(cidadao.created_at)
            if cidadao.created_at
            else None
        )
        if referencia is not None and referencia < limite:
            total += 1
    return total


def _contar_trilha_antiga(db: Session, limite: datetime) -> int:
    return db.query(AuditTrail).filter(AuditTrail.timestamp < limite).count()


# A ordem importa para leitura do relatório: do mais efêmero ao mais sensível.
REGRAS_PADRAO: Sequence[RegraRetencao] = (
    RegraRetencao(
        identificador="refresh_tokens_expirados",
        descricao="Refresh tokens expirados ou revogados",
        acao="EXPURGAR",
        base_legal="LGPD Art. 15/16 (minimização) — token não tem finalidade após expirar",
        retencao_dias=30,
        contar=_contar_refresh_tokens,
        aplicar=_expurgar_refresh_tokens,
    ),
    RegraRetencao(
        identificador="salas_virtuais_expiradas",
        descricao="Salas virtuais com link expirado (link inutilizado, sala preservada)",
        acao="ENCERRAR",
        base_legal="LGPD Art. 15/16 — o link é credencial temporária",
        retencao_dias=7,
        contar=_contar_salas_expiradas,
        aplicar=_encerrar_salas_expiradas,
        campos_anonimizados=("url_video",),
    ),
    RegraRetencao(
        identificador="atendimentos_offline_sincronizados",
        descricao="Cópias de contingência já sincronizadas (dado vive no prontuário)",
        acao="EXPURGAR",
        base_legal="LGPD Art. 16, II — finalidade cumprida; conteúdo preservado no prontuário",
        retencao_dias=90,
        contar=_contar_offline_sincronizados,
        aplicar=_expurgar_offline_sincronizados,
    ),
    RegraRetencao(
        identificador="mensagens_preventivas_antigas",
        descricao="Mensagens de WhatsApp/SMS com telefone, nome, CNS e CPF",
        acao="ANONIMIZAR",
        base_legal="LGPD Art. 16 — histórico de campanha sem identificação direta",
        retencao_dias=365,
        contar=_contar_mensagens_antigas,
        aplicar=_anonimizar_mensagens_antigas,
        campos_anonimizados=("telefone", "nome_destinatario", "cns", "cpf"),
    ),
    RegraRetencao(
        identificador="alertas_busca_ativa_antigos",
        descricao="Alertas de busca ativa encerrados com nome, CNS e CPF",
        acao="ANONIMIZAR",
        base_legal="LGPD Art. 16 — indicador epidemiológico sem identificação direta",
        retencao_dias=730,
        contar=_contar_alertas_antigos,
        aplicar=_anonimizar_alertas_antigos,
        campos_anonimizados=("nome", "cns", "cpf"),
    ),
    RegraRetencao(
        identificador="cidadaos_sem_movimento_20_anos",
        descricao="Cadastros sem atendimento há mais de 20 anos (exige decisão humana)",
        acao="REVISAR",
        base_legal="CFM 1.821/2007 e 2.314/2022 (guarda mínima de 20 anos do prontuário)",
        retencao_dias=365 * 20,
        contar=_candidatos_revisao_cidadaos,
    ),
    RegraRetencao(
        identificador="trilha_auditoria_antiga",
        descricao="Eventos de auditoria com mais de 5 anos (não são apagados aqui)",
        acao="REVISAR",
        base_legal="LGPD Art. 37 — registro das operações deve ser mantido; expurgo exige política própria",
        retencao_dias=365 * 5,
        contar=_contar_trilha_antiga,
    ),
)


class ServicoRetencao:
    """Avalia e aplica a política de retenção sobre o banco."""

    def __init__(self, regras: Optional[Sequence[RegraRetencao]] = None):
        self.regras = tuple(regras) if regras is not None else REGRAS_PADRAO

    # ------------------------------------------------------------------
    # Plano (somente leitura)
    # ------------------------------------------------------------------
    def plano(self, db: Session, agora: Optional[datetime] = None) -> List[ResultadoRegra]:
        """Calcula o que cada regra faria — sem alterar nada."""
        referencia = agora or _agora_utc()
        resultados: List[ResultadoRegra] = []
        for regra in self.regras:
            limite = referencia - timedelta(days=regra.retencao_dias)
            try:
                afetados = regra.contar(db, limite)
            except Exception as erro:  # pragma: no cover - defensivo
                logger.warning("Regra %s falhou ao contar: %s", regra.identificador, erro)
                afetados = 0
            resultados.append(
                ResultadoRegra(
                    regra=regra.identificador,
                    descricao=regra.descricao,
                    acao=regra.acao,
                    base_legal=regra.base_legal,
                    retencao_dias=regra.retencao_dias,
                    afetados=afetados,
                )
            )
        return resultados

    # ------------------------------------------------------------------
    # Execução
    # ------------------------------------------------------------------
    def executar(
        self,
        db: Session,
        agora: Optional[datetime] = None,
        *,
        regras: Optional[Iterable[str]] = None,
        confirmar: bool = False,
        usuario_id: Optional[int] = None,
        ip_origem: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Aplica as regras destrutivas. Exige ``confirmar=True``.

        Regras ``REVISAR`` nunca são executadas: elas só aparecem no relatório.
        """
        if not confirmar:
            raise ExecucaoNaoConfirmada(
                "A retenção apaga dados de forma irreversível. Chame com confirmar=True "
                "(CLI: --executar; API: {\"confirmar\": true})."
            )

        referencia = agora or _agora_utc()
        desejadas = set(regras) if regras else None

        resultados: List[ResultadoRegra] = []
        total = 0

        for regra in self.regras:
            if desejadas is not None and regra.identificador not in desejadas:
                continue
            if regra.acao == "REVISAR" or regra.aplicar is None:
                continue

            limite = referencia - timedelta(days=regra.retencao_dias)
            afetados = regra.aplicar(db, limite)
            total += afetados
            resultados.append(
                ResultadoRegra(
                    regra=regra.identificador,
                    descricao=regra.descricao,
                    acao=regra.acao,
                    base_legal=regra.base_legal,
                    retencao_dias=regra.retencao_dias,
                    afetados=afetados,
                    executado=True,
                )
            )

        db.commit()

        relatorio = {
            "executado_em": referencia.isoformat(),
            "total_afetado": total,
            "regras": [r.como_dicionario() for r in resultados],
        }

        # A execução precisa deixar rastro: quem rodou, quando e quantos registros
        # cada regra tocou. Sem isso não há como provar o cumprimento do Art. 16.
        try:
            from app.services.audit_service import AuditService

            AuditService.registrar_evento(
                db=db,
                acao="EXECUTAR_RETENCAO_DADOS",
                usuario_id=usuario_id,
                recurso_tipo="PoliticaRetencao",
                recurso_id="lgpd-art-16",
                ip_address=ip_origem,
                detalhes=relatorio,
            )
        except Exception as erro:  # pragma: no cover - defensivo
            logger.warning("Não foi possível auditar a execução da retenção: %s", erro)

        return relatorio
