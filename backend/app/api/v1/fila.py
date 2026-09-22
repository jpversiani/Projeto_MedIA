from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.fila import FilaAcolhimento
from app.models.cidadao import Cidadao
from app.schemas.fila import FilaAcolhimentoCreate, FilaAcolhimentoUpdate, FilaAcolhimentoOut

router = APIRouter(prefix="/fila", tags=["Fila de Atendimento & Acolhimento"])

@router.get("/", response_model=List[FilaAcolhimentoOut])
def listar_fila(
    status: Optional[str] = Query("AGUARDANDO_ATENDIMENTO", description="Filtrar por status"),
    db: Session = Depends(get_db)
):
    query = db.query(FilaAcolhimento)
    if status and status != "TODOS":
        query = query.filter(FilaAcolhimento.status == status)
    
    # Ordenar por prioridade de risco: VERMELHO > AMARELO > VERDE > AZUL, depois por data_hora_entrada
    return query.order_by(
        FilaAcolhimento.data_hora_entrada.asc()
    ).all()

@router.post("/", response_model=FilaAcolhimentoOut, status_code=201)
def acolher_cidadao(payload: FilaAcolhimentoCreate, db: Session = Depends(get_db)):
    cidadao = db.query(Cidadao).filter(Cidadao.id == payload.cidadao_id).first()
    if not cidadao:
        raise HTTPException(status_code=404, detail="Cidadão não encontrado.")

    item_fila = FilaAcolhimento(**payload.model_dump())
    db.add(item_fila)
    db.commit()
    db.refresh(item_fila)
    return item_fila

@router.get("/{fila_id}", response_model=FilaAcolhimentoOut)
def obter_item_fila(fila_id: int, db: Session = Depends(get_db)):
    item = db.query(FilaAcolhimento).filter(FilaAcolhimento.id == fila_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Registro da fila não encontrado.")
    return item

@router.put("/{fila_id}", response_model=FilaAcolhimentoOut)
def atualizar_status_fila(fila_id: int, payload: FilaAcolhimentoUpdate, db: Session = Depends(get_db)):
    item = db.query(FilaAcolhimento).filter(FilaAcolhimento.id == fila_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Registro da fila não encontrado.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item
