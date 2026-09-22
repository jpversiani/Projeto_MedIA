from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.atendimento import ProblemaCreate

class CopilotSOAPRequest(BaseModel):
    relato_clinico: str = Field(..., description="Texto livre da conversa médica, queixa ou áudio transcrito da consulta")
    cidadao_id: Optional[int] = Field(None, description="ID do cidadão para cruzar com histórico e alergias")
    pressao_aferida: Optional[str] = Field(None, description="Ex: 150/90")
    frequencia_cardiaca: Optional[int] = None
    glicemia: Optional[int] = None

class CopilotSOAPResponse(BaseModel):
    subjetivo_motivo: str
    subjetivo_notas: str
    objetivo_exame_fisico: str
    avaliacao_notas: str
    plano_conduta: str
    plano_prescricoes: str
    plano_exames: str
    problemas_sugeridos: List[ProblemaCreate] = []
    alertas_seguranca: List[str] = []
