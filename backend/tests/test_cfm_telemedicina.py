import pytest
from app.services.cfm_telemedicina import (
    MotorCFMTelemedicina,
    MedicoIdentificacaoCFM,
    PacienteIdentificacaoCFM,
)


def test_gerar_termo_consentimento_tcle_sucesso():
    paciente = PacienteIdentificacaoCFM(
        nome_completo="Carlos Eduardo Pereira",
        cpf="12345678909",
        telefone_whatsapp="38999887766"
    )
    medico = MedicoIdentificacaoCFM(
        nome_completo="Dr. João Paulo Versiani",
        crm="78421",
        uf_crm="MG",
        rqe="39412",
        especialidade="Cardiologia"
    )

    tcle = MotorCFMTelemedicina.gerar_termo_consentimento_tcle(paciente, medico, modalidade="TELECONSULTA")
    assert tcle["norma_regulamentar"] == "CFM-2314/2022"
    assert "Dr. João Paulo Versiani" in tcle["texto_integral"]
    assert "CRM: 78421-MG" in tcle["texto_integral"]
    assert "RQE: 39412" in tcle["texto_integral"]
    assert "Carlos Eduardo Pereira" in tcle["texto_integral"]
    assert "12345678909" in tcle["texto_integral"]
    assert len(tcle["hash_integridade_sha256"]) == 64


def test_registrar_aceite_tcle():
    paciente = PacienteIdentificacaoCFM(
        nome_completo="Mariana Souza Alencar",
        cpf="98765432100"
    )
    registro = MotorCFMTelemedicina.registrar_aceite_tcle(
        paciente=paciente,
        metodo="ELETRONICO_WHATSAPP",
        ip_origem="189.12.34.56"
    )
    assert registro.consentimento_id.startswith("TCLE-")
    assert registro.paciente_cpf == "98765432100"
    assert registro.metodo_aceite == "ELETRONICO_WHATSAPP"
    assert len(registro.hash_tcle) == 64


def test_validar_requisitos_medico_cfm():
    medico_valido = MedicoIdentificacaoCFM(
        nome_completo="Dra. Letícia Mendes",
        crm="54321",
        uf_crm="MG"
    )
    erros = MotorCFMTelemedicina.validar_requisitos_medico(medico_valido)
    assert len(erros) == 0

    medico_invalido = MedicoIdentificacaoCFM(
        nome_completo="A",
        crm="",
        uf_crm="MINAS"
    )
    erros_inv = MotorCFMTelemedicina.validar_requisitos_medico(medico_invalido)
    assert len(erros_inv) == 3


def test_gerar_link_paciente_whatsapp():
    link_info = MotorCFMTelemedicina.gerar_link_paciente(
        codigo_sala="sala_teste_99",
        nome_paciente="Roberto Fagundes",
        nome_medico="Dr. João Paulo Versiani",
        base_url="https://mediahealth.com.br",
        telefone_whatsapp="38991234567"
    )
    assert "sala_teste_99" in link_info["url_acesso_paciente"]
    assert "https://api.whatsapp.com/send?phone=5538991234567" in link_info["link_whatsapp_direto"]
    assert "Roberto Fagundes" in link_info["mensagem_formatada"]


def test_emitir_registro_conversao_presencial():
    medico = MedicoIdentificacaoCFM(
        nome_completo="Dr. João Paulo Versiani",
        crm="78421",
        uf_crm="MG"
    )
    registro = MotorCFMTelemedicina.emitir_registro_conversao_presencial(
        teleconsulta_id=101,
        paciente_nome="Juliana Prado",
        medico=medico,
        motivo_clinico="Dor precordial com sudorese fria, suspeita de síndrome coronariana aguda."
    )
    assert registro["status"] == "CONVERTIDA_PRESENCIAL"
    assert "ART. 3º CFM 2.314/2022" in registro["relatorio"]
    assert len(registro["hash_registro"]) == 64
