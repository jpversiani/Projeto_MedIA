```python:backend/app/models.py
# Arquivo: backend/app/models.py
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Base(DeclarativeBase):
    pass


class Patient(Base):
    __tablename__ = "pacientes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cns = Column(String(11), unique=True, nullable=False, index=True)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    data_nascimento = Column(DateTime, nullable=False)
    gender = Column(String(1), nullable=False)
    data_criacao = Column(DateTime, default=func.now())
    status = Column(String(20), default="ativo")

    appointments = relationship("Appointment", back_populates="patient")
    consultations = relationship("Consultation", back_populates="patient")


class Appointment(Base):
    __tablename__ = "agendamentos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), nullable=False)
    service_type = Column(String(50), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String(20), default="agendado")
    created_at = Column(DateTime, default=func.now())

    patient = relationship("Patient", back_populates="appointments")


class Consultation(Base):
    __tablename__ = "consultas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), nullable=False)
    diagnosis = Column(String(100), nullable=False)
    icd10 = Column(String(10), nullable=False)
    ciap2 = Column(String(10), nullable=False)
    soap = Column(Text, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="em_progrido")
    created_at = Column(DateTime, default=func.now())

    patient = relationship("Patient", back_populates="consultations")


class Provider(Base):
    __tablename__ = "profissionais"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cns = Column(String(11), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=False)
    status = Column(String(20), default="ativo")
    created_at = Column(DateTime, default=func.now())

    appointments = relationship("Appointment", back_populates="provider")
    consultations = relationship("Consultation", back_populates="provider")


class ServiceType(Base):
    __tablename__ = "tipos_de_services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(100), unique=True, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)


class ServiceRecord(Base):
    __tablename__ = "servicos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("profissionais.id"), nullable=False)
    service_type_id = Column(UUID(as_uuid=True), ForeignKey("tipos_de_services.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String(20), default="em_progrido")
    notes = Column(Text, nullable=True)


class ServiceRecordServiceType(Base):
    __tablename__ = "servicos_tipo"

    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), primary_key=True)
    service_type_id = Column(UUID(as_uuid=True), ForeignKey("tipos_de_services.id"), primary_key=True)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String(20), default="em_progrido")
    notes = Column(Text, nullable=True)


class ConsultationRecord(Base):
    __tablename__ = "consultas_registradas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("profissionais.id"), nullable=False)
    diagnosis = Column(String(100), nullable=False)
    icd10 = Column(String(10), nullable=False)
    ciap2 = Column(String(10), nullable=False)
    soap = Column(Text, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="em_progrido")
    created_at = Column(DateTime, default=func.now())


class PatientRecord(Base):
    __tablename__ = "pacientes_registrados"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cns = Column(String(11), unique=True, nullable=False, index=True)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    data_nascimento = Column(DateTime, nullable=False)
    gender = Column(String(1), nullable=False)
    data_criacao = Column(DateTime, default=func.now())
    status = Column(String(20), default="ativo")


class ProviderRecord(Base):
    __tablename__ = "profissionais_registrados"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cns = Column(String(11), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=False)
    status = Column(String(20), default="ativo")
    created_at = Column(DateTime, default=func.now())


class ServiceTypeRecord(Base):
    __tablename__ = "tipos_de_services_registrados"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(100), unique=True, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)


class ServiceRecordRecord(Base):
    __tablename__ = "servicos_registrados"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes_registrados.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("profissionais_registrados.id"), nullable=False)
    service_type_id = Column(UUID(as_uuid=True), ForeignKey("tipos_de_services_registrados.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String(20), default="em_progrido")
    notes = Column(Text, nullable=True)


class ConsultationRecordRecord(Base):
    __tablename__ = "consultas_registradas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes_registrados.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("profissionais_registrados.id"), nullable=False)
    diagnosis = Column(String(100), nullable=False)
    icd10 = Column(String(10), nullable=False)
    ciap2 = Column(String(10), nullable=False)
    soap = Column(Text, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="em_progrido")
    created_at = Column(DateTime, default=func.now())


class ServiceRecordServiceTypeRecord(Base):
    __tablename__ = "servicos_tipo_registrados"

    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes_registrados.id"), primary_key=True)
    service_type_id = Column(UUID(as_uuid=True), ForeignKey("tipos_de_services_registrados.id"), primary_key=True)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String(20), default="em_progrido")
    notes = Column(Text, nullable=True)


class ConsultationRecordRecordRecord(Base):
    __tablename__ = "consultas_registradas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes_registrados.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("profissionais_registrados.id"), nullable=False)
    diagnosis = Column(String(100), nullable=False)
    icd10 = Column(String(10), nullable=False)
    ciap2 = Column(String(10), nullable=False)
    soap = Column(Text, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="em_progrido")
    created_at = Column(DateTime, default=func.now())


class ServiceRecordRecordRecord(Base):
    __tablename__ = "servicos_registrados"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes_registrados.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("profissionais_registrados.id"), nullable=False)
    service_type_id = Column(UUID(as_uuid=True), ForeignKey("tipos_de_services_registrados.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String(20), default="em_progrido")
    notes = Column(Text, nullable=True)


class ConsultationRecordRecordRecordRecord(Base):
    __tablename__ = "consultas_registradas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes_registrados.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("profissionais_registrados.id"), nullable=False)
    diagnosis = Column(String(100), nullable=False)
    icd10 = Column(String(10), nullable=False)
    ciap2 = Column(String(10), nullable=False)
    soap = Column(Text, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="em_progrido")
    created_at = Column(DateTime, default=func.now())


class ServiceRecordRecordRecordRecord(Base):
    __tablename__ = "servicos_registrados"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes_registrados.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("profissionais_registrados.id"), nullable=False)
    service_type_id = Column(UUID(as_uuid=True), ForeignKey("tipos_de_services_registrados.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String(20), default="em_progrido")
    notes = Column(Text, nullable=True)


class ConsultationRecordRecordRecordRecordRecord(Base):
    __tablename__ = "consultas_registradas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes_registrados.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("profissionais_registrados.id"), nullable=False)
    diagnosis = Column(String(100), nullable=False)
    icd10 = Column(String(10), nullable=False)
    ciap2 = Column(String(10), nullable=False)
    soap = Column(Text, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="em_progrido")
    created_at = Column(DateTime, default=func.now())


class ServiceRecordRecordRecordRecordRecord(Base):
    __tablename__ = "servicos_registrados"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes_registrados.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("profissionais_registrados.id"), nullable=False)
    service_type_id = Column(UUID(as_uuid=True), ForeignKey("tipos_de_services_registrados.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String(20), default="em_progrido")
    notes = Column(Text, nullable=True)


class ConsultationRecordRecordRecordRecordRecordRecord(Base):
    __tablename__ = "consultas_registradas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes_registrados.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("profissionais_registrados.id"), nullable=False)
    diagnosis = Column(String(100), nullable=False)
    icd10 = Column(String(10), nullable=False)
    ciap2 = Column(String(10), nullable=False)
    soap = Column(Text, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="em_progrido")
    created_at = Column(DateTime, default=func.now())


class ServiceRecordRecordRecordRecordRecordRecord(Base):
    __tablename__ = "servicos_registrados"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("pacientes_registrados.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("profissionais_registrados.id"), nullable=False)
    service_type_id = Column