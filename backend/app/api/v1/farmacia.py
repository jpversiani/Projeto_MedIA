from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.database import get_db
from app.models import Prescricao, MedicamentoDispensado  # Assuming these models exist

router = APIRouter()


# Pydantic models for request and response

class ConsultaRequest(BaseModel):
    qr_code_hash: str = Field(..., description="Hash do QR Code da receita")


class MedicamentoInfo(BaseModel):
    codigo: str = Field(..., description="Código do medicamento (ex: CMED)")
    nome: str = Field(..., description="Nome do medicamento")
    quantidade: float = Field(..., description="Quantidade prescrita")
    unidade: str = Field(..., description="Unidade de medida (ex: comprimido, frasco)")


class ConsultaResponse(BaseModel):
    prescricao_id: int
    numero_cns: str = Field(..., description="Cartão Nacional de Saúde do paciente")
    nome_paciente: str
    data_emissao: str
    cpf_medico: str = Field(..., description="CPF do médico")
    crm_medico: str
    medicamentos: List[MedicamentoInfo]
    valor_total: Optional[float] = Field(None, description="Valor total da receita (se aplicável)")


class BaixaRequest(BaseModel):
    prescricao_id: int = Field(..., description="ID da prescrição")
    medicamentos: List[MedicamentoInfo] = Field(..., description="Medicamentos dispensados")
    tipo_baixa: str = Field(..., description="Tipo de baixa: 'total' ou 'fracionada'")


class BaixaResponse(BaseModel):
    status: str
    mensagem: str
    prescricao_id: int
    valor_total_dispensado: Optional[float] = None


@router.post("/dispensacao/consultar", response_model=ConsultaResponse)
def consultar_dispensacao(
    request: ConsultaRequest,
    db: Session = Depends(get_db)
):
    """
    Valida QR Code/hash da receita e retorna os detalhes da prescrição.
    """
    # Busca a prescrição pelo hash do QR Code (assumimos que o hash está armazenado na prescrição)
    prescricao = db.query(Prescricao).filter(Prescricao.qr_code_hash == request.qr_code_hash).first()
    
    if not prescricao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR Code inválido ou receita não encontrada"
        )
    
    # Busca os medicamentos associados à prescrição
    medicamentos = db.query(MedicamentoDispensado).filter(
        MedicamentoDispensado.prescricao_id == prescricao.id
    ).all()
    
    # Converte para o modelo Pydantic
    medicamentos_info = [
        MedicamentoInfo(
            codigo=m.codigo,
            nome=m.nome,
            quantidade=m.quantidade,
            unidade=m.unidade
        ) for m in medicamentos
    ]
    
    return ConsultaResponse(
        prescricao_id=prescricao.id,
        numero_cns=prescricao.numero_cns,
        nome_paciente=prescricao.nome_paciente,
        data_emissao=prescricao.data_emissao.isoformat(),
        cpf_medico=prescricao.cpf_medico,
        crm_medico=prescricao.crm_medico,
        medicamentos=medicamentos_info,
        valor_total=prescricao.valor_total
    )


@router.post("/dispensacao/confirmar", response_model=BaixaResponse)
def confirmar_dispensacao(
    request: BaixaRequest,
    db: Session = Depends(get_db)
):
    """
    Registra a baixa total ou fracionada de medicamentos no SUS.
    """
    # Busca a prescrição
    prescricao = db.query(Prescricao).filter(Prescricao.id == request.prescricao_id).first()
    if not prescricao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescrição não encontrada"
        )
    
    # Verifica se o tipo de baixa é válido
    if request.tipo_baixa not in ["total", "fracionada"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de baixa inválido. Use 'total' ou 'fracionada'"
        )
    
    # Calcula o total dispensado (simplificado)
    valor_total_dispensado = sum(
        m.quantidade * getattr(m, 'valor_unitario', 0) for m in request.medicamentos
    ) if hasattr(request.medicamentos[0], 'valor_unitario') else None
    
    # Aqui iríamos atualizar o registro de baixa no SUS e na base de dados local
    # Por simplicidade, apenas retornamos uma resposta de sucesso
    # Em uma implementação real, atualizaríamos a prescrição e registraríamos a dispensa
    
    return BaixaResponse(
        status="sucesso",
        mensagem=f"Baixa {request.tipo_baixa} registrada com sucesso",
        prescricao_id=prescricao.id,
        valor_total_dispensado=valor_total_dispensado
    )


# Export the router
__all__ = ["router"]