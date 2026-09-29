from datetime import date, datetime, timezone
from typing import List, Optional
import xml.etree.ElementTree as ET

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app.services.tiss_generator import (
    GuiaConsultaTISS,
    MotorFaturamentoTISS,
    RelatorioAuditoriaTISS,
)

router = APIRouter(prefix="/tiss", tags=["Faturamento TISS ANS 4.01"])


class GuiaConsultaRequest(BaseModel):
    numero_guia_prestador: str = Field(..., json_schema_extra={"example": "GUIA-2026-001"})
    registro_ans: str = Field(..., json_schema_extra={"example": "318011"}, min_length=6, max_length=6)
    nome_operadora: str = Field("Unimed / Bradesco Saúde", json_schema_extra={"example": "Bradesco Saúde"})
    numero_carteira: str = Field(..., json_schema_extra={"example": "9876543210123"})
    nome_beneficiario: str = Field(..., json_schema_extra={"example": "Maria Silva Santos"})
    cpf_beneficiario: Optional[str] = Field(None, json_schema_extra={"example": "12345678901"})
    cns_beneficiario: Optional[str] = Field(None, json_schema_extra={"example": "700000000000001"})
    codigo_cnes: str = Field(..., json_schema_extra={"example": "3180115"}, min_length=7, max_length=7)
    nome_contratado: str = Field("Consultório Particular MedIA", json_schema_extra={"example": "Consultório Particular MedIA"})
    crm_medico: str = Field("78421", json_schema_extra={"example": "78421"})
    uf_crm: str = Field("MG", json_schema_extra={"example": "MG"})
    cbos: str = Field("225125", json_schema_extra={"example": "225125"})
    data_atendimento: date = Field(default_factory=date.today)
    codigo_tuss_procedimento: str = Field("10101012", json_schema_extra={"example": "10101012"})
    descricao_procedimento: str = Field("Consulta médica em atenção primária/especializada")
    valor_procedimento: float = Field(150.00, json_schema_extra={"example": 150.00})
    cid10_principal: Optional[str] = Field(None, json_schema_extra={"example": "I10"})
    tipo_consulta: str = Field("1", json_schema_extra={"example": "1"})


class LoteTISSRequest(BaseModel):
    numero_lote: str = Field("1", json_schema_extra={"example": "1"})
    guias: Optional[List[GuiaConsultaRequest]] = None


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


@router.post("/exportar-lote-xml")
def exportar_lote_xml(dados: Optional[LoteTISSRequest] = None):
    """Gera e exporta arquivo consolidado XML de Lote TISS ANS 4.01.00 pronto para transmissão."""
    ns = "http://www.ans.gov.br/padroes/tiss/schemas"
    ET.register_namespace("ans", ns)

    root = ET.Element(f"{{{ns}}}mensagemTISS")
    cabecalho = ET.SubElement(root, f"{{{ns}}}cabecalho")
    identificacao = ET.SubElement(cabecalho, f"{{{ns}}}identificacaoTransacao")
    ET.SubElement(identificacao, f"{{{ns}}}tipoTransacao").text = "ENVIO_LOTE_GUIAS"
    numero_lote = dados.numero_lote if dados and dados.numero_lote else "1"
    ET.SubElement(identificacao, f"{{{ns}}}numeroTransacao").text = f"LOTE-TISS-{numero_lote}"
    ET.SubElement(identificacao, f"{{{ns}}}dataRegistroTransacao").text = date.today().isoformat()
    ET.SubElement(identificacao, f"{{{ns}}}horaRegistroTransacao").text = datetime.now().strftime("%H:%M:%S")

    origem = ET.SubElement(cabecalho, f"{{{ns}}}origem")
    ident_prestador = ET.SubElement(origem, f"{{{ns}}}identificacaoPrestador")
    ET.SubElement(ident_prestador, f"{{{ns}}}codigoPrestadorNaOperadora").text = "3180115"

    destino = ET.SubElement(cabecalho, f"{{{ns}}}destino")
    ET.SubElement(destino, f"{{{ns}}}registroANS").text = "318011"
    ET.SubElement(cabecalho, f"{{{ns}}}padrao").text = MotorFaturamentoTISS.VERSAO_TISS

    corpo = ET.SubElement(root, f"{{{ns}}}prestadorParaOperadora")
    lote = ET.SubElement(corpo, f"{{{ns}}}loteGuias")
    ET.SubElement(lote, f"{{{ns}}}numeroLote").text = numero_lote
    guias_node = ET.SubElement(lote, f"{{{ns}}}guiasTISS")

    # Guias a incluir
    lista_guias = dados.guias if dados and dados.guias else [
        GuiaConsultaRequest(
            numero_guia_prestador="TISS-2026-0001",
            registro_ans="318011",
            nome_operadora="Unimed",
            numero_carteira="9876543210123",
            nome_beneficiario="Maria Silva",
            cpf_beneficiario="12345678901",
            codigo_cnes="3180115",
            nome_contratado="Consultório Particular MedIA",
            crm_medico="78421",
            uf_crm="MG",
            cbos="225125",
            data_atendimento=date.today(),
            codigo_tuss_procedimento="10101012",
            descricao_procedimento="Consulta em consultório",
            valor_procedimento=250.00,
            cid10_principal="I10"
        ),
        GuiaConsultaRequest(
            numero_guia_prestador="TISS-2026-0002",
            registro_ans="318011",
            nome_operadora="Amil",
            numero_carteira="4567891230000",
            nome_beneficiario="João Santos",
            cpf_beneficiario="98765432100",
            codigo_cnes="3180115",
            nome_contratado="Consultório Particular MedIA",
            crm_medico="78421",
            uf_crm="MG",
            cbos="225125",
            data_atendimento=date.today(),
            codigo_tuss_procedimento="10101012",
            descricao_procedimento="Consulta em consultório",
            valor_procedimento=180.50,
            cid10_principal="E11"
        )
    ]

    for g_req in lista_guias:
        guia_node = ET.SubElement(guias_node, f"{{{ns}}}guiaConsulta")
        cab_guia = ET.SubElement(guia_node, f"{{{ns}}}cabecalhoConsulta")
        ET.SubElement(cab_guia, f"{{{ns}}}registroANS").text = g_req.registro_ans
        ET.SubElement(cab_guia, f"{{{ns}}}numeroGuiaPrestador").text = g_req.numero_guia_prestador

        dados_ben = ET.SubElement(guia_node, f"{{{ns}}}dadosBeneficiario")
        ET.SubElement(dados_ben, f"{{{ns}}}numeroCarteira").text = g_req.numero_carteira
        ET.SubElement(dados_ben, f"{{{ns}}}nomeBeneficiario").text = g_req.nome_beneficiario

        dados_cont = ET.SubElement(guia_node, f"{{{ns}}}dadosContratadoExecutante")
        ET.SubElement(dados_cont, f"{{{ns}}}codigoCNES").text = g_req.codigo_cnes
        ET.SubElement(dados_cont, f"{{{ns}}}nomeContratado").text = g_req.nome_contratado

        dados_prof = ET.SubElement(guia_node, f"{{{ns}}}profissionalExecutante")
        ET.SubElement(dados_prof, f"{{{ns}}}conselhoProfissional").text = "06"
        ET.SubElement(dados_prof, f"{{{ns}}}numeroConselhoProfissional").text = g_req.crm_medico
        ET.SubElement(dados_prof, f"{{{ns}}}UF").text = g_req.uf_crm
        ET.SubElement(dados_prof, f"{{{ns}}}cbos").text = g_req.cbos

        dados_atend = ET.SubElement(guia_node, f"{{{ns}}}dadosAtendimento")
        ET.SubElement(dados_atend, f"{{{ns}}}tipoConsulta").text = g_req.tipo_consulta
        ET.SubElement(dados_atend, f"{{{ns}}}dataAtendimento").text = g_req.data_atendimento.isoformat()

        proc = ET.SubElement(dados_atend, f"{{{ns}}}procedimento")
        ET.SubElement(proc, f"{{{ns}}}codigoTabela").text = "22"
        ET.SubElement(proc, f"{{{ns}}}codigoProcedimento").text = g_req.codigo_tuss_procedimento
        ET.SubElement(proc, f"{{{ns}}}valorProcedimento").text = f"{g_req.valor_procedimento:.2f}"

    epilogo = ET.SubElement(root, f"{{{ns}}}epilogo")
    ET.SubElement(epilogo, f"{{{ns}}}hash").text = f"TISS-HASH-LOTE-{numero_lote}"

    xml_content = ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    return Response(
        content=xml_content,
        media_type="application/xml; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=LOTE_TISS_4.01_{numero_lote}.xml"
        }
    )
