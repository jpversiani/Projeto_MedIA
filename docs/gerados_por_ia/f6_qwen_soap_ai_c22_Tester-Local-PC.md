Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/services/soap_assistant.py` for a medical AI system (MedIA).
   - **Functionality:** Generate a structured SOAP (Subjective, Objective, Assessment, Plan) draft evolution note from patient complaints during teleconsultation and past medical history.
   - **Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards (CIAP-2, ICD-10/CID-10, SOAP method, CNS/CPF identification).
     - Full compliance and automated test coverage with pytest.
     - Provide complete, executable code. Specify file paths in code blocks.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/services/soap_assistant.py`
   - **Core Functionality:** AI-assisted SOAP note generation. Since it's a backend service, it should interface with an LLM (or mock it for testing/demonstration), but the prompt says "com IA" (with AI). I'll design it to accept an AI client/interface but provide a deterministic/mock implementation for testing, or use a standard LLM API structure. Given the constraint "código completo e executável" and "cobertura de testes automatizados", I should make it self-contained enough to run/test, but clearly structured for AI integration. I'll use a mock AI service or a simple rule-based/template-based generator that can be easily swapped, but I'll also show how to integrate with an LLM (e.g., OpenAI) if needed. Actually, for testing and compliance, I'll implement a deterministic generator that follows SOAP structure strictly, and add a clear interface for AI integration. I'll also include Pydantic models for input/output.
   - **Standards:** CIAP-2 (Classificação Internacional de Atenção Primária), CID-10 (ICD-10), SOAP, CNS/CPF.
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0, pytest.
   - **Testing:** Need to provide pytest tests covering the service.

3.  **Design Architecture:**
   - **Pydantic Models:**
     - `PatientInfo`: cpf, cns, name, birth_date
     - `TeleconsultationData`: complaints, vital_signs, exam_results, past_history, current_medications
     - `SoapDraft`: subjective, objective, assessment, plan, ciap_codes, icd10_codes, generated_at
   - **Service Class:** `SoapAssistantService`
     - Methods: `generate_soap_draft(patient_info, teleconsultation_data)`
     - Internal logic: Parse complaints, map to CIAP-2/CID-10 (mock/dictionary for demo), structure SOAP sections, format output.
     - AI Integration: I'll add a `llm_client` parameter or use a strategy pattern. For simplicity and testability, I'll implement a deterministic generator that follows medical standards, and add a clear extension point for AI. I'll also include a mock AI function that simulates LLM output but is fully testable.
   - **SQLAlchemy 2.0:** The prompt mentions SQLAlchemy 2.0, but the service itself doesn't necessarily need DB models unless we're saving drafts. I'll add a simple `SoapDraftModel` for persistence, but keep the service focused on generation. Actually, the task says "crie backend/app/services/soap_assistant.py", so I'll focus on the service. I'll include a Pydantic model for DB interaction if needed, but keep it clean.
   - **Testing:** pytest tests for the service, covering happy path, edge cases, CIAP-2/CID-10 mapping, SOAP structure validation.

4.  **Draft Code (Mental Refinement):**
   ```python
   # backend/app/services/soap_assistant.py
   from __future__ import annotations
   import logging
   from datetime import datetime
   from typing import Optional
   from pydantic import BaseModel, Field, field_validator
   from enum import Enum

   logger = logging.getLogger(__name__)

   class SoapSection(str, Enum):
       SUBJECTIVE = "Subjetivo"
       OBJECTIVE = "Objetivo"
       ASSESSMENT = "Avaliação"
       PLAN = "Plano"

   class PatientInfo(BaseModel):
       cpf: str = Field(..., pattern=r"^\d{11}$")
       cns: str = Field(..., pattern=r"^\d{15}$")
       name: str
       birth_date: str  # ISO format

   class TeleconsultationData(BaseModel):
       complaints: str
       vital_signs: Optional[str] = None
       exam_results: Optional[str] = None
       past_history: Optional[str] = None
       current_medications: Optional[str] = None

       @field_validator("complaints")
       @classmethod
       def validate_complaints(cls, v: str) -> str:
           if not v.strip():
               raise ValueError("Queixas não podem estar vazias")
           return v.strip()

   class SoapDraft(BaseModel):
       patient_cpf: str
       patient_cns: str
       subjective: str
       objective: str
       assessment: str
       plan: str
       ciap_codes: list[str] = Field(default_factory=list)
       icd10_codes: list[str] = Field(default_factory=list)
       generated_at: datetime = Field(default_factory=datetime.utcnow)

       @field_validator("subjective", "objective", "assessment", "plan")
       @classmethod
       def validate_sections_not_empty(cls, v: str) -> str:
           if not v.strip():
               raise ValueError("Seções do SOAP não podem estar vazias")
           return v.strip()

   # Mock CIAP-2 and CID-10 mapping for demonstration
   CIAP2_MAPPING = {
       "dor de cabeça": "A89",
       "febre": "A95",
       "tosse": "A96",
       "fadiga": "B74",
       "náusea": "A98",
   }

   CID10_MAPPING = {
       "dor de cabeça": "R51",
       "febre": "R50.9",
       "tosse": "R05",
       "fadiga": "R53.83",
       "náusea": "R11.0",
   }

   class SoapAssistantService:
       def __init__(self, llm_client: Optional[object] = None):
           self.llm_client = llm_client
           self._ciap_map = CIAP2_MAPPING
           self._icd10_map = CID10_MAPPING

       def generate_soap_draft(self, patient: PatientInfo, consultation: TeleconsultationData) -> SoapDraft:
           # Extract keywords for mapping
           complaints_lower = consultation.complaints.lower()
           ciap_codes = [code for term, code in self._ciap_map.items() if term in complaints_lower]
           icd10_codes = [code for term, code in self._icd10_map.items() if term in complaints_lower]

           # Generate SOAP sections (deterministic/template-based for reliability & testing)
           subjective = self._generate_subjective(patient, consultation)
           objective = self._generate_objective(consultation)
           assessment = self._generate_assessment(consultation, ciap_codes, icd10_codes)
           plan = self._generate_plan(consultation)

           return SoapDraft(
               patient_cpf=patient.cpf,
               patient_cns=patient.cns,
               subjective=subjective,
               objective=objective,
               assessment=assessment,
               plan=plan,
               ciap_codes=ciap_codes,
               icd10_codes=icd10_codes,
           )

       def _generate_subjective(self, patient: PatientInfo, consultation: TeleconsultationData) -> str:
           return (
               f"Paciente {patient.name}, {patient.birth_date}, "
               f"relata queixa principal: {consultation.complaints}. "
               f"{'Histórico pregresso: ' + consultation.past_history if consultation.past_history else ''}"
           )

       def _generate_objective(self, consultation: TeleconsultationData) -> str:
           parts = []
           if consultation.vital_signs:
               parts.append(f"Sinais vitais: {consultation.vital_signs}")
           if consultation.exam_results:
               parts.append(f"Exames complementares: {consultation.exam_results}")
           if consultation.current_medications:
               parts.append(f"Medicamentos em uso: {consultation.current_medications}")
           return "; ".join(parts) if parts else "Exame físico não detalhado na teleconsulta."

       def _generate_assessment(self, consultation: TeleconsultationData, ciap_codes: list[str], icd10_codes: list[str]) -> str:
           assessment_parts = [f"Queixa principal: {consultation.complaints}"]
           if ciap_codes:
               assessment_parts.append(f"CIAP-2: {', '.join(ciap_codes)}")
           if icd10_codes:
               assessment_parts.append(f"CID-10: {', '.join(icd10_codes)}")
           return " ".join(assessment_parts)

       def _generate_plan(self, consultation: TeleconsultationData) -> str:
           plan_parts = ["Reposição de líquidos e repouso.", "Retorno em 7 dias ou ante-sinal."]
           if consultation.current_medications:
               plan_parts.append("Manter medicação atual sob supervisão.")
           return " | ".join(plan_parts)
   ```

   Wait, the prompt says "com IA". I should explicitly show how AI would be integrated, but keep it testable. I'll add a method that can use an LLM if provided, but fallback to the deterministic generator. Actually, for a medical system, deterministic + AI-assisted is better. I'll structure it so the AI is called if available, but the service itself is robust. I'll also add a clear interface for AI.

   Let's refine to include AI integration properly, but keep it mockable for tests. I'll use a strategy or just a simple `call_llm` method that can be overridden/mocked.

   Actually, the prompt says "gera rascunho... com IA". I'll implement a method that constructs a prompt and calls an LLM, but for the sake of "código completo e executável" and "cobertura de testes", I'll provide a mock LLM client that returns structured output, and show how to test it. I'll also add proper typing and Pydantic v2 features.

   Let's structure it properly:
   - Pydantic models for input/output
   - Service class with `generate_soap_draft`
   - AI prompt construction
   - Mock LLM for testing
   - Clear separation of concerns

   I'll also add SQLAlchemy 2.0 model for persistence if needed, but the task focuses on the service. I'll stick to the service.

   Now, tests:
   - Test happy path
   - Test CIAP-2/CID-10 mapping
   - Test validation
   - Test AI integration (mocked)
   - Test edge cases (empty fields, etc.)

   Let's write the code carefully.

   **File 1:** `backend/app/services/soap_assistant.py`
   **File 2:** `backend/tests/test_soap_assistant.py`

   I'll make sure it's Python 3.12 compatible, uses Pydantic v2, SQLAlchemy 2.0 (I'll add a simple model for draft persistence to satisfy the guideline, even if not strictly required by the service, to show compliance).

   Actually, the guideline says "tipagem estrita com Pydantic v2 e SQLAlchemy 2.0". I'll include a SQLAlchemy 2.0 model for `SoapDraftRecord` to show compliance, but keep the service focused on generation.

   Let's draft carefully.
   Structure:
   - Imports
   - Pydantic models
   - SQLAlchemy 2.0 model (optional but good for compliance)
   - Service class with AI integration
   - Helper methods
   - Tests

   I'll ensure strict typing, Pydantic v2 validators, and pytest coverage.
   I'll use `typing` module, `datetime`, `logging`, `enum`, `pydantic`, `sqlalchemy`.
   For AI, I'll define a protocol/interface for LLM client, then implement a mock for testing.

   Let's write it out. 
   Self-Correction/Refinement during thought:
   - The prompt says "com IA", so I must show AI integration. I'll use a simple prompt-based approach with a mock LLM that returns structured JSON/text, but for testing, I'll mock it to return deterministic SOAP.
   - I'll add a `llm_client` parameter to the service.
   - I'll use Pydantic v2's `model_validator` and `Field`.
   - I'll ensure SQLAlchemy 2.0 syntax (`Mapped`, `mapped_column`, etc.).
   - Tests will cover generation, validation, CIAP-2/CID-10 mapping, and AI mock.

   Code structure:
   ```python
   # backend/app/services/soap_assistant.py
   from __future__ import annotations
   import logging
   from datetime import datetime
   from typing import Optional, Protocol
   from pydantic import BaseModel, Field, field_validator, model_validator
   from enum import Enum
   from sqlalchemy import String, Text, DateTime
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

   # ... models ...
   # ... service ...
   ```

   I'll write it out carefully now.
   I'll make sure the AI part is realistic but testable. I'll use a simple prompt template and a mock LLM that parses the prompt and returns a structured response. For production, it would call OpenAI/Anthropic, but for this task, I'll show the integration pattern.

   Let's generate. 
   I'll produce two files: the service and the tests.
   I'll ensure strict typing, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards, and pytest coverage.
   All code will be complete and executable.
   I'll add comments for file paths.
   Ready.✅
   Output matches the response. 
   Structure of response:
   - `backend/app/services/soap_assistant.py`
   - `backend/tests/test_soap_assistant.py`
   - Brief explanation of architecture & testing strategy.
   - All code blocks properly tagged.
   - Strict typing, Pydantic v2, SQLAlchemy 2.0, CIAP-2/CID-10, SOAP, CNS/CPF, pytest.
   - Executable & testable.✅
   Proceeds. 
   *Self-Correction/Verification during drafting:*
   - Check Pydantic v2 syntax: `Field(pattern=...)`, `field_validator`, `model_validator` are correct.
   - Check SQLAlchemy 2.0: `DeclarativeBase`, `Mapped`, `mapped_column` are correct.
   - Check Python 3.12: `from __future__ import annotations` enables postponed evaluation, good for forward refs.
   - Check SUS/APS: CIAP-2, CID-10, CNS/CPF validation included.
   - Check AI: Protocol for LLM, mock implementation, prompt construction.
   - Check tests: pytest, coverage, edge cases, validation, AI mock.
   - All good. Output matches. 
   I'll generate the response now. 
   [Output Generation] -> *Proceeds*
Aqui está a implementação completa, seguindo rigorosamente as diretrizes de arquitetura, padrões do SUS/APS, tipagem estrita, Pydantic v2, SQLAlchemy 2.0 e cobertura de testes com pytest.

### 1. Serviço: `backend/app/services/soap_assistant.py`

```python
# Arquivo: backend/app/services/soap_assistant.py
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Protocol
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic v2: Modelos de Entrada e Saída
# ---------------------------------------------------------------------------

class PatientInfo(BaseModel):
    cpf: str = Field(..., pattern=r"^\d{11}$", description="CPF do paciente (11 dígitos)")
    cns: str = Field(..., pattern=r"^\d{15}$", description="Cartão Nacional de Saúde (15 dígitos)")
    name: str = Field(..., min_length=3, max_length=150)
    birth_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Data de nascimento no formato ISO (YYYY-MM-DD)")

class TeleconsultationData(BaseModel):
    complaints: str = Field(..., min_length=5, max_length=2000)
    vital_signs: Optional[str] = None
    exam_results: Optional[str] = None
    past_history: Optional[str] = None
    current_medications: Optional[str] = None

    @field_validator("complaints")
    @classmethod
    def validate_complaints(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("As queixas não podem estar vazias ou conter apenas espaços.")
        return v.strip()

class SoapDraft(BaseModel):
    patient_cpf: str
    patient_cns: str
    subjective: str
    objective: str
    assessment: str
    plan: str
    ciap_codes: list[str] = Field(default_factory=list)
    icd10_codes: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def validate_soap_sections(self) -> SoapDraft:
        for field_name in ("subjective", "objective