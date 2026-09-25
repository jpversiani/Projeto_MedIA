We need to create backend/tests/test_copiloto_clinico.py for the MedIA project. The task: 1) validate detection of severe contraindications in prescription; 2) test blocking of medication if patient has declared allergy; 3) validate structure and completeness of generated SOAP draft.

We need to write tests. We need to infer the code structure. The project likely has modules for copiloto clinico (clinical copilot) that handles alerts and SOAP generation. We need to write tests that import the relevant functions/classes. Since we don't have the actual implementation, we need to design tests that would pass given a reasonable implementation. But the instruction says "Crie backend/tests/test_copiloto_clinico.py" - we are to create the test file. We need to make it executable and precise. We can assume there are functions like `detect_contraindicacoes`, `verificar_alergias`, `gerar_rascunho_soap` or similar. We need to write tests that validate these behaviors.

We should follow the architecture: Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS patterns (CIAP-2, CID-10, SOAP, CNS/CPF). Tests should use pytest.

We need to create a test file that is self-contained, but it will import from the application. Since we don't have the actual code, we can define the expected interfaces and write tests that mock or use fixtures. However, the instruction says "valida detecção de contraindicações graves na prescrição" - we need to test the actual detection logic. We can create a test that uses a function `detect_contraindicacoes` and passes a prescription with a known contraindication (e.g., drug interaction or contraindication based on patient condition). We need to ensure the test is meaningful.

We can also create a test for allergy blocking: if patient has allergy to a medication, the system should block it. We can test that a function `verificar_alergias` returns a block.

For SOAP draft: validate structure and completeness. We can test that a function `gerar_rascunho_soap` returns a SOAP object with subjective, objective, assessment, plan sections, and that it includes required fields.

Since we don't have the actual implementation, we need to write tests that are likely to pass if the implementation follows the described architecture. We can also include some mocks or use pytest fixtures to simulate data.

We should also consider that the tests should be runnable. We can create a test file that imports from `backend.app.services.copiloto_clinico` or similar. But we don't know the exact module path. We can use relative imports? The test file is in backend/tests, so we can import from `app.services.copiloto_clinico` if the backend is a package. We can also use `from backend.app.services.copiloto_clinico import ...` if the project root is the parent of backend. To be safe, we can use `from app.services.copiloto_clinico import ...` assuming the tests are run from the backend directory. But the instruction says "backend/tests/test_copiloto_clinico.py", so the test file is inside backend/tests. The backend directory likely contains an `app` package. So we can do `from app.services.copiloto_clinico import ...`.

Alternatively, we can write tests that are independent and use mocks, but that wouldn't validate the actual implementation. The task says "valida detecção de contraindicações graves na prescrição" - it implies testing the real logic. So we need to assume the implementation exists.

Given the context, we should create a test file that is comprehensive and uses pytest. We'll define test functions that call the relevant functions and assert expected behavior. We'll also include fixtures for patient, prescription, etc.

We need to ensure the tests are precise and follow the guidelines. We'll use Pydantic models for data validation, but in tests we can use simple dicts or create instances.

Let's outline the test file:

- Imports: pytest, maybe from app.services.copiloto_clinico import detectar_contraindicacoes, verificar_alergias, gerar_rascunho_soap, etc.
- Fixtures: patient with allergies, prescription with medication that is contraindicated, etc.
- Test 1: test_detectar_contraindicacoes_graves - create a prescription with a drug that is contraindicated for a condition (e.g., pregnancy, renal failure). Assert that the function returns a list of alerts with severity "grave" or similar.
- Test 2: test_bloqueio_medicamento_por_alergia - create a patient with allergy to penicillin, prescribe amoxicillin, assert that the system blocks it (returns a block or raises an exception).
- Test 3: test_rascunho_soap_estrutura_completa - call gerar_rascunho_soap with some data, assert that the result has keys/attributes: subjetivo, objetivo, avaliacao, plano, and that they are non-empty.

We need to decide on the exact function names. We can use Portuguese names as per the domain. Let's use `detectar_contraindicacoes`, `verificar_alergias`, `gerar_rascunho_soap`. Or maybe `avaliar_prescricao` that does both. But the task separates them.

We'll write the tests with clear assertions. We'll also include type hints.

We need to ensure the test file is executable. We'll include a `if __name__ == "__main__":` block? Not necessary for pytest.

We should also consider that the tests might need to be run with `pytest` from the backend directory. We'll add a `conftest.py`? Not required.

Let's write the test file. We'll use `pytest` and `pytest.raises` for exceptions.

We'll also include some sample data using Pydantic models if available. But to avoid dependency on unknown models, we can use simple dicts or namedtuples. However, the guidelines say "tipagem estrita com Pydantic v2". So we should use Pydantic models in tests as well. We can define local Pydantic models for test data, or import from the app. Since we don't know the exact models, we can define minimal ones in the test file to simulate. But that would not test the actual models. Better to import from the app if possible.

Given the uncertainty, we can write tests that use the app's models and services. We'll assume the following structure:

- `backend/app/models/` contains Pydantic models for Patient, Prescription, Medication, Allergy, etc.
- `backend/app/services/copiloto_clinico.py` contains the functions.

We'll import from `app.models` and `app.services.copiloto_clinico`.

Let's create the test file with these imports. We'll also add a comment at the top with the file path.

We need to be careful: the instruction says "Crie backend/tests/test_copiloto_clinico.py" - so we are creating that file. We'll output the code.

We'll write the tests with descriptive names and docstrings.

Let's producethe final answer.```python
# Arquivo: backend/tests/test_copiloto_clinico.py
"""
Testes de validação dos alertas de interação e segurança do paciente (C22).

Cobre:
1. Detecção de contraindicações graves na prescrição.
2. Bloqueio de medicamento em caso de alergia declarada.
3. Estrutura e completude do rascunho SOAP gerado.

Executar com:
    pytest backend/tests/test_copiloto_clinico.py -v
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

# Importações do domínio (ajuste os caminhos conforme a estrutura real do projeto)
from app.models.paciente import Paciente, Alergia
from app.models.prescricao import Prescricao, Medicamento
from app.services.copiloto_clinico import (
    detectar_contraindicacoes,
    verificar_alergias,
    gerar_rascunho_soap,
)


# ----------------------------------------------------------------------
# Fixtures e dados de apoio
# ----------------------------------------------------------------------

class CondicaoClinica(BaseModel):
    """Modelo auxiliar para representar condição clínica do paciente."""
    cid10: str
    descricao: str


@pytest.fixture
def paciente_com_alergia() -> Paciente:
    """Paciente com alergia declarada a penicilina."""
    return Paciente(
        cns="123456789012345",
        cpf="123.456.789-00",
        nome="Maria da Silva",
        alergias=[
            Alergia(
                medicamento="Penicilina",
                reacao="Anafilaxia",
                gravidade="grave",
            )
        ],
        condicoes_clinicas=[
            CondicaoClinica(cid10="N18.0", descricao="Insuficiência renal crônica")
        ],
    )


@pytest.fixture
def paciente_sem_alergia() -> Paciente:
    """Paciente sem alergias declaradas."""
    return Paciente(
        cns="987654321012345",
        cpf="987.654.321-00",
        nome="João Souza",
        alergias=[],
        condicoes_clinicas=[],
    )


@pytest.fixture
def prescricao_contraindicada() -> Prescricao:
    """Prescrição com medicamento contraindicado para insuficiência renal grave."""
    return Prescricao(
        medicamentos=[
            Medicamento(
                nome="Ibuprofeno",
                dose="600mg",
                via="oral",
                frequencia="8/8h",
                duracao="7 dias",
            )
        ],
        observacoes="Paciente com IRC",
    )


@pytest.fixture
def prescricao_com_penicilina() -> Prescricao:
    """Prescrição contendo amoxicilina (derivado de penicilina)."""
    return Prescricao(
        medicamentos=[
            Medicamento(
                nome="Amoxicilina",
                dose="500mg",
                via="oral",
                frequencia="8/8h",
                duracao="10 dias",
            )
        ],
        observacoes="",
    )


@pytest.fixture
def dados_soap() -> dict:
    """Dados mínimos para geração do rascunho SOAP."""
    return {
        "queixa_principal": "Dor de cabeça há 3 dias",
        "historia_doenca_atual": "Paciente relata dor pulsátil bilateral, sem aura.",
        "revisao_sistemas": "Sem outras queixas.",
        "exame_fisico": "PA 120x80 mmHg, FC 72 bpm, sem alterações.",
        "hipoteses_diagnosticas": ["R51 - Cefaleia"],
        "plano_terapeutico": "Analgésico simples, hidratação, retorno em 7 dias.",
        "condutas": ["Prescrição de dipirona 500mg 6/6h por 5 dias"],
    }


# ----------------------------------------------------------------------
# Testes
# ----------------------------------------------------------------------

def test_detectar_contraindicacoes_graves(
    paciente_com_alergia: Paciente,
    prescricao_contraindicada: Prescricao,
) -> None:
    """
    Valida que a detecção de contraindicações graves identifica o uso de
    AINEs em paciente com insuficiência renal crônica (CID-10 N18.0).
    """
    alertas = detectar_contraindicacoes(
        paciente=paciente_com_alergia,
        prescricao=prescricao_contraindicada,
    )

    # Deve haver pelo menos um alerta de gravidade "grave"
    assert alertas, "Nenhum alerta de contraindicação foi gerado."

    alertas_graves = [a for a in alertas if a.gravidade == "grave"]
    assert alertas_graves, "Nenhum alerta de gravidade 'grave' foi retornado."

    # Verifica se o alerta menciona o medicamento e a condição
    alerta = alertas_graves[0]
    assert "Ibuprofeno" in alerta.medicamento
    assert "insuficiência renal" in alerta.descricao.lower()


def test_bloqueio_medicamento_por_alergia(
    paciente_com_alergia: Paciente,
    prescricao_com_penicilina: Prescricao,
) -> None:
    """
    Testa que o sistema bloqueia a prescrição de medicamento quando o
    paciente possui alergia declarada ao princípio ativo ou classe.
    """
    with pytest.raises(PermissionError) as excinfo:
        verificar_alergias(
            paciente=paciente_com_alergia,
            prescricao=prescricao_com_penicilina,
        )

    mensagem = str(excinfo.value)
    assert "Amoxicilina" in mensagem
    assert "alergia" in mensagem.lower()
    assert "Penicilina" in mensagem


def test_verificar_alergias_sem_bloqueio(
    paciente_sem_alergia: Paciente,
    prescricao_com_penicilina: Prescricao,
) -> None:
    """
    Garante que um paciente sem alergia não tem a prescrição bloqueada.
    """
    # Não deve lançar exceção
    verificar_alergias(
        paciente=paciente_sem_alergia,
        prescricao=prescricao_com_penicilina,
    )


def test_rascunho_soap_estrutura_completa(dados_soap: dict) -> None:
    """
    Valida que o rascunho SOAP gerado contém as quatro seções obrigatórias
    (Subjetivo, Objetivo, Avaliação, Plano) e que estão preenchidas.
    """
    soap = gerar_rascunho_soap(**dados_soap)

    # Verifica se o objeto possui os atributos esperados
    assert hasattr(soap, "subjetivo")
    assert hasattr(soap, "objetivo")
    assert hasattr(soap, "avaliacao")
    assert hasattr(soap, "plano")

    # Verifica se as seções não estão vazias
    assert soap.subjetivo.strip(), "Seção Subjetivo vazia."
    assert soap.objetivo.strip(), "Seção Objetivo vazia."
    assert soap.avaliacao.strip(), "Seção Avaliação vazia."
    assert soap.plano.strip(), "Seção Plano vazia."

    # Verifica se o plano contém as condutas
    assert "dipirona" in soap.plano.lower()


def test_rascunho_soap_inclui_cid_e_plano(dados_soap: dict) -> None:
    """
    Valida que o SOAP contém o código CID-10 na avaliação e o plano
    terapêutico detalhado.
    """
    soap = gerar_rascunho_soap(**dados_soap)

    # A avaliação deve conter o diagnóstico (CID-10)
    assert "R51" in soap.avaliacao

    # O plano deve conter as condutas e orientações
    assert "retorno em 7 dias" in soap.plano.lower()
    assert "hidratação" in soap.plano.lower()
```