import pytest
from app.services.prescricao_digital_cfm import MotorPrescricaoCFM, TipoPrescricao


def test_emitir_prescricao_e_validar_publicamente():
    doc = MotorPrescricaoCFM.emitir_prescricao(
        paciente_nome="Juliana Mendes Prado",
        paciente_cpf="45678912344",
        medico_nome="Dr. João Paulo Versiani",
        medico_crm="78421",
        medico_uf="MG",
        medico_rqe="39412",
        itens=[
            {
                "farmaco": "Amoxicilina + Clavulanato",
                "concentracao": "875mg + 125mg",
                "forma_farmaceutica": "comprimido revestido",
                "posologia": "1 comprimido de 12 em 12 horas por 7 dias",
                "quantidade_total": "14 comprimidos"
            }
        ],
        tipo=TipoPrescricao.ANTIBIOTICO,
        instrucoes_gerais="Ingerir no início de uma refeição para minimizar intolerância gastrointestinal."
    )

    assert doc.codigo_validacao.startswith("CFM-")
    assert doc.tipo_prescricao == TipoPrescricao.ANTIBIOTICO
    assert len(doc.hash_integridade_sha256) == 64
    assert len(doc.itens) == 1

    # Validação pública
    val = MotorPrescricaoCFM.validar_documento_publico(doc.codigo_validacao)
    assert val is not None
    assert val["codigo"] == doc.codigo_validacao
    assert val["status"] == "VALIDA"
    assert "Amoxicilina" in val["itens"][0]


def test_emitir_atestado_e_validar():
    doc = MotorPrescricaoCFM.emitir_atestado(
        paciente_nome="Roberto Carlos Fagundes",
        paciente_cpf="98765432100",
        medico_nome="Dr. João Paulo Versiani",
        medico_crm="78421",
        medico_uf="MG",
        dias_afastamento=5,
        cid10="I10"
    )
    assert doc.codigo_validacao.startswith("ATE-")
    assert doc.dias_afastamento == 5

    val = MotorPrescricaoCFM.validar_documento_publico(doc.codigo_validacao)
    assert val is not None
    assert val["dias_afastamento"] == 5
    assert val["cid10"] == "I10"


def test_validar_codigo_inexistente():
    val = MotorPrescricaoCFM.validar_documento_publico("CFM-0000-0000-0000")
    assert val is None
