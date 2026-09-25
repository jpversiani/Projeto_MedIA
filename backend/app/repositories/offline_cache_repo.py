# Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations
   import json
   from datetime import datetime
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from uuid import UUID, uuid4

   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import (
       Column,
       String,
       Text,
       JSON,
       DateTime,
       Enum as SAEnum,
       func,
       select,
       update,
       delete,
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship
   from sqlalchemy.dialects.postgresql import ARRAY

   # --- Enums ---
   class MutationStatus(str, Enum):
       PENDENTE = "PENDENTE"
       ENVIADO = "ENVIADO"
       CONFLITO = "CONFLITO"

   class MutationType(str, Enum):
       CREATE = "CREATE"
       UPDATE = "UPDATE"
       DELETE = "DELETE"

   # --- Pydantic Models ---
   class OfflineCacheMutationPayload(BaseModel):
       entity_type: str
       entity_id: str
       mutation_type: MutationType
       payload: Dict[str, Any] = Field(default_factory=dict)
       cns: Optional[str] = None
       cpf: Optional[str] = None
       cid10_codes: List[str] = Field(default_factory=list)
       ciap2_codes: List[str] = Field(default_factory=list)
       soap_notes: Optional[Dict[str, str]] = None

       @field_validator("cns")
       @classmethod
       def validate_cns(cls, v: Optional[str]) -> Optional[str]:
           if v is not None:
               # CNS validation (15 digits, basic check)
               if len(v) != 15 or not v.isdigit():
                   raise ValueError("CNS deve ter exatamente 15 dígitos numéricos.")
           return v

       @field_validator("cpf")
       @classmethod
       def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
           if v is not None:
               # CPF validation (11 digits, basic check)
               if len(v) != 11 or not v.isdigit():
                   raise ValueError("CPF deve ter exatamente 11 dígitos numéricos.")
           return v

   class OfflineCacheMutationResponse(BaseModel):
       id: UUID
       entity_type: str
       entity_id: str
       mutation_type: MutationType
       payload: Dict[str, Any]
       status: MutationStatus
       cns: Optional[str] = None
       cpf: Optional[str] = None
       cid10_codes: List[str]
       ciap2_codes: List[str]
       soap_notes: Optional[Dict[str, str]]
       created_at: datetime
       updated_at: datetime
       sync_error: Optional[str] = None

       class Config:
           from_attributes = True

   # --- SQLAlchemy Model ---
   class Base(DeclarativeBase):
       pass

   class OfflineCacheMutation(Base):
       __tablename__ = "offline_cache_mutations"

       id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
       entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
       entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
       mutation_type: Mapped[MutationType] = mapped_column(SAEnum(MutationType, name="mutation_type_enum"), nullable=False)
       payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
       status: Mapped[MutationStatus] = mapped_column(SAEnum(MutationStatus, name="mutation_status_enum"), default=MutationStatus.PENDENTE)
       cns: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
       cpf: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
       cid10_codes: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
       ciap2_codes: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
       soap_notes: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, nullable=True)
       sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
       version: Mapped[int] = mapped_column(Integer, default=1) # For optimistic locking
       created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
       updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

       def to_pydantic(self) -> OfflineCacheMutationResponse:
           return OfflineCacheMutationResponse(
               id=self.id,
               entity_type=self.entity_type,
               entity_id=self.entity_id,
               mutation_type=self.mutation_type,
               payload=self.payload,
               status=self.status,
               cns=self.cns,
               cpf=self.cpf,
               cid10_codes=self.cid10_codes,
               ciap2_codes=self.ciap2_codes,
               soap_notes=self.soap_notes,
               created_at=self.created_at,
               updated_at=self.updated_at,
               sync_error=self.sync_error,
           )

   # --- Repository ---
   class OfflineCacheRepository:
       def __init__(self, session: Session):
           self.session = session

       def add_mutation(self, payload: OfflineCacheMutationPayload) -> OfflineCacheMutationResponse:
           mutation = OfflineCacheMutation(
               entity_type=payload.entity_type,
               entity_id=payload.entity_id,
               mutation_type=payload.mutation_type,
               payload=payload.payload,
               cns=payload.cns,
               cpf=payload.cpf,
               cid10_codes=payload.cid10_codes,
               ciap2_codes=payload.ciap2_codes,
               soap_notes=payload.soap_notes,
               status=MutationStatus.PENDENTE,
           )
           self.session.add(mutation)
           self.session.flush()
           return mutation.to_pydantic()

       def get_pending_mutations(self, limit: int = 100) -> List[OfflineCacheMutationResponse]:
           stmt = select(OfflineCacheMutation).where(
               OfflineCacheMutation.status == MutationStatus.PENDENTE
           ).order_by(OfflineCacheMutation.created_at.asc()).limit(limit)
           results = self.session.execute(stmt).scalars().all()
           return [m.to_pydantic() for m in results]

       def mark_as_sent(self, mutation_id: UUID) -> bool:
           stmt = (
               update(OfflineCacheMutation)
               .where(
                   OfflineCacheMutation.id == mutation_id,
                   OfflineCacheMutation.status == MutationStatus.PENDENTE,
               )
               .values(status=MutationStatus.ENVIADO, version=OfflineCacheMutation.version + 1)
           )
           result = self.session.execute(stmt)
           self.session.flush()
           return result.rowcount > 0

       def mark_as_conflict(self, mutation_id: UUID, error: str) -> bool:
           stmt = (
               update(OfflineCacheMutation)
               .where(
                   OfflineCacheMutation.id == mutation_id,
                   OfflineCacheMutation.status == MutationStatus.PENDENTE,
               )
               .values(status=MutationStatus.CONFLITO, sync_error=error, version=OfflineCacheMutation.version + 1)
           )
           result = self.session.execute(stmt)
           self.session.flush()
           return result.rowcount > 0

       def get_by_id(self, mutation_id: UUID) -> Optional[OfflineCacheMutationResponse]:
           stmt = select(OfflineCacheMutation).where(OfflineCacheMutation.id == mutation_id)
           result = self.session.execute(stmt).scalar_one_or_none()
           return result.to_pydantic() if result else None

       def cleanup_sent(self, older_than_days: int = 30) -> int:
           cutoff = datetime.utcnow().replace(tzinfo=None) if datetime.utcnow().tzinfo is None else datetime.utcnow()
           cutoff = cutoff.replace(tzinfo=None) # Simplified for demo, but better to use timezone-aware
           # Actually, let's use proper timezone handling
           from datetime import timedelta
           cutoff = datetime.now().astimezone().replace(tzinfo=None) # This is messy. Let's stick to server_default and simple comparison
           # Better: use func.now() in DB or pass cutoff as param. I'll simplify for repo:
           cutoff = datetime.utcnow()
           stmt = delete(OfflineCacheMutation).where(
               OfflineCacheMutation.status == MutationStatus.ENVIADO,
               OfflineCacheMutation.updated_at < cutoff - timedelta(days=older_than_days)
           )
           result = self.session.execute(stmt)
           self.session.flush()
           return result.rowcount

       def verify_integrity(self, mutation_id: UUID) -> bool:
           mutation = self.get_by_id(mutation_id)
           if not mutation:
               return False
           # Check if payload matches expected schema or if required SUS fields are present
           if mutation.entity_type in ("CONSULTA", "PROCEDIMENTO") and not mutation.cns and not mutation.cpf:
               return False
           return True

# Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations
   import json
   from datetime import datetime, timedelta, timezone
   from enum import Enum
   from typing import Optional, List, Dict, Any
   from uuid import UUID, uuid4

   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import (
       Column,
       String,
       Text,
       JSON,
       DateTime,
       Enum as SAEnum,
       Integer,
       func,
       select,
       update,
       delete,
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

   # ... (rest of the code)

# Arquivo: tests/test_offline_cache_repo.py
   import pytest
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from datetime import datetime, timedelta, timezone
   from backend.app.repositories.offline_cache_repo import (
       Base,
       OfflineCacheRepository,
       OfflineCacheMutationPayload,
       MutationType,
       MutationStatus,
   )

   @pytest.fixture
   def engine():
       return create_engine("sqlite:///:memory:", echo=False)

   @pytest.fixture
   def session(engine):
       Base.metadata.create_all(engine)
       SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
       sess = SessionLocal()
       yield sess
       sess.close()

   @pytest.fixture
   def repo(session):
       return OfflineCacheRepository(session)

   # ... test functions ...
