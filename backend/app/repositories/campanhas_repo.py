from pydantic import BaseModel, Field, ConfigDict, field_validator
   from typing import Optional, List
   from datetime import datetime
   import re

   class CampanhaCreate(BaseModel):
       nome: str = Field(..., min_length=1, max_length=255)
       descricao: str = Field(..., min_length=1)
       objetivo: str = Field(..., min_length=1)
       data_inicio: datetime
       data_fim: datetime
       status: str = Field(default="ativa")

       model_config = ConfigDict(from_attributes=True)

   class CampanhaRead(CampanhaCreate):
       id: int
       criado_em: datetime
       atualizado_em: Optional[datetime] = None

       model_config = ConfigDict(from_attributes=True)

@field_validator('cpf')
   @classmethod
   def validar_cpf(cls, v: str) -> str:
       v = str(v).replace('.', '').replace('-', '')
       if len(v) != 11 or not v.isdigit():
           raise ValueError('CPF inválido')
       # Basic CPF validation logic (optional but good)
       return v

   @field_validator('cns')
   @classmethod
   def validar_cns(cls, v: str) -> str:
       v = str(v).replace('-', '')
       if len(v) != 15 or not v.isdigit():
           raise ValueError('CNS inválido')
       return v

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SAEnum
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
   from datetime import datetime
   import enum

   class Base(DeclarativeBase):
       pass

   class StatusCampanha(str, enum.Enum):
       RASCUNHO = "rascunho"
       ATIVA = "ativa"
       PAUSADA = "pausada"
       CONCLUIDA = "concluida"

   class StatusDisparo(str, enum.Enum):
       PENDENTE = "pendente"
       ENVIADO = "enviado"
       FALHA = "falha"
       LIDO = "lido"

   class StatusConfirmacao(str, enum.Enum):
       AGUARDANDO = "aguardando"
       CONFIRMADO = "confirmado"
       RECUSADO = "recusado"
       NAO_RESPONDIDO = "nao_respondido"

   class AcaoAuditoria(str, enum.Enum):
       CRIACAO = "criacao"
       ATUALIZACAO = "atualizacao"
       ACESSO = "acesso"
       EXCLUSAO = "exclusao"
       EXPORTACAO = "exportacao"

   class Campanha(Base):
       __tablename__ = "campanhas"
       id: Mapped[int] = mapped_column(primary_key=True)
       nome: Mapped[str] = mapped_column(String(255))
       descricao: Mapped[str] = mapped_column(Text)
       objetivo: Mapped[str] = mapped_column(String(500))
       status: Mapped[StatusCampanha] = mapped_column(SAEnum(StatusCampanha), default=StatusCampanha.RASCUNHO)
       data_inicio: Mapped[datetime] = mapped_column(DateTime)
       data_fim: Mapped[datetime] = mapped_column(DateTime)
       criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       atualizado_em: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)

       pacientes: Mapped[List["PacienteCampanha"]] = relationship(back_populates="campanha", lazy="selectin")
       disparos: Mapped[List["HistoricoDisparo"]] = relationship(back_populates="campanha", lazy="selectin")

   class PacienteCampanha(Base):
       __tablename__ = "pacientes_campanhas"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"))
       cns: Mapped[str] = mapped_column(String(15))
       cpf: Mapped[str] = mapped_column(String(14))
       cid10: Mapped[str] = mapped_column(String(10))
       ciap2: Mapped[str] = mapped_column(String(10))
       metodo_soap: Mapped[str] = mapped_column(String(50))
       status: Mapped[StatusConfirmacao] = mapped_column(SAEnum(StatusConfirmacao), default=StatusConfirmacao.AGUARDANDO)
       confirmacao_paciente: Mapped[Optional[str]] = mapped_column(String(20))
       ultima_atualizacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

       campanha: Mapped["Campanha"] = relationship(back_populates="pacientes")

   class HistoricoDisparo(Base):
       __tablename__ = "historico_disparos"
       id: Mapped[int] = mapped_column(primary_key=True)
       campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas.id"))
       participante_id: Mapped[int] = mapped_column(ForeignKey("pacientes_campanhas.id"))
       canal: Mapped[str] = mapped_column(String(20))
       conteudo: Mapped[str] = mapped_column(Text)
       status_envio: Mapped[StatusDisparo] = mapped_column(SAEnum(StatusDisparo), default=StatusDisparo.PENDENTE)
       data_envio: Mapped[datetime] = mapped_column(DateTime)
       resposta_paciente: Mapped[Optional[str]] = mapped_column(Text)
       tentativas: Mapped[int] = mapped_column(Integer, default=0)

       campanha: Mapped["Campanha"] = relationship(back_populates="disparos")

   class LogAuditoriaProtecaoDados(Base):
       __tablename__ = "logs_auditoria_lgpd"
       id: Mapped[int] = mapped_column(primary_key=True)
       entidade_tipo: Mapped[str] = mapped_column(String(50))
       entidade_id: Mapped[int] = mapped_column(Integer)
       acao: Mapped[AcaoAuditoria] = mapped_column(SAEnum(AcaoAuditoria))
       usuario_id: Mapped[Optional[int]] = mapped_column(Integer)
       data_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       ip_origem: Mapped[Optional[str]] = mapped_column(String(45))
       justificativa: Mapped[Optional[str]] = mapped_column(Text)
       conformidade_lgpd: Mapped[bool] = mapped_column(Boolean, default=True)
       dados_acessados: Mapped[Optional[str]] = mapped_column(Text)

from sqlalchemy.ext.asyncio import AsyncSession # Wait, the prompt says SQLAlchemy 2.0, doesn't specify sync/async. I'll use sync Session for simplicity, but note it's compatible. Actually, I'll use `sqlalchemy.orm.Session` as standard.
   from sqlalchemy import select, insert, update, delete
   from typing import Optional, List, Dict, Any
   from datetime import datetime
   import logging

   logger = logging.getLogger(__name__)

   class CampanhasRepository:
       def __init__(self, session: Session):
           self.session = session

       async def criar_campanha(self, data: CampanhaCreate) -> Campanha:
           # ...

from pydantic import BaseModel, Field, ConfigDict, field_validator, EmailStr
    from typing import Optional, List
    from datetime import datetime
    import re

    class CampanhaCreate(BaseModel):
        nome: str = Field(..., min_length=1, max_length=255)
        descricao: str = Field(..., min_length=1)
        objetivo: str = Field(..., min_length=1)
        data_inicio: datetime
        data_fim: datetime
        status: str = Field(default="ativa")

        model_config = ConfigDict(from_attributes=True)

    class CampanhaRead(CampanhaCreate):
        id: int
        criado_em: datetime
        atualizado_em: Optional[datetime] = None
        model_config = ConfigDict(from_attributes=True)

@field_validator('cpf')
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        v = str(v).strip()
        if len(v) != 11 or not v.isdigit():
            raise ValueError('CPF deve ter 11 dígitos numéricos')
        return v

    @field_validator('cns')
    @classmethod
    def validar_cns(cls, v: str) -> str:
        v = str(v).strip()
        if len(v) != 15 or not v.isdigit():
            raise ValueError('CNS deve ter 15 dígitos numéricos')
        return v
