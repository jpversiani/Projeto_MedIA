"""Criptografia em repouso para identificadores pessoais (CPF e CNS).

Problema corrigido (P0-7): `cidadaos.cpf`, `cidadaos.cns`, `profissionais.cpf` e
`profissionais.cns` eram `VARCHAR` em texto claro. Um vazamento de banco ou de
backup expunha a identificação de todos os pacientes — dado pessoal sensível
art. 5º II + art. 46 da LGPD — sem qualquer barreira.

P0-7b estende o mesmo tratamento às **cópias** desses documentos espalhadas em
tabelas operacionais (receita, dispensação, guia TISS, livro caixa, jornada,
contingência offline, mensageria, teleconsulta): `CampoProtegido` para as
colunas de texto, `TextoProtegido` para conteúdo longo (`xml_tiss`),
`JsonProtegido` para os campos embutidos em payloads JSON.

Modelo adotado:

* **Cifra (AES-256-GCM)** para leitura: aleatória por registro (nonce novo a
  cada gravação). É o que entra na coluna.
* **Índice cego (HMAC-SHA-256)** para busca e unicidade: determinístico, não
  reversível sem a chave. Sem ele, `WHERE cpf = ?` deixaria de funcionar, pois
  o mesmo CPF cifrado gera textos diferentes.

Formato da coluna: ``enc:v1:<base64url(nonce(12) + ciphertext + tag)>``.

Valores sem o prefixo são tratados como texto claro legado — é o que permite
subir o código antes de rodar a migração de dados sem quebrar a leitura.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
from typing import Optional, Sequence

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from sqlalchemy import JSON, String, Text, TypeDecorator
from sqlalchemy.sql import operators as _ops
from sqlalchemy.sql.elements import ColumnElement

PREFIXO = "enc:v1:"
TAMANHO_NONCE = 12
TAMANHO_MAXIMO_COLUNA = 255

_PADRAO_NAO_DIGITO = re.compile(r"\D")


class ErroCriptografia(RuntimeError):
    """Chave errada ou dado corrompido — deve falhar alto, nunca em silêncio."""


# ---------------------------------------------------------------------------
# Chaves
# ---------------------------------------------------------------------------
def _chaves() -> tuple[bytes, bytes]:
    """Deriva (chave de cifra, chave de HMAC) a partir da configuração.

    Import tardio de ``settings`` para evitar ciclo: ``config`` é importado por
    quase tudo e não deve depender deste módulo.
    """
    from app.core.config import settings

    segredo = settings.FIELD_ENCRYPTION_KEY or settings.effective_secret_key
    base = segredo.encode("utf-8")

    chave_cifra = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"media.campos.v1",
        info=b"aes-256-gcm",
    ).derive(base)
    chave_hash = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"media.campos.v1",
        info=b"hmac-busca",
    ).derive(base)
    return chave_cifra, chave_hash


# ---------------------------------------------------------------------------
# Cifra
# ---------------------------------------------------------------------------
def cifrar(valor: Optional[str]) -> Optional[str]:
    """Cifra um valor. ``None`` e string vazia atravessam."""
    if valor is None:
        return None
    texto = str(valor)
    if not texto:
        return texto
    if texto.startswith(PREFIXO):
        # Já cifrado: evita cifrar duas vezes em re-save.
        return texto

    chave, _ = _chaves()
    nonce = os.urandom(TAMANHO_NONCE)
    criptografado = AESGCM(chave).encrypt(nonce, texto.encode("utf-8"), None)
    return PREFIXO + base64.urlsafe_b64encode(nonce + criptografado).decode("ascii")


def decifrar(valor: Optional[str]) -> Optional[str]:
    """Decifra; devolve texto claro legado sem prefixo como está."""
    if valor is None:
        return None
    texto = str(valor)
    if not texto.startswith(PREFIXO):
        return texto

    chave, _ = _chaves()
    bruto = base64.urlsafe_b64decode(texto[len(PREFIXO) :].encode("ascii"))
    nonce, criptografado = bruto[:TAMANHO_NONCE], bruto[TAMANHO_NONCE:]
    try:
        return AESGCM(chave).decrypt(nonce, criptografado, None).decode("utf-8")
    except InvalidTag as exc:  # pragma: no cover - depende de chave errada
        raise ErroCriptografia(
            "Não foi possível decifrar o campo: a chave atual não corresponde à "
            "usada na gravação (FIELD_ENCRYPTION_KEY alterada?)."
        ) from exc


# ---------------------------------------------------------------------------
# Índice cego (busca/unicidade)
# ---------------------------------------------------------------------------
def somente_digitos(valor: Optional[str]) -> Optional[str]:
    if valor is None:
        return None
    digitos = _PADRAO_NAO_DIGITO.sub("", str(valor))
    return digitos or None


def hash_busca(valor: Optional[str]) -> Optional[str]:
    """HMAC-SHA-256 hex dos dígitos do documento (índice cego)."""
    digitos = somente_digitos(valor)
    if digitos is None:
        return None
    _, chave_hash = _chaves()
    return hmac.new(chave_hash, digitos.encode("utf-8"), hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# Tipo SQLAlchemy
# ---------------------------------------------------------------------------
# Operadores que nunca funcionam sobre um campo cifrado: a cifra não preserva
# a estrutura do documento e o índice cego é HMAC do valor completo (não do
# prefixo). Usá-los devolveria sempre vazio, em silêncio.
_OPS_BUSCA_PARCIAL = (
    _ops.like_op,
    _ops.not_like_op,
    _ops.ilike_op,
    _ops.not_ilike_op,
    _ops.startswith_op,
    _ops.not_startswith_op,
    _ops.istartswith_op,
    _ops.not_istartswith_op,
    _ops.endswith_op,
    _ops.not_endswith_op,
    _ops.iendswith_op,
    _ops.not_iendswith_op,
    _ops.contains_op,
    _ops.not_contains_op,
    _ops.icontains_op,
    _ops.not_icontains_op,
)

_OPS_IGUALDADE = (_ops.eq, _ops.ne, _ops.in_op, _ops.notin_op)


class ComparadorProtegido(TypeDecorator.Comparator):
    """Traduz ``coluna == "123"`` para ``coluna_hash == hmac("123")``.

    Sem isto, toda consulta existente (``Cidadao.cpf == cpf``) compararia o
    texto claro com o ciphertext e nunca encontraria ninguém — obrigando a
    reescrever cada ponto de busca e deixando os esquecidos quebrados em
    silêncio. A comparação correta fica no próprio tipo.

    **Falha alto** quando a comparação não tem como dar certo, em vez de
    devolver resultado vazio (que o chamador leria como "registro não
    existe"):

    * igualdade/``IN`` em coluna cifrada **sem** o índice cego ``<col>_hash``:
      o ciphertext é aleatório por gravação e o texto claro nunca casaria;
    * busca parcial (``LIKE``/``startswith``/``contains``): o índice cego é
      HMAC do documento inteiro, então nem ele preserva prefixo;
    * literal de tipo errado (``cpf == 123``): SQL compararia inteiros com
      ciphertext.

    As cópias de CPF/CNS em tabelas operacionais (P0-7b) são cifradas **sem**
    coluna de hash — nenhuma consulta do sistema filtra por elas —, então a
    primeira categoria é exatamente o que protege um futuro ``where`` contra
    um erro silencioso.
    """

    def _coluna_hash(self):
        elemento = self.__clause_element__()
        tabela = getattr(elemento, "table", None)
        if tabela is None or f"{elemento.name}_hash" not in tabela.c:
            return None
        return tabela.c[f"{elemento.name}_hash"]

    def operate(self, op, *other, **kwargs):
        coluna_hash = self._coluna_hash()
        valor = other[0] if other else None
        nome = getattr(self.__clause_element__(), "name", "campo cifrado")

        if op in _OPS_BUSCA_PARCIAL:
            raise ErroCriptografia(
                f"Busca parcial sobre a coluna cifrada '{nome}': ciphertext "
                "não preserva a estrutura do documento e o índice cego é HMAC "
                "do valor completo — o resultado seria sempre vazio. Use "
                "igualdade (== / IN), traduzida para o índice cego, ou "
                "busque por outro campo (ex.: nome)."
            )

        # `IS [NOT] NULL` (valor None) e comparações entre colunas não
        # dependem do hash e seguem adiante normalmente.
        literal = valor is not None and not isinstance(valor, ColumnElement)
        if literal and op in _OPS_IGUALDADE:
            colecao = isinstance(valor, (list, tuple, set))
            eh_operacao_de_lista = op in (_ops.in_op, _ops.notin_op)
            # Diagnóstico antes de tudo: dizer "crie o _hash" para um valor de
            # tipo errado (``cpf == 123``) apontaria a correção errada.
            tipo_correto = colecao if eh_operacao_de_lista else isinstance(valor, str)
            if not tipo_correto:
                raise ErroCriptografia(
                    f"A coluna cifrada '{nome}' é comparada por texto; o valor "
                    f"{valor!r} ({type(valor).__name__}) não é um CPF/CNS. "
                    "Passe a string do documento."
                )
            if coluna_hash is None:
                raise ErroCriptografia(
                    f"A coluna cifrada '{nome}' não tem a coluna de índice cego "
                    f"'{nome}_hash' nesta tabela: comparar texto claro com o "
                    "ciphertext casaria com nenhuma linha. Crie a coluna "
                    f"'{nome}_hash' (String(64), indexada) e a migração de dados, "
                    "ou consulte por outro identificador (ex.: id)."
                )
            if isinstance(valor, str):
                indice = hash_busca(valor)
                if op is _ops.eq:
                    return coluna_hash == indice
                return coluna_hash != indice
            indices = [hash_busca(item) for item in valor]
            if op is _ops.in_op:
                return coluna_hash.in_(indices)
            return coluna_hash.notin_(indices)

        return super().operate(op, *other, **kwargs)


class CampoProtegido(TypeDecorator):
    """Coluna cifrada de forma transparente para o restante do código.

    O ORM lê e grava texto claro; o banco guarda o ciphertext. Igualdade e
    ``IN`` são traduzidos para o índice cego (``<coluna>_hash``) — buscas
    parciais (``LIKE``/``ilike``) não funcionam sobre ciphertext e levantam
    ``ErroCriptografia`` ao serem tentadas.
    """

    impl = String(TAMANHO_MAXIMO_COLUNA)
    cache_ok = True
    comparator_factory = ComparadorProtegido

    def process_bind_param(self, value, dialect):
        return cifrar(value)

    def process_result_value(self, value, dialect):
        return decifrar(value)


class TextoProtegido(CampoProtegido):
    """Coluna ``Text`` cifrada (conteúdo longo, ex.: ``guias_tiss.xml_tiss``).

    Mesma semântica do :class:`CampoProtegido`, apenas com ``impl`` compatível
    com colunas de texto longo — o XML TISS tem CPF, CNS e CID dentro e não
    cabe em ``VARCHAR(255)``.
    """

    impl = Text
    cache_ok = True


def _processar_json(valor, campos, operacao):
    """Aplica ``operacao`` (cifrar/decifrar) aos campos indicados de um dict.

    Não muta o dicionário recebido: o mesmo payload é reutilizado (reemissão
    de PDF, hash de integridade) e não pode herdar ciphertext por engano.
    """
    if not isinstance(valor, dict) or not campos:
        return valor
    copia = dict(valor)
    alterado = False
    for campo in campos:
        atual = copia.get(campo)
        if isinstance(atual, str) and atual:
            copia[campo] = operacao(atual)
            alterado = True
    return copia if alterado else valor


class JsonProtegido(TypeDecorator):
    """Coluna JSON com campos pessoais cifrados individualmente.

    ``documentos_clinicos.payload_json`` e ``jornadas_atendimento.dados_json``
    guardam o CPF ao lado de itens clínicos, checklist e do hash de
    integridade. Cifrar o JSON inteiro quebraria a leitura desses vizinhos e a
    recomputação do hash; aqui só os campos listados em ``campos`` viram
    ciphertext, de forma transparente ao ORM.
    """

    impl = JSON
    cache_ok = True

    def __init__(self, campos: Sequence[str] = ()):
        super().__init__()
        self.campos = tuple(campos)

    def process_bind_param(self, value, dialect):
        return _processar_json(value, self.campos, cifrar)

    def process_result_value(self, value, dialect):
        return _processar_json(value, self.campos, decifrar)
