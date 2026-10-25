"""
Serviço de Autenticação Central, Single Sign-On (Google & Microsoft), JWT, MFA (TOTP) e Multi-Tenancy.
"""
import os
import time
import hmac
import struct
import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import jwt
from sqlalchemy.orm import Session

from app.models.usuario import Usuario, VinculoClinica, PapelUsuarioEnum
from app.models.estabelecimento import Estabelecimento
from app.schemas.auth import UsuarioOut, VinculoClinicaOut, TokenResponse
from app.core.config import settings

# Resolve a chave via settings. Em produção a ausência de JWT_SECRET_KEY gera
# RuntimeError em tempo de import — falha rápida e explícita, em vez de subir
# com uma chave pública conhecida e permitir forja de tokens.
SECRET_KEY = settings.effective_secret_key
ALGORITHM = "HS256"

# O token de acesso era de 24 horas — tempo demais para um bearer token que não
# pode ser revogado e que o frontend guardava em `localStorage`. Agora ele dura
# 15 minutos e a renovação é feita por refresh token rotativo e revogável.
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


# ------------------------------------------------------------------
# 1. Hashing de Senhas Seguro (PBKDF2-HMAC-SHA256)
# ------------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password or "$" not in hashed_password:
        return False
    salt, expected_hex = hashed_password.split("$", 1)
    key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return hmac.compare_digest(key.hex(), expected_hex)


# ------------------------------------------------------------------
# 2. MFA / TOTP (RFC 6238 - HMAC-SHA1 sem dependência externa)
# ------------------------------------------------------------------
def generate_totp_secret() -> str:
    """Gera um segredo Base32 para TOTP (16 caracteres)."""
    return base64.b32encode(secrets.token_bytes(10)).decode("utf-8").replace("=", "")


def get_totp_token(secret: str, interval: int = 30) -> str:
    """Calcula o token TOTP atual de 6 dígitos."""
    missing_padding = len(secret) % 8
    if missing_padding != 0:
        secret += "=" * (8 - missing_padding)
    key = base64.b32decode(secret, casefold=True)
    counter = int(time.time()) // interval
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1000000
    return f"{code:06d}"


def verify_totp_token(secret: str, token: str, window: int = 1) -> bool:
    """Valida o token com janela de tolerância de 30 segundos antes/depois."""
    missing_padding = len(secret) % 8
    if missing_padding != 0:
        secret += "=" * (8 - missing_padding)
    key = base64.b32decode(secret, casefold=True)
    now_counter = int(time.time()) // 30
    for offset_idx in range(-window, window + 1):
        msg = struct.pack(">Q", now_counter + offset_idx)
        digest = hmac.new(key, msg, hashlib.sha1).digest()
        offset = digest[-1] & 0x0F
        code = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1000000
        if f"{code:06d}" == str(token).strip():
            return True
    return False


# ------------------------------------------------------------------
# 3. Emissão e Validação de Tokens JWT com Claims de Tenancy
# ------------------------------------------------------------------
def create_access_token(usuario: Usuario, clinica_ativa: Optional[VinculoClinica] = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(usuario.id),
        "email": usuario.email,
        "nome": usuario.nome,
        "is_superuser": usuario.is_superuser,
        "clinica_id": clinica_ativa.estabelecimento_id if clinica_ativa else None,
        "papel": clinica_ativa.papel.value if clinica_ativa else "VISITANTE",
        "profissional_id": clinica_ativa.profissional_id if clinica_ativa else None,
        "tipo": "access",
        "jti": secrets.token_urlsafe(16),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    db: Session,
    usuario: Usuario,
    clinica_ativa: Optional[VinculoClinica] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[str, "RefreshToken"]:
    """Emite um refresh token de 7 dias e registra o ``jti`` para poder revogá-lo.

    O token é opaco para o frontend: tudo o que importa (validade, revogação,
    clínica) é verificado no banco a cada renovação.
    """
    from app.models.usuario import RefreshToken

    now = datetime.now(timezone.utc)
    expira_em = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = secrets.token_urlsafe(32)

    payload = {
        "sub": str(usuario.id),
        "clinica_id": clinica_ativa.estabelecimento_id if clinica_ativa else None,
        "tipo": "refresh",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expira_em.timestamp()),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    registro = RefreshToken(
        jti=jti,
        usuario_id=usuario.id,
        estabelecimento_id=payload["clinica_id"],
        expires_at=expira_em,
        ip_address=ip_address,
        user_agent=(user_agent or "")[:300] or None,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return token, registro


def decode_token(token: str, tipo_esperado: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Decodifica e valida o token, conferindo o ``tipo`` (access/refresh).

    Sem essa checagem, um refresh token válido por 7 dias poderia ser usado como
    bearer token de acesso, anulando a redução para 15 minutos.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None
    if tipo_esperado and payload.get("tipo", "access") != tipo_esperado:
        return None
    return payload


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    return decode_token(token, tipo_esperado="access")


def revogar_refresh_token(db: Session, jti: str, substituido_por: Optional[str] = None) -> bool:
    """Marca o refresh token como revogado. Devolve ``False`` se já não existia."""
    from app.models.usuario import RefreshToken

    registro = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if not registro:
        return False
    if registro.revoked_at is None:
        registro.revoked_at = datetime.now(timezone.utc)
    if substituido_por:
        registro.substituido_por = substituido_por
    db.commit()
    return True


def revogar_sessoes_do_usuario(db: Session, usuario_id: int) -> int:
    """Revoga todas as sessões ativas de um usuário (logout global / incidente)."""
    from app.models.usuario import RefreshToken

    agora = datetime.now(timezone.utc)
    quantidade = (
        db.query(RefreshToken)
        .filter(RefreshToken.usuario_id == usuario_id, RefreshToken.revoked_at.is_(None))
        .update({RefreshToken.revoked_at: agora}, synchronize_session=False)
    )
    db.commit()
    return quantidade


def validar_refresh_token(db: Session, token: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Valida o refresh token contra o banco. Devolve ``(payload, motivo_da_falha)``."""
    from app.models.usuario import RefreshToken

    payload = decode_token(token, tipo_esperado="refresh")
    if not payload or "jti" not in payload:
        return None, "token_invalido"

    registro = db.query(RefreshToken).filter(RefreshToken.jti == payload["jti"]).first()
    if not registro:
        return None, "token_desconhecido"
    if registro.revoked_at is not None:
        # Reutilização de token rotacionado é sinal clássico de roubo: revoga
        # toda a família de sessões do usuário.
        revogar_sessoes_do_usuario(db, registro.usuario_id)
        return None, "token_revogado"
    if registro.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return None, "token_expirado"

    return payload, ""


# ------------------------------------------------------------------
# 4. Serviço de Autenticação e Multi-Tenancy
# ------------------------------------------------------------------
class AuthService:
    @staticmethod
    def get_or_create_sso_user(
        db: Session,
        provider: str,
        sso_id: str,
        email: str,
        nome: str,
        foto_url: Optional[str] = None
    ) -> Usuario:
        """
        Provisiona ou sincroniza um usuário via SSO Google ou Microsoft.
        """
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if not user:
            user = Usuario(
                email=email,
                nome=nome,
                sso_provider=provider,
                sso_id=sso_id,
                foto_url=foto_url,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Auto-vincular à clínica default se existir
            est = db.query(Estabelecimento).first()
            if est:
                vinculo = VinculoClinica(
                    usuario_id=user.id,
                    estabelecimento_id=est.id,
                    papel=PapelUsuarioEnum.MEDICO,
                    is_default=True
                )
                db.add(vinculo)
                db.commit()
        else:
            # Atualiza metadata do SSO
            user.sso_provider = provider
            user.sso_id = sso_id
            if foto_url:
                user.foto_url = foto_url
            db.commit()
            db.refresh(user)
            
        return user

    @staticmethod
    def get_usuario_out(db: Session, usuario: Usuario, clinica_ativa_id: Optional[int] = None) -> UsuarioOut:
        """Monta o schema completo do usuário com seus vínculos a clínicas."""
        vinculos = db.query(VinculoClinica).filter(VinculoClinica.usuario_id == usuario.id).all()
        
        vinculos_out = []
        clinica_ativa_out = None
        
        # Mapeamento de CRM/RQE para perfis médicos de demonstração
        crm_demo = None
        rqe_demo = None
        user_email_lower = (usuario.email or "").lower()
        user_nome_lower = (usuario.nome or "").lower()
        if "francelli" in user_email_lower or "francelli" in user_nome_lower:
            crm_demo = "78421-MG"
            rqe_demo = "39412"
        elif "carlos" in user_email_lower or "carlos" in user_nome_lower:
            crm_demo = "65123-MG"
        elif "mariana" in user_email_lower or "mariana" in user_nome_lower:
            crm_demo = "81902-MG"
        elif "leticia" in user_email_lower or "leticia" in user_nome_lower:
            crm_demo = "54321-MG"

        for v in vinculos:
            est = db.query(Estabelecimento).filter(Estabelecimento.id == v.estabelecimento_id).first()
            
            vout = VinculoClinicaOut(
                id=v.id,
                estabelecimento_id=v.estabelecimento_id,
                estabelecimento_nome=est.nome_fantasia if est else "Clínica Geral",
                cnes=est.cnes if est else "0000000",
                papel=v.papel.value,
                profissional_id=v.profissional_id,
                crm=crm_demo if v.papel == PapelUsuarioEnum.MEDICO else None,
                rqe=rqe_demo if v.papel == PapelUsuarioEnum.MEDICO else None,
                is_default=v.is_default
            )
            vinculos_out.append(vout)
            
            if clinica_ativa_id and v.estabelecimento_id == clinica_ativa_id:
                clinica_ativa_out = vout
            elif not clinica_ativa_id and v.is_default:
                clinica_ativa_out = vout

        if not clinica_ativa_out and vinculos_out:
            clinica_ativa_out = vinculos_out[0]

        return UsuarioOut(
            id=usuario.id,
            email=usuario.email,
            nome=usuario.nome,
            sso_provider=usuario.sso_provider,
            foto_url=usuario.foto_url,
            is_active=usuario.is_active,
            is_superuser=usuario.is_superuser,
            mfa_enabled=usuario.mfa_enabled,
            clinica_ativa=clinica_ativa_out,
            vinculos=vinculos_out
        )
