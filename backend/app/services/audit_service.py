"""
Serviço de Trilha de Auditoria Imutável (LGPD Art. 11 & Resolução CFM 2.314/2022).
Garante registro inviolável de acesso a prontuários, teleconsultas e prescrições.
"""
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from app.models.usuario import AuditTrail


def calcular_hash_auditoria(
    usuario_id: Optional[int],
    estabelecimento_id: Optional[int],
    acao: str,
    recurso_tipo: str,
    recurso_id: str,
    timestamp: datetime,
    hash_anterior: Optional[str]
) -> str:
    """Gera hash criptográfico SHA-256 canônico encadeado."""
    raw = (
        f"{usuario_id}:{estabelecimento_id}:{acao}:{recurso_tipo}:{recurso_id}:"
        f"{timestamp.isoformat()}:{hash_anterior or 'GENESIS'}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


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
        """
        Registra uma ação clínica ou administrativa de forma imutável com prova criptográfica.
        """
        ultimo = db.query(AuditTrail).order_by(AuditTrail.id.desc()).first()
        hash_anterior = ultimo.hash_integridade if ultimo else None
        
        agora = datetime.now(timezone.utc)
        hash_atual = calcular_hash_auditoria(
            usuario_id=usuario_id,
            estabelecimento_id=estabelecimento_id,
            acao=acao,
            recurso_tipo=recurso_tipo,
            recurso_id=recurso_id,
            timestamp=agora,
            hash_anterior=hash_anterior
        )

        registro = AuditTrail(
            usuario_id=usuario_id,
            estabelecimento_id=estabelecimento_id,
            acao=acao,
            recurso_tipo=recurso_tipo,
            recurso_id=str(recurso_id),
            ip_address=ip_address,
            user_agent=user_agent,
            detalhes_json=json.dumps(detalhes, ensure_ascii=False, default=str) if detalhes else None,
            timestamp=agora,
            hash_anterior=hash_anterior,
            hash_integridade=hash_atual
        )
        db.add(registro)
        db.commit()
        db.refresh(registro)
        return registro
