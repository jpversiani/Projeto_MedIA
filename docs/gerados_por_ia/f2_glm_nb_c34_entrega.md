 The user wants a Python service file for cryptographic validation of digital prescriptions (Receita Digital) for a SUS/APS project. Need to create backend/app/services/receita_digital.py with SHA-256 canonical hash, digital signature, verification. Strict typing, Pydantic v2, SQLAlchemy 2.0 patterns, plus pytest tests.

I'll produce:
1. `backend/app/services/receita_digital.py` — main service with Pydantic models (PrescricaoDigital, ItemPrescricao), canonical JSON serialization, SHA-256 hash, Ed25519 signing (cryptography library), verification, tamper detection for dosages/medications.
2. Maybe a models file for SQLAlchemy 2.0 (ReceitaDigital table).
3. Tests file with pytest.

Use Ed25519 via `cryptography` library. Canonical JSON: sorted keys, separators, ensure_ascii=False, normalize decimals (dosage as string or Decimal normalized). Include CNS/CPF identifiers.

Let me write clean, well-documented code in Portuguese comments/docstrings.

Key design:
- `ItemPrescricao(BaseModel)`: codigo_anvisa/tuiss? Use medication code, nome, dosagem (Decimal), unidade, quantidade, via_administracao, posologia.
- `PrescricaoDigital(BaseModel)`: id, paciente_cns, profissional_cns, cpf optional, cid10, ciap2, data_emissao, itens, modelo SOAP? Maybe campo "evolucao_soap" not needed. Keep focused.
- canonical_json(prescricao) -> str: normalized dict with Decimal as string with fixed format, sorted keys.
- calcular_hash(prescricao) -> str hex.
- assinar_prescricao(prescricao, private_key) -> AssinaturaDigital containing hash, signature base64, algorithm, timestamp.
- verificar_integridade(prescricao, assinatura, public_key) -> ResultadoVerificacao with flags: hash_valido, assinatura_valida, adulteracoes detectadas (compare dosagens/medicamentos).

Tamper detection: recompute hash of received prescription vs stored hash; if mismatch, identify which fields differ by comparing canonical dicts — detect changes in dosagem or medicamento specifically.

SQLAlchemy 2.0 model: ReceitaDigitalORM with Mapped, mapped_column, storing hash, signature, payload JSON.

Tests: generate keys, sign, verify ok; tamper dosage -> detect; tamper medication -> detect; wrong key -> invalid; canonical determinism (key order irrelevant).

Write code. Keep reasonably concise but complete.# Serviço de Validação Criptográfica de Receita Digital (C34)

Abaixo a implementação completa do serviço, o modelo de persistência SQLAlchemy 2.0 e a suíte de testes pytest.

## 1. Serviço principal

**`backend/app/services/receita_digital.py`**

```python
"""
Serviço de Validação Criptográfica de Receita Digital (C34) — Projeto MedIA.

Implementa o ciclo criptográfico da Receita Digital no contexto do SUS/APS:

1. Canonicalização determinística da prescrição (JSON canônico RFC 8785-like).
2. Geração de hash SHA-256 sobre a representação canônica.
3. Assinatura digital Ed25519 (RFC 8032) pelo profissional prescritor.
4. Verificação de integridade na dispensação, com detecção de adulteração
   de dosagens e/ou medicamentos (conforme RDC 356/2020 — e-Receita BPA).

Conformidade:
- Identificação do paciente por CNS (Cartão Nacional de Saúde) ou CPF.
- Codificação de diagnóstico por CID-10 e/ou CIAP-2.
- Prescrição estruturada compatível com o método SOAP (campo `soap_s`).

Python 3.12 | Pydantic v2 | SQLAlchemy 2.0 | cryptography >= 42
"""

from __future__ import annotations

import base64
import hashlib
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Final, Literal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

__all__ = [
    "AlgoritmoAssinatura",
    "ItemPrescricao",
    "PrescricaoDigital",
    "AssinaturaDigital",
    "ResultadoVerificacao",
    "TipoAdulteracao",
    "canonicalizar_prescricao",
    "calcular_hash",
    "gerar_par_chaves",
    "assinar_prescricao",
    "verificar_integridade",
    "detectar_adulteracoes",
]

# ---------------------------------------------------------------------------
# Constantes e enums
# ---------------------------------------------------------------------------

ALGORITMO_HASH: Final[str] = "SHA-256"
ALGORITMO_ASSINATURA: Final[str] = "Ed25519"
VERSAO_ESQUEMA: Final[str] = "1.0.0"

CAMPOS_INTEGRIDADE: Final[tuple[str, ...]] = (
    "paciente_cns",
    "paciente_cpf",
    "profissional_cns",
    "cid10",
    "ciap2",
    "itens",
)


class AlgoritmoAssinatura(str, Enum):
    """Algoritmos suportados para assinatura da receita digital."""

    ED25519 = "Ed25519"


class TipoAdulteracao(str, Enum):
    """Classificação das adulterações detectadas na verificação."""

    DOSAGEM = "DOSAGEM"
    MEDICAMENTO = "MEDICAMENTO"
    QUANTIDADE = "QUANTIDADE"
    POSOLOGIA = "POSOLOGIA"
    PACIENTE = "PACIENTE"
    PRESCRITOR = "PRESCRITOR"
    DIAGNOSTICO = "DIAGNOSTICO"
    OUTRO = "OUTRO"


# ---------------------------------------------------------------------------
# Modelos Pydantic v2 (domínio)
# ---------------------------------------------------------------------------


class ItemPrescricao(BaseModel):
    """Item (medicamento) prescrito, com dosagem estruturada."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    codigo_medicamento: str = Field(
        ...,
        min_length=6,
        max_length=20,
        description="Código do medicamento (CATMAT/ANVISA/TUSS).",
    )
    nome_medicamento: str = Field(
        ..., min_length=2, max_length=255, description="Nome comercial/genérico."
    )
    principio_ativo: str = Field(
        ..., min_length=2, max_length=255, description="Denominação Genérica Brasileira (DGB)."
    )
    dosagem: Decimal = Field(
        ...,
        gt=Decimal("0"),
        description="Dosagem por unidade de administração (ex.: 500.00 mg).",
    )
    unidade_dosagem: Literal["mg", "mcg", "g", "mL", "UI", "UI/mL", "mg/mL", "%"] = Field(...)
    via_administracao: Literal[
        "ORAL", "TOPICA", "SUBCUTANEA", "INTRAMUSCULAR", "INTRAVENOSA",
        "INALATORIA", "OFTALMOLOGICA", "RETAL", "NASAL", "SUBLINGUAL",
    ] = Field(...)
    quantidade: int = Field(..., gt=0, le=1000, description="Quantidade dispensável.")
    posologia: str = Field(
        ..., min_length=3, max_length=500, description="Instruções de uso (frequência/duração)."
    )
    uso_continuo: bool = Field(default=False, description="Medicamento de uso contínuo (SUS).")

    @field_validator("dosagem", mode="before")
    @classmethod
    def _normalizar_dosagem(cls, v: Any) -> Decimal:
        """Aceita string ou numérico; converte para Decimal com 4 casas."""
        d = Decimal(str(v))
        return d.quantize(Decimal("0.0001"))


class PrescricaoDigital(BaseModel):
    """Receita Digital estruturada (padrão e-Receita SUS/APS)."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    id_prescricao: uuid.UUID = Field(default_factory=uuid.uuid4)
    versao_esquema: str = Field(default=VERSAO_ESQUEMA, frozen=True)

    # --- Identificação do paciente (CNS obrigatório; CPF opcional) ---
    paciente_cns: str = Field(..., pattern=r"^\d{15}$", description="CNS do paciente (15 dígitos).")
    paciente_cpf: str | None = Field(
        default=None, pattern=r"^\d{11}$", description="CPF do paciente (11 dígitos, opcional)."
    )

    # --- Identificação do prescritor ---
    profissional_cns: str = Field(..., pattern=r"^\d{15}$", description="CNS do prescritor.")
    cnes_estabelecimento: str = Field(
        ..., pattern=r"^\d{7}$", description="CNES da UBS/APS emissora."
    )

    # --- Contexto clínico (SOAP / CID-10 / CIAP-2) ---
    cid10: str | None = Field(
        default=None, pattern=r"^[A-TV-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$", description="CID-10."
    )
    ciap2: str | None = Field(
        default=None, pattern=r"^[A-Z]{1}[-][0-9]{2}$", description="CIAP-2 (ex.: R-05)."
    )
    soap_s: str | None = Field(default=None, max_length=4000, description="SOAP — Subjetivo.")
    soap_a: str | None = Field(default=None, max_length=4000, description="SOAP — Avaliação.")

    itens: tuple[ItemPrescricao, ...] = Field(..., min_length=1, max_length=20)
    data_emissao: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Momento da emissão (UTC).",
    )

    @field_validator("paciente_cns", "profissional_cns")
    @classmethod
    def _validar_cns(cls, v: str) -> str:
        """Valida dígito verificador do CNS (algoritmo oficial DATASUS)."""
        if not _cns_valido(v):
            raise ValueError(f"CNS inválido (dígito verificador): {v}")
        return v

    @field_validator("paciente_cpf")
    @classmethod
    def _validar_cpf(cls, v: str | None) -> str | None:
        if v is not None and not _cpf_valido(v):
            raise ValueError(f"CPF inválido (dígito verificador): {v}")
        return v

    @model_validator(mode="after")
    def _validar_diagnostico(self) -> PrescricaoDigital:
        """Exige ao menos um diagnóstico codificado (CID-10 ou CIAP-2)."""
        if self.cid10 is None and self.ciap2 is None:
            raise ValueError("Prescrição exige CID-10 e/ou CIAP-2.")
        return self


class AssinaturaDigital(BaseModel):
    """Envelope de assinatura anexado à prescrição."""

    model_config = ConfigDict(frozen=True)

    id_prescricao: uuid.UUID
    hash_conteudo: str = Field(..., pattern=r"^[a-f0-9]{64}$", description="SHA-256 hex.")
    assinatura_base64: str = Field(..., description="Assinatura Ed25519 em Base64.")
    algoritmo_hash: str = Field(default=ALGORITMO_HASH, frozen=True)
    algoritmo_assinatura: AlgoritmoAssinatura = Field(
        default=AlgoritmoAssinatura.ED25519, frozen=True
    )
    assinado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    versao_esquema: str = Field(default=VERSAO_ESQUEMA, frozen=True)


class ResultadoVerificacao(BaseModel):
    """Resultado da verificação de integridade na dispensação."""

    model_config = ConfigDict(frozen=True)

    id_prescricao: uuid.UUID
    hash_recalculado: str
    hash_original: str
    hash_valido: bool
    assinatura_valida: bool
    integro: bool
    adulteracoes: tuple[TipoAdulteracao, ...] = Field(default_factory=tuple)
    detalhes: tuple[str, ...] = Field(default_factory=tuple)
    verificado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Utilitários de validação de identificadores (DATASUS / Receita Federal)
# ---------------------------------------------------------------------------


def _cns_valido(cns: str) -> bool:
    """Valida CNS pelo algoritmo oficial (somas ponderadas 15/14/13...2)."""
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] in "012":
        # CNS definitivo: 1/2 (usuário) ou 7/8/9 (profissional) — 15 dígitos DV.
        pesos = range(15, 1, -1)
        soma = sum(int(d) * p for d, p in zip(cns[:11], pesos[:11]))
        resto = soma % 11
        dv = 0 if resto < 2 else 11 - resto
        return cns[11] == str(dv) and int(cns[12:15]) == 0 if False else _cns_definitivo_valido(cns)
    return False


def _cns_definitivo_valido(cns: str) -> bool:
    """Validação dos 12 primeiros dígitos + 3 dígitos de verificação (000)."""
    if cns[12:15] != "000":
        return False
    soma = sum(int(d) * p for d, p in zip(cns[:12], range(15, 3, -1)))
    resto = soma % 11
    dv = 0 if resto < 2 else 11 - resto
    return cns[11] == str(dv)


def _cpf_valido(cpf: str) -> bool:
    """Valida CPF pelos dígitos verificadores (algoritmo Receita Federal)."""
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for n in (9, 10):
        soma = sum(int(cpf[i]) * (n + 1 - i) for i in range(n))
        dv = (soma * 10) % 11 % 10
        if int(cpf[n]) != dv:
            return False
    return True


# ---------------------------------------------------------------------------
# 1) Canonicalização e hash
# ---------------------------------------------------------------------------


def _decimal_canonico(d: Decimal) -> str:
    """Serializa Decimal de forma determinística (notação fixa, sem zeros à direita)."""
    s = format(d.normalize(), "f")
    return s


def _para_dict_canonico(obj: Any) -> Any:
    """Converte recursivamente o modelo para uma estrutura JSON-canônica."""
    if isinstance(obj, BaseModel):
        return _para_dict_canonico(obj.model_dump(mode="python"))
    if isinstance(obj, dict):
        return {k: _para_dict_canonico(v) for k, v in sorted(obj.items()) if v is not None}
    if isinstance(obj, (tuple, list)):
        return [_para_dict_canonico(v) for v in obj]
    if isinstance(obj, Decimal):
        return _decimal_canonico(obj)
    if isinstance(obj, datetime):
        return obj.astimezone(timezone.utc).isoformat(timespec="milliseconds")
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    return obj


def canonicalizar_prescricao(prescricao: PrescricaoDigital) -> str:
    """
    Gera a representação canônica (string JSON) da prescrição.

    Propriedades garantidas:
    - Chaves ordenadas lexicograficamente.
    - Separadores compactos (',' e ':').
    - Decimais em notação fixa determinística.
    - Datas em UTC ISO-8601 com precisão de milissegundos.
    - Campos nulos omitidos.
    """
    return json.dumps(
        _para_dict_canonico(prescricao),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def calcular_hash(prescricao: PrescricaoDigital) -> str:
    """Calcula o hash SHA-256 (hex, minúsculo) da prescrição canônica."""
    canonico = canonicalizar_prescricao(prescricao)
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# 2) Geração de chaves e assinatura
# ---------------------------------------------------------------------------


def gerar_par_chaves() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """
    Gera um par de chaves Ed25519 para o prescritor.

    Em produção, a chave privada deve residir em HSM/certificado ICP-Brasil
    (A1/A3); esta função destina-se ao serviço e aos testes automatizados.
    """
    private_key = Ed25519PrivateKey.generate()
    return private_key, private_key.public_key()


def _serializar_chave_publica(public_key: Ed25519PublicKey) -> str:
    """Serializa a chave pública em Base64 (raw, 32 bytes)."""
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode("ascii")


def _desserializar_chave_publica(public_key_b64: str) -> Ed25519PublicKey:
    """Reconstrói a chave pública Ed25519 a partir de Base64 raw."""
    raw = base64.b64decode(public_key_b64, validate=True)
    if len(raw) != 32:
        raise ValueError("Chave pública Ed25519 deve ter 32 bytes.")
    return Ed25519PublicKey.from_public_bytes(raw)


