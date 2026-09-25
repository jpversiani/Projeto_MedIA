Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/convenios_repo.py` for the MedIA project.
   - **Domain:** Health insurance (convenios), TISS guides history (status: GERADA, ENVIADA, FATURADA, GLOSADA), and private receipts control.
   - **Architecture Guidelines:**
     - MedIA focuses on private care and health insurance (TISS ANS 4.01 / DMED Receita Federal).
     - Clinical method: Primary Care / Family Health.
     - No SUS/SISAB or IoT code.
     - Python 3.12, strict typing, Pydantic v2, SQLAlchemy 2.0.
     - Production code in `backend/app/`, tests in `backend/tests/`.
     - Preserve 100% green test suite (implies I should provide tests if needed, but the prompt specifically asks for the repo file. I'll focus on the repo but ensure it's testable and follows best practices. I'll also provide the test file to be safe, as the prompt says "Preservar 100% da suíte de testes verde" and I'm acting as a tester/engineer).
     - Provide complete, executable code. Specify file paths.

2.  **Analyze Requirements for `convenios_repo.py`:**
   - **Models needed:**
     - `Operadora` (Health Insurance Provider)
     - `PlanoSaude` (Health Plan)
     - `GuiaTISS` (TISS Guide) with status enum
     - `ReciboParticular` (Private Receipt)
   - **Relationships:**
     - Operadora -> Planos (1:N)
     - Plano -> Guias (1:N)
     - Guia -> Recibos? Or maybe Recibos are tied to consultations/patients, but the prompt says "controle de recibos particulares". I'll link it to a consultation/patient context, but for simplicity in this repo, I'll link it to a `GuiaTISS` or a `Consulta` model. Since it's a repo file, I'll define the models and the repository class with CRUD operations.
   - **Status Enum for Guias:** GERADA, ENVIADA, FATURADA, GLOSADA
   - **SQLAlchemy 2.0 Style:** Use declarative base, mapped columns, async/sync? The prompt doesn't specify, but modern SQLAlchemy 2.0 often uses async. I'll stick to sync for simplicity unless specified, but I'll make it compatible with both or explicitly use `sqlalchemy.orm` with `Session`. I'll use standard SQLAlchemy 2.0 syntax with `Mapped`, `mapped_column`, etc.
   - **Pydantic v2:** Used for schemas, but the prompt asks for the *repository* file. I'll include Pydantic models/schemas if needed, or just focus on SQLAlchemy models and the repo class. I'll add Pydantic schemas for validation as per guidelines.
   - **Repository Pattern:** Class with methods like `create_operadora`, `get_operadora`, `create_plano`, `get_plano`, `create_guia`, `update_guia_status`, `get_guias_by_status`, `create_recibo`, `get_recibos`, etc.

3.  **Design Models (SQLAlchemy 2.0):**
   ```python
   from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, Numeric, Integer
   from sqlalchemy.orm import Mapped, mapped_column, relationship
   from sqlalchemy.sql import func
   from datetime import datetime
   import enum

   class GuiaStatus(enum.Enum):
       GERADA = "GERADA"
       ENVIADA = "ENVIADA"
       FATURADA = "FATURADA"
       GLOSADA = "GLOSADA"

   class Operadora(Base):
       __tablename__ = "operadoras"
       id: Mapped[int] = mapped_column(primary_key=True)
       nome: Mapped[str] = mapped_column(String(100), unique=True)
       cnpj: Mapped[str] = mapped_column(String(14), unique=True)
       plano: Mapped[list["PlanoSaude"]] = relationship(back_populates="operadora")

   class PlanoSaude(Base):
       __tablename__ = "planos_saude"
       id: Mapped[int] = mapped_column(primary_key=True)
       nome: Mapped[str] = mapped_column(String(100))
       codigo_ans: Mapped[str] = mapped_column(String(10))
       operadora_id: Mapped[int] = mapped_column(ForeignKey("operadoras.id"))
       operadora: Mapped["Operadora"] = relationship(back_populates="plano")
       guias: Mapped[list["GuiaTISS"]] = relationship(back_populates="plano")

   class GuiaTISS(Base):
       __tablename__ = "guias_tiss"
       id: Mapped[int] = mapped_column(primary_key=True)
       numero_guia: Mapped[str] = mapped_column(String(50), unique=True)
       status: Mapped[GuiaStatus] = mapped_column(Enum(GuiaStatus), default=GuiaStatus.GERADA)
       plano_id: Mapped[int] = mapped_column(ForeignKey("planos_saude.id"))
       plano: Mapped["PlanoSaude"] = relationship(back_populates="guias")
       data_emissao: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
       data_faturamento: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
       data_glosa: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
       observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

   class ReciboParticular(Base):
       __tablename__ = "recibos_particulares"
       id: Mapped[int] = mapped_column(primary_key=True)
       numero_recibo: Mapped[str] = mapped_column(String(50), unique=True)
       valor: Mapped[float] = mapped_column(Numeric(10, 2))
       guia_tiss_id: Mapped[int | None] = mapped_column(ForeignKey("guias_tiss.id"), nullable=True)
       guia_tiss: Mapped["GuiaTISS | None"] = relationship(back_populates="recibos")
       data_emissao: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
       descricao: Mapped[str] = mapped_column(Text)
   ```
   Wait, I need to define `Base` and import it. I'll assume a standard `database.py` exists, but I'll define `Base` locally or import it. I'll use `from backend.app.database import Base` or define it inline for completeness. I'll define it inline to make it self-contained as requested.

   Actually, SQLAlchemy 2.0 uses `DeclarativeBase` or `registry`. I'll use `DeclarativeBase`.

   Let's refine the models to be strictly SQLAlchemy 2.0 compliant:
   ```python
   from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, Numeric, Integer
   from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
   from sqlalchemy.sql import func
   from datetime import datetime
   import enum
   from typing import Optional

   class Base(DeclarativeBase):
       pass

   class GuiaStatus(enum.Enum):
       GERADA = "GERADA"
       ENVIADA = "ENVIADA"
       FATURADA = "FATURADA"
       GLOSADA = "GLOSADA"

   class Operadora(Base):
       __tablename__ = "operadoras"
       id: Mapped[int] = mapped_column(primary_key=True)
       nome: Mapped[str] = mapped_column(String(100), unique=True)
       cnpj: Mapped[str] = mapped_column(String(14), unique=True)
       plano: Mapped[list["PlanoSaude"]] = relationship(back_populates="operadora")

   class PlanoSaude(Base):
       __tablename__ = "planos_saude"
       id: Mapped[int] = mapped_column(primary_key=True)
       nome: Mapped[str] = mapped_column(String(100))
       codigo_ans: Mapped[str] = mapped_column(String(10))
       operadora_id: Mapped[int] = mapped_column(ForeignKey("operadoras.id"))
       operadora: Mapped["Operadora"] = relationship(back_populates="plano")
       guias: Mapped[list["GuiaTISS"]] = relationship(back_populates="plano")

   class GuiaTISS(Base):
       __tablename__ = "guias_tiss"
       id: Mapped[int] = mapped_column(primary_key=True)
       numero_guia: Mapped[str] = mapped_column(String(50), unique=True)
       status: Mapped[GuiaStatus] = mapped_column(Enum(GuiaStatus), default=GuiaStatus.GERADA)
       plano_id: Mapped[int] = mapped_column(ForeignKey("planos_saude.id"))
       plano: Mapped["PlanoSaude"] = relationship(back_populates="guias")
       data_emissao: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
       data_faturamento: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
       data_glosa: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
       observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       recibos: Mapped[list["ReciboParticular"]] = relationship(back_populates="guia_tiss")

   class ReciboParticular(Base):
       __tablename__ = "recibos_particulares"
       id: Mapped[int] = mapped_column(primary_key=True)
       numero_recibo: Mapped[str] = mapped_column(String(50), unique=True)
       valor: Mapped[float] = mapped_column(Numeric(10, 2))
       guia_tiss_id: Mapped[Optional[int]] = mapped_column(ForeignKey("guias_tiss.id"), nullable=True)
       guia_tiss: Mapped[Optional["GuiaTISS"]] = relationship(back_populates="recibos")
       data_emissao: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
       descricao: Mapped[str] = mapped_column(Text)
   ```

4.  **Design Pydantic Schemas (v2):**
   Need schemas for validation. I'll include them in the same file or separate. The prompt says "modelos e consultas SQLAlchemy 2.0", but also mentions Pydantic v2. I'll add Pydantic models for request/response validation.

   ```python
   from pydantic import BaseModel, Field, ConfigDict
   from datetime import datetime
   from typing import Optional, List
   from enum import Enum

   class GuiaStatusPydantic(str, Enum):
       GERADA = "GERADA"
       ENVIADA = "ENVIADA"
       FATURADA = "FATURADA"
       GLOSADA = "GLOSADA"

   class OperadoraBase(BaseModel):
       nome: str = Field(..., min_length=1, max_length=100)
       cnpj: str = Field(..., pattern=r"^\d{14}$")

   class PlanoSaudeBase(BaseModel):
       nome: str = Field(..., min_length=1, max_length=100)
       codigo_ans: str = Field(..., min_length=1, max_length=10)
       operadora_id: int

   class GuiaTISSBase(BaseModel):
       numero_guia: str = Field(..., min_length=1, max_length=50)
       plano_id: int
       status: GuiaStatusPydantic = GuiaStatusPydantic.GERADA
       observacoes: Optional[str] = None

   class ReciboParticularBase(BaseModel):
       numero_recibo: str = Field(..., min_length=1, max_length=50)
       valor: float = Field(..., gt=0)
       guia_tiss_id: Optional[int] = None
       descricao: str = Field(..., min_length=1)
   ```

5.  **Design Repository Class:**
   Needs to handle CRUD operations using SQLAlchemy 2.0 syntax (select, insert, update, delete). I'll use `Session` as a parameter or assume it's passed. I'll make methods accept `session: Session` for explicit dependency injection, which is standard.

   ```python
   from sqlalchemy import select, update, delete, func
   from sqlalchemy.orm import Session
   from sqlalchemy.exc import IntegrityError
   from typing import List, Optional
   import uuid

   class ConveniosRepository:
       def __init__(self, session: Session):
           self.session = session

       # Operadora
       def create_operadora(self, data: OperadoraBase) -> Operadora:
           operadora = Operadora(**data.model_dump())
           self.session.add(operadora)
           self.session.flush()
           return operadora

       def get_operadora(self, operadora_id: int) -> Optional[Operadora]:
           return self.session.get(Operadora, operadora_id)

       def get_operadora_by_cnpj(self, cnpj: str) -> Optional[Operadora]:
           stmt = select(Operadora).where(Operadora.cnpj == cnpj)
           return self.session.execute(stmt).scalar_one_or_none()

       # PlanoSaude
       def create_plano(self, data: PlanoSaudeBase) -> PlanoSaude:
           plano = PlanoSaude(**data.model_dump())
           self.session.add(plano)
           self.session.flush()
           return plano

       def get_plano(self, plano_id: int) -> Optional[PlanoSaude]:
           return self.session.get(PlanoSaude, plano_id)

       def get_plano_by_codigo_ans(self, codigo_ans: str) -> Optional[PlanoSaude]:
           stmt = select(PlanoSaude).where(PlanoSaude.codigo_ans == codigo_ans)
           return self.session.execute(stmt).scalar_one_or_none()

       # GuiaTISS
       def create_guia(self, data: GuiaTISSBase) -> GuiaTISS:
           guia = GuiaTISS(**data.model_dump())
           self.session.add(guia)
           self.session.flush()
           return guia

       def update_guia_status(self, guia_id: int, novo_status: GuiaStatusPydantic) -> Optional[GuiaTISS]:
           stmt = (
               update(GuiaTISS)
               .where(GuiaTISS.id == guia_id)
               .values(status=novo_status)
           )
           # Update timestamps based on status
           if novo_status == GuiaStatusPydantic.FATURADA:
               stmt = stmt.values(data_faturamento=func.now())
           elif novo_status == GuiaStatusPydantic.GLOSADA:
               stmt = stmt.values(data_glosa=func.now())
           self.session.execute(stmt)
           self.session.flush()
           return self.session.get(GuiaTISS, guia_id)

       def get_guias_by_status(self, status: GuiaStatusPydantic) -> List[GuiaTISS]:
           stmt = select(GuiaTISS).where(GuiaTISS.status == status)
           return list(self.session.execute(stmt).scalars().all())

       def get_guia_by_numero(self, numero_guia: str) -> Optional[GuiaTISS]:
           stmt = select(GuiaTISS).where(GuiaTISS.numero_guia == numero_guia)
           return self.session.execute(stmt).scalar_one_or_none()

       # ReciboParticular
       def create_recibo(self, data: ReciboParticularBase) -> ReciboParticular:
           recibo = ReciboParticular(**data.model_dump())
           self.session.add(recibo)
           self.session.flush()
           return recibo

       def get_recibos(self, guia_tiss_id: Optional[int] = None) -> List[ReciboParticular]:
           stmt = select(ReciboParticular)
           if guia_tiss_id is not None:
               stmt = stmt.where(ReciboParticular.guia_tiss_id == guia_tiss_id)
           return list(self.session.execute(stmt).scalars().all())

       def delete_recibo(self, recibo_id: int) -> bool:
           recibo = self.session.get(ReciboParticular, recibo_id)
           if recibo:
               self.session.delete(recibo)
               self.session.flush()
               return True
           return False
   ```

   Wait, I need to handle the `GuiaStatus` enum mapping correctly. SQLAlchemy's `Enum` can be tricky with Python enums. I'll use `name` or `value`. I'll stick to `Enum(GuiaStatus)` but ensure it works. Actually, SQLAlchemy 2.0 recommends `Enum(GuiaStatus, name="guia_status")` or using `String` with check constraints. I'll use `String` with a check constraint for better compatibility, or stick to `Enum` but cast properly. I'll use `Enum(GuiaStatus, native_enum=False)` to store as VARCHAR, which is safer for cross-database.

   Let's adjust the model definition for `status`:
   ```python
   status: Mapped[GuiaStatus] = mapped_column(Enum(GuiaStatus, name="guia_status", native_enum=False), default=GuiaStatus.GERADA)
   ```

   Also, I should add proper type hints and docstrings. I'll structure the file carefully.

6.  **Consider Testing Requirements:**
   The prompt says "Preservar 100% da suíte de testes verde." and I'm acting as a tester. I should provide the test file `backend/tests/test_convenios_repo.py` to ensure it's green. I'll use `pytest`, `sqlalchemy.testing`, or `unittest.mock`. Since it's a repo, I'll use `pytest` with an in-memory SQLite database for testing.

   Test structure:
   - Setup DB session
   - Test CRUD for Operadora, Plano, Guia, Recibo
   - Test status transitions
   - Test constraints (CNPJ format, unique numbers)
   - Use `pytest.fixture` for