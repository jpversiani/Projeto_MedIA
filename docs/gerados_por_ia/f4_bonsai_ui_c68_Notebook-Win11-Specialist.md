```python:backend/app/database.py
# Arquivo: backend/app/database.py
"""
Base de dados assíncrona com SQLAlchemy 2.0.
Conexão PostgreSQL com pool de conexões.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/sisab_monitor"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos."""
    pass


async def get_db():
    """Dependência assíncrona para sessão de banco de dados."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

```python:backend/app/models.py
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para o sistema de monitoramento SISAB.
Conformidade com padrões SUS/APS:
- Identificação por CNS/CPF
- Método SOAP
- CID-10 e CIAP-2
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StatusRemessa(Enum):
    """Status da remessa no sistema SISAB."""
    ENVIADA = "enviada"
    ERRO = "erro"
    RETRANSSA = "retransmitida"
    RECONhecida = "reconhecida"
    PENDENTE = "pendente"


class TipoRemessa(Enum):
    """Tipo de remessa gerada."""
    INDIVIDUAL = "individual"
    LOTE = "lote"
    CORREIO = "correio"
    ELECTRONICA = "electronica"


class RemessaModel(Base):
    """
    Modelo de remessa SISAB.
    Identificação por CNS/CPF conforme padrão SUS.
    """
    __tablename__ = "remessas"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=func.uuid_generate_v4(),
    )
    cns: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    cpf: Mapped[str] = mapped_column(String(11), nullable=False)
    tipo_remessa: Mapped[TipoRemessa] = mapped_column(
        SAEnum(TipoRemessa), nullable=False
    )
    valor: Mapped[Decimal] = mapped_column(
        nullable=False, precision=12, scale=2
    )
    status: Mapped[StatusRemessa] = mapped_column(
        SAEnum(StatusRemessa), default=StatusRemessa.PENDENTE
    )
    metodo_soap: Mapped[str] = mapped_column(String(50), nullable=False)
    cid10: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    ciap2: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    data_envio: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    data_reconhecimento: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    erro: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lote_id: Mapped[Optional[UUID]] = mapped_column(
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )


class LoteRemessaModel(Base):
    """
    Lote de remessas para retransmissão em lote.
    """
    __tablename__ = "lotes_remessa"

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=func.uuid_generate_v4()
    )
    nome_lote: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[StatusRemessa] = mapped_column(
        SAEnum(StatusRemessa), default=StatusRemessa.PENDENTE
    )
    remessa_ids: Mapped[list[UUID]] = mapped_column(
        Text, nullable=False
    )
    erro: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_criação: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )


class RemessaRetransmissaoModel(Base):
    """
    Registro de retransmissão de remessas com erro.
    """
    __tablename__ = "retransmissao_remessa"

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=func.uuid_generate_v4()
    )
    remessa_id: Mapped[UUID] = mapped_column(
        nullable=False
    )
    motivo: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[StatusRemessa] = mapped_column(
        SAEnum(StatusRemessa), default=StatusRemessa.PENDENTE
    )
    data_retransmissao: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
```

```python:backend/app/schemas.py
# Arquivo: backend/app/schemas.py
"""
Esquemas Pydantic v2 para validação de dados.
Tipagem estrita conforme diretrizes.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class StatusRemessa(str, Enum):
    ENVIADA = "enviada"
    ERRO = "erro"
    RETRANSSA = "retransmitida"
    RECONHECIDA = "reconhecida"
    PENDENTE = "pendente"


class TipoRemessa(str, Enum):
    INDIVIDUAL = "individual"
    LOTE = "lote"
    CORREIO = "correio"
    ELECTRONICA = "electronica"


class RemessaCreate(BaseModel):
    """Esquema para criação de remessa."""
    cns: str = Field(..., min_length=1, max_length=15)
    cpf: str = Field(..., min_length=11, max_length=11)
    tipo_remessa: TipoRemessa
    valor: Decimal = Field(..., gt=0)
    metodo_soap: str = Field(..., min_length=1, max_length=50)
    cid10: Optional[str] = Field(None, max_length=10)
    ciap2: Optional[str] = Field(None, max_length=50)


class RemessaUpdate(BaseModel):
    """Esquema para atualização de remessa."""
    status: Optional[StatusRemessa] = None
    erro: Optional[str] = None
    data_envio: Optional[datetime] = None
    data_reconhecimento: Optional[datetime] = None


class RemessaResponse(BaseModel):
    """Esquema de resposta de remessa."""
    id: str
    cns: str
    cpf: str
    tipo_remessa: TipoRemessa
    valor: Decimal
    status: StatusRemessa
    metodo_soap: str
    cid10: Optional[str]
    ciap2: Optional[str]
    data_envio: Optional[datetime]
    data_reconhecimento: Optional[datetime]
    erro: Optional[str]
    lote_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoteRemessaCreate(BaseModel):
    """Esquema para criação de lote de retransmissão."""
    nome_lote: str = Field(..., min_length=1, max_length=100)
    remessa_ids: List[str] = Field(..., min_length=1)


class LoteRemessaResponse(BaseModel):
    """Esquema de resposta de lote."""
    id: str
    nome_lote: str
    status: StatusRemessa
    remessa_ids: List[str]
    erro: Optional[str]
    data_criação: datetime

    model_config = ConfigDict(from_attributes=True)


class RemessaRetransmissaoCreate(BaseModel):
    """Esquema para retransmissão de remessa."""
    remessa_id: str
    motivo: str = Field(..., min_length=1, max_length=200)


class RemessaRetransmissaoResponse(BaseModel):
    """Esquema de resposta de retransmissão."""
    id: str
    remessa_id: str
    motivo: str
    status: StatusRemessa
    data_retransmissao: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardMetrics(BaseModel):
    """Métricas do dashboard."""
    total_remessas: int
    total_enviadas: int
    total_erros: int
    total_retransmitidas: int
    total_reconhecidas: int
    remessas_urgentes: int
    lotes_em_erros: int
    valor_total_enviado: Decimal
    valor_total_erros: Decimal


class MonthlySendingData(BaseModel):
    """Dados mensais de envio."""
    mes: str
    ano: int
    total_remessas: int
    total_enviadas: int
    total_erros: int
    valor_total: Decimal


class WebSocketMessage(BaseModel):
    """Mensagem para WebSocket."""
    type: str
    data: dict
    timestamp: datetime
```

```python:backend/app/api.py
# Arquivo: backend/app/api.py
"""
API REST + WebSocket para monitoramento SISAB.
Endpoints:
- /api/remessas - Listar/remessas
- /api/remessas/{id} - Detalhes de remessa
- /api/remessas/{id}/retransmitir - Retransmitir remessa
- /api/lotes - Gerenciar lotes
- /api/dashboard/metrics - Métricas do dashboard
- /api/dashboard/mensual - Dados mensais
- /ws/monitor - WebSocket para atualização em tempo real
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    Base,
    LoteRemessaModel,
    RemessaModel,
    RemessaRetransmissaoModel,
    StatusRemessa,
    TipoRemessa,
)
from app.schemas import (
    DashboardMetrics,
    MonthlySendingData,
    LoteRemessaCreate,
    LoteRemessaResponse,
    RemessaCreate,
    RemessaResponse,
    RemessaRetransmissaoCreate,
    RemessaRetransmissaoResponse,
    RemessaUpdate,
    WebSocketMessage,
)

router = APIRouter(prefix="/api", tags=["SISAB Monitor"])


# =============================================================================
# REMESSAS
# =============================================================================

@router.get("/remessas", response_model=List[RemessaResponse])
async def list_remessas(
    status: Optional[StatusRemessa] = None,
    tipo: Optional[TipoRemessa] = None,
    cns: Optional[str] = None,
    cpf: Optional[str] = None,
    limite: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Listar remessas com filtros por status, tipo, CNS ou CPF."""
    query = select(RemessaModel)

    if status:
        query = query.where(RemessaModel.status == status)
    if tipo:
        query = query.where(RemessaModel.tipo_remessa == tipo)
    if cns:
        query = query.where(RemessaModel.cns.ilike(f"%{cns}%"))
    if cpf:
        query = query.where(RemessaModel.cpf.ilike(f"%{cpf}%"))

    query = query.order_by(RemessaModel.data_envio.desc())
    query = query.offset(offset).limit(limite)

    result = await db.execute(query)
    remessas = result.scalars().all()
    return remessas


@router.get("/remessas/{remessa_id}", response_model=RemessaResponse)
async def get_remessa(
    remessa_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Obter detalhes de uma remessa específica."""
    from uuid import UUID

    remessa = await db.get(RemessaModel, remessa_id)
    if not remessa:
        raise HTTPException(status_code=404, detail="Remessa não encontrada")
    return remessa


@router.post("/remessas", response_model=RemessaResponse)
async def create_remessa(
    remessa: RemessaCreate,
    db: AsyncSession = Depends(get_db),
):
    """Criar nova remessa SISAB."""
    from uuid import uuid4

    remessa_model = RemessaModel(
        id=uuid4(),
        cns=remessa.cns,
        cpf=remessa.cpf,
        tipo_remessa=remessa.tipo_remessa,
        valor=remessa.valor,
        metodo_soap=remessa.metodo_soap,
        cid10=remessa.cid10,
        ciap2=remessa.ciap2,
    )
    db.add(remessa_model)
    await db.flush()
    await db.refresh(remessa_model)
    return remessa_model


@router.patch("/remessas/{remessa_id}", response_model=RemessaResponse)
async def update_remessa(
    remessa_id: str,
    remessa_update: RemessaUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Atualizar status de uma remessa."""
    remessa = await db.get(RemessaModel, remessa_id)
    if not remessa:
        raise HTTPException(status_code=4