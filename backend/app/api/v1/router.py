from fastapi import APIRouter
from app.api.v1.cidadaos import router as cidadaos_router
from app.api.v1.fila import router as fila_router
from app.api.v1.atendimentos import router as atendimentos_router
from app.api.v1.terminologias import router as terminologias_router
from app.api.v1.estabelecimentos import router as estabelecimentos_router
from app.api.v1.telemedicina import router as telemedicina_router
from app.api.v1.prontuario import router as prontuario_router
from app.api.v1.copiloto import router as copiloto_router
from app.api.v1.farmacia import router as farmacia_router
from app.api.v1.telemedicina_ws import router as telemedicina_ws_router
from app.api.v1.convenios import router as convenios_router
from app.api.v1.auth import router as auth_router
from app.api.v1.tiss import router as tiss_router
from app.api.v1.dmed import router as dmed_router
from app.api.v1.clinica import router as clinica_router
from app.api.v1.agenda_medica import router as agenda_medica_router
from app.api.v1.prescricao_cfm import router as prescricao_cfm_router
from app.api.v1.financeiro_medico import router as financeiro_medico_router
from app.api.v1.fluxo_atendimento import router as fluxo_atendimento_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(cidadaos_router)

api_router.include_router(fila_router)
api_router.include_router(atendimentos_router)
api_router.include_router(terminologias_router)
api_router.include_router(estabelecimentos_router)
api_router.include_router(telemedicina_router)
api_router.include_router(agenda_medica_router)
api_router.include_router(prescricao_cfm_router)
api_router.include_router(financeiro_medico_router)
api_router.include_router(prontuario_router)
api_router.include_router(copiloto_router)
api_router.include_router(telemedicina_ws_router)
api_router.include_router(farmacia_router)
api_router.include_router(convenios_router)
api_router.include_router(tiss_router)
api_router.include_router(dmed_router)
api_router.include_router(clinica_router)
api_router.include_router(fluxo_atendimento_router)

