from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

from app.services.tiss_generator import (
    MotorFaturamentoTISS,
    GuiaConsultaTISS,
    RelatorioAuditoriaTISS
)

router = APIRouter(prefix="/tiss", tags=["Faturamento TISS ANS 4.01"])


class GuiaConsultaRequest(BaseModel):
    numero_guia_prestador: str = Field(..., example="GUIA-2026-001")
    registro_ans: str = Field(..., example="318011", min_length=6, max_length=6)
    nome_operadora: str = Field("Unimed / Bradesco Saúde", example="Bradesco Saúde")
    numero_carteira: str = Field(..., example="9876543210123")
    nome_beneficiario: str = Field(..., example="Maria Silva Santos")
    cpf_beneficiario: Optional[str] = Field(None, example="12345678901")
    cns_beneficiario: Optional[str] = Field(None, example="700000000000001")
    codigo_cnes: str = Field(..., example="3180115", min_length=7, max_length=7)
    nome_contratado: str = Field("Consultório Particular MedIA", example="Consultório Particular MedIA")
    crm_medico: str = Field("78421", example="78421")
    uf_crm: str = Field("MG", example="MG")
    cbos: str = Field("225125", example="225125")
    data_atendimento: date = Field(default_factory=date.today)
    codigo_tuss_procedimento: str = Field("10101012", example="10101012")
    descricao_procedimento: str = Field("Consulta médica em atenção primária/especializada")
    valor_procedimento: float = Field(150.00, example=150.00)
    cid10_principal: Optional[str] = Field(None, example="I10")
    tipo_consulta: str = Field("1", example="1")


@router.post("/gerar-guia-xml")
def gerar_guia_xml(dados: GuiaConsultaRequest):
    """Gera o XML padrão TISS ANS 4.01.00 pronto para faturamento com operadoras."""
    guia = GuiaConsultaTISS(**dados.model_dump())
    relatorio = MotorFaturamentoTISS.gerar_xml_guia_consulta(guia)
    
    return {
        "valida": relatorio.valida,
        "numero_guia": relatorio.numero_guia,
        "alertas_glosa": relatorio.alertas_glosa,
        "conformidade_ans": relatorio.conformidade_ans,
        "xml_gerado": relatorio.xml_gerado
    }


@router.post("/validar-glosas")
def validar_glosas(dados: GuiaConsultaRequest):
    """Audita preventivamente campos obrigatórios antes do envio para evitar glosa administrativa."""
    guia = GuiaConsultaTISS(**dados.model_dump())
    alertas = MotorFaturamentoTISS.validar_guia(guia)
    return {
        "numero_guia": guia.numero_guia_prestador,
        "aprovado_para_envio": len(alertas) == 0,
        "total_alertas": len(alertas),
        "alertas": alertas
    }
