Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for a "Health Campaigns Repository and Dispatch History" (C96) for the "MedIA" project.
   - **Requirements:**
     - Track sent messages, patient confirmation status, and data protection audit logs.
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification.
     - Full compliance and automated test coverage with pytest.
     - Provide complete, executable code.
     - Specify file path at the top of each code block.

2.  **Deconstruct Requirements:**
   - **Domain:** Health campaigns, message dispatch history, patient confirmation, data protection audit (LGPD compliance).
   - **Standards:** CIAP-2 (Classificação Internacional de Atenção Primária), CID-10 (ICD-10), SOAP (Subjective, Objective, Assessment, Plan), CNS (Cartão Nacional de Saúde), CPF (Cadastro de Pessoas Físicas).
   - **Tech Stack:** Python 3.12, Pydantic v2 (models/validation), SQLAlchemy 2.0 (ORM/database), pytest (testing).
   - **Architecture:** Repository pattern, strict typing, LGPD compliance, SUS/APS alignment.

3.  **Design Database Models (SQLAlchemy 2.0):**
   Need tables for:
   - `Campanha` (Campaign): ID, name, description, start/end dates, status, created_at, updated_at.
   - `CampanhaPaciente` (Campaign-Patient mapping): campaign_id, paciente_id, cns, cpf, cid10, ciap2, status, confirmation_status, last_contact, etc.
   - `HistoricoDisparo` (Dispatch History): id, campanha_id, paciente_id, canal (SMS/WhatsApp/Email), mensagem, status_envio, data_envio, resposta_paciente, etc.
   - `LogAuditoriaLGPD` (Audit Log): id, entidade_tipo, entidade_id, acao, usuario, data_hora, ip, justificativa, conformidade_lgpd, etc.

   Let's refine the models to align with SUS/APS standards:
   - `Campanha`: `id`, `nome`, `descricao`, `objetivo`, `status`, `data_inicio`, `data_fim`, `criado_em`, `atualizado_em`
   - `PacienteCampanha` (or `CampanhaParticipante`): `id`, `campanha_id`, `cns`, `cpf`, `cid10`, `ciap2`, `metodo_soap`, `status`, `confirmacao_paciente`, `ultima_atualizacao`
   - `HistoricoDisparo`: `id`, `campanha_id`, `participante_id`, `canal`, `conteudo`, `status_envio`, `data_envio`, `resposta_paciente`, `tentativas`
   - `LogAuditoriaProtecaoDados`: `id`, `entidade_tipo`, `entidade_id`, `acao`, `usuario_id`, `data_hora`, `ip_origem`, `justificativa`, `conformidade_lgpd`, `dados_acessados`

   Actually, to keep it focused on the repository task, I'll define the SQLAlchemy models and the repository class with methods for CRUD and specific tracking/audit operations.

4.  **Design Pydantic Models (v2):**
   Need schemas for request/response validation:
   - `CampanhaCreate`, `CampanhaRead`, `CampanhaUpdate`
   - `PacienteCampanhaCreate`, `PacienteCampanhaRead`
   - `HistoricoDisparoCreate`, `HistoricoDisparoRead`
   - `LogAuditoriaCreate`, `LogAuditoriaRead`
   - Use `ConfigDict`, `Field`, `model_validator`, `computed_field` as needed.
   - Strict typing: `str`, `int`, `datetime`, `bool`, `Optional`, `List`, `Enum`.

5.  **Design Repository Class:**
   - `class CampanhasRepository`:
     - `__init__(self, db_session: Session) -> None`
     - `criar_campanha(self, data: CampanhaCreate) -> Campanha`
     - `obter_campanha(self, campanha_id: int) -> Optional[Campanha]`
     - `adicionar_paciente_a_campanha(self, campanha_id: int, data: PacienteCampanhaCreate) -> PacienteCampanha`
     - `registrar_disparo(self, data: HistoricoDisparoCreate) -> HistoricoDisparo`
     - `atualizar_confirmacao_paciente(self, participante_id: int, status: str) -> PacienteCampanha`
     - `registrar_log_auditoria(self, data: LogAuditoriaCreate) -> LogAuditoria`
     - `obter_relatorio_campanha(self, campanha_id: int) -> dict`
     - Use SQLAlchemy 2.0 syntax: `select`, `insert`, `update`, `delete`, `session.execute()`.
     - Handle transactions, errors, and LGPD compliance (e.g., masking sensitive data in logs if needed, but audit logs should record access, not necessarily mask).

6.  **Align with SUS/APS Standards:**
   - CIAP-2: `ciap2: str` (field with validation pattern if possible, or just str with docstring)
   - CID-10: `cid10: str`
   - SOAP: `metodo_soap: str` (e.g., "S", "O", "A", "P" or full text)
   - CNS/CPF: `cns: str`, `cpf: str` with validation patterns.
   - Add Pydantic validators for CPF and CNS.

7.  **Write Pydantic Models (Mental Draft & Refinement):**
   ```python
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from typing import Optional, List
   from datetime import datetime
   import re

   class CampanhaCreate(BaseModel):
       nome: str = Field(..., min_length=1, max_length=255)
       descricao: str = Field(..., min_length=1)
       objetivo: str = Field(..., min_length=1)
       data_inicio: datetime
       data_fim: datetime
       status: str = Field(default="ativa")

       model_config = ConfigDict(from_attributes=True)

   class CampanhaRead(CampanhaCreate):
       id: int
       criado_em: datetime
       atualizado_em: Optional[datetime] = None

       model_config = ConfigDict(from_attributes=True)
   ```
   Need CPF/CNS validators:
   ```python
   @field_validator('cpf')
   @classmethod
   def validar_cpf(cls, v: str) -> str:
       v = str(v).replace('.', '').replace('-', '')
       if len(v) != 11 or not v.isdigit():
           raise ValueError('CPF inválido')
       # Basic CPF validation logic (optional but good)
       return v

   @field_validator('cns')
   @classmethod
   def validar_cns(cls, v: str) -> str:
       v = str(v).replace('-', '')
       if len(v) != 15 or not v.isdigit():
           raise ValueError('CNS inválido')
       return v
   ```
   Actually, Pydantic v2 uses `@field_validator`. I'll keep it simple but functional.

   Let's define all Pydantic models properly.

8.  **Write SQLAlchemy Models:**
   ```python
   from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SAEnum
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
   from datetime import datetime
   import enum

   class Base(DeclarativeBase):
       pass

   class StatusCampanha(str, enum.Enum):
       RASCUNHO = "rascunho"
       ATIVA = "ativa"
       PAUSADA = "pausada"
       CONCLUIDA = "concluida"

   class StatusDisparo(str, enum.Enum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       FALHA = "falha"
       LIDO = "lido"

   class StatusConfirmacao(str, enum.Enum):
       AGUARDANDO = "aguardando"
       CONFIRMADO = "confirmado"
       RECUSADO = "recusado"
       NAO_RESPONDIDO = "nao_respondido"

   class AcaoAuditoria(str, enum.Enum):
       CRIACAO = "criacao"
       ATUALIZACAO = "atualizacao"
       ACESSO = "acesso"
       EXCLUSAO = "exclusao"
       EXPORTACAO = "exportacao"

   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[int] = mapped_column(primary_key=True)
       nome: Mapped[str] = mapped_column(String(255))
       descricao: Mapped[str] = mapped_column(Text)
       objetivo: Mapped[str] = mapped_column(String(500))
       status: Mapped[StatusCampanha] = mapped_column(SAEnum(StatusCampanha), default=StatusCampanha.RASCUNHO)
       data_inicio: Mapped[datetime] = mapped_column(DateTime)
       data_fim: Mapped[datetime] = mapped_column(DateTime)
       criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       atualizado_em: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)

       pacientes: Mapped[List["PacienteCampanha"]] = relationship(back_populates="campanha", lazy="selectin")
       disparos: Mapped[List["HistoricoDisparo"]] = relationship(back_populates="campanha", lazy="selectin")

   class PacienteCampanha(Base):
       __tablename__ = "pacientes_campanhas"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"))
       cns: Mapped[str] = mapped_column(String(15))
       cpf: Mapped[str] = mapped_column(String(14))
       cid10: Mapped[str] = mapped_column(String(10))
       ciap2: Mapped[str] = mapped_column(String(10))
       metodo_soap: Mapped[str] = mapped_column(String(50))
       status: Mapped[StatusConfirmacao] = mapped_column(SAEnum(StatusConfirmacao), default=StatusConfirmacao.AGUARDANDO)
       confirmacao_paciente: Mapped[Optional[str]] = mapped_column(String(20))
       ultima_atualizacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

       campanha: Mapped["Campanha"] = relationship(back_populates="pacientes")

   class HistoricoDisparo(Base):
       __tablename__ = "historico_disparos"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"))
       participante_id: Mapped[int] = mapped_column(ForeignKey("pacientes_campanhas.id"))
       canal: Mapped[str] = mapped_column(String(20))
       conteudo: Mapped[str] = mapped_column(Text)
       status_envio: Mapped[StatusDisparo] = mapped_column(SAEnum(StatusDisparo), default=StatusDisparo.PENDENTE)
       data_envio: Mapped[datetime] = mapped_column(DateTime)
       resposta_paciente: Mapped[Optional[str]] = mapped_column(Text)
       tentativas: Mapped[int] = mapped_column(Integer, default=0)

       campanha: Mapped["Campanha"] = relationship(back_populates="disparos")

   class LogAuditoriaProtecaoDados(Base):
       __tablename__ = "logs_auditoria_lgpd"
       id: Mapped[int] = mapped_column(primary_key=True)
       entidade_tipo: Mapped[str] = mapped_column(String(50))
       entidade_id: Mapped[int] = mapped_column(Integer)
       acao: Mapped[AcaoAuditoria] = mapped_column(SAEnum(AcaoAuditoria))
       usuario_id: Mapped[Optional[int]] = mapped_column(Integer)
       data_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       ip_origem: Mapped[Optional[str]] = mapped_column(String(45))
       justificativa: Mapped[Optional[str]] = mapped_column(Text)
       conformidade_lgpd: Mapped[bool] = mapped_column(Boolean, default=True)
       dados_acessados: Mapped[Optional[str]] = mapped_column(Text)
   ```
   Need to handle forward references properly in SQLAlchemy. I'll use `TYPE_CHECKING` or string annotations.

9.  **Write Repository Class:**
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession # Wait, the prompt says SQLAlchemy 2.0, doesn't specify sync/async. I'll use sync Session for simplicity, but note it's compatible. Actually, I'll use `sqlalchemy.orm.Session` as standard.
   from sqlalchemy import select, insert, update, delete
   from typing import Optional, List, Dict, Any
   from datetime import datetime
   import logging

   logger = logging.getLogger(__name__)

   class CampanhasRepository:
       def __init__(self, session: Session):
           self.session = session

       async def criar_campanha(self, data: CampanhaCreate) -> Campanha:
           # ...
   ```
   Wait, the prompt doesn't specify async. I'll stick to synchronous SQLAlchemy 2.0 for broader compatibility, but I can make it async if needed. I'll use sync `Session` but note it's standard. Actually, I'll use `Session` from `sqlalchemy.orm`.

   Let's draft the repository methods carefully with SQLAlchemy 2.0 syntax:
   - `select(Campanha).where(Campanha.id == campanha_id)`
   - `self.session.execute(stmt).scalar_one_or_none()`
   - `self.session.add(instance)`
   - `self.session.commit()`

   I'll implement methods for:
   - CRUD Campanha
   - Add patient to campaign
   - Register dispatch
   - Update confirmation
   - Register audit log
   - Get campaign report (tracking messages, status, audit)

   I'll also add Pydantic models for requests/responses.

10. **Structure the File:**
    - Imports
    - Enums
    - Pydantic Models (v2)
    - SQLAlchemy Models
    - Repository Class
    - Type hints, docstrings, LGPD compliance notes
    - Ensure strict typing throughout.

11. **Draft Code (Mental Refinement):**
    I'll write it out carefully, ensuring all constraints are met.
    - Python 3.12 syntax
    - Pydantic v2 (`model_config = ConfigDict(from_attributes=True)`, `@field_validator`)
    - SQLAlchemy 2.0 (`Mapped`, `mapped_column`, `select`, `execute`)
    - SUS/APS fields: `ciap2`, `cid10`, `metodo_soap`, `cns`, `cpf`
    - Audit log for LGPD
    - Repository pattern
    - Complete & executable (will include a test file as requested: "cobertura de testes automatizados com pytest")

    Wait, the prompt says: "Execute com precisão conforme as diretrizes." and "Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo". I should provide both the repository file and the pytest file.

    Let's structure:
    1. `backend/app/repositories/campanhas_repo.py`
    2. `backend/tests/test_campanhas_repo.py`

    I'll make sure the code is self-contained and runnable (with mock DB for tests).

    **Pydantic Models:**
    ```python
    from pydantic import BaseModel, Field, ConfigDict, field_validator, EmailStr
    from typing import Optional, List
    from datetime import datetime
    import re

    class CampanhaCreate(BaseModel):
        nome: str = Field(..., min_length=1, max_length=255)
        descricao: str = Field(..., min_length=1)
        objetivo: str = Field(..., min_length=1)
        data_inicio: datetime
        data_fim: datetime
        status: str = Field(default="ativa")

        model_config = ConfigDict(from_attributes=True)

    class CampanhaRead(CampanhaCreate):
        id: int
        criado_em: datetime
        atualizado_em: Optional[datetime] = None
        model_config = ConfigDict(from_attributes=True)
    ```
    I'll add CPF/CNS validators properly.
    ```python
    @field_validator('cpf')
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        v = str(v).strip()
        if len(v) != 11 or not v.isdigit():
            raise ValueError('CPF deve ter 11 dígitos numéricos')
        return v

    @field_validator('cns')
    @classmethod
    def validar_cns(cls, v: str) -> str:
        v = str(v).strip()
        if len(v) != 15 or not v.isdigit():
            raise ValueError('CNS deve ter 15 dígitos numéricos')
        return v
    ```

    **SQLAlchemy Models:**
    I'll use `DeclarativeBase` and `Mapped`/`mapped_column`. I'll handle forward references with `TYPE_CHECKING` or string literals.

    **Repository:**
    I'll implement methods with proper SQLAlchemy 2.0 syntax. I'll add type hints strictly.

    **Tests:**
    I'll