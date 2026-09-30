"""API do Copiloto Clínico (C22) — Projeto MedIA.

Contrato consumido pelo widget ``backend/app/static/js/copiloto_sidebar.js``
(Painel Lateral do Copiloto na teleconsulta do médico — Home Office):

  GET  /api/v1/copiloto/atendimentos/{id}/alertas      -> List[AlertaClinicoOut]
  GET  /api/v1/copiloto/atendimentos/{id}/sugestoes    -> SugestoesCopilotoOut
  POST /api/v1/copiloto/atendimentos/{id}/soap/aceitar -> AuditoriaCopilotoOut
  WS   /api/v1/copiloto/ws/{id}                        -> eventos push (snapshot/ping)

Conformidade:
  - A IA só sugere; o aceite exige revisão do médico e gera auditoria
    (CFM Resolução 2.314/2022, LGPD).
  - Campos SOAP já preenchidos NUNCA são sobrescritos pelo aceite.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Final, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.atendimento import AtendimentoSOAP
from app.models.cidadao import Cidadao
from app.models.copiloto import CopilotoAuditoria
from app.models.prontuario import ProntuarioProblema
from app.schemas.copiloto import (
    AceiteSOAPIn,
    AlertaClinicoOut,
    AuditoriaCopilotoOut,
    EventoCopilotoWS,
    EventoWS,
    SugestoesCopilotoOut,
)
from app.services.copiloto_sugestoes import MODELO_CDS, MotorSugestoesCopiloto

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/copiloto", tags=["Copiloto Clínico (IA)"])

_motor = MotorSugestoesCopiloto()

# Campos SOAP que o aceite da IA pode preencher (nunca sobrescreve preenchidos)
CAMPOS_SOAP: Final[tuple[tuple[str, str, str], ...]] = (
    ("subjetivo", "subjetivo_motivo", "subjetivo_notas"),
    ("objetivo", "objetivo_exame_fisico", "objetivo_antropometria_sinais"),
    ("avaliacao", "avaliacao_notas", None),
    ("plano", "plano_conduta", None),
)


class HubCopilotoWS:
    """Hub em memória de conexões WebSocket do copiloto, por atendimento.

    Publica eventos (ex.: SOAP aceito) para todos os painéis abertos
    naquela teleconsulta, com segurança de threads (endpoint REST síncrono
    publica via ``call_soon_threadsafe`` no loop dos receptores WS).
    """

    def __init__(self) -> None:
        self._filas: dict[int, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._loops: dict[int, list[asyncio.AbstractEventLoop]] = defaultdict(list)

    def conectar(self, atendimento_id: int) -> asyncio.Queue[dict[str, Any]]:
        fila: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._filas[atendimento_id].append(fila)
        self._loops[atendimento_id].append(asyncio.get_running_loop())
        return fila

    def desconectar(self, atendimento_id: int, fila: asyncio.Queue[dict[str, Any]]) -> None:
        if fila in self._filas.get(atendimento_id, []):
            self._filas[atendimento_id].remove(fila)
        if not self._filas.get(atendimento_id):
            self._filas.pop(atendimento_id, None)
            self._loops.pop(atendimento_id, None)

    def publicar(self, atendimento_id: int, evento: dict[str, Any]) -> int:
        """Publica evento a partir de qualquer thread (REST ou WS)."""
        filas = list(self._filas.get(atendimento_id, []))
        loops = list(self._loops.get(atendimento_id, []))
        entregues = 0
        for fila, loop in zip(filas, loops):
            try:
                loop.call_soon_threadsafe(self._oferecer, fila, evento)
                entregues += 1
            except RuntimeError:  # loop encerrado
                continue
        return entregues

    @staticmethod
    def _oferecer(fila: asyncio.Queue[dict[str, Any]], evento: dict[str, Any]) -> None:
        fila.put_nowait(evento)

    def contagem_conexoes(self, atendimento_id: int) -> int:
        return len(self._filas.get(atendimento_id, []))


hub = HubCopilotoWS()


# ---------------------------------------------------------------------------
# Helpers de contexto clínico
# ---------------------------------------------------------------------------
def _obter_atendimento(db: Session, atendimento_id: int) -> AtendimentoSOAP:
    atendimento = db.query(AtendimentoSOAP).filter(AtendimentoSOAP.id == atendimento_id).first()
    if not atendimento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atendimento SOAP não encontrado.")
    return atendimento


def _resolver_problemas(db: Session, atendimento: AtendimentoSOAP) -> list[tuple[str, str, str]]:
    """Problemas ativos do atendimento + da lista de problemas do cidadão."""
    problemas: list[tuple[str, str, str]] = []
    for prob in atendimento.problemas:
        if prob.situacao == "ATIVO":
            problemas.append((prob.tipo_codigo, prob.codigo, prob.descricao))
    if atendimento.cidadao_id is not None:
        prontuario = (
            db.query(ProntuarioProblema)
            .filter(
                ProntuarioProblema.cidadao_id == atendimento.cidadao_id,
                ProntuarioProblema.situacao == "ATIVO",
            )
            .all()
        )
        problemas.extend((p.tipo_codigo, p.codigo, p.descricao) for p in prontuario)
    return problemas


def _gerar_alertas(db: Session, atendimento: AtendimentoSOAP) -> tuple[AlertaClinicoOut, ...]:
    cidadao = (
        db.query(Cidadao).filter(Cidadao.id == atendimento.cidadao_id).first()
        if atendimento.cidadao_id is not None
        else None
    )
    problemas = _resolver_problemas(db, atendimento)
    if cidadao is None:
        cidadao = Cidadao(
            id=atendimento.cidadao_id or 0,
            nome_completo="Cidadão não identificado",
            data_nascimento=datetime.now(timezone.utc).date(),
            sexo="I",
        )
    return _motor.gerar_alertas(atendimento, cidadao, problemas)


def _evento(
    tipo: EventoWS, atendimento_id: int, dados: dict[str, Any]
) -> dict[str, Any]:
    return EventoCopilotoWS(tipo=tipo, atendimento_id=atendimento_id, dados=dados).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints REST
# ---------------------------------------------------------------------------
@router.get("/atendimentos/{atendimento_id}/alertas", response_model=list[AlertaClinicoOut])
def listar_alertas(atendimento_id: int, db: Session = Depends(get_db)) -> list[AlertaClinicoOut]:
    """Alertas de risco/alergia do atendimento (painel piscante do médico)."""
    atendimento = _obter_atendimento(db, atendimento_id)
    return list(_gerar_alertas(db, atendimento))


@router.get("/atendimentos/{atendimento_id}/sugestoes", response_model=SugestoesCopilotoOut)
def listar_sugestoes(atendimento_id: int, db: Session = Depends(get_db)) -> SugestoesCopilotoOut:
    """Sugestão SOAP + exames complementares + dosagens usuais SUS (RENAME)."""
    atendimento = _obter_atendimento(db, atendimento_id)
    cidadao = (
        db.query(Cidadao).filter(Cidadao.id == atendimento.cidadao_id).first()
        if atendimento.cidadao_id is not None
        else None
    )
    problemas = _resolver_problemas(db, atendimento)
    exames = _motor.sugerir_exames(problemas)
    dosagens = _motor.sugerir_dosagens(problemas)
    soap = _motor.sugerir_soap(atendimento, cidadao or _cidadao_placeholder(atendimento), problemas, exames, dosagens)
    return SugestoesCopilotoOut(
        atendimento_id=atendimento.id, soap=soap, exames_complementares=exames, dosagens_sus=dosagens
    )


def _cidadao_placeholder(atendimento: AtendimentoSOAP) -> Cidadao:
    return Cidadao(
        id=atendimento.cidadao_id or 0,
        nome_completo="Cidadão não identificado",
        data_nascimento=datetime.now(timezone.utc).date(),
        sexo="I",
    )


@router.post(
    "/atendimentos/{atendimento_id}/soap/aceitar",
    response_model=AuditoriaCopilotoOut,
    status_code=status.HTTP_201_CREATED,
)
def aceitar_soap_ia(
    atendimento_id: int, payload: AceiteSOAPIn, db: Session = Depends(get_db)
) -> AuditoriaCopilotoOut:
    """Registra o aceite/revisão do rascunho SOAP da IA (auditoria CFM 2.314/2022).

    Preenche apenas campos vazios do atendimento; campos já preenchidos
    pelo médico NUNCA são sobrescritos (segurança assistencial).
    """
    atendimento = _obter_atendimento(db, atendimento_id)

    conteudos: dict[str, str] = {
        "subjetivo": payload.subjetivo,
        "objetivo": payload.objetivo,
        "avaliacao": payload.avaliacao,
        "plano": payload.plano,
    }
    preenchidos: list[str] = []
    for campo, coluna_a, coluna_b in CAMPOS_SOAP:
        valor = conteudos[campo]
        if getattr(atendimento, coluna_a) in (None, ""):
            setattr(atendimento, coluna_a, valor)
            preenchidos.append(coluna_a)
        elif coluna_b is not None and getattr(atendimento, coluna_b) in (None, ""):
            setattr(atendimento, coluna_b, valor)
            preenchidos.append(coluna_b)

    if payload.cid10 and not atendimento.diagnostico_cid10:
        atendimento.diagnostico_cid10 = payload.cid10
    if payload.ciap2 and not atendimento.diagnostico_ciap2:
        atendimento.diagnostico_ciap2 = payload.ciap2

    auditoria = CopilotoAuditoria(
        atendimento_id=atendimento.id,
        profissional_id=payload.profissional_id,
        origem=payload.origem.value,
        campos_preenchidos=preenchidos,
        subjetivo=payload.subjetivo,
        objetivo=payload.objetivo,
        avaliacao=payload.avaliacao,
        plano=payload.plano,
        cid10=payload.cid10,
        ciap2=payload.ciap2,
        modelo=MODELO_CDS,
    )
    db.add(auditoria)
    db.commit()
    db.refresh(auditoria)

    hub.publicar(
        atendimento.id,
        _evento(
            EventoWS.SOAP_ACEITO,
            atendimento.id,
            {"auditoria_id": auditoria.id, "origem": auditoria.origem, "campos_preenchidos": preenchidos},
        ),
    )
    return AuditoriaCopilotoOut.model_validate(auditoria)


# ---------------------------------------------------------------------------
# WebSocket (push em tempo real para o painel)
# ---------------------------------------------------------------------------
@router.websocket("/ws/{atendimento_id}")
async def ws_copiloto(
    websocket: WebSocket,
    atendimento_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Snapshot de alertas + eventos push + pong (keepalive do painel)."""
    await websocket.accept()
    fila = hub.conectar(atendimento_id)
    ids_enviados: set[str] = set()
    try:
        _obter_atendimento(db, atendimento_id)  # 404 equivalente: fecha WS
        alertas = _gerar_alertas(db, atendimento)
        ids_enviados = {a.id for a in alertas}
        await websocket.send_json(
            _evento(
                EventoWS.SNAPSHOT_ALERTAS,
                atendimento_id,
                {"alertas": [a.model_dump(mode="json") for a in alertas]},
            )
        )

        receber = asyncio.create_task(websocket.receive_text())
        extrair = asyncio.create_task(fila.get())
        try:
            while True:
                feito, pendente = await asyncio.wait(
                    {receber, extrair}, return_when=asyncio.FIRST_COMPLETED
                )
                if receber in feito:
                    try:
                        mensagem = receber.result()
                    except WebSocketDisconnect:
                        break
                    if mensagem.strip().lower() == "ping":
                        await websocket.send_json(_evento(EventoWS.PONG, atendimento_id, {}))
                    receber = asyncio.create_task(websocket.receive_text())
                if extrair in feito:
                    evento = extrair.result()
                    await websocket.send_json(evento)
                    extrair = asyncio.create_task(fila.get())
        finally:
            receber.cancel()
            extrair.cancel()
    except WebSocketDisconnect:
        logger.info("Painel do copiloto desconectado (atendimento %s)", atendimento_id)
    except HTTPException:
        await websocket.close(code=4404)
    finally:
        hub.desconectar(atendimento_id, fila)


# ---------------------------------------------------------------------------
# ROTAS DE IA GENERATIVA CLÍNICA (GEMINI & FALLBACK DE APS)
# ---------------------------------------------------------------------------

from app.services.copiloto_ia_generativa import (
    MotorIAGenerativaCopiloto,
    SugestaoSOAPIA,
    HipoteseDiagnosticaIA,
)
from pydantic import BaseModel, Field


class GerarSOAPRequest(BaseModel):
    texto_bruto: str = Field(..., description="Anotações clínicas livres ou transcrição da consulta")
    paciente_nome: Optional[str] = None


class DiagnosticoDiferencialRequest(BaseModel):
    sintomas: str = Field(..., description="Queixa e sintomas relatados pelo paciente")


GerarSOAPRequest.model_rebuild()
DiagnosticoDiferencialRequest.model_rebuild()


@router.post("/ia/gerar-soap", response_model=SugestaoSOAPIA)
def gerar_soap_com_ia(payload: GerarSOAPRequest):
    """
    Estrutura anotações clínicas livres ou transcrições de áudio no padrão SOAP
    utilizando IA Generativa (Google Gemini) com fallback determinístico de APS.
    """
    contexto = {"paciente_nome": payload.paciente_nome} if payload.paciente_nome else None
    return MotorIAGenerativaCopiloto.estruturar_soap(payload.texto_bruto, contexto)


@router.post("/ia/diagnostico-diferencial", response_model=list[HipoteseDiagnosticaIA])
def gerar_diagnostico_diferencial_ia(payload: DiagnosticoDiferencialRequest):
    """
    Gera hipóteses diagnósticas diferenciais estruturadas com justificativas e códigos CID-10 e CID-11.
    """
    return MotorIAGenerativaCopiloto.diagnostico_diferencial(payload.sintomas)
