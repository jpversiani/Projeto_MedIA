# Backend: Painel Visual da Triagem e Monitor de Fila APS (C91)

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── schemas.py
│   ├── services.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── triagem.py
│   ├── static/
│   │   └── painel_triagem.html
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_models.py
│       ├── test_schemas.py
│       ├── test_services.py
│       └── test_api.py
├── requirements.txt
└── pytest.ini
```

---

## Arquivo: `backend/app/__init__.py`

```python
# Arquivo: backend/app/__init__.py
"""
Aplicação backend para o Projeto MedIA.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF.
"""
from . import config
from . import models
from . import schemas
from . import services
from . import api

__version__ = "1.0.0"
__all__ = ["config", "models", "schemas", "services", "api"]
```

---

## Arquivo: `backend/app/config.py`

```python
# Arquivo: backend/app/config.py
"""
Configuração da aplicação backend.
Suporte a Python 3.12, Pydantic v2, SQLAlchemy 2.0.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF.
"""
from __future__ import annotations

import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Configuração da aplicação com validação estrita."""

    # --- Database ---
    DATABASE_URL: str = Field(
        default="sqlite:///media_aps.db",
        description="URL da banco de dados (PostgreSQL/SQLite)",
    )
    DATABASE_POOL_SIZE: int = Field(default=10, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=20, ge=0)
    DATABASE_ECHO: bool = Field(default=False)

    # --- API ---
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000, ge=1024, le=65535)
    API_DEBUG: bool = Field(default=False)
    API_PREFIX: str = Field(default="/api/v1")

    # --- SUS/APS ---
    CIAP_CODE: str = Field(default="01000000", description="Código CIAP da instituição")
    CID_CODE: str = Field(default="00000", description="Código CID da instituição")
    SOAP_PROTOCOL: str = Field(default="SOAP", description="Protocolo SOAP")
    IDENTIFICATION_METHOD: str = Field(
        default="CNS",
        description="Método de identificação (CNS ou CPF)",
    )

    # --- Triage ---
    TRIAGE_TIMEOUT_SECONDS: int = Field(
        default=300, ge=10, le=3600, description="Timeout da fila em segundos"
    )
    SOUND_CALL_INTERVAL_SECONDS: int = Field(
        default=60, ge=10, le=300, description="Intervalo para chamada sonora"
    )

    # --- Logging ---
    LOG_LEVEL: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
```

---

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para o Projeto MedIA.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Base declarativa SQLAlchemy 2.0."""


class TriagePriority(enum.Enum):
    """Níveis de prioridade de triagem (padrão SUS/APS)."""
    CRITICO = "CRITICO"  # Vermelho - Immediato
    URGENTE = "URGENTE"  # Amarelo - Prioritário
    ESTÁVEL = "ESTÁVEL"  # Verde - Roteiro
    OBSERVACAO = "OBSERVACAO"  # Azul - Observação


class PatientIdentification(enum.Enum):
    """Método de identificação do paciente."""
    CNS = "CNS"
    CPF = "CPF"


class Patient(Base):
    """
    Modelo do Paciente.
    Identificação por CNS/CPF conforme padrão SUS/APS.
    """
    __tablename__ = "pacientes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    identificador: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False,
        comment="CNS ou CPF do paciente"
    )
    identificador_type: Mapped[PatientIdentification] = mapped_column(
        Enum(PatientIdentification), nullable=False, default=PatientIdentification.CNS
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    data_nascimento: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="ativo", nullable=False,
        comment="Status do paciente na fila"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    fila: Mapped["Fila"] = relationship(
        "Fila", back_populates="paciente", uselist=False
    )


class Fila(Base):
    """
    Modelo da Fila de Triagem.
    Monitor de fila APS (C91) com tempo de espera e chamada sonora.
    """
    __tablename__ = "filas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[TriagePriority] = mapped_column(
        Enum(TriagePriority), nullable=False, default=TriagePriority.ESTÁVEL
    )
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    current_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_call_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="Próxima chamada sonora para o próximo paciente"
    )
    last_call_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="Última chamada sonora realizada"
    )
    sound_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Chamada sonora habilitada"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    pacientes: Mapped[list["PacienteFila"]] = relationship(
        "PacienteFila", back_populates="fila", cascade="all, delete-orphan"
    )


class PacienteFila(Base):
    """
    Modelo do Paciente na Fila.
    Vincula paciente à fila com tempo de espera.
    """
    __tablename__ = "pacientes_fila"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    fila_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
        comment="ID da fila"
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
        comment="ID do paciente"
    )
    ordem_na_fila: Mapped[int] = mapped_column(Integer, nullable=False)
    tempo_espera: Mapped[int] = mapped_column(
        Integer, default=0, comment="Tempo de espera em minutos"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="esperando", nullable=False
    )
    identificador: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="CNS ou CPF do paciente"
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[TriagePriority] = mapped_column(
        Enum(TriagePriority), nullable=False, default=TriagePriority.ESTÁVEL
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    fila: Mapped[Fila] = relationship(
        "Fila", back_populates="pacientes"
    )
    paciente: Mapped[Patient] = relationship(
        "Patient", back_populates="fila"
    )

    __table_args__ = (
        UniqueConstraint("fila_id", "ordem_na_fila", name="uq_fila_ordem"),
    )


class Nurse(Base):
    """
    Modelo da Equipe de Enfermagem.
    Monitor de fila APS (C91) com painel para equipe.
    """
    __tablename__ = "enfermeiros"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    identificador: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False,
        comment="CNS ou CPF do enfermeiro"
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    cargo: Mapped[str] = mapped_column(String(50), nullable=False)
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="disponivel", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class SOAPRecord(Base):
    """
    Modelo de Registro SOAP (Sick Note).
    Padrão SOAP: Subjective, Objective, Assessment, Plan.
    """
    __tablename__ = "registros_soap"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    identificador: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="CNS ou CPF do paciente"
    )
    subjective: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    assessment: Mapped[str] = mapped_column(Text, nullable=False)
    plan: Mapped[str] = mapped_column(Text, nullable=False)
    cid_10: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True,
        comment="Código CID-10"
    )
    ciap_2: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True,
        comment="Código CIAP-2"
    )
    nurse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    paciente: Mapped[Patient] = relationship("Patient")
    enfermeiro: Mapped[Optional[Nurse]] = relationship("Nurse")


class FilaEvent(Base):
    """
    Modelo de Eventos da Fila.
    Rastreia mudanças na fila para monitoramento APS.
    """
    __tablename__ = "eventos_fila"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    fila_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    evento_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="Entrada, Saída, Prioridade, Chamada"
    )
    identificador: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="CNS ou CPF do paciente"
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    mensagem: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    fila: Mapped[Fila] = relationship("Fila")
```

---

## Arquivo: `backend/app/schemas.py`

```python
# Arquivo: backend/app/schemas.py
"""
Esquemas Pydantic v2 para validação estrita.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/