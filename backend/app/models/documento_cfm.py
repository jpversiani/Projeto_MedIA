"""Modelo SQLAlchemy para persistência de Receitas e Atestados CFM.

Garante durabilidade e integridade legal aos documentos médicos eletrônicos emitidos,
substituindo repositórios voláteis em memória e vinculando os documentos aos atendimentos e cidadãos.
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class DocumentoCFM(Base):
    """Documento médico emitido segundo padrões CFM 2.314/2022."""

    __tablename__ = "documentos_cfm"

    id = Column(Integer, primary_key=True, index=True)
    codigo_validacao = Column(String(30), unique=True, nullable=False, index=True)
    tipo = Column(String(20), nullable=False)          # RECEITA | ATESTADO
    status = Column(String(20), nullable=False)         # VALIDA | VALIDO | REVOGADO | CANCELADO
    hash_integridade_sha256 = Column(String(64), nullable=False)

    # Vínculos clínicos
    atendimento_id = Column(Integer, ForeignKey("atendimentos_soap.id"), nullable=True, index=True)
    cidadao_id = Column(Integer, ForeignKey("cidadaos.id"), nullable=True, index=True)

    # Identificação do profissional
    medico_nome = Column(String(200), nullable=False)
    medico_crm = Column(String(20), nullable=False)
    medico_uf = Column(String(2), nullable=False)
    medico_rqe = Column(String(20), nullable=True)

    # Identificação do paciente
    paciente_nome = Column(String(200), nullable=False)
    paciente_cpf = Column(String(11), nullable=False, index=True)

    conteudo = Column(JSON, nullable=False)   # dados estruturados: itens, instruções, dias, cid, etc.
    data_emissao = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    atendimento = relationship("AtendimentoSOAP", foreign_keys=[atendimento_id])
    cidadao = relationship("Cidadao", foreign_keys=[cidadao_id])
