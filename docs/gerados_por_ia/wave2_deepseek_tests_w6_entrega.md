We need to create a test file for the MedIA project. The task is to create backend/tests/test_receita_digital.py with three specific tests. We need to ensure the tests are written in pytest style, using Python 3.12, Pydantic v2, SQLAlchemy 2.0, and following SUS/APS patterns. The tests should verify:

1. test_geracao_hash_prescricao: verifies SHA-256 hash integrity.
2. test_validacao_documento_emitido: tests authenticity validation.
3. test_prescricao_sem_medicamentos: validates rejection of empty prescription.

We need to assume there is existing code for prescription digital (receita digital) in the project. Since we are only asked to create the test file, we should write tests that import the relevant modules. However, we don't have the actual implementation. We need to design tests that would work with a typical implementation. We'll need to mock or use fixtures.

We should structure the test file with imports, fixtures, and test functions. We'll need to define sample data for prescriptions. We'll also need to ensure the tests are comprehensive.

Given the instructions, we should write the test file with proper docstrings and comments. We'll assume there is a module like `backend/app/services/receita_digital.py` or similar that contains functions like `gerar_hash_prescricao`, `validar_documento_emitido`, and a model for prescription that validates medications.

We'll write tests that use pytest fixtures to create sample prescriptions, and we'll test the functions.

Let's outline:

- Imports: pytest, maybe from app.services.receita_digital import gerar_hash_prescricao, validar_documento_emitido, etc. Also import models if needed.
- Fixtures: sample prescription data, maybe a valid prescription with medications, and an empty one.
- Test 1: test_geracao_hash_prescricao - generate hash for a prescription and verify it's a SHA-256 hash (64 hex chars), and that it changes if data changes.
- Test 2: test_validacao_documento_emitido - test that a valid document passes validation, and an invalid one fails.
- Test 3: test_prescricao_sem_medicamentos - test that creating a prescription without medications raises an error.

We'll need to define the expected behavior. Since we don't have the actual code, we'll write tests that assume certain functions exist and behave as expected. We'll also need to handle potential imports.

We'll write the test file with clear structure.

Let's produce the code.```python
# Arquivo: backend/tests/test_receita_digital.py
"""
Testes unitários para o módulo de Prescrição Digital e Validação.

Cobre:
- Geração de hash SHA-256 para integridade da prescrição.
- Validação de autenticidade do documento emitido.
- Rejeição de prescrição sem medicamentos.

Conformidade com:
- Python 3.12, Pydantic v2, SQLAlchemy 2.0.
- Padrões SUS/APS (CIAP-2, CID-10, método SOAP, CNS/CPF).
"""

import hashlib
import pytest
from datetime import datetime, timezone

# Importações dos módulos do projeto (ajuste conforme estrutura real)
from app.services.receita_digital import (
    gerar_hash_prescricao,
    validar_documento_emitido,
    PrescricaoInvalidaError,
)
from app.models.receita import ReceitaDigital, Medicamento


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def prescricao_valida():
    """Cria uma prescrição válida com medicamentos."""
    return ReceitaDigital(
        cns_paciente="123456789012345",
        cpf_paciente="12345678901",
        cid10="J00",
        ciap2="R74",
        data_emissao=datetime.now(timezone.utc),
        medicamentos=[
            Medicamento(nome="Amoxicilina", dosagem="500mg", frequencia="8/8h", quantidade=10),
            Medicamento(nome="Paracetamol", dosagem="750mg", frequencia="6/6h", quantidade=20),
        ],
        observacoes="Tomar conforme orientação médica.",
    )


@pytest.fixture
def prescricao_vazia():
    """Cria uma prescrição sem medicamentos (inválida)."""
    return ReceitaDigital(
        cns_paciente="123456789012345",
        cpf_paciente="12345678901",
        cid10="J00",
        ciap2="R74",
        data_emissao=datetime.now(timezone.utc),
        medicamentos=[],
        observacoes="",
    )


# ----------------------------------------------------------------------
# Testes
# ----------------------------------------------------------------------

class TestGeracaoHashPrescricao:
    """Testes para a geração do hash SHA-256 da prescrição."""

    def test_geracao_hash_prescricao(self, prescricao_valida):
        """
        Verifica que o hash gerado é um SHA-256 válido (64 caracteres hexadecimais)
        e que é determinístico para a mesma prescrição.
        """
        hash1 = gerar_hash_prescricao(prescricao_valida)
        hash2 = gerar_hash_prescricao(prescricao_valida)

        # Verifica formato SHA-256
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)

        # Verifica determinismo
        assert hash1 == hash2

    def test_hash_muda_com_dados_diferentes(self, prescricao_valida):
        """
        Verifica que alterações nos dados da prescrição geram hashes diferentes.
        """
        hash_original = gerar_hash_prescricao(prescricao_valida)

        # Modifica um campo (ex: observações)
        prescricao_modificada = prescricao_valida.model_copy(update={"observacoes": "Nova observação"})
        hash_modificado = gerar_hash_prescricao(prescricao_modificada)

        assert hash_original != hash_modificado

    def test_hash_consistente_com_sha256(self, prescricao_valida):
        """
        Verifica que o hash gerado corresponde ao cálculo manual de SHA-256
        sobre a representação canônica da prescrição.
        """
        # Supondo que a função serialize a prescrição em JSON canônico
        import json
        dados_json = prescricao_valida.model_dump_json(sort_keys=True)
        hash_esperado = hashlib.sha256(dados_json.encode()).hexdigest()
        hash_gerado = gerar_hash_prescricao(prescricao_valida)

        assert hash_gerado == hash_esperado


class TestValidacaoDocumentoEmitido:
    """Testes para validação de autenticidade do documento emitido."""

    def test_validacao_documento_emitido(self, prescricao_valida):
        """
        Verifica que uma prescrição válida passa na validação de autenticidade.
        """
        # Simula a emissão do documento (gera hash e assinatura)
        documento = validar_documento_emitido(prescricao_valida)
        assert documento is True  # ou algum retorno esperado

    def test_validacao_documento_invalido(self, prescricao_valida):
        """
        Verifica que uma prescrição com hash adulterado falha na validação.
        """
        # Corrompe o hash (simulando alteração)
        prescricao_valida.hash_assinatura = "hash_invalido"

        with pytest.raises(PrescricaoInvalidaError):
            validar_documento_emitido(prescricao_valida)

    def test_validacao_documento_sem_assinatura(self, prescricao_valida):
        """
        Verifica que uma prescrição sem assinatura é rejeitada.
        """
        prescricao_valida.assinatura = None  # ou campo equivalente

        with pytest.raises(PrescricaoInvalidaError):
            validar_documento_emitido(prescricao_valida)


class TestPrescricaoSemMedicamentos:
    """Testes para rejeição de prescrição sem medicamentos."""

    def test_prescricao_sem_medicamentos(self, prescricao_vazia):
        """
        Verifica que uma prescrição sem medicamentos é rejeitada.
        """
        with pytest.raises(PrescricaoInvalidaError) as exc_info:
            # A função de validação deve lançar erro
            validar_documento_emitido(prescricao_vazia)

        assert "medicamentos" in str(exc_info.value).lower()

    def test_prescricao_com_medicamentos_aceita(self, prescricao_valida):
        """
        Verifica que uma prescrição com medicamentos é aceita.
        """
        # Deve passar sem exceção
        validar_documento_emitido(prescricao_valida)

    def test_prescricao_vazia_nao_gera_hash(self, prescricao_vazia):
        """
        Verifica que a geração de hash para prescrição vazia também falha.
        """
        with pytest.raises(PrescricaoInvalidaError):
            gerar_hash_prescricao(prescricao_vazia)
```