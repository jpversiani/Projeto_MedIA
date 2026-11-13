"""Convite assinado do paciente para entrar na teleconsulta sem conta (Fase 2).

O paciente não tem usuário no sistema: o link que ele recebe é a própria
credencial. Este módulo emite um JWT curto (``tipo=convite_teleconsulta``, papel
PACIENTE) amarrado a UMA sala, persiste o ``jti`` em ``convites_teleconsulta``
para revogação e valida o convite contra o banco a cada uso.

Reusa a chave/algoritmo e o ``decode_token`` do ``auth_service`` (mesma confiança
do access token), mas com ``tipo`` próprio — um convite nunca vale como access
token de usuário, e um access token nunca vale como convite (o ``decode_token``
checa o ``tipo``).

Camadas de defesa na validação:
1. assinatura + ``exp`` do JWT (``decode_token``);
2. ``tipo`` correto (convite, não access/refresh);
3. escopo de sala (convite da sala A não entra na sala B);
4. ``jti`` conhecido, não revogado e não expirado no banco.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from sqlalchemy.orm import Session

from app.models.telemedicina import ConviteTeleconsulta
from app.services.auth_service import ALGORITHM, SECRET_KEY, decode_token

# Validade padrão do convite. O link é enviado perto do horário da consulta;
# 24 h cobre a janela de remarcação/queda de conexão sem deixar o link eterno.
CONVITE_EXPIRE_HORAS = 24
TIPO_CONVITE = "convite_teleconsulta"


def gerar_convite_paciente(
    db: Session,
    teleconsulta_id: int,
    codigo_sala: str,
    nome_paciente: str = "Paciente",
    cidadao_id: Optional[int] = None,
    ttl_horas: int = CONVITE_EXPIRE_HORAS,
) -> str:
    """Emite o convite assinado e persiste o ``jti`` para poder revogá-lo.

    ``sub`` é o id do cidadão quando conhecido (rastreabilidade), senão o id da
    teleconsulta. O papel é sempre PACIENTE: o convite nunca concede acesso de
    médico nem a outra sala.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=ttl_horas)
    jti = secrets.token_urlsafe(32)

    payload = {
        "sub": str(cidadao_id if cidadao_id is not None else teleconsulta_id),
        "nome": nome_paciente or "Paciente",
        "papel": "PACIENTE",
        "sala": codigo_sala,
        "teleconsulta_id": teleconsulta_id,
        "tipo": TIPO_CONVITE,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    registro = ConviteTeleconsulta(
        jti=jti,
        teleconsulta_id=teleconsulta_id,
        codigo_sala=codigo_sala,
        expires_at=expire,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return token


def validar_convite(
    db: Session, token: str, codigo_sala: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Valida o convite contra o banco. Devolve o payload, ou ``None``.

    ``codigo_sala`` (quando informado) amarra o convite à sala: um convite válido
    para outra sala é recusado, impedindo que o link de um paciente abra a
    teleconsulta de outro.
    """
    payload = decode_token(token, tipo_esperado=TIPO_CONVITE)
    if not payload or "jti" not in payload:
        return None

    if codigo_sala is not None and payload.get("sala") != codigo_sala:
        return None

    registro = (
        db.query(ConviteTeleconsulta)
        .filter(ConviteTeleconsulta.jti == payload["jti"])
        .first()
    )
    if not registro:
        return None
    if registro.revoked_at is not None:
        return None

    expiracao = registro.expires_at
    if expiracao.tzinfo is None:
        expiracao = expiracao.replace(tzinfo=timezone.utc)
    if expiracao < datetime.now(timezone.utc):
        return None

    return payload


def revogar_convites_da_teleconsulta(db: Session, teleconsulta_id: int) -> int:
    """Revoga todos os convites vigentes da teleconsulta (fim/cancelamento).

    Depois disto, o link do paciente deixa de funcionar mesmo que o JWT ainda
    não tenha expirado — é o que impede reutilização da sala encerrada.
    """
    agora = datetime.now(timezone.utc)
    quantidade = (
        db.query(ConviteTeleconsulta)
        .filter(
            ConviteTeleconsulta.teleconsulta_id == teleconsulta_id,
            ConviteTeleconsulta.revoked_at.is_(None),
        )
        .update({ConviteTeleconsulta.revoked_at: agora}, synchronize_session=False)
    )
    db.commit()
    return quantidade


def expiracao_sala(data_inicio: Optional[datetime], horas: int = CONVITE_EXPIRE_HORAS) -> datetime:
    """Validade da sala virtual: início da consulta + janela de graça (24 h).

    Sem data de início, conta a partir de agora. O WebSocket já recusa sala
    expirada (``_validar_sala``); preencher ``data_expiracao`` na criação é o
    que faz o link do paciente ter vida limitada em vez de eterna.
    """
    base = data_inicio or datetime.now(timezone.utc)
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    return base + timedelta(hours=horas)