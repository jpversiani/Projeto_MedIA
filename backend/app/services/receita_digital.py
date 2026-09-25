"""Serviço de Validação Criptográfica da Receita Digital (C2 — SUS/APS).

Ciclo de vida criptográfico da prescrição eletrônica do PEC:

1. **Serialização canônica** (``serializar_canonico``) — JSON determinístico
   com chaves ordenadas, separadores compactos, normalização Unicode NFC e
   datas convertidas para UTC (fuso ausente interpretado como Brasília, UTC-3),
   excluindo os metadados de integridade do documento.
2. **Hash SHA-256 canônico** (``gerar_hash_prescricao``) — identidade do
   conteúdo clínico (CNS/CPF do cidadão, CID-10, CIAP-2, medicamentos,
   dosagens e observações) em hexadecimal de 64 caracteres, pronta para o
   QR Code da farmácia.
3. **Assinatura digital** (``AssinadorReceitaDigital.assinar``) — HMAC-SHA256
   sobre o payload canônico com a chave secreta da unidade (mínimo de 16
   bytes, derivada por SHA-256), gravando hash, assinatura, algoritmo e data
   de assinatura no documento.
4. **Verificação de integridade** (``AssinadorReceitaDigital.verificar``) —
   confere assinatura, algoritmo e hash em comparação de tempo constante,
   detectando adulteração de dosagens, medicamentos, quantidades, CNS/CPF,
   CID-10 e CIAP-2 após a emissão.
5. **Verificação de dispensação** (``verificar_dispensacao``) — confere a
   assinatura da receita e valida a baixa farmacêutica contra o que foi
   prescrito (medicamento, dosagem, posologia e quantidade autorizada).

Conformidade: Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0,
padrões SUS/APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF) e
cobertura de testes automatizados com pytest.

Projeto MedIA — Atenção Primária à Saúde.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import unicodedata
from collections.abc import Iterable, Sequence
from datetime import datetime, timedelta, timezone
from typing import Final, Literal

from app.models.receita import Medicamento, ReceitaDigital

__all__ = [
    "ALGORITMO_ASSINATURA",
    "VARIAVEL_AMBIENTE_CHAVE",
    "AssinadorReceitaDigital",
    "AssinaturaInvalidaError",
    "DispensacaoInvalidaError",
    "HashInvalidoError",
    "PrescricaoInvalidaError",
    "gerar_hash_prescricao",
    "serializar_canonico",
    "validar_documento_emitido",
    "verificar_dispensacao",
]

ALGORITMO_ASSINATURA: Literal["HMAC-SHA256"] = "HMAC-SHA256"
VARIAVEL_AMBIENTE_CHAVE: Final[str] = "MEDIA_CHAVE_INTEGRIDADE"
FUSO_BRASILIA: Final[timedelta] = timedelta(hours=-3)

_MIN_COMPRIMENTO_CHAVE: Final[int] = 16
_TAMANHO_HASH_SHA256: Final[int] = 64
_TAMANHO_ASSINATURA_HMAC: Final[int] = 32
_HEXADECIMAIS: Final[frozenset[str]] = frozenset("0123456789abcdef")
_METADADOS: Final[tuple[str, ...]] = (
    "hash_assinatura",
    "assinatura",
    "algoritmo_assinatura",
    "data_assinatura",
)


class PrescricaoInvalidaError(ValueError):
    """Prescrição rejeitada: conteúdo clínico ou metadados de integridade."""


class HashInvalidoError(PrescricaoInvalidaError):
    """Hash SHA-256 do documento ausente, malformado ou não confere."""


class AssinaturaInvalidaError(PrescricaoInvalidaError):
    """Assinatura digital inválida: documento adulterado ou chave incorreta."""


class DispensacaoInvalidaError(PrescricaoInvalidaError):
    """Baixa farmacêutica incompatível com a receita digital assinada."""


def _normalizar_nfc(valor: object) -> object:
    """Normaliza toda a estrutura para Unicode NFC (mesmo texto, mesmo hash)."""
    if isinstance(valor, str):
        return unicodedata.normalize("NFC", valor)
    if isinstance(valor, list):
        return [_normalizar_nfc(item) for item in valor]
    if isinstance(valor, dict):
        return {chave: _normalizar_nfc(item) for chave, item in valor.items()}
    return valor


def _serializar_datetime(data: datetime) -> str:
    """Converte datas para UTC; data sem fuso é interpretada como Brasília."""
    if data.tzinfo is None:
        data = data.replace(tzinfo=timezone(FUSO_BRASILIA))
    return data.astimezone(timezone.utc).isoformat()


def _converter_valores(objeto: object) -> object:
    if isinstance(objeto, datetime):
        return _serializar_datetime(objeto)
    if isinstance(objeto, dict):
        return {chave: _converter_valores(item) for chave, item in objeto.items()}
    if isinstance(objeto, list):
        return [_converter_valores(item) for item in objeto]
    return objeto


def _conteudo_clinico(prescricao: ReceitaDigital) -> dict[str, object]:
    dados: dict[str, object] = dict(prescricao.model_dump())
    for campo in _METADADOS:
        dados.pop(campo, None)
    return dados


def serializar_canonico(prescricao: ReceitaDigital) -> str:
    """Serializa a prescrição em JSON canônico e determinístico.

    Regras: chaves ordenadas, separadores sem espaços, texto em NFC, datas em
    UTC e metadados de integridade (hash/assinatura/algoritmo/data) excluídos,
    de modo que assinar e verificar operem exatamente sobre o mesmo payload.
    """
    dados = _normalizar_nfc(_conteudo_clinico(prescricao))
    return json.dumps(_converter_valores(dados), sort_keys=True, separators=(",", ":"))


def gerar_hash_prescricao(prescricao: ReceitaDigital) -> str:
    """Gera o hash SHA-256 canônico (hex de 64 caracteres) da prescrição.

    Levanta ``PrescricaoInvalidaError`` para prescrição sem medicamentos —
    documento clínico incompleto não pode receber identidade criptográfica.
    """
    if not prescricao.medicamentos:
        raise PrescricaoInvalidaError("Prescrição sem medicamentos não pode ser hashada")
    return hashlib.sha256(serializar_canonico(prescricao).encode("utf-8")).hexdigest()


def _hash_valido(hex_hash: str) -> bool:
    """Confere o formato do hash SHA-256: 64 caracteres em hexadecimal minúsculo."""
    if len(hex_hash) != _TAMANHO_HASH_SHA256:
        return False
    return all(caractere in _HEXADECIMAIS for caractere in hex_hash)


def _normalizar_identificador(valor: str) -> str:
    """Normaliza nome/dosagem/posologia para comparação na dispensação."""
    return unicodedata.normalize("NFC", valor).strip().casefold()


def _conferir_dispensacao(
    receita: ReceitaDigital,
    itens_dispensados: Sequence[Medicamento] | Iterable[Medicamento],
) -> None:
    """Confere a baixa farmacêutica contra o conteúdo assinado da receita.

    Regras:
    * a receita precisa conter ao menos um medicamento prescrito;
    * cada item dispensado deve corresponder a um item prescrito
      (mesmo medicamento, dosagem e posologia após normalização NFC);
    * a soma das quantidades dispensadas por item não pode exceder a
      quantidade prescrita (dispensação fracionada é permitida).
    """
    if not receita.medicamentos:
        raise DispensacaoInvalidaError(
            "Receita sem medicamentos prescritos não admite dispensação"
        )
    itens = list(itens_dispensados)
    if not itens:
        raise DispensacaoInvalidaError("Dispensação sem itens não pode ser confirmada")

    autorizadas: dict[tuple[str, str, str], int] = {}
    for medicamento in receita.medicamentos:
        chave = (
            _normalizar_identificador(medicamento.nome),
            _normalizar_identificador(medicamento.dosagem),
            _normalizar_identificador(medicamento.frequencia),
        )
        autorizadas[chave] = autorizadas.get(chave, 0) + medicamento.quantidade

    dispensadas: dict[tuple[str, str, str], int] = {}
    for item in itens:
        chave = (
            _normalizar_identificador(item.nome),
            _normalizar_identificador(item.dosagem),
            _normalizar_identificador(item.frequencia),
        )
        if chave not in autorizadas:
            raise DispensacaoInvalidaError(
                "Medicamento não prescrito ou com dosagem/posologia divergente: "
                f"{item.nome} {item.dosagem} {item.frequencia}"
            )
        dispensadas[chave] = dispensadas.get(chave, 0) + item.quantidade

    for chave, quantidade_dispensada in dispensadas.items():
        quantidade_autorizada = autorizadas[chave]
        if quantidade_dispensada > quantidade_autorizada:
            raise DispensacaoInvalidaError(
                f"Quantidade dispensada ({quantidade_dispensada}) excede a prescrita "
                f"({quantidade_autorizada}) para {chave[0]} {chave[1]} {chave[2]}"
            )


class AssinadorReceitaDigital:
    """Assina e verifica receitas digitais com HMAC-SHA256 (chave da unidade).

    A chave é derivada com SHA-256 e ``chave_id`` expõe um identificador
    público (16 hex) para seleção da chave correta na verificação, sem
    revelar o segredo.
    """

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
        """Identificador público (16 hex) da chave usada na assinatura."""
        return self._chave_id

    @staticmethod
    def gerar_chave() -> bytes:
        """Gera uma chave secreta aleatória de 32 bytes (CSPRNG do sistema)."""
        return os.urandom(32)

    def assinar(self, prescricao: ReceitaDigital) -> ReceitaDigital:
        """Assina a prescrição e devolve uma cópia com os metadados preenchidos.

        A instância original nunca é modificada. ``hash_assinatura`` guarda o
        SHA-256 canônico (conteúdo do QR Code) e ``assinatura`` o HMAC-SHA256
        em base64 do mesmo payload canônico.
        """
        if not prescricao.medicamentos:
            raise PrescricaoInvalidaError(
                "Prescrição sem medicamentos não pode ser assinada"
            )
        hash_hex = gerar_hash_prescricao(prescricao)
        assinatura = hmac.new(
            self._chave, serializar_canonico(prescricao).encode("utf-8"), hashlib.sha256
        ).digest()
        return prescricao.model_copy(
            update={
                "hash_assinatura": hash_hex,
                "assinatura": base64.b64encode(assinatura).decode("ascii"),
                "algoritmo_assinatura": ALGORITMO_ASSINATURA,
                "data_assinatura": datetime.now(timezone.utc),
            }
        )

    def verificar(self, prescricao: ReceitaDigital) -> bool:
        """Verifica a integridade da receita assinada.

        Levanta ``PrescricaoInvalidaError`` (ou suas especializações
        ``HashInvalidoError`` e ``AssinaturaInvalidaError``) para qualquer
        adulteração de dosagem, medicamento, quantidade, CNS/CPF, CID-10,
        CIAP-2, observações, hash ou chave; devolve ``True`` quando íntegra.
        Todas as comparações usam ``hmac.compare_digest`` (tempo constante).
        """
        if not prescricao.medicamentos:
            raise PrescricaoInvalidaError(
                "Prescrição sem medicamentos não pode ser verificada"
            )
        if prescricao.hash_assinatura is None or prescricao.assinatura is None:
            raise PrescricaoInvalidaError("Prescrição não foi assinada")
        if not _hash_valido(prescricao.hash_assinatura):
            raise HashInvalidoError("Hash de integridade inválido")
        try:
            assinatura = base64.b64decode(prescricao.assinatura, validate=True)
        except Exception as erro:
            raise AssinaturaInvalidaError("Assinatura corrompida") from erro

        canonic = serializar_canonico(prescricao).encode("utf-8")
        esperado = hmac.new(self._chave, canonic, hashlib.sha256).digest()
        if len(assinatura) != _TAMANHO_ASSINATURA_HMAC or not hmac.compare_digest(
            assinatura, esperado
        ):
            raise AssinaturaInvalidaError(
                "Assinatura inválida - chave incorreta ou documento adulterado"
            )
        if prescricao.algoritmo_assinatura != ALGORITMO_ASSINATURA:
            raise AssinaturaInvalidaError(
                f"Algoritmo desconhecido: {prescricao.algoritmo_assinatura}"
            )
        if not hmac.compare_digest(
            prescricao.hash_assinatura, gerar_hash_prescricao(prescricao)
        ):
            raise HashInvalidoError("Hash de integridade não confere com o conteúdo")
        return True

    def verificar_dispensacao(
        self,
        receita: ReceitaDigital,
        itens_dispensados: Sequence[Medicamento] | Iterable[Medicamento],
    ) -> bool:
        """Verifica a assinatura e confere a dispensação contra a receita."""
        self.verificar(receita)
        _conferir_dispensacao(receita, itens_dispensados)
        return True


def verificar_dispensacao(
    receita: ReceitaDigital,
    itens_dispensados: Sequence[Medicamento] | Iterable[Medicamento],
    assinador: AssinadorReceitaDigital,
) -> bool:
    """Valida a baixa farmacêutica contra a receita digital assinada.

    Garante que medicamentos e dosagens dispensados correspondam ao documento
    autenticado — qualquer divergência levanta ``DispensacaoInvalidaError``
    (assinatura inválida levanta ``AssinaturaInvalidaError``).
    """
    return assinador.verificar_dispensacao(receita, itens_dispensados)


def validar_documento_emitido(
    prescricao: ReceitaDigital, chave: str | bytes | None = None
) -> bool:
    """Valida o documento emitido: usa a chave informada ou a de ambiente.

    Sem chave explícita nem variável ``MEDIA_CHAVE_INTEGRIDADE``, levanta
    ``RuntimeError`` — a verificação nunca pode ser contornada por ausência
    silenciosa de segredo.
    """
    if chave is None:
        chave_ambiente = os.environ.get(VARIAVEL_AMBIENTE_CHAVE)
        if chave_ambiente is None:
            raise RuntimeError(
                f"Variável de ambiente {VARIAVEL_AMBIENTE_CHAVE} não configurada"
            )
        chave = chave_ambiente
    chave_bytes = chave.encode("utf-8") if isinstance(chave, str) else chave
    return AssinadorReceitaDigital(chave_bytes).verificar(prescricao)
