from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.terminologia import CIAP2, CID10
from app.schemas.terminologia import CIAP2Out, CID10Out, CID11Out, CID11ConversaoOut
from app.services.cid11_service import cid11_service

router = APIRouter(prefix="/terminologias", tags=["Terminologias Médicas Oficiais (CIAP-2, CID-10 & CID-11 OMS)"])

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


@router.get("/cid11", response_model=List[CID11Out], summary="Consultar catálogo oficial CID-11 da OMS")
def buscar_cid11(
    busca: Optional[str] = Query(None, description="Código MMS (ex: BA00, 5A11), título clínico ou sinônimo"),
    capitulo: Optional[str] = Query(None, description="Filtrar por número ou nome do capítulo OMS"),
    limit: int = Query(25, ge=1, le=100)
):
    """
    Retorna entidades diagnósticas da CID-11 (WHO ICD-11 MMS).
    Suporta busca inteligente por sinônimos clínicos e correspondência cruzada com CID-10.
    """
    return cid11_service.buscar(termo=busca, capitulo=capitulo, limit=limit)


@router.get("/cid11/capitulos", summary="Listar capítulos oficiais da CID-11 da OMS")
def listar_capitulos_cid11():
    """Retorna os capítulos diagnósticos da CID-11 indexados na plataforma."""
    return {
        "padrao": "Organização Mundial da Saúde (OMS) - CID-11 MMS",
        "total_capitulos": len(cid11_service.listar_capitulos()),
        "capitulos": cid11_service.listar_capitulos()
    }


@router.get("/cid11/{codigo}", response_model=CID11Out, summary="Obter detalhe de código CID-11")
def obter_detalhe_cid11(codigo: str):
    """Retorna o registro completo, definição e mapeamento de um código CID-11."""
    resultado = cid11_service.obter_por_codigo(codigo)
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Código CID-11 '{codigo}' não encontrado no catálogo clínico do sistema."
        )
    return resultado


@router.get("/cid11/converter/{codigo}", response_model=CID11ConversaoOut, summary="Conversor Dual-Coding CID-10 <-> CID-11")
def converter_codigo_diagnostico(
    codigo: str,
    direcao: Optional[str] = Query("auto", description="'auto', 'cid10_para_cid11' ou 'cid11_para_cid10'")
):
    """
    Realiza o mapeamento cruzado (cross-walk) entre a CID-10 e a CID-11 da OMS.
    Facilita a transição regulatória entre o padrão internacional moderno e operadoras TISS.
    """
    cod_limpo = codigo.strip().upper()

    # Tentativa automática ou explícita de CID-10 -> CID-11
    if direcao in ("auto", "cid10_para_cid11"):
        conv10 = cid11_service.converter_cid10_para_cid11(cod_limpo)
        if conv10:
            return conv10

    # Tentativa de CID-11 -> CID-10
    if direcao in ("auto", "cid11_para_cid10"):
        conv11 = cid11_service.converter_cid11_para_cid10(cod_limpo)
        if conv11:
            return conv11

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Não foi possível converter o código '{codigo}'. Verifique se o código informado é válido na CID-10 ou CID-11."
    )

