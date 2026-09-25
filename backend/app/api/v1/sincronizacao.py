"""Endpoints de sincronização offline (C29) — upload de contingência do PEC.

Contrato consumido por ``backend/app/static/js/offline_sync_indicator.js``:

* ``POST /api/v1/sincronizacao/atendimentos`` — envia o lote de atendimentos
  aguardando upload (idempotente por ``id_local``).
* ``GET  /api/v1/sincronizacao/status`` — auditoria do servidor.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.atendimento_offline import (
    LoteSincronizacaoRequest,
    LoteSincronizacaoResponse,
    StatusSincronizacaoOut,
)
from app.services.sync_offline import ServicoSincronizacaoOffline

router = APIRouter(prefix="/sincronizacao", tags=["Sincronização Offline (C29)"])


@router.post(
    "/atendimentos",
    response_model=LoteSincronizacaoResponse,
    status_code=201,
    summary="Upload do lote de atendimentos aguardando sincronização",
)
def sincronizar_atendimentos_offline(
    lote: LoteSincronizacaoRequest, db: Session = Depends(get_db)
) -> LoteSincronizacaoResponse:
    """Recebe os atendimentos registrados em contingência offline na UBS.

    Idempotente por ``id_local``: itens reenviados (ex.: após queda de rede no
    meio do upload) são reportados em ``duplicados`` sem duplicar registros.
    """
    return ServicoSincronizacaoOffline(db).ingestar_lote(lote)


@router.get(
    "/status",
    response_model=StatusSincronizacaoOut,
    status_code=200,
    summary="Painel de auditoria da sincronização offline",
)
def status_sincronizacao_offline(db: Session = Depends(get_db)) -> StatusSincronizacaoOut:
    """Retorna o total de atendimentos de contingência já recebidos pelo servidor."""
    return ServicoSincronizacaoOffline(db).status_geral()
