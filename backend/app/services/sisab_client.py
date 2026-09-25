from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.validadores import normalizar_cns, normalizar_cpf, normalizar_ciap2, normalizar_cid10, normalizar_cnes

logger = logging.getLogger(__name__)

__all__ = [
    "TipoFicha",
    "StatusRecibo",
    "FichaSISAB",
    "LoteSISAB",
    "ReciboItem",
    "ReciboSISAB",
    "SISABClient",
    "SISABError",
    "LoteInvalidoError",
    "TimeoutSISABError",
    "ReciboRejeitadoError",
]


class TipoFicha(str, Enum):
    ATENDIMENTO_INDIVIDUAL = "atendimentoIndividual"
    VISITA_DOMICILIAR = "visitaDomiciliar"
    ATIVIDADE_COLETIVA = "atividadeColetiva"
    PROCEDIMENTO = "procedimento"
    CADASTRO_INDIVIDUAL = "cadastroIndividual"
    CADASTRO_DOMICILIAR = "cadastroDomiciliar"


class StatusRecibo(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class SISABError(Exception):
    """Base exception for SISAB client errors."""


class LoteInvalidoError(SISABError):
    """Raised when the lote fails validation."""


class TimeoutSISABError(SISABError):
    """Raised when the SISAB endpoint times out."""


class ReciboRejeitadoError(SISABError):
    """Raised when the Ministry rejects the lote."""


class FichaSISAB(BaseModel):
    """Ficha individual do SISAB (Ministério da Saúde)."""

    model_config = ConfigDict(strict=True, frozen=True)

    cns: str = Field(..., min_length=15, max_length=15, description="Cartão Nacional de Saúde (15 dígitos)")
    cpf: str | None = Field(default=None, description="CPF do paciente (11 dígitos)")
    cnes: str = Field(..., min_length=7, max_length=7, description="CNES do estabelecimento (7 dígitos)")
    ciap2: str | None = Field(default=None, min_length=3, max_length=3, description="Código CIAP-2 (ex.: A01)")
    cid10: str | None = Field(default=None, description="Código CID-10 (ex.: I10.9)")
    data_atendimento: str = Field(..., description="Data ISO 8601 do atendimento")
    tipo_ficha: TipoFicha = Field(default=TipoFicha.ATENDIMENTO_INDIVIDUAL)
    metodo_sus: str = Field(default="SOAP", max_length=20)
    profissional_cns: str | None = Field(default=None, description="CNS do profissional")

    @field_validator("cns", mode="before")
    @classmethod
    def validate_cns(cls, v: str) -> str:
        return normalizar_cns(v)

    @field_validator("cpf", mode="before")
    @classmethod
    def validate_cpf(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return normalizar_cpf(v)

    @field_validator("ciap2", mode="before")
    @classmethod
    def validate_ciap2(cls, v: str) -> str:
        return normalizar_ciap2(v)

    @field_validator("cid10", mode="before")
    @classmethod
    def validate_cid10(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return normalizar_cid10(v)

    @field_validator("cnes", mode="before")
    @classmethod
    def validate_cnes(cls, v: str) -> str:
        return normalizar_cnes(v)

    @field_validator("data_atendimento")
    @classmethod
    def validate_data(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"data_atendimento inválida: '{v}'. Esperado formato ISO 8601.")
        return v


class LoteSISAB(BaseModel):
    """Lote de fichas para transmissão ao SISAB."""

    model_config = ConfigDict(strict=True)

    lote_id: str = Field(..., min_length=1, max_length=50, description="Identificador único do lote")
    cnes_origem: str = Field(..., min_length=7, max_length=7, description="CNES do estabelecimento de origem")
    fichas: list[FichaSISAB] = Field(..., min_length=1, description="Lista de fichas no lote")
    data_hora_envio: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("cnes_origem", mode="before")
    @classmethod
    def validate_cnes_origem(cls, v: str) -> str:
        return normalizar_cnes(v)

    @property
    def total_fichas(self) -> int:
        return len(self.fichas)


class ReciboItem(BaseModel):
    """Item individual do recibo de retorno do Ministério da Saúde."""

    model_config = ConfigDict(strict=True)

    sequencial: int = Field(..., ge=0, description="Sequencial da ficha no lote")
    status: StatusRecibo
    codigo_retorno: str | None = Field(default=None, description="Código de retorno do DATASUS")
    mensagem: str = Field(default="", description="Mensagem de retorno")
    dados_xml: str | None = Field(default=None, description="XML de retorno bruto")


class ReciboSISAB(BaseModel):
    """Recibo completo de entrega do lote ao SISAB."""

    model_config = ConfigDict(strict=True)

    lote_id: str = Field(..., description="ID do lote correspondente")
    status_geral: StatusRecibo
    total_registros: int = Field(..., ge=0)
    registros_sucesso: int = Field(default=0, ge=0)
    registros_erro: int = Field(default=0, ge=0)
    registros_aviso: int = Field(default=0, ge=0)
    itens: list[ReciboItem] = Field(default_factory=list)
    data_processamento: datetime | None = Field(default=None)
    xml_recibo: str | None = Field(default=None, description="XML bruto do recibo")

    @property
    def sucesso_total(self) -> bool:
        return self.registros_erro == 0 and self.status_geral == StatusRecibo.SUCCESS


class SISABClient:
    """Cliente resiliente para transmissão de lotes ao SISAB (DATASUS).

    Implementa timeout resiliente, retry com backoff exponencial e
    parsing dos recibos de entrega do Ministério da Saúde.

    Args:
        base_url: URL base da API SISAB (ex.: https://apisus.gov.br/sisab)
        timeout_seg: Timeout por requisição em segundos (default: 30)
        max_retries: Número máximo de tentativas (default: 3)
        backoff_factor: Fator de backoff exponencial em segundos (default: 1.0)
        headers: Headers HTTP adicionais (autenticação, etc.)
    """

    def __init__(
        self,
        base_url: str,
        timeout_seg: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seg = timeout_seg
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.headers = headers or {}
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> SISABClient:
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout_seg, connect=10.0, read=self.timeout_seg),
            headers=self.headers,
        )
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout_seg, connect=10.0, read=self.timeout_seg),
                headers=self.headers,
            )
        return self._client

    async def enviar_lote(self, lote: LoteSISAB) -> ReciboSISAB:
        """Envia um lote de fichas ao SISAB com retry e backoff exponencial.

        Args:
            lote: LoteSISAB validado para transmissão.

        Returns:
            ReciboSISAB com o resultado da transmissão.

        Raises:
            LoteInvalidoError: Se o lote falhar na validação.
            TimeoutSISABError: Se todas as tentativas expirarem.
            ReciboRejeitadoError: Se o Ministério rejeitar o lote.
        """
        self._validar_lote(lote)

        last_error: Exception | None = None

        for tentativa in range(1, self.max_retries + 1):
            try:
                return await self._enviar_com_retry(lote)
            except httpx.TimeoutException as exc:
                last_error = exc
                logger.warning(
                    "Timeout no envio do lote %s (tentativa %d/%d)",
                    lote.lote_id, tentativa, self.max_retries,
                )
                if tentativa < self.max_retries:
                    await self._backoff(tentativa)
            except httpx.ConnectError as exc:
                last_error = exc
                logger.warning(
                    "Erro de conexão no envio do lote %s (tentativa %d/%d)",
                    lote.lote_id, tentativa, self.max_retries,
                )
                if tentativa < self.max_retries:
                    await self._backoff(tentativa)
            except httpx.HTTPStatusError as exc:
                last_error = exc
                logger.error(
                    "HTTP %d ao enviar lote %s (tentativa %d/%d)",
                    exc.response.status_code, lote.lote_id, tentativa, self.max_retries,
                )
                if exc.response.status_code < 500 and exc.response.status_code != 429:
                    raise ReciboRejeitadoError(
                        f" Ministério rejeitou o lote: HTTP {exc.response.status_code}"
                    ) from exc
                if tentativa < self.max_retries:
                    await self._backoff(tentativa)

        raise TimeoutSISABError(
            f"Falha ao enviar lote {lote.lote_id} após {self.max_retries} tentativas"
        ) from last_error

    async def _enviar_com_retry(self, lote: LoteSISAB) -> ReciboSISAB:
        """Envia o lote em uma única tentativa e processa o recibo."""
        client = self._get_client()
        payload = lote.model_dump(mode="json")

        response = await client.post(
            "/v1/lotes",
            json=payload,
        )
        response.raise_for_status()

        raw_data = response.json()
        xml_recibo = response.text

        recibo = self._parse_recibo(raw_data, xml_recibo)
        return recibo

    def _parse_recibo(self, data: dict[str, Any], xml_bruto: str | None = None) -> ReciboSISAB:
        """Parseia o recibo de retorno do Ministério da Saúde.

        Suporta ambos os formatos:
        - JSON (API REST moderna)
        - XML legado do DATASUS (convertido para dict pelo cliente)
        """
        lote_id = data.get("lote_id") or data.get("numeroLote") or data.get("id", "")

        status_geral = self._extrair_status_geral(data)
        total = data.get("totalRegistros") or data.get("total_registros", 0)
        sucesso = data.get("registrosSucesso") or data.get("sucesso", 0)
        erro = data.get("registrosErro") or data.get("erro", 0)
        aviso = data.get("registrosAviso") or data.get("aviso", 0)
        processamento = data.get("dataProcessamento") or data.get("data_processamento")
        if isinstance(processamento, str):
            processamento_dt = datetime.fromisoformat(processamento)
        elif isinstance(processamento, datetime):
            processamento_dt = processamento
        else:
            processamento_dt = None

        itens: list[ReciboItem] = []
        itens_raw = data.get("itens") or data.get("registros") or data.get("itensRecibo", [])
        for idx, item_data in enumerate(itens_raw):
            item = ReciboItem(
                sequencial=item_data.get("sequencial", idx),
                status=self._extrair_status_item(item_data),
                codigo_retorno=item_data.get("codigoRetorno") or item_data.get("codigo_retorno"),
                mensagem=item_data.get("mensagem") or item_data.get("msg", ""),
                dados_xml=item_data.get("dadosXml") or item_data.get("dados_xml"),
            )
            itens.append(item)

        return ReciboSISAB(
            lote_id=str(lote_id),
            status_geral=status_geral,
            total_registros=total,
            registros_sucesso=sucesso,
            registros_erro=erro,
            registros_aviso=aviso,
            itens=itens,
            data_processamento=processamento_dt,
            xml_recibo=xml_bruto,
        )

    @staticmethod
    def _extrair_status_geral(data: dict[str, Any]) -> StatusRecibo:
        raw = data.get("status") or data.get("statusGeral", "")
        if isinstance(raw, StatusRecibo):
            return raw
        try:
            return StatusRecibo(raw.lower())
        except ValueError:
            if "error" in str(raw).lower():
                return StatusRecibo.ERROR
            if "warning" in str(raw).lower():
                return StatusRecibo.WARNING
            return StatusRecibo.SUCCESS

    @staticmethod
    def _extrair_status_item(data: dict[str, Any]) -> StatusRecibo:
        raw = data.get("status") or data.get("statusItem", "")
        if isinstance(raw, StatusRecibo):
            return raw
        try:
            return StatusRecibo(raw.lower())
        except ValueError:
            if "error" in str(raw).lower():
                return StatusRecibo.ERROR
            if "warning" in str(raw).lower():
                return StatusRecibo.WARNING
            return StatusRecibo.SUCCESS

    def _validar_lote(self, lote: LoteSISAB) -> None:
        """Validação pré-envio do lote."""
        errors: list[str] = []
        if not lote.fichas:
            errors.append("Lote deve conter pelo menos uma ficha")
        for i, ficha in enumerate(lote.fichas):
            if ficha.cid10 and ficha.ciap2:
                pass
            if not ficha.cid10 and not ficha.ciap2:
                errors.append(f"Ficha [{i}]: deve conter CIAP-2 ou CID-10")
        if errors:
            raise LoteInvalidoError("; ".join(errors))

    @staticmethod
    async def _backoff(tentativa: int, base: float = 1.0, maximo: float = 32.0) -> None:
        """Backoff exponencial com jitter."""
        delay = min(base * (2 ** (tentativa - 1)), maximo)
        jitter = delay * 0.1
        await asyncio.sleep(delay + jitter)

    async def close(self) -> None:
        """Fecha o cliente HTTP."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None