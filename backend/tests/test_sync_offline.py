# Arquivo: backend/tests/test_sync_offline.py
"""
Testes para sincronização offline, resolução de conflitos e integridade criptográfica.

Este módulo valida os requisitos C5 do projeto MedIA:
1. Sincronização da fila outbox sem perda de dados.
2. Resolução correta de conflito de prontuário modificado concorrentemente.
3. Validação de integridade criptográfica do lote sincronizado.

Os testes são isolados e utilizam um banco SQLite em memória, seguindo as diretrizes
de arquitetura (sem SUS, sem IoT, apenas atendimento particular/convênios).
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pytest
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

# -----------------------------------------------------------------------------
# Modelos de exemplo (simulam a estrutura real do backend)
# -----------------------------------------------------------------------------
Base = declarative_base()

class OutboxItem(Base):
    """Item da fila outbox para sincronização offline."""
    __tablename__ = "outbox_items"

    id = Column(Integer, primary_key=True, index=True)
    payload = Column(String, nullable=False)  # JSON serializado
    status = Column(String, default="pending")  # pending, processed, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)

class MedicalRecord(Base):
    """Prontuário médico (simplificado)."""
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, nullable=False)
    content = Column(String, nullable=False)  # Conteúdo do prontuário
    version = Column(Integer, default=1)      # Controle de versão para conflitos
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SyncBatch(Base):
    """Lote de sincronização com hash criptográfico."""
    __tablename__ = "sync_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_hash = Column(String, nullable=False)  # SHA-256 do payload
    payload = Column(String, nullable=False)     # JSON com dados sincronizados
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# -----------------------------------------------------------------------------
# Serviços simulados (para testes)
# -----------------------------------------------------------------------------
class SyncService:
    """Serviço de sincronização offline (simulado)."""

    def __init__(self, session: Session):
        self.session = session

    def process_outbox(self) -> int:
        """
        Processa todos os itens pendentes da fila outbox.
        Retorna o número de itens processados com sucesso.
        """
        pending_items = self.session.query(OutboxItem).filter(
            OutboxItem.status.in_(["pending", "failed"])
        ).all()

        processed = 0
        for item in pending_items:
            try:
                # Simula processamento (ex: envio para servidor)
                # Se falhar, marca como 'failed' para retry posterior
                if self._process_item(item):
                    item.status = "processed"
                    item.processed_at = datetime.now(timezone.utc)
                    processed += 1
                else:
                    item.status = "failed"
            except Exception:
                item.status = "failed"
        self.session.commit()
        return processed

    def _process_item(self, item: OutboxItem) -> bool:
        """Processa um item individual. Retorna True se sucesso."""
        # Simulação: sempre sucesso, mas pode ser sobrescrito em testes
        return True

    def resolve_conflict(self, record_id: int, new_content: str, new_version: int) -> MedicalRecord:
        """
        Resolve conflito de prontuário modificado concorrentemente.
        Estratégia: last-write-wins baseado em versão (maior versão vence).
        """
        record = self.session.query(MedicalRecord).filter(
            MedicalRecord.id == record_id
        ).one()

        if new_version > record.version:
            record.content = new_content
            record.version = new_version
            record.updated_at = datetime.now(timezone.utc)
            self.session.commit()
        # Se versão menor, mantém o atual (não faz nada)
        return record

    def compute_batch_hash(self, payload: Dict[str, Any]) -> str:
        """Calcula o hash SHA-256 do payload JSON serializado."""
        serialized = json.dumps(payload, sort_keys=True, default=str).encode()
        return hashlib.sha256(serialized).hexdigest()

    def sync_batch(self, payload: Dict[str, Any]) -> SyncBatch:
        """
        Sincroniza um lote de dados, verificando a integridade criptográfica.
        Cria um registro SyncBatch com o hash calculado.
        """
        batch_hash = self.compute_batch_hash(payload)
        batch = SyncBatch(
            batch_hash=batch_hash,
            payload=json.dumps(payload, default=str)
        )
        self.session.add(batch)
        self.session.commit()
        return batch

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def db_session():
    """Cria um banco SQLite em memória e retorna uma sessão."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    yield session
    session.close()

@pytest.fixture
def sync_service(db_session):
    """Retorna uma instância do SyncService com a sessão de teste."""
    return SyncService(db_session)

# -----------------------------------------------------------------------------
# Testes
# -----------------------------------------------------------------------------
class TestOutboxSync:
    """Testes para sincronização da fila outbox sem perda de dados."""

    def test_all_pending_items_processed(self, db_session, sync_service):
        """Verifica que todos os itens pendentes são processados."""
        # Cria 10 itens pendentes
        for i in range(10):
            item = OutboxItem(payload=json.dumps({"data": f"item_{i}"}))
            db_session.add(item)
        db_session.commit()

        processed = sync_service.process_outbox()
        assert processed == 10

        # Verifica que não há itens pendentes ou falhos
        remaining = db_session.query(OutboxItem).filter(
            OutboxItem.status != "processed"
        ).count()
        assert remaining == 0

    def test_no_data_loss_on_failure(self, db_session, sync_service, monkeypatch):
        """Verifica que itens que falham são marcados e não perdidos."""
        # Cria 5 itens, um deles falhará
        for i in range(5):
            item = OutboxItem(payload=json.dumps({"data": f"item_{i}"}))
            db_session.add(item)
        db_session.commit()

        # Simula falha no processamento do item com payload "item_2"
        def fake_process(item):
            if "item_2" in item.payload:
                return False
            return True
        monkeypatch.setattr(sync_service, "_process_item", fake_process)

        processed = sync_service.process_outbox()
        assert processed == 4  # 4 sucessos, 1 falha

        # Verifica que o item falho está marcado como 'failed' e não foi perdido
        failed_items = db_session.query(OutboxItem).filter(
            OutboxItem.status == "failed"
        ).all()
        assert len(failed_items) == 1
        assert "item_2" in failed_items[0].payload

        # Após retry, o item deve ser processado
        # Simula que agora o processamento funciona
        monkeypatch.setattr(sync_service, "_process_item", lambda item: True)
        processed_retry = sync_service.process_outbox()
        assert processed_retry == 1
        assert db_session.query(OutboxItem).filter(
            OutboxItem.status == "failed"
        ).count() == 0

class TestConflictResolution:
    """Testes para resolução de conflito de prontuário modificado concorrentemente."""

    def test_last_write_wins(self, db_session, sync_service):
        """Verifica que a versão mais recente vence."""
        # Cria um prontuário inicial
        record = MedicalRecord(
            patient_id="P001",
            content="Versão original",
            version=1
        )
        db_session.add(record)
        db_session.commit()

        # Simula duas modificações concorrentes
        # Modificação A (versão 2)
        sync_service.resolve_conflict(record.id, "Conteúdo A", 2)
        # Modificação B (versão 3) - chega depois, deve vencer
        sync_service.resolve_conflict(record.id, "Conteúdo B", 3)

        # Verifica que o conteúdo final é o da versão mais alta
        updated_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == record.id
        ).one()
        assert updated_record.content == "Conteúdo B"
        assert updated_record.version == 3

    def test_older_version_ignored(self, db_session, sync_service):
        """Verifica que uma versão mais antiga não sobrescreve a atual."""
        record = MedicalRecord(
            patient_id="P002",
            content="Versão 2",
            version=2
        )
        db_session.add(record)
        db_session.commit()

        # Tenta aplicar uma versão mais antiga (versão 1)
        sync_service.resolve_conflict(record.id, "Versão 1", 1)

        # O conteúdo deve permanecer o da versão 2
        updated_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == record.id
        ).one()
        assert updated_record.content == "Versão 2"
        assert updated_record.version == 2

class TestCryptographicIntegrity:
    """Testes para validação de integridade criptográfica do lote sincronizado."""

    def test_batch_hash_matches_payload(self, db_session, sync_service):
        """Verifica que o hash calculado corresponde ao payload."""
        payload = {
            "records": [
                {"id": 1, "content": "Prontuário 1"},
                {"id": 2, "content": "Prontuário 2"}
            ],
            "timestamp": "2025-03-24T10:00:00Z"
        }
        batch = sync_service.sync_batch(payload)

        # Recalcula o hash e compara
        expected_hash = sync_service.compute_batch_hash(payload)
        assert batch.batch_hash == expected_hash

    def test_tampered_payload_detected(self, db_session, sync_service):
        """Verifica que um payload adulterado gera hash diferente."""
        payload = {"data": "original"}
        batch = sync_service.sync_batch(payload)

        # Simula adulteração do payload (ex: alteração no banco)
        batch.payload = json.dumps({"data": "tampered"})
        db_session.commit()

        # O hash armazenado não corresponde mais ao payload
        stored_hash = batch.batch_hash
        recalculated_hash = sync_service.compute_batch_hash(
            json.loads(batch.payload)
        )
        assert stored_hash != recalculated_hash

    def test_batch_integrity_verification(self, db_session, sync_service):
        """Verifica que a integridade do lote pode ser validada."""
        payload = {"items": [1, 2, 3]}
        batch = sync_service.sync_batch(payload)

        # Validação: recalcula o hash e compara
        stored_payload = json.loads(batch.payload)
        assert sync_service.compute_batch_hash(stored_payload) == batch.batch_hash

        # Se o payload for alterado, a validação falha
        stored_payload["items"].append(4)
        assert sync_service.compute_batch_hash(stored_payload) != batch.batch_hash
