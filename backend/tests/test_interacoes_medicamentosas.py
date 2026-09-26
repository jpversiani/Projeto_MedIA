import pytest
from app.services.interacoes_medicamentosas import VerificadorFarmacologico


def test_detectar_interacao_grave_enalapril_espironolactona():
    rel = VerificadorFarmacologico.checar_interacoes_e_alergias(
        medicamentos_prescritos=["Enalapril 20mg", "Espironolactona 25mg"],
        alergias_paciente=[]
    )
    assert len(rel.interacoes_detectadas) == 1
    assert rel.interacoes_detectadas[0].gravidade == "GRAVE"
    assert "hipercalemia" in rel.interacoes_detectadas[0].mecanismo.lower()


def test_detectar_contraindicacao_varfarina_ibuprofeno():
    rel = VerificadorFarmacologico.checar_interacoes_e_alergias(
        medicamentos_prescritos=["Varfarina 5mg", "Ibuprofeno 600mg"],
        alergias_paciente=[]
    )
    assert len(rel.interacoes_detectadas) == 1
    assert rel.interacoes_detectadas[0].gravidade == "CONTRAINDICADO"
    assert rel.aprovado_para_dispensacao is False


def test_detectar_alergia_cruzada_penicilina():
    rel = VerificadorFarmacologico.checar_interacoes_e_alergias(
        medicamentos_prescritos=["Amoxicilina 500mg"],
        alergias_paciente=["Alergia grave a Penicilina"]
    )
    assert len(rel.alertas_alergia) >= 1
    assert rel.aprovado_para_dispensacao is False


def test_prescricao_segura_sem_interacoes():
    rel = VerificadorFarmacologico.checar_interacoes_e_alergias(
        medicamentos_prescritos=["Paracetamol 750mg", "Loratadina 10mg"],
        alergias_paciente=[]
    )
    assert len(rel.interacoes_detectadas) == 0
    assert len(rel.alertas_alergia) == 0
    assert rel.aprovado_para_dispensacao is True
