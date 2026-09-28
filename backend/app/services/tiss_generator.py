"""
Motor de Faturamento TISS ANS 4.01.00 — Projeto MedIA (Saúde 4.0)
Geração, estruturação XML e auditoria anti-glosas de Guias de Consulta e SADT.
Conformidade: Padrão TISS ANS versão 4.01.00 e Tabela TUSS.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET
import re
import uuid


def gerar_numero_guia() -> str:
    """Gera um número sequencial único para a Guia TISS."""
    return f"TISS-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


@dataclass
class GuiaConsultaTISS:
    numero_guia_prestador: str
    registro_ans: str
    nome_operadora: str
    numero_carteira: str
    nome_beneficiario: str
    cpf_beneficiario: Optional[str]
    cns_beneficiario: Optional[str]
    codigo_cnes: str
    nome_contratado: str
    crm_medico: str
    uf_crm: str
    cbos: str
    data_atendimento: date
    codigo_tuss_procedimento: str = "10101012"  # Consulta em consultório (TUSS padrão)
    descricao_procedimento: str = "Consulta médica em atenção primária/especializada"
    valor_procedimento: float = 150.00
    cid10_principal: Optional[str] = None
    tipo_consulta: str = "1"  # 1: Primeira Consulta, 2: Retorno, 3: Pré-natal


@dataclass
class RelatorioAuditoriaTISS:
    valida: bool
    numero_guia: str
    alertas_glosa: List[str] = field(default_factory=list)
    conformidade_ans: bool = False
    xml_gerado: Optional[str] = None


class MotorFaturamentoTISS:
    """Motor de geração e validação de guias TISS ANS 4.01.00."""

    VERSAO_TISS = "4.01.00"
    TUSS_CONSULTA_PADRAO = "10101012"

    @classmethod
    def validar_guia(cls, guia: GuiaConsultaTISS) -> List[str]:
        """Audita campos obrigatórios para prevenir glosas administrativas."""
        alertas = []

        if not guia.numero_guia_prestador or len(guia.numero_guia_prestador) < 3:
            alertas.append("GLOSA_01: Número da guia do prestador ausente ou inválido.")

        if not guia.registro_ans or len(guia.registro_ans) != 6:
            alertas.append("GLOSA_02: Registro ANS da operadora deve conter exatamente 6 dígitos.")

        if not guia.numero_carteira or len(guia.numero_carteira) < 5:
            alertas.append("GLOSA_03: Número da carteira do beneficiário inválido.")

        if not guia.nome_beneficiario or len(guia.nome_beneficiario.strip()) < 3:
            alertas.append("GLOSA_04: Nome do beneficiário incompleto ou não informado.")

        if not guia.codigo_cnes or len(guia.codigo_cnes) != 7:
            alertas.append("GLOSA_05: Código CNES do estabelecimento deve ter exatamente 7 dígitos.")

        if not guia.crm_medico or not guia.crm_medico.isalnum():
            alertas.append("GLOSA_06: CRM do profissional médico inválido.")

        if not guia.codigo_tuss_procedimento or len(guia.codigo_tuss_procedimento) != 8:
            alertas.append("GLOSA_07: Código TUSS do procedimento deve conter 8 dígitos numéricos.")

        if guia.data_atendimento > date.today():
            alertas.append("GLOSA_08: Data do atendimento não pode ser futura.")

        if guia.cid10_principal:
            padrao_cid = r"^[A-Z][0-9]{2}(\.[0-9]{1,2})?$"
            if not re.match(padrao_cid, guia.cid10_principal):
                alertas.append(f"GLOSA_09: CID-10 '{guia.cid10_principal}' fora do padrão oficial CID-10/OMS.")

        return alertas

    @classmethod
    def gerar_xml_guia_consulta(cls, guia: GuiaConsultaTISS) -> RelatorioAuditoriaTISS:
        """Gera o payload XML formal do padrão TISS ANS 4.01.00."""
        alertas = cls.validar_guia(guia)
        valida = len(alertas) == 0

        # Montagem do XML estruturado com namespace TISS
        ns = "http://www.ans.gov.br/padroes/tiss/schemas"
        ET.register_namespace("ans", ns)

        root = ET.Element(f"{{{ns}}}mensagemTISS")
        
        # Cabeçalho
        cabecalho = ET.SubElement(root, f"{{{ns}}}cabecalho")
        identificacao = ET.SubElement(cabecalho, f"{{{ns}}}identificacaoTransacao")
        ET.SubElement(identificacao, f"{{{ns}}}tipoTransacao").text = "ENVIO_LOTE_GUIAS"
        ET.SubElement(identificacao, f"{{{ns}}}numeroTransacao").text = f"TX-{guia.numero_guia_prestador}"
        ET.SubElement(identificacao, f"{{{ns}}}dataRegistroTransacao").text = date.today().isoformat()
        ET.SubElement(identificacao, f"{{{ns}}}horaRegistroTransacao").text = datetime.now().strftime("%H:%M:%S")
        
        origem = ET.SubElement(cabecalho, f"{{{ns}}}origem")
        ident_prestador = ET.SubElement(origem, f"{{{ns}}}identificacaoPrestador")
        ET.SubElement(ident_prestador, f"{{{ns}}}codigoPrestadorNaOperadora").text = guia.codigo_cnes
        
        destino = ET.SubElement(cabecalho, f"{{{ns}}}destino")
        ET.SubElement(destino, f"{{{ns}}}registroANS").text = guia.registro_ans
        ET.SubElement(cabecalho, f"{{{ns}}}padrao").text = cls.VERSAO_TISS

        # Corpo da Guia
        corpo = ET.SubElement(root, f"{{{ns}}}prestadorParaOperadora")
        lote = ET.SubElement(corpo, f"{{{ns}}}loteGuias")
        ET.SubElement(lote, f"{{{ns}}}numeroLote").text = "1"
        
        guias = ET.SubElement(lote, f"{{{ns}}}guiasTISS")
        guia_node = ET.SubElement(guias, f"{{{ns}}}guiaConsulta")
        
        # Dados da Guia
        cab_guia = ET.SubElement(guia_node, f"{{{ns}}}cabecalhoConsulta")
        ET.SubElement(cab_guia, f"{{{ns}}}registroANS").text = guia.registro_ans
        ET.SubElement(cab_guia, f"{{{ns}}}numeroGuiaPrestador").text = guia.numero_guia_prestador
        
        dados_beneficiario = ET.SubElement(guia_node, f"{{{ns}}}dadosBeneficiario")
        ET.SubElement(dados_beneficiario, f"{{{ns}}}numeroCarteira").text = guia.numero_carteira
        ET.SubElement(dados_beneficiario, f"{{{ns}}}nomeBeneficiario").text = guia.nome_beneficiario
        if guia.cpf_beneficiario:
            ET.SubElement(dados_beneficiario, f"{{{ns}}}cpf").text = guia.cpf_beneficiario
        if guia.cns_beneficiario:
            ET.SubElement(dados_beneficiario, f"{{{ns}}}numeroCNS").text = guia.cns_beneficiario

        dados_contratado = ET.SubElement(guia_node, f"{{{ns}}}dadosContratadoExecutante")
        ET.SubElement(dados_contratado, f"{{{ns}}}codigoCNES").text = guia.codigo_cnes
        ET.SubElement(dados_contratado, f"{{{ns}}}nomeContratado").text = guia.nome_contratado

        dados_profissional = ET.SubElement(guia_node, f"{{{ns}}}profissionalExecutante")
        conselho = ET.SubElement(dados_profissional, f"{{{ns}}}conselhoProfissional")
        ET.SubElement(conselho, f"{{{ns}}}codigoConselho").text = "CRM"
        ET.SubElement(conselho, f"{{{ns}}}numeroConselho").text = guia.crm_medico
        ET.SubElement(conselho, f"{{{ns}}}uf").text = guia.uf_crm
        ET.SubElement(dados_profissional, f"{{{ns}}}cbos").text = guia.cbos

        dados_atendimento = ET.SubElement(guia_node, f"{{{ns}}}dadosAtendimento")
        ET.SubElement(dados_atendimento, f"{{{ns}}}tipoConsulta").text = guia.tipo_consulta
        ET.SubElement(dados_atendimento, f"{{{ns}}}dataAtendimento").text = guia.data_atendimento.isoformat()
        
        procedimento = ET.SubElement(dados_atendimento, f"{{{ns}}}procedimento")
        ET.SubElement(procedimento, f"{{{ns}}}codigoTabela").text = "22"  # TUSS Procedimentos e Eventos em Saúde
        ET.SubElement(procedimento, f"{{{ns}}}codigoProcedimento").text = guia.codigo_tuss_procedimento
        ET.SubElement(procedimento, f"{{{ns}}}descricaoProcedimento").text = guia.descricao_procedimento
        ET.SubElement(procedimento, f"{{{ns}}}valorProcedimento").text = f"{guia.valor_procedimento:.2f}"

        if guia.cid10_principal:
            ET.SubElement(dados_atendimento, f"{{{ns}}}diagnosticoCID").text = guia.cid10_principal

        # Epílogo com Hash
        epilogo = ET.SubElement(root, f"{{{ns}}}epilogo")
        ET.SubElement(epilogo, f"{{{ns}}}hash").text = "SIMULATED_TISS_HASH"

        xml_string = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")

        return RelatorioAuditoriaTISS(
            valida=valida,
            numero_guia=guia.numero_guia_prestador,
            alertas_glosa=alertas,
            conformidade_ans=valida,
            xml_gerado=xml_string
        )


class TISSGenerator(MotorFaturamentoTISS):
    """
    Classe de compatibilidade para faturamento TISS ANS e geração fiscal DMED.
    """
    VERSAO_TISS = "4.01.00"

    @classmethod
    def gerar_guia_consulta_xml(
        cls,
        numero_guia: str,
        operadora_registro_ans: str,
        paciente_nome: str,
        numero_carteira: str,
        paciente_cpf: Optional[str] = None,
        paciente_cns: Optional[str] = None,
        medico_nome: str = "Dr. MedIA",
        medico_crm: str = "123456",
        medico_uf: str = "MG",
        cbo: str = "225142",
        cnes_executante: str = "3180115",
        cid10: Optional[str] = None,
        ciap2: Optional[str] = None,
        procedimento_tuss: str = "10101012",
        valor_procedimento: float = 150.0,
        tipo_consulta: str = "1",
    ) -> str:
        """Gera o XML no padrão TISS ANS para Guia de Consulta."""
        ns = "http://www.ans.gov.br/padroes/tiss/schemas"
        ET.register_namespace("ans", ns)
        
        root = ET.Element(f"{{{ns}}}mensagemTISS")
        
        cabecalho = ET.SubElement(root, f"{{{ns}}}cabecalho")
        identificacao_transacao = ET.SubElement(cabecalho, f"{{{ns}}}identificacaoTransacao")
        ET.SubElement(identificacao_transacao, f"{{{ns}}}tipoTransacao").text = "ENVIO_LOTE_GUIAS"
        ET.SubElement(identificacao_transacao, f"{{{ns}}}numeroSequencialTransacao").text = str(uuid.uuid4().int)[:10]
        ET.SubElement(identificacao_transacao, f"{{{ns}}}dataRegistroTransacao").text = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ET.SubElement(identificacao_transacao, f"{{{ns}}}horaRegistroTransacao").text = datetime.now(timezone.utc).strftime("%H:%M:%S")
        
        origem = ET.SubElement(cabecalho, f"{{{ns}}}origem")
        ET.SubElement(origem, f"{{{ns}}}identificacaoPrestador").text = cnes_executante
        
        destino = ET.SubElement(cabecalho, f"{{{ns}}}destino")
        ET.SubElement(destino, f"{{{ns}}}registroANS").text = operadora_registro_ans
        
        ET.SubElement(cabecalho, f"{{{ns}}}padrao").text = cls.VERSAO_TISS

        prestador_para_operadora = ET.SubElement(root, f"{{{ns}}}prestadorParaOperadora")
        lote_guias = ET.SubElement(prestador_para_operadora, f"{{{ns}}}loteGuias")
        guias = ET.SubElement(lote_guias, f"{{{ns}}}guiasTISS")
        guia_consulta = ET.SubElement(guias, f"{{{ns}}}guiaConsulta")

        cabecalho_consulta = ET.SubElement(guia_consulta, f"{{{ns}}}cabecalhoConsulta")
        ET.SubElement(cabecalho_consulta, f"{{{ns}}}registroANS").text = operadora_registro_ans
        ET.SubElement(cabecalho_consulta, f"{{{ns}}}numeroGuiaPrestador").text = numero_guia

        dados_beneficiario = ET.SubElement(guia_consulta, f"{{{ns}}}dadosBeneficiario")
        ET.SubElement(dados_beneficiario, f"{{{ns}}}numeroCarteira").text = numero_carteira
        ET.SubElement(dados_beneficiario, f"{{{ns}}}nomeBeneficiario").text = paciente_nome
        if paciente_cpf:
            ET.SubElement(dados_beneficiario, f"{{{ns}}}cpfBeneficiario").text = paciente_cpf
        if paciente_cns:
            ET.SubElement(dados_beneficiario, f"{{{ns}}}cnsBeneficiario").text = paciente_cns

        dados_contratado = ET.SubElement(guia_consulta, f"{{{ns}}}dadosContratadoExecutante")
        ET.SubElement(dados_contratado, f"{{{ns}}}codigoCNES").text = cnes_executante
        ET.SubElement(dados_contratado, f"{{{ns}}}nomeContratado").text = medico_nome

        profissional = ET.SubElement(dados_contratado, f"{{{ns}}}profissionalExecutante")
        ET.SubElement(profissional, f"{{{ns}}}nomeProfissional").text = medico_nome
        ET.SubElement(profissional, f"{{{ns}}}conselhoProfissional").text = "06"
        ET.SubElement(profissional, f"{{{ns}}}numeroConselhoProfissional").text = medico_crm
        ET.SubElement(profissional, f"{{{ns}}}UF").text = medico_uf
        ET.SubElement(profissional, f"{{{ns}}}cbos").text = cbo

        dados_atendimento = ET.SubElement(guia_consulta, f"{{{ns}}}dadosAtendimento")
        ET.SubElement(dados_atendimento, f"{{{ns}}}dataAtendimento").text = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ET.SubElement(dados_atendimento, f"{{{ns}}}tipoConsulta").text = tipo_consulta
        
        procedimento = ET.SubElement(dados_atendimento, f"{{{ns}}}procedimento")
        ET.SubElement(procedimento, f"{{{ns}}}codigoTabela").text = "22"
        ET.SubElement(procedimento, f"{{{ns}}}codigoProcedimento").text = procedimento_tuss
        ET.SubElement(procedimento, f"{{{ns}}}valorProcedimento").text = f"{valor_procedimento:.2f}"

        if cid10:
            hipotese_cid = ET.SubElement(dados_atendimento, f"{{{ns}}}hipoteseDiagnostica")
            ET.SubElement(hipotese_cid, f"{{{ns}}}diagnosticoCID").text = cid10
        if ciap2:
            hipotese_ciap = ET.SubElement(dados_atendimento, f"{{{ns}}}diagnosticoCIAP2")
            ET.SubElement(hipotese_ciap, f"{{{ns}}}codigoCIAP2").text = ciap2

        epilogo = ET.SubElement(root, f"{{{ns}}}epilogo")
        hash_calc = uuid.uuid5(uuid.NAMESPACE_DNS, numero_guia).hex
        ET.SubElement(epilogo, f"{{{ns}}}hash").text = hash_calc

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    @classmethod
    def gerar_recibo_dmed(
        cls,
        numero_recibo: str,
        prestador_nome: str,
        prestador_cpf_cnpj: str,
        paciente_nome: str,
        paciente_cpf: str,
        valor: float,
        descricao_servico: str = "Consulta Médica em Atenção Primária à Saúde",
        data_emissao: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Gera estrutura fiscal compatível com as regras da DMED da Receita Federal."""
        data = data_emissao or datetime.now(timezone.utc)
        return {
            "recibo_numero": numero_recibo,
            "prestador": {
                "nome_razao_social": prestador_nome,
                "cpf_cnpj": prestador_cpf_cnpj,
            },
            "paciente": {
                "nome": paciente_nome,
                "cpf": paciente_cpf,
            },
            "servico": {
                "descricao": descricao_servico,
                "valor_total": valor,
                "data_prestacao": data.strftime("%Y-%m-%d"),
            },
            "dmed_dedutivel": True,
            "declaracao_irpf": "Recibo emitido para fins de comprovação junto à Receita Federal do Brasil (DMED).",
            "autenticacao_eletronica": uuid.uuid5(uuid.NAMESPACE_DNS, f"{numero_recibo}-{paciente_cpf}-{valor}").hex,
        }
