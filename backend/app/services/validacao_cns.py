"""Validação do CNS (Cartão Nacional de Saúde) — Projeto MedIA (SUS/APS).

Implementa o algoritmo oficial do Ministério da Saúde (DATASUS) para validação
do dígito verificador do CNS:

1. O CNS deve conter exatamente 15 dígitos numéricos;
2. O CNS deve iniciar com 1, 2, 7, 8 ou 9
   (1/2 = definitivo; 7/8/9 = provisório);
3. Cada dígito é multiplicado, da esquerda para a direita, pelos pesos
   15, 14, 13, ..., 1;
4. A soma ponderada dos produtos deve ser múltiplo de 11
   (resto da divisão por 11 igual a zero).

Referência: Manual de Integração do Cartão Nacional de Saúde —
Ministério da Saúde / DATASUS.

Também oferece a formatação canônica ``000 0000 0000 000``, o cálculo do
dígito verificador (15º dígito) e o tipo Pydantic v2 ``CNS``, útil em
schemas de APIs do serviço de Atenção Primária à Saúde (APS).
"""

from __future__ import annotations

import re
from typing import Annotated, Final, TypeAlias

__all__ = ["CNS", "CNSInvalidoError", "ValidadorCNS"]

try:  # pragma: no cover - depende do ambiente de execução
    from pydantic import AfterValidator

    _PYDANTIC_DISPONIVEL: Final[bool] = True
except ImportError:  # pragma: no cover - ambiente sem pydantic
    _PYDANTIC_DISPONIVEL = False


class CNSInvalidoError(ValueError):
    """Erro lançado quando o CNS informado não passa na validação oficial."""


class ValidadorCNS:
    """Validador do dígito verificador do CNS conforme o Ministério da Saúde.

    Exemplos de uso::

        >>> ValidadorCNS("110 4332 1819 6000").e_valido
        True
        >>> ValidadorCNS("110433218196000").formatar()
        '110 4332 1819 6000'
    """

    TAMANHO_CNS: Final[int] = 15
    PESO_INICIAL: Final[int] = 15
    PESO_FINAL: Final[int] = 1
    DIGITOS_INICIAIS_VALIDOS: Final[frozenset[str]] = frozenset("12789")
    DIGITOS_PROVISORIO: Final[frozenset[str]] = frozenset("789")
    PADRAO_NAO_NUMERICO: Final[re.Pattern[str]] = re.compile(r"[^0-9]")

    def __init__(self, valor: str) -> None:
        """Recebe o CNS (com ou sem pontuação) e armazena apenas os dígitos.

        Args:
            valor: CNS como texto; separadores ``.``, ``-`` e espaços são
                ignorados durante a normalização.

        Raises:
            TypeError: Se o valor informado não for uma string.
        """
        if not isinstance(valor, str):
            raise TypeError(
                "O CNS deve ser informado como texto (str); "
                f"recebido: {type(valor).__name__}."
            )
        self._digitos: str = self.PADRAO_NAO_NUMERICO.sub("", valor)

    @property
    def digitos(self) -> str:
        """CNS normalizado, contendo apenas os dígitos numéricos."""
        return self._digitos

    @property
    def e_provisorio(self) -> bool:
        """Indica se o CNS é provisório, isto é, iniciado em 7, 8 ou 9."""
        return len(self._digitos) == self.TAMANHO_CNS and self._digitos[0] in self.DIGITOS_PROVISORIO

    @property
    def e_definitivo(self) -> bool:
        """Indica se o CNS é definitivo, isto é, iniciado em 1 ou 2."""
        return (
            len(self._digitos) == self.TAMANHO_CNS
            and self._digitos[0] in self.DIGITOS_INICIAIS_VALIDOS
            and self._digitos[0] not in self.DIGITOS_PROVISORIO
        )

    @property
    def e_valido(self) -> bool:
        """Resultado completo da validação: tamanho, dígito inicial e dígito verificador."""
        if len(self._digitos) != self.TAMANHO_CNS:
            return False
        if self._digitos[0] not in self.DIGITOS_INICIAIS_VALIDOS:
            return False
        return self._soma_ponderada() % 11 == 0

    def validar(self) -> ValidadorCNS:
        """Valida o CNS e retorna a própria instância (uso encadeado).

        Raises:
            CNSInvalidoError: Se o CNS tiver tamanho, dígito inicial ou
                dígito verificador inválidos.
        """
        if len(self._digitos) != self.TAMANHO_CNS:
            raise CNSInvalidoError(
                "O CNS deve conter exatamente 15 dígitos numéricos; "
                f"recebidos {len(self._digitos)} dígito(s)."
            )
        if self._digitos[0] not in self.DIGITOS_INICIAIS_VALIDOS:
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

    def formatar(self) -> str:
        """Retorna o CNS na formatação canônica ``000 0000 0000 000``.

        Raises:
            CNSInvalidoError: Se o CNS não possuir 15 dígitos.
        """
        if len(self._digitos) != self.TAMANHO_CNS:
            raise CNSInvalidoError(
                "Não é possível formatar: o CNS deve conter 15 dígitos "
                f"(recebidos {len(self._digitos)})."
            )
        return (
            f"{self._digitos[:3]} {self._digitos[3:7]} "
            f"{self._digitos[7:11]} {self._digitos[11:]}"
        )

    @classmethod
    def calcular_digito_verificador(cls, prefixo: str) -> int:
        """Calcula o dígito verificador (15º dígito) de um prefixo de 14 dígitos.

        O DV é o único dígito que, acrescido ao prefixo com peso 1, torna a
        soma ponderada (pesos de 15 a 1) múltipla de 11.

        Args:
            prefixo: Primeiros 14 dígitos do CNS, com ou sem pontuação.

        Raises:
            CNSInvalidoError: Se o prefixo não tiver 14 dígitos ou se o DV
                calculado for igual a 10 (não representável em um dígito).
        """
        prefixo_normalizado = cls.PADRAO_NAO_NUMERICO.sub("", prefixo)
        if len(prefixo_normalizado) != cls.TAMANHO_CNS - 1:
            raise CNSInvalidoError(
                "O prefixo para cálculo do dígito verificador deve conter 14 dígitos "
                f"(recebidos {len(prefixo_normalizado)})."
            )
        soma = sum(
            int(digito) * peso
            for digito, peso in zip(prefixo_normalizado, range(cls.PESO_INICIAL, cls.PESO_FINAL, -1))
        )
        digito_verificador = (cls.PESO_FINAL * 11 - soma % 11) % 11
        if digito_verificador > 9:
            raise CNSInvalidoError(
                "O prefixo informado não admite dígito verificador válido "
                f"(dígito calculado: {digito_verificador})."
            )
        return digito_verificador

    def _soma_ponderada(self) -> int:
        """Calcula a soma ponderada dos 15 dígitos com pesos de 15 a 1."""
        pesos = range(self.PESO_INICIAL, self.PESO_FINAL - 1, -1)
        return sum(int(digito) * peso for digito, peso in zip(self._digitos, pesos))

    def __str__(self) -> str:
        """Representação textual na formatação canônica."""
        try:
            return self.formatar()
        except CNSInvalidoError:
            return self._digitos

    def __repr__(self) -> str:
        """Representação técnica do validador."""
        return f"{type(self).__name__}('{self}')"


# ---------------------------------------------------------------------------
# Tipagem estrita: integração opcional com Pydantic v2
# ---------------------------------------------------------------------------


def _normalizar_cns_valido(valor: str) -> str:
    """Valida o valor e devolve o CNS normalizado em apenas dígitos."""
    validador = ValidadorCNS(valor).validar()
    return validador.digitos


if _PYDANTIC_DISPONIVEL:  # pragma: no branch - simples: depende do ambiente
    CNS: TypeAlias = Annotated[str, AfterValidator(_normalizar_cns_valido)]
else:  # pragma: no cover - ambiente sem pydantic
    CNS: TypeAlias = str


# ---------------------------------------------------------------------------
# Testes embutidos (asserts no estilo pytest) — executáveis via __main__
# ---------------------------------------------------------------------------


def test_cns_definitivo_iniciado_em_1_e_2_e_valido() -> None:
    """CNS definitivos iniciados em 1 ou 2 devem ser aceitos."""
    for numero in ("110433218196000", "213389083863796"):
        validador = ValidadorCNS(numero)
        assert validador.e_valido is True, f"CNS {numero} deveria ser válido"
        assert validador.e_definitivo is True
        assert validador.e_provisorio is False


def test_cns_provisorio_iniciado_em_7_8_9_e_valido() -> None:
    """CNS provisórios iniciados em 7, 8 e 9 devem ser aceitos."""
    for numero in ("740265423511617", "855940781618495", "959310341316479"):
        validador = ValidadorCNS(numero)
        assert validador.e_valido is True, f"CNS provisório {numero} deveria ser válido"
        assert validador.e_provisorio is True
        assert validador.e_definitivo is False


def test_digito_verificador_invalido() -> None:
    """Alterar o último dígito deve invalidar a soma ponderada múltipla de 11."""
    validador = ValidadorCNS("110433218196001")
    assert validador.e_valido is False
    try:
        validador.validar()
        raise AssertionError("validar() deveria lançar CNSInvalidoError")
    except CNSInvalidoError as erro:
        assert "dígito verificador" in str(erro).lower()


def test_tamanho_invalido() -> None:
    """CNS com menos ou mais de 15 dígitos deve ser rejeitado."""
    for numero in ("11043321819600", "1104332181960000"):
        validador = ValidadorCNS(numero)
        assert validador.e_valido is False
        try:
            validador.validar()
            raise AssertionError("validar() deveria lançar CNSInvalidoError")
        except CNSInvalidoError as erro:
            assert "15 dígitos" in str(erro)


def test_digito_inicial_invalido() -> None:
    """CNS não pode iniciar com 0, 3, 4, 5 ou 6."""
    for numero in ("300000000000000", "400000000000000", "500000000000000", "600000000000000"):
        validador = ValidadorCNS(numero)
        assert validador.e_valido is False
        try:
            validador.validar()
            raise AssertionError("validar() deveria lançar CNSInvalidoError")
        except CNSInvalidoError as erro:
            assert "iniciar com 1, 2, 7, 8 ou 9" in str(erro)


def test_normalizacao_da_entrada() -> None:
    """Separadores '.', '-' e espaços devem ser removidos antes da validação."""
    validador = ValidadorCNS("  110.4332.1819-6000  ")
    assert validador.digitos == "110433218196000"
    assert validador.e_valido is True


def test_formatacao_canonica() -> None:
    """A formatação canônica deve seguir o padrão 000 0000 0000 000."""
    assert ValidadorCNS("110433218196000").formatar() == "110 4332 1819 6000"
    assert ValidadorCNS("110.4332.1819-6000").formatar() == "110 4332 1819 6000"
    assert str(ValidadorCNS("855940781618495")) == "855 9407 8161 8495"


def test_validar_retorna_instancia_para_encadeamento() -> None:
    """validar() deve retornar a própria instância, permitindo encadeamento."""
    assert ValidadorCNS("110433218196000").validar().formatar() == "110 4332 1819 6000"


def test_calculo_do_digito_verificador() -> None:
    """O DV calculado para o prefixo deve corresponder ao 15º dígito do CNS."""
    assert ValidadorCNS.calcular_digito_verificador("11043321819600") == 0
    assert ValidadorCNS.calcular_digito_verificador("74026542351161") == 7
    assert ValidadorCNS.calcular_digito_verificador("11200000000000") == 0
    completo = f"89870000000000{ValidadorCNS.calcular_digito_verificador('89870000000000')}"
    assert completo == "898700000000006"
    assert ValidadorCNS(completo).e_valido is True


def test_digito_verificador_dez_nao_representavel() -> None:
    """Prefixo cujo dígito calculado é 10 não admite DV válido (falha explícita)."""
    try:
        ValidadorCNS.calcular_digito_verificador("10000300000000")
        raise AssertionError("deveria lançar CNSInvalidoError (DV calculado = 10)")
    except CNSInvalidoError as erro:
        assert "dígito" in str(erro).lower()


def test_tipo_de_entrada_invalida() -> None:
    """Entradas que não sejam texto devem gerar TypeError (tipagem estrita)."""
    for valor in (None, 123, 15.0, ["110433218196000"]):
        try:
            ValidadorCNS(valor)  # type: ignore[arg-type]
            raise AssertionError("deveria lançar TypeError")
        except TypeError as erro:
            assert "str" in str(erro)


def test_integracao_pydantic_v2() -> None:
    """O tipo CNS deve validar e normalizar valores em modelos Pydantic v2."""
    if not _PYDANTIC_DISPONIVEL:
        print("(pulado — pydantic não instalado no ambiente)")
        return
    from pydantic import BaseModel, ValidationError

    class Paciente(BaseModel):
        cns: CNS

    paciente = Paciente.model_validate({"cns": "110 4332 1819 6000"})
    assert paciente.cns == "110433218196000"
    try:
        Paciente.model_validate({"cns": "110433218196001"})
        raise AssertionError("Paciente deveria recusar CNS inválido")
    except ValidationError:
        pass


if __name__ == "__main__":
    testes = [
        funcao
        for nome, funcao in sorted(globals().items())
        if nome.startswith("test_") and callable(funcao)
    ]
    falhas = 0
    for teste in testes:
        try:
            teste()
            print(f"[OK] {teste.__name__}")
        except AssertionError as erro:
            falhas += 1
            print(f"[FALHA] {teste.__name__}: {erro}")
    if falhas:
        raise SystemExit(f"{falhas} teste(s) falharam.")
    print(f"\n{len(testes)} teste(s) executado(s) com sucesso.")
