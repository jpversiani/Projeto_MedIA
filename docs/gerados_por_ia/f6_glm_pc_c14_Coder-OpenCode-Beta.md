```python
# Arquivo: backend/app/services/copiloto_clinico.py
"""
Motor de Apoio à Decisão Clínica e Alertas de Interação Medicamentosa.

Este serviço implementa:
- Análise de interações medicamentosas (ex.: Fluoxetina + Tramadol, Enalapril + Espironolactona).
- Alertas de alergias registradas no prontuário do paciente antes de prescrever.
- Sugestão automática de conduta baseada em protocolos do Ministério da Saúde / SUS.

A implementação segue as diretrizes do MedIA:
- Atendimento particular e convênios (TISS ANS 4.01 / DMED).
- Método clínico de Atenção Primária / Saúde da Família.
- Python 3.12, tipagem estrita com Pydantic v2.
"""

from __future__ import annotations

from typing import List, Optional, Set, Tuple

from pydantic import BaseModel, Field


# ----------------------------------------------------------------------
# Modelos de domínio (Pydantic v2)
# ----------------------------------------------------------------------

class Medication(BaseModel):
    """Representa um medicamento com seus princípios ativos e classes."""
    name: str = Field(..., description="Nome comercial ou genérico do medicamento.")
    active_ingredients: List[str] = Field(
        default_factory=list,
        description="Lista de princípios ativos (ex.: ['fluoxetina']).",
    )
    drug_classes: List[str] = Field(
        default_factory=list,
        description="Classes farmacológicas (ex.: ['ISRS', 'antidepressivo']).",
    )


class Allergy(BaseModel):
    """Alergia registrada no prontuário do paciente."""
    allergen: str = Field(..., description="Substância ou grupo alergênico (ex.: 'penicilina').")
    severity: str = Field(default="moderada", description="Leve, moderada ou grave.")
    reaction: Optional[str] = Field(default=None, description="Reação observada.")


class Patient(BaseModel):
    """Dados mínimos do paciente para o copiloto clínico."""
    id: str
    name: str
    allergies: List[Allergy] = Field(default_factory=list)
    conditions: List[str] = Field(
        default_factory=list,
        description="Condições crônicas ou diagnósticos ativos (ex.: ['hipertensão', 'diabetes']).",
    )
    current_medications: List[Medication] = Field(
        default_factory=list,
        description="Medicamentos em uso atualmente.",
    )


class Prescription(BaseModel):
    """Nova prescrição médica a ser analisada."""
    medication: Medication
    dosage: str = Field(..., description="Posologia (ex.: '20mg 1x/dia').")
    duration: Optional[str] = Field(default=None, description="Duração do tratamento.")


# ----------------------------------------------------------------------
# Alertas e sugestões
# ----------------------------------------------------------------------

class InteractionAlert(BaseModel):
    """Alerta de interação medicamentosa."""
    medication_a: str
    medication_b: str
    severity: str = Field(..., description="Leve, moderada, grave ou contraindicação.")
    description: str
    recommendation: str


class AllergyAlert(BaseModel):
    """Alerta de alergia a medicamento."""
    medication: str
    allergen: str
    severity: str
    description: str
    recommendation: str


class ConductSuggestion(BaseModel):
    """Sugestão de conduta baseada em protocolos do Ministério da Saúde / SUS."""
    title: str
    description: str
    protocol_source: str = Field(..., description="Referência ao protocolo (ex.: 'Protocolo Clínico e Diretrizes Terapêuticas – HAS').")
    recommendations: List[str] = Field(default_factory=list)


class ClinicalDecision(BaseModel):
    """Resultado consolidado da análise do copiloto clínico."""
    patient_id: str
    prescription: Prescription
    interaction_alerts: List[InteractionAlert] = Field(default_factory=list)
    allergy_alerts: List[AllergyAlert] = Field(default_factory=list)
    conduct_suggestions: List[ConductSuggestion] = Field(default_factory=list)
    is_safe: bool = Field(default=True, description="False se houver alerta grave ou contraindicação.")


# ----------------------------------------------------------------------
# Base de conhecimento – Interações medicamentosas
# ----------------------------------------------------------------------
# Estrutura: (medicamento_ou_classe, medicamento_ou_classe) -> (severidade, descrição, recomendação)
# Usamos princípios ativos e classes para permitir correspondência flexível.

INTERACTIONS: List[Tuple[Set[str], Set[str], str, str, str]] = [
    (
        {"fluoxetina", "isrs", "antidepressivo"},
        {"tramadol", "opioide"},
        "grave",
        "Risco de síndrome serotoninérgica (hipertermia, rigidez, agitação, confusão).",
        "Evitar associação. Se necessário, usar alternativa com menor risco e monitorar sinais de toxicidade.",
    ),
    (
        {"enalapril", "ieca", "inibidor da enzima conversora de angiotensina"},
        {"espironolactona", "diurético poupador de potássio"},
        "grave",
        "Risco de hipercalemia grave, especialmente em pacientes com insuficiência renal.",
        "Monitorar potássio sérico e função renal. Considerar alternativa terapêutica.",
    ),
    (
        {"varfarina", "anticoagulante"},
        {"aspirina", "aas", "antiagregante plaquetário"},
        "moderada",
        "Aumento do risco de sangramento gastrointestinal.",
        "Avaliar risco-benefício. Se necessário, associar protetor gástrico e monitorar INR.",
    ),
    (
        {"metformina", "biguanida"},
        {"contraste iodado", "meios de contraste"},
        "moderada",
        "Risco de acidose láctica em pacientes com função renal comprometida.",
        "Suspender metformina antes de exames com contraste e reavaliar após 48h.",
    ),
    (
        {"sildenafil", "inibidor da fosfodiesterase 5"},
        {"nitrato", "mononitrato", "dinitrato"},
        "contraindicação",
        "Hipotensão grave potencialmente fatal.",
        "Contraindicação absoluta. Não prescrever em conjunto.",
    ),
]


# ----------------------------------------------------------------------
# Base de conhecimento – Alergias a medicamentos
# ----------------------------------------------------------------------
# Mapeia princípios ativos ou grupos para alérgenos comuns.
MEDICATION_ALLERGENS: dict[str, str] = {
    "amoxicilina": "penicilina",
    "ampicilina": "penicilina",
    "penicilina": "penicilina",
    "cefalexina": "cefalosporina",
    "ceftriaxona": "cefalosporina",
    "sulfametoxazol": "sulfa",
    "sulfadiazina": "sulfa",
    "sulfa": "sulfa",
    "ibuprofeno": "aas/nsaids",
    "naproxeno": "aas/nsaids",
    "diclofenaco": "aas/nsaids",
    "aspirina": "aas/nsaids",
    "aas": "aas/nsaids",
    "codeína": "opioide",
    "morfina": "opioide",
    "tramadol": "opioide",
}


# ----------------------------------------------------------------------
# Base de conhecimento – Protocolos do Ministério da Saúde / SUS
# ----------------------------------------------------------------------
# Regras simples baseadas em condições clínicas. Em produção, isso seria
# integrado a um sistema de regras mais robusto ou a uma base de diretrizes.

PROTOCOL_RULES = [
    {
        "conditions": {"hipertensão", "diabetes"},
        "title": "Hipertensão + Diabetes – Tratamento farmacológico",
        "description": "Conforme o Protocolo Clínico e Diretrizes Terapêuticas (PCDT) do SUS, a primeira escolha deve ser IECA ou BRA.",
        "protocol_source": "PCDT – Hipertensão Arterial e Diabetes Mellitus (Ministério da Saúde)",
        "recommendations": [
            "Iniciar IECA (ex.: enalapril) ou BRA (ex.: losartana) se houver albuminúria.",
            "Associar bloqueador de canal de cálcio ou diurético tiazídico se necessário.",
            "Meta pressórica: < 130/80 mmHg.",
        ],
    },
    {
        "conditions": {"asma"},
        "title": "Asma – Evitar betabloqueadores",
        "description": "Pacientes asmáticos não devem usar betabloqueadores não seletivos, pois podem precipitar broncoespasmo.",
        "protocol_source": "PCDT – Asma (Ministério da Saúde)",
        "recommendations": [
            "Evitar propranolol, nadolol e outros betabloqueadores não seletivos.",
            "Se betabloqueador for imprescindível, usar cardioseletivo com cautela (ex.: metoprolol).",
        ],
    },
    {
        "conditions": {"insuficiência cardíaca"},
        "title": "Insuficiência Cardíaca – Terapia tripla",
        "description": "Conforme o PCDT, a base do tratamento inclui IECA/BRA, betabloqueador e antagonista da aldosterona.",
        "protocol_source": "PCDT – Insuficiência Cardíaca (Ministério da Saúde)",
        "recommendations": [
            "Iniciar IECA (ou BRA) e betabloqueador (carvedilol, succinato de metoprolol).",
            "Adicionar espironolactona se NYHA II-IV e fração de ejeção reduzida.",
            "Monitorar função renal e potássio.",
        ],
    },
    {
        "conditions": {"dor crônica"},
        "title": "Dor Crônica – Abordagem escalonada",
        "description": "A OMS e o Ministério da Saúde recomendam escada analgésica: não opioides, opioides fracos, opioides fortes.",
        "protocol_source": "Diretrizes para o Manejo da Dor Crônica (Ministério da Saúde)",
        "recommendations": [
            "Iniciar com paracetamol ou AINEs (se não houver contraindicação).",
            "Se dor moderada, considerar opioide fraco (tramadol) associado a não opioide.",
            "Avaliar necessidade de adjuvantes (antidepressivos, anticonvulsivantes).",
        ],
    },
]


# ----------------------------------------------------------------------
# Serviço CopilotoClínico
# ----------------------------------------------------------------------

class CopilotoClinico:
    """
    Motor de apoio à decisão clínica.

    Fornece métodos para verificar interações medicamentosas, alergias e
    sugerir condutas baseadas em protocolos do Ministério da Saúde / SUS.
    """

    def __init__(self) -> None:
        # Em um cenário real, as bases de conhecimento seriam carregadas
        # de um banco de dados ou serviço externo. Aqui usamos estruturas
        # estáticas para manter o serviço autocontido.
        self.interactions = INTERACTIONS
        self.allergens_map = MEDICATION_ALLERGENS
        self.protocol_rules = PROTOCOL_RULES

    # ------------------------------------------------------------------
    # Interações medicamentosas
    # ------------------------------------------------------------------
    def check_interactions(self, medications: List[Medication]) ->