```python
# Arquivo: backend/app/services/triagem_clinica.py
"""
Motor de Inferência de Risco Clínico (Manchester Adaptado) para Atenção Primária à Saúde.

Este módulo implementa a classificação de risco clínico baseada em:
- Sinais vitais extremos (frequência cardíaca, respiratória, pressão arterial, SpO2, temperatura, nível de consciência)
- Queixas sentinelas (dor torácica, dispneia grave)
- Atribuição de prioridades: Vermelho, Laranja, Amarelo, Verde, Azul

A lógica segue uma adaptação do Sistema de Triagem de Manchester, focada no contexto
de atendimento particular e convênios (TISS ANS 4.01 / DMED), com método clínico de
Atenção Primária / Saúde da Família.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Prioridade(str, Enum):
    """Prioridades de atendimento conforme o sistema de triagem."""
    VERMELHO = "Vermelho"   # Atendimento imediato
    LARANJA = "Laranja"     # Muito urgente
    AMARELO = "Amarelo"     # Urgente
    VERDE = "Verde"         # Pouco urgente
    AZUL = "Azul"           # Não urgente


class SinaisVitais(BaseModel):
    """Modelo de dados para sinais vitais do paciente."""
    pressao_sistolica: Optional[int] = Field(default=None, ge=0, le=300, description="Pressão arterial sistólica (mmHg)")
    pressao_diastolica: Optional[int] = Field(default=None, ge=0, le=200, description="Pressão arterial diastólica (mmHg)")
    frequencia_cardiaca: Optional[int] = Field(default=None, ge=0, le=300, description="Frequência cardíaca (bpm)")
    frequencia_respiratoria: Optional[int] = Field(default=None, ge=0, le=100, description="Frequência respiratória (irpm)")
    saturacao_oxigenio: Optional[int] = Field(default=None, ge=0, le=100, description="Saturação de oxigênio (SpO2 %)")
    temperatura: Optional[float] = Field(default=None, ge=30.0, le=45.0, description="Temperatura corporal (°C)")
    nivel_consciencia: Optional[str] = Field(
        default="alerta",
        description="Nível de consciência: 'alerta', 'confuso', 'sonolento', 'irresponsivo'"
    )


class Sintomas(BaseModel):
    """Modelo de dados para queixas sentinelas."""
    dor_toracica: bool = Field(default=False, description="Presença de dor torácica")
    dor_toracica_intensidade: Optional[int] = Field(default=None, ge=0, le=10, description="Intensidade da dor (escala 0-10)")
    dor_toracica_com_sudorese: bool = Field(default=False, description="Dor torácica acompanhada de sudorese")
    dor_toracica_irradiacao: bool = Field(default=False, description="Dor torácica irradiada para braço, mandíbula ou costas")
    dispneia: bool = Field(default=False, description="Presença de dispneia (falta de ar)")
    dispneia_grave: bool = Field(default=False, description="Dispneia grave (incapacidade de falar frases completas, uso de musculatura acessória)")
    dispneia_repouso: bool = Field(default=False, description="Dispneia em repouso")
    sincope: bool = Field(default=False, description="Síncope (desmaio) recente")
    sangramento_grave: bool = Field(default=False, description="Sangramento grave ou incontrolável")


class TriagemClinica:
    """
    Motor de classificação de risco clínico.

    Utiliza regras baseadas em sinais vitais extremos e queixas sentinelas
    para atribuir uma prioridade de atendimento.
    """

    # Limiares para sinais vitais extremos
    LIMIAR_VERMELHO = {
        "spo2_min": 90,
        "fc_max": 140,
        "fc_min": 40,
        "fr_max": 30,
        "fr_min": 8,
        "pas_min": 90,
        "pas_max": 200,
        "temp_max": 41.0,
        "temp_min": 35.0,
    }

    LIMIAR_LARANJA = {
        "spo2_min": 92,  # se SpO2 < 92% mas >= 90% -> laranja
        "fc_max": 120,
        "fc_min": 50,
        "fr_max": 24,
        "fr_min": 10,
        "pas_min": 100,
        "pas_max": 180,
        "temp_max": 39.0,
        "temp_min": 36.0,
    }

    def classificar(self, sinais: SinaisVitais, sintomas: Sintomas) -> Prioridade:
        """
        Avalia os sinais vitais e sintomas e retorna a prioridade de atendimento.

        Args:
            sinais: Dados de sinais vitais do paciente.
            sintomas: Queixas sentinelas relatadas.

        Returns:
            Prioridade: Vermelho, Laranja, Amarelo, Verde ou Azul.
        """
        # 1. Avaliação de risco imediato (Vermelho)
        if self._avaliar_vermelho(sinais, sintomas):
            return Prioridade.VERMELHO

        # 2. Avaliação de risco muito urgente (Laranja)
        if self._avaliar_laranja(sinais, sintomas):
            return Prioridade.LARANJA

        # 3. Avaliação de risco urgente (Amarelo)
        if self._avaliar_amarelo(sinais, sintomas):
            return Prioridade.AMARELO

        # 4. Avaliação de risco pouco urgente (Verde)
        if self._avaliar_verde(sinais, sintomas):
            return Prioridade.VERDE

        # 5. Caso contrário, não urgente (Azul)
        return Prioridade.AZUL

    def _avaliar_vermelho(self, sinais: SinaisVitais, sintomas: Sintomas) -> bool:
        """Verifica critérios de risco imediato (Vermelho)."""
        # Sinais vitais extremos
        if sinais.saturacao_oxigenio is not None and sinais.saturacao_oxigenio < self.LIMIAR_VERMELHO["spo2_min"]:
            return True
        if sinais.frequencia_cardiaca is not None and (
            sinais.frequencia_cardiaca > self.LIMIAR_VERMELHO["fc_max"] or
            sinais.frequencia_cardiaca < self.LIMIAR_VERMELHO["fc_min"]
        ):
            return True
        if sinais.frequencia_respiratoria is not None and (
            sinais.frequencia_respiratoria > self.LIMIAR_VERMELHO["fr_max"] or
            sinais.frequencia_respiratoria < self.LIMIAR_VERMELHO["fr_min"]
        ):
            return True
        if sinais.pressao_sistolica is not None and (
            sinais.pressao_sistolica < self.LIMIAR_VERMELHO["pas_min"] or
            sinais.pressao_sistolica > self.LIMIAR_VERMELHO["pas_max"]
        ):
            return True
        if sinais.temperatura is not None and (
            sinais.temperatura > self.LIMIAR_VERMELHO["temp_max"] or
            sinais.temperatura < self.LIMIAR_VERMELHO["temp_min"]
        ):
            return True
        if sinais.nivel_consciencia == "irresponsivo":
            return True

        # Queixas sentinelas graves
        if sintomas.dispneia_grave or sintomas.dispneia_repouso:
            return True
        if sintomas.dor_toracica and (
            sintomas.dor_toracica_intensidade is not None and sintomas.dor_toracica_intensidade >= 8 or
            sintomas.dor_toracica_com_sudorese or
            sintomas.dor_toracica_irradiacao or
            (sinais.pressao_sistolica is not None and sinais.pressao_sistolica < 100)
        ):
            return True
        if sintomas.sangramento_grave:
            return True

        return False

    def _avaliar_laranja(self, sinais: SinaisVitais, sintomas: Sintomas) -> bool:
        """Verifica critérios de risco muito urgente (Laranja)."""
        # Sinais vitais alterados (dentro dos limites de laranja)
        if sinais.saturacao_oxigenio is not None and (
            self.LIMIAR_VERMELHO["spo2_min"] <= sinais.saturacao_oxigenio < self.LIMIAR_LARANJA["spo2_min"]
        ):
            return True
        if sinais.frequencia_cardiaca is not None and (
            self.LIMIAR_LARANJA["fc_max"] < sinais.frequencia_cardiaca <= self.LIMIAR_VERMELHO["fc_max"] or
            self.LIMIAR_VERMELHO["fc_min"] <= sinais.frequencia_cardiaca < self.LIMIAR_LARANJA["fc_min"]
        ):
            return True
        if sinais.frequencia_respiratoria is not None and (
            self.LIMIAR_LARANJA["fr_max"] < sinais.frequencia_respiratoria <= self.LIMIAR_VERMELHO["fr_max"] or
            self.LIMIAR_VERMELHO["fr_min"] <= sinais.frequencia_respiratoria < self.LIMIAR_LARANJA["fr_min"]
        ):
            return True
        if sinais.pressao_sistolica is not None and (
            self.LIMIAR_LARANJA["pas_min"] <= sinais.pressao_sistolica < self.LIMIAR_VERMELHO["pas_min"] or
            self.LIMIAR_VERMELHO["pas_max"] < sinais.pressao_sistolica <= self.LIMIAR_LARANJA["pas_max"]
        ):
            return True
        if sinais.temperatura is not None and (
            self.LIMIAR_LARANJA["temp_max"] <= sinais.temperatura < self.LIMIAR_VERMELHO["temp_max"] or
            self.LIMIAR_VERMELHO["temp