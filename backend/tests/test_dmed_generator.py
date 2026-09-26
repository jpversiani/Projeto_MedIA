import pytest
from datetime import date
from app.services.dmed_generator import MotorFiscalDMED, DeclaracaoDMED, LancamentoDespesaMedica


def test_gerar_arquivo_magnetico_dmed():
    lancamentos = [
        LancamentoDespesaMedica(
            cpf_responsavel_pagamento="12345678909",
            nome_responsavel_pagamento="MARIA DAS GRACAS SILVA",
            cpf_beneficiario="12345678909",
            data_nascimento_beneficiario=date(1978, 5, 22),
            nome_beneficiario="MARIA DAS GRACAS SILVA",
            valor_pago=350.00,
            data_servico=date(2025, 6, 15)
        ),
        LancamentoDespesaMedica(
            cpf_responsavel_pagamento="98765432100",
            nome_responsavel_pagamento="JOSE ANTONIO SANTOS",
            cpf_beneficiario=None,
            data_nascimento_beneficiario=date(2018, 10, 10),
            nome_beneficiario="LUCAS SANTOS",
            valor_pago=250.50,
            data_servico=date(2025, 7, 20)
        )
    ]

    declaracao = DeclaracaoDMED(
        ano_calendario=2025,
        cnpj_prestador="12345678000199",
        nome_empresarial="CONSULTORIO PARTICULAR MEDIA LTDA",
        lancamentos=lancamentos
    )

    txt = MotorFiscalDMED.gerar_arquivo_magnetico(declaracao)
    linhas = txt.strip().split("\r\n")

    assert len(linhas) == 4  # Header + 2 ROPs + Trailer
    assert linhas[0].startswith("DMED|2025|12345678000199|CONSULTORIO PARTICULAR MEDIA LTDA")
    assert linhas[1].startswith("ROP|12345678909|MARIA DAS GRACAS SILVA")
    assert "000000035000" in linhas[1]  # R$ 350.00 em centavos (12 digitos)
    assert linhas[3].startswith("T9|00000004|")  # 4 registros
    assert "000000000060050" in linhas[3]  # R$ 600.50 em centavos (15 digitos)


def test_validar_cpf_algoritmo():
    assert MotorFiscalDMED.validar_cpf("11111111111") is False  # Sequência
    assert MotorFiscalDMED.validar_cpf("123") is False
    assert MotorFiscalDMED.validar_cpf("00000000000") is False
