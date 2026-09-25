```python
# Arquivo: backend/tests/test_triagem_clinica.py
"""
Testes unitários para os algoritmos de triagem clínica do projeto MedIA.

Cobre três funcionalidades críticas:
1. Classificação de emergência hipertensiva.
2. Rebaixamento de risco para casos estáveis.
3. Cálculo do escore MEWS (adulto e pediátrico).

Os testes assumem que as funções estão implementadas em:
backend/app/services/triagem.py
"""

import pytest

# Importação das funções de triagem (a ser implementado no código de produção)
from backend.app.services.triagem import (
    classify_hypertensive_emergency,
    downgrade_stable_case,
    calculate_mews,
    # Para garantir que a assinatura está correta, usamos os nomes conforme esperado.
    # Caso os nomes sejam diferentes, os testes serão ajustados.
)


# =============================================================================
# 1. Emergência hipertensiva
# =============================================================================
class TestClassifyHypertensiveEmergency:
    """
    Testa a função `classify_hypertensive_emergency`.

    Casos:
    - PA muito alta (SBP >= 180 ou DBP >= 120) com sintomas de lesão de órgão-alvo
      deve ser classificada como emergência.
    - PA muito alta sem sintomas não deve ser emergência (apenas urgência).
    - PA normal com sintomas não é emergência.
    - Casos limítrofes.
    """

    def test_alta_pa_com_sintomas_neurologicos_retorna_emergencia(self):
        """
        PA sistólica 190, diastólica 120, com déficit neurológico focal -> emergência.
        """
        result = classify_hypertensive_emergency(
            systolic=190,
            diastolic=120,
            symptoms=["déficit neurológico focal"]
        )
        assert result is True, "Deveria ser emergência hipertensiva"

    def test_alta_pa_com_sintomas_cardiovascular_retorna_emergencia(self):
        """
        PA 180/110 com dor torácica intensa -> emergência.
        """
        result = classify_hypertensive_emergency(
            systolic=180,
            diastolic=110,
            symptoms=["dor torácica intensa"]
        )
        assert result is True

    def test_alta_pa_sem_sintomas_nao_retorna_emergencia(self):
        """
        PA 185/120, sem sintomas -> não é emergência (apenas urgência).
        """
        result = classify_hypertensive_emergency(
            systolic=185,
            diastolic=120,
            symptoms=[]
        )
        assert result is False, "Sem sintomas não configura emergência"

    def test_pa_limiar_baixo_sem_sintomas_nao_retorna_emergencia(self):
        """
        PA 179/119 (abaixo do limiar) mesmo com sintomas leves não é emergência.
        """
        result = classify_hypertensive_emergency(
            systolic=179,
            diastolic=119,
            symptoms=["cefaleia leve"]
        )
        assert result is False

    def test_pa_normal_com_sintomas_nao_retorna_emergencia(self):
        """
        PA 130/85 com sintomas genéricos não é emergência.
        """
        result = classify_hypertensive_emergency(
            systolic=130,
            diastolic=85,
            symptoms=["náusea"]
        )
        assert result is False

    def test_pa_limiar_superior_sem_sintomas_nao_retorna_emergencia(self):
        """
        PA 180/120 exatamente no limite, sem sintomas -> não emergência.
        """
        result = classify_hypertensive_emergency(
            systolic=180,
            diastolic=120,
            symptoms=[]
        )
        assert result is False


# =============================================================================
# 2. Rebaixamento de casos estáveis
# =============================================================================
class TestDowngradeStableCase:
    """
    Testa a função `downgrade_stable_case`.

    A lógica deve:
    - Se o risco atual é alto e o paciente está estável (vitals normais e sem
      sinais de deterioração), rebaixar para moderado.
    - Se risco moderado e estável, rebaixar para baixo.
    - Se risco baixo, permanece baixo.
    - Se instável, mantém o mesmo nível.
    """

    def test_risco_alto_estavel_rebaixa_para_moderado(self):
        """
        Risco alto, sinais vitais estáveis -> moderado.
        """
        # Exemplo: sinais vitais dentro da normalidade, sem alteração
        vitals = {
            "heart_rate": 75,
            "respiratory_rate": 16,
            "systolic_bp": 120,
            "temperature": 36.8,
            "avpu": "A",
            "spo2": 98
        }
        result = downgrade_stable_case(
            initial_risk="alto",
            vitals=vitals,
            stability_time_minutes=30
        )
        assert result == "moderado"

    def test_risco_moderado_estavel_rebaixa_para_baixo(self):
        """
        Risco moderado, estável -> baixo.
        """
        vitals = {
            "heart_rate": 80,
            "respiratory_rate": 18,
            "systolic_bp": 125,
            "temperature": 36.6,
            "avpu": "A",
            "spo2": 99
        }
        result = downgrade_stable_case(
            initial_risk="moderado",
            vitals=vitals,
            stability_time_minutes=30
        )
        assert result == "baixo"

    def test_risco_baixo_estavel_permanece_baixo(self):
        """
        Risco baixo, estável -> permanece baixo.
        """
        vitals = {
            "heart_rate": 72,
            "respiratory_rate": 14,
            "systolic_bp": 118,
            "temperature": 36.7,
            "avpu": "A",
            "spo2": 99
        }
        result = downgrade_stable_case(
            initial_risk="baixo",
            vitals=vitals,
            stability_time_minutes=30
        )
        assert result == "baixo"

    def test_risco_alto_instavel_permanece_alto(self):
        """
        Risco alto, sinais vitais instáveis -> permanece alto.
        """
        vitals = {
            "heart_rate": 130,
            "respiratory_rate": 28,
            "systolic_bp": 85,
            "temperature": 38.5,
            "avpu": "V",
            "spo2": 90
        }
        result = downgrade_stable_case(
            initial_risk="alto",
            vitals=vitals,
            stability_time_minutes=30
        )
        assert result == "alto"

    def test_risco_alto_estavel_tempo_insuficiente_nao_rebaixa(self):
        """
        Risco alto, vitals estáveis mas tempo de estabilidade curto -> não rebaixa.
        """
        vitals = {
            "heart_rate": 75,
            "respiratory_rate": 16,
            "systolic_bp": 120,
            "temperature": 36.8,
            "avpu": "A",
            "spo2": 98
        }
        result = downgrade_stable_case(
            initial_risk="alto",
            vitals=vitals,
            stability_time_minutes=10
        )
        assert result == "alto", "Ainda não houve tempo suficiente para considerar estável"

    def test_risco_moderado_estavel_tempo_insuficiente_nao_rebaixa(self):
        """
        Risco moderado, estável mas tempo curto -> permanece moderado.
        """
        vitals = {
            "heart_rate": 78,
            "respiratory_rate": 16,
            "systolic_bp": 122,
            "temperature": 36.9,
            "avpu": "A",
            "spo2": 98
        }
        result = downgrade_stable_case(
            initial_risk="moderado",
            vitals=vitals,
            stability_time_minutes=5
        )
        assert result == "moderado"


# =============================================================================
# 3. Cálculo do escore MEWS (adulto e pediátrico)
# =============================================================================
class TestCalculateMEWS:
    """
    Testa a função `calculate_mews`.

    Escore MEWS adulto (valores padrão) e PEWS (pediátrico) devem ser calculados
    corretamente com base nos parâmetros fornecidos.

    Consideramos a seguinte pontuação para adulto (faixas típicas):
    - FC: <40 (3), 41-50 (1), 51-100 (0), 101-110 (1), 111-129 (2), >=130 (3)
    - FR: <6 (3), 6-8 (2), 9-14 (0), 15-20 (1), 21-29 (2), >=30 (3)
    - PAS: <70 (3), 71-80 (2), 81-100 (1), 101-199 (0), >=200 (1)
    - Temp: <=34 (