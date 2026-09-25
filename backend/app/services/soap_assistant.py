# Arquivo: backend/app/services/soap_assistant.py
   from __future__ import annotations
   from datetime import datetime
   from typing import Optional
   from pydantic import BaseModel, Field, field_validator
   import logging

   logger = logging.getLogger(__name__)

   # Pydantic Models
   class PatientInfo(BaseModel):
       cpf: str = Field(..., pattern=r"^\d{11}$")
       cns: str = Field(..., pattern=r"^\d{15}$")
       name: str

   class VitalSigns(BaseModel):
       temperature: Optional[float] = None
       systolic_bp: Optional[int] = None
       diastolic_bp: Optional[int] = None
       heart_rate: Optional[int] = None
       spo2: Optional[int] = None

   class TeleconsultationData(BaseModel):
       complaints: str
       past_history: str
       vitals: Optional[VitalSigns] = None
       exam_findings: Optional[str] = None

   class SOAPDraft(BaseModel):
       patient_cns: str
       patient_cpf: str
       patient_name: str
       subjective: str
       objective: str
       assessment: str
       plan: str
       ciap_codes: list[str] = Field(default_factory=list)
       icd_codes: list[str] = Field(default_factory=list)
       generated_at: datetime = Field(default_factory=datetime.utcnow)

       @field_validator('subjective', 'objective', 'assessment', 'plan')
       @classmethod
       def not_empty(cls, v):
           if not v or not v.strip():
               raise ValueError("SOAP sections cannot be empty")
           return v.strip()

   # Service Logic
   class SOAPAssistantService:
       def __init__(self, ai_client: Optional[object] = None):
           self.ai_client = ai_client

       def generate_draft(self, patient: PatientInfo, data: TeleconsultationData) -> SOAPDraft:
           # 1. Validate inputs
           # 2. Generate AI prompt
           # 3. Call AI (or fallback)
           # 4. Parse & structure result
           # 5. Return SOAPDraft
           pass

# Arquivo: backend/app/services/test_soap_assistant.py
   import pytest
   from datetime import datetime
   from pydantic import ValidationError
   from unittest.mock import MagicMock, patch
   from backend.app.services.soap_assistant import (
       PatientInfo, TeleconsultationData, SOAPDraft, SOAPAssistantService
   )

   # Fixtures
   @pytest.fixture
   def valid_patient():
       return PatientInfo(cpf="12345678901", cns="700000000000000", name="João Silva")

   @pytest.fixture
   def valid_data():
       return TeleconsultationData(
           complaints="Dor de cabeça há 3 dias, febre 38°C",
           past_history="Hipertensão, Diabetes tipo 2",
           vitals=VitalSigns(temperature=38.2, systolic_bp=140, diastolic_bp=90, heart_rate=88, spo2=96),
           exam_findings="Faringe hiperêmica, amígdalas aumentadas"
       )

   # Tests...
