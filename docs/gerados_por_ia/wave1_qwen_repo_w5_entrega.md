Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create a SQLAlchemy repository file `backend/app/repositories/telemedicina_repo.py` for a Telemedicine project (MedIA).
   - **Class:** `TelemedicinaRepository`
   - **Methods:**
     - `criar_agendamento(db, dados)`
     - `buscar_por_codigo_sala(db, codigo)`
     - `atualizar_status(db, teleconsulta_id, novo_status)`
     - `registrar_evolucao_soap(db, teleconsulta_id, dados_soap)`
   - **Requirements:**
     - Python 3.12 strict typing
     - Pydantic v2 for data validation (implied by "tipagem estrita com Pydantic v2")
     - SQLAlchemy 2.0 compatibility
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification
     - Exception handling
     - Full test coverage with pytest (I should provide the repo code, and optionally mention/test structure, but the prompt says "Forneça o código completo e executável" for each file. I'll focus on the repo file as requested, but I'll make sure it's complete and ready for testing.)
     - File path: `backend/app/repositories/telemedicina_repo.py`

2.  **Analyze Requirements & Constraints:**
   - **Python 3.12:** Use modern type hints, `from __future__ import annotations` if needed, but standard `typing` module is fine.
   - **Pydantic v2:** Use `pydantic` for data models. The `dados` and `dados_soap` parameters should be validated Pydantic models.
   - **SQLAlchemy 2.0:** Use `Session` from `sqlalchemy.orm`, `select`, `update`, `delete`, etc. Async isn't specified, so I'll stick to sync for simplicity unless implied. I'll use `sqlalchemy.orm.Session`.
   - **SUS/APS Standards:** The repository should handle fields like `codigo_sala`, `status`, `cid10`, `ciap2`, `cns`, `cpf`, `evolucao_soap`. I'll define appropriate Pydantic models for input data.
   - **Exception Handling:** Use custom exceptions or standard ones (e.g., `ValueError`, `sqlalchemy.exc.SQLAlchemyError`). I'll create a specific `TelemedicinaRepositoryError` or use standard ones with clear messages.
   - **Testing:** The prompt says "Manter conformidade total e cobertura de testes automatizados com pytest." I should provide the repository code that is testable, and maybe include a brief test file or ensure the code is structured for easy mocking. Since the prompt asks for the repository file, I'll focus on that, but I'll make sure it's production-ready and testable.

3.  **Design the Repository:**
   - **Imports:** `sqlalchemy`, `sqlalchemy.orm`, `pydantic`, `typing`, `datetime`, `uuid`, etc.
   - **Pydantic Models:**
     - `AgendamentoCreate` (for `criar_agendamento`)
     - `EvolucaoSOAP` (for `registrar_evolucao_soap`)
   - **Repository Class:** `TelemedicinaRepository`
   - **Methods:**
     - `criar_agendamento(db: Session, dados: AgendamentoCreate) -> Any` (or return a dict/model)
     - `buscar_por_codigo_sala(db: Session, codigo: str) -> Any`
     - `atualizar_status(db: Session, teleconsulta_id: str, novo_status: str) -> bool`
     - `registrar_evolucao_soap(db: Session, teleconsulta_id: str, dados_soap: EvolucaoSOAP) -> bool`
   - **SQLAlchemy 2.0 Patterns:** Use `Session.execute()`, `select()`, `update()`, etc.
   - **SUS/APS Fields:** `cns`, `cpf`, `cid10`, `ciap2`, `codigo_sala`, `status`, `evolucao_soap` (JSON/text), `data_agendamento`, etc.

   Let's draft the Pydantic models first:
   ```python
   from pydantic import BaseModel, Field, field_validator
   from typing import Optional
   from datetime import datetime

   class AgendamentoCreate(BaseModel):
       paciente_cns: str = Field(..., min_length=15, max_length=15)
       paciente_cpf: str = Field(..., min_length=11, max_length=14)
       medico_cns: str = Field(..., min_length=15, max_length=15)
       codigo_sala: str
       data_agendamento: datetime
       cid10: Optional[str] = None
       ciap2: Optional[str] = None
       status: str = "AGENDADO"

       @field_validator('paciente_cns', 'medico_cns')
       @classmethod
       def validate_cns(cls, v):
           if not v.isdigit() or len(v) != 15:
               raise ValueError('CNS deve ter 15 dígitos numéricos')
           return v

   class EvolucaoSOAP(BaseModel):
       teleconsulta_id: str
       subjetiva: str
       objetiva: str
       avaliativa: str
       plano: str
       cid10: Optional[str] = None
       ciap2: Optional[str] = None
       data_registro: datetime = Field(default_factory=datetime.now)
   ```

   Now, the Repository class:
   ```python
   from sqlalchemy.orm import Session
   from sqlalchemy import select, update
   from sqlalchemy.exc import SQLAlchemyError
   from typing import Any, Optional
   import logging

   logger = logging.getLogger(__name__)

   class TelemedicinaRepositoryError(Exception):
       pass

   class TelemedicinaRepository:
       def __init__(self):
           pass

       def criar_agendamento(self, db: Session, dados: AgendamentoCreate) -> dict[str, Any]:
           try:
               # Simulating model creation. In a real app, we'd map to an ORM model.
               # For this repo, I'll assume we're inserting into a table directly or using an ORM model.
               # Since the prompt asks for a repository with SQLAlchemy methods, I'll write it assuming an ORM model `TeleConsulta` exists,
               # but to keep it self-contained and testable, I'll use SQLAlchemy Core or assume a model is available.
               # Actually, I'll define the method to work with a hypothetical `TeleConsulta` ORM model, but I'll make it clear.
               # Better: I'll write it using SQLAlchemy 2.0 style with a mock/expected ORM model structure, or use Core.
               # Given the prompt, I'll assume standard ORM usage but keep it generic enough.
               # I'll use `db.execute()` with `insert()` for SQLAlchemy 2.0 core, or assume an ORM model.
               # Let's stick to ORM style but use SQLAlchemy 2.0 syntax: `db.execute(select(...))` etc.
               # Actually, I'll write it assuming a `TeleConsulta` model exists, but I'll make the code robust.
               # To be strictly compliant with "métodos SQLAlchemy", I'll use `db.execute()` with `insert`, `select`, `update`.
               pass
           except SQLAlchemyError as e:
               logger.error(f"Erro ao criar agendamento: {e}")
               raise TelemedicinaRepositoryError(f"Falha ao criar agendamento: {e}") from e
   ```

   Wait, the prompt says "contendo uma classe TelemedicinaRepository com métodos SQLAlchemy". It doesn't specify ORM vs Core. I'll use SQLAlchemy 2.0 ORM style with `Session` and assume a model `TeleConsulta` exists, but I'll make it clear. Actually, it's better to write it using SQLAlchemy 2.0 `select`, `update`, `insert` with a hypothetical model, or I can define the model inline for completeness. Since it's a repository, it should interact with an ORM model. I'll assume `TeleConsulta` is the model.

   Let's structure it properly with SQLAlchemy 2.0 patterns:
   - Use `db.execute(select(TeleConsulta).where(...))`
   - Use `db.execute(update(TeleConsulta).where(...).values(...))`
   - Use `db.add()` and `db.commit()` for inserts.

   I'll add the necessary imports and define the repository. I'll also ensure Pydantic v2 validation is used.

   Let's draft the full file:

   ```python
   # Arquivo: backend/app/repositories/telemedicina_repo.py
   from __future__ import annotations

   from datetime import datetime
   from typing import Any, Optional

   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import select, update
   from sqlalchemy.orm import Session
   from sqlalchemy.exc import SQLAlchemyError
   import logging

   logger = logging.getLogger(__name__)

   # --- Pydantic v2 Models para Validação de Entrada ---
   class AgendamentoCreate(BaseModel):
       paciente_cns: str = Field(..., min_length=15, max_length=15)
       paciente_cpf: str = Field(..., min_length=11, max_length=14)
       medico_cns: str = Field(..., min_length=15, max_length=15)
       codigo_sala: str
       data_agendamento: datetime
       cid10: Optional[str] = None
       ciap2: Optional[str] = None
       status: str = "AGENDADO"

       @field_validator('paciente_cns', 'medico_cns')
       @classmethod
       def validar_cns(cls, v: str) -> str:
           if not v.isdigit() or len(v) != 15:
               raise ValueError('CNS deve conter exatamente 15 dígitos numéricos.')
           return v

   class EvolucaoSOAPCreate(BaseModel):
       teleconsulta_id: str
       subjetiva: str
       objetiva: str
       avaliativa: str
       plano: str
       cid10: Optional[str] = None
       ciap2: Optional[str] = None
       data_registro: datetime = Field(default_factory=datetime.now)

   # --- Exceção Personalizada ---
   class TelemedicinaRepositoryError(Exception):
       """Exceção base para erros no repositório de telemedicina."""
       pass

   # --- Repositório ---
   class TelemedicinaRepository:
       """
       Repositório para operações de teleconsulta conforme padrões SUS/APS.
       Utiliza SQLAlchemy 2.0 e Pydantic v2 para validação e tipagem estrita.
       """

       def criar_agendamento(self, db: Session, dados: AgendamentoCreate) -> dict[str, Any]:
           """
           Cria um novo agendamento de teleconsulta.
           """
           try:
               # Assumindo que existe um ORM model `TeleConsulta` mapeado para a tabela
               from app.models.teleconsulta import TeleConsulta  # Import local para evitar circularidade

               novo_agendamento = TeleConsulta(
                   paciente_cns=dados.paciente_cns,
                   paciente_cpf=dados.paciente_cpf,
                   medico_cns=dados.medico_cns,
                   codigo_sala=dados.codigo_sala,
                   data_agendamento=dados.data_agendamento,
                   cid10=dados.cid10,
                   ciap2=dados.ciap2,
                   status=dados.status,
               )
               db.add(novo_agendamento)
               db.flush()
               db.refresh(novo_agendamento)

               logger.info(f"Agendamento criado com sucesso: {novo_agendamento.id}")
               return {
                   "id": str(novo_agendamento.id),
                   "codigo_sala": novo_agendamento.codigo_sala,
                   "status": novo_agendamento.status,
                   "data_agendamento": novo_agendamento.data_agendamento.isoformat(),
               }
           except SQLAlchemyError as e:
               db.rollback()
               logger.error(f"Erro ao criar agendamento: {e}")
               raise TelemedicinaRepositoryError(f"Falha ao criar agendamento: {e}") from e
           except Exception as e:
               db.rollback()
               logger.error(f"Erro inesperado ao criar agendamento: {e}")
               raise TelemedicinaRepositoryError(f"Erro inesperado: {e}") from e

       def buscar_por_codigo_sala(self, db: Session, codigo: str) -> Optional[dict[str, Any]]:
           """
           Busca agendamento pelo código da sala de teleconsulta.
           """
           try:
               from app.models.teleconsulta import TeleConsulta

               stmt = select(TeleConsulta).where(TeleConsulta.codigo_sala == codigo)
               result = db.execute(stmt).scalar_one_or_none()

               if not result:
                   return None

               return {
                   "id": str(result.id),
                   "codigo_sala": result.codigo_sala,
                   "status": result.status,
                   "paciente_cns": result.paciente_cns,
                   "medico_cns": result.medico_cns,
                   "cid10": result.cid10,
                   "ciap2": result.ciap2,
                   "data_agendamento": result.data_agendamento.isoformat() if result.data_agendamento else None,
               }
           except SQLAlchemyError as e:
               logger.error(f"Erro ao buscar por código da sala {codigo}: {e}")
               raise TelemedicinaRepositoryError(f"Falha ao buscar agendamento: {e}") from e

       def atualizar_status(self, db: Session, teleconsulta_id: str, novo_status: str) -> bool:
           """
           Atualiza o status de uma teleconsulta.
           """
           try:
               from app.models.teleconsulta import TeleConsulta

               stmt = (
                   update(TeleConsulta)
                   .where(TeleConsulta.id == teleconsulta_id)
                   .values(status=novo_status)
               )
               result = db.execute(stmt)
               db.commit()

               if result.rowcount == 0:
                   logger.warning(f"Nenhuma teleconsulta encontrada com ID {teleconsulta_id} para atualização de status.")
                   return False

               logger.info(f"Status atualizado para {novo_status} na teleconsulta {teleconsulta_id}")
               return True
           except SQLAlchemyError as e:
               db.rollback()
               logger.error(f"Erro ao atualizar status da teleconsulta {teleconsulta_id}: {e}")
               raise TelemedicinaRepositoryError(f"Falha ao atualizar status: {e}") from e

       def registrar_evolucao_soap(self, db: Session, teleconsulta_id: str, dados_soap: EvolucaoSOAPCreate) -> bool:
           """
           Registra evolução clínica no formato SOAP.
           """
           try:
               from app.models.teleconsulta import TeleConsulta

               stmt = select(TeleConsulta).where(TeleConsulta.id == teleconsulta_id)
               teleconsulta = db.execute(stmt).scalar_one_or_none()

               if not teleconsulta:
                   logger.warning(f"Teleconsulta {teleconsulta_id} não encontrada para registrar evolução.")
                   return False

               # Atualiza campos de evolução e códigos
               teleconsulta.evolucao_subjetiva = dados_soap.subjetiva
               teleconsulta.evolucao_objetiva = dados_soap.objetiva
               teleconsulta.evolucao_avaliativa = dados_soap.avaliativa
               teleconsulta.evolucao_plano = dados_soap.plano
               teleconsulta.cid10 = dados_soap.cid10
               teleconsulta.ciap2 = dados_soap.ciap2
               teleconsulta.data_evolucao = dados_soap.data_registro
               teleconsulta.status = "EM_ANDAMENTO" if teleconsulta.status == "AGENDADO" else teleconsulta.status

               db.flush()
               db.commit()

               logger.info(f"Evolução SOAP registrada para teleconsulta {teleconsulta_id}")
               return True
           except SQLAlchemyError as e:
               db.rollback()
               logger.error(f"Erro ao registrar evolução SOAP para {teleconsulta_id}: {e}")
               raise TelemedicinaRepositoryError(f"Falha ao registrar evolução SOAP: {e}") from e
   ```

4.  **Review & Refine:**
   - **Python 3.12:** Uses modern type hints, `from __future__ import annotations` for forward references, `dict[str, Any]` syntax.
   - **Pydantic v2:** Uses `BaseModel`, `Field`, `field_validator`, `default_factory`. Correct.
   - **SQLAlchemy 2.0:** Uses `select`, `update`, `db.execute()`, `scalar_one_or_none()`, `db.flush()`, `db.commit()`, `db.rollback()`. Correct.
   - **SUS/APS:** Includes `cid10`, `ciap2`, `cns`, `cpf`, `soap` fields. Validates CNS format. Correct.
   - **Exception Handling:** Catches `SQLAlchemyError`, rolls back, logs, raises custom `TelemedicinaRepositoryError`. Correct.
   - **Testability:** The code is structured to be easily mocked. I'll add a note about pytest fixtures/mocking, but the prompt asks for the file. I'll ensure the imports are handled gracefully (using lazy imports or assuming the model exists). To make it fully self-contained and executable, I should either define the model inline or use SQLAlchemy Core. Given it's a repository, it's standard to depend on an ORM model. I'll keep the lazy import but add a comment. Alternatively, I can use SQLAlchemy Core to avoid model dependency, but ORM is more common. I'll stick with ORM but make it clear.
   - **Strict Typing:** All parameters and return types are annotated. `Optional` used where appropriate.
   - **File Path:** `backend/app/repositories/telemedicina_repo.py` as requested.

   One improvement: Instead of lazy imports inside methods (which can cause circular dependency issues in tests), I'll assume the model is available or use a generic approach. Actually, in production, repositories import models. I'll keep it but add a comment. To make it more robust for testing, I'll use `typing.TYPE_CHECKING` or just assume the model exists. I'll leave it as is, it's standard.

   Let's check Py