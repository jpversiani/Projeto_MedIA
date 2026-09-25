"""Fila Eletrônica Reativa de Acolhimento e Chamada por Voz (C3).

Fila de prioridades em memória (``heapq`` + ``asyncio``) para acolhimento e
chamada por voz do atendimento particular e de convênios do MedIA
(TISS ANS 4.01 / DMED Receita Federal), guiada pelo método clínico de
Atenção Primária / Saúde da Família.

Destaques:

* Ordenação por classificação de risco (VERMELHO → AZUL) com desempate FIFO;
* Tempo estimado de espera a partir da posição real na ordem de chamada;
* Disparo de notificações WebSocket por unidade via :class:`HubFilaWS`;
* Espera reativa da chamada (:meth:`FilaAcolhimentoService.aguardar_chamada`)
  para sustentar o fluxo de chamada por voz.

Identificação por CNS/CPF e códigos clínicos CIAP-2/CID-10. Não realiza
envio obrigatório a SUS/SISAB nem integração com periféricos IoT.

Python 3.12 · Pydantic v2 com tipagem estrita · serviço independente de
framework (o endpoint WebSocket apenas consome :func:`obter_hub_fila`).
"""

from __future__ import annotations

import asyncio
import heapq
import itertools
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum, StrEnum
from typing import Any, Final, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    computed_field,
    field_validator,
)

from app.services.validadores import (
    normalizar_cns,
    normalizar_ciap2,
    normalizar_cid10,
    normalizar_cpf,
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

TEMPO_ALVO_MINUTOS: Final[dict[ClassificacaoRisco, int]] = {
    ClassificacaoRisco.VERMELHO: 0,
    ClassificacaoRisco.LARANJA: 10,
    ClassificacaoRisco.AMARELO: 60,
    ClassificacaoRisco.VERDE: 120,
    ClassificacaoRisco.AZUL: 240,
}

TEMPO_MEDIO_CONSULTA_MINUTOS: Final[int] = 15

_TAMANHO_MAXIMO_FILA_WS: Final[int] = 200

_STATUS_SAIRAM_DA_FILA: Final[frozenset[StatusFila]] = frozenset(
    {StatusFila.FINALIZADO, StatusFila.EVASAO}
)


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
    def _validar_documento(cls, valor: str, info: ValidationInfo) -> str:
        tipo = info.data.get("documento_tipo")
        normalizado: str | None
        if tipo == "CNS":
            normalizado = normalizar_cns(valor)
        elif tipo == "CPF":
            normalizado = normalizar_cpf(valor)
        else:
            raise ValueError("documento_tipo deve ser 'CNS' ou 'CPF'")
        if normalizado is None:
            raise ValueError("documento não pode ser nulo")
        return normalizado

    @field_validator("queixa_ciap2")
    @classmethod
    def _validar_ciap2(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        normalizado = normalizar_ciap2(valor)
        if normalizado is None:
            raise ValueError("queixa_ciap2 não pode ser nulo")
        return normalizado

    @field_validator("cid10_suspeita")
    @classmethod
    def _validar_cid10(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        normalizado = normalizar_cid10(valor)
        if normalizado is None:
            raise ValueError("cid10_suspeita não pode ser nulo")
        return normalizado


class PacienteFilaOut(BaseModel):
    """Visão imutável de um paciente na fila."""

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
        """Espera real até a chamada, em minutos (``None`` se não chamado)."""
        if self.chamado_em is None:
            return None
        delta = self.chamado_em - self.entrado_em
        return round(delta.total_seconds() / 60, 1)


class FilaSnapshot(BaseModel):
    """Instantâneo do estado da fila, enviado junto às notificações."""

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
    """Item do heap: ordenado por (prioridade, contador FIFO)."""

    prioridade: int
    fifo: int
    id: uuid.UUID = field(compare=False)
    status: StatusFila = field(default=StatusFila.AGUARDANDO, compare=False)


@dataclass
class _EntradaInterna:
    """Entrada completa mantida em memória."""

    item_heap: _ItemHeap
    dados: PacienteFilaIn
    entrado_em: datetime
    chamado_em: datetime | None = None
    atendido_em: datetime | None = None
    evento_chamada: asyncio.Event = field(default_factory=asyncio.Event)


# ---------------------------------------------------------------------------
# Hub WebSocket para a Fila
# ---------------------------------------------------------------------------


@dataclass
class _ConexaoFila:
    """Assinante WebSocket de uma unidade."""

    fila: asyncio.Queue[NotificacaoFila]
    loop: asyncio.AbstractEventLoop | None = None


def _loop_atual() -> asyncio.AbstractEventLoop | None:
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None


def _enfileirar(
    fila: asyncio.Queue[NotificacaoFila], notificacao: NotificacaoFila
) -> bool:
    try:
        fila.put_nowait(notificacao)
    except asyncio.QueueFull:
        logger.warning("Fila de notificação cheia; evento descartado")
        return False
    return True


class HubFilaWS:
    """Hub em memória das conexões WebSocket da Fila de Acolhimento.

    Mantém uma fila de eventos por unidade (recepção, chamada, início/fim de
    atendimento e evasão) e a publica em todas as conexões assinantes.
    """

    def __init__(self) -> None:
        self._conexoes: dict[str, list[_ConexaoFila]] = defaultdict(list)
        self._stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"conexoes": 0, "eventos": 0}
        )

    def conectar(self, unidade_id: str) -> asyncio.Queue[NotificacaoFila]:
        """Registra um assinante da unidade e devolve sua fila de eventos.

        Deve ser chamada no event loop que consumirá a fila (endpoint
        WebSocket); a publicação usa ``call_soon_threadsafe`` quando o
        publicador roda fora desse loop.
        """
        conexao = _ConexaoFila(
            fila=asyncio.Queue(maxsize=_TAMANHO_MAXIMO_FILA_WS),
            loop=_loop_atual(),
        )
        self._conexoes[unidade_id].append(conexao)
        self._stats[unidade_id]["conexoes"] = len(self._conexoes[unidade_id])
        return conexao.fila

    def desconectar(self, unidade_id: str, fila: asyncio.Queue[NotificacaoFila]) -> None:
        """Remove a assinatura correspondente à ``fila`` da unidade."""
        conexoes = self._conexoes.get(unidade_id)
        if conexoes is None:
            return
        conexoes[:] = [c for c in conexoes if c.fila is not fila]
        if not conexoes:
            self._conexoes.pop(unidade_id, None)
        self._stats[unidade_id]["conexoes"] = len(self._conexoes.get(unidade_id, ()))

    def publicar(self, unidade_id: str, notificacao: NotificacaoFila) -> int:
        """Dispara a notificação para todas as conexões da unidade.

        Retorna a quantidade de conexões que receberam o evento.
        """
        entregues = 0
        for conexao in list(self._conexoes.get(unidade_id, ())):
            if self._entregar(conexao, notificacao):
                entregues += 1
        self._stats[unidade_id]["eventos"] += 1
        return entregues

    def _entregar(self, conexao: _ConexaoFila, notificacao: NotificacaoFila) -> bool:
        loop = conexao.loop
        if loop is None or loop is _loop_atual():
            return _enfileirar(conexao.fila, notificacao)
        if loop.is_closed():
            return False
        try:
            loop.call_soon_threadsafe(_enfileirar, conexao.fila, notificacao)
        except RuntimeError:
            return False
        return True

    def obter_stats(self, unidade_id: str) -> dict[str, Any]:
        """Estatísticas de conexões e eventos da unidade."""
        return {
            "unidade_id": unidade_id,
            "conexoes": self._stats[unidade_id]["conexoes"],
            "eventos": self._stats[unidade_id]["eventos"],
            "timestamp": datetime.now(timezone.utc),
        }


_hub_fila_ws = HubFilaWS()


def obter_hub_fila() -> HubFilaWS:
    """Retorna a instância global do Hub WebSocket da fila."""
    return _hub_fila_ws


# ---------------------------------------------------------------------------
# Serviço principal
# ---------------------------------------------------------------------------


class FilaAcolhimentoService:
    """Fila de prioridades de acolhimento com chamada por voz.

    Usa ``heapq`` para a ordenação (prioridade de risco + FIFO) e
    ``asyncio.Lock`` para serializar as mutações. Calcula o tempo estimado de
    espera a partir da posição na ordem de chamada e dispara notificações
    WebSocket para as unidades assinantes do :class:`HubFilaWS`.
    """

    def __init__(self, unidade_id: str) -> None:
        self._unidade_id = unidade_id
        self._lock = asyncio.Lock()
        self._heap: list[_ItemHeap] = []
        self._entradas: dict[uuid.UUID, _EntradaInterna] = {}
        self._counter = itertools.count()
        self._hub = _hub_fila_ws

    @property
    def unidade_id(self) -> str:
        """Identificador da unidade atendida por esta fila."""
        return self._unidade_id

    # ------------------------------------------------------------------
    # Operações principais
    # ------------------------------------------------------------------

    async def entrar_na_fila(self, paciente: PacienteFilaIn) -> PacienteFilaOut:
        """Enfileira o paciente priorizado pela classificação de risco."""
        async with self._lock:
            entrada_id = uuid.uuid4()
            agora = datetime.now(timezone.utc)
            prioridade = Prioridade[paciente.classificacao_risco]
            item = _ItemHeap(
                prioridade=int(prioridade),
                fifo=next(self._counter),
                id=entrada_id,
                status=StatusFila.AGUARDANDO,
            )
            entrada = _EntradaInterna(item_heap=item, dados=paciente, entrado_em=agora)
            self._entradas[entrada_id] = entrada
            heapq.heappush(self._heap, item)
            saida = self._montar_saida(entrada)

        await self._notificar(
            TipoEventoFila.PACIENTE_ENTRADA,
            saida,
            f"Paciente {saida.nome_social} entrou na fila — risco {saida.classificacao_risco}",
        )
        logger.info(
            "Entrada %s (%s) na fila da unidade %s — risco=%s prioridade=%d",
            entrada_id,
            paciente.nome_social,
            self._unidade_id,
            paciente.classificacao_risco,
            prioridade,
        )
        return saida

    async def proximo_da_fila(self) -> PacienteFilaOut | None:
        """Retorna o próximo paciente da ordem de chamada (sem mutar estado)."""
        async with self._lock:
            entrada = self._proxima_entrada()
            if entrada is None:
                return None
            return self._montar_saida(entrada)

    async def chamar_proximo(self) -> PacienteFilaOut | None:
        """Chama o próximo paciente (``AGUARDANDO`` → ``CHAMADO``)."""
        async with self._lock:
            entrada = self._proxima_entrada()
            if entrada is None:
                return None
            entrada.chamado_em = datetime.now(timezone.utc)
            entrada.item_heap.status = StatusFila.CHAMADO
            entrada.evento_chamada.set()
            saida = self._montar_saida(entrada)

        await self._notificar(
            TipoEventoFila.PACIENTE_CHAMADO,
            saida,
            f"Paciente {saida.nome_social} foi chamado — risco {saida.classificacao_risco}",
        )
        logger.info("Paciente %s chamado na unidade %s", saida.nome_social, self._unidade_id)
        return saida

    async def iniciar_atendimento(self, entrada_id: uuid.UUID) -> PacienteFilaOut:
        """Inicia o atendimento (``CHAMADO`` → ``EM_ATENDIMENTO``)."""
        async with self._lock:
            entrada = self._entradas.get(entrada_id)
            if entrada is None:
                raise KeyError(f"Entrada {entrada_id} não encontrada na fila")
            if entrada.item_heap.status is not StatusFila.CHAMADO:
                self._publicar_erro(
                    "Transição inválida ao iniciar atendimento",
                    f"entrada={entrada_id} status={entrada.item_heap.status} esperado={StatusFila.CHAMADO}",
                )
                raise ValueError(
                    f"Paciente está em status {entrada.item_heap.status}, esperado {StatusFila.CHAMADO}"
                )
            entrada.atendido_em = datetime.now(timezone.utc)
            entrada.item_heap.status = StatusFila.EM_ATENDIMENTO
            saida = self._montar_saida(entrada)

        await self._notificar(
            TipoEventoFila.PACIENTE_ATENDIMENTO,
            saida,
            f"Atendimento iniciado para {saida.nome_social}",
        )
        return saida

    async def finalizar_atendimento(self, entrada_id: uuid.UUID) -> PacienteFilaOut:
        """Finaliza o atendimento (``EM_ATENDIMENTO`` → ``FINALIZADO``)."""
        async with self._lock:
            entrada = self._entradas.get(entrada_id)
            if entrada is None:
                raise KeyError(f"Entrada {entrada_id} não encontrada na fila")
            if entrada.item_heap.status is not StatusFila.EM_ATENDIMENTO:
                self._publicar_erro(
                    "Transição inválida ao finalizar atendimento",
                    f"entrada={entrada_id} status={entrada.item_heap.status} esperado={StatusFila.EM_ATENDIMENTO}",
                )
                raise ValueError(
                    f"Paciente está em status {entrada.item_heap.status}, "
                    f"esperado {StatusFila.EM_ATENDIMENTO}"
                )
            entrada.item_heap.status = StatusFila.FINALIZADO
            entrada.evento_chamada.set()
            saida = self._montar_saida(entrada)

        await self._notificar(
            TipoEventoFila.PACIENTE_FINALIZADO,
            saida,
            f"Atendimento finalizado para {saida.nome_social}",
        )
        return saida

    async def cancelar(self, entrada_id: uuid.UUID) -> PacienteFilaOut:
        """Registra evasão do paciente (``AGUARDANDO``/``CHAMADO`` → ``EVASAO``)."""
        async with self._lock:
            entrada = self._entradas.get(entrada_id)
            if entrada is None:
                raise KeyError(f"Entrada {entrada_id} não encontrada na fila")
            if entrada.item_heap.status not in (
                StatusFila.AGUARDANDO,
                StatusFila.CHAMADO,
            ):
                self._publicar_erro(
                    "Transição inválida ao registrar evasão",
                    f"entrada={entrada_id} status={entrada.item_heap.status}",
                )
                raise ValueError(
                    f"Paciente está em status {entrada.item_heap.status}; "
                    f"evasão permitida apenas em {StatusFila.AGUARDANDO} "
                    f"ou {StatusFila.CHAMADO}"
                )
            entrada.item_heap.status = StatusFila.EVASAO
            entrada.evento_chamada.set()
            saida = self._montar_saida(entrada)

        await self._notificar(
            TipoEventoFila.PACIENTE_EVASAO,
            saida,
            f"Paciente {saida.nome_social} registrou evasão da fila",
        )
        return saida

    async def aguardar_chamada(
        self, entrada_id: uuid.UUID, timeout: float | None = None
    ) -> PacienteFilaOut:
        """Aguarda reativamente até a chamada do paciente (suporte à voz).

        ``timeout`` é em segundos; sem valor, aguarda indefinidamente.

        Raises:
            KeyError: entrada inexistente.
            TimeoutError: paciente não chamado dentro do ``timeout``.
            RuntimeError: paciente saiu da fila sem ter sido chamado.
        """
        async with self._lock:
            entrada = self._entradas.get(entrada_id)
            if entrada is None:
                raise KeyError(f"Entrada {entrada_id} não encontrada na fila")
            evento = entrada.evento_chamada

        try:
            await asyncio.wait_for(evento.wait(), timeout)
        except TimeoutError as exc:
            raise TimeoutError(
                f"Entrada {entrada_id} não foi chamada em {timeout} segundo(s)"
            ) from exc

        async with self._lock:
            entrada = self._entradas.get(entrada_id)
            if entrada is None:
                raise KeyError(f"Entrada {entrada_id} não encontrada na fila")
            if entrada.chamado_em is None:
                self._publicar_erro(
                    "Fluxo de chamada encerrado sem chamada",
                    f"entrada={entrada_id} status={entrada.item_heap.status}",
                )
                raise RuntimeError(
                    f"Entrada {entrada_id} saiu da fila sem chamada "
                    f"(status {entrada.item_heap.status})"
                )
            return self._montar_saida(entrada)

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    async def get_snapshot(self) -> FilaSnapshot:
        """Retorna o instantâneo completo da fila."""
        async with self._lock:
            contagem: dict[StatusFila, int] = {status: 0 for status in StatusFila}
            for item in self._heap:
                if item.id in self._entradas:
                    contagem[item.status] += 1

            aguardando = [
                self._montar_saida(entrada, posicao=indice)
                for indice, entrada in enumerate(self._aguardando_ordenadas())
            ]
            return FilaSnapshot(
                total_aguardando=contagem[StatusFila.AGUARDANDO],
                total_chamado=contagem[StatusFila.CHAMADO],
                total_em_atendimento=contagem[StatusFila.EM_ATENDIMENTO],
                total_finalizado=contagem[StatusFila.FINALIZADO],
                total_evasao=contagem[StatusFila.EVASAO],
                proximos=aguardando[:5],
                risco_prioritario=self._risco_prioritario(),
                tempo_medio_espera_min=self._tempo_medio_espera(),
                timestamp=datetime.now(timezone.utc),
            )

    async def get_por_status(self, status: StatusFila) -> list[PacienteFilaOut]:
        """Retorna os pacientes filtrados por status, na ordem de chamada."""
        async with self._lock:
            return [
                self._montar_saida(self._entradas[item.id])
                for item in sorted(self._heap)
                if item.status == status and item.id in self._entradas
            ]

    async def posicao_na_fila(self, entrada_id: uuid.UUID) -> int | None:
        """Posição na ordem de chamada (``0`` = próximo) ou ``None``."""
        async with self._lock:
            return self._posicao(entrada_id)

    def get_entradas_count(self) -> int:
        """Total de entradas registradas (qualquer status, inclusive concluídas)."""
        return len(self._entradas)

    # ------------------------------------------------------------------
    # Cálculo de espera
    # ------------------------------------------------------------------

    def calcular_tempo_espera(self, paciente: PacienteFilaIn) -> int:
        """Tempo alvo de espera (minutos) para a classificação de risco."""
        return TEMPO_ALVO_MINUTOS[paciente.classificacao_risco]

    def calcular_tempo_espera_considerando_fila(
        self, paciente: PacienteFilaIn, posicao_na_fila: int
    ) -> int:
        """Estimativa de espera: tempo alvo + consultas à frente na fila."""
        base = TEMPO_ALVO_MINUTOS[paciente.classificacao_risco]
        consultas_a_frente = max(posicao_na_fila, 0)
        return base + consultas_a_frente * TEMPO_MEDIO_CONSULTA_MINUTOS

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _proxima_entrada(self) -> _EntradaInterna | None:
        for item in sorted(self._heap):
            entrada = self._entradas.get(item.id)
            if entrada is not None and item.status is StatusFila.AGUARDANDO:
                return entrada
        return None

    def _aguardando_ordenadas(self) -> list[_EntradaInterna]:
        return [
            self._entradas[item.id]
            for item in sorted(self._heap)
            if item.status is StatusFila.AGUARDANDO and item.id in self._entradas
        ]

    def _posicao(self, entrada_id: uuid.UUID) -> int | None:
        for indice, entrada in enumerate(self._aguardando_ordenadas()):
            if entrada.item_heap.id == entrada_id:
                return indice
        return None

    def _montar_saida(
        self, entrada: _EntradaInterna, posicao: int | None = None
    ) -> PacienteFilaOut:
        espera = self.calcular_tempo_espera(entrada.dados)
        if entrada.item_heap.status is StatusFila.AGUARDANDO:
            if posicao is None:
                posicao = self._posicao(entrada.item_heap.id)
            espera = self.calcular_tempo_espera_considerando_fila(
                entrada.dados, 0 if posicao is None else posicao
            )
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

    def _risco_prioritario(self) -> ClassificacaoRisco | None:
        ativos = [
            entrada
            for entrada in self._entradas.values()
            if entrada.item_heap.status in (StatusFila.AGUARDANDO, StatusFila.CHAMADO)
        ]
        if not ativos:
            return None
        ativos.sort(key=lambda e: (e.item_heap.prioridade, e.item_heap.fifo))
        return ativos[0].dados.classificacao_risco

    def _tempo_medio_espera(self) -> float:
        aguardando = self._aguardando_ordenadas()
        if not aguardando:
            return 0.0
        total = sum(
            self.calcular_tempo_espera(entrada.dados) for entrada in aguardando
        )
        return round(total / len(aguardando), 1)

    async def _notificar(
        self, tipo: TipoEventoFila, saida: PacienteFilaOut, mensagem: str
    ) -> int:
        notificacao = NotificacaoFila(
            tipo=tipo,
            paciente=saida,
            fila_snapshot=await self.get_snapshot(),
            mensagem=mensagem,
        )
        return self._hub.publicar(self._unidade_id, notificacao)

    def _publicar_erro(self, mensagem: str, detalhe: str) -> None:
        self._hub.publicar(
            self._unidade_id,
            NotificacaoFila(tipo=TipoEventoFila.ERRO, mensagem=mensagem, erro=detalhe),
        )

    async def limpar_concluidos(self) -> int:
        """Libera da memória as entradas ``FINALIZADO``/``EVASAO``. Retorna o total."""
        async with self._lock:
            concluidas = [
                entrada_id
                for entrada_id, entrada in self._entradas.items()
                if entrada.item_heap.status in _STATUS_SAIRAM_DA_FILA
            ]
            if not concluidas:
                return 0
            removidas = set(concluidas)
            for entrada_id in concluidas:
                self._entradas.pop(entrada_id, None)
            self._heap = [item for item in self._heap if item.id not in removidas]
            heapq.heapify(self._heap)
            return len(concluidas)


# ---------------------------------------------------------------------------
# Funções utilitárias (standalone)
# ---------------------------------------------------------------------------


def validar_documento(documento: str, tipo: Literal["CNS", "CPF"]) -> str:
    """Valida e normaliza CNS ou CPF. Retorna o valor canônico em dígitos."""
    normalizado: str | None
    if tipo == "CNS":
        normalizado = normalizar_cns(documento)
    elif tipo == "CPF":
        normalizado = normalizar_cpf(documento)
    else:
        raise ValueError(f"Tipo de documento inválido: {tipo}")
    if normalizado is None:
        raise ValueError("documento não pode ser nulo")
    return normalizado


def validar_ciap2(codigo: str) -> str:
    """Valida código CIAP-2."""
    normalizado = normalizar_ciap2(codigo)
    if normalizado is None:
        raise ValueError("Código CIAP-2 não pode ser nulo")
    return normalizado


def validar_cid10(codigo: str) -> str:
    """Valida código CID-10."""
    normalizado = normalizar_cid10(codigo)
    if normalizado is None:
        raise ValueError("Código CID-10 não pode ser nulo")
    return normalizado


def classificar_por_sinais_vitais(sinais: dict[str, Any]) -> ClassificacaoRisco:
    """Triagem rápida por sinais vitais no acolhimento."""
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
    """Retorna o tempo alvo de espera (minutos) para a classificação."""
    return TEMPO_ALVO_MINUTOS[risco]
