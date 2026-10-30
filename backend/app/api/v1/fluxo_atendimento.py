"""
Endpoints REST para Orquestração do Fluxo de Atendimento Clínico e Perfis de Usuários.
MedIA Practice & Telemedicina OS.

**P0-4, parte 2:** todas as rotas passam uma sessão ao serviço, que persiste a
jornada em ``jornadas_atendimento``. Antes o estado vivia só num dicionário do
processo: reiniciar o servidor apagava a consulta em andamento e cada worker
via uma lista diferente. As rotas também propagam o tenant do token
(``estabelecimento_id``/``profissional_id``) para a jornada.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.crypto import hash_busca
from app.core.database import get_db
from app.models.agendamento import Agendamento
from app.models.cidadao import Cidadao
from app.models.jornada import JornadaAtendimento
from app.schemas.fluxo_atendimento import (
    JornadaAtendimentoOut,
    PreAnamneseInput,
    IntraConsultaPayload,
    PosConsultaPayload,
    PacotePosConsultaOut,
    ModalidadeAtendimentoEnum,
)
from app.services.fluxo_atendimento_service import fluxo_service

from app.core.rbac import (
    PAPEIS_ACOLHIMENTO,
    ContextoClinico,
    dependencias_rbac,
    get_contexto_clinico,
)
router = APIRouter(prefix="/fluxo-atendimento", tags=["Orquestração do Fluxo Clínico & Perfis de Usuários"], dependencies=dependencias_rbac(*PAPEIS_ACOLHIMENTO))


class NovoAgendamentoRequest(BaseModel):
    paciente_nome: str = Field(min_length=1)
    # Aceita CPF formatado ("123.456.789-00") ou só dígitos; a normalização
    # acontece na rota, não na validação de tamanho.
    paciente_cpf: str = Field(min_length=11, max_length=20)
    paciente_telefone: str = ""
    medico_nome: str = "Dr. Lucas Bittencourt"
    medico_crm: str = "CRM-MG 54.321 / RQE 12.876"
    especialidade: str = "Clínica Médica & Telemedicina"
    modalidade: ModalidadeAtendimentoEnum = ModalidadeAtendimentoEnum.TELEMEDICINA
    valor_honorarios: float = 350.00
    data_hora: Optional[str] = None
    # Vínculos reais. Sem eles a jornada não tem paciente nem tenant — que era
    # o estado anterior, em que `paciente_id` era sorteado com uuid4.
    cidadao_id: Optional[int] = None
    agendamento_codigo: Optional[str] = Field(
        default=None, description="Código do agendamento da agenda a vincular."
    )


class PreConsultaRequest(BaseModel):
    pre_anamnese: PreAnamneseInput
    tcle_aceito: bool = True
    pagamento_confirmado: bool = True


def _escopo(contexto: Optional[ContextoClinico]) -> tuple[Optional[int], Optional[int]]:
    if contexto is None:
        return None, None
    return contexto.estabelecimento_id, contexto.profissional_id


def _resolver_cidadao(
    db: Session, cidadao_id: Optional[int], cpf: str
) -> Optional[Cidadao]:
    if cidadao_id is not None:
        return db.get(Cidadao, cidadao_id)
    cpf_limpo = "".join(filter(str.isdigit, cpf))
    if not cpf_limpo:
        return None
    # CPF cifrado em repouso: igualdade pelo índice cego (HMAC).
    return db.query(Cidadao).filter(Cidadao.cpf_hash == hash_busca(cpf_limpo)).first()


def _resolver_agendamento(
    db: Session, codigo: Optional[str]
) -> Optional[Agendamento]:
    if not codigo:
        return None
    return db.query(Agendamento).filter(Agendamento.codigo == codigo).first()


@router.get("/perfis", summary="Matriz de perfis de usuários e seus fluxos operacionais")
def obter_matriz_perfis():
    """Retorna os papéis do sistema (Médico, Recepção, Paciente, Admin, Farmacêutico) e suas competências."""
    return fluxo_service.obter_matriz_perfis()


@router.get("/consultas", response_model=List[JornadaAtendimentoOut], summary="Listar todas as jornadas na agenda")
def listar_consultas(
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    """Retorna as consultas ativas, lendo também o que está persistido."""
    return fluxo_service.listar_jornadas_ativas(db=db)


@router.get("/{consulta_id}/jornada", response_model=JornadaAtendimentoOut, summary="Obter detalhes da jornada da consulta")
def obter_jornada(
    consulta_id: str,
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    """Consulta o status em tempo real das etapas Pré, Intra e Pós-consulta de um paciente específico."""
    try:
        return fluxo_service.obter_jornada(consulta_id, db=db)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta com ID '{consulta_id}' não localizada."
        )


@router.post("/novo-agendamento", response_model=JornadaAtendimentoOut, summary="Criar novo agendamento de consulta")
def criar_agendamento(
    payload: NovoAgendamentoRequest,
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    """Inicia um novo ciclo de atendimento na etapa AGENDADA.

    Quando o CPF corresponde a um cidadão cadastrado, a jornada é vinculada a
    ele (``cidadao_id``). Isso é o que permite finalizar a consulta emitindo
    documentos para o paciente certo, e não para um id sorteado.
    """
    estabelecimento_id, profissional_id = _escopo(contexto)

    cpf_normalizado = "".join(filter(str.isdigit, payload.paciente_cpf))
    cidadao = _resolver_cidadao(db, payload.cidadao_id, cpf_normalizado)
    agendamento = _resolver_agendamento(db, payload.agendamento_codigo)
    if agendamento is not None:
        cidadao = cidadao or db.get(Cidadao, agendamento.cidadao_id)
        profissional_id = profissional_id or agendamento.profissional_id
        estabelecimento_id = estabelecimento_id or agendamento.estabelecimento_id

    consulta_id = None
    if agendamento is not None:
        # Reaproveita a jornada existente do agendamento, se houver.
        existente = (
            db.query(JornadaAtendimento)
            .filter(JornadaAtendimento.consulta_id == agendamento.codigo)
            .first()
        ) or (
            db.query(JornadaAtendimento)
            .filter(JornadaAtendimento.agendamento_id == agendamento.id)
            .first()
        )
        if existente is not None:
            return fluxo_service.obter_jornada(existente.consulta_id, db=db)
        consulta_id = agendamento.codigo

    dados = fluxo_service.criar_agendamento(
        paciente_nome=payload.paciente_nome,
        paciente_cpf=cpf_normalizado,
        paciente_telefone=payload.paciente_telefone,
        medico_nome=payload.medico_nome,
        medico_crm=payload.medico_crm,
        especialidade=payload.especialidade,
        modalidade=payload.modalidade,
        valor_honorarios=payload.valor_honorarios,
        data_hora=payload.data_hora,
        db=db,
        cidadao_id=cidadao.id if cidadao is not None else None,
        profissional_id=profissional_id,
        estabelecimento_id=estabelecimento_id,
        agendamento_id=agendamento.id if agendamento is not None else None,
        consulta_id=consulta_id,
        # O código real da sala (quando telemedicina): é ele que entra no link
        # do paciente — antes a URL era montada com o `consulta_id`.
        codigo_sala=agendamento.codigo_sala_telemedicina if agendamento is not None else None,
    )
    return JornadaAtendimentoOut(**dados)


@router.post("/{consulta_id}/pre-consulta", response_model=JornadaAtendimentoOut, summary="Registrar checklist de Pré-Consulta")
def registrar_pre_consulta(
    consulta_id: str,
    payload: PreConsultaRequest,
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    """
    Registra a conclusão da pré-anamnese e a assinatura digital do TCLE pelo paciente.
    Avança a consulta para o estado PRE_CONSULTA.
    """
    try:
        dados = fluxo_service.registrar_pre_consulta(
            consulta_id=consulta_id,
            pre_anamnese=payload.pre_anamnese,
            tcle_aceito=payload.tcle_aceito,
            pagamento_confirmado=payload.pagamento_confirmado,
            db=db,
        )
        return JornadaAtendimentoOut(**dados)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta com ID '{consulta_id}' não localizada."
        )


@router.post("/{consulta_id}/iniciar", response_model=JornadaAtendimentoOut, summary="Iniciar atendimento médico (Intra-Consulta)")
def iniciar_atendimento(
    consulta_id: str,
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    """Marca o início do atendimento e registra o timestamp exigido pelo CFM."""
    try:
        dados = fluxo_service.iniciar_atendimento_medico(consulta_id, db=db)
        return JornadaAtendimentoOut(**dados)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta com ID '{consulta_id}' não localizada."
        )


@router.post("/intra-consulta/salvar", response_model=JornadaAtendimentoOut, summary="Salvar evolução SOAP, CID-11 e prescrição")
def salvar_evolucao_intra(
    payload: IntraConsultaPayload,
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    """Persiste SOAP, hipóteses CID-11/CID-10, prescrições e exames da consulta em andamento."""
    try:
        dados = fluxo_service.salvar_evolucao_intra_consulta(payload, db=db)
        return JornadaAtendimentoOut(**dados)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta com ID '{payload.consulta_id}' não localizada."
        )


@router.post("/pos-consulta/finalizar", response_model=PacotePosConsultaOut, summary="Finalizar consulta e gerar pacote Pós-Consulta")
def finalizar_consulta_e_gerar_pacote(
    payload: PosConsultaPayload,
    contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    db: Session = Depends(get_db),
):
    """
    Conclui o atendimento e dispara a automação de pós-consulta:
    1. Prescrição Digital ICP-Brasil / CFM com QR Code validador público
    2. Recibo oficial DMED da Receita Federal (IRPF)
    3. Escrituração no Livro Caixa / Carnê-Leão (DARF 0190)
    4. Link de acesso ao WhatsApp e Portal do Paciente
    5. Agendamento do retorno preventivo
    """
    try:
        return fluxo_service.finalizar_consulta_e_gerar_pacote_pos(payload, db=db)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta com ID '{payload.consulta_id}' não localizada."
        )
