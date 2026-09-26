import pytest
from app.services.calculadoras_clinicas import CalculadorasClinicas


def test_calcular_framingham_alto_risco():
    resultado = CalculadorasClinicas.calcular_framingham(
        sexo="M",
        idade=62,
        colesterol_total=260.0,
        colesterol_hdl=38.0,
        pressao_sistolica=155.0,
        em_tratamento_has=True,
        fumante=True,
        diabetico=True
    )
    assert resultado.pontuacao_total > 15
    assert resultado.risco_percentual >= 20.0
    assert "Alto Risco" in resultado.categoria_risco


def test_calcular_framingham_baixo_risco():
    resultado = CalculadorasClinicas.calcular_framingham(
        sexo="F",
        idade=28,
        colesterol_total=170.0,
        colesterol_hdl=65.0,
        pressao_sistolica=115.0,
        em_tratamento_has=False,
        fumante=False,
        diabetico=False
    )
    assert resultado.risco_percentual < 10.0
    assert "Baixo Risco" in resultado.categoria_risco


def test_calcular_ckd_epi_estagios():
    # Mulher jovem com função normal
    res_normal = CalculadorasClinicas.calcular_ckd_epi(creatinina_serica=0.8, idade=35, sexo="F")
    assert res_normal.egfr >= 90.0
    assert res_normal.estagio_drc == "G1"

    # Idoso com redução moderada a grave
    res_drc = CalculadorasClinicas.calcular_ckd_epi(creatinina_serica=2.2, idade=72, sexo="M")
    assert res_drc.egfr < 45.0
    assert res_drc.estagio_drc in ("G3b", "G4")


def test_classificar_imc():
    imc_eutrofico = CalculadorasClinicas.classificar_imc(peso_kg=70.0, altura_cm=175.0)
    assert imc_eutrofico["imc"] == 22.9
    assert "Eutrofia" in imc_eutrofico["classificacao"]

    imc_obesidade = CalculadorasClinicas.classificar_imc(peso_kg=105.0, altura_cm=170.0)
    assert imc_obesidade["imc"] == 36.3
    assert "Obesidade Grau II" in imc_obesidade["classificacao"]
