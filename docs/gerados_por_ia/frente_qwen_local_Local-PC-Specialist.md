```python
# Arquivo: backend/app/models/telemedicina.py
"""
Módulo de Modelagem de Dados para Telemedicina (SUS Compliance)
Diretrizes atendidas:
- DIR 1: Isolamento de módulo. Operações de escrita devem ser envoltas por FileLockManager no repositório.
- DIR 2: Python 3.12, SQLAlchemy 2.0 (mapped_column/Mapped) e Pydantic v2 (validação/serialização).
- DIR 3: Terminologias CIAP-2/CID-10, método SOAP, identificação CNS/CPF conforme e-SUS.
- DIR 4: Suporte a salas virtuais, evolução clínica remota e emissão de documentos digitais.
- DIR 5: Estrutura otimizada para testes unitários/integração com pytest (fixtures, mocks, transações).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from uuid import uuid4, UUID
from enum import Enum as PyEnum

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SqlEnum, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import BaseModel, Field, ConfigDict, field_validator, EmailStr

if TYPE_CHECKING:
    from backend.app.models.cidadao import Cidadao
    from backend.app.models.profissional import Profissional

# =============================================================================
# Base & Enums
# =============================================================================

class Base(DeclarativeBase):
    """Base declarativa SQLAlchemy 2.0 para todo o domínio."""
    pass


class TeleconsultaStatus(str, PyEnum):
    """Status da teleconsulta conforme fluxo SUS."""
    AGENDADA = "agendada"
    EM_ANDAMENTO = "em_andamento"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"


class DocumentoTipo(str, PyEnum):
    """Tipos de documentos digitais emitíveis."""
    PRESCRICAO = "prescricao"
    ATESTADO = "atestado"
    RELATORIO_CLINICO = "relatorio"


# =============================================================================
# Modelos SQLAlchemy 2.0
# =============================================================================

class SalaVirtual(Base):
    """
    Representa a infraestrutura de vídeo/áudio da teleconsulta.
    Mantém isolamento de estado e código de acesso para controle de entrada.
    """
    __tablename__ = "salas_virtuais"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    codigo_sala: Mapped[str] = mapped_column(String(16), unique=True, index=True, comment="Código de acesso à sala (ex: ABC123XYZ)")
    status: Mapped[TeleconsultaStatus] = mapped_column(default=TeleconsultaStatus.AGENDADA)
    teleconsulta_id: Mapped[UUID] = mapped_column(ForeignKey("teleconsultas.id", ondelete="CASCADE"))
    
    # Relacionamento
    teleconsulta: Mapped["Teleconsulta"] = relationship(back_populates="sala")

    # Timestamps
    criado_em: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    atualizado_em: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<SalaVirtual(id={self.id}, codigo={self.codigo_sala}, status={self.status.value})>"


class Teleconsulta(Base):
    """
    Entidade central da teleconsulta. Armazena evolução SOAP, códigos de morbidade
    e relaciona Cidadão e Profissional conforme diretrizes do e-SUS Atenção Básica.
    """
    __tablename__ = "teleconsultas"

    id: Mapped[