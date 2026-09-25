from sqlalchemy import String, Text, DateTime, Boolean, Enum, JSON, ForeignKey
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
   from sqlalchemy.sql import func
   import enum

   class Base(DeclarativeBase):
       pass

   class StatusDisparo(str, enum.Enum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       ENTREGUE = "entregue"
       CONFIRMADO = "confirmado"
       FALHA = "falha"

   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[int] = mapped_column(primary_key=True)
       nome: Mapped[str] = mapped_column(String(100))
       descricao: Mapped[str] = mapped_column(Text)
       codigos_ciap2: Mapped[list[str]] = mapped_column(JSON)
       codigos_cid10: Mapped[list[str]] = mapped_column(JSON)
       status: Mapped[str] = mapped_column(String(20), default="ativa")
       data_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
       data_fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))
       criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

   class Disparo(Base):
       __tablename__ = "disparos"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"))
       cns_paciente: Mapped[str] = mapped_column(String(15))
       cpf_paciente: Mapped[str] = mapped_column(String(14))
       conteudo_mensagem: Mapped[str] = mapped_column(Text)
       status_envio: Mapped[StatusDisparo] = mapped_column(Enum(StatusDisparo), default=StatusDisparo.PENDENTE)
       data_envio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
       data_confirmacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
       notas_soap: Mapped[dict] = mapped_column(JSON, nullable=True)
       criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

   class LogAuditoriaLGPD(Base):
       __tablename__ = "logs_auditoria_lgpd"
       id: Mapped[int] = mapped_column(primary_key=True)
       entidade_tipo: Mapped[str] = mapped_column(String(50))
       entidade_id: Mapped[int] = mapped_column(Integer)
       acao: Mapped[str] = mapped_column(String(50))
       usuario_id: Mapped[int] = mapped_column(Integer, nullable=True)
       ip_origem: Mapped[str] = mapped_column(String(45), nullable=True)
       justificativa_lgpd: Mapped[str] = mapped_column(Text)
       data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

# Arquivo: backend/app/repositories/campanhas_repo.py
   import enum
   from datetime import datetime, timezone
   from typing import Optional, List, Dict, Any
   from uuid import uuid4

   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from pydantic.v2 import EmailStr # Not needed
   from sqlalchemy import String, Text, DateTime, Boolean, Enum, JSON, ForeignKey, Integer
   from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, update, delete
   from sqlalchemy.sql import func
   import re

   # Base
   class Base(DeclarativeBase):
       pass

   # Enums
   class StatusDisparo(str, enum.Enum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       ENTREGUE = "entregue"
       CONFIRMADO = "confirmado"
       FALHA = "falha"

   # Models
   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[int] = mapped_column(primary_key=True)
       nome: Mapped[str] = mapped_column(String(100))
       descricao: Mapped[str] = mapped_column(Text)
       codigos_ciap2: Mapped[list[str]] = mapped_column(JSON)
       codigos_cid10: Mapped[list[str]] = mapped_column(JSON)
       status: Mapped[str] = mapped_column(String(20), default="ativa")
       data_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
       data_fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))
       criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

   class Disparo(Base):
       __tablename__ = "disparos"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"))
       cns_paciente: Mapped[str] = mapped_column(String(15))
       cpf_paciente: Mapped[str] = mapped_column(String(14))
       conteudo_mensagem: Mapped[str] = mapped_column(Text)
       status_envio: Mapped[StatusDisparo] = mapped_column(Enum(StatusDisparo), default=StatusDisparo.PENDENTE)
       data_envio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
       data_confirmacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
       notas_soap: Mapped[dict] = mapped_column(JSON, nullable=True)
       criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

   class LogAuditoriaLGPD(Base):
       __tablename__ = "logs_auditoria_lgpd"
       id: Mapped[int] = mapped_column(primary_key=True)
       entidade_tipo: Mapped[str] = mapped_column(String(50))
       entidade_id: Mapped[int] = mapped_column(Integer)
       acao: Mapped[str] = mapped_column(String(50))
       usuario_id: Mapped[int] = mapped_column(Integer, nullable=True)
       ip_origem: Mapped[str] = mapped_column(String(45), nullable=True)
       justificativa_lgpd: Mapped[str] = mapped_column(Text)
       data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class CampanhasRepository:
       def __init__(self, session: AsyncSession):
           self.session = session

       async def criar_campanha(self, schema: CampanhaCreate) -> Campanha:
           # audit log
           await self._registrar_auditoria("CAMPAIGN", None, "CREATE", schema.criado_por, schema.ip_origem, "Criação de campanha de saúde pública")
           campanha = Campanha(**schema.model_dump())
           self.session.add(campanha)
           await self.session.flush()
           return campanha

       async def registrar_disparo(self, campanha_id: int, schema: DisparoCreate) -> Disparo:
           # check campaign exists
           # insert
           # audit
           ...
