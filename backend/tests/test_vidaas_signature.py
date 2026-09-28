"""
Testes unitários para o conector de assinatura digital ICP-Brasil VIDAAS (Valid PSC).
"""
import pytest
from app.services.vidaas_signature_service import (
    VidaasSignatureService,
    VidaasConfig,
    AssinaturaDocumentoRequest,
)


def test_calcular_hash_sha256_canonica():
    service = VidaasSignatureService()
    conteudo = "Receita Médica Digital - MedIA Practice OS"
    hash1 = service.calcular_hash_documento(conteudo)
    hash2 = service.calcular_hash_documento(conteudo.encode("utf-8"))
    assert hash1 == hash2
    assert len(hash1) == 64


def test_solicitar_assinatura_em_nuvem_fluxo_push():
    service = VidaasSignatureService(VidaasConfig(ambiente="HOMOLOGACAO"))
    req = AssinaturaDocumentoRequest(
        documento_id="REC-2026-001",
        tipo_documento="CONTROLE_ESPECIAL",
        conteudo_bytes=b"PDF_CONTEUDO_RECEITA_MEDICA",
        cpf_medico="11122233344",
        crm_medico="78421",
        uf_crm="MG"
    )
    res = service.solicitar_assinatura_em_nuvem(req)
    assert res["sucesso"] is True
    assert res["status"] == "PENDENTE_AUTORIZACAO_PUSH"
    assert "VIDAAS-" in res["solicitacao_id"]
    assert len(res["hash_sha256"]) == 64


def test_confirmar_assinatura_pades_com_carimbo_tempo():
    service = VidaasSignatureService()
    recibo = service.confirmar_assinatura_pades(
        solicitacao_id="VIDAAS-2026-AB12CD34EF56",
        documento_id="REC-2026-001",
        cpf_medico="11122233344",
        crm_medico="78421",
        uf_crm="MG"
    )
    assert recibo.status == "ASSINADO"
    assert "ACT-VALID-ICP-BRASIL" in recibo.carimbo_tempo_icp
    assert "validador.iti.gov.br" in recibo.url_qrcode_validacao
    assert "78421" in recibo.certificado_titular
