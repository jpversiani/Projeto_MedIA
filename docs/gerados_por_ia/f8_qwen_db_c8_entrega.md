Here's a thinking process:

1.  **Understand User Role & Task:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for a "Health Campaigns Repository and Send History" (C8).
   - **Requirements:**
     - Track sent messages, confirmation status by patient, and data protection audit log.
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification.
     - Full compliance and automated test coverage with pytest.
     - Provide complete, executable code. Specify file paths in code blocks.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/campanhas_repo.py`
   - **Domain:** Health campaigns (Campanhas de Saúde)
   - **Key Entities/Models:**
     - Campaign (Campanha)
     - Message Send/Dispatch (Disparo/Mensagem)
     - Patient Confirmation Status (Status de Confirmação)
     - Data Protection Audit Log (Log de Auditoria LGPD)
   - **Standards:** CIAP-2, CID-10, SOAP, CNS, CPF
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0
   - **Testing:** pytest coverage, full compliance

3.  **Design Database Models (SQLAlchemy 2.0):**
   Need tables for:
   - `campanhas`: id, name, description, start_date, end_date, status, created_at, updated_at
   - `disparos`: id, campanha_id, paciente_cns, paciente_cpf, mensagem, status_envio, data_envio, metodo_sus (CIAP-2/CID-10/SOAP), created_at
   - `confirmacoes_paciente`: id, disparo_id, confirmado, data_confirmacao, observacoes
   - `auditoria_lgpd`: id, disparo_id, acao, usuario_sistema, ip, data_hora, detalhes

   Let's refine the models to align with SUS/APS standards and Pydantic v2.
   - Use `Enum` for status fields.
   - Use `UUID` or `Integer` for IDs. I'll use `Integer` for simplicity, but `UUID` is often better. I'll stick to `Integer` as per common SUS systems, but add `UUID` if needed. Actually, `UUID` is fine. I'll use `Integer` for simplicity in examples.
   - Pydantic schemas for request/response validation.
   - Repository pattern with async SQLAlchemy 2.0.

   Let's define the SQLAlchemy models first:
   ```python
   from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
   from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
   from datetime import datetime
   import enum

   class Base(DeclarativeBase):
       pass

   class CampanhaStatus(enum.Enum):
       RASCUNHO = "rascunho"
       ATIVA = "ativa"
       PAUSADA = "pausada"
       CONCLUIDA = "concluida"

   class DisparoStatus(enum.Enum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       FALHA = "falha"
       CONFIRMADO = "confirmado"
       NAO_CONFIRMADO = "nao_confirmado"

   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       nome: Mapped[str] = mapped_column(String(255))
       descricao: Mapped[str] = mapped_column(Text)
       status: Mapped[CampanhaStatus] = mapped_column(Enum(CampanhaStatus), default=CampanhaStatus.RASCUNHO)
       data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       data_atualizacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

   class Disparo(Base):
       __tablename__ = "disparos"
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       campanha_id: Mapped[int] = mapped_column(Integer, ForeignKey("campanhas.id"))
       paciente_cns: Mapped[str] = mapped_column(String(15)) # CNS format
       paciente_cpf: Mapped[str] = mapped_column(String(14)) # CPF format
       mensagem: Mapped[str] = mapped_column(Text)
       metodo_sus: Mapped[str] = mapped_column(String(50)) # CIAP-2, CID-10, SOAP
       status: Mapped[DisparoStatus] = mapped_column(Enum(DisparoStatus), default=DisparoStatus.PENDENTE)
       data_envio: Mapped[datetime] = mapped_column(DateTime, nullable=True)
       data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

       confirmacoes: Mapped[list["ConfirmacaoPaciente"]] = relationship(back_populates="disparo")
       auditoria: Mapped[list["AuditoriaLgpd"]] = relationship(back_populates="disparo")

   class ConfirmacaoPaciente(Base):
       __tablename__ = "confirmacoes_paciente"
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       disparo_id: Mapped[int] = mapped_column(Integer, ForeignKey("disparos.id"))
       confirmado: Mapped[bool] = mapped_column(Boolean, default=False)
       data_confirmacao: Mapped[datetime] = mapped_column(DateTime, nullable=True)
       observacoes: Mapped[str] = mapped_column(Text, nullable=True)

       disparo: Mapped["Disparo"] = relationship(back_populates="confirmacoes")

   class AuditoriaLgpd(Base):
       __tablename__ = "auditoria_lgpd"
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       disparo_id: Mapped[int] = mapped_column(Integer, ForeignKey("disparos.id"))
       acao: Mapped[str] = mapped_column(String(100)) # e.g., "ENVIO", "CONFIRMACAO", "ACESSO"
       usuario_sistema: Mapped[str] = mapped_column(String(100))
       ip: Mapped[str] = mapped_column(String(45))
       data_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       detalhes: Mapped[str] = mapped_column(Text, nullable=True)

       disparo: Mapped["Disparo"] = relationship(back_populates="auditoria")
   ```

4.  **Design Pydantic Schemas (v2):**
   Need schemas for validation and serialization.
   ```python
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from datetime import datetime
   from typing import Optional
   import re

   class CampanhaCreate(BaseModel):
       nome: str = Field(..., min_length=3, max_length=255)
       descricao: str = Field(..., min_length=10)
       status: Optional[CampanhaStatus] = None

       model_config = ConfigDict(from_attributes=True)

   class DisparoCreate(BaseModel):
       campanha_id: int
       paciente_cns: str = Field(..., pattern=r"^\d{15}$")
       paciente_cpf: str = Field(..., pattern=r"^\d{11}$")
       mensagem: str = Field(..., min_length=1)
       metodo_sus: str = Field(..., pattern=r"^(CIAP-2|CID-10|SOAP)$")

       model_config = ConfigDict(from_attributes=True)

       @field_validator("paciente_cpf")
       @classmethod
       def validate_cpf(cls, v):
           # Basic CPF validation logic could go here, but regex is enough for schema
           return v

   class ConfirmacaoCreate(BaseModel):
       disparo_id: int
       confirmado: bool
       observacoes: Optional[str] = None

       model_config = ConfigDict(from_attributes=True)

   class AuditoriaLgpdCreate(BaseModel):
       disparo_id: int
       acao: str
       usuario_sistema: str
       ip: str
       detalhes: Optional[str] = None

       model_config = ConfigDict(from_attributes=True)
   ```

5.  **Design Repository Class:**
   Need async methods for CRUD and specific tracking queries.
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, func
   from sqlalchemy.orm import selectinload
   from typing import List, Optional, Dict, Any
   import logging

   logger = logging.getLogger(__name__)

   class CampanhasRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def criar_campanha(self, data: CampanhaCreate) -> Campanha:
           campanha = Campanha(**data.model_dump())
           self.session.add(campanha)
           await self.session.commit()
           await self.session.refresh(campanha)
           return campanha

       async def criar_disparo(self, data: DisparoCreate) -> Disparo:
           disparo = Disparo(**data.model_dump())
           self.session.add(disparo)
           await self.session.commit()
           await self.session.refresh(disparo)
           return disparo

       async def registrar_confirmacao(self, data: ConfirmacaoCreate) -> ConfirmacaoPaciente:
           confirmacao = ConfirmacaoPaciente(**data.model_dump())
           self.session.add(confirmacao)
           await self.session.commit()
           await self.session.refresh(confirmacao)
           return confirmacao

       async def registrar_auditoria(self, data: AuditoriaLgpdCreate) -> AuditoriaLgpd:
           auditoria = AuditoriaLgpd(**data.model_dump())
           self.session.add(auditoria)
           await self.session.commit()
           await self.session.refresh(auditoria)
           return auditoria

       async def get_disparos_por_campanha(self, campanha_id: int) -> List[Disparo]:
           stmt = select(Disparo).options(selectinload(Dispo.confirmacoes), selectinload(Disparo.auditoria)).where(Disparo.campanha_id == campanha_id)
           result = await self.session.execute(stmt)
           return list(result.scalars().all())

       async def get_status_confirmacao_por_paciente(self, paciente_cns: str) -> Dict[str, Any]:
           stmt = select(Disparo, ConfirmacaoPaciente).join(ConfirmacaoPaciente, Disparo.id == ConfirmacaoPaciente.disparo_id, isouter=True).where(Disparo.paciente_cns == paciente_cns)
           result = await self.session.execute(stmt)
           rows = result.all()
           status_map = {}
           for d, c in rows:
               status_map[d.id] = {
                   "disparo_id": d.id,
                   "status": d.status.value,
                   "confirmado": c.confirmado if c else None,
                   "data_confirmacao": c.data_confirmacao if c else None
               }
           return status_map
   ```
   Wait, I need to fix the typo `Dispo.confirmacoes` -> `Disparo.confirmacoes`.
   Also, SQLAlchemy 2.0 uses `mapped_column` and `relationship` correctly. I'll adjust the imports and types.
   I should also add a method to track message send history with audit logs specifically for LGPD compliance.
   Let's refine the repository to be more robust and aligned with the prompt.

   Key requirements to address:
   - Rastreio de mensagens enviadas (Send history tracking)
   - Status de confirmação pelo paciente (Patient confirmation status)
   - Log de auditoria de proteção de dados (LGPD audit log)
   - SUS/APS standards: CIAP-2, CID-10, SOAP, CNS/CPF
   - Pydantic v2, SQLAlchemy 2.0, Python 3.12
   - pytest coverage

   I'll structure the file properly with all models, schemas, and repository class. I'll also add a test file `backend/app/tests/test_campanhas_repo.py` to fulfill the "cobertura de testes automatizados com pytest" requirement.

6.  **Draft the Repository File (`backend/app/repositories/campanhas_repo.py`):**
   I'll combine models, schemas, and repository into one file as requested, but keep it clean.
   I'll use `sqlalchemy.orm.Mapped` and `mapped_column` correctly.
   I'll ensure Pydantic v2 compatibility (`model_config`, `field_validator`, `ConfigDict`).
   I'll add type hints strictly.

   Let's write it out carefully.

   ```python
   # Arquivo: backend/app/repositories/campanhas_repo.py
   from __future__ import annotations

   import enum
   import logging
   from datetime import datetime
   from typing import Any, Dict, List, Optional

   from pydantic import BaseModel, ConfigDict, Field, field_validator
   from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, String, Text, DateTime, Boolean, select
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, selectinload

   logger = logging.getLogger(__name__)

   # ------------------------------------------------------------------
   # 1. Modelos SQLAlchemy 2.0 (SUS/APS Standards)
   # ------------------------------------------------------------------

   class Base(DeclarativeBase):
       pass

   class CampanhaStatus(enum.Enum):
       RASCUNHO = "rascunho"
       ATIVA = "ativa"
       PAUSADA = "pausada"
       CONCLUIDA = "concluida"

   class DisparoStatus(enum.Enum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       FALHA = "falha"
       CONFIRMADO = "confirmado"
       NAO_CONFIRMADO = "nao_confirmado"

   class MetodoSUS(enum.Enum):
       CIAP2 = "CIAP-2"
       CID10 = "CID-10"
       SOAP = "SOAP"

   class Campanha(Base):
       __tablename__ = "campanhas"

       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       nome: Mapped[str] = mapped_column(String(255))
       descricao: Mapped[str] = mapped_column(Text)
       status: Mapped[CampanhaStatus] = mapped_column(SAEnum(CampanhaStatus), default=CampanhaStatus.RASCUNHO)
       data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       data_atualizacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

   class Disparo(Base):
       __tablename__ = "disparos"

       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       campanha_id: Mapped[int] = mapped_column(Integer, ForeignKey("campanhas.id"))
       paciente_cns: Mapped[str] = mapped_column(String(15))  # Código Nacional de Saúde
       paciente_cpf: Mapped[str] = mapped_column(String(14))  # CPF formatado
       mensagem: Mapped[str] = mapped_column(Text)
       metodo_sus: Mapped[MetodoSUS] = mapped_column(SAEnum(MetodoSUS))
       status: Mapped[DisparoStatus] = mapped_column(SAEnum(DisparoStatus), default=DisparoStatus.PENDENTE)
       data_envio: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
       data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

       confirmacoes: Mapped[list[ConfirmacaoPaciente]] = relationship(back_populates="disparo", cascade="all, delete-orphan")
       auditoria: Mapped[list[AuditoriaLgpd]] = relationship(back_populates="disparo", cascade="all, delete-orphan")

   class ConfirmacaoPaciente(Base):
       __tablename__ = "confirmacoes_paciente"

       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       disparo_id: Mapped[int] = mapped_column(Integer, ForeignKey("disparos.id"))
       confirmado: Mapped[bool] = mapped_column(Boolean, default=False)
       data_confirmacao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
       observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

       disparo: Mapped[Disparo] = relationship(back_populates="confirmacoes")

   class AuditoriaLgpd(Base):
       __tablename__ = "auditoria_lgpd"

       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       disparo_id: Mapped[int] = mapped_column(Integer, ForeignKey("disparos.id"))
       acao: Mapped[str] = mapped_column(String(100))  # ENVIO, CONFIRMACAO, ACESSO, etc.
       usuario_sistema: Mapped[str] = mapped_column(String(100))
       ip: Mapped[str] = mapped_column(String(45))
       data_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       detalhes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

       disparo: Mapped[Disparo] = relationship(back_populates="auditoria")

   # ------------------------------------------------------------------
   # 2. Schemas Pydantic v2 (Validação Estrita)
   # ------------------------------------------------------------------

   class CampanhaCreate(BaseModel):
       nome: str = Field(..., min_length=3, max_length=255)
       descricao: str = Field(..., min_length=10)
       status: Optional[CampanhaStatus] = None

       model_config = ConfigDict(from_attributes=True)

   class DisparoCreate(BaseModel):
       campanha_id: int
       paciente_cns: str = Field(..., pattern=r"^\d