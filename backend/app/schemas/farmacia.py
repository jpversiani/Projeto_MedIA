"""Schemas Pydantic v2 da Dispensação Farmacêutica (C34 — SUS/APS).

Contratos de entrada e saída das rotas ``POST /dispensacao/consultar`` e
``POST /dispensacao/confirmar``: validação do QR Code/hash da receita e
registro de baixa total ou fracionada, com identificação do farmacêutico
(CNS/CPF — algoritmos oficiais DATASUS/Receita Federal) e do estabelecimento
dispensador (CNES).

Projeto MedIA — SUS/APS (Python 3.12, Pydantic v2).
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Annotated, Final, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.services.validadores import normalizar_cnes, normalizar_cns, normalizar_cpf

# Hash SHA-256 em hex minúsculo (conteúdo do QR Code da receita digital)
REGEX_HASH_RECEITA: Final[str] = r"^[a-f0-9]{64}$"

TipoDispensacao = Literal["TOTAL", "FRACIONADA"]
StatusReceita = Literal[
    "EMITIDA", "PARCIALMENTE_DISPENSADA", "DISPENSADA", "CANCELADA"
]

CNSFarmaceutico = Annotated[str, AfterValidator(normalizar_cns)]
CPFOpcional = Annotated[str | None, AfterValidator(normalizar_cpf)]
CNESFarmacia = Annotated[str, AfterValidator(normalizar_cnes)]


def _normalizar_hash(valor: str) -> str:
    """Exige hash SHA-256 (64 caracteres hexadecimais) do QR Code da receita."""
    hash_normalizado = valor.strip().lower()
    if len(hash_normalizado) != 64 or any(c not in "0123456789abcdef" for c in hash_normalizado):
        raise ValueError(
            "Hash do QR Code inválido: esperado SHA-256 em hexadecimal "
            f"com 64 caracteres; recebido {len(hash_normalizado)} caractere(s)."
        )
    return hash_normalizado


HashReceita = Annotated[str, AfterValidator(_normalizar_hash)]


class DispensacaoConsultarIn(BaseModel):
    """Entrada da consulta do QR Code/hash da receita digital."""

    model_config = ConfigDict(str_strip_whitespace=True)

    codigo_hash: HashReceita = Field(
        description="Hash SHA-256 (hex, 64 caracteres) contido no QR Code da receita"
    )


class ItemReceitaOut(BaseModel):
    """Item prescrito da receita com o saldo remanescente para dispensação."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    medicamento: str = Field(description="Fármaco/princípio ativo prescrito")
    dosagem: str = Field(description="Concentração/apresentação (ex.: 500 mg)")
    posologia: str = Field(description="Posologia (ex.: 1 comprimido de 8/8h por 7 dias)")
    quantidade_prescrita: int = Field(ge=1)
    quantidade_dispensada: int = Field(ge=0)
    saldo_remanescente: int = Field(ge=0)
    dispensavel: bool = Field(description="Se ainda há saldo para baixa deste item")


class DispensacaoConsultarOut(BaseModel):
    """Resposta da validação do QR Code/hash da receita na farmácia."""

    model_config = ConfigDict(from_attributes=True)

    receita_id: int
    codigo_hash: str
    status: StatusReceita
    dispensavel: bool = Field(description="Se a receita admite baixa (total ou fracionada)")
    motivo_bloqueio: str | None = Field(
        None,
        description="Motivo da impossibilidade (cancelada, vencida, dispensada ou adulterada)",
    )

    # Identificação SUS do paciente
    cns_paciente: str = Field(description="CNS do paciente (15 dígitos)")
    cpf_paciente: str | None = None

    # Episódio clínico (terminologias SUS/APS)
    cid10: str | None = None
    ciap2: str | None = None

    # Prescritor e emissão
    prescritor_nome: str
    prescritor_cns: str
    prescritor_registro: str = Field(description="Registro no conselho profissional (CRM/COREN)")
    unidade_cnes: str = Field(description="CNES da unidade emissora")
    data_emissao: datetime
    data_validade: date

    itens: list[ItemReceitaOut] = Field(description="Itens prescritos com saldo remanescente")


class ItemDispensacaoIn(BaseModel):
    """Baixa solicitada para um item da receita."""

    model_config = ConfigDict(str_strip_whitespace=True)

    receita_item_id: int = Field(ge=1, description="Identificador do item na receita")
    quantidade: int = Field(ge=1, description="Quantidade a dispensar neste evento")
    lote: str | None = Field(None, max_length=30, description="Lote do medicamento")
    validade_lote: date | None = Field(None, description="Validade do lote informado")


class FarmaceuticoIn(BaseModel):
    """Identificação do farmacêutico dispensador (trilha de auditoria SUS)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=3, max_length=200)
    cns: CNSFarmaceutico = Field(description="CNS do farmacêutico (15 dígitos, DV oficial)")
    cpf: CPFOpcional = Field(None, description="CPF do farmacêutico (DV oficial, opcional)")
    unidade_cnes: CNESFarmacia = Field(description="CNES da farmácia/unidade dispensadora")


class DispensacaoConfirmarIn(BaseModel):
    """Entrada do registro de baixa (total ou fracionada) da receita."""

    model_config = ConfigDict(str_strip_whitespace=True)

    codigo_hash: HashReceita = Field(
        description="Hash SHA-256 (hex, 64 caracteres) contido no QR Code da receita"
    )
    farmaceutico: FarmaceuticoIn
    itens: list[ItemDispensacaoIn] = Field(
        min_length=1, description="Baixas por item (quantidade <= saldo remanescente)"
    )
    observacoes: str | None = Field(None, max_length=500)
    chave_idempotencia: str | None = Field(
        None, max_length=64, description="Chave opcional contra duplicidade (reenvio de rede)"
    )


class DispensacaoItemOut(BaseModel):
    """Baixa efetivada de um item da receita."""

    model_config = ConfigDict(from_attributes=True)

    receita_item_id: int
    medicamento: str
    quantidade_dispensada: int = Field(ge=1)
    lote: str | None = None
    validade_lote: date | None = None


class DispensacaoConfirmarOut(BaseModel):
    """Resposta do registro da dispensação com o novo estado da receita."""

    model_config = ConfigDict(from_attributes=True)

    dispensacao_id: int
    receita_id: int
    tipo: TipoDispensacao = Field(description="'TOTAL' ou 'FRACIONADA'")
    status_receita: StatusReceita
    data_dispensacao: datetime
    itens: list[DispensacaoItemOut]
    saldos_remanescentes: list[ItemReceitaOut] = Field(
        description="Estado atualizado dos itens da receita após a baixa"
    )


__all__ = [
    "DispensacaoConsultarIn",
    "DispensacaoConsultarOut",
    "DispensacaoConfirmarIn",
    "DispensacaoConfirmarOut",
    "ItemDispensacaoIn",
]