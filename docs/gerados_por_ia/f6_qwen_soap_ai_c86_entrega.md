Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/services/soap_assistant.py` for a medical AI system (MedIA).
   - **Functionality:** Generate a structured SOAP (Subjective, Objective, Assessment, Plan) draft from patient complaints during teleconsultation and past medical history.
   - **Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards (CIAP-2, CID-10, SOAP method, identification by CNS/CPF).
     - Full compliance and automated test coverage with pytest.
     - Provide complete, executable code.
     - Specify file paths in code blocks.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/services/soap_assistant.py`
   - **Core Functionality:** Generate SOAP draft from input data (complaints, history, etc.)
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0
   - **Standards:** SUS/APS (CIAP-2, CID-10, CNS/CPF)
   - **Testing:** pytest coverage required (I'll provide the service code and a corresponding test file, as requested "cobertura de testes automatizados com pytest")
   - **Output:** Complete, executable code with file paths specified.

3.  **Design the Service (`soap_assistant.py`):**
   - Need Pydantic models for input/output.
   - Need a class/function to generate the SOAP draft.
   - Since it's an AI assistant, I'll simulate the AI generation logic (or provide a structured template-based approach with placeholders for LLM integration, but the prompt says "com IA", so I'll design it to be LLM-ready but provide a deterministic fallback/template for testing, or mock the AI call).
   - I'll create:
     - `SOAPInput` (Pydantic): patient_id, cns, cpf, chief_complaint, past_history, vitals, exam_results, icd10_codes, ciap2_codes, consultation_date
     - `SOAPOutput` (Pydantic): subjective, objective, assessment, plan, generated_at, confidence_score
     - `SOAPAssistantService`: method `generate_draft(input_data: SOAPInput) -> SOAPOutput`
   - I'll implement a rule-based/template engine that mimics AI generation for reliability in testing, but structure it so it can easily integrate with an actual LLM API later. I'll also add a mock AI provider interface.
   - Need to handle SUS/APS standards: CIAP-2 (CIEPC-2), CID-10, CNS/CPF validation.
   - I'll add validation for CNS/CPF using standard algorithms.
   - I'll make it strictly typed.

   Structure:
   ```python
   # Arquivo: backend/app/services/soap_assistant.py
   from __future__ import annotations
   import re
   from datetime import datetime
   from typing import Optional
   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy.orm import Session
   # ... (imports)
   ```

   Wait, the prompt says "gera rascunho de evolução SOAP estruturado... a partir das queixas relatadas... e histórico pregresso". It doesn't strictly require DB integration in this service, but mentions SQLAlchemy 2.0. I'll include a `Session` parameter for potential DB lookups, but keep the core logic self-contained for testing. I'll also add a mock LLM client interface.

   Let's design the Pydantic models carefully:
   - `SOAPInput`:
     - `patient_cns: str`
     - `patient_cpf: str`
     - `chief_complaint: str`
     - `past_history: str`
     - `vitals: dict[str, float]`
     - `exam_results: str`
     - `icd10_codes: list[str]`
     - `ciap2_codes: list[str]`
     - `consultation_date: datetime`
   - `SOAPOutput`:
     - `subjective: str`
     - `objective: str`
     - `assessment: str`
     - `plan: str`
     - `generated_at: datetime`
     - `confidence_score: float`
     - `model_config = ConfigDict(frozen=True)`

   Validation for CNS/CPF:
   - CNS: 15 digits, valid check digit.
   - CPF: 11 digits, valid check digits.
   - I'll implement basic validators.

   SOAP Generation Logic:
   - Since it's "com IA", I'll create a `generate_soap_draft` function that uses a template engine but is structured to call an LLM. For the purpose of this task, I'll implement a deterministic generation that follows SUS/APS guidelines, and add a `use_llm` flag. I'll also mock the AI call for testing.
   - Actually, to keep it executable and testable without external APIs, I'll implement a rule-based generator that formats the input into SOAP structure according to medical standards, and provide a clear interface for AI integration. I'll also add a `MockAIProvider` for testing.

   Let's draft the code mentally:
   ```python
   # Arquivo: backend/app/services/soap_assistant.py
   from __future__ import annotations
   import re
   from datetime import datetime
   from typing import Optional, Protocol
   from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationError
   from sqlalchemy.orm import Session

   # ... validators for CNS/CPF ...
   # ... Pydantic models ...
   # ... AI Provider Protocol ...
   # ... SOAPAssistantService class ...
   ```

   I need to ensure strict typing, Pydantic v2, SQLAlchemy 2.0 compatibility (though I won't use DB models directly here, I'll accept a Session for potential future use or pass it as context).

   Let's refine the CNS/CPF validators:
   - CNS: 15 digits. Check digit algorithm: sum of digits at odd positions * 2 + even positions, modulo 10.
   - CPF: 11 digits. Check digits: first = sum(i*d[i] for i in 1..9) % 11, second = sum(i*d[i] for i in 1..10) % 11.
   I'll implement these as `field_validator`.

   SOAP Generation:
   I'll create a `SOAPDraftGenerator` class that takes the input and produces the draft. It will follow SUS/APS structure:
   - S: Queixa principal, história da doença atual, antecedentes, uso de medicamentos.
   - O: Sinais vitais, exame físico, exames complementares.
   - A: Hipóteses diagnósticas (CID-10/CIAP-2), evolução.
   - P: Conduta, prescrição, encaminhamento, retorno.

   I'll make it generate a structured string or dict. The prompt says "rascunho de evolução SOAP estruturado", so I'll return a Pydantic model with the 4 fields.

   For AI integration, I'll define a `LLMProvider` protocol and a `MockLLMProvider` for testing. The service will use it if configured, otherwise fall back to a deterministic template.

   Let's write the code carefully.

   Structure:
   ```python
   # Arquivo: backend/app/services/soap_assistant.py
   from __future__ import annotations
   import re
   from datetime import datetime
   from typing import Optional, Protocol
   from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationError
   from sqlalchemy.orm import Session

   # CNS/CPF Validators
   def _validate_cns(cns: str) -> str:
       cns = cns.strip().replace('.', '').replace('-', '')
       if len(cns) != 15 or not cns.isdigit():
           raise ValueError("CNS deve ter 15 dígitos numéricos.")
       # Check digit logic
       total = 0
       for i, digit in enumerate(cns):
           d = int(digit)
           if i % 2 == 0:
               total += d * 2
           else:
               total += d
       remainder = total % 10
       check = 10 - remainder if remainder != 0 else 0
       if int(cns[-1]) != check:
           raise ValueError("CNS inválido.")
       return cns

   def _validate_cpf(cpf: str) -> str:
       cpf = cpf.strip().replace('.', '').replace('-', '')
       if len(cpf) != 11 or not cpf.isdigit():
           raise ValueError("CPF deve ter 11 dígitos numéricos.")
       if len(set(cpf)) == 1:
           raise ValueError("CPF inválido.")
       # First check digit
       total = sum(int(cpf[i]) * (10 - i) for i in range(9))
       remainder = (total * 10) % 11
       if remainder == 10: remainder = 0
       if int(cpf[9]) != remainder:
           raise ValueError("CPF inválido.")
       # Second check digit
       total = sum(int(cpf[i]) * (11 - i) for i in range(10))
       remainder = (total * 10) % 11
       if remainder == 10: remainder = 0
       if int(cpf[10]) != remainder:
           raise ValueError("CPF inválido.")
       return cpf

   # Pydantic Models
   class SOAPInput(BaseModel):
       model_config = ConfigDict(frozen=True, str_strip_whitespace=True)
       patient_cns: str = Field(..., description="Número do CNS do paciente")
       patient_cpf: str = Field(..., description="Número do CPF do paciente")
       chief_complaint: str = Field(..., description="Queixa principal relatada na teleconsulta")
       past_history: str = Field(default="", description="Histórico pregresso relevante")
       vitals: dict[str, float] = Field(default_factory=dict, description="Sinais vitais")
       exam_results: str = Field(default="", description="Resultados de exames complementares")
       icd10_codes: list[str] = Field(default_factory=list, description="Códigos CID-10 suspeitos/confirmados")
       ciap2_codes: list[str] = Field(default_factory=list, description="Códigos CIAP-2")
       consultation_date: datetime = Field(default_factory=datetime.now)

       @field_validator("patient_cns")
       @classmethod
       def validate_cns(cls, v: str) -> str:
           return _validate_cns(v)

       @field_validator("patient_cpf")
       @classmethod
       def validate_cpf(cls, v: str) -> str:
           return _validate_cpf(v)

   class SOAPOutput(BaseModel):
       model_config = ConfigDict(frozen=True)
       subjective: str
       objective: str
       assessment: str
       plan: str
       generated_at: datetime = Field(default_factory=datetime.now)
       confidence_score: float = Field(ge=0.0, le=1.0, default=0.85)

   # AI Provider Protocol
   class ILLMProvider(Protocol):
       def generate_soap(self, input_data: SOAPInput) -> SOAPOutput: ...

   class MockLLMProvider:
       def generate_soap(self, input_data: SOAPInput) -> SOAPOutput:
           # Simulates AI generation with deterministic output for testing
           return SOAPOutput(
               subjective=f"[S] Queixa principal: {input_data.chief_complaint}. Histórico pregresso: {input_data.past_history or 'N/A'}.",
               objective=f"[O] Sinais vitais: {input_data.vitals}. Exames: {input_data.exam_results or 'N/A'}.",
               assessment=f"[A] Hipóteses diagnósticas: {', '.join(input_data.icd10_codes) or 'Aguardar exames'}. CIAP-2: {', '.join(input_data.ciap2_codes) or 'N/A'}.",
               plan=f"[P] Conduta: Acompanhar evolução. Retorno em 15 dias. Prescrição: conforme protocolo SUS/APS.",
               confidence_score=0.95
           )

   # Service
   class SOAPAssistantService:
       def __init__(self, llm_provider: Optional[ILLMProvider] = None):
           self.llm_provider = llm_provider or MockLLMProvider()

       def generate_draft(self, input_data: SOAPInput, db: Optional[Session] = None) -> SOAPOutput:
           # In a real app, db could be used to fetch patient history, validate codes, etc.
           # For now, we rely on input_data validation and LLM generation.
           return self.llm_provider.generate_soap(input_data)
   ```

   This looks solid. Now I need to create the pytest test file as requested ("cobertura de testes automatizados com pytest"). The prompt says "Manter conformidade total e cobertura de testes automatizados com pytest." I'll provide `backend/app/services/test_soap_assistant.py`.

   Test file structure:
   - Test CNS/CPF validation
   - Test MockLLMProvider generation
   - Test SOAPAssistantService
   - Test edge cases (empty vitals, invalid codes, etc.)
   - Use pytest fixtures
   - Ensure strict typing and coverage

   Let's draft the test file:
   ```python
   # Arquivo: backend/app/services/test_soap_assistant.py
   import pytest
   from datetime import datetime
   from pydantic import ValidationError
   from .soap_assistant import SOAPInput, SOAPOutput, SOAPAssistantService, MockLLMProvider, _validate_cns, _validate_cpf

   class TestCNSCPFValidation:
       def test_valid_cns(self):
           assert _validate_cns("123456789012345") == "123456789012345"

       def test_invalid_cns_length(self):
           with pytest.raises(ValueError, match="CNS deve ter 15 dígitos"):
               _validate_cns("12345678901234")

       def test_valid_cpf(self):
           assert _validate_cpf("12345678909") == "12345678909"

       def test_invalid_cpf_digits(self):
           with pytest.raises(ValueError, match="CPF inválido"):
               _validate_cpf("11111111111")

   class TestSOAPInput:
       def test_valid_input(self):
           data = SOAPInput(
               patient_cns="123456789012345",
               patient_cpf="12345678909",
               chief_complaint="Dor de cabeça há 3 dias",
               consultation_date=datetime(2024, 1, 1)
           )
           assert data.chief_complaint == "Dor de cabeça há 3 dias"

       def test_invalid_cns_in_model(self):
           with pytest.raises(ValidationError, match="CNS inválido"):
               SOAPInput(
                   patient_cns="000000000000000",
                   patient_cpf="12345678909",
                   chief_complaint="Teste"
               )

   class TestSOAPAssistantService:
       def test_generate_draft_with_mock_llm(self):
           service = SOAPAssistantService()
           input_data = SOAPInput(
               patient_cns="123456789012345",
               patient_cpf="12345678909",
               chief_complaint="Febre e tosse",
               vitals={"temp": 38.5, "pa_sist": 120, "pa_diast": 80},
               icd10_codes=["J06.9", "R50.9"],
               ciap2_codes=["R00", "R01"],
               consultation_date=datetime(2024, 5, 20)
           )
           output = service.generate_draft(input_data)
           assert isinstance(output, SOAPOutput)
           assert output.confidence_score == 0.95
           assert "Febre e tosse" in output.subjective
           assert "J06.9" in output.assessment

       def test_generate_draft_with_custom_llm(self):
           class CustomLLM:
               def generate_soap(self, input_data: SOAPInput) -> SOAPOutput:
                   return SOAPOutput(
                       subjective="Custom S", objective="Custom O",
                       assessment="Custom A", plan="Custom P", confidence_score=1.0
                   )
           service = SOAPAssistantService(llm_provider=CustomLLM())
           input_data = SOAPInput(
               patient_cns="123456789012345",
               patient_cpf="12345678909",
               chief_complaint="Teste"
           )
           output = service.generate_draft(input_data)
           assert output.confidence_score == 1.0
           assert output.subjective == "Custom S"
   ```

   Wait, I need to make sure the CNS/CPF validation in the test uses valid numbers. The ones I used might not pass the check digit algorithm. Let me generate valid test numbers or adjust the validator to be more lenient for testing, or just compute valid ones.
   Actually, I'll compute valid CNS and CPF for testing:
   - CPF: 52998224725 is a known valid CPF.
   - CNS: I'll use a simple valid one or adjust the validator to skip check digit for tests? No, better to keep it strict and use a valid CNS. Let's calculate a valid CNS or use a known one. Actually, I'll just use a placeholder that passes the algorithm or adjust the test to use