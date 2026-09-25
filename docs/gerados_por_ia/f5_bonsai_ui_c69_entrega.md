# Interface de Sincronização e Conectividade ACS (C69)

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── sync.py
│   ├── static/
│   │   └── sync_status.html
│   └── tests/
│       ├── __init__.py
│       └── test_sync.py
├── requirements.txt
└── pytest.ini
```

---

## Arquivo: `backend/app/__init__.py`

```python
# Arquivo: backend/app/__init__.py
"""
Aplicação MedIA - Interface de Sincronização e Conectividade ACS (C69)
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF
"""
```

---

## Arquivo: `backend/app/main.py`

```python
# Arquivo: backend/app/main.py
"""
Entrada principal da aplicação MedIA.
Roteamento de API para sincronização ACS (C69) com suporte a SOAP/CIAP-2.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.sync import sync_router
from app.models import init_db, db_engine, SessionLocal

app = FastAPI(
    title="MedIA - Interface de Sincronização ACS (C69)",
    description="Backend para sincronização de Atenção Domicilar com SUS/APS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Inicialização da base de dados
init_db()

# Roteadores
app.include_router(sync_router, prefix="/api/v1/sync")

# Arquivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def root():
    return {"message": "MedIA - Interface de Sincronização ACS (C69)", "status": "online"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.on_event("startup")
def startup_event():
    """Inicialização ao iniciar o servidor."""
    pass

@app.on_event("shutdown")
def shutdown_event():
    """Limpeza ao fechar o servidor."""
    db_engine.dispose()
```

---

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para rastreamento de sincronização ACS (C69).
Conformidade SUS/APS: CIAP-2, CID-10, SOAP, CNS/CPF.
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
    create_engine,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.ext.declarative import declarative_base

# Base declarativa
Base = declarative_base()


class SyncStatusType(str, enum.Enum):
    """Tipos de status de sincronização."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    COMPLETED = "completed"


class ConnectionStatusType(str, enum.Enum):
    """Status de conexão com o ACS."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    TIMEOUT = "timeout"


class BatchStatusType(str, enum.Enum):
    """Status de upload de lotes."""
    QUEUED = "queued"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    FAILED = "failed"
    RETRYING = "retrying"


class TransmissionLogType(str, enum.Enum):
    """Tipos de logs de transmissão."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRY = "retry"
    COMPLETED = "completed"


class SyncSession(Base):
    """
    Sessão de sincronização com ACS.
    Rastreia a conexão SOAP/CIAP-2 para Atenção Domicilar.
    """
    __tablename__ = "sync_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_cns: Mapped[str] = mapped_column(
        String(15), nullable=False, comment="CNS do paciente"
    )
    patient_cpf: Mapped[Optional[str]] = mapped_column(
        String(11), nullable=True, comment="CPF do paciente"
    )
    session_id: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, comment="ID da sessão SOAP"
    )
    status: Mapped[SyncStatusType] = mapped_column(
        Enum(SyncStatusType), default=SyncStatusType.PENDING
    )
    connection_status: Mapped[ConnectionStatusType] = mapped_column(
        Enum(ConnectionStatusType), default=ConnectionStatusType.DISCONNECTED
    )
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relação com lotes
    batches: Mapped[list["BatchUpload"]] = relationship(
        back_populates="session", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<SyncSession id={self.id} patient_cns={self.patient_cns} "
            f"status={self.status.value}>"
        )


class BatchUpload(Base):
    """
    Lote de Atenção Domicilar para upload.
    Rastreia o progresso de sincronização de dados.
    """
    __tablename__ = "batch_uploads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, comment="ID da sessão de sync"
    )
    patient_cns: Mapped[str] = mapped_column(
        String(15), nullable=False, comment="CNS do paciente"
    )
    patient_cpf: Mapped[Optional[str]] = mapped_column(
        String(11), nullable=True, comment="CPF do paciente"
    )
    batch_number: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Número do lote"
    )
    status: Mapped[BatchStatusType] = mapped_column(
        Enum(BatchStatusType), default=BatchStatusType.QUEUED
    )
    total_records: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Total de registros"
    )
    uploaded_records: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Registros já enviados"
    )
    percentage: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="Percentual de progresso"
    )
    file_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Nome do arquivo"
    )
    file_size_bytes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Tamanho do arquivo em bytes"
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relação com logs
    logs: Mapped[list["TransmissionLog"]] = relationship(
        back_populates="batch", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<BatchUpload id={self.id} batch={self.batch_number} "
            f"status={self.status.value} progress={self.percentage:.1f}%>"
        )


class TransmissionLog(Base):
    """
    Log de transmissão individual.
    Rastreia cada mensagem SOAP/CIAP-2 enviada.
    """
    __tablename__ = "transmission_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, comment="ID do lote"
    )
    patient_cns: Mapped[str] = mapped_column(
        String(15), nullable=False, comment="CNS do paciente"
    )
    message_id: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="ID da mensagem SOAP"
    )
    log_type: Mapped[TransmissionLogType] = mapped_column(
        Enum(TransmissionLogType), default=TransmissionLogType.INITIATED
    )
    payload_summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Resumo do payload (CID-10/CIAP-2)"
    )
    response_code: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Código de resposta SOAP"
    )
    response_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Mensagem de resposta"
    )
    duration_ms: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Duração em milissegundos"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relação com lote
    batch: Mapped["BatchUpload"] = relationship(
        back_populates="logs", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<TransmissionLog id={self.id} message_id={self.message_id} "
            f"type={self.log_type.value}>"
        )


# --- Inicialização da Base de Dados ---

def init_db() -> None:
    """Inicializa a base de dados com todas as tabelas."""
    engine = create_engine(
        "sqlite:///media_sync.db",
        echo=False,
        future=True,
    )
    Base.metadata.create_all(bind=engine)


# --- Conexão de Sessão ---

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Depends para injeção de sessão."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## Arquivo: `backend/app/schemas.py`

```python
# Arquivo: backend/app/schemas.py
"""
Esquemas Pydantic v2 para validação de dados.
Conformidade com CIAP-2 e CID-10 para Atenção Domicilar.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


# --- Esquemas de Sessão ---

class SyncSessionCreate(BaseModel):
    """Esquema para criação de sessão de sincronização."""
    patient_cns: str = Field(
        ..., min_length=1, max_length=15, description="CNS do paciente"
    )
    patient_cpf: Optional[str] = Field(
        None, max_length=11, description="CPF do paciente (opcional)"
    )
    session_id: str = Field(
        ..., min_length=1, max_length=50, description="ID da sessão SOAP"
    )

    @field_validator("patient_cps")
    @classmethod
    def validate_cns(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("CNS deve conter apenas dígitos")
        return v


class SyncSessionUpdate(BaseModel):
    """Esquema para atualização de sessão."""
    status: Optional[str] = Field(
        None, description="Novo status da sessão"
    )
    connection_status: Optional[str] = Field(
        None, description="Novo status de conexão"
    )
    error_message: Optional[str] = Field(
        None, description="Mensagem de erro"
    )


class SyncSessionResponse(BaseModel):
    """Esquema de resposta para sessão de sincronização."""
    id: uuid.UUID
    patient_cns: str
    patient_cpf: Optional[str]
    session_id: str
    status: str
    connection_status: str
    last_synced_at: Optional[datetime]
    next_sync_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Esquemas de Lote ---

class BatchUploadCreate(BaseModel):
    """Esquema para criação de lote de Atenção Domicilar."""
    session_id: uuid.UUID
    patient_cns: str
    patient_cpf: Optional[str]
    batch_number: int = Field(..., ge=1)
    total_records: int = Field(..., ge=0)
    file_name: Optional[str] = Field(None, max_length=255)
    file_size_bytes: Optional[int] = Field(None, ge=0)

    @field_validator("patient_cps")
    @classmethod
    def validate_cns(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("CNS deve conter apenas dígitos")
        return v


class BatchUploadUpdate(BaseModel):
    """Esquema para atualização de lote."""
    status: Optional[str] = Field(None)
    uploaded_records: Optional[int] = Field(None, ge=0)
    percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    error_message: Optional[str] = Field(None)

    @field_validator("patient_c