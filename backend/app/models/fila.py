from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class FilaAcolhimento(Base):
    __tablename__ = "fila_acolhimento"

    id = Column(Integer, primary_key=True, index=True)
    cidadao_id = Column(Integer, ForeignKey("cidadaos.id"), nullable=False)
    estabelecimento_id = Column(Integer, ForeignKey("estabelecimentos.id"), nullable=False)
    profissional_triagem_id = Column(Integer, ForeignKey("profissionais.id"), nullable=True)

    data_hora_entrada = Column(DateTime, default=datetime.utcnow, index=True)
    tipo_demanda = Column(String(50), default="ESPONTANEA") # ESPONTANEA, AGENDADA, URGENCIA
    classificacao_risco = Column(String(20), default="VERDE") # VERMELHO, AMARELO, VERDE, AZUL
    motivo_acolhimento = Column(String(500), nullable=True)

    # Sinais Vitais e Antropometria
    pressao_sistolica = Column(Integer, nullable=True)   # Ex: 120 mmHg
    pressao_diastolica = Column(Integer, nullable=True)  # Ex: 80 mmHg
    frequencia_cardiaca = Column(Integer, nullable=True) # bpm
    frequencia_respiratoria = Column(Integer, nullable=True) # irpm
    temperatura = Column(Float, nullable=True)           # °C
    saturacao_o2 = Column(Integer, nullable=True)        # %
    glicemia_capilar = Column(Integer, nullable=True)    # mg/dL
    peso_kg = Column(Float, nullable=True)
    altura_cm = Column(Float, nullable=True)
    imc = Column(Float, nullable=True)

    status = Column(String(30), default="AGUARDANDO_ATENDIMENTO") # AGUARDANDO_ATENDIMENTO, EM_ATENDIMENTO, FINALIZADO, EVASAO
    created_at = Column(DateTime, default=datetime.utcnow)

    cidadao = relationship("Cidadao", back_populates="acolhimentos")
    atendimento = relationship("AtendimentoSOAP", back_populates="fila", uselist=False)
