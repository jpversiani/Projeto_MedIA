import pytest
from pydantic import ValidationError
from backend.models.paciente import Paciente, Alergia, Condicao
from backend.models.prescricao import Prescricao, Medicamento
from backend.models.soap import SOAPNote
from backend.services.copiloto_clinico import CopilotoClinico, ResultadoAvaliacao

from backend.models.paciente import Paciente, Alergia, Condicao
from backend.models.prescricao import Prescricao, Medicamento
from backend.models.soap import SOAPNote
from backend.services.copiloto_clinico import CopilotoClinico, ResultadoAvaliacao

class SOAPNote(BaseModel):
    paciente_id: str
    data: datetime
    subjetivo: str
    objetivo: str
    avaliacao: str
    plano: str
