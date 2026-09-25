"""API de Dispensação Farmacêutica e Baixa de Receita (C10).

Endpoints para a farmácia do Projeto MedIA: consulta da receita digital a
partir do hash lido do QR Code e confirmação da baixa (dispensação) total ou
fracionada dos medicamentos prescritos, com trilha de auditoria do
farmacêutico e do estabelecimento dispensador.

Projeto MedIA (Python 3.12, Pydantic v2, SQLAlchemy 2.0).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Final

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.farmacia import (
    STATUS_CANCELADA,
    STATUS_DISPENSADA,
    STATUS_PARCIALMENTE_DISPENSADA,
    Dispensacao,
    DispensacaoItem,
    Receita,
    ReceitaItem,
)

router = APIRouter(prefix="/farmacia", tags=["Farmácia"])

_ERRO_RECEITA_NAO_ENCONTRADA: Final[str] = "QR Code inválido ou receita não encontrada"
_ERRO_RECEITA_CANCELADA: Final[str] = "Receita cancelada — baixa não permitida"
_ERRO_RECEITA_EXPIRADA: Final[str] = "Receita vencida — baixa não permitida"
_ERRO_RECEITA_COMPLETA: Final[str] = "Receita já totalmente dispensada"
_ERRO_ITENS_OBRIGATORIOS: Final[str] = "Baixa fracionada exige a lista de itens dispensados"
_ERRO_ITEM_NAO_ENCONTRADO: Final[str] = "Item {item_id} não pertence à receita informada"
_ERRO_QUANTIDADE_INVALIDA: Final[str] = (
    "Quantidade solicitada para o item {item_id} excede o saldo remanescente ({saldo})"
)
_ERRO_IDEMPOTENCIA: Final[str] = "Dispensação já registrada para esta chave de idempotência"


class TipoBaixa(StrEnum):
    TOTAL = "TOTAL"
    FRACIONADA = "FRACIONADA"


class ItemConsultaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    medicamento: str
    dosagem: str
    posologia: str
    quantidade_prescrita: int
    quantidade_dispensada: int
    saldo_remanescente: int


class ConsultaRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    qr_code_hash: str = Field(min_length=32, max_length=64, description="Hash SHA-256 lido do QR Code")


class ConsultaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    receita_id: int
    qr_code_hash: str
    cns_paciente: str
    cpf_paciente: str | None
    prescritor_nome: str
    prescritor_registro: str
    unidade_cnes: str
    data_emissao: datetime
    data_validade: date
    status: str
    medicamentos: list[ItemConsultaResponse]


class ItemBaixaRequest(BaseModel):
    receita_item_id: int = Field(ge=1)
    quantidade: int = Field(ge=1)
    lote: str | None = Field(default=None, max_length=30)
    validade_lote: date | None = None


class ConfirmarRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    qr_code_hash: str = Field(min_length=32, max_length=64)
    tipo_baixa: TipoBaixa
    farmaceutico_nome: str = Field(min_length=1, max_length=200)
    farmaceutico_cns: str = Field(min_length=15, max_length=15)
    farmaceutico_cpf: str | None = Field(default=None, min_length=11, max_length=11)
    unidade_cnes: str = Field(min_length=7, max_length=7)
    itens: list[ItemBaixaRequest] = Field(default_factory=list)
    observacoes: str | None = Field(default=None, max_length=500)
    chave_idempotencia: str | None = Field(default=None, max_length=64)


class ItemBaixaResponse(BaseModel):
    item_id: int
    medicamento: str
    quantidade_dispensada: int
    saldo_remanescente: int


class ConfirmarResponse(BaseModel):
    dispensacao_id: int
    receita_id: int
    qr_code_hash: str
    tipo_baixa: TipoBaixa
    status_receita: str
    itens: list[ItemBaixaResponse]
    mensagem: str


def _obter_receita(db: Session, qr_code_hash: str) -> Receita:
    receita = db.scalar(
        select(Receita)
        .where(Receita.codigo_hash == qr_code_hash)
        .options(selectinload(Receita.itens))
    )
    if receita is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_ERRO_RECEITA_NAO_ENCONTRADA)
    return receita


def _validar_disponibilidade(receita: Receita) -> None:
    if receita.status == STATUS_CANCELADA:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_ERRO_RECEITA_CANCELADA)
    if receita.data_validade < date.today():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_ERRO_RECEITA_EXPIRADA)
    if all(item.saldo_remanescente <= 0 for item in receita.itens):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_ERRO_RECEITA_COMPLETA)


@router.post("/dispensacao/consultar", response_model=ConsultaResponse)
def consultar_dispensacao(request: ConsultaRequest, db: Session = Depends(get_db)) -> ConsultaResponse:
    """Valida o hash do QR Code e retorna a receita com o saldo de cada item."""
    receita = _obter_receita(db, request.qr_code_hash)
    _validar_disponibilidade(receita)

    medicamentos = [
        ItemConsultaResponse(
            item_id=item.id,
            medicamento=item.medicamento,
            dosagem=item.dosagem,
            posologia=item.posologia,
            quantidade_prescrita=item.quantidade_prescrita,
            quantidade_dispensada=item.quantidade_dispensada,
            saldo_remanescente=item.saldo_remanescente,
        )
        for item in receita.itens
    ]
    return ConsultaResponse(
        receita_id=receita.id,
        qr_code_hash=receita.codigo_hash,
        cns_paciente=receita.cns_paciente,
        cpf_paciente=receita.cpf_paciente,
        prescritor_nome=receita.prescritor_nome,
        prescritor_registro=receita.prescritor_registro,
        unidade_cnes=receita.unidade_cnes,
        data_emissao=receita.data_emissao,
        data_validade=receita.data_validade,
        status=receita.status,
        medicamentos=medicamentos,
    )


@router.post("/dispensacao/confirmar", response_model=ConfirmarResponse, status_code=status.HTTP_201_CREATED)
def confirmar_dispensacao(request: ConfirmarRequest, db: Session = Depends(get_db)) -> ConfirmarResponse:
    """Registra a baixa total ou fracionada dos medicamentos da receita."""
    if request.chave_idempotencia is not None:
        existente = db.scalar(
            select(Dispensacao).where(Dispensacao.chave_idempotencia == request.chave_idempotencia)
        )
        if existente is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_ERRO_IDEMPOTENCIA)

    receita = _obter_receita(db, request.qr_code_hash)
    _validar_disponibilidade(receita)

    itens_por_id = {item.id: item for item in receita.itens}
    if request.tipo_baixa is TipoBaixa.FRACIONADA and not request.itens:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_ERRO_ITENS_OBRIGATORIOS)

    solicitacoes = (
        request.itens
        if request.tipo_baixa is TipoBaixa.FRACIONADA
        else [
            ItemBaixaRequest(receita_item_id=item.id, quantidade=item.saldo_remanescente)
            for item in receita.itens
            if item.saldo_remanescente > 0
        ]
    )

    baixas_por_item: dict[int, int] = {}
    for solicitacao in solicitacoes:
        if solicitacao.receita_item_id not in itens_por_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_ERRO_ITEM_NAO_ENCONTRADO.format(item_id=solicitacao.receita_item_id),
            )
        baixas_por_item[solicitacao.receita_item_id] = (
            baixas_por_item.get(solicitacao.receita_item_id, 0) + solicitacao.quantidade
        )

    for item_id, quantidade in baixas_por_item.items():
        saldo = itens_por_id[item_id].saldo_remanescente
        if quantidade > saldo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_ERRO_QUANTIDADE_INVALIDA.format(item_id=item_id, saldo=saldo),
            )

    dispensacao = Dispensacao(
        receita_id=receita.id,
        tipo=request.tipo_baixa.value,
        farmaceutico_nome=request.farmaceutico_nome,
        farmaceutico_cns=request.farmaceutico_cns,
        farmaceutico_cpf=request.farmaceutico_cpf,
        unidade_cnes=request.unidade_cnes,
        observacoes=request.observacoes,
        chave_idempotencia=request.chave_idempotencia,
        data_dispensacao=datetime.now(timezone.utc),
    )
    db.add(dispensacao)
    db.flush()

    for item_id, quantidade in baixas_por_item.items():
        item = itens_por_id[item_id]
        item.quantidade_dispensada += quantidade
        db.add(
            DispensacaoItem(
                dispensacao_id=dispensacao.id,
                receita_item_id=item_id,
                quantidade_dispensada=quantidade,
            )
        )

    if all(item.saldo_remanescente <= 0 for item in receita.itens):
        receita.status = STATUS_DISPENSADA
    else:
        receita.status = STATUS_PARCIALMENTE_DISPENSADA
    db.add(receita)
    db.commit()
    db.refresh(dispensacao)

    itens_resposta = [
        ItemBaixaResponse(
            item_id=item.id,
            medicamento=item.medicamento,
            quantidade_dispensada=baixas_por_item.get(item.id, 0),
            saldo_remanescente=item.saldo_remanescente,
        )
        for item in receita.itens
    ]
    return ConfirmarResponse(
        dispensacao_id=dispensacao.id,
        receita_id=receita.id,
        qr_code_hash=receita.codigo_hash,
        tipo_baixa=request.tipo_baixa,
        status_receita=receita.status,
        itens=itens_resposta,
        mensagem=f"Baixa {request.tipo_baixa.value} registrada com sucesso",
    )
