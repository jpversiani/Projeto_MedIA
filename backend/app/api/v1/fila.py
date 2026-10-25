from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.rbac import (
    PAPEIS_ACOLHIMENTO,
    ContextoClinico,
    dependencias_rbac,
    exigir_mesmo_estabelecimento,
    filtrar_tenant,
    get_contexto_clinico,
)
from app.models.fila import FilaAcolhimento
from app.models.cidadao import Cidadao
from app.schemas.fila import FilaAcolhimentoCreate, FilaAcolhimentoUpdate, FilaAcolhimentoOut

router = APIRouter(
    prefix="/fila",
    tags=["Fila de Atendimento & Acolhimento"],
    dependencies=dependencias_rbac(*PAPEIS_ACOLHIMENTO),
)

# Ordem de prioridade clínica (triagem de risco). Vermelho é emergência e deve
# ser atendido antes de qualquer caso menos grave, independentemente da ordem
# de chegada — é o princípio da triagem de Manchester.
_ORDEM_RISCO = case(
    (FilaAcolhimento.classificacao_risco == "VERMELHO", 0),
    (FilaAcolhimento.classificacao_risco == "AMARELO", 1),
    (FilaAcolhimento.classificacao_risco == "VERDE", 2),
    (FilaAcolhimento.classificacao_risco == "AZUL", 3),
    else_=4,  # sem classificação vai para o fim
)


@router.get("/", response_model=List[FilaAcolhimentoOut])
def listar_fila(
    status: Optional[str] = Query("AGUARDANDO_ATENDIMENTO", description="Filtrar por status"),
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db)
):
    query = filtrar_tenant(db.query(FilaAcolhimento), FilaAcolhimento, contexto)
    if status and status != "TODOS":
        query = query.filter(FilaAcolhimento.status == status)

    # A query ordenava APENAS por data_hora_entrada, apesar do comentário acima
    # prometer prioridade por risco. Na prática, um caso VERMELHO (emergência)
    # entrava atrás de dez casos AZUL. A ordenação agora é risco primeiro e,
    # dentro do mesmo risco, ordem de chegada.
    return query.order_by(
        _ORDEM_RISCO.asc(),
        FilaAcolhimento.data_hora_entrada.asc(),
    ).all()

@router.post("/", response_model=FilaAcolhimentoOut, status_code=201)
def acolher_cidadao(
    payload: FilaAcolhimentoCreate,
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    # Impede acolher um paciente "na unidade do vizinho": o estabelecimento do
    # payload precisa ser a clínica ativa do token.
    if contexto is not None and not contexto.is_superuser:
        if payload.estabelecimento_id != contexto.estabelecimento_id:
            raise HTTPException(
                status_code=403,
                detail="Não é permitido acolher em unidade diferente da clínica ativa.",
            )

    cidadao = db.query(Cidadao).filter(Cidadao.id == payload.cidadao_id).first()
    if not cidadao:
        raise HTTPException(status_code=404, detail="Cidadão não encontrado.")

    item_fila = FilaAcolhimento(**payload.model_dump())
    db.add(item_fila)
    db.commit()
    db.refresh(item_fila)
    return item_fila

@router.get("/{fila_id}", response_model=FilaAcolhimentoOut)
def obter_item_fila(
    fila_id: int,
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    item = db.query(FilaAcolhimento).filter(FilaAcolhimento.id == fila_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Registro da fila não encontrado.")
    exigir_mesmo_estabelecimento(item.estabelecimento_id, contexto, acao="consultar")
    return item

@router.put("/{fila_id}", response_model=FilaAcolhimentoOut)
def atualizar_status_fila(
    fila_id: int,
    payload: FilaAcolhimentoUpdate,
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    item = db.query(FilaAcolhimento).filter(FilaAcolhimento.id == fila_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Registro da fila não encontrado.")
    exigir_mesmo_estabelecimento(item.estabelecimento_id, contexto, acao="atualizar")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item
