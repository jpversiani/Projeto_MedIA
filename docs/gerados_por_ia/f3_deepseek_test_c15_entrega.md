We need to create backend/tests/test_triagem_clinica.py for the MedIA project. The task is to write unit tests for risk triage algorithms. Specifically:

1) correct classification of hypertensive emergency
2) proper downgrading of stable cases
3) correct calculation of MEWS score for pediatric and adult.

We need to understand the existing code structure. The user didn't provide the actual implementation, but we need to write tests that would pass against expected behavior. Since we are the coder, we need to create the test file. We might need to infer the functions/classes to test. The instructions mention "Algoritmos de Triagem de Risco (C15)" and "backend/tests/test_triagem_clinica.py". We need to test the triage logic. Likely there is a module like backend/app/services/triagem.py or similar. Since we don't have the code, we need to design tests that are reasonable and follow the architecture.

We should create a test file that imports the relevant modules. But since we don't know the exact names, we can either:

- Assume a certain structure and write tests accordingly, possibly with mocks or using the actual code if it exists.
- Or we can write tests that are self-contained, testing the logic directly if we implement the functions in the test? But the task says "crie backend/tests/test_triagem_clinica.py testando: ..." so we need to write tests for existing code. However, as an AI, we need to produce a file that would be appropriate. We can make reasonable assumptions about the API.

Given the context of MedIA, a medical AI project, likely there are services for triage. Let's search memory: There is a known "MEWS" (Modified Early Warning Score) for adults and "PEWS" (Pediatric Early Warning Score) or "MEWS pediátrico" maybe. The task says "MEWS pediátrico e adulto" - so they want both.

We need to write tests that verify:

1) Classification of hypertensive emergency: likely a function that takes blood pressure and other symptoms and returns a risk level (e.g., "emergência hipertensiva" vs "urgência hipertensiva" vs "normal"). We need to test that it correctly identifies hypertensive emergency.

2) Downgrading of stable cases: maybe a triage algorithm that assigns a risk score (like Manchester triage) and downgrades if the patient is stable. Could be a function that adjusts the risk level based on stability criteria.

3) MEWS calculation: a function that computes MEWS score from vital signs (respiratory rate, heart rate, systolic BP, temperature, consciousness, etc.) for adults, and a pediatric version.

We need to write tests using pytest, with Pydantic v2 and SQLAlchemy 2.0? The tests themselves may not need SQLAlchemy unless we test database models. But the architecture says "Código em Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0." So the tests should be compatible.

We should create a test file that imports the actual functions from the backend. Since we don't have the code, we can define the expected interfaces and write tests that would pass if the implementation matches. But the user expects us to "execute com precisão conforme as diretrizes." That means we need to produce a file that is ready to run. However, without the actual implementation, the tests will fail if the functions don't exist. But maybe the project already has these functions, and we are just adding tests. Since we are the AI, we need to generate the test file based on our understanding of the codebase. We can also include some mock implementations? No, the task is to create tests, not implementation.

Maybe we should write tests that are self-contained, i.e., we implement the algorithms within the test file? That would not be unit tests of the actual code. The instruction says "Testes Unitários de Algoritmos de Triagem de Risco (C15)" - so we need to test the algorithms. If the algorithms are not implemented, we can't test them. But the user likely expects us to write tests for existing code. Since we don't have the code, we need to infer the structure from common patterns.

Let's think: In a typical FastAPI project, there would be a service layer. For example, backend/app/services/triagem.py containing functions like:

- classificar_emergencia_hipertensiva(pressao_arterial: PressaoArterial, sintomas: ...) -> NivelRisco
- calcular_mews_adulto(vitais: SinaisVitais) -> int
- calcular_mews_pediatrico(vitais: SinaisVitais, idade: int) -> int
- rebaixar_caso_estavel(nivel_risco: NivelRisco, estabilidade: bool) -> NivelRisco

We can write tests that import these functions and assert their behavior.

Alternatively, we can create a test file that uses pytest and defines the tests with expected values, and we can also include a fixture that mocks the functions? No, that would not test the actual logic.

Given the ambiguity, I'll proceed by writing a test file that assumes the existence of a module `backend.app.services.triagem` with specific functions. I'll also include imports that may need to be adjusted. I'll use Pydantic v2 models for input data. I'll write tests that cover the three requirements.

Let's design the test cases:

1) Test for hypertensive emergency classification:
   - Input: systolic BP >= 180 and/or diastolic >= 120, plus symptoms of target organ damage (e.g., chest pain, dyspnea, neurological deficit). Should classify as "emergencia_hipertensiva".
   - Also test that high BP without symptoms is "urgencia_hipertensiva" or "hipertensao_estadio_3" etc.
   - We need to know the exact classification function. Let's assume there is a function `classificar_crise_hipertensiva(pa: PressaoArterial, sintomas: List[str]) -> str` that returns "emergencia" or "urgencia" or "controle". We'll test accordingly.

2) Test for downgrading stable cases:
   - Perhaps a function `ajustar_risco_por_estabilidade(risco_inicial: str, estavel: bool) -> str` that downgrades risk if stable. For example, if risk is "alto" and stable, becomes "moderado". We'll test that.

3) Test for MEWS calculation:
   - Adult MEWS: typical scoring based on respiratory rate, heart rate, systolic BP, temperature, AVPU. We'll test a few cases.
   - Pediatric MEWS: maybe different thresholds based on age. We'll test with a known case.

We need to define the expected scores. Let's recall standard MEWS:

Adult MEWS (Modified Early Warning Score) commonly:
- Respiratory rate: <=8 (3), 9-14 (0), 15-20 (1), 21-29 (2), >=30 (3)
- Heart rate: <=40 (3), 41-50 (1), 51-100 (0), 101-110 (1), 111-129 (2), >=130 (3)
- Systolic BP: <=70 (3), 71-80 (2), 81-100 (1), 101-199 (0), >=200 (2)
- Temperature: <=35 (2), 35.1-36 (1), 36.1-38 (0), 38.1-38.5 (1), >=38.6 (2)
- AVPU: Alert (0), Voice (1), Pain (2), Unresponsive (3)

Pediatric MEWS (or PEWS) varies by age. There is a "Pediatric Early Warning Score" (PEWS) that uses different parameters: behavior, cardiovascular, respiratory. But the task says "MEWS pediátrico" - maybe they use a modified version. We can assume a function that takes age and vitals and returns a score.

Given the lack of specifics, we can define our own expected behavior in the tests, but that would be arbitrary. To make the tests meaningful, we need to align with the actual implementation. Since we don't have it, we can write tests that are plausible and would pass if the implementation follows standard guidelines.

Maybe the project already has these functions, and we can find them in the codebase? But as an AI, I don't have access to the actual files. I need to generate a test file that is likely to be correct.

I'll structure the test file with:

- Imports: pytest, pydantic, and from backend.app.services.triagem import (classificar_crise_hipertensiva, calcular_mews_adulto, calcular_mews_pediatrico, rebaixar_risco_estavel) - or similar names.
- Define Pydantic models for inputs if needed.
- Write test functions.

To avoid import errors, we can use `pytest.importorskip` or try/except? But the test should be runnable. Since we are creating the file, we can assume the modules exist. If they don't, the tests will fail, but that's expected if the implementation is missing.

Alternatively, we can write the tests in a way that they can be run independently by implementing the algorithms in the test file? That would be weird.

Let's read the task again: "TAREFA: Testes Unitários de Algoritmos de Triagem de Risco (C15)" - it says "crie backend/tests/test_triagem_clinica.py testando: ..." So we are to create the test file. The instructions also say "Execute com precisão conforme as diretrizes." That means we should produce the code for the test file. We are not asked to implement the algorithms themselves. So we need to write tests that would test the existing algorithms. Since we don't have the algorithms, we need to make reasonable assumptions about their interfaces.

I'll proceed by creating a test file that is well-structured, uses Pydantic v2 for data validation, and tests the three requirements with clear assertions. I'll include comments explaining the expected behavior. I'll also include a conftest.py if needed? No, just the test file.

Let's decide on the function names and signatures. I'll use:

- `classificar_crise_hipertensiva(pressao_arterial: PressaoArterial, sintomas: list[str]) -> str` where `PressaoArterial` is a Pydantic model with `sistolica` and `diastolica`. Returns "emergencia", "urgencia", or "nao_crise".

- `calcular_mews_adulto(vitais: SinaisVitaisAdulto) -> int` where `SinaisVitaisAdulto` has fields: `frequencia_respiratoria`, `frequencia_cardiaca`, `pressao_sistolica`, `temperatura`, `nivel_consciencia` (AVPU). Returns int.

- `calcular_mews_pediatrico(vitais: SinaisVitaisPediatrico) -> int` where `SinaisVitaisPediatrico` has fields: `idade_meses`, `frequencia_respiratoria`, `frequencia_cardiaca`, `pressao_sistolica`, `temperatura`, `nivel_consciencia`. Returns int.

- `rebaixar_risco_estavel(nivel_risco: str, estavel: bool) -> str` that downgrades risk if stable.

We'll write tests for these.

Now, let's write the test file with detailed test cases.

We need to ensure the tests are comprehensive. For hypertensive emergency, we can test:

- BP 190/120 with symptoms -> "emergencia"
- BP 180/110 without symptoms -> "urgencia" or "nao_crise"? Actually, hypertensive emergency is defined as severe hypertension (>=180/120) with acute target organ damage. So if no symptoms, it's "urgencia hipertensiva" (or "hipertensao severa assintomatica"). We'll test that.

For downgrading stable cases:

- If risk is "emergencia" and stable? Actually, emergency should not be downgraded. But the requirement says "rebaixamento adequado de casos estáveis" - maybe it's about triage color codes (e.g., Manchester) where a stable patient with a high-risk complaint can be downgraded. We'll test that a stable patient with "vermelho" (red) becomes "laranja" or something. Let's define a function that takes a triage level and a stability flag and returns the adjusted level.

For MEWS:

- Adult: test a normal patient (all vitals normal) -> score 0.
- Test a patient with high respiratory rate and low BP -> score >0.
- Pediatric: test a normal child -> score 0, and a sick child -> score >0.

We'll need to know the exact thresholds. I'll use standard MEWS thresholds for adult. For pediatric, I'll use a simplified version based on age-adjusted heart rate and respiratory rate. But to avoid guessing, I'll write tests that are based on common sense: e.g., a child with very high heart rate and respiratory rate should have a higher score than a normal child.

Alternatively, we can write tests that check the function returns an integer and that it increases with severity. But the requirement says "cálculo correto do escore MEWS pediátrico e adulto" - so we need to assert specific values.

Given the lack of specification, I'll define the expected scores based on standard MEWS for adult and a plausible pediatric version. I'll include comments that the thresholds are based on the implementation.

Let's write the code.

We'll also need to handle Pydantic v2: use `from pydantic import BaseModel`.

We'll use `pytest` and `pytest.mark.parametrize` for multiple cases.

Let's create the file.

I'll also include a `conftest.py`? Not necessary.

Now, let's write the test file.```python
# Arquivo: backend/tests/test_triagem_clinica.py
"""
Testes unitários para os algoritmos de triagem de risco do Projeto MedIA.

Cobre:
1. Classificação correta de emergência hipertensiva.
2. Rebaixamento adequado de casos estáveis.
3. Cálculo correto do escore MEWS pediátrico e adulto.

Conformidade:
- Python 3.12, tipagem estrita com Pydantic v2.
- Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, CNS/CPF).
- Testes automatizados com pytest.
"""

from __future__ import annotations

from typing import Literal

import pytest
from pydantic import BaseModel, Field

# Importações dos serviços de triagem (ajuste conforme a implementação real)
from backend.app.services.triagem import (
    calcular_mews_adulto,
    calcular_mews_pediatrico,
    classificar_crise_hipertensiva,
    rebaixar_risco_estavel,
)


# -----------------------------------------------------------------------------
# Modelos de entrada (Pydantic v2)
# -----------------------------------------------------------------------------
class PressaoArterial(BaseModel):
    """Pressão arterial sistólica e diastólica em mmHg."""

    sistolica: int = Field(ge=50, le=300)
    diastolica: int = Field(ge=30, le=200)


class SinaisVitaisAdulto(BaseModel):
    """Sinais vitais para cálculo do MEWS adulto."""

    frequencia_respiratoria: int = Field(ge=0, le=80)
    frequencia_cardiaca: int = Field(ge=0, le=250)
    pressao_sistolica: int = Field(ge=0, le=300)
    temperatura: float = Field(ge=30.0, le=45.0)
    nivel_consciencia: Literal["alerta", "voz", "dor", "nao_responsivo"]


class SinaisVitaisPediatrico(BaseModel):
    """Sinais vitais para cálculo do MEWS pediátrico (idade em meses)."""

    idade_meses: int = Field(ge=0, le=216)  # até 18 anos
    frequencia_respiratoria: int = Field(ge=0, le=100)
    frequencia_cardiaca: int = Field(ge=0, le=250)
    pressao_sistolica: int = Field(ge=0, le=200)
    temperatura: float = Field(ge=30.0, le=45.0)
    nivel_consciencia: Literal["alerta", "voz", "dor", "nao_responsivo"]


# -----------------------------------------------------------------------------
# Testes: Classificação de Emergência Hipertensiva
# -----------------------------------------------------------------------------
class TestClassificacaoEmergenciaHipertensiva:
    """
    Testa a função `classificar_crise_hipertensiva`.

    Critérios esperados:
    - PA >= 180/120 com sintomas de lesão de órgão-alvo → "emergencia"
    - PA >= 180/120 sem sintomas → "urgencia"
    - PA < 180/120 → "nao_crise"
    """

    @pytest.mark.parametrize(
        "pa, sintomas, esperado",
        [
            (
                PressaoArterial(sistolica=190, diastolica=120),
                ["dor_toracica", "dispneia"],
                "emergencia",
            ),
            (
                PressaoArterial(sistolica=180, diastolica=130),
                ["deficit_neurologico"],
                "emergencia",
            ),
            (
                PressaoArterial(sistolica=200, diastolica=110),
                ["cefaleia_intensa", "escotomas"],
                "emergencia",
            ),
        ],
    )
    def test_emergencia_hipertensiva_com_sintomas(
        self, pa: PressaoArterial, sintomas: list[str], esperado: str
    ) -> None:
        assert classificar_crise_hipertensiva(pa, sintomas) == esperado

    @pytest.mark.parametrize(
        "pa, sintomas, esperado",
        [
            (
                PressaoArterial(sistolica=185, diastolica=120),
                [],
                "urgencia",
            ),
            (
                PressaoArterial(sistolica=180, diastolica=115),
                ["assintomatico"],
                "urgencia",
            ),
