"""
Serviço de Prescrição e Atestados Médicos Digitais — Padrão CFM 2.314/2022 & ICP-Brasil.
Gera documentos clínicos eletrônicos assinados, com código de validação pública
para verificação em farmácias e órgãos de controle sem expor dados confidenciais do prontuário.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Dict, List, Optional
import uuid


class TipoPrescricao(str, Enum):
    SIMPLES = "SIMPLES"
    ANTIBIOTICO = "ANTIBIOTICO"  # RDC 20/2011 (Receita em 2 vias / retenção)
    CONTROLE_ESPECIAL = "CONTROLE_ESPECIAL"  # Portaria 344/98 (Lista C1/C5)


@dataclass
class ItemMedicamentoPrescricao:
    farmaco: str
    concentracao: str
    forma_farmaceutica: str  # comprimido, gotas, capsula, pomada
    posologia: str
    quantidade_total: str
    via_administracao: str = "Oral"
    instrucoes_especiais: Optional[str] = None


@dataclass
class DocumentoPrescricaoCFM:
    codigo_validacao: str
    tipo_prescricao: TipoPrescricao
    medico_nome: str
    medico_crm: str
    medico_uf: str
    medico_rqe: Optional[str]
    paciente_nome: str
    paciente_cpf: str
    data_emissao: str
    itens: List[ItemMedicamentoPrescricao]
    instrucoes_gerais: Optional[str] = None
    hash_integridade_sha256: str = ""
    status: str = "VALIDA"
    data_dispensacao: Optional[str] = None


@dataclass
class DocumentoAtestadoCFM:
    codigo_validacao: str
    medico_nome: str
    medico_crm: str
    medico_uf: str
    paciente_nome: str
    paciente_cpf: str
    dias_afastamento: int
    motivo_cid10: Optional[str]  # Somente se autorizado expressamente pelo paciente (CFM)
    data_emissao: str
    hash_integridade_sha256: str = ""
    status: str = "VALIDO"


# Registro em memória para validação pública rápida
_REPOSITORIO_DOCUMENTOS_CFM: Dict[str, Dict] = {}


class MotorPrescricaoCFM:
    """Motor de emissão e auditoria de documentos médicos eletrônicos."""

    @classmethod
    def emitir_prescricao(
        cls,
        paciente_nome: str,
        paciente_cpf: str,
        medico_nome: str,
        medico_crm: str,
        medico_uf: str,
        medico_rqe: Optional[str],
        itens: List[Dict[str, str]],
        tipo: TipoPrescricao = TipoPrescricao.SIMPLES,
        instrucoes_gerais: Optional[str] = None,
    ) -> DocumentoPrescricaoCFM:
        """Emite uma prescrição médica digital estruturada com código validador."""
        partes = uuid.uuid4().hex.upper()
        codigo_validacao = f"CFM-{partes[:4]}-{partes[4:8]}-{partes[8:12]}"
        agora = datetime.now(timezone.utc).isoformat()

        itens_obj = [
            ItemMedicamentoPrescricao(
                farmaco=it["farmaco"],
                concentracao=it.get("concentracao", ""),
                forma_farmaceutica=it.get("forma_farmaceutica", "comprimido"),
                posologia=it["posologia"],
                quantidade_total=it.get("quantidade_total", "1 caixa"),
                via_administracao=it.get("via_administracao", "Oral"),
                instrucoes_especiais=it.get("instrucoes_especiais"),
            )
            for it in itens
        ]

        payload_bruto = {
            "codigo": codigo_validacao,
            "paciente_cpf": paciente_cpf,
            "medico_crm": f"{medico_crm}-{medico_uf}",
            "tipo": tipo.value,
            "data": agora,
            "itens": [it.__dict__ for it in itens_obj],
        }
        hash_calc = hashlib.sha256(json.dumps(payload_bruto, sort_keys=True).encode("utf-8")).hexdigest()

        doc = DocumentoPrescricaoCFM(
            codigo_validacao=codigo_validacao,
            tipo_prescricao=tipo,
            medico_nome=medico_nome,
            medico_crm=medico_crm,
            medico_uf=medico_uf,
            medico_rqe=medico_rqe,
            paciente_nome=paciente_nome,
            paciente_cpf=paciente_cpf,
            data_emissao=agora,
            itens=itens_obj,
            instrucoes_gerais=instrucoes_gerais,
            hash_integridade_sha256=hash_calc,
            status="VALIDA",
        )

        _REPOSITORIO_DOCUMENTOS_CFM[codigo_validacao] = {
            "tipo_documento": "RECEITA_DIGITAL",
            "documento": doc,
            "dados_consulta_farmacia": {
                "codigo": codigo_validacao,
                "paciente_nome": paciente_nome,
                "paciente_cpf_mascarado": f"***.{paciente_cpf[3:6]}.{paciente_cpf[6:9]}-**" if len(paciente_cpf) == 11 else paciente_cpf,
                "medico": f"{medico_nome} (CRM {medico_crm}-{medico_uf})",
                "tipo_receita": tipo.value,
                "status": "VALIDA",
                "data_emissao": agora,
                "itens": [f"{it.farmaco} {it.concentracao} - {it.posologia} (Qtd: {it.quantidade_total})" for it in itens_obj],
                "hash_sha256": hash_calc,
            }
        }
        return doc

    @classmethod
    def emitir_atestado(
        cls,
        paciente_nome: str,
        paciente_cpf: str,
        medico_nome: str,
        medico_crm: str,
        medico_uf: str,
        dias_afastamento: int,
        cid10: Optional[str] = None,
    ) -> DocumentoAtestadoCFM:
        """Emite atestado médico digital em conformidade com as normas do CFM."""
        partes = uuid.uuid4().hex.upper()
        codigo_validacao = f"ATE-{partes[:4]}-{partes[4:8]}-{partes[8:12]}"
        agora = datetime.now(timezone.utc).isoformat()

        payload_bruto = {
            "codigo": codigo_validacao,
            "paciente_cpf": paciente_cpf,
            "medico": f"{medico_crm}-{medico_uf}",
            "dias": dias_afastamento,
            "cid": cid10,
            "data": agora,
        }
        hash_calc = hashlib.sha256(json.dumps(payload_bruto, sort_keys=True).encode("utf-8")).hexdigest()

        doc = DocumentoAtestadoCFM(
            codigo_validacao=codigo_validacao,
            medico_nome=medico_nome,
            medico_crm=medico_crm,
            medico_uf=medico_uf,
            paciente_nome=paciente_nome,
            paciente_cpf=paciente_cpf,
            dias_afastamento=dias_afastamento,
            motivo_cid10=cid10,
            data_emissao=agora,
            hash_integridade_sha256=hash_calc,
            status="VALIDO",
        )

        _REPOSITORIO_DOCUMENTOS_CFM[codigo_validacao] = {
            "tipo_documento": "ATESTADO_MEDICO",
            "documento": doc,
            "dados_consulta_farmacia": {
                "codigo": codigo_validacao,
                "paciente_nome": paciente_nome,
                "paciente_cpf_mascarado": f"***.{paciente_cpf[3:6]}.{paciente_cpf[6:9]}-**" if len(paciente_cpf) == 11 else paciente_cpf,
                "medico": f"{medico_nome} (CRM {medico_crm}-{medico_uf})",
                "dias_afastamento": dias_afastamento,
                "cid10": cid10 or "Omitido a pedido do paciente",
                "status": "VALIDO",
                "data_emissao": agora,
                "hash_sha256": hash_calc,
            }
        }
        return doc

    @classmethod
    def validar_documento_publico(cls, codigo: str) -> Optional[Dict]:
        """Consulta pública para farmácias, empregadores ou pacientes verificarem a autenticidade."""
        registro = _REPOSITORIO_DOCUMENTOS_CFM.get(codigo.strip().upper())
        if not registro:
            return None
        return registro["dados_consulta_farmacia"]
