```python
# backend/app/services/mensageria_preventiva.py
"""
Serviço de mensageria e alertas preventivos para vacinas e consultas.

Gera lembretes automáticos para teleconsultas agendadas (WhatsApp/SMS mock)
e identifica pacientes que necessitam de busca ativa:
- Crianças com vacinas atrasadas
- Diabéticos sem acompanhamento há mais de 90 dias
"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

# Importação dos modelos existentes no projeto
# Ajuste os nomes conforme a estrutura real do projeto
from ..models import (
    Appointment,
    Consultation,
    Patient,
    VaccineRecord,
)


# Schemas Pydantic para os dados de saída
class LembreteTeleconsulta(BaseModel):
    """Representa um lembrete de teleconsulta a ser enviado."""
    paciente_id: int
    paciente_nome: str
    telefone: str
    data_hora_consulta: datetime
    mensagem: str
    canal: str = Field(..., pattern="^(whatsapp|sms)$")


class AlertaBuscaAtiva(BaseModel):
    """Representa um alerta de busca ativa para um paciente."""
    paciente_id: int
    paciente_nome: str
    tipo_alerta: str = Field(..., pattern="^(vacina_atrasada|diabetico_sem_acompanhamento)$")
    detalhes: Optional[str] = None


class MensageriaPreventivaService:
    """
    Serviço responsável por gerar lembretes e identificar busca ativa.
    """

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------
    # Lembretes de teleconsultas
    # ------------------------------------------------------------------
    def gerar_lembretes_teleconsultas(
        self, horas_antecedencia: int =