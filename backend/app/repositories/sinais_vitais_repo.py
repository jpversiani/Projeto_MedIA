from pydantic import BaseModel, Field, field_validator
   from enum import Enum
   from datetime import datetime
   from typing import Optional

   class VitalSignType(str, Enum):
       PA = "PA"
       FC = "FC"
       FR = "FR"
       TEMP = "TEMP"
       GLICEMIA = "GLICEMIA"
       SPO2 = "SPO2"

   class UrgencyLevel(str, Enum):
       LOW = "BAIXO"
       MEDIUM = "MEDIO"
       HIGH = "ALTO"
       CRITICAL = "CRITICO"

   class VitalSignCreate(BaseModel):
       paciente_cns: str = Field(..., pattern=r"^\d{15}$")
       paciente_cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       tipo_sinal: VitalSignType
       valor: float
       data_hora: datetime = Field(default_factory=datetime.now)
       ciap2: Optional[str] = Field(None, pattern=r"^[A-Z0-9]{1,4}$")
       cid10: Optional[str] = Field(None, pattern=r"^[A-Z]\d{2}$")
       nota_soap: Optional[str] = None

   class VitalSignResponse(BaseModel):
       id: int
       paciente_cns: str
       paciente_cpf: Optional[str]
       tipo_sinal: VitalSignType
       valor: float
       data_hora: datetime
       ciap2: Optional[str]
       cid10: Optional[str]
       nota_soap: Optional[str]
       alertas: list[VitalSignAlert] = []

       class ConfigDict = {"from_attributes": True}

from pydantic import BaseModel, Field, field_validator, ConfigDict
   from enum import Enum
   from datetime import datetime
   from typing import Optional, List

   class VitalSignType(str, Enum):
       PA = "PA"
       FC = "FC"
       FR = "FR"
       TEMP = "TEMP"
       GLICEMIA = "GLICEMIA"
       SPO2 = "SPO2"

   class UrgencyLevel(str, Enum):
       LOW = "BAIXO"
       MEDIUM = "MEDIO"
       HIGH = "ALTO"
       CRITICAL = "CRITICO"

   class VitalSignAlert(BaseModel):
       tipo_sinal: VitalSignType
       valor: float
       limite_inferior: Optional[float] = None
       limite_superior: Optional[float] = None
       nivel_urgencia: UrgencyLevel
       mensagem: str

   class VitalSignCreate(BaseModel):
       paciente_cns: str = Field(..., pattern=r"^\d{15}$")
       paciente_cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
       tipo_sinal: VitalSignType
       valor: float
       data_hora: datetime = Field(default_factory=datetime.now)
       ciap2: Optional[str] = Field(None, pattern=r"^[A-Z0-9]{1,4}$")
       cid10: Optional[str] = Field(None, pattern=r"^[A-Z]\d{2}$")
       nota_soap: Optional[str] = None

   class VitalSignResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: int
       paciente_cns: str
       paciente_cpf: Optional[str]
       tipo_sinal: VitalSignType
       valor: float
       data_hora: datetime
       ciap2: Optional[str]
       cid10: Optional[str]
       nota_soap: Optional[str]
       alertas: List[VitalSignAlert] = []

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SAEnum
   from sqlalchemy.orm import DeclarativeBase
   import enum

   class Base(DeclarativeBase):
       pass

   class VitalSignTypeEnum(str, enum.Enum):
       PA = "PA"
       FC = "FC"
       FR = "FR"
       TEMP = "TEMP"
       GLICEMIA = "GLICEMIA"
       SPO2 = "SPO2"

   class UrgencyLevelEnum(str, enum.Enum):
       LOW = "BAIXO"
       MEDIUM = "MEDIO"
       HIGH = "ALTO"
       CRITICAL = "CRITICO"

   class SinalVitalModel(Base):
       __tablename__ = "sinais_vitais"

       id = Column(Integer, primary_key=True, autoincrement=True)
       paciente_cns = Column(String(15), nullable=False, index=True)
       paciente_cpf = Column(String(11), nullable=True)
       tipo_sinal = Column(SAEnum(VitalSignTypeEnum), nullable=False)
       valor = Column(Float, nullable=False)
       data_hora = Column(DateTime, nullable=False, default=datetime.now)
       ciap2 = Column(String(4), nullable=True)
       cid10 = Column(String(3), nullable=True)
       nota_soap = Column(String, nullable=True)

from sqlalchemy import String, Float, DateTime, Enum as SAEnum
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
   from datetime import datetime
   import enum

   class Base(DeclarativeBase):
       pass

   class VitalSignTypeEnum(str, enum.Enum):
       PA = "PA"
       FC = "FC"
       FR = "FR"
       TEMP = "TEMP"
       GLICEMIA = "GLICEMIA"
       SPO2 = "SPO2"

   class UrgencyLevelEnum(str, enum.Enum):
       LOW = "BAIXO"
       MEDIUM = "MEDIO"
       HIGH = "ALTO"
       CRITICAL = "CRITICO"

   class SinalVitalModel(Base):
       __tablename__ = "sinais_vitais"

       id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
       paciente_cns: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
       paciente_cpf: Mapped[str | None] = mapped_column(String(11), nullable=True)
       tipo_sinal: Mapped[VitalSignTypeEnum] = mapped_column(SAEnum(VitalSignTypeEnum), nullable=False)
       valor: Mapped[float] = mapped_column(Float, nullable=False)
       data_hora: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
       ciap2: Mapped[str | None] = mapped_column(String(4), nullable=True)
       cid10: Mapped[str | None] = mapped_column(String(3), nullable=True)
       nota_soap: Mapped[str | None] = mapped_column(String, nullable=True)
