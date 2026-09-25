"""Schemas Pydantic v2 do Prontuário do Cidadão (PEC e-SUS APS).

Contratos de entrada e saída das rotas REST do prontuário: resumo clínico
(problemas ativos, alergias e medicamentos em uso), evoluções paginadas
(método SOAP), registro de alergias e de problemas (CIAP-2 / CID-10).

Projeto MedIA — SUS/APS (Python 3.12, Pydantic v2).
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Annotated, Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.schemas.atendimento import AtendimentoSOAPOut

# Padrões oficiais de codificação SUS (CNS, CIAP-2 e CID-10)
REGEX_CNS: Final[str] = r"^\d{15}$"
REGEX_CIAP2: Final[str] = r"^[A-Za-z]\d{2}$"
REGEX_CID10: Final[str] = r"^[A-Za-z]\d{2}(\.\d{1,2})?$"

TipoCodigo = Literal["CIAP2", "CID10"]
SituacaoProblema = Literal["ATIVO", "RESOLVIDO", "RASTREAMENTO"]
OrigemProblema = Literal["ATENDIMENTO", "PRONTUARIO"]

CNS = Annotated[str, StringConstraints(pattern=REGEX_CNS)]


class ProblemaProntuarioCreate(BaseModel):
    """Entrada de problema/condição na Lista de Problemas do cidadão."""

    model_config = ConfigDict(str_strip_whitespace=True)

    tipo_codigo: TipoCodigo = Field(description="Terminologia SUS: 'CIAP2' ou 'CID10'")
    codigo: Annotated[
        str,
        StringConstraints(to_upper=True, min_length=3, max_length=7),
        Field(description="Código CIAP-2 (ex.: K86) ou CID-10 (ex.: I10, N39.0)"),
    ]
    descricao: str = Field(min_length=3, max_length=300)
    situacao: SituacaoProblema = "ATIVO"

    @model_validator(mode="after")
    def validar_codigo_por_terminologia(self) -> Self:
        """Exige que o código siga o padrão oficial da terminologia informada."""
        padrao = REGEX_CIAP2 if self.tipo_codigo == "CIAP2" else REGEX_CID10
        if re.fullmatch(padrao, self.codigo) is None:
            raise ValueError(
                f"Código '{self.codigo}' não é um {self.tipo_codigo} válido "
                "(formato oficial do SUS)."
            )
        return self


class ProblemaProntuarioOut(ProblemaProntuarioCreate):
    """Problema registrado na Lista de Problemas do cidadão."""

    id: int
    cidadao_id: int
    data_registro: datetime

    model_config = ConfigDict(from_attributes=True)


class AlergiaCreate(BaseModel):
    """Entrada de alergia registrada no prontuário do cidadão."""

    model_config = ConfigDict(str_strip_whitespace=True)

    descricao: str = Field(
        min_length=2,
        max_length=200,
        description="Substância/agente causador da alergia (ex.: Penicilina, Dipirona)",
    )


class AlergiaCriadaOut(BaseModel):
    """Resposta do registro de alergia: item criado e lista atualizada."""

    cidadao_id: int
    descricao: str
    alergias: list[str] = Field(description="Lista completa de alergias do cidadão")


class ProblemaAtivoOut(BaseModel):
    """Problema ativo no resumo do prontuário (CIAP-2 ou CID-10)."""

    tipo_codigo: str = Field(description="'CIAP2' ou 'CID10'")
    codigo: str
    descricao: str
    situacao: str = Field(description="'ATIVO' ou 'RASTREAMENTO'")
    data_registro: datetime | None = None
    origem: OrigemProblema = Field(description="Origem do registro no prontuário")


class MedicamentoEmUsoOut(BaseModel):
    """Medicamento em uso contínuo identificado nas prescrições (plano SOAP)."""

    nome: str
    detalhe: str | None = Field(None, description="Dosagem/posologia/quantidade quando informada")


class CidadaoIdentificacaoOut(BaseModel):
    """Identificação do cidadão no cabeçalho do prontuário (padrões SUS/APS)."""

    id: int
    cns: str | None = Field(None, description="Cartão Nacional de Saúde (15 dígitos)")
    cpf: str | None = None
    nome_completo: str
    nome_social: str | None = None
    nome_mae: str | None = None
    data_nascimento: date
    sexo: str = Field(description="'M', 'F' ou 'I'")
    telefone: str | None = None
    municipio_ibge: str | None = None
    hipertenso: bool = False
    diabetico: bool = False
    gestante: bool = False
    fumante: bool = False

    model_config = ConfigDict(from_attributes=True)


class ProntuarioResumoOut(BaseModel):
    """Resumo clínico do prontuário: problemas ativos, alergias e medicamentos em uso."""

    cidadao: CidadaoIdentificacaoOut
    problemas_ativos: list[ProblemaAtivoOut] = []
    alergias: list[str] = []
    medicamentos_em_uso: list[MedicamentoEmUsoOut] = []
    total_atendimentos: int = Field(0, ge=0, description="Total de evoluções (atendimentos SOAP)")
    data_ultimo_atendimento: datetime | None = None


class PaginaEvolucoesOut(BaseModel):
    """Página de evoluções clínicas (atendimentos SOAP) do prontuário."""

    total: int = Field(ge=0, description="Total de evoluções do cidadão")
    skip: int = Field(ge=0, description="Registros ignorados (paginação por offset)")
    limit: int = Field(ge=1, description="Tamanho máximo da página")
    itens: list[AtendimentoSOAPOut] = []