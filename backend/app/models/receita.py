"""Modelos de domínio da Receita Digital (padrões SUS/APS).

Define a prescrição eletrônica assinável do PEC OpenSUS: identificação do
cidadão por CNS/CPF, codificação do episódio por CID-10 e CIAP-2, lista de
medicamentos prescritos e metadados criptográficos (hash do documento e
assinatura digital) preenchidos pelo serviço de validação criptográfica
(``app.services.receita_digital``).

Projeto MedIA — SUS/APS (Python 3.12, Pydantic v2).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

REGEX_CID10: Final[str] = r"^[A-Za-z]\d{2}(\.\d{1,2})?$"
REGEX_CIAP2: Final[str] = r"^[A-Za-z]\d{2}$"


class Medicamento(BaseModel):
    """Item de prescrição: fármaco, dosagem, posologia e quantidade."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=1)
    dosagem: str = Field(min_length=1)
    frequencia: str = Field(min_length=1)
    quantidade: int = Field(ge=1)


class ReceitaDigital(BaseModel):
    """Prescrição digital do SUS pronta para hash canônico e assinatura HMAC.

    Os campos ``hash_assinatura``, ``assinatura``, ``algoritmo_assinatura`` e
    ``data_assinatura`` são metadados de integridade e são EXCLUÍDOS do hash
    canônico do conteúdo clínico pelo serviço de validação criptográfica.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    cns_paciente: str = Field(min_length=15, max_length=15)
    cpf_paciente: str = Field(min_length=11, max_length=11)
    cid10: str = Field(pattern=REGEX_CID10)
    ciap2: str = Field(pattern=REGEX_CIAP2)
    data_emissao: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    medicamentos: list[Medicamento] = Field(default_factory=list)
    observacoes: str = ""
    hash_assinatura: str | None = None
    assinatura: str | None = None
    algoritmo_assinatura: str | None = None
    data_assinatura: datetime | None = None