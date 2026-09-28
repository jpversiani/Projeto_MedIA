from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class StatusTeleconsulta(str, Enum):
    AGENDADA = "AGENDADA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"
    SUSPENSA = "SUSPENSA"


class TipoDocumento(str, Enum):
    RECEITA = "RECEITA"
    ATESTADO = "ATESTADO"
    LAUDO = "LAUDO"


class SalaVirtual(Base):
    __tablename__ = "salas_virtuais"

    id = Column(Integer, primary_key=True, index=True)
    codigo_sala = Column(String(64), unique=True, nullable=False, index=True)
    url_video = Column(String(512), nullable=True)
    status = Column(SAEnum(StatusTeleconsulta), default=StatusTeleconsulta.EM_ANDAMENTO)
    data_criacao = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    data_expiracao = Column(DateTime, nullable=True)

    teleconsulta = relationship("Teleconsulta", back_populates="sala_virtual", uselist=False)


class Teleconsulta(Base):
    __tablename__ = "teleconsultas"

    id = Column(Integer, primary_key=True, index=True)
    cidadao_id = Column(Integer, ForeignKey("cidadaos.id"), nullable=True)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=True)
    sala_virtual_id = Column(Integer, ForeignKey("salas_virtuais.id"), nullable=True)
    paciente_cpf = Column(String(11), nullable=True, index=True)
    medico_crm = Column(String(6), nullable=True)
    status = Column(SAEnum(StatusTeleconsulta), default=StatusTeleconsulta.AGENDADA)
    data_inicio = Column(DateTime, nullable=True)
    data_fim = Column(DateTime, nullable=True)
    motivo_consulta = Column(Text, nullable=True)
    diagnostico_ciap2 = Column(String(10), nullable=True)
    diagnostico_cid10 = Column(String(10), nullable=True)
    evolucao_soap = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    cidadao = relationship("Cidadao", backref="teleconsultas", foreign_keys=[cidadao_id])
    profissional = relationship("Profissional", backref="teleconsultas", foreign_keys=[profissional_id])
    sala_virtual = relationship("SalaVirtual", back_populates="teleconsulta", foreign_keys=[sala_virtual_id])
    documentos = relationship("DocumentoEmitido", back_populates="teleconsulta", cascade="all, delete-orphan")


class DocumentoEmitido(Base):
    __tablename__ = "documentos_emitidos"

    id = Column(Integer, primary_key=True, index=True)
    teleconsulta_id = Column(Integer, ForeignKey("teleconsultas.id"), nullable=False)
    tipo_documento = Column(SAEnum(TipoDocumento), nullable=False)
    conteudo = Column(JSON, nullable=False)
    hash_assinatura = Column(String(64), nullable=True)
    status = Column(String(20), default="EMITIDO")
    data_emissao = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    teleconsulta = relationship("Teleconsulta", back_populates="documentos")
