"""Validadores oficiais de identificação e terminologia clínica (SUS/APS).

Implementa os algoritmos oficiais utilizados pelo Ministério da Saúde:

* **CNS** (Cartão Nacional de Saúde) — 15 dígitos, iniciado em 1/2 (definitivo)
  ou 7/8/9 (provisório); soma ponderada com pesos de 15 a 1 deve ser múltipla
  de 11 (Manual de Integração do Cartão Nacional de Saúde — DATASUS).
* **CPF** — 11 dígitos, com os dois dígitos verificadores calculados pelo
  algoritmo de módulo 11 da Receita Federal.
* **CIAP-2** — código de 3 caracteres: letra (A–Z) seguida de 2 dígitos.
* **CID-10** — categoria ``A99`` com extensão opcional ``.9`` / ``.99``.
* **CNES** — 7 dígitos numéricos do estabelecimento.

Todos os validadores normalizam a entrada (removem pontuação) e devolvem o
valor canônico em dígitos, prontos para persistência.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "CNSInvalidoError",
    "CPFInvalidoError",
    "CodigoClinicoInvalidoError",
    "ValidadorCNS",
    "normalizar_cns",
    "normalizar_cpf",
    "normalizar_ciap2",
    "normalizar_cid10",
    "normalizar_cnes",
]

_PADRAO_NAO_NUMERICO: Final[re.Pattern[str]] = re.compile(r"[^0-9]")
_PADRAO_CIAP2: Final[re.Pattern[str]] = re.compile(r"^[A-Z]\d{2}$")
_PADRAO_CID10: Final[re.Pattern[str]] = re.compile(r"^[A-Z]\d{2}(?:\.\d{1,2})?$")
_PADRAO_CNES: Final[re.Pattern[str]] = re.compile(r"^\d{7}$")

_DIGITOS_INICIAIS_CNS: Final[frozenset[str]] = frozenset("12789")
_TAMANHO_CNS: Final[int] = 15
_TAMANHO_CPF: Final[int] = 11


class CNSInvalidoError(ValueError):
    """CNS não passou na validação oficial do DATASUS."""


class CPFInvalidoError(ValueError):
    """CPF não passou na validação da Receita Federal."""


class CodigoClinicoInvalidoError(ValueError):
    """Código clínico (CIAP-2/CID-10/CNES) fora do padrão esperado."""


class ValidadorCNS:
    """Validador do dígito verificador do CNS conforme o DATASUS.

    Exemplos de uso::

        >>> ValidadorCNS("110 4332 1819 6000").e_valido
        True
    """

    def __init__(self, valor: str) -> None:
        if not isinstance(valor, str):
            raise TypeError(
                "O CNS deve ser informado como texto (str); "
                f"recebido: {type(valor).__name__}."
            )
        self._digitos: str = _PADRAO_NAO_NUMERICO.sub("", valor)

    @property
    def digitos(self) -> str:
        """CNS normalizado, contendo apenas os dígitos numéricos."""
        return self._digitos

    @property
    def e_valido(self) -> bool:
        """Valida tamanho, dígito inicial e soma ponderada (múltiplo de 11)."""
        if len(self._digitos) != _TAMANHO_CNS:
            return False
        if self._digitos[0] not in _DIGITOS_INICIAIS_CNS:
            return False
        return self._soma_ponderada() % 11 == 0

    def validar(self) -> ValidadorCNS:
        """Valida o CNS e retorna a própria instância (uso encadeado)."""
        if len(self._digitos) != _TAMANHO_CNS:
            raise CNSInvalidoError(
                "O CNS deve conter exatamente 15 dígitos numéricos; "
                f"recebidos {len(self._digitos)} dígito(s)."
            )
        if self._digitos[0] not in _DIGITOS_INICIAIS_CNS:
            raise CNSInvalidoError(
                "O CNS deve iniciar com 1, 2, 7, 8 ou 9 "
                f"(1/2 = definitivo, 7/8/9 = provisório); recebido: {self._digitos[0]}."
            )
        if self._soma_ponderada() % 11 != 0:
            raise CNSInvalidoError(
                "Dígito verificador inválido: a soma ponderada do CNS "
                "(pesos de 15 a 1) não é múltiplo de 11."
            )
        return self

    def _soma_ponderada(self) -> int:
        pesos = range(15, 0, -1)
        return sum(int(digito) * peso for digito, peso in zip(self._digitos, pesos))


def normalizar_cns(valor: str | None) -> str | None:
    """Valida o CNS e devolve o valor canônico em 15 dígitos (``None`` atravessa)."""
    if valor is None:
        return None
    return ValidadorCNS(valor).validar().digitos


def _digitos_verificadores_cpf(nove_digitos: str) -> tuple[int, int]:
    """Calcula os dois dígitos verificadores do CPF (módulo 11)."""

    def _dv(sequencia: str, peso_inicial: int) -> int:
        soma = sum(
            int(digito) * peso
            for digito, peso in zip(sequencia, range(peso_inicial, 1, -1))
        )
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    digito_1 = _dv(nove_digitos, 10)
    digito_2 = _dv(nove_digitos + str(digito_1), 11)
    return digito_1, digito_2


def normalizar_cpf(valor: str | None) -> str | None:
    """Valida o CPF (algoritmo oficial de módulo 11) e devolve 11 dígitos."""
    if valor is None:
        return None
    digitos = _PADRAO_NAO_NUMERICO.sub("", valor)
    if len(digitos) != _TAMANHO_CPF:
        raise CPFInvalidoError(
            f"O CPF deve conter exatamente {_TAMANHO_CPF} dígitos numéricos; "
            f"recebidos {len(digitos)}."
        )
    if len(set(digitos)) == 1:
        raise CPFInvalidoError("CPF inválido: todos os dígitos são iguais.")
    esperados = _digitos_verificadores_cpf(digitos[:9])
    if tuple(int(d) for d in digitos[9:]) != esperados:
        raise CPFInvalidoError("Dígitos verificadores do CPF inválidos.")
    return digitos


def normalizar_ciap2(valor: str | None) -> str | None:
    """Valida o código CIAP-2 (letra + 2 dígitos, ex.: ``K86``)."""
    if valor is None:
        return None
    codigo = valor.strip().upper()
    if not _PADRAO_CIAP2.match(codigo):
        raise CodigoClinicoInvalidoError(
            f"CIAP-2 inválido: '{valor}'. Formato esperado: letra (A-Z) seguida de 2 dígitos."
        )
    return codigo


def normalizar_cid10(valor: str | None) -> str | None:
    """Valida o código CID-10 (ex.: ``I10`` ou ``I10.9``)."""
    if valor is None:
        return None
    codigo = valor.strip().upper().replace(" ", "")
    if not _PADRAO_CID10.match(codigo):
        raise CodigoClinicoInvalidoError(
            f"CID-10 inválido: '{valor}'. Formato esperado: categoria (ex. I10) "
            "com extensão opcional (.9 / .99)."
        )
    return codigo


def normalizar_cnes(valor: str | None) -> str | None:
    """Valida o CNES do estabelecimento (7 dígitos numéricos)."""
    if valor is None:
        return None
    cnes = _PADRAO_NAO_NUMERICO.sub("", valor)
    if not _PADRAO_CNES.match(cnes):
        raise CodigoClinicoInvalidoError(
            f"CNES inválido: '{valor}'. O CNES deve conter exatamente 7 dígitos numéricos."
        )
    return cnes
