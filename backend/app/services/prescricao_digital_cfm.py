"""
Serviço de Prescrição e Atestados Médicos Digitais — Padrão CFM 2.314/2022 & ICP-Brasil.

Gera documentos clínicos eletrônicos assinados, com código de validação pública
para verificação em farmácias e órgãos de controle sem expor dados
confidenciais do prontuário.

**Persistência (correção T2):** os documentos eram guardados num dicionário em
memória (``_REPOSITORIO_DOCUMENTOS_CFM``). Ao reiniciar o processo, todo QR
Code/link de validação passava a responder **404** e a farmácia não conseguia
conferir a receita. Agora, quando o chamador informa uma sessão ``db``, o
documento é gravado na tabela ``documentos_clinicos`` e a validação pública
consulta o banco. O dicionário em memória permanece apenas como caminho legado
para chamadas sem sessão (scripts e testes unitários do motor puro).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional
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


# Registro em memória — apenas caminho legado (chamadas sem sessão de banco).
_REPOSITORIO_DOCUMENTOS_CFM: Dict[str, Dict] = {}

TIPO_RECEITA = "RECEITA_DIGITAL"
TIPO_ATESTADO = "ATESTADO_MEDICO"


def _mascarar_cpf(cpf: str) -> str:
    if len(cpf) == 11:
        return f"***.{cpf[3:6]}.{cpf[6:9]}-**"
    return cpf


def _serializar_prescricao(doc: DocumentoPrescricaoCFM) -> Dict[str, Any]:
    """Converte o documento em dict JSON-serializável (para ``payload_json``)."""
    return {
        "codigo_validacao": doc.codigo_validacao,
        "tipo_prescricao": doc.tipo_prescricao.value,
        "medico_nome": doc.medico_nome,
        "medico_crm": doc.medico_crm,
        "medico_uf": doc.medico_uf,
        "medico_rqe": doc.medico_rqe,
        "paciente_nome": doc.paciente_nome,
        "paciente_cpf": doc.paciente_cpf,
        "data_emissao": doc.data_emissao,
        "itens": [item.__dict__.copy() for item in doc.itens],
        "instrucoes_gerais": doc.instrucoes_gerais,
        "hash_integridade_sha256": doc.hash_integridade_sha256,
        "status": doc.status,
        "data_dispensacao": doc.data_dispensacao,
    }


def _serializar_atestado(doc: DocumentoAtestadoCFM) -> Dict[str, Any]:
    return {
        "codigo_validacao": doc.codigo_validacao,
        "medico_nome": doc.medico_nome,
        "medico_crm": doc.medico_crm,
        "medico_uf": doc.medico_uf,
        "paciente_nome": doc.paciente_nome,
        "paciente_cpf": doc.paciente_cpf,
        "dias_afastamento": doc.dias_afastamento,
        "motivo_cid10": doc.motivo_cid10,
        "data_emissao": doc.data_emissao,
        "hash_integridade_sha256": doc.hash_integridade_sha256,
        "status": doc.status,
    }


def _desserializar_prescricao(dados: Dict[str, Any]) -> DocumentoPrescricaoCFM:
    return DocumentoPrescricaoCFM(
        codigo_validacao=dados["codigo_validacao"],
        tipo_prescricao=TipoPrescricao(dados["tipo_prescricao"]),
        medico_nome=dados["medico_nome"],
        medico_crm=dados["medico_crm"],
        medico_uf=dados["medico_uf"],
        medico_rqe=dados.get("medico_rqe"),
        paciente_nome=dados["paciente_nome"],
        paciente_cpf=dados["paciente_cpf"],
        data_emissao=dados["data_emissao"],
        itens=[ItemMedicamentoPrescricao(**item) for item in dados.get("itens", [])],
        instrucoes_gerais=dados.get("instrucoes_gerais"),
        hash_integridade_sha256=dados.get("hash_integridade_sha256", ""),
        status=dados.get("status", "VALIDA"),
        data_dispensacao=dados.get("data_dispensacao"),
    )


def _desserializar_atestado(dados: Dict[str, Any]) -> DocumentoAtestadoCFM:
    return DocumentoAtestadoCFM(
        codigo_validacao=dados["codigo_validacao"],
        medico_nome=dados["medico_nome"],
        medico_crm=dados["medico_crm"],
        medico_uf=dados["medico_uf"],
        paciente_nome=dados["paciente_nome"],
        paciente_cpf=dados["paciente_cpf"],
        dias_afastamento=int(dados["dias_afastamento"]),
        motivo_cid10=dados.get("motivo_cid10"),
        data_emissao=dados["data_emissao"],
        hash_integridade_sha256=dados.get("hash_integridade_sha256", ""),
        status=dados.get("status", "VALIDO"),
    )


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
        *,
        db=None,
        cidadao_id: Optional[int] = None,
        profissional_id: Optional[int] = None,
        estabelecimento_id: Optional[int] = None,
    ) -> DocumentoPrescricaoCFM:
        """Emite uma prescrição médica digital estruturada com código validador.

        Com ``db`` informado, o documento é persistido em ``documentos_clinicos``
        e sobrevive a reinícios. Sem ``db``, cai no repositório em memória
        (comportamento legado, apenas para o motor puro).
        """
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

        dados_publicos = {
            "codigo": codigo_validacao,
            "paciente_nome": paciente_nome,
            "paciente_cpf_mascarado": _mascarar_cpf(paciente_cpf),
            "medico": f"{medico_nome} (CRM {medico_crm}-{medico_uf})",
            "tipo_receita": tipo.value,
            "status": "VALIDA",
            "data_emissao": agora,
            "itens": [
                f"{it.farmaco} {it.concentracao} - {it.posologia} (Qtd: {it.quantidade_total})"
                for it in itens_obj
            ],
            "hash_sha256": hash_calc,
        }

        if db is not None:
            cls._persistir(
                db,
                doc,
                tipo_documento=TIPO_RECEITA,
                dados_publicos=dados_publicos,
                cidadao_id=cidadao_id,
                profissional_id=profissional_id,
                estabelecimento_id=estabelecimento_id,
            )
        else:
            _REPOSITORIO_DOCUMENTOS_CFM[codigo_validacao] = {
                "tipo_documento": TIPO_RECEITA,
                "documento": doc,
                "dados_consulta_farmacia": dados_publicos,
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
        *,
        db=None,
        cidadao_id: Optional[int] = None,
        profissional_id: Optional[int] = None,
        estabelecimento_id: Optional[int] = None,
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

        dados_publicos = {
            "codigo": codigo_validacao,
            "paciente_nome": paciente_nome,
            "paciente_cpf_mascarado": _mascarar_cpf(paciente_cpf),
            "medico": f"{medico_nome} (CRM {medico_crm}-{medico_uf})",
            "dias_afastamento": dias_afastamento,
            "cid10": cid10 or "Omitido a pedido do paciente",
            "status": "VALIDO",
            "data_emissao": agora,
            "hash_sha256": hash_calc,
        }

        if db is not None:
            cls._persistir(
                db,
                doc,
                tipo_documento=TIPO_ATESTADO,
                dados_publicos=dados_publicos,
                cidadao_id=cidadao_id,
                profissional_id=profissional_id,
                estabelecimento_id=estabelecimento_id,
            )
        else:
            _REPOSITORIO_DOCUMENTOS_CFM[codigo_validacao] = {
                "tipo_documento": TIPO_ATESTADO,
                "documento": doc,
                "dados_consulta_farmacia": dados_publicos,
            }
        return doc

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------
    @classmethod
    def _persistir(
        cls,
        db,
        doc,
        *,
        tipo_documento: str,
        dados_publicos: Dict[str, Any],
        cidadao_id: Optional[int],
        profissional_id: Optional[int],
        estabelecimento_id: Optional[int],
    ) -> None:
        from app.models.documento_clinico import DocumentoClinicoEmitido

        if isinstance(doc, DocumentoPrescricaoCFM):
            payload = _serializar_prescricao(doc)
        else:
            payload = _serializar_atestado(doc)

        emitido_em = datetime.fromisoformat(payload["data_emissao"])
        registro = DocumentoClinicoEmitido(
            codigo_validacao=doc.codigo_validacao,
            tipo_documento=tipo_documento,
            cidadao_id=cidadao_id,
            profissional_id=profissional_id,
            estabelecimento_id=estabelecimento_id,
            paciente_nome=doc.paciente_nome,
            paciente_cpf=doc.paciente_cpf,
            medico_nome=doc.medico_nome,
            medico_crm=doc.medico_crm,
            medico_uf=doc.medico_uf,
            medico_rqe=getattr(doc, "medico_rqe", None),
            data_emissao=emitido_em,
            hash_integridade_sha256=doc.hash_integridade_sha256,
            status=doc.status,
            payload_json=payload,
            dados_consulta_publica=dados_publicos,
        )
        db.add(registro)
        db.commit()
        db.refresh(registro)

    @classmethod
    def _buscar_registro(cls, db, codigo: str):
        from app.models.documento_clinico import DocumentoClinicoEmitido

        return (
            db.query(DocumentoClinicoEmitido)
            .filter(DocumentoClinicoEmitido.codigo_validacao == codigo.strip().upper())
            .first()
        )

    # ------------------------------------------------------------------
    # Consulta
    # ------------------------------------------------------------------
    @classmethod
    def validar_documento_publico(cls, codigo: str, db=None) -> Optional[Dict]:
        """Consulta pública para farmácias, empregadores ou pacientes verificarem a autenticidade."""
        if db is not None:
            registro = cls._buscar_registro(db, codigo)
            return registro.dados_consulta_publica if registro else None
        registro = _REPOSITORIO_DOCUMENTOS_CFM.get(codigo.strip().upper())
        if not registro:
            return None
        return registro["dados_consulta_farmacia"]

    @classmethod
    def obter_documento(cls, codigo: str, db=None) -> Optional[Dict]:
        """Retorna o registro completo contendo o objeto do documento para geração de PDF."""
        if db is not None:
            registro = cls._buscar_registro(db, codigo)
            if not registro:
                return None
            payload = registro.payload_json or {}
            if registro.tipo_documento == TIPO_ATESTADO:
                documento = _desserializar_atestado(payload)
            else:
                documento = _desserializar_prescricao(payload)
            return {
                "tipo_documento": registro.tipo_documento,
                "documento": documento,
                "dados_consulta_farmacia": registro.dados_consulta_publica or {},
            }
        return _REPOSITORIO_DOCUMENTOS_CFM.get(codigo.strip().upper())


# Alias canônico para importação padronizada nos demais serviços
prescricao_service = MotorPrescricaoCFM
