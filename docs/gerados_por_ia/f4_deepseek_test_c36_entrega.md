We need to create backend/tests/test_sisab_export.py for the MedIA project. The task: "Testes de Validação Estrutural da Exportação SISAB (C36)". We need to test integrity of fichas (records) for SISAB export. Specifically:

1) validation of mandatory filling of CIAP-2/CID-10;
2) rejection of batches with invalid CNS or CNES;
3) generation of consistent payload.

We need to write pytest tests. We need to understand the project structure. Since we only have the instruction, we need to infer the likely models/services. We'll create tests that mock or use actual classes. We need to ensure code is Python 3.12, Pydantic v2, SQLAlchemy 2.0. We'll write tests that verify the validation logic.

We should probably create a test file that imports from the backend modules. Since we don't have the actual code, we need to design tests based on expected interfaces. We can define fixtures and use mocks. But the instruction says "crie backend/tests/test_sisab_export.py testando integridade das fichas". We need to produce a file that would pass if the implementation is correct. We'll write tests that assume certain functions/classes exist. We can also create a minimal implementation in the test? No, tests should test the actual code. But we don't have the code. We need to make reasonable assumptions.

Let's think: The project MedIA likely has a module for SISAB export. It might have models for Ficha (e.g., FichaAtendimento, FichaCadastroIndividual, etc.) with fields like cns, cnes, ciap, cid, etc. There might be a service that validates and generates payload.

We'll write tests that:

- Test that a ficha without CIAP-2 or CID-10 is invalid (mandatory filling). But note: In SISAB, for atendimento, either CIAP-2 or CID-10 must be filled? Actually, in the Brazilian e-SUS APS, the ficha de atendimento has "Conduta" and "Exames", and the "CID-10" or "CIAP-2" is mandatory? Let's recall: The ficha de atendimento individual has fields for "diagnóstico" with CIAP-2 or CID-10. The validation may require at least one of them. The instruction says "validação de preenchimento obrigatório de CIAP-2/CID-10" meaning mandatory filling of CIAP-2/CID-10. Could be that at least one must be present. We'll test that a ficha with neither is rejected, and with at least one is accepted.

- Test that batches with invalid CNS or CNES are rejected. CNS is the Cartão Nacional de Saúde (15 digits). CNES is the National Register of Health Establishments (7 digits). We'll test invalid formats.

- Test generation of consistent payload: maybe a function that converts a validated ficha to a dict/JSON for SISAB. We'll test that the payload contains the expected fields and values.

We need to structure the tests. We'll create a test class or functions. We'll use pytest. We'll need to import from the actual modules. Since we don't have them, we can use `from backend.app.services.sisab_export import ...` or similar. We'll need to make sure the imports are correct. Alternatively, we can write tests that are self-contained by defining minimal classes? But the instruction says "crie backend/tests/test_sisab_export.py" - it's a test file, not implementation. It should test the project's code. We'll assume the project has the following:

- `backend/app/models/sisab.py` with Pydantic models for Ficha.
- `backend/app/services/sisab_export.py` with functions like `validate_ficha`, `validate_lote`, `generate_payload`.

We'll write tests that import these. To make the tests runnable even if the actual code is not present, we could use `pytest.importorskip` or just assume. But the user expects a complete test file. We'll write it with imports that match a plausible structure.

Let's define a plausible structure:

- `backend/app/schemas/sisab.py` (Pydantic models)
- `backend/app/services/sisab_export.py` (business logic)

We'll write tests that use `from backend.app.schemas.sisab import FichaAtendimento, LoteSISAB` and `from backend.app.services.sisab_export import validar_ficha, validar_lote, gerar_payload`.

But we need to be careful: The test file itself should be valid Python. We'll include type hints.

We'll also need to create fixtures for valid/invalid data.

Let's design the tests:

1. Test mandatory CIAP-2/CID-10:
   - Create a ficha with neither ciap nor cid -> should raise ValidationError or return False.
   - Create with ciap only -> valid.
   - Create with cid only -> valid.
   - Create with both -> valid.

2. Test invalid CNS/CNES:
   - Create a lote (batch) with a ficha having invalid CNS (e.g., wrong length or invalid check digit) -> should be rejected.
   - Create a lote with invalid CNES -> rejected.
   - Create a lote with valid CNS/CNES -> accepted.

3. Test payload consistency:
   - Create a valid ficha, generate payload, assert that payload contains the same data, with proper keys, and that the payload is a dict or JSON string.

We need to know the exact field names. We'll use common names: `cns`, `cnes`, `ciap2`, `cid10`, `data_atendimento`, `profissional_cns`, etc.

We'll also need to implement validation logic in the test? No, we just call the functions.

But if the actual code doesn't exist, the tests will fail. That's okay; the user asked to create tests, not to implement the code. However, the instruction says "Execute com precisão conforme as diretrizes." We need to provide a test file that is well-written and follows the architecture.

We can also include a `conftest.py`? The instruction only asks for the test file. We'll put everything in one file.

Let's write the test file with clear comments and structure.

We'll use Pydantic v2 style: `from pydantic import BaseModel, ValidationError`. But we are testing, not defining models. We'll import the models.

We'll also use `pytest` fixtures.

Let's draft:

```python
# Arquivo: backend/tests/test_sisab_export.py
"""
Testes de Validação Estrutural da Exportação SISAB (C36).

Cobertura:
1. Validação de preenchimento obrigatório de CIAP-2/CID-10.
2. Rejeição de lotes com CNS ou CNES inválido.
3. Geração de payload consistente.
"""

import pytest
from pydantic import ValidationError

from backend.app.schemas.sisab import FichaAtendimento, LoteSISAB
from backend.app.services.sisab_export import (
    validar_ficha,
    validar_lote,
    gerar_payload,
)
```

But we need to ensure the imports are correct. We can also use `from backend.app.models.sisab import ...` if that's the case. We'll choose schemas.

We'll create fixtures:

```python
@pytest.fixture
def ficha_valida():
    return FichaAtendimento(
        cns="123456789012345",  # 15 digits
        cnes="1234567",          # 7 digits
        ciap2="A01",
        cid10=None,
        data_atendimento="2024-01-01",
        ...
    )
```

But we don't know the required fields. We'll include only the ones we need. To avoid over-specification, we can use `**kwargs` or just pass the fields we care about. However, if the model has required fields, the test will fail if not provided. We can use `model_config` to allow extra? No.

Alternative: We can create a simple mock model in the test file? But that would not test the real code. The instruction says "testando integridade das fichas" - we need to test the actual validation logic.

Given the ambiguity, we can write tests that are independent of the exact model by using `create` functions from the service. For example, `validar_ficha` might accept a dict. We'll assume that `validar_ficha` takes a dict or a Pydantic model.

Let's think of a more robust approach: We can write tests that use `validar_ficha` with a dictionary, and the function returns a boolean or raises. That way we don't need to instantiate the model. But the instruction says "fichas" - likely Pydantic models.

We'll write tests that call `validar_ficha` with a dict and expect `ValidationError` if invalid. That is common.

Let's define:

```python
def validar_ficha(ficha: dict) -> bool:
    # returns True if valid, raises ValidationError if invalid
```

But we don't know. We'll write tests that assert `validar_ficha` raises `ValidationError` for missing CIAP/CID. We'll use `pytest.raises`.

For the lote, we'll have `validar_lote(lote: dict)` that raises if any ficha has invalid CNS/CNES.

For payload, `gerar_payload(ficha: dict) -> dict`.

We'll write tests accordingly.

Let's create the test file with these assumptions. We'll also include a note that the tests assume the service functions exist.

We'll also include tests for CNS validation: The CNS has a check digit algorithm. We can use a known valid CNS. For example, a valid CNS: 123456789012345? Actually, the CNS is 15 digits, where the first digit is 1 or 2 for the SUS card? There is a check digit algorithm. We can use a known valid CNS from examples. Let's recall: The CNS is composed of 15 digits, the last digit is a check digit calculated by modulo 11. We can generate a valid one. But for tests, we can use a fixed valid CNS: "123456789012345" might not be valid. We need a valid one. Let's compute.

The CNS validation algorithm: The first digit is 1, 2, 7, 8, or 9? Actually, the CNS number is 15 digits. The check digit is the 15th digit. The calculation: multiply each of the first 14 digits by (15 - position) (i.e., weights 15,14,...,2), sum, then mod 11, and if remainder is 0, check digit is 0; if remainder is 1, check digit is 0? Wait, let's recall the official algorithm:

For CNS, the check digit is calculated as follows:
- Multiply each of the 15 digits by its position (from 1 to 15) and sum? Actually, I've seen two methods. Let's search memory: The CNS validation uses the same algorithm as CPF? No.

Let's look up: The Cartão Nacional de Saúde (CNS) has a check digit that is the last digit. The algorithm: 
- Take the first 14 digits.
- Multiply each digit by its position (from 1 to 14) in reverse? Or by weights 15,14,...,2.
- Sum the products.
- Divide by 11.
- If remainder is 0, check digit is 0.
- If remainder is 1, check digit is 0? Actually, if remainder is 1, the number is invalid? Let's find a reliable source.

I recall that the CNS check digit is calculated using the same method as the CPF? No, CPF uses weights 10,9,...,2. For CNS, I think it's:
- The first 14 digits are multiplied by weights 15,14,...,2 (i.e., 15 for the 1st digit, 14 for the 2nd, ..., 2 for the 14th).
- Sum the results.
- The check digit is the remainder of the division by 11, but if remainder is 0 or 1, the check digit is 0? Actually, I've seen: 
```
soma = sum(int(d) * (15 - i) for i, d in enumerate(cns[:14]))
resto = soma % 11
if resto == 0:
    dv = 0
else:
    dv = 11 - resto
```
But then the check digit can be 10? No, it's a digit, so if dv == 10, then it's 0? Let's check.

I found a known valid CNS: "123456789012345" - let's test with that algorithm. We'll compute manually? Let's do a quick mental calculation? Not necessary. We can use a known valid CNS from examples: "700000000000000" is often used as a test? Actually, the CNS for a person is 15 digits. There are examples online: "123456789012345" might be invalid. Let's use a generator? We can write a small function in the test to generate a valid CNS. But that would be overkill.

Alternatively, we can test invalid CNS by using a clearly invalid one like "123" or "12345678901234" (14 digits) or "123456789012345" (if we know it's invalid). But we need to be sure. We can use a string with non-digits or wrong length. The validation likely checks length and check digit. We can test that a CNS with wrong length is rejected. That's safe. For valid CNS, we can use a known valid one. Let's find a valid CNS online? I recall that "123456789012345" is not valid because the check digit doesn't match. Let's compute using the algorithm I described.

Let's compute for "123456789012345":
Digits: 1,2,3,4,5,6,7,8,9,0,1,2,3,4,5 (first 14: 1,2,3,4,5,6,7,8,9,0,1,2,3,4)
Weights: 15,14,13,12,11,10,9,8,7,6,5,4,3,2
Products:
1*15=15
2*14=28
3*13=39
4*12=48
5*11=55
6*10=60
7*9=63
8*8=64
9*7=63
0*6=0
1*5=5
2*4=8
3*3=9
4*2=8
Sum = 15+28=43, +39=82, +48=130, +55=185, +60=245, +63=308, +64=372, +63=435, +0=435, +5=440, +8=448, +9=457, +8=465.
465 % 11 = 465 - 11*42 = 465 - 462 = 3. If dv = 11 - 3 = 8. The check digit is 5, so invalid. So "123456789012345" is invalid. Good.

We can use a valid CNS: we need one where the check digit matches. Let's generate one: We can use "12345678901234" and compute dv. For first 14 digits "12345678901234", we already computed sum = 465 (without the last digit). dv = 11 - (465 % 11) = 11 - 3 = 8. So the valid CNS would be "123456789012348". Let's verify: The last digit is 8. So "123456789012348" is valid. We'll use that.

For CNES: It is 7 digits. There is no check digit? Actually, CNES is just a 7-digit number. It may be validated as numeric and length 7. We'll use "1234567" as valid, and "123456" as invalid.

Now, for the tests, we'll create a valid ficha dict with these values.

Let's define the test data:

```python
CNS_VALIDO = "123456789012348"
CNS_INVALIDO = "123456789012345"
CNES_VALIDO = "1234567"
CNES_INVALIDO = "123456"
```

Now, the tests:

```python
def test_ficha_sem_ciap_e_cid_é_invalida():
    ficha = {
        "cns": CNS_VALIDO,
        "cnes": CNES_VALIDO,
        # sem ciap2 e sem cid10
    }
    with pytest.raises(ValidationError):
        validar_ficha(ficha)
```

But `validar_ficha` might not raise `ValidationError`; it might return False. We can test both? We'll assume it raises. We'll use `pytest.raises(Exception)`? Better to be specific. We'll use `ValidationError` from Pydantic.

We'll also test that with ciap2 present, it's valid.

For the lote test:

```python
def test_lote_com_cns_invalido_é_rejeitado():
    lote = {
        "fichas": [
            {"cns": CNS_INVALIDO, "cnes": CNES_VALIDO, "ciap2": "A01"},
        ]
    }
    with pytest.raises(ValidationError):
        validar_lote(lote)
```

Similarly for CNES.

For payload:

```python
def test_gerar_payload_consistente():
    ficha = {
        "cns": CNS_VALIDO,
        "cnes": CNES_VALIDO,
        "ciap2": "A01",
        "cid10": None,
        "data_atendimento": "2024-01-01",
    }
    payload = gerar_payload(ficha)
    assert payload["cns"] == CNS_VALIDO
    assert payload["cnes"] == CNES_VALIDO
    assert payload["ciap2"] == "A01"
    assert "cid10" in payload
```

But we need to know the exact output. We'll keep it generic.

We also need to test that the payload is a JSON string? The instruction says "geração de payload consistente" - likely a dict. We'll test it's a dict.

We'll also test that the payload includes the mandatory fields.

Now, we need to make the test file