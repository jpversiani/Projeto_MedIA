"""
Schemas Pydantic v2 para Orquestração do Fluxo de Atendimento Clínico e Perfis de Usuários.
MedIA Practice & Telemedicina OS.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EtapaFluxoEnum(str, Enum):
    AGENDADA = "AGENDADA"
    PRE_CONSULTA = "PRE_CONSULTA"
    EM_ATENDIMENTO = "EM_ATENDIMENTO"
    POS_CONSULTA = "POS_CONSULTA"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"


class ModalidadeAtendimentoEnum(str, Enum):
    PRESENCIAL = "PRESENCIAL"
    TELEMEDICINA = "TELEMEDICINA"


class PapelUsuarioEnum(str, Enum):
    MEDICO = "MEDICO"
    RECEPCAO = "RECEPCAO"
    PACIENTE = "PACIENTE"
    ADMIN = "ADMIN"
    FARMACEUTICO = "FARMACEUTICO"


# -------------------------------------------------------------
# 1. PRÉ-CONSULTA
# -------------------------------------------------------------

class PreAnamneseInput(BaseModel):
    motivo_consulta: str = Field(..., description="Queixa ou motivo informado pelo paciente previamente")
    sintomas_principais: list[str] = Field(default_factory=list, description="Lista de sintomas relatados")
    medicamentos_em_uso: list[str] = Field(default_factory=list, description="Medicações que o paciente já toma")
    alergias_conhecidas: list[str] = Field(default_factory=list, description="Alergias a medicamentos ou substâncias")
    pressao_arterial_recente: str | None = None
    glicemia_recente: str | None = None
    observacoes_paciente: str | None = None


class ChecklistPreConsulta(BaseModel):
    tcle_confirmado: bool = False
    pagamento_confirmado: bool = False
    pre_anamnese_preenchida: bool = False
    historico_revisado_medico: bool = False
    dispositivo_testado: bool = True  # Áudio e vídeo testados pelo paciente


# -------------------------------------------------------------
# 2. INTRA-CONSULTA
# -------------------------------------------------------------

class DiagnosticoDualCodingInput(BaseModel):
    cid11_codigo: str = Field(..., description="Código oficial CID-11 MMS (ex: BA00, 5A11)")
    cid11_titulo: str
    cid10_codigo: str | None = Field(None, description="Código equivalente CID-10 para faturamento TISS")
    observacao: str | None = None


class MedicamentoPrescritoInput(BaseModel):
    nome_farmaco: str
    dosagem: str
    forma_farmaceutica: str
    posologia: str
    duracao_dias: int
    quantidade: str
    tipo_receita: str = "SIMPLES" # "SIMPLES", "CONTROLE_ESPECIAL", "ANTIMICROBIANO"


class ExameSolicitadoInput(BaseModel):
    codigo_tuss: str | None = None
    descricao_exame: str
    justificativa_clinica: str | None = None


class AtestadoInput(BaseModel):
    dias_afastamento: int = 1
    motivo_manifesto: str | None = None
    incluir_cid: bool = False
    cid_codigo: str | None = None


class IntraConsultaPayload(BaseModel):
    consulta_id: str
    soap_subjetivo: str
    soap_objetivo: str
    soap_avaliacao: str
    soap_plano: str
    diagnosticos: list[DiagnosticoDualCodingInput] = Field(default_factory=list)
    prescricoes: list[MedicamentoPrescritoInput] = Field(default_factory=list)
    exames: list[ExameSolicitadoInput] = Field(default_factory=list)
    atestado: AtestadoInput | None = None
    escala_risco: dict[str, Any] | None = None  # ex: Framingham, CKD-EPI


# -------------------------------------------------------------
# 3. PÓS-CONSULTA
# -------------------------------------------------------------

class PosConsultaPayload(BaseModel):
    consulta_id: str
    emitir_recibo_dmed: bool = True
    lancar_livro_caixa: bool = True
    dias_retorno_sugerido: int | None = 30
    canal_despacho_paciente: str = "WHATSAPP" # "WHATSAPP", "PORTAL", "EMAIL"


class PacotePosConsultaOut(BaseModel):
    consulta_id: str
    paciente_nome: str
    medico_nome: str
    medico_crm: str
    data_atendimento: str
    link_paciente_portal: str
    link_whatsapp_despacho: str
    codigo_verificador_receita: str | None = None
    codigo_verificador_atestado: str | None = None
    recibo_dmed_numero: str | None = None
    valor_consulta: float
    livro_caixa_id: str | None = None
    darf_carnê_leão_prevista: float
    retorno_agendado_para: str | None = None
    status: EtapaFluxoEnum


# -------------------------------------------------------------
# 4. STATUS CONSOLIDADO DA JORNADA
# -------------------------------------------------------------

class JornadaAtendimentoOut(BaseModel):
    consulta_id: str
    paciente_id: int
    paciente_nome: str
    paciente_cpf: str
    paciente_telefone: str
    medico_id: int
    medico_nome: str
    medico_crm: str
    especialidade: str
    modalidade: ModalidadeAtendimentoEnum
    etapa_atual: EtapaFluxoEnum
    checklist_pre: ChecklistPreConsulta
    pre_anamnese: PreAnamneseInput | None = None
    data_hora_agendamento: str
    data_hora_inicio: str | None = None
    data_hora_fim: str | None = None
    duracao_minutos: int | None = None
    valor_honorarios: float
    sala_virtual_url: str | None = None
    tcle_aceito: bool = False
    tcle_timestamp: str | None = None
    pacote_pos_consulta: PacotePosConsultaOut | None = None

    model_config = ConfigDict(from_attributes=True)
