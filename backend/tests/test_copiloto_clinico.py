import pytest
from pydantic import BaseModel, Field
from typing import List, Optional

class Alergia(BaseModel):
    medicamento: str
    gravidade: str

class Condicao(BaseModel):
    codigo_cid: str
    descricao: str

class Paciente(BaseModel):
    id: str
    nome: str
    alergias: List[Alergia] = Field(default_factory=list)
    condicoes: List[Condicao] = Field(default_factory=list)

def test_modelo_paciente_copiloto():
    paciente = Paciente(
        id="pac-123",
        nome="Joao Silva",
        alergias=[Alergia(medicamento="Penicilina", gravidade="Alta")],
        condicoes=[Condicao(codigo_cid="I10", descricao="Hipertensao Arterial")]
    )
    assert paciente.nome == "Joao Silva"
    assert len(paciente.alergias) == 1
    assert paciente.alergias[0].medicamento == "Penicilina"

def test_alerta_contraindicacao_simulada():
    alergias = ["Dipirona", "AAS"]
    medicamento_prescrito = "AAS"
    conflito = medicamento_prescrito in alergias
    assert conflito is True
