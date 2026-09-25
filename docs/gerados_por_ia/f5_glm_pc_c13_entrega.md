```python
# backend/app/services/sync_offline.py
"""
Protocolo de Sincronização Delta Offline para Unidades Móveis.

Implementa reconciliação bidirecional com resolução de conflitos Last-Write-Wins,
empacotamento de atendimentos SOAP offline em lotes comprimidos e sincronização
quando a conexão 4G/Satélite restabelecer.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

# Assumindo que os modelos existem em backend/app/models
from app.models import Atendimento, SyncState  # type: ignore

# Configuração de sessão - será injetada via factory
SessionLocal = sessionmaker()


class SyncPayload(BaseModel):
    """Estrutura de um lote de sincronização."""
    device_id: str
    last_sync_at: Optional[datetime] = None
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    # Cada change: {"id": int, "soap_data": dict, "updated_at": datetime, "version_hash": str, "deleted": bool}


class SyncResponse(BaseModel):
    """Resposta do servidor com mudanças a aplicar localmente."""
    server_time: datetime
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    # Mesma estrutura de change


class SyncOfflineService:
    """
    Serviço de sincronização offline.

    Utiliza Last-Write-Wins (LWW) com hash de versão para resolução de conflitos.
    """

    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    @staticmethod
    def generate_version_hash(data: Dict[str, Any]) -> str:
        """Gera um hash SHA256 do conteúdo para controle de versão."""
        canonical = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    @staticmethod
    def pack_batch(changes: List[Dict[str, Any]]) -> bytes:
        """Serializa e comprime (gzip) uma lista de mudanças."""
        payload = json.dumps(changes, default=str).encode("utf-8")
        return gzip.compress(payload)

    @staticmethod
    def unpack_batch(payload: bytes) -> List[Dict[str, Any]]:
        """Descomprime e desserializa um lote de mudanças."""
        decompressed = gzip.decompress(payload)
        return json.loads(decompressed.decode("utf-8"))

    @staticmethod
    def resolve_conflict(
        local: Dict[str, Any], remote: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve conflito usando Last-Write-Wins.

        Critérios:
        1. Maior `updated_at` vence.
        2. Se timestamps iguais, maior `version_hash` vence.
        """
        local_ts = local.get("updated_at")
        remote_ts = remote.get("updated_at")

        if local_ts is None:
            return remote
        if remote_ts is None:
            return local

        # Converte para datetime se necessário
        if isinstance(local_ts, str):
            local_ts = datetime.fromisoformat(local_ts)
        if isinstance(remote_ts, str):
            remote_ts = datetime.fromisoformat(remote_ts)

        if local_ts > remote_ts:
            return local
        if remote_ts > local_ts:
            return remote

        # Timestamps iguais: compara hash
        local_hash = local.get("version_hash", "")
        remote_hash = remote.get("version_hash", "")
        return local if local_hash >= remote_hash else remote

    # ------------------------------------------------------------------
    # Operações principais
    # ------------------------------------------------------------------
    def get_pending_changes(self, session: Session, device_id: str) -> List[Dict[str, Any]]:
        """
        Obtém todos os atendimentos locais que ainda não foram sincronizados
        (sync_status = 'pending') ou que foram alterados após a última sincronização.
        """
        # Busca o último sync state para este dispositivo
        sync_state = session.execute(
            select(SyncState).where(SyncState.device_id == device_id)
        ).scalar_one_or_none()

        last_sync_at = sync_state.last_sync_at if sync_state else None

        query = select(Atendimento).where(
            (Atendimento.sync_status == "pending") |
            (Atendimento.updated_at > last_sync_at) if last_sync_at else (Atendimento.sync_status == "pending")
        )
        # Nota: a lógica acima é simplificada; em produção seria mais robusta.

        atendimentos = session.execute(query).scalars().all()

        changes = []
        for at in atendimentos:
            change = {
                "id": at.id,
                "soap_data": at.soap_data,
                "updated_at": at.updated_at,
                "version_hash": at.version_hash,
                "deleted": at.deleted,
            }
            changes.append(change)
        return changes

    def apply_remote_changes(
        self, session: Session, changes: List[Dict[str, Any]]
    ) -> None:
        """
        Aplica mudanças recebidas do servidor, resolvendo conflitos com LWW.
        """
        for change in changes:
            at_id = change["id"]
            # Busca o registro local
            local = session.execute(
                select(Atendimento).where(Atendimento.id == at_id)
            ).scalar_one_or_none()

            if local is None:
                # Novo registro vindo do servidor
                new_at = Atendimento(
                    id=at_id,
                    soap_data=change["soap_data"],
                    updated_at=change["updated_at"],
                    version_hash=change["version_hash"],
                    deleted=change.get("deleted", False),
                    sync_status="synced",
                )
                session.add(new_at)
            else:
                # Conflito potencial
                local_change = {
                    "id": local.id,
                    "soap_data": local.soap_data,
                    "updated_at": local.updated_at,
                    "version_hash": local.version_hash,
                    "deleted": local.deleted,
                }
                resolved = self.resolve_conflict(local_change, change)

                # Atualiza apenas se o remoto venceu
                if resolved is change:
                    local.soap_data = change["soap_data"]
                    local.updated_at = change["updated_at"]
                    local.version_hash = change["version_hash"]
                    local.deleted = change.get("deleted", False)
                # Se o local venceu, mantém e marca como pendente para enviar novamente
                else:
                    local.sync_status = "pending"

        session.commit()

    def sync(self, device_id: str) -> SyncResponse:
        """
        Executa a sincronização completa:
        1. Coleta mudanças locais pendentes.
        2. Envia para o servidor (simulado aqui).
        3. Recebe mudanças remotas.
        4. Aplica mudanças remotas localmente.
        5. Atualiza o estado de sincronização.
        """
        with self.session_factory() as session:
            # 1. Coleta mudanças locais
            local_changes = self.get_pending_changes(session, device_id)

            # 2. Simula envio para o servidor e recebe resposta
            # Em produção, isso seria uma chamada HTTP para o endpoint de sync.
            # Aqui simulamos uma resposta com as mudanças que o servidor tem.
            # Para fins de teste, assumimos que o servidor retorna as mudanças
            # que ele tem e que não estão no nosso dispositivo.
            # Vamos simular um servidor que retorna uma lista vazia ou algumas mudanças.
            # Na prática, o servidor processaria o lote e retornaria as mudanças conflitantes.

            # Simulação: servidor responde com as mudanças que ele tem (exemplo)
            # Para um teste real, isso seria substituído por uma chamada HTTP.
            # Vamos assumir que o servidor retorna uma lista de mudanças que ele
            # considera mais recentes que as nossas.
            # Para simplificar, vamos retornar uma lista vazia.
            remote_changes: List[Dict[str, Any]] = []

            # 3. Aplica mudanças remotas
            self.apply_remote_changes(session, remote_changes)

            # 4. Marca as mudanças locais como sincronizadas
            if local_changes:
                ids = [c["id"] for c in local_changes]
                session.execute(
                    update(Atendimento)
                    .where(Atendimento.id.in_(ids))
                    .values(sync_status="synced")
                )

            # 5. Atualiza o estado de sincronização
            sync_state = session.execute(
                select(SyncState).where(SyncState.device_id == device_id)
            ).scalar_one_or_none()
            now = datetime.now(timezone.utc)
            if sync_state:
                sync_state.last_sync_at = now
            else:
                session.add(SyncState(device_id=device_id, last_sync_at=now))

            session.commit()

            return SyncResponse(server_time=now, changes=remote_changes)

    def pack_pending_batch(self, device_id: str) -> bytes:
        """
        Empacota as mudanças pendentes em um lote comprimido para envio.
        """
        with self.session_factory() as session:
            changes = self.get_pending_changes(session, device_id)
            return self.pack_batch(changes)

    def unpack_and_apply(self, payload: bytes) -> None:
        """
        Desempacota um lote recebido e aplica as mudanças.
        """
        changes = self.unpack_batch(payload)
        with self.session_factory() as session:
            self.apply_remote_changes(session, changes)
```

E os testes:

```python
# backend/tests/test_sync_offline.py
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Atendimento, SyncState
from app.services.sync_offline import SyncOfflineService

# Configuração de banco de testes
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_pack_unpack_batch():
    service = SyncOfflineService(TestingSessionLocal)
    changes = [
        {"id": 1, "soap_data": {"a": 1}, "updated_at": "2025-01-01T00:00:00", "version_hash": "abc"},
        {"id": 2, "soap_data": {"b": 2}, "updated_at": "2025-01-02T00:00:00", "version_hash": "def"},
    ]
    packed = service.pack_batch(changes)
    assert isinstance(packed, bytes)
    unpacked = service.unpack_batch(packed)
    assert unpacked == changes

def test_resolve_conflict_lww():
    service = SyncOfflineService(TestingSessionLocal)
    local = {
        "id": 1,
        "soap_data": {"v": "local"},
        "updated_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "version_hash": "aaa",
    }
    remote = {
        "id": 1,
        "soap_data": {"v": "remote"},
        "updated_at": datetime(2025, 1, 2, tzinfo=timezone.utc),
        "version_hash": "bbb",
    }
    resolved = service.resolve_conflict(local, remote)
    assert resolved == remote

def test_resolve_conflict_tie_hash():
    service = SyncOfflineService(TestingSessionLocal)
    local = {
        "id": 1,
        "soap_data": {"v": "local"},
        "updated_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "version_hash": "bbb",
    }
    remote = {
        "id": 1,
        "soap_data": {"v": "remote"},
        "updated_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "version_hash": "aaa",
    }
    resolved = service.resolve_conflict(local, remote)
    assert resolved == local  # maior hash vence

def test_sync_flow():
    service = SyncOfflineService(TestingSessionLocal)

    # Cria um atendimento local pendente
    with TestingSessionLocal() as session:
        at = Atendimento(
            id=1,
            soap_data={"queixa": "dor"},
            updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            version_hash=service.generate_version_hash({"queixa": "dor"}),
            sync_status="pending",
            deleted=False,
        )
        session.add(at)
        session.commit()

    # Executa sincronização
    response = service.sync("device-001")
    assert response.server_time is not None

    # Verifica que o atendimento foi marcado como sincronizado
    with TestingSessionLocal() as session:
        at = session.get(Atendimento, 1)
        assert at.sync_status == "synced"

        # Verifica que o SyncState foi criado
        state = session.execute(
            select(SyncState).where(SyncState.device_id == "device-001")
        ).scalar_one()
        assert state.last_sync_at is not None

def test_apply_remote_changes_conflict():
    service = SyncOfflineService(TestingSessionLocal)

    # Cria um atendimento local com timestamp antigo
    with TestingSessionLocal() as session:
        at = Atendimento(
            id=1,
            soap_data={"v": "local"},
            updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            version_hash="aaa",
            sync_status="synced",
            deleted=False,
        )
        session.add(at)
        session.commit()

    # Recebe uma mudança remota mais recente
    remote_change = {
        "id": 1,
        "soap_data": {"v": "remote"},
        "updated_at": datetime(2025, 1, 2, tzinfo=timezone.utc),
        "version_hash": "bbb",
        "deleted": False,
    }

    with TestingSessionLocal() as session:
        service.apply_remote_changes(session, [remote_change])

    with Testing