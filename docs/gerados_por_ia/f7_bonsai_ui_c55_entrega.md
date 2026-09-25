# Dashboard Executivo Interativo - MedIA

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
│   │   └── telemedicina.py
│   └── static/
│       └── dashboard_analytics.html
├── tests/
│   ├── __init__.py
│   └── test_dashboard.py
└── requirements.txt
```

---

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 com tipagem estrita.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, CNS/CPF.
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql import text


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos."""


class CID10Category(Enum):
    """Código Internacional de Diagnoses - 10ª edição (CID-10)."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"
    J = "J"
    K = "K"
    L = "L"
    M = "M"
    N = "N"
    O = "O"
    P = "P"
    Q = "Q"
    R = "R"
    S = "S"
    T = "T"
    U = "U"
    V = "V"
    W = "W"
    X = "X"
    Y = "Y"
    Z = "Z"


class SOAPProcedureType(Enum):
    """Método SOAP (Sobre, Objetivo, Avaliação, Plano)."""
    SO = "SO"
    OA = "OA"
    AP = "AP"
    SOAP = "SOAP"


class PatientType(Enum):
    """Tipo de identificação do paciente conforme SUS/APS."""
    CNS = "CNS"
    CPF = "CPF"
    RG = "RG"


class Patient(Base):
    """
    Modelo Patient com identificação por CNS/CPF.
    Conformidade SUS/APS: identificação única por CNS ou CPF.
    """
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    CNS: Mapped[Optional[str]] = mapped_column(String(13), nullable=True)
    CPF: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
    patient_type: Mapped[PatientType] = mapped_column(
        Enum(PatientType), nullable=False, default=PatientType.CNS
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    gender: Mapped[str] = mapped_column(String(1), nullable=False, default="M")
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("CNS", name="uq_patient_cns"),
        UniqueConstraint("CPF", name="uq_patient_cpf"),
    )


class Appointment(Base):
    """
    Modelo de agendamento com método SOAP.
    CID-10 para diagnóstico, SOAP para registro.
    """
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    appointment_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SCHEDULED"
    )
    # SOAP
    so: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    oa: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ap: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    soap: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # CID-10
    cid10_code: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )
    cid10_category: Mapped[Optional[CID10Category]] = mapped_column(
        Enum(CID10Category), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped["Patient"] = relationship(
        back_populates="appointments"
    )


class TelemedicineSession(Base):
    """
    Sessão de telemedicina com rastreamento de horários.
    Usado para heatmap de picos de demanda.
    """
    __tablename__ = "telemedicine_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    appointment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="COMPLETED"
    )
    physician_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    patient: Mapped["Patient"] = relationship(
        back_populates="telemedicine_sessions"
    )
    appointment: Mapped[Optional["Appointment"]] = relationship(
        back_populates="telemedicine_sessions"
    )


class KPI(Base):
    """
    KPIs em tempo real para o dashboard executivo.
    Agregações de métricas de desempenho.
    """
    __tablename__ = "kpi_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    target_value: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("metric_name", "period_start", name="uq_kpi_metric_period"),
    )


# Relações inversas
Patient.appointments = relationship(
    "Appointment", back_populates="patient"
)
Patient.telemedicine_sessions = relationship(
    "TelemedicineSession", back_populates="patient"
)
Appointment.telemedicine_sessions = relationship(
    "TelemedicineSession", back_populates="appointment"
)
```

---

## Arquivo: `backend/app/schemas.py`

```python
# Arquivo: backend/app/schemas.py
"""
Esquemas Pydantic v2 com tipagem estrita.
"""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ─── Enums ───────────────────────────────────────────────────────────────

class PatientType(str, Enum):
    CNS = "CNS"
    CPF = "CPF"
    RG = "RG"


class AppointmentStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class TelemedicineStatus(str, Enum):
    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class KPIMetric(BaseModel):
    """
    KPI para o dashboard executivo.
    """
    id: UUID
    metric_name: str
    value: float
    target_value: Optional[float] = None
    period_start: datetime
    period_end: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentSchema(BaseModel):
    """Esquema de agendamento."""
    id: UUID
    patient_id: UUID
    appointment_date: date
    appointment_time: datetime
    duration_minutes: int
    status: AppointmentStatus
    soap: Optional[str] = None
    cid10_code: Optional[str] = None
    cid10_category: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TelemedicineSessionSchema(BaseModel):
    """Esquema de sessão de telemedicina."""
    id: UUID
    patient_id: UUID
    appointment_id: Optional[UUID] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: int
    status: TelemedicineStatus
    physician_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Dashboard Schemas ───────────────────────────────────────────────────

class KPICard(BaseModel):
    """
    Card de KPI para o dashboard.
    """
    id: UUID
    metric_name: str
    value: float
    target_value: Optional[float] = None
    trend: str  # "UP", "DOWN", "STABLE"
    percentage_change: float
    period_start: datetime
    period_end: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HeatmapDataPoint(BaseModel):
    """
    Ponto de dados para heatmap de horários.
    """
    hour: int
    day_of_week: int
    count: int
    date: date


class LineChartData(BaseModel):
    """
    Dados para gráfico de linha dos últimos 30 dias.
    """
    date: date
    value: float
    label: str


class DashboardSummary(BaseModel):
    """
    Resumo do dashboard com todos os KPIs.
    """
    total_appointments: int
    total_patients: int
    completed_sessions: int
    no_show_rate: float
    avg_duration_minutes: float
    peak_hours: List[int]
    last_30_days_trend: List[float]
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    """
    Resposta completa para o endpoint de dashboard.
    """
    summary: DashboardSummary
    kpis: List[KPICard]
    heatmap_data: List[HeatmapDataPoint]
    line_chart_data: List[LineChartData]
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

---

## Arquivo: `backend/app/api/v1/telemedicina.py`

```python
# Arquivo: backend/app/api/v1/telemedicina.py
"""
API de Telemedicina - Endpoints para o dashboard executivo.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, CNS/CPF.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, and_, or_
from sqlalchemy.orm import Session

from ..models import (
    Base,
    Patient,
    Appointment,
    TelemedicineSession,
    KPI,
    PatientType,
    AppointmentStatus,
    TelemedicineStatus,
    CID10Category,
)
from ..schemas import (
    DashboardResponse,
    DashboardSummary,
    KPICard,
    HeatmapDataPoint,
    LineChartData,
)

router = APIRouter(prefix="/api/v1/telemedicina", tags=["telemedicina"])


# ─── Dependency ──────────────────────────────────────────────────────────

def get_db() -> Session:
    """
    Dependency para session de banco de dados.
    Substituir por sua dependência real.
    """
    # Placeholder - substituir por sua dependência real
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///./media.db")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── KPI Cards ───────────────────────────────────────────────────────────

@router.get("/kpis", response_model=List[KPICard])
def get_kpis(
    db: Session = Depends(get_db),
    days: int = Query(default=