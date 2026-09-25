import pytest
from pydantic import BaseModel
from typing import List

class ItemPrescricao(BaseModel):
    medicamento: str
    dosagem: str
    quantidade: int

class Prescricao(BaseModel):
    id: str
    medico_crm: str
    paciente_cpf: str
    itens: List[ItemPrescricao]

def test_modelo_prescricao():
    p = Prescricao(
        id="rec-001",
        medico_crm="CRM/MG 12345",
        paciente_cpf="111.222.333-44",
        itens=[ItemPrescricao(medicamento="Losartana 50mg", dosagem="1 comp ao dia", quantidade=30)]
    )
    assert p.id == "rec-001"
    assert len(p.itens) == 1
    assert p.itens[0].quantidade == 30
