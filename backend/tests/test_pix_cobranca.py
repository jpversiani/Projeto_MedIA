import pytest
from app.services.pix_cobranca import MotorPixCobranca, DadosCobrancaPix, calcular_crc16


def test_calcular_crc16():
    # Teste de integridade do algoritmo CRC16-CCITT
    crc = calcular_crc16("00020126360014br.gov.bcb.pix0114+551199999999520400005303986540510.005802BR5913Fulano de Tal6008SAO PAULO62070503***6304")
    assert len(crc) == 4
    assert crc.isalnum()


def test_gerar_pix_copia_e_cola_sucesso():
    dados = DadosCobrancaPix(
        chave_pix="12345678901",
        nome_beneficiario="Dr. Joao Paulo Versiani",
        cidade_beneficiario="Montes Claros",
        valor=350.00,
        identificador_transacao="CONSULTA101",
        descricao_consulta="Teleconsulta Cardiologia"
    )
    resultado = MotorPixCobranca.gerar_pix_copia_e_cola(dados)

    assert resultado["txid"] == "CONSULTA101"
    assert resultado["chave_pix"] == "12345678901"
    assert resultado["beneficiario"] == "DR. JOAO PAULO VERSIANI"
    assert resultado["valor"] == "350.00"
    assert "br.gov.bcb.pix" in resultado["pix_copia_e_cola"]
    assert resultado["pix_copia_e_cola"].endswith(resultado["crc16"])
    assert len(resultado["hash_seguranca"]) == 64
