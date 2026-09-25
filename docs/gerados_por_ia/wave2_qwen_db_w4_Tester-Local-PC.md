Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/services/fila_teleatendimento.py` for a virtual waiting queue for teleconsultations in Primary Care (APS).
   - **Key Features:**
     - Risk classification (simplified Manchester: Red, Yellow, Green, Blue)
     - Dynamic ordering by clinical priority and arrival time
     - Notification of the next patient call
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
     - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
     - Full compliance and automated test coverage with pytest
   - **Output Requirement:** Provide complete, executable code. Specify file paths in code blocks.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/services/fila_teleatendimento.py`
   - **Core Logic:**
     - Queue management (add, remove, get next)
     - Priority classification (Red, Yellow, Green, Blue)
     - Sorting: Priority first, then arrival time
     - Notification mechanism (mock/simulated for now, but structured)
   - **Data Models (Pydantic v2):**
     - Patient info: CNS, CPF, name, etc.
     - Queue entry: patient, priority, arrival_time, status
     - Classification logic
   - **Database (SQLAlchemy 2.0):**
     - Need models for `TeleconsultationQueue`, `Patient`, etc. (but the task focuses on the service file, so I'll define models inline or import them, but since it's a single file request, I'll define necessary models/types within or assume standard structure. I'll create a self-contained service with Pydantic models and SQLAlchemy ORM models defined for clarity, or just focus on the service logic with type hints and Pydantic models as requested. I'll include SQLAlchemy models in the same file for completeness, or structure it so it's clear.)
   - **Testing (pytest):**
     - Need a test file `tests/test_fila_teleatendimento.py`
     - Cover classification, ordering, queue operations, notifications.

3.  **Design the Service (`fila_teleatendimento.py`):**
   - **Enums:** `Prioridade` (VERMELHO, AMARELO, VERDE, AZUL)
   - **Pydantic Models:**
     - `Paciente`: cns, cpf, nome, data_nascimento
     - `EntradaFila`: id, paciente, prioridade, horario_chegada, status, notificado
   - **Service Class:** `FilaTeleatendimentoService`
     - `__init__`: Initialize queue (in-memory list for simplicity, but structured for DB integration)
     - `adicionar_paciente`: Validate, classify, add to queue
     - `classificar_risco`: Map clinical data to priority
     - `ordenar_fila`: Sort by priority (Red > Yellow > Green > Blue), then by arrival time
     - `chamar_proximo`: Get next, mark as notified, trigger notification
     - `notificar_paciente`: Mock/async notification
   - **SQLAlchemy Models:** Define `TeleconsultaFila` and `Paciente` models for DB integration context.
   - **Type Hints:** Strict Python 3.12 typing.
   - **SUS/APS Standards:** Include CNS, CPF, CIAP-2/CID-10 fields in models, SOAP method reference.

   Let's draft the code structure mentally:
   ```python
   from __future__ import annotations
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, List
   from pydantic import BaseModel, Field, ConfigDict
   from sqlalchemy import Column, String, DateTime, Enum as SAEnum, ForeignKey, Integer, Boolean
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
   import asyncio

   class Prioridade(str, Enum):
       VERMELHO = "VERMELHO"
       AMARELO = "AMARELO"
       VERDE = "VERDE"
       AZUL = "AZUL"

   PRIORIDADE_ORDEM = {Prioridade.VERMELHO: 0, Prioridade.AMARELO: 1, Prioridade.VERDE: 2, Prioridade.AZUL: 3}

   class Paciente(BaseModel):
       cns: str = Field(..., pattern=r"^\d{15}$")
       cpf: str = Field(..., pattern=r"^\d{11}$")
       nome: str
       data_nascimento: datetime

   class EntradaFila(BaseModel):
       id: str = Field(default_factory=lambda: str(uuid.uuid4()))
       paciente: Paciente
       prioridade: Prioridade
       horario_chegada: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
       status: str = "AGUARDANDO"
       notificado: bool = False

   class FilaTeleatendimentoService:
       def __init__(self):
           self.fila: List[EntradaFila] = []

       def adicionar_paciente(self, paciente: Paciente, dados_clinicos: dict) -> EntradaFila:
           prioridade = self.classificar_risco(dados_clinicos)
           entrada = EntradaFila(paciente=paciente, prioridade=prioridade)
           self.fila.append(entrada)
           self.ordenar_fila()
           return entrada

       def classificar_risco(self, dados_clinicos: dict) -> Prioridade:
           # Simplified Manchester logic
           if dados_clinicos.get("sintomas_vitais", {}).get("fc") is not None and dados_clinicos["sintomas_vitais"]["fc"] > 120:
               return Prioridade.VERMELHO
           if dados_clinicos.get("dor") in ["MODERADA", "INTENSA"]:
               return Prioridade.AMARELO
           if dados_clinicos.get("sintomas_vitais", {}).get("temp") is not None and dados_clinicos["sintomas_vitais"]["temp"] > 38.5:
               return Prioridade.VERDE
           return Prioridade.AZUL

       def ordenar_fila(self):
           self.fila.sort(key=lambda x: (PRIORIDADE_ORDEM[x.prioridade], x.horario_chegada))

       def chamar_proximo(self) -> Optional[EntradaFila]:
           if not self.fila:
               return None
           proximo = self.fila[0]
           proximo.status = "CHAMADO"
           proximo.notificado = True
           self.notificar_paciente(proximo)
           return proximo

       async def notificar_paciente(self, entrada: EntradaFila):
           # Mock notification
           print(f"Notificação enviada para {entrada.paciente.cpf} - {entrada.paciente.nome}")
           await asyncio.sleep(0.1)
   ```

   Wait, I need to align with SQLAlchemy 2.0 and Pydantic v2 strictly. I should define the ORM models properly. Also, the service should ideally interact with a DB session, but for a single file, I'll keep it in-memory but structured for DB, or add a `session` parameter. The prompt says "código completo e executável", so I'll make it self-contained but production-ready in structure.

   Let's refine the service to be more robust and aligned with the guidelines:
   - Use `datetime.now(timezone.utc)` consistently.
   - Add CIAP-2/CID-10 fields to clinical data.
   - Add SOAP method reference.
   - Ensure strict typing.
   - Add SQLAlchemy models for completeness.
   - Add pytest tests.

   I'll structure the output with two files:
   1. `backend/app/services/fila_teleatendimento.py`
   2. `tests/test_fila_teleatendimento.py`

   Let's draft the service file carefully.

   **Service File Structure:**
   ```python
   # Arquivo: backend/app/services/fila_teleatendimento.py
   from __future__ import annotations
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from sqlalchemy import Column, String, DateTime, Enum as SAEnum, Boolean, Float, Text
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
   import asyncio

   # --- Enums & Constants ---
   class Prioridade(str, Enum):
       VERMELHO = "VERMELHO"
       AMARELO = "AMARELO"
       VERDE = "VERDE"
       AZUL = "AZUL"

   PRIORIDADE_ORDEM: Dict[Prioridade, int] = {
       Prioridade.VERMELHO: 0,
       Prioridade.AMARELO: 1,
       Prioridade.VERDE: 2,
       Prioridade.AZUL: 3
   }

   # --- Pydantic Models (DTOs) ---
   class PacienteDTO(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True)
       cns: str = Field(..., pattern=r"^\d{15}$", description="CNS do paciente")
       cpf: str = Field(..., pattern=r"^\d{11}$", description="CPF do paciente")
       nome: str = Field(..., min_length=1)
       data_nascimento: datetime

   class DadosClinicosDTO(BaseModel):
       ciap2: Optional[str] = None
       cid10: str = Field(..., pattern=r"^[A-Z]\d{2}$")
       metodo_suspeito: str = "SOAP"
       sintomas_vitais: Dict[str, Any] = {}
       dor: Optional[str] = None

   class EntradaFilaDTO(BaseModel):
       id: str = Field(default_factory=lambda: str(uuid.uuid4()))
       paciente: PacienteDTO
       prioridade: Prioridade
       horario_chegada: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
       status: str = "AGUARDANDO"
       notificado: bool = False

   # --- SQLAlchemy Models ---
   class Base(DeclarativeBase):
       pass

   class PacienteORM(Base):
       __tablename__ = "pacientes"
       cns: Mapped[str] = mapped_column(String(15), primary_key=True)
       cpf: Mapped[str] = mapped_column(String(11), unique=True)
       nome: Mapped[str]
       data_nascimento: Mapped[datetime]

   class FilaTeleconsultaORM(Base):
       __tablename__ = "fila_teleconsulta"
       id: Mapped[str] = mapped_column(String(36), primary_key=True)
       paciente_cns: Mapped[str] = mapped_column(String(15), ForeignKey("pacientes.cns"))
       prioridade: Mapped[Prioridade] = mapped_column(SAEnum(Prioridade), nullable=False)
       horario_chegada: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
       status: Mapped[str] = mapped_column(String(20), default="AGUARDANDO")
       notificado: Mapped[bool] = mapped_column(Boolean, default=False)

   # --- Service ---
   class FilaTeleatendimentoService:
       def __init__(self):
           self.fila: List[EntradaFilaDTO] = []

       def adicionar_paciente(self, paciente: PacienteDTO, dados_clinicos: DadosClinicosDTO) -> EntradaFilaDTO:
           prioridade = self.classificar_risco(dados_clinicos)
           entrada = EntradaFilaDTO(paciente=paciente, prioridade=prioridade)
           self.fila.append(entrada)
           self.ordenar_fila()
           return entrada

       def classificar_risco(self, dados_clinicos: DadosClinicosDTO) -> Prioridade:
           # Protocolo de Manchester Simplificado
           vitais = dados_clinicos.sintomas_vitais
           if vitais.get("fc") is not None and vitais["fc"] > 120:
               return Prioridade.VERMELHO
           if dados_clinicos.dor in ("MODERADA", "INTENSA"):
               return Prioridade.AMARELO
           if vitais.get("temp") is not None and vitais["temp"] > 38.5:
               return Prioridade.VERDE
           return Prioridade.AZUL

       def ordenar_fila(self) -> None:
           self.fila.sort(key=lambda x: (PRIORIDADE_ORDEM[x.prioridade], x.horario_chegada))

       def chamar_proximo(self) -> Optional[EntradaFilaDTO]:
           if not self.fila:
               return None
           proximo = self.fila.pop(0)
           proximo.status = "CHAMADO"
           proximo.notificado = True
           asyncio.create_task(self.notificar_paciente(proximo))
           return proximo

       async def notificar_paciente(self, entrada: EntradaFilaDTO) -> None:
           # Simulação de notificação (SMS/Push/Email)
           msg = f"Chamado {entrada.id} - Paciente {entrada.paciente.nome} (CPF: {entrada.paciente.cpf})"
           print(f"[NOTIFICAÇÃO] {msg}")
           await asyncio.sleep(0.01)
   ```

   Wait, `asyncio.create_task` inside a sync method might cause issues if no event loop is running. I'll make `chamar_proximo` sync but handle notification synchronously for simplicity in testing, or keep it async but note it. Actually, for testing, it's better to keep notification sync or mock it. I'll change `chamar_proximo` to sync and call `self.notificar_paciente_sync` or just keep it simple. The prompt says "Notificação de chamada do próximo paciente", I'll implement it as a sync method for reliability in tests, or use `asyncio.run` in tests. I'll stick to sync for the service method to avoid event loop complexity in a single file, but I'll add an async version if needed. Actually, I'll make `notificar_paciente` sync for simplicity, or keep it async but handle it properly. Let's make it sync to avoid `RuntimeError: no running event loop` in tests.

   Revised `chamar_proximo`:
   ```python
       def chamar_proximo(self) -> Optional[EntradaFilaDTO]:
           if not self.fila:
               return None
           proximo = self.fila.pop(0)
           proximo.status = "CHAMADO"
           proximo.notificado = True
           self.notificar_paciente(proximo)
           return proximo

       def notificar_paciente(self, entrada: EntradaFilaDTO) -> None:
           print(f"[NOTIFICAÇÃO] Paciente {entrada.paciente.nome} (CPF: {entrada.paciente.cpf}) chamado para teleconsulta.")
   ```

   Now, the test file. It needs to cover:
   - Classification logic
   - Queue ordering
   - Adding patients
   - Calling next
   - Notification
   - Edge cases (empty queue, same priority, same time)
   - Use pytest, strict typing, mock if needed.

   **Test File Structure:**
   ```python
   # Arquivo: tests/test_fila_teleatendimento.py
   import pytest
   from datetime import datetime, timezone
   from backend.app.services.fila_teleatendimento import (
       FilaTeleatendimentoService,
       PacienteDTO,
       DadosClinicosDTO,
       EntradaFilaDTO,
       Prioridade
   )

   @pytest.fixture
   def service():
       return FilaTeleatendimentoService()

   @pytest.fixture
   def paciente_base():
       return PacienteDTO(
           cns="123456789012345",
           cpf="12345678901",
           nome="João da Silva",
           data_nascimento=datetime(1980, 5, 15, tzinfo=timezone.utc)
       )

   @pytest.fixture
   def dados_clinicos_vermelho():
       return DadosClinicosDTO(
           cid10="J06.9",
           ciap2="R11",
           sintomas_vitais={"fc": 130},
           dor=None
       )

   @pytest.fixture
   def dados_clinicos_amarelo():
       return DadosClinicosDTO(
           cid10="M54.5",
           ciap2="R12",
           sintomas_vitais={},
           dor="INTENSA"
       )

   @pytest.fixture
   def dados_clinicos_verde():
       return DadosClinicosDTO(
           cid10="R50.9",
           ciap2="R13",
           sintomas_vitais={"temp": 39.0},
           dor=None
       )

   @pytest.fixture
   def dados_clinicos_azul():
       return DadosClinicosDTO(
           cid10="Z00.00",
           ciap2="R14",
           sintomas_vitais={},
           dor=None
       )

   def test_classificacao_risco(service, paciente_base):
       assert service.classificar_risco(DadosClinicosDTO(cid10="J06.9", sintomas_vitais={"fc": 130})) == Prioridade.VERMELHO
       assert service.classificar_risco(DadosClinicosDTO(cid10="M54.5", dor="INTENSA")) == Prioridade.AMARELO
       assert service.classificar_risco(DadosClinicosDTO(cid10="R50.9", sintomas_vitais={"temp": 39.0})) == Prioridade.VERDE
       assert service.classificar_risco(DadosClinicosDTO(cid10="Z00.00")) == Prioridade.AZUL

   def test_adicionar_e_ordenar_fila(service, paciente_base):
