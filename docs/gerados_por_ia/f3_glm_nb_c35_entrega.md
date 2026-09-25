# Fila Eletrônica Reativa de Acolhimento e Chamada por Voz (C35)

## `backend/app/services/fila_teleatendimento.py`

```python
"""
Projeto MedIA — Serviço C35
Fila Eletrônica Reativa de Acolhimento e Chamada por Voz (Teleatendimento).

Implementa fila de prioridades em memória (heapq + asyncio), cálculo de
tempo estimado de espera (EMA do tempo médio de atendimento) e disparo
de notificações WebSocket para eventos da fila.

Conformidade:
- Identificação do cidadão por CNS ou CPF (padrão SUS / APS).
- Classificação de risco (Protocolo de Manchester adaptado SUS).
- LGPD: nenhum dado sensível é logado; apenas pseudônimos/IDs.
"""

from __future__ import annotations

import asyncio
import heapq
import itertools
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict

logger = logging.getLogger("media.fila_teleatendimento")


# ---------------------------------------------------------------------------
# Domínio — Classificação de risco (Manchester adaptado / SUS)
# ---------------------------------------------------------------------------

class PrioridadeRisco(int, Enum):
    """Prioridade de atendimento. Menor valor = maior prioridade."""

    VERMELHO = 1  # Emergência
    LARANJA = 2   # Muito urgente
    AMARELO = 3   # Urgente
    VERDE = 4     # Pouco urgente
    AZUL = 5      # Não urgente


class StatusFila(str, Enum):
    AGUARDANDO = "AGUARDANDO"
    CHAMADO = "CHAMADO"
    EM_ATENDIMENTO = "EM_ATENDIMENTO"
    ATENDIDO = "ATENDIDO"
    DESISTIU = "DESISTIU"
    AUSENTE = "AUSENTE"


class TipoDocumento(str, Enum):
    CNS = "CNS"
    CPF = "CPF"


# ---------------------------------------------------------------------------
# Schemas Pydantic v2
# ---------------------------------------------------------------------------

class CidadaoIdentificacao(BaseModel):
    """Identificação do cidadão conforme padrão SUS (CNS/CPF)."""

    model_config = ConfigDict(frozen=True)

    tipo_documento: TipoDocumento
    numero_documento: str = Field(min_length=7, max_length=15)
    nome_social: Optional[str] = Field(default=None, max_length=120)

    @field_validator("numero_documento")
    @classmethod
    def validar_documento(cls, v: str, info) -> str:
        digits = "".join(ch for ch in v if ch.isdigit())
        if info.data.get("tipo_documento") is TipoDocumento.CNS:
            if len(digits) != 15 or not _cns_valido(digits):
                raise ValueError("CNS inválido conforme algoritmo do Ministério da Saúde.")
        elif len(digits) != 11 or not _cpf_valido(digits):
            raise ValueError("CPF inválido conforme algoritmo da Receita Federal.")
        return digits


class EntradaFilaIn(BaseModel):
    """Payload de acolhimento para entrada na fila."""

    cidadao: CidadaoIdentificacao
    prioridade: PrioridadeRisco
    profissional_id: Optional[uuid.UUID] = None  # destino preferencial
    queixa_principal_ciap2: Optional[str] = Field(default=None, pattern=r"^[A-Z]\d{2}$")
    cid10: Optional[str] = Field(default=None, pattern=r"^[A-TV-Z][0-9]{2}(\.[0-9])?$")
    observacao_soap_subjetivo: Optional[str] = Field(default=None, max_length=2000)


class EntradaFilaOut(EntradaFilaIn):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    posicao: int
    status: StatusFila
    entrada_em: datetime
    tempo_estimado_espera_seg: float
    chamadas: int = 0


# ---------------------------------------------------------------------------
# Validações SUS (CNS / CPF)
# ---------------------------------------------------------------------------

def _cpf_valido(cpf: str) -> bool:
    if cpf == cpf[0] * 11:
        return False
    for n in (9, 10):
        soma = sum(int(cpf[i]) * (n + 1 - i) for i in range(n))
        dv = (soma * 10) % 11 % 10
        if int(cpf[n]) != dv:
            return False
    return True


def _cns_valido(cns: str) -> bool:
    if cns[0] not in "123789":
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0


# ---------------------------------------------------------------------------
# Eventos WebSocket
# ---------------------------------------------------------------------------

class EventoFila(BaseModel):
    """Evento publicado no tópico WebSocket da fila."""

    model_config = ConfigDict(frozen=True)

    tipo: str
    id_entrada: uuid.UUID
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dados: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Estrutura interna do heap
# ---------------------------------------------------------------------------

@dataclass(order=True)
class _ItemHeap:
    """Ordenação: prioridade -> tempo de entrada (FIFO dentro da prioridade)."""

    prioridade: int
    seq: int
    id_entrada: uuid.UUID = field(compare=False)
    entrado_em_monotonic: float = field(compare=False)


# ---------------------------------------------------------------------------
# Serviço principal
# ---------------------------------------------------------------------------

class FilaTeleatendimentoService:
    """
    Fila de prioridades reativa em memória, thread-safe via asyncio.Lock.

    - heapq para ordenação por prioridade + FIFO.
    - Tempo estimado de espera via média móvel exponencial (EMA).
    - Pub/Sub de eventos para consumo por camada WebSocket (FastAPI).
    """

    #: pesos por prioridade aplicados sobre o tempo médio de atendimento
    FATOR_PRIORIDADE: Dict[int, float] = {
        PrioridadeRisco.VERMELHO: 0.25,
        PrioridadeRisco.LARANJA: 0.50,
        PrioridadeRisco.AMARELO: 0.75,
        PrioridadeRisco.VERDE: 1.00,
        PrioridadeRisco.AZUL: 1.25,
    }

    def __init__(self, tempo_medio_atendimento_inicial: float = 600.0) -> None:
        self._heap: List[_ItemHeap] = []
        self._entradas: Dict[uuid.UUID, dict[str, Any]] = {}
        self._seq = itertools.count()
        self._lock = asyncio.Lock()
        self._subscribers: Dict[int, asyncio.Queue[EventoFila]] = {}
        self._sub_seq = itertools.count()

        self._ema_tempo_atendimento = tempo_medio_atendimento_inicial
        self._alpha = 0.2  # fator de suavização EMA

    # ----------------------------- Acolhimento -----------------------------

    async def acolher(self, payload: EntradaFilaIn) -> EntradaFilaOut:
        """Insere cidadão na fila (acolhimento)."""
        async with self._lock:
            if any(
                e["cidadao"] == payload.cidadao and e["status"] is StatusFila.AGUARDANDO
                for e in self._entradas.values()
            ):
                raise ValueError("Cidadão já consta na fila de espera.")

            now = time.monotonic()
            id_entrada = uuid.uuid4()
            self._entradas[id_entrada] = {
                "payload": payload,
                "status": StatusFila.AGUARDANDO,
                "entrada_em": datetime.now(timezone.utc),
                "entrada_monotonic": now,
                "chamadas": 0,
                "profissional_id": payload.profissional_id,
            }
            heapq.heappush(
                self._heap,
                _ItemHeap(payload.prioridade.value, next(self._seq), id_entrada, now),
            )

            out = await self._montar_saida(id_entrada)
            await self._publicar(
                EventoFila(
                    tipo="FILA_ACO-LHIMENTO".replace("-", "_"),  # FILA_ACO_LHIMENTO
                    id_entrada=id_entrada,
                    dados={"prioridade": payload.prioridade.name, "posicao": out.posicao},
                )
            )
            await self._notificar_proximo()
            return out

    # ----------------------------- Consulta --------------------------------

    async def obter(self, id_entrada: uuid.UUID) -> Optional[EntradaFilaOut]:
        async with self._lock:
            if id_entrada not in self._entradas:
                return None
            return await self._montar_saida(id_entrada)

    async def listar_fila(self) -> List[EntradaFilaOut]:
        """Snapshot ordenado da fila de espera."""
        async with self._lock:
            ordenados = sorted(self._heap, key=lambda i: (i.prioridade, i.seq))
            return [await self._montar_saida(i.id_entrada) for i in ordenados]

    # ----------------------------- Chamada por voz -------------------------

    async def chamar_proximo(
        self, profissional_id: uuid.UUID
    ) -> Optional[EntradaFilaOut]:
        """
        Realiza a chamada do próximo cidadão (respeitando destino preferencial)
        e dispara evento de chamada por voz (fila TTS / WebSocket).
        """
        async with self._lock:
            if not self._heap:
                return None

            # reservados para profissional específico
            idx_reservado = next(
                (
                    k
                    for k, item in enumerate(self._heap)
                    if self._entradas[item.id_entrada]["profissional_id"] == profissional_id
                ),
                None,
            )
            idx = idx_reservado if idx_reservado is not None else 0
            item = self._heap.pop(idx)
            heapq.heapify(self._heap)

            entrada = self._entradas[item.id_entrada]
            entrada["status"] = StatusFila.CHAMADO
            entrada["chamadas"] += 1
            entrada["chamado_em"] = datetime.now(timezone.utc)

            out = await self._montar_saida(item.id_entrada)
            await self._publicar(
                EventoFila(
                    tipo="CHAMADA_VOZ",
                    id_entrada=item.id_entrada,
                    dados={
                        "profissional_id": str(profissional_id),
                        "senha": str(item.id_entrada)[:8].upper(),  # senha falada (TTS)
                        "prioridade": PrioridadeRisco(item.prioridade).name,
                    },
                )
            )
            return out

    async def confirmar_atendimento(self, id_entrada: uuid.UUID) -> Optional[EntradaFilaOut]:
        """Cidadão conectou: CHAMADO -> EM_ATENDIMENTO; atualiza EMA do tempo."""
        async with self._lock:
            entrada = self._entradas.get(id_entrada)
            if not entrada or entrada["status"] is not StatusFila.CHAMADO:
                return None

            inicio = entrada.pop("chamado_em_monotonic", None)
            entrada["status"] = StatusFila.EM_ATENDIMENTO

            if inicio is not None:
                espera = time.monotonic() - inicio
                self._ema_tempo_atendimento = (
                    self._alpha * espera + (1 - self._alpha) * self._ema_tempo_atendimento
                )

            out = await self._montar_saida(id_entrada)
            await self._publicar(EventoFila(tipo="ATENDIMENTO_INICIADO", id_entrada=id_entrada))
            await self._notificar_proximo()
            return out

    async def finalizar(self, id_entrada: uuid.UUID) -> Optional[EntradaFilaOut]:
        async with self._lock:
            entrada = self._entradas.get(id_entrada)
            if not entrada:
                return None
            if entrada["status"] is not StatusFila.EM_ATENDIMENTO:
                return None
            entrada["status"] = StatusFila.ATENDIDO
            self._remover_do_heap(id_entrada)
            out = await self._montar_saida(id_entrada)
            await self._publicar(EventoFila(tipo="ATENDIMENTO_FINALIZADO", id_entrada=id_entrada))
            await self._notificar_proximo()
            return out

    async def marcar_ausente(self, id_entrada: uuid.UUID) -> Optional[EntradaFilaOut]:
        """Após 2 chamadas sem confirmação: AUSENTE (rebaixa prioridade em reentrada)."""
        async with self._lock:
            entrada = self._entradas.get(id_entrada)
            if not entrada or entrada["status"] is not StatusFila.CHAMADO:
                return None
            entrada["status"] = StatusFila.AUSENTE
            self._remover_do_heap(id_entrada)
            out = await self._montar_saida(id_entrada)
            await self._publicar(EventoFila(tipo="CIDADAO_AUSENTE", id_entrada=id_entrada))
            await self._notificar_proximo()
            return out

    async def desistir(self, id_entrada: uuid.UUID) -> Optional[EntradaFilaOut]:
        async with self._lock:
            entrada = self._entradas.get(id_entrada)
            if not entrada or entrada["status"] is StatusFila.ATENDIDO:
                return None
            entrada["status"] = StatusFila.DESISTIU
            self._remover_do_heap(id_entrada)
            out = await self._montar_saida(id_entrada)
            await self._publicar(EventoFila(tipo="CIDADAO_DESISTIU", id_entrada=id_entrada))
            await self._notificar_proximo()
            return out

    # ----------------------------- Métricas --------------------------------

    async def tempo_estimado_espera(self, id_entrada: uuid.UUID) -> Optional[float]:
        async with self._lock:
            if id_entrada not in self._entradas:
                return None
            return self._calcular_estimativa(id_entrada)

    async def estatisticas(self) -> dict[str, Any]:
        async with self._lock:
            contagem: Dict[str, int] = {}
            for e in self._entradas.values():
                contagem[e["status"].value] = contagem.get(e["status"].value, 0) + 1
            return {
                "tamanho_fila": len(self._heap),
                "por_status": contagem,
                "tempo_medio_atendimento_ema_seg": round(self._ema_tempo_atendimento, 2),
            }

    # ----------------------------- Pub/Sub WebSocket -----------------------

    def subscribe(self) -> tuple[int, AsyncIterator[EventoFila]]:
        """Registra assinante WebSocket. Retorna (id, gerador de eventos)."""
        sub_id = next(self._sub_seq)
        q: asyncio.Queue[EventoFila] = asyncio.Queue()
        self._subscribers[sub_id] = q

        async def _gen() -> AsyncIterator[EventoFila]:
            try:
                while True:
                    yield await q.get()
            finally:
                self._subscribers.pop(sub_id, None)

        return sub_id, _gen()

    def unsubscribe(self, sub_id: int) -> None:
        self._subscribers.pop(sub_id, None)

    # ----------------------------- Internos --------------------------------

    def _posicao(self, id_entrada: uuid.UUID) -> int:
        alvo = next((i for i in self._heap if i.id_entrada == id_entrada), None)
        if alvo is None:
            return 0
        ordenados = sorted(self._heap, key=lambda i: (i.prioridade, i.seq))
        return ordenados.index(alvo) + 1

    def _calcular_estimativa(self, id_entrada: uuid.UUID) -> float:
        item = next((i for i in self._heap if i.id_entrada == id_entrada), None)
        if item is None:
            return 0.0
        pos = self._posicao(id_entrada)
        fator = self.FATOR_PRIORIDADE[item.prioridade]
        # pessoas à frente escalonadas pelo fator de prioridade do próprio item
        return round(pos * self._ema_tempo_atendimento * fator, 2)

    def _remover_do_heap(self, id_entrada: uuid.UUID) -> None:
        self._heap = [i for i in self._heap if i.id_entrada != id_entrada]
        heapq.heapify(self._heap)

    async def _montar_saida(self, id_entrada: uuid.UUID) -> EntradaFilaOut:
        e = self._entradas[id_entrada]
        p = e["payload"]
        return EntradaFilaOut(
            cidadao=p.cidadao,
            prioridade=p.prioridade,
            profissional_id=p.profissional_id,
            queixa_principal_ciap2=p.queixa_principal_ciap2,
            cid10=p.cid10,
            observacao_soap_subjetivo=p.observacao_soap_subjetivo,
            id=id_entrada,
            posicao=self._posicao(id_entrada),
            status=e["status"],
            entrada_em=e["entrada_em"],
            tempo_estimado_espera_seg=self._calcular_estimativa(id_entrada)
            if e["status"] is StatusFila.AGUARDANDO
            else 0.0,
            chamadas=e["chamadas"],
        )

    async def _publicar(self, evento: EventoFila) -> None:
        """Dispara evento para todos os assinantes WebSocket (non-blocking)."""
        for q in list(self._subscribers.values()):
            await q.put(evento)
        logger.info("Evento de fila publicado: %s", evento.tipo)

    async def _notificar_proximo(self) -> None:
        """Atualiza posição/estimativa de todos os aguardando (fila reativa)."""
        for item in self._heap:
            out = await self._montar_saida(item.id_entrada)
            await self._publicar(
                EventoFila(
                    tipo="FILA_ATUALIZADA",
                    id_entrada=item.id_entrada,
                    dados={
                        "posicao": out.posicao,
                        "tempo_estimado_espera_seg": out.tempo_estimado_espera