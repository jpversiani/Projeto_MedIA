from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.estabelecimento import Estabelecimento
from app.models.profissional import Profissional
from app.schemas.estabelecimento import EstabelecimentoOut
from app.schemas.profissional import ProfissionalOut

router = APIRouter(tags=["Configurações da Unidade & Profissionais"])

@router.get("/estabelecimentos", response_model=List[EstabelecimentoOut])
def listar_estabelecimentos(db: Session = Depends(get_db)):
    return db.query(Estabelecimento).all()

@router.get("/profissionais", response_model=List[ProfissionalOut])
def listar_profissionais(db: Session = Depends(get_db)):
    return db.query(Profissional).all()
