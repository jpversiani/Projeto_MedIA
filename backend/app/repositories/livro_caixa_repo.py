"""Repositório do livro caixa do médico (receitas e despesas persistidas).

A rota ``/financeiro-medico/livro-caixa/demonstrativo`` devolvia dados
*hardcoded* — cinco consultas e três despesas fictícias, com nomes e CPFs de
pacientes que não existem. Este módulo substitui a semente por leitura real da
tabela ``lancamentos_livro_caixa``, escopada por estabelecimento (tenant).

O cálculo fiscal continua em ``MotorLivroCaixaMedico`` (tabela progressiva do
IRPF); aqui só se resolve a origem dos dados.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.financeiro import LancamentoLivroCaixa, TipoLancamento
from app.services.livro_caixa import (
    LancamentoDespesa,
    LancamentoReceita,
    MotorLivroCaixaMedico,
)

ORIGEM_MANUAL = "MANUAL"
ORIGEM_FLUXO = "FLUXO_ATENDIMENTO"

COMPETENCIA_PADRAO = "%m/%Y"


def normalizar_competencia(mes_ano: str, referencia: Optional[date] = None) -> str:
    """Aceita ``MM/AAAA`` (e ``AAAA-MM``) e devolve sempre ``MM/AAAA``.

    Competência inválida vira erro de contrato (422 na rota), e não um
    demonstrativo zerado silencioso.
    """
    texto = (mes_ano or "").strip()
    if not texto:
        hoje = referencia or date.today()
        return f"{hoje.month:02d}/{hoje.year}"

    if "/" in texto:
        partes = texto.split("/")
    elif "-" in texto:
        partes = texto.split("-")[::-1]
    else:
        raise ValueError("Competência inválida: use MM/AAAA.")

    if len(partes) != 2:
        raise ValueError("Competência inválida: use MM/AAAA.")

    mes_txt, ano_txt = partes
    try:
        mes = int(mes_txt)
        ano = int(ano_txt)
    except ValueError as exc:  # pragma: no cover - mensagem depende do input
        raise ValueError("Competência inválida: use MM/AAAA.") from exc

    if not 1 <= mes <= 12:
        raise ValueError("Mês inválido: use um valor entre 01 e 12.")
    if not 1900 <= ano <= 2200:
        raise ValueError("Ano inválido.")

    return f"{mes:02d}/{ano}"


def intervalo_competencia(mes_ano: str) -> tuple[date, date]:
    """Primeiro e último dia da competência (inclusive)."""
    mes, ano = (int(parte) for parte in mes_ano.split("/"))
    inicio = date(ano, mes, 1)
    if mes == 12:
        fim = date(ano + 1, 1, 1)
    else:
        fim = date(ano, mes + 1, 1)
    return inicio, fim


def _filtrar(
    query,
    *,
    mes_ano: str,
    estabelecimento_id: Optional[int],
    profissional_id: Optional[int],
):
    inicio, fim = intervalo_competencia(mes_ano)
    query = query.where(
        LancamentoLivroCaixa.data_competencia >= inicio,
        LancamentoLivroCaixa.data_competencia < fim,
    )
    if estabelecimento_id is not None:
        query = query.where(
            LancamentoLivroCaixa.estabelecimento_id == estabelecimento_id
        )
    if profissional_id is not None:
        query = query.where(
            LancamentoLivroCaixa.profissional_id == profissional_id
        )
    return query


class LivroCaixaRepo:
    """Acesso ao livro caixa persistido."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Escrita
    # ------------------------------------------------------------------
    def registrar(self, lancamento: LancamentoLivroCaixa) -> LancamentoLivroCaixa:
        """Insere (sem commit) um lançamento e devolve o objeto com id."""
        if lancamento.chave_idempotencia:
            existente = self.db.scalar(
                select(LancamentoLivroCaixa).where(
                    LancamentoLivroCaixa.chave_idempotencia
                    == lancamento.chave_idempotencia
                )
            )
            if existente is not None:
                return existente
        self.db.add(lancamento)
        self.db.flush()
        return lancamento

    def registrar_receita(
        self,
        *,
        data_competencia: date,
        descricao: str,
        valor: float | Decimal,
        paciente_nome: Optional[str] = None,
        paciente_cpf: Optional[str] = None,
        modalidade: Optional[str] = None,
        numero_recibo: Optional[str] = None,
        metodo_pagamento: Optional[str] = None,
        estabelecimento_id: Optional[int] = None,
        profissional_id: Optional[int] = None,
        origem: str = ORIGEM_MANUAL,
        chave_idempotencia: Optional[str] = None,
    ) -> LancamentoLivroCaixa:
        return self.registrar(
            LancamentoLivroCaixa(
                tipo=TipoLancamento.RECEITA.value,
                data_competencia=data_competencia,
                descricao=descricao,
                valor=Decimal(str(valor)),
                paciente_nome=paciente_nome,
                paciente_cpf=paciente_cpf,
                modalidade=modalidade,
                numero_recibo=numero_recibo,
                metodo_pagamento=metodo_pagamento,
                estabelecimento_id=estabelecimento_id,
                profissional_id=profissional_id,
                origem=origem,
                chave_idempotencia=chave_idempotencia,
            )
        )

    def registrar_despesa(
        self,
        *,
        data_competencia: date,
        descricao: str,
        valor: float | Decimal,
        categoria: str,
        dedutivel: bool = True,
        estabelecimento_id: Optional[int] = None,
        profissional_id: Optional[int] = None,
        origem: str = ORIGEM_MANUAL,
        chave_idempotencia: Optional[str] = None,
    ) -> LancamentoLivroCaixa:
        return self.registrar(
            LancamentoLivroCaixa(
                tipo=TipoLancamento.DESPESA.value,
                data_competencia=data_competencia,
                descricao=descricao,
                valor=Decimal(str(valor)),
                categoria=categoria,
                dedutivel=dedutivel,
                estabelecimento_id=estabelecimento_id,
                profissional_id=profissional_id,
                origem=origem,
                chave_idempotencia=chave_idempotencia,
            )
        )

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------
    def listar(
        self,
        *,
        mes_ano: str,
        estabelecimento_id: Optional[int] = None,
        profissional_id: Optional[int] = None,
        tipo: Optional[str] = None,
    ) -> Sequence[LancamentoLivroCaixa]:
        query = _filtrar(
            select(LancamentoLivroCaixa),
            mes_ano=mes_ano,
            estabelecimento_id=estabelecimento_id,
            profissional_id=profissional_id,
        )
        if tipo is not None:
            query = query.where(LancamentoLivroCaixa.tipo == tipo)
        return list(
            self.db.scalars(
                query.order_by(
                    LancamentoLivroCaixa.data_competencia,
                    LancamentoLivroCaixa.id,
                )
            )
        )

    def totais(
        self,
        *,
        mes_ano: str,
        estabelecimento_id: Optional[int] = None,
        profissional_id: Optional[int] = None,
    ) -> tuple[float, float, int]:
        """(receitas, despesas, quantidade de lançamentos) da competência."""
        consulta = _filtrar(
            select(
                LancamentoLivroCaixa.tipo,
                func.coalesce(func.sum(LancamentoLivroCaixa.valor), 0),
                func.count(LancamentoLivroCaixa.id),
            ).group_by(LancamentoLivroCaixa.tipo),
            mes_ano=mes_ano,
            estabelecimento_id=estabelecimento_id,
            profissional_id=profissional_id,
        )
        receitas = 0.0
        despesas = 0.0
        quantidade = 0
        for tipo, soma, contagem in self.db.execute(consulta):
            if tipo == TipoLancamento.RECEITA.value:
                receitas = float(soma)
            else:
                despesas = float(soma)
            quantidade += int(contagem)
        return receitas, despesas, quantidade

    def demonstrativo(
        self,
        *,
        mes_ano: str,
        estabelecimento_id: Optional[int] = None,
        profissional_id: Optional[int] = None,
    ) -> dict:
        """Balancete do mês a partir dos lançamentos persistidos.

        Sem lançamentos, devolve um demonstrativo **zerado** e explícito
        (``quantidade_consultas: 0``), nunca uma semente fictícia.
        """
        registros = self.listar(
            mes_ano=mes_ano,
            estabelecimento_id=estabelecimento_id,
            profissional_id=profissional_id,
        )

        receitas = [
            LancamentoReceita(
                data=registro.data_competencia.isoformat(),
                paciente_nome=registro.paciente_nome or "",
                paciente_cpf=registro.paciente_cpf or "",
                tipo_consulta=registro.modalidade or "PRESENCIAL",
                valor=float(registro.valor),
                numero_recibo=registro.numero_recibo or "",
                metodo_pagamento=registro.metodo_pagamento or "PIX",
            )
            for registro in registros
            if registro.tipo == TipoLancamento.RECEITA.value
        ]
        despesas = [
            LancamentoDespesa(
                data=registro.data_competencia.isoformat(),
                descricao=registro.descricao,
                categoria=registro.categoria or "OUTROS",
                valor=float(registro.valor),
                dedutivel_carne_leao=registro.dedutivel,
            )
            for registro in registros
            if registro.tipo == TipoLancamento.DESPESA.value
        ]

        return MotorLivroCaixaMedico.gerar_demonstrativo_mensal(
            receitas, despesas, mes_ano
        )

    def resumo_cobertura(
        self,
        *,
        mes_ano: str,
        estabelecimento_id: Optional[int] = None,
        profissional_id: Optional[int] = None,
    ) -> dict:
        """Metadados de honestidade do demonstrativo (o que existe de fato)."""
        receitas, despesas, quantidade = self.totais(
            mes_ano=mes_ano,
            estabelecimento_id=estabelecimento_id,
            profissional_id=profissional_id,
        )
        return {
            "competencia": mes_ano,
            "quantidade_lancamentos": quantidade,
            "total_receitas": round(receitas, 2),
            "total_despesas": round(despesas, 2),
            "possui_lancamentos": quantidade > 0,
            "escopo_estabelecimento_id": estabelecimento_id,
            "escopo_profissional_id": profissional_id,
        }


def competencia_de(instante: datetime) -> date:
    """Data de competência (dia) de um instante, normalizada para UTC."""
    if instante.tzinfo is not None:
        instante = instante.astimezone(timezone.utc)
    return instante.date()


__all__ = [
    "COMPETENCIA_PADRAO",
    "ORIGEM_FLUXO",
    "ORIGEM_MANUAL",
    "LivroCaixaRepo",
    "competencia_de",
    "intervalo_competencia",
    "normalizar_competencia",
]
