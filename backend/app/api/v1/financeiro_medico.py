"""
Rotas REST de Gestão Financeira, Pix e Livro Caixa para Médicos.

**Correção P0-6:** o demonstrativo devolvia uma lista *hardcoded* de cinco
consultas e três despesas. O médico via um faturamento inventado (R$ 1.780,00),
com nomes e CPFs de pacientes fictícios, e não existia rota para lançar nada.
Agora o livro caixa é uma tabela real (``lancamentos_livro_caixa``): as rotas
abaixo escrevem e leem dela, escopadas pelo estabelecimento do token. Sem
lançamentos, o demonstrativo vem zerado e diz isso explicitamente, em vez de
fabricar números.
"""

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.financeiro import (
    LancamentoLivroCaixa,
    ModalidadeConsulta,
    TipoLancamento,
)
from app.repositories.livro_caixa_repo import (
    LivroCaixaRepo,
    normalizar_competencia,
)
from app.services.pix_cobranca import DadosCobrancaPix, MotorPixCobranca

from app.core.rbac import (
    PAPEIS_FATURAMENTO,
    ContextoClinico,
    dependencias_rbac,
    get_contexto_clinico,
)
router = APIRouter(prefix="/financeiro-medico", tags=["Financeiro & Pix Médico"], dependencies=dependencias_rbac(*PAPEIS_FATURAMENTO))


class GerarPixRequest(BaseModel):
    chave_pix: str = Field(min_length=1)
    nome_beneficiario: str = Field(default="", max_length=60)
    cidade_beneficiario: str = Field(default="", max_length=40)
    valor: float = Field(default=0, ge=0)
    identificador_transacao: Optional[str] = None
    descricao: Optional[str] = "Consulta Medica Telemedicina"


class LancamentoRequest(BaseModel):
    """Um lançamento no livro caixa (receita de consulta ou despesa)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    tipo: TipoLancamento
    data_competencia: date
    descricao: str = Field(min_length=3, max_length=300)
    valor: float = Field(gt=0, le=1_000_000)

    # Receita
    paciente_nome: Optional[str] = Field(default=None, max_length=200)
    paciente_cpf: Optional[str] = Field(default=None, min_length=11, max_length=11)
    modalidade: Optional[ModalidadeConsulta] = None
    numero_recibo: Optional[str] = Field(default=None, max_length=50)
    metodo_pagamento: Optional[str] = Field(default=None, max_length=30)

    # Despesa
    categoria: Optional[str] = Field(default=None, max_length=40)
    dedutivel: bool = True

    chave_idempotencia: Optional[str] = Field(default=None, max_length=64)


class LancamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoLancamento
    data_competencia: date
    descricao: str
    valor: float
    paciente_nome: Optional[str]
    paciente_cpf: Optional[str]
    modalidade: Optional[str]
    numero_recibo: Optional[str]
    metodo_pagamento: Optional[str]
    categoria: Optional[str]
    dedutivel: bool
    origem: str
    estabelecimento_id: Optional[int]
    profissional_id: Optional[int]
    created_at: Optional[datetime]


@router.post("/pix/gerar-cobranca")
def gerar_cobranca_pix(payload: GerarPixRequest):
    """Gera string oficial Pix Copia e Cola (padrão EMV Banco Central) com CRC16."""
    dados = DadosCobrancaPix(
        chave_pix=payload.chave_pix,
        nome_beneficiario=payload.nome_beneficiario,
        cidade_beneficiario=payload.cidade_beneficiario,
        valor=payload.valor,
        identificador_transacao=payload.identificador_transacao,
        descricao_consulta=payload.descricao,
    )
    return MotorPixCobranca.gerar_pix_copia_e_cola(dados)


def _competencia_ou_422(mes_ano: str) -> str:
    try:
        return normalizar_competencia(mes_ano)
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail=str(exc)
        ) from exc


def _escopo(contexto: Optional[ContextoClinico]) -> tuple[Optional[int], Optional[int]]:
    """Estabelecimento e profissional do token (``None`` em desenvolvimento)."""
    if contexto is None:
        return None, None
    return contexto.estabelecimento_id, contexto.profissional_id


@router.post(
    "/lancamentos",
    response_model=LancamentoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Lançar receita ou despesa no livro caixa",
)
def criar_lancamento(
    payload: LancamentoRequest,
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    """Escritura um honorário ou uma despesa na competência informada.

    A receita exige paciente e modalidade (é o que comprova o atendimento no
    DMED); a despesa exige categoria e informa se é dedutível no Carnê-Leão.
    """
    estabelecimento_id, profissional_id = _escopo(contexto)
    repo = LivroCaixaRepo(db)

    if payload.tipo is TipoLancamento.RECEITA:
        if not payload.paciente_nome:
            raise HTTPException(
                status_code=422,
                detail="Receita exige o nome do paciente (comprovação do DMED).",
            )
        if payload.modalidade is None:
            raise HTTPException(
                status_code=422,
                detail="Receita exige a modalidade (PRESENCIAL ou TELEMEDICINA).",
            )
        lancamento = repo.registrar_receita(
            data_competencia=payload.data_competencia,
            descricao=payload.descricao,
            valor=payload.valor,
            paciente_nome=payload.paciente_nome,
            paciente_cpf=payload.paciente_cpf,
            modalidade=payload.modalidade.value,
            numero_recibo=payload.numero_recibo,
            metodo_pagamento=payload.metodo_pagamento,
            estabelecimento_id=estabelecimento_id,
            profissional_id=profissional_id,
            chave_idempotencia=payload.chave_idempotencia,
        )
    else:
        if not payload.categoria:
            raise HTTPException(
                status_code=422,
                detail="Despesa exige a categoria (ex.: ALUGUEL_CONSULTORIO).",
            )
        lancamento = repo.registrar_despesa(
            data_competencia=payload.data_competencia,
            descricao=payload.descricao,
            valor=payload.valor,
            categoria=payload.categoria,
            dedutivel=payload.dedutivel,
            estabelecimento_id=estabelecimento_id,
            profissional_id=profissional_id,
            chave_idempotencia=payload.chave_idempotencia,
        )

    db.commit()
    db.refresh(lancamento)
    return lancamento


@router.get(
    "/lancamentos",
    response_model=List[LancamentoOut],
    summary="Listar lançamentos da competência",
)
def listar_lancamentos(
    mes_ano: str = Query(
        default="", description="Competência MM/AAAA (padrão: mês corrente)."
    ),
    tipo: Optional[TipoLancamento] = None,
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    competencia = _competencia_ou_422(mes_ano)
    estabelecimento_id, profissional_id = _escopo(contexto)
    repo = LivroCaixaRepo(db)
    return list(
        repo.listar(
            mes_ano=competencia,
            estabelecimento_id=estabelecimento_id,
            profissional_id=profissional_id,
            tipo=tipo.value if tipo else None,
        )
    )


@router.get("/livro-caixa/demonstrativo")
def obter_demonstrativo_livro_caixa(
    mes_ano: str = Query(
        default="", description="Competência MM/AAAA (padrão: mês corrente)."
    ),
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    """Balancete da competência a partir dos lançamentos reais.

    Sem lançamentos, todos os totais vêm zerados (nunca uma semente fictícia) e
    ``quantidade_consultas`` é 0.
    """
    competencia = _competencia_ou_422(mes_ano)
    estabelecimento_id, profissional_id = _escopo(contexto)

    repo = LivroCaixaRepo(db)
    demonstrativo = repo.demonstrativo(
        mes_ano=competencia,
        estabelecimento_id=estabelecimento_id,
        profissional_id=profissional_id,
    )
    demonstrativo["cobertura"] = repo.resumo_cobertura(
        mes_ano=competencia,
        estabelecimento_id=estabelecimento_id,
        profissional_id=profissional_id,
    )
    return demonstrativo
