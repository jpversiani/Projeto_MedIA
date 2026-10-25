"""Hub WebSocket de telemedicina: sinalização WebRTC (SDP/ICE) e estado clínico.

Esta rota é o **plano de controle** da teleconsulta: por ela passam ``offer``,
``answer`` e candidatos ICE — nunca áudio ou vídeo, que seguem direto entre os
navegadores por RTP/SRTP.

O que mudou (T3):

* **Autenticação** — o WebSocket exige o mesmo access token JWT das rotas
  REST. Antes qualquer pessoa que soubesse o código da sala entrava como
  "médico", porque o papel vinha da query string e não era verificado.
* **Roteamento por destino** — mensagens de sinalização vão apenas para o
  outro participante. Antes o ``offer`` era republicado para todos, inclusive
  para quem ofertou, e a negociação nunca fechava.
* **Presença explícita** — ``peer_joined``/``peer_left`` avisam o médico que o
  paciente entrou ou caiu, em vez de deixar a tela preta sem explicação.
* **Limite de sala** — teleconsulta é 1:1; um terceiro conexão é recusada.
* **Auditoria** — entrada e saída geram evento na trilha encadeada (LGPD/CFM).
"""

import asyncio
import json
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, field_validator

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.signaling_hub import (
    Participante,
    ParticipanteJaConectado,
    SalaOcupada,
    hub_signaling,
)

router = APIRouter(tags=["telemedicina"])


class PapelParticipante(str, Enum):
    MEDICO = "medico"
    PACIENTE = "paciente"


class TipoMensagemWS(str, Enum):
    JOIN = "join"
    JOIN_SALA = "join_sala"
    LEAVE_SALA = "leave_sala"
    LEAVE = "leave"
    OFFER = "offer"
    ANSWER = "answer"
    ICE_CANDIDATE = "ice_candidate"
    ESTADO_MEDICO = "estado_medico"
    ESTADO_PACIENTE = "estado_paciente"
    CONSENTIMENTO = "consentimento"
    PING = "ping"
    PONG = "pong"
    PEER_JOINED = "peer_joined"
    PEER_LEFT = "peer_left"
    SALA_INGRESSADA = "sala_ingressada"
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
    """Representação em memória usada pelos testes de unidade do hub legado."""

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
    """Hub legado (fila por participante) mantido para compatibilidade.

    A teleconsulta real usa ``app.services.signaling_hub.SignalingHub``, que
    roteia por destino. Esta classe continua existindo porque testes de unidade
    e utilitários internos usam ``criar_sala``/``publicar``/``obter_estatisticas``.
    """

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


# =========================================================================
# Autenticação e validação da sala
# =========================================================================
def _extrair_token(websocket: WebSocket, token_query: Optional[str]) -> Optional[str]:
    """Token via query string (o browser não consegue definir cabeçalhos no WS)."""
    if token_query:
        return token_query
    cabecalho = websocket.headers.get("authorization") or ""
    if cabecalho.lower().startswith("bearer "):
        return cabecalho.split(" ", 1)[1]
    return None


def _autenticar(websocket: WebSocket, token_query: Optional[str]):
    """Resolve ``(usuario_id, papel, nome)`` a partir do token.

    Devolve ``(None, papel_da_query, "Convidado")`` quando a autenticação está
    desligada (desenvolvimento), preservando o comportamento da demo.
    """
    from app.services.auth_service import decode_access_token

    token = _extrair_token(websocket, token_query)
    if not token:
        if settings.require_auth:
            raise PermissionError("Token de acesso ausente.")
        return None, None, "Convidado"

    dados = decode_access_token(token)
    if not dados or "sub" not in dados:
        raise PermissionError("Token inválido ou expirado.")

    papel_token = str(dados.get("papel") or "").upper()
    if papel_token in ("MEDICO", "ADMIN"):
        papel = PapelParticipante.MEDICO.value
    elif papel_token == "PACIENTE":
        papel = PapelParticipante.PACIENTE.value
    else:
        # Recepção/farmácia não participam da chamada clínica.
        raise PermissionError("Papel sem permissão para entrar na teleconsulta.")

    return int(dados["sub"]), papel, dados.get("nome") or "Usuário"


def _validar_sala(codigo_sala: str) -> Optional[str]:
    """Confere a sala no banco. Devolve o motivo da recusa, ou ``None``.

    Sala inexistente só é aceita quando a autenticação está desligada — nesse
    caso a demo roda sem pré-cadastro. Com ``require_auth`` ligado, o código da
    sala precisa existir de verdade (o link do paciente vira credencial).
    """
    from app.models.telemedicina import SalaVirtual as SalaVirtualModel, StatusTeleconsulta

    db = SessionLocal()
    try:
        sala = (
            db.query(SalaVirtualModel)
            .filter(SalaVirtualModel.codigo_sala == codigo_sala)
            .first()
        )
        if not sala:
            return None if not settings.require_auth else "Sala não encontrada."

        if sala.status in (StatusTeleconsulta.CONCLUIDA, StatusTeleconsulta.CANCELADA):
            return f"Teleconsulta já encerrada ({sala.status.value})."

        if sala.data_expiracao is not None:
            expiracao = sala.data_expiracao
            if expiracao.tzinfo is None:
                expiracao = expiracao.replace(tzinfo=timezone.utc)
            if expiracao < datetime.now(timezone.utc):
                return "Link da teleconsulta expirado."

        return None
    finally:
        db.close()


def _auditar(acao: str, sala: str, usuario_id: Optional[int], detalhes: Dict[str, Any]) -> None:
    """Registra entrada/saída da teleconsulta na trilha encadeada."""
    try:
        from app.services.audit_service import AuditService

        db = SessionLocal()
        try:
            AuditService.registrar_evento(
                db=db,
                acao=acao,
                recurso_tipo="SalaVirtual",
                recurso_id=sala,
                usuario_id=usuario_id,
                detalhes=detalhes,
            )
        finally:
            db.close()
    except Exception:
        # Auditoria não pode derrubar a chamada em andamento.
        pass


def _envelope(tipo: str, papel: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return EnvelopeSaida(tipo=tipo, de_papel=papel, payload=payload).model_dump(mode="json")


# =========================================================================
# Endpoint de sinalização
# =========================================================================
@router.websocket("/ws/telemedicina/sala/{codigo_sala}")
async def telemedicina_sala_ws(
    websocket: WebSocket,
    codigo_sala: str,
    papel: str = Query("medico"),
    token: Optional[str] = Query(None),
) -> None:
    """Sinalização da teleconsulta: presença, SDP e candidatos ICE.

    O primeiro paciente/médico a entrar aguarda; o segundo cria a oferta. A
    partir daí as mensagens de sinalização vão apenas para o outro lado.
    """
    await websocket.accept()

    try:
        usuario_id, papel_autenticado, nome = _autenticar(websocket, token)
    except PermissionError as erro:
        await websocket.send_json(
            _envelope(TipoMensagemWS.ERRO.value, "servidor", {"motivo": str(erro)})
        )
        await websocket.close(code=4401, reason="nao autorizado")
        return
    except Exception:
        await websocket.send_json(
            _envelope(TipoMensagemWS.ERRO.value, "servidor", {"motivo": "Falha de autenticação."})
        )
        await websocket.close(code=4401, reason="nao autorizado")
        return

    papel_final = papel_autenticado or papel
    if papel_final not in (PapelParticipante.MEDICO.value, PapelParticipante.PACIENTE.value):
        await websocket.send_json(
            _envelope(TipoMensagemWS.ERRO.value, "servidor", {"motivo": "Papel inválido."})
        )
        await websocket.close(code=4400, reason="papel invalido")
        return

    recusa = _validar_sala(codigo_sala)
    if recusa:
        await websocket.send_json(
            _envelope(TipoMensagemWS.ERRO.value, "servidor", {"motivo": recusa})
        )
        await websocket.close(code=4404, reason="sala indisponivel")
        return

    participante = Participante(
        usuario_id=usuario_id,
        nome=nome,
        papel=papel_final,
        websocket=websocket,
        codigo_sala=codigo_sala,
    )

    try:
        anteriores = await hub_signaling.entrar(
            codigo_sala, participante, max_por_sala=settings.WS_SALA_MAX_PARTICIPANTES
        )
    except SalaOcupada:
        await websocket.send_json(
            _envelope(
                TipoMensagemWS.ERRO.value,
                "servidor",
                {"motivo": "Sala cheia: a teleconsulta já tem os dois participantes."},
            )
        )
        await websocket.close(code=4409, reason="sala cheia")
        return
    except ParticipanteJaConectado:
        await websocket.send_json(
            _envelope(
                TipoMensagemWS.ERRO.value,
                "servidor",
                {"motivo": "Você já está conectado a esta sala em outra aba."},
            )
        )
        await websocket.close(code=4408, reason="conexao duplicada")
        return

    _auditar(
        "ENTRAR_TELECONSULTA",
        codigo_sala,
        usuario_id,
        {"papel": papel_final, "participantes": len(anteriores) + 1},
    )

    # `deve_criar_oferta`: o segundo a entrar inicia a negociação. O primeiro
    # apenas espera — é o que evita duas ofertas simultâneas (glare).
    await websocket.send_json(
        _envelope(
            TipoMensagemWS.SALA_INGRESSADA.value,
            papel_final,
            {
                "sala_codigo": codigo_sala,
                "seu_id": participante.identificador,
                "seu_papel": papel_final,
                "participantes": [p.resumo() for p in anteriores],
                "deve_criar_oferta": len(anteriores) == 1,
                "ice_servers": settings.ice_servers,
            },
        )
    )

    if anteriores:
        await hub_signaling.enviar_para_outros(
            codigo_sala,
            participante.identificador,
            _envelope(
                TipoMensagemWS.PEER_JOINED.value,
                papel_final,
                {"participante": participante.resumo()},
            ),
        )

    try:
        while True:
            try:
                bruto = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=settings.WS_TIMEOUT_OCIOSO_SEGUNDOS,
                )
            except asyncio.TimeoutError:
                await websocket.send_json(
                    _envelope(
                        TipoMensagemWS.ERRO.value,
                        "servidor",
                        {"motivo": "Conexão ociosa encerrada. Reabra a teleconsulta."},
                    )
                )
                break

            try:
                dados = json.loads(bruto)
            except (TypeError, ValueError):
                await websocket.send_json(
                    _envelope(
                        TipoMensagemWS.ERRO.value,
                        "servidor",
                        {"motivo": "Mensagem não é JSON válido."},
                    )
                )
                continue

            try:
                envelope = EnvelopeEntrada.model_validate(dados)
            except Exception:
                # Antes, uma mensagem malformada derrubava a conexão inteira no
                # meio da teleconsulta. Agora responde erro e segue.
                await websocket.send_json(
                    _envelope(
                        TipoMensagemWS.ERRO.value,
                        "servidor",
                        {"motivo": "Envelope inválido: esperado {tipo, payload}."},
                    )
                )
                continue

            tipo = envelope.tipo
            payload = envelope.payload or {}

            if tipo in (TipoMensagemWS.PING.value,):
                await websocket.send_json(
                    _envelope(TipoMensagemWS.PONG.value, "servidor", {"ok": True})
                )
                continue

            if tipo in (TipoMensagemWS.LEAVE.value, TipoMensagemWS.LEAVE_SALA.value):
                break

            if tipo in (TipoMensagemWS.JOIN.value, TipoMensagemWS.JOIN_SALA.value):
                atuais = await hub_signaling.participantes(codigo_sala)
                await websocket.send_json(
                    _envelope(
                        TipoMensagemWS.SALA_INGRESSADA.value,
                        papel_final,
                        {
                            "sala_codigo": codigo_sala,
                            "seu_id": participante.identificador,
                            "seu_papel": papel_final,
                            "participantes": [
                                p.resumo()
                                for p in atuais
                                if p.identificador != participante.identificador
                            ],
                            "deve_criar_oferta": False,
                            "ice_servers": settings.ice_servers,
                        },
                    )
                )
                continue

            # -- Mensagens de sinalização e estado clínico -----------------
            if tipo in (
                TipoMensagemWS.OFFER.value,
                TipoMensagemWS.ANSWER.value,
                TipoMensagemWS.ICE_CANDIDATE.value,
            ):
                if tipo != TipoMensagemWS.ICE_CANDIDATE.value and not payload.get("sdp"):
                    await websocket.send_json(
                        _envelope(
                            TipoMensagemWS.ERRO.value,
                            "servidor",
                            {"motivo": f"Mensagem '{tipo}' exige o campo 'sdp'."},
                        )
                    )
                    continue

                entregues = await hub_signaling.enviar_para_outros(
                    codigo_sala,
                    participante.identificador,
                    _envelope(
                        tipo, papel_final, {**payload, "de": participante.identificador}
                    ),
                )
                if entregues == 0:
                    await websocket.send_json(
                        _envelope(
                            TipoMensagemWS.ERRO.value,
                            "servidor",
                            {"motivo": "Não há outro participante conectado ainda."},
                        )
                    )
                continue

            if tipo in (
                TipoMensagemWS.ESTADO_MEDICO.value,
                TipoMensagemWS.ESTADO_PACIENTE.value,
                TipoMensagemWS.CONSENTIMENTO.value,
            ):
                await hub_signaling.enviar_para_outros(
                    codigo_sala,
                    participante.identificador,
                    _envelope(tipo, papel_final, payload),
                )
                if tipo == TipoMensagemWS.CONSENTIMENTO.value:
                    _auditar(
                        "REGISTRAR_CONSENTIMENTO_TELECONSULTA",
                        codigo_sala,
                        usuario_id,
                        {"escopo": payload.get("escopo")},
                    )
                continue

            await websocket.send_json(
                _envelope(
                    TipoMensagemWS.ERRO.value,
                    "servidor",
                    {"motivo": f"Tipo de mensagem desconhecido: '{tipo}'."},
                )
            )

    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close(code=4410, reason="erro interno")
        except Exception:
            pass
    finally:
        await hub_signaling.sair(codigo_sala, participante.identificador)
        _auditar("SAIR_TELECONSULTA", codigo_sala, usuario_id, {"papel": papel_final})
        aviso = _envelope(
            TipoMensagemWS.PEER_LEFT.value,
            papel_final,
            {"participante": participante.resumo()},
        )
        # Best-effort: se a sala já esvaziou, não há a quem avisar.
        try:
            await hub_signaling.enviar_para_outros(
                codigo_sala, participante.identificador, aviso
            )
        except Exception:
            pass

        # Fechamento explícito. Se o handler apenas retorna, o encerramento do
        # WebSocket não é garantido — o cliente (navegador ou TestClient) fica
        # esperando uma mensagem que nunca chega e a chamada "trava" aberta.
        try:
            await websocket.close(code=1000)
        except Exception:
            # Já estava fechado (disconnect do cliente): nada a fazer.
            pass
