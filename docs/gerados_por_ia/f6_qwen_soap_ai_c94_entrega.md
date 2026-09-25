Here's a thinking process:

1.  **Understand User Goal:** The user wants me to act as a software engineer/tester and create a specific file: `backend/app/services/soap_assistant.py`. This file should generate a structured SOAP (Subjective, Objective, Assessment, Plan) draft for a family medicine doctor in a system called "MedIA". It should use AI (implied, though I'll need to design it to be adaptable, likely using a mock or configurable LLM interface, but I'll stick to the requirements: Pydantic v2, SQLAlchemy 2.0, SUS/APS standards like CIAP-2, CID-10, CNS/CPF, and full pytest coverage).

2.  **Key Requirements:**
   - File: `backend/app/services/soap_assistant.py`
   - Language: Python 3.12
   - Strict typing with Pydantic v2
   - SQLAlchemy 2.0 compatibility (though this is a service, it might interact with models, but the prompt focuses on the service itself)
   - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification
   - Full automated test coverage with pytest
   - Provide complete, executable code
   - Specify file path in comments

3.  **Deconstruct the Task:**
   - **SOAP Structure:** Subjective (Subjetivo), Objective (Objetivo), Assessment (Avaliação), Plan (Plano)
   - **Input:** Patient complaints (queixas), historical data (histórico pregresso), patient ID (CNS/CPF)
   - **Output:** Structured SOAP draft
   - **AI Integration:** The prompt says "com IA", so I should design it to call an AI service/function. Since I can't actually call an external API in a standalone script, I'll create a configurable interface with a mock/default implementation that demonstrates the structure, and make it easy to swap in a real LLM later. I'll use Pydantic for input/output validation.
   - **Standards:** CIAP-2 (Classificação Internacional de Atenção Primária), CID-10 (ICD-10), CNS (Cartão Nacional de Saúde), CPF. I'll include validation/encoding for these.
   - **Testing:** Need a comprehensive pytest suite covering validation, generation, error handling, and mock AI calls.

4.  **Design the Service (`soap_assistant.py`):**
   - **Models/DTOs (Pydantic v2):**
     - `SOAPDraft`: Output model with fields for S, O, A, P, plus metadata (patient_cns, patient_cpf, generated_at, ciap_codes, cid_codes).
     - `SOAPInput`: Input model with patient info, complaints, history, vitals (optional), etc.
   - **Service Class/Function:** `SOAPAssistantService` or just a function `generate_soap_draft(input_data: SOAPInput) -> SOAPDraft`. I'll use a class for better structure and potential DI later.
   - **AI Integration:** Define an abstract interface or a simple function that takes text and returns structured text. I'll implement a default "rule-based/template" generator that simulates AI output for testing, but structure it so a real LLM can be plugged in. Actually, the prompt says "com IA", so I'll create a `AIProvider` protocol/interface and a `MockAIProvider` for testing, plus a `generate_soap_draft` function that uses it.
   - **SUS/APS Compliance:**
     - Validate CNS format (15 digits)
     - Validate CPF format (11 digits)
     - Include CIAP-2 and CID-10 code mapping/validation
     - Follow SOAP structure strictly
   - **Code Structure:**
     ```python
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
     ```

5.  **Design Tests (`test_soap_assistant.py`):**
   - Need comprehensive pytest coverage.
   - Test Pydantic validation (CNS, CPF)
   - Test service generation with mock AI
   - Test error handling
   - Test SUS/APS standards compliance (CIAP-2, CID-10, SOAP structure)
   - Use `pytest`, `pytest-mock`, `pydantic`, `datetime`
   - Structure:
     ```python
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
     ```

6.  **Refine & Check Requirements:**
   - *Python 3.12, strict typing:* Used `from __future__ import annotations`, type hints, Pydantic v2.
   - *Pydantic v2:* Used `BaseModel`, `Field`, `field_validator`, `model_dump`, `ConfigDict`.
   - *SQLAlchemy 2.0:* The prompt mentions it in guidelines, but this is a service file. I'll add a comment about SQLAlchemy 2.0 compatibility for future model integration, or create a simple example of how it would map to a DB model if needed. Actually, I can add a SQLAlchemy 2.0 mapped class for `SOAPDraft` to fully comply with the guideline, or just note that the service is DB-agnostic but ready for SQLAlchemy 2.0 integration. I'll add a `SOAPDraftORM` model using SQLAlchemy 2.0 style to be thorough.
   - *SUS/APS standards:* CNS/CPF validation, CIAP-2/CID-10 fields, SOAP structure. I'll add comments explaining compliance.
   - *Full pytest coverage:* The test file covers validation, service logic, mock AI, default AI, serialization. I'll make it more robust with `pytest.mark.parametrize` and edge cases.
   - *Complete & executable:* I'll ensure imports are correct, structure is clean, and tests can run directly.
   - *File path comments:* Added as requested.

   Let's enhance the service to include a SQLAlchemy 2.0 model for persistence, as the guidelines explicitly mention it. I'll add it in the same file or note it. Actually, the prompt says "backend/app/services/soap_assistant.py", so I'll keep it focused but add the ORM model at the bottom or in a separate section within the file.

   I'll structure the file properly:
   - Imports
   - Pydantic models (Input/Output)
   - AI Provider protocol & implementation
   - Service class
   - SQLAlchemy 2.0 model (optional but good for compliance)
   - Tests in a separate block as requested? The prompt says "Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo". I'll provide both files in the response.

   Let's draft the code carefully.

   **Self-Correction/Refinement during thought:**
   - Pydantic v2 uses `field_validator` correctly. I should use `@field_validator("patient_cns")` properly.
   - SQLAlchemy 2.0 uses `Mapped`, `mapped_column`, `DeclarativeBase`. I'll add a simple model to show compliance.
   - The prompt says "código completo e executável". I'll make sure the test file is self-contained and uses `pytest` correctly.
   - I'll add type hints strictly.
   - I'll ensure SUS/APS standards are explicitly handled (CNS/CPF validation, CIAP-2/CID-10 fields, SOAP structure).
   - I'll make the AI provider configurable and add a realistic mock for testing.
   - I'll add comprehensive docstrings and comments.

   Structure of response:
   1. `backend/app/services/soap_assistant.py`
   2. `backend/app/services/test_soap_assistant.py`
   Both with proper path comments.

   Let's write it out carefully. 
   I'll verify Pydantic v2 syntax: `field_validator` is correct. `model_dump(by_alias=True)` is correct. `ConfigDict` is correct.
   SQLAlchemy 2.0: `from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column`
   I'll add the ORM model to the same file as requested, or note it. The prompt says "backend/app/services/soap_assistant.py", so I'll put everything there.

   Test coverage: I'll use `pytest.mark.parametrize`, test edge cases, mock AI, validate structure, test serialization, test validation errors.

   All good. Proceed. 
   Output matches the refined code.✅
   I will generate the response now. 
   Structure:
   - File 1: `backend/app/services/soap_assistant.py`
   - File 2: `backend/app/services/test_soap_assistant.py`
   - Both with path comments, strict typing, Pydantic v2, SQLAlchemy 2.0 model, SUS/APS compliance, full pytest coverage.
   - Ready. 
   *Self-Correction/Verification during drafting:*
   - Pydantic v2 `field_validator` needs `@field_validator("field_name")` decorator. Correct.
   - SQLAlchemy 2.0 model: I'll add it but keep it optional/configurable to avoid DB dependency in a service file. I'll use `DeclarativeBase` and `Mapped` correctly.
   - The prompt says "código completo e executável". I'll ensure imports are standard library + pydantic + sqlalchemy + pytest.
   - I'll add a `__main__` block or just ensure it's importable.
   - Tests will be comprehensive.
   - All constraints met.
   Proceed. 
   Output generation. 
   [Done] 
   *Output Generation* (matches the final response)
   - Provides `soap_assistant.py` with Pydantic v2, SQLAlchemy 2.0 model, AI protocol, service, SUS/APS compliance.
   - Provides `test_soap_assistant.py` with full pytest coverage.
   - Includes path comments.
   - Strict typing, Python 3.12 compatible.
   - Ready. 
   *Output Generation* (proceeds)
Aqui estão os arquivos completos e executáveis, seguindo rigorosamente as diretrizes de arquitetura, tipagem estrita, padrões SUS/APS e cobertura de testes.

```python:backend/app/services/soap_assistant.py
# Arquivo: backend/app/services/soap_assistant.py
"""
Serviço de Assistente SOAP para MedIA (APS/SUS)
Gera rascunho estruturado de evolução médica (Subjetivo, Objetivo, Avaliação, Plano)
com validação de padrões SUS (CNS/CPF, CIAP-2, CID-10) e integração com provedor