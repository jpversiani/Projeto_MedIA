# Arquivo: backend/app/services/soap_assistant.py
   from __future__ import annotations
   import logging
   from datetime import datetime
   from typing import Optional
   from pydantic import BaseModel, Field, field_validator

   logger = logging.getLogger(__name__)

   class SOAPInput(BaseModel):
       patient_id: str
       complaints: list[str]
       teleconsultation_notes: str
       past_history: list[str]
       vitals: dict[str, float] = Field(default_factory=dict)
       lab_results: dict[str, str] = Field(default_factory=dict)
       risk_factors: list[str] = Field(default_factory=list)

       @field_validator("complaints")
       @classmethod
       def validate_complaints(cls, v: list[str]) -> list[str]:
           if not v:
               raise ValueError("Complaints cannot be empty")
           return [c.strip() for c in v if c.strip()]

   class SOAPOutput(BaseModel):
       subjective: str
       objective: str
       assessment: str
       plan: str
       confidence_score: float = Field(ge=0.0, le=1.0)
       generated_at: datetime = Field(default_factory=datetime.utcnow)
       patient_id: str

       @field_validator("confidence_score")
       @classmethod
       def validate_confidence(cls, v: float) -> float:
           return round(v, 2)

   class SOAPAssistantService:
       def __init__(self) -> None:
           self._logger = logging.getLogger(__name__)

       def generate_draft(self, input_data: SOAPInput) -> SOAPOutput:
           self._logger.info("Generating SOAP draft for patient %s", input_data.patient_id)

           subjective = self._generate_subjective(input_data)
           objective = self._generate_objective(input_data)
           assessment = self._generate_assessment(input_data)
           plan = self._generate_plan(input_data)

           # Confidence score based on data completeness
           confidence = self._calculate_confidence(input_data)

           return SOAPOutput(
               patient_id=input_data.patient_id,
               subjective=subjective,
               objective=objective,
               assessment=assessment,
               plan=plan,
               confidence_score=confidence,
           )

       def _generate_subjective(self, data: SOAPInput) -> str:
           complaints_str = " | ".join(data.complaints)
           notes_str = data.teleconsultation_notes.strip()
           history_str = " | ".join(data.past_history) if data.past_history else "N/A"
           return f"Queixa Principal: {complaints_str}\nHistória da Doença Atual: {notes_str}\nHistórico Pregresso: {history_str}"

       def _generate_objective(self, data: SOAPInput) -> str:
           vitals_parts = [f"{k}: {v}" for k, v in data.vitals.items()]
           labs_parts = [f"{k}: {v}" for k, v in data.lab_results.items()]
           vitals_str = ", ".join(vitals_parts) if vitals_parts else "Não informado"
           labs_str = ", ".join(labs_parts) if labs_parts else "Não informado"
           return f"Sinais Vitais: {vitals_str}\nExames Complementares: {labs_str}"

       def _generate_assessment(self, data: SOAPInput) -> str:
           risk_str = " | ".join(data.risk_factors) if data.risk_factors else "Nenhum fator de risco relevante identificado"
           # Simplified clinical logic for demonstration
           if "hipertensão" in " ".join(data.complaints).lower() or "hipertensão" in " ".join(data.past_history).lower():
               impression = "Hipertensão arterial sistêmica em acompanhamento."
           elif "dor" in " ".join(data.complaints).lower():
               impression = "Dor aguda em investigação. Diferenciais: musculoesquelética, visceral ou inflamatória."
           else:
               impression = "Quadro clínico em evolução. Necessita correlação clínica e exames complementares."
           return f"Impressão Diagnóstica: {impression}\nFatores de Risco: {risk_str}"

       def _generate_plan(self, data: SOAPInput) -> str:
           plan_items = []
           if data.vitals.get("pa_sistolica", 0) > 140:
               plan_items.append("Ajuste terapêutico para hipertensão conforme protocolo local.")
           if data.lab_results:
               plan_items.append("Acompanhar resultados laboratoriais para reavaliação.")
           plan_items.append("Orientações sobre estilo de vida e adesão terapêutica.")
           plan_items.append("Retorno em 15 dias ou antes se piora dos sintomas.")
           return "Plano Terapêutico:\n" + "\n".join(f"- {item}" for item in plan_items)

       def _calculate_confidence(self, data: SOAPInput) -> float:
           score = 0.0
           if data.complaints: score += 0.3
           if data.teleconsultation_notes: score += 0.2
           if data.vitals: score += 0.2
           if data.lab_results: score += 0.15
           if data.past_history: score += 0.15
           return min(score, 1.0)
