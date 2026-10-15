from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from app.core import database

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship


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


class SalaVirtual(database.Base):
    __tablename__ = "salas_virtuais"

    id = Column(Integer, primary_key=True, index=True)
    codigo_sala = Column(String(64), unique=True, nullable=False, index=True)
    url_video = Column(String(512), nullable=True)
    status = Column(SAEnum(StatusTeleconsulta), default=StatusTeleconsulta.EM_ANDAMENTO)
    data_criacao = Column(DateTime, default=lambda: datetime.now(UTC))
    data_expiracao = Column(DateTime, nullable=True)

    teleconsulta = relationship(
        "Teleconsulta", back_populates="sala_virtual", uselist=False
    )


class Teleconsulta(database.Base):
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
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    cidadao = relationship("Cidadao", backref="teleconsultas", foreign_keys=[cidadao_id])
    profissional = relationship(
        "Profissional", backref="teleconsultas", foreign_keys=[profissional_id]
    )
    sala_virtual = relationship(
        "SalaVirtual", back_populates="teleconsulta", foreign_keys=[sala_virtual_id]
    )
    documentos = relationship(
        "DocumentoEmitido",
        back_populates="teleconsulta",
        cascade="all, delete-orphan",
    )
    consentimentos = relationship(
        "ConsentimentoTCLE",
        back_populates="teleconsulta",
        cascade="all, delete-orphan",
    )


class ConsentimentoTCLE(database.Base):
    """Registro legal de consentimento livre e esclarecido (CFM 2.314/2022 e LGPD)."""
    __tablename__ = "consentimentos_tcle"

    id = Column(Integer, primary_key=True, index=True)
    codigo_tcle = Column(String(32), unique=True, nullable=False, index=True)
    teleconsulta_id = Column(Integer, ForeignKey("teleconsultas.id"), nullable=True, index=True)
    cidadao_id = Column(Integer, ForeignKey("cidadaos.id"), nullable=True, index=True)
    paciente_cpf = Column(String(11), nullable=False, index=True)
    paciente_nome = Column(String(255), nullable=True)
    versao_termo = Column(String(32), default="CFM_2314_2022_V1", nullable=False)
    texto_integral = Column(Text, nullable=False)
    hash_sha256 = Column(String(64), nullable=False, index=True)
    ip_origem = Column(String(45), nullable=False)
    user_agent = Column(String(512), nullable=True)
    metodo_aceite = Column(String(64), default="ELETRONICO_WEB", nullable=False)
    aceito_em = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    teleconsulta = relationship("Teleconsulta", back_populates="consentimentos")
    cidadao = relationship("Cidadao", backref="consentimentos_tcle", foreign_keys=[cidadao_id])


class DocumentoEmitido(database.Base):
    __tablename__ = "documentos_emitidos"

    id = Column(Integer, primary_key=True, index=True)
    teleconsulta_id = Column(Integer, ForeignKey("teleconsultas.id"), nullable=False)
    tipo_documento = Column(SAEnum(TipoDocumento), nullable=False)
    conteudo = Column(JSON, nullable=False)
    hash_assinatura = Column(String(64), nullable=True)
    status = Column(String(20), default="EMITIDO")
    data_emissao = Column(DateTime, default=lambda: datetime.now(UTC))

    teleconsulta = relationship("Teleconsulta", back_populates="documentos")

