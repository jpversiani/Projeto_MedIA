from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum as SAEnum
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
   from sqlalchemy.dialects.postgresql import UUID
   import uuid
   from datetime import datetime
   from enum import Enum as PyEnum

   class Base(DeclarativeBase):
       pass

   class StatusCampanha(PyEnum):
       RASCUNHO = "rascunho"
       ATIVA = "ativa"
       PAUSADA = "pausada"
       CONCLUIDA = "concluida"

   class StatusEnvio(PyEnum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       FALHA = "falha"
       LIDO = "lido"

   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       nome: Mapped[str] = mapped_column(String(255), nullable=False)
       descricao: Mapped[str] = mapped_column(Text, nullable=True)
       status: Mapped[StatusCampanha] = mapped_column(SAEnum(StatusCampanha), default=StatusCampanha.RASCUNHO)
       criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
       disparos: Mapped[list["Disparo"]] = relationship(back_populates="campanha", cascade="all, delete-orphan")

   class Disparo(Base):
       __tablename__ = "disparos"
       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       campanha_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campanhas.id"), nullable=False)
       paciente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
       mensagem: Mapped[str] = mapped_column(Text, nullable=False)
       status_envio: Mapped[StatusEnvio] = mapped_column(SAEnum(StatusEnvio), default=StatusEnvio.PENDENTE)
       criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       campanha: Mapped["Campanha"] = relationship(back_populates="disparos")
       confirmacao: Mapped["ConfirmacaoPaciente"] = relationship(back_populates="disparo", uselist=False, cascade="all, delete-orphan")

   class ConfirmacaoPaciente(Base):
       __tablename__ = "confirmacoes_paciente"
       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       disparo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("disparos.id"), nullable=False)
       confirmado: Mapped[bool] = mapped_column(Boolean, default=False)
       confirmado_em: Mapped[datetime] = mapped_column(DateTime, nullable=True)
       metadados: Mapped[str] = mapped_column(Text, nullable=True)
       disparo: Mapped["Disparo"] = relationship(back_populates="confirmacao")

   class LogAuditoriaLGPD(Base):
       __tablename__ = "logs_auditoria_lgpd"
       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       entidade_tipo: Mapped[str] = mapped_column(String(50), nullable=False) # 'CAMPAHNA', 'DISPARO', 'PACIENTE'
       entidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
       acao: Mapped[str] = mapped_column(String(100), nullable=False) # 'CRIAR', 'ACESSAR', 'MODIFICAR', 'EXCLUIR'
       detalhes: Mapped[str] = mapped_column(Text, nullable=True)
       realizado_por: Mapped[str] = mapped_column(String(255), nullable=False)
       criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
