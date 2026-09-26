"""
Schemas Pydantic v2 para Autenticação, SSO (Google/Microsoft), MFA e Multi-Tenancy.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = None
    mfa_code: Optional[str] = None
    demo_role: Optional[str] = None # Para login rápido de teste de MVP


class SSOLoginRequest(BaseModel):
    provider: str = Field(..., description="'google' ou 'microsoft'")
    id_token: Optional[str] = None
    access_token: Optional[str] = None
    code: Optional[str] = None


class VinculoClinicaOut(BaseModel):
    id: int
    estabelecimento_id: int
    estabelecimento_nome: str
    cnes: str
    papel: str
    profissional_id: Optional[int] = None
    crm: Optional[str] = None
    is_default: bool

    class Config:
        from_attributes = True


class UsuarioOut(BaseModel):
    id: int
    email: str
    nome: str
    sso_provider: str
    foto_url: Optional[str] = None
    is_active: bool
    is_superuser: bool
    mfa_enabled: bool
    clinica_ativa: Optional[VinculoClinicaOut] = None
    vinculos: List[VinculoClinicaOut] = []

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900 # 15 minutos
    usuario: UsuarioOut


class SwitchClinicRequest(BaseModel):
    estabelecimento_id: int


class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_url: str
    qr_code_svg: str


class MfaVerifyRequest(BaseModel):
    code: str


class AuditTrailOut(BaseModel):
    id: int
    usuario_id: Optional[int] = None
    usuario_email: Optional[str] = None
    estabelecimento_id: Optional[int] = None
    acao: str
    recurso_tipo: str
    recurso_id: str
    ip_address: Optional[str] = None
    timestamp: datetime
    hash_integridade: str

    class Config:
        from_attributes = True
