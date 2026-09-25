```python
# Arquivo: backend/app/services/triagem_clinica.py
"""
Motor de Inferência de Risco Clínico (Manchester Adaptado) para Atenção Primária.

Este módulo implementa a classificação de risco baseada no Sistema de Triagem de
Manchester, adaptado para o contexto de Atenção Primária à Saúde (APS) no âmbito
do projeto MedIA. O motor avalia sinais vitais extremos, queixas sentinelas
(dor torácica, dispneia grave) e atribui prioridades (Vermelho, Laranja, Amarelo,
Verde, Azul) conforme a urgência clínica.

A implementação é puramente lógica, sem dependências externas além de Pydantic v2,
e segue as diretrizes do projeto: código limpo, tipagem estrita e foco em
atendimento particular/convênios (TISS ANS 4.01 / DMED).
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Priority(str, Enum):
    """Níveis de prioridade clínica (cores do Manchester)."""
    RED = "vermelho"
    ORANGE = "laranja"
    YELLOW = "amarelo"
    GREEN = "verde"
    BLUE = "azul"


class ConsciousnessLevel(str, Enum):
    """Escala AVPU para nível de consciência."""
    ALERT = "alerta"
    VOICE = "voz"
    PAIN = "dor"
    UNRESPONSIVE = "irresponsivo"


class VitalSigns(BaseModel):
    """Sinais vitais do paciente."""
    heart_rate: int = Field(..., ge=0, le=300, description="Frequência cardíaca (bpm)")
    respiratory_rate: int = Field(..., ge=0, le=100, description="Frequência respiratória (irpm)")
    oxygen_saturation: int = Field(..., ge=0, le=100, description="Saturação de oxigênio (%)")
    systolic_bp: int = Field(..., ge=0, le=300, description="Pressão arterial sistólica (mmHg)")
    diastolic_bp: int = Field(..., ge=0, le=200, description="Pressão arterial diastólica (mmHg)")
    temperature: float = Field(..., ge=30, le=45, description="Temperatura corporal (°C)")
    consciousness: ConsciousnessLevel = Field(..., description="Nível de consciência (AVPU)")


class TriageInput(BaseModel):
    """Dados de entrada para a classificação de risco."""
    vital_signs: VitalSigns
    chest_pain: bool = Field(False, description="Presença de dor torácica")
    severe_dyspnea: bool = Field(False, description="Presença de dispneia grave")
    other_red_flags: List[str] = Field(
        default_factory=list,
        description="Outros sinais de alerta (ex.: hemorragia, rebaixamento súbito)"
    )


class TriageOutput(BaseModel):
    """Resultado da classificação de risco."""
    priority: Priority
    reason: str
    recommendations: List[str] = Field(default_factory=list)


class TriageEngine:
    """
    Motor de classificação de risco clínico.

    Utiliza regras baseadas no Sistema de Manchester adaptado para APS.
    A prioridade é determinada pela presença de sinais de alerta e valores
    extremos de sinais vitais.
    """

    # Limiares para sinais vitais extremos (valores considerados críticos)
    RED_THRESHOLDS = {
        "heart_rate_min": 40,
        "heart_rate_max": 140,
        "respiratory_rate_min": 8,
        "respiratory_rate_max": 30,
        "oxygen_saturation_min": 90,
        "systolic_bp_min": 80,
        "systolic_bp_max": 220,
        "diastolic_bp_max": 120,
        "temperature_min": 35.0,
        "temperature_max": 41.0,
    }

    ORANGE_THRESHOLDS = {
        "heart_rate_min": 50,
        "heart_rate_max": 120,
        "respiratory_rate_min": 10,
        "respiratory_rate_max": 24,
        "oxygen_saturation_min": 92,
        "systolic_bp_min": 90,
        "systolic_bp_max": 200,
        "diastolic_bp_max": 110,
        "temperature_min": 36.0,
        "temperature_max": 39.5,
    }

    def classify(self, input_data: TriageInput) -> TriageOutput:
        """
        Classifica o risco do paciente com base nos dados fornecidos.

        Args:
            input_data: Dados de entrada (sinais vitais e queixas).

        Returns:
            TriageOutput com a prioridade, motivo e recomendações.
        """
        # Verifica critérios de prioridade Vermelha (maior urgência)
        red_reason = self._check_red_flags(input_data)
        if red_reason:
            return TriageOutput(
                priority=Priority.RED,
                reason=red_reason,
                recommendations=self._get_red_recommendations()
            )

        # Verifica critérios de prioridade Laranja
        orange_reason = self._check_orange_flags(input_data)
        if orange_reason:
            return TriageOutput(
                priority=Priority.ORANGE,
                reason=orange_reason,
                recommendations=self._get_orange_recommendations()
            )

        # Verifica critérios de prioridade Amarela
        yellow_reason = self._check_yellow_flags(input_data)
        if yellow_reason:
            return TriageOutput(
                priority=Priority.YELLOW,
                reason=yellow_reason,
                recommendations=self._get_yellow_recommendations()
            )

        # Verifica critérios de prioridade Verde
        green_reason = self._check_green_flags(input_data)
        if green_reason:
            return TriageOutput(
                priority=Priority.GREEN,
                reason=green_reason,
                recommendations=self._get_green_recommendations()
            )

        # Caso contrário, prioridade Azul (não urgente)
        return TriageOutput(
            priority=Priority.BLUE,
            reason="Quadro clínico sem sinais de urgência.",
            recommendations=self._get_blue_recommendations()
        )

    def _check_red_flags(self, input_data: TriageInput) -> Optional[str]:
        """
        Verifica critérios de prioridade Vermelha.

        Retorna uma string com o motivo se algum critério for atendido,
        caso contrário None.
        """
        vs = input_data.vital_signs
        thresholds = self.RED_THRESHOLDS

        # Nível de consciência
        if vs.consciousness == ConsciousnessLevel.UNRESPONSIVE:
            return "Paciente irresponsivo (AVPU: U)."

        # Frequência cardíaca
        if vs.heart_rate < thresholds["heart_rate_min"] or vs.heart_rate > thresholds["heart_rate_max"]:
            return f"Frequência cardíaca extrema: {vs.heart_rate} bpm."

        # Frequência respiratória
        if vs.respiratory_rate < thresholds["respiratory_rate_min"] or vs.respiratory_rate > thresholds["respiratory_rate_max"]:
            return f"Frequência respiratória extrema: {vs.respiratory_rate} irpm."

        # Saturação de oxigênio
        if vs.oxygen_saturation < thresholds["oxygen_saturation_min"]:
            return f"Saturação de oxigênio crítica: {vs.oxygen_saturation}%."

        # Pressão arterial
        if vs.systolic_bp < thresholds["systolic_bp_min"] or vs.systolic_bp > thresholds["systolic_bp_max"]:
            return f"Pressão arterial sistólica extrema: {vs.systolic_bp} mmHg."

        # Temperatura
        if vs.temperature < thresholds["temperature_min"] or vs.temperature > thresholds["temperature_max"]:
            return f"Temperatura extrema: {vs.temperature}°C."

        # Queixas sentinelas
        if input_data.chest_pain and vs.systolic_bp < 100:
            return "Dor torácica com hipotensão."

        if input_data.severe_dyspnea and vs.oxygen_saturation < 92:
            return "Dispneia grave com dessaturação."

        # Outros sinais de alerta (ex.: hemorragia, rebaixamento súbito)
        if input_data.other_red_flags:
            return "Sinais de alerta adicionais: " + ", ".join(input_data.other_red_flags)

        return None

    def _check_orange_flags(self, input_data: TriageInput) -> Optional[str]:
        """
        Verifica critérios de prioridade Laranja.

        Retorna uma string com o motivo se algum critério for atendido,
        caso contrário None.
        """
        vs = input_data.vital_signs
        thresholds = self.ORANGE_THRESHOLDS

        # Nível de consciência (Voz ou Dor)
        if vs.consciousness in (ConsciousnessLevel.VOICE, ConsciousnessLevel.PAIN):
            return f"Alteração do nível de consciência: {vs.consciousness.value}."

        # Frequência cardíaca
        if vs.heart_rate < thresholds["heart_rate_min"] or vs.heart_rate > thresholds["heart_rate_max"]:
            return f"Frequência cardíaca anormal: {vs.heart_rate} bpm."

        # Frequência respiratória
        if vs.respiratory_rate < thresholds["respiratory_rate_min"] or vs.respiratory_rate > thresholds["respiratory_rate_max"]:
            return f"Frequência respiratória anormal: {vs.respiratory_rate} irpm."

        # Saturação de oxigênio
        if vs.oxygen_saturation < thresholds["oxygen_saturation_min"]:
            return f"Saturação de oxigênio baixa: {vs.oxygen_saturation}%."

        # Pressão arterial
        if vs.systolic_bp < thresholds["systolic_bp_min"] or vs.systolic_bp > thresholds["systolic_bp_max"]:
            return f"Pressão arterial sistólica anormal: {vs.systolic_bp} mmHg."

        # Temperatura
        if vs.temperature < thresholds["temperature_min"] or vs.temperature > thresholds["temperature_max"]:
            return f"Temperatura anormal: {vs.temperature}°C."

        # Queixas sentinelas
        if input_data.chest_pain:
            return "Dor torácica."

        if input_data.severe_dyspnea:
            return "Dispneia grave."

        return None

    def _check_yellow_flags(self, input_data: TriageInput) -> Optional[str]:
        """
        Verifica critérios de prioridade Amarela.

        Retorna uma string com o motivo se algum critério for atendido,
        caso contrário None.
        """
        vs = input_data.vital_signs

        # Frequência cardíaca fora da faixa normal (mas não extrema)
        if vs.heart_rate < 60 or vs.heart_rate > 100:
            return f"Frequência