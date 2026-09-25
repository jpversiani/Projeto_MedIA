We need to create backend/tests/test_sisab_export.py for the MedIA project. The task: "Testes de Validação Estrutural da Exportação SISAB (C8)" - structural validation tests for SISAB export. We need to test integrity of fichas (forms): 1) validation of mandatory filling of CIAP-2/CID-10; 2) rejection of batches with invalid CNS or CNES; 3) generation of consistent payload.

We need to understand the context: MedIA is a project, likely a healthcare system. SISAB is the Brazilian primary care information system. Fichas are forms used in e-SUS APS (like Ficha de Atendimento, Ficha de Cadastro Individual, etc.). CIAP-2 is International Classification of Primary Care, 2nd edition. CID-10 is ICD-10. CNS is Cartão Nacional de Saúde (National Health Card), CNES is Cadastro Nacional de Estabelecimentos de Saúde (National Registry of Health Establishments). SOAP is Subjective, Objective, Assessment, Plan method.

We need to write tests that validate the export of these fichas. The tests should ensure that the export module correctly validates mandatory fields, rejects invalid CNS/CNES, and generates consistent payloads.

We need to infer the structure of the backend. Likely there is a service or module responsible for SISAB export. We need to test it. Since we are only asked to create the test file, we need to design tests that would pass given a correct implementation. But we also need to make sure the tests are meaningful and cover the requirements.

We should define fixtures and mock data. We need to know what the export function looks like. Since we don't have the actual code, we need to make reasonable assumptions. The test file should import from the actual backend modules. We can create tests that use the public API of the export service.

Let's think about the structure: The project likely has a module like `backend/app/services/sisab_export.py` or `backend/app/api/v1/sisab.py`. The tests should be placed in `backend/tests/test_sisab_export.py`. We'll need to import the relevant functions/classes.

We can design tests that:

1. Test that when creating a ficha (e.g., FichaAtendimento), if CIAP-2 or CID-10 is missing, validation fails. But note: "validação de preenchimento obrigatório de CIAP-2/CID-10" - mandatory filling of CIAP-2/CID-10. In SISAB, for atendimento, you must fill either CIAP-2 or CID-10? Actually, in e-SUS APS, for Ficha de Atendimento, the "Conduta" and "Diagnóstico" fields: you can use CIAP-2 or CID-10. There is a requirement that at least one must be filled? Or both? The task says "preenchimento obrigatório de CIAP-2/CID-10" - mandatory filling of CIAP-2/CID-10. Could mean that each ficha must have either CIAP-2 or CID-10 (or both) as a mandatory field. We'll test that if both are missing, validation fails.

2. Rejection of batches with invalid CNS or CNES: The export service likely accepts a batch of fichas and validates them. If any ficha has invalid CNS (e.g., wrong check digit) or invalid CNES, the batch should be rejected. We need to test that.

3. Generation of consistent payload: The export service should generate a JSON payload (or XML) that is consistent with the input data. We need to test that the payload contains all required fields, correct structure, and matches the original data.

We'll need to create test data. We can use Pydantic models to represent the fichas. We'll need to know the models. Since we don't have them, we can define our own test models? But the tests should test the actual code. We can assume there are models like `FichaAtendimento` in `backend/app/models/sisab.py` or similar. We can import them.

Alternatively, we can write tests that use the export service's public functions, and we can create mock data using dictionaries that are validated by the service. The service might use Pydantic to validate input.

Given the instructions, we need to produce a test file that is complete and executable. We'll need to make assumptions about the codebase. We can structure the tests to be robust: use pytest fixtures, use `pytest.raises` for validation errors, and use `assert` for payload consistency.

We should also consider that the tests might need to be run in the project's environment. We'll include imports that are likely present.

Let's design the test file:

- Import pytest, maybe from pydantic import ValidationError.
- Import the relevant modules: from app.services.sisab_export import export_fichas, validate_ficha, etc. But we don't know the exact names. We can use `from app.services import sisab_export` and then access functions. Or we can use `from app.schemas.sisab import FichaAtendimento` etc.

Since we are not given the actual code, we need to make the tests generic enough to work with a reasonable implementation. But the task says "Crie backend/tests/test_sisab_export.py testando integridade das fichas". We need to create the test file. It's okay to assume the existence of certain functions/classes. We can write tests that would fail if the implementation is missing, but that's expected.

We can also include comments explaining the assumptions.

Let's outline:

```python
# backend/tests/test_sisab_export.py
"""
Testes de Validação Estrutural da Exportação SISAB (C8)
"""

import pytest
from pydantic import ValidationError

# Importações do módulo de exportação SISAB
from app.services.sisab_export import (
    export_fichas,
    validate_ficha,
    validate_batch,
    generate_payload,
)
from app.schemas.sisab import FichaAtendimento, FichaCadastroIndividual
from app.core.exceptions import InvalidCNSException, InvalidCNESException
```

But we need to be careful: if these imports don't exist, the tests will fail to collect. However, the task is to create the test file, so it's okay to assume the modules exist. We can also use `pytest.importorskip` to skip if not available, but that would hide failures. Better to assume they exist.

Alternatively, we can write tests that use the actual models and services that we expect to be implemented. We can also create our own minimal models in the test file to simulate, but that would not test the actual code. The instruction says "testando integridade das fichas" - testing the integrity of the fichas. So we need to test the actual export logic.

Given the context, I'll write tests that import from `app.services.sisab_export` and `app.schemas.sisab`. I'll define fixtures with valid and invalid data.

Let's think about the structure of the export service. It might have a function like `export_fichas(fichas: list[Ficha]) -> dict` that validates and returns a payload. Or it might have separate validation functions.

We can write tests:

1. Test mandatory CIAP-2/CID-10:
   - Create a FichaAtendimento with no CIAP-2 and no CID-10.
   - Call `validate_ficha` or `export_fichas` and expect a ValidationError.
   - Also test that with either CIAP-2 or CID-10 present, validation passes.

2. Test invalid CNS/CNES:
   - Create a ficha with invalid CNS (e.g., wrong check digit).
   - Create a batch with that ficha and expect rejection.
   - Similarly for CNES.

3. Test payload consistency:
   - Create a valid ficha with known data.
   - Call `generate_payload` or `export_fichas` and verify the output contains the expected fields and values.

We need to know the exact field names. We can infer from SISAB standard: Ficha de Atendimento has fields like `cns`, `cnes`, `data_atendimento`, `cid10`, `ciap2`, etc. We'll use those.

Let's define some sample data.

We'll also need to handle the fact that CNS and CNES have validation algorithms. We can use known valid test numbers. For CNS, the format is 15 digits, with check digit. There are known valid test CNS numbers. For example, 898001281410004 is a valid test CNS? Actually, we can use a known valid one: 700000000000000? No, that's not valid. We can use a generator or a known valid CNS from documentation. Let's search memory: A valid CNS is 15 digits, the first digit is 1,2,3,4,5,7,8,9 (not 0 or 6). The check digit is calculated using mod 11. Example: 898001281410004? Let's verify: I recall that 898001281410004 is a valid CNS used in tests. Actually, I've seen that in e-SUS documentation. Let's use that. For CNES, it's 7 digits. A valid CNES example: 0000001? But CNES has a check digit? Actually, CNES is just a 7-digit number, but there is a check digit? I think CNES is 7 digits without check digit? Wait, CNES is the National Registry of Health Establishments, it's a 7-digit number. There is no check digit? Actually, there is a validation algorithm for CNES? I'm not sure. Let's check: CNES is a 7-digit number, and the first digit indicates the type. There is no check digit. But the task says "CNS ou CNES inválido" - invalid CNS or CNES. So we need to test that invalid values are rejected. For CNES, invalid could be a number with wrong length or non-numeric. We can test that.

We'll write tests that use invalid CNS (e.g., wrong length, or invalid check digit) and invalid CNES (e.g., 12345 - too short, or 12345678 - too long).

Now, let's design the test file.

We'll use pytest fixtures to create valid and invalid fichas.

We'll need to know the Pydantic models. We can assume they have fields like:

- `cns`: str
- `cnes`: str
- `data_atendimento`: date
- `cid10`: Optional[str]
- `ciap2`: Optional[str]
- etc.

We'll create a valid ficha with both cid10 and ciap2, and one with only one.

For the payload consistency test, we'll call the export function and check that the output is a dict with a list of fichas, each containing the same data.

We should also test that the export function validates the batch as a whole, i.e., if any ficha is invalid, the whole batch is rejected.

Let's write the code.

First, we need to define the imports. Since we don't know the exact module paths, we'll use common patterns. We'll also include a `pytestmark` to mark the tests.

We'll also need to handle the case where the modules are not yet implemented. We can use `pytest.importorskip` to skip if not available, but that would not be ideal. However, the task is to create the test file, so we can assume the modules exist. We'll write the tests as if they exist.

Let's create the file:

```python
# backend/tests/test_sisab_export.py
"""
Testes de Validação Estrutural da Exportação SISAB (C8)

Este módulo contém testes para garantir a integridade das fichas exportadas
para o SISAB, incluindo validação de campos obrigatórios (CIAP-2/CID-10),
rejeição de lotes com CNS/CNES inválidos e consistência do payload gerado.
"""

import pytest
from datetime import date
from pydantic import ValidationError

# Importações do domínio SISAB
from app.schemas.sisab import FichaAtendimento
from app.services.sisab_export import (
    export_fichas,
    validate_ficha,
    validate_batch,
    generate_payload,
)
from app.core.exceptions import (
    InvalidCNSException,
    InvalidCNESException,
    ValidationException,
)
```

Now, fixtures:

```python
@pytest.fixture
def ficha_valida():
    """Ficha de atendimento válida com CIAP-2 e CID-10 preenchidos."""
    return FichaAtendimento(
        cns="898001281410004",
        cnes="0001234",
        data_atendimento=date(2024, 5, 10),
        ciap2="A01",
        cid10="A09",
        # outros campos obrigatórios...
    )

@pytest.fixture
def ficha_sem_diagnostico():
    """Ficha sem CIAP-2 e sem CID-10 (inválida)."""
    return FichaAtendimento(
        cns="898001281410004",
        cnes="0001234",
        data_atendimento=date(2024, 5, 10),
        ciap2=None,
        cid10=None,
    )

@pytest.fixture
def ficha_cns_invalido():
    """Ficha com CNS inválido."""
    return FichaAtendimento(
        cns="123456789012345",  # inválido
        cnes="0001234",
        data_atendimento=date(2024, 5, 10),
        ciap2="A01",
        cid10="A09",
    )

@pytest.fixture
def ficha_cnes_invalido():
    """Ficha com CNES inválido."""
    return FichaAtendimento(
        cns="898001281410004",
        cnes="12345",  # inválido (menos de 7 dígitos)
        data_atendimento=date(2024, 5, 10),
        ciap2="A01",
        cid10="A09",
    )
```

Now, tests:

Test 1: Mandatory CIAP-2/CID-10.

```python
def test_validacao_obrigatoria_ciap_cid(ficha_sem_diagnostico):
    """Deve rejeitar ficha sem CIAP-2 ou CID-10."""
    with pytest.raises(ValidationError):
        validate_ficha(ficha_sem_diagnostico)
```

But note: if the model itself enforces that at least one is present, then creating the ficha would raise ValidationError. In that case, the fixture would fail. We need to decide: the validation might be at the model level or at the service level. The task says "validação de preenchimento obrigatório de CIAP-2/CID-10" - it could be in the schema. We'll test both: if the model raises, then the fixture creation would raise. We can adjust: we can create the ficha using `FichaAtendimento.model_validate` with a dict, and expect ValidationError. Or we can create a dict and pass to the service.

Better: we can test the service's validation function. We'll assume that `validate_ficha` takes a dict or a model and raises `ValidationException` if missing. But we can also test that the model itself enforces it.

To be safe, we can write tests that use a dict and call `validate_ficha` or `export_fichas`. Let's design:

- `validate_ficha(ficha: dict) -> bool` or raises.
- `export_fichas(fichas: list[dict]) -> dict` validates and returns payload.

We'll use dicts to avoid model-level validation issues. But we need to know the expected structure. We can use `FichaAtendimento` model to validate the dict, but if the model enforces the mandatory fields, then the dict would be invalid. So we can test that the model rejects it.

Let's write tests that use the model directly:

```python
def test_ficha_sem_diagnostico_invalida():
    with pytest.raises(ValidationError):
        FichaAtendimento(
            cns="898001281410004",
            cnes="0001234",
            data_atendimento=date(2024, 5, 10),
            ciap2=None,
            cid10=None,
        )
```

But this tests the model, not the export service. The task says "Testes de Validação Estrutural da Exportação SISAB" - structural validation of the export. So we should test the export service's validation.

Let's assume the export service has a function `validate_ficha` that takes a dict and returns a validated model or raises. We'll write tests for that.

We'll also need to test that a batch with invalid CNS/CNES is rejected. We'll use `validate_batch` or `export_fichas`.

Let's define the tests:

```python
class TestValidacaoObrigatoriaCIAPCID:
    def test_ficha_sem_ciap_e_cid_gera_erro(self):
        ficha = {
            "cns": "898001281410004",
            "cnes": "0001234",
            "data_atendimento": "2024-05-10",
            # sem ciap2 e cid10
        }
        with pytest.raises(ValidationError):
            validate_ficha(ficha)

    def test_ficha_com_ciap_ou_cid_e_valida(self):
        ficha = {
            "cns": "898001281410004",
            "cnes": "0001234",
            "data_atendimento": "2024-05-10",
            "ciap2": "A01",
        }
        assert validate_ficha(ficha) is True
```

But we need to know the exact exception. The service might raise a custom `ValidationException`. We can use `pytest.raises(Exception)` but better to be specific. We'll assume `ValidationError` from Pydantic or a custom exception.

Given the instructions mention Pydantic v2, we can use `ValidationError`.

Now, test invalid CNS/CNES:

```python
class TestRejeicaoDeLotesComCNSOuCNESInvalido:
    def test_lote_com_cns_invalido_rejeitado(self, ficha_cns_invalido):
        with pytest.raises(InvalidCNSException):
            validate_batch([ficha_cns_invalido])

    def test_lote_com_cnes_invalido_rejeit