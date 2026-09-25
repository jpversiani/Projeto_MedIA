"""Serviço de cálculo renal do Projeto MedIA (SUS / Atenção Primária à Saúde).

Implementa:

- **TFGe pela equação CKD-EPI 2021** (Inker et al., NEJM 2021), sem a variável
  raça, utilizando creatinina sérica, idade e sexo biológico;
- **Classificação em estágios da Doença Renal Crônica (DRC)** de G1 a G5
  conforme a diretriz KDIGO (Kidney Disease: Improving Global Outcomes);
- **Ajuste de dose de medicamentos por estágio renal** (metformina, IECA e
  vancomicina), com orientações alinhadas aos PCDT e à RENAME/SUS;
- **Alertas de nefrotoxicidade** para apoiar a prescrição segura na APS.

Padrões SUS/APS adotados:

- CID-10 (N18.1 a N18.5 para os estágios da DRC, conforme DATASUS);
- CIAP-2 (U13 — insuficiência renal, para o registro na APS);
- Documentação clínica no método SOAP (o laudo retorna o "P" — plano);
- Identificação do paciente por CNS (validado pelo algoritmo oficial do
  DATASUS) ou CPF (dígitos verificadores módulo 11).

Referências:

- Inker LA, Eneanya ND, Coresh J, et al. New creatinine- and cystatin
  C-based equations to estimate GFR without race. N Engl J Med.
  2021;385(19):1737-1749.
- KDIGO. CKD Work Group. KDIGO 2024 Clinical Practice Guideline for the
  Evaluation and Management of Chronic Kidney Disease. Kidney Int.
  2024;105(4S):S117-S314.
- Ministério da Saúde. Formulário Terapêutico Nacional / RENAME;
  Protocolos da atenção primária à saúde (e-Multi).
- Manual de Integração do Cartão Nacional de Saúde — Ministério da
  Saúde / DATASUS (validação do CNS).

Limitações: ferramenta de apoio à decisão clínica — não substitui a
avaliação médica, a bula dos medicamentos nem os protocolos do serviço.
A equação CKD-EPI 2021 é validada para adultos (≥ 18 anos).
"""

from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from typing import Callable, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Constantes e enumerações
# ---------------------------------------------------------------------------


class Sexo(StrEnum):
    """Sexo biológico registrado (parâmetro da equação CKD-EPI 2021)."""

    MASCULINO = "M"
    FEMININO = "F"


class EstagioDRC(StrEnum):
    """Estágios da Doença Renal Crônica segundo KDIGO (2012/2024)."""

    G1 = "G1"
    G2 = "G2"
    G3A = "G3a"
    G3B = "G3b"
    G4 = "G4"
    G5 = "G5"


class GravidadeAlerta(StrEnum):
    """Níveis de gravidade dos alertas clínicos gerados pelo serviço."""

    INFORMATIVO = "informativo"
    ATENCAO = "atencao"
    CRITICO = "critico"


class Medicamento(StrEnum):
    """Medicamentos suportados para ajuste de dose por função renal."""

    METFORMINA = "metformina"
    IECA = "ieca"
    VANCOMICINA = "vancomicina"


# Constantes da equação CKD-EPI 2021 (Inker et al., NEJM 2021), sem variável raça.
#: κ (limiar de creatinina), α (expoente para Scr ≤ κ) e fator sexual por sexo.
_CKD_EPI_2021: Final[dict[Sexo, dict[str, float]]] = {
    Sexo.FEMININO: {"k": 0.7, "alpha": -0.241, "fator_sexo": 1.012},
    Sexo.MASCULINO: {"k": 0.9, "alpha": -0.302, "fator_sexo": 1.0},
}

#: Expoente de creatinina aplicado quando Scr > κ (comum a ambos os sexos).
_CKD_EPI_ALPHA_ACIMA_K: Final[float] = -1.200

#: Fator de decaimento da idade (por ano).
_CKD_EPI_FATOR_IDADE: Final[float] = 0.9938

#: Coeficiente base da equação CKD-EPI 2021.
_CKD_EPI_COEFICIENTE: Final[float] = 142.0

#: Limites de idade válidos para aplicação da equação (adultos).
_IDADE_MINIMA: Final[int] = 18
_IDADE_MAXIMA: Final[int] = 120

#: Arredondamento oficial de TFGe em mL/min/1,73 m² (uma casa decimal).
_CASAS_TFGE: Final[Decimal] = Decimal("0.1")

#: Limites clínicos de creatinina sérica (mg/dL) aceitáveis para cálculo.
_CREATININA_MINIMA: Final[float] = 0.1
_CREATININA_MAXIMA: Final[float] = 30.0

#: CID-10 por estágio da DRC, conforme a CID-10 oficial do SUS/DATASUS
#: (N18.3 contempla o estágio 3, incluindo as subdivisões clínicas G3a/G3b).
_CID10_POR_ESTAGIO: Final[dict[EstagioDRC, str]] = {
    EstagioDRC.G1: "N18.1",
    EstagioDRC.G2: "N18.2",
    EstagioDRC.G3A: "N18.3",
    EstagioDRC.G3B: "N18.3",
    EstagioDRC.G4: "N18.4",
    EstagioDRC.G5: "N18.5",
}

#: CIAP-2 para registro na APS (U13 — insuficiência renal).
_CIAP2_RENAL: Final[str] = "U13"

# ---------------------------------------------------------------------------
# Modelos de entrada e saída (Pydantic v2)
# ---------------------------------------------------------------------------


class EntradaTFGe(BaseModel):
    """Dados de entrada para o cálculo da TFGe (CKD-EPI 2021)."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    creatinina_mg_dl: float = Field(
        ...,
        gt=_CREATININA_MINIMA,
        le=_CREATININA_MAXIMA,
        description="Creatinina sérica em mg/dL.",
    )
    idade_anos: int = Field(
        ...,
        ge=_IDADE_MINIMA,
        le=_IDADE_MAXIMA,
        description="Idade do paciente em anos completos (adultos).",
    )
    sexo: Sexo = Field(..., description="Sexo biológico: 'M' masculino ou 'F' feminino.")

    @field_validator("creatinina_mg_dl")
    @classmethod
    def validar_creatinina(cls, valor: float) -> float:
        """Garante creatinina com precisão razoável e coerência clínica."""
        if not math.isfinite(valor):
            raise ValueError("Creatinina sérica deve ser um número finito.")
        return round(valor, 2)


class TFGeResultado(BaseModel):
    """Resultado numérico e classificação da TFGe."""

    model_config = ConfigDict(frozen=True)

    tfge_ml_min_173m2: float = Field(
        ..., description="TFGe em mL/min/1,73 m² (1 casa decimal)."
    )
    estagio: EstagioDRC = Field(..., description="Estágio KDIGO (G1 a G5).")
    cid10: str = Field(..., description="CID-10 correspondente ao estágio (N18.x).")
    ciap2: str = Field(_CIAP2_RENAL, description="Código CIAP-2 para registro na APS.")
    equacao: Literal["CKD-EPI 2021"] = Field("CKD-EPI 2021", description="Equação utilizada.")
    descritivo_estagio: str = Field(..., description="Descrição textual do estágio.")


class AjusteMedicamento(BaseModel):
    """Orientação de ajuste de dose de um medicamento conforme função renal."""

    model_config = ConfigDict(frozen=True)

    medicamento: Medicamento = Field(..., description="Medicamento avaliado.")
    pode_usar: bool = Field(..., description="Se o uso é permitido no estágio atual.")
    dose_ajustada: str = Field(..., description="Orientação de dose em texto padronizado.")
    observacao: str = Field(..., description="Observação clínica para prescrição.")


class AlertaNefrotoxicidade(BaseModel):
    """Alerta gerado quando o estágio renal contraindica ou exige cautela."""

    model_config = ConfigDict(frozen=True)

    gravidade: GravidadeAlerta = Field(..., description="Gravidade do alerta.")
    mensagem: str = Field(..., description="Mensagem clínica em Português do Brasil.")
    medicamento_relacionado: Medicamento | None = Field(
        None, description="Medicamento que motivou o alerta, quando aplicável."
    )


class LaudoRenal(BaseModel):
    """Laudo consolidado (formato SOAP) do cálculo renal."""

    model_config = ConfigDict(frozen=True)

    cns: str | None = Field(None, description="Cartão Nacional de Saúde do paciente (15 dígitos).")
    cpf: str | None = Field(None, description="CPF do paciente, se disponível.")
    resultado: TFGeResultado = Field(..., description="Resultado da TFGe e estágio.")
    ajustes: list[AjusteMedicamento] = Field(
        default_factory=list, description="Ajustes de dose por medicamento."
    )
    alertas: list[AlertaNefrotoxicidade] = Field(
        default_factory=list, description="Alertas de nefrotoxicidade."
    )
    plano: str = Field(..., description="Plano (P do SOAP) sugerido para a APS.")

    @field_validator("cns")
    @classmethod
    def validar_cns(cls, valor: str | None) -> str | None:
        """Valida o CNS de 15 dígitos pelo algoritmo oficial do DATASUS.

        Regras (Manual de Integração do Cartão Nacional de Saúde):
        1. Deve conter exatamente 15 dígitos numéricos;
        2. Deve iniciar com 1, 2, 7, 8 ou 9 (1/2 = definitivo; 7/8/9 = provisório);
        3. Cada dígito é multiplicado pelos pesos 15, 14, ..., 1;
        4. A soma ponderada deve ser múltiplo de 11.
        """
        if valor is None:
            return None
        digitos = "".join(c for c in valor if c.isdigit())
        if len(digitos) != 15 or digitos[0] not in {"1", "2", "7", "8", "9"}:
            raise ValueError(
                "CNS inválido: deve ter 15 dígitos iniciando com 1, 2, 7, 8 ou 9."
            )
        soma = sum(int(d) * w for d, w in zip(digitos, range(15, 0, -1)))
        if soma % 11 != 0:
            raise ValueError("CNS inválido: dígito verificador não confere.")
        return digitos


# ---------------------------------------------------------------------------
# Serviço principal
# ---------------------------------------------------------------------------


class CalculadoraRenal:
    """Calculadora de TFGe (CKD-EPI 2021) e gestão renal para a APS/SUS."""

    #: Faixas de TFGe (mL/min/1,73 m²) que delimitam os estágios KDIGO.
    _FAIXAS_ESTAGIO: Final[list[tuple[float, EstagioDRC, str]]] = [
        (
            90.0,
            EstagioDRC.G1,
            "TFGe normal ou aumentada - DRC apenas se houver marcador de lesão renal.",
        ),
        (60.0, EstagioDRC.G2, "Redução levemente diminuída da TFGe."),
        (45.0, EstagioDRC.G3A, "Redução leve a moderada da TFGe."),
        (30.0, EstagioDRC.G3B, "Redução moderada a grave da TFGe."),
        (15.0, EstagioDRC.G4, "Redução grave da TFGe - preparar terapia renal substitutiva."),
        (-math.inf, EstagioDRC.G5, "Falência renal - indicar diálise ou transplante."),
    ]

    def calcular_tfge(self, entrada: EntradaTFGe) -> TFGeResultado:
        """Calcula a TFGe pela equação CKD-EPI 2021 e classifica o estágio KDIGO.

        Equação (Inker et al., NEJM 2021), sem variável de raça::

            TFGe = 142 × min(Scr/κ, 1)^α × max(Scr/κ, 1)^−1,200
                   × 0,9938^idade × 1,012 (se sexo feminino)

        onde κ = 0,7 (feminino) ou 0,9 (masculino);
        α = −0,241 (feminino) ou −0,302 (masculino).
        """
        params = _CKD_EPI_2021[entrada.sexo]
        razao_scr_k = entrada.creatinina_mg_dl / params["k"]

        tfge_bruta = (
            _CKD_EPI_COEFICIENTE
            * min(razao_scr_k, 1.0) ** params["alpha"]
            * max(razao_scr_k, 1.0) ** _CKD_EPI_ALPHA_ACIMA_K
            * _CKD_EPI_FATOR_IDADE ** entrada.idade_anos
            * params["fator_sexo"]
        )
        tfge_arredondada = float(
            Decimal(str(tfge_bruta)).quantize(_CASAS_TFGE, rounding=ROUND_HALF_UP)
        )
        # Em estágios G5, padroniza qualquer valor residual para o piso do estágio.
        tfge_final = max(tfge_arredondada, 0.0)

        estagio, descritivo = self._classificar_estagio(tfge_final)
        return TFGeResultado(
            tfge_ml_min_173m2=tfge_final,
            estagio=estagio,
            cid10=_CID10_POR_ESTAGIO[estagio],
            descritivo_estagio=descritivo,
        )

    def _classificar_estagio(self, tfge: float) -> tuple[EstagioDRC, str]:
        """Classifica o estágio KDIGO conforme a faixa de TFGe informada."""
        for limite, estagio, descritivo in self._FAIXAS_ESTAGIO:
            if tfge >= limite:
                return estagio, descritivo
        return EstagioDRC.G5, self._FAIXAS_ESTAGIO[-1][2]

    # ------------------------------------------------------------------
    # Ajuste de medicamentos por estágio
    # ------------------------------------------------------------------

    def ajustar_medicamento(
        self,
        medicamento: Medicamento,
        resultado: TFGeResultado,
    ) -> AjusteMedicamento:
        """Retorna a orientação de dose do medicamento conforme o estágio da DRC."""
        despachos: dict[Medicamento, Callable[[EstagioDRC], AjusteMedicamento]] = {
            Medicamento.METFORMINA: self._ajuste_metformina,
            Medicamento.IECA: self._ajuste_ieca,
            Medicamento.VANCOMICINA: self._ajuste_vancomicina,
        }
        return despachos[medicamento](resultado.estagio)

    def _ajuste_metformina(self, estagio: EstagioDRC) -> AjusteMedicamento:
        """Metformina: contraindicada < 30; reduzir dose e monitorar entre 30-45."""
        if estagio in {EstagioDRC.G4, EstagioDRC.G5}:
            return AjusteMedicamento(
                medicamento=Medicamento.METFORMINA,
                pode_usar=False,
                dose_ajustada="Não utilizar.",
                observacao=(
                    "Metformina contraindicada para TFGe < 30 mL/min/1,73 m² "
                    "(risco de acidose láctica). Considerar alternativa (ex.: DPP-4, SGLT2)."
                ),
            )
        if estagio in {EstagioDRC.G3A, EstagioDRC.G3B}:
            return AjusteMedicamento(
                medicamento=Medicamento.METFORMINA,
                pode_usar=True,
                dose_ajustada="Máximo 1.000 mg/dia (ex.: 500 mg 2x/dia), com refeições.",
                observacao=(
                    "TFGe 30-44: reduzir dose para no máximo 1.000 mg/dia e "
                    "reavaliar função renal a cada 3 meses. Não iniciar em TFGe < 45."
                ),
            )
        return AjusteMedicamento(
            medicamento=Medicamento.METFORMINA,
            pode_usar=True,
            dose_ajustada="Dose usual: 1.500-2.000 mg/dia, conforme resposta glicêmica.",
            observacao="TFGe ≥ 45: dose habitual do Componente Básico da Farmácia Popular/SUS.",
        )

    def _ajuste_ieca(self, estagio: EstagioDRC) -> AjusteMedicamento:
        """IECA: usar com titulação e monitoramento de potássio/creatinina na DRC."""
        if estagio in {EstagioDRC.G4, EstagioDRC.G5}:
            return AjusteMedicamento(
                medicamento=Medicamento.IECA,
                pode_usar=True,
                dose_ajustada="Dose reduzida com titulação cautelosa; exemplo: enalapril 2,5 mg 1x/dia.",
                observacao=(
                    "TFGe < 30: iniciar com a menor dose, monitorar potássio e creatinina em 1-2 semanas. "
                    "Evitar associação com espironolactona em TFGe < 30 sem nefrologia."
                ),
            )
        if estagio in {EstagioDRC.G3A, EstagioDRC.G3B}:
            return AjusteMedicamento(
                medicamento=Medicamento.IECA,
                pode_usar=True,
                dose_ajustada="Dose inicial reduzida (ex.: enalapril 5 mg 1x/dia ou lisinopril 5-10 mg/dia).",
                observacao=(
                    "TFGe 30-59: titular até dose-alvo tolerada; checar potássio e creatinina "
                    "em 2-4 semanas após início ou aumento de dose."
                ),
            )
        return AjusteMedicamento(
            medicamento=Medicamento.IECA,
            pode_usar=True,
            dose_ajustada="Dose usual conforme indicação (HAS/DM/IC), titulada até dose-alvo.",
            observacao="TFGe ≥ 60: monitorar creatinina e potássio perante rotina da APS.",
        )

    def _ajuste_vancomicina(self, estagio: EstagioDRC) -> AjusteMedicamento:
        """Vancomicina: exige ajuste/monitoramento em qualquer redução de TFGe."""
        if estagio in {EstagioDRC.G4, EstagioDRC.G5}:
            return AjusteMedicamento(
                medicamento=Medicamento.VANCOMICINA,
                pode_usar=True,
                dose_ajustada=(
                    "Ajuste individualizado por farmacocinética/nefrologia: "
                    "ex. dose de manutenção prolongada (24-48 h) guiada por taxa de filtração."
                ),
                observacao=(
                    "TFGe < 30: dosagem guiada por nível sérico (área sob a curva) e avaliação nefrológica. "
                    "Alta nefrotoxicidade combinada com outros fármacos."
                ),
            )
        if estagio in {EstagioDRC.G3A, EstagioDRC.G3B}:
            return AjusteMedicamento(
                medicamento=Medicamento.VANCOMICINA,
                pode_usar=True,
                dose_ajustada="Intervalo estendido: 15-20 mg/kg a cada 24-48 h, guiado por nível sérico.",
                observacao=(
                    "TFGe 30-59: monitorar nível sérico pré-4ª dose e função renal a cada 48-72 h."
                ),
            )
        if estagio in {EstagioDRC.G2}:
            return AjusteMedicamento(
                medicamento=Medicamento.VANCOMICINA,
                pode_usar=True,
                dose_ajustada="15-20 mg/kg a cada 12-24 h, conforme nível sérico alvo.",
                observacao="TFGe 60-89: monitorar nível sérico em terapia prolongada (> 72 h).",
            )
        return AjusteMedicamento(
            medicamento=Medicamento.VANCOMICINA,
            pode_usar=True,
            dose_ajustada="Dose usual: 15-20 mg/kg a cada 8-12 h (dose de ataque 25-30 mg/kg).",
            observacao="TFGe ≥ 90: monitorar nível sérico (ASC/MIC) conforme protocolo institucional.",
        )

    # ------------------------------------------------------------------
    # Alertas de nefrotoxicidade
    # ------------------------------------------------------------------

    def alerta_nefrotoxicidade(self, resultado: TFGeResultado) -> list[AlertaNefrotoxicidade]:
        """Gera alertas de nefrotoxicidade conforme o estágio renal identificado."""
        alertas: list[AlertaNefrotoxicidade] = []
        estagio = resultado.estagio

        if estagio in {EstagioDRC.G3A, EstagioDRC.G3B, EstagioDRC.G4, EstagioDRC.G5}:
            alertas.append(
                AlertaNefrotoxicidade(
                    gravidade=GravidadeAlerta.ATENCAO,
                    medicamento_relacionado=None,
                    mensagem=(
                        "Evitar anti-inflamatórios não esteroides (AINEs), contraste iodado "
                        "desnecessário e aminoglicosídeos; revisar todos os medicamentos em uso "
                        f"({resultado.cid10} - {estagio.value})."
                    ),
                )
            )

        if estagio in {EstagioDRC.G4, EstagioDRC.G5}:
            alertas.append(
                AlertaNefrotoxicidade(
                    gravidade=GravidadeAlerta.CRITICO,
                    medicamento_relacionado=Medicamento.METFORMINA,
                    mensagem=(
                        "Metformina contraindicada (risco de acidose láctica); suspender e "
                        "encaminhar avaliação nefrológica para terapia renal substitutiva."
                    ),
                )
            )
            alertas.append(
                AlertaNefrotoxicidade(
                    gravidade=GravidadeAlerta.CRITICO,
                    medicamento_relacionado=Medicamento.VANCOMICINA,
                    mensagem=(
                        "Vancomicina exige dosagem guiada por nível sérico e ajuste por "
                        "farmacocinética; risco elevado de nefrotoxicidade adicional."
                    ),
                )
            )

        if estagio == EstagioDRC.G5:
            alertas.insert(
                0,
                AlertaNefrotoxicidade(
                    gravidade=GravidadeAlerta.CRITICO,
                    medicamento_relacionado=None,
                    mensagem=(
                        "Falência renal (TFGe < 15): qualquer fármaco eliminado renalmente "
                        "requer reavaliação de dose; priorizar referência à nefrologia no SUS."
                    ),
                ),
            )

        return alertas

    # ------------------------------------------------------------------
    # Laudo consolidado (SOAP)
    # ------------------------------------------------------------------

    def gerar_laudo(
        self,
        entrada: EntradaTFGe,
        medicamentos: list[Medicamento] | None = None,
        *,
        cns: str | None = None,
        cpf: str | None = None,
    ) -> LaudoRenal:
        """Gera o laudo renal completo no formato SOAP (S - dados, A - estágio, P - plano).

        Parâmetros:
            entrada: dados clínicos (creatinina, idade, sexo).
            medicamentos: lista de medicamentos para ajuste de dose.
            cns: Cartão Nacional de Saúde (opcional, validado).
            cpf: CPF do paciente (opcional).

        Retorna:
            LaudoRenal com resultado, ajustes, alertas e plano sugerido.
        """
        cpf_digital = self._validar_cpf(cpf)
        resultado = self.calcular_tfge(entrada)

        ajustes = (
            [self.ajustar_medicamento(med, resultado) for med in medicamentos]
            if medicamentos
            else []
        )
        alertas = self.alerta_nefrotoxicidade(resultado)

        bloqueados = [a.medicamento.value for a in ajustes if not a.pode_usar]
        frase_bloqueio = f" Suspender/evitar: {', '.join(bloqueados)}." if bloqueados else ""
        plano = (
            f"Registro na APS: {resultado.ciap2} / {resultado.cid10} ({resultado.estagio.value}). "
            f"TFGe {resultado.tfge_ml_min_173m2} mL/min/1,73 m². "
            f"{resultado.descritivo_estagio} "
            "Monitorar creatinina, potássio e proteinúria (RAC) conforme periodicidade do estágio."
            f"{frase_bloqueio} "
            "Educação em saúde: hidratação, controle de HAS/DM e revisão de nefrotóxicos."
        )

        return LaudoRenal(
            cns=cns,
            cpf=cpf_digital,
            resultado=resultado,
            ajustes=ajustes,
            alertas=alertas,
            plano=plano,
        )

    @staticmethod
    def _validar_cpf(cpf: str | None) -> str | None:
        """Valida CPF (11 dígitos com dígitos verificadores módulo 11)."""
        if cpf is None:
            return None
        digitos = "".join(c for c in cpf if c.isdigit())
        if len(digitos) != 11 or digitos == digitos[0] * 11:
            raise ValueError("CPF inválido: deve ter 11 dígitos distintos.")
        for offset in (9, 10):
            peso = range(offset + 1, 1, -1)
            soma = sum(int(d) * w for d, w in zip(digitos[:offset], peso))
            dv_calculado = (soma * 10) % 11 % 10
            if dv_calculado != int(digitos[offset]):
                raise ValueError("CPF inválido: dígitos verificadores não conferem.")
        return digitos


__all__ = [
    "AlertaNefrotoxicidade",
    "AjusteMedicamento",
    "CalculadoraRenal",
    "EntradaTFGe",
    "EstagioDRC",
    "GravidadeAlerta",
    "LaudoRenal",
    "Medicamento",
    "Sexo",
    "TFGeResultado",
]
