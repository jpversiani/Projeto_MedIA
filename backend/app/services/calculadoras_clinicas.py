"""
Calculadoras Clínicas Baseadas em Evidências — Projeto MedIA (Saúde 4.0)
Algoritmos computacionais validados:
1. Escore de Risco Cardiovascular de Framingham (10 anos)
2. Taxa de Filtração Glomerular Estimada (eGFR / CKD-EPI 2021)
3. Antropometria e Estadiamento Nutricional OMS
"""

from dataclasses import dataclass
from typing import Dict, Optional
import math


@dataclass
class ResultadoFramingham:
    pontuacao_total: int
    risco_percentual: float
    categoria_risco: str  # Baixo (<10%), Intermediário (10-20%), Alto (>20%)
    recomendacao_clinica: str


@dataclass
class ResultadoCKDEPI:
    egfr: float
    estagio_drc: str  # G1, G2, G3a, G3b, G4, G5
    descricao_estagio: str
    alerta_clinico: str


class CalculadorasClinicas:
    """Implementação precisa de escores clínicos para Atenção Primária e Secundária."""

    @classmethod
    def calcular_framingham(
        cls,
        sexo: str,
        idade: int,
        colesterol_total: float,
        colesterol_hdl: float,
        pressao_sistolica: float,
        em_tratamento_has: bool,
        fumante: bool,
        diabetico: bool
    ) -> ResultadoFramingham:
        """
        Calcula o risco cardiovascular em 10 anos (Escore de Framingham ajustado).
        """
        sexo_upper = sexo.strip().upper()
        pontos = 0

        # Pontos por Idade
        if sexo_upper == "M":
            if idade <= 34: pontos += -9
            elif idade <= 39: pontos += -4
            elif idade <= 44: pontos += 0
            elif idade <= 49: pontos += 3
            elif idade <= 54: pontos += 6
            elif idade <= 59: pontos += 8
            elif idade <= 64: pontos += 10
            elif idade <= 69: pontos += 11
            elif idade <= 74: pontos += 12
            else: pontos += 13
        else:  # Feminino
            if idade <= 34: pontos += -7
            elif idade <= 39: pontos += -3
            elif idade <= 44: pontos += 0
            elif idade <= 49: pontos += 3
            elif idade <= 54: pontos += 6
            elif idade <= 59: pontos += 8
            elif idade <= 64: pontos += 10
            elif idade <= 69: pontos += 12
            elif idade <= 74: pontos += 14
            else: pontos += 16

        # Pontos por Colesterol Total
        if colesterol_total >= 280: pontos += 5
        elif colesterol_total >= 240: pontos += 4
        elif colesterol_total >= 200: pontos += 3
        elif colesterol_total >= 160: pontos += 1

        # Pontos por HDL (proteção vs risco)
        if colesterol_hdl >= 60: pontos -= 1
        elif colesterol_hdl < 35: pontos += 2
        elif colesterol_hdl < 45: pontos += 1

        # Pontos por Pressão Sistólica
        if em_tratamento_has:
            if pressao_sistolica >= 160: pontos += 3
            elif pressao_sistolica >= 140: pontos += 2
            elif pressao_sistolica >= 130: pontos += 2
            elif pressao_sistolica >= 120: pontos += 1
        else:
            if pressao_sistolica >= 160: pontos += 2
            elif pressao_sistolica >= 140: pontos += 1
            elif pressao_sistolica >= 130: pontos += 1

        # Tabagismo e Diabetes
        if fumante: pontos += 4
        if diabetico: pontos += 3

        # Estimativa de probabilidade
        if pontos <= 0: risco = 1.0
        elif pontos <= 5: risco = 2.0
        elif pontos <= 8: risco = 5.0
        elif pontos <= 11: risco = 8.0
        elif pontos <= 14: risco = 16.0
        elif pontos <= 17: risco = 25.0
        else: risco = 30.0

        if risco < 10.0:
            categoria = "Baixo Risco (< 10%)"
            rec = "Metas de estilo de vida saudável e reavaliação a cada 2 a 5 anos."
        elif risco <= 20.0:
            categoria = "Risco Intermediário (10% - 20%)"
            rec = "Otimizar controle pressórico e lipídico com MEV e considerar estatinas."
        else:
            categoria = "Alto Risco (> 20%)"
            rec = "Intervenção intensiva: estatina de alta potência, controle estrito de PA < 130/80 e AAS."

        return ResultadoFramingham(
            pontuacao_total=pontos,
            risco_percentual=risco,
            categoria_risco=categoria,
            recomendacao_clinica=rec
        )

    @classmethod
    def calcular_ckd_epi(
        cls,
        creatinina_serica: float,
        idade: int,
        sexo: str
    ) -> ResultadoCKDEPI:
        """
        Fórmula CKD-EPI 2021 (sem coeficiente de raça - recomendação internacional KDIGO).
        """
        sexo_upper = sexo.strip().upper()
        is_fem = (sexo_upper == "F")

        kappa = 0.7 if is_fem else 0.9
        alpha = -0.241 if is_fem else -0.302
        fator_sexo = 1.012 if is_fem else 1.0

        cr_div_kappa = creatinina_serica / kappa
        min_cr = min(cr_div_kappa, 1.0)
        max_cr = max(cr_div_kappa, 1.0)

        egfr = 142.0 * (min_cr ** alpha) * (max_cr ** -1.200) * (0.9938 ** idade) * fator_sexo
        egfr = round(egfr, 1)

        if egfr >= 90:
            estagio = "G1"
            desc = "Função renal normal ou elevada"
            alerta = "Sem evidência de perda de função renal se não houver proteinúria."
        elif egfr >= 60:
            estagio = "G2"
            desc = "Redução leve da função renal"
            alerta = "Monitorar pressão arterial e glicemia; rastrear microalbuminúria."
        elif egfr >= 45:
            estagio = "G3a"
            desc = "Redução leve a moderada"
            alerta = "Ajustar posologia de medicamentos de excreção renal; avaliar nefropatia."
        elif egfr >= 30:
            estagio = "G3b"
            desc = "Redução moderada a grave"
            alerta = "Alto risco cardiovascular e de progressão; acompanhamento conjunto."
        elif egfr >= 15:
            estagio = "G4"
            desc = "Redução grave da função renal"
            alerta = "Encaminhamento prioritário ao nefrologista e preparo para TRS."
        else:
            estagio = "G5"
            desc = "Falência renal / Doença renal terminal"
            alerta = "Terapia Renal Substitutiva (Diálise / Transplante renal imediato)."

        return ResultadoCKDEPI(
            egfr=egfr,
            estagio_drc=estagio,
            descricao_estagio=desc,
            alerta_clinico=alerta
        )

    @classmethod
    def classificar_imc(cls, peso_kg: float, altura_cm: float) -> Dict[str, any]:
        """Calcula IMC e classificação antropométrica."""
        if altura_cm <= 0 or peso_kg <= 0:
            return {"imc": 0.0, "classificacao": "Dados inválidos"}

        altura_m = altura_cm / 100.0
        imc = round(peso_kg / (altura_m * altura_m), 1)

        if imc < 18.5:
            cat = "Abaixo do peso (Magreza)"
        elif imc < 25.0:
            cat = "Peso normal (Eutrofia)"
        elif imc < 30.0:
            cat = "Sobrepeso (Pré-obesidade)"
        elif imc < 35.0:
            cat = "Obesidade Grau I"
        elif imc < 40.0:
            cat = "Obesidade Grau II (Severa)"
        else:
            cat = "Obesidade Grau III (Mórbida)"

        return {
            "imc": imc,
            "classificacao": cat,
            "peso_ideal_min": round(18.5 * (altura_m ** 2), 1),
            "peso_ideal_max": round(24.9 * (altura_m ** 2), 1)
        }
