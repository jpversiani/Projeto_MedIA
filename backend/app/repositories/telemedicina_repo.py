from pydantic import BaseModel, Field, field_validator
   from typing import Optional
   from datetime import datetime

   class AgendamentoCreate(BaseModel):
       paciente_cns: str = Field(..., min_length=15, max_length=15)
       paciente_cpf: str = Field(..., min_length=11, max_length=14)
       medico_cns: str = Field(..., min_length=15, max_length=15)
       codigo_sala: str
       data_agendamento: datetime
       cid10: Optional[str] = None
       ciap2: Optional[str] = None
       status: str = "AGENDADO"

       @field_validator('paciente_cns', 'medico_cns')
       @classmethod
       def validate_cns(cls, v):
           if not v.isdigit() or len(v) != 15:
               raise ValueError('CNS deve ter 15 dígitos numéricos')
           return v

   class EvolucaoSOAP(BaseModel):
       teleconsulta_id: str
       subjetiva: str
       objetiva: str
       avaliativa: str
       plano: str
       cid10: Optional[str] = None
       ciap2: Optional[str] = None
       data_registro: datetime = Field(default_factory=datetime.now)
