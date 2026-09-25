Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/convenios_repo.py` for the MedIA project.
   - **Domain:** Health insurance (convênios), TISS guides (TISS 4.01), Financial receipts (private billing).
   - **Architecture/Constraints:**
     - Python 3.12, strict typing, Pydantic v2, SQLAlchemy 2.0.
     - Models & queries for: operators/plans, TISS guide history (status: GERADA, ENVIADA, FATURADA, GLOSADA), private receipts control.
     - No SUS/SISAB or IoT code.
     - Production code in `backend/app/`, tests in `backend/tests/`.
     - Preserve 100% test suite (green).
     - Provide complete, executable code.
     - Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **Models Needed:**
     - `Operadora` (Health Insurance Operator)
     - `PlanoSaude` (Health Insurance Plan)
     - `GuiaTISS` (TISS Guide) with status enum
     - `ReciboParticular` (Private Receipt)
   - **Queries/Repository Methods:**
     - CRUD for operators/plans
     - Guide history/status tracking
     - Receipt control
   - **Tech Stack:** SQLAlchemy 2.0 (declarative, async/sync? I'll assume sync for simplicity unless specified, but I'll use `sqlalchemy.orm` with `Mapped` and `mapped_column` for modern SQLAlchemy 2.0 style), Pydantic v2 for schemas, Python 3.12 type hints.
   - **Structure:** The file should contain models, enums, and repository functions/classes. Since it's a repository file, I'll structure it with SQLAlchemy models and a repository class/function set.

3.  **Design Models (SQLAlchemy 2.0 style):**
   - Use `sqlalchemy.orm.Mapped`, `mapped_column`, `MappedAsDataclass` or standard declarative. I'll stick to standard declarative with `__tablename__` and `mapped_column` for clarity.
   - Enums: `GuiaStatus` (GERADA, ENVIADA, FATURADA, GLOSADA)
   - Relationships: Operadora -> Planos, Plano -> Guias, Guia -> Recibos (or direct to Plano/Paciente? I'll keep it simple: Guia links to Plano and has receipts).
   - Let's define:
     - `Operadora`: id, nome, cns (ANS code), cnpj, ativo
     - `PlanoSaude`: id, operadora_id, nome, codigo_ans, tipo (AMB, HOSP, etc.), ativo
     - `GuiaTISS`: id, plano_id, paciente_cpf, numero_guias, status, data_emissao, data_envio, data_faturamento, data_glosa, xml_tiss, json_tiss, ativo
     - `ReciboParticular`: id, guia_id, valor, descricao, data_emissao, pdf_path, ativo

   Wait, TISS 4.01 has specific fields, but I'll keep it practical for the repository layer. I'll add necessary columns for the domain.

4.  **Design Repository:**
   - Need async or sync? I'll use sync for simplicity but structure it to be easily adaptable. Actually, modern FastAPI uses async, but SQLAlchemy 2.0 recommends `AsyncSession` for async. I'll provide sync for broader compatibility unless specified, but I'll stick to sync with `Session` for simplicity, or explicitly use `AsyncSession` if needed. I'll go with sync `Session` but note it's easily adaptable. Actually, I'll use `sqlalchemy.orm.Session` as it's standard.
   - Repository class `ConveniosRepository` with methods:
     - `criar_operadora`, `atualizar_operadora`, `listar_operadoras`
     - `criar_plano`, `listar_planos_por_operadora`
     - `criar_guia_tiss`, `atualizar_status_guia`, `listar_guias_por_status`, `listar_historico_guias`
     - `criar_recibo_particular`, `listar_recibos_por_guia`, `atualizar_recibo`
   - I'll use Pydantic v2 schemas for input/output validation within the repository or assume they're passed as dicts/models. I'll define Pydantic models at the top of the file for clarity.

5.  **Draft Code (Mental Refinement):**
   ```python
   # Arquivo: backend/app/repositories/convenios_repo.py
   from __future__ import annotations
   from datetime import datetime
   from enum import Enum
   from typing import Optional, List
   from pydantic import BaseModel, Field, ConfigDict
   from sqlalchemy import String, Text, Numeric, DateTime, Boolean, ForeignKey, Enum as SAEnum, func
   from sqlalchemy.orm import Mapped, mapped_column, relationship, Session, DeclarativeBase
   import uuid

   class Base(DeclarativeBase):
       pass

   class GuiaStatus(str, Enum):
       GERADA = "GERADA"
       ENVIADA = "ENVIADA"
       FATURADA = "FATURADA"
       GLOSADA = "GLOSADA"

   # Pydantic Schemas
   class OperadoraCreate(BaseModel):
       nome: str = Field(..., min_length=2, max_length=100)
       cns: str = Field(..., pattern=r"^\d{15}$")
       cnpj: str = Field(..., pattern=r"^\d{14}$")

   class PlanoCreate(BaseModel):
       nome: str
       codigo_ans: str
       tipo: str = "AMB"

   class GuiaTISSCreate(BaseModel):
       plano_id: uuid.UUID
       paciente_cpf: str
       numero_guias: int = 1
       xml_tiss: Optional[str] = None
       json_tiss: Optional[str] = None

   class ReciboParticularCreate(BaseModel):
       guia_id: uuid.UUID
       valor: float = Field(..., gt=0)
       descricao: str
       pdf_path: Optional[str] = None

   # SQLAlchemy Models
   class OperadoraModel(Base):
       __tablename__ = "operadoras"
       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       nome: Mapped[str] = mapped_column(String(100), unique=True)
       cns: Mapped[str] = mapped_column(String(15), unique=True)
       cnpj: Mapped[str] = mapped_column(String(14), unique=True)
       ativo: Mapped[bool] = mapped_column(Boolean, default=True)
       planos: Mapped[List["PlanoSaudeModel"]] = relationship(back_populates="operadora", lazy="selectin")

   class PlanoSaudeModel(Base):
       __tablename__ = "planos_saude"
       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       operadora_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("operadoras.id"))
       nome: Mapped[str] = mapped_column(String(100))
       codigo_ans: Mapped[str] = mapped_column(String(20), unique=True)
       tipo: Mapped[str] = mapped_column(String(10))
       ativo: Mapped[bool] = mapped_column(Boolean, default=True)
       operadora: Mapped["OperadoraModel"] = relationship(back_populates="planos")
       guias: Mapped[List["GuiaTISSModel"]] = relationship(back_populates="plano")

   class GuiaTISSModel(Base):
       __tablename__ = "guias_tiss"
       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       plano_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("planos_saude.id"))
       paciente_cpf: Mapped[str] = mapped_column(String(14))
       numero_guias: Mapped[int] = mapped_column(default=1)
       status: Mapped[GuiaStatus] = mapped_column(SAEnum(GuiaStatus, name="guia_status_enum"), default=GuiaStatus.GERADA)
       data_emissao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       data_envio: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
       data_faturamento: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
       data_glosa: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
       xml_tiss: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       json_tiss: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       ativo: Mapped[bool] = mapped_column(Boolean, default=True)
       plano: Mapped["PlanoSaudeModel"] = relationship(back_populates="guias")
       recibos: Mapped[List["ReciboParticularModel"]] = relationship(back_populates="guia")

   class ReciboParticularModel(Base):
       __tablename__ = "recibos_particulares"
       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       guia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("guias_tiss.id"))
       valor: Mapped[float] = mapped_column(Numeric(10, 2))
       descricao: Mapped[str] = mapped_column(String(255))
       data_emissao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
       ativo: Mapped[bool] = mapped_column(Boolean, default=True)
       guia: Mapped["GuiaTISSModel"] = relationship(back_populates="recibos")

   # Repository
   class ConveniosRepository:
       def __init__(self, session: Session):
           self.session = session

       # Operadoras
       def criar_operadora(self, data: OperadoraCreate) -> OperadoraModel:
           op = OperadoraModel(**data.model_dump())
           self.session.add(op)
           self.session.flush()
           return op

       def listar_operadoras(self, ativo: Optional[bool] = None) -> List[OperadoraModel]:
           query = self.session.query(OperadoraModel)
           if ativo is not None:
               query = query.filter(OperadoraModel.ativo == ativo)
           return query.all()

       # Planos
       def criar_plano(self, data: PlanoCreate, operadora_id: uuid.UUID) -> PlanoSaudeModel:
           plano = PlanoSaudeModel(**data.model_dump(), operadora_id=operadora_id)
           self.session.add(plano)
           self.session.flush()
           return plano

       def listar_planos_por_operadora(self, operadora_id: uuid.UUID) -> List[PlanoSaudeModel]:
           return self.session.query(PlanoSaudeModel).filter(
               PlanoSaudeModel.operadora_id == operadora_id,
               PlanoSaudeModel.ativo == True
           ).all()

       # Guias TISS
       def criar_guia(self, data: GuiaTISSCreate) -> GuiaTISSModel:
           guia = GuiaTISSModel(**data.model_dump())
           self.session.add(guia)
           self.session.flush()
           return guia

       def atualizar_status_guia(self, guia_id: uuid.UUID, novo_status: GuiaStatus) -> Optional[GuiaTISSModel]:
           guia = self.session.get(GuiaTISSModel, guia_id)
           if not guia:
               return None
           guia.status = novo_status
           if novo_status == GuiaStatus.ENVIADA:
               guia.data_envio = datetime.utcnow()
           elif novo_status == GuiaStatus.FATURADA:
               guia.data_faturamento = datetime.utcnow()
           elif novo_status == GuiaStatus.GLOSADA:
               guia.data_glosa = datetime.utcnow()
           self.session.flush()
           return guia

       def listar_guias_por_status(self, status: GuiaStatus) -> List[GuiaTISSModel]:
           return self.session.query(GuiaTISSModel).filter(
               GuiaTISSModel.status == status,
               GuiaTISSModel.ativo == True
           ).all()

       def historico_guias(self, plano_id: Optional[uuid.UUID] = None, paciente_cpf: Optional[str] = None) -> List[GuiaTISSModel]:
           query = self.session.query(GuiaTISSModel).filter(GuiaTISSModel.ativo == True)
           if plano_id:
               query = query.filter(GuiaTISSModel.plano_id == plano_id)
           if paciente_cpf:
               query = query.filter(GuiaTISSModel.paciente_cpf == paciente_cpf)
           return query.order_by(GuiaTISSModel.data_emissao.desc()).all()

       # Recibos
       def criar_recibo(self, data: ReciboParticularCreate) -> ReciboParticularModel:
           recibo = ReciboParticularModel(**data.model_dump())
           self.session.add(recibo)
           self.session.flush()
           return recibo

       def listar_recibos_por_guia(self, guia_id: uuid.UUID) -> List[ReciboParticularModel]:
           return self.session.query(ReciboParticularModel).filter(
               ReciboParticularModel.guia_id == guia_id,
               ReciboParticularModel.ativo == True
           ).all()

       def atualizar_recibo(self, recibo_id: uuid.UUID, valor: Optional[float] = None, descricao: Optional[str] = None, pdf_path: Optional[str] = None) -> Optional[ReciboParticularModel]:
           recibo = self.session.get(ReciboParticularModel, recibo_id)
           if not recibo:
               return None
           if valor is not None: recibo.valor = valor
           if descricao is not None: recibo.descricao = descricao
           if pdf_path is not None: recibo.pdf_path = pdf_path
           self.session.flush()
           return recibo
   ```

6.  **Check Constraints & Requirements:**
   - *Python 3.12, strict typing, Pydantic v2, SQLAlchemy 2.0*: Used `from __future__ import annotations`, `Mapped`, `mapped_column`, Pydantic v2 `BaseModel`, `Field`, `model_dump()`. Type hints are explicit.
   - *Models & Queries*: Covers operadoras, planos, guias TISS (with status enum), recibos particulares.
   - *TISS 4.01 / DMED*: Added XML/JSON TISS fields, status tracking, CPF for patient, ANS codes.
   - *No SUS/SISAB/IoT*: Checked. Not included.
   - *Production code in backend/app/*: Path matches.
   - *Preserve 100% test suite*: I should ensure the code is testable and doesn't break existing patterns. I'll add a `__init__.py` stub if needed, but the prompt just asks for the file. I'll make sure it's self-contained and follows standard patterns.
   - *Complete & Executable*: I'll add necessary imports and ensure it runs without external dependencies beyond standard ones. I'll also add a `__init__.py` for the repository package if needed, but the prompt asks specifically for `convenios_repo.py`.
   - *Architecture*: I'll structure it cleanly. I should also consider that SQLAlchemy 2.0 recommends `select()` for queries, but `session.query()` is still valid. I'll switch to `select()` for modern SQLAlchemy 2.0 compliance.
   - Let's refactor queries to use `select()` and `session.scalars()` for strict SQLAlchemy 2.0 style.

   Refactoring queries to SQLAlchemy 2.0 style:
   ```python
   from sqlalchemy import select
   # ...
   def listar_operadoras(self, ativo: Optional[bool] = None) -> List[OperadoraModel]:
       stmt = select(OperadoraModel)
       if ativo is not None:
           stmt = stmt.where(OperadoraModel.ativo == ativo)
       return self.session.scalars(stmt).all()
   ```
   This is better.

   Also, Pydantic v2 uses `model_dump()` instead of `dict()`. I used that.
   I'll add `__init__.py` for the repo package to make it importable.
   I'll ensure all type hints are correct.
   I'll add docstrings and comments for clarity.
   I'll make sure the file path comment is at the top.

   Let's draft the final version carefully.

   Structure:
   - Imports
   - Enums
   - Pydantic Schemas
   - SQLAlchemy Models
   - Repository Class
   - All in one file as requested.

   Check TISS 4.01 specifics: The prompt mentions "histórico de guias TISS emitidas (status: GERADA, ENVIADA, FATURADA, GLOSADA)". I've covered that.
   Check DMED/Receita Federal: Private receipts control. Covered.
   Check Python 3.12: `from __future__ import annotations` ensures forward references work without quotes.
   Check SQLAlchemy 2.0: `Mapped`, `mapped_column`, `select()`, `session.scalars()`.
   Check Pydantic v2: `BaseModel`, `Field`, `model_dump()`.
   Check Architecture: Clean, no external framework coupling, just SQLAlchemy + Pydantic.

   One thing: The prompt says "Preservar 100% da suíte de testes verde." This implies I should be careful not to break existing interfaces. Since I'm creating a new file, I'll make the API explicit and stable. I'll also add a `__init__.py` for the repository package to ensure imports work.

   I'll write the code now. I'll make sure it's production-ready, strictly typed, and follows all constraints.

   Self-Correction/Refinement during thought:
   - SQLAlchemy