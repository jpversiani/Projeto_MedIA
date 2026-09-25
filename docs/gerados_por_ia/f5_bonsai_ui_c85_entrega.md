# Interface de Sincronização e Conectividade ACS (C85)

## Arquivo: backend/app/models.py

```python
# Arquivo: backend/app/models.py
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SyncStatusType(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    SYNCING = "syncing"
    ERROR = "error"


class BatchStatus(str, enum.Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"


class TransmissionStatus(str, enum.Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class SyncStatus(Base):
    """Modelo que rastreia o status de conexão com o ACS (C85)."""

    __tablename__ = "sync_status"

    id: Mapped[PG_UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    patient_id: Mapped[Optional[str]] = mapped_column(
        String(11), nullable=True, comment="CNS ou CPF do paciente"
    )
    status: Mapped[SyncStatusType] = mapped_column(
        SAEnum(SyncStatusType, name="sync_status_type"),
        default=SyncStatusType.DISCONNECTED,
    )
    last_sync_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Erro da última tentativa de sincronização"
    )
    batch_count: Mapped[int] = mapped_column(Integer, default=0)
    last_batch_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<SyncStatus(id={self.id}, patient_id={self.patient_id}, status={self.status})>"


class BatchUpload(Base):
    """Modelo que rastreia o upload de lotes da Atenção Domiciliar."""

    __tablename__ = "batch_upload"

    id: Mapped[PG_UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    patient_id: Mapped[Optional[str]] = mapped_column(
        String(11), nullable=True, comment="CNS ou CPF do paciente"
    )
    batch_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[BatchStatus] = mapped_column(
        SAEnum(BatchStatus, name="batch_status"), default=BatchStatus.PENDING
    )
    file_size_mb: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Tamanho do lote em MB"
    )
    uploaded_bytes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0, comment="Bytes já uploadados"
    )
    upload_start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    upload_complete_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Erro durante o upload"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def progress_percentage(self) -> float:
        """Calcula o percentual de progresso do upload."""
        if self.file_size_mb is None or self.file_size_mb <= 0:
            return 0.0
        return (self.uploaded_bytes / (self.file_size_mb * 1024 * 1024)) * 100

    def __repr__(self) -> str:
        return f"<BatchUpload(id={self.id}, patient_id={self.patient_id}, batch={self.batch_number}, status={self.status})>"


class TransmissionLog(Base):
    """Modelo que rastreia os logs de transmissão SOAP para o ACS."""

    __tablename__ = "transmission_log"

    id: Mapped[PG_UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    patient_id: Mapped[Optional[str]] = mapped_column(
        String(11), nullable=True, comment="CNS ou CPF do paciente"
    )
    message_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Tipo de mensagem SOAP (ex: PatientDemographics, ClinicalObservation)"
    )
    status: Mapped[TransmissionStatus] = mapped_column(
        SAEnum(TransmissionStatus, name="transmission_status"),
        default=TransmissionStatus.QUEUED,
    )
    message_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="ID da mensagem SOAP"
    )
    message_body: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Corpo da mensagem SOAP (truncado para exibição)"
    )
    sent_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    response_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Tempo de resposta do ACS"
    )
    response_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Status da resposta (ex: 200 OK, 400 Bad Request)"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Erro na transmissão"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<TransmissionLog(id={self.id}, patient_id={self.patient_id}, type={self.message_type}, status={self.status})>"
```

## Arquivo: backend/app/schemas.py

```python
# Arquivo: backend/app/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SyncStatusType(str, BaseModel):
    """Enum serializado para o status de conexão."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    SYNCING = "syncing"
    ERROR = "error"


class BatchStatus(str, BaseModel):
    """Enum serializado para o status do upload de lote."""

    PENDING = "pending"
    UPLOADED = "uploaded"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"


class TransmissionStatus(str, BaseModel):
    """Enum serializado para o status da transmissão."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class SyncStatusResponse(BaseModel):
    """Resposta com o status de conexão com o ACS."""

    id: str
    patient_id: Optional[str] = None
    status: SyncStatusType
    last_sync_time: Optional[datetime] = None
    last_error: Optional[str] = None
    batch_count: int = 0
    last_batch_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BatchUploadResponse(BaseModel):
    """Resposta com o status de upload de um lote."""

    id: str
    patient_id: Optional[str] = None
    batch_number: int
    status: BatchStatus
    file_size_mb: Optional[float] = None
    uploaded_bytes: int = 0
    progress_percentage: float = 0.0
    upload_start_time: Optional[datetime] = None
    upload_complete_time: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TransmissionLogResponse(BaseModel):
    """Resposta com um log de transmissão."""

    id: str
    patient_id: Optional[str] = None
    message_type: str
    status: TransmissionStatus
    message_id: Optional[str] = None
    message_body: Optional[str] = None
    sent_time: Optional[datetime] = None
    response_time: Optional[datetime] = None
    response_status: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SyncStatusSummary(BaseModel):
    """Resposta resumida para o dashboard."""

    connection_status: SyncStatusType
    last_sync_time: Optional[datetime] = None
    last_error: Optional[str] = None
    total_batches: int = 0
    pending_batches: int = 0
    in_progress_batches: int = 0
    completed_batches: int = 0
    failed_batches: int = 0
    last_batch_id: Optional[str] = None
```

## Arquivo: backend/app/api/v1/telemedicina.py

```python
# Arquivo: backend/app/api/v1/telemedicina.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    BatchUpload,
    SyncStatus,
    SyncStatusType,
    TransmissionLog,
    TransmissionStatus,
)
from ..schemas import (
    BatchStatus,
    BatchUploadResponse,
    SyncStatusResponse,
    SyncStatusSummary,
    TransmissionLogResponse,
    TransmissionStatus,
)
from ..dependencies import get_db

router = APIRouter(prefix="/api/v1/telemedicina", tags=["telemedicina"])


@router.get("/sync-status", response_model=SyncStatusResponse)
async def get_sync_status(
    patient_id: Optional[str] = Query(None, description="CNS ou CPF do paciente"),
    db: AsyncSession = Depends(get_db),
) -> SyncStatusResponse:
    """Retorna o status de conexão com o ACS (C85) para um paciente específico."""
    if patient_id:
        result = await db.execute(
            select(SyncStatus).where(SyncStatus.patient_id == patient_id).limit(1)
        )
        sync_status = result.scalar_one_or_none()
    else:
        result = await db.execute(
            select(SyncStatus).order_by(SyncStatus.updated_at.desc()).limit(1)
        )
        sync_status = result.scalar_one_or_none()

    if not sync_status:
        raise HTTPException(status_code=404, detail="Nenhum registro de status encontrado")

    return SyncStatusResponse.model_validate(sync_status)


@router.get("/sync-status/summary", response_model=SyncStatusSummary)
async def get_sync_status_summary(
    db: AsyncSession = Depends(get_db),
) -> SyncStatusSummary:
    """Retorna um resumo agregado do status de sincronização."""
    # Status atual de conexão
    result = await db.execute(
        select(SyncStatus).order_by(SyncStatus.updated_at.desc()).limit(1)
    )
    sync_status = result.scalar_one_or_none()

    if not sync_status:
        return SyncStatusSummary(
            connection_status=SyncStatusType.DISCONNECTED,
            total_batches=0,
            pending_batches=0,
            in_progress_batches=0,
            completed_batches=0,
            failed_batches=0,
        )

    # Contagem de lotes por status
    batch_result = await db.execute(
        select(
            BatchUpload.status,
            func.count(),
        )
        .group_by(BatchUpload.status)
    )
    batch_counts = {row[0]: row[1] for row in batch_result.all()}

    return SyncStatusSummary(
        connection_status=SyncStatusType(sync_status.status),
        last_sync_time=sync_status.last_sync_time,
        last_error=sync_status.last_error,
        total_batches=sync_status.batch_count,
        pending_batches=batch_counts.get(BatchStatus.PENDING, 0),
        in_progress_batches=batch_counts.get(BatchStatus.SYNCING, 0),
        completed_batches=batch_counts.get(BatchStatus.COMPLETED, 0),
        failed_batches=batch_counts.get(BatchStatus.FAILED, 0),
        last_batch_id=sync_status.last_batch_id,
    )


@router.get("/batches", response_model=list[BatchUploadResponse])
async def get_batches(
    patient_id: Optional[str] = Query(None, description="CNS ou CPF do paciente"),
    status: Optional[BatchStatus] = Query(None, description="Filtrar por status"),
    limit: int = Query(50, ge=1, le=100, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset de paginação"),
    db: AsyncSession = Depends(get_db),
) -> list[BatchUploadResponse]:
    """Retorna a lista de lotes de upload com progresso."""
    query = select(BatchUpload)

    if patient_id:
        query = query.where(BatchUpload.patient_id == patient_id)
    if status:
        query = query.where(BatchUpload.status == status)

    query = query.order_by(BatchUpload.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    batches = result.scalars().all()

    return [BatchUploadResponse.model_validate(batch) for batch in batches]


@router.get("/b