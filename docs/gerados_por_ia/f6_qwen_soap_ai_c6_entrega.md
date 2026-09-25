Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/services/soap_assistant.py` for a "Smart Medical Record Summarizer and SOAP Draft with AI (C6)".
   - **Context:** MedIA platform for family medicine/primary care, private & insurance (TISS ANS 4.01 / DMED). Uses primary care clinical method.
   - **Constraints:**
     - Python 3.12, strict typing, Pydantic v2, SQLAlchemy 2.0.
     - Production code in `backend/app/`, tests in `backend/tests/`.
     - Do NOT generate code for SUS/SISAB or IoT peripherals.
     - Preserve 100% green test suite (meaning I need to provide tests that pass with the implementation).
     - Provide complete, executable code. Specify file paths.
     - Generate a structured SOAP draft (Subjective, Objective, Assessment, Plan) from patient complaints and history.

2.  **Deconstruct Requirements:**
   - **Input:** Patient complaints, historical data (could be structured or unstructured text).
   - **Output:** Structured SOAP draft.
   - **AI Integration:** The prompt says "com IA" (with AI). I need to simulate or interface with an AI service. Since I can't actually call an external API in a self-contained code snippet, I'll design a service that uses a mock AI client or a configurable LLM interface, but I'll implement a deterministic fallback or a clear interface for AI integration. I'll use a mock/simulated AI response for testing purposes, but structure it so it's easily replaceable with a real LLM call.
   - **Pydantic v2:** Define request/response models.
   - **SQLAlchemy 2.0:** Define models for storing SOAP drafts if needed, or just focus on the service logic. The task says "gera rascunho", so the service should generate it. I'll add a repository/service pattern if needed, but keep it focused on the service.
   - **Testing:** Provide comprehensive tests in `backend/tests/` that verify the service works correctly, including edge cases, and ensure they pass.

3.  **Design the Solution:**
   - **Models (Pydantic v2):**
     - `SOAPDraftRequest`: Contains patient_id, complaints, history, visit_date, etc.
     - `SOAPSection`: Pydantic model for each section (subjective, objective, assessment, plan).
     - `SOAPDraftResponse`: Contains the full draft with sections.
   - **Service (`soap_assistant.py`):**
     - `SoapAssistantService` class.
     - `generate_draft(request: SOAPDraftRequest) -> SOAPDraftResponse` method.
     - Internal logic to structure the input into SOAP format. Since it's "com IA", I'll simulate an AI call but provide a deterministic fallback for testing. I'll use a mock LLM client interface.
     - I'll also add a repository method to save the draft (SQLAlchemy 2.0 style) to show integration, but keep it optional/configurable.
   - **SQLAlchemy Models:**
     - `SoapDraft` table: id, patient_id, visit_date, subjective, objective, assessment, plan, created_at, updated_at.
   - **Tests:**
     - Unit tests for the service.
     - Mock the AI client.
     - Test Pydantic validation.
     - Test SQLAlchemy model creation.
     - Ensure 100% coverage/green suite.

4.  **Draft Code - Step by Step:**

   *File 1: `backend/app/models/soap_draft.py` (SQLAlchemy model)*
   Need to define the model for persistence.
   ```python
   from datetime import datetime
   from sqlalchemy import String, Text, DateTime, ForeignKey, Numeric
   from sqlalchemy.orm import Mapped, mapped_column, relationship
   from backend.app.database import Base

   class SoapDraft(Base):
       __tablename__ = "soap_drafts"

       id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
       patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
       visit_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
       subjective: Mapped[str] = mapped_column(Text, nullable=True)
       objective: Mapped[str] = mapped_column(Text, nullable=True)
       assessment: Mapped[str] = mapped_column(Text, nullable=True)
       plan: Mapped[str] = mapped_column(Text, nullable=True)
       created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

       patient = relationship("Patient", back_populates="soap_drafts")
   ```
   Wait, I need to be careful with imports. I'll assume a standard FastAPI/SQLAlchemy setup. I'll keep it self-contained but note dependencies.

   *File 2: `backend/app/schemas/soap_schemas.py` (Pydantic v2)*
   ```python
   from pydantic import BaseModel, Field
   from datetime import datetime
   from typing import Optional

   class SOAPDraftRequest(BaseModel):
       patient_id: int
       visit_date: datetime
       complaints: str = Field(..., min_length=1, description="Queixas relatadas pelo paciente")
       history: str = Field(default="", description="Histórico pregresso relevante")
       vitals: Optional[str] = Field(default=None, description="Sinais vitais ou dados objetivos coletados")

   class SOAPSection(BaseModel):
       content: str = Field(..., min_length=0)
       confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)

   class SOAPDraftResponse(BaseModel):
       subjective: SOAPSection
       objective: SOAPSection
       assessment: SOAPSection
       plan: SOAPSection
       generated_at: datetime = Field(default_factory=datetime.utcnow)
   ```

   *File 3: `backend/app/services/soap_assistant.py` (Core Service)*
   Need to implement the AI integration logic. I'll create a mock AI client for testing, but structure it so it can be swapped.
   ```python
   import logging
   from typing import Optional
   from datetime import datetime
   from pydantic import ValidationError
   from backend.app.schemas.soap_schemas import SOAPDraftRequest, SOAPDraftResponse, SOAPSection
   from backend.app.database import SessionLocal
   from backend.app.models.soap_draft import SoapDraft

   logger = logging.getLogger(__name__)

   class MockAIClient:
       """Mock AI client for deterministic testing. Replace with actual LLM integration in production."""
       def generate_soap(self, complaints: str, history: str, vitals: Optional[str]) -> dict:
           # Simulate AI response structure
           return {
               "subjective": f"Queixa principal: {complaints}. Histórico: {history if history else 'Sem histórico relevante informado.'}",
               "objective": f"Sinais vitais/exame físico: {vitals if vitals else 'Não informado.'}",
               "assessment": f"Hipótese diagnóstica baseada em {complaints} e histórico. Necessário aprofundamento clínico.",
               "plan": f"Conduta sugerida: acompanhamento, exames complementares se indicado, orientações ao paciente."
           }

   class SoapAssistantService:
       def __init__(self, ai_client: Optional[MockAIClient] = None):
           self.ai_client = ai_client or MockAIClient()

       def generate_draft(self, request: SOAPDraftRequest) -> SOAPDraftResponse:
           # Validate input
           try:
               validated_request = SOAPDraftRequest(**request.model_dump())
           except ValidationError as e:
               raise ValueError(f"Invalid request data: {e}") from e

           # Call AI
           ai_response = self.ai_client.generate_soap(
               complaints=validated_request.complaints,
               history=validated_request.history,
               vitals=validated_request.vitals
           )

           # Map to Pydantic response
           response = SOAPDraftResponse(
               subjective=SOAPSection(content=ai_response["subjective"]),
               objective=SOAPSection(content=ai_response["objective"]),
               assessment=SOAPSection(content=ai_response["assessment"]),
               plan=SOAPSection(content=ai_response["plan"]),
               generated_at=datetime.utcnow()
           )
           return response

       def save_draft(self, draft: SOAPDraftResponse, patient_id: int, visit_date: datetime) -> SoapDraft:
           db = SessionLocal()
           try:
               soap_record = SoapDraft(
                   patient_id=patient_id,
                   visit_date=visit_date,
                   subjective=draft.subjective.content,
                   objective=draft.objective.content,
                   assessment=draft.assessment.content,
                   plan=draft.plan.content
               )
               db.add(soap_record)
               db.commit()
               db.refresh(soap_record)
               return soap_record
           except Exception as e:
               db.rollback()
               logger.error(f"Failed to save SOAP draft: {e}")
               raise
           finally:
               db.close()
   ```

   *File 4: `backend/tests/test_soap_assistant.py` (Tests)*
   Need to ensure 100% green suite. I'll use `pytest`, `unittest.mock`, and test Pydantic validation, service logic, and DB interaction (mocked).
   ```python
   import pytest
   from datetime import datetime
   from pydantic import ValidationError
   from backend.app.schemas.soap_schemas import SOAPDraftRequest, SOAPDraftResponse, SOAPSection
   from backend.app.services.soap_assistant import SoapAssistantService, MockAIClient

   class TestSoapDraftRequest:
       def test_valid_request(self):
           req = SOAPDraftRequest(
               patient_id=1,
               visit_date=datetime.utcnow(),
               complaints="Dor abdominal há 3 dias",
               history="Hipertensão controlada",
               vitals="PA 130/80, FC 72"
           )
           assert req.patient_id == 1
           assert req.complaints == "Dor abdominal há 3 dias"

       def test_invalid_request_missing_complaints(self):
           with pytest.raises(ValidationError):
               SOAPDraftRequest(
                   patient_id=1,
                   visit_date=datetime.utcnow(),
                   complaints="",
                   history="Histórico"
               )

   class TestSoapAssistantService:
       def setup_method(self):
           self.service = SoapAssistantService()

       def test_generate_draft_success(self):
           request = SOAPDraftRequest(
               patient_id=1,
               visit_date=datetime.utcnow(),
               complaints="Febre e tosse",
               history="Alergia a dipirona",
               vitals="T 38.5°C"
           )
           response = self.service.generate_draft(request)
           assert isinstance(response, SOAPDraftResponse)
           assert "Febre e tosse" in response.subjective.content
           assert "Alergia a dipirona" in response.assessment.content
           assert response.generated_at is not None

       def test_generate_draft_with_mock_ai(self):
           class CustomMockAIClient:
               def generate_soap(self, complaints, history, vitals):
                   return {
                       "subjective": f"Custom subj: {complaints}",
                       "objective": f"Custom obj: {vitals}",
                       "assessment": f"Custom assess: {history}",
                       "plan": "Custom plan: Follow-up"
                   }
           service = SoapAssistantService(ai_client=CustomMockAIClient())
           request = SOAPDraftRequest(
               patient_id=2,
               visit_date=datetime.utcnow(),
               complaints="Teste",
               history="Histórico teste",
               vitals="Vitals teste"
           )
           response = service.generate_draft(request)
           assert "Custom subj: Teste" in response.subjective.content
           assert "Custom obj: Vitals teste" in response.objective.content
           assert "Custom assess: Histórico teste" in response.assessment.content
           assert "Custom plan: Follow-up" in response.plan.content

       def test_save_draft_success(self, mocker):
           mock_session = mocker.MagicMock()
           mock_session_instance = mocker.MagicMock()
           mock_session.return_value = mock_session_instance
           mock_session_instance.__enter__ = mocker.MagicMock(return_value=mock_session_instance)
           mock_session_instance.__exit__ = mocker.MagicMock(return_value=False)

           # Patch SessionLocal
           from backend.app.services import soap_assistant
           original_session = soap_assistant.SessionLocal
           soap_assistant.SessionLocal = mock_session

           draft = SOAPDraftResponse(
               subjective=SOAPSection(content="Subj"),
               objective=SOAPSection(content="Obj"),
               assessment=SOAPSection(content="Assess"),
               plan=SOAPSection(content="Plan")
           )
           result = self.service.save_draft(draft, patient_id=1, visit_date=datetime.utcnow())
           assert result is not None
           mock_session_instance.add.assert_called_once()
           mock_session_instance.commit.assert_called_once()

           soap_assistant.SessionLocal = original_session

   if __name__ == "__main__":
       pytest.main([__file__, "-v"])
   ```

5.  **Refine & Check Constraints:**
   - *Python 3.12, strict typing, Pydantic v2, SQLAlchemy 2.0*: Used `Mapped`, `mapped_column`, Pydantic v2 (`model_dump`, `Field`), type hints throughout.
   - *MedIA context*: Added comments/context about TISS/DMED compliance in docstrings. SOAP structure matches primary care standards.
   - *No SUS/SISAB/IoT*: Explicitly avoided.
   - *Production code in `backend/app/`, tests in `backend/tests/`*: Structured accordingly.
   - *Preserve 100% green test suite*: Tests are comprehensive, cover validation, service logic, mock AI, and DB interaction. I'll make sure the test code is self-contained and runnable. I'll adjust the DB mocking to be more standard for pytest.
   - *Complete & executable*: I'll provide all files with clear paths. I'll add necessary imports and setup comments. I'll ensure the test uses `pytest-mock` properly.

   Let's adjust the test for DB to be more robust and standard:
   ```python
   # backend/tests/test_soap_assistant.py
   import pytest
   from datetime import datetime
   from pydantic import ValidationError
   from backend.app.schemas.soap_schemas import SOAPDraftRequest, SOAPDraftResponse, SOAPSection
   from backend.app.services.soap_assistant import SoapAssistantService, MockAIClient
   from unittest.mock import MagicMock, patch

   class TestSoapDraftRequest:
       def test_valid_request(self):
           req = SOAPDraftRequest(
               patient_id=1,
               visit_date=datetime.utcnow(),
               complaints="Dor abdominal há 3 dias",
               history="Hipertensão controlada",
               vitals="PA 130/80, FC 72"
           )
           assert req.patient_id == 1
           assert req.complaints == "Dor abdominal há 3 dias"

       def test_invalid_request_missing_complaints(self):
           with pytest.raises(ValidationError):
               SOAPDraftRequest(
                   patient_id=1,
                   visit_date=datetime.utcnow(),
                   complaints="",
                   history="Histórico"
               )

   class TestSoapAssistantService:
       def setup_method(self):
           self.service = SoapAssistantService()

       def test_generate_draft_success(self):
           request = SOAPDraftRequest(
               patient_id=1,
               visit_date=datetime.utcnow(),
               complaints="Febre e tosse",
               history="Alergia a dipirona",
               vitals="T 38.5°C"
           )
           response = self.service.generate_draft(request)
           assert isinstance(response, SOAPDraftResponse)
           assert "Febre e tosse" in response.subjective.content
           assert "Alergia a dipirona" in response.assessment.content
           assert response.generated_at is not None

       def test_generate_draft_with_custom_ai_client(self):
           class CustomMockAIClient:
               def generate_soap(self, complaints, history, vitals):
                   return {
                       "subjective": f"Custom subj: {complaints}",
                       "objective": f"Custom obj: {vitals}",
                       "assessment": f"Custom assess: {history}",
                       "plan": "Custom plan: Follow-up"
                   }
           service = SoapAssistantService(ai_client=CustomMockAIClient())
           request = SOAPDraftRequest(
               patient_id=2,
               visit_date=datetime.utcnow(),
               complaints="Teste",
               history="Histórico teste",
               vitals="Vitals teste"
           )
           response = service.generate_draft(request)
           assert "Custom subj: Teste" in response.subjective.content
           assert "Custom obj: Vitals teste" in response.objective.content
           assert "Custom assess: Histórico teste" in response.assessment.content
           assert "Custom plan: Follow-up" in response.plan.content

       def test_save_draft_success(self):
           mock_session = MagicMock()
           mock_db_instance = MagicMock()
           mock_session.return_value = mock_db_instance
           mock_db_instance.__enter__ = MagicMock(return_value=mock_db_instance)
           mock_db_instance.__exit__ = MagicMock(return_value=False)

           with patch("backend.app.services.soap_assistant.SessionLocal", mock_session):
               draft = SOAPDraftResponse(
                   subjective=SOAPSection(content="Subj"),
                   objective=SOAPSection(content="Obj"),
                   assessment=SOAPSection(content="Assess"),
                   plan=SOAPSection(content="Plan")
               )
               result = self.service.save_draft(draft, patient_id=1, visit_date=datetime.utcnow())
               assert result is not None
               mock_db_instance.add.assert_called_once()
               mock_db_instance.commit.assert_called_once()
   ```

   Check SQLAlchemy 2.0 compatibility: `SessionLocal` is typically a function or class. I'll mock it properly. The test uses `patch` correctly.
   Check Pydantic v2: `model_dump()` is correct. `Field` with `min_length`, `ge`, `le` is correct.