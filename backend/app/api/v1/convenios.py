"""
API V1 de Convênios, Guias TISS e Faturamento Particular (DMED).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.convenios import GuiaStatus, LancamentoTipo
from app.repositories.convenios_repo import ConveniosRepository
from app.services.tiss_generator import TISSGenerator

router = APIRouter(prefix="/convenios", tags=["Convênios & TISS"])

# Schemas Pydantic
class OperadoraCreate(BaseModel):
    nome: str = Field(..., example="Unimed")
    registro_ans: str = Field(..., example="305685")
    cnpj: str = Field(..., example="12345678000199")
    contato_email: Optional[str] = Field(None, example="faturamento@operadora.com.br")

class OperadoraResponse(BaseModel):
    id: int
    nome: str
    registro_ans: str
    cnpj: str
    ativo: bool

    class Config:
        from_attributes = True

class PlanoCreate(BaseModel):
    operadora_id: int
    nome: str = Field(..., example="Plano Básico Nacional")
    codigo_plano: str = Field(..., example="PL-001")
    tipo: str = Field("AMBULATORIAL", example="AMBULATORIAL")

class PlanoResponse(BaseModel):
    id: int
    operadora_id: int
    nome: str
    codigo_plano: str
    tipo: str
    ativo: bool

    class Config:
        from_attributes = True

class EmissaoGuiaConsultaRequest(BaseModel):
    plano_id: int
    paciente_nome: str
    numero_carteira: str
    paciente_cpf: Optional[str] = None
    paciente_cns: Optional[str] = None
    ciap2: Optional[str] = None
    cid10: Optional[str] = None
    procedimento_tuss: str = "10101012"
    valor: float = 150.0
    atendimento_id: Optional[int] = None

class GuiaTISSResponse(BaseModel):
    id: int
    numero_guia: str
    tipo_guia: str
    status: str
    valor_total: float
    paciente_nome: str
    procedimento_tuss: str
    xml_tiss: Optional[str] = None

    class Config:
        from_attributes = True

class AtualizacaoStatusGuia(BaseModel):
    status: GuiaStatus

class ReciboDMEDRequest(BaseModel):
    paciente_nome: str
    paciente_cpf: str
    valor: float
    descricao: str = "Consulta Médica em Atenção Primária"
    atendimento_id: Optional[int] = None
    prestador_nome: str = "Clínica MedIA Saúde da Família"
    prestador_cpf_cnpj: str = "12345678000100"

# Endpoints
@router.post("/operadoras", response_model=OperadoraResponse, status_code=status.HTTP_201_CREATED)
def criar_operadora(payload: OperadoraCreate, db: Session = Depends(get_db)):
    return ConveniosRepository.criar_operadora(
        db=db,
        nome=payload.nome,
        registro_ans=payload.registro_ans,
        cnpj=payload.cnpj,
        contato_email=payload.contato_email,
    )

@router.get("/operadoras", response_model=List[OperadoraResponse])
def listar_operadoras(db: Session = Depends(get_db)):
    return ConveniosRepository.listar_operadoras(db=db)

@router.post("/planos", response_model=PlanoResponse, status_code=status.HTTP_201_CREATED)
def criar_plano(payload: PlanoCreate, db: Session = Depends(get_db)):
    operadora = ConveniosRepository.obter_operadora(db=db, operadora_id=payload.operadora_id)
    if not operadora:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operadora não encontrada")
    return ConveniosRepository.criar_plano(
        db=db,
        operadora_id=payload.operadora_id,
        nome=payload.nome,
        codigo_plano=payload.codigo_plano,
        tipo=payload.tipo,
    )

@router.get("/planos", response_model=List[PlanoResponse])
def listar_planos(operadora_id: Optional[int] = None, db: Session = Depends(get_db)):
    return ConveniosRepository.listar_planos(db=db, operadora_id=operadora_id)

@router.post("/guias/consulta", response_model=GuiaTISSResponse, status_code=status.HTTP_201_CREATED)
def emitir_guia_consulta(payload: EmissaoGuiaConsultaRequest, db: Session = Depends(get_db)):
    try:
        return ConveniosRepository.emitir_guia_consulta_tiss(
            db=db,
            plano_id=payload.plano_id,
            paciente_nome=payload.paciente_nome,
            numero_carteira=payload.numero_carteira,
            paciente_cpf=payload.paciente_cpf,
            paciente_cns=payload.paciente_cns,
            ciap2=payload.ciap2,
            cid10=payload.cid10,
            procedimento_tuss=payload.procedimento_tuss,
            valor=payload.valor,
            atendimento_id=payload.atendimento_id,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/guias/{guia_id}", response_model=GuiaTISSResponse)
def obter_guia(guia_id: int, db: Session = Depends(get_db)):
    guia = ConveniosRepository.obter_guia(db=db, guia_id=guia_id)
    if not guia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guia TISS não encontrada")
    return guia

@router.patch("/guias/{guia_id}/status", response_model=GuiaTISSResponse)
def atualizar_status(guia_id: int, payload: AtualizacaoStatusGuia, db: Session = Depends(get_db)):
    guia = ConveniosRepository.atualizar_status_guia(db=db, guia_id=guia_id, novo_status=payload.status)
    if not guia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guia TISS não encontrada")
    return guia

@router.post("/dmed/recibo")
def gerar_recibo_dmed(payload: ReciboDMEDRequest, db: Session = Depends(get_db)):
    lancamento = ConveniosRepository.registrar_recibo_particular_dmed(
        db=db,
        paciente_nome=payload.paciente_nome,
        paciente_cpf=payload.paciente_cpf,
        valor=payload.valor,
        descricao=payload.descricao,
        atendimento_id=payload.atendimento_id,
    )
    recibo_fiscal = TISSGenerator.gerar_recibo_dmed(
        numero_recibo=lancamento.recibo_numero,
        prestador_nome=payload.prestador_nome,
        prestador_cpf_cnpj=payload.prestador_cpf_cnpj,
        paciente_nome=payload.paciente_nome,
        paciente_cpf=payload.paciente_cpf,
        valor=payload.valor,
        descricao_servico=payload.descricao,
    )
    return {
        "lancamento_id": lancamento.id,
        "recibo_numero": lancamento.recibo_numero,
        "dados_fiscais_dmed": recibo_fiscal,
    }
