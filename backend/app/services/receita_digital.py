from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.receita import ReceitaDigital

ALGORITMO_ASSINATURA: Literal["HMAC-SHA256"] = "HMAC-SHA256"
VARIAVEL_AMBIENTE_CHAVE: str = "MEDIA_CHAVE_INTEGRIDADE"
_MIN_COMPRIMENTO_CHAVE = 16

_METADADOS_CAMPOS: tuple[str, ...] = (
    "hash_assinatura",
    "assinatura",
    "algoritmo_assinatura",
    "data_assinatura",
)


class PrescricaoInvalidaError(ValueError):
    pass


class HashInvalidoError(PrescricaoInvalidaError):
    pass


class AssinaturaInvalidaError(PrescricaoInvalidaError):
    pass


def _normalizar_nfc(valor: object) -> object:
    if isinstance(valor, str):
        return unicodedata.normalize("NFC", valor)
    if isinstance(valor, list):
        return [_normalizar_nfc(item) for item in valor]
    if isinstance(valor, dict):
        return {k: _normalizar_nfc(v) for k, v in valor.items()}
    return valor


def _serializar_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone(timedelta(hours=-3)))
    dt = dt.astimezone(timezone.utc)
    return dt.isoformat()


def _dict_sem_metadados(prescricao: ReceitaDigital) -> dict[str, object]:
    dados = prescricao.model_dump()
    for campo in _METADADOS_CAMPOS:
        dados.pop(campo, None)
    return dados


def _converter_valores(obj: object) -> object:
    if isinstance(obj, datetime):
        return _serializar_datetime(obj)
    if isinstance(obj, dict):
        return {k: _converter_valores(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_converter_valores(item) for item in obj]
    return obj


def serializar_canonico(prescricao: ReceitaDigital) -> str:
    dados = _dict_sem_metadados(prescricao)
    dados = _normalizar_nfc(dados)
    dados = _converter_valores(dados)
    return json.dumps(dados, sort_keys=True, separators=(",", ":"))


def gerar_hash_prescricao(prescricao: ReceitaDigital) -> str:
    if not prescricao.medicamentos:
        raise PrescricaoInvalidaError("Prescrição sem medicamentos não pode ser hashada")
    canonic = serializar_canonico(prescricao)
    return hashlib.sha256(canonic.encode("utf-8")).hexdigest()


def _hash_valido(hex_hash: str) -> bool:
    if len(hex_hash) != 64:
        return False
    return all(c in "0123456789abcdef" for c in hex_hash)


class AssinadorReceitaDigital:
    def __init__(self, chave: bytes) -> None:
        if not isinstance(chave, bytes):
            raise TypeError("A chave deve ser bytes")
        if len(chave) < _MIN_COMPRIMENTO_CHAVE:
            raise ValueError(
                f"A chave deve ter pelo menos {_MIN_COMPRIMENTO_CHAVE} bytes"
            )
        self._chave = hashlib.sha256(chave).digest()
        self._chave_id = hashlib.sha256(chave).hexdigest()[:16]

    @property
    def chave_id(self) -> str:
        return self._chave_id

    @staticmethod
    def gerar_chave() -> bytes:
        return os.urandom(32)

    def assinar(self, prescricao: ReceitaDigital) -> ReceitaDigital:
        if not prescricao.medicamentos:
            raise PrescricaoInvalidaError("Prescrição sem medicamentos não pode ser assinada")
        hash_hex = gerar_hash_prescricao(prescricao)
        canonic = serializar_canonico(prescricao)
        assinatura_bytes = hmac.new(
            self._chave, canonic.encode("utf-8"), hashlib.sha256
        ).digest()
        assinatura_b64 = base64.b64encode(assinatura_bytes).decode("ascii")
        agora = datetime.now(timezone.utc)
        return prescricao.model_copy(
            update={
                "hash_assinatura": hash_hex,
                "assinatura": assinatura_b64,
                "algoritmo_assinatura": ALGORITMO_ASSINATURA,
                "data_assinatura": agora,
            }
        )

    def verificar(self, prescricao: ReceitaDigital) -> bool:
        if not prescricao.medicamentos:
            raise PrescricaoInvalidaError("Prescrição sem medicamentos não pode ser verificada")
        if prescricao.hash_assinatura is None or prescricao.assinatura is None:
            raise PrescricaoInvalidaError("Prescrição não foi assinada")
        if not _hash_valido(prescricao.hash_assinatura):
            raise HashInvalidoError("Hash de integridade inválido")
        try:
            assinatura_bytes = base64.b64decode(
                prescricao.assinatura, validate=True
            )
        except Exception:
            raise AssinaturaInvalidaError("Assinatura corrompida")
        canonic = serializar_canonico(prescricao)
        esperado_hmac = hmac.new(
            self._chave, canonic.encode("utf-8"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(assinatura_bytes, esperado_hmac):
            raise AssinaturaInvalidaError(
                "Assinatura inválida - chave incorreta ou documento adulterado"
            )
        if prescricao.algoritmo_assinatura != ALGORITMO_ASSINATURA:
            raise AssinaturaInvalidaError(
                f"Algoritmo desconhecido: {prescricao.algoritmo_assinatura}"
            )
        computado = gerar_hash_prescricao(prescricao)
        if not hmac.compare_digest(prescricao.hash_assinatura, computado):
            raise HashInvalidoError("Hash de integridade não confere com o conteúdo")
        return True


def validar_documento_emitido(
    prescricao: ReceitaDigital, chave: str | bytes | None = None
) -> bool:
    if chave is None:
        chave_env = os.environ.get(VARIAVEL_AMBIENTE_CHAVE)
        if chave_env is None:
            raise RuntimeError(f"Variável de ambiente {VARIAVEL_AMBIENTE_CHAVE} não configurada")
        chave = chave_env.encode("ascii")
    if isinstance(chave, str):
        chave = chave.encode("ascii")
    assinador = AssinadorReceitaDigital(chave)
    return assinador.verificar(prescricao)