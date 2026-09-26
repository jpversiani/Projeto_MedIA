"""
Serviço de Livro Caixa e Gestão Fiscal para Médicos Autônomos (Carnê-Leão & DMED).
Permite apurar receitas de consultas presenciais e telemedicina, calcular despesas dedutíveis
e estimar o IRPF mensal do profissional da saúde.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional


@dataclass
class LancamentoReceita:
    data: str
    paciente_nome: str
    paciente_cpf: str
    tipo_consulta: str  # "PRESENCIAL" ou "TELEMEDICINA"
    valor: float
    numero_recibo: str
    metodo_pagamento: str = "PIX"


@dataclass
class LancamentoDespesa:
    data: str
    descricao: str
    categoria: str  # "ALUGUEL_CONSULTORIO", "TELECOMUNICACOES", "ANUIDADE_CRM", "MATERIAIS", "OUTROS"
    valor: float
    dedutivel_carne_leao: bool = True


class MotorLivroCaixaMedico:
    """Motor de cálculo e apuração de Carnê-Leão e livro caixa para médicos."""

    # Tabela Progressiva Mensal do IRPF (Vigente 2026)
    FAIXAS_IRPF = [
        {"limite": 2259.20, "aliquota": 0.0, "parcela_deduzir": 0.0},
        {"limite": 2826.65, "aliquota": 0.075, "parcela_deduzir": 169.44},
        {"limite": 3751.05, "aliquota": 0.15, "parcela_deduzir": 381.44},
        {"limite": 4664.68, "aliquota": 0.225, "parcela_deduzir": 662.77},
        {"limite": float("inf"), "aliquota": 0.275, "parcela_deduzir": 896.00},
    ]

    @classmethod
    def calcular_irpf_carne_leao(cls, base_calculo: float) -> Dict[str, float]:
        """Calcula o imposto devido no mês com base na tabela progressiva oficial."""
        if base_calculo <= 0:
            return {"base_calculo": 0.0, "aliquota_efetiva": 0.0, "imposto_devido": 0.0}

        aliquota_aplicada = 0.0
        parcela_deducao = 0.0

        for faixa in cls.FAIXAS_IRPF:
            if base_calculo <= faixa["limite"]:
                aliquota_aplicada = faixa["aliquota"]
                parcela_deducao = faixa["parcela_deduzir"]
                break

        imposto = max(0.0, (base_calculo * aliquota_aplicada) - parcela_deducao)
        aliquota_efetiva = (imposto / base_calculo) if base_calculo > 0 else 0.0

        return {
            "base_calculo": round(base_calculo, 2),
            "aliquota_nominal": round(aliquota_aplicada * 100, 1),
            "aliquota_efetiva_percentual": round(aliquota_efetiva * 100, 2),
            "imposto_devido": round(imposto, 2),
        }

    @classmethod
    def gerar_demonstrativo_mensal(
        cls,
        receitas: List[LancamentoReceita],
        despesas: List[LancamentoDespesa],
        mes_ano: str = "09/2026",
    ) -> Dict:
        """Gera o balancete completo do mês com segregação Presencial vs Telemedicina."""
        total_presencial = sum(r.valor for r in receitas if r.tipo_consulta == "PRESENCIAL")
        total_telemedicina = sum(r.valor for r in receitas if r.tipo_consulta == "TELEMEDICINA")
        total_receita_bruta = total_presencial + total_telemedicina

        despesas_dedutiveis = sum(d.valor for d in despesas if d.dedutivel_carne_leao)
        despesas_nao_dedutiveis = sum(d.valor for d in despesas if not d.dedutivel_carne_leao)
        total_despesas = despesas_dedutiveis + despesas_nao_dedutiveis

        base_calculo = max(0.0, total_receita_bruta - despesas_dedutiveis)
        calculo_irpf = cls.calcular_irpf_carne_leao(base_calculo)
        lucro_liquido_apos_imposto = total_receita_bruta - total_despesas - calculo_irpf["imposto_devido"]

        return {
            "competencia": mes_ano,
            "receitas": {
                "total_bruto": round(total_receita_bruta, 2),
                "consultorio_presencial": round(total_presencial, 2),
                "home_office_telemedicina": round(total_telemedicina, 2),
                "quantidade_consultas": len(receitas),
                "percentual_telemedicina": round((total_telemedicina / total_receita_bruta * 100) if total_receita_bruta > 0 else 0.0, 1),
            },
            "despesas": {
                "total_despesas": round(total_despesas, 2),
                "dedutiveis_carne_leao": round(despesas_dedutiveis, 2),
                "nao_dedutiveis": round(despesas_nao_dedutiveis, 2),
            },
            "apuracao_fiscal": {
                "base_carne_leao": calculo_irpf["base_calculo"],
                "aliquota_nominal_percentual": calculo_irpf["aliquota_nominal"],
                "aliquota_efetiva_percentual": calculo_irpf["aliquota_efetiva_percentual"],
                "imposto_a_recolher_darf": calculo_irpf["imposto_devido"],
                "codigo_darf": "0190",
            },
            "resultado_liquido_medico": round(lucro_liquido_apos_imposto, 2),
        }
