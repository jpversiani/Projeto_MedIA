Here's a thinking process:

1.  **Understand User Goal:** The user wants me to create a backend service file `backend/app/services/soap_assistant.py` for a medical application called "MedIA". This service should generate a structured SOAP (Subjective, Objective, Assessment, Plan) draft using AI, based on patient complaints from a teleconsultation and their medical history. It must follow SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), use Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0, and include full test coverage with pytest.

2.  **Key Requirements:**
   - File: `backend/app/services/soap_assistant.py`
   - Functionality: Generate SOAP draft from patient complaints & history
   - Standards: SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF)
   - Tech Stack: Python 3.12, Pydantic v2, SQLAlchemy 2.0
   - Testing: pytest coverage
   - Output: Complete, executable code with file paths specified

3.  **Architecture & Design Considerations:**
   - **Pydantic Models:** Need models for input (patient info, complaints, history) and output (SOAP draft).
   - **SQLAlchemy Models:** Need to represent Patient, MedicalHistory, Consultation, etc., but since this is a service file, I'll focus on the service logic and define minimal necessary models or assume they exist. However, to make it self-contained and testable, I'll define the necessary Pydantic schemas and mock/define SQLAlchemy models if needed, or just focus on the service logic that interacts with a hypothetical DB/session.
   - **AI Integration:** The prompt says "com IA" (with AI). I'll simulate an AI call (e.g., using a placeholder function or a mock LLM interface) but structure it so it can be easily swapped with a real API call (like OpenAI, local LLM, etc.). I'll use a simple prompt generation + mock response for demonstration, but structure it properly.
   - **SUS/APS Standards:** CIAP-2 (Classificação Internacional de Atenção Primária), CID-10 (ICD-10), SOAP format, CNS/CPF identification. I'll include validation/formatting for these.
   - **Testing:** Need a `test_soap_assistant.py` file with pytest tests covering happy path, validation, AI mock, etc.

4.  **File Structure Planning:**
   - `backend/app/services/soap_assistant.py` - Main service
   - `backend/app/services/soap_assistant.py` will contain:
     - Pydantic models for input/output
     - Service class/function
     - AI prompt generation
     - Mock AI call (or interface)
     - Validation for SUS/APS standards
   - `backend/tests/services/test_soap_assistant.py` - Pytest tests

   Since the prompt asks for `backend/app/services/soap_assistant.py`, I'll provide that. I'll also provide the test file as requested ("cobertura de testes automatizados com pytest").

5.  **Drafting `soap_assistant.py`:**
   - *Imports:* `pydantic`, `sqlalchemy`, `typing`, `re`, `datetime`, `abc` (for AI interface)
   - *Pydantic Models:*
     - `PatientInfo`: cns, cpf, name, age
     - `ConsultationInput`: patient, complaints, vital_signs, medical_history, previous_diagnoses
     - `SOAPDraft`: subjective, objective, assessment, plan, ciap_codes, cid_codes, generated_at
   - *Service Class:* `SOAPAssistantService`
     - `__init__`: takes AI client (abstracted)
     - `generate_draft`: main method
     - `_build_prompt`: constructs prompt for AI
     - `_validate_sus_standards`: checks CIAP-2/CID-10 format, CNS/CPF
     - `_parse_ai_response`: extracts JSON from AI response
   - *AI Interface:* Define an abstract base class or simple callable interface. For simplicity, I'll use a callable `AIProvider` protocol or just a mock function in tests. I'll stick to a simple `call_llm(prompt: str) -> str` interface.
   - *SUS/APS Validation:* CIAP-2 codes are alphanumeric (e.g., R10, A01). CID-10 are alphanumeric (e.g., J06.9). CNS is 15 digits. CPF is 11 digits. I'll add regex validation.
   - *SOAP Structure:* Standard medical documentation format.

   Let's write it out carefully.

   ```python
   # Arquivo: backend/app/services/soap_assistant.py
   from __future__ import annotations
   import re
   from abc import ABC, abstractmethod
   from datetime import datetime
   from typing import Protocol, runtime_checkable
   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy.orm import Session

   # --- Pydantic Models ---
   class PatientInfo(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True)
       cns: str = Field(..., description="Cartão Nacional de Saúde (15 dígitos)")
       cpf: str = Field(..., description="Cadastro de Pessoas Físicas (11 dígitos)")
       nome: str
       idade: int

   class ConsultationInput(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True)
       paciente: PatientInfo
       queixas: str = Field(..., description="Queixas relatadas pelo paciente")
       sinais_sintomas: str = Field(default="", description="Sinais e sintomas observados")
       historico_pregresso: str = Field(default="", description="Histórico médico pregresso")
       diagnoticos_anteriores: list[str] = Field(default_factory=list, description="Diagnósticos anteriores (CID-10 ou CIAP-2)")

   class SOAPDraft(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True)
       cns: str
       cpf: str
       nome_paciente: str
       data_geracao: datetime = Field(default_factory=datetime.now)
       subjetivo: str
       objetivo: str
       avaliacao: str
       plano: str
       ciap_codes: list[str] = Field(default_factory=list)
       cid_codes: list[str] = Field(default_factory=list)

       @field_validator("ciap_codes", "cid_codes")
       @classmethod
       def validate_codes(cls, v: list[str]) -> list[str]:
           # CIAP-2: 1-2 letters + 1-2 digits (e.g., R10, A01)
           # CID-10: 1 letter + 1-2 digits + optional . + digits (e.g., J06.9, I10)
           ciap_pattern = re.compile(r"^[A-Z]{1,2}\d{1,2}$")
           cid_pattern = re.compile(r"^[A-Z]\d{1,2}(\.\d{1,2})?$")
           valid_v = []
           for code in v:
               if ciap_pattern.match(code):
                   valid_v.append(code)
               elif cid_pattern.match(code):
                   valid_v.append(code)
           return valid_v

   # --- AI Provider Interface ---
   @runtime_checkable
   class AIProvider(Protocol):
       def generate(self, prompt: str) -> str: ...

   # --- Service ---
   class SOAPAssistantService:
       def __init__(self, ai_provider: AIProvider):
           self.ai = ai_provider

       def generate_draft(self, input_data: ConsultationInput) -> SOAPDraft:
           # 1. Validate SUS/APS standards
           self._validate_standards(input_data)

           # 2. Build prompt
           prompt = self._build_prompt(input_data)

           # 3. Call AI
           raw_response = self.ai.generate(prompt)

           # 4. Parse & Validate Output
           draft = self._parse_response(raw_response, input_data)

           # 5. Final validation
           draft.model_validate(draft.model_dump())
           return draft

       def _validate_standards(self, data: ConsultationInput) -> None:
           cns_pattern = re.compile(r"^\d{15}$")
           cpf_pattern = re.compile(r"^\d{11}$")
           if not cns_pattern.match(data.paciente.cns):
               raise ValueError("CNS inválido. Deve conter 15 dígitos numéricos.")
           if not cpf_pattern.match(data.paciente.cpf):
               raise ValueError("CPF inválido. Deve conter 11 dígitos numéricos.")

       def _build_prompt(self, data: ConsultationInput) -> str:
           return f"""
           Você é um assistente médico especializado em Atenção Primária à Saúde (APS) do SUS.
           Gere um rascunho de evolução médica no formato SOAP (Subjetivo, Objetivo, Avaliação, Plano)
           com base nas informações abaixo. Retorne APENAS um JSON válido seguindo o schema:
           {{
             "subjetivo": "string",
             "objetivo": "string",
             "avaliacao": "string",
             "plano": "string",
             "ciap_codes": ["string"],
             "cid_codes": ["string"]
           }}

           Dados do Paciente:
           - CNS: {data.paciente.cns}
           - CPF: {data.paciente.cpf}
           - Nome: {data.paciente.nome}
           - Idade: {data.paciente.idade}

           Informações da Consulta:
           - Queixas: {data.queixas}
           - Sinais/Sintomas: {data.sinais_sintomas}
           - Histórico Pregresso: {data.historico_pregresso}
           - Diagnósticos Anteriores: {', '.join(data.diagnosticos_anteriores) if data.diagnosticos_anteriores else 'Nenhum'}

           Diretrizes:
           - Use terminologia médica padrão SUS/APS.
           - CIAP-2 para problemas de saúde primários.
           - CID-10 para diagnósticos clínicos.
           - Mantenha o tom profissional e conciso.
           - Se não houver dados suficientes para um campo, indique "Não informado" ou "A avaliar".
           """

       def _parse_response(self, raw: str, input_data: ConsultationInput) -> SOAPDraft:
           import json
           try:
               # Extract JSON from markdown or raw text
               json_str = raw.strip()
               if json_str.startswith("```"):
                   lines = json_str.split("\n")
                   json_str = "\n".join(lines[1:-1])
               data = json.loads(json_str)
           except json.JSONDecodeError as e:
               raise ValueError(f"Falha ao parsear resposta da IA: {e}")

           return SOAPDraft(
               cns=input_data.paciente.cns,
               cpf=input_data.paciente.cpf,
               nome_paciente=input_data.paciente.nome,
               subjetivo=data.get("subjetivo", "Não informado"),
               objetivo=data.get("objetivo", "Não informado"),
               avaliacao=data.get("avaliacao", "Não informado"),
               plano=data.get("plano", "Não informado"),
               ciap_codes=data.get("ciap_codes", []),
               cid_codes=data.get("cid_codes", [])
           )
   ```

6.  **Drafting `test_soap_assistant.py`:**
   - Need to mock the AI provider.
   - Test cases:
     - Valid input -> valid draft
     - Invalid CNS -> ValueError
     - Invalid CPF -> ValueError
     - AI returns invalid JSON -> ValueError
     - AI returns markdown JSON -> parsed correctly
     - CIAP/CID validation
   - Use `pytest`, `unittest.mock`, `pydantic` validation.
   - Ensure strict typing and coverage.

   ```python
   # Arquivo: backend/tests/services/test_soap_assistant.py
   import pytest
   from unittest.mock import MagicMock
   from pydantic import ValidationError
   from backend.app.services.soap_assistant import (
       SOAPAssistantService,
       ConsultationInput,
       PatientInfo,
       SOAPDraft,
   )

   # Mock AI Provider
   class MockAIProvider:
       def __init__(self, response: str):
           self.response = response
       def generate(self, prompt: str) -> str:
           return self.response

   VALID_INPUT = ConsultationInput(
       paciente=PatientInfo(cns="123456789012345", cpf="12345678901", nome="João Silva", idade=45),
       queixas="Dor no peito há 3 dias, piora com esforço.",
       sinais_sintomas="TA 140/90 mmHg, FC 88 bpm",
       historico_pregresso="Hipertensão, Diabetes Tipo 2",
       diagnosticos_anteriores=["I10", "E11.9"]
   )

   MOCK_JSON_RESPONSE = """
   {
     "subjetivo": "Paciente refere dor precordial há 3 dias, de intensidade moderada, irradiada para braço esquerdo.",
     "objetivo": "PA 140/90 mmHg, FC 88 bpm, FR 18 ipm. Ausculta cardíaca regular, sem sopros.",
     "avaliacao": "Suspeita de síndrome coronariana aguda não supradesionada. Fatores de risco: HTA, DM2.",
     "plano": "1. ECG de repouso; 2. Troponina seriada; 3. Orientação sobre sinais de alerta; 4. Retorno em 24h.",
     "ciap_codes": ["R10", "A01"],
     "cid_codes": ["I20.9", "I10", "E11.9"]
   }
   """

   @pytest.fixture
   def service():
       mock_ai = MockAIProvider(MOCK_JSON_RESPONSE)
       return SOAPAssistantService(ai_provider=mock_ai)

   def test_generate_draft_valid(service):
       draft = service.generate_draft(VALID_INPUT)
       assert draft.cns == VALID_INPUT.paciente.cns
       assert draft.nome_paciente == VALID_INPUT.paciente.nome
       assert draft.subjetivo != ""
       assert draft.cid_codes == ["I20.9", "I10", "E11.9"]
       assert draft.ciap_codes == ["R10", "A01"]

   def test_generate_draft_invalid_cns():
       bad_input = ConsultationInput(
           paciente=PatientInfo(cns="123", cpf="12345678901", nome="Teste", idade=30),
           queixas="Dor", sinais_sintomas="", historico_pregresso="", diagnosticos_anteriores=[]
       )
       mock_ai = MockAIProvider("{}")
       svc = SOAPAssistantService(ai_provider=mock_ai)
       with pytest.raises(ValueError, match="CNS inválido"):
           svc.generate_draft(bad_input)

   def test_generate_draft_invalid_cpf():
       bad_input = ConsultationInput(
           paciente=PatientInfo(cns="123456789012345", cpf="123", nome="Teste", idade=30),
           queixas="Dor", sinais_sintomas="", historico_pregresso="", diagnosticos_anteriores=[]
       )
       mock_ai = MockAIProvider("{}")
       svc = SOAPAssistantService(ai_provider=mock_ai)
       with pytest.raises(ValueError, match="CPF inválido"):
           svc.generate_draft(bad_input)

   def test_generate_draft_invalid_json(service):
       mock_ai = MockAIProvider("Não é JSON")
       svc = SOAPAssistantService(ai_provider=mock_ai)
       with pytest.raises(ValueError, match="Falha ao parsear resposta da IA"):
           svc.generate_draft(VALID_INPUT)

   def test_generate_draft_with_markdown_json():
       mock_ai = MockAIProvider("```json\n" + MOCK_JSON_RESPONSE.strip() + "\n```")
       svc = SOAPAssistantService(ai_provider=mock_ai)
       draft = svc.generate_draft(VALID_INPUT)
       assert draft.subjetivo != ""

   def test_soap_draft_validation():
       # Test CIAP/CID validation
       draft = SOAPDraft(
           cns="123456789012345",
           cpf="12345678901",
           nome_paciente="Teste",
           subjetivo="S",
           objetivo="O",
           avaliacao="A",
           plano="P",
           ciap_codes=["R10", "INVALID"],
           cid_codes=["I10", "BAD"]
       )
       assert draft.ciap_codes == ["R10"]
       assert draft.cid_codes == ["I10"]
   ```

7.  **Review & Refine:**
   - Check Python 3.12 compatibility: `from __future__ import annotations`, `Protocol`, `typing` are fine. Pydantic v2 uses `model_config`, `field_validator`, `ConfigDict`. All good.
   - SQLAlchemy 2.0: The prompt mentions it, but this service is stateless and doesn't directly interact with DB models. I should add a note or minimal SQLAlchemy integration if needed, but the service is meant to be called from a repository/controller. I'll keep it focused on the service logic. I'll add a comment about SQLAlchemy 2.0 compatibility and how it would be used in a repository pattern.
   - SUS/APS standards: CIAP-2/CID-10 validation added. CNS/CPF validation added. SOAP structure enforced.
   - AI integration: Abstracted via `Protocol`. Mocked in tests. Prompt follows SUS/APS guidelines.
   - Testing: Covers validation, AI parsing, markdown handling, invalid inputs. Uses pytest.
   - File paths specified as requested.
   - Code is complete and executable (with mock).
   - I'll adjust the Pydantic v2 syntax to be strictly correct. `model_config = ConfigDict(...)` is