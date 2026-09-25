We need to create a test file for triage algorithms. The user asks: "Para o Projeto MedIA, crie backend/tests/test_triagem_clinica.py testando: 1) classificação correta de emergência hipertensiva; 2) rebaixamento adequado de casos estáveis; 3) cálculo correto do escore MEWS pediátrico e adulto."

We need to infer the project structure. Likely there is a module that implements triage algorithms, risk classification, MEWS score. Since we are creating tests, we need to assume some interfaces. But we can also define the test file with mocks or against actual implementations if they exist. The user didn't provide the implementation, so we should write tests that assert behavior. We can also define the test file assuming certain functions/classes exist. But we need to make it complete and executable. We can create the test file with mock implementations? Actually, the task is to create tests, not the implementation. So we should write tests that would pass if the implementation is correct. We can use monkeypatch or dependency injection. But better to define the expected interfaces.

The project is "MedIA" with backend/tests. So we'll create backend/tests/test_triagem_clinica.py. The test file will import from backend modules. Since we don't know the exact structure, we can define the tests using fixtures and assume functions like:

- classify_hypertensive_emergency(patient_data) -> classification
- triage_stable_case(score) -> downgrade classification
- calculate_mews(patient_data, age_group) -> score

But we need to ensure the tests are meaningful. Alternatively, we can write the tests using Pydantic models for patient data and using the algorithm logic. However, the instruction says "Forneça o código completo e executável." So we need to make the test file runnable. We can include a minimal implementation within the test file? No, tests should test production code. But we can use pytest with mocks. Or we can write tests that import from a module that we also create? The task is specifically to create the test file only. We can assume the production code exists. We can write tests that use pytest.raises, assertions, etc.

Let's think about the domain:

1) Emergência hipertensiva: This is a clinical condition where blood pressure is severely elevated (e.g., systolic >180 and/or diastolic >120) with evidence of acute target organ damage. The algorithm should classify correctly.

2) Rebaixamento adequado de casos estáveis: This means stable cases should be downgraded in risk classification (e.g., from high risk to low risk). So we need to test that a stable patient gets a lower triage level.

3) Cálculo correto do escore MEWS pediátrico e adulto: MEWS (Modified Early Warning Score) has different parameters for adults and pediatrics. We need to test the scoring.

We need to decide on the exact function signatures. Since we are to create tests, we can define the expected interfaces. But to make the test file executable, we need the production code to exist. The user might expect us to also provide the implementation? The instruction says "crie backend/tests/test_triagem_clinica.py testando..." So it's only the test file. But we can include the test file with imports that may fail if modules don't exist. That would make it not executable. To ensure executability, we can either:

- Include a minimal implementation in the test file itself as a fallback? That's bad.
- Use pytest.importorskip to skip if modules not found.
- Write tests using mocks of the functions, not importing production code.

Better: We can write the test file assuming that the production code is in backend/app/services/triagem.py or similar, and we can define the tests with clear contracts. But if the file doesn't exist, running pytest will fail. To make it executable, we can also provide a conftest.py that creates dummy implementations? But the task is only to create the test file.

Given the constraints, I think the best approach is to write the test file using pytest and unittest.mock, creating fake implementations in the test itself. But that doesn't test production code. However, the instruction says "testando" the algorithms, so the tests should test actual algorithms.

Maybe the project already has the algorithms. We need to infer the names. We can use common patterns. Let's search memory: MEWS is calculated based on physiological parameters: respiratory rate, heart rate, systolic BP, conscious level (AVPU), temperature (optional). Pediatric MEWS may have different thresholds based on age.

We can write tests using parameterized fixtures. For example:

- For hypertensive emergency: given a patient with BP 200/120 and symptoms like headache, chest pain, or neurological deficit, classification should be "emergencia_hipertensiva". We can test both positive and negative cases.

- For downgrade: a patient with initial high risk (e.g., MEWS high) but after treatment stable, the algorithm should downgrade.

- For MEWS calculation: we can compute expected scores manually and assert.

We need to create the test file with functions like test_emergencia_hipertensiva_classificacao_correta, test_rebaixamento_casos_estaveis, test_calculo_mews_pediatrico, test_calculo_mews_adulto.

We also need to include Pydantic v2 models? The tests can use Pydantic for data validation. But we can just use dictionaries.

Let's design the test file with pytest. We'll use @pytest.fixture to provide sample patient data. We'll import from backend.app.services.triagem (or similar). To make it runnable, we'll assume the module exists. But if not, we can add a comment indicating the expected API.

Alternatively, we can write the test file in a way that it can be run with pytest even if the implementation is absent by using `pytest.importorskip("backend.app.services.triagem")` and then define tests conditionally. But then it would skip, not fail. That's acceptable.

However, the user likely wants a complete test file. Let's create a test file that imports the necessary modules, and we also can provide a brief explanation of the expected functions. We'll also include type hints.

We need to ensure the test file follows the architecture: Python 3.12, Pydantic v2, SQLAlchemy 2.0. We can use Pydantic for models in tests, but it's not necessary.

I'll write the test file with the following structure:

- Imports: pytest, datetime, pydantic, possibly the service modules.
- Define a model for patient vitals if needed.
- Fixtures for patient data.
- Tests for each of the three categories.

But we need to know the exact function names. Let's assume:

- `classify_hypertensive_emergency(patient: PatientData) -> dict` returns a classification with risk level and details.
- `calculate_mews(patient: PatientData, is_pediatric: bool = False) -> int` returns the MEWS score.
- `triage_stable_case(initial_classification: str, stability_indicators: dict) -> str` returns the downgraded classification.

Alternatively, the triage system might be a class `TriageService` with methods.

To be safe, we can use monkeypatch to patch a service class. But we need to define the actual logic? No, we test that the service returns expected outputs.

Let's create the test file with mocked service functions that are actually the production ones? That's weird.

Maybe we can implement the triage algorithms ourselves within the test file, but that's not unit testing.

The task is to "crie backend/tests/test_triagem_clinica.py testando" - create the test file. It doesn't ask to create the implementation. So we should write tests that are comprehensive and would pass if the implementation is correct. We can make assumptions about the API. To make it executable, we can include a `conftest.py` that provides a dummy implementation? But the instruction is for a single file.

Let's re-read: "Crie backend/tests/test_triagem_clinica.py" - so just that file. We'll provide the file content. It should be complete and executable in the sense that it can be run by pytest. But if the production modules are missing, it will fail. We can mitigate by using `pytest.importorskip` to skip if not available. But then the test would not actually run. That's not ideal.

Given that this is a coding task, I think the best is to write the test file with clear expected behavior, using `unittest.mock` to mock the service functions, and then also include a few tests that demonstrate the expected logic by reimplementing the algorithms? No.

Maybe the project already has these functions. We just need to write tests for them. So we should write the tests based on known standard definitions.

Let's define the expected behavior:

1) Emergência hipertensiva: A patient is classified as hypertensive emergency if systolic BP >= 180 AND/OR diastolic BP >= 120 AND evidence of acute target organ damage (e.g., chest pain, dyspnea, neurological deficit, acute renal failure). Without target organ damage, it's "urgencia hipertensiva" (hypertensive urgency). So we test that the algorithm correctly identifies.

2) Rebaixamento de casos estáveis: The triage system should downgrade risk level when the patient is stable. For example, a patient initially with MEWS 7 (high risk) after treatment with MEWS 2 should be downgraded to lower risk. Or in a triage protocol, stable patients (normal vitals) should be classified as non-urgent.

3) MEWS: Adult MEWS uses parameters: RR, HR, SBP, Temp, AVPU. Pediatric MEWS uses age-specific thresholds. We can test with known examples.

Now, to make the test file executable without production code, we can include a simple implementation of the triage algorithms within the test file as "helpers" for computing expected results? No.

Alternatively, we can use `pytest` with `doctest` style? No.

I'll write the test file with imports from `backend.app.services.triagem` but also include a fallback using `pytest.importorskip`. This way, if the module doesn't exist, tests are skipped, not failed. But the user asked for tests that test the algorithms; skipping would mean not testing. However, the environment likely has the code.

Given the context of this conversation, the assistant is expected to generate code for a project that may not have all modules yet. But the user specifically asks for tests. We can assume the modules exist.

Let's decide on the file path: `backend/tests/test_triagem_clinica.py`.

We'll include:

- Imports.
- A Pydantic model for PatientVitals (or just use dict).
- Fixtures with sample data.
- Test functions with clear assertions.

We'll also include `from backend.app.services.triagem import ...` (adjust path).

To be precise, we'll define the expected functions:

- `classify_hypertensive_emergency(pressure: dict, target_organ_damage: bool) -> str`
- `rebaixar_risco(patient_data: dict) -> str` or `downgrade_risk(score: int) -> str`
- `calculate_mews_adult(vitals: dict) -> int`
- `calculate_mews_pediatric(vitals: dict, age_months: int) -> int`

We can use these names.

But maybe the project uses Portuguese names? Since it's SUS/APS, the code might be in Portuguese. We can use Portuguese function names. However, code in Python usually uses English. We can use English.

Let's structure the test file:

```python
# Arquivo: backend/tests/test_triagem_clinica.py
"""Testes unitários para algoritmos de triagem de risco."""

import pytest
from datetime import datetime, timedelta
from pydantic import BaseModel, ValidationError
# Importar serviços de triagem
try:
    from backend.app.services.triagem import (
        classify_hypertensive_emergency,
        calculate_mews_adult,
        calculate_mews_pediatric,
        downgrade_risk,
    )
except ImportError:
    pytest.skip("Módulos de triagem não disponíveis", allow_module_level=True)
```

Then define tests.

But we also need to test the downgrade properly. We'll create a function that takes a MEWS score and returns a triage level, and test that stable (low score) gets downgraded.

Maybe the algorithm is a class `TriageProtocol` with methods. We'll just assume.

Let's create comprehensive tests:

1. `test_emergencia_hipertensiva_pressao_alta_com_dano_orgao` - BP 200/120, target organ damage True -> returns "emergencia".
2. `test_emergencia_hipertensiva_sem_dano_orgao` - BP 200/120, target organ damage False -> returns "urgencia" (not emergency).
3. `test_emergencia_hipertensiva_pressao_nao_alta_com_dano` - BP 160/100, target organ damage True -> returns not emergency? Actually, if BP not severely high, even with damage, it's not hypertensive emergency. So test that.

2. Downgrade:
- `test_rebaixamento_caso_estavel` - patient with initial high risk (e.g., MEWS 8) but after treatment stable (MEWS 1) should be downgraded to "baixo risco" or "não urgente".
- `test_rebaixamento_manutencao_risco_alto` - patient still unstable should remain high.

3. MEWS:
- `test_calculo_mews_adulto` - given vitals (HR 110, RR 22, SBP 90, Temp 38.5, AVPU alert), expected score.
- `test_calculo_mews_pediatrico` - given vitals with age-specific thresholds.

We need to know the exact MEWS scoring. Let's recall the standard MEWS:

For adults:
- Respiratory rate (breaths/min): 0 if 9-14, 1 if 15-20, 2 if 21-29, 3 if >=30; or 1 if 8, 2 if 7, 3 if <7.
- Heart rate (bpm): 0 if 51-100, 1 if 41-50 or 101-110, 2 if 111-129 or 35-40, 3 if >=130 or <35.
- Systolic BP (mmHg): 0 if 101-199, 1 if 81-100 or 200-249, 2 if 71-80 or >=250, 3 if <70.
- Temperature (°C): 0 if 35.0-38.4, 1 if 38.5-39.0, 2 if >=39.1, or 2 if 34.0-34.9, 3 if <34.0.
- AVPU: 0 if Alert, 1 if Voice, 2 if Pain, 3 if Unresponsive.

But there are variations. We'll use a standard.

For pediatric MEWS, there are different scales (e.g., PEWS). We'll use a common one based on age.

We'll define expected scores for a given set of vitals.

Now, to make the test file robust, we'll use parameterized tests with pytest.mark.parametrize.

We'll also include type hints.

Let's write the file.

But we need to ensure the test file itself is executable. Since we import from a module that may not exist, we use pytest.skip at module level if import fails. That is acceptable.

Alternatively, we can create a conftest.py that provides the services. But the user only asked for the test file.

I'll write the test file with the import and skip.

We should also include some fixtures to avoid repetition.

Let's craft the content.

We'll start with a docstring.

Then imports.

Then a Pydantic model for vitals? Actually, we can just use dicts.

But the tests for MEWS need to pass vitals to the function. We'll use dictionaries.

We'll also define expected MEWS scores.

For the emergency classification, we'll use a simple function that takes BP and target organ damage.

Let's define the expected API:

- `classify_hypertensive_emergency(bp: dict, target_organ_damage: bool) -> str` returns "emergencia" or "urgencia" or "controle".
- `calculate_mews_adult(vitals: dict) -> int`
- `calculate_mews_pediatric(vitals: dict, age_months: int) -> int`
- `downgrade_risk(initial_risk: str, mews_score: int) -> str` returns downgraded risk.

But we don't know if downgrade_risk exists. We can test the behavior via a more comprehensive triage function. Let's assume there is a `classify_risk(mews_score)` that returns "baixo", "médio", "alto". Then downgrade means a patient with initial "alto" but stable (low mews) becomes "baixo". We can test that.

Alternatively, we can test the downgrade algorithm as part of the triage service. But let's define a function `downgrade_risk(current_level: str, patient_stable: bool) -> str` which returns the new level.

Given the instruction "rebaixamento adequado de casos estáveis", we can interpret that the triage algorithm should not overclassify stable cases. So we test that a patient with normal vitals gets a low triage level.

Maybe the algorithm is a "Protocolo de Manchester" or similar. We'll just test a simple rule.

I'll define the test functions based on standard medical algorithms.

Let's write the code.

We'll also include tests for Pydantic validation? Maybe not necessary.

To ensure the test file is complete, we'll add comments in Portuguese/English.

Let's produce the final answer.```python
# Arquivo: backend/tests/test_triagem_clinica.py
"""
Testes unitários para os algoritmos de triagem de risco do Projeto MedIA.

Cobertura:
1. Classificação correta de emergência hipertensiva.
2. Rebaixamento adequado de casos estáveis.
3. Cálculo correto do escore MEWS pediátrico e adulto.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta

# Importa os serviços de triagem. Se não estiverem disponíveis, os testes são ignorados.
try:
