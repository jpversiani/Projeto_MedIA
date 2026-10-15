from datetime import datetime, timezone
import hashlib
import re
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.telemedicina import (
    Teleconsulta as TeleconsultaModel,
    SalaVirtual as SalaVirtualModel,
    StatusTeleconsulta,
    ConsentimentoTCLE,
)
from app.schemas.telemedicina import TeleconsultaCreate
from app.services.cfm_telemedicina import (
    MotorCFMTelemedicina,
    MedicoIdentificacaoCFM,
    PacienteIdentificacaoCFM,
)
from app.services.templates_especialidades import (
    listar_todas_especialidades,
    obter_especialidade,
)

router = APIRouter(prefix="/telemedicina", tags=["Telemedicina"])


class IniciarChamadaRequest(BaseModel):
    teleconsulta_id: int


class FinalizarChamadaRequest(BaseModel):
    teleconsulta_id: int
    dados_soap: Optional[Dict[str, Any]] = None


class TCLEGerarRequest(BaseModel):
    paciente_nome: str
    paciente_cpf: str
    medico_nome: str = "Dra. Francelli Neves Versiani"
    medico_crm: str = "78421"
    medico_uf: str = "MG"
    medico_rqe: Optional[str] = "39412"
    especialidade: str = "Clínica Médica"
    modalidade: str = "TELECONSULTA"


class TCLERegistrarRequest(BaseModel):
    paciente_nome: str
    paciente_cpf: str
    metodo: str = "ELETRONICO_WEB"
    ip_origem: Optional[str] = None
    teleconsulta_id: Optional[int] = None
    cidadao_id: Optional[int] = None
    texto_integral: Optional[str] = None


class ConverterPresencialRequest(BaseModel):
    teleconsulta_id: int
    paciente_nome: str
    motivo_clinico: str
    medico_nome: str = "Dra. Francelli Neves Versiani"
    medico_crm: str = "78421"
    medico_uf: str = "MG"


@router.post("/agendamentos", status_code=status.HTTP_201_CREATED)
def criar_agendamento(dados: TeleconsultaCreate, db: Session = Depends(get_db)):
    codigo_sala = f"sala_{uuid.uuid4().hex[:12]}"
    nova_sala = SalaVirtualModel(
        codigo_sala=codigo_sala,
        status=StatusTeleconsulta.AGENDADA,
        data_criacao=datetime.now(timezone.utc)
    )
    db.add(nova_sala)
    db.flush()

    nova_consulta = TeleconsultaModel(
        paciente_cpf=dados.paciente_cpf,
        medico_crm=dados.medico_crm,
        sala_virtual_id=nova_sala.id,
        status=StatusTeleconsulta.AGENDADA,
        diagnostico_ciap2=dados.ciap2,
        diagnostico_cid10=dados.cid10,
        data_inicio=dados.data_hora,
    )
    db.add(nova_consulta)
    db.commit()
    db.refresh(nova_consulta)

    return {
        "id": nova_consulta.id,
        "codigo_sala": codigo_sala,
        "paciente_cpf": nova_consulta.paciente_cpf,
        "medico_crm": nova_consulta.medico_crm,
        "status": nova_consulta.status.value,
        "data_hora": nova_consulta.data_inicio.isoformat() if nova_consulta.data_inicio else None,
    }


@router.get("/salas/{codigo_sala}")
def consultar_sala_virtual(codigo_sala: str, db: Session = Depends(get_db)):
    sala = db.query(SalaVirtualModel).filter(SalaVirtualModel.codigo_sala == codigo_sala).first()
    if not sala:
        raise HTTPException(status_code=404, detail="Sala virtual não encontrada")

    consulta = db.query(TeleconsultaModel).filter(TeleconsultaModel.sala_virtual_id == sala.id).first()
    return {
        "id": sala.id,
        "codigo": sala.codigo_sala,
        "status": sala.status.value,
        "teleconsulta_id": consulta.id if consulta else None,
        "paciente_cpf": consulta.paciente_cpf if consulta else None,
    }


@router.post("/iniciar-chamada")
def iniciar_chamada(payload: IniciarChamadaRequest, db: Session = Depends(get_db)):
    consulta = db.query(TeleconsultaModel).filter(TeleconsultaModel.id == payload.teleconsulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Teleconsulta não encontrada")

    consulta.status = StatusTeleconsulta.EM_ANDAMENTO
    consulta.data_inicio = datetime.now(timezone.utc)
    db.commit()
    db.refresh(consulta)
    return {"id": consulta.id, "status": consulta.status.value, "mensagem": "Chamada iniciada"}


@router.post("/finalizar-chamada")
def finalizar_chamada(payload: FinalizarChamadaRequest, db: Session = Depends(get_db)):
    consulta = db.query(TeleconsultaModel).filter(TeleconsultaModel.id == payload.teleconsulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Teleconsulta não encontrada")

    consulta.status = StatusTeleconsulta.CONCLUIDA
    consulta.data_fim = datetime.now(timezone.utc)
    if payload.dados_soap:
        consulta.evolucao_soap = payload.dados_soap
    db.commit()
    db.refresh(consulta)
    return {"id": consulta.id, "status": consulta.status.value, "mensagem": "Chamada finalizada com sucesso"}


# =========================================================================
# ENDPOINTS EM CONFORMIDADE COM A RESOLUÇÃO CFM Nº 2.314/2022
# =========================================================================

@router.post("/tcle/gerar")
def gerar_termo_consentimento(payload: TCLEGerarRequest):
    """Gera o texto formal do TCLE conforme Art. 4º da Resolução CFM 2.314/2022."""
    paciente = PacienteIdentificacaoCFM(
        nome_completo=payload.paciente_nome,
        cpf=payload.paciente_cpf
    )
    medico = MedicoIdentificacaoCFM(
        nome_completo=payload.medico_nome,
        crm=payload.medico_crm,
        uf_crm=payload.medico_uf,
        rqe=payload.medico_rqe,
        especialidade=payload.especialidade
    )
    return MotorCFMTelemedicina.gerar_termo_consentimento_tcle(
        paciente=paciente,
        medico=medico,
        modalidade=payload.modalidade
    )


@router.post("/tcle/registrar")
def registrar_aceite_consentimento(
    payload: TCLERegistrarRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Registra auditadamente e PERSISTE o consentimento do paciente no banco (CFM 2.314/2022 e LGPD)."""
    # IP real capturado no servidor (não falsificável pelo body do cliente)
    ip_real = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else None)
        or payload.ip_origem
        or "127.0.0.1"
    )
    user_agent = request.headers.get("user-agent", "")

    texto = payload.texto_integral
    if not texto:
        paciente_info = PacienteIdentificacaoCFM(
            nome_completo=payload.paciente_nome,
            cpf=payload.paciente_cpf,
        )
        medico_info = MedicoIdentificacaoCFM(
            nome_completo="Médico Assistente",
            crm="CRM",
            uf_crm="BR",
        )
        termo = MotorCFMTelemedicina.gerar_termo_consentimento_tcle(paciente_info, medico_info)
        texto = termo["texto_integral"]

    hash_sha256 = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    cpf_limpo = re.sub(r"\D", "", payload.paciente_cpf)
    data_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    codigo_tcle = f"TCLE-{data_str}-{uuid.uuid4().hex[:8].upper()}"

    novo_consentimento = ConsentimentoTCLE(
        codigo_tcle=codigo_tcle,
        teleconsulta_id=payload.teleconsulta_id,
        cidadao_id=payload.cidadao_id,
        paciente_cpf=cpf_limpo,
        paciente_nome=payload.paciente_nome,
        versao_termo="CFM_2314_2022_V1",
        texto_integral=texto,
        hash_sha256=hash_sha256,
        ip_origem=ip_real,
        user_agent=user_agent,
        metodo_aceite=payload.metodo or "ELETRONICO_WEB",
        aceito_em=datetime.now(timezone.utc),
    )
    db.add(novo_consentimento)
    db.commit()
    db.refresh(novo_consentimento)

    return {
        "consentimento_id": novo_consentimento.codigo_tcle,
        "paciente_cpf": novo_consentimento.paciente_cpf,
        "paciente_nome": novo_consentimento.paciente_nome,
        "data_hora_aceite": novo_consentimento.aceito_em.isoformat(),
        "metodo_aceite": novo_consentimento.metodo_aceite,
        "hash_tcle": novo_consentimento.hash_sha256,
        "ip_origem": novo_consentimento.ip_origem,
        "status": "VALIDADO_CFM_2314",
    }


@router.get("/tcle/status/{paciente_cpf}")
def verificar_status_tcle_paciente(
    paciente_cpf: str,
    db: Session = Depends(get_db),
):
    """Consulta se o paciente possui consentimento TCLE válido persistido no banco."""
    cpf_limpo = re.sub(r"\D", "", paciente_cpf)
    ultimo_tcle = (
        db.query(ConsentimentoTCLE)
        .filter(ConsentimentoTCLE.paciente_cpf == cpf_limpo)
        .order_by(ConsentimentoTCLE.aceito_em.desc())
        .first()
    )
    if not ultimo_tcle:
        return {
            "tem_consentimento": False,
            "paciente_cpf": cpf_limpo,
            "status": "NAO_REGISTRADO",
        }
    return {
        "tem_consentimento": True,
        "consentimento_id": str(ultimo_tcle.id),
        "paciente_cpf": ultimo_tcle.paciente_cpf,
        "paciente_nome": ultimo_tcle.paciente_nome,
        "data_hora_aceite": ultimo_tcle.aceito_em.isoformat(),
        "hash_tcle": ultimo_tcle.hash_sha256,
        "versao_termo": ultimo_tcle.versao_termo,
        "ip_origem": ultimo_tcle.ip_origem,
        "status": "VALIDADO_CFM_2314",
    }


@router.get("/link-paciente/{codigo_sala}")
def obter_link_acesso_paciente(
    codigo_sala: str,
    paciente_nome: str = Query("Paciente"),
    medico_nome: str = Query("Dra. Francelli Neves Versiani"),
    telefone: Optional[str] = Query(None),
):
    """Gera o link efêmero direto para o paciente e mensagem de WhatsApp."""
    return MotorCFMTelemedicina.gerar_link_paciente(
        codigo_sala=codigo_sala,
        nome_paciente=paciente_nome,
        nome_medico=medico_nome,
        telefone_whatsapp=telefone
    )


@router.post("/converter-presencial")
def converter_para_presencial(payload: ConverterPresencialRequest, db: Session = Depends(get_db)):
    """Registra a prerrogativa do médico de converter teleconsulta para presencial (Art. 3º CFM)."""
    consulta = db.query(TeleconsultaModel).filter(TeleconsultaModel.id == payload.teleconsulta_id).first()
    if consulta:
        consulta.status = StatusTeleconsulta.CANCELADA
        db.commit()

    medico = MedicoIdentificacaoCFM(
        nome_completo=payload.medico_nome,
        crm=payload.medico_crm,
        uf_crm=payload.medico_uf,
    )
    resultado = MotorCFMTelemedicina.emitir_registro_conversao_presencial(
        teleconsulta_id=payload.teleconsulta_id,
        paciente_nome=payload.paciente_nome,
        medico=medico,
        motivo_clinico=payload.motivo_clinico
    )
    return resultado


@router.get("/especialidades")
def listar_especialidades():
    """Retorna todas as especialidades médicas com templates e anamneses personalizadas."""
    return listar_todas_especialidades()


@router.get("/especialidades/{codigo}")
def obter_especialidade_detalhes(codigo: str):
    """Retorna os dados e templates de uma especialidade específica."""
    esp = obter_especialidade(codigo)
    return {
        "codigo": esp.codigo,
        "nome": esp.nome,
        "icone": esp.icone,
        "descricao": esp.descricao,
        "queixas": esp.queixa_sugestoes,
        "anamnese_guia": esp.anamnese_guia,
        "exame_fisico_template": esp.exame_fisico_template,
        "codigos_frequentes": esp.principais_ciap2_cid10,
        "alertas_seguranca": esp.alertas_seguranca_telemedicina,
    }
