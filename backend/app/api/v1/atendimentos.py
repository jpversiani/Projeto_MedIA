from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.atendimento import AtendimentoSOAP, AtendimentoProblema
from app.models.fila import FilaAcolhimento
from app.models.cidadao import Cidadao
from app.schemas.atendimento import AtendimentoSOAPCreate, AtendimentoSOAPOut

router = APIRouter(prefix="/atendimentos", tags=["Atendimento Clínico (SOAP)"])

@router.post("/", response_model=AtendimentoSOAPOut, status_code=201)
def registrar_atendimento_soap(payload: AtendimentoSOAPCreate, db: Session = Depends(get_db)):
    cidadao = db.query(Cidadao).filter(Cidadao.id == payload.cidadao_id).first()
    if not cidadao:
        raise HTTPException(status_code=404, detail="Cidadão não encontrado.")

    data = payload.model_dump(exclude={"problemas"})
    atendimento = AtendimentoSOAP(**data)
    atendimento.data_hora_fim = datetime.utcnow()
    db.add(atendimento)
    db.flush()

    for prob in payload.problemas:
        item_problema = AtendimentoProblema(
            atendimento_id=atendimento.id,
            tipo_codigo=prob.tipo_codigo,
            codigo=prob.codigo,
            descricao=prob.descricao,
            situacao=prob.situacao
        )
        db.add(item_problema)

    # Se veio de uma fila de acolhimento, marca como FINALIZADO
    if payload.fila_id:
        fila_item = db.query(FilaAcolhimento).filter(FilaAcolhimento.id == payload.fila_id).first()
        if fila_item:
            fila_item.status = "FINALIZADO"

    db.commit()
    db.refresh(atendimento)
    return atendimento

@router.get("/{atendimento_id}", response_model=AtendimentoSOAPOut)
def obter_atendimento_soap(atendimento_id: int, db: Session = Depends(get_db)):
    atendimento = db.query(AtendimentoSOAP).filter(AtendimentoSOAP.id == atendimento_id).first()
    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento SOAP não encontrado.")
    return atendimento

@router.get("/{atendimento_id}/exportar-fai")
def exportar_fai(atendimento_id: int, db: Session = Depends(get_db)):
    from app.services.fai_exporter import gerar_fai_ledi_payload
    atendimento = db.query(AtendimentoSOAP).filter(AtendimentoSOAP.id == atendimento_id).first()
    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento SOAP não encontrado.")
    return gerar_fai_ledi_payload(atendimento)

