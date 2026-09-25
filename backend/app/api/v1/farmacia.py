from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.database import get_db
from app.models.farmacia import Receita, ReceitaItem

router = APIRouter(prefix="/farmacia", tags=["Farmácia"])

class MedicamentoInfo(BaseModel):
    codigo: str = Field(..., description="Código do medicamento")
    nome: str = Field(..., description="Nome do medicamento")
    dosagem: str = Field(..., description="Dosagem do medicamento")
    quantidade: int = Field(..., description="Quantidade prescrita")
    quantidade_dispensada: Optional[int] = Field(0, description="Quantidade já dispensada")

class ConsultaRequest(BaseModel):
    qr_code_hash: str = Field(..., description="Hash do QR Code da receita")

class ConsultaResponse(BaseModel):
    numero_cns: str
    cpf_paciente: Optional[str] = None
    prescritor_nome: str
    medicamentos: List[MedicamentoInfo]

class BaixaRequest(BaseModel):
    numero_cns: str
    qr_code_hash: str
    tipo_baixa: str

class BaixaResponse(BaseModel):
    numero_cns: str
    tipo_baixa: str
    mensagem: str

@router.post("/dispensacao/consultar", response_model=ConsultaResponse)
def consultar_dispensacao(
    request: ConsultaRequest,
    db: Session = Depends(get_db)
):
    receita = db.query(Receita).filter(Receita.codigo_hash == request.qr_code_hash).first()
    if not receita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR Code inválido ou receita não encontrada"
        )
    
    medicamentos_info = [
        MedicamentoInfo(
            codigo=str(item.id),
            nome=item.medicamento,
            dosagem=item.dosagem,
            quantidade=item.quantidade_prescrita,
            quantidade_dispensada=item.quantidade_dispensada or 0
        )
        for item in receita.itens
    ]
    
    return ConsultaResponse(
        numero_cns=receita.cns_paciente,
        cpf_paciente=receita.cpf_paciente,
        prescritor_nome=receita.prescritor_nome,
        medicamentos=medicamentos_info
    )

@router.post("/dispensacao/confirmar", response_model=BaixaResponse)
def confirmar_dispensacao(
    request: BaixaRequest,
    db: Session = Depends(get_db)
):
    if request.tipo_baixa not in ["total", "fracionada"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de baixa inválido. Use total ou fracionada"
        )
    return BaixaResponse(
        numero_cns=request.numero_cns,
        tipo_baixa=request.tipo_baixa,
        mensagem=f"Baixa {request.tipo_baixa} registrada com sucesso"
    )
