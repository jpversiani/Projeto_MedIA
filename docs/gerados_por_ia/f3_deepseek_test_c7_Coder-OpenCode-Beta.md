We need to create backend/tests/test_triagem_clinica.py for the MedIA project. The task: test unit tests for risk triage algorithms. Specifically: 1) correct classification of hypertensive emergency; 2) adequate downgrading of stable cases; 3) correct calculation of pediatric and adult MEWS score.

We need to write tests. But we need to know the actual implementation of the triage algorithms. Since we are only asked to create the test file, we need to assume the existence of some module with functions/classes. We should design tests that would pass if the implementation is correct. We need to follow the architecture: Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS patterns, CIAP-2, CID-10, SOAP, CNS/CPF. But the test file itself may just import from the backend modules.

We need to infer the structure. Likely there is a module like backend/app/services/triagem_clinica.py or backend/app/algorithms/triagem.py. We need to create tests that test the functions.

Let's think: The task says "crie backend/tests/test_triagem_clinica.py testando: 1) classificação correta de emergência hipertensiva; 2) rebaixamento adequado de casos estáveis; 3) cálculo correto do escore MEWS pediátrico e adulto."

So we need to write pytest tests for these three aspects.

We need to decide what functions to test. Possibly:

- A function that classifies hypertensive emergency based on blood pressure and symptoms.
- A function that downgrades risk level for stable cases (maybe after reassessment).
- A function that calculates MEWS (Modified Early Warning Score) for adults and pediatric (maybe PEWS? But they say MEWS pediátrico e adulto, so maybe there is a pediatric version of MEWS? Actually MEWS is for adults, PEWS for pediatrics. But they explicitly say "MEWS pediátrico e adulto", so maybe they have a unified function that takes age and calculates accordingly.)

We need to write tests that are plausible. Since we don't have the actual implementation, we need to define the expected behavior based on clinical guidelines.

Let's outline:

1) Hypertensive emergency classification: Typically, hypertensive emergency is severe hypertension (SBP > 180 or DBP > 120) with acute target organ damage (e.g., neurological symptoms, chest pain, dyspnea, etc.). Hypertensive urgency is severe hypertension without target organ damage. So the algorithm should classify as "emergência hipertensiva" if BP is very high and there are symptoms of target organ damage. Otherwise, maybe "urgência hipertensiva" or "estável".

We need to test that the function correctly identifies emergency vs non-emergency.

2) Downgrading of stable cases: This likely refers to a triage protocol where after a period of observation or after treatment, a patient's risk level can be downgraded if they are stable. For example, in emergency triage, a patient initially classified as high risk may be downgraded to lower risk if vital signs improve. We need to test that the algorithm correctly downgrades when criteria are met.

3) MEWS calculation: MEWS uses physiological parameters: respiratory rate, heart rate, systolic BP, temperature, level of consciousness (AVPU), and maybe oxygen saturation. Each parameter scores 0-3, total score. For pediatric, there is a modified version with age-specific thresholds. We need to test that the calculation is correct for both adult and pediatric.

We need to write tests with sample inputs and expected outputs.

We should also consider the architecture: Pydantic v2 for data validation, SQLAlchemy 2.0 for ORM, but tests may not need DB. We can use simple data classes or dictionaries.

We need to create the test file with proper imports. Since we don't know the exact module path, we can assume something like:

from backend.app.services.triagem_clinica import classificar_emergencia_hipertensiva, rebaixar_risco, calcular_mews

Or maybe there is a class TriagemService. We can write tests that import from a module and use functions. To make it robust, we can use pytest and maybe skip if import fails? But the task expects us to create the test file, not the implementation. We should write tests that would work with a reasonable implementation.

We can also create a conftest.py? Not needed.

Let's design the test file.

We'll use pytest, with parametrize for multiple cases.

We need to ensure type hints and Pydantic v2. We can use pydantic models for input data? The test can create instances of models if they exist. But we don't know. We can just use dictionaries.

Better to write tests that call functions with keyword arguments.

Let's define expected function signatures:

- classificar_emergencia_hipertensiva(pressao_sistolica: int, pressao_diastolica: int, sintomas: list[str]) -> str (or enum)
- rebaixar_risco(nivel_risco_atual: str, sinais_vitais: dict, tempo_observacao: int) -> str
- calcular_mews(idade: int, frequencia_respiratoria: int, frequencia_cardiaca: int, pressao_sistolica: int, temperatura: float, nivel_consciencia: str) -> int

But we need to be careful: MEWS for pediatric may have different parameters. We can have a function that takes age and uses appropriate thresholds.

Let's research typical MEWS:

Adult MEWS (from literature):
- Respiratory rate: <=9 = 2, 10-14 = 0, 15-20 = 1, 21-29 = 2, >=30 = 3
- Heart rate: <=40 = 2, 41-50 = 1, 51-100 = 0, 101-110 = 1, 111-129 = 2, >=130 = 3
- Systolic BP: <=70 = 3, 71-80 = 2, 81-100 = 1, 101-199 = 0, >=200 = 2? Actually some versions: >200 = 2 or 3. Let's use a standard.
- Temperature: <=35 = 2, 35.1-36 = 0? Actually <35 = 2, 35-38.4 = 0, >=38.5 = 2
- AVPU: Alert=0, Voice=1, Pain=2, Unresponsive=3

Pediatric MEWS (or PEWS) varies by age. There is a "Pediatric Early Warning Score" (PEWS) that uses different parameters: behavior, cardiovascular, respiratory. But the task says "MEWS pediátrico", so maybe they have a modified MEWS for children with age-specific thresholds for heart rate, respiratory rate, etc.

We can define a plausible algorithm and test accordingly.

Since we are only writing tests, we can define expected values based on our own understanding. The tests should be clear and cover edge cases.

Let's structure the test file:

- Imports: pytest, maybe from backend.app.services.triagem_clinica import ...
- If the module doesn't exist, tests will fail. But that's okay; the task is to create tests for the implementation that should exist.

We can also include a comment that the implementation must be in place.

We'll write tests with parametrize.

Let's create the test file.

We need to ensure Python 3.12, Pydantic v2, SQLAlchemy 2.0. We can use type hints.

We'll write:

```python
# Arquivo: backend/tests/test_triagem_clinica.py
"""
Testes unitários para algoritmos de triagem de risco clínico.
Cobre: emergência hipertensiva, rebaixamento de casos estáveis e cálculo de MEWS.
"""

import pytest
from typing import Dict, List, Any

# Importações do módulo de triagem (a implementar)
from backend.app.services.triagem_clinica import (
    classificar_emergencia_hipertensiva,
    rebaixar_risco,
    calcular_mews,
)
```

But we need to be careful: if the module doesn't exist, the import will fail at collection. That's fine; the tests are meant to be run after implementation.

Alternatively, we can use pytest.importorskip to skip if not available. But the task says to create the tests, so we assume the implementation exists.

Let's define the tests.

Test 1: Emergência hipertensiva

We need to test that the function returns "emergencia" when BP is high and there are symptoms of target organ damage, and "urgencia" or "sem_emergencia" otherwise.

We'll use parametrize with cases:

- PA 200/120, sintomas: ["cefaleia intensa", "escotomas"] -> emergencia
- PA 180/110, sintomas: ["dor torácica"] -> emergencia
- PA 180/110, sintomas: [] -> urgencia (or nao_emergencia)
- PA 160/100, sintomas: ["cefaleia"] -> nao_emergencia (since not severe)

We need to define the expected output. Let's assume the function returns a string: "emergencia_hipertensiva", "urgencia_hipertensiva", "sem_emergencia". Or maybe an enum. We'll use strings.

We'll write:

```python
@pytest.mark.parametrize(
    "sistolica, diastolica, sintomas, esperado",
    [
        (200, 120, ["cefaleia intensa", "escotomas"], "emergencia_hipertensiva"),
        (180, 110, ["dor toracica"], "emergencia_hipertensiva"),
        (180, 110, [], "urgencia_hipertensiva"),
        (160, 100, ["cefaleia"], "sem_emergencia"),
    ],
)
def test_classificar_emergencia_hipertensiva(sistolica, diastolica, sintomas, esperado):
    assert classificar_emergencia_hipertensiva(
        pressao_sistolica=sistolica,
        pressao_diastolica=diastolica,
        sintomas=sintomas,
    ) == esperado
```

Test 2: Rebaixamento de casos estáveis

We need to test that a patient initially classified as high risk can be downgraded if stable after observation. The function might take current risk level, vital signs, and time.

We'll define cases:

- Current risk "vermelho" (high), after 30 min, vital signs stable (HR 80, RR 14, BP 120/80, SpO2 98%, conscious) -> "amarelo" or "verde"?
- Current risk "amarelo", after 60 min, stable -> "verde"
- Current risk "vermelho", but still unstable -> remains "vermelho"

We need to define the expected output. Let's assume the function returns a risk level string: "vermelho", "amarelo", "verde", "azul" (Brazilian triage colors). Or maybe "alto", "médio", "baixo". We'll use "vermelho", "amarelo", "verde".

We'll write:

```python
@pytest.mark.parametrize(
    "nivel_atual, sinais_vitais, tempo_minutos, esperado",
    [
        ("vermelho", {"frequencia_cardiaca": 80, "frequencia_respiratoria": 14, "pressao_sistolica": 120, "pressao_diastolica": 80, "saturacao_oxigenio": 98, "nivel_consciencia": "alerta"}, 30, "amarelo"),
        ("amarelo", {"frequencia_cardiaca": 75, "frequencia_respiratoria": 16, "pressao_sistolica": 110, "pressao_diastolica": 70, "saturacao_oxigenio": 97, "nivel_consciencia": "alerta"}, 60, "verde"),
        ("vermelho", {"frequencia_cardiaca": 120, "frequencia_respiratoria": 28, "pressao_sistolica": 90, "pressao_diastolica": 60, "saturacao_oxigenio": 90, "nivel_consciencia": "confuso"}, 30, "vermelho"),
    ],
)
def test_rebaixar_risco(nivel_atual, sinais_vitais, tempo_minutos, esperado):
    assert rebaixar_risco(
        nivel_risco_atual=nivel_atual,
        sinais_vitais=sinais_vitais,
        tempo_observacao_minutos=tempo_minutos,
    ) == esperado
```

Test 3: Cálculo de MEWS

We need to test adult and pediatric. We'll write two test functions or parametrize with age.

We'll define a function calcular_mews(idade, ...). For adults, we use adult thresholds; for children, we use pediatric thresholds.

We need to define expected scores for specific inputs.

Let's define adult MEWS thresholds:

- Respiratory rate (irpm): <=9 = 2, 10-14 = 0, 15-20 = 1, 21-29 = 2, >=30 = 3
- Heart rate (bpm): <=40 = 2, 41-50 = 1, 51-100 = 0, 101-110 = 1, 111-129 = 2, >=130 = 3
- Systolic BP (mmHg): <=70 = 3, 71-80 = 2, 81-100 = 1, 101-199 = 0, >=200 = 2
- Temperature (°C): <=35 = 2, 35.1-38.4 = 0, >=38.5 = 2
- AVPU: alerta=0, voz=1, dor=2, inconsciente=3

We'll test with a normal patient: HR 80, RR 14, BP 120, Temp 36.5, Alert -> score 0.

Another with abnormal: HR 130, RR 30, BP 90, Temp 39, Pain -> 3+3+1+2+2 = 11? Actually HR 130=3, RR 30=3, BP 90=1, Temp 39=2, Pain=2 => total 11.

We'll test.

For pediatric, we need age-specific thresholds. Let's define a simplified pediatric MEWS based on age groups. For example, for infants (<1 year), normal HR 110-160, RR 30-60, etc. But we can define a simple version.

Since the task says "MEWS pediátrico e adulto", we can have a function that takes age and uses different tables. We'll test with a child age 5.

We'll define pediatric thresholds (simplified):

- Respiratory rate: for age 1-5: <=20 = 2, 21-30 = 0, 31-40 = 1, 41-50 = 2, >50 = 3
- Heart rate: for age 1-5: <=80 = 2, 81-110 = 0, 111-130 = 1, 131-150 = 2, >150 = 3
- Systolic BP: <=70 = 3, 71-80 = 2, 81-90 = 1, 91-120 = 0, >120 = 2
- Temperature: same as adult
- AVPU: same

We'll test with a normal child: HR 100, RR 25, BP 100, Temp 37, Alert -> score 0.

And an abnormal child: HR 160, RR 55, BP 75, Temp 39, Pain -> 3+3+2+2+2 = 12.

We'll write parametrized tests.

We need to decide how to pass parameters. We'll use keyword arguments.

Let's write the test file.

We'll also include a test for invalid inputs? Maybe not necessary.

We'll use pytest.approx for floats? Not needed.

We'll also include a test for the function raising ValueError on invalid age? Maybe.

But the task specifically asks for three things. We'll cover them.

Let's write the code.

We need to be careful with the import path. The project is "MedIA", backend is a package. We'll use "backend.app.services.triagem_clinica". If the module is elsewhere, the test will fail. But we can add a comment.

We'll also include a conftest? Not needed.

Let's create the file.

We'll also add type hints and docstrings.

Now, let's produce the final answer with the code.```python
# Arquivo: backend/tests/test_triagem_clinica.py
"""
Testes unitários para os algoritmos de triagem de risco clínico do Projeto MedIA.

Cobre:
1. Classificação correta de emergência hipertensiva.
2. Rebaixamento adequado de casos estáveis.
3. Cálculo correto do escore MEWS pediátrico e adulto.

Padrões adotados:
- Python 3.12, tipagem estrita.
- Pydantic v2 e SQLAlchemy 2.0 (quando aplicável).
- Terminologia SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF).
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest

# Importações do módulo de triagem clínica (a ser implementado).
# Caso o módulo ainda não exista, os testes falharão na coleta,
# indicando que a implementação deve ser criada.
from backend.app.services.triagem_clinica import (
    classificar_emergencia_hipertensiva,
    rebaixar_risco,
    calcular_mews,
)


# -----------------------------------------------------------------------------
# 1. Emergência hipertensiva
# -----------------------------------------------------------------------------
class TestEmergenciaHipertensiva:
    """
    Testes para a classificação de emergência hipertensiva.
    Critérios clínicos:
    - PA sistólica ≥ 180 mmHg OU diastólica ≥ 120 mmHg.
    - Presença de sintomas de lesão de órgão-alvo (ex.: c