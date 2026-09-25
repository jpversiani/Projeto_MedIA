We need to create backend/tests/test_sisab_export.py for the MedIA project, focusing on validation of SISAB export (C12). The tests should cover:

1) Validation of mandatory filling of CIAP-2/CID-10.
2) Rejection of batches with invalid CNS or CNES.
3) Generation of consistent payload.

We need to understand the context: The project is a medical AI assistant (MedIA) for primary care (APS). It likely uses SISAB (Sistema de Informação em Saúde para Atenção Básica) export, which requires specific files (fichas) like Ficha de Atendimento, Ficha de Cadastro Individual, etc. The tests are for the export module.

We must assume the structure: The export module probably has functions to generate payloads from database models, and validation logic. The test file should test these functions.

We'll need to import relevant modules from the backend. Since the project is not given, we'll have to make reasonable assumptions.

We'll create tests using pytest and possibly use fixtures to mock database objects.

Let's outline the test cases:

1) Test that when creating an export payload (maybe a function like `generate_ficha_atendimento`) it validates that either CIAP-2 or CID-10 is present. Possibly both optional but at least one required? Or maybe both are required? The instruction says "validação de preenchimento obrigatório de CIAP-2/CID-10" - could mean that one of them must be filled. We'll check the business rule: In APS, CIAP-2 is for primary care, CID-10 for hospital. For SISAB, it's usually required to have at least one diagnosis code. So we'll test that if neither is present, it raises an error.

2) Test that invalid CNS (Cartão Nacional de Saúde) or CNES (Cadastro Nacional de Estabelecimento de Saúde) cause rejection. We need to validate format/checksum.

3) Test that the generated payload is consistent: e.g., contains required fields, has correct structure, types.

We'll write tests that call functions from the export module. Since we don't know the exact module names, we'll assume there is a module `backend/app/services/sisab_export.py` or similar. We'll define these functions in the test with mocks, but better to import and test actual implementation.

Given that the task says "crie backend/tests/test_sisab_export.py" and "Execute com precisão conforme as diretrizes", we need to provide the test file code. We'll write the tests with placeholders for the actual functions, and we'll make sure they follow the project's coding style.

We'll also need to set up the test environment, but the task only asks for the test file. So we'll write the test file with proper imports, fixtures, and test functions.

We'll assume the following:

- The project uses FastAPI, SQLAlchemy, Pydantic.
- There is a service `SISABExportService` that handles export.
- The export payload is a Pydantic model, e.g., `FichaAtendimentoPayload`.
- Validation functions exist: `validate_cns`, `validate_cnes`, `validate_diagnosis`.

We'll write tests that mock these functions or test them directly if they exist. Since we don't have the actual code, we'll write tests that would pass if the implementation is correct. We'll also include tests for edge cases.

We'll structure the test file with:

- Imports: pytest, pydantic, etc.
- Fixtures: mock db session, sample data.
- Tests:
  1. Test for mandatory diagnosis: 
     - Test that a payload with both CIAP-2 and CID-10 is accepted.
     - Test that a payload with only CIAP-2 is accepted.
     - Test that a payload with only CID-10 is accepted.
     - Test that a payload with neither raises a validation error.
  2. Test for CNS validation:
     - Test that invalid CNS (wrong length, invalid check digit) raises error.
     - Test that valid CNS passes.
  3. Test for CNES validation:
     - Similar.
  4. Test for payload generation:
     - Test that the generated payload contains all required fields and correct types.

We'll write these tests in a way that they can be run with pytest. We'll also include some fixtures to mock data.

Since the test file is part of the project, we should follow the same style: Python 3.12, type hints, Pydantic v2, SQLAlchemy 2.0. We'll use pytest.asyincio if async is needed? Probably not; the service might be sync.

Let's write the test file. We'll include comments to explain.

We'll assume the following module paths:
- `backend.app.models` for SQLAlchemy models.
- `backend.app.schemas` for Pydantic schemas.
- `backend.app.services.sisab_export` for the export service.

We'll write tests that import these, but since they may not exist, we'll use mocks or placeholders. However, the instruction says to provide the test file; it doesn't require that the rest of the project exists. We'll write the tests with actual imports but we can also add a comment that these are placeholders. But to be safe, we'll write the tests to be executable even if the actual implementation is missing by mocking the dependencies. But that might be too complex.

Better to write the tests as they would be written if the actual implementation exists. So we'll import the necessary modules and functions, and we'll write tests that assert expected behavior. Since we don't have the actual code, we'll assume the interface based on typical patterns.

We'll define a fixture for a sample patient data.

Let's craft the test file.

We'll include:

```python
import pytest
from pydantic import ValidationError
from backend.app.services.sisab_export import SISABExportService
from backend.app.schemas.sisab import FichaAtendimentoPayload
```

But these may not exist. To make the test file self-contained, we could create a minimal service and schema inside the test, but that would be misleading.

Given the task is to "crie backend/tests/test_sisab_export.py", we just need to provide the test code. We'll assume the actual implementation exists and we are testing it.

We'll write tests that would fail if the implementation is not correct. So we need to be precise about expected behavior.

Let's outline the test functions:

```python
def test_diagnosis_required():
    # Test that missing both CIAP and CID raises error
    # Test that one of them is enough
```

For CNS validation, we'll test with known invalid CNS like "123456789012345" (should be 15 digits, but last digit check). We'll implement a helper to generate invalid CNS.

Similarly for CNES.

For payload consistency, we'll test that the generated payload has all required fields, and data types.

We'll use pytest fixtures to provide sample data.

Now, write the code.

We'll also include a test that the service uses the correct validation functions.

Let's write it.

We'll use `unittest.mock` to patch validation functions if needed, but we'll just call the actual functions.

We'll assume the service has a method `generate_ficha_atendimento(patient_data)` that returns a Pydantic model.

We'll test that.

Alright, let's produce the test file.```python:backend/tests/test_sisab_export.py
"""
Testes de Validação Estrutural da Exportação SISAB (C12)

Cobertura:
1. Validação de preenchimento obrigatório de CIAP-2/CID-10.
2. Rejeição de lotes com CNS ou CNES inválido.
3. Geração de payload consistente.
"""

import pytest
from pydantic import ValidationError

from backend.app.services.sisab_export import SISABExportService
from backend.app.schemas.sisab import FichaAtendimentoPayload


# ----------------------------------------------------------------------
# Fixtures e dados auxiliares
# ----------------------------------------------------------------------

@pytest.fixture
def paciente_valido() -> dict:
    """Dados mínimos válidos para um paciente em uma ficha de atendimento."""
    return {
        "cns": "123456789012345",          # CNS válido (15 dígitos)
        "cnes": "1234567",                 # CNES válido (7 dígitos)
        "ciap2": "A01",                    # CIAP-2 opcional (mas pelo menos um diagnóstico)
        "cid10": None,                     # CID-10 opcional
        "data_atendimento": "2025-04-10",
        "procedimentos": ["CONSULTA"],
        "idade": 35,
        "sexo": "M",
        "municipio": "530010",
        "equipe": "E01",
        "turno": "M",
        "tipo_atendimento": "CONSULTA_AGENDADA",
    }


@pytest.fixture
def service() -> SISABExportService:
    """Instância do serviço de exportação SISAB."""
    return SISABExportService()


# ----------------------------------------------------------------------
# 1. Testes de preenchimento obrigatório de CIAP-2/CID-10
# ----------------------------------------------------------------------

class TestDiagnosticoObrigatorio:
    """Testa que pelo menos um código de diagnóstico (CIAP-2 ou CID-10) é exigido."""

    def test_aceita_somente_ciap2(self, service, paciente_valido):
        """Deve aceitar payload com apenas CIAP-2 preenchido."""
        payload_data = paciente_valido.copy()
        payload_data["cid10"] = None
        payload_data["ciap2"] = "A01"
        try:
            payload = FichaAtendimentoPayload(**payload_data)
        except ValidationError:
            pytest.fail("Payload com CIAP-2 deveria ser válido")
        # Verifica que o serviço também aceita
        service.validate_payload(payload)  # não deve lançar exceção

    def test_aceita_somente_cid10(self, service, paciente_valido):
        """Deve aceitar payload com apenas CID-10 preenchido."""
        payload_data = paciente_valido.copy()
        payload_data["cid10"] = "J10.0"
        payload_data["ciap2"] = None
        try:
            payload = FichaAtendimentoPayload(**payload_data)
        except ValidationError:
            pytest.fail("Payload com CID-10 deveria ser válido")
        service.validate_payload(payload)

    def test_aceita_ambos(self, service, paciente_valido):
        """Deve aceitar payload com ambos os códigos preenchidos."""
        payload_data = paciente_valido.copy()
        payload_data["ciap2"] = "A01"
        payload_data["cid10"] = "J10.0"
        try:
            payload = FichaAtendimentoPayload(**payload_data)
        except ValidationError:
            pytest.fail("Payload com ambos os códigos deveria ser válido")
        service.validate_payload(payload)

    def test_rejeita_sem_diagnostico(self, service, paciente_valido):
        """Deve rejeitar payload sem nenhum código de diagnóstico."""
        payload_data = paciente_valido.copy()
        payload_data["ciap2"] = None
        payload_data["cid10"] = None
        with pytest.raises(ValidationError):
            FichaAtendimentoPayload(**payload_data)

    def test_rejeita_vazio_mas_com_campos_presentes(self, service, paciente_valido):
        """Deve rejeitar payload com campos vazios (string vazia) para ambos."""
        payload_data = paciente_valido.copy()
        payload_data["ciap2"] = ""
        payload_data["cid10"] = ""
        with pytest.raises(ValidationError):
            FichaAtendimentoPayload(**payload_data)


# ----------------------------------------------------------------------
# 2. Testes de rejeição de CNS ou CNES inválido
# ----------------------------------------------------------------------

class TestCnsCnesValidation:
    """Testa que CNS e CNES inválidos são rejeitados na validação do lote."""

    def test_cns_invalido_formato(self, service, paciente_valido):
        """CNS com menos de 15 dígitos deve ser rejeitado."""
        payload_data = paciente_valido.copy()
        payload_data["cns"] = "12345"
        with pytest.raises(ValidationError):
            FichaAtendimentoPayload(**payload_data)

    def test_cns_invalido_checagem(self, service, paciente_valido):
        """CNS com dígito verificador incorreto deve ser rejeitado."""
        payload_data = paciente_valido.copy()
        # CNS inválido: altera o último dígito para quebrar o dígito verificador
        payload_data["cns"] = "123456789012340"  # último dígito incorreto
        with pytest.raises(ValidationError):
            FichaAtendimentoPayload(**payload_data)

    def test_cnes_invalido_formato(self, service, paciente_valido):
        """CNES com comprimento incorreto deve ser rejeitado."""
        payload_data = paciente_valido.copy()
        payload_data["cnes"] = "123456"  # 6 dígitos em vez de 7
        with pytest.raises(ValidationError):
            FichaAtendimentoPayload(**payload_data)

    def test_cnes_invalido_nao_numerico(self, service, paciente_valido):
        """CNES com caracteres não numéricos deve ser rejeitado."""
        payload_data = paciente_valido.copy()
        payload_data["cnes"] = "12a4567"
        with pytest.raises(ValidationError):
            FichaAtendimentoPayload(**payload_data)

    def test_cns_e_cnes_validos_passam(self, service, paciente_valido):
        """CNS e CNES válidos não devem gerar erro de validação."""
        payload = FichaAtendimentoPayload(**paciente_valido)
        service.validate_payload(payload)  # não deve lançar exceção


# ----------------------------------------------------------------------
# 3. Testes de geração de payload consistente
# ----------------------------------------------------------------------

class TestPayloadConsistencia:
    """Testa que o payload gerado segue o contrato esperado."""

    def test_campos_obrigatorios_presentes(self, service, paciente_valido):
        """O payload gerado deve conter todos os campos obrigatórios."""
        payload = service.generate_ficha_atendimento(paciente_valido)
        # Verifica os campos essenciais
        assert hasattr(payload, "cns")
        assert hasattr(payload, "cnes")
        assert hasattr(payload, "data_atendimento")
        assert hasattr(payload, "procedimentos")
        assert hasattr(payload, "idade")
        assert hasattr(payload, "sexo")
        assert hasattr(payload, "municipio")
        assert hasattr(payload, "equipe")
        assert hasattr(payload, "turno")
        assert hasattr(payload, "tipo_atendimento")

    def test_tipos_corretos(self, service, paciente_valido):
        """Os tipos dos campos devem respeitar o schema."""
        payload = service.generate_ficha_atendimento(paciente_valido)
        assert isinstance(payload.cns, str)
        assert isinstance(payload.cnes, str)
        assert isinstance(payload.data_atendimento, str)  # ou date
        assert isinstance(payload.procedimentos, list)
        assert all(isinstance(p, str) for p in payload.procedimentos)
        assert isinstance(payload.idade, int)
        assert payload.sexo in ["M", "F", "I"]  # Masculino, Feminino, Indefinido

    def test_diagnostico_preenchido(self, service, paciente_valido):
        """Ao menos um dos campos de diagnóstico deve ser preenchido no payload gerado."""
        payload = service.generate_ficha_atendimento(paciente_valido)
        assert payload.ciap2 is not None or payload.cid10 is not None

    def test_cns_validado(self, service, paciente_valido):
        """O payload gerado deve conter um CNS válido (dígito verificador correto)."""
        payload = service.generate_ficha_atendimento(paciente_valido)
        # Reutiliza a validação do schema
        try:
            FichaAtendimentoPayload(**payload.dict())
        except ValidationError:
            pytest.fail("Payload gerado não passou na validação do schema")

    def test_cnes_validado(self, service, paciente_valido):
        """O payload gerado deve conter um CNES válido."""
        payload = service.generate_ficha_atendimento(paciente_valido)
        # Verifica que o CNES tem exatamente 7 dígitos
        assert len(payload.cnes) == 7
        assert payload.cnes.isdigit()

    def test_geracao_com_diagnostico_apenas_ciap(self, service, paciente_valido):
        """Se somente CIAP-2 for fornecido, o payload gerado deve ter cid10=None."""
        data = paciente_valido.copy()
        data["cid10"] = None
        payload = service.generate_ficha_atendimento(data)
        assert payload.cid10 is None
        assert payload.ciap2 == "A01"

    def test_geracao_com_diagnostico_apenas_cid(self, service, paciente_valido):
        """Se somente CID-10 for fornecido, o payload gerado deve ter ciap2=None."""
        data = paciente_valido.copy()
        data["ciap2"] = None
        data["cid10"] = "J10.0"
        payload = service.generate_ficha_atendimento(data)
        assert payload.ciap2 is None
        assert payload.cid10 == "J10.0"

    def test_geracao_sem_diagnostico_levanta_erro(self, service, paciente_valido):
        """Se nenhum diagnóstico for fornecido, o serviço deve lançar erro."""
        data = paciente_valido.copy()
        data["ciap2"] = None
        data["cid10"] = None
        with pytest.raises(ValueError):
            service.generate_ficha_atendimento(data)
```