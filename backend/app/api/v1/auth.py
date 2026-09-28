"""
Rotas de Autenticação, SSO (Google e Microsoft), Multi-Tenancy e Auditoria de Acesso.
"""
import os
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.usuario import Usuario, VinculoClinica, PapelUsuarioEnum, AuditTrail
from app.models.estabelecimento import Estabelecimento
from app.models.profissional import Profissional
from app.schemas.auth import (
    LoginRequest,
    SSOLoginRequest,
    TokenResponse,
    UsuarioOut,
    SwitchClinicRequest,
    MfaSetupResponse,
    MfaVerifyRequest,
    AuditTrailOut,
)
from app.services.auth_service import (
    AuthService,
    verify_password,
    hash_password,
    create_access_token,
    decode_access_token,
    generate_totp_secret,
    verify_totp_token,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["Autenticação & SSO (Google/Microsoft)"])


# ------------------------------------------------------------------
# Dependência de Usuário Autenticado via Bearer Token
# ------------------------------------------------------------------
def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Tuple[Usuario, Optional[int]]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso ausente ou inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada ou token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = int(payload["sub"])
    usuario = db.query(Usuario).filter(Usuario.id == user_id, Usuario.is_active == True).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    
    clinica_id = payload.get("clinica_id")
    return usuario, clinica_id


# ------------------------------------------------------------------
# Endpoints de Autenticação e Demo
# ------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Login tradicional por email/senha ou login instantâneo de demonstração para testes de MVP.

    - Login demo: basta enviar ``{"demo_role": "medico_titular"}`` (email é opcional).
    - Login local: ``{"email": "...", "password": "..."}`` (com ``mfa_code`` opcional).
    """
    usuario = None
    
    # Suporte a login rápido de demonstração (Dr. Versiani, Dra. Letícia, Secretária, Admin)
    if payload.demo_role:
        role_map = {
            "medico_titular": ("dr.versiani@media-saude.com.br", "Dr. João Paulo Versiani", PapelUsuarioEnum.MEDICO),
            "medica_familia": ("dra.leticia@media-saude.com.br", "Dra. Letícia Mendes", PapelUsuarioEnum.MEDICO),
            "secretaria": ("recepcao@media-saude.com.br", "Maria Auxiliadora (Recepção)", PapelUsuarioEnum.RECEPCAO),
            "admin": ("admin@media-saude.com.br", "Carlos Eduardo (Gestor)", PapelUsuarioEnum.ADMIN),
        }
        if payload.demo_role in role_map:
            email, nome, papel = role_map[payload.demo_role]
            usuario = db.query(Usuario).filter(Usuario.email == email).first()
            if not usuario:
                usuario = Usuario(
                    email=email,
                    nome=nome,
                    sso_provider="local",
                    is_active=True,
                    is_superuser=(papel == PapelUsuarioEnum.ADMIN)
                )
                db.add(usuario)
                db.commit()
                db.refresh(usuario)
                
                # Criar vínculos com clínicas existentes
                ests = db.query(Estabelecimento).all()
                for idx, est in enumerate(ests):
                    vinculo = VinculoClinica(
                        usuario_id=usuario.id,
                        estabelecimento_id=est.id,
                        papel=papel,
                        is_default=(idx == 0)
                    )
                    db.add(vinculo)
                db.commit()

    if not usuario:
        usuario = db.query(Usuario).filter(Usuario.email == payload.email).first()
        if not usuario or not verify_password(payload.password or "", usuario.hashed_password or ""):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")

    # Validar MFA se ativado
    if usuario.mfa_enabled and usuario.mfa_secret:
        if not payload.mfa_code or not verify_totp_token(usuario.mfa_secret, payload.mfa_code):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código MFA inválido.")

    # Resolver vínculo de clínica ativa padrão
    vinculo_padrao = db.query(VinculoClinica).filter(
        VinculoClinica.usuario_id == usuario.id,
        VinculoClinica.is_default == True
    ).first() or db.query(VinculoClinica).filter(VinculoClinica.usuario_id == usuario.id).first()

    token = create_access_token(usuario, vinculo_padrao)
    user_out = AuthService.get_usuario_out(db, usuario, vinculo_padrao.estabelecimento_id if vinculo_padrao else None)

    # Registrar na Trilha de Auditoria (LGPD)
    AuditService.registrar_evento(
        db=db,
        acao="LOGIN_SUCESSO",
        recurso_tipo="Usuario",
        recurso_id=str(usuario.id),
        usuario_id=usuario.id,
        estabelecimento_id=vinculo_padrao.estabelecimento_id if vinculo_padrao else None,
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent"),
        detalhes={"provider": usuario.sso_provider, "papel": vinculo_padrao.papel.value if vinculo_padrao else None}
    )

    return TokenResponse(access_token=token, usuario=user_out)


# ------------------------------------------------------------------
# Endpoints de SSO (Google & Microsoft)
# ------------------------------------------------------------------
@router.get("/sso/google/url")
def get_google_auth_url():
    """Gera a URL de redirecionamento para login federado com o Google."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "mock_media_google_client_id.apps.googleusercontent.com")
    redirect_uri = "http://localhost:8000/api/v1/auth/sso/google/callback"
    scope = "openid%20profile%20email"
    url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&access_type=offline&prompt=consent"
    return {"provider": "google", "auth_url": url}


@router.post("/sso/google/callback", response_model=TokenResponse)
def google_sso_callback(payload: SSOLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Processa o callback ou id_token do Google OIDC."""
    # Simulação segura de extração ou validação OIDC para testes locais
    email = "medico.google@clinica-exemplo.com.br"
    nome = "Dr. Médico Google Workspace"
    sub_id = payload.id_token or "google_sub_109283741"
    
    usuario = AuthService.get_or_create_sso_user(
        db=db,
        provider=payload.provider or "google",
        sso_id=sub_id,
        email=email,
        nome=nome,
        foto_url="https://lh3.googleusercontent.com/a/default-user"
    )

    vinculo_padrao = db.query(VinculoClinica).filter(VinculoClinica.usuario_id == usuario.id).first()
    token = create_access_token(usuario, vinculo_padrao)
    user_out = AuthService.get_usuario_out(db, usuario, vinculo_padrao.estabelecimento_id if vinculo_padrao else None)

    AuditService.registrar_evento(
        db=db,
        acao="LOGIN_SSO_GOOGLE",
        recurso_tipo="Usuario",
        recurso_id=str(usuario.id),
        usuario_id=usuario.id,
        estabelecimento_id=vinculo_padrao.estabelecimento_id if vinculo_padrao else None,
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent")
    )
    return TokenResponse(access_token=token, usuario=user_out)


@router.get("/sso/microsoft/url")
def get_microsoft_auth_url():
    """Gera a URL de autenticação com Microsoft Entra ID (Azure AD / Office 365)."""
    client_id = os.getenv("MICROSOFT_CLIENT_ID", "mock_media_microsoft_client_id")
    redirect_uri = "http://localhost:8000/api/v1/auth/sso/microsoft/callback"
    scope = "openid%20profile%20email%20User.Read"
    url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={scope}"
    return {"provider": "microsoft", "auth_url": url}


@router.post("/sso/microsoft/callback", response_model=TokenResponse)
def microsoft_sso_callback(payload: SSOLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Processa o callback do Microsoft Entra ID OIDC."""
    email = "medico.office365@clinica-exemplo.com.br"
    nome = "Dr. Médico Microsoft 365"
    sub_id = payload.id_token or "ms_sub_89237482"

    usuario = AuthService.get_or_create_sso_user(
        db=db,
        provider=payload.provider or "microsoft",
        sso_id=sub_id,
        email=email,
        nome=nome
    )

    vinculo_padrao = db.query(VinculoClinica).filter(VinculoClinica.usuario_id == usuario.id).first()
    token = create_access_token(usuario, vinculo_padrao)
    user_out = AuthService.get_usuario_out(db, usuario, vinculo_padrao.estabelecimento_id if vinculo_padrao else None)

    AuditService.registrar_evento(
        db=db,
        acao="LOGIN_SSO_MICROSOFT",
        recurso_tipo="Usuario",
        recurso_id=str(usuario.id),
        usuario_id=usuario.id,
        estabelecimento_id=vinculo_padrao.estabelecimento_id if vinculo_padrao else None,
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent")
    )
    return TokenResponse(access_token=token, usuario=user_out)


# ------------------------------------------------------------------
# Multi-Tenancy: Alternância de Clínica Ativa
# ------------------------------------------------------------------
@router.post("/switch-clinic", response_model=TokenResponse)
def switch_clinic(
    payload: SwitchClinicRequest,
    request: Request,
    auth_data: Tuple[Usuario, Optional[int]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permite ao médico alternar sua clínica ativa e emite um novo JWT com as permissões daquela unidade.
    """
    usuario, _ = auth_data
    vinculo = db.query(VinculoClinica).filter(
        VinculoClinica.usuario_id == usuario.id,
        VinculoClinica.estabelecimento_id == payload.estabelecimento_id
    ).first()

    if not vinculo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não possui vínculo cadastrado com este estabelecimento."
        )

    novo_token = create_access_token(usuario, vinculo)
    user_out = AuthService.get_usuario_out(db, usuario, payload.estabelecimento_id)

    AuditService.registrar_evento(
        db=db,
        acao="ALTERNANCIA_CLINICA_ATIVA",
        recurso_tipo="Estabelecimento",
        recurso_id=str(payload.estabelecimento_id),
        usuario_id=usuario.id,
        estabelecimento_id=payload.estabelecimento_id,
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent")
    )
    return TokenResponse(access_token=novo_token, usuario=user_out)


@router.get("/me", response_model=UsuarioOut)
def get_me(auth_data: Tuple[Usuario, Optional[int]] = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna dados do perfil autenticado e suas clínicas cadastradas."""
    usuario, clinica_id = auth_data
    return AuthService.get_usuario_out(db, usuario, clinica_id)


# ------------------------------------------------------------------
# Trilha de Auditoria (LGPD / CFM)
# ------------------------------------------------------------------
@router.get("/audit-trail", response_model=List[AuditTrailOut])
def listar_trilha_auditoria(
    limit: int = 50,
    auth_data: Tuple[Usuario, Optional[int]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna os eventos recentes da trilha de auditoria criptográfica."""
    return db.query(AuditTrail).order_by(AuditTrail.id.desc()).limit(limit).all()
