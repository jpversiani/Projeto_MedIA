```python:backend/app/models.py
"""
Modelos do banco de dados para o sistema de campanhas de saúde com suporte a SUS/APS.
- CIAP-2: Código de Identificação do Ativo de Pesquisa
- CID-10: Código Internacional de Diagnóstico
- Método SOAP: Simptomatização, Observação, Avaliação, Plano
- Identificação por CNS/CPF
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EstadoVisita(str, Enum):
    """Estados do ciclo de vida de uma visita domiciliar."""
    agendada = "agendada"
    em_progr = "em_progr"
    realizada = "realizada"
    cancelada = "cancelada"
    não_respondida = "nao_respondida"


class EstadoTeleatendimento(str, Enum):
    """Estados de confirmação de teleatendimento."""
    pendente = "pendente"
    confirmada = "confirmada"
    não_realizada = "nao_realizada"
    concluida = "concluida"


class TipoCampanha(str, Enum):
    """Tipos de campanhas de saúde."""
    vacinacao = "vacinacao"
    checkup = "checkup"
    monitoramento = "monitoramento"
    emergencial = "emergencial"
    prevention = "prevencao"


class Visitante(Base):
    """
    Modelo do Visitante com suporte a CNS/CPF e CIAP-2.
    """
    __tablename__ = "visitantes"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cnpj: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
    cnpj_cpf: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
    cnpj_cpf_formatado: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
    cnpj_cpf_valido: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    cnpj_cpf_validacao: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    sobrenome: Mapped[str] = mapped_column(String(100), nullable=False)
    data_nascimento: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ano_nascimento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
   