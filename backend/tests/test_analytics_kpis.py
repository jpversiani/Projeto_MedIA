# Arquivo: backend/tests/test_analytics_kpis.py
"""Testes de precisão algorítmica dos indicadores e agregações (C23)."""

import pytest
from backend.app.services.analytics import (
    calculate_absenteeism_rate,
    build_heatmap_matrix,
    aggregate_prevalent_diagnoses,
)

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
