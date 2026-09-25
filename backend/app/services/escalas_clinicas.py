"""Escalas Clínicas de Triagem (Glasgow, MEWS e EVA) — Projeto MedIA (SUS/APS).

Serviço de apoio à decisão para a Atenção Primária à Saúde (APS/SUS) que
implementa três escalas clínicas consolidadas na literatura e nos protocolos
do Ministério da Saúde:

1. **Escala de Coma de Glasgow (GCS)** — Teasdale/Jennett: pontua a abertura
   ocular (E, 1–4), a resposta verbal (V, 1–5) e a resposta motora (M, 1–6),
   totalizando de 3 a 15 pontos, com estadiamento do traumatismo
   cranioencefálico (TCE) em leve (13–14), moderado (9–12) e grave (3–8).
2. **Modified Early Warning Score (MEWS)** — Subbe et al.: pontua pressão
   arterial sistólica, frequência cardíaca, frequência respiratória,
   temperatura e nível de consciência (AVPU), totalizando de 0 a 14 pontos,
   para detecção precoce de deterioração clínica.
3. **Escala Visual Analógica da Dor (EVA)** — valor autorreferido de 0 a 10,
   com escalonamento analgésico por degraus conforme CEME/RENAME e PCDT.

Cada escala retorna o escore, a interpretação clínica e a conduta recomendada
no contexto do SUS/APS — incluindo acionamento do SAMU-192, regulação via
SISREG, contra-referência e sugestão de codificação CID-10/CIAP-2 — além de
um resumo pronto para o registro SOAP do prontuário.

Referências:

    - Teasdale G, Jennett B. Assessment of coma and impaired consciousness:
      a practical scale. Lancet. 1974;2(7872):81-84.
    - Teasdale G, Maas A, Lecky F, et al. The Glasgow Coma Scale at 40 years:
      standing the test of time. Lancet Neurol. 2014;13(8):844-854.
    - Subbe CP, Kruger M, Rutherford P, Gemmel L. Validation of a modified
      Early Warning Score in medical admissions. QJM. 2001;94(10):521-526.
    - NICE. Acutely ill adults in hospital: recognising and responding to
      deterioration (CG50/NG122) — gatilhos de parâmetro único.
    - Ministério da Saúde. Acolhimento com classificação de risco (Portaria
      SAS/MS nº 204/2002); Linha de Cuidado do Trauma; RENAME e CEME;
      Protocolos da atenção primária à saúde (e-Multi/PCDT).
    - Jensen MP, Karoly P, Braver S. The measurement of clinical pain
      intensity: a comparison of six methods. Pain. 1986;27(1):117-126.
    - WONCA. CIAP-2 — Classificação Internacional de Atenção Primária;
      CID-10 (OMS/DATASUS).

Limitações: escalas de apoio à decisão — não substituem o protocolo do
serviço, a bula dos medicamentos nem o julgamento clínico do profissional.
A Glasgow não deve ser aplicada sob sedação sem registrar o fator "S"; o
MEWS é validado para adultos (≥ 16 anos); a EVA depende do autorrelato.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Final, TypeAlias

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)

__all__ = [
    "AberturaOcular",
    "DadosClinicosInvalidosError",
    "EntradaEVA",
    "EntradaGlasgow",
    "EntradaMEWS",
    "EscalaGlasgow",
    "EscalaMEWS",
    "EscalaVisualAnalogaDor",
    "GravidadeGlasgow",
    "IntensidadeDor",
    "NivelConscienciaAVPU",
    "PontuacaoComponente",
    "ResultadoEVA",
    "ResultadoGlasgow",
    "ResultadoMEWS",
    "RespostaMotora",
    "RespostaVerbal",
    "RiscoMEWS",
]

# ---------------------------------------------------------------------------
# Integração com a identificação SUS (CNS) — degradação graciosa fora do pacote
# ---------------------------------------------------------------------------

try:  # pragma: no cover - depende do ambiente de execução
    from .validacao_cns import CNS

    VALIDACAO_CNS_DISPONIVEL: Final[bool] = True
except ImportError:  # pragma: no cover - execução fora do pacote (script direto)
    CNS: TypeAlias = str  # type: ignore[no-redef]
    VALIDACAO_CNS_DISPONIVEL = False


class DadosClinicosInvalidosError(ValueError):
    """Erro lançado quando os dados clínicos são inválidos para as escalas."""


# ---------------------------------------------------------------------------
# Escala de Coma de Glasgow — componentes (Teasdale/Jennett, 1974)
# ---------------------------------------------------------------------------


class AberturaOcular(int, Enum):
    """Componente E (Eye) da Glasgow — abertura ocular pontuada de 1 a 4."""

    def __new__(cls, valor: int, rotulo: str) -> "AberturaOcular":
        obj = int.__new__(cls, valor)
        obj._value_ = valor
        obj._rotulo = rotulo
        return obj

    ESPONTANEA = (4, "Abertura ocular espontânea")
    A_VOZ = (3, "Abre os olhos ao comando verbal")
    A_DOR = (2, "Abre os olhos apenas ao estímulo doloroso")
    NENHUMA = (1, "Sem abertura ocular")

    @property
    def rotulo(self) -> str:
        """Descrição clínica do achado de abertura ocular."""
        return self._rotulo


class RespostaVerbal(int, Enum):
    """Componente V (Verbal) da Glasgow — resposta verbal pontuada de 1 a 5."""

    def __new__(cls, valor: int, rotulo: str) -> "RespostaVerbal":
        obj = int.__new__(cls, valor)
        obj._value_ = valor
        obj._rotulo = rotulo
        return obj

    ORIENTADA = (5, "Conversação orientada no tempo e no espaço")
    CONFUSA = (4, "Discurso confuso, desorientado")
    PALAVRAS_INAPROPRIADAS = (3, "Palavras inapropriadas, sem conversação")
    SONS_INCOMPREENSIVEIS = (2, "Sons incompreensíveis, sem palavras")
    NENHUMA = (1, "Sem resposta verbal")

    @property
    def rotulo(self) -> str:
        """Descrição clínica do achado de resposta verbal."""
        return self._rotulo


class RespostaMotora(int, Enum):
    """Componente M (Motor) da Glasgow — resposta motora pontuada de 1 a 6."""

    def __new__(cls, valor: int, rotulo: str) -> "RespostaMotora":
        obj = int.__new__(cls, valor)
        obj._value_ = valor
        obj._rotulo = rotulo
        return obj

    OBEDECE_COMANDOS = (6, "Obedece a comandos simples")
    LOCALIZA_DOR = (5, "Localiza o estímulo doloroso")
    FLEXAO_RETIRADA = (4, "Flexão de retirada ao estímulo doloroso")
    FLEXAO_ANORMAL = (3, "Flexão anormal (decorticação)")
    EXTENSAO_ANORMAL = (2, "Extensão anormal (decerebração)")
    NENHUMA = (1, "Sem resposta motora")

    @property
    def rotulo(self) -> str:
        """Descrição clínica do achado de resposta motora."""
        return self._rotulo


class GravidadeGlasgow(str, Enum):
    """Estadiamento do TCE pelo escore de Glasgow (3–15) na APS/SUS.

    Cada membro carrega o rótulo clínico, a faixa de escore, a interpretação,
    a conduta recomendada no SUS e a sugestão de codificação CID-10/CIAP-2.
    """

    def __new__(
        cls,
        valor: str,
        rotulo: str,
        faixa: str,
        interpretacao: str,
        conduta_sus: str,
        cid10: str,
        ciap2: str,
        ordem: int,
    ) -> "GravidadeGlasgow":
        obj = str.__new__(cls, valor)
        obj._value_ = valor
        obj._rotulo = rotulo
        obj._faixa = faixa
        obj._interpretacao = interpretacao
        obj._conduta_sus = conduta_sus
        obj._codigo_cid10 = cid10
        obj._codigo_ciap2 = ciap2
        obj._ordem = ordem
        return obj

    NORMAL = (
        "normal",
        "sem alteração do nível de consciência",
        "15 pontos",
        "Escore máximo (15/15): sem depressão do nível de consciência.",
        (
            "Prosseguir com a avaliação clínica de rotina na APS; registrar a "
            "evolução no prontuário (SOAP); orientar sinais de alerta e retorno "
            "imediato ao serviço, com contra-referência quando procedente."
        ),
        "—",
        "A80",
        1,
    )
    LEVE = (
        "leve",
        "TCE leve",
        "13–14 pontos",
        "Traumatismo cranioencefálico leve: alteração discreta do nível de consciência.",
        (
            "Observação clínica com reavaliação neurológica seriada (30–60 min) "
            "no serviço; aplicar critérios de imagem (regra canadense de TC) e "
            "solicitar TC de crânio quando indicado; orientar sinais de alerta "
            "(cefaleia progressiva, vômitos persistentes, sonolência, perda de "
            "memória) e retorno imediato; alta com responsável e registro SOAP."
        ),
        "S06.9",
        "A80",
        2,
    )
    MODERADO = (
        "moderado",
        "TCE moderado",
        "9–12 pontos",
        "Traumatismo cranioencefálico moderado: comprometimento importante do nível de consciência.",
        (
            "Avaliação médica urgente; monitorização de sinais vitais e pupilas; "
            "solicitar TC de crânio; referenciar a serviço hospitalar/porta de "
            "trauma via regulação estadual (SISREG); acionar o SAMU-192 quando "
            "houver risco de deterioração durante o transporte."
        ),
        "S06.9",
        "A80",
        3,
    )
    GRAVE = (
        "grave",
        "TCE grave",
        "3–8 pontos",
        "Traumatismo cranioencefálico grave: coma ou depressão profunda do nível de consciência; alto risco de hipertensão intracraniana.",
        (
            "EMERGÊNCIA: acionar imediatamente o SAMU-192; garantir via aérea — "
            "GCS ≤ 8 indica intubação orotraqueal — com imobilização cervical e "
            "monitorização; manter cabeceira elevada (30°) e jejum; referenciar "
            "ao centro de trauma de referência pela regulação estadual (SISREG)."
        ),
        "S06.9",
        "A80",
        4,
    )

    @property
    def rotulo(self) -> str:
        """Rótulo clínico da classificação (ex.: "TCE grave")."""
        return self._rotulo

    @property
    def faixa(self) -> str:
        """Faixa de escore correspondente (ex.: "3–8 pontos")."""
        return self._faixa

    @property
    def interpretacao(self) -> str:
        """Interpretação clínica do estadiamento."""
        return self._interpretacao

    @property
    def conduta_sus(self) -> str:
        """Conduta recomendada no contexto SUS/APS."""
        return self._conduta_sus

    @property
    def codigo_cid10(self) -> str:
        """Sugestão de código CID-10 (refinar conforme quadro completo)."""
        return self._codigo_cid10

    @property
    def codigo_ciap2(self) -> str:
        """Sugestão de código CIAP-2 (A80 — trauma/lesão, outro)."""
        return self._codigo_ciap2

    @property
    def ordem(self) -> int:
        """Severidade ordinal da classificação (1 = normal ... 4 = grave)."""
        return self._ordem


# ---------------------------------------------------------------------------
# Schemas Pydantic v2 — Escala de Glasgow (tipagem estrita)
# ---------------------------------------------------------------------------


class EntradaGlasgow(BaseModel):
    """Dados de entrada da Escala de Coma de Glasgow.

    Attributes:
        cns: CNS do cidadão (identificação SUS, opcional; validado pelo
            módulo ``validacao_cns`` quando disponível no pacote).
        cpf: CPF do cidadão (opcional; normalizado para 11 dígitos).
        abertura_ocular: Componente E (1–4).
        resposta_verbal: Componente V (1–5).
        resposta_motora: Componente M (1–6).
        sedado: ``True`` quando o cidadão está sob sedação/paralisia (o GCS
            deve ser registrado com o fator "S" — ex.: GCS 6S).
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    cns: CNS | None = None
    cpf: str | None = None
    abertura_ocular: AberturaOcular
    resposta_verbal: RespostaVerbal
    resposta_motora: RespostaMotora
    sedado: bool = False

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


class ResultadoGlasgow(BaseModel):
    """Resultado consolidado da Escala de Glasgow para o prontuário (SOAP).

    Attributes:
        cns: CNS informado na entrada (rastreabilidade do cidadão).
        escore_total: Somatório E + V + M (entre 3 e 15).
        componentes: Linhas de detalhamento de cada componente avaliado.
        classificacao: Estadiamento do TCE (normal/leve/moderado/grave).
        interpretacao: Interpretação clínica do estadiamento.
        conduta_sus: Conduta recomendada no contexto SUS/APS.
        codigo_cid10: Sugestão de código CID-10.
        codigo_ciap2: Sugestão de código CIAP-2.
        observacoes: Ressalvas clínicas do resultado.
        resumo_soap: Linha pronta para o campo "A" (Avaliação) do SOAP.
        calculado_em: Data/hora (UTC) do cálculo.
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    cns: str | None = None
    escore_total: int = Field(ge=3, le=15)
    componentes: tuple[str, ...] = ()
    classificacao: GravidadeGlasgow
    interpretacao: str
    conduta_sus: str
    codigo_cid10: str
    codigo_ciap2: str
    observacoes: tuple[str, ...] = ()
    resumo_soap: str
    calculado_em: datetime


# ---------------------------------------------------------------------------
# MEWS — nível de consciência (AVPU) e schemas
# ---------------------------------------------------------------------------


class NivelConscienciaAVPU(str, Enum):
    """Nível de consciência pelo método AVPU, usado pelo MEWS e pela triagem.

    Attributes:
        letra: Letra do método AVPU (A/V/P/U).
        rotulo: Descrição clínica do estado de consciência.
        pontos: Pontuação do componente consciência no MEWS (0–3).
    """

    def __new__(cls, valor: str, letra: str, rotulo: str, pontos: int) -> "NivelConscienciaAVPU":
        obj = str.__new__(cls, valor)
        obj._value_ = valor
        obj._letra = letra
        obj._rotulo = rotulo
        obj._pontos = pontos
        return obj

    ALERTA = ("alerta", "A", "Alerta (olhos abertos, atento)", 0)
    RESPOSTA_A_VOZ = ("responde_a_voz", "V", "Responde ao comando verbal", 1)
    RESPOSTA_A_DOR = ("responde_a_dor", "P", "Responde apenas ao estímulo doloroso", 2)
    INCONSCIENTE = ("inconsciente", "U", "Não responde a estímulos (inconsciente)", 3)

    @property
    def letra(self) -> str:
        """Letra do método AVPU (A, V, P ou U)."""
        return self._letra

    @property
    def rotulo(self) -> str:
        """Descrição clínica do estado de consciência."""
        return self._rotulo

    @property
    def pontos(self) -> int:
        """Pontuação do componente no MEWS (0–3)."""
        return self._pontos


class PontuacaoComponente(BaseModel):
    """Pontuação de um componente do MEWS para exibição na interface.

    Attributes:
        componente: Nome clínico do componente avaliado.
        valor_informado: Valor medido (ou "não informado").
        pontos: Pontos atribuídos ao componente (0–3).
        observacao: Ressalva (ex.: componente não medido).
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    componente: str
    valor_informado: str
    pontos: int = Field(ge=0, le=3)
    observacao: str | None = None


class EntradaMEWS(BaseModel):
    """Sinais vitais e consciência para o cálculo do MEWS.

    Componentes não informados contam 0 ponto e geram observação — o escore
    pode estar subestimado quando há lacunas na coleta.

    Attributes:
        cns: CNS do cidadão (identificação SUS, opcional).
        cpf: CPF do cidadão (opcional; normalizado para 11 dígitos).
        pressao_sistolica_mmhg: Pressão arterial sistólica em mmHg (40–300).
        frequencia_cardiaca_bpm: Frequência cardíaca em bpm (0–300).
        frequencia_respiratoria_irpm: Frequência respiratória em irpm (0–100).
        temperatura_celsius: Temperatura em °C (25,0–45,0).
        nivel_consciencia: Nível de consciência pelo método AVPU.
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    cns: CNS | None = None
    cpf: str | None = None
    pressao_sistolica_mmhg: int | None = Field(None, ge=40, le=300)
    frequencia_cardiaca_bpm: int | None = Field(None, ge=0, le=300)
    frequencia_respiratoria_irpm: int | None = Field(None, ge=0, le=100)
    temperatura_celsius: float | None = Field(None, ge=25.0, le=45.0)
    nivel_consciencia: NivelConscienciaAVPU | None = None

    @field_validator("temperatura_celsius", mode="before")
    @classmethod
    def _aceitar_inteiro_na_temperatura(cls, valor: object) -> object:
        """Aceita inteiros na temperatura (ex.: 39 °C) convertendo para float."""
        if isinstance(valor, int) and not isinstance(valor, bool):
            return float(valor)
        return valor

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


class RiscoMEWS(str, Enum):
    """Estratificação de risco pelo escore MEWS (0–14) na APS/SUS.

    Cada membro carrega o rótulo, a faixa, a interpretação, a conduta
    recomendada no SUS e a frequência de reavaliação dos sinais vitais.
    """

    def __new__(
        cls,
        valor: str,
        rotulo: str,
        faixa: str,
        interpretacao: str,
        conduta_sus: str,
        reavaliacao: str,
        ordem: int,
    ) -> "RiscoMEWS":
        obj = str.__new__(cls, valor)
        obj._value_ = valor
        obj._rotulo = rotulo
        obj._faixa = faixa
        obj._interpretacao = interpretacao
        obj._conduta_sus = conduta_sus
        obj._reavaliacao = reavaliacao
        obj._ordem = ordem
        return obj

    BAIXO = (
        "baixo",
        "risco baixo",
        "0–2 pontos",
        "Sinais vitais estáveis ou com discreta variação; risco imediato de deterioração clínica baixo.",
        (
            "Manter vigilância de rotina na APS; registrar sinais vitais e "
            "evolução no SOAP; orientar sinais de alarme e retorno ao serviço; "
            "reavaliar conforme demanda da linha de cuidado."
        ),
        "Conforme demanda clínica (no mínimo ao fim do atendimento do dia).",
        1,
    )
    MODERADO = (
        "moderado",
        "risco moderado",
        "3–4 pontos",
        "Alterações moderadas de sinais vitais; risco intermediário de deterioração clínica em 24–48 horas.",
        (
            "Reavaliar sinais vitais em até 4–6 horas; discutir o caso com o "
            "médico da equipe (NASF/e-Multi) e intensificar o monitoramento; "
            "avaliar indicação de regulação (SISREG) se não houver resposta ao "
            "tratamento inicial; registrar no SOAP."
        ),
        "A cada 4–6 horas.",
        2,
    )
    ALTO = (
        "alto",
        "risco alto",
        "≥ 5 pontos",
        "Escore ≥ 5: alto risco de deterioração clínica iminente, parada cardiorrespiratória e mortalidade em até 48 horas.",
        (
            "EMERGÊNCIA: avaliação médica imediata; acionar o SAMU-192; "
            "referenciar à porta de emergência hospitalar pela regulação "
            "estadual (SISREG); manter monitorização contínua até a "
            "transferência; registrar no SOAP."
        ),
        "A cada 1 hora ou a cada novo conjunto de sinais vitais.",
        3,
    )

    @property
    def rotulo(self) -> str:
        """Rótulo de risco (ex.: "risco alto")."""
        return self._rotulo

    @property
    def faixa(self) -> str:
        """Faixa de escore correspondente (ex.: "≥ 5 pontos")."""
        return self._faixa

    @property
    def interpretacao(self) -> str:
        """Interpretação clínica do risco."""
        return self._interpretacao

    @property
    def conduta_sus(self) -> str:
        """Conduta recomendada no contexto SUS/APS."""
        return self._conduta_sus

    @property
    def reavaliacao(self) -> str:
        """Frequência de reavaliação dos sinais vitais."""
        return self._reavaliacao

    @property
    def ordem(self) -> int:
        """Severidade ordinal do risco (1 = baixo ... 3 = alto)."""
        return self._ordem


class ResultadoMEWS(BaseModel):
    """Resultado consolidado do MEWS para o prontuário (SOAP).

    Attributes:
        cns: CNS informado na entrada (rastreabilidade do cidadão).
        escore_total: Somatório dos componentes informados (0–14).
        escore_maximo: Maior escore possível com os componentes informados.
        detalhamento: Pontuação por componente (para a interface).
        classificacao: Estratificação de risco (baixo/moderado/alto).
        interpretacao: Interpretação clínica do risco.
        conduta_sus: Conduta recomendada no contexto SUS/APS (inclui gatilhos).
        reavaliacao: Frequência de reavaliação recomendada.
        gatilhos_individuais: Gatilhos de parâmetro único detectados.
        observacoes: Ressalvas clínicas do resultado.
        resumo_soap: Linha pronta para o campo "A" (Avaliação) do SOAP.
        calculado_em: Data/hora (UTC) do cálculo.
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    cns: str | None = None
    escore_total: int = Field(ge=0, le=14)
    escore_maximo: int = Field(ge=0, le=14)
    detalhamento: tuple[PontuacaoComponente, ...] = ()
    classificacao: RiscoMEWS
    interpretacao: str
    conduta_sus: str
    reavaliacao: str
    gatilhos_individuais: tuple[str, ...] = ()
    observacoes: tuple[str, ...] = ()
    resumo_soap: str
    calculado_em: datetime


# ---------------------------------------------------------------------------
# EVA — escala visual analógica da dor (0–10)
# ---------------------------------------------------------------------------


class IntensidadeDor(str, Enum):
    """Estratificação da dor pela EVA (0–10) com escalonamento por degraus.

    Cada membro carrega o rótulo, a faixa, a interpretação, a conduta
    recomendada no SUS, a analgesia sugerida (CEME/RENAME/PCDT), a
    reavaliação e a sugestão de codificação CID-10/CIAP-2.
    """

    def __new__(
        cls,
        valor: str,
        rotulo: str,
        faixa: str,
        interpretacao: str,
        conduta_sus: str,
        analgesia_sugerida: str,
        reavaliacao: str,
        cid10: str,
        ciap2: str,
        ordem: int,
    ) -> "IntensidadeDor":
        obj = str.__new__(cls, valor)
        obj._value_ = valor
        obj._rotulo = rotulo
        obj._faixa = faixa
        obj._interpretacao = interpretacao
        obj._conduta_sus = conduta_sus
        obj._analgesia_sugerida = analgesia_sugerida
        obj._reavaliacao = reavaliacao
        obj._codigo_cid10 = cid10
        obj._codigo_ciap2 = ciap2
        obj._ordem = ordem
        return obj

    SEM_DOR = (
        "sem_dor",
        "Sem dor",
        "0",
        "Ausência de dor referida na escala visual analógica.",
        (
            "Prosseguir com a avaliação da queixa principal; registrar a "
            "ausência de dor no SOAP."
        ),
        "Não indicar analgesia.",
        "Conforme evolução clínica.",
        "—",
        "—",
        0,
    )
    LEVE = (
        "leve",
        "Dor leve",
        "1–3",
        "Dor de intensidade leve, sem comprometimento relevante da função.",
        (
            "Analgesia por degrau I (analgésico simples) conforme CEME/RENAME; "
            "orientar medidas não farmacológicas e sinais de alarme; registrar "
            "no SOAP e reavaliar."
        ),
        "Degrau I: dipirona 500–1.000 mg VO até 4×/dia OU paracetamol 500–750 mg VO até 4×/dia.",
        "Reavaliar em 24–48 horas (retorno, visita domiciliar ou teleatendimento).",
        "R52",
        "A01",
        1,
    )
    MODERADA = (
        "moderada",
        "Dor moderada",
        "4–6",
        "Dor de intensidade moderada com interferência funcional.",
        (
            "Escalonar para degrau II (analgesia associada) com avaliação médica "
            "no turno; checar contraindicações de AINE (úlcera péptica, DRC, "
            "gestação, cardiopatia); investigar a causa da dor; registrar no SOAP."
        ),
        "Degrau II: manter degrau I + AINE (ex.: ibuprofeno 400–600 mg VO até 3×/dia) conforme contraindicações.",
        "Reavaliar em até 24 horas; ajustar o escalonamento conforme resposta.",
        "R52",
        "A01",
        2,
    )
    INTENSA = (
        "intensa",
        "Dor intensa",
        "7–8",
        "Dor de intensidade intensa com grande interferência funcional; exige prioridade no acolhimento.",
        (
            "Prioridade no acolhimento com avaliação médica no mesmo dia; "
            "analgesia por degrau III (associar opioide fraco conforme "
            "PCDT/RENAME); investigar a causa e documentar; reavaliar resposta "
            "à analgesia."
        ),
        "Degrau III: degrau II + opioide fraco (ex.: tramadol 50–100 mg VO/IV a cada 6–8 h), conforme PCDT/RENAME.",
        "Reavaliar no mesmo dia após a analgesia inicial.",
        "R52",
        "A01",
        3,
    )
    MUITO_INTENSA = (
        "muito_intensa",
        "Dor muito intensa",
        "9–10",
        "Dor máxima referida (pior dor imaginável); potencialmente emergência (dor torácica, abdominal aguda, trauma etc.).",
        (
            "Atendimento imediato; investigar sinais de alarme (dor torácica, "
            "dispneia, alteração do nível de consciência, instabilidade "
            "hemodinâmica) e acionar o SAMU-192 quando presentes; analgesia com "
            "opioide forte conforme protocolo do serviço; registrar no SOAP."
        ),
        "Opioide forte conforme protocolo do serviço (ex.: morfina 2,5–5 mg IV a cada 4–6 h) com monitorização.",
        "Reavaliar continuamente até o controle da dor; investigação imediata da causa.",
        "R52",
        "A01",
        4,
    )

    @property
    def rotulo(self) -> str:
        """Rótulo de intensidade (ex.: "Dor intensa")."""
        return self._rotulo

    @property
    def faixa(self) -> str:
        """Faixa de escore correspondente (ex.: "7–8")."""
        return self._faixa

    @property
    def interpretacao(self) -> str:
        """Interpretação clínica da intensidade da dor."""
        return self._interpretacao

    @property
    def conduta_sus(self) -> str:
        """Conduta recomendada no contexto SUS/APS."""
        return self._conduta_sus

    @property
    def analgesia_sugerida(self) -> str:
        """Escalonamento analgésico sugerido (CEME/RENAME/PCDT)."""
        return self._analgesia_sugerida

    @property
    def reavaliacao(self) -> str:
        """Frequência de reavaliação da dor."""
        return self._reavaliacao

    @property
    def codigo_cid10(self) -> str:
        """Sugestão de código CID-10 (R52 — dor, refinar conforme tipo)."""
        return self._codigo_cid10

    @property
    def codigo_ciap2(self) -> str:
        """Sugestão de código CIAP-2 (A01 — dor generalizada, refinar pelo local)."""
        return self._codigo_ciap2

    @property
    def ordem(self) -> int:
        """Severidade ordinal da intensidade (0 = sem dor ... 4 = muito intensa)."""
        return self._ordem


class EntradaEVA(BaseModel):
    """Dados de entrada da Escala Visual Analógica da Dor (EVA 0–10).

    Attributes:
        cns: CNS do cidadão (identificação SUS, opcional).
        cpf: CPF do cidadão (opcional; normalizado para 11 dígitos).
        valor: Intensidade autorreferida da dor (0 = sem dor; 10 = pior dor
            imaginável).
        local_da_dor: Local da dor referido (opcional; refina o CIAP-2).
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    cns: CNS | None = None
    cpf: str | None = None
    valor: int = Field(ge=0, le=10)
    local_da_dor: str | None = None

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

    @field_validator("local_da_dor")
    @classmethod
    def _limpar_local(cls, valor: str | None) -> str | None:
        """Remove espaços extras do local da dor."""
        if valor is None:
            return None
        valor = valor.strip()
        return valor or None


class ResultadoEVA(BaseModel):
    """Resultado consolidado da EVA para o prontuário (SOAP).

    Attributes:
        cns: CNS informado na entrada (rastreabilidade do cidadão).
        valor: Intensidade autorreferida da dor (0–10).
        intensidade: Estratificação de intensidade correspondente.
        interpretacao: Interpretação clínica da intensidade.
        conduta_sus: Conduta recomendada no contexto SUS/APS.
        analgesia_sugerida: Escalonamento analgésico sugerido.
        reavaliacao: Frequência de reavaliação da dor.
        exige_atencao_imediata: ``True`` para EVA ≥ 9 (potencial emergência).
        codigo_cid10: Sugestão de código CID-10.
        codigo_ciap2: Sugestão de código CIAP-2.
        observacoes: Ressalvas clínicas do resultado.
        resumo_soap: Linha pronta para o campo "A" (Avaliação) do SOAP.
        calculado_em: Data/hora (UTC) do cálculo.
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    cns: str | None = None
    valor: int = Field(ge=0, le=10)
    intensidade: IntensidadeDor
    interpretacao: str
    conduta_sus: str
    analgesia_sugerida: str
    reavaliacao: str
    exige_atencao_imediata: bool
    codigo_cid10: str
    codigo_ciap2: str
    observacoes: tuple[str, ...] = ()
    resumo_soap: str
    calculado_em: datetime


# ---------------------------------------------------------------------------
# Serviço principal — Escala de Glasgow
# ---------------------------------------------------------------------------


class EscalaGlasgow:
    """Escala de Coma de Glasgow (Teasdale/Jennett): escore, interpretação e conduta.

    Exemplos de uso::

        >>> escala = EscalaGlasgow()
        >>> entrada = EntradaGlasgow(
        ...     abertura_ocular=AberturaOcular.A_VOZ,
        ...     resposta_verbal=RespostaVerbal.CONFUSA,
        ...     resposta_motora=RespostaMotora.OBEDECE_COMANDOS,
        ... )
        >>> resultado = escala.avaliar(entrada)
        >>> resultado.escore_total, resultado.classificacao.value
        (12, 'moderado')
    """

    ESCORE_MAXIMO: Final[int] = 15
    ESCORE_MINIMO: Final[int] = 3

    LIMIARES: Final[tuple[tuple[int, GravidadeGlasgow], ...]] = (
        (15, GravidadeGlasgow.NORMAL),
        (13, GravidadeGlasgow.LEVE),
        (9, GravidadeGlasgow.MODERADO),
    )

    def pontuar(self, entrada: EntradaGlasgow) -> int:
        """Somatoria os componentes E + V + M da escala (3–15).

        Args:
            entrada: Componentes avaliados da Glasgow.

        Returns:
            Escore total da escala de Glasgow.
        """
        return (
            entrada.abertura_ocular.value
            + entrada.resposta_verbal.value
            + entrada.resposta_motora.value
        )

    def classificar(self, escore: int) -> GravidadeGlasgow:
        """Estadia o TCE a partir do escore da Glasgow.

        Args:
            escore: Escore total da escala (3–15).

        Raises:
            DadosClinicosInvalidosError: Se o escore estiver fora de 3–15.
        """
        if not isinstance(escore, int) or not self.ESCORE_MINIMO <= escore <= self.ESCORE_MAXIMO:
            raise DadosClinicosInvalidosError(
                f"Escore de Glasgow inválido: {escore!r} (esperado número inteiro entre "
                f"{self.ESCORE_MINIMO} e {self.ESCORE_MAXIMO})."
            )
        for limite, classificacao in self.LIMIARES:
            if escore >= limite:
                return classificacao
        return GravidadeGlasgow.GRAVE

    def avaliar(self, entrada: EntradaGlasgow) -> ResultadoGlasgow:
        """Avaliação completa da Glasgow: escore, estadiamento e conduta SUS.

        Args:
            entrada: Componentes da Glasgow e identificação (CNS/CPF).

        Returns:
            Resultado consolidado com resumo pronto para o campo "A" do SOAP.
        """
        escore = self.pontuar(entrada)
        classificacao = self.classificar(escore)

        componentes: tuple[str, ...] = (
            f"Abertura ocular (E): {entrada.abertura_ocular.rotulo} — {entrada.abertura_ocular.value} ponto(s)",
            f"Resposta verbal (V): {entrada.resposta_verbal.rotulo} — {entrada.resposta_verbal.value} ponto(s)",
            f"Resposta motora (M): {entrada.resposta_motora.rotulo} — {entrada.resposta_motora.value} ponto(s)",
        )

        observacoes: list[str] = [
            "Escala aplicada em adultos e crianças a partir de 5 anos; em menores, usar a escala de Glasgow pediátrica modificada (AVPU).",
            "Codificação CID-10/CIAP-2 sugerida — refinar conforme o quadro clínico completo.",
        ]
        if entrada.sedado:
            observacoes.append(
                "Sedação/paralisia pode subestimar o GCS — registrar o fator 'S' "
                "(ex.: GCS 6S) e reavaliar após o efeito do fármaco."
            )

        resumo_soap = (
            f"A: GCS {escore}/15 ({classificacao.rotulo}) — E{entrada.abertura_ocular.value} "
            f"V{entrada.resposta_verbal.value} M{entrada.resposta_motora.value}. CID-10 "
            f"{classificacao.codigo_cid10} | CIAP-2 {classificacao.codigo_ciap2}. "
            f"Interpretação: {classificacao.interpretacao} Conduta SUS: {classificacao.conduta_sus}"
        )

        return ResultadoGlasgow(
            cns=entrada.cns,
            escore_total=escore,
            componentes=componentes,
            classificacao=classificacao,
            interpretacao=classificacao.interpretacao,
            conduta_sus=classificacao.conduta_sus,
            codigo_cid10=classificacao.codigo_cid10,
            codigo_ciap2=classificacao.codigo_ciap2,
            observacoes=tuple(observacoes),
            resumo_soap=resumo_soap,
            calculado_em=datetime.now(timezone.utc),
        )

    @classmethod
    def avaliar_valores(
        cls,
        abertura_ocular: AberturaOcular,
        resposta_verbal: RespostaVerbal,
        resposta_motora: RespostaMotora,
        sedado: bool = False,
        cns: str | None = None,
        cpf: str | None = None,
    ) -> ResultadoGlasgow:
        """Avaliação a partir de valores crus, com erros em português.

        Raises:
            DadosClinicosInvalidosError: Se os dados violarem a tipagem estrita.
        """
        try:
            entrada = EntradaGlasgow(
                abertura_ocular=abertura_ocular,
                resposta_verbal=resposta_verbal,
                resposta_motora=resposta_motora,
                sedado=sedado,
                cns=cns,
                cpf=cpf,
            )
        except ValidationError as erro:
            raise DadosClinicosInvalidosError(
                f"Dados inválidos para a Escala de Glasgow: {erro}"
            ) from erro
        return cls().avaliar(entrada)


# ---------------------------------------------------------------------------
# Serviço principal — MEWS
# ---------------------------------------------------------------------------


class EscalaMEWS:
    """Modified Early Warning Score (Subbe et al.): escore, risco e conduta SUS.

    Pontua pressão arterial sistólica (0–3), frequência cardíaca (0–3),
    frequência respiratória (0–3), temperatura (0–2) e nível de consciência
    AVPU (0–3), com máximo de 14 pontos. Complementa o escore com gatilhos de
    parâmetro único (NICE), como PA sistólica ≤ 90 mmHg e FR ≥ 30 irpm.

    Exemplos de uso::

        >>> escala = EscalaMEWS()
        >>> entrada = EntradaMEWS(
        ...     pressao_sistolica_mmhg=85,
        ...     frequencia_cardiaca_bpm=120,
        ...     frequencia_respiratoria_irpm=26,
        ...     temperatura_celsius=39.0,
        ...     nivel_consciencia=NivelConscienciaAVPU.INCONSCIENTE,
        ... )
        >>> resultado = escala.avaliar(entrada)
        >>> resultado.escore_total, resultado.classificacao.value
        (10, 'alto')
    """

    ESCORE_MAXIMO: Final[int] = 14

    PONTOS_MAXIMOS: Final[dict[str, int]] = {
        "pressao_sistolica": 3,
        "frequencia_cardiaca": 3,
        "frequencia_respiratoria": 3,
        "temperatura": 2,
        "consciencia": 3,
    }

    GATILHO_PA_SISTOLICA: Final[int] = 90
    GATILHO_FREQUENCIA_CARDIACA: Final[int] = 130
    GATILHO_FREQUENCIA_RESPIRATORIA: Final[int] = 30
    GATILHO_TEMPERATURA_ALTA: Final[float] = 39.0
    GATILHO_TEMPERATURA_BAIXA: Final[float] = 35.0

    # ------------------------------------------------------------------ #
    # Pontuação por componente (Subbe et al., 2001)                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _pontuar_pressao_sistolica(pas: int) -> int:
        """Pontua a pressão arterial sistólica (mmHg) conforme o MEWS."""
        if pas <= 70:
            return 3
        if pas <= 80:
            return 2
        if pas <= 100:
            return 1
        if pas <= 199:
            return 0
        return 2

    @staticmethod
    def _pontuar_frequencia_cardiaca(fc: int) -> int:
        """Pontua a frequência cardíaca (bpm) conforme o MEWS."""
        if fc < 40:
            return 2
        if fc <= 50:
            return 1
        if fc <= 100:
            return 0
        if fc <= 110:
            return 1
        if fc <= 129:
            return 2
        return 3

    @staticmethod
    def _pontuar_frequencia_respiratoria(fr: int) -> int:
        """Pontua a frequência respiratória (irpm) conforme o MEWS."""
        if fr < 9:
            return 2
        if fr <= 14:
            return 0
        if fr <= 20:
            return 1
        if fr <= 29:
            return 2
        return 3

    @staticmethod
    def _pontuar_temperatura(temperatura: float) -> int:
        """Pontua a temperatura (°C) conforme o MEWS."""
        if temperatura < 35.0:
            return 2
        if temperatura < 38.5:
            return 0
        return 2

    # ------------------------------------------------------------------ #
    # Detalhamento e escore                                               #
    # ------------------------------------------------------------------ #

    def detalhar(self, entrada: EntradaMEWS) -> tuple[PontuacaoComponente, ...]:
        """Pontua cada componente do MEWS, sinalizando lacunas de coleta.

        Args:
            entrada: Sinais vitais e nível de consciência informados.

        Returns:
            Pontuação detalhada, com observação para componentes não medidos.
        """
        observacao_lacuna = "Componente não medido — conta 0 ponto; o escore pode estar subestimado."

        def quando_informado(
            componente: str, valor_informado: str, pontos: int
        ) -> PontuacaoComponente:
            return PontuacaoComponente(
                componente=componente,
                valor_informado=valor_informado,
                pontos=pontos,
            )

        def quando_ausente(componente: str) -> PontuacaoComponente:
            return PontuacaoComponente(
                componente=componente,
                valor_informado="não informado",
                pontos=0,
                observacao=observacao_lacuna,
            )

        if entrada.pressao_sistolica_mmhg is None:
            pressao = quando_ausente("Pressão arterial sistólica (mmHg)")
        else:
            pressao = quando_informado(
                "Pressão arterial sistólica (mmHg)",
                f"{entrada.pressao_sistolica_mmhg} mmHg",
                self._pontuar_pressao_sistolica(entrada.pressao_sistolica_mmhg),
            )

        if entrada.frequencia_cardiaca_bpm is None:
            cardiaca = quando_ausente("Frequência cardíaca (bpm)")
        else:
            cardiaca = quando_informado(
                "Frequência cardíaca (bpm)",
                f"{entrada.frequencia_cardiaca_bpm} bpm",
                self._pontuar_frequencia_cardiaca(entrada.frequencia_cardiaca_bpm),
            )

        if entrada.frequencia_respiratoria_irpm is None:
            respiratoria = quando_ausente("Frequência respiratória (irpm)")
        else:
            respiratoria = quando_informado(
                "Frequência respiratória (irpm)",
                f"{entrada.frequencia_respiratoria_irpm} irpm",
                self._pontuar_frequencia_respiratoria(entrada.frequencia_respiratoria_irpm),
            )

        if entrada.temperatura_celsius is None:
            temperatura = quando_ausente("Temperatura (°C)")
        else:
            temperatura = quando_informado(
                "Temperatura (°C)",
                f"{entrada.temperatura_celsius:.1f}".replace(".", ",") + " °C",
                self._pontuar_temperatura(entrada.temperatura_celsius),
            )

        if entrada.nivel_consciencia is None:
            consciencia = quando_ausente("Nível de consciência (AVPU)")
        else:
            consciencia = quando_informado(
                "Nível de consciência (AVPU)",
                f"{entrada.nivel_consciencia.letra} — {entrada.nivel_consciencia.rotulo}",
                entrada.nivel_consciencia.pontos,
            )

        return (pressao, cardiaca, respiratoria, temperatura, consciencia)

    def pontuar(self, entrada: EntradaMEWS) -> int:
        """Somatório dos pontos dos componentes informados (0–14).

        Args:
            entrada: Sinais vitais e nível de consciência informados.

        Returns:
            Escore total do MEWS.
        """
        return sum(componente.pontos for componente in self.detalhar(entrada))

    def escore_maximo_disponivel(self, entrada: EntradaMEWS) -> int:
        """Maior escore possível considerando apenas os componentes informados.

        Args:
            entrada: Sinais vitais e nível de consciência informados.

        Returns:
            Somatório dos pontos máximos dos componentes efetivamente medidos.
        """
        maximos = self.PONTOS_MAXIMOS
        total = 0
        if entrada.pressao_sistolica_mmhg is not None:
            total += maximos["pressao_sistolica"]
        if entrada.frequencia_cardiaca_bpm is not None:
            total += maximos["frequencia_cardiaca"]
        if entrada.frequencia_respiratoria_irpm is not None:
            total += maximos["frequencia_respiratoria"]
        if entrada.temperatura_celsius is not None:
            total += maximos["temperatura"]
        if entrada.nivel_consciencia is not None:
            total += maximos["consciencia"]
        return total

    def gatilhos_individuais(self, entrada: EntradaMEWS) -> tuple[str, ...]:
        """Detecta gatilhos de parâmetro único (NICE) nos sinais vitais.

        Gatilhos detectados: PA sistólica ≤ 90 mmHg, FC ≥ 130 bpm,
        FR ≥ 30 irpm, temperatura ≥ 39,0 °C ou < 35,0 °C e consciência
        diferente de "alerta".

        Args:
            entrada: Sinais vitais e nível de consciência informados.

        Returns:
            Descrição dos gatilhos detectados (vazia quando nenhum).
        """
        gatilhos: list[str] = []
        if (
            entrada.pressao_sistolica_mmhg is not None
            and entrada.pressao_sistolica_mmhg <= self.GATILHO_PA_SISTOLICA
        ):
            gatilhos.append(
                f"PA sistólica ≤ {self.GATILHO_PA_SISTOLICA} mmHg (registrada: {entrada.pressao_sistolica_mmhg} mmHg)"
            )
        if (
            entrada.frequencia_cardiaca_bpm is not None
            and entrada.frequencia_cardiaca_bpm >= self.GATILHO_FREQUENCIA_CARDIACA
        ):
            gatilhos.append(
                f"FC ≥ {self.GATILHO_FREQUENCIA_CARDIACA} bpm (registrada: {entrada.frequencia_cardiaca_bpm} bpm)"
            )
        if (
            entrada.frequencia_respiratoria_irpm is not None
            and entrada.frequencia_respiratoria_irpm >= self.GATILHO_FREQUENCIA_RESPIRATORIA
        ):
            gatilhos.append(
                f"FR ≥ {self.GATILHO_FREQUENCIA_RESPIRATORIA} irpm (registrada: {entrada.frequencia_respiratoria_irpm} irpm)"
            )
        if entrada.temperatura_celsius is not None and (
            entrada.temperatura_celsius >= self.GATILHO_TEMPERATURA_ALTA
            or entrada.temperatura_celsius < self.GATILHO_TEMPERATURA_BAIXA
        ):
            temperatura = f"{entrada.temperatura_celsius:.1f}".replace(".", ",")
            gatilhos.append(
                f"Temperatura ≥ {str(self.GATILHO_TEMPERATURA_ALTA).replace('.', ',')} °C ou < "
                f"{str(self.GATILHO_TEMPERATURA_BAIXA).replace('.', ',')} °C (registrada: {temperatura} °C)"
            )
        if entrada.nivel_consciencia is not None and entrada.nivel_consciencia is not NivelConscienciaAVPU.ALERTA:
            gatilhos.append(
                f"Consciência diferente de alerta ({entrada.nivel_consciencia.letra} — {entrada.nivel_consciencia.rotulo})"
            )
        return tuple(gatilhos)

    def classificar(self, escore: int) -> RiscoMEWS:
        """Estratifica o risco a partir do escore do MEWS.

        Args:
            escore: Escore total do MEWS (0–14).

        Raises:
            DadosClinicosInvalidosError: Se o escore estiver fora de 0–14.
        """
        if not isinstance(escore, int) or not 0 <= escore <= self.ESCORE_MAXIMO:
            raise DadosClinicosInvalidosError(
                f"Escore de MEWS inválido: {escore!r} (esperado número inteiro entre "
                f"0 e {self.ESCORE_MAXIMO})."
            )
        if escore >= 5:
            return RiscoMEWS.ALTO
        if escore >= 3:
            return RiscoMEWS.MODERADO
        return RiscoMEWS.BAIXO

    def avaliar(self, entrada: EntradaMEWS) -> ResultadoMEWS:
        """Avaliação completa do MEWS: escore, gatilhos, risco e conduta SUS.

        Args:
            entrada: Sinais vitais, consciência e identificação (CNS/CPF).

        Returns:
            Resultado consolidado com resumo pronto para o campo "A" do SOAP.
        """
        detalhamento = self.detalhar(entrada)
        escore = sum(componente.pontos for componente in detalhamento)
        classificacao = self.classificar(escore)
        gatilhos = self.gatilhos_individuais(entrada)

        conduta_sus = classificacao.conduta_sus
        if gatilhos:
            conduta_sus += (
                " Gatilho(s) individual(is) presente(s): "
                + "; ".join(gatilhos)
                + " — reavaliar como prioridade, mesmo com escore baixo."
            )

        observacoes: list[str] = [
            "MEWS validado para adultos (≥ 16 anos); não substitui o protocolo do serviço nem o julgamento clínico.",
        ]
        lacunas = [componente.componente for componente in detalhamento if componente.observacao]
        if lacunas:
            observacoes.append(
                "Componente(s) não medido(s) contam 0 ponto (" + "; ".join(lacunas) + ") — o escore pode estar subestimado."
            )

        medicoes: list[str] = []
        for componente in detalhamento:
            if componente.observacao is None:
                medicoes.append(f"{componente.componente.split(' (')[0]}: {componente.valor_informado}")
        resumo_soap = (
            f"A: MEWS {escore}/14 ({classificacao.rotulo}) — "
            + "; ".join(medicoes)
            + f". {classificacao.interpretacao} Conduta SUS: {conduta_sus}"
        )

        return ResultadoMEWS(
            cns=entrada.cns,
            escore_total=escore,
            escore_maximo=self.escore_maximo_disponivel(entrada),
            detalhamento=detalhamento,
            classificacao=classificacao,
            interpretacao=classificacao.interpretacao,
            conduta_sus=conduta_sus,
            reavaliacao=classificacao.reavaliacao,
            gatilhos_individuais=gatilhos,
            observacoes=tuple(observacoes),
            resumo_soap=resumo_soap,
            calculado_em=datetime.now(timezone.utc),
        )

    @classmethod
    def avaliar_valores(
        cls,
        pressao_sistolica_mmhg: int | None = None,
        frequencia_cardiaca_bpm: int | None = None,
        frequencia_respiratoria_irpm: int | None = None,
        temperatura_celsius: float | None = None,
        nivel_consciencia: NivelConscienciaAVPU | None = None,
        cns: str | None = None,
        cpf: str | None = None,
    ) -> ResultadoMEWS:
        """Avaliação a partir de valores crus, com erros em português.

        Raises:
            DadosClinicosInvalidosError: Se os dados violarem os limites clínicos.
        """
        try:
            entrada = EntradaMEWS(
                pressao_sistolica_mmhg=pressao_sistolica_mmhg,
                frequencia_cardiaca_bpm=frequencia_cardiaca_bpm,
                frequencia_respiratoria_irpm=frequencia_respiratoria_irpm,
                temperatura_celsius=temperatura_celsius,
                nivel_consciencia=nivel_consciencia,
                cns=cns,
                cpf=cpf,
            )
        except ValidationError as erro:
            raise DadosClinicosInvalidosError(
                f"Dados inválidos para o MEWS: {erro}"
            ) from erro
        return cls().avaliar(entrada)


# ---------------------------------------------------------------------------
# Serviço principal — Escala Visual Analógica da Dor (EVA)
# ---------------------------------------------------------------------------


class EscalaVisualAnalogaDor:
    """Escala Visual Analógica da Dor (EVA 0–10): escore, interpretação e conduta.

    Estratifica a dor autorreferida e sugere o escalonamento analgésico por
    degraus conforme CEME/RENAME e PCDT do Ministério da Saúde, com prioridade
    de acolhimento quando indicado.

    Exemplos de uso::

        >>> escala = EscalaVisualAnalogaDor()
        >>> resultado = escala.avaliar(EntradaEVA(valor=8, local_da_dor="lombar"))
        >>> resultado.intensidade.value, resultado.exige_atencao_imediata
        ('intensa', False)
    """

    VALOR_MAXIMO: Final[int] = 10

    def classificar(self, valor: int) -> IntensidadeDor:
        """Estratifica a intensidade da dor a partir do valor da EVA.

        Args:
            valor: Intensidade autorreferida (0–10).

        Raises:
            DadosClinicosInvalidosError: Se o valor estiver fora de 0–10.
        """
        if not isinstance(valor, int) or not 0 <= valor <= self.VALOR_MAXIMO:
            raise DadosClinicosInvalidosError(
                f"Valor de EVA inválido: {valor!r} (esperado número inteiro entre "
                f"0 e {self.VALOR_MAXIMO})."
            )
        if valor == 0:
            return IntensidadeDor.SEM_DOR
        if valor <= 3:
            return IntensidadeDor.LEVE
        if valor <= 6:
            return IntensidadeDor.MODERADA
        if valor <= 8:
            return IntensidadeDor.INTENSA
        return IntensidadeDor.MUITO_INTENSA

    def avaliar(self, entrada: EntradaEVA) -> ResultadoEVA:
        """Avaliação completa da EVA: intensidade, analgesia e conduta SUS.

        Args:
            entrada: Valor da EVA, local da dor e identificação (CNS/CPF).

        Returns:
            Resultado consolidado com resumo pronto para o campo "A" do SOAP.
        """
        intensidade = self.classificar(entrada.valor)

        observacoes: list[str] = [
            "A EVA é autorrelato; quando o cidadão não puder pontuar, usar escala alternativa (ex.: Wong-Baker/FACES).",
        ]
        if entrada.local_da_dor:
            observacoes.append(
                "Refinar o código CIAP-2 pelo local da dor (ex.: L03 — lombalgia)."
            )
        if intensidade is IntensidadeDor.MUITO_INTENSA:
            observacoes.append(
                "EVA ≥ 9 exige investigação imediata de causas graves (dor torácica, abdominal aguda, trauma)."
            )

        local = f", local: {entrada.local_da_dor}" if entrada.local_da_dor else ""
        resumo_soap = (
            f"A: {intensidade.rotulo} (EVA {entrada.valor}/10{local}). CID-10 "
            f"{intensidade.codigo_cid10} | CIAP-2 {intensidade.codigo_ciap2}. "
            f"Interpretação: {intensidade.interpretacao} Conduta SUS: "
            f"{intensidade.conduta_sus} Analgesia: {intensidade.analgesia_sugerida}"
        )

        return ResultadoEVA(
            cns=entrada.cns,
            valor=entrada.valor,
            intensidade=intensidade,
            interpretacao=intensidade.interpretacao,
            conduta_sus=intensidade.conduta_sus,
            analgesia_sugerida=intensidade.analgesia_sugerida,
            reavaliacao=intensidade.reavaliacao,
            exige_atencao_imediata=intensidade is IntensidadeDor.MUITO_INTENSA,
            codigo_cid10=intensidade.codigo_cid10,
            codigo_ciap2=intensidade.codigo_ciap2,
            observacoes=tuple(observacoes),
            resumo_soap=resumo_soap,
            calculado_em=datetime.now(timezone.utc),
        )

    @classmethod
    def avaliar_valores(
        cls,
        valor: int,
        local_da_dor: str | None = None,
        cns: str | None = None,
        cpf: str | None = None,
    ) -> ResultadoEVA:
        """Avaliação a partir de valores crus, com erros em português.

        Raises:
            DadosClinicosInvalidosError: Se o valor estiver fora de 0–10.
        """
        try:
            entrada = EntradaEVA(valor=valor, local_da_dor=local_da_dor, cns=cns, cpf=cpf)
        except ValidationError as erro:
            raise DadosClinicosInvalidosError(
                f"Dados inválidos para a EVA: {erro}"
            ) from erro
        return cls().avaliar(entrada)


# ---------------------------------------------------------------------------
# Testes embutidos (asserts no estilo pytest) — executáveis via __main__
# ---------------------------------------------------------------------------


def test_glasgow_escores_extremos() -> None:
    """E4 V5 M6 → 15 (normal) e E1 V1 M1 → 3 (TCE grave)."""
    escala = EscalaGlasgow()
    maximo = EntradaGlasgow(
        abertura_ocular=AberturaOcular.ESPONTANEA,
        resposta_verbal=RespostaVerbal.ORIENTADA,
        resposta_motora=RespostaMotora.OBEDECE_COMANDOS,
    )
    minimo = EntradaGlasgow(
        abertura_ocular=AberturaOcular.NENHUMA,
        resposta_verbal=RespostaVerbal.NENHUMA,
        resposta_motora=RespostaMotora.NENHUMA,
    )
    assert escala.pontuar(maximo) == 15
    assert escala.classificar(15) is GravidadeGlasgow.NORMAL
    assert escala.pontuar(minimo) == 3
    assert escala.classificar(3) is GravidadeGlasgow.GRAVE


def test_glasgow_limiares_de_classificacao() -> None:
    """Fronteiras do estadiamento: 15/14/13/12/9/8/3 pertencem às faixas corretas."""
    escala = EscalaGlasgow()
    casos = [
        (15, GravidadeGlasgow.NORMAL),
        (14, GravidadeGlasgow.LEVE),
        (13, GravidadeGlasgow.LEVE),
        (12, GravidadeGlasgow.MODERADO),
        (9, GravidadeGlasgow.MODERADO),
        (8, GravidadeGlasgow.GRAVE),
        (3, GravidadeGlasgow.GRAVE),
    ]
    for escore, esperado in casos:
        assert escala.classificar(escore) is esperado, f"GCS {escore} → {esperado.value}"


def test_glasgow_tce_grave_consolidado() -> None:
    """E2 V2 M4 → 8 (grave): conduta menciona SAMU-192 e resumo SOAP completo."""
    escala = EscalaGlasgow()
    resultado = escala.avaliar(
        EntradaGlasgow(
            abertura_ocular=AberturaOcular.A_DOR,
            resposta_verbal=RespostaVerbal.SONS_INCOMPREENSIVEIS,
            resposta_motora=RespostaMotora.FLEXAO_RETIRADA,
            cns="110433218196000",
        )
    )
    assert resultado.escore_total == 8
    assert resultado.classificacao is GravidadeGlasgow.GRAVE
    assert "SAMU-192" in resultado.conduta_sus
    assert "intubação orotraqueal" in resultado.conduta_sus
    assert resultado.codigo_cid10 == "S06.9" and resultado.codigo_ciap2 == "A80"
    assert "GCS 8/15" in resultado.resumo_soap and "E2 V2 M4" in resultado.resumo_soap
    assert resultado.cns == "110433218196000"


def test_glasgow_sedado_gera_observacao() -> None:
    """Cidadão sedado gera observação orientando registro do fator 'S'."""
    resultado = EscalaGlasgow().avaliar(
        EntradaGlasgow(
            abertura_ocular=AberturaOcular.NENHUMA,
            resposta_verbal=RespostaVerbal.NENHUMA,
            resposta_motora=RespostaMotora.NENHUMA,
            sedado=True,
        )
    )
    assert any("'S'" in observacao for observacao in resultado.observacoes)


def test_glasgow_validacao_estrita() -> None:
    """Tipagem estrita (Pydantic v2) e domínio do escore devem ser respeitados."""
    try:
        EntradaGlasgow.model_validate(
            {
                "abertura_ocular": 2,
                "resposta_verbal": RespostaVerbal.CONFUSA,
                "resposta_motora": RespostaMotora.OBEDECE_COMANDOS,
                "campo_extra": True,
            }
        )
        raise AssertionError("deveria recusar valor bruto e campo extra")
    except ValidationError:
        pass
    try:
        EscalaGlasgow().classificar(16)
        raise AssertionError("deveria recusar escore > 15")
    except DadosClinicosInvalidosError:
        pass
    try:
        EscalaGlasgow.avaliar_valores(
            abertura_ocular=AberturaOcular.ESPONTANEA,
            resposta_verbal=RespostaVerbal.ORIENTADA,
            resposta_motora=RespostaMotora.OBEDECE_COMANDOS,
            cpf="123",
        )
        raise AssertionError("deveria recusar CPF malformado")
    except DadosClinicosInvalidosError:
        pass


def test_mews_limiares_pressao_sistolica() -> None:
    """Fronteiras da pontuação da PA sistólica: 70/71/80/81/100/101/199/200."""
    for pas, esperado in [
        (70, 3),
        (71, 2),
        (80, 2),
        (81, 1),
        (100, 1),
        (101, 0),
        (199, 0),
        (200, 2),
    ]:
        assert EscalaMEWS._pontuar_pressao_sistolica(pas) == esperado, f"PAS {pas} → {esperado}"


def test_mews_limiares_frequencia_cardiaca() -> None:
    """Fronteiras da pontuação da FC: 39/40/50/51/100/101/110/111/129/130."""
    for fc, esperado in [
        (39, 2),
        (40, 1),
        (50, 1),
        (51, 0),
        (100, 0),
        (101, 1),
        (110, 1),
        (111, 2),
        (129, 2),
        (130, 3),
    ]:
        assert EscalaMEWS._pontuar_frequencia_cardiaca(fc) == esperado, f"FC {fc} → {esperado}"


def test_mews_limiares_frequencia_respiratoria() -> None:
    """Fronteiras da pontuação da FR: 8/9/14/15/20/21/29/30."""
    for fr, esperado in [
        (8, 2),
        (9, 0),
        (14, 0),
        (15, 1),
        (20, 1),
        (21, 2),
        (29, 2),
        (30, 3),
    ]:
        assert EscalaMEWS._pontuar_frequencia_respiratoria(fr) == esperado, f"FR {fr} → {esperado}"


def test_mews_limiares_temperatura_e_consciencia() -> None:
    """Fronteiras da temperatura (35,0/38,5) e pontuação AVPU (0–3)."""
    for temperatura, esperado in [
        (34.9, 2),
        (35.0, 0),
        (38.4, 0),
        (38.5, 2),
    ]:
        assert EscalaMEWS._pontuar_temperatura(temperatura) == esperado, f"T {temperatura} → {esperado}"
    pontos_avpu = [nivel.pontos for nivel in NivelConscienciaAVPU]
    assert pontos_avpu == [0, 1, 2, 3]


def test_mews_avaliacao_alto_risco_com_gatilhos() -> None:
    """PAS 85, FC 120, FR 26, T 39,0 e U → MEWS 10 (alto) com 3 gatilhos."""
    resultado = EscalaMEWS().avaliar(
        EntradaMEWS(
            pressao_sistolica_mmhg=85,
            frequencia_cardiaca_bpm=120,
            frequencia_respiratoria_irpm=26,
            temperatura_celsius=39.0,
            nivel_consciencia=NivelConscienciaAVPU.INCONSCIENTE,
        )
    )
    assert resultado.escore_total == 10
    assert resultado.classificacao is RiscoMEWS.ALTO
    assert "SAMU-192" in resultado.conduta_sus
    assert len(resultado.gatilhos_individuais) == 3
    assert "MEWS 10/14" in resultado.resumo_soap
    assert resultado.escore_maximo == 14


def test_mews_componente_omitido_conta_zero() -> None:
    """FR não informada pontua 0, gera observação e reduz o escore máximo."""
    resultado = EscalaMEWS().avaliar(
        EntradaMEWS(
            pressao_sistolica_mmhg=120,
            frequencia_cardiaca_bpm=80,
            temperatura_celsius=36.5,
            nivel_consciencia=NivelConscienciaAVPU.ALERTA,
        )
    )
    fr = next(c for c in resultado.detalhamento if "respirat" in c.componente.lower())
    assert fr.pontos == 0 and fr.observacao is not None
    assert resultado.escore_total == 0
    assert resultado.escore_maximo == 11
    assert any("subestimado" in observacao for observacao in resultado.observacoes)


def test_mews_risco_baixo_sem_gatilhos() -> None:
    """Sinais vitais normais → MEWS 0 (baixo) sem gatilho individual."""
    resultado = EscalaMEWS().avaliar(
        EntradaMEWS(
            pressao_sistolica_mmhg=120,
            frequencia_cardiaca_bpm=80,
            frequencia_respiratoria_irpm=14,
            temperatura_celsius=36.5,
            nivel_consciencia=NivelConscienciaAVPU.ALERTA,
        )
    )
    assert resultado.escore_total == 0
    assert resultado.classificacao is RiscoMEWS.BAIXO
    assert resultado.gatilhos_individuais == ()


def test_mews_risco_moderado_e_temperatura_inteira() -> None:
    """PAS 100, FC 105, FR 18 e T 37 (inteiro aceito) → MEWS 3 (moderado)."""
    resultado = EscalaMEWS.avaliar_valores(
        pressao_sistolica_mmhg=100,
        frequencia_cardiaca_bpm=105,
        frequencia_respiratoria_irpm=18,
        temperatura_celsius=37,
        nivel_consciencia=NivelConscienciaAVPU.ALERTA,
    )
    assert resultado.escore_total == 3
    assert resultado.classificacao is RiscoMEWS.MODERADO
    assert resultado.reavaliacao.startswith("A cada 4–6 horas")


def test_mews_validacao_estrita() -> None:
    """Limites clínicos e tipagem estrita (Pydantic v2) devem ser respeitados."""
    casos_invalidos = [
        dict(pressao_sistolica_mmhg=20),
        dict(frequencia_cardiaca_bpm="80"),
        dict(temperatura_celsius=50.0),
        dict(campo_extra=1),
        dict(nivel_consciencia="alerta"),
    ]
    for caso in casos_invalidos:
        try:
            EntradaMEWS.model_validate(caso)
            raise AssertionError(f"deveria recusar {caso}")
        except ValidationError:
            pass
    try:
        EscalaMEWS().classificar(15)
        raise AssertionError("deveria recusar escore > 14")
    except DadosClinicosInvalidosError:
        pass


def test_eva_faixas_de_classificacao() -> None:
    """Fronteiras da EVA: 0/1/3/4/6/7/8/9/10 pertencem às faixas corretas."""
    escala = EscalaVisualAnalogaDor()
    casos = [
        (0, IntensidadeDor.SEM_DOR),
        (1, IntensidadeDor.LEVE),
        (3, IntensidadeDor.LEVE),
        (4, IntensidadeDor.MODERADA),
        (6, IntensidadeDor.MODERADA),
        (7, IntensidadeDor.INTENSA),
        (8, IntensidadeDor.INTENSA),
        (9, IntensidadeDor.MUITO_INTENSA),
        (10, IntensidadeDor.MUITO_INTENSA),
    ]
    for valor, esperado in casos:
        assert escala.classificar(valor) is esperado, f"EVA {valor} → {esperado.value}"


def test_eva_escalonamento_analgesico_por_degrau() -> None:
    """Cada faixa sugere o degrau analgésico correspondente (CEME/RENAME)."""
    escala = EscalaVisualAnalogaDor()
    leve = escala.avaliar(EntradaEVA(valor=2))
    moderada = escala.avaliar(EntradaEVA(valor=5))
    intensa = escala.avaliar(EntradaEVA(valor=7))
    muito_intensa = escala.avaliar(EntradaEVA(valor=10))
    assert "Degrau I" in leve.analgesia_sugerida and "dipirona" in leve.analgesia_sugerida
    assert "Degrau II" in moderada.analgesia_sugerida and "AINE" in moderada.analgesia_sugerida
    assert "Degrau III" in intensa.analgesia_sugerida and "tramadol" in intensa.analgesia_sugerida
    assert "opioide forte" in muito_intensa.analgesia_sugerida.lower()
    assert "SAMU-192" in muito_intensa.conduta_sus


def test_eva_atencao_imediata_e_codigos() -> None:
    """EVA 10 sinaliza atenção imediata; EVA 5 não; codificação R52/A01."""
    escala = EscalaVisualAnalogaDor()
    emergencia = escala.avaliar(EntradaEVA(valor=10))
    moderada = escala.avaliar(EntradaEVA(valor=5))
    assert emergencia.exige_atencao_imediata is True
    assert moderada.exige_atencao_imediata is False
    assert moderada.codigo_cid10 == "R52" and moderada.codigo_ciap2 == "A01"


def test_eva_local_da_dor_e_resumo_soap() -> None:
    """Local da dor entra no resumo SOAP e orienta o refino do CIAP-2."""
    resultado = EscalaVisualAnalogaDor().avaliar(
        EntradaEVA(valor=5, local_da_dor="lombar", cpf="529.982.247-25")
    )
    assert "EVA 5/10" in resultado.resumo_soap
    assert "local: lombar" in resultado.resumo_soap
    assert any("CIAP-2" in observacao for observacao in resultado.observacoes)


def test_eva_validacao_de_valor() -> None:
    """Valores fora de 0–10 devem ser recusados com erro de domínio."""
    try:
        EntradaEVA(valor=11)
        raise AssertionError("deveria recusar EVA 11")
    except ValidationError:
        pass
    try:
        EscalaVisualAnalogaDor.avaliar_valores(valor=-1)
        raise AssertionError("deveria recusar EVA -1")
    except DadosClinicosInvalidosError:
        pass


def test_resultados_sao_imutaveis() -> None:
    """Os três resultados são frozen: alteração deve falhar."""
    glasgow = EscalaGlasgow().avaliar(
        EntradaGlasgow(
            abertura_ocular=AberturaOcular.ESPONTANEA,
            resposta_verbal=RespostaVerbal.ORIENTADA,
            resposta_motora=RespostaMotora.OBEDECE_COMANDOS,
        )
    )
    mews = EscalaMEWS().avaliar(EntradaMEWS(pressao_sistolica_mmhg=110))
    eva = EscalaVisualAnalogaDor().avaliar(EntradaEVA(valor=3))
    for resultado, campo in (
        (glasgow, "escore_total"),
        (mews, "escore_total"),
        (eva, "valor"),
    ):
        try:
            setattr(resultado, campo, 999)  # type: ignore[misc]
            raise AssertionError(f"deveria recusar alteração em {type(resultado).__name__}")
        except ValidationError:
            pass


def test_cpf_normalizado_em_todas_as_entradas() -> None:
    """CPF pontuado deve ser normalizado para 11 dígitos em todas as escalas."""
    assert (
        EntradaGlasgow(
            abertura_ocular=AberturaOcular.ESPONTANEA,
            resposta_verbal=RespostaVerbal.ORIENTADA,
            resposta_motora=RespostaMotora.OBEDECE_COMANDOS,
            cpf="529.982.247-25",
        ).cpf
        == "52998224725"
    )
    assert EntradaMEWS(cpf="529.982.247-25").cpf == "52998224725"
    assert EntradaEVA(valor=0, cpf="529.982.247-25").cpf == "52998224725"


if __name__ == "__main__":
    testes_disponiveis = [
        test_glasgow_escores_extremos,
        test_glasgow_limiares_de_classificacao,
        test_glasgow_tce_grave_consolidado,
        test_glasgow_sedado_gera_observacao,
        test_glasgow_validacao_estrita,
        test_mews_limiares_pressao_sistolica,
        test_mews_limiares_frequencia_cardiaca,
        test_mews_limiares_frequencia_respiratoria,
        test_mews_limiares_temperatura_e_consciencia,
        test_mews_avaliacao_alto_risco_com_gatilhos,
        test_mews_componente_omitido_conta_zero,
        test_mews_risco_baixo_sem_gatilhos,
        test_mews_risco_moderado_e_temperatura_inteira,
        test_mews_validacao_estrita,
        test_eva_faixas_de_classificacao,
        test_eva_escalonamento_analgesico_por_degrau,
        test_eva_atencao_imediata_e_codigos,
        test_eva_local_da_dor_e_resumo_soap,
        test_eva_validacao_de_valor,
        test_resultados_sao_imutaveis,
        test_cpf_normalizado_em_todas_as_entradas,
    ]
    falhas = 0
    for teste in testes_disponiveis:
        try:
            teste()
            print(f"[OK] {teste.__name__}")
        except AssertionError as erro:
            falhas += 1
            print(f"[FALHA] {teste.__name__}: {erro}")
    if falhas:
        raise SystemExit(f"{falhas} teste(s) falharam.")
    print(f"\n{len(testes_disponiveis)} teste(s) executado(s) com sucesso.")
