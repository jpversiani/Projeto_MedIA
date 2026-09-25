from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text
   from sqlalchemy.dialects.postgresql import UUID
   from sqlalchemy.orm import Mapped, mapped_column, relationship
   from sqlalchemy.sql import func
   import enum
   from app.core.database import Base # Assuming base exists, but I'll define it inline or import from a standard location. I'll use a standard setup.

from __future__ import annotations
   import enum
   import uuid
   from datetime import datetime
   from typing import Optional, List, AsyncGenerator
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from sqlalchemy import String, Integer, DateTime, Enum as SAEnum, ForeignKey, Text
   from sqlalchemy.dialects.postgresql import UUID
   from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
   from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
   from sqlalchemy import select, update, insert
   import asyncio

class Base(DeclarativeBase):
       pass

class RemessaStatus(str, enum.Enum):
       GERADO = "GERADO"
       ENVIADO = "ENVIADO"
       PROCESSADO = "PROCESSADO"
       REJEITADO = "REJEITADO"

class RemessaSISAB(Base):
       __tablename__ = "remessas_sisab"

       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       lote_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
       status: Mapped[RemessaStatus] = mapped_column(SAEnum(RemessaStatus), default=RemessaStatus.GERADO)
       total_registros: Mapped[int] = mapped_column(Integer, default=0)
       registros_sucesso: Mapped[int] = mapped_column(Integer, default=0)
       registros_erro: Mapped[int] = mapped_column(Integer, default=0)
       data_criacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       data_envio: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
       data_processamento: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
       data_ultima_atualizacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

       # SUS/APS Standards Metadata
       metodo_sus: Mapped[str] = mapped_column(String(20), default="SOAP")
       classificacao_ciap2: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
       classificacao_cid10: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
       identificacao_cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       identificacao_cpf: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)

       logs: Mapped[List["LogRetornoSISAB"]] = relationship(back_populates="remessa", cascade="all, delete-orphan")

   class LogRetornoSISAB(Base):
       __tablename__ = "log_retorno_sisab"

       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       remessa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("remessas_sisab.id", ondelete="CASCADE"), nullable=False)
       tipo: Mapped[str] = mapped_column(String(10), nullable=False) # INFO, WARN, ERROR, RETORNO
       mensagem: Mapped[str] = mapped_column(Text, nullable=False)
       codigo_retorno: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
       detalhes_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       data_criacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

       remessa: Mapped["RemessaSISAB"] = relationship(back_populates="logs")

class RemessaSISABCreate(BaseModel):
       lote_id: str = Field(..., min_length=1, max_length=50)
       total_registros: int = Field(..., ge=0)
       metodo_sus: str = Field(default="SOAP")
       classificacao_ciap2: Optional[str] = Field(None, max_length=10)
       classificacao_cid10: Optional[str] = Field(None, max_length=10)
       identificacao_cns: Optional[str] = Field(None, max_length=15)
       identificacao_cpf: Optional[str] = Field(None, max_length=14)

       @field_validator("identificacao_cpf")
       @classmethod
       def validate_cpf(cls, v):
           if v is not None:
               v = v.replace(".", "").replace("-", "")
               if not v.isdigit() or len(v) != 11:
                   raise ValueError("CPF deve conter 11 dígitos numéricos")
           return v

       @field_validator("identificacao_cns")
       @classmethod
       def validate_cns(cls, v):
           if v is not None:
               v = v.replace("-", "")
               if not v.isdigit() or len(v) != 15:
                   raise ValueError("CNS deve conter 15 dígitos numéricos")
           return v

   class RemessaSISABUpdate(BaseModel):
       status: Optional[RemessaStatus] = None
       registros_sucesso: Optional[int] = None
       registros_erro: Optional[int] = None
       data_envio: Optional[datetime] = None
       data_processamento: Optional[datetime] = None

   class LogRetornoSISABCreate(BaseModel):
       tipo: str = Field(..., pattern="^(INFO|WARN|ERROR|RETORNO)$")
       mensagem: str = Field(..., min_length=1)
       codigo_retorno: Optional[str] = None
       detalhes_xml: Optional[str] = None

   class RemessaSISABResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: uuid.UUID
       lote_id: str
       status: RemessaStatus
       total_registros: int
       registros_sucesso: int
       registros_erro: int
       data_criacao: datetime
       data_envio: Optional[datetime]
       data_processamento: Optional[datetime]
       data_ultima_atualizacao: datetime
       metodo_sus: str
       classificacao_ciap2: Optional[str]
       classificacao_cid10: Optional[str]
       identificacao_cns: Optional[str]
       identificacao_cpf: Optional[str]
       logs: List[LogRetornoSISABResponse] = []

   class LogRetornoSISABResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: uuid.UUID
       remessa_id: uuid.UUID
       tipo: str
       mensagem: str
       codigo_retorno: Optional[str]
       detalhes_xml: Optional[str]
       data_criacao: datetime

class RemessaSISABRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def create_remessa(self, dto: RemessaSISABCreate) -> RemessaSISAB:
           remessa = RemessaSISAB(
               lote_id=dto.lote_id,
               total_registros=dto.total_registros,
               metodo_sus=dto.metodo_sus,
               classificacao_ciap2=dto.classificacao_ciap2,
               classificacao_cid10=dto.classificacao_cid10,
               identificacao_cns=dto.identificacao_cns,
               identificacao_cpf=dto.identificacao_cpf,
           )
           self.session.add(remessa)
           await self.session.flush()
           await self.session.refresh(remessa)
           return remessa

       async def get_remessa_by_lote_id(self, lote_id: str) -> Optional[RemessaSISAB]:
           stmt = select(RemessaSISAB).where(RemessaSISAB.lote_id == lote_id)
           result = await self.session.execute(stmt)
           return result.scalar_one_or_none()

       async def update_status(self, remessa_id: uuid.UUID, status: RemessaStatus, **kwargs) -> RemessaSISAB:
           stmt = (
               update(RemessaSISAB)
               .where(RemessaSISAB.id == remessa_id)
               .values(status=status, **kwargs)
               .returning(RemessaSISAB)
           )
           result = await self.session.execute(stmt)
           await self.session.commit()
           return result.scalar_one()

       async def add_log(self, remessa_id: uuid.UUID, dto: LogRetornoSISABCreate) -> LogRetornoSISAB:
           log = LogRetornoSISAB(remessa_id=remessa_id, **dto.model_dump())
           self.session.add(log)
           await self.session.flush()
           await self.session.refresh(log)
           return log

       async def get_logs_by_remessa(self, remessa_id: uuid.UUID) -> List[LogRetornoSISAB]:
           stmt = select(LogRetornoSISAB).where(LogRetornoSISAB.remessa_id == remessa_id).order_by(LogRetornoSISAB.data_criacao)
           result = await self.session.execute(stmt)
           return list(result.scalars().all())

       async def get_remessa_with_logs(self, remessa_id: uuid.UUID) -> Optional[RemessaSISAB]:
           stmt = select(RemessaSISAB).options(
               sqlalchemy.orm.selectinload(RemessaSISAB.logs)
           ).where(RemessaSISAB.id == remessa_id)
           result = await self.session.execute(stmt)
           return result.scalar_one_or_none()

async def update_counts(self, remessa_id: uuid.UUID, sucesso: int, erro: int) -> RemessaSISAB:
       stmt = (
           update(RemessaSISAB)
           .where(RemessaSISAB.id == remessa_id)
           .values(registros_sucesso=sucesso, registros_erro=erro)
           .returning(RemessaSISAB)
       )
       result = await self.session.execute(stmt)
       await self.session.commit()
       return result.scalar_one()
