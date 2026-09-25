"""Motor de Inferência de Risco Clínico — Manchester Adaptado (C3)

Módulo para classificação de risco para APS:
- Avaliação de sinais vitais extremos
- Queixas sentinelas (dor torácica, dispneia grave)
- Atribuição de prioridades (Vermelho, Laranja, Amarelo, Verde, Azul)

Segue padrões SUS/APS:
- CIAP-2, CID-10
- Método SOAP
- Identificação por CNS/CPF
- Validação de dados com Pydantic v2
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.validadores import normalizar_cns, normalizar_cpf

__all__ = [
    "NivelRisco",
    "QueixaSentinela",
    "CaracteristicasDorToracica",
    "CaracteristicasDispneia",
    "SinaisVitais",
    "PacienteTriagem",
    "ResultadoTriagem",
    "evaluate_extreme_vitals",
    "evaluate_sentinel_complaints",
    "assign_priority_level",
]


class NivelRisco(str, Enum):
    VERMELHO = "VERMELHO"
    LARANJA = "LARANJA"
    AMARELO = "AMARELO"
    VERDE = "VERDE"
    AZUL = "AZUL"

    @property
    def peso_ordem(self) -> int:
        """Peso ordinal para ordenação (VERMELHO = 1, AZUL = 5)."""
        return {
            self.VERMELHO: 1,
            self.LARANJA: 2,
            self.AMARELO: 3,
            self.VERDE: 4,
            self.AZUL: 5,
        }[self]

    @property
    def tempo_maximo_espera_min(self) -> int:
        """Tempo máximo de espera em minutos (Verde: 120, Azul: 240, outros: 60)."""
        if self == NivelRisco.VERDE:
            return 120
        if self == NivelRisco.AZUL:
            return 240
        return 60

    @property
    def condicao_sus(self) -> str:
        """Conduta recomendada no SUS conforme o nível de risco."""
        if self == NivelRisco.VERMELHO:
            return (
                "EMERGÊNCIA: avaliação médica imediata; acionar o SAMU-192; "
                "referenciar à porta de emergência hospitalar pela regulação estadual (SISREG)."
            )
        if self == NivelRisco.LARANJA:
            return (
                "URGÊNCIA: avaliação médica em até 10 minutos; monitorização contínua; "
                "solicitar regulação quando indicado."
            )
        if self == NivelRisco.AMARELO:
            return (
                "URGENTE: reavaliar sinais vitais em 4–6 horas; discutir caso com médico da equipe; "
                "avaliar regulação."
            )
        if self == NivelRisco.VERDE:
            return (
                "POUCO URGENTE: proceder com a avaliação clínica de rotina na APS; "
                "registrar no prontuário (SOAP)."
            )
        return "NÃO URGENTE: agendamento normal conforme demanda da linha de cuidado."


class QueixaSentinela(str, Enum):
    """Queixas sentinelas conforme SUS/APS."""

    DOR_TORACICA = "DOR_TORACICA"
    DISPNEIA = "DISPNEIA"
    DEFICIT_NEUROLOGICO = "DEFICIT_NEUROLOGICO"
    SANGRAMENTO_GRAVE = "SANGRAMENTO_GRAVE"
    REACAO_ALERGICA = "REACAO_ALERGICA"
    CONVULSAO = "CONVULSAO"
    PERDA_CONSCIENCIA = "PERDA_CONSCIENCIA"
    FEBRE_PERSISTENTE = "FEBRE_PERSISTENTE"
    VOMITO_PERSISTENTE = "VOMITO_PERSISTENTE"
    CEFALEIA_BRUSCA = "CEFALEIA_BRUSCA"
    DOR_ABDOMINAL_INTENSA = "DOR_ABDOMINAL_INTENSA"
    GESTACAO_COMPLICACAO = "GESTACAO_COMPLICACAO"


class CaracteristicasDorToracica(BaseModel):
    """Características específicas da dor torácica."""

    model_config = ConfigDict(strict=True, frozen=True)

    em_aperto: bool = False
    irradia_braco_mandibula: bool = False
    sudorese: bool = False
    nausea: bool = False
    inicio_brusco: bool = False
    esforco: bool = False
    duracao_min: int | None = None

    @property
    def diagnostico_cid10(self) -> str:
        """Código CID-10 recomendado para estas características."""
        if self.em_aperto and self.irradia_braco_mandibula:
            return "I20"
        return "R07.2"


class CaracteristicasDispneia(BaseModel):
    """Características específicas da dispneia."""

    model_config = ConfigDict(strict=True, frozen=True)

    fala_entrecortada: bool = False
    uso_musculatura_acessoria: bool = False
    cianose: bool = False
    inicio_brusco: bool = False
    ortopneia: bool = False

    @property
    def diagnostico_cid10(self) -> str:
        """Código CID-10 recomendado para esta dispneia."""
        return "R06.02"


class SinaisVitais(BaseModel):
    """Avaliação de sinais vitais críticos (método Manchester Adapted)."""

    model_config = ConfigDict(strict=True, frozen=True)

    pa_sistolica: int | None = Field(None, ge=40, le=300, description="mmHg")
    pa_diistolica: int | None = Field(None, ge=20, le=200, description="mmHg")
    frequencia_cardiaca: int | None = Field(None, ge=0, le=300, description="bpm")
    frequencia_respiratoria: int | None = Field(None, ge=0, le=80, description="irpm")
    temperatura: float | None = Field(None, ge=30.0, le=45.0, description="°C")
    saturacao_o2: float | None = Field(None, ge=0.0, le=100.0, description="%")
    glicemia_capilar: int | None = Field(None, ge=0, le=1000, description="mg/dL")
    escala_glasgow: int | None = Field(None, ge=3, le=15)
    nivel_consciencia: Literal["A", "V", "P", "U"] | None = Field(None, description="Escala AVPU")
    escala_dor: int | None = Field(None, ge=0, le=10, description="Escala 0-10")

    @field_validator("pa_sistolica", "pa_diistolica")
    @classmethod
    def validar_relacao_pa(cls, v, info):
        """Validar que PA sistólica > PA diastólica quando ambos informados."""
        if info.data.get("pa_sistolica") is not None and v is not None:
            pa_sistolica = info.data["pa_sistolica"]
            if v >= pa_sistolica:
                raise ValueError("PA diastólica deve ser menor que PA sistólica")
        return v

    def calcular_escore_mews(self, idade_anos: int | None = None) -> int:
        """Calcular escore MEWS (Modified Early Warning Score)."""
        score = 0

        if self.pa_sistolica is not None:
            if self.pa_sistolica >= 180:
                score += 3
            elif self.pa_sistolica >= 160:
                score += 2

        if self.pa_diistolica is not None:
            if self.pa_diistolica >= 120:
                score += 3
            elif self.pa_diistolica >= 100:
                score += 2

        if self.frequencia_cardiaca is not None:
            if idade_anos is None or idade_anos >= 18:
                if self.frequencia_cardiaca >= 130:
                    score += 3
                elif self.frequencia_cardiaca >= 110:
                    score += 2
            else:
                if self.frequencia_cardiaca >= 180:
                    score += 3
                elif self.frequencia_cardiaca >= 160:
                    score += 2

        if self.frequencia_respiratoria is not None:
            if self.frequencia_respiratoria >= 30:
                score += 3
            elif self.frequencia_respiratoria >= 25:
                score += 2

        if self.temperatura is not None:
            if self.temperatura >= 40.0:
                score += 3
            elif self.temperatura >= 39.0:
                score += 2

        if self.saturacao_o2 is not None:
            if self.saturacao_o2 < 90:
                score += 3
            elif self.saturacao_o2 < 94:
                score += 2

        if self.escala_glasgow is not None:
            if self.escala_glasgow <= 8:
                score += 3
            elif self.escala_glasgow <= 12:
                score += 2

        if self.nivel_consciencia is not None and self.nivel_consciencia in ("P", "U"):
            score += 3

        if self.escala_dor is not None:
            if self.escala_dor >= 9:
                score += 3
            elif self.escala_dor >= 7:
                score += 2

        return score


class PacienteTriagem(BaseModel):
    """Paciente para triagem clínica com dados obrigatórios para avaliação de risco."""

    model_config = ConfigDict(strict=True)

    nome: str
    cns: str | None
    cpf: str | None
    idade_anos: int | None
    idade_meses: int | None
    sexo: Literal["M", "F"]
    gestante: bool = False
    sinais_vitais: SinaisVitais | None
    queixas: list[QueixaSentinela]
    caracteristicas_dor_toracica: CaracteristicasDorToracica | None = None
    caracteristicas_dispneia: CaracteristicasDispneia | None = None

    @field_validator("cns")
    @classmethod
    def normalizar_cns_validado(cls, v: str | None) -> str | None:
        return normalizar_cns(v)

    @field_validator("cpf")
    @classmethod
    def normalizar_cpf_validado(cls, v: str | None) -> str | None:
        return normalizar_cpf(v)

    @field_validator("queixas")
    @classmethod
    def validar_queixas_sentinelas(cls, v: list[QueixaSentinela]) -> list[QueixaSentinela]:
        if not v:
            raise ValueError("Pelo menos uma queixa sentinela deve ser informada")
        return v

    @property
    def idade_estruturada(self) -> str:
        """Retorna a idade estruturada para fins clínicos."""
        if self.idade_anos is None:
            return "Idade não informada"
        if self.idade_meses is None:
            return f"{self.idade_anos} ano(s)"
        return f"{self.idade_anos} ano(s), {self.idade_meses} mês(es)"

    @property
    def classificar_risco_manchester(self) -> NivelRisco:
        """Classifica o risco utilizando o método Manchester Adapted."""
        score_total = 0
        discriminadores = []

        if self.sinais_vitais:
            signos_criticos = []

            if self.sinais_vitais.pa_sistolica is not None:
                if self.sinais_vitais.pa_sistolica >= 180:
                    score_total += 3
                    signos_criticos.append("PA sistólica crítica")
                elif self.sinais_vitais.pa_sistolica >= 160:
                    score_total += 2
                    signos_criticos.append("PA sistólica elevada")

            if self.sinais_vitais.pa_diistolica is not None:
                if self.sinais_vitais.pa_diistolica >= 120:
                    score_total += 3
                    signos_criticos.append("PA diastólica crítica")
                elif self.sinais_vitais.pa_diistolica >= 100:
                    score_total += 2
                    signos_criticos.append("PA diastólica elevada")

            if self.sinais_vitais.frequencia_cardiaca is not None:
                idade = self.idade_anos or 18
                if idade >= 18:
                    if self.sinais_vitais.frequencia_cardiaca >= 130:
                        score_total += 3
                        signos_criticos.append("Taquicardia crítica")
                    elif self.sinais_vitais.frequencia_cardiaca >= 110:
                        score_total += 2
                        signos_criticos.append("Taquicardia moderada")
                else:
                    if self.sinais_vitais.frequencia_cardiaca >= 180:
                        score_total += 3
                        signos_criticos.append("Taquicardia crítica (pediátrica)")
                    elif self.sinais_vitais.frequencia_cardiaca >= 160:
                        score_total += 2
                        signos_criticos.append("Taquicardia moderada (pediátrica)")

            if self.sinais_vitais.frequencia_respiratoria is not None:
                if self.sinais_vitais.frequencia_respiratoria >= 30:
                    score_total += 3
                    signos_criticos.append("Taquipneia crítica")
                elif self.sinais_vitais.frequencia_respiratoria >= 25:
                    score_total += 2
                    signos_criticos.append("Taquipneia moderada")

            if self.sinais_vitais.temperatura is not None:
                if self.sinais_vitais.temperatura >= 40.0:
                    score_total += 3
                    signos_criticos.append("Hipertermia crítica")
                elif self.sinais_vitais.temperatura >= 39.0:
                    score_total += 2
                    signos_criticos.append("Hipertermia moderada")

            if self.sinais_vitais.saturacao_o2 is not None:
                if self.sinais_vitais.saturacao_o2 < 90:
                    score_total += 3
                    signos_criticos.append("Hipoxemia crítica")
                elif self.sinais_vitais.saturacao_o2 < 94:
                    score_total += 2
                    signos_criticos.append("Hipoxemia moderada")

            if self.sinais_vitais.escala_glasgow is not None:
                if self.sinais_vitais.escala_glasgow <= 8:
                    score_total += 3
                    signos_criticos.append("Glasgow crítico")
                elif self.sinais_vitais.escala_glasgow <= 12:
                    score_total += 2
                    signos_criticos.append("Glasgow moderado")

            if self.sinais_vitais.nivel_consciencia is not None and self.sinais_vitais.nivel_consciencia in ("P", "U"):
                score_total += 3
                signos_criticos.append("Comprometimento de consciência crítico")

            if self.sinais_vitais.escala_dor is not None:
                if self.sinais_vitais.escala_dor >= 9:
                    score_total += 3
                    signos_criticos.append("Dor intensa crítica")
                elif self.sinais_vitais.escala_dor >= 7:
                    score_total += 2
                    signos_criticos.append("Dor intensa moderada")

            discriminadores.extend(signos_criticos)

        sentinelas_criticas = []
        if QueixaSentinela.DOR_TORACICA in self.queixas:
            if self.caracteristicas_dor_toracica and (
                self.caracteristicas_dor_toracica.em_aperto
                and self.caracteristicas_dor_toracica.irradia_braco_mandibula
            ):
                score_total += 3
                sentinelas_criticas.append("Dor torácica crítica (pressão + irradiação)")
            else:
                score_total += 2
                sentinelas_criticas.append("Dor torácica presente")

        if QueixaSentinela.DISPNEIA in self.queixas:
            if self.caracteristicas_dispneia and self.caracteristicas_dispneia.fala_entrecortada:
                score_total += 3
                sentinelas_criticas.append("Dispneia crítica (fala entrecortada)")
            else:
                score_total += 2
                sentinelas_criticas.append("Dispneia presente")

        for queixa in self.queixas:
            if queixa in [
                QueixaSentinela.DEFICIT_NEUROLOGICO,
                QueixaSentinela.SANGRAMENTO_GRAVE,
                QueixaSentinela.REACAO_ALERGICA,
                QueixaSentinela.CONVULSAO,
                QueixaSentinela.PERDA_CONSCIENCIA,
                QueixaSentinela.FEBRE_PERSISTENTE,
                QueixaSentinela.VOMITO_PERSISTENTE,
                QueixaSentinela.CEFALEIA_BRUSCA,
                QueixaSentinela.DOR_ABDOMINAL_INTENSA,
                QueixaSentinela.GESTACAO_COMPLICACAO,
            ]:
                score_total += 3
                sentinelas_criticas.append(f"{queixa}")

        discriminadores.extend(sentinelas_criticas)

        if score_total >= 10:
            return NivelRisco.VERMELHO
        if score_total >= 7:
            return NivelRisco.LARANJA
        if score_total >= 5:
            return NivelRisco.AMARELO
        if score_total >= 2:
            return NivelRisco.VERDE
        return NivelRisco.AZUL

    @property
    def ciap2_recomendado(self) -> list[str]:
        """Retorna os códigos CIAP-2 recomendados com base na avaliação."""
        return self.cidap2_recomendado

    @property
    def cidap2_recomendado(self) -> list[str]:
        """Retorna os códigos CIAP-2 recomendados com base na avaliação."""
        codigos: set[str] = set()

        if QueixaSentinela.DOR_TORACICA in self.queixas:
            codigos.add("A01")
        if QueixaSentinela.DISPNEIA in self.queixas:
            codigos.add("A03")
        if QueixaSentinela.DEFICIT_NEUROLOGICO in self.queixas:
            codigos.add("A80")
        if QueixaSentinela.FEBRE_PERSISTENTE in self.queixas:
            codigos.add("A01")
        if QueixaSentinela.SANGRAMENTO_GRAVE in self.queixas:
            codigos.add("A02")
        if QueixaSentinela.REACAO_ALERGICA in self.queixas:
            codigos.add("L27")
        if QueixaSentinela.CONVULSAO in self.queixas:
            codigos.add("G40")
        if QueixaSentinela.PERDA_CONSCIENCIA in self.queixas:
            codigos.add("R40.2")

        return sorted(codigos)

    @property
    def cid10_recomendado(self) -> list[str]:
        """Retorna os códigos CID-10 recomendados com base na avaliação."""
        codigos: set[str] = set()

        if QueixaSentinela.DOR_TORACICA in self.queixas:
            if self.caracteristicas_dor_toracica:
                codigos.add(self.caracteristicas_dor_toracica.diagnostico_cid10)
            else:
                codigos.add("R07.2")

        if QueixaSentinela.DISPNEIA in self.queixas:
            if self.caracteristicas_dispneia:
                codigos.add(self.caracteristicas_dispneia.diagnostico_cid10)
            else:
                codigos.add("R06.02")

        if QueixaSentinela.DEFICIT_NEUROLOGICO in self.queixas:
            codigos.add("I63")

        if QueixaSentinela.PERDA_CONSCIENCIA in self.queixas:
            codigos.add("R40.2")

        return sorted(codigos)

    @property
    def soap_subjetivo(self) -> str:
        """Gera o campo Subjetivo do SOAP com base nos dados do paciente."""
        queixas_str = ", ".join(self.queixas)
        return (
            f"Paciente {self.nome}, {self.idade_estruturada}, sexo {self.sexo}. "
            f"Motivo da consulta: {queixas_str}."
        )

    @property
    def soap_objetivo(self) -> str:
        """Gera o campo Objetivo do SOAP com base nos sinais vitais."""
        if not self.sinais_vitais:
            return "Sinais vitais não informados."

        partes = []
        if self.sinais_vitais.pa_sistolica is not None and self.sinais_vitais.pa_diistolica is not None:
            partes.append(f"PA {self.sinais_vitais.pa_sistolica}/{self.sinais_vitais.pa_diistolica} mmHg")
        if self.sinais_vitais.frequencia_cardiaca is not None:
            partes.append(f"FC {self.sinais_vitais.frequencia_cardiaca} bpm")
        if self.sinais_vitais.frequencia_respiratoria is not None:
            partes.append(f"FR {self.sinais_vitais.frequencia_respiratoria} irpm")
        if self.sinais_vitais.temperatura is not None:
            partes.append(f"T {self.sinais_vitais.temperatura:.1f} °C")
        if self.sinais_vitais.saturacao_o2 is not None:
            partes.append(f"SatO2 {self.sinais_vitais.saturacao_o2:.0f}%")
        if self.sinais_vitais.escala_glasgow is not None:
            partes.append(f"GCS {self.sinais_vitais.escala_glasgow}")
        if self.sinais_vitais.nivel_consciencia is not None:
            partes.append(f"AVPU {self.sinais_vitais.nivel_consciencia}")
        if self.sinais_vitais.escala_dor is not None:
            partes.append(f"EVA {self.sinais_vitais.escala_dor}")

        return ", ".join(partes) if partes else "Sinais vitais dentro da normalidade."

    @property
    def soap_avaliacao(self) -> str:
        """Gera o campo Avaliação do SOAP com base na classificação e diagnóstico."""
        nivel_risco = self.classificar_risco_manchester
        cidaps = ", ".join(self.ciap2_recomendado)
        cid10s = ", ".join(self.cid10_recomendado)

        avaliacao = (
            f"Paciente apresenta risco {nivel_risco} com base em sinais vitais e sintomas. "
            f"Classificação CIAP-2: {cidaps}. "
            f"Classificação CID-10: {cid10s}."
        )

        if nivel_risco == NivelRisco.VERMELHO:
            avaliacao += " EMERGÊNCIA: acionar SAMU-192, referenciar imediatamente."
        elif nivel_risco == NivelRisco.LARANJA:
            avaliacao += " URGENTE: avaliar indicação de regulação SISREG."
        elif nivel_risco == NivelRisco.AMARELO:
            avaliacao += " MODERADO: reavaliar em 4–6 horas, discutir com equipe."
        elif nivel_risco == NivelRisco.VERDE:
            avaliacao += " ESTRATÉGIA: prosseguir com avaliação de rotina na APS."
        else:
            avaliacao += " PLANO: aguardar agendamento normal."

        return avaliacao

    @property
    def soap_plano(self) -> str:
        """Gera o campo Plano do SOAP com base no tratamento recomendado."""
        nivel_risco = self.classificar_risco_manchester
        if nivel_risco == NivelRisco.VERMELHO:
            return "Intervenção imediata, possível internação hospitalar."
        if nivel_risco == NivelRisco.LARANJA:
            return "Avaliação médica urgente, tratamento prescrito no mesmo dia."
        if nivel_risco == NivelRisco.AMARELO:
            return "Tratamento ambulatorial, reavaliação em 4–6 horas."
        if nivel_risco == NivelRisco.VERDE:
            return "Tratamento ambulatorial, acompanhamento normal."
        return "Acompanhamento eletivo conforme demanda da linha de cuidado."

    @property
    def soap_completo(self) -> str:
        """Retorna o registro SOAP completo."""
        return (
            f"S: {self.soap_subjetivo}\n"
            f"O: {self.soap_objetivo}\n"
            f"A: {self.soap_avaliacao}\n"
            f"P: {self.soap_plano}"
        )


class ResultadoTriagem(BaseModel):
    """Resultado da triagem clínica com classificação de risco e recomendações."""

    model_config = ConfigDict(strict=True)

    nivel: NivelRisco
    tempo_maximo_espera_min: int
    discriminadores: list[str]
    justificativa: str
    condutas: list[str]
    ciap2_sugeridos: list[str]
    cid10_sugeridos: list[str]
    soap_subjetivo: str
    soap_objetivo: str
    soap_avaliacao: str
    soap_plano: str
    requer_reavaliacao_min: int | None = None
    pontuacao: float

    @property
    def tempo_regulacao_sus(self) -> int:
        """Tempo de regulação no SUS conforme nível de risco."""
        if self.nivel == NivelRisco.VERMELHO:
            return 0
        if self.nivel == NivelRisco.LARANJA:
            return 10
        if self.nivel == NivelRisco.AMARELO:
            return 240
        if self.nivel == NivelRisco.VERDE:
            return 720
        return 1440


def evaluate_extreme_vitals(sinais_vitais: SinaisVitais, idade_anos: int | None = None) -> tuple[list[str], int]:
    """
    Avalia sinais vitais extremos e retorna lista de problemas e pontuação.

    Args:
        sinais_vitais: Dados de sinais vitais
        idade_anos: Idade em anos (opcional)

    Returns:
        Tupla com (lista de problemas, pontuação total)
    """
    problemas = []
    pontuacao = 0

    if sinais_vitais.pa_sistolica is not None:
        if sinais_vitais.pa_sistolica >= 180:
            problemas.append("Hipertensão grave (PA >= 180/120)")
            pontuacao += 3
        elif sinais_vitais.pa_sistolica >= 160:
            problemas.append("Hipertensão moderada (PA >= 160/100)")
            pontuacao += 2

    if sinais_vitais.pa_diistolica is not None:
        if sinais_vitais.pa_diistolica >= 120:
            problemas.append("Hipertensão diastólica grave")
            pontuacao += 3
        elif sinais_vitais.pa_diistolica >= 100:
            problemas.append("Hipertensão diastólica moderada")
            pontuacao += 2

    if sinais_vitais.frequencia_cardiaca is not None:
        if idade_anos is None or idade_anos >= 18:
            if sinais_vitais.frequencia_cardiaca >= 130:
                problemas.append("Taquicardia grave")
                pontuacao += 3
            elif sinais_vitais.frequencia_cardiaca >= 110:
                problemas.append("Taquicardia moderada")
                pontuacao += 2
        else:
            if sinais_vitais.frequencia_cardiaca >= 180:
                problemas.append("Taquicardia grave (pediátrica)")
                pontuacao += 3
            elif sinais_vitais.frequencia_cardiaca >= 160:
                problemas.append("Taquicardia moderada (pediátrica)")
                pontuacao += 2

    if sinais_vitais.frequencia_respiratoria is not None:
        if sinais_vitais.frequencia_respiratoria >= 30:
            problemas.append("Taquipneia grave")
            pontuacao += 3
        elif sinais_vitais.frequencia_respiratoria >= 25:
            problemas.append("Taquipneia moderada")
            pontuacao += 2

    if sinais_vitais.temperatura is not None:
        if sinais_vitais.temperatura >= 40.0:
            problemas.append("Hipertermia grave")
            pontuacao += 3
        elif sinais_vitais.temperatura >= 39.0:
            problemas.append("Hipertermia moderada")
            pontuacao += 2

    if sinais_vitais.saturacao_o2 is not None:
        if sinais_vitais.saturacao_o2 < 90:
            problemas.append("Hipoxemia grave")
            pontuacao += 3
        elif sinais_vitais.saturacao_o2 < 94:
            problemas.append("Hipoxemia moderada")
            pontuacao += 2

    if sinais_vitais.escala_glasgow is not None:
        if sinais_vitais.escala_glasgow <= 8:
            problemas.append("Glasgow crítico")
            pontuacao += 3
        elif sinais_vitais.escala_glasgow <= 12:
            problemas.append("Glasgow moderado")
            pontuacao += 2

    if sinais_vitais.nivel_consciencia is not None and sinais_vitais.nivel_consciencia in ("P", "U"):
        problemas.append("Comprometimento de consciência")
        pontuacao += 3

    if sinais_vitais.escala_dor is not None:
        if sinais_vitais.escala_dor >= 9:
            problemas.append("Dor intensa grave")
            pontuacao += 3
        elif sinais_vitais.escala_dor >= 7:
            problemas.append("Dor intensa moderada")
            pontuacao += 2

    return problemas, pontuacao


def evaluate_sentinel_complaints(queixas: list[QueixaSentinela], caracteristicas: dict | None = None) -> tuple[list[str], int]:
    """
    Avalia queixas sentinelas e retorna lista de problemas e pontuação.

    Args:
        queixas: Lista de queixas sentinelas
        caracteristicas: Características específicas das queixas (opcional)

    Returns:
        Tupla com (lista de problemas, pontuação total)
    """
    problemas = []
    pontuacao = 0

    for queixa in queixas:
        if queixa == QueixaSentinela.DOR_TORACICA:
            if caracteristicas and (
                caracteristicas.get("em_aperto", False)
                and caracteristicas.get("irradia_braco_mandibula", False)
            ):
                problemas.append("Dor torácica crítica (pressão + irradiação)")
                pontuacao += 3
            else:
                problemas.append("Dor torácica")
                pontuacao += 2

        elif queixa == QueixaSentinela.DISPNEIA:
            if caracteristicas and caracteristicas.get("fala_entrecortada", False):
                problemas.append("Dispneia crítica (fala entrecortada)")
                pontuacao += 3
            else:
                problemas.append("Dispneia")
                pontuacao += 2

        elif queixa in [
            QueixaSentinela.DEFICIT_NEUROLOGICO,
            QueixaSentinela.SANGRAMENTO_GRAVE,
            QueixaSentinela.REACAO_ALERGICA,
            QueixaSentinela.CONVULSAO,
            QueixaSentinela.PERDA_CONSCIENCIA,
            QueixaSentinela.FEBRE_PERSISTENTE,
            QueixaSentinela.VOMITO_PERSISTENTE,
            QueixaSentinela.CEFALEIA_BRUSCA,
            QueixaSentinela.DOR_ABDOMINAL_INTENSA,
            QueixaSentinela.GESTACAO_COMPLICACAO,
        ]:
            problemas.append(f"{queixa}")
            pontuacao += 3

    return problemas, pontuacao


def assign_priority_level(pontuacao_total: int, problemas: list[str]) -> NivelRisco:
    """
    Atribui nível de prioridade com base na pontuação total e problemas identificados.

    Args:
        pontuacao_total: Pontuação total dos critérios avaliados
        problemas: Lista de problemas identificados

    Returns:
        Nível de risco (Vermelho, Laranja, Amarelo, Verde, Azul)
    """
    problemas_str = str(problemas)
    if pontuacao_total >= 10 or "Hipertensão grave" in problemas_str or "Dor torácica crítica" in problemas_str:
        return NivelRisco.VERMELHO
    if pontuacao_total >= 7 or "Hipertensão moderada" in problemas_str or "Dispneia crítica" in problemas_str:
        return NivelRisco.LARANJA
    if pontuacao_total >= 5:
        return NivelRisco.AMARELO
    if pontuacao_total >= 2:
        return NivelRisco.VERDE
    return NivelRisco.AZUL
