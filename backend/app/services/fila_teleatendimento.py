"""Fila Eletrônica Reativa de Acolhimento e Chamada por Voz (C3).

Implementa fila de prioridades em memória (heapq/asyncio), cálculo de tempo
estimado de espera e disparo de notificações WebSocket, conforme padrões
SUS/APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF).

Conformidade:
- Python 3.12, tipagem estrita com Pydantic v2
- Padrões SUS/APS: CIAP-2, CID-10, método SOAP, CNS/CPF
- Código limpo, sem dependência de framework (chamado de routers/services)
"""

from __future__ import annotations

import asyncio
import heapq
import itertools
import logging
import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum, IntEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field

from app.services.validadores import (
    CNSInvalidoError,
    CPFInvalidoError,
    CodigoClinicoInvalidoError,
    normalizar_cns,
    normalizar_cpf,
    normalizar_ciap2,
    normalizar_cid10,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ClassificacaoRisco(StrEnum):
    VERMELHO = "VERMELHO"
    LARANJA = "LARANJA"
    AMARELO = "AMARELO"
    VERDE = "VERDE"
    AZUL = "AZUL"


class Prioridade(IntEnum):
    VERMELHO = 1
    LARANJA = 2
    AMARELO = 3
    VERDE = 4
    AZUL = 5


class StatusFila(StrEnum):
    AGUARDANDO = "AGUARDANDO_ATENDIMENTO"
    CHAMADO = "CHAMADO"
    EM_ATENDIMENTO = "EM_ATENDIMENTO"
    FINALIZADO = "FINALIZADO"
    EVASAO = "EVASAO"


class TipoDemanda(StrEnum):
    ESPONTANEA = "ESPONTANEA"
    AGENDADA = "AGENDADA"
    URGENCIA = "URGENCIA"


class TipoEventoFila(StrEnum):
    PACIENTE_ENTRADA = "paciente_entrada"
    PACIENTE_CHAMADO = "paciente_chamado"
    PACIENTE_ATENDIMENTO = "paciente_atendimento"
    PACIENTE_FINALIZADO = "paciente_finalizado"
    PACIENTE_EVASAO = "paciente_evasao"
    FILA_ATUALIZADA = "fila_atualizada"
    ERRO = "erro"


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

TEMPO_ALVO_MINUTOS: dict[ClassificacaoRisco, int] = {
    ClassificacaoRisco.VERMELHO: 0,
    ClassificacaoRisco.LARANJA: 10,
    ClassificacaoRisco.AMARELO: 60,
    ClassificacaoRisco.VERDE: 120,
    ClassificacaoRisco.AZUL: 240,
}

_PRIORIDADE_RISCO: Final[dict[int, ClassificacaoRisco]] = {
    int(Prioridade.VERMELHO): ClassificacaoRisco.VERMELHO,
    int(Prioridade.LARANJA): ClassificacaoRisco.LARANJA,
    int(Prioridade.AMARELO): ClassificacaoRisco.AMARELO,
    int(Prioridade.VERDE): ClassificacaoRisco.VERDE,
    int(Prioridade.AZUL): ClassificacaoRisco.AZUL,
}

TEMPO_MEDIO_CONSULTA_MINUTOS: Final[int] = 15

_PESOS_CNS = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
_PESOS_CNS_11 = list(range(15, 0, -1))


# ---------------------------------------------------------------------------
# Modelos Pydantic v2
# ---------------------------------------------------------------------------


class PacienteFilaIn(BaseModel):
    """Entrada de paciente na fila de acolhimento."""

    model_config = ConfigDict(extra="forbid")

    paciente_id: uuid.UUID
    nome_social: str = Field(..., min_length=1, max_length=255)
    documento_tipo: Literal["CNS", "CPF"]
    documento: str = Field(..., min_length=1, max_length=20, description="CNS ou CPF")
    classificacao_risco: ClassificacaoRisco
    queixa_ciap2: str | None = Field(None, max_length=10, description="Código CIAP-2")
    cid10_suspeita: str | None = Field(None, max_length=10, description="Código CID-10")
    unidade_id: uuid.UUID
    profissional_id: uuid.UUID | None = None
    consultorio: str | None = Field(None, max_length=100)
    tipo_demanda: TipoDemanda = TipoDemanda.ESPONTANEA
    sinais_vitais: dict[str, Any] | None = None

    @field_validator("documento")
    @classmethod
    def _validar_documento(cls, v: str, info) -> str:
        tipo = info.data.get("documento_tipo")
        if tipo == "CNS":
            return normalizar_cns(v)
        if tipo == "CPF":
            return normalizar_cpf(v)
        raise ValueError("documento_tipo deve ser 'CNS' ou 'CPF'")

    @field_validator("queixa_ciap2")
    @classmethod
    def _validar_ciap2(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return normalizar_ciap2(v)

    @field_validator("cid10_suspeita")
    @classmethod
    def _validar_cid10(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return normalizar_cid10(v)


class PacienteFilaOut(BaseModel):
    """Saída de paciente na fila."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: uuid.UUID
    paciente_id: uuid.UUID
    nome_social: str
    documento: str
    documento_tipo: Literal["CNS", "CPF"]
    classificacao_risco: ClassificacaoRisco
    prioridade: Prioridade
    queixa_ciap2: str | None
    cid10_suspeita: str | None
    unidade_id: uuid.UUID
    profissional_id: uuid.UUID | None
    consultorio: str | None
    tipo_demanda: TipoDemanda
    status: StatusFila
    entrado_em: datetime
    chamado_em: datetime | None
    atendido_em: datetime | None
    tempo_espera_estimado_min: int
    sinais_vitais: dict[str, Any] | None

    @computed_field  # type: ignore[misc]
    @property
    def tempo_espera_real_min(self) -> float | None:
        if self.chamado_em is None:
            return None
        delta = self.chamado_em - self.entrado_em
        return round(delta.total_seconds() / 60, 1)


class FilaSnapshot(BaseModel):
    """Snapshot completo do estado da fila."""

    model_config = ConfigDict(frozen=True)

    total_aguardando: int
    total_chamado: int
    total_em_atendimento: int
    total_finalizado: int
    total_evasao: int
    proximos: list[PacienteFilaOut]
    risco_prioritario: ClassificacaoRisco | None
    tempo_medio_espera_min: float
    timestamp: datetime


class NotificacaoFila(BaseModel):
    """Payload de notificação WebSocket."""

    model_config = ConfigDict(frozen=True)

    tipo: TipoEventoFila
    paciente: PacienteFilaOut | None = None
    fila_snapshot: FilaSnapshot | None = None
    mensagem: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    erro: str | None = None


# ---------------------------------------------------------------------------
# Modelos internos do serviço
# ---------------------------------------------------------------------------


@dataclass(order=True, slots=True)
class _ItemHeap:
    """Item interno do heap: (prioridade, contador_fifo, id)."""

    prioridade: int
    fifo: int
    id: uuid.UUID = field(compare=False)
    status: StatusFila = field(default=StatusFila.AGUARDANDO, compare=False)


@dataclass
class _EntradaInterna:
    """Entrada completa em memória."""

    item_heap: _ItemHeap
    dados: PacienteFilaIn
    entrado_em: datetime
    chamado_em: datetime | None = None
    atendido_em: datetime | None = None


# ---------------------------------------------------------------------------
# Hub WebSocket para Fila
# ---------------------------------------------------------------------------


@dataclass
class _ConexaoFila:
    fila: asyncio.Queue[NotificacaoFila]
    loop: asyncio.AbstractEventLoop


class HubFilaWS:
    """Hub em memória de conexões WebSocket da Fila de Acolhimento.

    Gerencia as conexões por unidade e dispara notificações de entrada,
    chamada, início/fim de atendimento e evasão.
    """

    def __init__(self) -> None:
        self._conexoes: dict[str, list[_ConexaoFila]] = defaultdict(list)
        self._stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"conexoes": 0, "eventos": 0}
        )

    def conectar(self, unidade_id: str) -> tuple[asyncio.Queue[NotificacaoFila], asyncio.Lock]:
        fila: asyncio.Queue[NotificacaoFila] = asyncio.Queue(maxsize=200)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        self._conexoes[unidade_id].append(_ConexaoFila(fila=fila, loop=loop))
        self._stats[unidade_id]["conexoes"] = len(self._conexoes[unidade_id])
        return fila, asyncio.Lock()

    def desconectar(self, unidade_id: str, fila: asyncio.Queue[NotificacaoFila]) -> None:
        conexoes = self._conexoes.get(unidade_id, [])
        for i, c in enumerate(conexoes):
            if c.fila is fila:
                conexoes.pop(i)
                break
        if not conexoes:
            self._conexoes.pop(unidade_id, None)
        self._stats[unidade_id]["conexoes"] = len(self._conexoes.get(unidade_id, []))

    def publicar(self, unidade_id: str, notificacao: NotificacaoFila) -> int:
        conexoes = list(self._conexoes.get(unidade_id, []))
        entregues = 0
        for conn in conexoes:
            try:
                conn.loop.call_soon_threadsafe(conn.fila.put_nowait, notificacao)
                entregues += 1
            except asyncio.QueueFull:
                logger.warning("Fila de notificação cheia para unidade %s", unidade_id)
            except RuntimeError:
                continue
        self._stats[unidade_id]["eventos"] += 1
        return entregues

    def obter_stats(self, unidade_id: str) -> dict[str, Any]:
        return {
            "unidade_id": unidade_id,
            "conexoes": self._stats[unidade_id]["conexoes"],
            "eventos": self._stats[unidade_id]["eventos"],
            "timestamp": datetime.now(timezone.utc),
        }


# Instância global do hub
_hub_fila_ws = HubFilaWS()


# ---------------------------------------------------------------------------
# Serviço principal
# ---------------------------------------------------------------------------


class FilaAcolhimentoService:
    """Serviço de Fila Eletrônica de Acolhimento com prioridades.

    Thread-safe via asyncio.Lock. Utiliza heapq para ordenação por prioridade
    e FIFO interno. Calcula tempo estimado de espera e dispara notificações
    WebSocket para unidades conectadas.
    """

    def __init__(self, unidade_id: str) -> None:
        self._unidade_id = unidade_id
        self._lock = asyncio.Lock()
        self._heap: list[_ItemHeap] = []
        self._entradas: dict[uuid.UUID, _EntradaInterna] = {}
        self._counter = itertools.count()
        self._hub = _hub_fila_ws

    # ------------------------------------------------------------------
    # Operações principais
    # ------------------------------------------------------------------

    async def entrar_na_fila(self, paciente: PacienteFilaIn) -> PacienteFilaOut:
        """Adiciona paciente à fila com prioridade baseada na classificação de risco."""
        async with self._lock:
            paciente_id = uuid.uuid4()
            agora = datetime.now(timezone.utc)
            prioridade = Prioridade[paciente.classificacao_risco]
            fifo = next(self._counter)
            item = _ItemHeap(
                prioridade=int(prioridade),
                fifo=fifo,
                id=paciente_id,
                status=StatusFila.AGUARDANDO,
            )
            entrada = _EntradaInterna(
                item_heap=item,
                dados=paciente,
                entrado_em=agora,
            )
            self._entradas[paciente_id] = entrada
            heapq.heappush(self._heap, item)

            saida = self._montar_saida(entrada)

        notif = NotificacaoFila(
            tipo=TipoEventoFila.PACIENTE_ENTRADA,
            paciente=saida,
            fila_snapshot=await self.get_snapshot(),
            mensagem=f"Paciente {paciente.nome_social} entraram na fila — risco {paciente.classificacao_risco}",
        )
        self._hub.publicar(self._unidade_id, notif)
        logger.info(
            "Paciente %s (%s) entrou na fila da unidade %s — risco=%s prioridade=%d",
            paciente.nome_social,
            paciente_id,
            self._unidade_id,
            paciente.classificacao_risco,
            prioridade,
        )
        return saida

    async def proximo_da_fila(self) -> PacienteFilaOut | None:
        """Retorna o próximo paciente sem alterar status (peek)."""
        async with self._lock:
            for item in self._heap:
                if item.status == StatusFila.AGUARDANDO:
                    entrada = self._entradas.get(item.id)
                    if entrada:
                        return self._montar_saida(entrada)
            return None

    async def chamar_proximo(self) -> PacienteFilaOut | None:
        """Chama o próximo paciente (status AGUARDANDO -> CHAMADO)."""
        async with self._lock:
            agora = datetime.now(timezone.utc)
            for item in self._heap:
                if item.status == StatusFila.AGUARDANDO:
                    entrada = self._entradas[item.id]
                    entrada.chamado_em = agora
                    item.status = StatusFila.CHAMADO
                    saida = self._montar_saida(entrada)
                    break
            else:
                return None

        notif = NotificacaoFila(
            tipo=TipoEventoFila.PACIENTE_CHAMADO,
            paciente=saida,
            fila_snapshot=await self.get_snapshot(),
            mensagem=f"Paciente {saida.nome_social} foi chamado — risco {saida.classificacao_risco}",
        )
        self._hub.publicar(self._unidade_id, notif)
        logger.info("Paciente %s chamado na unidade %s", saida.nome_social, self._unidade_id)
        return saida

    async def iniciar_atendimento(self, paciente_id: uuid.UUID) -> PacienteFilaOut:
        """Inicia atendimento (status CHAMADO -> EM_ATENDIMENTO)."""
        async with self._lock:
            entrada = self._entradas.get(paciente_id)
            if not entrada:
                raise KeyError(f"Paciente {paciente_id} não encontrado na fila")
            if entrada.item_heap.status != StatusFila.CHAMADO:
                raise ValueError(
                    f"Paciente está em status {entrada.item_heap.status}, "
                    f"esperado CHAMADO"
                )
            entrada.atendido_em = datetime.now(timezone.utc)
            entrada.item_heap.status = StatusFila.EM_ATENDIMENTO
            saida = self._montar_saida(entrada)

        notif = NotificacaoFila(
            tipo=TipoEventoFila.PACIENTE_ATENDIMENTO,
            paciente=saida,
            fila_snapshot=await self.get_snapshot(),
            mensagem=f"Atendimento iniciado para {saida.nome_social}",
        )
        self._hub.publicar(self._unidade_id, notif)
        return saida

    async def finalizar_atendimento(self, paciente_id: uuid.UUID) -> PacienteFilaOut:
        """Finaliza atendimento (status -> FINALIZADO)."""
        async with self._lock:
            entrada = self._entradas.get(paciente_id)
            if not entrada:
                raise KeyError(f"Paciente {paciente_id} não encontrado na fila")
            entrada.item_heap.status = StatusFila.FINALIZADO
            saida = self._montar_saida(entrada)

        notif = NotificacaoFila(
            tipo=TipoEventoFila.PACIENTE_FINALIZADO,
            paciente=saida,
            fila_snapshot=await self.get_snapshot(),
            mensagem=f"Atendimento finalizado para {saida.nome_social}",
        )
        self._hub.publicar(self._unidade_id, notif)
        return saida

    async def cancelar(self, paciente_id: uuid.UUID) -> PacienteFilaOut:
        """Cancela/evasão (status -> EVASAO)."""
        async with self._lock:
            entrada = self._entradas.get(paciente_id)
            if not entrada:
                raise KeyError(f"Paciente {paciente_id} não encontrado na fila")
            entrada.item_heap.status = StatusFila.EVASAO
            saida = self._montar_saida(entrada)

        notif = NotificacaoFila(
            tipo=TipoEventoFila.PACIENTE_EVASAO,
            paciente=saida,
            fila_snapshot=await self.get_snapshot(),
            mensagem=f"Paciente {saida.nome_social} evadiu da fila",
        )
        self._hub.publicar(self._unidade_id, notif)
        return saida

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    async def get_snapshot(self) -> FilaSnapshot:
        """Retorna snapshot completo da fila."""
        async with self._lock:
            aguardando = 0
            chamado = 0
            em_atendimento = 0
            finalizado = 0
            evasao = 0
            pacientes_aguardando: list[PacienteFilaOut] = []

            for item in self._heap:
                entrada = self._entradas.get(item.id)
                if not entrada:
                    continue
                saida = self._montar_saida(entrada)
                match item.status:
                    case StatusFila.AGUARDANDO:
                        aguardando += 1
                        pacientes_aguardando.append(saida)
                    case StatusFila.CHAMADO:
                        chamado += 1
                    case StatusFila.EM_ATENDIMENTO:
                        em_atendimento += 1
                    case StatusFila.FINALIZADO:
                        finalizado += 1
                    case StatusFila.EVASAO:
                        evasao += 1

            pacientes_aguardando.sort(key=lambda p: (p.prioridade, p.entrado_em))

            risco_prioritario = self._risco_prioritario_interno()
            tempo_medio = self._tempo_medio_espera_interno()

            return FilaSnapshot(
                total_aguardando=aguardando,
                total_chamado=chamado,
                total_em_atendimento=em_atendimento,
                total_finalizado=finalizado,
                total_evasao=evasao,
                proximos=pacientes_aguardando[:5],
                risco_prioritario=risco_prioritario,
                tempo_medio_espera_min=tempo_medio,
                timestamp=datetime.now(timezone.utc),
            )

    async def get_por_status(self, status: StatusFila) -> list[PacienteFilaOut]:
        """Retorna pacientes filtrados por status."""
        async with self._lock:
            resultado: list[PacienteFilaOut] = []
            for item in self._heap:
                entrada = self._entradas.get(item.id)
                if entrada and item.status == status:
                    resultado.append(self._montar_saida(entrada))
            return resultado

    def get_entradas_count(self) -> int:
        """Total de entradas na fila (inclui todos os status)."""
        return len(self._entradas)

    # ------------------------------------------------------------------
    # Cálculos
    # ------------------------------------------------------------------

    def calcular_tempo_espera(self, paciente: PacienteFilaIn) -> int:
        """Calcula tempo estimado de espera em minutos."""
        base = TEMPO_ALVO_MINUTOS[paciente.classificacao_risco]
        return base

    def calcular_tempo_espera_considerando_fila(
        self, paciente: PacienteFilaIn, posicao_na_fila: int
    ) -> int:
        """Calcula tempo estimado considerando posição na fila."""
        base = TEMPO_ALVO_MINUTOS[paciente.classificacao_risco]
        contagem_acima = sum(
            1
            for item in self._heap
            if item.status == StatusFila.AGUARDANDO
            and item.prioridade < int(Prioridade[paciente.classificacao_risco])
        )
        return base + (contagem_acima * TEMPO_MEDIO_CONSULTA_MINUTOS)

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _montar_saida(self, entrada: _EntradaInterna) -> PacienteFilaOut:
        espera = self.calcular_tempo_espera(entrada.dados)
        return PacienteFilaOut(
            id=entrada.item_heap.id,
            paciente_id=entrada.dados.paciente_id,
            nome_social=entrada.dados.nome_social,
            documento=entrada.dados.documento,
            documento_tipo=entrada.dados.documento_tipo,
            classificacao_risco=entrada.dados.classificacao_risco,
            prioridade=Prioridade[entrada.dados.classificacao_risco],
            queixa_ciap2=entrada.dados.queixa_ciap2,
            cid10_suspeita=entrada.dados.cid10_suspeita,
            unidade_id=entrada.dados.unidade_id,
            profissional_id=entrada.dados.profissional_id,
            consultorio=entrada.dados.consultorio,
            tipo_demanda=entrada.dados.tipo_demanda,
            status=entrada.item_heap.status,
            entrado_em=entrada.entrado_em,
            chamado_em=entrada.chamado_em,
            atendido_em=entrada.atendido_em,
            tempo_espera_estimado_min=espera,
            sinais_vitais=entrada.dados.sinais_vitais,
        )

    def _risco_prioritario_interno(self) -> ClassificacaoRisco | None:
        for item in sorted(self._heap, key=lambda x: (x.prioridade, x.fifo)):
            if item.status in (StatusFila.AGUARDANDO, StatusFila.CHAMADO):
                entrada = self._entradas.get(item.id)
                if entrada:
                    return entrada.dados.classificacao_risco
        return None

    def _tempo_medio_espera_interno(self) -> float:
        aguardando = [
            item
            for item in self._heap
            if item.status == StatusFila.AGUARDANDO
        ]
        if not aguardando:
            return 0.0
        total = sum(
            TEMPO_ALVO_MINUTOS[_PRIORIDADE_RISCO[item.prioridade]]
            for item in aguardando
        )
        return round(total / len(aguardando), 1)


# ---------------------------------------------------------------------------
# Funções utilitárias (standalone)
# ---------------------------------------------------------------------------


def validar_documento(documento: str, tipo: Literal["CNS", "CPF"]) -> str:
    """Valida e normaliza CNS ou CPF. Retorna valor canônico em dígitos."""
    if tipo == "CNS":
        return normalizar_cns(documento)
    if tipo == "CPF":
        return normalizar_cpf(documento)
    raise ValueError(f"Tipo de documento inválido: {tipo}")


def validar_ciap2(codigo: str) -> str:
    """Valida código CIAP-2."""
    return normalizar_ciap2(codigo)


def validar_cid10(codigo: str) -> str:
    """Valida código CID-10."""
    return normalizar_cid10(codigo)


def classificar_por_sinais_vitais(sinais: dict[str, Any]) -> ClassificacaoRisco:
    """Classificação rápida por sinais vitais (triagem rápida)."""
    pas = sinais.get("pa_sistolica")
    pad = sinais.get("pa_diastolica")
    fc = sinais.get("frequencia_cardiaca")
    fr = sinais.get("frequencia_respiratoria")
    sat = sinais.get("saturacao_o2")
    temp = sinais.get("temperatura")

    if pas is not None and pas >= 180:
        return ClassificacaoRisco.VERMELHO
    if pad is not None and pad >= 120:
        return ClassificacaoRisco.VERMELHO
    if fc is not None and fc >= 130:
        return ClassificacaoRisco.VERMELHO
    if fr is not None and fr >= 30:
        return ClassificacaoRisco.VERMELHO
    if sat is not None and sat < 90:
        return ClassificacaoRisco.VERMELHO
    if temp is not None and temp >= 40.0:
        return ClassificacaoRisco.VERMELHO

    if pas is not None and pas >= 160:
        return ClassificacaoRisco.LARANJA
    if fc is not None and fc >= 110:
        return ClassificacaoRisco.LARANJA
    if sat is not None and sat < 94:
        return ClassificacaoRisco.LARANJA

    return ClassificacaoRisco.VERDE


def tempo_espera_por_classificacao(risco: ClassificacaoRisco) -> int:
    """Retorna tempo máximo de espera em minutos para cada classificação."""
    return TEMPO_ALVO_MINUTOS[risco]


def obter_hub_fila() -> HubFilaWS:
    """Retorna a instância global do Hub WebSocket da fila."""
    return _hub_fila_ws
