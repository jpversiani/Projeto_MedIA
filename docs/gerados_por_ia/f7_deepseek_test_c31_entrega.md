We need to create a test file for the MedIA project. The task is to create backend/tests/test_analytics_kpis.py with three specific tests:

1. Validate exact calculation of absenteeism rate with zero-protected division.
2. Verify consistency of heatmap matrix.
3. Test aggregations of prevalent diagnosis by CIAP-2.

We need to follow architecture guidelines: Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0. SUS/APS patterns (CIAP-2, CID-10, SOAP, CNS/CPF). Maintain full compliance and coverage with pytest.

We need to produce the complete code for the test file. We should also consider that the test file will be part of a larger project, but we only need to create this file. We need to ensure it's executable and well-structured.

We should design tests that are self-contained, perhaps using mocks or fixtures. Since we don't have the actual implementation, we need to write tests that would pass if the implementation is correct. But the task says "crie backend/tests/test_analytics_kpis.py" - create the test file. We need to write tests that validate the described behaviors. We can assume there are functions/classes in the backend that we need to test. We'll need to import them. Since we don't know the exact structure, we can define the tests in a way that they test the expected behavior, possibly using mocks or by defining minimal implementations? But the instruction says "valida cálculo exato da taxa de absenteísmo com divisão protegida por zero" - so we need to test a function that calculates absenteeism rate. We'll need to import that function from somewhere. We can either assume it exists and import it, or we can create a test that uses a function we define? The task is to create tests, not implementation. So we should write tests that import from the actual codebase. Since we don't have the codebase, we need to make reasonable assumptions about the module paths and function names.

We can structure the test file with imports like:

from backend.services.analytics import calculate_absenteeism_rate, build_heatmap_matrix, get_prevalent_diagnoses

But we don't know if these exist. Alternatively, we can write tests that use mocks to simulate the behavior, but that would not test actual implementation. The task says "Testes de Precisão Algorítmica dos Indicadores e Agregações" - tests of algorithmic precision. So we need to test the actual algorithms. Since we are the engineer, we might also need to create the implementation? But the task only asks to create the test file. However, to make the tests pass, we need to have the implementation. But the instruction is to create the test file, not the implementation. In a real scenario, we would have the implementation already. So we should write tests that assume the implementation exists and follows certain contracts.

We can define the expected behavior and write tests that would pass if the implementation is correct. We'll need to import the functions from the appropriate modules. We can also use pytest fixtures to set up test data.

Let's outline the three tests:

1. Test absenteeism rate calculation:
   - Function signature: maybe `calculate_absenteeism_rate(total_appointments, missed_appointments)` returns float.
   - Should handle zero total appointments: return 0.0 or None? "divisão protegida por zero" means protected division, so likely return 0.0 when total is zero.
   - Test exact calculation: e.g., 3 missed out of 10 -> 0.3 or 30%? We need to decide. Usually rate is a percentage. We'll assume it returns a float between 0 and 1 or 0-100. We'll test with known values.

2. Heatmap matrix consistency:
   - "verifica consistência da matriz de heatmap" - verify consistency of heatmap matrix. This could mean that the matrix dimensions are correct, values are within expected ranges, row/column sums match, etc.
   - We need to test a function that builds a heatmap matrix, maybe from appointment data by day/hour or by some dimensions. We'll assume a function `build_heatmap_matrix(data)` returns a 2D list or numpy array.
   - We'll test that the matrix has expected shape, values are non-negative, and maybe that the sum of all entries equals the total count.

3. Prevalent diagnosis aggregation by CIAP-2:
   - Test that given a list of diagnoses with CIAP-2 codes, the aggregation returns the most frequent ones, correctly grouped.
   - We'll test that the function returns a sorted list of (code, count) or a dict.

We need to write these tests with proper typing and Pydantic v2? The tests themselves may not need Pydantic, but we can use it for fixtures. We'll use pytest.

Let's design the test file.

We'll start with imports:

import pytest
from typing import List, Dict, Any
from decimal import Decimal

We'll import the functions we need. Since we don't know the exact paths, we can use a try-except or assume a standard structure. Let's assume the project has a backend package with modules like:

- backend/services/analytics.py
- backend/models/schemas.py (Pydantic models)

We'll import:

from backend.services.analytics import calculate_absenteeism_rate, build_heatmap_matrix, aggregate_prevalent_diagnoses

If these don't exist, the tests will fail. But that's okay; the task is to create the tests. We'll also add a comment that these are the expected functions.

We'll write test functions with descriptive names.

Test 1:

def test_absenteeism_rate_exact_calculation():
    # Test with known values
    assert calculate_absenteeism_rate(100, 20) == 0.2  # or 20.0 if percentage
    assert calculate_absenteeism_rate(0, 0) == 0.0  # zero-protected
    assert calculate_absenteeism_rate(10, 3) == pytest.approx(0.3)

We need to decide on return type. We'll assume it returns a float between 0 and 1. We'll use pytest.approx for floating point.

Test 2:

def test_heatmap_matrix_consistency():
    # Create sample data: list of appointments with day and hour
    data = [
        {"day": "Mon", "hour": 9},
        {"day": "Mon", "hour": 9},
        {"day": "Tue", "hour": 10},
        # etc.
    ]
    matrix = build_heatmap_matrix(data)
    # Check it's a 2D list
    assert isinstance(matrix, list)
    assert all(isinstance(row, list) for row in matrix)
    # Check dimensions: maybe 7 days x 24 hours? Or configurable.
    # We'll assume 7x24.
    assert len(matrix) == 7
    assert all(len(row) == 24 for row in matrix)
    # Check all values are non-negative integers
    for row in matrix:
        for val in row:
            assert isinstance(val, int) and val >= 0
    # Check sum equals total number of appointments
    total = sum(sum(row) for row in matrix)
    assert total == len(data)

We need to be careful: if the function returns a numpy array, we can still check. We'll use list.

Test 3:

def test_prevalent_diagnosis_aggregation_by_ciap2():
    # Sample diagnoses with CIAP-2 codes
    diagnoses = [
        {"code": "A01", "description": "Pain"},
        {"code": "A01", "description": "Pain"},
        {"code": "B02", "description": "Infection"},
        {"code": "C03", "description": "Other"},
        {"code": "A01", "description": "Pain"},
    ]
    result = aggregate_prevalent_diagnoses(diagnoses)
    # Expect a list of tuples or dicts sorted by count descending
    # We'll assume it returns a list of (code, count) sorted descending.
    assert result[0] == ("A01", 3)
    assert result[1] == ("B02", 1)
    assert result[2] == ("C03", 1)

We can also test that it handles empty list.

We should also add type hints and docstrings.

Now, we need to ensure the test file is complete and executable. We'll include a pytest fixture for sample data if needed.

We'll also add a test for zero-protected division specifically: when total is zero, it should not raise ZeroDivisionError.

Let's write the file.

We'll also include a conftest? Not necessary.

We'll put the file at backend/tests/test_analytics_kpis.py.

We'll use absolute imports. We'll assume the backend is a package. If not, we can adjust.

Let's produce the code.```python
# Arquivo: backend/tests/test_analytics_kpis.py
"""
Testes de precisão algorítmica para indicadores e agregações do Projeto MedIA.

Cobre:
1. Cálculo exato da taxa de absenteísmo com divisão protegida por zero.
2. Consistência da matriz de heatmap.
3. Agregações de diagnóstico prevalente por CIAP-2.

Conformidade:
- Python 3.12, tipagem estrita.
- Pydantic v2 e SQLAlchemy 2.0 (quando aplicável).
- Padrões SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF).
- Execução via pytest.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

import pytest

# Importações das funções de analytics do backend.
# Ajuste os caminhos conforme a estrutura real do projeto.
from backend.services.analytics import (
    aggregate_prevalent_diagnoses,
    build_heatmap_matrix,
    calculate_absenteeism_rate,
)


# -----------------------------------------------------------------------------
# 1. Taxa de absenteísmo
# -----------------------------------------------------------------------------
class TestAbsenteeismRate:
    """
    Testes para o cálculo da taxa de absenteísmo.
    A função `calculate_absenteeism_rate` deve receber o total de consultas
    agendadas e o número de faltas, retornando um float entre 0 e 1.
    Em caso de total zero, deve retornar 0.0 (divisão protegida).
    """

    def test_exact_calculation_with_known_values(self) -> None:
        """
        Verifica o cálculo exato para valores inteiros e decimais.
        """
        # 20 faltas em 100 consultas -> 0.2
        assert calculate_absenteeism_rate(100, 20) == pytest.approx(0.2)

        # 3 faltas em 10 consultas -> 0.3
        assert calculate_absenteeism_rate(10, 3) == pytest.approx(0.3)

        # 0 faltas em 50 consultas -> 0.0
        assert calculate_absenteeism_rate(50, 0) == 0.0

        # 1 falta em 3 consultas -> 0.333...
        assert calculate_absenteeism_rate(3, 1) == pytest.approx(1 / 3)

    def test_zero_total_does_not_raise(self) -> None:
        """
        Garante que a divisão por zero é protegida e retorna 0.0.
        """
        assert calculate_absenteeism_rate(0, 0) == 0.0
        assert calculate_absenteeism_rate(0, 5) == 0.0

    def test_missed_greater_than_total_raises_value_error(self) -> None:
        """
        Caso o número de faltas exceda o total, a função deve levantar
        ValueError (dado inconsistente).
        """
        with pytest.raises(ValueError):
            calculate_absenteeism_rate(10, 11)

    def test_negative_values_raise_value_error(self) -> None:
        """
        Valores negativos não são aceitos.
        """
        with pytest.raises(ValueError):
            calculate_absenteeism_rate(-1, 0)
        with pytest.raises(ValueError):
            calculate_absenteeism_rate(10, -1)


# -----------------------------------------------------------------------------
# 2. Matriz de heatmap
# -----------------------------------------------------------------------------
class TestHeatmapMatrix:
    """
    Testes para a construção e consistência da matriz de heatmap.
    A função `build_heatmap_matrix` deve receber uma lista de eventos
    (consultas) e retornar uma matriz 7x24 (dias da semana x horas),
    com contagens inteiras não negativas.
    """

    @pytest.fixture
    def sample_appointments(self) -> List[Dict[str, Any]]:
        """
        Gera uma lista de consultas com dia da semana e hora.
        """
        return [
            {"day": "Mon", "hour": 9},
            {"day": "Mon", "hour": 9},
            {"day": "Mon", "hour": 10},
            {"day": "Tue", "hour": 14},
            {"day": "Wed", "hour": 9},
            {"day": "Sun", "hour": 0},  # domingo à meia-noite
        ]

    def test_matrix_dimensions(self, sample_appointments: List[Dict[str, Any]]) -> None:
        """
        A matriz deve ter 7 linhas (dias) e 24 colunas (horas).
        """
        matrix = build_heatmap_matrix(sample_appointments)
        assert len(matrix) == 7
        for row in matrix:
            assert len(row) == 24

    def test_matrix_values_are_non_negative_integers(
        self, sample_appointments: List[Dict[str, Any]]
    ) -> None:
        """
        Todos os valores da matriz devem ser inteiros >= 0.
        """
        matrix = build_heatmap_matrix(sample_appointments)
        for row in matrix:
            for value in row:
                assert isinstance(value, int)
                assert value >= 0

    def test_matrix_sum_matches_total_appointments(
        self, sample_appointments: List[Dict[str, Any]]
    ) -> None:
        """
        A soma de todos os elementos da matriz deve ser igual ao número total
        de consultas fornecidas.
        """
        matrix = build_heatmap_matrix(sample_appointments)
        total = sum(sum(row) for row in matrix)
        assert total == len(sample_appointments)

    def test_matrix_consistency_with_known_counts(
        self, sample_appointments: List[Dict[str, Any]]
    ) -> None:
        """
        Verifica se as contagens em posições específicas estão corretas.
        """
        matrix = build_heatmap_matrix(sample_appointments)
        # Segunda-feira (índice 0) às 9h -> 2 consultas
        assert matrix[0][9] == 2
        # Segunda-feira às 10h -> 1
        assert matrix[0][10] == 1
        # Terça-feira (índice 1) às 14h -> 1
        assert matrix[1][14] == 1
        # Quarta-feira (índice 2) às 9h -> 1
        assert matrix[2][9] == 1
        # Domingo (índice 6) às 0h -> 1
        assert matrix[6][0] == 1

    def test_empty_input_returns_zero_matrix(self) -> None:
        """
        Para lista vazia, a matriz deve ser toda zeros.
        """
        matrix = build_heatmap_matrix([])
        assert len(matrix) == 7
        for row in matrix:
            assert all(value == 0 for value in row)


# -----------------------------------------------------------------------------
# 3. Agregação de diagnósticos prevalentes por CIAP-2
# -----------------------------------------------------------------------------
class TestPrevalentDiagnoses:
    """
    Testes para a agregação de diagnósticos por código CIAP-2.
    A função `aggregate_prevalent_diagnoses` deve receber uma lista de
    dicionários contendo pelo menos a chave 'code' (CIAP-2) e retornar
    uma lista de tuplas (code, count) ordenada por contagem decrescente.
    """

    @pytest.fixture
    def sample_diagnoses(self) -> List[Dict[str, str]]:
        """
        Lista de diagnósticos com códigos CIAP-2.
        """
        return [
            {"code": "A01", "description": "Dor generalizada"},
            {"code": "A01", "description": "Dor generalizada"},
            {"code": "B02", "description": "Infecção"},
            {"code": "C03", "description": "Outro"},
            {"code": "A01", "description": "Dor generalizada"},
            {"code": "D01", "description": "Dor abdominal"},
        ]

    def test_aggregation_counts_and_order(
        self, sample_diagnoses: List[Dict[str, str]]
    ) -> None:
        """
        Verifica se a agregação retorna as contagens corretas e ordenadas.
        """
        result = aggregate_prevalent_diagnoses(sample_diagnoses)
        # Espera-se que o resultado seja uma lista de tuplas (code, count)
        assert isinstance(result, list)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in result)

        # Ordenação decrescente por contagem
        counts = [count for _, count in result]
        assert counts == sorted(counts, reverse=True)

        # Verifica os valores exatos
        assert result[0] == ("A01", 3)
        assert ("B02", 1) in result
        assert ("C03", 1) in result
        assert ("D01", 1) in result

    def test_aggregation_empty_list(self) -> None:
        """
        Lista vazia deve retornar lista vazia.
        """
        assert aggregate_prevalent_diagnoses([]) == []

    def test_aggregation_single_item(self) -> None:
        """
        Um único diagnóstico deve retornar contagem 1.
        """
        diagnoses = [{"code": "A01", "description": "Dor"}]
        result = aggregate_prevalent_diagnoses(diagnoses)
        assert result == [("A01", 1