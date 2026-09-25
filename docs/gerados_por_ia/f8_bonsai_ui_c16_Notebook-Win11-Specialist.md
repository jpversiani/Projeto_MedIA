# Painel de Campanhas de Busca Ativa da Comunidade (C16)

## 1. Modelo de Banco de Dados (SQLAlchemy 2.0)

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para o sistema MedIA - Atenção Primária / Saúde da Família.
Tipagem estrita, compatível com Python 3.12.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

Base = declarative_base()


class EstadoVisita(str, enum.Enum):
    """Estado do registro de visita domiciliar."""
    AGENDADA = "agendada"
    EM_PROGRESSO = "em_progresso"
    COMPLETA = "completa"
    ANULADA = "anulada"
    PENDENTE = "pendente"


class EstadoTeleatendimento(str, enum.Enum):
    """Estado do registro de teleatendimento."""
    AGENDADA = "agendada"
    EM_PROGRESSO = "em_progresso"
    COMPLETA = "completa"
    ANULADA = "anulada"
    PENDENTE = "pendente"


class TipoCampanha(str, enum.Enum):
    """Tipo de campanha de busca ativa."""
    VACINA = "vacina"
    PREVENCAO = "prevencao"
    SCREENING = "screening"
    ATENCAO_PRIMARIA = "atencao_primaria"
    SAUDE_DA_FAMILIA = "saude_da_familia"
    MONITORAÇÃO_CRONICA = "monitoracao_cronica"
    ATENCAO_PEDIATRICA = "atencao_pediatrica"
    ATENCAO_GERINARIA = "atencao_gerinaria"


class EstadoCampanha(str, enum.Enum):
    """Estado da campanha."""
    ATIVA = "ativa"
    ENCERRADA = "encerrada"
    PANDA = "panda"
    PAUSA = "pausa"


class CommunityHealthAgent(Base):
    """
    Agente Comunitário de Saúde (ACS).
    Responsável por visitas domiciliares e coordenação de teleatendimentos.
    """

    __tablename__ = "agents"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    sobrenome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    telefone: Mapped[str] = mapped_column(String(20), nullable=False)
    codigo_saude: Mapped[str] = mapped_column(String(20), nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    campanhas: Mapped[list["Campaign"]] = mapped_column(
        relationship("Campaign", back_populates="agent", lazy="selectin")
    )


class Campaign(Base):
    """
    Campanha de busca ativa da comunidade.
    Representa um evento de saúde (vaccinação, screening, etc.)
    que requer coordenação de visitas domiciliares e teleatendimentos.
    """

    __tablename__ = "campaigns"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tipo: Mapped[TipoCampanha] = mapped_column(
        Enum(TipoCampanha), nullable=False
    )
    estado: Mapped[EstadoCampanha] = mapped_column(
        Enum(EstadoCampanha), default=EstadoCampanha.ACTIVA
    )
    data_inicio: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_fim: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    agente_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    agente: Mapped["CommunityHealthAgent"] = mapped_column(
        relationship("CommunityHealthAgent", back_populates="campanhas")
    )
    visitas_agendadas: Mapped[int] = mapped_column(Integer, default=0)
    teleatendidos_agendados: Mapped[int] = mapped_column(Integer, default=0)
    visitas_completadas: Mapped[int] = mapped_column(Integer, default=0)
    teleatendidos_completados: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    visitas: Mapped[list["HomeVisit"]] = mapped_column(
        relationship("HomeVisit", back_populates="campaign", lazy="selectin")
    )
    teleatendimentos: Mapped[list["TeleConsultation"]] = mapped_column(
        relationship("TeleConsultation", back_populates="campaign", lazy="selectin")
    )


class HomeVisit(Base):
    """
    Registro de visita domiciliar.
    Prioridade baseada em critério clínico: gravidade, idade, comorbidades.
    """

    __tablename__ = "home_visits"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    campaign_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    campaign: Mapped["Campaign"] = mapped_column(
        relationship("Campaign", back_populates="visitas")
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    sobrenome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    telefone: Mapped[str] = mapped_column(String(20), nullable=False)
    data_nascimento: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    idade: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[EstadoVisita] = mapped_column(
        Enum(EstadoVisita), default=EstadoVisita.AGENDADA
    )
    prioridade: Mapped[int] = mapped_column(Integer, nullable=False)
    # Prioridade: 1 = mais alta, 10 = mais baixa
    # Cálculo: base 5 + (idade > 60) + (comorbidades) + (urgência)
    comorbidades: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    motivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nota_clinica: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_hora_visita: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    estado_do_visitante: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class TeleConsultation(Base):
    """
    Registro de teleatendimento.
    Confirmação de consulta virtual para pacientes que não podem ou não querem
    visitar fisicamente.
    """

    __tablename__ = "tele_consultations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    campaign_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    campaign: Mapped["Campaign"] = mapped_column(
        relationship("Campaign", back_populates="teleatendimentos")
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    sobrenome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    telefone: Mapped[str] = mapped_column(String(20), nullable=False)
    data_nascimento: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    idade: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[EstadoTeleatendimento] = mapped_column(
        Enum(EstadoTeleatendimento), default=EstadoTeleatendimento.AGENDADA
    )
    prioridade: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nota_clinica: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_hora_consulta: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# Utility para UUID
import uuid as uuid_module


def init_db(url: str) -> None:
    """Inicializa o banco de dados com as tabelas."""
    engine = create_engine(url, echo=False)
    Base.metadata.create_all(bind=engine)


# Exemplo de sessão para uso em testes
SessionLocal = sessionmaker(autocommit=False, autoflush=False)
```

---

## 2. Esquemas Pydantic v2

```python
# Arquivo: backend/app/schemas.py
"""
Esquemas de validação com Pydantic v2.
Tipagem estrita, compatível com Python 3.12.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# --- Enums ---

class EstadoVisitaEnum(str):
    AGENDADA = "agendada"
    EM_PROGRESSO = "em_progresso"
    COMPLETA = "completa"
    ANULADA = "anulada"
    PENDENTE = "pendente"


class EstadoTeleatendimentoEnum(str):
    AGENDADA = "agendada"
    EM_PROGRESSO = "em_progresso"
    COMPLETA = "completa"
    ANULADA = "anulada"
    PENDENTE = "pendente"


class TipoCampanhaEnum(str):
    VACINA = "vacina"
    PREVENCAO = "prevencao"
    SCREENING = "screening"
    ATENCAO_PRIMARIA = "atenacao_primaria"
    SAUDE_DA_FAMILIA = "saude_da_familia"
    MONITORAÇÃO_CRONICA = "monitoracao_cronica"
    ATENCAO_PEDIATRICA = "atencao_pediatrica"
    ATENCAO_GERINARIA = "atencao_gerinaria"


class EstadoCampanhaEnum(str):
    ATIVA = "ativa"
    ENCERRADA = "encerrada"
    PANDA = "panda"
    PAUSA = "pausa"


# --- Agentes ---

class CommunityHealthAgentCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    sobrenome: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=1, max_length=255)
    telefone: str = Field(..., min_length=1, max_length=20)
    codigo_saude: str = Field(..., min_length=1, max_length=20)
    estado: bool = True


class CommunityHealthAgentResponse(BaseModel):
    id: str
    nome: str
    sobrenome: str
    email: str
    telefone: str
    codigo_saude: str
    estado: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Campanhas ---

class CampaignCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=200)
    descricao: Optional[str] = Field(None, max_length=5000)
    tipo: TipoCampanhaEnum
    estado: EstadoCampanhaEnum = EstadoCampanhaEnum