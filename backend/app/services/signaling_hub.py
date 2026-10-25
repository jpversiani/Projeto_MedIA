"""Hub de sinalização WebRTC para teleconsulta (T3).

O que existia antes: um dicionário de filas em memória que republicava qualquer
mensagem recebida para **todos** os participantes da sala, inclusive para quem
enviou. Isso não é sinalização WebRTC:

* o ``offer`` voltava para o ofertante, que tentava aplicar a própria oferta;
* ``answer`` e ``ice_candidate`` iam para o peer errado quando havia mais de um;
* não havia aviso de presença (``peer_joined``/``peer_left``), então o médico
  ficava olhando para uma tela preta sem saber se o paciente entrou ou caiu;
* nenhuma mensagem era autenticada: ``papel`` vinha da query string.

Este módulo implementa o roteamento correto: cada mensagem de sinalização vai
**exclusivamente para o outro participante**, com presença explícita e limites
de sala.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class Participante:
    """Uma conexão WebSocket identificada dentro de uma sala."""

    usuario_id: Optional[int]
    nome: str
    papel: str
    websocket: Any
    codigo_sala: str
    conectado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Último instante em que o cliente deu sinal de vida (ping/qualquer msg).
    ultimo_sinal: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def identificador(self) -> str:
        """Chave pública do participante para o outro lado da chamada."""
        return f"u{self.usuario_id}" if self.usuario_id else f"anon-{id(self)}"

    def resumo(self) -> Dict[str, Any]:
        """Dados que podem ser revelados ao outro participante (sem PII extra)."""
        return {
            "id": self.identificador,
            "nome": self.nome,
            "papel": self.papel,
            "conectado_em": self.conectado_em.isoformat(),
        }


class SalaOcupada(Exception):
    """A sala já atingiu o limite de participantes."""


class ParticipanteJaConectado(Exception):
    """O mesmo usuário tentou abrir uma segunda conexão na mesma sala."""


class SignalingHub:
    """Roteador de mensagens de sinalização por sala.

    Vive no processo do servidor, portanto é válido para **uma instância**. Com
    múltiplos workers/instâncias é necessário um backplane (Redis pub/sub); isso
    está registrado como pendência em ``docs/STATUS_ATUAL_CONSOLIDADO.md``.
    """

    def __init__(self, max_por_sala: int = 2):
        self._salas: Dict[str, Dict[str, Participante]] = {}
        self._lock = asyncio.Lock()
        self.max_por_sala = max_por_sala
        self.eventos_roteados = 0

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    async def entrar(
        self,
        codigo_sala: str,
        participante: Participante,
        max_por_sala: Optional[int] = None,
    ) -> List[Participante]:
        """Registra o participante e devolve quem já estava na sala.

        A lista de retorno é usada para (a) montar o ``sala_ingressada`` e
        (b) decidir quem cria a oferta — o **segundo** a entrar oferece.
        """
        limite = max_por_sala if max_por_sala is not None else self.max_por_sala
        async with self._lock:
            sala = self._salas.setdefault(codigo_sala, {})

            if participante.identificador in sala:
                raise ParticipanteJaConectado(participante.identificador)
            if limite and len(sala) >= limite:
                raise SalaOcupada(codigo_sala)

            anteriores = list(sala.values())
            sala[participante.identificador] = participante
            return anteriores

    async def sair(self, codigo_sala: str, identificador: str) -> Optional[Participante]:
        """Remove o participante e devolve o registro removido (ou ``None``)."""
        async with self._lock:
            sala = self._salas.get(codigo_sala)
            if not sala:
                return None
            removido = sala.pop(identificador, None)
            if not sala:
                self._salas.pop(codigo_sala, None)
            return removido

    async def participantes(self, codigo_sala: str) -> List[Participante]:
        async with self._lock:
            return list(self._salas.get(codigo_sala, {}).values())

    async def outros(self, codigo_sala: str, identificador: str) -> List[Participante]:
        """Todos os participantes da sala, exceto o informado."""
        return [
            p
            for p in await self.participantes(codigo_sala)
            if p.identificador != identificador
        ]

    # ------------------------------------------------------------------
    # Envio
    # ------------------------------------------------------------------
    async def enviar(self, participante: Participante, mensagem: Dict[str, Any]) -> bool:
        """Envia uma mensagem para um participante. ``False`` se a conexão caiu."""
        try:
            await participante.websocket.send_json(mensagem)
            return True
        except Exception:
            # Conexão morta: o laço principal detecta e limpa a sala.
            return False

    async def enviar_para_outros(
        self,
        codigo_sala: str,
        identificador: str,
        mensagem: Dict[str, Any],
    ) -> int:
        """Roteia para todos, menos o remetente.

        O ``except``-do-remetente é o ponto central: sem ele o ``offer`` volta
        para quem o criou e a negociação nunca fecha.
        """
        entregues = 0
        for destino in await self.outros(codigo_sala, identificador):
            if await self.enviar(destino, mensagem):
                entregues += 1
        self.eventos_roteados += 1
        return entregues

    async def enviar_para(
        self,
        codigo_sala: str,
        identificador_destino: str,
        mensagem: Dict[str, Any],
    ) -> bool:
        """Entrega direcionada a um participante específico."""
        for destino in await self.participantes(codigo_sala):
            if destino.identificador == identificador_destino:
                ok = await self.enviar(destino, mensagem)
                if ok:
                    self.eventos_roteados += 1
                return ok
        return False

    # ------------------------------------------------------------------
    # Observabilidade
    # ------------------------------------------------------------------
    async def estatisticas(self, codigo_sala: str) -> Dict[str, Any]:
        participantes = await self.participantes(codigo_sala)
        return {
            "sala_codigo": codigo_sala,
            "participantes": len(participantes),
            "papeis": sorted({p.papel for p in participantes}),
            "nomes": [p.nome for p in participantes],
            "eventos_roteados": self.eventos_roteados,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def salas_abertas(self) -> Iterable[str]:
        async with self._lock:
            return list(self._salas.keys())

    async def encerrar_sala(self, codigo_sala: str) -> int:
        """Remove a sala inteira (chamado quando a teleconsulta é encerrada)."""
        async with self._lock:
            sala = self._salas.pop(codigo_sala, None)
            return len(sala) if sala else 0


# Instância única usada pela rota WebSocket.
hub_signaling = SignalingHub()
