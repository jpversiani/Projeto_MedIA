from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from app.core.crypto import CampoProtegido
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


class ConsentimentoTeleconsulta(Base):
    """Consentimento livre e esclarecido (TCLE) de uma teleconsulta.

    A Resolução CFM nº 2.314/2022 (Art. 4º, § 2º) exige consentimento prévio,
    livre e esclarecido do paciente **antes** da teleconsulta. Antes desta
    tabela o aceite virava um dataclass em memória e morria na resposta HTTP:
    não havia prova persistida do consentimento e `/iniciar-chamada` iniciava
    mesmo sem ele — uma lacuna de conformidade e de auditoria.

    Agora o aceite é gravado com o texto, o hash SHA-256, o método e o IP de
    origem, e o início da chamada passa a exigir um registro vigente.
    """

    __tablename__ = "consentimentos_teleconsulta"

    id = Column(Integer, primary_key=True, index=True)
    # Código público do termo (TCLE-AAAAMMDD-XXXXXXXX), usado para referência.
    codigo = Column(String(40), unique=True, nullable=False, index=True)
    teleconsulta_id = Column(
        Integer, ForeignKey("teleconsultas.id"), nullable=True, index=True
    )
    # Identificação do paciente (cifrada como no resto do módulo).
    paciente_nome = Column(String(200), nullable=False)
    paciente_cpf = Column(CampoProtegido, nullable=True, index=True)

    texto_integral = Column(Text, nullable=False)
    hash_integridade_sha256 = Column(String(64), nullable=False)
    # Aceite eletrônico: ELETRONICO_WEB, ELETRONICO_WHATSAPP, ELETRONICO_SMS,
    # VERBAL_GRAVADO...
    metodo_aceite = Column(String(40), nullable=False)
    ip_origem = Column(String(45), nullable=True)
    data_aceite = Column(DateTime, nullable=False)

    teleconsulta = relationship("Teleconsulta", back_populates="consentimentos")


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
    paciente_cpf = Column(CampoProtegido, nullable=True, index=True)
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
    consentimentos = relationship(
        "ConsentimentoTeleconsulta", back_populates="teleconsulta", cascade="all, delete-orphan"
    )


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
