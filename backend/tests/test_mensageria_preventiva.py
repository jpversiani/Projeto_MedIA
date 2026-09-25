import pytest
from datetime import datetime, timedelta

def test_regra_lembrete_consulta():
    horario_consulta = datetime.now() + timedelta(minutes=15)
    agora = datetime.now()
    diferenca_minutos = (horario_consulta - agora).total_seconds() / 60
    deve_lembrar = 10 <= diferenca_minutos <= 20
    assert deve_lembrar is True
