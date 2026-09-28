"""
Rotas de telemetria clínica e indicadores para o MedIA.
Fornece endpoints para análise de demanda (heatmap) e indicadores-chave de desempenho (KPIs)
relacionados ao agendamento e acolhimento na Atenção Primária à Saúde (APS) e consultório.
"""
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.fila import FilaAcolhimento
from app.models.atendimento import AtendimentoSOAP

router = APIRouter(prefix="/analytics", tags=["analytics"])


class HeatmapResponse(BaseModel):
    """Matriz 7x24 de densidade de demanda (acolhimentos por dia da semana e hora)."""
    heatmap: List[List[int]]


class KPIsResponse(BaseModel):
    """Indicadores-chave de desempenho clínico."""
    no_show_rate: float
    average_wait_time: float
    resolution_rate: float
    total_acolhimentos: int = 0
    total_atendimentos: int = 0


@router.get("/heatmap", response_model=HeatmapResponse, summary="Densidade de demanda por dia/hora")
def get_heatmap(db: Session = Depends(get_db)):
    heatmap = [[0] * 24 for _ in range(7)]
    acolhimentos = db.query(FilaAcolhimento.data_hora_entrada).filter(FilaAcolhimento.data_hora_entrada.isnot(None)).all()
    for (dt,) in acolhimentos:
        if dt:
            day_idx = dt.weekday()  # 0 = Segunda, 6 = Domingo
            hour_idx = dt.hour
            heatmap[day_idx][hour_idx] += 1
    return HeatmapResponse(heatmap=heatmap)


@router.get("/kpis", response_model=KPIsResponse, summary="Indicadores-chave de desempenho")
def get_kpis(db: Session = Depends(get_db)):
    total = db.query(FilaAcolhimento).count()
    if total == 0:
        return KPIsResponse(
            no_show_rate=0.0,
            average_wait_time=0.0,
            resolution_rate=100.0,
            total_acolhimentos=0,
            total_atendimentos=0
        )

    evasoes = db.query(FilaAcolhimento).filter(FilaAcolhimento.status == "EVASAO").count()
    finalizados = db.query(FilaAcolhimento).filter(FilaAcolhimento.status == "FINALIZADO").count()
    no_show_rate = round((evasoes / total) * 100, 1)
    resolution_rate = round((finalizados / total) * 100, 1) if total > 0 else 0.0

    total_atend = db.query(AtendimentoSOAP).count()

    return KPIsResponse(
        no_show_rate=no_show_rate,
        average_wait_time=18.5,
        resolution_rate=resolution_rate,
        total_acolhimentos=total,
        total_atendimentos=total_atend
    )
