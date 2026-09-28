from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional

from app.services.calculadoras_clinicas import CalculadorasClinicas
from app.services.interacoes_medicamentosas import VerificadorFarmacologico

router = APIRouter(prefix="/clinica", tags=["Inteligência Clínica & Farmacológica"])


class FraminghamRequest(BaseModel):
    sexo: str = Field(..., json_schema_extra={"example": "M"}, description="M ou F")
    idade: int = Field(..., ge=20, le=100, json_schema_extra={"example": 52})
    colesterol_total: float = Field(..., json_schema_extra={"example": 220.0})
    colesterol_hdl: float = Field(..., json_schema_extra={"example": 42.0})
    pressao_sistolica: float = Field(..., json_schema_extra={"example": 145.0})
    em_tratamento_has: bool = Field(True, json_schema_extra={"example": True})
    fumante: bool = Field(False, json_schema_extra={"example": False})
    diabetico: bool = Field(True, json_schema_extra={"example": True})


class CKDEPISchema(BaseModel):
    creatinina_serica: float = Field(..., json_schema_extra={"example": 1.3}, description="Creatinina sérica em mg/dL")
    idade: int = Field(..., ge=18, le=120, json_schema_extra={"example": 64})
    sexo: str = Field(..., json_schema_extra={"example": "F"}, description="M ou F")


class IMCSchema(BaseModel):
    peso_kg: float = Field(..., json_schema_extra={"example": 82.5})
    altura_cm: float = Field(..., json_schema_extra={"example": 172.0})


class InteracaoRequest(BaseModel):
    medicamentos: List[str] = Field(..., json_schema_extra={"example": ["Enalapril 20mg", "Espironolactona 25mg"]})
    alergias: List[str] = Field(default_factory=list, json_schema_extra={"example": ["Penicilina"]})


@router.post("/framingham")
def calcular_framingham(dados: FraminghamRequest):
    """Calcula o risco cardiovascular em 10 anos com categorização e conduta clínica."""
    res = CalculadorasClinicas.calcular_framingham(**dados.model_dump())
    return {
        "pontuacao_total": res.pontuacao_total,
        "risco_percentual": res.risco_percentual,
        "categoria_risco": res.categoria_risco,
        "recomendacao_clinica": res.recomendacao_clinica
    }


@router.post("/ckd-epi")
def calcular_ckd_epi(dados: CKDEPISchema):
    """Calcula eGFR pelo algoritmo internacional KDIGO CKD-EPI 2021."""
    res = CalculadorasClinicas.calcular_ckd_epi(**dados.model_dump())
    return {
        "egfr": res.egfr,
        "estagio_drc": res.estagio_drc,
        "descricao_estagio": res.descricao_estagio,
        "alerta_clinico": res.alerta_clinico
    }


@router.post("/imc")
def calcular_imc(dados: IMCSchema):
    """Calcula IMC e peso ideal mínimo e máximo segundo faixas OMS."""
    return CalculadorasClinicas.classificar_imc(dados.peso_kg, dados.altura_cm)


@router.post("/checar-interacoes")
def checar_interacoes(dados: InteracaoRequest):
    """Varre interações medicamentosas graves da Rename e hipersensibilidades alérgicas."""
    relatorio = VerificadorFarmacologico.checar_interacoes_e_alergias(
        medicamentos_prescritos=dados.medicamentos,
        alergias_paciente=dados.alergias
    )
    return {
        "total_medicamentos_analisados": relatorio.total_medicamentos_analisados,
        "aprovado_para_dispensacao": relatorio.aprovado_para_dispensacao,
        "total_interacoes": len(relatorio.interacoes_detectadas),
        "interacoes": [
            {
                "medicamento_a": i.medicamento_a,
                "medicamento_b": i.medicamento_b,
                "gravidade": i.gravidade,
                "mecanismo": i.mecanismo,
                "conduta_recomendada": i.conduta_recomendada
            } for i in relatorio.interacoes_detectadas
        ],
        "alertas_alergia": relatorio.alertas_alergia
    }
