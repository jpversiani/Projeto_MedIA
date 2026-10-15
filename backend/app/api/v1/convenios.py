"""
API V1 de Convênios, Guias TISS e Faturamento Particular (DMED).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.convenios import GuiaStatus, LancamentoTipo
from app.repositories.convenios_repo import ConveniosRepository
from app.services.tiss_generator import TISSGenerator

router = APIRouter(prefix="/convenios", tags=["Convênios & TISS"])

# Schemas Pydantic
class OperadoraCreate(BaseModel):
    nome: str = Field(..., json_schema_extra={"example": "Unimed"})
    registro_ans: str = Field(..., json_schema_extra={"example": "305685"})
    cnpj: str = Field(..., json_schema_extra={"example": "12345678000199"})
    contato_email: Optional[str] = Field(None, json_schema_extra={"example": "faturamento@operadora.com.br"})

class OperadoraResponse(BaseModel):
    id: int
    nome: str
    registro_ans: str
    cnpj: str
    ativo: bool

    model_config = ConfigDict(from_attributes=True)

class PlanoCreate(BaseModel):
    operadora_id: int
    nome: str = Field(..., json_schema_extra={"example": "Plano Básico Nacional"})
    codigo_plano: str = Field(..., json_schema_extra={"example": "PL-001"})
    tipo: str = Field("AMBULATORIAL", json_schema_extra={"example": "AMBULATORIAL"})

class PlanoResponse(BaseModel):
    id: int
    operadora_id: int
    nome: str
    codigo_plano: str
    tipo: str
    ativo: bool

    model_config = ConfigDict(from_attributes=True)

class EmissaoGuiaConsultaRequest(BaseModel):
    plano_id: Optional[int] = None
    operadora_nome: Optional[str] = None
    paciente_nome: str
    numero_carteira: Optional[str] = "123456789"
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

    model_config = ConfigDict(from_attributes=True)

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

@router.get("/guias")
def listar_guias(operadora: Optional[str] = None, db: Session = Depends(get_db)):
    """Lista todas as guias TISS gravadas no banco de dados."""
    from sqlalchemy.orm import joinedload
    from app.models.convenios import GuiaTISS, Plano
    query = db.query(GuiaTISS).options(joinedload(GuiaTISS.plano).joinedload(Plano.operadora)).order_by(GuiaTISS.id.desc())
    guias = query.all()
    resultado = []
    for g in guias:
        op_nome = g.plano.operadora.nome if g.plano and g.plano.operadora else "Particular"
        if operadora and operadora != "TODAS" and op_nome.lower() != operadora.lower():
            continue
        status_str = g.status.value if hasattr(g.status, "value") else str(g.status)
        resultado.append({
            "id": g.id,
            "numero": g.numero_guia,
            "paciente": g.paciente_nome or "Paciente",
            "operadora": op_nome,
            "data": g.data_emissao.strftime("%Y-%m-%d") if g.data_emissao else "2026-03-01",
            "valor": float(g.valor_total or 0.0),
            "status": status_str,
            "tuss": g.procedimento_tuss or "10101012"
        })
    return resultado

@router.get("/lancamentos")
def listar_lancamentos_financeiros(db: Session = Depends(get_db)):
    """Lista todos os lançamentos financeiros gravados no banco de dados."""
    lancamentos = ConveniosRepository.listar_lancamentos(db=db)
    return [
        {
            "id": l.id,
            "recibo": l.recibo_numero or f"REC-2026-{l.id:03d}",
            "paciente": l.paciente_nome,
            "cpf": l.paciente_cpf,
            "tipo": l.tipo.value if hasattr(l.tipo, "value") else str(l.tipo),
            "valor": float(l.valor),
            "data": l.data_lancamento.strftime("%d/%m/%Y") if l.data_lancamento else "15/10/2026",
            "status": l.status.value if hasattr(l.status, "value") else str(l.status)
        }
        for l in lancamentos
    ]

@router.post("/guias/consulta", response_model=GuiaTISSResponse, status_code=status.HTTP_201_CREATED)
def emitir_guia_consulta(payload: EmissaoGuiaConsultaRequest, db: Session = Depends(get_db)):
    try:
        plano_id = payload.plano_id
        if not plano_id:
            # Localiza ou cria a operadora e o plano correspondente no banco
            from app.models.convenios import Operadora, Plano
            nome_op = (payload.operadora_nome or "Unimed").strip()
            op = db.query(Operadora).filter(Operadora.nome.ilike(f"%{nome_op}%")).first()
            if not op:
                op = Operadora(
                    nome=nome_op,
                    registro_ans="305685",
                    cnpj="12345678000199",
                    ativo=True
                )
                db.add(op)
                db.commit()
                db.refresh(op)
            plano = db.query(Plano).filter(Plano.operadora_id == op.id).first()
            if not plano:
                plano = Plano(
                    operadora_id=op.id,
                    nome=f"{nome_op} Saúde Integral",
                    codigo_plano=f"PL-{op.id:03d}",
                    tipo="AMBULATORIAL",
                    ativo=True
                )
                db.add(plano)
                db.commit()
                db.refresh(plano)
            plano_id = plano.id

        return ConveniosRepository.emitir_guia_consulta_tiss(
            db=db,
            plano_id=plano_id,
            paciente_nome=payload.paciente_nome,
            numero_carteira=payload.numero_carteira or "123456789",
            paciente_cpf=payload.paciente_cpf,
            paciente_cns=payload.paciente_cns,
            ciap2=payload.ciap2,
            cid10=payload.cid10,
            procedimento_tuss=payload.procedimento_tuss or "10101012",
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
