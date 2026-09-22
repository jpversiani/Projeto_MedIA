from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class AtendimentoSOAP(Base):
    __tablename__ = "atendimentos_soap"

    id = Column(Integer, primary_key=True, index=True)
    cidadao_id = Column(Integer, ForeignKey("cidadaos.id"), nullable=False)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=False)
    estabelecimento_id = Column(Integer, ForeignKey("estabelecimentos.id"), nullable=False)
    fila_id = Column(Integer, ForeignKey("fila_acolhimento.id"), nullable=True)

    data_hora_inicio = Column(DateTime, default=datetime.utcnow)
    data_hora_fim = Column(DateTime, nullable=True)

    # SUBJETIVO: Queixa principal, histórico da moléstia atual, percepção do paciente
    subjetivo_motivo = Column(String(500), nullable=True)
    subjetivo_notas = Column(Text, nullable=True)

    # OBJETIVO: Exame físico e achados clínicos
    objetivo_exame_fisico = Column(Text, nullable=True)
    objetivo_antropometria_sinais = Column(Text, nullable=True) # JSON resumido dos sinais vitais

    # AVALIAÇÃO: Diagnóstico, raciocínio clínico e problemas
    avaliacao_notas = Column(Text, nullable=True)

    # PLANO: Conduta clínica, intervenções, medicamentos e exames
    plano_conduta = Column(Text, nullable=True)
    plano_prescricoes = Column(Text, nullable=True) # JSON ou texto estruturado de medicamentos
    plano_exames = Column(Text, nullable=True)      # Exames solicitados
    plano_encaminhamentos = Column(Text, nullable=True)

    status = Column(String(30), default="FINALIZADO") # FINALIZADO, EM_ANDAMENTO
    created_at = Column(DateTime, default=datetime.utcnow)

    cidadao = relationship("Cidadao", back_populates="atendimentos")
    fila = relationship("FilaAcolhimento", back_populates="atendimento")
    problemas = relationship("AtendimentoProblema", back_populates="atendimento", cascade="all, delete-orphan")

class AtendimentoProblema(Base):
    __tablename__ = "atendimento_problemas"

    id = Column(Integer, primary_key=True, index=True)
    atendimento_id = Column(Integer, ForeignKey("atendimentos_soap.id"), nullable=False)
    tipo_codigo = Column(String(10), nullable=False) # 'CIAP2' ou 'CID10'
    codigo = Column(String(10), nullable=False)      # Ex: K86, I10
    descricao = Column(String(300), nullable=False)
    situacao = Column(String(30), default="ATIVO")    # ATIVO, RESOLVIDO, RASTREAMENTO

    atendimento = relationship("AtendimentoSOAP", back_populates="problemas")
