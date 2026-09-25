from __future__ import annotations
   import logging
   from datetime import datetime
   from decimal import Decimal
   from typing import Optional, Sequence
   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import (
       Column,
       DateTime,
       Numeric,
       String,
       Text,
       func,
       select,
   )
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
   import uuid

   # Base class for SQLAlchemy models
   class Base(DeclarativeBase):
       pass

   # SQLAlchemy Model
   class VitalSign(Base):
       __tablename__ = "sinais_vitais"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       patient_cns: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
       patient_cpf: Mapped[str] = mapped_column(String(14), nullable=False, index=True)
       recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
       pa_sistolica: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
       pa_diastolica: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
       fc: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
       fr: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
       temperatura: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
       glicemia: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
       spo2: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
       cid10: Mapped[Optional[str]] = mapped_column(String(7))
       ciap2: Mapped[Optional[str]] = mapped_column(String(4))
       soap_note: Mapped[Optional[str]] = mapped_column(Text)
       created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
       updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

   # Pydantic Schemas
   class VitalSignCreate(BaseModel):
       patient_cns: str
       patient_cpf: str
       recorded_at: Optional[datetime] = None
       pa_sistolica: Optional[Decimal] = None
       pa_diastolica: Optional[Decimal] = None
       fc: Optional[Decimal] = None
       fr: Optional[Decimal] = None
       temperatura: Optional[Decimal] = None
       glicemia: Optional[Decimal] = None
       spo2: Optional[Decimal] = None
       cid10: Optional[str] = None
       ciap2: Optional[str] = None
       soap_note: Optional[str] = None

       @field_validator("pa_sistolica", "pa_diastolica", "fc", "fr", "temperatura", "glicemia", "spo2")
       @classmethod
       def validate_vital_sign(cls, v):
           if v is not None and v < 0:
               raise ValueError("Valores de sinais vitais não podem ser negativos")
           return v

   class VitalSignResponse(BaseModel):
       id: uuid.UUID
       patient_cns: str
       patient_cpf: str
       recorded_at: datetime
       pa_sistolica: Optional[Decimal] = None
       pa_diastolica: Optional[Decimal] = None
       fc: Optional[Decimal] = None
       fr: Optional[Decimal] = None
       temperatura: Optional[Decimal] = None
       glicemia: Optional[Decimal] = None
       spo2: Optional[Decimal] = None
       cid10: Optional[str] = None
       ciap2: Optional[str] = None
       soap_note: Optional[str] = None
       created_at: datetime
       updated_at: datetime

       model_config = {"from_attributes": True}

   class VitalSignAlert(BaseModel):
       vital_sign_type: str
       value: Decimal
       threshold: str
       severity: str  # "CRITICO", "ALERTA", "NORMAL"
       message: str

   # Thresholds for decompensation
   VITAL_SIGN_THRESHOLDS = {
       "pa_sistolica": {"min": Decimal("90"), "max": Decimal("180"), "crit_min": Decimal("80"), "crit_max": Decimal("200")},
       "pa_diastolica": {"min": Decimal("60"), "max": Decimal("110"), "crit_min": Decimal("50"), "crit_max": Decimal("120")},
       "fc": {"min": Decimal("50"), "max": Decimal("120"), "crit_min": Decimal("40"), "crit_max": Decimal("140")},
       "fr": {"min": Decimal("10"), "max": Decimal("30"), "crit_min": Decimal("8"), "crit_max": Decimal("35")},
       "temperatura": {"min": Decimal("35.0"), "max": Decimal("39.0"), "crit_min": Decimal("34.0"), "crit_max": Decimal("40.0")},
       "glicemia": {"min": Decimal("70"), "max": Decimal("300"), "crit_min": Decimal("50"), "crit_max": Decimal("400")},
       "spo2": {"min": Decimal("90"), "max": Decimal("100"), "crit_min": Decimal("85"), "crit_max": Decimal("100")},
   }

   class SinaisVitaisRepository:
       def __init__(self, session: Session):
           self.session = session

       def create_vital_sign(self, data: VitalSignCreate) -> VitalSign:
           now = datetime.utcnow()
           db_obj = VitalSign(
               patient_cns=data.patient_cns,
               patient_cpf=data.patient_cpf,
               recorded_at=data.recorded_at or now,
               pa_sistolica=data.pa_sistolica,
               pa_diastolica=data.pa_diastolica,
               fc=data.fc,
               fr=data.fr,
               temperatura=data.temperatura,
               glicemia=data.glicemia,
               spo2=data.spo2,
               cid10=data.cid10,
               ciap2=data.ciap2,
               soap_note=data.soap_note,
           )
           self.session.add(db_obj)
           self.session.flush()
           return db_obj

       def get_vital_signs_history(
           self,
           patient_cns: str,
           patient_cpf: str,
           start_date: Optional[datetime] = None,
           end_date: Optional[datetime] = None,
           vital_type: Optional[str] = None,
       ) -> Sequence[VitalSign]:
           stmt = select(VitalSign).where(
               VitalSign.patient_cns == patient_cns,
               VitalSign.patient_cpf == patient_cpf,
           )
           if start_date:
               stmt = stmt.where(VitalSign.recorded_at >= start_date)
           if end_date:
               stmt = stmt.where(VitalSign.recorded_at <= end_date)
           if vital_type:
               # Filter by specific vital sign type (e.g., 'fc', 'pa_sistolica')
               stmt = stmt.where(getattr(VitalSign, vital_type) != None)
           stmt = stmt.order_by(VitalSign.recorded_at.desc())
           result = self.session.execute(stmt)
           return result.scalars().all()

       def check_decompensation_alerts(self, vital_sign: VitalSign) -> list[VitalSignAlert]:
           alerts = []
           for field, thresholds in VITAL_SIGN_THRESHOLDS.items():
               value = getattr(vital_sign, field)
               if value is None:
                   continue
               severity = "NORMAL"
               threshold_desc = "dentro da faixa"
               if value < thresholds["crit_min"] or value > thresholds["crit_max"]:
                   severity = "CRITICO"
                   threshold_desc = f"< {thresholds['crit_min']} ou > {thresholds['crit_max']}"
               elif value < thresholds["min"] or value > thresholds["max"]:
                   severity = "ALERTA"
                   threshold_desc = f"< {thresholds['min']} ou > {thresholds['max']}"

               if severity != "NORMAL":
                   alerts.append(VitalSignAlert(
                       vital_sign_type=field,
                       value=value,
                       threshold=threshold_desc,
                       severity=severity,
                       message=f"Sinal vital {field} descompensado: {value} ({threshold_desc}). Severidade: {severity}."
                   ))
           return alerts

       def get_alerts_for_patient(
           self,
           patient_cns: str,
           patient_cpf: str,
           start_date: Optional[datetime] = None,
           end_date: Optional[datetime] = None,
       ) -> list[VitalSignAlert]:
           history = self.get_vital_signs_history(patient_cns, patient_cpf, start_date, end_date)
           all_alerts = []
           for sign in history:
               all_alerts.extend(self.check_decompensation_alerts(sign))
           return all_alerts
