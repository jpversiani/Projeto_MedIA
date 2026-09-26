"""
Rotas REST de Prescrição Digital e Validação Pública CFM 2.314/2022.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services.prescricao_digital_cfm import (
    MotorPrescricaoCFM,
    TipoPrescricao,
)

router = APIRouter(prefix="/prescricao", tags=["Prescrição Digital CFM"])


class EmitirPrescricaoRequest(BaseModel):
    paciente_nome: str
    paciente_cpf: str
    medico_nome: str = "Dr. João Paulo Versiani"
    medico_crm: str = "78421"
    medico_uf: str = "MG"
    medico_rqe: Optional[str] = "39412"
    tipo: TipoPrescricao = TipoPrescricao.SIMPLES
    itens: List[Dict[str, str]]
    instrucoes_gerais: Optional[str] = None


class EmitirAtestadoRequest(BaseModel):
    paciente_nome: str
    paciente_cpf: str
    medico_nome: str = "Dr. João Paulo Versiani"
    medico_crm: str = "78421"
    medico_uf: str = "MG"
    dias_afastamento: int = 3
    cid10: Optional[str] = None


@router.post("/emitir", status_code=status.HTTP_201_CREATED)
def emitir_prescricao_digital(payload: EmitirPrescricaoRequest):
    """Emite prescrição eletrônica com código de validação pública e hash de integridade."""
    doc = MotorPrescricaoCFM.emitir_prescricao(
        paciente_nome=payload.paciente_nome,
        paciente_cpf=payload.paciente_cpf,
        medico_nome=payload.medico_nome,
        medico_crm=payload.medico_crm,
        medico_uf=payload.medico_uf,
        medico_rqe=payload.medico_rqe,
        itens=payload.itens,
        tipo=payload.tipo,
        instrucoes_gerais=payload.instrucoes_gerais,
    )
    return {
        "codigo_validacao": doc.codigo_validacao,
        "tipo": doc.tipo_prescricao.value,
        "data_emissao": doc.data_emissao,
        "hash_integridade": doc.hash_integridade_sha256,
        "status": doc.status,
        "url_validacao_publica": f"https://validador.media-saude.com.br/verificar?codigo={doc.codigo_validacao}",
    }


@router.post("/atestado/emitir", status_code=status.HTTP_201_CREATED)
def emitir_atestado_digital(payload: EmitirAtestadoRequest):
    """Emite atestado médico digital em conformidade com as normas do CFM."""
    doc = MotorPrescricaoCFM.emitir_atestado(
        paciente_nome=payload.paciente_nome,
        paciente_cpf=payload.paciente_cpf,
        medico_nome=payload.medico_nome,
        medico_crm=payload.medico_crm,
        medico_uf=payload.medico_uf,
        dias_afastamento=payload.dias_afastamento,
        cid10=payload.cid10,
    )
    return {
        "codigo_validacao": doc.codigo_validacao,
        "dias_afastamento": doc.dias_afastamento,
        "data_emissao": doc.data_emissao,
        "hash_integridade": doc.hash_integridade_sha256,
        "status": doc.status,
    }


@router.get("/validar/{codigo}")
def consultar_documento_publico(codigo: str):
    """Endpoint público para farmácias e pacientes validarem a autenticidade do documento."""
    dados = MotorPrescricaoCFM.validar_documento_publico(codigo)
    if not dados:
        raise HTTPException(status_code=404, detail="Documento médico não encontrado ou expirado no validador público.")
    return dados
