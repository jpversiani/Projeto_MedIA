"""
Modelos de Autenticação, Usuários, Multi-Tenancy (Multi-Clínica) e Trilha de Auditoria (LGPD/CFM).
"""
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class PapelUsuarioEnum(str, enum.Enum):
    MEDICO = "MEDICO"
    RECEPCAO = "RECEPCAO"
    ADMIN = "ADMIN"
    FARMACEUTICO = "FARMACEUTICO"
    PACIENTE = "PACIENTE"


class Usuario(Base):
    """Usuário do sistema com suporte a SSO (Google / Microsoft) e credenciais locais."""
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, index=True, nullable=False)
    nome = Column(String(200), nullable=False)
    hashed_password = Column(String(300), nullable=True) # Nullable para usuários puramente SSO
    
    # SSO Metadata
    sso_provider = Column(String(50), default="local") # "google", "microsoft", "local"
    sso_id = Column(String(200), nullable=True, index=True)
    foto_url = Column(String(500), nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # 2FA / MFA (TOTP)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vinculos = relationship("VinculoClinica", back_populates="usuario", cascade="all, delete-orphan")


class VinculoClinica(Base):
    """
    Relação N:N entre Usuário e Estabelecimentos (Clínicas/Consultórios).
    Permite que o mesmo médico atenda no consultório particular e em clínicas conveniadas.
    """
    __tablename__ = "vinculos_clinica"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    estabelecimento_id = Column(Integer, ForeignKey("estabelecimentos.id"), nullable=False, index=True)
    
    papel = Column(SAEnum(PapelUsuarioEnum), nullable=False, default=PapelUsuarioEnum.MEDICO)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=True) # Vincula ao CRM/CNS se for médico
    is_default = Column(Boolean, default=False) # Clínica ativa padrão ao logar
    created_at = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="vinculos")
    estabelecimento = relationship("Estabelecimento")
    profissional = relationship("Profissional")


class AuditTrail(Base):
    """
    Trilha de Auditoria Imutável (LGPD Art. 11 & Resolução CFM 2.314/2022).
    Registra todo acesso, visualização ou alteração em dados sensíveis de saúde com hash encadeado.
    """
    __tablename__ = "audit_trail"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    estabelecimento_id = Column(Integer, ForeignKey("estabelecimentos.id"), nullable=True, index=True)
    
    acao = Column(String(100), nullable=False, index=True) # "LOGIN_SSO", "ACESSAR_PRONTUARIO", "EMITIR_PRESCRICAO", "EXPORTAR_TISS"
    recurso_tipo = Column(String(100), nullable=False) # "Cidadao", "Prontuario", "Receita", "GuiaTISS"
    recurso_id = Column(String(100), nullable=False)
    
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(300), nullable=True)
    detalhes_json = Column(Text, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    hash_anterior = Column(String(64), nullable=True) # Encadeamento de integridade
    hash_integridade = Column(String(64), nullable=False) # SHA-256 canônico do registro
