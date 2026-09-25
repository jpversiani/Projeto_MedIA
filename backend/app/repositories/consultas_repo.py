"""Repositório de Consultas da Atenção Primária à Saúde (APS).

Módulo responsável pela persistência e pelas regras de acesso a dados do
agendamento de consultas no contexto do SUS/APS (Projeto MedIA):

- Agendamento de consultas APS com validação de CNS (algoritmo oficial do
  Ministério da Saúde/DATASUS), verificação de conflito de agenda do
  profissional e codificação CIAP-2 (problema) / CID-10 (diagnóstico);
- Listagem da agenda por profissional (cronológica ou priorizada) e por dia,
  com ordenação pela Classificação de Risco de Manchester
  (Vermelho > Laranja > Amarelo > Verde > Azul);
- Cancelamento de consulta com motivo obrigatório e trilha de auditoria;
- Histórico longitudinal do cidadão identificado pelo CNS (linha de vida);
- Contadores de absenteísmo (no-show) por paciente, no formato esperado
  para indicadores de gestão da agenda na APS.

Padrões adotados: SQLAlchemy 2.0 (``Mapped`` / ``mapped_column``), Pydantic v2
com tipagem estrita, identificação por CNS/CPF e terminologias CIAP-2 e
CID-10. Todas as mensagens, comentários e docstrings em Português do Brasil.
"""

from collections.abc import Sequence
from datetime import date, datetime, timedelta
from enum import StrEnum
from re import Pattern, compile as re_compilar
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    ColumnElement,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    case,
    func,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.core.database import Base
from app.models.cidadao import Cidadao
from app.models.estabelecimento import Estabelecimento
from app.models.profissional import Profissional
from app.services.validacao_cns import CNSInvalidoError, ValidadorCNS

__all__ = [
    "PrioridadeManchester",
    "StatusConsulta",
    "TipoConsultaAPS",
    "ConsultaAPS",
    "ConsultaAPSCreate",
    "ConsultaCancelamentoInput",
    "ConsultaAPSRead",
    "AbsenteismoResumo",
    "CNSInvalidoError",
    "CidadaoNaoEncontradoError",
    "ProfissionalNaoEncontradoError",
    "EstabelecimentoNaoEncontradoError",
    "ConsultaNaoEncontradaError",
    "ConflitoDeAgendaError",
    "TransicaoDeStatusInvalidaError",
    "ConsultasRepository",
]


# ---------------------------------------------------------------------------
# Enumerações do domínio (padrões SUS / APS)
# ---------------------------------------------------------------------------


class StatusConsulta(StrEnum):
    """Estados possíveis de uma consulta APS ao longo do seu ciclo de vida.

    ``FALTA`` registra o absenteísmo (no-show) do cidadão e alimenta os
    contadores de gestão da agenda.
    """

    AGENDADA = "AGENDADA"
    CONFIRMADA = "CONFIRMADA"
    REALIZADA = "REALIZADA"
    FALTA = "FALTA"
    CANCELADA = "CANCELADA"


class PrioridadeManchester(StrEnum):
    """Cores da Classificação de Risco de Manchester (prioridade clínica).

    Ordem canônica de atendimento na APS: VERMELHO (emergência, imediato),
    LARANJA (muito urgente, até 10 min), AMARELO (urgente, até 60 min),
    VERDE (pouco urgente, até 120 min) e AZUL (não urgente, até 240 min).
    """

    VERMELHO = "VERMELHO"
    LARANJA = "LARANJA"
    AMARELO = "AMARELO"
    VERDE = "VERDE"
    AZUL = "AZUL"

    @property
    def ordem(self) -> int:
        """Posição canônica na fila de atendimento (1 = mais prioritário)."""
        return _ORDEM_MANCHESTER[self]


class TipoConsultaAPS(StrEnum):
    """Tipos de atendimento agendável na APS."""

    CONSULTA_AGENDADA = "CONSULTA_AGENDADA"
    RETORNO = "RETORNO"
    VISITA_DOMICILIAR = "VISITA_DOMICILIAR"
    TELECONSULTA = "TELECONSULTA"
    PROCEDIMENTO = "PROCEDIMENTO"


# Pesos canônicos de ordenação por prioridade Manchester (menor valor atende antes).
_ORDEM_MANCHESTER: Final[dict[PrioridadeManchester, int]] = {
    PrioridadeManchester.VERMELHO: 1,
    PrioridadeManchester.LARANJA: 2,
    PrioridadeManchester.AMARELO: 3,
    PrioridadeManchester.VERDE: 4,
    PrioridadeManchester.AZUL: 5,
}

# Formato canônico do código CIAP-2: uma letra maiúscula seguida de dois dígitos (ex.: K86).
_REGEX_CIAP2: Final[Pattern[str]] = re_compilar(r"^[A-Z]\d{2}$")

# Formato canônico do código CID-10: letra + 2 dígitos, com categoria opcional (ex.: I10, E11.9).
_REGEX_CID10: Final[Pattern[str]] = re_compilar(r"^[A-Z]\d{2}(?:\.\d{1,2})?$")

# Status que permitem transição para cancelamento, falta ou realização.
_STATUS_MUTAVEIS: Final[frozenset[str]] = frozenset(
    {StatusConsulta.AGENDADA.value, StatusConsulta.CONFIRMADA.value}
)


def _agora() -> datetime:
    """Relógio canônico do módulo (data/hora local naive, padrão do projeto)."""
    return datetime.now()


# ---------------------------------------------------------------------------
# Modelo ORM (SQLAlchemy 2.0)
# ---------------------------------------------------------------------------


class ConsultaAPS(Base):
    """Consulta agendada da Atenção Primária à Saúde.

    Cada registro representa um slot de agenda vinculado a um cidadão
    (identificado pelo CNS), a um profissional de saúde e a um estabelecimento
    (UBS/ESF), com prioridade de Manchester, codificação do problema
    (CIAP-2) e/ou diagnóstico (CID-10) e rastreio de absenteísmo (no-show).
    """

    __tablename__ = "consultas_aps"
    __table_args__ = (
        Index("ix_consultas_aps_profissional_data", "profissional_id", "data_hora"),
        Index("ix_consultas_aps_cidadao_data", "cidadao_id", "data_hora"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Identificação dos participantes da consulta (padrões SUS: CNS/CPF)
    cidadao_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cidadaos.id"), nullable=False, index=True
    )
    profissional_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("profissionais.id"), nullable=False, index=True
    )
    estabelecimento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("estabelecimentos.id"), nullable=False, index=True
    )

    # Agenda
    data_hora: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    duracao_minutos: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    # Classificação clínica e terminologias
    tipo_consulta: Mapped[str] = mapped_column(
        String(30), nullable=False, default=TipoConsultaAPS.CONSULTA_AGENDADA.value
    )
    prioridade_manchester: Mapped[str] = mapped_column(
        String(10), nullable=False, default=PrioridadeManchester.VERDE.value, index=True
    )  # VERMELHO, LARANJA, AMARELO, VERDE, AZUL
    motivo_consulta: Mapped[str] = mapped_column(String(500), nullable=False)
    ciap2: Mapped[str | None] = mapped_column(String(3), nullable=True)  # ex.: K86
    cid10: Mapped[str | None] = mapped_column(String(6), nullable=True)  # ex.: I10, E11.9

    # Ciclo de vida e absenteísmo (no-show)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=StatusConsulta.AGENDADA.value,
        index=True,
    )  # AGENDADA, CONFIRMADA, REALIZADA, FALTA, CANCELADA
    atendida_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    motivo_cancelamento: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cancelado_por: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cancelado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Auditoria
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_agora)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_agora, onupdate=_agora
    )

    # Relacionamentos (carregados antecipadamente para leitura segura após commit)
    cidadao: Mapped["Cidadao"] = relationship("Cidadao", lazy="selectin")
    profissional: Mapped["Profissional"] = relationship("Profissional", lazy="selectin")
    estabelecimento: Mapped["Estabelecimento"] = relationship(
        "Estabelecimento", lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover - representação auxiliar
        """Representação textual resumida para depuração."""
        return (
            f"<ConsultaAPS id={self.id} cidadao_id={self.cidadao_id} "
            f"profissional_id={self.profissional_id} data_hora={self.data_hora} "
            f"status={self.status!r} prioridade={self.prioridade_manchester!r}>"
        )


# ---------------------------------------------------------------------------
# Exceções de domínio
# ---------------------------------------------------------------------------


class CidadaoNaoEncontradoError(LookupError):
    """Erro levantado quando o CNS não corresponde a um cidadão cadastrado."""

    def __init__(self, cns: str) -> None:
        """Inicializa o erro com o CNS pesquisado."""
        super().__init__(f"Cidadão não encontrado para o CNS informado: {cns}.")


class ProfissionalNaoEncontradoError(LookupError):
    """Erro levantado quando o CNS não corresponde a um profissional cadastrado."""

    def __init__(self, cns: str) -> None:
        """Inicializa o erro com o CNS pesquisado."""
        super().__init__(f"Profissional não encontrado para o CNS informado: {cns}.")


class EstabelecimentoNaoEncontradoError(LookupError):
    """Erro levantado quando o estabelecimento informado não existe."""

    def __init__(self, estabelecimento_id: int) -> None:
        """Inicializa o erro com o identificador pesquisado."""
        super().__init__(
            f"Estabelecimento não encontrado para o id informado: {estabelecimento_id}."
        )


class ConsultaNaoEncontradaError(LookupError):
    """Erro levantado quando a consulta informada não existe."""

    def __init__(self, consulta_id: int) -> None:
        """Inicializa o erro com o identificador pesquisado."""
        super().__init__(f"Consulta não encontrada para o id informado: {consulta_id}.")


class ConflitoDeAgendaError(ValueError):
    """Erro levantado quando o profissional já possui consulta sobreposta.

    O agendamento é recusado quando o intervalo [início, início + duração)
    da nova consulta colide com outra consulta ativa (AGENDADA ou CONFIRMADA)
    do mesmo profissional.
    """

    def __init__(self, profissional_id: int, data_hora: datetime) -> None:
        """Inicializa o erro com o profissional e o horário em conflito."""
        super().__init__(
            "Conflito de agenda: o profissional já possui consulta sobreposta "
            f"em {data_hora.strftime('%d/%m/%Y %H:%M')}."
        )
        self.profissional_id = profissional_id
        self.data_hora = data_hora


class TransicaoDeStatusInvalidaError(ValueError):
    """Erro levantado quando o status atual não permite a operação solicitada."""

    def __init__(self, operacao: str, status_atual: str) -> None:
        """Inicializa o erro com a operação recusada e o status vigente."""
        super().__init__(
            f"Operação '{operacao}' não permitida: consulta com status '{status_atual}'."
        )


# ---------------------------------------------------------------------------
# Schemas Pydantic v2 (entrada e saída da camada de repositório)
# ---------------------------------------------------------------------------


class ConsultaAPSCreate(BaseModel):
    """Dados de entrada para o agendamento de uma consulta APS.

    A identificação do cidadão e do profissional é feita pelo CNS, conforme
    o padrão de identificação do SUS. O código CIAP-2 é a terminologia de
    referência do motivo da consulta na APS; o CID-10 é opcional.
    """

    model_config = ConfigDict(strict=True, extra="forbid")

    cidadao_cns: str = Field(..., description="CNS do cidadão (15 dígitos)")
    profissional_cns: str = Field(..., description="CNS do profissional (15 dígitos)")
    estabelecimento_id: int = Field(..., gt=0, description="Identificador da UBS/ESF")
    data_hora: datetime = Field(..., description="Data e hora futuras da consulta")
    duracao_minutos: int = Field(
        30, ge=10, le=120, description="Duração prevista da consulta em minutos"
    )
    tipo_consulta: TipoConsultaAPS = Field(
        TipoConsultaAPS.CONSULTA_AGENDADA, description="Tipo de atendimento APS"
    )
    prioridade_manchester: PrioridadeManchester = Field(
        PrioridadeManchester.VERDE,
        description="Prioridade de Manchester da consulta agendada",
    )
    motivo_consulta: str = Field(
        ..., min_length=3, max_length=500, description="Motivo/queixa da consulta"
    )
    ciap2: str | None = Field(None, description="Código CIAP-2 do problema (ex.: K86)")
    cid10: str | None = Field(None, description="Código CID-10 (ex.: I10, E11.9)")
    observacoes: str | None = Field(
        None, max_length=2000, description="Observações complementares do agendamento"
    )

    @field_validator("cidadao_cns", "profissional_cns")
    @classmethod
    def _validar_cns(cls, valor: str) -> str:
        """Valida o CNS pelo algoritmo oficial do MS e devolve os 15 dígitos limpos."""
        validador = ValidadorCNS(valor)
        try:
            validador.validar()
        except CNSInvalidoError as erro:
            raise ValueError(f"CNS inválido: {erro}") from erro
        return validador.digitos

    @field_validator("ciap2")
    @classmethod
    def _validar_ciap2(cls, valor: str | None) -> str | None:
        """Normaliza e valida o formato do código CIAP-2 (letra + 2 dígitos)."""
        if valor is None:
            return valor
        normalizado = valor.strip().upper()
        if not _REGEX_CIAP2.fullmatch(normalizado):
            raise ValueError(
                "Código CIAP-2 inválido: use o formato letra + 2 dígitos (ex.: K86)."
            )
        return normalizado

    @field_validator("cid10")
    @classmethod
    def _validar_cid10(cls, valor: str | None) -> str | None:
        """Normaliza e valida o formato do código CID-10 (ex.: I10, E11.9)."""
        if valor is None:
            return valor
        normalizado = valor.strip().upper().replace(" ", "")
        if not _REGEX_CID10.fullmatch(normalizado):
            raise ValueError(
                "Código CID-10 inválido: use o formato letra + 2 dígitos (ex.: I10)."
            )
        return normalizado

    @field_validator("data_hora")
    @classmethod
    def _validar_data_hora_futura(cls, valor: datetime) -> datetime:
        """Exige data e hora futuras e normaliza para naive local (padrão do projeto)."""
        normalizado = valor
        if normalizado.tzinfo is not None:
            normalizado = normalizado.astimezone().replace(tzinfo=None)
        if normalizado <= _agora():
            raise ValueError("A data e hora da consulta devem ser futuras.")
        return normalizado


class ConsultaCancelamentoInput(BaseModel):
    """Dados exigidos para o cancelamento de uma consulta APS."""

    model_config = ConfigDict(strict=True, extra="forbid")

    motivo_cancelamento: str = Field(
        ..., min_length=3, max_length=500, description="Motivo do cancelamento"
    )
    cancelado_por: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Identificação de quem cancelou (ex.: CNS, CPF ou matrícula)",
    )


class ConsultaAPSRead(BaseModel):
    """Representação de leitura de uma consulta APS (contrato de saída)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cidadao_id: int
    cidadao_cns: str
    cidadao_nome: str
    profissional_id: int
    profissional_nome: str
    estabelecimento_id: int
    estabelecimento_nome: str
    data_hora: datetime
    duracao_minutos: int
    tipo_consulta: str
    prioridade_manchester: str
    motivo_consulta: str
    ciap2: str | None
    cid10: str | None
    status: str
    atendida_em: datetime | None
    motivo_cancelamento: str | None
    cancelado_por: str | None
    cancelado_em: datetime | None
    observacoes: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def de_orm(cls, consulta: ConsultaAPS) -> "ConsultaAPSRead":
        """Constrói a representação de leitura a partir do objeto ORM.

        Os relacionamentos ``cidadao``, ``profissional`` e ``estabelecimento``
        devem estar carregados (o repositório utiliza ``lazy="selectin"``).
        """
        return cls(
            id=consulta.id,
            cidadao_id=consulta.cidadao_id,
            cidadao_cns=consulta.cidadao.cns or "",
            cidadao_nome=consulta.cidadao.nome_social or consulta.cidadao.nome_completo,
            profissional_id=consulta.profissional_id,
            profissional_nome=consulta.profissional.nome,
            estabelecimento_id=consulta.estabelecimento_id,
            estabelecimento_nome=consulta.estabelecimento.nome_fantasia,
            data_hora=consulta.data_hora,
            duracao_minutos=consulta.duracao_minutos,
            tipo_consulta=consulta.tipo_consulta,
            prioridade_manchester=consulta.prioridade_manchester,
            motivo_consulta=consulta.motivo_consulta,
            ciap2=consulta.ciap2,
            cid10=consulta.cid10,
            status=consulta.status,
            atendida_em=consulta.atendida_em,
            motivo_cancelamento=consulta.motivo_cancelamento,
            cancelado_por=consulta.cancelado_por,
            cancelado_em=consulta.cancelado_em,
            observacoes=consulta.observacoes,
            created_at=consulta.created_at,
            updated_at=consulta.updated_at,
        )


class AbsenteismoResumo(BaseModel):
    """Contadores de absenteísmo (no-show) por paciente.

    A taxa de absenteísmo é calculada como ``faltas / (realizadas + faltas)``,
    expressa em percentual, conforme o indicador de gestão da agenda na APS.
    """

    model_config = ConfigDict(strict=True, extra="forbid")

    cidadao_id: int
    cns: str
    nome_cidadao: str
    total_consultas: int = Field(..., ge=0, description="Total de consultas registradas")
    total_realizadas: int = Field(..., ge=0, description="Consultas realizadas")
    total_faltas: int = Field(..., ge=0, description="Absenteísmo (no-show) registrado")
    total_canceladas: int = Field(..., ge=0, description="Consultas canceladas")
    total_pendentes: int = Field(
        ..., ge=0, description="Consultas agendadas/confirmadas a cumprir"
    )
    taxa_absenteismo: float = Field(
        ..., ge=0.0, le=100.0, description="Percentual de faltas sobre consultas esperadas"
    )


# ---------------------------------------------------------------------------
# Repositório
# ---------------------------------------------------------------------------


class ConsultasRepository:
    """Repositório de consultas APS (SQLAlchemy 2.0, sessão síncrona).

    Centraliza todas as operações de persistência da agenda de consultas da
    APS: agendamento, listagens (por profissional e por dia com ordenação por
    prioridade Manchester), cancelamento com motivo, histórico longitudinal do
    cidadão por CNS e contadores de absenteísmo por paciente.
    """

    def __init__(self, session: Session) -> None:
        """Inicializa o repositório com a sessão SQLAlchemy gerenciada pela aplicação."""
        self.session = session

    # ------------------------------------------------------------------
    # Escrita: agendamento, cancelamento e registro de desfechos
    # ------------------------------------------------------------------

    def agendar(self, dados: ConsultaAPSCreate) -> ConsultaAPS:
        """Agenda uma consulta APS validando participantes, estabelecimento e agenda.

        Levanta :class:`CidadaoNaoEncontradoError`, :class:`ProfissionalNaoEncontradoError`,
        :class:`EstabelecimentoNaoEncontradoError` ou :class:`ConflitoDeAgendaError`
        quando o agendamento não pode ser realizado.
        """
        cidadao = self._obter_cidadao_por_cns(dados.cidadao_cns)
        profissional = self._obter_profissional_por_cns(dados.profissional_cns)
        if self.session.get(Estabelecimento, dados.estabelecimento_id) is None:
            raise EstabelecimentoNaoEncontradoError(dados.estabelecimento_id)
        self._garantir_disponibilidade(
            profissional_id=profissional.id,
            data_hora=dados.data_hora,
            duracao_minutos=dados.duracao_minutos,
        )

        consulta = ConsultaAPS(
            cidadao_id=cidadao.id,
            profissional_id=profissional.id,
            estabelecimento_id=dados.estabelecimento_id,
            data_hora=dados.data_hora,
            duracao_minutos=dados.duracao_minutos,
            tipo_consulta=dados.tipo_consulta.value,
            prioridade_manchester=dados.prioridade_manchester.value,
            motivo_consulta=dados.motivo_consulta,
            ciap2=dados.ciap2,
            cid10=dados.cid10,
            observacoes=dados.observacoes,
            status=StatusConsulta.AGENDADA.value,
        )
        self.session.add(consulta)
        self.session.commit()
        self.session.refresh(consulta)
        return consulta

    def cancelar(self, consulta_id: int, dados: ConsultaCancelamentoInput) -> ConsultaAPS:
        """Cancela a consulta com motivo e registro de auditoria.

        Só é permitido cancelar consultas nos status ``AGENDADA`` ou
        ``CONFIRMADA``; caso contrário, levanta
        :class:`TransicaoDeStatusInvalidaError`.
        """
        consulta = self._obter_ou_lancar(consulta_id)
        self._garantir_status_mutavel(consulta, "cancelamento")
        consulta.status = StatusConsulta.CANCELADA.value
        consulta.motivo_cancelamento = dados.motivo_cancelamento
        consulta.cancelado_por = dados.cancelado_por
        consulta.cancelado_em = _agora()
        self.session.commit()
        self.session.refresh(consulta)
        return consulta

    def registrar_atendimento(self, consulta_id: int) -> ConsultaAPS:
        """Registra a realização da consulta (desfecho positivo da agenda)."""
        consulta = self._obter_ou_lancar(consulta_id)
        self._garantir_status_mutavel(consulta, "registro de atendimento")
        consulta.status = StatusConsulta.REALIZADA.value
        consulta.atendida_em = _agora()
        self.session.commit()
        self.session.refresh(consulta)
        return consulta

    def registrar_falta(self, consulta_id: int) -> ConsultaAPS:
        """Registra o absenteísmo (no-show) do cidadão na consulta agendada."""
        consulta = self._obter_ou_lancar(consulta_id)
        self._garantir_status_mutavel(consulta, "registro de falta")
        consulta.status = StatusConsulta.FALTA.value
        self.session.commit()
        self.session.refresh(consulta)
        return consulta

    # ------------------------------------------------------------------
    # Leitura: agendas e listagens
    # ------------------------------------------------------------------

    def listar_por_profissional(
        self,
        profissional_id: int,
        *,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        incluir_canceladas: bool = False,
        ordenar_por_prioridade: bool = False,
    ) -> Sequence[ConsultaAPS]:
        """Lista a agenda de um profissional.

        Por padrão, ordena cronologicamente (dia a dia de trabalho). Com
        ``ordenar_por_prioridade=True``, aplica a precedência clínica de
        Manchester (Vermelho → Laranja → Amarelo → Verde → Azul) e, dentro da
        mesma prioridade, ordena por horário. Filtros opcionais por intervalo
        de datas (ambos inclusivos) e inclusão de consultas canceladas (por
        padrão excluídas da agenda).
        """
        filtros: list[ColumnElement[bool]] = [
            ConsultaAPS.profissional_id == profissional_id,
        ]
        if not incluir_canceladas:
            filtros.append(ConsultaAPS.status != StatusConsulta.CANCELADA.value)
        if data_inicio is not None:
            filtros.append(
                ConsultaAPS.data_hora >= datetime.combine(data_inicio, datetime.min.time())
            )
        if data_fim is not None:
            filtros.append(ConsultaAPS.data_hora < data_fim + timedelta(days=1))

        prioridade = self._expressao_ordem_manchester()
        declaracao = (
            select(ConsultaAPS)
            .where(*filtros)
            .order_by(
                *(prioridade, ConsultaAPS.data_hora.asc(), ConsultaAPS.id.asc())
                if ordenar_por_prioridade
                else (ConsultaAPS.data_hora.asc(), ConsultaAPS.id.asc())
            )
        )
        return self.session.scalars(declaracao).all()

    def listar_por_dia(
        self,
        data: date,
        *,
        estabelecimento_id: int | None = None,
        profissional_id: int | None = None,
        incluir_canceladas: bool = False,
    ) -> Sequence[ConsultaAPS]:
        """Lista a agenda do dia com ordenação por prioridade de Manchester.

        A ordenação prioriza clinicamente as consultas (Vermelho → Laranja →
        Amarelo → Verde → Azul) e, dentro da mesma prioridade, ordena por
        horário. Opcionalmente restringe a um estabelecimento (UBS/ESF) e/ou a
        um profissional.
        """
        inicio_dia = datetime.combine(data, datetime.min.time())
        fim_dia = inicio_dia + timedelta(days=1)
        filtros: list[ColumnElement[bool]] = [
            ConsultaAPS.data_hora >= inicio_dia,
            ConsultaAPS.data_hora < fim_dia,
        ]
        if not incluir_canceladas:
            filtros.append(ConsultaAPS.status != StatusConsulta.CANCELADA.value)
        if estabelecimento_id is not None:
            filtros.append(ConsultaAPS.estabelecimento_id == estabelecimento_id)
        if profissional_id is not None:
            filtros.append(ConsultaAPS.profissional_id == profissional_id)

        declaracao = (
            select(ConsultaAPS)
            .where(*filtros)
            .order_by(
                self._expressao_ordem_manchester(),
                ConsultaAPS.data_hora.asc(),
                ConsultaAPS.id.asc(),
            )
        )
        return self.session.scalars(declaracao).all()

    def historico_por_cns(self, cns: str, *, limite: int = 200) -> Sequence[ConsultaAPS]:
        """Retorna o histórico longitudinal do cidadão identificado pelo CNS.

        Inclui consultas realizadas, faltas (no-show) e cancelamentos, em ordem
        cronológica decrescente (mais recentes primeiro), permitindo a análise
        da linha de vida do cidadão na APS. Levanta :class:`CNSInvalidoError`
        para CNS malformado e :class:`CidadaoNaoEncontradoError` para CNS não
        cadastrado.
        """
        cidadao = self._obter_cidadao_por_cns(cns)
        declaracao = (
            select(ConsultaAPS)
            .where(ConsultaAPS.cidadao_id == cidadao.id)
            .order_by(ConsultaAPS.data_hora.desc(), ConsultaAPS.id.desc())
            .limit(limite)
        )
        return self.session.scalars(declaracao).all()

    def contadores_absenteismo_por_cns(self, cns: str) -> AbsenteismoResumo:
        """Calcula os contadores de absenteísmo (no-show) do paciente pelo CNS.

        Considera como denominador do indicador as consultas esperadas
        (realizadas + faltas); consultas canceladas e pendentes não compõem a
        taxa, mas são reportadas nos totais. Levanta :class:`CNSInvalidoError`
        para CNS malformado e :class:`CidadaoNaoEncontradoError` para CNS não
        cadastrado.
        """
        cidadao = self._obter_cidadao_por_cns(cns)
        declaracao = (
            select(ConsultaAPS.status, func.count())
            .where(ConsultaAPS.cidadao_id == cidadao.id)
            .group_by(ConsultaAPS.status)
        )
        contagens: dict[str, int] = {
            status: quantidade
            for status, quantidade in self.session.execute(declaracao).all()
        }

        total_realizadas = contagens.get(StatusConsulta.REALIZADA.value, 0)
        total_faltas = contagens.get(StatusConsulta.FALTA.value, 0)
        total_canceladas = contagens.get(StatusConsulta.CANCELADA.value, 0)
        total_pendentes = contagens.get(StatusConsulta.AGENDADA.value, 0) + contagens.get(
            StatusConsulta.CONFIRMADA.value, 0
        )
        esperadas = total_realizadas + total_faltas
        taxa = round(total_faltas / esperadas * 100, 2) if esperadas > 0 else 0.0

        return AbsenteismoResumo(
            cidadao_id=cidadao.id,
            cns=cidadao.cns or self._normalizar_cns(cns),
            nome_cidadao=cidadao.nome_social or cidadao.nome_completo,
            total_consultas=sum(contagens.values()),
            total_realizadas=total_realizadas,
            total_faltas=total_faltas,
            total_canceladas=total_canceladas,
            total_pendentes=total_pendentes,
            taxa_absenteismo=taxa,
        )

    def obter_por_id(self, consulta_id: int) -> ConsultaAPS | None:
        """Recupera a consulta pelo identificador, ou ``None`` se inexistente."""
        return self.session.get(ConsultaAPS, consulta_id)

    # ------------------------------------------------------------------
    # Métodos internos de apoio
    # ------------------------------------------------------------------

    def _obter_ou_lancar(self, consulta_id: int) -> ConsultaAPS:
        """Recupera a consulta ou levanta :class:`ConsultaNaoEncontradaError`."""
        consulta = self.obter_por_id(consulta_id)
        if consulta is None:
            raise ConsultaNaoEncontradaError(consulta_id)
        return consulta

    def _obter_cidadao_por_cns(self, cns: str) -> Cidadao:
        """Localiza o cidadão pelo CNS validado (15 dígitos limpos)."""
        cns_limpo = self._normalizar_cns(cns)
        cidadao = self.session.scalars(
            select(Cidadao).where(Cidadao.cns == cns_limpo)
        ).first()
        if cidadao is None:
            raise CidadaoNaoEncontradoError(cns_limpo)
        return cidadao

    def _obter_profissional_por_cns(self, cns: str) -> Profissional:
        """Localiza o profissional pelo CNS validado (15 dígitos limpos)."""
        cns_limpo = self._normalizar_cns(cns)
        profissional = self.session.scalars(
            select(Profissional).where(Profissional.cns == cns_limpo)
        ).first()
        if profissional is None:
            raise ProfissionalNaoEncontradoError(cns_limpo)
        return profissional

    def _garantir_disponibilidade(
        self, *, profissional_id: int, data_hora: datetime, duracao_minutos: int
    ) -> None:
        """Garante que não há sobreposição de consultas ativas do profissional.

        Verifica, dentro do mesmo dia, se o intervalo [início, início + duração)
        da nova consulta colide com alguma consulta nos status ``AGENDADA`` ou
        ``CONFIRMADA``. O teste de sobreposição é
        ``inicio_existente < fim_nova and fim_existente > inicio_nova``.
        """
        inicio_janela = data_hora.replace(hour=0, minute=0, second=0, microsecond=0)
        fim_janela = inicio_janela + timedelta(days=1)
        declaracao = select(ConsultaAPS).where(
            ConsultaAPS.profissional_id == profissional_id,
            ConsultaAPS.status.in_(_STATUS_MUTAVEIS),
            ConsultaAPS.data_hora >= inicio_janela,
            ConsultaAPS.data_hora < fim_janela,
        )
        fim_nova = data_hora + timedelta(minutes=duracao_minutos)
        for existente in self.session.scalars(declaracao):
            inicio_existente = existente.data_hora
            fim_existente = inicio_existente + timedelta(
                minutes=existente.duracao_minutos
            )
            if inicio_existente < fim_nova and fim_existente > data_hora:
                raise ConflitoDeAgendaError(profissional_id, data_hora)

    def _garantir_status_mutavel(self, consulta: ConsultaAPS, operacao: str) -> None:
        """Valida se o status atual permite cancelamento, falta ou realização."""
        if consulta.status not in _STATUS_MUTAVEIS:
            raise TransicaoDeStatusInvalidaError(operacao, consulta.status)

    @staticmethod
    def _normalizar_cns(cns: str) -> str:
        """Valida o CNS pelo algoritmo oficial do MS e devolve os 15 dígitos limpos."""
        validador = ValidadorCNS(cns)
        validador.validar()
        return validador.digitos

    @staticmethod
    def _expressao_ordem_manchester() -> ColumnElement[int]:
        """Constrói a expressão SQL de ordenação pela prioridade de Manchester.

        Mapeia cada cor para um peso canônico (Vermelho = 1 ... Azul = 5),
        garantindo a precedência clínica na agenda do dia; valores não
        reconhecidos são posicionados ao final da fila.
        """
        whens: list[tuple[ColumnElement[bool], int]] = [
            (ConsultaAPS.prioridade_manchester == prioridade.value, peso)
            for prioridade, peso in _ORDEM_MANCHESTER.items()
        ]
        return case(
            *whens,
            else_=_ORDEM_MANCHESTER[PrioridadeManchester.AZUL] + 1,
        )