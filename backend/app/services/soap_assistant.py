# Arquivo: backend/app/services/soap_assistant.py
     from __future__ import annotations
     from dataclasses import dataclass
     from datetime import datetime
     from typing import Protocol
     from pydantic import BaseModel, Field, field_validator, ConfigDict
     import re

     # Pydantic models
     class SOAPInput(BaseModel):
         patient_cns: str = Field(..., description="Cartão Nacional de Saúde (15 dígitos)")
         patient_cpf: str = Field(..., description="CPF do paciente (11 dígitos)")
         complaints: str = Field(..., description="Queixas relatadas pelo paciente")
         history: str = Field(..., description="Histórico pregresso relevante")
         vitals: dict[str, str | float | int] = Field(default_factory=dict, description="Sinais vitais")
         ciap_codes: list[str] = Field(default_factory=list, description="Códigos CIAP-2 sugeridos")
         cid_codes: list[str] = Field(default_factory=list, description="Códigos CID-10 sugeridos")

         @field_validator("patient_cns")
         @classmethod
         def validate_cns(cls, v: str) -> str:
             if not re.match(r"^\d{15}$", v):
                 raise ValueError("CNS deve conter exatamente 15 dígitos numéricos")
             return v

         @field_validator("patient_cpf")
         @classmethod
         def validate_cpf(cls, v: str) -> str:
             if not re.match(r"^\d{11}$", v):
                 raise ValueError("CPF deve conter exatamente 11 dígitos numéricos")
             return v

     class SOAPDraft(BaseModel):
         model_config = ConfigDict(populate_by_name=True)
         patient_cns: str
         patient_cpf: str
         generated_at: datetime = Field(default_factory=datetime.now)
         subjective: str = Field(..., alias="Subjetivo")
         objective: str = Field(..., alias="Objetivo")
         assessment: str = Field(..., alias="Avaliação")
         plan: str = Field(..., alias="Plano")
         ciap_codes: list[str] = []
         cid_codes: list[str] = []

     # AI Provider Interface
     class AIProvider(Protocol):
         def generate_soap_sections(self, input_data: SOAPInput) -> dict[str, str]: ...

     # Mock/Default AI Provider (simulates AI for deterministic testing)
     class DefaultAIProvider:
         def generate_soap_sections(self, input_data: SOAPInput) -> dict[str, str]:
             # Simulate AI generation based on input
             return {
                 "Subjetivo": f"Queixa principal: {input_data.complaints}. Histórico: {input_data.history}",
                 "Objetivo": f"Sinais vitais: {input_data.vitals}. Exame físico: conforme histórico.",
                 "Avaliação": f"CID-10: {', '.join(input_data.cid_codes) if input_data.cid_codes else 'Aguardar exames'}. CIAP-2: {', '.join(input_data.ciap_codes) if input_data.ciap_codes else 'Aguardar'}.",
                 "Plano": "1. Exames complementares conforme avaliação.\n2. Conduta terapêutica.\n3. Retorno em 15 dias."
             }

     # Service
     class SOAPAssistantService:
         def __init__(self, ai_provider: AIProvider | None = None):
             self.ai_provider = ai_provider or DefaultAIProvider()

         def generate_draft(self, input_data: SOAPInput) -> SOAPDraft:
             sections = self.ai_provider.generate_soap_sections(input_data)
             return SOAPDraft(
                 patient_cns=input_data.patient_cns,
                 patient_cpf=input_data.patient_cpf,
                 subjective=sections.get("Subjetivo", ""),
                 objective=sections.get("Objetivo", ""),
                 assessment=sections.get("Avaliação", ""),
                 plan=sections.get("Plano", ""),
                 ciap_codes=input_data.ciap_codes,
                 cid_codes=input_data.cid_codes,
             )

# Arquivo: backend/app/services/test_soap_assistant.py
     import pytest
     from pydantic import ValidationError
     from datetime import datetime
     from backend.app.services.soap_assistant import SOAPInput, SOAPDraft, SOAPAssistantService, DefaultAIProvider, AIProvider
     from unittest.mock import MagicMock

     class TestSOAPInputValidation:
         def test_valid_cns_and_cpf(self):
             input_data = SOAPInput(
                 patient_cns="123456789012345",
                 patient_cpf="12345678901",
                 complaints="Dor de cabeça",
                 history="Hipertensão"
             )
             assert input_data.patient_cns == "123456789012345"
             assert input_data.patient_cpf == "12345678901"

         def test_invalid_cns_length(self):
             with pytest.raises(ValidationError):
                 SOAPInput(patient_cns="123", patient_cpf="12345678901", complaints="X", history="Y")

         def test_invalid_cpf_length(self):
             with pytest.raises(ValidationError):
                 SOAPInput(patient_cns="123456789012345", patient_cpf="123", complaints="X", history="Y")

     class TestSOAPAssistantService:
         def test_generate_draft_with_mock_ai(self, mocker):
             mock_ai = MagicMock(spec=AIProvider)
             mock_ai.generate_soap_sections.return_value = {
                 "Subjetivo": "S", "Objetivo": "O", "Avaliação": "A", "Plano": "P"
             }
             service = SOAPAssistantService(ai_provider=mock_ai)
             input_data = SOAPInput(patient_cns="123456789012345", patient_cpf="12345678901", complaints="C", history="H")
             draft = service.generate_draft(input_data)
             assert draft.subjective == "S"
             assert draft.objective == "O"
             assert draft.assessment == "A"
             assert draft.plan == "P"
             assert draft.patient_cns == "123456789012345"
             assert draft.patient_cpf == "12345678901"
             assert isinstance(draft.generated_at, datetime)

         def test_generate_draft_with_default_ai(self):
             service = SOAPAssistantService()
             input_data = SOAPInput(
                 patient_cns="123456789012345",
                 patient_cpf="12345678901",
                 complaints="Dor abdominal",
                 history="Diabetes tipo 2",
                 vitals={"PA": "130/80", "FC": "78"},
                 ciap_codes=["B10"],
                 cid_codes=["E11.9"]
             )
             draft = service.generate_draft(input_data)
             assert "Dor abdominal" in draft.subjective
             assert "Diabetes tipo 2" in draft.subjective
             assert "E11.9" in draft.assessment
             assert "B10" in draft.assessment

         def test_draft_serialization(self):
             service = SOAPAssistantService()
             input_data = SOAPInput(patient_cns="123456789012345", patient_cpf="12345678901", complaints="C", history="H")
             draft = service.generate_draft(input_data)
             json_data = draft.model_dump(by_alias=True)
             assert "Subjetivo" in json_data
             assert "Objetivo" in json_data
             assert "Avaliação" in json_data
             assert "Plano" in json_data
