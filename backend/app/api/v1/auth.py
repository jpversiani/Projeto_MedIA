"""
Rotas de Autenticação, SSO (Google e Microsoft), Multi-Tenancy e Auditoria de Acesso.
"""
import os
from typing import List, Optional, Tuple
from fastapi import (
    APIRouter,
    Body,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.usuario import Usuario, VinculoClinica, PapelUsuarioEnum, AuditTrail
from app.models.estabelecimento import Estabelecimento
from app.models.profissional import Profissional
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    SSOLoginRequest,
    TokenResponse,
    UsuarioOut,
    SwitchClinicRequest,
    MfaSetupResponse,
    MfaVerifyRequest,
    AuditTrailOut,
)
from app.services.auth_service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    AuthService,
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_token,
    generate_totp_secret,
    revogar_refresh_token,
    revogar_sessoes_do_usuario,
    validar_refresh_token,
    verify_totp_token,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["Autenticação & SSO (Google/Microsoft)"])

# Nomes dos cookies de sessão. O refresh token fica em cookie HttpOnly: o
# JavaScript da página nunca o lê, então um XSS não consegue exfiltrá-lo.
COOKIE_REFRESH = "media_refresh"
COOKIE_ACESSO = "media_access"


def _cookie_seguro() -> bool:
    """Cookies só viajam em HTTPS em produção."""
    return bool(getattr(settings, "is_production", False))


def _gravar_cookies_sessao(response, access_token: str, refresh_token: Optional[str]) -> None:
    response.set_cookie(
        key=COOKIE_ACESSO,
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=_cookie_seguro(),
        path="/",
    )
    if refresh_token:
        response.set_cookie(
            key=COOKIE_REFRESH,
            value=refresh_token,
            max_age=60 * 60 * 24 * 7,
            httponly=True,
            samesite="lax",
            secure=_cookie_seguro(),
            path="/api/v1/auth",
        )


def _limpar_cookies_sessao(response) -> None:
    response.delete_cookie(COOKIE_ACESSO, path="/")
    response.delete_cookie(COOKIE_REFRESH, path="/api/v1/auth")


# ------------------------------------------------------------------
# Dependência de Usuário Autenticado (Bearer ou cookie HttpOnly)
# ------------------------------------------------------------------
def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Tuple[Usuario, Optional[int]]:
    token: Optional[str] = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    if not token:
        # Fallback para o cookie HttpOnly: permite que a sessão do navegador
        # funcione sem o token trafegar em `localStorage`.
        token = request.cookies.get(COOKIE_ACESSO)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso ausente ou inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # `decode_access_token` recusa refresh token: sem isso, um token de 7 dias
    # valeria como bearer de acesso e a redução para 15 minutos seria inócua.
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
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Login tradicional por email/senha ou login instantâneo de demonstração para testes de MVP.

    - Login demo: basta enviar ``{"demo_role": "medico_titular"}`` (email é opcional).
    - Login local: ``{"email": "...", "password": "..."}`` (com ``mfa_code`` opcional).
    """
    usuario = None
    
    # Suporte a login rápido de demonstração (Dr. Versiani, Dra. Letícia, Secretária, Admin)
    if payload.demo_role:
        if not settings.DEMO_LOGIN_ENABLED or settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Login de demonstração indisponível neste ambiente.",
            )
        role_map = {
            "medico_titular": ("dra.francelli@media-saude.com.br", "Dra. Francelli Neves Versiani", PapelUsuarioEnum.MEDICO),
            "cardiologista": ("dr.carlos@media-saude.com.br", "Dr. Carlos Mendes", PapelUsuarioEnum.MEDICO),
            "psiquiatra": ("dra.mariana@media-saude.com.br", "Dra. Mariana Silveira", PapelUsuarioEnum.MEDICO),
            "medica_familia": ("dra.leticia@media-saude.com.br", "Dra. Letícia Mendes", PapelUsuarioEnum.MEDICO),
            "secretaria": ("recepcao@media-saude.com.br", "Maria Auxiliadora (Recepção)", PapelUsuarioEnum.RECEPCAO),
            "recepcionista": ("recepcao@media-saude.com.br", "Maria Auxiliadora (Recepção)", PapelUsuarioEnum.RECEPCAO),
            "admin": ("admin@media-saude.com.br", "Carlos Eduardo (Gestor)", PapelUsuarioEnum.ADMIN),
        }
        if payload.demo_role in role_map:
            email, nome, papel = role_map[payload.demo_role]
            usuario = db.query(Usuario).filter(Usuario.email == email).first()
            if not usuario and payload.demo_role == "medico_titular":
                # Migra registro legado em bancos existentes
                usuario = db.query(Usuario).filter(
                    (Usuario.email == "dr.versiani@media-saude.com.br") | (Usuario.nome.like("%João Paulo%"))
                ).first()
                if usuario:
                    usuario.email = email
                    usuario.nome = nome
                    db.commit()
                    db.refresh(usuario)
            if usuario and payload.demo_role == "medico_titular" and usuario.nome != nome:
                usuario.nome = nome
                usuario.email = email
                db.commit()
                db.refresh(usuario)
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

            # Garante os vínculos com as clínicas cadastradas. Isto precisa
            # acontecer também para usuários JÁ existentes: sem isso, um usuário
            # criado antes da primeira clínica receberia `clinica_ativa = null`
            # e o Workspace Switcher do Cockpit ficaria sem clínica ativa.
            ests = db.query(Estabelecimento).order_by(Estabelecimento.id).all()
            for idx, est in enumerate(ests):
                ja_vinculado = db.query(VinculoClinica).filter(
                    VinculoClinica.usuario_id == usuario.id,
                    VinculoClinica.estabelecimento_id == est.id,
                ).first()
                if ja_vinculado:
                    continue
                db.add(VinculoClinica(
                    usuario_id=usuario.id,
                    estabelecimento_id=est.id,
                    papel=papel,
                    is_default=(idx == 0)
                ))
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

    refresh_token, _ = create_refresh_token(
        db,
        usuario,
        vinculo_padrao,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _gravar_cookies_sessao(response, token, refresh_token)

    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
        usuario=user_out,
    )


# ------------------------------------------------------------------
# Renovação e encerramento de sessão
# ------------------------------------------------------------------
@router.post("/refresh", response_model=TokenResponse)
def renovar_sessao(
    request: Request,
    response: Response,
    payload: Optional[RefreshRequest] = Body(default=None),
    db: Session = Depends(get_db),
):
    """Renova o access token (15 min) a partir do refresh token.

    O refresh token é **rotacionado**: o usado nesta chamada é revogado e um
    novo é emitido. Reutilizar um token já rotacionado derruba todas as sessões
    do usuário — comportamento padrão de detecção de roubo.
    """
    token_refresh = (payload.refresh_token if payload else None) or request.cookies.get(COOKIE_REFRESH)
    if not token_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token ausente. Faça login novamente.",
        )

    dados, motivo = validar_refresh_token(db, token_refresh)
    if not dados:
        _limpar_cookies_sessao(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Sessão não renovável ({motivo}). Faça login novamente.",
        )

    usuario = db.query(Usuario).filter(
        Usuario.id == int(dados["sub"]), Usuario.is_active == True
    ).first()
    if not usuario:
        _limpar_cookies_sessao(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo.")

    clinica_id = dados.get("clinica_id")
    vinculo = None
    if clinica_id is not None:
        vinculo = db.query(VinculoClinica).filter(
            VinculoClinica.usuario_id == usuario.id,
            VinculoClinica.estabelecimento_id == clinica_id,
        ).first()
    if vinculo is None:
        vinculo = db.query(VinculoClinica).filter(
            VinculoClinica.usuario_id == usuario.id
        ).order_by(VinculoClinica.is_default.desc()).first()

    novo_access = create_access_token(usuario, vinculo)
    novo_refresh, registro = create_refresh_token(
        db,
        usuario,
        vinculo,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    revogar_refresh_token(db, dados["jti"], substituido_por=registro.jti)

    user_out = AuthService.get_usuario_out(
        db, usuario, vinculo.estabelecimento_id if vinculo else None
    )
    _gravar_cookies_sessao(response, novo_access, novo_refresh)

    return TokenResponse(
        access_token=novo_access,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=novo_refresh,
        usuario=user_out,
    )


@router.post("/logout")
def encerrar_sessao(
    request: Request,
    response: Response,
    payload: Optional[RefreshRequest] = Body(default=None),
    db: Session = Depends(get_db),
):
    """Encerra a sessão: revoga o refresh token e apaga os cookies.

    Não exige access token válido de propósito — uma sessão expirada também
    precisa conseguir se encerrar e limpar o cookie.
    """
    token_refresh = (payload.refresh_token if payload else None) or request.cookies.get(COOKIE_REFRESH)
    if token_refresh:
        dados = decode_token(token_refresh, tipo_esperado="refresh")
        if dados and dados.get("jti"):
            revogar_refresh_token(db, dados["jti"])

    _limpar_cookies_sessao(response)
    return {"detail": "Sessão encerrada."}


@router.post("/logout-all")
def encerrar_todas_as_sessoes(
    response: Response,
    auth_data: Tuple[Usuario, Optional[int]] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoga todas as sessões do usuário (perda de dispositivo / incidente)."""
    usuario, _ = auth_data
    quantidade = revogar_sessoes_do_usuario(db, usuario.id)
    _limpar_cookies_sessao(response)
    return {"detail": "Sessões encerradas.", "revogadas": quantidade}


# ------------------------------------------------------------------
# Endpoints de SSO (Google & Microsoft)
#
# IMPORTANTE: os callbacks abaixo NÃO validam o id_token contra a JWKS do
# provedor. Eles CONFIAM no `id_token` enviado pelo cliente e, a partir dele,
# abrem uma sessão válida. Isso é aceitável apenas como mock de interface
# durante o desenvolvimento e está atrás de `SSO_ENABLED` (por padrão
# DESLIGADO). A validação real do id_token está registrada como pendência
# de integração — ver docs/ROADMAP_V1.md.
# ------------------------------------------------------------------
def _exigir_sso_habilitado() -> None:
    """Impede o uso do mock de SSO fora de desenvolvimento.

    Mesmo com `SSO_ENABLED=true`, o mock não pode responder em produção: ele
    confia no `id_token` do cliente sem verificação criptográfica e abriria
    uma sessão para qualquer pessoa. A validação real contra a JWKS do provedor
    ainda não foi implementada — ver docs/ROADMAP_V1.md.
    """
    if not settings.SSO_ENABLED or settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Login SSO não disponível neste ambiente. "
                "A federação real (Google/Microsoft) ainda exige validação do "
                "id_token contra a JWKS do provedor."
            ),
        )


@router.get("/sso/google/url")
def get_google_auth_url():
    """Gera a URL de redirecionamento para login federado com o Google."""
    _exigir_sso_habilitado()
    client_id = settings.GOOGLE_CLIENT_ID or "mock_media_google_client_id.apps.googleusercontent.com"
    redirect_uri = "http://localhost:8000/api/v1/auth/sso/google/callback"
    scope = "openid%20profile%20email"
    url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&access_type=offline&prompt=consent"
    return {"provider": "google", "auth_url": url}


@router.post("/sso/google/callback", response_model=TokenResponse)
def google_sso_callback(payload: SSOLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Processa o callback ou id_token do Google OIDC."""
    _exigir_sso_habilitado()
    # MOCK CONTROLADO (apenas com SSO_ENABLED=true em ambiente de testes):
    # extração fixa de identidade, sem verificação criptográfica do token.
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
    _exigir_sso_habilitado()
    client_id = settings.MICROSOFT_CLIENT_ID or "mock_media_microsoft_client_id"
    redirect_uri = "http://localhost:8000/api/v1/auth/sso/microsoft/callback"
    scope = "openid%20profile%20email%20User.Read"
    url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={scope}"
    return {"provider": "microsoft", "auth_url": url}


@router.post("/sso/microsoft/callback", response_model=TokenResponse)
def microsoft_sso_callback(payload: SSOLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Processa o callback do Microsoft Entra ID OIDC."""
    _exigir_sso_habilitado()
    # MOCK CONTROLADO (apenas com SSO_ENABLED=true em ambiente de testes).
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
    limit: int = Query(50, ge=1, le=500),
    auth_data: Tuple[Usuario, Optional[int]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna os eventos recentes da trilha de auditoria criptográfica.

    A trilha é filtrada pela clínica ativa do token: sem este filtro qualquer
    usuário autenticado — inclusive uma recepcionista — lia os eventos de todas
    as unidades (vazamento entre tenants). Somente superusuários veem tudo.
    """
    usuario, clinica_id = auth_data

    query = db.query(AuditTrail)
    if not usuario.is_superuser:
        if clinica_id is None:
            # Sem clínica ativa no token, restringe ao próprio usuário.
            query = query.filter(AuditTrail.usuario_id == usuario.id)
        else:
            query = query.filter(AuditTrail.estabelecimento_id == clinica_id)

    return query.order_by(AuditTrail.id.desc()).limit(limit).all()
