from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.terminologia import CIAP2, CID10
from app.schemas.terminologia import CIAP2Out, CID10Out

router = APIRouter(prefix="/terminologias", tags=["Terminologias Oficiais (CIAP-2 & CID-10)"])

@router.get("/ciap2", response_model=List[CIAP2Out])
def buscar_ciap2(
    busca: Optional[str] = Query(None, description="Código ou termo clínico"),
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(CIAP2).filter(CIAP2.ativo == True)
    if busca:
        termo = f"%{busca}%"
        query = query.filter((CIAP2.codigo.ilike(termo)) | (CIAP2.descricao.ilike(termo)))
    return query.limit(limit).all()

@router.get("/cid10", response_model=List[CID10Out])
def buscar_cid10(
    busca: Optional[str] = Query(None, description="Código CID ou descrição"),
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(CID10).filter(CID10.ativo == True)
    if busca:
        termo = f"%{busca}%"
        query = query.filter((CID10.codigo.ilike(termo)) | (CID10.descricao.ilike(termo)))
    return query.limit(limit).all()
