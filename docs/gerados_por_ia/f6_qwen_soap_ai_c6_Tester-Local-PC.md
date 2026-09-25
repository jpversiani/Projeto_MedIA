Here's a thinking process:

1.  **Understand User Goal:** The user wants me to act as a software engineer/tester and create a specific file: `backend/app/services/soap_assistant.py`. This file should generate a structured SOAP (Subjective, Objective, Assessment, Plan) draft for a family doctor in a system called "MedIA". It should use AI (implied by "IA" in the title, but I need to implement it in a way that's testable and follows the architecture guidelines). The system should follow SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification). It must use Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0, and include full test coverage with pytest.

2.  **Analyze Requirements & Constraints:**
   - **File to create:** `backend/app/services/soap_assistant.py`
   - **Functionality:** Generate a structured SOAP draft from patient complaints and historical data.
   - **Standards:** SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF).
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0.
   - **Testing:** Full pytest coverage.
   - **Output:** Complete, executable code for the requested file, plus tests if needed (though the prompt specifically asks for the service file, I should probably provide the test file as well to satisfy "cobertura de testes automatizados com pytest").
   - **Format:** Specify file path at the top of each code block.

3.  **Design the Service (`soap_assistant.py`):**
   - Need Pydantic models for input/output.
   - Input: Patient complaints (subjective), objective data (vitals, exam results), historical context (previous diagnoses, medications), patient ID (CNS/CPF).
   - Output: Structured SOAP draft.
   - Since it says "com IA" (with AI), I should simulate an AI call or use a placeholder for an LLM integration, but make it deterministic/testable. I'll create a service class that can be configured with an AI provider (or use a mock/fake implementation for testing). I'll structure it to be easily swappable with a real LLM API later.
   - I'll define Pydantic models for the SOAP structure.
   - I'll use SQLAlchemy 2.0 style for data access (though the service itself might just take data as input, I can show how it interacts with models if needed, but the prompt says "a partir das queixas relatadas... e histórico pregresso", so I'll accept these as parameters).
   - I'll ensure strict typing.
   - I'll implement a `SoapAssistantService` class with a `generate_draft` method.
   - I'll include logic to map complaints to CIAP-2/CID-10 codes (simulated or rule-based for determinism in tests).
   - I'll structure the output as a Pydantic model.

   Let's draft the structure:
   ```python
   # Arquivo: backend/app/services/soap_assistant.py
   from __future__ import annotations
   from dataclasses import dataclass
   from typing import Optional
   from pydantic import BaseModel, Field, field_validator
   import re

   # Pydantic models for SOAP structure
   class SoapSection(BaseModel):
       content: str
       codes: list[str] = Field(default_factory=list) # CIAP-2 or CID-10

   class SoapDraft(BaseModel):
       patient_cns: str
       patient_cpf: str
       subjective: SoapSection
       objective: SoapSection
       assessment: SoapSection
       plan: SoapSection
       generated_at: str = Field(default_factory=lambda: __import__('datetime').datetime.now().isoformat())

   # Service class
   class SoapAssistantService:
       def __init__(self, ai_client: Optional[Any] = None):
           self.ai_client = ai_client

       def generate_draft(self,
                          patient_cns: str,
                          patient_cpf: str,
                          subjective_input: str,
                          objective_data: str,
                          historical_context: str) -> SoapDraft:
           # Logic to generate SOAP
           # Since we need it testable and deterministic, I'll implement a rule-based generator
           # that can be swapped with an AI call. I'll add a flag/method to use AI if available.
           ...
   ```

   Wait, the prompt says "com IA" (with AI). I should probably use a mock AI or a structured prompt that simulates AI output, but keep it testable. I'll implement a deterministic generator that mimics AI structure, and add a method to integrate with a real LLM later. For now, I'll make it a pure function/service that processes inputs into SOAP format, following SUS/APS standards. I'll add CIAP-2/CID-10 mapping logic (simplified for demonstration).

   Let's refine the Pydantic models to be more robust:
   ```python
   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from typing import Optional, List
   from datetime import datetime

   class SoapSection(BaseModel):
       model_config = ConfigDict(extra='ignore')
       content: str
       codes: List[str] = Field(default_factory=list)
       icd10_codes: List[str] = Field(default_factory=list)
       ciap2_codes: List[str] = Field(default_factory=list)

   class SoapDraft(BaseModel):
       patient_cns: str
       patient_cpf: str
       subjective: SoapSection
       objective: SoapSection
       assessment: SoapSection
       plan: SoapSection
       generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

       @field_validator('patient_cns', 'patient_cpf')
       @classmethod
       def validate_identifiers(cls, v: str) -> str:
           if not v or len(v) < 3:
               raise ValueError("Identificador inválido")
           return v.strip()
   ```

   Now the service logic. I'll create a deterministic generator that structures the input into SOAP format, extracts/infers codes (simulated), and validates. I'll also add a method to call an external AI if configured, but default to a robust template-based generator for testability.

   Actually, to strictly follow "com IA", I should probably use a prompt template and a mock/async client, but keep it simple and testable. I'll implement a `generate_soap_draft` function that uses a structured approach, and I'll add a `use_ai` flag. For the purpose of this task, I'll make it a pure service that can be tested without external dependencies, but structured to integrate with an LLM later. I'll simulate the AI output generation deterministically for tests.

   Let's think about SUS/APS standards:
   - CIAP-2: Classificação Internacional de Atenção Primária (2nd edition)
   - CID-10: Classificação Internacional de Doenças (10th revision)
   - SOAP: Subjetivo (queixas, história), Objetivo (sinais, exames), Avaliação (diagnóstico, hipóteses), Plano (conduta, medicamentos, encaminhamentos)
   - CNS: Cadastro Nacional de Saúde (15 digits)
   - CPF: Cadastro de Pessoas Físicas (11 digits)

   I'll add validation for CNS and CPF formats.
   I'll add a simple code mapping dictionary for demonstration.
   I'll structure the service to be stateless and functional.

   Let's draft the full `soap_assistant.py`:

   ```python
   # Arquivo: backend/app/services/soap_assistant.py
   from __future__ import annotations
   from typing import Optional, List
   from datetime import datetime
   from pydantic import BaseModel, Field, field_validator, ConfigDict
   import re

   # --- Models ---
   class SoapSection(BaseModel):
       model_config = ConfigDict(extra='ignore')
       content: str
       codes: List[str] = Field(default_factory=list, description="CIAP-2 codes")
       icd10_codes: List[str] = Field(default_factory=list, description="CID-10 codes")

       @field_validator('content')
       @classmethod
       def validate_content_not_empty(cls, v: str) -> str:
           if not v.strip():
               raise ValueError("O conteúdo da seção não pode estar vazio")
           return v.strip()

   class SoapDraft(BaseModel):
       patient_cns: str
       patient_cpf: str
       subjective: SoapSection
       objective: SoapSection
       assessment: SoapSection
       plan: SoapSection
       generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

       @field_validator('patient_cns')
       @classmethod
       def validate_cns(cls, v: str) -> str:
           if not re.match(r'^\d{15}$', v):
               raise ValueError("CNS inválido. Deve conter 15 dígitos numéricos.")
           return v

       @field_validator('patient_cpf')
       @classmethod
       def validate_cpf(cls, v: str) -> str:
           if not re.match(r'^\d{11}$', v):
               raise ValueError("CPF inválido. Deve conter 11 dígitos numéricos.")
           return v

   # --- Service ---
   class SoapAssistantService:
       """
       Serviço para geração de rascunho SOAP estruturado conforme padrões SUS/APS.
       Utiliza lógica determinística para garantir testabilidade, com suporte a integração futura com LLMs.
       """

       # Mapeamento simplificado para demonstração de CIAP-2/CID-10
       _CODE_MAP = {
           "dor": ("R51", "A01"),
           "febre": ("R50", "A01"),
           "tosse": ("R05", "A01"),
           "fadiga": ("R53", "A01"),
           "náusea": ("R11", "A01"),
       }

       def __init__(self, ai_client: Optional[Any] = None):
           self.ai_client = ai_client

       def generate_draft(
           self,
           patient_cns: str,
           patient_cpf: str,
           subjective_input: str,
           objective_data: str,
           historical_context: str,
           use_ai: bool = False
       ) -> SoapDraft:
           """
           Gera um rascunho SOAP estruturado.
           Se use_ai=True e ai_client estiver configurado, delega à IA.
           Caso contrário, utiliza gerador determinístico baseado em regras SUS/APS.
           """
           if use_ai and self.ai_client:
               return self._generate_with_ai(patient_cns, patient_cpf, subjective_input, objective_data, historical_context)

           return self._generate_deterministic(patient_cns, patient_cpf, subjective_input, objective_data, historical_context)

       def _generate_deterministic(
           self,
           patient_cns: str,
           patient_cpf: str,
           subjective_input: str,
           objective_data: str,
           historical_context: str
       ) -> SoapDraft:
           # Processamento Subjetivo
           subj_content = f"Queixa principal: {subjective_input}\nHistória da doença atual: {subjective_input}\nHistórico pregresso: {historical_context}"
           subj_codes = self._extract_codes(subjective_input)

           # Processamento Objetivo
           obj_content = f"Sinais vitais e exame físico: {objective_data}\nExames complementares: {objective_data}"
           obj_codes = self._extract_codes(objective_data)

           # Processamento Avaliação (hipótese diagnóstica baseada em CIAP-2/CID-10)
           assessment_codes = subj_codes + obj_codes
           assessment_content = f"Hipóteses diagnósticas: {', '.join(assessment_codes) if assessment_codes else 'Avaliação clínica em andamento'}\nContexto histórico: {historical_context}"

           # Processamento Plano (conduta padrão SUS/APS)
           plan_content = f"Conduta: Acompanhamento clínico, orientações de autocuidado e retorno em 15 dias.\nMedicamentos: A critério médico.\nEncaminhamentos: Nenhum no momento."
           plan_codes = []

           return SoapDraft(
               patient_cns=patient_cns,
               patient_cpf=patient_cpf,
               subjective=SoapSection(content=subj_content, codes=subj_codes, icd10_codes=[f"CID-{c}" for c in subj_codes]),
               objective=SoapSection(content=obj_content, codes=obj_codes, icd10_codes=[f"CID-{c}" for c in obj_codes]),
               assessment=SoapSection(content=assessment_content, codes=assessment_codes, icd10_codes=[f"CID-{c}" for c in assessment_codes]),
               plan=SoapSection(content=plan_content, codes=plan_codes, icd10_codes=[])
           )

       def _extract_codes(self, text: str) -> List[str]:
           """Extrai códigos CIAP-2/CID-10 simulados com base em palavras-chave."""
           found_codes = set()
           text_lower = text.lower()
           for keyword, codes in self._CODE_MAP.items():
               if keyword in text_lower:
                   found_codes.update(codes)
           return list(found_codes)

       def _generate_with_ai(self, *args, **kwargs) -> SoapDraft:
           """Placeholder para integração com LLM. Retorna estrutura padrão para testes."""
           # Em produção, aqui seria: return self.ai_client.generate_soap(*args, **kwargs)
           raise NotImplementedError("Integração com IA não configurada. Use use_ai=False para teste determinístico.")
   ```

   This looks solid. It uses Pydantic v2, strict typing, follows SUS/APS standards, and is testable. Now I need to create the pytest test file to satisfy "cobertura de testes automatizados com pytest".

4.  **Design Tests (`test_soap_assistant.py`):**
   - Test Pydantic validation (CNS, CPF, empty content).
   - Test deterministic generation.
   - Test code extraction.
   - Test AI client placeholder behavior.
   - Use `pytest`, `pytest-asyncio` (if needed, but not here), `pydantic`.
   - Ensure full coverage.

   Let's draft the tests:
   ```python
   # Arquivo: backend/app/services/test_soap_assistant.py
   import pytest
   from pydantic import ValidationError
   from backend.app.services.soap_assistant import SoapAssistantService, SoapDraft, SoapSection

   class TestSoapSection:
       def test_valid_content(self):
           section = SoapSection(content="Test content", codes=["A01"])
           assert section.content == "Test content"
           assert section.codes == ["A01"]

       def test_empty_content_raises(self):
           with pytest.raises(ValidationError, match="O conteúdo da seção não pode estar vazio"):
               SoapSection(content="  ")

   class TestSoapDraft:
       def test_valid_draft(self):
           draft = SoapDraft(
               patient_cns="123456789012345",
               patient_cpf="12345678901",
               subjective=SoapSection(content="S"),
               objective=SoapSection(content="O"),
               assessment=SoapSection(content="A"),
               plan=SoapSection(content="P")
           )
           assert draft.patient_cns == "123456789012345"
           assert draft.generated_at is not None

       def test_invalid_cns(self):
           with pytest.raises(ValidationError, match="CNS inválido"):
               SoapDraft(
                   patient_cns="123",
                   patient_cpf="12345678901",
                   subjective=SoapSection(content="S"),
                   objective=SoapSection(content="O"),
                   assessment=SoapSection(content="A"),
                   plan=SoapSection(content="P")
               )

       def test_invalid_cpf(self):
           with pytest.raises(ValidationError, match="CPF inválido"):
               SoapDraft(
                   patient_cns="123456789012345",
                   patient_cpf="123",
                   subjective=SoapSection(content="S"),
                   objective=SoapSection(content="O"),
                   assessment=SoapSection(content="A"),
                   plan=SoapSection(content="P")
               )

   class TestSoapAssistantService:
       def setup_method(self):
           self.service = SoapAssistantService()

       def test_generate_deterministic(self):
           draft = self.service.generate_draft(
               patient_cns="123456789012345",
               patient_cpf="12345678901",
               subjective_input="Paciente relata dor de cabeça e febre.",
               objective_data="PA 120x80, FC 80, Temp 38.5°C.",
               historical_context="Hipertensão, Diabetes."
           )
           assert draft.patient_cns == "123456789012345"
           assert "dor" in draft.subjective.content.lower()
           assert "febre" in draft.subjective.content.lower()
           assert len(draft.subjective.codes) > 0
           assert "R51" in draft.subjective.codes
           assert "R50" in draft.subjective.codes

       def test_extract_codes_mapping(self):
           codes = self.service._extract_codes("Paciente com tosse e fadiga.")
           assert "R05" in codes
           assert "R53" in codes

       def test_generate_with_ai_raises(self):
           with pytest.raises(NotImplementedError, match="Integração com IA não configurada"):
               self.service.generate_draft(
                   patient_cns="123456789012345",
                   patient_cpf="12345678901",
                   subjective_input="Test",
                   objective_data="Test",
                   historical_context="