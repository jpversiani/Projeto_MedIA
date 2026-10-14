"""
Serviço de Prescrição e Atestados Médicos Digitais — Padrão CFM 2.314/2022 & ICP-Brasil.
Gera documentos clínicos eletrônicos assinados, com código de validação pública
para verificação em farmácias e órgãos de controle sem expor dados confidenciais do prontuário.
Persiste todos os documentos no banco de dados (tabela documentos_cfm).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.models.documento_cfm import DocumentoCFM


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
    atendimento_id: Optional[int] = None
    cidadao_id: Optional[int] = None


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
    atendimento_id: Optional[int] = None
    cidadao_id: Optional[int] = None


class MotorPrescricaoCFM:
    """Motor de emissão e auditoria de documentos médicos eletrônicos com persistência em banco."""

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
        atendimento_id: Optional[int] = None,
        cidadao_id: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> DocumentoPrescricaoCFM:
        """Emite uma prescrição médica digital estruturada com código validador e persistência em banco."""
        if db is None:
            from app.core.database import SessionLocal
            with SessionLocal() as session:
                return cls._emitir_prescricao_db(
                    session,
                    paciente_nome=paciente_nome,
                    paciente_cpf=paciente_cpf,
                    medico_nome=medico_nome,
                    medico_crm=medico_crm,
                    medico_uf=medico_uf,
                    medico_rqe=medico_rqe,
                    itens=itens,
                    tipo=tipo,
                    instrucoes_gerais=instrucoes_gerais,
                    atendimento_id=atendimento_id,
                    cidadao_id=cidadao_id,
                )
        return cls._emitir_prescricao_db(
            db,
            paciente_nome=paciente_nome,
            paciente_cpf=paciente_cpf,
            medico_nome=medico_nome,
            medico_crm=medico_crm,
            medico_uf=medico_uf,
            medico_rqe=medico_rqe,
            itens=itens,
            tipo=tipo,
            instrucoes_gerais=instrucoes_gerais,
            atendimento_id=atendimento_id,
            cidadao_id=cidadao_id,
        )

    @classmethod
    def _emitir_prescricao_db(
        cls,
        db: Session,
        paciente_nome: str,
        paciente_cpf: str,
        medico_nome: str,
        medico_crm: str,
        medico_uf: str,
        medico_rqe: Optional[str],
        itens: List[Dict[str, str]],
        tipo: TipoPrescricao,
        instrucoes_gerais: Optional[str],
        atendimento_id: Optional[int],
        cidadao_id: Optional[int],
    ) -> DocumentoPrescricaoCFM:
        partes = uuid.uuid4().hex.upper()
        codigo_validacao = f"CFM-{partes[:4]}-{partes[4:8]}-{partes[8:12]}"
        now_dt = datetime.now(timezone.utc)
        agora = now_dt.isoformat()

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

        conteudo_dict = {
            "tipo_documento": "RECEITA_DIGITAL",
            "tipo_prescricao": tipo.value,
            "itens": [it.__dict__ for it in itens_obj],
            "instrucoes_gerais": instrucoes_gerais,
            "data_dispensacao": None,
        }

        doc_db = DocumentoCFM(
            codigo_validacao=codigo_validacao,
            tipo="RECEITA",
            status="VALIDA",
            hash_integridade_sha256=hash_calc,
            atendimento_id=atendimento_id,
            cidadao_id=cidadao_id,
            medico_nome=medico_nome,
            medico_crm=medico_crm,
            medico_uf=medico_uf,
            medico_rqe=medico_rqe,
            paciente_nome=paciente_nome,
            paciente_cpf=paciente_cpf,
            conteudo=conteudo_dict,
            data_emissao=now_dt,
        )
        db.add(doc_db)
        db.commit()
        db.refresh(doc_db)

        return DocumentoPrescricaoCFM(
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
            atendimento_id=atendimento_id,
            cidadao_id=cidadao_id,
        )

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
        atendimento_id: Optional[int] = None,
        cidadao_id: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> DocumentoAtestadoCFM:
        """Emite atestado médico digital em conformidade com as normas do CFM com persistência em banco."""
        if db is None:
            from app.core.database import SessionLocal
            with SessionLocal() as session:
                return cls._emitir_atestado_db(
                    session,
                    paciente_nome=paciente_nome,
                    paciente_cpf=paciente_cpf,
                    medico_nome=medico_nome,
                    medico_crm=medico_crm,
                    medico_uf=medico_uf,
                    dias_afastamento=dias_afastamento,
                    cid10=cid10,
                    atendimento_id=atendimento_id,
                    cidadao_id=cidadao_id,
                )
        return cls._emitir_atestado_db(
            db,
            paciente_nome=paciente_nome,
            paciente_cpf=paciente_cpf,
            medico_nome=medico_nome,
            medico_crm=medico_crm,
            medico_uf=medico_uf,
            dias_afastamento=dias_afastamento,
            cid10=cid10,
            atendimento_id=atendimento_id,
            cidadao_id=cidadao_id,
        )

    @classmethod
    def _emitir_atestado_db(
        cls,
        db: Session,
        paciente_nome: str,
        paciente_cpf: str,
        medico_nome: str,
        medico_crm: str,
        medico_uf: str,
        dias_afastamento: int,
        cid10: Optional[str],
        atendimento_id: Optional[int],
        cidadao_id: Optional[int],
    ) -> DocumentoAtestadoCFM:
        partes = uuid.uuid4().hex.upper()
        codigo_validacao = f"ATE-{partes[:4]}-{partes[4:8]}-{partes[8:12]}"
        now_dt = datetime.now(timezone.utc)
        agora = now_dt.isoformat()

        payload_bruto = {
            "codigo": codigo_validacao,
            "paciente_cpf": paciente_cpf,
            "medico": f"{medico_crm}-{medico_uf}",
            "dias": dias_afastamento,
            "cid": cid10,
            "data": agora,
        }
        hash_calc = hashlib.sha256(json.dumps(payload_bruto, sort_keys=True).encode("utf-8")).hexdigest()

        conteudo_dict = {
            "tipo_documento": "ATESTADO_MEDICO",
            "dias_afastamento": dias_afastamento,
            "cid10": cid10,
        }

        doc_db = DocumentoCFM(
            codigo_validacao=codigo_validacao,
            tipo="ATESTADO",
            status="VALIDO",
            hash_integridade_sha256=hash_calc,
            atendimento_id=atendimento_id,
            cidadao_id=cidadao_id,
            medico_nome=medico_nome,
            medico_crm=medico_crm,
            medico_uf=medico_uf,
            medico_rqe=None,
            paciente_nome=paciente_nome,
            paciente_cpf=paciente_cpf,
            conteudo=conteudo_dict,
            data_emissao=now_dt,
        )
        db.add(doc_db)
        db.commit()
        db.refresh(doc_db)

        return DocumentoAtestadoCFM(
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
            atendimento_id=atendimento_id,
            cidadao_id=cidadao_id,
        )

    @classmethod
    def validar_documento_publico(cls, codigo: str, db: Optional[Session] = None) -> Optional[Dict]:
        """Consulta pública para farmácias, empregadores ou pacientes verificarem a autenticidade."""
        registro = cls.obter_documento(codigo, db=db)
        if not registro:
            return None
        return registro["dados_consulta_farmacia"]

    @classmethod
    def obter_documento(cls, codigo: str, db: Optional[Session] = None) -> Optional[Dict]:
        """Retorna o registro completo contendo o objeto do documento para geração de PDF e validação."""
        if db is None:
            from app.core.database import SessionLocal
            with SessionLocal() as session:
                return cls._obter_documento_db(codigo, session)
        return cls._obter_documento_db(codigo, db)

    @classmethod
    def _obter_documento_db(cls, codigo: str, db: Session) -> Optional[Dict]:
        codigo_limpo = codigo.strip().upper()
        doc_db = db.query(DocumentoCFM).filter(DocumentoCFM.codigo_validacao == codigo_limpo).first()
        if not doc_db:
            return None

        data_emissao_str = doc_db.data_emissao.isoformat() if doc_db.data_emissao else ""
        conteudo = doc_db.conteudo or {}

        if doc_db.tipo == "RECEITA" or conteudo.get("tipo_documento") == "RECEITA_DIGITAL":
            itens_obj = [
                ItemMedicamentoPrescricao(
                    farmaco=it.get("farmaco", ""),
                    concentracao=it.get("concentracao", ""),
                    forma_farmaceutica=it.get("forma_farmaceutica", "comprimido"),
                    posologia=it.get("posologia", ""),
                    quantidade_total=it.get("quantidade_total", "1 caixa"),
                    via_administracao=it.get("via_administracao", "Oral"),
                    instrucoes_especiais=it.get("instrucoes_especiais"),
                )
                for it in conteudo.get("itens", [])
            ]
            tipo_val = conteudo.get("tipo_prescricao", "SIMPLES")
            tipo_enum = TipoPrescricao(tipo_val) if tipo_val in TipoPrescricao._value2member_map_ else TipoPrescricao.SIMPLES

            doc = DocumentoPrescricaoCFM(
                codigo_validacao=doc_db.codigo_validacao,
                tipo_prescricao=tipo_enum,
                medico_nome=doc_db.medico_nome,
                medico_crm=doc_db.medico_crm,
                medico_uf=doc_db.medico_uf,
                medico_rqe=doc_db.medico_rqe,
                paciente_nome=doc_db.paciente_nome,
                paciente_cpf=doc_db.paciente_cpf,
                data_emissao=data_emissao_str,
                itens=itens_obj,
                instrucoes_gerais=conteudo.get("instrucoes_gerais"),
                hash_integridade_sha256=doc_db.hash_integridade_sha256,
                status=doc_db.status,
                data_dispensacao=conteudo.get("data_dispensacao"),
                atendimento_id=doc_db.atendimento_id,
                cidadao_id=doc_db.cidadao_id,
            )
            dados_consulta = {
                "codigo": doc_db.codigo_validacao,
                "paciente_nome": doc_db.paciente_nome,
                "paciente_cpf_mascarado": f"***.{doc_db.paciente_cpf[3:6]}.{doc_db.paciente_cpf[6:9]}-**" if len(doc_db.paciente_cpf) == 11 else doc_db.paciente_cpf,
                "medico": f"{doc_db.medico_nome} (CRM {doc_db.medico_crm}-{doc_db.medico_uf})",
                "tipo_receita": tipo_enum.value,
                "status": doc_db.status,
                "data_emissao": data_emissao_str,
                "itens": [f"{it.farmaco} {it.concentracao} - {it.posologia} (Qtd: {it.quantidade_total})" for it in itens_obj],
                "hash_sha256": doc_db.hash_integridade_sha256,
            }
            return {
                "tipo_documento": "RECEITA_DIGITAL",
                "documento": doc,
                "dados_consulta_farmacia": dados_consulta,
            }
        else:
            dias = conteudo.get("dias_afastamento", 1)
            cid10 = conteudo.get("cid10")
            doc = DocumentoAtestadoCFM(
                codigo_validacao=doc_db.codigo_validacao,
                medico_nome=doc_db.medico_nome,
                medico_crm=doc_db.medico_crm,
                medico_uf=doc_db.medico_uf,
                paciente_nome=doc_db.paciente_nome,
                paciente_cpf=doc_db.paciente_cpf,
                dias_afastamento=dias,
                motivo_cid10=cid10,
                data_emissao=data_emissao_str,
                hash_integridade_sha256=doc_db.hash_integridade_sha256,
                status=doc_db.status,
                atendimento_id=doc_db.atendimento_id,
                cidadao_id=doc_db.cidadao_id,
            )
            dados_consulta = {
                "codigo": doc_db.codigo_validacao,
                "paciente_nome": doc_db.paciente_nome,
                "paciente_cpf_mascarado": f"***.{doc_db.paciente_cpf[3:6]}.{doc_db.paciente_cpf[6:9]}-**" if len(doc_db.paciente_cpf) == 11 else doc_db.paciente_cpf,
                "medico": f"{doc_db.medico_nome} (CRM {doc_db.medico_crm}-{doc_db.medico_uf})",
                "dias_afastamento": dias,
                "cid10": cid10 or "Omitido a pedido do paciente",
                "status": doc_db.status,
                "data_emissao": data_emissao_str,
                "hash_sha256": doc_db.hash_integridade_sha256,
            }
            return {
                "tipo_documento": "ATESTADO_MEDICO",
                "documento": doc,
                "dados_consulta_farmacia": dados_consulta,
            }


# Alias canônico para importação padronizada nos demais serviços
prescricao_service = MotorPrescricaoCFM
