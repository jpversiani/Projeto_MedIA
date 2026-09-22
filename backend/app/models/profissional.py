from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base

class Profissional(Base):
    __tablename__ = "profissionais"

    id = Column(Integer, primary_key=True, index=True)
    cns = Column(String(15), unique=True, index=True, nullable=False) # Cartão Nacional de Saúde
    cpf = Column(String(11), unique=True, index=True, nullable=False)
    nome = Column(String(200), nullable=False)
    cbo = Column(String(10), nullable=False) # Ex: 225142 (Médico da Estratégia de Saúde da Família), 223505 (Enfermeiro)
    cbo_descricao = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
