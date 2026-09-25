We need to create a test file for the SISAB export validation. The task specifies: "crie backend/tests/test_sisab_export.py testando integridade das fichas: 1) validação de preenchimento obrigatório de CIAP-2/CID-10; 2) rejeição de lotes com CNS ou CNES inválido; 3) geração de payload consistente."

We need to write tests for the SISAB export functionality. We need to understand the existing codebase. Since we are given only the task, we must assume the structure. Likely there is a module for SISAB export in backend/app/services or similar. We need to write tests that validate:

1. Validation of mandatory filling of CIAP-2/CID-10: meaning that when exporting fichas (records), if a ficha lacks a CIAP-2 or CID-10 code, it should be rejected or flagged. Probably the export function should raise an error or skip invalid records.

2. Rejection of batches with invalid CNS or CNES: CNS (Cartão Nacional de Saúde) and CNES (Cadastro Nacional de Estabelecimentos de Saúde) must be valid. The test should ensure that if a batch contains invalid CNS or CNES, it is rejected.

3. Generation of consistent payload: The export should produce a payload (likely JSON or XML) that is consistent with the data.

We need to write pytest tests. We'll need to mock or use fixtures. Since we don't have the actual code, we'll write tests that assume certain interfaces. We'll need to import the relevant functions/classes. We'll also need to create sample data.

We'll structure the test file with:

- Imports: pytest, pydantic, sqlalchemy, etc.
- Fixtures: sample fichas (maybe using Pydantic models), sample batches.
- Tests for each requirement.

We'll need to know the function names. Possibly there is a service like `SISABExporter` or `export_sisab`. We'll assume a function `validate_ficha` and `validate_batch` or something.

Since we are writing tests, we can define the expected behavior. We'll write tests that check that invalid data raises exceptions or returns errors.

We'll also need to ensure we have proper type hints.

Let's outline:

```python
# backend/tests/test_sisab_export.py
"""
Testes de validação estrutural da exportação SISAB.
"""
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session
# Importar módulos relevantes (ajustar conforme estrutura real)
from backend.app.services.sisab_export import SISABExporter
from backend.app.schemas.ficha import FichaAtendimento, FichaCadastroIndividual, LoteFichas
# ... etc
```

But we don't know the actual module names. We'll need to make reasonable assumptions. Since the task says "crie backend/tests/test_sisab_export.py", we'll create that file. We'll write tests that are plausible and can be adapted.

We'll also need to consider the architecture: Pydantic v2, SQLAlchemy 2.0. So we'll use Pydantic models for validation.

We'll write tests that:

- Test that a ficha without CIAP-2 or CID-10 raises a validation error when trying to export.
- Test that a batch with invalid CNS or CNES is rejected.
- Test that a valid batch produces a consistent payload (e.g., JSON structure with expected fields).

We'll need to create sample data. We'll use Pydantic models to create valid and invalid instances.

We'll also need to mock the database session if needed, but maybe the export function is pure and doesn't need DB.

Let's write the test file with clear comments.

We'll also include a conftest.py if needed, but the task only asks for the test file. We'll assume the project structure.

We'll write the tests using pytest fixtures.

Let's produce the code.```python
# Arquivo: backend/tests/test_sisab_export.py
"""
Testes de validação estrutural da exportação SISAB.

Cobre:
1. Validação de preenchimento obrigatório de CIAP-2/CID-10.
2. Rejeição de lotes com CNS ou CNES inválido.
3. Geração de payload consistente.
"""

import pytest
from pydantic import ValidationError

# Importações dos módulos do projeto (ajustar conforme estrutura real)
from backend.app.schemas.ficha import (
    FichaAtendimento,
    FichaCadastroIndividual,
    LoteFichas,
)
from backend.app.services.sisab_export import SISABExporter


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------
@pytest.fixture
def ficha_valida_com_ciap():
    """Ficha de atendimento válida com CIAP-2 preenchido."""
    return FichaAtendimento(
        cns="123456789012345",
        cnes="1234567",
        data_atendimento="2025-03-01",
        ciap2="A01",
        procedimento="consulta",
        profissional="123456",
    )


@pytest.fixture
def ficha_valida_com_cid():
    """Ficha de atendimento válida com CID-10 preenchido."""
    return FichaAtendimento(
        cns="123456789012345",
        cnes="1234567",
        data_atendimento="2025-03-01",
        cid10="A01.0",
        procedimento="consulta",
        profissional="123456",
    )


@pytest.fixture
def ficha_sem_ciap_cid():
    """Ficha de atendimento sem CIAP-2 e sem CID-10 (inválida)."""
    return FichaAtendimento(
        cns="123456789012345",
        cnes="1234567",
        data_atendimento="2025-03-01",
        procedimento="consulta",
        profissional="123456",
    )


@pytest.fixture
def lote_valido(ficha_valida_com_ciap):
    """Lote de fichas válido."""
    return LoteFichas(
        cnes="1234567",
        fichas=[ficha_valida_com_ciap],
    )


@pytest.fixture
def lote_cns_invalido(ficha_valida_com_ciap):
    """Lote com CNS inválido."""
    ficha_invalida = ficha_valida_com_ciap.model_copy(update={"cns": "123"})
    return LoteFichas(cnes="1234567", fichas=[ficha_invalida])


@pytest.fixture
def lote_cnes_invalido(ficha_valida_com_ciap):
    """Lote com CNES inválido."""
    return LoteFichas(cnes="123", fichas=[ficha_valida_com_ciap])


# ----------------------------------------------------------------------
# Testes
# ----------------------------------------------------------------------
class TestValidacaoCIAPCID:
    """Testes de preenchimento obrigatório de CIAP-2 ou CID-10."""

    def test_ficha_com_ciap_aceita(self, ficha_valida_com_ciap):
        """Uma ficha com CIAP-2 deve ser aceita."""
        exporter = SISABExporter()
        # Deve processar sem exceção
        exporter.validar_ficha(ficha_valida_com_ciap)

    def test_ficha_com_cid_aceita(self, ficha_valida_com_cid):
        """Uma ficha com CID-10 deve ser aceita."""
        exporter = SISABExporter()
        exporter.validar_ficha(ficha_valida_com_cid)

    def test_ficha_sem_ciap_cid_rejeitada(self, ficha_sem_ciap_cid):
        """Uma ficha sem CIAP-2 e sem CID-10 deve ser rejeitada."""
        exporter = SISABExporter()
        with pytest.raises(ValidationError) as exc_info:
            exporter.validar_ficha(ficha_sem_ciap_cid)
        assert "CIAP-2 ou CID-10" in str(exc_info.value)

    def test_lote_com_ficha_sem_ciap_cid_rejeitado(self, ficha_sem_ciap_cid):
        """Um lote contendo ficha sem CIAP/CID deve ser rejeitado."""
        lote = LoteFichas(cnes="1234567", fichas=[ficha_sem_ciap_cid])
        exporter = SISABExporter()
        with pytest.raises(ValidationError):
            exporter.validar_lote(lote)


class TestValidacaoCNS_CNES:
    """Testes de validação de CNS e CNES."""

    def test_lote_cns_invalido_rejeitado(self, lote_cns_invalido):
        """Lote com CNS inválido deve ser rejeitado."""
        exporter = SISABExporter()
        with pytest.raises(ValidationError) as exc_info:
            exporter.validar_lote(lote_cns_invalido)
        assert "CNS" in str(exc_info.value)

    def test_lote_cnes_invalido_rejeitado(self, lote_cnes_invalido):
        """Lote com CNES inválido deve ser rejeitado."""
        exporter = SISABExporter()
        with pytest.raises(ValidationError) as exc_info:
            exporter.validar_lote(lote_cnes_invalido)
        assert "CNES" in str(exc_info.value)

    def test_lote_valido_aceito(self, lote_valido):
        """Lote válido deve ser aceito."""
        exporter = SISABExporter()
        exporter.validar_lote(lote_valido)  # não deve lançar exceção


class TestGeracaoPayload:
    """Testes de geração de payload consistente."""

    def test_payload_contem_campos_obrigatorios(self, lote_valido):
        """O payload gerado deve conter os campos obrigatórios do SISAB."""
        exporter = SISABExporter()
        payload = exporter.gerar_payload(lote_valido)

        # Verificar estrutura básica
        assert "lote" in payload
        assert "fichas" in payload["lote"]
        assert len(payload["lote"]["fichas"]) == 1

        ficha_payload = payload["lote"]["fichas"][0]
        # Campos obrigatórios
        assert "cns" in ficha_payload
        assert "cnes" in ficha_payload
        assert "data_atendimento" in ficha_payload
        # Deve conter pelo menos um dos códigos
        assert "ciap2" in ficha_payload or "cid10" in ficha_payload

    def test_payload_consistente_com_dados_originais(self, lote_valido):
        """O payload deve refletir fielmente os dados do lote."""
        exporter = SISABExporter()
        payload = exporter.gerar_payload(lote_valido)

        ficha_original = lote_valido.fichas[0]
        ficha_payload = payload["lote"]["fichas"][0]

        assert ficha_payload["cns"] == ficha_original.cns
        assert ficha_payload["cnes"] == ficha_original.cnes
        assert ficha_payload["data_atendimento"] == ficha_original.data_atendimento.isoformat()
        # Se CIAP-2 presente, deve ser igual
        if ficha_original.ciap2:
            assert ficha_payload["ciap2"] == ficha_original.ciap2
        # Se CID-10 presente, deve ser igual
        if ficha_original.cid10:
            assert ficha_payload["cid10"] == ficha_original.cid10

    def test_payload_json_serializavel(self, lote_valido):
        """O payload deve ser serializável em JSON."""
        import json
        exporter = SISABExporter()
        payload = exporter.gerar_payload(lote_valido)
        # Deve funcionar sem erro
        json.dumps(payload)
```