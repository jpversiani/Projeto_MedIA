```python
"""
Serviço de geração e validação de guias TISS (ANS 4.01.00+).

Gera XML para guias de Consulta Médica e SP/SADT, conforme o padrão TISS
da Agência Nacional de Saúde Suplementar (ANS), com validação contra schema XSD.

Uso típico:
    generator = TISSGenerator()
    xml = generator.generate_consulta_guide(data)
    generator.validate_xml(xml, schema_path)
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Union

from lxml import etree
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Namespace padrão TISS
NAMESPACE = "http://www.ans.gov.br/padroes/tiss/schemas"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOCATION = (
    f"{NAMESPACE} http://www.ans.gov.br/padroes/tiss/schemas/TISS-4.01.00.xsd"
)


# ---------------------------------------------------------------------------
# Modelos de dados (Pydantic v2)
# ---------------------------------------------------------------------------

class Beneficiario(BaseModel):
    """Dados do beneficiário (paciente) do convênio."""

    model_config = ConfigDict(extra="forbid")

    nome: str = Field(..., min_length=1, max_length=70)
    numero_carteira: str = Field(..., min_length=1, max_length=20)
    validade_carteira: Optional[date] = None


class Prestador(BaseModel):
    """Dados do prestador (médico/executante)."""

    model_config = ConfigDict(extra="forbid")

    nome: str = Field(..., min_length=1, max_length=70)
    cpf: str = Field(..., pattern=r"^\d{11}$")
    conselho: str = Field("CRM", max_length=10)
    numero_conselho: str = Field(..., min_length=1, max_length=15)
    uf_conselho: str = Field(..., min_length=2, max_length=2)


class Procedimento(BaseModel):
    """Procedimento executado (consulta, exame, terapia etc.)."""

    model_config = ConfigDict(extra="forbid")

    codigo: str = Field(..., min_length=1, max_length=10)
    descricao: str = Field(..., min_length=1, max_length=150)
    quantidade: int = Field(1, ge=1)
    valor: float = Field(0.0, ge=0.0)


class Diagnostico(BaseModel):
    """Diagnóstico informado em CID-10."""

    model_config = ConfigDict(extra="forbid")

    codigo_cid10: str = Field(..., pattern=r"^[A-Z]\d{2}(\.\d)?$")
    descricao: Optional[str] = Field(None, max_length=150)


class ConsultaGuideData(BaseModel):
    """Dados para geração de uma guia de consulta."""

    model_config = ConfigDict(extra="forbid")

    operadora: str = Field(..., min_length=6, max_length=6)  # registro ANS
    beneficiario: Beneficiario
    prestador: Prestador
    data_atendimento: date
    diagnostico: Diagnostico
    procedimento: Procedimento


class SPSADTGuideData(BaseModel):
    """Dados para geração de uma guia SP/SADT."""

    model_config = ConfigDict(extra="forbid")

    operadora: str = Field(..., min_length=6, max_length=6)
    beneficiario: Beneficiario
    prestador: Prestador
    data_atendimento: date
    diagnosticos: List[Diagnostico] = Field(..., min_length=1)
    procedimentos: List[Procedimento] = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Gerador TISS
# ---------------------------------------------------------------------------

class TISSGenerator:
    """
    Gera e valida XML de guias TISS (Consulta e SP/SADT).

    A geração produz um lote contendo uma única guia, em conformidade
    estrutural com o padrão ANS 4.01.00. A validação contra o schema XSD
    é opcional e depende do arquivo de schema fornecido.
    """

    def __init__(self) -> None:
        self._nsmap = {
            "ans": NAMESPACE,
            "xsi": XSI_NAMESPACE,
        }

    # ------------------------------------------------------------------
    # Geração pública
    # ------------------------------------------------------------------

    def generate_consulta_guide(self, data: ConsultaGuideData) -> str:
        """
        Gera XML de uma guia de consulta.

        Args:
            data: Dados estruturados da guia.

        Returns:
            String contendo o XML TISS.
        """
        root = self._create_root()
        lote = self._create_lote(root)

        guia = etree.SubElement(lote, self._q("guiaConsulta"))
        self._add_operadora(guia, data.operadora)
        self._add_numero_guia(guia)
        self._add_beneficiario(guia, data.beneficiario)
        self._add_prestador(guia, data.prestador)
        self._add_data_atendimento(guia, data.data_atendimento)
        self._add_diagnostico(guia, data.diagnostico)
        self._add_procedimentos(guia, [data.procedimento])

        return self._serialize(root)

    def generate_spsadt_guide(self, data: SPSADTGuideData) -> str:
        """
        Gera XML de uma guia SP/SADT.

        Args:
            data: Dados estruturados da guia.

        Returns:
            String contendo o XML TISS.
        """
        root = self._create_root()
        lote = self._create_lote(root)

        guia = etree.SubElement(lote, self._q("guiaSP_SADT"))
        self._add_operadora(guia, data.operadora)
        self._add_numero_gu