```python
# backend/app/services/sync_offline.py
"""
Protocolo de Sincronização Delta Offline para Unidades Móveis.

Implementa reconciliação bidirecional com resolução de conflitos
Last-Write-Wins (LWW) baseada em hash de versão, empacotamento de
atendimentos SOAP offline em lotes comprimidos e sincronização
automática quando a conectividade é restabelecida.

Inspirado na arquitetura de atendimento remoto do Sistema TAM,
adaptado para o contexto MedIA (atendimento particular e convênios).
"""

from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, TypeVar

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

# ----------------------------------------------------------------------
# Tipos genéricos e modelos auxiliares
# ----------------------------------------------------------------------

T = TypeVar("T", bound="SyncableMixin")


class SyncableMixin:
    """
    Mixin para modelos que participam da sincronização offline.

    Espera-se que o modelo possua os seguintes campos:
        - id: chave primária (int ou UUID)
        - updated_at: datetime (UTC) da última modificação
        - version_hash: string hash calculado a partir do conteúdo
        - deleted: bool (soft delete)
    """

    id: Any
    updated_at: datetime
    version_hash: str
    deleted: bool = False

    def compute_version_hash(self) -> str:
        """
        Calcula um hash SHA-256 baseado no conteúdo serializado do objeto.
        Deve ser sobrescrito em subclasses para incluir todos os campos relevantes.
        """
        raise NotImplementedError


class SyncState(BaseModel):
    """
    Estado de sincronização para um dispositivo móvel.
    Armazena o último timestamp de sincronização e o último hash de versão.
    """

    device_id: str
    last_sync_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_version_hash: str = ""


class SyncBatch(BaseModel):
    """
    Lote de mudanças a serem enviadas ou recebidas.
    """

    device_id: str
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ----------------------------------------------------------------------
# Serviço de sincronização
# ----------------------------------------------------------------------

class SyncOfflineService:
    """
    Serviço responsável pela sincronização delta offline.

    Utiliza a estratégia Last-Write-Wins (LWW) com hash de versão.
    O hash é calculado a partir do conteúdo do registro e do timestamp.
    O registro com timestamp mais recente vence; em caso de empate,
    o hash maior vence (ordem lexicográfica).
    """

    def __init__(
        self,
        session_factory: sessionmaker,
        model_class: Type[SyncableMixin],
        device_id: str,
    ):
        """
        Inicializa o serviço.

        Args:
            session_factory: fábrica de sessões SQLAlchemy.
            model_class: classe do modelo sincronizável (ex: Atendimento).
            device_id: identificador único do dispositivo móvel.
        """
        self.session_factory = session_factory
        self.model_class = model_class
        self.device_id = device_id

    # ------------------------------------------------------------------
    # Métodos públicos
    # ------------------------------------------------------------------

    def sync(self) -> Dict[str, Any]:
        """
        Executa o ciclo completo de sincronização:
        1. Puxa mudanças do servidor (pull).
        2. Envia mudanças locais (push).
        3. Atualiza o estado de sincronização.

        Returns:
            Dicionário com estatísticas da sincronização.
        """
        with self.session_factory() as session:
            # 1. Pull: obter mudanças do servidor desde o último sync
            server_changes = self._pull_changes(session)

            # 2. Push: enviar mudanças locais para o servidor
            local_changes = self._get_local_changes(session)
            push_result = self._push_changes(session, local_changes)

            # 3. Atualizar estado de sincronização
            self._update_sync_state(session, server_changes, local_changes)

            return {
                "pulled": len(server_changes),
                "pushed": len(local_changes),
                "conflicts_resolved": push_result.get("conflicts", 0),
            }

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _pull_changes(self, session: Session) -> List[Dict[str, Any]]:
        """
        Obtém mudanças do servidor desde o último sync.

        Em uma implementação real, isso consultaria uma API remota.
        Aqui, simulamos consultando registros com updated_at > last_sync.
        """
        state = self._get_sync_state(session)
        last_sync = state.last_sync_at if state else datetime.min.replace(tzinfo=timezone.utc)

        stmt = select(self.model_class).where(
            self.model_class.updated_at > last_sync
        )
        result = session.execute(stmt).scalars().all()

        # Serializa os registros para o formato de transferência
        changes = [self._serialize_record(record) for record in result]
        return changes

    def _get_local_changes(self, session: Session) -> List[Dict[str, Any]]:
        """
        Obtém mudanças locais que ainda não foram sincronizadas.
        Em uma implementação real, isso viria de uma fila local.
        Aqui, assumimos que todos os registros com updated_at > last_sync
        são locais (simplificação).
        """
        state = self._get_sync_state(session)
        last_sync = state.last_sync_at if state else datetime.min.replace(tzinfo=timezone.utc)

        stmt = select(self.model_class).where(
            self.model_class.updated_at > last_sync
        )
        result = session.execute(stmt).scalars().all()
        return [self._serialize_record(record) for record in result]

    def _push_changes(
        self, session: Session, local_changes: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Envia mudanças locais para o servidor e resolve conflitos.

        Em uma implementação real, isso enviaria para uma API.
        Aqui, aplicamos as mudanças diretamente no banco (simulação).
        """
        conflicts = 0
        for change in local_changes:
            # Verifica se o registro já existe no servidor
            record_id = change["id"]
            stmt = select(self.model_class).where(self.model_class.id == record_id)
            existing = session.execute(stmt).scalar_one_or_none()

            if existing is None:
                # Novo registro: insere
                self._apply_change(session, change)
            else:
                # Conflito potencial: resolve com LWW
                if self._resolve_conflict(existing, change):
                    self._apply_change(session, change)
                else:
                    conflicts += 1

        session.commit()
        return {"conflicts": conflicts}

    def _resolve_conflict(
        self, existing: SyncableMixin, incoming: Dict[str, Any]
    ) -> bool:
        """
        Resolve conflito usando Last-Write-Wins com hash de versão.

        Regra:
        - Se o timestamp do incoming é maior que o do existing, incoming vence.
        - Se timestamps iguais, o hash maior vence (ordem lexicográfica).
        - Caso contrário, existing vence (não aplica mudança).

        Returns:
            True se o incoming deve ser aplicado, False caso contrário.
        """
        incoming_ts = incoming["updated_at"]
        existing_ts = existing.updated_at

        if incoming_ts > existing_ts:
            return True
        elif incoming_ts == existing_ts:
            return incoming["version_hash"] > existing.version_hash
        return False

    def _apply_change(self, session: Session, change: Dict[str, Any]) -> None:
        """
        Aplica uma mudança (inserção ou atualização) no banco.
        """
        record_id = change["id"]
        stmt = select(self.model_class).where(self.model_class.id == record_id)
        record = session.execute(stmt).scalar_one_or_none()

        if record is None:
            # Novo registro
            record = self.model_class(**change)
            session.add(record)
        else:
            # Atualização
            for key, value in change.items():
                setattr(record, key, value)

    def _serialize_record(self, record: SyncableMixin) -> Dict[str, Any]:
        """
        Serializa um registro para o formato de transferência.
        """
        return {
            "id": record.id,
            "updated_at": record.updated_at.isoformat(),
            "version_hash": record.version_hash,
            "deleted": record.deleted,
            # Incluir outros campos conforme necessário
            # Aqui, assumimos que o modelo tem um método to_dict()
            **record.to_dict(),
        }

    def _get_sync_state(self, session: Session) -> Optional[SyncState]:
        """
        Obtém o estado de sincronização para o dispositivo.
        Em uma implementação real, isso viria de uma tabela dedicada.
        Aqui, usamos um dicionário em memória (simulação).
        """
        # Simulação: retorna um estado fixo
        return SyncState(device_id=self.device_id, last_sync_at=datetime.min.replace(tzinfo=timezone.utc))

    def _update_sync_state(
        self,
        session: Session,
        server_changes: List[Dict[str, Any]],
        local_changes: List[Dict[str, Any]],
    ) -> None:
        """
        Atualiza o estado de sincronização após o ciclo.
        Em uma implementação real, persistiria o estado.
        """
        # Simulação: não faz nada
        pass

    # ------------------------------------------------------------------
    # Empacotamento e compressão
    # ------------------------------------------------------------------

    @staticmethod
    def compress_batch(batch: SyncBatch) -> bytes:
        """
        Comprime um lote de mudanças usando gzip.

        Args:
            batch: objeto SyncBatch.

        Returns:
            Bytes comprimidos.
        """
        data = batch.model_dump_json().encode("utf-8")
        return gzip.compress(data)

    @staticmethod
    def decompress_batch(compressed: bytes) -> SyncBatch:
        """
        Descomprime um lote de mudanças.

        Args:
            compressed: bytes comprimidos.

        Returns:
            Objeto SyncBatch.
        """
        data = gzip.decompress(compressed).decode("utf-8")
        return SyncBatch.model_validate_json(data)

    @staticmethod
    def compute_version_hash(content: Dict[str, Any], timestamp: datetime) -> str:
        """
        Calcula um hash SHA-256 a partir do conteúdo e do timestamp.

        Args:
            content: dicionário com os dados do registro.
            timestamp: timestamp da modificação.

        Returns:
            String hash hexadecimal.
        """
        # Serializa de forma canônica (ordenando chaves)
        canonical = json.dumps(content, sort_keys=True, default=str)
        payload = f"{canonical}|{timestamp.isoformat()}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
```