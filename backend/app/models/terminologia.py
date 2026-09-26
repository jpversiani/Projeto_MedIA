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


class CID11(Base):
    __tablename__ = "terminologias_cid11"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(15), unique=True, index=True, nullable=False) # Ex: BA00, 5A11, 6B00 (Padrão MMS da OMS)
    titulo = Column(String(300), nullable=False, index=True)
    capitulo = Column(String(150), nullable=True, index=True)
    capitulo_numero = Column(String(10), nullable=True)
    cid10_equivalente = Column(String(10), nullable=True, index=True) # Mapeamento dual-coding para faturamento TISS
    definicao = Column(String(1000), nullable=True)
    ativo = Column(Boolean, default=True)

