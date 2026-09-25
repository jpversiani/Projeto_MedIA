```python
# Arquivo: backend/app/services/copiloto_clinico.py
"""
Serviço de Apoio à Decisão Clínica e Alertas de Interação Medicamentosa.

Este módulo implementa um motor de verificação de interações medicamentosas,
alertas de alergias registradas no prontuário do paciente e sugestões de
conduta clínica baseadas em protocolos do Ministério da Saúde / SUS.

Arquitetura:
- Python 3.12
- Pydantic v2 (validação de dados)
- SQLAlchemy 2.0 (opcional, não utilizado diretamente aqui)
- Código limpo e tipagem estrita
"""

from __future__ import annotations

import unicodedata
from typing import List, Optional

from pydantic import BaseModel, Field


# ----------------------------------------------------------------------
# Modelos de dados de saída (Pydantic v2)
# ----------------------------------------------------------------------

class InteractionAlert(BaseModel):
    """
    Alerta de interação medicamentosa.
    """
    medicamento_a: str
    medicamento_b: str
    severidade: str = Field(..., description="'leve', 'moderada' ou 'grave'")
    descricao: str
    recomendacao: str
    protocolo_sus: Optional[str] = Field(
        default=None,
        description="Referência ao protocolo do Ministério da Saúde"
    )


class AllergyAlert(BaseModel):
    """
    Alerta de alergia do paciente a um medicamento.
    """
    alergia: str
    medicamento: str
    severidade: str = Field(..., description="'leve', 'moderada' ou 'grave'")
    descricao: str
    recomendacao: str


class ConductSuggestion(BaseModel):
    """
    Sugestão de conduta clínica.
    """
    tipo: str
    descricao: str
    recomendacao: str


class PrescriptionCheckResult(BaseModel):
    """
    Resultado completo da análise de prescrição.
    """
    interacoes: List[InteractionAlert] = Field(default_factory=list)
    alergias: List[AllergyAlert] = Field(default_factory=list)
    conduta_sugerida: List[ConductSuggestion] = Field(default_factory=list)


# ----------------------------------------------------------------------
# Base de conhecimento de interações medicamentosas
# ----------------------------------------------------------------------
# Fonte: Protocolos Clínicos e Diretrizes Terapêuticas do Ministério da Saúde
#        e referências farmacológicas oficiais.
# As chaves são pares de princípios ativos (ordem não importa).

DRUG_INTERACTIONS = {
    frozenset(["fluoxetina", "tramadol"]): {
        "severidade": "grave",
        "descricao": "Risco de síndrome serotoninérgica, que pode ser fatal.",
        "recomendacao": (
            "Evitar o uso concomitante. Se necessário, considerar analgésico "
            "alternativo (ex.: dipirona, paracetamol ou anti-inflamatório não "
            "esteroide) e monitorar sinais de toxicidade por serotonina."
        ),
        "protocolo_sus": "Protocolo de Segurança na Prescrição de Opioides e Psicotrópicos (MS/SUS)"
    },
    frozenset(["enalapril", "espironolactona"]): {
        "severidade": "moderada",
        "descricao": "Risco de hipercalemia, especialmente em pacientes com insuficiência renal ou diabetes.",
        "recomendacao": (
            "Monitorar potássio sérico e função renal. Se necessário, considerar "
            "a troca de espironolactona por outro diurético poupador de potássio "
            "ou acompanhamento mais frequente."
        ),
        "protocolo_sus": "Protocolo Clínico e Diretrizes Terapêuticas da Hipertensão Arterial (MS/SUS)"
    },
    frozenset(["varfarina", "ibuprofeno"]): {
        "severidade": "grave",
        "descricao": "Aumento do risco de sangramento gastrointestinal.",
        "recomendacao": (
            "Evitar o uso concomitante. Preferir paracetamol ou opioides se "
            "analgesia for necessária."
        ),
        "protocolo_sus": "Protocolo de Segurança no Uso de Anticoagulantes Orais (MS/SUS)"
    },
    frozenset(["metformina", "contraste_iodado"]): {
        "severidade": "moderada",
        "descricao": "Risco de acidose láctica em pacientes com insuficiência renal após administração de contraste.",
        "recomendacao": (
            "Suspender metformina no dia do exame e retomar 48 horas após, "
            "apenas se função renal normal."
        ),
        "protocolo_sus": "Recomendações do Ministério da Saúde para prevenção de acidose láctica"
    },
    # Adicione outras interações relevantes conforme necessidade
}


# ----------------------------------------------------------------------
# Base de conhecimento auxiliar para alergias a medicamentos
# ----------------------------------------------------------------------
# Mapeia classes/alergia comum a listas de princípios ativos/sinônimos.
COMMON_DRUG_ALERGY_KEYWORDS = {
    "penicilina": ["amoxicilina", "ampicilina", "benzilpenicilina", "penicilina v", "penicilina g"],
    "sulfa": ["sulfametoxazol", "sulfadiazina", "sulfasalazina", "cotrimoxazol"],
    "aspirina": ["ácido acetilsalicílico", "aas", "aspirina"],
    "ibuprofeno": ["ibuprofeno"],
    "dipirona": ["dipirona", "metamizol"],
    "codeina": ["codeína", "codeina"],
    "morfina": ["morfina"],
    "insulina": ["insulina"],
    "iode": ["iodo", "contraste iodado", "povidona-iodo"],
    "contraste": ["contraste iodado", "gadolínio", "contraste"],
}


# ----------------------------------------------------------------------
# Serviço principal
# ----------------------------------------------------------------------

class CopilotoClinico:
    """
    Serviço de apoio à decisão clínica.

    Verifica interações medicamentosas, alergias registradas e sugere conduta
    baseada em protocolos do Ministério da Saúde / SUS.
    """

    def __init__(self) -> None:
        # Em um projeto maior, poderíamos injetar dependências (ex.: repositórios)
        pass

    def check_drug_interactions(self, medications: List[str]) -> List[InteractionAlert]:
        """
        Verifica interações medicamentosas entre os medicamentos fornecidos.

        Args:
            medications: Lista de nomes de medicamentos (princípio ativo).

        Returns:
            Lista de alertas de interação.
        """
        alerts: List[InteractionAlert] = []
        normalized = [self._normalize_medication_name(med) for med in medications]

        # Comparação par a par
        for i in range(len(normalized)):
            for j in range(i + 1, len(normalized)):
                med_a = normalized[i]
                med_b = normalized[j]
                pair = frozenset([med_a, med_b])
                if pair in DRUG_INTERACTIONS:
                    info = DRUG_INTERACTIONS[pair]
                    alerts.append(
                        InteractionAlert(
                            medicamento_a=med_a,
                            medicamento_b=med_b,
                            severidade=info["severidade"],
                            descricao=info["descricao"],
                            recomendacao=info["recomendacao"],
                            protocolo_sus=info.get("protocolo_sus"),
                        )
                    )
        return alerts

    def check_allergies(
        self,
        patient_allergies: List[str],
        medications: List[str]
    ) -> List[AllergyAlert]:
        """
        Verifica se algum medicamento prescrito está na lista de alergias do paciente.

        Args:
            patient_allergies: Lista de alergias registradas no prontuário.
            medications: Lista de medicamentos prescritos.

        Returns:
            Lista de alertas de alergia.
        """
        alerts: List[AllergyAlert] = []
        if not patient_allergies:
            return alerts

        normalized_allergies = [self._normalize_medication_name(al) for al in patient_allergies]

        for med in medications:
            normalized_med = self._normalize_medication_name(med)
            # Verificação direta: nome igual ou contido
            for allergy_norm in normalized_allergies:
                if self._is_allergy_match(allergy_norm, med, normalized_med):
                    alerts.append(
                        AllergyAlert(
                            alergia=allergy_norm,
                            medicamento=med,
                            severidade="grave",
                            descricao=(
                                f"Paciente possui alergia registrada a '{allergy_norm}' "
                                f"e o medicamento '{med}' pode causar reação cruzada."
                            ),
                            recomendacao=(
                                "Suspender a prescrição deste medicamento e buscar "
                                "alternativa terapêutica segura. Informar o paciente "
                                "e registrar o alerta no prontuário."
                            ),
                        )
                    )
                    break  # Evita duplicidade para a mesma alergia e medicamento

        return alerts

    def suggest_conduct(
        self,
        interaction_alerts: List[InteractionAlert],
        allergy_alerts: List[AllergyAlert]
    ) -> List[ConductSuggestion]:
        """
        Gera sugestões de conduta clínica a partir dos alertas detectados.

        Args:
            interaction_alerts: Alertas de interação medicamentosa.
            allergy_alerts: Alertas de alergia.

        Returns:
            Lista de sugestões de conduta.
        """
        conduta: List[ConductSuggestion] = []

        # Sugestão para interações graves
        for alert in interaction_alerts:
            if alert.severidade == "grave":
                conduta.append(
                    ConductSuggestion(
                        tipo="interacao_grave",
                        descricao=f"Interação grave entre {alert.medicamento_a} e {alert.medicamento_b}.",
                        recomendacao=alert.recomendacao,
                    )
                )

        # Sugestão para alergias
        for alert in allergy_alerts:
            conduta.append(
                ConductSuggestion(
                    tipo="alergia",
                    descricao=f"Alergia ao medicamento {alert.medicamento}.",
                    recomendacao=alert.recomendacao,
                )
            )

        # Se não houver alertas, sugerir conduta padrão (prescrição segura)
        if not conduta:
            conduta.append(
                ConductSuggestion(
                    tipo="prescricao_segura",
                    descricao="Nenhuma interação ou alergia detectada.",
                    recomendacao=(
                        "Manter prescrição conforme protocolo do Ministério da Saúde. "
                        "Revisar dose e duração do tratamento."
                    ),
                )
            )

        return conduta

    def analyze_prescription(
        self,
        patient_allergies: List[str],
        medications: List[str]
    ) -> PrescriptionCheckResult:
        """
        Executa a análise completa de uma prescrição.

        Args:
            patient_allergies: Lista de alergias do paciente.
            medications: Lista de medicamentos prescritos.

        Returns:
            Resultado da análise com interações, alergias e conduta sugerida.
        """
        interacoes = self.check_drug_interactions(medications)
        alergias = self.check_allergies(patient_allergies, medications)
        conduta = self.suggest_conduct(interacoes, alergias)

        return PrescriptionCheckResult(
            interacoes=interacoes,
            alergias=alergias,
            conduta_sugerida=conduta,
        )

    # ------------------------------------------------------------------
    # Métodos auxiliares
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_medication_name(name: str) -> str:
        """
        Normaliza nome de medicamento (minúsculas, sem acentos).
        """
        nfkd_form = unicodedata.normalize('NFKD', name)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).strip().lower()

    @classmethod
    def _normalize_allergy_item(cls, allergy: str) -> str:
        """Normaliza o nome da alergia."""
        return cls._normalize_medication_name(allergy)

    @classmethod
    def _is_allergy_match(cls, allergy_norm: str, original_med: str, normalized_med: str) -> bool:
        """
        Verifica se a alergia corresponde ao medicamento ou a algum ingrediente.
        """
        # Verificação direta: alergia igual ao medicamento
        if allergy_norm == normalized_med:
            return True

        # Verificação se alergia contida no medicamento ou vice-versa
        if allergy_norm in normalized_med or normalized_med in allergy_norm:
            return True

        # Verificação via base de sinônimos de alergias comuns
        for allergen, synonyms in COMMON_DRUG_ALERGY_KEYWORDS.items():
            # Se a alergia é de uma classe, verificar se o medicamento pertence
            if allergy_norm == allergen or any(syn in allergy_norm for syn in synonyms):
                if any(syn in normalized_med for syn in synonyms):
                    return True

            # Se o medicamento é o alérgeno conhecido
            if allergy_norm in synonyms and normalized_med in synonyms:
                return True

        return False


# Conveniência: função incapsulada para uso direto
def check_prescription(
    patient_allergies: List[str],
    medications: List[str]
) -> PrescriptionCheckResult:
    """
    Função de conveniência para análise de prescrição.

    Args:
        patient_allergies: Lista de alergias registradas do paciente.
        medications: Lista de medicamentos prescritos.

    Returns:
        PrescriptionCheckResult com alertas e conduta.
    """
    service = CopilotoClinico()
    return service.analyze_prescription(patient_allergies, medications)
```