"""
Serviço de Conformidade e Auditoria para Telemedicina — Resolução CFM nº 2.314/2022
Regulamenta a prática da telemedicina no Brasil para consultas médicas, teleinterconsultas,
telediagnóstico, telemonitoramento e teletriagem.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Dict, List, Optional
import urllib.parse
import uuid


@dataclass
class MedicoIdentificacaoCFM:
    nome_completo: str
    crm: str
    uf_crm: str
    rqe: Optional[str] = None  # Registro de Qualificação de Especialista (quando especialista)
    especialidade: str = "Clínica Médica"
    email_contato: Optional[str] = None
    endereco_profissional: Optional[str] = "Consultório Médico Particular"


@dataclass
class PacienteIdentificacaoCFM:
    nome_completo: str
    cpf: str
    telefone_whatsapp: Optional[str] = None
    email: Optional[str] = None
    data_nascimento: Optional[str] = None


@dataclass
class RegistroTCLE:
    """Termo de Consentimento Livre e Esclarecido (Art. 4º, § 2º da CFM 2.314/2022)."""
    consentimento_id: str
    paciente_cpf: str
    paciente_nome: str
    data_hora_aceite: str
    metodo_aceite: str  # "ELETRONICO_SMS", "ELETRONICO_WHATSAPP", "ELETRONICO_WEB", "VERBAL_GRAVADO"
    ip_origem: Optional[str] = None
    hash_tcle: str = ""
    texto_resumo: str = ""


class MotorCFMTelemedicina:
    """
    Implementação dos requisitos legais e éticos estabelecidos pela Resolução CFM nº 2.314/2022.
    """

    VERSAO_NORMA = "CFM-2314/2022"

    @classmethod
    def gerar_termo_consentimento_tcle(
        cls,
        paciente: PacienteIdentificacaoCFM,
        medico: MedicoIdentificacaoCFM,
        modalidade: str = "TELECONSULTA",
    ) -> Dict[str, str]:
        """
        Gera o texto formal do TCLE contendo as informações obrigatórias:
        - Natureza e limites da telemedicina (impossibilidade de exame físico presencial completo);
        - Sigilo profissional e confidencialidade médica (LGPD Art. 11 e CFM);
        - Prerrogativa médica e do paciente de converter para consulta presencial a qualquer momento;
        - Ausência de garantia de resultados.
        """
        data_hora_emissao = datetime.now(timezone.utc).strftime("%d/%m/%Y às %H:%M:%S UTC")
        
        texto_tcle = (
            f"TERMO DE CONSENTIMENTO LIVRE E ESCLARECIDO (TCLE) PARA TELEMEDICINA\n"
            f"Conforme Resolução CFM nº 2.314/2022 (Conselho Federal de Medicina) e LGPD (Lei 13.709/2018)\n\n"
            f"1. PARTES ENVOLVIDAS:\n"
            f"Médico(a) Responsável: {medico.nome_completo} | CRM: {medico.crm}-{medico.uf_crm}"
            + (f" | RQE: {medico.rqe}" if medico.rqe else "")
            + f" | Especialidade: {medico.especialidade}\n"
            f"Paciente: {paciente.nome_completo} | CPF: {paciente.cpf}\n"
            f"Modalidade: {modalidade}\n"
            f"Data/Hora de Emissão: {data_hora_emissao}\n\n"
            f"2. ESCLARECIMENTOS LEGAIS E TÉCNICOS:\n"
            f"a) A telemedicina é realizada com uso de tecnologias interativas de comunicação audiovisual segura.\n"
            f"b) O paciente está ciente de que o atendimento a distância possui limitações inerentes pela impossibilidade de exame físico direto.\n"
            f"c) O(a) médico(a) possui total autonomia para indicar ou contraindicar a continuidade do atendimento remoto, "
            f"podendo a qualquer tempo determinar o encaminhamento para consulta presencial ou pronto atendimento (Art. 3º).\n"
            f"d) As informações prestadas e os dados clínicos serão arquivados em prontuário eletrônico seguro com guarda de sigilo médico.\n"
            f"e) A transmissão de receitas, pedidos de exames e atestados será realizada em formato digital assinado eletronicamente.\n\n"
            f"3. MANIFESTAÇÃO DE CONSENTIMENTO:\n"
            f"O paciente confirma ter compreendido as informações, esclarecido suas dúvidas e consente livremente com a realização desta {modalidade.lower()}."
        )

        hash_tcle = hashlib.sha256(texto_tcle.encode("utf-8")).hexdigest()

        return {
            "norma_regulamentar": cls.VERSAO_NORMA,
            "texto_integral": texto_tcle,
            "hash_integridade_sha256": hash_tcle,
            "data_hora_emissao": data_hora_emissao,
        }

    @classmethod
    def registrar_aceite_tcle(
        cls,
        paciente: PacienteIdentificacaoCFM,
        metodo: str = "ELETRONICO_WEB",
        ip_origem: Optional[str] = "127.0.0.1",
    ) -> RegistroTCLE:
        """Gera o registro auditado de confirmação do TCLE."""
        consentimento_id = f"TCLE-{datetime.now(timezone.utc).strftime("%Y%m%d")}-{uuid.uuid4().hex[:8].upper()}"
        agora_iso = datetime.now(timezone.utc).isoformat()
        
        payload_hash = f"{consentimento_id}:{paciente.cpf}:{agora_iso}:{metodo}:{ip_origem}"
        hash_registro = hashlib.sha256(payload_hash.encode("utf-8")).hexdigest()

        return RegistroTCLE(
            consentimento_id=consentimento_id,
            paciente_cpf=paciente.cpf,
            paciente_nome=paciente.nome_completo,
            data_hora_aceite=agora_iso,
            metodo_aceite=metodo,
            ip_origem=ip_origem,
            hash_tcle=hash_registro,
            texto_resumo=f"Consentimento informado registrado para teleconsulta em {agora_iso} via {metodo}."
        )

    @classmethod
    def validar_requisitos_medico(cls, medico: MedicoIdentificacaoCFM) -> List[str]:
        """Valida exigências do Art. 5º da Resolução CFM 2.314/2022."""
        erros = []
        if not medico.nome_completo or len(medico.nome_completo.strip()) < 3:
            erros.append("CFM_01: Nome completo do médico é de preenchimento obrigatório.")
        if not medico.crm or not medico.crm.strip().isalnum():
            erros.append("CFM_02: Número de inscrição no CRM inválido.")
        if not medico.uf_crm or len(medico.uf_crm.strip()) != 2:
            erros.append("CFM_03: UF de inscrição no CRM deve conter exatamente 2 caracteres (ex: MG, SP).")
        return erros

    @classmethod
    def gerar_link_paciente(
        cls,
        codigo_sala: str,
        nome_paciente: str,
        nome_medico: str,
        base_url: str = "http://localhost:8000",
        telefone_whatsapp: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Gera link direto e seguro para o paciente entrar na sala WebRTC pelo navegador
        (sem precisar instalar nenhum aplicativo ou fazer cadastro prévio).
        """
        url_sala_paciente = f"{base_url}/static/telemedicina_paciente.html?sala={codigo_sala}"
        
        mensagem_whatsapp = (
            f"Olá {nome_paciente}! Sua teleconsulta com o(a) {nome_medico} está pronta. "
            f"Clique no link para acessar a sala segura pelo seu navegador (celular ou computador, sem precisar baixar aplicativo): "
            f"{url_sala_paciente}\n\n"
            f"Orientações: Conecte-se alguns minutos antes em um local silencioso e com boa iluminação."
        )

        link_whatsapp = ""
        if telefone_whatsapp:
            tel_limpo = "".join(filter(str.isdigit, telefone_whatsapp))
            if len(tel_limpo) in (10, 11) and not tel_limpo.startswith("55"):
                tel_limpo = "55" + tel_limpo
            link_whatsapp = f"https://api.whatsapp.com/send?phone={tel_limpo}&text={urllib.parse.quote(mensagem_whatsapp)}"

        return {
            "codigo_sala": codigo_sala,
            "url_acesso_paciente": url_sala_paciente,
            "mensagem_formatada": mensagem_whatsapp,
            "link_whatsapp_direto": link_whatsapp,
        }

    @classmethod
    def emitir_registro_conversao_presencial(
        cls,
        teleconsulta_id: int,
        paciente_nome: str,
        medico: MedicoIdentificacaoCFM,
        motivo_clinico: str,
    ) -> Dict[str, str]:
        """
        Registra a conversão de teleconsulta para atendimento presencial (Art. 3º do CFM 2.314/2022).
        O médico tem soberania e autonomia técnica para exigir exame presencial quando considerar necessário.
        """
        agora = datetime.now(timezone.utc).isoformat()
        relatorio = (
            f"CONVERSÃO DE TELECONSULTA PARA ATENDIMENTO PRESENCIAL (ART. 3º CFM 2.314/2022)\n"
            f"Teleconsulta ID: {teleconsulta_id}\n"
            f"Data/Hora: {agora}\n"
            f"Médico(a): {medico.nome_completo} (CRM: {medico.crm}-{medico.uf_crm})\n"
            f"Paciente: {paciente_nome}\n"
            f"Motivo Clínico da Indicação Presencial: {motivo_clinico}\n"
            f"Conduta: Atendimento remoto interrompido com segurança. Paciente orientado a comparecer ao consultório/serviço hospitalar."
        )
        return {
            "status": "CONVERTIDA_PRESENCIAL",
            "data_hora": agora,
            "relatorio": relatorio,
            "hash_registro": hashlib.sha256(relatorio.encode("utf-8")).hexdigest(),
        }
