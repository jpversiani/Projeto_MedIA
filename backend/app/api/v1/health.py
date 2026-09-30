"""
Endpoint de Healthcheck e Liveness/Readiness Probe para Kubernetes e Docker.
"""

from datetime import datetime, timezone
import time
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["Saúde do Sistema"])

_START_TIME = time.time()


@router.get("/health")
def healthcheck(db: Session = Depends(get_db)):
    """Verifica a conectividade do banco de dados e a integridade dos serviços."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_ok = False

    uptime_segundos = int(time.time() - _START_TIME)

    resposta = {
        "status": "healthy" if db_ok else "degraded",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected" if db_ok else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_segundos": uptime_segundos,
    }

    status_code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=resposta, status_code=status_code)
