Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/services/soap_assistant.py` for a "Smart Medical Record Summarizer and SOAP Draft with AI (C14)".
   - **Target User:** Family doctor in "MedIA".
   - **Functionality:** Generate a structured SOAP draft (Subjective, Objective, Assessment, Plan) from patient complaints during teleconsultation and past history, saving typing time.
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards: CIAP-2, ICD-10 (CID-10), SOAP method, identification by CNS/CPF.
     - Full compliance and automated test coverage with pytest.
   - **Output Requirement:** Provide complete, executable code. Specify file path for each block.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/services/soap_assistant.py`
   - **Core Logic:** Generate SOAP draft from input data (complaints, history, vitals, etc.)
   - **Standards:** CIAP-2 (Classificação Internacional de Atenção Primária), CID-10 (ICD-10), SOAP format, CNS/CPF identification.
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0, pytest.
   - **Testing:** Need to provide pytest tests covering the functionality.
   - **AI Integration:** The prompt mentions "com IA" (with AI). I should simulate or structure it for AI integration (e.g., using a placeholder or mock LLM call, or structure it to accept an AI provider interface). Since I can't actually call an external AI API in a self-contained code block, I'll design it with a clear interface for AI integration, possibly using a mock or a simple rule-based/template engine as a fallback, but clearly mark where AI would be called. I'll implement a structured prompt generation and a mock AI response parser, or just a deterministic generator that follows SOAP standards strictly, as requested for testing/compliance. I'll make it configurable for AI.

3.  **Design the Service (`soap_assistant.py`):**
   - **Models/DTOs (Pydantic v2):**
     - `PatientInfo`: cpf, cns, name
     - `TeleconsultationData`: complaints, history, vitals (temp, bp, hr, rr, spo2), exam_findings
     - `SOAPDraft`: subjective, objective, assessment, plan, icd_codes, ciap_codes, generated_at
   - **Service Class/Function:** `generate_soap_draft(patient_info, teleconsultation_data) -> SOAPDraft`
   - **Logic:**
     - Map complaints to CIAP-2 codes (simplified mapping for demo/testing)
     - Map assessment to CID-10 codes
     - Structure SOAP sections based on input
     - Ensure SUS/APS compliance (e.g., standard SOAP structure, CNS/CPF in header)
     - Include AI integration point (e.g., `call_ai_service(prompt) -> str`)
   - **Type Hints:** Strict Python 3.12 style.
   - **Error Handling:** Validation via Pydantic, custom exceptions.

   Let's draft the code structure:
   ```python
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
   ```

   I need to flesh out the AI integration and mapping logic. Since it's a testable service, I'll implement a deterministic fallback that strictly follows SUS/APS standards, and clearly mark the AI call. I'll also add CIAP-2 and CID-10 mapping logic (simplified for the example, but structured for testing).

   Let's refine the service to be more robust and testable:
   - Use a prompt template for AI.
   - Simulate AI response parsing (or use a mock in tests).
   - Ensure strict typing and Pydantic v2 compliance.
   - Add logging.

   I'll write the complete `soap_assistant.py` with:
   - Pydantic models
   - Service class with `generate_soap_draft`
   - CIAP-2/CID-10 mapping helper
   - AI prompt builder
   - Fallback generator (deterministic)
   - Type hints throughout

4.  **Design Tests (`test_soap_assistant.py`):**
   - Use pytest.
   - Test Pydantic validation (invalid CPF/CNS, empty SOAP sections).
   - Test deterministic generation (fallback).
   - Test AI integration (mock AI client).
   - Test CIAP-2/CID-10 mapping.
   - Test edge cases (missing vitals, long text, etc.).
   - Use `pytest` fixtures, `unittest.mock`, `pydantic` validation errors.

   Structure:
   ```python
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
   ```

   I'll write comprehensive tests covering:
   - Validation errors
   - Draft generation (deterministic)
   - AI mock integration
   - CIAP-2/CID-10 extraction
   - Type checking (implicitly via Pydantic)

5.  **Refine & Self-Correction/Verification:**
   - *Python 3.12*: Use `from __future__ import annotations` or modern syntax. I'll use modern type hints.
   - *Pydantic v2*: Use `Field`, `field_validator`, `model_validator` if needed. Ensure strict validation.
   - *SQLAlchemy 2.0*: The prompt mentions it, but the service itself doesn't directly need DB models unless I add them. I'll add a simple SQLAlchemy 2.0 model for `SOAPDraft` persistence to fully comply with the architecture guideline, or at least mention it. Actually, the task says "backend/app/services/soap_assistant.py", so I'll keep it as a service layer. I'll add a SQLAlchemy 2.0 model in a separate file or include it if needed, but the prompt specifically asks for `soap_assistant.py`. I'll stick to Pydantic for DTOs and SQLAlchemy for persistence if needed, but I'll focus on the service. I'll add a comment about SQLAlchemy 2.0 compliance and maybe a simple repository interface or just note that it's designed to work with SQLAlchemy 2.0 models. Actually, I'll create a SQLAlchemy 2.0 model for `SOAPRecord` in the same file or a separate one? The prompt says "Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo". I'll create two files: `soap_assistant.py` (service) and `test_soap_assistant.py` (tests). I'll also add a SQLAlchemy 2.0 model in `soap_assistant.py` or a separate `models.py`? I'll keep it focused on the service and tests, but ensure SQLAlchemy 2.0 compatibility is mentioned or used if needed. Actually, I'll add a simple SQLAlchemy 2.0 model for persistence to fully satisfy "SQLAlchemy 2.0" in guidelines, but it's optional. I'll stick to Pydantic for the service logic and note SQLAlchemy 2.0 integration points.
   - *SUS/APS Standards*: CIAP-2, CID-10, SOAP, CNS/CPF. I'll implement a mapping dictionary for CIAP-2 and CID-10 based on keywords, and ensure the output format matches SUS standards.
   - *AI Integration*: I'll design a clear `call_ai` method that can be mocked. I'll use a deterministic fallback for testing.
   - *Testing*: pytest, strict coverage, mock AI, validation tests.

   Let's draft the code carefully.

   **Structure of `soap_assistant.py`:**
   - Imports
   - Pydantic models (PatientInfo, VitalSigns, TeleconsultationData, SOAPDraft)
   - CIAP-2 & CID-10 mapping constants
   - SOAPAssistantService class
     - `__init__`
     - `_build_prompt`
     - `_parse_ai_response` (or fallback)
     - `generate_draft`
   - Type hints throughout.

   **Structure of `test_soap_assistant.py`:**
   - Imports
   - Fixtures
   - Test validation
   - Test deterministic generation
   - Test AI mock
   - Test CIAP-2/CID-10 mapping
   - Test edge cases

   I'll write it out now, ensuring strict compliance.
   *Self-Correction/Refinement during thought:*
   - Pydantic v2 uses `model_validator` and `field_validator`. I'll use `field_validator`.
   - SQLAlchemy 2.0: I'll add a simple ORM model in the same file or a separate `models.py`? The prompt says "backend/app/services/soap_assistant.py". I'll keep the service focused, but I'll add a SQLAlchemy 2.0 model for `SOAPRecord` in a separate block if needed, or just note it. Actually, I'll create `backend/app/models/soap_record.py` for SQLAlchemy 2.0 compliance, but the prompt specifically asks for `soap_assistant.py`. I'll stick to the service and tests, but ensure the service is designed to work with SQLAlchemy 2.0 repositories. I'll add a comment about it.
   - I'll make sure the code is fully executable and testable.
   - I'll use `typing` module properly.
   - I'll ensure CIAP-2 and CID-10 mapping is realistic but simplified for testing.
   - I'll add proper docstrings and type hints.

   Let's write the code. 
   I'll structure it as two files:
   1. `backend/app/services/soap_assistant.py`
   2. `backend/app/services/test_soap_assistant.py`

   I'll carefully implement the logic.
   *Checklist:*
   - Python 3.12? Yes.
   - Pydantic v2? Yes.
   - SQLAlchemy 2.0? I'll add a model file or integrate it. I'll add `backend/app/models/soap_record.py` for completeness, but focus on the requested file. Actually, I'll just include the service and tests as requested.
   - SUS/APS standards? CIAP-2, CID-10, SOAP, CNS/CPF. Yes.
   - pytest coverage? Yes, comprehensive tests.
   - Complete & executable? Yes.

   Proceed. 
   I'll generate the code now. 
   *Self-Correction/Note during drafting:* 
   I should make sure the AI integration is clearly separated so tests can mock it. I'll use a protocol or interface for the AI client. I'll also ensure the SOAP draft generation follows a strict template when AI is unavailable, which is crucial for testing. I'll add a `generate_soap_draft` function as the main entry point, and a `SOAPAssistantService` class. I'll use Pydantic v2's `TypeAdapter` or just standard models. I'll stick to standard Pydantic v2 models.

   Let's write it out carefully. 
   Structure:
   - `backend/app/services/soap_assistant.py`
   - `backend/app/services/test_soap_assistant.py`
   - I'll add comments for SQLAlchemy 2.0 integration points.
   - I'll ensure strict typing.
   - I'll make sure tests are comprehensive.
   - I'll follow SUS/APS standards in the output format.
   - I'll use `datetime` correctly.
   - I'll handle CIAP-2/CID-10 mapping.
   - I'll mock AI properly.
   - I'll ensure pytest compatibility.

   All set. Generating. 
   *Output Generation matches the response.* 
   I'll produce the code blocks now. 
   [Done.] 
   *Self-Correction/Verification during generation prep:*
   - Pydantic v2 `field_validator` needs `@field_validator('field', mode='before')` or similar. I'll use `mode='after'` or just validate in `model_validator`.
   - I'll use `model_validator(mode='after')` for cross-field validation if needed, but `field_validator` is fine.
   - I'll ensure the code runs with `pytest`.
   - I'll add `__init__.py` if needed, but not required for the prompt.
   - I'll make sure the AI mock works correctly.
   - I'll add type hints strictly.
   - I'll follow the exact file path requested.
   - I'll include SQLAlchemy 2.0 model in a separate block for completeness, as requested by architecture guidelines. Actually, the prompt says "backend/app/services/soap_assistant.py", so I'll stick to that. I'll mention SQLAlchemy 2.0 compatibility in comments.

   Ready. Output matches the final response. 
   Proceeds. 
   [Output Generation] -> *See response.* 
   *(Note: I'll make sure the code is production-ready, strictly typed, and fully testable.)*
   *Structure of response:*
   - `backend/app/services/soap_assistant.py`
   - `backend/app/services/test_soap_assistant.py`
   - Instructions for running tests.
   - All compliant with guidelines.✅
   *Self-Correction/Refinement during thought:* 
   I should explicitly include a SQLAlchemy 2.0 model to satisfy the architecture guideline, even if it's in a separate file. I'll add `backend/app/models/soap_record.py` briefly, but focus on the requested service. Actually, I'll just keep it to the requested files to avoid overcomplication, but I'll ensure the service is designed to work with SQLAlchemy 2.0 repositories. I'll add a comment about it. The prompt says "backend/app/services/soap_assistant.py", so I'll strictly follow that.

   I'll write the code now. 
   [Done.] 
   *Output Generation* (matches the final response)
   - File 1: `backend/app/services/soap_assistant.py`
   - File 2: `backend/app/services/test_soap_assistant.py`
   - Strict typing, Pydantic v2, SQLAlchemy 2.0 compatibility notes, SUS/APS standards, pytest coverage.
   - All requirements met.✅
   Proceeds. 
   *(Self-Correction/Verification during output gen prep)*: 
   I'll make sure the Pydantic v2 syntax is correct: `from pydantic import BaseModel, Field, field_validator, ConfigDict`. I'll use `model_config = ConfigDict(strict=True)` if needed, but Pydantic v2 defaults to strict mode in many contexts. I'll explicitly set `strict=True` in model config.
   I'll ensure the AI mock works with `unittest.mock.patch`.
   I'll add comprehensive tests.
   All good.
   Output matches response. 
   [Done.]
Aqui está a implementação completa, seguindo rigorosamente as diretrizes de arquitetura, tipagem estrita, padrões SUS/APS e cobertura de testes com pytest.

### 1. Serviço Principal
```python
# Arquivo: backend/app/services/soap_assistant.py
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Protocol
from pydantic import BaseModel, Field, field_validator,