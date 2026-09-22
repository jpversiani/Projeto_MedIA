from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Estabelecimento(Base):
    __tablename__ = "estabelecimentos"

    id = Column(Integer, primary_key=True, index=True)
    cnes = Column(String(7), unique=True, index=True, nullable=False) # Código Nacional de Estabelecimentos de Saúde
    nome_fantasia = Column(String(200), nullable=False)
    razao_social = Column(String(200), nullable=True)
    municipio_ibge = Column(String(7), nullable=False)
    logradouro = Column(String(200), nullable=True)
    numero = Column(String(20), nullable=True)
    bairro = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    equipes = relationship("Equipe", back_populates="estabelecimento")

class Equipe(Base):
    __tablename__ = "equipes"

    id = Column(Integer, primary_key=True, index=True)
    ine = Column(String(10), unique=True, index=True, nullable=False) # Identificador Nacional de Equipe
    nome = Column(String(100), nullable=False)
    tipo_equipe = Column(String(50), default="eSF") # eSF (Estratégia Saúde da Família), eAP (Atenção Primária)
    estabelecimento_id = Column(Integer, ForeignKey("estabelecimentos.id"), nullable=False)

    estabelecimento = relationship("Estabelecimento", back_populates="equipes")
