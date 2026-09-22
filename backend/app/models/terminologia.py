from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class CIAP2(Base):
    __tablename__ = "terminologias_ciap2"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), unique=True, index=True, nullable=False) # Ex: K86 (Hipertensão sem complicações), T90 (Diabetes)
    descricao = Column(String(300), nullable=False, index=True)
    capitulo = Column(String(100), nullable=True)
    ativo = Column(Boolean, default=True)

class CID10(Base):
    __tablename__ = "terminologias_cid10"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), unique=True, index=True, nullable=False) # Ex: I10, E11, J00
    descricao = Column(String(300), nullable=False, index=True)
    ativo = Column(Boolean, default=True)
