from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/analytics", tags=["analytics"])

class KPISummary(BaseModel):
    taxa_absenteismo: float
    total_agendamentos: int
    total_faltas: int

@router.get("/kpis", response_model=KPISummary)
def get_kpis():
    return KPISummary(taxa_absenteismo=0.0, total_agendamentos=0, total_faltas=0)

@router.get("/heatmap")
def get_heatmap() -> Dict[str, Any]:
    # Matriz 7x24 para dias da semana e horas
    matriz = [[0 for _ in range(24)] for _ in range(7)]
    return {"heatmap": matriz}
