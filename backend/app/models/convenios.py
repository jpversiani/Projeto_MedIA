import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class GuiaStatus(str, enum.Enum):
    GERADA = "GERADA"
    ENVIADA = "ENVIADA"
    AUTORIZADA = "AUTORIZADA"
    GLOSADA = "GLOSADA"
    PAGA = "PAGA"
    CANCELADA = "CANCELADA"

class TipoGuia(str, enum.Enum):
    CONSULTA = "CONSULTA"
    SP_SADT = "SP_SADT"

class LancamentoTipo(str, enum.Enum):
    PARTICULAR = "PARTICULAR"
    CONVENIO = "CONVENIO"
    REEMBOLSO = "REEMBOLSO"

class LancamentoStatus(str, enum.Enum):
    PENDENTE = "PENDENTE"
    PAGO = "PAGO"
    GLOSADO = "GLOSADO"
    CANCELADO = "CANCELADO"

class Operadora(Base):
    __tablename__ = "operadoras"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False)
    registro_ans = Column(String(20), unique=True, nullable=False)
    cnpj = Column(String(14), unique=True, nullable=False)
    contato_email = Column(String(255), nullable=True)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    planos = relationship("Plano", back_populates="operadora", cascade="all, delete-orphan")

class Plano(Base):
    __tablename__ = "planos"

    id = Column(Integer, primary_key=True, index=True)
    operadora_id = Column(Integer, ForeignKey("operadoras.id"), nullable=False)
    nome = Column(String(100), nullable=False)
    codigo_plano = Column(String(50), nullable=False)
    tipo = Column(String(50), default="AMBULATORIAL")
    ativo = Column(Boolean, default=True)

    operadora = relationship("Operadora", back_populates="planos")
    guias = relationship("GuiaTISS", back_populates="plano", cascade="all, delete-orphan")

class GuiaTISS(Base):
    __tablename__ = "guias_tiss"

    id = Column(Integer, primary_key=True, index=True)
    numero_guia = Column(String(50), unique=True, nullable=False, index=True)
    tipo_guia = Column(Enum(TipoGuia), default=TipoGuia.CONSULTA, nullable=False)
    plano_id = Column(Integer, ForeignKey("planos.id"), nullable=True)
    atendimento_id = Column(Integer, ForeignKey("atendimentos_soap.id"), nullable=True)
    paciente_cns = Column(String(15), nullable=True)
    paciente_cpf = Column(String(14), nullable=True)
    paciente_nome = Column(String(200), nullable=True)
    numero_carteira = Column(String(50), nullable=True)
    
    data_emissao = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(GuiaStatus), default=GuiaStatus.GERADA, nullable=False)
    
    ciap2_codigo = Column(String(10), nullable=True)
    cid10_codigo = Column(String(10), nullable=True)
    procedimento_tuss = Column(String(20), default="10101012")  # Consulta médica em consultório (TUSS)
    valor_total = Column(Float, default=0.0)
    
    xml_tiss = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)

    plano = relationship("Plano", back_populates="guias")
    lancamentos = relationship("LancamentoFinanceiro", back_populates="guia", cascade="all, delete-orphan")

class LancamentoFinanceiro(Base):
    __tablename__ = "lancamentos_financeiros"

    id = Column(Integer, primary_key=True, index=True)
    guia_id = Column(Integer, ForeignKey("guias_tiss.id"), nullable=True)
    atendimento_id = Column(Integer, ForeignKey("atendimentos_soap.id"), nullable=True)
    
    paciente_cpf = Column(String(14), nullable=False)
    paciente_nome = Column(String(200), nullable=False)
    tipo = Column(Enum(LancamentoTipo), default=LancamentoTipo.CONVENIO, nullable=False)
    valor = Column(Float, nullable=False)
    descricao = Column(String(255), nullable=True)
    status = Column(Enum(LancamentoStatus), default=LancamentoStatus.PENDENTE, nullable=False)
    data_lancamento = Column(DateTime, default=datetime.utcnow)
    data_pagamento = Column(DateTime, nullable=True)
    
    # DMED / Comprovante Fiscal
    recibo_numero = Column(String(50), nullable=True)
    cpf_cnpj_pagador = Column(String(14), nullable=True)
    nome_pagador = Column(String(200), nullable=True)

    guia = relationship("GuiaTISS", back_populates="lancamentos")
