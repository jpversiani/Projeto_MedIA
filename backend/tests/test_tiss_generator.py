import pytest
from datetime import date
from app.services.tiss_generator import MotorFaturamentoTISS, GuiaConsultaTISS


def test_gerar_xml_guia_consulta_sucesso():
    guia = GuiaConsultaTISS(
        numero_guia_prestador="GUIA-2026-999",
        registro_ans="318011",
        nome_operadora="Bradesco Saúde",
        numero_carteira="123456789012345",
        nome_beneficiario="Carlos Eduardo Pereira",
        cpf_beneficiario="12345678909",
        cns_beneficiario="700000000000001",
        codigo_cnes="3180115",
        nome_contratado="Consultório Particular MedIA",
        crm_medico="78421",
        uf_crm="MG",
        cbos="225125",
        data_atendimento=date(2026, 9, 20),
        cid10_principal="I10"
    )

    relatorio = MotorFaturamentoTISS.gerar_xml_guia_consulta(guia)
    assert relatorio.valida is True
    assert relatorio.conformidade_ans is True
    assert len(relatorio.alertas_glosa) == 0
    assert "<ans:mensagemTISS" in relatorio.xml_gerado
    assert "<ans:codigoProcedimento>10101012</ans:codigoProcedimento>" in relatorio.xml_gerado
    assert "<ans:padrao>4.01.00</ans:padrao>" in relatorio.xml_gerado


def test_validar_guia_detecta_glosas():
    guia_invalida = GuiaConsultaTISS(
        numero_guia_prestador="1",  # Muito curto
        registro_ans="123",        # Deve ter 6 dígitos
        nome_operadora="Operadora X",
        numero_carteira="12",      # Muito curto
        nome_beneficiario="Ab",    # Muito curto
        cpf_beneficiario=None,
        cns_beneficiario=None,
        codigo_cnes="123",         # Deve ter 7 dígitos
        nome_contratado="Clínica",
        crm_medico="",             # Vazio
        uf_crm="MG",
        cbos="225125",
        data_atendimento=date(2030, 1, 1),  # Futura
        cid10_principal="INVALIDO"
    )

    alertas = MotorFaturamentoTISS.validar_guia(guia_invalida)
    assert len(alertas) >= 5
    assert any("GLOSA_01" in a for a in alertas)
    assert any("GLOSA_02" in a for a in alertas)
    assert any("GLOSA_05" in a for a in alertas)
    assert any("GLOSA_08" in a for a in alertas)
