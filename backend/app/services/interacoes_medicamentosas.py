"""
Motor de Validação Farmacológica & Interações Medicamentosas Graves — Projeto MedIA (Saúde 4.0)
Conformidade: Relação Nacional de Medicamentos Essenciais (Rename) e Bulário Eletrônico da Anvisa.
"""

from dataclasses import dataclass
from typing import Dict, List, Set
import re


@dataclass
class AlertaInteracao:
    medicamento_a: str
    medicamento_b: str
    gravidade: str  # CONTRAINDICADO, GRAVE, MODERADO
    mecanismo: str
    conduta_recomendada: str


@dataclass
class RelatorioFarmacologico:
    total_medicamentos_analisados: int
    interacoes_detectadas: List[AlertaInteracao]
    alertas_alergia: List[str]
    aprovado_para_dispensacao: bool


class VerificadorFarmacologico:
    """Motor de checagem cruzada de interações medicamentosas e hipersensibilidades."""

    # Base de pares de interação de alta relevância clínica
    INTERACOES_CONHECIDAS = [
        AlertaInteracao(
            medicamento_a="enalapril",
            medicamento_b="espironolactona",
            gravidade="GRAVE",
            mecanismo="Sinergismo na retenção de potássio levando a risco iminente de hipercalemia severa e arritmias cardíacas.",
            conduta_recomendada="Monitorar potássio sérico e creatinina em 7 e 14 dias; considerar ajuste de dose."
        ),
        AlertaInteracao(
            medicamento_a="captopril",
            medicamento_b="espironolactona",
            gravidade="GRAVE",
            mecanismo="Retenção aditiva de potássio por inibição simultânea do eixo renina-angiotensina e aldosterona.",
            conduta_recomendada="Monitorização eletrolítica estrita."
        ),
        AlertaInteracao(
            medicamento_a="varfarina",
            medicamento_b="ibuprofeno",
            gravidade="CONTRAINDICADO",
            mecanismo="Inibição plaquetária por AINEs associada à anticoagulação oral eleva criticamente o risco de hemorragia gastrointestinal.",
            conduta_recomendada="Evitar AINEs; substituir por paracetamol ou dipirona para dor/febre."
        ),
        AlertaInteracao(
            medicamento_a="varfarina",
            medicamento_b="diclofenaco",
            gravidade="CONTRAINDICADO",
            mecanismo="AINEs potencializam a ação hipoprotrombinêmica e provocam lesão de mucosa gástrica.",
            conduta_recomendada="Substituir analgesia; monitorar RNI/TP com urgência se administrado."
        ),
        AlertaInteracao(
            medicamento_a="litio",
            medicamento_b="hidroclorotiazida",
            gravidade="GRAVE",
            mecanismo="Diuréticos tiazídicos reduzem o clearance renal do lítio em 20-40%, deflagrando intoxicação por lítio.",
            conduta_recomendada="Evitar tiazídico ou reduzir dose de lítio pela metade monitorando litemia sérica."
        ),
        AlertaInteracao(
            medicamento_a="fluoxetina",
            medicamento_b="tramadol",
            gravidade="GRAVE",
            mecanismo="Aumento acentuado da atividade serotoninérgica central com risco de Síndrome Serotoninérgica potencialmente fatal.",
            conduta_recomendada="Utilizar analgésico não-serotoninérgico ou monitorar rigidez, hipertermia e clônus."
        ),
        AlertaInteracao(
            medicamento_a="digoxina",
            medicamento_b="amiodarona",
            gravidade="GRAVE",
            mecanismo="A amiodarona eleva as concentrações plasmáticas de digoxina em até 70%, gerando bradiarritmias graves.",
            conduta_recomendada="Reduzir a dose de digoxina em 50% ao introduzir amiodarona."
        ),
        AlertaInteracao(
            medicamento_a="metformina",
            medicamento_b="contraste_iodado",
            gravidade="GRAVE",
            mecanismo="Risco de disfunção renal aguda induzida por contraste com acúmulo de metformina e acidose lática.",
            conduta_recomendada="Suspender metformina 48h antes e retomar 48h após exame radiológico com função renal checada."
        ),
    ]

    # Grupos de reatividade cruzada de alergias comuns
    CLASSES_ALERGICAS = {
        "penicilina": ["amoxicilina", "ampicilina", "penicilina", "benzetacil", "cefalexina"],
        "sulfa": ["sulfametoxazol", "furosemida", "hidroclorotiazida", "glibenclamida"],
        "dipirona": ["dipirona", "metamizol"],
        "aines": ["ibuprofeno", "diclofenaco", "cetoprofeno", "nimesulida", "ácido acetilsalicílico", "aspirina"],
    }

    @classmethod
    def normalizar_termo(cls, termo: str) -> str:
        """Limpa e padroniza strings farmacológicas."""
        return re.sub(r"[^a-z0-9]", "", termo.lower())

    @classmethod
    def checar_interacoes_e_alergias(
        cls,
        medicamentos_prescritos: List[str],
        alergias_paciente: List[str]
    ) -> RelatorioFarmacologico:
        """Realiza varredura combinatória de interações medicamentosas e hipersensibilidades."""
        meds_norm = [cls.normalizar_termo(m) for m in medicamentos_prescritos if m]
        alergias_norm = [cls.normalizar_termo(a) for a in alergias_paciente if a]

        interacoes_encontradas: List[AlertaInteracao] = []
        alertas_alergias: List[str] = []

        # 1. Checagem de Alergias
        for med in meds_norm:
            for alergia in alergias_norm:
                # Confronto direto por substring
                if alergia in med or med in alergia:
                    alertas_alergias.append(f"ALERTA CRÍTICO: Paciente possui alergia direta relatada a '{alergia}' compatível com '{med}'.")
                
                # Confronto por classe farmacológica de reatividade cruzada
                for classe, membros in cls.CLASSES_ALERGICAS.items():
                    if any(cls.normalizar_termo(m) in alergia for m in membros):
                        if any(cls.normalizar_termo(m) in med for m in membros):
                            alertas_alergias.append(
                                f"ALERTA DE REATIVIDADE CRUZADA: Prescrição de '{med}' perigosa para histórico alérgico de '{alergia}' (Classe: {classe.upper()})."
                            )

        # 2. Checagem de Interações Par-a-Par
        for i in range(len(meds_norm)):
            for j in range(i + 1, len(meds_norm)):
                m1 = meds_norm[i]
                m2 = meds_norm[j]

                for interacao in cls.INTERACOES_CONHECIDAS:
                    norm_a = cls.normalizar_termo(interacao.medicamento_a)
                    norm_b = cls.normalizar_termo(interacao.medicamento_b)

                    if (norm_a in m1 and norm_b in m2) or (norm_a in m2 and norm_b in m1):
                        interacoes_encontradas.append(interacao)

        # Decisão de dispensa clínica
        tem_contraindicacao = any(i.gravidade == "CONTRAINDICADO" for i in interacoes_encontradas)
        tem_alergia_grave = len(alertas_alergias) > 0
        aprovado = not (tem_contraindicacao or tem_alergia_grave)

        return RelatorioFarmacologico(
            total_medicamentos_analisados=len(meds_norm),
            interacoes_detectadas=interacoes_encontradas,
            alertas_alergia=list(set(alertas_alergias)),
            aprovado_para_dispensacao=aprovado
        )
