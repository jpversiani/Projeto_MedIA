from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Sequence
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import String, Text, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
import asyncio

# --- Enums & Pydantic Models ---
class RemessaSISABStatus(str, Enum):
    GERADO = "GERADO"
    ENVIADO = "ENVIADO"
    PROCESSADO = "PROCESSADO"
    REJEITADO = "REJEITADO"

class RemessaSISABCreate(BaseModel):
    lote_id: str = Field(..., pattern=r"^[A-Za-z0-9-]+$")
    cns_paciente: Optional[str] = Field(None, pattern=r"^\d{15}$")
    cpf_paciente: Optional[str] = Field(None, pattern=r"^\d{11}$")
    ciap2: Optional[str] = Field(None, pattern=r"^[A-Z]\d{2}$")
    cid10: Optional[str] = Field(None, pattern=r"^[A-Z]\d{2}(\.\d{1,2})?$")
    metodo_soap: Optional[str] = Field(None, pattern=r"^(SOAP|REST)$")
    logs_retorno: Optional[str] = None

    @field_validator("cns_paciente", "cpf_paciente", "ciap2", "cid10", "metodo_soap")
    @classmethod
    def validate_optional_fields(cls, v):
        if v is None:
            return v
        return v.strip()

class RemessaSISABRead(BaseModel):
    id: uuid.UUID
    lote_id: str
    status: RemessaSISABStatus
    cns_paciente: Optional[str]
    cpf_paciente: Optional[str]
    ciap2: Optional[str]
    cid10: Optional[str]
    metodo_soap: Optional[str]
    logs_retorno: Optional[str]
    data_transmissao: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

# --- SQLAlchemy Base & Model ---
class Base(DeclarativeBase):
    pass

class RemessaSISABModel(Base):
    __tablename__ = "remessas_sisab"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lote_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[RemessaSISABStatus] = mapped_column(SAEnum(RemessaSisabStatus), nullable=False, default=RemessaSISABStatus.GERADO)
    cns_paciente: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    cpf_paciente: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
    ciap2: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    cid10: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    metodo_soap: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    logs_retorno: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_transmissao: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

# --- Repository ---
class RemessaSISABRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def create(self, data: RemessaSISABCreate) -> RemessaSISABRead:
        async with self.session_factory() as session:
            model = RemessaSISABModel(
                lote_id=data.lote_id,
                status=RemessaSISABStatus.GERADO,
                cns_paciente=data.cns_paciente,
                cpf_paciente=data.cpf_paciente,
                ciap2=data.ciap2,
                cid10=data.cid10,
                metodo_soab=data.metodo_soap, # typo fix: metodo_soap
                logs_retorno=data.logs_retorno,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return RemessaSISABRead.model_validate(model)

    async def get_by_id(self, remessa_id: uuid.UUID) -> Optional[RemessaSISABRead]:
        async with self.session_factory() as session:
            model = await session.get(RemessaSISABModel, remessa_id)
            return RemessaSISABRead.model_validate(model) if model else None

    async def update_status(self, remessa_id: uuid.UUID, new_status: RemessaSISABStatus) -> Optional[RemessaSISABRead]:
        async with self.session_factory() as session:
            model = await session.get(RemessaSISABModel, remessa_id)
            if not model:
                return None
            model.status = new_status
            await session.commit()
            await session.refresh(model)
            return RemessaSISABRead.model_validate(model)

    async def add_log(self, remessa_id: uuid.UUID, log_entry: str) -> Optional[RemessaSISABRead]:
        async with self.session_factory() as session:
            model = await session.get(RemessaSISABModel, remessa_id)
            if not model:
                return None
            current_logs = model.logs_retorno or ""
            model.logs_retorno = f"{current_logs}\n{log_entry}" if current_logs else log_entry
            await session.commit()
            await session.refresh(model)
            return RemessaSISABRead.model_validate(model)

    async def list_by_status(self, status: RemessaSISABStatus) -> Sequence[RemessaSISABRead]:
        async with self.session_factory() as session:
            stmt = sa.select(RemessaSISABModel).where(RemessaSISABModel.status == status)
            result = await session.execute(stmt)
            return [RemessaSISABRead.model_validate(m) for m in result.scalars().all()]

    async def delete(self, remessa_id: uuid.UUID) -> bool:
        async with self.session_factory() as session:
            model = await session.get(RemessaSISABModel, remessa_id)
            if not model:
                return False
            await session.delete(model)
            await session.commit()
            return True

