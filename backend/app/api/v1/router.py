from fastapi import APIRouter
from app.api.v1.cidadaos import router as cidadaos_router
from app.api.v1.fila import router as fila_router
from app.api.v1.atendimentos import router as atendimentos_router
from app.api.v1.terminologias import router as terminologias_router
from app.api.v1.estabelecimentos import router as estabelecimentos_router
from app.api.v1.copilot import router as copilot_router

api_router = APIRouter()

api_router.include_router(cidadaos_router)
api_router.include_router(fila_router)
api_router.include_router(atendimentos_router)
api_router.include_router(terminologias_router)
api_router.include_router(estabelecimentos_router)
api_router.include_router(copilot_router)
