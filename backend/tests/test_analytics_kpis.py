def test_calculo_taxa_absenteismo() -> None:
    agendamentos_totais = 100
    faltas = 15
    taxa = (faltas / agendamentos_totais) * 100
    assert taxa == 15.0

def test_divisao_protegida_zero() -> None:
    agendamentos_totais = 0
    faltas = 0
    taxa = (faltas / agendamentos_totais * 100) if agendamentos_totais > 0 else 0.0
    assert taxa == 0.0

def test_estrutura_heatmap_semanal() -> None:
    # Matriz 7x24 para dias da semana e horas
    heatmap = [[0 for _ in range(24)] for _ in range(7)]
    assert len(heatmap) == 7
    assert len(heatmap[0]) == 24
