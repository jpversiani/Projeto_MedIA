"""
API de Agenda Médica Híbrida — Consultório Presencial & Telemedicina Home Office
Otimizada para o médico autônomo e de consultório privado.
"""

from datetime import date, datetime, time, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/agenda", tags=["Agenda Médica"])


class TipoAtendimento(str, Enum):
    PRESENCIAL = "PRESENCIAL"
    TELEMEDICINA = "TELEMEDICINA"


class StatusConsultaAgenda(str, Enum):
    AGENDADO = "AGENDADO"
    SALA_DE_ESPERA = "SALA_DE_ESPERA"
    EM_CONSULTA = "EM_CONSULTA"
    CONCLUIDO = "CONCLUIDO"
    CANCELADO = "CANCELADO"


class AgendamentoCreate(BaseModel):
    paciente_nome: str
    paciente_cpf: str
    telefone_whatsapp: Optional[str] = None
    email: Optional[str] = None
    tipo: TipoAtendimento = TipoAtendimento.TELEMEDICINA
    horario: str = "09:00"
    data_consulta: Optional[str] = None
    especialidade: str = "Clínica Médica"
    motivo_queixa: Optional[str] = None
    valor_consulta: float = 300.00
    modalidade_pagamento: str = "PARTICULAR_PIX"


class AgendamentoItem(BaseModel):
    id: str
    paciente_nome: str
    paciente_cpf: str
    telefone_whatsapp: Optional[str]
    email: Optional[str]
    tipo: TipoAtendimento
    horario: str
    data_consulta: str
    especialidade: str
    motivo_queixa: Optional[str]
    valor_consulta: float
    status: StatusConsultaAgenda
    codigo_sala_telemedicina: Optional[str] = None
    link_whatsapp: Optional[str] = None


# Armazenamento em memória com semente de consultas para o consultório / home office do médico
_AGENDA_MEMORIA: Dict[str, Dict[str, Any]] = {}

def _inicializar_semente():
    if _AGENDA_MEMORIA:
        return
    hoje = date.today().isoformat()
    sementes = [
        {
            "id": "AG-01",
            "paciente_nome": "Mariana Souza Alencar",
            "paciente_cpf": "12345678901",
            "telefone_whatsapp": "38998765432",
            "email": "mariana.alencar@email.com",
            "tipo": TipoAtendimento.TELEMEDICINA,
            "horario": "08:30",
            "data_consulta": hoje,
            "especialidade": "Psiquiatria & Saúde Mental",
            "motivo_queixa": "Ajuste de escitalopram e ansiedade com insônia",
            "valor_consulta": 350.00,
            "status": StatusConsultaAgenda.SALA_DE_ESPERA,
            "codigo_sala_telemedicina": "sala_mariana_psi01",
        },
        {
            "id": "AG-02",
            "paciente_nome": "Roberto Carlos Fagundes",
            "paciente_cpf": "98765432100",
            "telefone_whatsapp": "38991234567",
            "email": "roberto.fagundes@email.com",
            "tipo": TipoAtendimento.PRESENCIAL,
            "horario": "09:15",
            "data_consulta": hoje,
            "especialidade": "Cardiologia",
            "motivo_queixa": "Retorno pós-holter 24h e palpação de ictus",
            "valor_consulta": 400.00,
            "status": StatusConsultaAgenda.AGENDADO,
            "codigo_sala_telemedicina": None,
        },
        {
            "id": "AG-03",
            "paciente_nome": "Juliana Mendes Prado",
            "paciente_cpf": "45678912344",
            "telefone_whatsapp": "38988776655",
            "email": "juliana.prado@email.com",
            "tipo": TipoAtendimento.TELEMEDICINA,
            "horario": "10:00",
            "data_consulta": hoje,
            "especialidade": "Dermatologia",
            "motivo_queixa": "Avaliação de lesão eritematosa pruriginosa em antebraço",
            "valor_consulta": 350.00,
            "status": StatusConsultaAgenda.AGENDADO,
            "codigo_sala_telemedicina": "sala_juliana_derm02",
        },
        {
            "id": "AG-04",
            "paciente_nome": "Carlos Eduardo Pereira",
            "paciente_cpf": "11122233344",
            "telefone_whatsapp": "38999112233",
            "email": "carlos.pereira@email.com",
            "tipo": TipoAtendimento.PRESENCIAL,
            "horario": "11:00",
            "data_consulta": hoje,
            "especialidade": "Clínica Médica / Geral",
            "motivo_queixa": "Check-up de rotina e controle pressórico",
            "valor_consulta": 300.00,
            "status": StatusConsultaAgenda.AGENDADO,
            "codigo_sala_telemedicina": None,
        },
        {
            "id": "AG-05",
            "paciente_nome": "Camila Guimarães Ribeiro",
            "paciente_cpf": "55566677788",
            "telefone_whatsapp": "38992345678",
            "email": "camila.ribeiro@email.com",
            "tipo": TipoAtendimento.TELEMEDICINA,
            "horario": "14:00",
            "data_consulta": hoje,
            "especialidade": "Endocrinologia & Metabologia",
            "motivo_queixa": "Ajuste de dose de levotiroxina e TSH recente",
            "valor_consulta": 380.00,
            "status": StatusConsultaAgenda.AGENDADO,
            "codigo_sala_telemedicina": "sala_camila_endo03",
        },
    ]
    for item in sementes:
        _AGENDA_MEMORIA[item["id"]] = item

_inicializar_semente()


@router.get("/")
def listar_consultas_agenda(
    data: Optional[str] = Query(None, description="Data no formato AAAA-MM-DD"),
    tipo: Optional[str] = Query(None, description="PRESENCIAL, TELEMEDICINA ou vazio para todas"),
    status_consulta: Optional[str] = Query(None, description="Filtrar por status"),
):
    """Lista as consultas da agenda médica com suporte a filtros híbridos."""
    data_filtro = data or date.today().isoformat()
    resultado = []

    for item in _AGENDA_MEMORIA.values():
        if item["data_consulta"] != data_filtro:
            continue
        if tipo and item["tipo"] != tipo:
            continue
        if status_consulta and item["status"] != status_consulta:
            continue
        resultado.append(item)

    resultado.sort(key=lambda x: x["horario"])
    return {
        "data_referencia": data_filtro,
        "total": len(resultado),
        "total_presencial": sum(1 for x in resultado if x["tipo"] == TipoAtendimento.PRESENCIAL),
        "total_telemedicina": sum(1 for x in resultado if x["tipo"] == TipoAtendimento.TELEMEDICINA),
        "consultas": resultado,
    }


@router.post("/novo", status_code=status.HTTP_201_CREATED)
def criar_agendamento_consulta(payload: AgendamentoCreate):
    """Cria um novo agendamento de consulta presencial ou telemedicina."""
    novo_id = f"AG-{uuid.uuid4().hex[:6].upper()}"
    data_cons = payload.data_consulta or date.today().isoformat()
    
    codigo_sala = None
    if payload.tipo == TipoAtendimento.TELEMEDICINA:
        codigo_sala = f"sala_{uuid.uuid4().hex[:10]}"

    item = {
        "id": novo_id,
        "paciente_nome": payload.paciente_nome,
        "paciente_cpf": payload.paciente_cpf,
        "telefone_whatsapp": payload.telefone_whatsapp,
        "email": payload.email,
        "tipo": payload.tipo.value,
        "horario": payload.horario,
        "data_consulta": data_cons,
        "especialidade": payload.especialidade,
        "motivo_queixa": payload.motivo_queixa,
        "valor_consulta": payload.valor_consulta,
        "status": StatusConsultaAgenda.AGENDADO.value,
        "codigo_sala_telemedicina": codigo_sala,
    }
    _AGENDA_MEMORIA[novo_id] = item
    return item


@router.patch("/{consulta_id}/status")
def atualizar_status_consulta(consulta_id: str, novo_status: StatusConsultaAgenda):
    """Atualiza o status de atendimento de uma consulta na agenda."""
    if consulta_id not in _AGENDA_MEMORIA:
        raise HTTPException(status_code=404, detail="Consulta não encontrada na agenda")
    
    _AGENDA_MEMORIA[consulta_id]["status"] = novo_status.value
    return _AGENDA_MEMORIA[consulta_id]
