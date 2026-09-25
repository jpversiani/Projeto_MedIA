backend/app/
├── api/v1/
│   ├── analytics.py          # main deliverable
├── schemas/
│   └── analytics.py          # Pydantic v2 schemas
├── repositories/
│   └── analytics.py          # SQLAlchemy 2.0 queries
├── services/
│   └── analytics.py          # business logic
├── models/
│   ├── agendamento.py
│   └── atendimento.py

# backend/app/models/agendamento.py
import enum
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

class StatusAgendamento(str, enum.Enum):
    AGENDADO = "AGENDADO"
    CONFIRMADO = "CONFIRMADO"
    ATENDIDO = "ATENDIDO"
    FALTOU = "FALTOU"          # no-show
    CANCELADO_PACIENTE = "CANCELADO_PACIENTE"
    CANCELADO_UNIDADE = "CANCELADO_UNIDADE"
    REAGENDADO = "REAGENDADO"

class Agendamento(Base):
    __tablename__ = "agendamentos"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id"))
    profissional_id: Mapped[int] = mapped_column(ForeignKey("profissionais.id"))
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"))  # UBS
    inicio_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fim_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[StatusAgendamento] = mapped_column(Enum(StatusAgendamento, name="status_agendamento"))
    chegada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # check-in
    inicio_atendimento_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canal: Mapped[str] = ...
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class CondutaEncaminhamento(str, enum.Enum):
    RESOLVIDO_APS = "RESOLVIDO_APS"          # alta/resolução na APS
    ENCAMINHADO_ESPECIALISTA = "ENCAMINHADO_ESPECIALISTA"
    ENCAMINHADO_URGENCIA = "ENCAMINHADO_URGENCIA"
    RETORNO_APS = "RETORNO_APS"              # retorno agendado na APS — still APS care
    ...

class Atendimento(Base):
    __tablename__ = "atendimentos"
    id, agendamento_id (FK unique), paciente_id, profissional_id, unidade_id
    cid10_principal: Mapped[str | None] = mapped_column(String(4))   # CID-10
    ciap2_principal: Mapped[str | None] = mapped_column(String(5))   # CIAP-2 (3 letras + 2 dígitos, e.g., "A01"? Actually CIAP-2 codes are like "A01"? CIAP-2: letter (chapter) + 2 digits, e.g., K29? Hmm CIAP codes: chapter letter + 2 digits, e.g., "A01"? Let me recall: CIAP-2 codes like "K29" (hipertensão não especificada? no that's K86?). CIAP-2: e.g., A01, K29... Actually CIAP-2 code format: one letter (A–Z, chapter) + two digits. Examples: K29 = "Hypertension, unspecified"? I believe K29 is "Blood pressure high" hmm. Anyway format: letter + 2 digits = 3 chars. e.g., "S27"? I'll use String(3) with regex ^[A-Z]\d{2}$.
    subjetiva/objetiva/avaliacao/plano: Text (SOAP)
    conduta: enum
    encaminhamento_especialidade: str | None

# schemas/analytics.py
from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field, computed_field

class DiaSemana(int, Enum):
    SEGUNDA = 1 ... DOMINGO = 7

class HeatmapCelula(BaseModel):
    dia_semana: DiaSemana  # 1..7 ISO
    hora: int = Field(ge=0, le=23)
    total: int = Field(ge=0)
    atendidos: int
    faltas: int
    cancelados: int
    taxa_absenteismo: float | None  # per cell? maybe
    densidade: float  # normalized 0..1 relative to max cell

class HeatmapResponse(BaseModel):
    periodo: PeriodoInfo
    filtros: ...
    matriz: list[HeatmapCelula]  # 168 cells
    total_agendamentos: int
    pico: PicoInfo  # dia/hora com maior densidade
    gerado_em: datetime

class KpisResponse(BaseModel):
    periodo: ...
    absenteismo: TaxaAbsenteismo
    espera: TempoEspera
    resolutividade: TaxaResolutividade

class TaxaAbsenteismo(BaseModel):
    total_esperados: int      # ATENDIDO + FALTOU
    faltas: int
    taxa: float               # 0..1 or percent? I'll use percent 0-100 with 2 decimals? Or fraction. I'll use fraction with 4 decimals and also percent field? Keep "taxa" as percent (0-100). Hmm. In Brazilian health dashboards, "taxa de absenteísmo" usually shown as %. I'll return `taxa_percentual: float` and maybe `taxa` fraction. Choose: `taxa: float = Field(..., ge=0, le=1, description="proporção")` plus `percentual` computed. Simpler: return percent with description. I'll go with fraction (0..1) named `taxa` and a computed `percentual`. Actually to avoid confusion, single field `taxa_percentual` (0–100). Let me do both: `taxa` (0–1) and `taxa_percentual` computed_field = taxa*100. Fine.
