# Arquivo: backend/app/repositories/analytics_repo.py
   from __future__ import annotations
   from typing import Any, Dict, List, Optional
   from dataclasses import dataclass
   from pydantic import BaseModel, Field
   from sqlalchemy import select, func, extract, over, case, text
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy.orm import DeclarativeBase
   import asyncio

   # Pydantic v2 DTOs
   class ConsultationVolumeDTO(BaseModel):
       hour: int = Field(..., ge=0, le=23)
       dow: int = Field(..., ge=1, le=7) # 1=Monday, 7=Sunday
       count: int = Field(..., ge=0)
       percentage: float = Field(..., ge=0.0, le=100.0)

   class ProcedureDistributionDTO(BaseModel):
       codigo_procedimento: str
       descricao: str
       quantidade: int
       percentual: float

   class SOAPAdherenceDTO(BaseModel):
       metodo: str # SOAP, OPQRST, etc.
       quantidade: int
       percentual: float

   class IdentificationRateDTO(BaseModel):
       tipo_identificador: str # CNS, CPF
       quantidade: int
       percentual: float

   class CIAP2CID10DistributionDTO(BaseModel):
       codigo: str
       descricao: str
       tipo: str # CIAP-2 ou CID-10
       quantidade: int
       percentual: float

   class PatientTrendDTO(BaseModel):
       paciente_cns: str
       total_consultas: int
       ultima_consulta: str
       media_mensal: float
       tendencia: str # "crescente", "estavel", "decrescente"

   class AnalyticsRepository:
       def __init__(self, session_factory):
           self.session_factory = session_factory

       async def get_consultation_volume_by_hour_dow(self) -> List[ConsultationVolumeDTO]:
           # Query using extract hour and dayofweek
           # ...

# Arquivo: backend/app/repositories/analytics_repo.py
   from __future__ import annotations
   from typing import Any, Dict, List, Optional, Sequence
   from pydantic import BaseModel, Field, field_validator
   from sqlalchemy import select, func, extract, over, case, text, String, Integer
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
   from datetime import datetime, date
   import asyncio

   # Pydantic v2 DTOs
   class ConsultationVolumeDTO(BaseModel):
       hour: int = Field(..., ge=0, le=23)
       dow: int = Field(..., ge=1, le=7)
       count: int = Field(..., ge=0)
       percentage: float = Field(..., ge=0.0, le=100.0)

       class ConfigDict = {"from_attributes": True}

   class ProcedureDistributionDTO(BaseModel):
       codigo_procedimento: str
       descricao: str
       quantidade: int
       percentual: float

   class SOAPAdherenceDTO(BaseModel):
       metodo: str
       quantidade: int
       percentual: float

   class IdentificationRateDTO(BaseModel):
       tipo_identificador: str
       quantidade: int
       percentual: float

   class CIAP2CID10DistributionDTO(BaseModel):
       codigo: str
       descricao: str
       tipo: str
       quantidade: int
       percentual: float

   class PatientTrendDTO(BaseModel):
       paciente_cns: str
       total_consultas: int
       ultima_consulta: str
       media_mensal: float
       tendencia: str

   class AnalyticsRepository:
       def __init__(self, session_factory):
           self.session_factory = session_factory

       async def get_consultation_volume_by_hour_dow(self) -> List[ConsultationVolumeDTO]:
           # ...

stmt = (
       select(
           extract('hour', Consultas.data_hora).label('hour'),
           extract('dow', Consultas.data_hora).label('dow'),
           func.count(Consultas.id).label('count')
       )
       .where(Consultas.data_hora >= datetime.now() - timedelta(days=365))
       .group_by('hour', 'dow')
       .order_by('dow', 'hour')
   )

stmt = (
       select(
           Procedimentos.codigo.label('codigo'),
           Procedimentos.descricao.label('descricao'),
           Procedimentos.tipo.label('tipo'),
           func.count(ConsultasProcedimentos.id).label('quantidade')
       )
       .join(ConsultasProcedimentos, Procedimentos.id == ConsultasProcedimentos.procedimento_id)
       .join(Consultas, ConsultasProcedimentos.consulta_id == Consultas.id)
       .where(Consultas.data_hora >= datetime.now() - timedelta(days=365))
       .group_by(Procedimentos.codigo, Procedimentos.descricao, Procedimentos.tipo)
       .order_by(func.count(ConsultasProcedimentos.id).desc())
   )

stmt = (
       select(
           Evolucoes.metodo.label('metodo'),
           func.count(Evolucoes.id).label('quantidade')
       )
       .where(Evolucoes.metodo.in_(['SOAP', 'OPQRST', 'AVDI']))
       .group_by('metodo')
   )

stmt = (
       select(
           case(
               (Usuarios.cns.isnot(None), 'CNS'),
               (Usuarios.cpf.isnot(None), 'CPF'),
               else_='N/A'
           ).label('tipo_identificador'),
           func.count(Usuarios.id).label('quantidade')
       )
       .group_by('tipo_identificador')
   )

stmt = (
       select(
           Consultas.paciente_cns.label('paciente_cns'),
           func.count(Consultas.id).label('total_consultas'),
           func.max(Consultas.data_hora).label('ultima_consulta'),
           func.avg(func.extract('month', Consultas.data_hora)).label('media_mensal'),
           over(
               func.row_number().partition_by(Consultas.paciente_cns).order_by(Consultas.data_hora.desc()),
               label='rn'
           ).label('rn')
       )
       .group_by(Consultas.paciente_cns)
       .having(func.count(Consultas.id) > 1)
   )
