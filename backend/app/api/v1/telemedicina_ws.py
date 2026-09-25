"""Hub WebSocket de telemedicina: signaling WebRTC (SDP/ICE) e sincronização de estado médico."""

import asyncio
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, field_validator

router = APIRouter(tags=["telemedicina"])


class PapelParticipante(str, Enum):
    MEDICO = "medico"
    PACIENTE = "paciente"


class TipoMensagemWS(str, Enum):
    JOIN = "join"
    JOIN_SALA = "join_sala"
    LEAVE_SALA = "leave_sala"
    OFFER = "offer"
    ANSWER = "answer"
    ICE_CANDIDATE = "ice_candidate"
    ESTADO_MEDICO = "estado_medico"
    ESTADO_PACIENTE = "estado_paciente"
    CONSENTIMENTO = "consentimento"
    ERRO = "erro"
    OK = "ok"


class EstadoSessao(str, Enum):
    AGUARDANDO_MEDICO = "aguardando_medico"
    AGUARDANDO_PACIENTE = "aguardando_paciente"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"


def _normalizar_cns(valor: Optional[str]) -> str:
    return re.sub(r"\D", "", valor or "")


class ConsentimentoBase(BaseModel):
    cns_profissional: str
    escopo: str
    metodo_contato: str

    @field_validator("cns_profissional")
    @classmethod
    def normalizar_cns(cls, valor: str) -> str:
        return _normalizar_cns(valor)


class AtualizacaoEstadoMedico(BaseModel):
    status: str
    cns_medico: str

    @field_validator("cns_medico")
    @classmethod
    def normalizar_cns(cls, valor: str) -> str:
        return _normalizar_cns(valor)


class AtualizacaoEstadoPaciente(BaseModel):
    cns_paciente: str
    status: str
    queixa_principal: Optional[str] = None

    @field_validator("cns_paciente")
    @classmethod
    def normalizar_cns(cls, valor: str) -> str:
        return _normalizar_cns(valor)


class MensagemSDPSignal(BaseModel):
    tipo: str
    sala_codigo: str
    sdp: str
    paciente_id: Optional[str] = None
    prestador_id: Optional[str] = None


class EnvelopeEntrada(BaseModel):
    tipo: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class EnvelopeSaida(BaseModel):
    tipo: str
    de_papel: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SalaVirtual:
    def __init__(self, codigo: str, db: Any = None):
        self.codigo = codigo
        self.db = db
        self.participantes: List[Any] = []
        self.status = EstadoSessao.AGUARDANDO_MEDICO
        self.criada_em = datetime.now(timezone.utc)


class FilaParticipante:
    __slots__ = ("papel", "fila")

    def __init__(self, papel: PapelParticipante, fila: Any):
        self.papel = papel
        self.fila = fila


def _papeis_alvo(tipo: str) -> Optional[Set[str]]:
    if tipo == TipoMensagemWS.ESTADO_MEDICO.value:
        return {PapelParticipante.PACIENTE.value}
    if tipo == TipoMensagemWS.ESTADO_PACIENTE.value:
        return {PapelParticipante.MEDICO.value}
    return None


class HubTelemedicinaWS:
    def __init__(self):
        self._salas: Dict[str, SalaVirtual] = {}
        self._filas: Dict[str, List[Any]] = {}
        self._stats: Dict[str, Dict[str, Any]] = {}

    def criar_sala(self, codigo: str, db: Any = None) -> SalaVirtual:
        sala = SalaVirtual(codigo, db)
        self._salas[codigo] = sala
        self._filas.setdefault(codigo, [])
        self._stats.setdefault(codigo, {"conexoes": 0, "eventos": 0})
        return sala

    def encerrar_sala(self, codigo: str) -> None:
        self._salas.pop(codigo, None)
        self._filas.pop(codigo, None)

    def adicionar_participante(self, codigo: str, participante: Any) -> None:
        sala = self._salas[codigo]
        if participante not in sala.participantes:
            sala.participantes.append(participante)

    def remover_participante(self, codigo: str, papel: PapelParticipante) -> None:
        sala = self._salas[codigo]
        sala.participantes = [
            p for p in sala.participantes if getattr(p, "papel", None) != papel
        ]

    def obter_estatisticas(self, codigo: str) -> Dict[str, Any]:
        sala = self._salas.get(codigo)
        stats = self._stats.get(codigo, {"conexoes": 0, "eventos": 0})
        return {
            "sala_codigo": codigo,
            "conexoes": stats.get("conexoes", 0),
            "eventos": stats.get("eventos", 0),
            "existe": sala is not None,
            "status": sala.status.value if sala else None,
            "participantes": len(sala.participantes) if sala else 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def registrar_fila(self, codigo: str, papel: PapelParticipante, fila: Any) -> None:
        self._filas.setdefault(codigo, []).append(FilaParticipante(papel, fila))
        stats = self._stats.setdefault(codigo, {"conexoes": 0, "eventos": 0})
        stats["conexoes"] += 1

    def remover_fila(self, codigo: str, fila: Any) -> None:
        filas = self._filas.get(codigo, [])
        self._filas[codigo] = [f for f in filas if getattr(f, "fila", None) is not fila]
        stats = self._stats.get(codigo)
        if stats and stats.get("conexoes", 0) > 0:
            stats["conexoes"] -= 1

    def publicar(
        self,
        codigo: str,
        evento: Dict[str, Any],
        papeis: Optional[Set[Any]] = None,
    ) -> int:
        entregues = 0
        for item in self._filas.get(codigo, []):
            papel = getattr(item, "papel", None)
            if papeis and isinstance(papel, (PapelParticipante, str)):
                if papel not in papeis:
                    continue
            alvo = getattr(item, "fila", item)
            try:
                alvo.put_nowait(evento)
                entregues += 1
            except Exception:
                continue
        stats = self._stats.setdefault(codigo, {"conexoes": 0, "eventos": 0})
        stats["eventos"] += 1
        return entregues


hub = HubTelemedicinaWS()


@router.websocket("/ws/telemedicina/sala/{codigo_sala}")
async def telemedicina_sala_ws(
    websocket: WebSocket, codigo_sala: str, papel: str = "medico"
) -> None:
    try:
        papel_enum = PapelParticipante(papel)
    except ValueError:
        await websocket.close(code=4400, reason="papel invalido")
        return

    await websocket.accept()

    if codigo_sala not in hub._salas:
        hub.criar_sala(codigo_sala)

    fila: asyncio.Queue = asyncio.Queue(maxsize=256)
    hub.registrar_fila(codigo_sala, papel_enum, fila)

    async def _enviador() -> None:
        while True:
            evento = await fila.get()
            await websocket.send_json(evento)

    remetente = asyncio.create_task(_enviador())
    try:
        await websocket.send_json(
            EnvelopeSaida(
                tipo=TipoMensagemWS.OK.value,
                de_papel=papel_enum.value,
                payload={"evento": "conectado", "sala_codigo": codigo_sala},
            ).model_dump(mode="json")
        )
        while True:
            bruto = await websocket.receive_json()
            envelope = EnvelopeEntrada.model_validate(bruto)
            if envelope.tipo == TipoMensagemWS.JOIN_SALA.value:
                await websocket.send_json(
                    EnvelopeSaida(
                        tipo=TipoMensagemWS.OK.value,
                        de_papel=papel_enum.value,
                        payload={
                            "evento": "sala_ingressada",
                            "sala_codigo": codigo_sala,
                            "estatisticas": hub.obter_estatisticas(codigo_sala),
                        },
                    ).model_dump(mode="json")
                )
                continue
            evento = {
                "tipo": envelope.tipo,
                "de_papel": papel_enum.value,
                "payload": envelope.payload,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            hub.publicar(codigo_sala, evento, _papeis_alvo(envelope.tipo))
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close(code=4410, reason="erro interno")
        except Exception:
            pass
    finally:
        remetente.cancel()
        hub.remover_fila(codigo_sala, fila)
