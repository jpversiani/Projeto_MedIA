from app.models.documento_cfm import DocumentoCFM
from app.services.prescricao_digital_cfm import MotorPrescricaoCFM, TipoPrescricao


def test_emitir_prescricao_e_validar_publicamente(db_session):
    doc = MotorPrescricaoCFM.emitir_prescricao(
        paciente_nome="Juliana Mendes Prado",
        paciente_cpf="45678912344",
        medico_nome="Dra. Francelli Neves Versiani",
        medico_crm="78421",
        medico_uf="MG",
        medico_rqe="39412",
        itens=[
            {
                "farmaco": "Amoxicilina + Clavulanato",
                "concentracao": "875mg + 125mg",
                "forma_farmaceutica": "comprimido revestido",
                "posologia": "1 comprimido de 12 em 12 horas por 7 dias",
                "quantidade_total": "14 comprimidos",
            }
        ],
        tipo=TipoPrescricao.ANTIBIOTICO,
        instrucoes_gerais="Ingerir no início de uma refeição para minimizar intolerância gastrointestinal.",
        db=db_session,
    )

    assert doc.codigo_validacao.startswith("CFM-")
    assert doc.tipo_prescricao == TipoPrescricao.ANTIBIOTICO
    assert len(doc.hash_integridade_sha256) == 64
    assert len(doc.itens) == 1

    # Validação pública
    val = MotorPrescricaoCFM.validar_documento_publico(doc.codigo_validacao, db=db_session)
    assert val is not None
    assert val["codigo"] == doc.codigo_validacao
    assert val["status"] == "VALIDA"
    assert "Amoxicilina" in val["itens"][0]


def test_emitir_atestado_e_validar(db_session):
    doc = MotorPrescricaoCFM.emitir_atestado(
        paciente_nome="Roberto Carlos Fagundes",
        paciente_cpf="98765432100",
        medico_nome="Dra. Francelli Neves Versiani",
        medico_crm="78421",
        medico_uf="MG",
        dias_afastamento=5,
        cid10="I10",
        db=db_session,
    )
    assert doc.codigo_validacao.startswith("ATE-")
    assert doc.dias_afastamento == 5

    val = MotorPrescricaoCFM.validar_documento_publico(doc.codigo_validacao, db=db_session)
    assert val is not None
    assert val["dias_afastamento"] == 5
    assert val["cid10"] == "I10"


def test_validar_codigo_inexistente(db_session):
    val = MotorPrescricaoCFM.validar_documento_publico("CFM-0000-0000-0000", db=db_session)
    assert val is None


def test_receita_sobrevive_ao_reinicio(client, db_session):
    """Critério T2 do Handoff: emite documento via HTTP, limpa cache/sessão da memória e valida que persiste no banco."""
    payload = {
        "paciente_nome": "Marcos Silveira Rocha",
        "paciente_cpf": "11122233344",
        "medico_nome": "Dr. Fernando Augusto",
        "medico_crm": "12345",
        "medico_uf": "MG",
        "tipo": "SIMPLES",
        "itens": [
            {
                "farmaco": "Dipirona Monoidratada",
                "concentracao": "500mg",
                "forma_farmaceutica": "comprimido",
                "posologia": "1 comprimido se dor ou febre até de 6 em 6 horas",
                "quantidade_total": "1 caixa",
            }
        ],
        "instrucoes_gerais": "Uso se necessário.",
    }

    resp = client.post("/api/v1/prescricao/emitir", json=payload)
    assert resp.status_code == 201
    dados = resp.json()
    codigo = dados["codigo_validacao"]
    assert codigo.startswith("CFM-")

    # Simula reinício / isolamento de memória: limpa identity map e cache local
    db_session.expire_all()

    # Validação pública via API JSON
    val_resp = client.get(f"/api/v1/prescricao/validar/{codigo}")
    assert val_resp.status_code == 200
    val_dados = val_resp.json()
    assert val_dados["codigo"] == codigo
    assert val_dados["status"] == "VALIDA"
    assert "Dipirona" in val_dados["itens"][0]

    # Validação pública via página HTML (acessada pelo QR code da farmácia)
    html_resp = client.get(f"/api/v1/prescricao/validar-html/{codigo}")
    assert html_resp.status_code == 200
    assert "DOCUMENTO MÉDICO VÁLIDO E REGISTRADO" in html_resp.text
    assert codigo in html_resp.text

    # Confirmação direta no banco de dados na tabela documentos_cfm
    doc_banco = db_session.query(DocumentoCFM).filter_by(codigo_validacao=codigo).first()
    assert doc_banco is not None
    assert doc_banco.paciente_cpf == "11122233344"
    assert doc_banco.medico_crm == "12345"
    assert doc_banco.tipo == "RECEITA"
