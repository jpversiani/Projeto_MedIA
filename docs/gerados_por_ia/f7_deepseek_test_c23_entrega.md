We need to create backend/tests/test_analytics_kpis.py for the MedIA project. The task: 1) validate exact calculation of absenteeism rate with protected division by zero; 2) verify consistency of heatmap matrix; 3) test aggregations of prevalent diagnosis by CIAP-2.

We need to infer the project structure. Likely there are existing modules for analytics/KPIs. Since we are asked to create tests, we need to assume some functions/classes exist. We should design tests that would pass given correct implementation. We can also create the test file with mocks or using actual code if we know the structure. But we don't have the actual source. We need to write tests that are self-contained, possibly using pytest and maybe creating dummy data.

The instructions say "Crie backend/tests/test_analytics_kpis.py". So we need to produce a file. We should include tests for:

1) Absenteeism rate calculation with zero division protection. Likely a function like calculate_absenteeism_rate(absent, total) returns 0.0 if total == 0 else absent/total * 100. We'll test that.

2) Heatmap matrix consistency: maybe a function that generates a matrix of some indicators (e.g., attendance by day/hour or by professional/period). We need to verify that the matrix sums match totals, dimensions, etc. We'll write tests for a hypothetical function.

3) Aggregations of prevalent diagnosis by CIAP-2: likely a function that groups diagnoses by CIAP-2 code and returns top N. We'll test that it correctly counts and sorts.

Since we don't have actual code, we can write tests that import from a module like backend.app.services.analytics or similar. But to make tests runnable, we need to define the expected interfaces. We can also write tests that use monkeypatching or direct function calls with sample data.

Given the instruction "Execute com precisão conforme a arquitetura", we should write tests that are consistent with the described architecture: Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS patterns. But tests can be unit tests that don't require DB.

I'll create a test file with:

- Imports: pytest, maybe from backend.app.services.analytics import calculate_absenteeism_rate, build_heatmap, aggregate_prevalent_diagnoses. But since we don't know if these exist, we can define them as expected. Alternatively, we can write tests that are self-contained by defining the functions within the test file? No, that would be testing our own code, not the project's. Better to assume the functions exist and write tests that will fail if they don't, which is typical TDD. But the task is to create tests, not implementation. So we should write tests that validate the behavior.

We can also use pytest.raises for division by zero? Actually protected division means it should not raise, but return 0. So test that.

Let's structure:

```python
# Arquivo: backend/tests/test_analytics_kpis.py
"""Testes de precisão algorítmica dos indicadores e agregações (C23)."""

import pytest
from backend.app.services.analytics import (
    calculate_absenteeism_rate,
    build_heatmap_matrix,
    aggregate_prevalent_diagnoses,
)
```

But we need to ensure the import path is correct. Since we are in backend/tests, the project root is backend. So we can use `from app.services.analytics import ...` if the backend is the root. Usually tests are run from backend directory. We'll use `from app.services.analytics import ...` or `from backend.app.services.analytics`? The instruction says "backend/tests/test_analytics_kpis.py", so the tests directory is inside backend. If backend is a package, we might need __init__.py. We'll assume the project uses a src layout or just app. To be safe, we can use `from app.services.analytics import ...` because backend is the project root and app is a package inside. But the instruction says "Projeto MedIA" and "backend/tests". So likely the backend directory contains app and tests. We'll use `from app.services.analytics import ...`.

Alternatively, we can write tests that don't rely on actual implementation by using monkeypatch or by defining the functions in a conftest? No.

Given the ambiguity, I'll write tests that import from a module and include a comment that the module must exist. But to make the test file self-contained and runnable, we could also include a fallback: if import fails, we define dummy functions? That would be bad practice.

Better: We'll write tests that are clear about the expected interface. The user will likely have the implementation. We'll provide the test file as requested.

Let's design each test:

### 1) Test absenteeism rate

Function signature: `calculate_absenteeism_rate(absent: int, total: int) -> float` returns percentage (0-100) or 0.0 if total == 0.

Tests:
- test_absenteeism_rate_normal: absent=5, total=20 -> 25.0
- test_absenteeism_rate_zero_total: absent=0, total=0 -> 0.0 (no division error)
- test_absenteeism_rate_all_absent: absent=10, total=10 -> 100.0
- test_absenteeism_rate_no_absent: absent=0, total=10 -> 0.0
- test_absenteeism_rate_float_precision: absent=1, total=3 -> 33.333333333333336 (or round to 2? We'll test with approx)

Also test that it doesn't raise ZeroDivisionError.

### 2) Heatmap matrix consistency

Function signature: `build_heatmap_matrix(records: list[dict]) -> list[list[float]]` or something. We need to define what "consistency" means. Possibly the matrix represents, e.g., attendance by day of week and time slot. The consistency could be that the sum of all cells equals the total number of records, and each cell is non-negative, and dimensions are as expected.

We'll define a sample input: list of records with 'day' and 'time_slot' keys. The function returns a matrix with rows = days (e.g., 5 weekdays) and columns = time slots (e.g., morning, afternoon, evening). We'll test that the sum of all cells equals the number of records, and that each cell is integer (or float) and non-negative.

Alternatively, the heatmap could be for "absenteísmo por hora do dia" etc. We'll keep generic.

We'll write tests:

- test_heatmap_matrix_sum_matches_total: create records, call function, sum all cells == len(records)
- test_heatmap_matrix_dimensions: expected rows/cols
- test_heatmap_matrix_no_negative_values
- test_heatmap_matrix_empty_records: returns matrix of zeros with correct dimensions.

We need to know the exact signature. We'll assume `build_heatmap_matrix(records: list[dict]) -> list[list[int]]` where each dict has 'day' (int 0-4) and 'time_slot' (int 0-2). We'll document that.

### 3) Prevalent diagnosis by CIAP-2

Function signature: `aggregate_prevalent_diagnoses(records: list[dict], top_n: int = 10) -> list[dict]` or returns a list of (code, count) sorted descending. We'll test:

- test_aggregate_prevalent_diagnoses_counts: given records with 'ciap2' codes, returns correct counts.
- test_aggregate_prevalent_diagnoses_sorted: sorted by count descending.
- test_aggregate_prevalent_diagnoses_top_n: returns only top N.
- test_aggregate_prevalent_diagnoses_empty: returns empty list.

We'll need to define the input format. We'll assume records are dicts with 'ciap2' key.

We'll also test that it handles missing 'ciap2'? Maybe not.

Now, to make the tests runnable, we need to ensure the import works. Since we don't have the actual module, we can create a conftest.py that adds the backend directory to sys.path, or we can use relative imports. But the test file itself should be runnable with pytest from the backend directory. We'll include a comment about the expected module.

Alternatively, we can write tests that use `pytest.importorskip` to skip if module not available. But that would not validate anything if missing. The task is to create tests, so we should assume the module exists.

I'll write the test file with clear docstrings and type hints. I'll also include a fixture for sample data.

Let's produce the final answer with the code block.

We need to specify the file path at the top: `# Arquivo: backend/tests/test_analytics_kpis.py`.

Let's write the code.

We'll also include a test for protected division by zero using `pytest.raises(ZeroDivisionError)`? Actually we want to assert it does NOT raise. So we just call it and assert result == 0.0.

We'll use `pytest.approx` for float comparisons.

Now, let's craft the code.```python
# Arquivo: backend/tests/test_analytics_kpis.py
"""
Testes de precisão algorítmica dos indicadores e agregações (C23).

Valida:
1. Cálculo exato da taxa de absenteísmo com divisão protegida por zero.
2. Consistência da matriz de heatmap (somas, dimensões, não negatividade).
3. Agregações de diagnóstico prevalente por CIAP-2 (contagem, ordenação, top N).
"""

import pytest

from app.services.analytics import (
    calculate_absenteeism_rate,
    build_heatmap_matrix,
    aggregate_prevalent_diagnoses,
)


# -----------------------------------------------------------------------------
# 1. Taxa de absenteísmo
# -----------------------------------------------------------------------------

class TestAbsenteeismRate:
    """Testes para o cálculo da taxa de absenteísmo."""

    def test_normal_rate(self):
        """Cálculo padrão: 5 faltas em 20 consultas -> 25%."""
        assert calculate_absenteeism_rate(absent=5, total=20) == pytest.approx(25.0)

    def test_zero_total_protected(self):
        """Divisão por zero protegida: total=0 deve retornar 0.0, sem exceção."""
        assert calculate_absenteeism_rate(absent=0, total=0) == 0.0
        assert calculate_absenteeism_rate(absent=3, total=0) == 0.0

    def test_all_absent(self):
        """100% de absenteísmo."""
        assert calculate_absenteeism_rate(absent=10, total=10) == pytest.approx(100.0)

    def test_no_absent(self):
        """0% de absenteísmo."""
        assert calculate_absenteeism_rate(absent=0, total=10) == pytest.approx(0.0)

    def test_float_precision(self):
        """Precisão com dízima: 1 falta em 3 consultas -> 33.333...%."""
        assert calculate_absenteeism_rate(absent=1, total=3) == pytest.approx(33.333333333333336)

    def test_does_not_raise_zero_division(self):
        """Garante que nenhuma chamada levanta ZeroDivisionError."""
        try:
            calculate_absenteeism_rate(absent=0, total=0)
            calculate_absenteeism_rate(absent=5, total=0)
        except ZeroDivisionError:
            pytest.fail("calculate_absenteeism_rate não deve levantar ZeroDivisionError")


# -----------------------------------------------------------------------------
# 2. Consistência da matriz de heatmap
# -----------------------------------------------------------------------------

class TestHeatmapMatrixConsistency:
    """
    Testes para a matriz de heatmap.

    A função `build_heatmap_matrix` recebe uma lista de registros (dicts) com
    as chaves 'day' (int 0-4) e 'time_slot' (int 0-2) e retorna uma matriz
    (list[list[int]]) de dimensões 5x3, onde cada célula representa a contagem
    de ocorrências para aquele dia e período.
    """

    @pytest.fixture
    def sample_records(self):
        """Registros de exemplo com distribuição conhecida."""
        return [
            {"day": 0, "time_slot": 0},
            {"day": 0, "time_slot": 0},
            {"day": 0, "time_slot": 1},
            {"day": 1, "time_slot": 2},
            {"day": 2, "time_slot": 0},
            {"day": 2, "time_slot": 1},
            {"day": 2, "time_slot": 1},
            {"day": 3, "time_slot": 2},
            {"day": 4, "time_slot": 0},
            {"day": 4, "time_slot": 2},
        ]

    def test_matrix_dimensions(self, sample_records):
        """A matriz deve ter 5 linhas (dias) e 3 colunas (períodos)."""
        matrix = build_heatmap_matrix(sample_records)
        assert len(matrix) == 5
        assert all(len(row) == 3 for row in matrix)

    def test_matrix_sum_matches_total_records(self, sample_records):
        """A soma de todas as células deve ser igual ao número de registros."""
        matrix = build_heatmap_matrix(sample_records)
        total = sum(sum(row) for row in matrix)
        assert total == len(sample_records)

    def test_matrix_no_negative_values(self, sample_records):
        """Nenhuma célula pode ser negativa."""
        matrix = build_heatmap_matrix(sample_records)
        assert all(cell >= 0 for row in matrix for cell in row)

    def test_matrix_known_values(self, sample_records):
        """Verifica contagens específicas para o exemplo."""
        matrix = build_heatmap_matrix(sample_records)
        # Dia 0, período 0: 2 ocorrências
        assert matrix[0][0] == 2
        # Dia 2, período 1: 2 ocorrências
        assert matrix[2][1] == 2
        # Dia 4, período 1: 0 ocorrências
        assert matrix[4][1] == 0

    def test_empty_records(self):
        """Lista vazia deve gerar matriz 5x3 toda zerada."""
        matrix = build_heatmap_matrix([])
        assert len(matrix) == 5
        assert all(len(row) == 3 for row in matrix)
        assert all(cell == 0 for row in matrix for cell in row)


# -----------------------------------------------------------------------------
# 3. Agregações de diagnóstico prevalente por CIAP-2
# -----------------------------------------------------------------------------

class TestAggregatePrevalentDiagnoses:
    """
    Testes para a agregação de diagnósticos prevalentes por código CIAP-2.

    A função `aggregate_prevalent_diagnoses` recebe uma lista de registros
    (dicts) com a chave 'ciap2' e um parâmetro opcional `top_n` (default 10).
    Retorna uma lista de dicionários no formato:
        [{"code": "A01", "count": 5}, ...]
    ordenada por contagem decrescente e limitada a `top_n` itens.
    """

    @pytest.fixture
    def diagnosis_records(self):
        """Registros com códigos CIAP-2 repetidos."""
        return [
            {"ciap2": "A01"},
            {"ciap2": "A01"},
            {"ciap2": "A01"},
            {"ciap2": "B02"},
            {"ciap2": "B02"},
            {"ciap2": "C03"},
            {"ciap2": "D04"},
            {"ciap2": "D04"},
            {"ciap2": "D04"},
            {"ciap2": "D04"},
            {"ciap2": "E05"},
        ]

    def test_counts(self, diagnosis_records):
        """Contagem correta por código."""
        result = aggregate_prevalent_diagnoses(diagnosis_records)
        result_map = {item["code"]: item["count"] for item in result}
        assert result_map["A01"] == 3
        assert result_map["B02"] == 2
        assert result_map["C03"] == 1
        assert result_map["D04"] == 4
        assert result_map["E05"] == 1

    def test_sorted_by_count_descending(self, diagnosis_records):
        """Resultado deve estar ordenado por contagem decrescente."""
        result = aggregate_prevalent_diagnoses(diagnosis_records)
        counts = [item["count"] for item in result]
        assert counts == sorted(counts, reverse=True)

    def test_top_n(self, diagnosis_records):
        """Deve retornar apenas os top N itens."""
        result = aggregate_prevalent_diagnoses(diagnosis_records, top_n=3)
        assert len(result) == 3
        # Os três maiores: D04 (4), A01 (3), B02 (2)
        codes = [item["code"] for item in result]
        assert codes == ["D04", "A01", "B02"]

    def test_empty_records(self):
        """Lista vazia deve retornar lista vazia."""
        assert aggregate_prevalent_diagnoses([]) == []

    def test_all_same_code(self):
        """Quando todos os registros têm o mesmo código, retorna apenas ele."""
        records = [{"ciap2": "A01"} for _ in range(10)]
        result = aggregate_prevalent_diagnoses(records)
        assert len(result) == 1
        assert result[0] == {"code": "A01", "count": 10}
```