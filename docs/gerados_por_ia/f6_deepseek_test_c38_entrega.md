We need to create a test file for the MedIA project: backend/tests/test_copiloto_clinico.py. The task says: "1) valida detecção de contraindicações graves na prescrição; 2) testa bloqueio de medicamento caso o paciente tenha alergia declarada; 3) valida estrutura e completude do rascunho SOAP gerado."

We need to write tests for a "copiloto clínico" (clinical copilot) module. We need to infer the expected functionality. The project uses Pydantic v2, SQLAlchemy 2.0, Python 3.12, SUS/APS patterns (CIAP-2, CID-10, SOAP, CNS/CPF). We need to create tests that validate these features.

We should create a test file that imports the relevant modules from the backend. Since we don't have the actual implementation, we need to write tests that would pass if the implementation is correct. We'll assume there are classes/functions like `ClinicalCopilot`, `Prescription`, `Patient`, `Allergy`, `SOAPNote`, etc. We need to design tests that check:

1. Detection of serious contraindications in prescription: e.g., prescribing a drug that is contraindicated for a condition (like pregnancy, renal impairment, etc.) should raise an alert or block.

2. Blocking medication if patient has declared allergy: if patient has allergy to a substance, the copilot should block that medication.

3. Validate structure and completeness of generated SOAP draft: check that the SOAP note has sections Subjective, Objective, Assessment, Plan, and contains required fields.

We need to write tests using pytest. We'll need to mock or use fixtures. Since we don't have the actual code, we'll write tests that assume certain interfaces. We'll also need to ensure the tests are runnable with pytest.

We should also consider the architecture: Pydantic v2 models, SQLAlchemy 2.0. Tests might use in-memory SQLite or mocks.

Let's outline the test file:

- Imports: pytest, maybe from backend modules.
- Fixtures: create a patient with allergies, a prescription with a contraindicated drug, etc.
- Test functions:
  - test_detect_serious_contraindication
  - test_block_medication_for_allergy
  - test_soap_draft_structure_and_completeness

We need to decide on the exact API. Since we are writing tests, we can define expected behavior. For example:

- There is a class `CopilotoClinico` with methods:
  - `avaliar_prescricao(prescricao, paciente)` -> returns a list of alerts or raises an exception.
  - `gerar_soap(consulta)` -> returns a SOAPNote object.

Alternatively, we can have functions like `check_contraindications`, `check_allergies`, `generate_soap`.

Given the task says "valida detecção de contraindicações graves na prescrição" and "testa bloqueio de medicamento caso o paciente tenha alergia declarada", we can assume there is a service that processes prescriptions and returns a result indicating whether it's safe or not.

Let's design a simple interface:

- `Prescription` model: has `medicamentos` (list of `Medicamento`), `paciente_id`, etc.
- `Medicamento` model: has `principio_ativo`, `dosagem`, etc.
- `Paciente` model: has `alergias` (list of `Alergia`), `condicoes` (list of `Condicao`), etc.
- `Alergia` model: has `substancia`.
- `Condicao` model: has `cid10` or `descricao`.

- `CopilotoClinico` class with:
  - `avaliar_prescricao(prescricao, paciente) -> ResultadoAvaliacao` where `ResultadoAvaliacao` has `contraindicacoes` (list), `alergias` (list), `pode_prescrever` (bool).
  - `gerar_rascunho_soap(consulta) -> SOAPNote`.

We'll write tests that instantiate these models with sample data and assert the behavior.

Since we don't have the actual implementation, we need to write tests that would fail if the implementation is missing, but we can also write them in a way that they are self-contained and can be run with mocks. However, the task says "crie backend/tests/test_copiloto_clinico.py" - we are to create the test file. We should write tests that are meaningful and would pass with a correct implementation.

We'll assume the project has these models already defined. We'll import them. If they don't exist, the tests will fail, but that's okay because the task is to create tests for the feature.

Let's write the test file with clear structure.

We'll use pytest fixtures to create sample data.

We'll also need to ensure we use Pydantic v2 style (e.g., `model_config = ConfigDict(...)`). But for tests, we just use the models.

Let's craft the code.

First, we'll define the test file with imports:

```python
import pytest
from pydantic import ValidationError
from backend.models.paciente import Paciente, Alergia, Condicao
from backend.models.prescricao import Prescricao, Medicamento
from backend.models.soap import SOAPNote
from backend.services.copiloto_clinico import CopilotoClinico, ResultadoAvaliacao
```

But we don't know the exact paths. We can use relative imports if the tests are in the backend/tests directory. Usually, tests are run from the project root, so we can use `from backend...` or `from app...`. The task says "Projeto MedIA", so likely the backend is a package. We'll use `backend` as the top-level package.

Alternatively, we can use `from ..models...` if tests are inside backend/tests. But it's safer to use absolute imports assuming the project root is in sys.path.

We'll write:

```python
from backend.models.paciente import Paciente, Alergia, Condicao
from backend.models.prescricao import Prescricao, Medicamento
from backend.models.soap import SOAPNote
from backend.services.copiloto_clinico import CopilotoClinico, ResultadoAvaliacao
```

Now, we need to define fixtures.

Fixture for a patient with allergy to penicillin and a condition of pregnancy (CID-10 Z33).

Fixture for a prescription containing amoxicillin (contraindicated for penicillin allergy) and another drug that is contraindicated in pregnancy (e.g., isotretinoin - but that's not typical; maybe warfarin or ACE inhibitors). We'll use a known contraindication: e.g., "Ibuprofeno" in pregnancy (third trimester) or "Losartana" in pregnancy.

We'll create a prescription with two medications: one that the patient is allergic to, and one that is contraindicated due to a condition.

Then we test:

- `resultado = copiloto.avaliar_prescricao(prescricao, paciente)`
- Assert that `resultado.pode_prescrever` is False.
- Assert that `resultado.alergias` contains the medication with allergy.
- Assert that `resultado.contraindicacoes` contains the medication with contraindication.

For the SOAP test, we'll create a consulta (medical visit) with subjective, objective, assessment, plan data, and call `copiloto.gerar_rascunho_soap(consulta)`. Then assert that the returned SOAPNote has all sections filled, and maybe that it includes the patient's CNS/CPF.

We need to define what "estrutura e completude" means. We'll check that the SOAPNote has fields: subjetivo, objetivo, avaliacao, plano, and that they are non-empty. Also check that it includes patient identification (CNS/CPF) and date.

Let's design the SOAPNote model:

```python
class SOAPNote(BaseModel):
    paciente_id: str
    data: datetime
    subjetivo: str
    objetivo: str
    avaliacao: str
    plano: str
```

We'll assert that all fields are present and non-empty.

Now, let's write the test file.

We'll also need to consider that the copiloto might raise exceptions instead of returning a result. But we'll assume it returns a result object.

Let's write the code.

We'll also add a test for the allergy blocking specifically: maybe the copiloto should not allow the prescription to be created, i.e., it raises an exception. But the task says "testa bloqueio de medicamento caso o paciente tenha alergia declarada". So we can test that the copiloto returns an alert and sets `pode_prescrever` to False.

We'll write two separate tests: one for contraindication detection, one for allergy blocking, and one for SOAP.

Let's also include a test for the structure of the result.

Now, let's write the file content.

We'll need to ensure the tests are runnable. We'll use `pytest`.

We'll also add a `conftest.py`? Not necessary.

Let's produce the final answer with the code block.

We'll include comments explaining each test.

We'll also add a `if __name__ == "__main__":`? Not needed.

Let's write.```python
# Arquivo: backend/tests/test_copiloto_clinico.py
"""
Testes de validação dos alertas de interação e segurança do paciente (C38).

Cobre:
1. Detecção de contraindicações graves na prescrição.
2. Bloqueio de medicamento quando o paciente possui alergia declarada.
3. Estrutura e completude do rascunho SOAP gerado.

Executar com: pytest backend/tests/test_copiloto_clinico.py -v
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.models.paciente import Alergia, Condicao, Paciente
from backend.models.prescricao import Medicamento, Prescricao
from backend.models.soap import SOAPNote
from backend.services.copiloto_clinico import CopilotoClinico, ResultadoAvaliacao


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def paciente_com_alergia_e_condicao():
    """Paciente com alergia a penicilina e condição de gravidez (CID-10 Z33)."""
    return Paciente(
        id="12345678901",  # CPF fictício
        nome="Maria da Silva",
        cns="123456789012345",  # CNS fictício
        data_nascimento=datetime(1990, 5, 10),
        alergias=[
            Alergia(substancia="Penicilina", gravidade="grave"),
        ],
        condicoes=[
            Condicao(cid10="Z33", descricao="Gravidez"),
        ],
    )


@pytest.fixture
def prescricao_com_contraindicacao_e_alergia():
    """
    Prescrição contendo:
    - Amoxicilina (alergia à penicilina)
    - Losartana (contraindicado na gravidez)
    """
    return Prescricao(
        paciente_id="12345678901",
        medicamentos=[
            Medicamento(
                principio_ativo="Amoxicilina",
                dosagem="500mg",
                via="oral",
                posologia="8/8h por 7 dias",
            ),
            Medicamento(
                principio_ativo="Losartana",
                dosagem="50mg",
                via="oral",
                posologia="12/12h",
            ),
        ],
    )


@pytest.fixture
def consulta_para_soap():
    """Dados de uma consulta para geração do rascunho SOAP."""
    return {
        "paciente_id": "12345678901",
        "cns": "123456789012345",
        "data": datetime(2025, 3, 20, 14, 30),
        "subjetivo": "Paciente relata dor de cabeça há 3 dias, piora com luz.",
        "objetivo": "PA 120x80 mmHg, FC 72 bpm, pupilas isocóricas.",
        "avaliacao": "Enxaqueca sem aura (G43.0).",
        "plano": "Prescrito paracetamol 750mg 6/6h por 5 dias. Orientado hidratação.",
    }


# -----------------------------------------------------------------------------
# Testes
# -----------------------------------------------------------------------------

class TestContraindicacoesGraves:
    """Testes para detecção de contraindicações graves na prescrição."""

    def test_detecta_contraindicacao_por_condicao(
        self,
        paciente_com_alergia_e_condicao,
        prescricao_com_contraindicacao_e_alergia,
    ):
        """Deve identificar a losartana como contraindicada na gravidez."""
        copiloto = CopilotoClinico()
        resultado = copiloto.avaliar_prescricao(
            prescricao=prescricao_com_contraindicacao_e_alergia,
            paciente=paciente_com_alergia_e_condicao,
        )

        assert isinstance(resultado, ResultadoAvaliacao)
        assert resultado.pode_prescrever is False

        # Verifica se a losartana está na lista de contraindicações
        contraindicados = [c.principio_ativo for c in resultado.contraindicacoes]
        assert "Losartana" in contraindicados

    def test_contraindicacao_grave_impede_prescricao(
        self,
        paciente_com_alergia_e_condicao,
        prescricao_com_contraindicacao_e_alergia,
    ):
        """A presença de contraindicação grave deve bloquear a prescrição."""
        copiloto = CopilotoClinico()
        resultado = copiloto.avaliar_prescricao(
            prescricao=prescricao_com_contraindicacao_e_alergia,
            paciente=paciente_com_alergia_e_condicao,
        )

        assert resultado.pode_prescrever is False
        assert len(resultado.contraindicacoes) > 0


class TestBloqueioPorAlergia:
    """Testes para bloqueio de medicamento por alergia declarada."""

    def test_bloqueia_medicamento_por_alergia(
        self,
        paciente_com_alergia_e_condicao,
        prescricao_com_contraindicacao_e_alergia,
    ):
        """Deve bloquear a amoxicilina por alergia à penicilina."""
        copiloto = CopilotoClinico()
        resultado = copiloto.avaliar_prescricao(
            prescricao=prescricao_com_contraindicacao_e_alergia,
            paciente=paciente_com_alergia_e_condicao,
        )

        assert resultado.pode_prescrever is False

        alergias_detectadas = [a.principio_ativo for a in resultado.alergias]
        assert "Amoxicilina" in alergias_detectadas

    def test_alergia_impede_prescricao_mesmo_sem_outras_contraindicacoes(
        self,
        paciente_com_alergia_e_condicao,
    ):
        """Somente a alergia já deve ser suficiente para bloquear."""
        prescricao = Prescricao(
            paciente_id="12345678901",
            medicamentos=[
                Medicamento(
                    principio_ativo="Amoxicilina",
                    dosagem="500mg",
                    via="oral",
                    posologia="8/8h",
                )
            ],
        )
        copiloto = CopilotoClinico()
        resultado = copiloto.avaliar_prescricao(
            prescricao=prescricao,
            paciente=paciente_com_alergia_e_condicao,
        )

        assert resultado.pode_prescrever is False
        assert len(resultado.alergias) == 1
        assert resultado.alergias[0].principio_ativo == "Amoxicilina"


class TestRascunhoSOAP:
    """Testes para estrutura e completude do rascunho SOAP."""

    def test_estrutura_soap_completa(self, consulta_para_soap):
        """O rascunho SOAP deve conter todas as seções preenchidas."""
        copiloto = CopilotoClinico()
        soap = copiloto.gerar_rascunho_soap(consulta_para_soap)

        assert isinstance(soap, SOAPNote)
        assert soap.subjetivo.strip() != ""
        assert soap.objetivo.strip() != ""
        assert soap.avaliacao.strip() != ""
        assert soap.plano.strip() != ""

    def test_soap_inclui_identificacao_do_paciente(self, consulta_para_soap):
        """O SOAP deve conter CNS/CPF e data da consulta."""
        copiloto = CopilotoClinico()
        soap = copiloto.gerar_rascunho_soap(consulta_para_soap)

        assert soap.paciente_id == "12345678901"
        assert soap.cns == "123456789012345"
        assert soap.data == datetime(2025, 3, 20, 14, 30)

    def test_soap_nao_aceita_campos_vazios(self):
        """Se alguma seção estiver vazia, deve gerar erro de validação."""
        copiloto = CopilotoClinico()
        consulta_incompleta = {
            "paciente_id": "12345678901",
            "cns": "123456789012345",
            "data": datetime(2025, 3, 20, 14, 30),
            "subjetivo": "",
            "objetivo": "PA 120x80 mmHg",
            "avaliacao": "Enxaqueca",
            "plano": "Paracetamol",
        }

        with pytest.raises(ValidationError):
