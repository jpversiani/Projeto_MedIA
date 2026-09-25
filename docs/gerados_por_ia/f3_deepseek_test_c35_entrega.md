We need to create a test file for triage algorithms. The task: "backend/tests/test_triagem_clinica.py" testing: 1) correct classification of hypertensive emergency; 2) adequate downgrading of stable cases; 3) correct calculation of pediatric and adult MEWS score.

We need to infer the actual implementation to test. Since we are only asked to create tests, we need to design tests that would pass given a correct implementation. However, we don't have the implementation. We need to write tests that define expected behavior. We can assume there are functions/classes like `classify_hypertensive_emergency`, `downgrade_stable_case`, `calculate_mews` (adult and pediatric). We'll write tests using pytest.

We need to follow architecture: Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS patterns. But tests can be simple.

We'll create a test file with multiple test functions. We'll need to import from the actual module? The task says "crie backend/tests/test_triagem_clinica.py". We'll create that file. We'll need to define tests that import from the app's modules. Since we don't know the exact module structure, we can use relative imports or assume a package. Typically, tests are in backend/tests, and the app is in backend/app. We can do `from app.services.triagem import ...` or similar. But to be safe, we can write tests that import from a module `app.triagem` or `app.services.triagem`. We'll need to make reasonable assumptions.

Alternatively, we can write tests that are self-contained by defining the functions inside the test file? No, that would not test actual code. We need to test the actual algorithms. So we need to import from the project.

Given the task is to create tests, we'll assume there is an existing module `backend/app/services/triagem_clinica.py` with functions. We'll write tests accordingly.

We'll include:

1. Test hypertensive emergency classification: e.g., blood pressure >= 180/120 with target organ damage -> emergency. Or maybe a function `classify_hypertensive_emergency(sbp, dbp, symptoms)` returns boolean or a severity level.

2. Test downgrading of stable cases: e.g., a stable patient with no acute symptoms should be downgraded to low urgency. Could be a function `reclassify_stable_case(initial_acuity, vital_signs, symptoms)`.

3. MEWS score: adult MEWS uses parameters: HR, SBP, RR, Temp, Neuro (AVPU). Pediatric MEWS uses different thresholds. We'll test known values.

We'll write tests with clear assertions.

Let's design the test file.

We'll need to import pytest, maybe pydantic for validation.

We'll create a fixture? Not necessary.

We'll write test functions:

- test_hypertensive_emergency_classification
- test_stable_case_downgrade
- test_mews_adult_calculation
- test_mews_pediatric_calculation

We'll need to know the exact function signatures. We'll define them based on common sense.

Let's assume:

- `classify_hypertensive_emergency(sbp: int, dbp: int, target_organ_damage: bool = False) -> bool` or returns a string like "emergency", "urgency", "normal". We'll test that when sbp >= 180 and dbp >= 120 and target_organ_damage is True, it's emergency.

- `downgrade_stable_case(initial_acuity: str, vital_signs: dict, symptoms: list) -> str` returns lower acuity if stable.

- `calculate_mews_adult(hr, sbp, rr, temp, avpu)` returns int.

- `calculate_mews_pediatric(hr, sbp, rr, temp, avpu, age_group)` maybe.

We'll write tests accordingly.

We need to ensure tests are comprehensive.

Let's write the file.

We'll include docstrings.

We'll use type hints.

We'll import from `app.services.triagem_clinica` (or `app.triagem`). We'll use `from app.services import triagem_clinica as triagem` and call functions.

But to avoid import errors if not present, we can use a try-except? No, tests should fail if module missing. That's fine.

Let's write.

We'll also include a test for edge cases.

Now, let's produce the final answer with the code block.

We'll include the file path comment at top.

We'll write the code.```python
# Arquivo: backend/tests/test_triagem_clinica.py
"""
Testes unitários para os algoritmos de triagem de risco do Projeto MedIA.

Cobre:
1. Classificação correta de emergência hipertensiva.
2. Rebaixamento adequado de casos estáveis.
3. Cálculo correto do escore MEWS pediátrico e adulto.

Padrões de arquitetura:
- Python 3.12, tipagem estrita.
- Pydantic v2 e SQLAlchemy 2.0 (usados indiretamente via domínio).
- Padrões SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF).
"""

import pytest

# Importações do domínio de triagem clínica.
# Ajuste o caminho conforme a estrutura real do projeto.
from app.services.triagem_clinica import (
    classify_hypertensive_emergency,
    downgrade_stable_case,
    calculate_mews_adult,
    calculate_mews_pediatric,
)


# ---------------------------------------------------------------------------
# 1. Emergência hipertensiva
# ---------------------------------------------------------------------------
class TestHypertensiveEmergency:
    """Testes para a classificação de emergência hipertensiva."""

    def test_emergency_when_pressure_extreme_and_organ_damage(self):
        """
        Deve classificar como emergência quando PA >= 180x120 e há
        lesão de órgão-alvo (ex.: sintomas neurológicos, dor torácica).
        """
        result = classify_hypertensive_emergency(
            sbp=185, dbp=122, target_organ_damage=True
        )
        assert result is True

    def test_emergency_when_pressure_extreme_without_organ_damage(self):
        """
        PA muito elevada sem lesão de órgão-alvo é urgência, não emergência.
        """
        result = classify_hypertensive_emergency(
            sbp=190, dbp=125, target_organ_damage=False
        )
        assert result is False

    def test_not_emergency_when_pressure_below_threshold(self):
        """PA elevada mas abaixo do limiar não é emergência."""
        result = classify_hypertensive_emergency(
            sbp=160, dbp=100, target_organ_damage=True
        )
        assert result is False

    def test_emergency_with_symptoms_and_pressure_slightly_above(self):
        """
        Sintomas de lesão de órgão-alvo com PA >= 180x120 confirmam emergência.
        """
        result = classify_hypertensive_emergency(
            sbp=180, dbp=120, target_organ_damage=True
        )
        assert result is True


# ---------------------------------------------------------------------------
# 2. Rebaixamento de casos estáveis
# ---------------------------------------------------------------------------
class TestStableCaseDowngrade:
    """Testes para o rebaixamento de classificação de pacientes estáveis."""

    def test_downgrade_from_high_to_low_when_vitals_normal(self):
        """
        Caso inicialmente classificado como alto risco, mas com sinais vitais
        estáveis e sem sintomas agudos, deve ser rebaixado.
        """
        initial_acuity = "high"
        vital_signs = {
            "hr": 72,
            "sbp": 118,
            "dbp": 76,
            "rr": 16,
            "temp": 36.5,
            "avpu": "A",
        }
        symptoms = []
        result = downgrade_stable_case(initial_acuity, vital_signs, symptoms)
        assert result == "low"

    def test_no_downgrade_when_symptoms_present(self):
        """
        Paciente com sintomas agudos (ex.: dor torácica) não deve ser rebaixado.
        """
        initial_acuity = "high"
        vital_signs = {
            "hr": 72,
            "sbp": 118,
            "dbp": 76,
            "rr": 16,
            "temp": 36.5,
            "avpu": "A",
        }
        symptoms = ["chest_pain"]
        result = downgrade_stable_case(initial_acuity, vital_signs, symptoms)
        assert result == "high"

    def test_downgrade_only_one_level(self):
        """
        O rebaixamento deve ser de no máximo um nível de prioridade.
        """
        initial_acuity = "medium"
        vital_signs = {
            "hr": 70,
            "sbp": 120,
            "dbp": 80,
            "rr": 14,
            "temp": 36.0,
            "avpu": "A",
        }
        symptoms = []
        result = downgrade_stable_case(initial_acuity, vital_signs, symptoms)
        assert result == "low"

    def test_no_downgrade_when_vitals_unstable(self):
        """
        Sinais vitais alterados (ex.: taquicardia) impedem o rebaixamento.
        """
        initial_acuity = "medium"
        vital_signs = {
            "hr": 115,
            "sbp": 100,
            "dbp": 60,
            "rr": 22,
            "temp": 37.5,
            "avpu": "A",
        }
        symptoms = []
        result = downgrade_stable_case(initial_acuity, vital_signs, symptoms)
        assert result == "medium"


# ---------------------------------------------------------------------------
# 3. Escore MEWS
# ---------------------------------------------------------------------------
class TestMewsAdult:
    """Testes para o cálculo do escore MEWS em adultos."""

    def test_adult_mews_zero_for_normal_vitals(self):
        """Valores normais resultam em escore 0."""
        score = calculate_mews_adult(
            hr=75, sbp=120, rr=16, temp=36.5, avpu="A"
        )
        assert score == 0

    def test_adult_mews_high_hr(self):
        """Frequência cardíaca muito alta deve pontuar 3."""
        score = calculate_mews_adult(
            hr=135, sbp=120, rr=16, temp=36.5, avpu="A"
        )
        assert score == 3

    def test_adult_mews_low_sbp(self):
        """Pressão sistólica muito baixa deve pontuar 3."""
        score = calculate_mews_adult(
            hr=80, sbp=70, rr=16, temp=36.5, avpu="A"
        )
        assert score == 3

    def test_adult_mews_high_rr(self):
        """Frequência respiratória elevada deve pontuar 2."""
        score = calculate_mews_adult(
            hr=80, sbp=120, rr=28, temp=36.5, avpu="A"
        )
        assert score == 2

    def test_adult_mews_avpu_voice(self):
        """Resposta ao chamado (V) deve pontuar 2."""
        score = calculate_mews_adult(
            hr=80, sbp=120, rr=16, temp=36.5, avpu="V"
        )
        assert score == 2

    def test_adult_mews_combined(self):
        """
        Combinação de alterações: HR 130 (3) + RR 30 (3) + Temp 38.5 (1)
        deve resultar em 7.
        """
        score = calculate_mews_adult(
            hr=130, sbp=110, rr=30, temp=38.5, avpu="P"
        )
        assert score == 7


class TestMewsPediatric:
    """Testes para o cálculo do escore MEWS pediátrico."""

    def test_pediatric_mews_zero_for_normal_vitals(self):
        """Valores normais para a faixa etária resultam em 0."""
        score = calculate_mews_pediatric(
            hr=100, sbp=80, rr=20, temp=37.0, avpu="A", age_group="infant"
        )
        assert score == 0

    def test_pediatric_mews_tachycardia_infant(self):
        """
        Taquicardia em lactente (FC > 180) deve pontuar 3.
        """
        score = calculate_mews_pediatric(
            hr=190, sbp=80, rr=20, temp=37.0, avpu="A", age_group="infant"
        )
        assert score == 3

    def test_pediatric_mews_hypotension_child(self):
        """
        Hipotensão em criança (PAS < 70) deve pontuar 3.
        """
        score = calculate_mews_pediatric(
            hr=90, sbp=65, rr=18, temp=36.5, avpu="A", age_group="child"
        )
        assert score == 3

    def test_pediatric_mews_avpu_unresponsive(self):
        """
        Inconsciência (U) deve pontuar 3.
        """
        score = calculate_mews_pediatric(
            hr=100, sbp=80, rr=20, temp=37.0, avpu="U", age_group="infant"
        )
        assert score == 3

    def test_pediatric_mews_combined(self):
        """
        Combinação: FC 200 (3) + PAS 60 (3) + FR 40 (3) + Temp 39 (2) + AVPU P (2)
        = 13.
        """
        score = calculate_mews_pediatric(
            hr=200, sbp=60, rr=40, temp=39.0, avpu="P", age_group="child"
        )
        assert score == 13
```