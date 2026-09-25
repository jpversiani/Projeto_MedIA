Here's a thinking process:

1.  **Understand User Goal:** The user wants me to create a Python backend service (`backend/app/services/soap_assistant.py`) for a medical application called "MedIA". This service should generate a structured SOAP (Subjective, Objective, Assessment, Plan) draft for family medicine doctors, based on patient complaints from a teleconsultation and past medical history. It needs to follow SUS/APS standards (CIAP-2, ICD-10/CID-10, SOAP method, CNS/CPF identification), use Python 3.12 with strict typing (Pydantic v2, SQLAlchemy 2.0), and include comprehensive automated tests with pytest.

2.  **Key Requirements:**
   - **File:** `backend/app/services/soap_assistant.py`
   - **Functionality:** Generate SOAP draft from patient complaints & history.
   - **Standards:** SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF)
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0, pytest
   - **Output:** Complete, executable code with file paths specified.
   - **Testing:** Comprehensive pytest coverage.

3.  **Deconstruct the Problem:**
   - **Input Data:** Patient complaints (subjective), teleconsultation notes, past medical history (objective/assessment), patient ID (CNS/CPF).
   - **Output Data:** Structured SOAP draft.
   - **AI Integration:** The prompt mentions "IA" (AI) in the title. I need to simulate or integrate an AI service for generating the SOAP draft. Since I can't actually call an external LLM API in a self-contained code snippet, I'll design a service that uses a mock/placeholder AI client but structure it so it can be easily swapped with a real LLM API (like OpenAI, local LLM, etc.). I'll use Pydantic for validation and SQLAlchemy for data models.
   - **SUS/APS Standards:** Need to handle CIAP-2 codes, CID-10 codes, CNS/CPF IDs, and SOAP structure.
   - **Testing:** Need pytest tests covering validation, generation logic, error handling, and mocking AI calls.

4.  **Design the Solution:**
   - **Models (Pydantic v2):**
     - `PatientInfo`: CNS, CPF, name, age, etc.
     - `TeleconsultationData`: complaints, vital signs, exam results, duration, etc.
     - `PastHistory`: previous diagnoses (CID-10/CIAP-2), medications, allergies, etc.
     - `SOAPDraft`: Subjective, Objective, Assessment, Plan fields.
     - `SOAPAssistantInput`: Combined input for the service.
   - **Service (`soap_assistant.py`):**
     - `SOAPAssistantService` class with a `generate_draft` method.
     - Uses a mock AI client (or configurable AI client interface).
     - Validates input using Pydantic.
     - Formats the draft according to SUS/APS standards.
     - Handles CIAP-2/CID-10 mapping (simplified for demo, but structured).
   - **Database Models (SQLAlchemy 2.0):**
     - `Patient`, `Teleconsultation`, `MedicalHistory` (simplified for context).
   - **AI Client Interface:** Abstract base class or simple mock for testing.
   - **Tests:** `test_soap_assistant.py` covering happy path, validation errors, AI failure, CIAP-2/CID-10 handling, etc.

5.  **Draft Code - `soap_assistant.py`:**
   ```python
   # Arquivo: backend/app/services/soap_assistant.py
   from __future__ import annotations
   from typing import Optional, List
   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy.orm import Session
   from datetime import datetime

   # --- Pydantic Models ---
   class PatientIdentifier(BaseModel):
       cns: str = Field(..., pattern=r"^\d{15}$", description="Cartão Nacional de Saúde (CNS)")
       cpf: str = Field(..., pattern=r"^\d{11}$", description="Cadastro de Pessoas Físicas")

   class VitalSigns(BaseModel):
       temperature: Optional[float] = None
       blood_pressure_sys: Optional[int] = None
       blood_pressure_dia: Optional[int] = None
       heart_rate: Optional[int] = None
       spo2: Optional[int] = None

   class PastMedicalHistory(BaseModel):
       previous_diagnoses: List[str] = Field(default_factory=list, description="Lista de códigos CID-10 ou CIAP-2")
       chronic_conditions: List[str] = Field(default_factory=list)
       current_medications: List[str] = Field(default_factory=list)
       allergies: List[str] = Field(default_factory=list)

   class TeleconsultationInput(BaseModel):
       patient: PatientIdentifier
       complaints: str = Field(..., min_length=1, description="Queixas relatadas pelo paciente")
       vital_signs: Optional[VitalSigns] = None
       exam_results: Optional[str] = None
       past_history: Optional[PastMedicalHistory] = None
       consultation_date: datetime = Field(default_factory=datetime.now)

   class SOAPDraft(BaseModel):
       subjectivo: str = Field(..., description="Queixas, história da doença atual, contexto psicossocial")
       objetivo: str = Field(..., description="Sinais vitais, exame físico, resultados de exames")
       avaliacao: str = Field(..., description="Hipóteses diagnósticas (CID-10/CIAP-2), análise clínica")
       plano: str = Field(..., description="Conduta, prescrições, encaminhamentos, orientações")
       generated_at: datetime = Field(default_factory=datetime.now)
       confidence_score: float = Field(ge=0.0, le=1.0, default=0.0, description="Score de confiança da IA")

   # --- AI Client Interface (Mock/Placeholder) ---
   class BaseAIAssistant(BaseModel):
       def generate_soap(self, input_data: TeleconsultationInput) -> SOAPDraft:
           raise NotImplementedError

   class MockAIAssistant(BaseAIAssistant):
       def generate_soap(self, input_data: TeleconsultationInput) -> SOAPDraft:
           # Simulates AI generation logic
           subj = f"Queixa principal: {input_data.complaints}. "
           subj += "Contexto psicossocial: Paciente em acompanhamento ambulatorial."
           obj = "Sinais vitais: "
           if input_data.vital_signs:
               obj += f"TA {input_data.vital_signs.blood_pressure_sys}/{input_data.vital_signs.blood_pressure_dia}mmHg, FC {input_data.vital_signs.heart_rate}bpm, Temp {input_data.vital_signs.temperature}°C."
           else:
               obj += "Não informados."
           obj += f" Exames: {input_data.exam_results or 'Pendentes/Normal'}."
           eval_text = "Hipóteses diagnósticas: "
           if input_data.past_history:
               eval_text += f"CID-10/CIAP-2: {', '.join(input_data.past_history.previous_diagnoses)}. "
           eval_text += "Análise clínica: Evolução compatível com quadro relatado."
           plan = "Conduta: "
           plan += "Manter acompanhamento na APS. "
           if input_data.past_history:
               plan += f"Revisar medicação: {', '.join(input_data.past_history.current_medications)}. "
           plan += "Orientações sobre dieta, atividade física e sinais de alerta."
           return SOAPDraft(
               subjectivo=subj,
               objetivo=obj,
               avaliacao=eval_text,
               plano=plan,
               confidence_score=0.85
           )

   # --- Service Layer ---
   class SOAPAssistantService:
       def __init__(self, ai_client: BaseAIAssistant = None):
           self.ai_client = ai_client or MockAIAssistant()

       def generate_draft(self, input_data: TeleconsultationInput, db: Optional[Session] = None) -> SOAPDraft:
           # Validate input
           validated_input = TeleconsultationInput.model_validate(input_data)

           # Generate SOAP using AI
           draft = self.ai_client.generate_soap(validated_input)

           # Optional: Save to DB or log (simplified)
           # if db:
           #     self._save_draft(db, validated_input, draft)

           return draft
   ```

6.  **Draft Code - `test_soap_assistant.py`:**
   Need comprehensive pytest tests.
   - Test Pydantic validation (CNS/CPF format, required fields)
   - Test happy path generation
   - Test AI failure handling (mock raises exception)
   - Test CIAP-2/CID-10 handling
   - Test optional fields (vital signs, past history)
   - Test confidence score bounds
   - Use `pytest`, `pytest-mock`, `pydantic`, `datetime`

   ```python
   # Arquivo: backend/app/tests/services/test_soap_assistant.py
   import pytest
   from datetime import datetime
   from pydantic import ValidationError
   from unittest.mock import MagicMock, patch
   from backend.app.services.soap_assistant import (
       TeleconsultationInput,
       PatientIdentifier,
       VitalSigns,
       PastMedicalHistory,
       SOAPDraft,
       BaseAIAssistant,
       MockAIAssistant,
       SOAPAssistantService
   )

   class TestTeleconsultationInputValidation:
       def test_valid_input(self):
           data = {
               "patient": {"cns": "123456789012345", "cpf": "12345678901"},
               "complaints": "Dor abdominal há 3 dias",
               "consultation_date": datetime.now()
           }
           input_data = TeleconsultationInput(**data)
           assert input_data.patient.cns == "123456789012345"
           assert input_data.patient.cpf == "12345678901"

       def test_invalid_cns_format(self):
           with pytest.raises(ValidationError):
               TeleconsultationInput(
                   patient={"cns": "123", "cpf": "12345678901"},
                   complaints="Dor"
               )

       def test_invalid_cpf_format(self):
           with pytest.raises(ValidationError):
               TeleconsultationInput(
                   patient={"cns": "123456789012345", "cpf": "123"},
                   complaints="Dor"
               )

       def test_empty_complaints(self):
           with pytest.raises(ValidationError):
               TeleconsultationInput(
                   patient={"cns": "123456789012345", "cpf": "12345678901"},
                   complaints=""
               )

   class TestMockAIAssistant:
       def test_generate_soap_basic(self):
           ai = MockAIAssistant()
           input_data = TeleconsultationInput(
               patient={"cns": "123456789012345", "cpf": "12345678901"},
               complaints="Febre e tosse",
               consultation_date=datetime.now()
           )
           draft = ai.generate_soap(input_data)
           assert isinstance(draft, SOAPDraft)
           assert "Febre e tosse" in draft.subjectivo
           assert draft.confidence_score == 0.85

       def test_generate_soap_with_vitals(self):
           ai = MockAIAssistant()
           input_data = TeleconsultationInput(
               patient={"cns": "123456789012345", "cpf": "12345678901"},
               complaints="Dor de cabeça",
               vital_signs={"temperature": 37.5, "blood_pressure_sys": 120, "blood_pressure_dia": 80, "heart_rate": 75, "spo2": 98},
               consultation_date=datetime.now()
           )
           draft = ai.generate_soap(input_data)
           assert "120/80mmHg" in draft.objetivo
           assert "75bpm" in draft.objetivo
           assert "37.5°C" in draft.objetivo

       def test_generate_soap_with_history(self):
           ai = MockAIAssistant()
           input_data = TeleconsultationInput(
               patient={"cns": "123456789012345", "cpf": "12345678901"},
               complaints="Hipertensão",
               past_history={"previous_diagnoses": ["I10", "K21.0"], "current_medications": ["Losartana 50mg"]},
               consultation_date=datetime.now()
           )
           draft = ai.generate_soap(input_data)
           assert "I10" in draft.avaliacao
           assert "Losartana 50mg" in draft.plano

   class TestSOAPAssistantService:
       def test_generate_draft_success(self, mocker):
           mock_ai = MagicMock(spec=BaseAIAssistant)
           mock_draft = SOAPDraft(
               subjectivo="Teste",
               objetivo="Teste",
               avaliacao="Teste",
               plano="Teste",
               confidence_score=0.9
           )
           mock_ai.generate_soap.return_value = mock_draft

           service = SOAPAssistantService(ai_client=mock_ai)
           input_data = TeleconsultationInput(
               patient={"cns": "123456789012345", "cpf": "12345678901"},
               complaints="Dor lombar",
               consultation_date=datetime.now()
           )
           result = service.generate_draft(input_data)

           assert result == mock_draft
           mock_ai.generate_soap.assert_called_once()

       def test_generate_draft_validation_error(self):
           service = SOAPAssistantService()
           with pytest.raises(ValidationError):
               service.generate_draft({
                   "patient": {"cns": "123", "cpf": "12345678901"},
                   "complaints": ""
               })

       def test_generate_draft_ai_failure(self, mocker):
           mock_ai = MagicMock(spec=BaseAIAssistant)
           mock_ai.generate_soap.side_effect = Exception("AI Service Unavailable")

           service = SOAPAssistantService(ai_client=mock_ai)
           input_data = TeleconsultationInput(
               patient={"cns": "123456789012345", "cpf": "12345678901"},
               complaints="Teste",
               consultation_date=datetime.now()
           )
           with pytest.raises(Exception, match="AI Service Unavailable"):
               service.generate_draft(input_data)

   class TestSOAPDraftValidation:
       def test_confidence_score_bounds(self):
           with pytest.raises(ValidationError):
               SOAPDraft(
                   subjectivo="S",
                   objetivo="O",
                   avaliacao="A",
                   plano="P",
                   confidence_score=-0.1
               )
           with pytest.raises(ValidationError):
               SOAPDraft(
                   subjectivo="S",
                   objetivo="O",
                   avaliacao="A",
                   plano="P",
                   confidence_score=1.1
               )
   ```

7.  **Review & Refine:**
   - **Python 3.12 & Strict Typing:** Used `from __future__ import annotations`, type hints, Pydantic v2 models with `Field`, `pattern`, `ge`, `le`.
   - **SQLAlchemy 2.0:** The prompt mentions SQLAlchemy 2.0. I should include a simple DB model or at least show how it integrates. I'll add a minimal SQLAlchemy 2.0 model for `SOAPDraftRecord` to satisfy the requirement, even if not fully used in the service logic. Actually, the prompt says "tipagem estrita com Pydantic v2 e SQLAlchemy 2.0". I'll add a SQLAlchemy 2.0 model for persistence and show how the service could use it.
   - **SUS/APS Standards:** Handled CNS/CPF validation, CIAP-2/CID-10 in past history, SOAP structure, APS terminology.
   - **AI Integration:** Used a mock/placeholder AI client with a clear interface. This is standard practice for testable code. I'll document how to swap it with a real LLM.
   - **Testing:** Comprehensive pytest coverage with validation, happy path, edge cases, AI failure, and Pydantic constraints.
   - **Structure:** I'll organize the code into two files as requested: `backend/app/services/soap_assistant.py` and `backend/app/tests/services/test_soap_assistant.py`. I'll also add a minimal SQLAlchemy 2.0 model file to satisfy the requirement explicitly, or integrate it into the service. Actually, I'll keep it focused on the service and tests, but add a SQLAlchemy 2.0 model for `SOAPDraft` to show compliance.

   Let's adjust `soap_assistant.py` to include a SQLAlchemy 2.0 model and ensure it's fully compliant with the prompt. I'll also add proper error handling and logging placeholders.

   Revised `soap_assistant.py` structure:
   - Pydantic models
   - SQLAlchemy 2.0 model
   - AI Client interface & Mock
   - Service class with DB integration placeholder
   - Clear comments

   I'll make sure the code is production-ready, follows SOLID principles, and is fully testable.

   Check Pydantic v2 syntax: `Field(pattern=...)`, `Field(ge=..., le=...)`, `model_validate` are correct.
   Check SQLAlchemy 2.0 syntax: `Mapped`, `mapped_column`, `DeclarativeBase` are correct.
   Check typing: `Optional`, `List`, `datetime` imports are correct.
  