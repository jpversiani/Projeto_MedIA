"""Documentos clínicos emitidos (receita e atestado) com persistência definitiva.

Antes desta tabela, ``MotorPrescricaoCFM`` guardava os documentos emitidos num
dicionário em memória (``_REPOSITORIO_DOCUMENTOS_CFM``). Consequência prática:
ao reiniciar o processo, **todo QR Code/link de validação passava a responder
404** — a farmácia não conseguia conferir a receita e o paciente ficava com um
documento "não encontrado", o que é inaceitável sob a Resolução CFM 2.314/2022.

A tabela guarda o payload completo (para reemitir o PDF) e uma visão pública
mascarada (para a consulta de farmácia, sem expor CID nem CPF completo).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class DocumentoClinicoEmitido(Base):
    """Receita ou atestado emitido, com código público de validação."""

    __tablename__ = "documentos_clinicos"

    id = Column(Integer, primary_key=True, index=True)

    # Código que vai no QR Code (CFM-XXXX-XXXX-XXXX / ATE-XXXX-XXXX-XXXX).
    codigo_validacao = Column(String(32), unique=True, nullable=False, index=True)
    tipo_documento = Column(String(30), nullable=False, index=True)

    # Vínculos clínicos e de tenant.
    cidadao_id = Column(Integer, ForeignKey("cidadaos.id"), nullable=True, index=True)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=True)
    estabelecimento_id = Column(
        Integer, ForeignKey("estabelecimentos.id"), nullable=True, index=True
    )

    # Identificação impressa no documento (CFM exige nome + CRM/UF).
    paciente_nome = Column(String(200), nullable=False)
    paciente_cpf = Column(String(11), nullable=False, index=True)
    medico_nome = Column(String(200), nullable=False)
    medico_crm = Column(String(20), nullable=False)
    medico_uf = Column(String(2), nullable=False)
    medico_rqe = Column(String(30), nullable=True)

    data_emissao = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    hash_integridade_sha256 = Column(String(64), nullable=False)
    status = Column(String(20), default="VALIDA", nullable=False, index=True)

    # Conteúdo completo (itens, posologia, instruções) para regerar o PDF.
    payload_json = Column(JSON, nullable=True)
    # Visão mascarada servida ao validador público (farmácia/empregador).
    dados_consulta_publica = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    cidadao = relationship("Cidadao", foreign_keys=[cidadao_id])
    profissional = relationship("Profissional", foreign_keys=[profissional_id])
