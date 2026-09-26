import pytest
from app.services.livro_caixa import (
    MotorLivroCaixaMedico,
    LancamentoReceita,
    LancamentoDespesa,
)


def test_calcular_irpf_carne_leao_isencao():
    calc = MotorLivroCaixaMedico.calcular_irpf_carne_leao(2000.00)
    assert calc["imposto_devido"] == 0.0
    assert calc["aliquota_nominal"] == 0.0


def test_calcular_irpf_carne_leao_faixa_maxima():
    calc = MotorLivroCaixaMedico.calcular_irpf_carne_leao(10000.00)
    # 10000 * 0.275 - 896 = 2750 - 896 = 1854.00
    assert calc["imposto_devido"] == 1854.00
    assert calc["aliquota_nominal"] == 27.5


def test_demonstrativo_mensal_hibrido():
    receitas = [
        LancamentoReceita("2026-09-01", "Paciente A", "111", "PRESENCIAL", 400.0, "R1"),
        LancamentoReceita("2026-09-02", "Paciente B", "222", "TELEMEDICINA", 350.0, "R2"),
        LancamentoReceita("2026-09-03", "Paciente C", "333", "TELEMEDICINA", 350.0, "R3"),
    ]
    despesas = [
        LancamentoDespesa("2026-09-05", "Internet", "TELECOMUNICACOES", 200.0, dedutivel_carne_leao=True),
        LancamentoDespesa("2026-09-10", "Almoço", "OUTROS", 100.0, dedutivel_carne_leao=False),
    ]

    demo = MotorLivroCaixaMedico.gerar_demonstrativo_mensal(receitas, despesas, "09/2026")
    assert demo["receitas"]["total_bruto"] == 1100.0
    assert demo["receitas"]["consultorio_presencial"] == 400.0
    assert demo["receitas"]["home_office_telemedicina"] == 700.0
    assert demo["despesas"]["dedutiveis_carne_leao"] == 200.0
    assert demo["apuracao_fiscal"]["base_carne_leao"] == 900.0
