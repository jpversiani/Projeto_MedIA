"""
Serviço de Trilha de Auditoria Imutável (LGPD Art. 11 & Resolução CFM 2.314/2022).

Garante registro inviolável de acesso a prontuários, teleconsultas e prescrições.

Correções aplicadas nesta versão:

* O hash encadeado passou a cobrir **IP, User-Agent e detalhes** do evento. Antes
  o digest era calculado só com usuário/estabelecimento/ação/recurso/timestamp,
  então ``ip_address``, ``user_agent`` e ``detalhes_json`` podiam ser alterados
  no banco sem quebrar a cadeia — a "prova criptográfica" não provava nada sobre
  esses campos.
* A leitura do último elo usa ``FOR UPDATE`` (quando o banco suporta) para
  evitar que duas requisições simultâneas escrevam com o mesmo ``hash_anterior``
  e quebrem a corrente.
* ``verificar_cadeia()`` recomputa a corrente inteira e devolve o primeiro elo
  inconsistente — sem isso não havia como auditar a auditoria.

Compatibilidade: o digest só incorpora os campos extras quando eles existem, e
a verificação aceita tanto o formato canônico (estável no banco) quanto o
formato legado (``datetime.isoformat()``), de modo que eventos antigos
continuam verificáveis.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.usuario import AuditTrail


def _detalhes_canonico(detalhes: Optional[Dict[str, Any]]) -> Optional[str]:
    """Serializa os detalhes de forma determinística (chaves ordenadas)."""
    if not detalhes:
        return None
    return json.dumps(detalhes, ensure_ascii=False, sort_keys=True, default=str)


def _timestamp_canonico(valor: datetime) -> str:
    """Timestamp em formato estável após round-trip no banco.

    O SQLite devolve ``datetime`` sem timezone, e ``isoformat()`` de um valor
    com/sem ``tzinfo`` gera strings diferentes. Normalizar em UTC com formato
    fixo mantém o hash reprodutível na verificação.
    """
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")


def calcular_hash_auditoria(
    usuario_id: Optional[int],
    estabelecimento_id: Optional[int],
    acao: str,
    recurso_tipo: str,
    recurso_id: str,
    timestamp: datetime,
    hash_anterior: Optional[str],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    detalhes_json: Optional[str] = None,
    formato: str = "canonico",
) -> str:
    """Gera hash SHA-256 canônico encadeado do evento de auditoria.

    ``formato="legado"`` reproduz o digest antigo (sem IP/UA/detalhes e com
    ``isoformat()``), usado apenas para verificar eventos gravados antes desta
    correção.
    """
    if formato == "legado":
        raw = (
            f"{usuario_id}:{estabelecimento_id}:{acao}:{recurso_tipo}:{recurso_id}:"
            f"{timestamp.isoformat()}:{hash_anterior or 'GENESIS'}"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    partes = [
        str(usuario_id),
        str(estabelecimento_id),
        acao,
        recurso_tipo,
        str(recurso_id),
        _timestamp_canonico(timestamp),
        hash_anterior or "GENESIS",
    ]
    extras = []
    if ip_address:
        extras.append(f"ip={ip_address}")
    if user_agent:
        extras.append(f"ua={user_agent}")
    if detalhes_json:
        extras.append(f"det={detalhes_json}")
    if extras:
        partes.append("|".join(extras))
    return hashlib.sha256(":".join(partes).encode("utf-8")).hexdigest()


class AuditService:
    @staticmethod
    def registrar_evento(
        db: Session,
        acao: str,
        recurso_tipo: str,
        recurso_id: str,
        usuario_id: Optional[int] = None,
        estabelecimento_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        detalhes: Optional[Dict[str, Any]] = None
    ) -> AuditTrail:
        """Registra uma ação clínica ou administrativa de forma imutável."""
        # `FOR UPDATE` serializa a leitura do último elo em bancos que suportam
        # (PostgreSQL). SQLite ignora a cláusula — ali a escrita é serializada
        # pelo próprio arquivo.
        ultimo = (
            db.query(AuditTrail)
            .order_by(AuditTrail.id.desc())
            .with_for_update()
            .first()
        )
        hash_anterior = ultimo.hash_integridade if ultimo else None

        detalhes_json = _detalhes_canonico(detalhes)
        agora = datetime.now(timezone.utc)
        hash_atual = calcular_hash_auditoria(
            usuario_id=usuario_id,
            estabelecimento_id=estabelecimento_id,
            acao=acao,
            recurso_tipo=recurso_tipo,
            recurso_id=recurso_id,
            timestamp=agora,
            hash_anterior=hash_anterior,
            ip_address=ip_address,
            user_agent=user_agent,
            detalhes_json=detalhes_json,
        )

        registro = AuditTrail(
            usuario_id=usuario_id,
            estabelecimento_id=estabelecimento_id,
            acao=acao,
            recurso_tipo=recurso_tipo,
            recurso_id=str(recurso_id),
            ip_address=ip_address,
            user_agent=user_agent,
            detalhes_json=detalhes_json,
            timestamp=agora,
            hash_anterior=hash_anterior,
            hash_integridade=hash_atual
        )
        db.add(registro)
        db.commit()
        db.refresh(registro)
        return registro

    @staticmethod
    def verificar_cadeia(db: Session) -> Tuple[bool, Optional[int]]:
        """Recomputa a corrente inteira e devolve ``(ok, primeiro_id_invalido)``.

        Um elo é inválido quando (a) o ``hash_anterior`` não é o hash do elo
        precedente ou (b) o ``hash_integridade`` não corresponde ao conteúdo
        gravado — o que denuncia alteração posterior no banco.
        """
        anterior: Optional[str] = None
        for registro in db.query(AuditTrail).order_by(AuditTrail.id.asc()).all():
            if registro.hash_anterior != anterior:
                return False, registro.id

            esperados = {
                calcular_hash_auditoria(
                    usuario_id=registro.usuario_id,
                    estabelecimento_id=registro.estabelecimento_id,
                    acao=registro.acao,
                    recurso_tipo=registro.recurso_tipo,
                    recurso_id=registro.recurso_id,
                    timestamp=registro.timestamp,
                    hash_anterior=registro.hash_anterior,
                    ip_address=registro.ip_address,
                    user_agent=registro.user_agent,
                    detalhes_json=registro.detalhes_json,
                    formato="canonico",
                ),
                calcular_hash_auditoria(
                    usuario_id=registro.usuario_id,
                    estabelecimento_id=registro.estabelecimento_id,
                    acao=registro.acao,
                    recurso_tipo=registro.recurso_tipo,
                    recurso_id=registro.recurso_id,
                    timestamp=registro.timestamp,
                    hash_anterior=registro.hash_anterior,
                    formato="legado",
                ),
            }
            if registro.hash_integridade not in esperados:
                return False, registro.id
            anterior = registro.hash_integridade
        return True, None


def auditar_acesso_phi(
    db: Session,
    *,
    contexto,
    request,
    acao: str,
    recurso_tipo: str,
    recurso_id,
    detalhes: Optional[Dict[str, Any]] = None,
) -> Optional[AuditTrail]:
    """Registra acesso a dado clínico (PHI) a partir do contexto da requisição.

    Centraliza a coleta de IP/User-Agent para que toda leitura sensível seja
    auditada do mesmo jeito. Não levanta exceção: falha de auditoria não pode
    derrubar o atendimento do paciente (mas é registrada no log da aplicação).
    """
    if contexto is None:
        # Autenticação desligada (desenvolvimento): não há usuário a auditar.
        return None

    import logging

    logger = logging.getLogger("media.auditoria")
    try:
        ip = None
        user_agent = None
        if request is not None:
            ip = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent") if request.headers else None

        return AuditService.registrar_evento(
            db=db,
            acao=acao,
            recurso_tipo=recurso_tipo,
            recurso_id=str(recurso_id),
            usuario_id=getattr(contexto.usuario, "id", None),
            estabelecimento_id=contexto.estabelecimento_id,
            ip_address=ip,
            user_agent=user_agent,
            detalhes=detalhes,
        )
    except Exception as erro:  # pragma: no cover - depende do banco
        logger.error("Falha ao registrar auditoria de %s %s: %s", acao, recurso_tipo, erro)
        return None
