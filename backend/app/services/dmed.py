from typing import Any


def calcular_relatorio_dmed_anual(registros: list[dict[str, Any]], ano: int | None = None) -> dict[str, float]:
    """
    Agrupa e calcula o valor total pago por operadora para a declaração anual da DMED.
    """
    resultado: dict[str, float] = {}
    for item in registros:
        val = item.get("valor")
        if val is None:
            continue
        item_ano = item.get("ano")
        if ano is not None and item_ano != ano:
            continue
        op = item.get("operadora", "Outros")
        resultado[op] = round(resultado.get(op, 0.0) + float(val), 2)
    return resultado
