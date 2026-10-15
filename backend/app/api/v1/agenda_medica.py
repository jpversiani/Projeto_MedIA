"""Agenda médica híbrida — consultório presencial e telemedicina.

Este módulo foi reescrito sobre o banco de dados. Antes ele mantinha um
dicionário `_AGENDA_MEMORIA` no escopo do módulo, semeado no import, com cinco
consultas fictícias. As consequências eram:

* reiniciar o servidor apagava a agenda e re-semeava os mesmos pacientes;
* com mais de um worker do uvicorn, cada processo tinha a própria agenda — a
  recepção agendava em um e o médico não via no outro;
* o agendamento não tinha `cidadao_id`, então era impossível abrir o prontuário
  de quem estava na sala de espera.

O contrato HTTP foi preservado (`GET /agenda/`, `POST /agenda/novo`,
`PATCH /agenda/{id}/status`) para não quebrar o Cockpit, e foram acrescentados
o check-in e a listagem por cidadão.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.agendamento import Agendamento, StatusAgendamento, TipoAtendimento
from app.models.cidadao import Cidadao
from app.models.estabelecimento import Estabelecimento
from app.models.fila import FilaAcolhimento
from app.models.profissional import Profissional

router = APIRouter(prefix="/agenda", tags=["Agenda Médica"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class AgendamentoCreate(BaseModel):
    """Criação de agendamento.

    O paciente é identificado por `cidadao_id` (preferencial) ou por CPF. O CPF
    é aceito para não quebrar o fluxo da recepção, que costuma ter apenas o
    documento em mãos — mas é resolvido para um cidadão cadastrado, nunca
    guardado como texto solto.
    """

    cidadao_id: Optional[int] = None
    paciente_cpf: Optional[str] = None
    paciente_nome: Optional[str] = None
    telefone_whatsapp: Optional[str] = None

    tipo: TipoAtendimento = TipoAtendimento.PRESENCIAL
    data_consulta: Optional[date] = None
    horario: str = "09:00"
    duracao_minutos: int = Field(default=30, ge=5, le=480)

    especialidade: Optional[str] = "Clínica Médica"
    motivo_queixa: Optional[str] = None

    valor_consulta: Optional[float] = None
    modalidade_pagamento: Optional[str] = None

    profissional_id: Optional[int] = None
    estabelecimento_id: Optional[int] = None
    observacoes: Optional[str] = None


class AgendamentoOut(BaseModel):
    id: int
    codigo: str
    cidadao_id: int
    paciente_nome: Optional[str] = None
    paciente_cpf: Optional[str] = None
    telefone_whatsapp: Optional[str] = None
    tipo: str
    status: str
    data_consulta: str
    horario: str
    especialidade: Optional[str] = None
    motivo_queixa: Optional[str] = None
    valor_consulta: Optional[float] = None
    codigo_sala_telemedicina: Optional[str] = None
    fila_id: Optional[int] = None
    profissional_id: Optional[int] = None
    estabelecimento_id: Optional[int] = None


class CheckinOut(BaseModel):
    agendamento_id: int
    fila_id: int
    cidadao_id: int
    status_agendamento: str
    mensagem: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_horario(valor: str) -> time:
    """Converte 'HH:MM' em `time`, com mensagem clara se o formato for inválido."""
    try:
        hh, mm = valor.strip().split(":")
        return time(int(hh), int(mm))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=422,
            detail=f"Horário inválido: {valor!r}. Use o formato HH:MM (ex.: 09:30).",
        )


def _serializar(ag: Agendamento) -> AgendamentoOut:
    cidadao = ag.cidadao
    return AgendamentoOut(
        id=ag.id,
        codigo=ag.codigo,
        cidadao_id=ag.cidadao_id,
        paciente_nome=cidadao.nome_completo if cidadao else None,
        paciente_cpf=cidadao.cpf if cidadao else None,
        telefone_whatsapp=cidadao.telefone if cidadao else None,
        tipo=ag.tipo,
        status=ag.status,
        data_consulta=ag.data_consulta.isoformat() if ag.data_consulta else "",
        horario=ag.horario.strftime("%H:%M") if ag.horario else "",
        especialidade=ag.especialidade,
        motivo_queixa=ag.motivo_queixa,
        valor_consulta=ag.valor_consulta,
        codigo_sala_telemedicina=ag.codigo_sala_telemedicina,
        fila_id=ag.fila_id,
        profissional_id=ag.profissional_id,
        estabelecimento_id=ag.estabelecimento_id,
    )


def _resolver_cidadao(
    db: Session,
    cidadao_id: Optional[int],
    cpf: Optional[str],
) -> Cidadao:
    """Localiza o cidadão do agendamento, exigindo que ele exista no cadastro."""
    if cidadao_id:
        cidadao = db.query(Cidadao).filter(Cidadao.id == cidadao_id).first()
        if not cidadao:
            raise HTTPException(status_code=404, detail="Cidadão não encontrado.")
        return cidadao

    if cpf:
        cpf_limpo = "".join(filter(str.isdigit, cpf))
        cidadao = db.query(Cidadao).filter(Cidadao.cpf == cpf_limpo).first()
        if not cidadao:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Nenhum cidadão cadastrado com o CPF {cpf_limpo}. "
                    "Cadastre o paciente antes de agendar (POST /api/v1/cidadaos/)."
                ),
            )
        return cidadao

    raise HTTPException(
        status_code=422,
        detail="Informe `cidadao_id` ou `paciente_cpf` para identificar o paciente.",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/")
def listar_consultas_agenda(
    data: Optional[str] = Query(None, description="Data no formato AAAA-MM-DD"),
    tipo: Optional[str] = Query(None, description="PRESENCIAL, TELEMEDICINA ou vazio para todas"),
    status_consulta: Optional[str] = Query(None, description="Filtrar por status"),
    db: Session = Depends(get_db),
):
    """Lista as consultas da agenda médica com suporte a filtros híbridos."""
    data_filtro = data or date.today().isoformat()
    try:
        dia = date.fromisoformat(data_filtro)
    except ValueError:
        raise HTTPException(
            status_code=422, detail=f"Data inválida: {data_filtro!r}. Use AAAA-MM-DD."
        )

    query = db.query(Agendamento).filter(Agendamento.data_consulta == dia)
    if tipo:
        query = query.filter(Agendamento.tipo == tipo)
    if status_consulta:
        query = query.filter(Agendamento.status == status_consulta)

    consultas = query.order_by(Agendamento.horario.asc()).all()
    itens = [_serializar(a) for a in consultas]

    return {
        "data_referencia": data_filtro,
        "total": len(itens),
        "total_presencial": sum(1 for x in itens if x.tipo == TipoAtendimento.PRESENCIAL.value),
        "total_telemedicina": sum(1 for x in itens if x.tipo == TipoAtendimento.TELEMEDICINA.value),
        "consultas": itens,
    }


@router.post("/novo", status_code=status.HTTP_201_CREATED, response_model=AgendamentoOut)
def criar_agendamento_consulta(payload: AgendamentoCreate, db: Session = Depends(get_db)):
    """Cria um novo agendamento de consulta presencial ou telemedicina."""
    cidadao = _resolver_cidadao(db, payload.cidadao_id, payload.paciente_cpf)

    # Estabelecimento é obrigatório no modelo da fila; usamos o informado ou o
    # primeiro cadastrado, para que o check-in sempre tenha destino.
    estabelecimento_id = payload.estabelecimento_id
    if not estabelecimento_id:
        primeiro = db.query(Estabelecimento).order_by(Estabelecimento.id).first()
        estabelecimento_id = primeiro.id if primeiro else None

    codigo_sala = None
    if payload.tipo == TipoAtendimento.TELEMEDICINA:
        codigo_sala = f"sala_{uuid.uuid4().hex[:10]}"

    agendamento = Agendamento(
        codigo=f"AG-{uuid.uuid4().hex[:6].upper()}",
        cidadao_id=cidadao.id,
        profissional_id=payload.profissional_id,
        estabelecimento_id=estabelecimento_id,
        tipo=payload.tipo.value,
        status=StatusAgendamento.AGENDADO.value,
        data_consulta=payload.data_consulta or date.today(),
        horario=_parse_horario(payload.horario),
        duracao_minutos=payload.duracao_minutos,
        especialidade=payload.especialidade,
        motivo_queixa=payload.motivo_queixa,
        valor_consulta=payload.valor_consulta,
        modalidade_pagamento=payload.modalidade_pagamento,
        codigo_sala_telemedicina=codigo_sala,
        observacoes=payload.observacoes,
    )
    db.add(agendamento)
    db.commit()
    db.refresh(agendamento)
    return _serializar(agendamento)


@router.patch("/{consulta_id}/status", response_model=AgendamentoOut)
def atualizar_status_consulta(
    consulta_id: str, novo_status: str = Query(..., description="Novo status do agendamento"),
    db: Session = Depends(get_db),
):
    """Atualiza o status de atendimento de uma consulta na agenda.

    Aceita tanto o `id` numérico quanto o `codigo` (AG-XXXXXX), porque o
    Cockpit historicamente trabalhava com o código.
    """
    agendamento = _buscar_agendamento(db, consulta_id)

    try:
        status_enum = StatusAgendamento(novo_status)
    except ValueError:
        validos = ", ".join(s.value for s in StatusAgendamento)
        raise HTTPException(
            status_code=422, detail=f"Status inválido: {novo_status!r}. Válidos: {validos}."
        )

    agendamento.status = status_enum.value
    db.commit()
    db.refresh(agendamento)
    return _serializar(agendamento)


def _buscar_agendamento(db: Session, identificador: str) -> Agendamento:
    agendamento = None
    if identificador.isdigit():
        agendamento = db.query(Agendamento).filter(Agendamento.id == int(identificador)).first()
    if not agendamento:
        agendamento = db.query(Agendamento).filter(Agendamento.codigo == identificador).first()
    if not agendamento:
        raise HTTPException(status_code=404, detail="Consulta não encontrada na agenda.")
    return agendamento


# ---------------------------------------------------------------------------
# Check-in: liga a agenda à fila de acolhimento
# ---------------------------------------------------------------------------
@router.post("/{consulta_id}/checkin", status_code=status.HTTP_201_CREATED, response_model=CheckinOut)
def realizar_checkin(
    consulta_id: str,
    classificacao_risco: str = Query("VERDE", description="VERMELHO, AMARELO, VERDE ou AZUL"),
    motivo_acolhimento: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Coloca o paciente agendado na fila de acolhimento.

    Este é o elo que faltava entre a agenda e o atendimento: sem ele, o
    paciente agendado não chegava à fila, o médico não tinha como chamá-lo, e
    não havia caminho de um agendamento até o prontuário.

    A operação é idempotente: um segundo check-in no mesmo agendamento devolve
    a entrada de fila já criada em vez de duplicar o paciente na espera.
    """
    agendamento = _buscar_agendamento(db, consulta_id)

    if agendamento.status == StatusAgendamento.CANCELADO.value:
        raise HTTPException(
            status_code=409, detail="Agendamento cancelado não pode fazer check-in."
        )

    if agendamento.fila_id:
        return CheckinOut(
            agendamento_id=agendamento.id,
            fila_id=agendamento.fila_id,
            cidadao_id=agendamento.cidadao_id,
            status_agendamento=agendamento.status,
            mensagem="Check-in já realizado para este agendamento.",
        )

    if not agendamento.estabelecimento_id:
        raise HTTPException(
            status_code=409,
            detail="Agendamento sem estabelecimento definido; não é possível acolher.",
        )

    risco = (classificacao_risco or "VERDE").upper()
    if risco not in {"VERMELHO", "AMARELO", "VERDE", "AZUL"}:
        raise HTTPException(
            status_code=422,
            detail=f"Classificação de risco inválida: {classificacao_risco!r}.",
        )

    entrada = FilaAcolhimento(
        cidadao_id=agendamento.cidadao_id,
        estabelecimento_id=agendamento.estabelecimento_id,
        profissional_triagem_id=agendamento.profissional_id,
        data_hora_entrada=datetime.now(timezone.utc),
        tipo_demanda="AGENDADA",
        classificacao_risco=risco,
        motivo_acolhimento=motivo_acolhimento or agendamento.motivo_queixa,
        status="AGUARDANDO_ATENDIMENTO",
    )
    db.add(entrada)
    db.flush()

    agendamento.fila_id = entrada.id
    agendamento.status = StatusAgendamento.SALA_DE_ESPERA.value
    db.commit()
    db.refresh(agendamento)

    return CheckinOut(
        agendamento_id=agendamento.id,
        fila_id=entrada.id,
        cidadao_id=agendamento.cidadao_id,
        status_agendamento=agendamento.status,
        mensagem="Paciente acolhido e aguardando atendimento.",
    )


@router.get("/cidadao/{cidadao_id}", response_model=List[AgendamentoOut])
def listar_agendamentos_do_cidadao(
    cidadao_id: int,
    limite: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Histórico de agendamentos de um paciente.

    Só é possível porque o agendamento passou a ter `cidadao_id`; antes o
    vínculo era um CPF em texto livre e esta consulta não existia.
    """
    cidadao = db.query(Cidadao).filter(Cidadao.id == cidadao_id).first()
    if not cidadao:
        raise HTTPException(status_code=404, detail="Cidadão não encontrado.")

    agendamentos = (
        db.query(Agendamento)
        .filter(Agendamento.cidadao_id == cidadao_id)
        .order_by(Agendamento.data_consulta.desc(), Agendamento.horario.desc())
        .limit(limite)
        .all()
    )
    return [_serializar(a) for a in agendamentos]
