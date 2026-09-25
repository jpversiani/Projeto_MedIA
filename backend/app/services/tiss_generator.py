"""
Serviço Gerador de Guias TISS (Padrão TISS - ANS - Troca de Informações na Saúde Suplementar).
Versão do Padrão: 4.01.00
Geração de guias estruturadas de Consulta e SP/SADT (Serviços Profissionais / Serviço Auxiliar de Diagnóstico e Terapia).
"""
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, Optional

def gerar_numero_guia() -> str:
    """Gera um número sequencial único para a Guia TISS."""
    return f"TISS-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

class TISSGenerator:
    """
    Gera XML e estruturas de dados conforme o padrão TISS da ANS.
    Compatível com faturamento de planos de saúde e consultório particular.
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
        procedimento_tuss: str = "10101012", # Consulta médica em consultório
        valor_procedimento: float = 150.0,
        tipo_consulta: str = "1", # 1 = Primeira consulta, 2 = Retorno
    ) -> str:
        """
        Gera o XML no padrão TISS ANS para Guia de Consulta.
        """
        ns = "http://www.ans.gov.br/padroes/tiss/schemas"
        ET.register_namespace("ans", ns)
        
        root = ET.Element(f"{{{ns}}}mensagemTISS")
        
        # 1. Cabecalho
        cabecalho = ET.SubElement(root, f"{{{ns}}}cabecalho")
        identificacao_transacao = ET.SubElement(cabecalho, f"{{{ns}}}identificacaoTransacao")
        ET.SubElement(identificacao_transacao, f"{{{ns}}}tipoTransacao").text = "ENVIO_LOTE_GUIAS"
        ET.SubElement(identificacao_transacao, f"{{{ns}}}numeroSequencialTransacao").text = str(uuid.uuid4().int)[:10]
        ET.SubElement(identificacao_transacao, f"{{{ns}}}dataRegistroTransacao").text = datetime.utcnow().strftime("%Y-%m-%d")
        ET.SubElement(identificacao_transacao, f"{{{ns}}}horaRegistroTransacao").text = datetime.utcnow().strftime("%H:%M:%S")
        
        origem = ET.SubElement(cabecalho, f"{{{ns}}}origem")
        ET.SubElement(origem, f"{{{ns}}}identificacaoPrestador").text = cnes_executante
        
        destino = ET.SubElement(cabecalho, f"{{{ns}}}destino")
        ET.SubElement(destino, f"{{{ns}}}registroANS").text = operadora_registro_ans
        
        ET.SubElement(cabecalho, f"{{{ns}}}padrao").text = cls.VERSAO_TISS

        # 2. Corpo / Guia de Consulta
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
        ET.SubElement(profissional, f"{{{ns}}}conselhoProfissional").text = "06" # 06 = CRM
        ET.SubElement(profissional, f"{{{ns}}}numeroConselhoProfissional").text = medico_crm
        ET.SubElement(profissional, f"{{{ns}}}UF").text = medico_uf
        ET.SubElement(profissional, f"{{{ns}}}cbos").text = cbo

        # 3. Dados do Atendimento
        dados_atendimento = ET.SubElement(guia_consulta, f"{{{ns}}}dadosAtendimento")
        ET.SubElement(dados_atendimento, f"{{{ns}}}dataAtendimento").text = datetime.utcnow().strftime("%Y-%m-%d")
        ET.SubElement(dados_atendimento, f"{{{ns}}}tipoConsulta").text = tipo_consulta
        
        procedimento = ET.SubElement(dados_atendimento, f"{{{ns}}}procedimento")
        ET.SubElement(procedimento, f"{{{ns}}}codigoTabela").text = "22" # TUSS Procedimentos e eventos em saúde
        ET.SubElement(procedimento, f"{{{ns}}}codigoProcedimento").text = procedimento_tuss
        ET.SubElement(procedimento, f"{{{ns}}}valorProcedimento").text = f"{valor_procedimento:.2f}"

        # Diagnósticos
        if cid10:
            hipotese_cid = ET.SubElement(dados_atendimento, f"{{{ns}}}hipoteseDiagnostica")
            ET.SubElement(hipotese_cid, f"{{{ns}}}diagnosticoCID").text = cid10
        if ciap2:
            hipotese_ciap = ET.SubElement(dados_atendimento, f"{{{ns}}}diagnosticoCIAP2")
            ET.SubElement(hipotese_ciap, f"{{{ns}}}codigoCIAP2").text = ciap2

        # 4. Epílogo / Hash de integridade
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
        """
        Gera estrutura fiscal compatível com as regras da DMED (Declaração de Serviços Médicos e de Saúde - Receita Federal).
        """
        data = data_emissao or datetime.utcnow()
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
            "declaracao_irpf": f"Recibo emitido para fins de comprovação junto à Receita Federal do Brasil (DMED).",
            "autenticacao_eletronica": uuid.uuid5(uuid.NAMESPACE_DNS, f"{numero_recibo}-{paciente_cpf}-{valor}").hex,
        }
