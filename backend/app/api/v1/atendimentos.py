from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.atendimento import AtendimentoSOAP, AtendimentoProblema
from app.models.fila import FilaAcolhimento
from app.models.cidadao import Cidadao
from app.schemas.atendimento import AtendimentoSOAPCreate, AtendimentoSOAPOut
from app.core.rbac import (
    PAPEIS_CLINICOS,
    ContextoClinico,
    dependencias_rbac,
    exigir_mesmo_estabelecimento,
    get_contexto_clinico,
)

router = APIRouter(
    prefix="/atendimentos",
    tags=["Atendimento Clínico (SOAP)"],
    dependencies=dependencias_rbac(*PAPEIS_CLINICOS),
)


@router.post("/", response_model=AtendimentoSOAPOut, status_code=201)
def registrar_atendimento_soap(
    payload: AtendimentoSOAPCreate,
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    # O atendimento é do tenant: não se registra SOAP em outra unidade.
    if contexto is not None and not contexto.is_superuser:
        if payload.estabelecimento_id != contexto.estabelecimento_id:
            raise HTTPException(
                status_code=403,
                detail="Não é permitido registrar atendimento em unidade diferente da clínica ativa.",
            )

    cidadao = db.query(Cidadao).filter(Cidadao.id == payload.cidadao_id).first()
    if not cidadao:
        raise HTTPException(status_code=404, detail="Cidadão não encontrado.")

    data = payload.model_dump(exclude={"problemas"})
    atendimento = AtendimentoSOAP(**data)
    atendimento.data_hora_fim = datetime.now(timezone.utc)
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

    # Se veio de uma fila de acolhimento, marca como FINALIZADO — mas só se a
    # entrada de fila pertence à mesma unidade do atendimento.
    if payload.fila_id:
        fila_item = db.query(FilaAcolhimento).filter(FilaAcolhimento.id == payload.fila_id).first()
        if fila_item:
            if (
                contexto is not None
                and not contexto.is_superuser
                and fila_item.estabelecimento_id != contexto.estabelecimento_id
            ):
                raise HTTPException(
                    status_code=403,
                    detail="A entrada de fila informada pertence a outra unidade.",
                )
            fila_item.status = "FINALIZADO"

    db.commit()
    db.refresh(atendimento)
    return atendimento


@router.get("/{atendimento_id}", response_model=AtendimentoSOAPOut)
def obter_atendimento_soap(
    atendimento_id: int,
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    atendimento = db.query(AtendimentoSOAP).filter(AtendimentoSOAP.id == atendimento_id).first()
    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento SOAP não encontrado.")
    exigir_mesmo_estabelecimento(atendimento.estabelecimento_id, contexto, acao="consultar")
    return atendimento


@router.get("/{atendimento_id}/exportar-fai")
def exportar_fai(
    atendimento_id: int,
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    from app.services.fai_exporter import gerar_fai_ledi_payload
    atendimento = db.query(AtendimentoSOAP).filter(AtendimentoSOAP.id == atendimento_id).first()
    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento SOAP não encontrado.")
    exigir_mesmo_estabelecimento(atendimento.estabelecimento_id, contexto, acao="exportar")
    return gerar_fai_ledi_payload(atendimento)
