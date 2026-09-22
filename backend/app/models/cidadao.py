from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class Cidadao(Base):
    __tablename__ = "cidadaos"

    id = Column(Integer, primary_key=True, index=True)
    cns = Column(String(15), unique=True, index=True, nullable=True) # Cartão Nacional de Saúde
    cpf = Column(String(11), unique=True, index=True, nullable=True)
    nome_completo = Column(String(200), nullable=False, index=True)
    nome_social = Column(String(200), nullable=True)
    nome_mae = Column(String(200), nullable=True)
    data_nascimento = Column(Date, nullable=False)
    sexo = Column(String(1), nullable=False) # M (Masculino), F (Feminino), I (Indeterminado)
    raca_cor = Column(String(20), default="Parda") # Branca, Preta, Parda, Amarela, Indígena
    
    # Contato e Localização
    telefone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    cep = Column(String(8), nullable=True)
    logradouro = Column(String(200), nullable=True)
    numero = Column(String(20), nullable=True)
    complemento = Column(String(100), nullable=True)
    bairro = Column(String(100), nullable=True)
    municipio_ibge = Column(String(7), nullable=True) # Ex: 3143302 (Montes Claros - MG)

    # Condições de saúde autorreferidas na APS
    hipertenso = Column(Boolean, default=False)
    diabetico = Column(Boolean, default=False)
    gestante = Column(Boolean, default=False)
    fumante = Column(Boolean, default=False)
    alergias = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    acolhimentos = relationship("FilaAcolhimento", back_populates="cidadao")
    atendimentos = relationship("AtendimentoSOAP", back_populates="cidadao")
