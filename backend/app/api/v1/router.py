from fastapi import APIRouter, Depends
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
from app.api.v1.prescricao_cfm import router_publico as prescricao_publico_router
from app.api.v1.financeiro_medico import router as financeiro_medico_router
from app.api.v1.fluxo_atendimento import router as fluxo_atendimento_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.health import router as health_router
from app.api.v1.sincronizacao import router as sincronizacao_router
from app.api.v1.auth import router as auth_router, get_current_user
from app.api.v1.conformidade import router as conformidade_router
from app.core.config import settings

api_router = APIRouter()

# --------------------------------------------------------------------------
# Rotas públicas: health e autenticação (login, SSO, troca de clínica).
# `/auth/me`, `/auth/switch-clinic` e `/auth/audit-trail` já validam o token
# por conta própria via `Depends(get_current_user)`.
# --------------------------------------------------------------------------
api_router.include_router(health_router)
api_router.include_router(auth_router)

# Validação pública de receita/atestado: o QR Code é conferido em farmácia por
# alguém que NÃO tem conta no sistema, então esta rota não pode exigir Bearer
# token. Ela devolve apenas a visão mascarada do documento.
api_router.include_router(prescricao_publico_router)

# Sinalização da teleconsulta (WebSocket). NÃO entra no bloco clínico porque
# `Depends(get_current_user)` é uma dependência HTTP: aplicada a um WebSocket
# ela levanta HTTPException no handshake e derruba a conexão antes de o
# navegador conseguir autenticar. A autenticação acontece dentro do próprio
# handler (`_autenticar`), que aceita o token por query string — o browser não
# permite definir cabeçalhos em `new WebSocket()`.
api_router.include_router(telemedicina_ws_router)

# --------------------------------------------------------------------------
# Rotas clínicas (prontuário, cidadão, agenda, prescrição, TISS, DMED,
# telemedicina, farmácia, convênios, financeiro, sincronização...).
#
# Antes, cada uma dessas ~88 rotas aceitava requisição anônima: bastava
# `curl /api/v1/cidadaos/` para listar pacientes e `curl -X POST
# /api/v1/prescricao/emitir` para gerar uma receita. A autenticação agora é
# aplicada no nível do router, de modo que nenhuma rota nova nasce aberta.
# Fora de desenvolvimento (`settings.require_auth`) isso é OBRIGATÓRIO.
# --------------------------------------------------------------------------
_ROUTERS_CLINICOS = (
    cidadaos_router,
    fila_router,
    atendimentos_router,
    terminologias_router,
    estabelecimentos_router,
    telemedicina_router,
    agenda_medica_router,
    prescricao_cfm_router,
    financeiro_medico_router,
    prontuario_router,
    copiloto_router,
    farmacia_router,
    convenios_router,
    tiss_router,
    dmed_router,
    clinica_router,
    fluxo_atendimento_router,
    analytics_router,
    # Ciclo de vida do dado (LGPD Art. 16): plano de retenção e execução.
    # Restrito a gestão; a execução, a ADMIN.
    conformidade_router,
    # Upload de contingência offline: transporta CNS, CPF e o SOAP completo,
    # portanto é dado clínico e precisa da mesma proteção das demais rotas.
    sincronizacao_router,
)


def build_clinical_router(require_auth: bool) -> APIRouter:
    """Monta o router clínico, exigindo Bearer token quando `require_auth`.

    Factory separada para que os testes possam montar as duas variantes sem
    depender do estado global da aplicação.
    """
    dependencias = [Depends(get_current_user)] if require_auth else []
    router = APIRouter(dependencies=dependencias)
    for sub in _ROUTERS_CLINICOS:
        router.include_router(sub)
    return router


clinicas_router = build_clinical_router(settings.require_auth)

api_router.include_router(clinicas_router)

