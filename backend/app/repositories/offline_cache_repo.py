from __future__ import annotations
   import json
   import uuid
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Any, Optional

   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from sqlalchemy import (
       Column,
       DateTime,
       Enum as SAEnum,
       ForeignKey,
       Index,
       JSON,
       String,
       Text,
       UUID,
       func,
       select,
   )
   from sqlalchemy.dialects.postgresql import JSONB
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
   from sqlalchemy.ext.asyncio import AsyncSession

class SyncStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

class MutationPayload(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True)
       patient_cns: Optional[str] = Field(None, min_length=15, max_length=15)
       patient_cpf: Optional[str] = Field(None, min_length=11, max_length=11)
       mutation_type: str = Field(..., pattern=r"^(CREATE|UPDATE|DELETE)$")
       clinical_data: dict[str, Any] = Field(default_factory=dict)
       # SUS/APS fields
       ciap2_codes: list[str] = Field(default_factory=list)
       cid10_codes: list[str] = Field(default_factory=list)
       soap_note: Optional[str] = None

       @field_validator("patient_cns")
       @classmethod
       def validate_cns(cls, v: Optional[str]) -> Optional[str]:
           if v is None:
               return v
           # Simplified CNS validation (15 digits, checksum logic omitted for brevity but noted)
           if not v.isdigit() or len(v) != 15:
               raise ValueError("CNS deve ter 15 dígitos numéricos")
           return v

       @field_validator("patient_cpf")
       @classmethod
       def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
           if v is None:
               return v
           if not v.isdigit() or len(v) != 11:
               raise ValueError("CPF deve ter 11 dígitos numéricos")
           return v

class Base(DeclarativeBase):
       pass

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutations"

       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       patient_cns: Mapped[Optional[str]] = mapped_column(String(15), index=True)
       patient_cpf: Mapped[Optional[str]] = mapped_column(String(11), index=True)
       mutation_type: Mapped[str] = mapped_column(String(10))
       clinical_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
       ciap2_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
       cid10_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
       soap_note: Mapped[Optional[str]] = mapped_column(Text)
       status: Mapped[SyncStatus] = mapped_column(SAEnum(SyncStatus), default=SyncStatus.PENDENTE)
       sync_error: Mapped[Optional[str]] = mapped_column(Text)
       version: Mapped[int] = mapped_column(default=1)
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

       __table_args__ = (
           Index("ix_offline_cache_status", "status"),
           Index("ix_offline_cache_patient", "patient_cns", "patient_cpf"),
       )

class OfflineCacheRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def add_mutation(self, payload: MutationPayload) -> MutationResponse:
           # ... implementation

class MutationResponse(BaseModel):
       id: uuid.UUID
       patient_cns: Optional[str]
       patient_cpf: Optional[str]
       mutation_type: str
       clinical_data: dict[str, Any]
       ciap2_codes: list[str]
       cid10_codes: list[str]
       soap_note: Optional[str]
       status: SyncStatus
       sync_error: Optional[str]
       version: int
       created_at: datetime
       updated_at: datetime

       model_config = ConfigDict(from_attributes=True)

   class SyncResult(BaseModel):
       success_count: int = 0
       conflict_count: int = 0
       errors: list[str] = Field(default_factory=list)

class OfflineCacheRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def add_mutation(self, payload: MutationPayload) -> MutationResponse:
           # Integrity: CNS or CPF required
           if not payload.patient_cns and not payload.patient_cpf:
               raise ValueError("É obrigatório informar CNS ou CPF do paciente.")

           # SUS/APS: Validate SOAP/CID-10/CIAP-2 structure if present
           if payload.soap_note:
               # Simplified validation for SOAP structure (S, O, A, P sections)
               soap_sections = ["S", "O", "A", "P"]
               if not all(section in payload.soap_note.upper() for section in soap_sections):
                   raise ValueError("SOAP note deve conter as seções S, O, A, P.")

           mutation = OfflineCacheMutation(
               patient_cns=payload.patient_cns,
               patient_cpf=payload.patient_cpf,
               mutation_type=payload.mutation_type,
               clinical_data=payload.clinical_data,
               ciap2_codes=payload.ciap2_codes,
               cid10_codes=payload.cid10_codes,
               soap_note=payload.soap_note,
           )
           self.session.add(mutation)
           await self.session.flush()
           await self.session.refresh(mutation)
           return MutationResponse.model_validate(mutation)

       async def get_pending_mutations(self, limit: int = 100) -> list[MutationResponse]:
           stmt = (
               select(OfflineCacheMutation)
               .where(OfflineCacheMutation.status == SyncStatus.PENDENTE)
               .order_by(OfflineCacheMutation.created_at.asc())
               .limit(limit)
           )
           result = await self.session.execute(stmt)
           mutations = result.scalars().all()
           return [MutationResponse.model_validate(m) for m in mutations]

       async def mark_as_sent(self, mutation_id: uuid.UUID) -> None:
           stmt = (
               update(OfflineCacheMutation)
               .where(OfflineCacheMutation.id == mutation_id)
               .values(status=SyncStatus.ENVIADO, updated_at=func.now(timezone=True))
           )
           await self.session.execute(stmt)
           await self.session.commit()

       async def mark_as_conflict(self, mutation_id: uuid.UUID, error: str) -> None:
           stmt = (
               update(OfflineCacheMutation)
               .where(OfflineCacheMutation.id == mutation_id)
               .values(status=SyncStatus.CONFLITO, sync_error=error, updated_at=func.now(timezone=True))
           )
           await self.session.execute(stmt)
           await self.session.commit()

       async def sync_batch(self, mutations: list[MutationResponse]) -> SyncResult:
           result = SyncResult()
           for mutation in mutations:
               try:
                   # Simulate sync logic (in real app, this would call remote API)
                   # For now, just mark as sent
                   await self.mark_as_sent(mutation.id)
                   result.success_count += 1
               except Exception as e:
                   await self.mark_as_conflict(mutation.id, str(e))
                   result.conflict_count += 1
                   result.errors.append(f"Mutation {mutation.id}: {str(e)}")
           return result

       async def get_by_patient(self, cns: Optional[str] = None, cpf: Optional[str] = None) -> list[MutationResponse]:
           conditions = [OfflineCacheMutation.status == SyncStatus.PENDENTE]
           if cns:
               conditions.append(OfflineCacheMutation.patient_cns == cns)
           if cpf:
               conditions.append(OfflineCacheMutation.patient_cpf == cpf)

           stmt = select(OfflineCacheMutation).where(*conditions).order_by(OfflineCacheMutation.created_at.desc())
           res = await self.session.execute(stmt)
           mutations = res.scalars().all()
           return [MutationResponse.model_validate(m) for m in mutations]

from sqlalchemy import update, func, select

import pytest
   import asyncio
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   from sqlalchemy.orm import sessionmaker
   from backend.app.repositories.offline_cache_repo import (
       OfflineCacheRepository,
       MutationPayload,
       SyncStatus,
       OfflineCacheMutation,
       Base,
   )

   @pytest.fixture(scope="module")
   def event_loop():
       loop = asyncio.new_event_loop()
       yield loop
       loop.close()

   @pytest.fixture(scope="module")
   async def engine():
       engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
       yield engine
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.drop_all)
       await engine.dispose()

   @pytest.fixture
   async def session(engine):
       async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
       async with async_session() as sess:
           yield sess

   @pytest.fixture
   def repo(session):
       return OfflineCacheRepository(session)
