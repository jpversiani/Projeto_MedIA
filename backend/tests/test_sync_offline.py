# backend/tests/test_sync_offline.py
"""
Testes de Resolução de Conflitos e Integridade Offline (C29)

Valida:
1. Sincronização de fila outbox sem perda de dados.
2. Resolução correta de conflito de prontuário modificado concorrentemente.
3. Validação de integridade criptográfica do lote sincronizado.

Conformidade com:
- Python 3.12, Pydantic v2, SQLAlchemy 2.0
- Padrões SUS/APS: CIAP-2, CID-10, SOAP, CNS/CPF
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import pytest
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

class Prontuario(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    cns: str
    cpf: str
    cid10: Optional[str] = None
    ciap2: Optional[str] = None
    metodo_soap: Optional[str] = None  # S, O, A, P
    conteudo_clinico: str
    versao: int = 1
    atualizado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EventoOutbox(BaseModel):
    id: str
    prontuario_id: str
    versao_base: int
    dados: Dict[str, Any]
    status: str = "pendente"
    tentativas: int = 0
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Prontuario(BaseModel):
    id: str
    cns: str
    cpf: str
    cid10: Optional[str] = None
    ciap2: Optional[str] = None
    metodo_soap: Optional[str] = None
    campos: Dict[str, Any] = Field(default_factory=dict)
    versao: int = 1
    atualizado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EventoAlteracao(BaseModel):
    prontuario_id: str
    versao_base: int
    campos_alterados: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SyncService:
    def __init__(self, max_tentativas: int = 3):
        self.max_tentativas = max_tentativas

    def aplicar_evento(self, prontuario: Prontuario, evento: EventoAlteracao) -> Prontuario:
        if evento.versao_base != prontuario.versao:
            raise ConflitoError(...)
        novos_campos = {**prontuario.campos, **evento.campos_alterados}
        prontuario.campos = novos_campos
        prontuario.versao += 1
        prontuario.atualizado_em = evento.timestamp
        return prontuario

    def resolver_conflito(self, prontuario_atual: Prontuario, evento: EventoAlteracao) -> Prontuario:
        # merge por campo, último timestamp vence
        # para simplificar, se evento.timestamp > prontuario_atual.atualizado_em, aplica, senão mantém
        if evento.timestamp > prontuario_atual.atualizado_em:
            return self.aplicar_evento(prontuario_atual, evento)
        return prontuario_atual

def resolver_conflito(self, prontuario_atual: Prontuario, evento: EventoAlteracao) -> Prontuario:
    # Se a versão base do evento é anterior à versão atual, há conflito.
    if evento.versao_base < prontuario_atual.versao:
        # Merge: para cada campo, se o campo foi alterado no evento e não foi alterado no prontuario atual desde a versão base, aplica.
        # Mas não temos histórico de alterações por campo. Vamos assumir que o prontuario_atual.campos contém os valores mais recentes conhecidos.
        # Para simplificar, se o timestamp do evento é maior que o timestamp do prontuario, aplica tudo; senão, descarta.
        if evento.timestamp > prontuario_atual.atualizado_em:
            return self.aplicar_evento(prontuario_atual, evento)
        return prontuario_atual
    else:
        return self.aplicar_evento(prontuario_atual, evento)

class Prontuario(BaseModel):
    id: str
    cns: str
    cpf: str
    cid10: Optional[str] = None
    ciap2: Optional[str] = None
    metodo_soap: Optional[str] = None
    campos: Dict[str, Any] = Field(default_factory=dict)
    campos_metadata: Dict[str, datetime] = Field(default_factory=dict)
    versao: int = 1
    atualizado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EventoAlteracao(BaseModel):
    prontuario_id: str
    versao_base: int
    campos_alterados: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

def aplicar_evento(self, prontuario: Prontuario, evento: EventoAlteracao) -> Prontuario:
    if evento.versao_base != prontuario.versao:
        raise ConflitoError(...)
    for campo, valor in evento.campos_alterados.items():
        prontuario.campos[campo] = valor
        prontuario.campos_metadata[campo] = evento.timestamp
    prontuario.versao += 1
    prontuario.atualizado_em = evento.timestamp
    return prontuario
