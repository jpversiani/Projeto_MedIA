Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/services/soap_assistant.py` for a "Smart Medical Record Summarizer and SOAP Draft with AI (C46)" feature.
   - **Target User:** Family doctor in "MedIA" (presumably a telemedicine platform).
   - **Functionality:** Generate a structured SOAP draft (Subjective, Objective, Assessment, Plan) from patient complaints during teleconsultation and past medical history, saving typing time.
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Full compliance and automated test coverage with pytest.
   - **Output Requirement:** Provide complete, executable code. Specify file paths in code blocks.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/services/soap_assistant.py`
   - **Core Logic:** Generate SOAP draft from inputs (complaints, history, vitals, etc.)
   - **Standards:** CIAP-2 (International Classification of Primary Care), CID-10 (ICD-10), SOAP format, CNS/CPF IDs.
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0, pytest.
   - **Testing:** Need to provide pytest tests for this service.
   - **AI Integration:** The prompt mentions "com IA" (with AI). I should simulate or structure it to call an AI service, but keep it testable. I'll create a mockable AI client interface or use a placeholder that can be swapped with an actual LLM API call. For the sake of the task, I'll implement a deterministic/template-based generator that can be easily extended, or use a mock AI call with clear interfaces. Actually, the prompt says "com IA", so I should structure it to use an AI service, but keep it abstract enough for testing. I'll create a `SoapAssistantService` class that takes inputs and returns a structured SOAP draft. I'll include a mock AI integration point.

3.  **Design the Service (`soap_assistant.py`):**
   - **Models (Pydantic v2):**
     - `PatientInfo`: CNS, CPF, name, age, etc.
     - `TeleconsultationData`: chief_complaint, history, vitals, exam_results, etc.
     - `SoapDraft`: Subjective, Objective, Assessment, Plan, ciap_codes, cid_codes, generated_at.
   - **Service Class:** `SoapAssistantService`
     - Method: `generate_soap_draft(patient_info: PatientInfo, consultation_data: TeleconsultationData) -> SoapDraft`
     - Logic: Parse inputs, map to SOAP structure, apply CIAP-2/CID-10 mapping (simplified for demo), call AI (mocked/abstracted), return structured draft.
   - **AI Integration:** I'll define an `AIClient` protocol/interface and use a mock for testing. Or just implement a simple template-based generator that simulates AI output for reliability in this context, but clearly mark where AI would be called. Given the constraint "código completo e executável", I'll implement a deterministic generator that follows SOAP guidelines and includes CIAP-2/CID-10 mapping logic, with a clear extension point for AI. I'll also add a `generate_with_ai` method that uses a simulated AI call (or actual OpenAI-like structure if needed, but mock is safer for testing).
   - **SUS/APS Standards:** CIAP-2 codes for symptoms/complaints, CID-10 for diagnoses, SOAP structure, CNS/CPF identification.

4.  **Draft `soap_assistant.py` (Mental Refinement):**
   ```python
   # Arquivo: backend/app/services/soap_assistant.py
   from __future__ import annotations
   from dataclasses import dataclass
   from datetime import datetime
   from typing import Protocol
   from pydantic import BaseModel, Field, field_validator
   import re

   # Pydantic Models
   class PatientInfo(BaseModel):
       cns: str = Field(..., pattern=r"^\d{15}$", description="Cartão Nacional de Saúde")
       cpf: str = Field(..., pattern=r"^\d{11}$", description="Cadastro de Pessoas Físicas")
       nome: str
       idade: int

   class TeleconsultationData(BaseModel):
       queixa_principal: str
       historia_pregressa: str = ""
       sinais_sintomas: list[str] = Field(default_factory=list)
       sinais_vitais: dict[str, str] = Field(default_factory=dict)
       exames_resultados: list[str] = Field(default_factory=list)

   class SoapDraft(BaseModel):
       paciente: PatientInfo
       consulta: TeleconsultationData
       subjetivo: str
       objetivo: str
       avaliacao: str
       plano: str
       ciap_codes: list[str] = Field(default_factory=list)
       cid_codes: list[str] = Field(default_factory=list)
       gerado_em: datetime = Field(default_factory=datetime.utcnow)

       @field_validator("ciap_codes", "cid_codes")
       @classmethod
       def validate_codes(cls, v):
           # CIAP-2 format: 2 letters + 2 digits (e.g., A01.1)
           # CID-10 format: 1 letter + 2 digits (e.g., J06.9)
           ciap_pattern = re.compile(r"^[A-Z]{2}\.\d{1,2}$")
           cid_pattern = re.compile(r"^[A-Z]\d{2}(\.\d{1,2})?$")
           for code in v:
               if not ciap_pattern.match(code) and not cid_pattern.match(code):
                   raise ValueError(f"Código inválido: {code}")
           return v

   # AI Client Protocol
   class AIClientProtocol(Protocol):
       async def generate_soap_text(self, prompt: str) -> str: ...

   # Mock/Real AI Client
   class MockAIClient:
       async def generate_soap_text(self, prompt: str) -> str:
           return f"[IA] Rascunho gerado a partir de: {prompt[:50]}..."

   # Service
   class SoapAssistantService:
       def __init__(self, ai_client: AIClientProtocol | None = None):
           self.ai_client = ai_client or MockAIClient()

       async def generate_soap_draft(
           self,
           patient: PatientInfo,
           consultation: TeleconsultationData
       ) -> SoapDraft:
           # 1. Map symptoms to CIAP-2 (simplified mapping for demo)
           ciap_map = {
               "dor de cabeça": "A01.1",
               "febre": "A04.1",
               "tosse": "A06.1",
               "fadiga": "A08.1",
               "dor abdominal": "A10.1"
           }
           ciap_codes = []
           for symptom in consultation.sinais_sintomas:
               for key, code in ciap_map.items():
                   if key.lower() in symptom.lower():
                       ciap_codes.append(code)
                       break

           # 2. Map to CID-10 (simplified)
           cid_map = {
               "dor de cabeça": "R51",
               "febre": "R50.9",
               "tosse": "R05",
               "fadiga": "R53.83",
               "dor abdominal": "R10.9"
           }
           cid_codes = []
           for symptom in consultation.sinais_sintomas:
               for key, code in cid_map.items():
                   if key.lower() in symptom.lower():
                       cid_codes.append(code)
                       break

           # 3. Generate SOAP sections
           subjetivo = f"{patient.nome} ({patient.idade} anos, CNS: {patient.cns}, CPF: {patient.cpf})\n" \
                       f"Queixa principal: {consultation.queixa_principal}\n" \
                       f"História pregressa: {consultation.historia_pregressa or 'Não informada'}"

           objetivo = "Exame físico e sinais vitais:\n"
           for vital, value in consultation.sinais_vitais.items():
               objetivo += f"- {vital}: {value}\n"
           objetivo += "Exames complementares:\n"
           for exam in consultation.exames_resultados:
               objetivo += f"- {exam}\n"

           avaliacao = f"Diagnóstico diferencial: {', '.join(cid_codes) if cid_codes else 'A definir'}\n" \
                       f"CIAP-2: {', '.join(ciap_codes) if ciap_codes else 'A definir'}"

           plano = "Plano terapêutico e conduta:\n" \
                   "- Acompanhamento ambulatorial\n" \
                   "- Exames complementares conforme necessidade\n" \
                   "- Orientações ao paciente"

           # 4. AI Enhancement (optional but requested)
           if self.ai_client:
               prompt = f"Paciente: {patient.nome}. Queixa: {consultation.queixa_principal}. Sintomas: {consultation.sinais_sintomas}. Histórica: {consultation.historia_pregressa}."
               ai_enhanced = await self.ai_client.generate_soap_text(prompt)
               # In a real app, we'd parse AI output and merge. For now, we'll keep the structured draft.
               # Let's assume AI returns a structured text that we can use to refine sections.
               # For simplicity, we'll just note it in the draft or use it to generate the full text.
               # Actually, I'll make the service return the structured draft, and the AI part can be integrated later.
               # To satisfy "com IA", I'll add a method that uses AI to generate the full SOAP text.

           return SoapDraft(
               paciente=patient,
               consulta=consultation,
               subjetivo=subjetivo,
               objetivo=objetivo,
               avaliacao=avaliacao,
               plano=plano,
               ciap_codes=ciap_codes,
               cid_codes=cid_codes,
               gerado_em=datetime.utcnow()
           )
   ```

   Wait, the prompt says "com IA". I should make the AI integration more explicit and testable. I'll create a proper async service that uses an AI client, and provide a mock for testing. I'll also ensure Pydantic v2 and SQLAlchemy 2.0 compatibility (though SQLAlchemy isn't directly used in this service, it's part of the architecture guidelines. I'll add a note or a simple model if needed, but the service itself is stateless. I'll stick to Pydantic for data validation).

   Let's refine the service to be more robust and aligned with SUS/APS standards. I'll add proper CIAP-2/CID-10 mapping logic (simplified but structured), and ensure the AI part is clearly defined. I'll also make sure it's fully type-hinted and uses Pydantic v2 correctly.

5.  **Draft `test_soap_assistant.py`:**
   - Need pytest tests covering:
     - Valid input generation
     - CIAP-2/CID-10 mapping
     - AI client integration (mocked)
     - Validation errors (invalid CNS/CPF, invalid codes)
     - Edge cases (empty symptoms, missing history)
   - Use `pytest-asyncio` for async methods.
   - Mock the AI client.
   - Test Pydantic validation.

   Structure:
   ```python
   # Arquivo: tests/unit/services/test_soap_assistant.py
   import pytest
   from datetime import datetime
   from backend.app.services.soap_assistant import (
       PatientInfo,
       TeleconsultationData,
       SoapDraft,
       SoapAssistantService,
       AIClientProtocol,
       MockAIClient
   )
   from pydantic import ValidationError
   from unittest.mock import AsyncMock, MagicMock

   class TestPatientInfo:
       def test_valid_cns_cpf(self):
           p = PatientInfo(cns="123456789012345", cpf="12345678901", nome="João", idade=30)
           assert p.cns == "123456789012345"
           assert p.cpf == "12345678901"

       def test_invalid_cns(self):
           with pytest.raises(ValidationError):
               PatientInfo(cns="123", cpf="12345678901", nome="João", idade=30)

   # ... more tests ...
   ```

   I'll flesh out the tests properly.

6.  **Check Requirements:**
   - Python 3.12, strict typing: ✅
   - Pydantic v2: ✅
   - SQLAlchemy 2.0: The service doesn't directly use DB, but I should mention it's designed to integrate with SQLAlchemy models. I'll add a simple SQLAlchemy model for `SoapDraft` in a separate file or note it, but the prompt asks for `backend/app/services/soap_assistant.py`. I'll keep it focused on the service. I can add a comment about SQLAlchemy integration or create a simple model if needed. Actually, the prompt says "tipagem estrita com Pydantic v2 e SQLAlchemy 2.0", so I should ensure compatibility. I'll add a SQLAlchemy 2.0 mapped class for `SoapDraft` in the same file or as a separate model, but the service is the focus. I'll stick to Pydantic for the service layer and note SQLAlchemy compatibility.
   - SUS/APS standards (CIAP-2, CID-10, SOAP, CNS/CPF): ✅
   - Full compliance and pytest coverage: ✅
   - Complete executable code: ✅

   I need to make sure the code is production-ready, well-structured, and includes proper error handling, type hints, and async support. I'll also add a `generate_soap_with_ai` method that actually uses the AI client to enhance the draft, and provide a mock for testing.

   Let's refine the service to be more complete:
   - Use `pydantic` for validation
   - Use `asyncio` for AI calls
   - Add proper logging
   - Ensure CIAP-2/CID-10 mapping is robust
   - Add tests

   I'll structure the response with:
   1. `backend/app/services/soap_assistant.py`
   2. `tests/unit/services/test_soap_assistant.py`
   3. Brief instructions on how to run tests.

   I'll make sure the code is self-contained and executable. I'll use `pytest-asyncio` for async tests. I'll mock the AI client properly.

   Let's write it out carefully. 
   Self-Correction/Refinement during thought:
   - The prompt says "SQLAlchemy 2.0". I should include a SQLAlchemy 2.0 model for `SoapDraft` to fully comply, or at least show how it integrates. I'll add a `SoapDraftModel` using SQLAlchemy 2.0 declarative base in the same file or as a separate model. But the service is the focus. I'll keep the service focused on Pydantic for data transfer, and add a note about SQLAlchemy integration. Actually, I'll add a simple SQLAlchemy 2.0 mapped class for completeness.
   - I'll ensure all type hints are strict.
   - I'll use `pydantic.v1`? No, v2. I'll use `BaseModel` from `pydantic`.
   - I'll add proper docstrings and comments.
   - I'll make sure the AI part is testable with mocks.

   Structure of `soap_assistant.py`:
   - Imports
   - Pydantic models (PatientInfo, TeleconsultationData, SoapDraft)
   - SQLAlchemy 2.0 model (SoapDraftORM)
   - AI Client Protocol & Mock
   - SoapAssistantService class with async methods
   - CIAP-2/CID-10 mapping logic
   - SOAP generation logic

   Structure of `test_soap_assistant.py`:
   - Fixtures for patient, consultation, service
   - Tests for validation, generation, AI integration, edge cases
   - Use `pytest-asyncio`

   Let's write it. 
   I'll be careful with Python 3.12 syntax (e.g., `type` hints, `match` statements if needed, but I'll stick to standard typing).
   I'll use `datetime.now(timezone.utc)` instead of `utcnow()` for Python 3.12 compliance.
   I'll ensure Pydantic v2 uses `model_validator` or `field_validator` correctly.
   I'll make sure the code is complete and ready to run.

   Proceed. 
   Output matches the response. 
   Self-Correction/Verification during drafting:
   - `datetime.utcnow()` is deprecated in Python 3.12. I'll use `datetime.now(timezone.utc)`.
   - Pydantic v2 uses `model_validator` for cross-field validation. I'll use that.
   - SQLAlchemy 2.0 uses `Mapped` and `mapped_column`. I'll add a simple ORM model.
   - I'll ensure the AI client is properly mocked in tests.
   - I'll add `pytest-asyncio` mode configuration note.
   - All good.

   Final check of the prompt: "backend/app/services/soap_assistant.py", "Python 3.12", "Pydantic v2", "SQLAlchemy 2.0", "CIAP-2, CID-10, SOAP, CNS/CPF", "pytest coverage".
   I'll generate the code accordingly. 
   Output generation. 
   [Done] 
   *Self-Correction/Refinement during thought process*:
   - I need to make sure the SQLAlchemy model is properly defined for Python 3.12 + SQLAlchemy 2.0.
   - I'll use `sqlalchemy.orm.decl_api.MappedAsDataclass