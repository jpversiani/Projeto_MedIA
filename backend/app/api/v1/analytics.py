# backend/app/api/v1/analytics.py
"""
Rotas de telemetria clínica para o MedIA.

Fornece endpoints para análise de demanda (heatmap) e indicadores-chave de desempenho (KPIs)
relacionados ao agendamento e atendimento na Atenção Primária à Saúde (APS).
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.appointment import Appointment
from pydantic import BaseModel

router = APIRouter(prefix="/analytics", tags=["analytics"])


# Schemas de resposta
class HeatmapResponse(BaseModel):
    """Matriz 7x24 de densidade de demanda (agendamentos por dia da semana e hora)."""
    heatmap: List[List[int]]  # 7 dias (segunda=0, domingo=6) x 24 horas


class KPIsResponse(BaseModel):
    """Indicadores-chave de desempenho clínico."""
    no_show_rate: float          # percentual de não comparecimento
    average_wait_time: float     # tempo médio de espera em minutos
    resolution_rate: float       # taxa de resolutividade na APS


@router.get("/heatmap", response_model=HeatmapResponse, summary="Densidade de demanda por dia/hora")
def get_heatmap(db: Session = Depends(get_db)):
    """
    Retorna uma matriz 7x24 com a contagem de agendamentos por dia da semana e hora.

    - Dia da semana: segunda-feira = 0, domingo = 6
    - Hora: 0 a 23
    """
    # Consulta agregada: conta agendamentos agrupados por dia da semana e hora
    results = db.query(
        func.extract('dow', Appointment.scheduled_at).label('dow'),
        func.extract('hour', Appointment.scheduled_at).label('hour'),
        func.count(Appointment.id).label('count')
    ).group_by('dow', 'hour').all()

    # Inicializa matriz 7x24 com zeros
    heatmap = [[0] * 24 for _ in range(7)]

    for dow, hour, count in results:
        # Converte dow (0=domingo, 1=segunda, ..., 6=sábado) para índice (segunda=0, domingo=6)
        day_index = (int(dow) - 1) % 7
        heatmap[day_index][int(hour)] = count

    return HeatmapResponse(heatmap=heatmap)


@router.get("/kpis", response_model=KPIsResponse, summary="Indicadores-chave de desempenho")
def get_kpis(db: Session = Depends(get_db)):
    """
    Calcula KPIs a partir dos dados de agendamento e atendimento.

    - no_show_rate: percentual de agendamentos com status 'no_show' em relação aos agendamentos
      que não foram cancelados (status em 'scheduled', 'completed', 'no_show').
    - average_wait_time: média em minutos entre o check-in e o início do atendimento.
    - resolution_rate: percentual de atendimentos concluídos que foram resolvidos na APS
      (campo 'resolved' = True).
    """
    # No-show rate
    total_scheduled = db.query(func.count(Appointment.id)).filter(
        Appointment.status.in_(['scheduled', 'completed', 'no_show'])
    ).scalar()
    no_show = db.query(func.count(Appointment.id)).filter(
        Appointment.status == 'no_show'
    ).scalar()
    no_show_rate = (no_show / total_scheduled * 100) if total_scheduled else 0.0

    # Average wait time (minutos)
    avg_wait = db.query(
        func.avg(
            func.extract('epoch', Appointment.start_time - Appointment.check_in_time) / 60
        )
    ).filter(
        Appointment.check_in_time.isnot(None),
        Appointment.start_time.isnot(None)
    ).scalar()
    average_wait_time = float(avg_wait) if avg_wait is not None else 0.0

    # Resolution rate
    completed = db.query(func.count(Appointment.id)).filter(
        Appointment.status == 'completed'
    ).scalar()
    resolved = db.query(func.count(Appointment.id)).filter(
        Appointment.status == 'completed',
        Appointment.resolved == True  # noqa: E712
    ).scalar()
    resolution_rate = (resolved / completed * 100) if completed else 0.0

    return KPIsResponse(
        no_show_rate=no_show_rate,
        average_wait_time=average_wait_time,
        resolution_rate=resolution_rate
    )
