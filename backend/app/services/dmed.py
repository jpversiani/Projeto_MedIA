from typing import List, Dict, Any, Optional

def calcular_relatorio_dmed_anual(registros: List[Dict[str, Any]], ano: Optional[int] = None) -> Dict[str, float]:
    """
    Agrupa e calcula o valor total pago por operadora para a declaração anual da DMED.
    """
    resultado: Dict[str, float] = {}
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
