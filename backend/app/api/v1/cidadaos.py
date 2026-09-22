from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.cidadao import Cidadao
from app.models.atendimento import AtendimentoSOAP
from app.schemas.cidadao import CidadaoCreate, CidadaoUpdate, CidadaoOut
from app.schemas.atendimento import AtendimentoSOAPOut

router = APIRouter(prefix="/cidadaos", tags=["Cidadãos (Cadastros)"])

@router.get("/", response_model=List[CidadaoOut])
def listar_cidadaos(
    busca: Optional[str] = Query(None, description="Nome, CPF ou CNS"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Cidadao)
    if busca:
        busca_termo = f"%{busca}%"
        query = query.filter(
            (Cidadao.nome_completo.ilike(busca_termo)) |
            (Cidadao.cpf.like(busca_termo)) |
            (Cidadao.cns.like(busca_termo))
        )
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=CidadaoOut, status_code=201)
def criar_cidadao(payload: CidadaoCreate, db: Session = Depends(get_db)):
    if payload.cpf:
        cpf_existente = db.query(Cidadao).filter(Cidadao.cpf == payload.cpf).first()
        if cpf_existente:
            raise HTTPException(status_code=400, detail="CPF já cadastrado.")
    if payload.cns:
        cns_existente = db.query(Cidadao).filter(Cidadao.cns == payload.cns).first()
        if cns_existente:
            raise HTTPException(status_code=400, detail="Cartão SUS (CNS) já cadastrado.")

    cidadao = Cidadao(**payload.model_dump())
    db.add(cidadao)
    db.commit()
    db.refresh(cidadao)
    return cidadao

@router.get("/{cidadao_id}", response_model=CidadaoOut)
def obter_cidadao(cidadao_id: int, db: Session = Depends(get_db)):
    cidadao = db.query(Cidadao).filter(Cidadao.id == cidadao_id).first()
    if not cidadao:
        raise HTTPException(status_code=404, detail="Cidadão não encontrado.")
    return cidadao

@router.put("/{cidadao_id}", response_model=CidadaoOut)
def atualizar_cidadao(cidadao_id: int, payload: CidadaoUpdate, db: Session = Depends(get_db)):
    cidadao = db.query(Cidadao).filter(Cidadao.id == cidadao_id).first()
    if not cidadao:
        raise HTTPException(status_code=404, detail="Cidadão não encontrado.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cidadao, field, value)

    db.commit()
    db.refresh(cidadao)
    return cidadao

@router.get("/{cidadao_id}/historico", response_model=List[AtendimentoSOAPOut])
def obter_historico_prontuario(cidadao_id: int, db: Session = Depends(get_db)):
    cidadao = db.query(Cidadao).filter(Cidadao.id == cidadao_id).first()
    if not cidadao:
        raise HTTPException(status_code=404, detail="Cidadão não encontrado.")

    atendimentos = (
        db.query(AtendimentoSOAP)
        .filter(AtendimentoSOAP.cidadao_id == cidadao_id)
        .order_by(AtendimentoSOAP.created_at.desc())
        .all()
    )
    return atendimentos
