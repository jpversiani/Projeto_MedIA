Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/services/soap_assistant.py` for a medical AI system (MedIA).
   - **Functionality:** Generate a structured SOAP (Subjective, Objective, Assessment, Plan) draft evolution note from patient complaints during teleconsultation and past medical history.
   - **Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification).
     - Full compliance and automated test coverage with pytest.
     - Provide complete, executable code.
     - Specify file paths in code blocks.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/services/soap_assistant.py`
   - **Core Logic:** Generate SOAP draft from input data (complaints, history, etc.)
   - **Standards:** SUS/APS, CIAP-2, CID-10, CNS/CPF
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0, pytest
   - **Output:** Complete code with tests

3.  **Identify Key Components:**
   - **Pydantic Models:** For input validation (Patient data, Complaints, History, SOAP draft)
   - **Service/Assistant Class:** `SOAPAssistant` or similar, with a method to generate the draft
   - **AI Integration:** Since it's an "AI assistant", I'll simulate the AI generation logic (or use a placeholder for LLM integration) but structure it to be easily replaceable. I'll implement a deterministic/template-based generator that follows SOAP structure and SUS standards, as actual LLM calls would require external dependencies. I'll make it configurable and mockable for testing.
   - **SUS/APS Compliance:** Include fields for CNS, CPF, CIAP-2, CID-10, SOAP sections.
   - **Tests:** Comprehensive pytest suite covering validation, generation logic, edge cases, and SUS standards.

4.  **Design Pydantic Models (Pydantic v2):**
   ```python
   from pydantic import BaseModel, Field, field_validator
   from typing import Optional, List
   from datetime import date
   import re

   class PatientInfo(BaseModel):
       cns: str = Field(..., pattern=r"^\d{15}$", description="Cartão Nacional de Saúde")
       cpf: str = Field(..., pattern=r"^\d{11}$", description="Cadastro de Pessoas Físicas")
       name: str
       birth_date: date

   class Complaint(BaseModel):
       description: str
       onset_date: Optional[date] = None
       severity: Optional[str] = Field(None, pattern=r"^(leve|moderada|grave)$")

   class PastHistory(BaseModel):
       chronic_diseases: List[str] = Field(default_factory=list)
       allergies: List[str] = Field(default_factory=list)
       medications: List[str] = Field(default_factory=list)
       ciap2_codes: List[str] = Field(default_factory=list, description="CIAP-2 codes")
       cid10_codes: List[str] = Field(default_factory=list, description="CID-10 codes")

   class SOAPDraftInput(BaseModel):
       patient: PatientInfo
       complaints: List[Complaint]
       past_history: PastHistory
       vital_signs: Optional[dict] = None
       exam_findings: Optional[str] = None
       physician_notes: Optional[str] = None
   ```

5.  **Design SOAP Assistant Logic:**
   - Need a method `generate_draft(input_data: SOAPDraftInput) -> dict`
   - Structure the output according to SOAP:
     - **S (Subjetivo):** Patient complaints, history, subjective data
     - **O (Objetivo):** Vital signs, exam findings, objective data
     - **A (Avaliação):** Assessment, CIAP-2/CID-10 codes, differential diagnosis
     - **P (Plano):** Treatment plan, follow-up, referrals
   - Incorporate SUS/APS standards: Use standard terminology, reference CIAP-2/CID-10, CNS/CPF identification.
   - Since it's an "AI assistant", I'll simulate AI generation with a rule-based/template approach that can be extended. I'll add a placeholder for LLM integration but keep it deterministic for testing.
   - I'll implement a `SOAPAssistant` class with a `generate` method.

   ```python
   class SOAPAssistant:
       def generate_draft(self, input_data: SOAPDraftInput) -> dict:
           # Validate input
           input_data.model_validate(input_data) # Already validated by Pydantic

           # S: Subjetivo
           subjective = self._build_subjective(input_data)

           # O: Objetivo
           objective = self._build_objective(input_data)

           # A: Avaliação
           assessment = self._build_assessment(input_data)

           # P: Plano
           plan = self._build_plan(input_data)

           return {
               "patient_id": input_data.patient.cns,
               "cpf": input_data.patient.cpf,
               "date": date.today().isoformat(),
               "soap": {
                   "subjective": subjective,
                   "objective": objective,
                   "assessment": assessment,
                   "plan": plan
               }
           }

       def _build_subjective(self, data: SOAPDraftInput) -> str:
           # ...
   ```

   I need to flesh out the methods to follow SUS/APS standards and generate coherent text. I'll use templates and combine input data.

   Let's refine the logic to be more robust and testable. I'll make it generate structured text with clear sections, referencing CIAP-2/CID-10, CNS/CPF, etc.

   Since the prompt asks for "IA" (AI), I'll add a mock LLM integration point but keep the core deterministic for testing. I'll also add type hints strictly.

6.  **Write the Code (Mental Refinement):**
   I'll structure the file with:
   - Imports
   - Pydantic models
   - `SOAPAssistant` class with methods
   - Helper functions for text generation
   - Strict typing throughout
   - Comments for SUS/APS compliance

   I'll also create a comprehensive `test_soap_assistant.py` file.

   Let's draft `backend/app/services/soap_assistant.py`:

   ```python
   # Arquivo: backend/app/services/soap_assistant.py
   from __future__ import annotations
   from datetime import date, datetime
   from typing import Optional, List, Dict, Any
   from pydantic import BaseModel, Field, field_validator, ConfigDict
   import re

   class PatientInfo(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True)
       cns: str = Field(..., pattern=r"^\d{15}$", description="Cartão Nacional de Saúde (15 dígitos)")
       cpf: str = Field(..., pattern=r"^\d{11}$", description="Cadastro de Pessoas Físicas (11 dígitos)")
       name: str = Field(..., min_length=3, max_length=100)
       birth_date: date

       @field_validator("cns")
       @classmethod
       def validate_cns_checksum(cls, v: str) -> str:
           # Simplified CNS validation (real SUS uses specific algorithm)
           if not re.match(r"^\d{15}$", v):
               raise ValueError("CNS deve ter exatamente 15 dígitos numéricos")
           return v

   class Complaint(BaseModel):
       description: str = Field(..., min_length=1)
       onset_date: Optional[date] = None
       severity: Optional[str] = Field(None, pattern=r"^(leve|moderada|grave)$")

   class PastHistory(BaseModel):
       chronic_diseases: List[str] = Field(default_factory=list)
       allergies: List[str] = Field(default_factory=list)
       medications: List[str] = Field(default_factory=list)
       ciap2_codes: List[str] = Field(default_factory=list, description="Códigos CIAP-2")
       cid10_codes: List[str] = Field(default_factory=list, description="Códigos CID-10")

   class SOAPDraftInput(BaseModel):
       patient: PatientInfo
       complaints: List[Complaint]
       past_history: PastHistory
       vital_signs: Optional[Dict[str, Any]] = None
       exam_findings: Optional[str] = None
       physician_notes: Optional[str] = None

   class SOAPDraftOutput(BaseModel):
       patient_cns: str
       patient_cpf: str
       consultation_date: str
       subjective: str
       objective: str
       assessment: str
       plan: str
       ciap2_codes: List[str]
       cid10_codes: List[str]

   class SOAPAssistant:
       """
       Assistente para geração de rascunho SOAP estruturado conforme padrões SUS/APS.
       Integra lógica de template com placeholders para futura integração com LLM.
       """
       def generate_draft(self, input_data: SOAPDraftInput) -> SOAPDraftOutput:
           # Validação implícita via Pydantic v2
           subjective = self._generate_subjective(input_data)
           objective = self._generate_objective(input_data)
           assessment = self._generate_assessment(input_data)
           plan = self._generate_plan(input_data)

           return SOAPDraftOutput(
               patient_cns=input_data.patient.cns,
               patient_cpf=input_data.patient.cpf,
               consultation_date=date.today().isoformat(),
               subjective=subjective,
               objective=objective,
               assessment=assessment,
               plan=plan,
               ciap2_codes=input_data.past_history.ciap2_codes,
               cid10_codes=input_data.past_history.cid10_codes,
           )

       def _generate_subjective(self, data: SOAPDraftInput) -> str:
           lines = [f"Paciente {data.patient.name}, {data.patient.cns}, CPF {data.patient.cpf}."]
           lines.append("Queixa principal:")
           for c in data.complaints:
               line = f"- {c.description}"
               if c.onset_date:
                   line += f" (início: {c.onset_date.isoformat()})"
               if c.severity:
                   line += f" (intensidade: {c.severity})"
               lines.append(line)

           if data.past_history.chronic_diseases:
               lines.append(f"Histórico de doenças crônicas: {', '.join(data.past_history.chronic_diseases)}")
           if data.past_history.allergies:
               lines.append(f"Alergias: {', '.join(data.past_history.allergies)}")
           if data.past_history.medications:
               lines.append(f"Medicamentos em uso: {', '.join(data.past_history.medications)}")

           return "\n".join(lines)

       def _generate_objective(self, data: SOAPDraftInput) -> str:
           lines = ["Exame físico e sinais vitais:"]
           if data.vital_signs:
               for k, v in data.vital_signs.items():
                   lines.append(f"- {k}: {v}")
           if data.exam_findings:
               lines.append(f" achados do exame físico: {data.exam_findings}")
           return "\n".join(lines)

       def _generate_assessment(self, data: SOAPDraftInput) -> str:
           lines = ["Avaliação clínica (Método SOAP / APS SUS):"]
           if data.past_history.cid10_codes:
               lines.append(f"CID-10 provável: {', '.join(data.past_history.cid10_codes)}")
           if data.past_history.ciap2_codes:
               lines.append(f"CIAP-2: {', '.join(data.past_history.ciap2_codes)}")
           if data.physician_notes:
               lines.append(f"Notas do médico: {data.physician_notes}")
           return "\n".join(lines)

       def _generate_plan(self, data: SOAPDraftInput) -> str:
           lines = ["Plano terapêutico e conduta (APS/SUS):"]
           lines.append("- Acompanhamento ambulatorial conforme protocolo de atenção primária.")
           lines.append("- Encaminhamento para exames complementares se indicado.")
           lines.append("- Retorno em 15 dias ou conforme evolução.")
           return "\n".join(lines)
   ```

   Wait, the prompt says "IA" (AI). I should make it clear that this is a service layer that can integrate with an AI model, but for testing purposes, it uses a deterministic generator. I'll add a method to simulate AI generation or keep it as a template-based generator that follows SUS standards strictly. The prompt says "gera rascunho... com IA", so I'll add a placeholder for LLM integration but keep the core logic testable. I'll also add a `generate_with_llm` method signature or use a strategy pattern. Actually, for a tester/engineer, it's better to keep it deterministic and mockable, but I'll add a comment about AI integration. I'll stick to the deterministic approach but structure it so it's clear it's the "assistant" logic.

   Let's refine the code to be more professional and strictly typed. I'll also add proper error handling and validation.

   Now, the test file: `test_soap_assistant.py`
   Needs to cover:
   - Valid input generation
   - Pydantic validation (CNS, CPF, severity)
   - SOAP structure output
   - SUS/APS standards (CIAP-2, CID-10, CNS/CPF)
   - Edge cases (empty lists, optional fields)
   - Type checking (implicit in pytest)

   I'll write comprehensive tests using `pytest`, `pytest-mock`, and `pydantic` validation.

   Structure of tests:
   - `test_valid_input_generation`
   - `test_pydantic_validation_cns`
   - `test_pydantic_validation_cpf`
   - `test_pydantic_validation_severity`
   - `test_soap_structure_content`
   - `test_optional_fields_handling`
   - `test_sus_aps_standards_compliance`

   Let's draft the test file mentally, then write it out.

   ```python
   # Arquivo: backend/app/services/test_soap_assistant.py
   import pytest
   from datetime import date
   from pydantic import ValidationError
   from .soap_assistant import (
       SOAPAssistant,
       SOAPDraftInput,
       PatientInfo,
       Complaint,
       PastHistory,
   )

   class TestSOAPAssistant:
       @pytest.fixture
       def assistant(self) -> SOAPAssistant:
           return SOAPAssistant()

       @pytest.fixture
       def valid_input(self) -> SOAPDraftInput:
           return SOAPDraftInput(
               patient=PatientInfo(
                   cns="123456789012345",
                   cpf="12345678901",
                   name="Maria da Silva",
                   birth_date=date(1980, 5, 15),
               ),
               complaints=[
                   Complaint(description="Dor abdominal há 3 dias", severity="moderada"),
                   Complaint(description="Náuseas", severity="leve"),
               ],
               past_history=PastHistory(
                   chronic_diseases=["Hipertensão"],
                   allergies=["Dipirona"],
                   medications=["Losartana 50mg"],
                   ciap2_codes=["R73"],
                   cid10_codes=["K30", "I10"],
               ),
               vital_signs={"PA": "130/85 mmHg", "FC": "78 bpm"},
               exam_findings="Abdome doloroso à palpação epigástrica",
               physician_notes="Suspeita de gastrite",
           )

       def test_generate_draft_returns_expected_structure(self, assistant, valid_input):
           result = assistant.generate_draft(valid_input)
           assert result.patient_cns == valid_input.patient.cns
           assert result.patient_cpf == valid_input.patient.cpf
           assert result.consultation_date == date.today().isoformat()
           assert "subjective" in result.model_fields
           assert "objective" in result.model_fields
           assert "assessment" in result.model_fields
           assert "plan" in result.model_fields
           assert "R73" in result.ciap2_codes
           assert "K30" in result.cid10_codes

       def test_subjective_contains_complaints_and_history(self, assistant, valid_input):
           result = assistant.generate_draft(valid_input)
           assert "Maria da Silva" in result.subjective
           assert "Dor abdominal há 3 dias" in result.subjective
           assert "Hipertensão" in result.subjective
           assert "Dipirona" in result.subjective
           assert "Losartana 50mg" in result.subjective

       def test_objective_contains_vital_signs_and_exams(self, assistant, valid_input):
           result = assistant.generate_draft(valid_input)
           assert "PA" in result.objective
           assert "130/85 mmHg" in result.objective
           assert "Abdome doloroso" in result.objective

       def test_assessment_contains_ciap2_and_cid10(self, assistant, valid_input):
           result = assistant.generate_draft(valid_input)
           assert "CID-10 provável" in result.assessment
           assert "CIAP-2" in result.assessment
           assert "Suspeita de gastrite" in result.assessment

       def test_plan_contains_standard_aps_guidance(self, assistant, valid_input):
           result = assistant.generate_draft(valid_input)
           assert "Acompanhamento ambulatorial" in result.plan
           assert "Encaminhamento" in result.plan
           assert "Retorno em 15 dias" in result.plan

       def test_pydantic_validates_cns_length(self):
           with pytest.raises(ValidationError):
               PatientInfo(cns="123",