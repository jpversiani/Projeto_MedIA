from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.cidadao import CidadaoOut


class FilaAcolhimentoBase(BaseModel):
    cidadao_id: int
    estabelecimento_id: int
    profissional_triagem_id: int | None = None
    tipo_demanda: str = "ESPONTANEA"
    classificacao_risco: str = "VERDE"  # VERMELHO (Emergência), AMARELO (Urgência), VERDE (Pouco urgente), AZUL (Não urgente)
    motivo_acolhimento: str | None = None

    # Sinais Vitais
    pressao_sistolica: int | None = None
    pressao_diastolica: int | None = None
    frequencia_cardiaca: int | None = None
    frequencia_respiratoria: int | None = None
    temperatura: float | None = None
    saturacao_o2: int | None = None
    glicemia_capilar: int | None = None
    peso_kg: float | None = None
    altura_cm: float | None = None
    imc: float | None = None


class FilaAcolhimentoCreate(FilaAcolhimentoBase):
    @model_validator(mode="after")
    def compute_imc(self):
        if self.peso_kg and self.altura_cm and self.altura_cm > 0:
            altura_m = self.altura_cm / 100.0
            self.imc = round(self.peso_kg / (altura_m * altura_m), 2)
        return self


class FilaAcolhimentoUpdate(BaseModel):
    status: str | None = None
    classificacao_risco: str | None = None
    motivo_acolhimento: str | None = None


class FilaAcolhimentoOut(FilaAcolhimentoBase):
    id: int
    data_hora_entrada: datetime
    status: str
    created_at: datetime
    cidadao: CidadaoOut | None = None
    model_config = ConfigDict(from_attributes=True)
