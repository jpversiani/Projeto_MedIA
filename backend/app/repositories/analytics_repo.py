# Arquivo: backend/app/repositories/analytics_repo.py
   from __future__ import annotations
   from typing import List, Dict, Any, Optional
   from datetime import date, datetime
   from sqlalchemy import select, func, extract, over, window, case, text
   from sqlalchemy.orm import Session, joinedload
   from pydantic import BaseModel, Field
   from enum import Enum

   # Models (simplified for context)
   # ... define Consultation, Atendimento, AcaoPreventiva, Usuario, RegistroSOAP, Classificacao ...

   # DTOs
   class HourlyConsultationDTO(BaseModel):
       hour: int
       count: int

   class DayOfWeekConsultationDTO(BaseModel):
       day_of_week: int
       day_name: str
       count: int

   class PreventiveCoverageDTO(BaseModel):
       municipio_id: int
       estabelecimento_id: int
       populacao_cadastrada: int
       acoes_realizadas: int
       cobertura_percentual: float

   class FollowUpRateDTO(BaseModel):
       consulta_id: int
       usuario_cns: str
       dias_para_seguimento: Optional[int]
       followup_existe: bool

   class CIAP2DistributionDTO(BaseModel):
       codigo_ciap2: str
       descricao: str
       total_consultas: int

   class SOAPComplianceDTO(BaseModel):
       usuario_cpf: str
       consultas_com_soap: int
       total_consultas: int
       taxa_conformidade: float

   class AnalyticsRepository:
       def __init__(self, session: Session):
           self.session = session

       def get_consultas_por_hora(self, data_inicio: date, data_fim: date) -> List[HourlyConsultationDTO]:
           # EXTRACT(HOUR FROM data_hora)
           ...

       def get_consultas_por_dia_semana(self, data_inicio: date, data_fim: date) -> List[DayOfWeekConsultationDTO]:
           # EXTRACT(DOW FROM data_hora)
           ...

       def get_cobertura_preventiva(self, municipio_id: Optional[int] = None) -> List[PreventiveCoverageDTO]:
           # GROUP BY municipio, estabelecimento
           ...

       def get_taxa_seguimento(self, data_inicio: date, data_fim: date) -> List[FollowUpRateDTO]:
           # Window function: LAG/LEAD or ROW_NUMBER to find next consultation
           ...

       def get_distribuicao_ciap2(self, data_inicio: date, data_fim: date) -> List[CIAP2DistributionDTO]:
           # GROUP BY CIAP-2 code
           ...

       def get_conformidade_soap(self, data_inicio: date, data_fim: date) -> List[SOAPComplianceDTO]:
           # Check SOAP fields presence
           ...

from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
   from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, Boolean
   from typing import Optional

   class Base(DeclarativeBase):
       pass

   class Consulta(Base):
       __tablename__ = "consultas"
       id: Mapped[int] = mapped_column(primary_key=True)
       usuario_cns: Mapped[str] = mapped_column(String(15))
       usuario_cpf: Mapped[Optional[str]] = mapped_column(String(14))
       data_hora: Mapped[datetime] = mapped_column(DateTime)
       municipio_id: Mapped[int] = mapped_column(Integer)
       estabelecimento_id: Mapped[int] = mapped_column(Integer)
       ciap2_code: Mapped[Optional[str]] = mapped_column(String(4))
       cid10_code: Mapped[Optional[str]] = mapped_column(String(7))
       tem_assunto: Mapped[bool] = mapped_column(Boolean, default=False)
       tem_objetivo: Mapped[bool] = mapped_column(Boolean, default=False)
       tem_avaliacao: Mapped[bool] = mapped_column(Boolean, default=False)
       tem_plano: Mapped[bool] = mapped_column(Boolean, default=False)

   class AcaoPreventiva(Base):
       __tablename__ = "acoes_preventivas"
       id: Mapped[int] = mapped_column(primary_key=True)
       consulta_id: Mapped[int] = mapped_column(ForeignKey("consultas.id"))
       tipo_acao: Mapped[str] = mapped_column(String(50))
       # ...

stmt = (
       select(
           func.extract('hour', Consulta.data_hora).label('hour'),
           func.count(Consulta.id).label('count')
       )
       .where(Consulta.data_hora >= data_inicio, Consulta.data_hora < data_fim + timedelta(days=1))
       .group_by(func.extract('hour', Consulta.data_hora))
       .order_by('hour')
   )

stmt = (
       select(
           func.extract('dow', Consulta.data_hora).label('dow'),
           func.count(Consulta.id).label('count')
       )
       .where(...)
       .group_by(func.extract('dow', Consulta.data_hora))
       .order_by('dow')
   )

stmt = (
       select(
           Consulta.municipio_id,
           Consulta.estabelecimento_id,
           func.count(distinct=Consulta.usuario_cns).label('populacao_cadastrada'),
           func.count(AcaoPreventiva.id).label('acoes_realizadas')
       )
       .join(AcaoPreventiva, Consulta.id == AcaoPreventiva.consulta_id, isouter=True)
       .where(...)
       .group_by(Consulta.municipio_id, Consulta.estabelecimento_id)
   )

stmt = (
       select(
           Consulta.id.label('consulta_id'),
           Consulta.usuario_cns,
           func.lag(Consulta.data_hora).over(
               partition_by=Consulta.usuario_cns,
               order_by=Consulta.data_hora
           ).label('prev_data_hora'),
           Consulta.data_hora.label('curr_data_hora')
       )
       .where(...)
       .order_by(Consulta.usuario_cns, Consulta.data_hora)
   )

stmt = (
       select(
           Consulta.ciap2_code.label('codigo_ciap2'),
           func.count(Consulta.id).label('total_consultas')
       )
       .where(Consulta.ciap2_code.isnot(None))
       .group_by(Consulta.ciap2_code)
       .order_by(func.count(Consulta.id).desc())
   )

stmt = (
       select(
           Consulta.usuario_cpf,
           func.count(Consulta.id).label('total_consultas'),
           func.sum(
               case(
                   (Consulta.tem_assunto & Consulta.tem_objetivo & Consulta.tem_avaliacao & Consulta.tem_plano, 1),
                   else_=0
               )
           ).label('consultas_com_soap')
       )
       .where(...)
       .group_by(Consulta.usuario_cpf)
   )

# Arquivo: backend/app/repositories/analytics_repo.py
   from __future__ import annotations
   from datetime import date, datetime, timedelta
   from typing import Optional, List
   from sqlalchemy import select, func, extract, over, window, case, text
   from sqlalchemy.orm import Session, Mapped, mapped_column, DeclarativeBase
   from pydantic import BaseModel, Field

   # ... models ...
   # ... DTOs ...
   # ... Repository ...
