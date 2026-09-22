from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional
from datetime import datetime
from app.schemas.cidadao import CidadaoOut

class FilaAcolhimentoBase(BaseModel):
    cidadao_id: int
    estabelecimento_id: int
    profissional_triagem_id: Optional[int] = None
    tipo_demanda: str = "ESPONTANEA"
    classificacao_risco: str = "VERDE" # VERMELHO (Emergência), AMARELO (Urgência), VERDE (Pouco urgente), AZUL (Não urgente)
    motivo_acolhimento: Optional[str] = None
    
    # Sinais Vitais
    pressao_sistolica: Optional[int] = None
    pressao_diastolica: Optional[int] = None
    frequencia_cardiaca: Optional[int] = None
    frequencia_respiratoria: Optional[int] = None
    temperatura: Optional[float] = None
    saturacao_o2: Optional[int] = None
    glicemia_capilar: Optional[int] = None
    peso_kg: Optional[float] = None
    altura_cm: Optional[float] = None
    imc: Optional[float] = None

class FilaAcolhimentoCreate(FilaAcolhimentoBase):
    @model_validator(mode="after")
    def compute_imc(self):
        if self.peso_kg and self.altura_cm and self.altura_cm > 0:
            altura_m = self.altura_cm / 100.0
            self.imc = round(self.peso_kg / (altura_m * altura_m), 2)
        return self

class FilaAcolhimentoUpdate(BaseModel):
    status: Optional[str] = None
    classificacao_risco: Optional[str] = None
    motivo_acolhimento: Optional[str] = None

class FilaAcolhimentoOut(FilaAcolhimentoBase):
    id: int
    data_hora_entrada: datetime
    status: str
    created_at: datetime
    cidadao: Optional[CidadaoOut] = None
    model_config = ConfigDict(from_attributes=True)
