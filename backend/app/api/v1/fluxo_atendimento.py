"""
Endpoints REST para Orquestração do Fluxo de Atendimento Clínico e Perfis de Usuários.
MedIA Practice & Telemedicina OS.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.schemas.fluxo_atendimento import (
    JornadaAtendimentoOut,
    PreAnamneseInput,
    IntraConsultaPayload,
    PosConsultaPayload,
    PacotePosConsultaOut,
    ModalidadeAtendimentoEnum
)
from app.services.fluxo_atendimento_service import fluxo_service

router = APIRouter(prefix="/fluxo-atendimento", tags=["Orquestração do Fluxo Clínico & Perfis de Usuários"])


class NovoAgendamentoRequest(BaseModel):
    paciente_nome: str
    paciente_cpf: str
    paciente_telefone: str
    medico_nome: str = "Dr. Lucas Bittencourt"
    medico_crm: str = "CRM-MG 54.321 / RQE 12.876"
    especialidade: str = "Clínica Médica & Telemedicina"
    modalidade: ModalidadeAtendimentoEnum = ModalidadeAtendimentoEnum.TELEMEDICINA
    valor_honorarios: float = 350.00
    data_hora: Optional[str] = None


class PreConsultaRequest(BaseModel):
    pre_anamnese: PreAnamneseInput
    tcle_aceito: bool = True
    pagamento_confirmado: bool = True


@router.get("/perfis", summary="Matriz de perfis de usuários e seus fluxos operacionais")
def obter_matriz_perfis():
    """Retorna os papéis do sistema (Médico, Recepção, Paciente, Admin, Farmacêutico) e suas competências."""
    return fluxo_service.obter_matriz_perfis()


@router.get("/consultas", response_model=List[JornadaAtendimentoOut], summary="Listar todas as jornadas na agenda")
def listar_consultas():
    """Retorna a lista de consultas ativas na agenda com o progresso de cada jornada."""
    return fluxo_service.listar_jornadas_ativas()


@router.get("/{consulta_id}/jornada", response_model=JornadaAtendimentoOut, summary="Obter detalhes da jornada da consulta")
def obter_jornada(consulta_id: str):
    """Consulta o status em tempo real das etapas Pré, Intra e Pós-consulta de um paciente específico."""
    try:
        return fluxo_service.obter_jornada(consulta_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta com ID '{consulta_id}' não localizada."
        )


@router.post("/novo-agendamento", response_model=JornadaAtendimentoOut, summary="Criar novo agendamento de consulta")
def criar_agendamento(payload: NovoAgendamentoRequest):
    """Inicia um novo ciclo de atendimento na etapa AGENDADA."""
    dados = fluxo_service.criar_agendamento(
        paciente_nome=payload.paciente_nome,
        paciente_cpf=payload.paciente_cpf,
        paciente_telefone=payload.paciente_telefone,
        medico_nome=payload.medico_nome,
        medico_crm=payload.medico_crm,
        especialidade=payload.especialidade,
        modalidade=payload.modalidade,
        valor_honorarios=payload.valor_honorarios,
        data_hora=payload.data_hora
    )
    return JornadaAtendimentoOut(**dados)


@router.post("/{consulta_id}/pre-consulta", response_model=JornadaAtendimentoOut, summary="Registrar checklist de Pré-Consulta")
def registrar_pre_consulta(consulta_id: str, payload: PreConsultaRequest):
    """
    Registra a conclusão da pré-anamnese e a assinatura digital do TCLE pelo paciente.
    Avança a consulta para o estado PRE_CONSULTA.
    """
    try:
        dados = fluxo_service.registrar_pre_consulta(
            consulta_id=consulta_id,
            pre_anamnese=payload.pre_anamnese,
            tcle_aceito=payload.tcle_aceito,
            pagamento_confirmado=payload.pagamento_confirmado
        )
        return JornadaAtendimentoOut(**dados)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta com ID '{consulta_id}' não localizada."
        )


@router.post("/{consulta_id}/iniciar", response_model=JornadaAtendimentoOut, summary="Iniciar atendimento médico (Intra-Consulta)")
def iniciar_atendimento(consulta_id: str):
    """
    Registra o início da consulta pelo médico (carimbo temporal obrigatório pelo CFM 2.314/2022).
    Avança o status para EM_ATENDIMENTO.
    """
    try:
        dados = fluxo_service.iniciar_atendimento_medico(consulta_id)
        return JornadaAtendimentoOut(**dados)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta com ID '{consulta_id}' não localizada."
        )


@router.post("/intra-consulta/salvar", response_model=JornadaAtendimentoOut, summary="Salvar evolução SOAP, CID-11 e prescrição")
def salvar_evolucao_intra(payload: IntraConsultaPayload):
    """
    Grava as informações clínicas da consulta em tempo real:
    - Prontuário SOAP
    - Diagnósticos em CID-11 (OMS) com Dual-Coding em CID-10 (TISS)
    - Itens da Prescrição e Atestados
    """
    try:
        dados = fluxo_service.salvar_evolucao_intra_consulta(payload)
        return JornadaAtendimentoOut(**dados)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta com ID '{payload.consulta_id}' não localizada."
        )


@router.post("/pos-consulta/finalizar", response_model=PacotePosConsultaOut, summary="Finalizar consulta e gerar pacote Pós-Consulta")
def finalizar_consulta_e_gerar_pacote(payload: PosConsultaPayload):
    """
    Conclui o atendimento e dispara a automação de pós-consulta:
    1. Prescrição Digital ICP-Brasil / CFM com QR Code validador público
    2. Recibo oficial DMED da Receita Federal (IRPF)
    3. Escrituração no Livro Caixa / Carnê-Leão (DARF 0190)
    4. Link de acesso ao WhatsApp e Portal do Paciente
    5. Agendamento do retorno preventivo
    """
    try:
        return fluxo_service.finalizar_consulta_e_gerar_pacote_pos(payload)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta com ID '{payload.consulta_id}' não localizada."
        )
