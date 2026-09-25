```python
# Arquivo: backend/app/__init__.py
"""
Projeto MedIA - Backend para Agentes Comunitários de Saúde (ACS)
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF
"""
from . import config, models, schemas, routes, services
```

```python
# Arquivo: backend/app/config.py
"""
Configuração do projeto MedIA com SQLAlchemy 2.0 e Pydantic v2
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuração do projeto MedIA"""
    
    # Banco de Dados
    DATABASE_URL: str = "sqlite:///media.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # API
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "media-secret-key-change-in-production"
    DEBUG: bool = True
    
    # SUS/APS
    SUS_CNPJ: str = "000.000.000/0001-00"
    REGIONALITY: str = "01"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para o projeto MedIA
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean,
    ForeignKey, Enum, CheckConstraint, Index, UniqueConstraint
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship,
    validates, validates_source
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from enum import Enum as PyEnum
import uuid


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos"""
    pass


class SusType(Enum):
    """Tipos de SUS: CIAP-2 e CID-10"""
    CIAP_2 = "CIAP-2"
    CID_10 = "CID-10"
    SOAP = "SOAP"


class VisitType(Enum):
    """Tipos de visita domiciliar"""
    DOMICILAR = "DOMICILAR"
    TELEATENDIMENTO = "TELEATENDIMENTO"
    AVALIAÇÃO = "AVALIAÇÃO"
    SEGUINHO = "SEGUINHO"


class Priority(Enum):
    """Prioridade de visita"""
    URGENTE = "URGENTE"
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAIXA = "BAIXA"


class VisitStatus(Enum):
    """Status da visita"""
    AGENDADA = "AGENDADA"
    EM_PROGRESSO = "EM_PROGRESSO"
    COMPLETA = "COMPLETA"
    ANULADA = "ANULADA"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"


class TeleConsultationStatus(Enum):
    """Status da teleatendimento"""
    AGENDADA = "AGENDADA"
    EM_PROGRESSO = "EM_PROGRESSO"
    COMPLETA = "COMPLETA"
    REJEITADA = "REJEITADA"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"


class CommunityHealthAgent(Base):
    """
    Agente Comunitário de Saúde (ACS)
    Identificação por CNS/CPF conforme SUS
    """
    __tablename__ = "community_health_agents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cns = Column(String(11), unique=True, nullable=False, index=True)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    sobrenome = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    telefone = Column(String(20), nullable=False)
    estado = Column(String(2), nullable=False)
    municipio = Column(String(100), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relações
    visits = relationship("HomeVisit", back_populates="agent")
    teleconsultations = relationship("TeleConsultation", back_populates="agent")
    
    @validates_source("cpf")
    def validate_cpf(self, key, value):
        """Validação do CPF (11 dígitos)"""
        if len(value) != 11:
            raise ValueError("CPF deve ter exatamente 11 dígitos")
        return value
    
    @validates_source("cns")
    def validate_cns(self, key, value):
        """Validação do CNS (9 dígitos)"""
        if len(value) != 9:
            raise ValueError("CNS deve ter exatamente 9 dígitos")
        return value
    
    def __repr__(self):
        return f"<ACS {self.cns} - {self.nome} {self.sobrenome}>"


class HomeVisit(Base):
    """
    Visita Domicilar - Padrão SUS/APS
    CIAP-2, CID-10, SOAP, identificação por CNS/CPF
    """
    __tablename__ = "home_visits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cns = Column(String(11), nullable=False, index=True)
    cpf = Column(String(14), nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    sobrenome = Column(String(100), nullable=False)
    data_nascimento = Column(DateTime, nullable=True)
    data_nascimento_str = Column(String(10), nullable=True)
    gender = Column(String(1), nullable=False)  # M/F
    age = Column(Integer, nullable=True)
    
    # CIAP-2 e CID-10
    ciap2 = Column(String(5), nullable=True)  # Código de Identificação da Área de Prioridade 2
    cid10 = Column(String(10), nullable=True)  # Código de Identificação da Disease 10
    diagnosis = Column(Text, nullable=True)
    
    # SOAP
    soap_history = Column(Text, nullable=True)
    soap_assessment = Column(Text, nullable=True)
    soap_plan = Column(Text, nullable=True)
    
    # Prioridade e Status
    priority = Column(Enum(Priority), default=Priority.MEDIA, nullable=False)
    status = Column(Enum(VisitStatus), default=VisitStatus.AGENDADA, nullable=False)
    
    # Agendamento
    scheduled_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relações
    agent = relationship("CommunityHealthAgent", back_populates="visits")
    
    __table_args__ = (
        CheckConstraint("age >= 0", name="check_age"),
        CheckConstraint("gender IN ('M', 'F')", name="check_gender"),
        Index("ix_home_visit_cnpj", "cpf"),
        Index("ix_home_visit_priority_status", "priority", "status"),
    )
    
    @validates_source("cpf")
    def validate_cpf(self, key, value):
        if len(value) != 11:
            raise ValueError("CPF deve ter exatamente 11 dígitos")
        return value
    
    @validates_source("cns")
    def validate_cns(self, key, value):
        if len(value) != 9:
            raise ValueError("CNS deve ter exatamente 9 dígitos")
        return value
    
    def __repr__(self):
        return f"<Visit {self.id} - {self.nome} {self.sobrenome} [{self.priority.value}]>"


class TeleConsultation(Base):
    """
    Teleatendimento - Padrão SUS/APS
    CIAP-2, CID-10, SOAP, identificação por CNS/CPF
    """
    __tablename__ = "teleconsultations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cns = Column(String(11), nullable=False, index=True)
    cpf = Column(String(14), nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    sobrenome = Column(String(100), nullable=False)
    data_nascimento = Column(DateTime, nullable=True)
    data_nascimento_str = Column(String(10), nullable=True)
    gender = Column(String(1), nullable=False)
    age = Column(Integer, nullable=True)
    
    # CIAP-2 e CID-10
    ciap2 = Column(String(5), nullable=True)
    cid10 = Column(String(10), nullable=True)
    diagnosis = Column(Text, nullable=True)
    
    # SOAP
    soap_history = Column(Text, nullable=True)
    soap_assessment = Column(Text, nullable=True)
    soap_plan = Column(Text, nullable=True)
    
    # Tipo e Status
    visit_type = Column(Enum(VisitType), default=VisitType.TELEATENDIMENTO, nullable=False)
    status = Column(Enum(TeleConsultationStatus), default=TeleConsultationStatus.AGENDADA, nullable=False)
    
    # Agendamento
    scheduled_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relações
    agent = relationship("CommunityHealthAgent", back_populates="teleconsultations")
    
    __table_args__ = (
        CheckConstraint("age >= 0", name="check_age"),
        CheckConstraint("gender IN ('M', 'F')", name="check_gender"),
        Index("ix_teleconsultation_cnpj", "cpf"),
        Index("ix_teleconsultation_priority_status", "status"),
    )
    
    @validates_source("cpf")
    def validate_cpf(self, key, value):
        if len(value) != 11:
            raise ValueError("CPF deve ter exatamente 11 dígitos")
        return value
    
    @validates_source("cns")
    def validate_cns(self, key, value):
        if len(value) != 9:
            raise ValueError("CNS deve ter exatamente 9 dígitos")
        return value
    
    def __repr__(self):
        return f"<TeleConsultation {self.id} - {self.nome} {self.sobrenome} [{self.status.value}]>"


class Campaign(Base):
    """
    Campanha de Saúde - Padrão SUS/APS
    CIAP-2, CID-10, SOAP, identificação por CNS/CPF
    """
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    ciap2 = Column(String(5), nullable=True)
    cid10 = Column(String(10), nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relações
    visits = relationship("HomeVisit", back_populates="campaign")
    teleconsultations = relationship("TeleConsultation", back_populates="campaign")
    
    def __repr__(self):
        return f"<Campaign {self.id} - {self.name} [{self.start_date.date()} - {self.end_date.date()}]>"


class HomeVisitCampaign(Base):
    """
    Relação entre visita e campanha
    """
    __tablename__ = "home_visit_campaigns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    visit_id = Column(Integer, ForeignKey("home_visits.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIA, nullable=False)
    scheduled_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    __table_args__ = (
        UniqueConstraint("visit_id", "campaign_id", name="uq_visit_campaign"),
        Index("ix_home_visit_campaign_priority", "priority"),
    )
    
    visit = relationship("HomeVisit", back_populates="campaigns")
    campaign = relationship("Campaign", back_populates="visits")


class TeleConsultationCampaign(Base):
    """
    Relação entre teleconsultação e campanha
    """
    __tablename__ = "teleconsultation_campaigns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    consultation_id = Column(Integer, ForeignKey("teleconsultations.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIA, nullable=False)
    scheduled_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    __table_args__ = (
        UniqueConstraint("consultation_id", "campaign_id", name="uq_consultation_campaign"),
        Index("ix_teleconsultation_campaign_priority", "priority"),
    )
    
    consultation = relationship("TeleConsultation", back_populates="campaigns")
    campaign = relationship("Campaign", back_populates="teleconsultations")
```

```python
# Arquivo: backend/app/schemas.py
"""
Esquemas Pydantic v2 para validação de dados
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import re


class AgentCNPJ(BaseModel):
    """Identificação do Agente Comunitário de Saúde"""
    cns: str = Field(..., min_length=9, max_length=9, description="CNS do agente")
    cpf: str = Field(..., min_length=11, max_length=11, description="CPF do agente")
    nome: str = Field(..., min_length=1, max_length=100, description="Nome do agente")
    sobrenome: str = Field(..., min_length=1, max_length=100, description="Sobrenome do agente")
    email: str = Field(..., max_length=255, description="E-mail do agente")
    telefone: str = Field(..., min_length=10, max_length=20, description="Telefone do agente")