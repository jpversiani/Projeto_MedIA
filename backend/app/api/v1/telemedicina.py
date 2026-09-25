from datetime import datetime
import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.telemedicina import Teleconsulta as TeleconsultaModel, SalaVirtual as SalaVirtualModel, StatusTeleconsulta
from app.schemas.telemedicina import TeleconsultaCreate

router = APIRouter(prefix="/telemedicina", tags=["Telemedicina"])


class IniciarChamadaRequest(BaseModel):
    teleconsulta_id: int


class FinalizarChamadaRequest(BaseModel):
    teleconsulta_id: int
    dados_soap: Optional[Dict[str, Any]] = None


@router.post("/agendamentos", status_code=status.HTTP_201_CREATED)
def criar_agendamento(dados: TeleconsultaCreate, db: Session = Depends(get_db)):
    codigo_sala = f"sala_{uuid.uuid4().hex[:12]}"
    nova_sala = SalaVirtualModel(
        codigo_sala=codigo_sala,
        status=StatusTeleconsulta.AGENDADA,
        data_criacao=datetime.utcnow()
    )
    db.add(nova_sala)
    db.flush()

    nova_consulta = TeleconsultaModel(
        paciente_cpf=dados.paciente_cpf,
        medico_crm=dados.medico_crm,
        sala_virtual_id=nova_sala.id,
        status=StatusTeleconsulta.AGENDADA,
        diagnostico_ciap2=dados.ciap2,
        diagnostico_cid10=dados.cid10,
        data_inicio=dados.data_hora,
    )
    db.add(nova_consulta)
    db.commit()
    db.refresh(nova_consulta)

    return {
        "id": nova_consulta.id,
        "codigo_sala": codigo_sala,
        "paciente_cpf": nova_consulta.paciente_cpf,
        "medico_crm": nova_consulta.medico_crm,
        "status": nova_consulta.status.value,
        "data_hora": nova_consulta.data_inicio.isoformat() if nova_consulta.data_inicio else None,
    }


@router.get("/salas/{codigo_sala}")
def consultar_sala_virtual(codigo_sala: str, db: Session = Depends(get_db)):
    sala = db.query(SalaVirtualModel).filter(SalaVirtualModel.codigo_sala == codigo_sala).first()
    if not sala:
        raise HTTPException(status_code=404, detail="Sala virtual não encontrada")

    consulta = db.query(TeleconsultaModel).filter(TeleconsultaModel.sala_virtual_id == sala.id).first()
    return {
        "id": sala.id,
        "codigo": sala.codigo_sala,
        "status": sala.status.value,
        "teleconsulta_id": consulta.id if consulta else None,
        "paciente_cpf": consulta.paciente_cpf if consulta else None,
    }


@router.post("/iniciar-chamada")
def iniciar_chamada(payload: IniciarChamadaRequest, db: Session = Depends(get_db)):
    consulta = db.query(TeleconsultaModel).filter(TeleconsultaModel.id == payload.teleconsulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Teleconsulta não encontrada")

    consulta.status = StatusTeleconsulta.EM_ANDAMENTO
    consulta.data_inicio = datetime.utcnow()
    db.commit()
    db.refresh(consulta)
    return {"id": consulta.id, "status": consulta.status.value, "mensagem": "Chamada iniciada"}


@router.post("/finalizar-chamada")
def finalizar_chamada(payload: FinalizarChamadaRequest, db: Session = Depends(get_db)):
    consulta = db.query(TeleconsultaModel).filter(TeleconsultaModel.id == payload.teleconsulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Teleconsulta não encontrada")

    consulta.status = StatusTeleconsulta.CONCLUIDA
    consulta.data_fim = datetime.utcnow()
    if payload.dados_soap:
        consulta.evolucao_soap = payload.dados_soap
    db.commit()
    db.refresh(consulta)
    return {"id": consulta.id, "status": consulta.status.value, "mensagem": "Chamada finalizada com sucesso"}
