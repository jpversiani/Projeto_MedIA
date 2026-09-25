"""Acompanhamento Pré-Natal (Protocolo SisPreNatal) — Projeto MedIA (SUS/APS).

Serviço de apoio ao acompanhamento pré-natal na Atenção Primária à Saúde
(APS/SUS), conforme o protocolo SisPreNatal do Ministério da Saúde:

1. **Número mínimo de consultas por idade gestacional (IG)** — tabela de
   adequação do acompanhamento: janela oportuna de cada consulta em dias
   de gestação (1ª até 120; 2ª entre 140 e 180; 3ª entre 180 e 200; 4ª
   entre 200 e 210; 5ª entre 230 e 240; 6ª entre 250 e 260 dias) e o
   mínimo de consultas esperado para a IG avaliada.
2. **Exames obrigatórios por trimestre** — HIV, sífilis (VDRL), urina
   tipo I, glicemia de jejum e tipagem sanguínea (ABO/Rh): coleta completa
   no 1º trimestre (1ª consulta), glicemia no 2º trimestre (sobrecarga/
   TTG 75 g entre 24 e 28 semanas quando indicado) e repetição de HIV,
   sífilis, urina tipo I e glicemia no 3º trimestre.
3. **Alertas de IG avançada sem consulta** — gestação avançada (IG ≥ 36
   semanas) sem consulta registrada na janela oportuna (semanal a partir
   de 36 semanas), com gravidade informativo/atenção/crítico.
4. **Cálculo de DPP pela regra de Naegele** — DPP = DUM − 3 meses +
   7 dias (+ 1 ano), com IG atual (semanas e dias), trimestre gestacional
   e janela de parto (37–42 semanas).

Padrões do SUS/APS: CID-10, CIAP-2, método SOAP (Subjetivo, Avaliação,
Plano) e identificação por CNS/CPF. Todas as mensagens em Português do
Brasil.

Referências:

    - Ministério da Saúde. Manual de Pré-Natal e Puerpério: Atenção
      Qualificada e Humanizada. Brasília: MS, 2020 (Cadernos de Atenção
      Básica nº 32).
    - Ministério da Saúde. SisPreNatal — Sistema de Acompanhamento do
      Pré-Natal e do Nascimento: critérios de avaliação da qualidade do
      pré-natal (número mínimo de consultas por período gestacional).
    - Naegele FR. Regra de Naegele para o cálculo da data provável do
      parto: DPP = DUM − 3 meses + 7 dias (+ 1 ano).
    - CID-10 (OMS/DATASUS); CIAP-2 (WONCA); método SOAP (Subjetivo,
      Avaliação, Planejamento).

Limitações: serviço de apoio à decisão — não substitui o protocolo do
serviço nem o julgamento clínico do profissional. A DPP pela regra de
Naegele pressupõe ciclo menstrual regular de 28 dias e DUM conhecida; a
IG calculada por DUM deve ser refinada com ultrassonografia do 1º
trimestre; exames laboratoriais são guias de coleta oportuna.
"""

from __future__ import annotations

import re
import unicodedata
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from enum import StrEnum
from typing import Final, Sequence, TypeAlias

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

# ---------------------------------------------------------------------------
# Integração com a identificação SUS (CNS) — degradação graciosa fora do pacote
# ---------------------------------------------------------------------------

try:  # pragma: no cover - depende do ambiente de execução
    from .validacao_cns import CNS

    VALIDACAO_CNS_DISPONIVEL: Final[bool] = True
except ImportError:  # pragma: no cover - execução fora do pacote (script direto)
    CNS: TypeAlias = str  # type: ignore[no-redef]
    VALIDACAO_CNS_DISPONIVEL = False


class PreNatalInvalidoError(ValueError):
    """Erro lançado quando os dados do pré-natal são inválidos."""


# ---------------------------------------------------------------------------
# Enumerações clínicas
# ---------------------------------------------------------------------------


class TrimestreGestacional(StrEnum):
    """Trimestre gestacional conforme o protocolo do pré-natal (MS)."""

    PRIMEIRO = "primeiro"
    SEGUNDO = "segundo"
    TERCEIRO = "terceiro"

    @property
    def rotulo(self) -> str:
        """Rótulo do trimestre (ex.: "1º trimestre")."""
        return _ROTULOS_TRIMESTRE[str(self)]


#: Rótulos dos trimestres gestacionais (por valor do enum).
_ROTULOS_TRIMESTRE: Final[dict[str, str]] = {
    "primeiro": "1º trimestre",
    "segundo": "2º trimestre",
    "terceiro": "3º trimestre",
}


class GravidadeAlerta(StrEnum):
    """Níveis de gravidade dos alertas do acompanhamento pré-natal."""

    INFORMATIVO = "informativo"
    ATENCAO = "atencao"
    CRITICO = "critico"

    @property
    def rotulo(self) -> str:
        """Rótulo de gravidade (ex.: "crítico")."""
        return _ROTULOS_GRAVIDADE[str(self)]


#: Rótulos de gravidade dos alertas (por valor do enum).
_ROTULOS_GRAVIDADE: Final[dict[str, str]] = {
    "informativo": "informativo",
    "atencao": "atenção",
    "critico": "crítico",
}


class ExamePreNatal(StrEnum):
    """Exames laboratoriais obrigatórios do pré-natal (SisPreNatal/MS)."""

    HIV = "hiv"
    SIFILIS = "sifilis"  # VDRL (sífilis)
    URINA_TIPO_I = "urina_tipo_i"
    GLICEMIA = "glicemia"
    TIPAGEM_SANGUINEA = "tipagem_sanguinea"

    @property
    def rotulo(self) -> str:
        """Rótulo clínico do exame (ex.: "Sífilis (VDRL)")."""
        return _ROTULOS_EXAME[str(self)]


#: Rótulos clínicos dos exames obrigatórios (por valor do enum).
_ROTULOS_EXAME: Final[dict[str, str]] = {
    "hiv": "HIV",
    "sifilis": "Sífilis (VDRL)",
    "urina_tipo_i": "Urina tipo I",
    "glicemia": "Glicemia de jejum",
    "tipagem_sanguinea": "Tipagem sanguínea (ABO/Rh)",
}


# ---------------------------------------------------------------------------
# Constantes do protocolo SisPreNatal (janelas de consulta e exames)
# ---------------------------------------------------------------------------

#: Limite máximo de IG calculável (42 semanas — 294 dias).
IG_MAXIMA_DIAS: Final[int] = 294

#: Janela oportuna da 1ª consulta (até 120 dias de gestação).
JANELA_PRIMEIRA_CONSULTA_DIAS: Final[int] = 120

#: Janela oportuna de cada consulta pré-natal, em dias de gestação
#: (SisPreNatal/MS): 1ª até 120; 2ª entre 140 e 180; 3ª entre 180 e 200;
#: 4ª entre 200 e 210; 5ª entre 230 e 240; 6ª entre 250 e 260 dias.
JANELAS_CONSULTA: Final[tuple[tuple[int, int], ...]] = (
    (0, 120),
    (140, 180),
    (180, 200),
    (200, 210),
    (230, 240),
    (250, 260),
)

#: Mínimo de consultas por IG, em dias de gestação (limite, mínimo):
#: IG ≤ 120 dias → 1 consulta; IG ≤ 180 → 2; IG ≤ 200 → 3; IG ≤ 210 → 4;
#: IG ≤ 240 → 5; IG acima de 240 dias → 6 (mínimo do protocolo SisPreNatal).
MINIMO_CONSULTAS_POR_IG_DIAS: Final[tuple[tuple[int, int], ...]] = (
    (120, 1),
    (180, 2),
    (200, 3),
    (210, 4),
    (240, 5),
    (261, 6),
)

#: Exames obrigatórios por trimestre (SisPreNatal/MS): coleta completa
#: no 1º trimestre (1ª consulta); glicemia no 2º trimestre (sobrecarga/
#: TTG 75 g entre 24 e 28 semanas quando indicado); repetição de HIV,
#: sífilis (VDRL), urina tipo I e glicemia no 3º trimestre.
EXAMES_OBRIGATORIOS_POR_TRIMESTRE: Final[
    dict[TrimestreGestacional, frozenset[ExamePreNatal]]
] = {
    TrimestreGestacional.PRIMEIRO: frozenset(ExamePreNatal),
    TrimestreGestacional.SEGUNDO: frozenset({ExamePreNatal.GLICEMIA}),
    TrimestreGestacional.TERCEIRO: frozenset(
        {
            ExamePreNatal.HIV,
            ExamePreNatal.SIFILIS,
            ExamePreNatal.URINA_TIPO_I,
            ExamePreNatal.GLICEMIA,
        }
    ),
}

#: IG (em dias) a partir da qual o acompanhamento é semanal (MS).
IG_SEMANAL_DIAS: Final[int] = 252  # 36 semanas

#: Intervalo recomendado entre consultas (dias) a partir de 36 semanas.
INTERVALO_SEMANAL_DIAS: Final[int] = 7

#: IG (em semanas) de janela de parto (termo: 37–42 semanas).
IG_JANELA_PARTO_SEMANAS: Final[tuple[int, int]] = (37, 42)

#: IG (em semanas) de termo tardio/pós-termo (alertas do acompanhamento).
IG_TERMO_TARDIO_SEMANAS: Final[int] = 41
IG_POS_TERMO_SEMANAS: Final[int] = 42

#: Limiar de glicemia de jejum (mg/dL) da 1ª consulta (MS) — sobrecarga
#: (TTG 75 g) entre 24 e 28 semanas quando indicado.
GLICEMIA_JEJUM_LIMIAR_MG_DL: Final[int] = 92

#: Intervalo (dias) que caracteriza atraso do acompanhamento semanal
#: (gera alerta de atenção quando a última consulta é mais antiga).
INTERVALO_ATENCAO_DIAS: Final[int] = 15

#: IG (em dias) de termo tardio (41 semanas) e pós-termo (42 semanas).
IG_TERMO_TARDIO_DIAS: Final[int] = 287
IG_POS_TERMO_DIAS: Final[int] = 294

#: CID-10 e CIAP-2 de referência do acompanhamento pré-natal (MS).
CID10_PRE_NATAL: Final[str] = "Z34.0"
CIAP2_PRE_NATAL: Final[str] = "W17"  # Gravidez: vigilância de saúde

#: Número de semanas do intervalo de parto (Naegele: IG 40 semanas no DPP).
IG_NO_DPP_SEMANAS: Final[int] = 40

#: Mínimo de consultas por trimestre gestacional (SisPreNatal/MS).
_MINIMO_CONSULTAS_POR_TRIMESTRE: Final[dict[TrimestreGestacional, int]] = {
    TrimestreGestacional.PRIMEIRO: 1,
    TrimestreGestacional.SEGUNDO: 3,
    TrimestreGestacional.TERCEIRO: 6,
}

#: Mínimo de consultas por trimestre (para os alertas de IG avançada).
_MINIMO_CONSULTAS_POR_IG_DIAS: Final[dict[TrimestreGestacional, int]] = {
    TrimestreGestacional.PRIMEIRO: 1,
    TrimestreGestacional.SEGUNDO: 3,
    TrimestreGestacional.TERCEIRO: 6,
}


# ---------------------------------------------------------------------------
# Schemas Pydantic v2 — entrada e resultados (tipagem estrita)
# ---------------------------------------------------------------------------


class EntradaPreNatal(BaseModel):
    """Dados de entrada do acompanhamento pré-natal (SisPreNatal/MS).

    Attributes:
        cns: CNS do cidadão (identificação SUS, opcional; validado pelo
            módulo ``validacao_cns`` quando disponível no pacote).
        cpf: CPF do cidadão (opcional; normalizado para 11 dígitos).
        dum: Data da última menstruação (DUM) — base da IG e da DPP.
        data_referencia: Data de avaliação do acompanhamento (padrão: hoje).
        consultas_realizadas: Número de consultas pré-natais registradas.
        data_ultima_consulta: Data da última consulta pré-natal registrada.
        exames_realizados: Exames com resultado laboratorial registrado.
        ig_semanas_informada: IG informada (semanas) por US, quando disponível
            (refina a IG calculada pela DUM).
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    cns: CNS | None = None
    cpf: str | None = None
    dum: date
    data_referencia: date | None = None
    consultas_realizadas: int = Field(default=0, ge=0)
    data_ultima_consulta: date | None = None
    exames_realizados: Sequence[ExamePreNatal] = ()
    ig_semanas_informada: int | None = Field(default=None, ge=0, le=42)

    @field_validator("cpf")
    @classmethod
    def _normalizar_cpf(cls, valor: str | None) -> str | None:
        """Normaliza o CPF para 11 dígitos numéricos (sem DV check aqui)."""
        if valor is None:
            return None
        digitos = re.sub(r"\D", "", valor)
        if len(digitos) != 11:
            raise ValueError("O CPF deve conter exatamente 11 dígitos numéricos.")
        return digitos

    @field_validator("data_referencia", mode="before")
    @classmethod
    def _definir_data_referencia(cls, valor: object) -> object:
        """Define a data de avaliação como hoje quando não informada."""
        if valor is None:
            return date.today()
        return valor


class ConsultaAvaliada(BaseModel):
    """Avaliação de uma consulta pré-natal pela janela oportuna (MS).

    Attributes:
        numero: Número ordinal da consulta (1ª a 6ª).
        janela_inicio_dias: Início da janela oportuna (dias de gestação).
        janela_fim_dias: Fim da janela oportuna (dias de gestação).
        ig_ideal_dias: IG ideal da consulta (centro da janela, em dias).
        realizada: ``True`` quando a consulta está registrada.
        oportuna: ``True`` quando a consulta foi registrada dentro da janela.
        data_ideal: Data ideal da consulta (DUM + IG ideal da janela).
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    numero: int = Field(ge=1, le=6)
    janela_inicio_dias: int = Field(ge=0, le=294)
    janela_fim_dias: int = Field(ge=0, le=294)
    ig_ideal_dias: int = Field(ge=0, le=294)
    realizada: bool
    oportuna: bool = False
    data_ideal: date


class ResultadoDPP(BaseModel):
    """Resultado do cálculo de DPP pela regra de Naegele e IG atual.

    Attributes:
        dum: Data da última menstruação (DUM).
        data_referencia: Data de avaliação do acompanhamento.
        dpp: Data provável do parto (Naegele: DUM − 3 meses + 7 dias + 1 ano).
        ig_dias: IG atual em dias (DUM → data de avaliação).
        ig_semanas: IG atual em semanas completas.
        ig_dias_restantes: Dias restantes para completar a semana atual.
        trimestre: Trimestre gestacional da IG atual.
        semanas_ate_dpp: Semanas restantes até a DPP (pode ser negativa).
        janela_parto_inicio: Início da janela de parto (37 semanas).
        janela_parto_fim: Fim da janela de parto (42 semanas).
        observacoes: Ressalvas clínicas do cálculo.
        resumo_soap: Linha pronta para o campo "S" do SOAP.
        calculado_em: Data/hora (UTC) do cálculo.
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    dum: date
    data_referencia: date
    dpp: date
    ig_dias: int = Field(ge=0, le=294)
    ig_semanas: int = Field(ge=0, le=42)
    ig_dias_restantes: int = Field(ge=0, le=6)
    trimestre: TrimestreGestacional
    semanas_ate_dpp: int
    janela_parto_inicio: date
    janela_parto_fim: date
    observacoes: tuple[str, ...] = ()
    resumo_soap: str
    calculado_em: datetime


class AvaliacaoTrimestre(BaseModel):
    """Avaliação dos exames obrigatórios de um trimestre gestacional.

    Attributes:
        trimestre: Trimestre gestacional avaliado.
        exames_obrigatorios: Exames obrigatórios do trimestre.
        exames_realizados: Exames com resultado registrado.
        exames_pendentes: Exames obrigatórios ainda pendentes.
        adequado: ``True`` quando não há exames pendentes.
        observacao: Ressalva da avaliação (ex.: exames pendentes).
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    trimestre: TrimestreGestacional
    exames_obrigatorios: tuple[ExamePreNatal, ...] = ()
    exames_realizados: tuple[ExamePreNatal, ...] = ()
    exames_pendentes: tuple[ExamePreNatal, ...] = ()
    adequado: bool
    observacao: str | None = None


class AlertaPreNatal(BaseModel):
    """Alerta do acompanhamento pré-natal (IG avançada sem consulta).

    Attributes:
        gravidade: Gravidade do alerta (informativo/atenção/crítico).
        mensagem: Mensagem clínica em Português do Brasil.
        ig_semanas: IG avaliada (semanas), quando aplicável.
        dias_ultima_consulta: Dias desde a última consulta, quando aplicável.
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    gravidade: GravidadeAlerta
    mensagem: str
    ig_semanas: int | None = None
    dias_ultima_consulta: int | None = None


class ResultadoPreNatal(BaseModel):
    """Resultado consolidado do acompanhamento pré-natal (SisPreNatal/MS).

    Attributes:
        cns: CNS informado na entrada (rastreabilidade do cidadão).
        cpf: CPF informado na entrada (rastreabilidade do cidadão).
        dpp: Resultado do cálculo de DPP pela regra de Naegele.
        consultas: Avaliação de cada consulta pela janela oportuna (MS).
        trimestres: Avaliação dos exames obrigatórios por trimestre.
        alertas: Alertas de IG avançada sem consulta.
        minimo_consultas: Mínimo de consultas esperado para a IG avaliada.
        acompanhamento_adequado: ``True`` quando o acompanhamento é adequado.
        plano: Plano (P do SOAP) sugerido para a APS.
        resumo_soap: Linha pronta para o registro SOAP do prontuário.
        avaliado_em: Data/hora (UTC) da avaliação.
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    cns: str | None = None
    cpf: str | None = None
    dpp: ResultadoDPP
    consultas: tuple[ConsultaAvaliada, ...] = ()
    trimestres: tuple[AvaliacaoTrimestre, ...] = ()
    alertas: tuple[AlertaPreNatal, ...] = ()
    minimo_consultas: int = Field(ge=1, le=6)
    acompanhamento_adequado: bool
    plano: str
    resumo_soap: str
    avaliado_em: datetime


# ---------------------------------------------------------------------------
# Serviço principal — Acompanhamento Pré-Natal (SisPreNatal/MS)
# ---------------------------------------------------------------------------


class PreNatalService:
    """Acompanhamento pré-natal pelo protocolo SisPreNatal (MS).

    Implementa o número mínimo de consultas por IG (tabela SisPreNatal),
    os exames obrigatórios por trimestre (HIV, sífilis/VDRL, urina tipo I,
    glicemia de jejum e tipagem sanguínea ABO/Rh), alertas de IG avançada
    sem consulta e o cálculo da DPP pela regra de Naegele, com resumo pronto
    para o registro SOAP do prontuário e códigos CID-10/CIAP-2.

    Exemplos de uso::

        >>> servico = PreNatalService()
        >>> entrada = EntradaPreNatal(dum=date(2024, 10, 10))
        >>> resultado = servico.avaliar(entrada)
        >>> resultado.dpp.dpp.isoformat()
        '2025-07-17'
    """

    # ------------------------------------------------------------------ #
    # Cálculo de DPP pela regra de Naegele e IG atual                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def calcular_dpp_naegele(dum: date) -> date:
        """Calcula a DPP pela regra de Naegele: DUM − 3 meses + 7 dias (+ 1 ano).

        Args:
            dum: Data da última menstruação (DUM).

        Returns:
            Data provável do parto (DPP) pela regra de Naegele.

        Raises:
            PreNatalInvalidoError: Se a DUM é futura (IG negativa).
        """
        mes_dpp = dum.month - 3
        if mes_dpp <= 0:
            mes_dpp += 12
            ano_dpp = dum.year
        else:
            ano_dpp = dum.year + 1
        ultimo_dia = monthrange(ano_dpp, mes_dpp)[1]
        dia_dpp = min(dum.day, ultimo_dia)
        dpp = date(ano_dpp, mes_dpp, dia_dpp) + timedelta(days=7)
        return dpp

    @staticmethod
    def classificar_ig(ig_dias: int) -> tuple[int, TrimestreGestacional]:
        """Classifica a IG (em dias) em semanas e trimestre gestacional.

        Args:
            ig_dias: Idade gestacional em dias (0 a 294).

        Returns:
            Tupla (semanas completas, trimestre gestacional).

        Raises:
            PreNatalInvalidoError: Se a IG está fora de 0 a 294 dias.
        """
        if not isinstance(ig_dias, int) or isinstance(ig_dias, bool) or not 0 <= ig_dias <= IG_MAXIMA_DIAS:
            raise PreNatalInvalidoError(
                f"IG inválida: {ig_dias!r} (esperado número de dias entre 0 e {IG_MAXIMA_DIAS})."
            )
        semanas = ig_dias // 7
        if ig_dias <= 91:
            trimestre = TrimestreGestacional.PRIMEIRO
        elif ig_dias <= 189:
            trimestre = TrimestreGestacional.SEGUNDO
        else:
            trimestre = TrimestreGestacional.TERCEIRO
        return semanas, trimestre

    # ------------------------------------------------------------------ #
    # Número mínimo de consultas por IG (tabela SisPreNatal)              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def minimo_consultas_para_ig(ig_dias: int) -> int:
        """Mínimo de consultas pré-natais esperado para a IG (dias).

        Tabela de adequação (SisPreNatal/MS): IG ≤ 120 dias → 1 consulta;
        IG ≤ 180 → 2; IG ≤ 200 → 3; IG ≤ 210 → 4; IG ≤ 240 → 5; IG acima
        de 240 dias → 6 (mínimo do protocolo).

        Args:
            ig_dias: Idade gestacional em dias (0 a 294).

        Returns:
            Número mínimo de consultas esperado para a IG.

        Raises:
            PreNatalInvalidoError: Se a IG está fora de 0 a 294 dias.
        """
        _, trimestre = PreNatalService.classificar_ig(ig_dias)
        return _MINIMO_CONSULTAS_POR_TRIMESTRE[trimestre]

    # ------------------------------------------------------------------ #
    # Exames obrigatórios por trimestre (SisPreNatal/MS)                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def exames_obrigatorios_para_trimestre(trimestre: TrimestreGestacional) -> frozenset[ExamePreNatal]:
        """Exames obrigatórios do trimestre gestacional (SisPreNatal/MS).

        Args:
            trimestre: Trimestre gestacional avaliado.

        Returns:
            Exames obrigatórios do trimestre.
        """
        return EXAMES_OBRIGATORIOS_POR_TRIMESTRE[trimestre]

    @staticmethod
    def avaliar_exames_trimestre(
        trimestre: TrimestreGestacional,
        exames_realizados: Sequence[ExamePreNatal],
    ) -> AvaliacaoTrimestre:
        """Avalia os exames obrigatórios do trimestre gestacional.

        Args:
            trimestre: Trimestre gestacional avaliado.
            exames_realizados: Exames com resultado laboratorial registrado.

        Returns:
            Avaliação do trimestre com exames obrigatórios, realizados e
            pendentes, e ressalva quando houver pendências.
        """
        obrigatorios = EXAMES_OBRIGATORIOS_POR_TRIMESTRE[trimestre]
        realizados = frozenset(exames_realizados)
        pendentes = tuple(sorted(obrigatorios - realizados, key=str))
        adequado = not pendentes
        observacao: str | None = None
        if pendentes:
            rotulos = ", ".join(exame.rotulo for exame in pendentes)
            observacao = f"Exames pendentes no {trimestre.rotulo}: {rotulos}."
        return AvaliacaoTrimestre(
            trimestre=trimestre,
            exames_obrigatorios=tuple(sorted(obrigatorios, key=str)),
            exames_realizados=tuple(sorted(realizados, key=str)),
            exames_pendentes=pendentes,
            adequado=adequado,
            observacao=observacao,
        )

    # ------------------------------------------------------------------ #
    # Alertas de IG avançada sem consulta                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def avaliar_alertas(
        ig_dias: int,
        consultas_realizadas: int,
        data_ultima_consulta: date | None,
        data_referencia: date,
    ) -> tuple[AlertaPreNatal, ...]:
        """Gera alertas de IG avançada sem consulta (SisPreNatal/MS).

        Regras: IG ≥ 36 semanas com consultas abaixo do mínimo esperado
        gera alerta crítico; IG ≥ 36 semanas com a última consulta há 15
        dias ou mais gera alerta de atenção (janela semanal a partir de
        36 semanas); IG ≥ 41 semanas gera alerta de avaliação do parto
        (termo tardio); IG ≥ 42 semanas gera alerta crítico (pós-termo).

        Args:
            ig_dias: Idade gestacional em dias (0 a 294).
            consultas_realizadas: Número de consultas pré-natais registradas.
            data_ultima_consulta: Data da última consulta (opcional).
            data_referencia: Data de avaliação do acompanhamento.

        Returns:
            Alertas gerados (vazia quando não houver).

        Raises:
            PreNatalInvalidoError: Se a IG está fora de 0 a 294 dias.
        """
        _, trimestre = PreNatalService.classificar_ig(ig_dias)
        alertas: list[AlertaPreNatal] = []

        if ig_dias >= IG_SEMANAL_DIAS:
            minimo = _MINIMO_CONSULTAS_POR_IG_DIAS[trimestre]
            if consultas_realizadas < minimo:
                alertas.append(
                    AlertaPreNatal(
                        gravidade=GravidadeAlerta.CRITICO,
                        mensagem=(
                            f"IG avançada ({trimestre.rotulo}) com {consultas_realizadas} "
                            f"consulta(s) registrada(s) — mínimo de {minimo} consulta(s) "
                            "esperado(s) pelo protocolo SisPreNatal."
                        ),
                        ig_semanas=ig_dias // 7,
                    )
                )
            if data_ultima_consulta is not None:
                dias_ultima = (data_referencia - data_ultima_consulta).days
                if dias_ultima >= INTERVALO_ATENCAO_DIAS:
                    alertas.append(
                        AlertaPreNatal(
                            gravidade=GravidadeAlerta.ATENCAO,
                            mensagem=(
                                f"IG avançada ({trimestre.rotulo}) com a última consulta "
                                f"há {dias_ultima} dia(s) — acompanhamento semanal "
                                "recomendado a partir de 36 semanas."
                            ),
                            ig_semanas=ig_dias // 7,
                            dias_ultima_consulta=dias_ultima,
                        )
                    )
            if ig_dias >= IG_TERMO_TARDIO_DIAS:
                alertas.append(
                    AlertaPreNatal(
                        gravidade=GravidadeAlerta.ATENCAO,
                        mensagem=(
                            f"IG de {ig_dias // 7} semanas (termo tardio) — avaliar "
                            "indicação de parto conforme protocolo do serviço."
                        ),
                        ig_semanas=ig_dias // 7,
                    )
                )
            if ig_dias >= IG_POS_TERMO_DIAS:
                alertas.insert(
                    0,
                    AlertaPreNatal(
                        gravidade=GravidadeAlerta.CRITICO,
                        mensagem=(
                            f"IG de {ig_dias // 7} semanas (pós-termo) — referenciar "
                            "para avaliação imediata do parto."
                        ),
                        ig_semanas=ig_dias // 7,
                    ),
                )
        return tuple(alertas)

    # ------------------------------------------------------------------ #
    # Avaliação completa (SOAP)                                           #
    # ------------------------------------------------------------------ #

    def avaliar(self, entrada: EntradaPreNatal) -> ResultadoPreNatal:
        """Avaliação completa do acompanhamento pré-natal (SisPreNatal/MS).

        Consolidates o cálculo de DPP pela regra de Naegele, a avaliação
        de cada consulta pela janela oportuna, os exames obrigatórios por
        trimestre e os alertas de IG avançada sem consulta, com plano
        sugerido para a APS e resumo pronto para o registro SOAP.

        Args:
            entrada: Dados de entrada (DUM, consultas, exames e
                identificação CNS/CPF).

        Returns:
            Resultado consolidado com plano e resumo SOAP.

        Raises:
            PreNatalInvalidoError: Se os dados violarem a tipagem estrita.
        """
        ig_dias = (entrada.data_referencia - entrada.dum).days
        semanas, trimestre = self.classificar_ig(ig_dias)

        # DPP pela regra de Naegele e IG atual.
        dpp = self.calcular_dpp_naegele(entrada.dum)
        resultado_dpp = ResultadoDPP(
            dum=entrada.dum,
            data_referencia=entrada.data_referencia,
            dpp=dpp,
            ig_dias=ig_dias,
            ig_semanas=semanas,
            ig_dias_restantes=ig_dias % 7,
            trimestre=trimestre,
            semanas_ate_dpp=40 - semanas,
            observacoes=(
                "DPP pela regra de Naegele: DUM − 3 meses + 7 dias (+ 1 ano) — "
                "pressupõe ciclo menstrual regular de 28 dias e DUM conhecida.",
                "IG calculada por DUM deve ser refinada com ultrassonografia "
                "do 1º trimestre.",
            ),
            resumo_soap=(
                f"S: Gestante com DUM em {entrada.dum.strftime('%d/%m/%Y')} — DPP "
                f"{dpp.strftime('%d/%m/%Y')} pela regra de Naegele. IG atual "
                f"{semanas} semanas e {ig_dias % 7} dia(s) ({trimestre.rotulo})."
            ),
            calculado_em=datetime.now(timezone.utc),
        )

        # Consultas pela janela oportuna (SisPreNatal/MS).
        consultas: list[ConsultaAvaliada] = []
        realizadas = entrada.consultas_realizadas
        for numero, (inicio, fim) in enumerate(JANELAS_CONSULTA, start=1):
            realizada = realizadas >= numero
            oportuna = realizada and ig_dias <= fim
            consultas.append(
                ConsultaAvaliada(
                    numero=numero,
                    janela_inicio_dias=inicio,
                    janela_fim_dias=fim,
                    ig_ideal_dias=(inicio + fim) // 2,
                    realizada=realizada,
                    oportuna=oportuna,
                    data_ideal=entrada.dum + timedelta(days=(inicio + fim) // 2),
                )
            )

        # Exames obrigatórios por trimestre (SisPreNatal/MS).
        trimestres: list[AvaliacaoTrimestre] = [
            self.avaliar_exames_trimestre(trimestre, entrada.exames_realizados)
        ]

        # Alertas de IG avançada sem consulta (SisPreNatal/MS).
        alertas = self.avaliar_alertas(
            ig_dias=ig_dias,
            consultas_realizadas=realizadas,
            data_ultima_consulta=entrada.data_ultima_consulta,
            data_referencia=entrada.data_referencia,
        )

        minimo_consultas = self.minimo_consultas_para_ig(ig_dias)
        acompanhamento_adequado = realizadas >= minimo_consultas and not any(
            avaliacao.exames_pendentes for avaliacao in trimestres
        )

        plano = (
            f"Registro na APS: {CIAP2_PRE_NATAL} / {CID10_PRE_NATAL} (pré-natal). "
            f"IG atual {semanas} semanas e {ig_dias % 7} dia(s) ({trimestre.rotulo}); "
            f"DPP {dpp.strftime('%d/%m/%Y')} pela regra de Naegele. "
            f"Mínimo de {minimo_consultas} consulta(s) esperado(s) para a IG — "
            f"registrada(s): {realizadas} consulta(s). "
            "Acompanhamento "
            + ("adequado" if acompanhamento_adequado else "com pendências")
            + " conforme o protocolo SisPreNatal; monitorar exames por trimestre "
            "e orientar sinais de alarme (sangramento, cefaleia persistente, "
            "edema, dor abdominal, movimentos fetais reduzidos) e retorno "
            "imediato ao serviço."
        )

        return ResultadoPreNatal(
            cns=entrada.cns,
            cpf=entrada.cpf,
            dpp=resultado_dpp,
            consultas=tuple(consultas),
            trimestres=tuple(trimestres),
            alertas=alertas,
            minimo_consultas=minimo_consultas,
            acompanhamento_adequado=acompanhamento_adequado,
            plano=plano,
            resumo_soap=resultado_dpp.resumo_soap,
            avaliado_em=datetime.now(timezone.utc),
        )


__all__ = [
    "AlertaPreNatal",
    "AvaliacaoTrimestre",
    "ConsultaAvaliada",
    "EntradaPreNatal",
    "ExamePreNatal",
    "GravidadeAlerta",
    "PreNatalInvalidoError",
    "PreNatalService",
    "ResultadoDPP",
    "ResultadoPreNatal",
    "TrimestreGestacional",
]
