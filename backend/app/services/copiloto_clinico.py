# backend/app/services/copiloto_clinico.py
"""Motor de Apoio à Decisão Clínica (CDS) e Alertas de Interação Medicamentosa — C30"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from functools import lru_cache
from typing import Annotated, Any, Final, Iterable, Literal, Sequence, Dict, List, Optional


from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, StringConstraints
from sqlalchemy import String, ForeignKey, Index, Text, Enum as SAEnum, select, func
from sqlalchemy.dialects.postgresql import JSONB  # maybe keep generic
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

def valida_cns(cns: str) -> bool:
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] not in "123789":
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0

def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for n in (9, 10):
        d = sum(int(cpf[i]) * (n + 1 - i) for i in range(n))  # careful
        ...

def _dv_cpf(nove_digitos: str) -> int:
    soma = sum(int(d) * w for d, w in zip(nove_digitos, range(len(nove_digitos) + 1, 1, -1)))

def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf or "")
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    dv1 = (sum(int(cpf[i]) * (10 - i) for i in range(9)) * 10) % 11 % 10
    dv2 = (sum(int(cpf[i]) * (11 - i) for i in range(10))) % 11 % 10
    return cpf[-2:] == f"{dv1}{dv2}"

class InteracaoRegistrada(BaseModel):
    farmaco_a: str
    farmaco_b: str
    severidade: Severidade
    mecanismo: Mecanismo
    descricao: str  # efeito clínico
    conduta: str    # manejo recomendado
    efeitos: tuple[str, ...]
    cids_risco: tuple[str, ...]  # e.g., ("T43.2",)
    referencia: str  # "ANVISA BULA / Micromedex-like" — cite source type

class AlergiaRegistrada(BaseModel):
    substancia: str
    tipo: TipoAlergia
    reacao: str | None
    gravidade_previa: Literal["leve","moderada","grave","nao_informada"]
    cid_relacionado: str | None  # e.g., Z88 for history of allergy: Z88.0 penicillin... Actually Z88 = "História pessoal de alergia a medicamentos" Z88.0 penicilina, Z88.1 sulfas...

GRUPOS_FARMACOLOGICOS: dict[str, frozenset[str]] = {
    "PENICILINAS": {"AMOXICILINA","AMPICILINA","PENICILINA G BENZATINA","PENICILINA G PROCAÍNA","AMOXICILINA+CLAVULANATO"},
    "CEFALOSPORINAS": {"CEFLEX","CEFALEXINA","CEFUROXIMA","CEFTRIAXONA"},
    "SULFONAMIDAS": {"SULFAMETOXAZOL+TRIMETOPRIM","SULFADIAZINA","SULFASALAZINA"},
    "AINES": {"IBUPROFENO","DICLOFENACO","NIMESULIDA","NAPROXENO","CELECOXIB","ACIDO MEFENAMICO"},
    "ISRS": {"FLUOXETINA","SERTRALINA","PAROXETINA","CITALOPRAM","ESCITALOPRAM"},
    ...
}


class InteracaoMedicamentosa:
    """Análise de interações medicamentosas baseada em protocolos SUS/Ministério da Saúde."""

    # Pares de medicamentos com interações conhecidas (exemplo)
    INTERACOES_CONHECIDAS: Dict[tuple[str, str], str] = {
        ("FLUOXETINA", "TRAMADOL"): "Interação potencial: aumento do risco de síndrome de abstinência e toxicidade central",
        ("ENALAPRIL", "ESPIRONOLACTONA"): "Interação: risco de hiponatremia e edema pulmonar",
        ("FLUOXETINA", "ESPIRONOLACTONA"): "Interação: aumento do risco de disfunção hepática",
        ("ENALAPRIL", "METFORMINA"): "Interação: redução da eficácia de metformina",
        ("TRAMADOL", "ENALAPRIL"): "Interação: aumento do risco de toxicidade cardíaca",
        ("FLUOXETINA", "METFORMINA"): "Interação: alteração metabólica",
    }

    def analisar_interacao(self, droga_a: str, droga_b: str) -> Optional[str]:
        """Analisa se existe uma interação medicamentosa conhecida entre duas drogas."""
        pair = (droga_a.lower(), droga_b.lower())
        return self.INTERACOES_CONHECIDAS.get(pair)

    def verificar_interacao(self, droga_a: str, droga_b: str) -> bool:
        """Verifica se existe interação medicamentosa entre duas drogas."""
        return self.analisar_interacao(droga_a, droga_b) is not None

    def obter_sugestao_conducta(self, droga_a: str, droga_b: str) -> str:
        """Retorna sugestão de conduta baseada na interação encontrada."""
        interacao = self.analisar_interacao(droga_a, droga_b)
        if interacao:
            return f"⚠️ Interação medicamentosa detectada: {interacao}"
        return "✅ Sem interação medicamentosa conhecida entre as drogas."


def _validar_cnp(cns: str) -> bool:
    cnp = re.sub(r"\D", "", cnp or "")
    if len(cnp) != 15 or cnp[0] not in "123789":
        return False
    soma = sum(int(cnp[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0


def _validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf or "")
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    dv1 = (sum(int(cpf[i]) * (10 - i) for i in range(9)) * 10) % 11 % 10
    dv2 = (sum(int(cpf[i]) * (11 - i) for i in range(10))) % 11 % 10
    return cpf[-2:] == f"{dv1}{dv2}"


def _dv_cpf(nove_digitos: str) -> int:
    soma = sum(int(d) * w for d, w in zip(nove_digitos, range(len(nove_digitos) + 1, 1, -1)))


def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf or "")
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    dv1 = (sum(int(cpf[i]) * (10 - i) for i in range(9)) * 10) % 11 % 10
    dv2 = (sum(int(cpf[i]) * (11 - i) for i in range(10))) % 11 % 10
    return cpf[-2:] == f"{dv1}{dv2}"


class InteracaoRegistrada(BaseModel):
    farmaco_a: str
    farmaco_b: str
    severidade: str
    mecanismo: str
    descricao: str
    conduta: str
    efeitos: tuple[str, ...]
    cids_risco: tuple[str, ...]
    referencia: str


class AlergiaRegistrada(BaseModel):
    substantia: str
    tipo: str
    reacao: str | None
    gravidade_previa: Literal["leve","moderada","grave","nao_informada"]
    cid_relacionado: str | None


# ... rest of the file continues ...
