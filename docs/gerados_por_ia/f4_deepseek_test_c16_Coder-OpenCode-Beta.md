We need to create backend/tests/test_sisab_export.py for the MedIA project. The task: "Testes de Validação Estrutural da Exportação SISAB (C16)" - structural validation tests for SISAB export. We need to test integrity of fichas (records): 1) validation of mandatory filling of CIAP-2/CID-10; 2) rejection of batches with invalid CNS or CNES; 3) generation of consistent payload.

We need to write tests. We need to understand the project structure. Since we are only given the task, we must infer the codebase. Likely there is a module for SISAB export that generates payloads (maybe XML or JSON) for SISAB (Sistema de Informação em Saúde para a Atenção Básica). The tests should validate that the export logic enforces mandatory fields, validates CNS/CNES, and produces consistent payloads.

We need to create a test file. We should assume there is a service or function that handles export. We'll need to mock or use actual classes. Since we don't have the actual code, we need to design tests that are plausible and follow the architecture. We can create tests that import from the backend modules. We need to define what we are testing.

Let's think: The project MedIA likely has models for Ficha (record) with fields like patient CNS, professional CNS, CNES, procedures, diagnoses (CIAP-2 or CID-10). The export to SISAB likely involves generating a payload (maybe XML) that must conform to SISAB schema.

We need to write tests that:

1) Validate mandatory filling of CIAP-2/CID-10: For each ficha, at least one diagnosis code (CIAP-2 or CID-10) must be present. If missing, the export should raise an error or the validation should fail.

2) Rejection of batches with invalid CNS or CNES: The export should validate that CNS numbers are valid (check digit) and CNES is valid (maybe length/format). If any invalid, the batch should be rejected.

3) Generation of consistent payload: The payload should contain all required fields, correctly formatted, and consistent with the input data.

We need to write pytest tests. We'll need to create fixtures, maybe use factories. Since we don't have the actual implementation, we can write tests that assume certain interfaces. We should make them robust and self-contained.

We can create a test module that imports from the app's services. We'll need to define some dummy data.

Let's propose a structure:

- backend/tests/test_sisab_export.py

We'll use pytest, pydantic, maybe sqlalchemy. We'll create tests that:

- Use a fixture to create a valid ficha (or a batch of fichas).
- Test that export raises ValidationError when CIAP-2/CID-10 missing.
- Test that export rejects invalid CNS/CNES.
- Test that export generates payload with correct structure.

We need to know the function names. We can assume there is a service like `SISABExportService` or a function `generate_sisab_payload(fichas)`. We'll write tests that import from `backend.app.services.sisab_export` or similar. Since we don't know, we can use a placeholder and note that the tests are based on expected interface.

Alternatively, we can write tests that are more generic, using dependency injection. But the task says "crie backend/tests/test_sisab_export.py testando integridade das fichas". So we need to produce a test file.

We should also follow the architecture: Python 3.12, Pydantic v2, SQLAlchemy 2.0. So we can use Pydantic models for validation.

Let's design the test file with clear sections.

We'll need to create some sample data. We can define a Ficha model (maybe from the app) or create a simple dataclass. But to test the export, we need to have the actual export function. Since we don't have it, we can mock it or create a fake implementation? No, the test should test the real code. But we are writing tests for a project that presumably already has the code. We need to write tests that will pass when the code is correct. So we need to assume the existence of certain functions and models.

Let's search our memory: In a typical FastAPI project, there might be a module `backend/app/schemas/sisab.py` with Pydantic models, and `backend/app/services/sisab_export.py` with export logic. We'll write tests that import from these.

We'll define:

```python
from backend.app.schemas.sisab import FichaSISAB, LoteSISAB
from backend.app.services.sisab_export import export_lote, validar_cns, validar_cnes
```

But we don't know if these exist. To be safe, we can write tests that are self-contained and use a mock for the export function? No, the task is to test the export. We need to test the actual implementation. We can write tests that will fail if the implementation is missing, but that's okay; the tests are meant to be run in the project.

Given the instruction "Execute com precisão conforme as diretrizes", we should produce a test file that is well-structured and follows best practices. We can include comments explaining the expected behavior.

Let's create a test file with:

- Imports: pytest, pydantic, maybe datetime, etc.
- Fixtures: sample valid ficha data, invalid data.
- Tests for each requirement.

We'll need to decide on the exact validation rules for CNS and CNES. CNS (Cartão Nacional de Saúde) has a specific check digit algorithm. CNES (Cadastro Nacional de Estabelecimentos de Saúde) is a 7-digit number. We can implement a simple validation function in the test to check if the export function uses it. But we are testing the export, so we need to verify that the export function rejects invalid ones. We can create invalid CNS/CNES and assert that the export raises an error.

We'll also test that the payload is consistent: e.g., the payload contains the same number of records, the fields are correctly mapped, etc.

Let's outline the test file:

```python
# Arquivo: backend/tests/test_sisab_export.py
"""
Testes de validação estrutural da exportação SISAB (C16).
"""

import pytest
from pydantic import ValidationError
from datetime import date, datetime

# Importações do projeto (ajustar conforme estrutura real)
from backend.app.schemas.sisab import FichaSISAB, LoteSISAB
from backend.app.services.sisab_export import (
    export_lote,
    validar_cns,
    validar_cnes,
    gerar_payload,
)
```

But we need to be careful: if these modules don't exist, the test file will have import errors. However, the task is to create the test file, not the implementation. We can assume the implementation exists. We'll write the tests accordingly.

Alternatively, we can write tests that use monkeypatching to simulate the export function? No, that would not test the real thing.

Let's think about what the export function might look like. It could be a function that takes a list of FichaSISAB objects and returns a payload (e.g., XML string). The validation might be done via Pydantic validators in the schema. So we can test the schema validation directly.

For requirement 1: "validação de preenchimento obrigatório de CIAP-2/CID-10". This could be a Pydantic validator on FichaSISAB that ensures at least one of ciap2 or cid10 is present. So we can test that creating a FichaSISAB without both raises ValidationError.

For requirement 2: "rejeição de lotes com CNS ou CNES inválido". This could be a validator on LoteSISAB or on the export function that checks each ficha's CNS and CNES. We can test that a LoteSISAB with invalid CNS/CNES raises ValidationError.

For requirement 3: "geração de payload consistente". This could be a function that converts a LoteSISAB to XML/JSON. We can test that the payload contains the expected data and is well-formed.

We'll write tests accordingly.

Let's define sample data:

- Valid CNS: We need a valid CNS number. The CNS has 15 digits, with a check digit. We can use a known valid CNS: 123456789012345? Let's check the algorithm. Actually, the CNS check digit is calculated using the first 14 digits, then the 15th is the check digit. There are known examples. We can use "123456789012345" but we need to ensure it's valid. Let's compute: For CNS, the check digit is the remainder of the sum of the products of each digit (from left to right) with weights 15 down to 2, divided by 11. The check digit is 11 - remainder, or 0 if remainder is 0. Let's compute for 12345678901234? Actually, we can use a known valid CNS from the internet: "123456789012345" might not be valid. Let's compute quickly.

We can implement a function in the test to generate a valid CNS. But we need to test the export function's validation. We can create a valid CNS by using a known algorithm. Let's do that.

CNS algorithm: The CNS number is composed of 15 digits. The first digit is 1, 2, 3, 4, 5, or 7 (depending on type). The check digit is calculated as follows:

- Multiply each of the first 14 digits by a weight from 15 down to 2.
- Sum the products.
- The remainder is sum % 11.
- If remainder is 0, check digit is 0; otherwise check digit = 11 - remainder.

Let's test with a known valid CNS: "123456789012345"? Let's compute:

Digits: 1,2,3,4,5,6,7,8,9,0,1,2,3,4,5 (first 14: 1,2,3,4,5,6,7,8,9,0,1,2,3,4)
Weights: 15,14,13,12,11,10,9,8,7,6,5,4,3,2
Products: 15,28,39,48,55,60,63,64,63,0,5,8,9,8 = sum? Let's sum: 15+28=43, +39=82, +48=130, +55=185, +60=245, +63=308, +64=372, +63=435, +0=435, +5=440, +8=448, +9=457, +8=465. 465 % 11 = 465 - 11*42=465-462=3. Check digit = 11-3=8. So the valid CNS would be 123456789012348. So "123456789012345" is invalid. We'll use "123456789012348" as valid.

For CNES: It's a 7-digit number. We can use "1234567" as valid (any 7-digit number). Invalid: "123456" (6 digits) or "12345678" (8 digits) or non-numeric.

Now, let's write the test file.

We'll need to import the actual modules. Since we don't know the exact paths, we'll use a try-except to handle import errors? No, we should just write the imports as expected. The test file will be part of the project, so the paths should match.

Let's assume the project structure:

- backend/app/schemas/sisab.py
- backend/app/services/sisab_export.py

We'll write tests that import from these.

We'll also need to create fixtures for valid and invalid data.

Let's write the code.

We'll use Pydantic v2 style: `model_config = ConfigDict(...)` etc.

We'll write tests:

1. `test_ficha_sem_ciap_ou_cid_rejeitada`: Create a FichaSISAB with no ciap2 and no cid10, expect ValidationError.

2. `test_ficha_com_ciap_aceita`: Create with ciap2 only, should pass.

3. `test_ficha_com_cid_aceita`: Create with cid10 only, should pass.

4. `test_lote_com_cns_invalido_rejeitado`: Create a LoteSISAB with a ficha that has invalid CNS, expect ValidationError.

5. `test_lote_com_cnes_invalido_rejeitado`: Similar.

6. `test_lote_valido_gera_payload_consistente`: Create a valid LoteSISAB, call export function, assert payload contains expected data.

We'll need to define the FichaSISAB and LoteSISAB models. But we are not writing the models, just the tests. So we'll assume they exist.

We'll also need to define the export function. We'll assume `export_lote(lote)` returns a string (XML) or dict.

Let's write the test file with detailed comments.

We'll also include a helper function to generate a valid CNS.

Let's implement the CNS validation in the test to create valid numbers.

We'll also test that the export function validates CNS/CNES even if the schema doesn't. But we can test both.

Let's write the code.

We'll need to be careful with Pydantic v2: ValidationError is raised when creating an object with invalid data. We'll use `with pytest.raises(ValidationError)`.

For the payload consistency test, we'll need to know what the payload looks like. We can assert that the payload contains the CNS, CNES, and the diagnosis codes. We'll use `assert` statements.

Let's produce the final answer.

We'll include the file path at the top.

Now, let's write the test file.```python
# Arquivo: backend/tests/test_sisab_export.py
"""
Testes de validação estrutural da exportação SISAB (C16).

Cobre:
1. Preenchimento obrigatório de CIAP-2 ou CID-10 nas fichas.
2. Rejeição de lotes com CNS ou CNES inválidos.
3. Geração de payload consistente com os dados de entrada.
"""

import pytest
from pydantic import ValidationError
from datetime import date, datetime

# Importações do projeto (ajustar conforme estrutura real)
from backend.app.schemas.sisab import FichaSISAB, LoteSISAB
from backend.app.services.sisab_export import export_lote, validar_cns, validar_cnes


# -----------------------------------------------------------------------------
# Utilitários para geração de dados válidos
# -----------------------------------------------------------------------------
def gerar_cns_valido() -> str:
    """
    Gera um CNS válido (15 dígitos) usando o algoritmo oficial de dígito verificador.
    """
    # 14 primeiros dígitos (base)
    base = "12345678901234"
    pesos = list(range(15, 1, -1))  # 15, 14, ..., 2
    soma = sum(int(d) * p for d, p in zip(base, pesos))
    resto = soma % 11
    digito = 0 if resto == 0 else 11 - resto
    return base + str(digito)


def gerar_cnes_valido() -> str:
    """CNES válido: 7 dígitos numéricos."""
    return "1234567"


def ficha_valida() -> FichaSISAB:
    """Cria uma ficha válida para testes."""
    return FichaSISAB(
        paciente_nome="Maria da Silva",
        paciente_cns=gerar_cns_valido(),
        profissional_cns=gerar_cns_valido(),
        cnes=gerar_cnes_valido(),
        data_atendimento=date(2025, 3, 10),
        ciap2="A01",
        cid10=None,
        soap_subjetivo="Dor de cabeça",
        soap_objetivo="Paciente consciente",
        soap_avaliacao="Enxaqueca",
        soap_plano="Prescrito analgésico",
    )


# -----------------------------------------------------------------------------
# 1. Validação de preenchimento obrigatório de CIAP-2/CID-10
# -----------------------------------------------------------------------------
class TestPreenchimentoDiagnostico:
    def test_ficha_sem_ciap_e_sem_cid_rejeitada(self):
        """Ficha sem CIAP-2 e sem CID-10 deve ser rejeitada."""
        with pytest.raises(ValidationError):
            FichaSISAB(
                paciente_nome="João",
                paciente_cns=gerar_cns_valido(),
                profissional_cns=gerar_cns_valido(),
                cnes=gerar_cnes_valido(),
                data_atendimento=date(2025, 3, 10),
                ciap2=None,
                cid10=None,
            )

    def test_ficha_com_ciap_aceita(self):
        """Ficha com CIAP-2 preenchido é aceita."""
        ficha = ficha_valida()
        assert ficha.ciap2 == "A01"

    def test_ficha_com_cid_aceita(self):
        """Ficha com CID-10 preenchido é aceita."""
        ficha = FichaSISAB(
            paciente_nome="João",
            paciente_cns=gerar_cns_valido(),
            profissional_cns=gerar_cns_valido(),
            cnes=gerar_cnes_valido(),
            data_atendimento=date(2025, 3, 10),
            ciap2=None,
            cid10="J06.9",
        )
        assert ficha.cid10 == "J06.9"

    def test_ficha_com_ciap_e_cid_aceita(self):
        """Ficha com ambos os códigos também é aceita."""
        ficha = ficha_valida()
        ficha.cid10 = "G43.9"
        assert ficha.ciap2 and ficha.cid10


# -----------------------------------------------------------------------------
# 2. Rejeição de lotes com CNS ou CNES inválido
# -----------------------------------------------------------------------------
class TestValidacaoCnsCnes:
    def test_lote_com_cns_invalido_rejeitado(self):
        """Lote contendo CNS inválido deve ser rejeitado."""
        ficha = ficha_valida()
        ficha.paciente_cns = "123