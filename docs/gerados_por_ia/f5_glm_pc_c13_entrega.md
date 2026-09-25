Provide implementation of sync_offline.py plus tests. Keep concise but complete.# Protocolo de Sincronização Delta Offline (C13)

## `backend/app/services/sync_offline.py`

```python
"""
Protocolo de Sincronização Delta Offline para Unidades Móveis (C13).

Inspirado na arquitetura de atendimento remoto do Sistema TAM:
- Unidades móveis (barco/veículo) atendem sem conectividade.
- Atendimentos SOAP são empacotados em lotes comprimidos (zlib + base64).
- Reconciliação bidirecional com resolução de conflitos Last-Write-Wins (LWW)
  usando hash de versão determinístico.
- Sincronização dispara quando conexão 4G/Satélite é restabelecida.
"""

from __future__ import annotations

import hashlib
import zlib
import base64
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger("sync_offline")

# ---------------------------------------------------------------------------
# Constantes SUS / APS
# ---------------------------------------------------------------------------

CNS_LENGTH = 15
CPF_LENGTH = 11
MAX_BATCH_BYTES = 512 * 1024  # 512 KiB por lote (limite prático p/ satélite)
COMPRESSION_LEVEL = 9


class MetodosValidos(StrEnum):
    """Métodos de identificação do cidadão (RNDS/e-SUS APS)."""
    CNS = "CNS"
    CPF = "CPF"
    NOME_SOCIAL = "NOME_SOCIAL"  # atendimento sem documento (desconhecido)


class StatusSync(StrEnum):
    PENDENTE = "PENDENTE"
    EM_TRANSITO = "EM_TRANSITO"
    SINCRONIZADO = "SINCRONIZADO"
    CONFLITO = "CONFLITO"
    REJEITADO = "REJEITADO"


# ---------------------------------------------------------------------------
# Modelos Pydantic v2 — domínio clínico
# ---------------------------------------------------------------------------

class IdentificacaoCidadao(BaseModel):
    """Identificação por CNS/CPF conforme padrão SUS."""
    nome: str = Field(min_length=3, max_length=200)
    metodo: MetodosValidos
    valor: str

    @field_validator("valor")
    @classmethod
    def validar_documento(cls, v: str, info) -> str:
        metodo = info.data.get("metodo")
        v = v.replace(".", "").replace("-", "").strip()
        if metodo == MetodosValidos.CNS:
            if len(v) != CNS_LENGTH or not v.isdigit():
                raise ValueError(f"CNS deve ter {CNS_LENGTH} dígitos numéricos")
            if not _cns_valido(v):
                raise ValueError("CNS inválido (dígito verificador)")
        elif metodo == MetodosValidos.CPF:
            if len(v) != CPF_LENGTH or not v.isdigit():
                raise ValueError(f"CPF deve ter {CPF_LENGTH} dígitos numéricos")
            if not _cpf_valido(v):
                raise ValueError("CPF inválido (dígitos verificadores)")
        return v


class SOAPRecord(BaseModel):
    """Registro de atendimento no método SOAP (e-SUS APS / CIAP-2 / CID-10)."""
    id_offline: UUID = Field(default_factory=uuid4)
    id_unidade_movel: str = Field(min_length=1)
    identificacao: IdentificacaoCidadao
    subjetivo: str = ""
    objetivo: str = ""
    avaliacao: str = ""
    plano: str = ""
    ciap2: str = Field(pattern=r"^[A-Z][0-9]{2}$")  # ex.: U15, K29
    cid10: str | None = Field(default=None, pattern=r"^[A-Z][0-9]{2}(\.[0-9]{1,2})?$")
    profissional_cns: str
    data_atendimento: datetime

    @model_validator(mode="after")
    def validar_soap(self) -> "SOAPRecord":
        if not any([self.subjetivo, self.objetivo, self.avaliacao, self.plano]):
            raise ValueError("SOAP exige ao menos um campo (S/O/A/P) preenchido")
        return self

    def hash_version(self) -> str:
        """Hash determinístico SHA-256 do conteúdo clínico (base do LWW)."""
        payload = "|".join([
            str(self.id_offline),
            self.subjetivo, self.objetivo, self.avaliacao, self.plano,
            self.ciap2, self.cid10 or "",
            self.data_atendimento.astimezone(timezone.utc).isoformat(),
        ])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Empacotamento (lote comprimido)
# ---------------------------------------------------------------------------

def empacotar_lote(registros: list[SOAPRecord]) -> str:
    """Comprime registros em lote base64/zlib para transmissão via 4G/Satélite."""
    if not registros:
        raise ValueError("Lote não pode ser vazio")
    import json
    bruto = json.dumps(
        [r.model_dump(mode="json") for r in registros],
        ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")
    comprimido = zlib.compress(bruto, level=COMPRESSION_LEVEL)
    if len(comprimido) > MAX_BATCH_BYTES:
        raise ValueError(f"Lote excede {MAX_BATCH_BYTES} bytes comprimidos")
    return base64.b64encode(comprimido).decode("ascii")


def desempacotar_lote(payload_b64: str) -> list[SOAPRecord]:
    import json
    bruto = zlib.decompress(base64.b64decode(payload_b64))
    return [SOAPRecord.model_validate(d) for d in json.loads(bruto)]


# ---------------------------------------------------------------------------
# Resolução de conflitos — Last-Write-Wins com hash de versão
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class DeltaRecord:
    """Representação sincronizável de um atendimento com metadados de versão."""
    registro: SOAPRecord
    status: StatusSync = StatusSync.PENDENTE
    version_hash: str = ""
    synced_at: datetime | None = None
    motivo_conflito: str | None = None

    def __post_init__(self) -> None:
        if not self.version_hash:
            self.version_hash = self.registro.hash_version()


@dataclass(slots=True)
class SyncReport:
    enviados: int = 0
    recebidos: int = 0
    conflitos_resolvidos: int = 0
    rejeitados: int = 0
    detalhes: list[dict[str, Any]] = field(default_factory=list)


class ConflictResolver:
    """
    Last-Write-Wins (LWW): o registro com `data_atendimento` mais recente prevalece.
    Desempate determinístico: se timestamps idênticos, o maior `version_hash` vence
    (garante convergência em todos os nós sem relógio atômico).
    """

    @staticmethod
    def resolver(local: DeltaRecord, remoto: DeltaRecord) -> tuple[DeltaRecord, bool]:
        """Retorna (vencedor, houve_conflito)."""
        if local.version_hash == remoto.version_hash:
            return local, False  # idênticos, sem conflito

        t_local = local.registro.data_atendimento
        t_remoto = remoto.registro.data_atendimento

        if t_local != t_remoto:
            vencedor = local if t_local > t_remoto else remoto
            vencedor.status = StatusSync.SINCRONIZADO
            vencedor.synced_at = _utcnow()
            perdedor = remoto if vencedor is local else local
            perdedor.status = StatusSync.CONFLITO
            perdedor.motivo_conflito = "superseded_by_lww"
            return vencedor, True

        # Desempate por hash (ordem lexicográfica determinística)
        vencedor = local if local.version_hash > remoto.version_hash else remoto
        vencedor.status = StatusSync.SINCRONIZADO
        vencedor.synced_at = _utcnow()
        return vencedor, True


# ---------------------------------------------------------------------------
# Motor de sincronização (reconciliação bidirecional)
# ---------------------------------------------------------------------------

class DeltaSyncEngine:
    """
    Mantém o delta local da unidade móvel e reconcilia com o servidor central
    quando a conexão é restabelecida.
    """

    def __init__(self, id_unidade_movel: str) -> None:
        if not id_unidade_movel:
            raise ValueError("id_unidade_movel é obrigatório")
        self.id_unidade_movel = id_unidade_movel
        self._pendentes: dict[UUID, DeltaRecord] = {}
        self._sincronizados: dict[UUID, DeltaRecord] = {}

    # -- fila offline -------------------------------------------------------

    def enfileirar(self, registro: SOAPRecord) -> DeltaRecord:
        if registro.id_unidade_movel != self.id_unidade_movel:
            raise ValueError("Registro pertence a outra unidade móvel")
        delta = DeltaRecord(registro=registro)
        self._pendentes[registro.id_offline] = delta
        logger.info("Enfileirado offline: %s", registro.id_offline)
        return delta

    @property
    def pendentes(self) -> list[DeltaRecord]:
        return list(self._pendentes.values())

    @property
    def sincronizados(self) -> list[DeltaRecord]:
        return list(self._sincronizados.values())

    # -- empacotamento / upload ---------------------------------------------

    def criar_lote_upload(self) -> str:
        """Empacota todos os pendentes para transmissão quando houver link."""
        registros = [d.registro for d in self._pendentes.values()]
        payload = empacotar_lote(registros)
        for d in self._pendentes.values():
            d.status = StatusSync.EM_TRANSITO
        return payload

    # -- reconciliação bidirecional ------------------------------------------

    def reconciliar(
        self,
        deltas_remotos: list[DeltaRecord],
    ) -> SyncReport:
        """
        Executa sincronização bidirecional:
        1. Upload: pendentes locais são enviados (já empacotados).
        2. Download/reconciliação: deltas do servidor são comparados via LWW.
        """
        report = SyncReport(recebidos=len(deltas_remotos))
        resolver = ConflictResolver()

        # Upload dos pendentes
        for delta in list(self._pendentes.values()):
            self._sincronizados[delta.registro.id_offline] = delta
            delta.status = StatusSync.SINCRONIZADO
            delta.synced_at = _utcnow()
            del self._pendentes[delta.registro.id_offline]
            report.enviados += 1

        # Reconciliação de downloads contra o estado local
        for remoto in deltas_remotos:
            rid = remoto.registro.id_offline
            local = self._sincronizados.get(rid) or self._pendentes.get(rid)
            if local is None:
                remoto.status = StatusSync.SINCRONIZADO
                remoto.synced_at = _utcnow()
                self._sincronizados[rid] = remoto
                continue

            vencedor, conflito = resolver.resolver(local, remoto)
            if conflito:
                report.conflitos_resolvidos += 1
                report.detalhes.append({
                    "id": str(rid),
                    "vencedor": vencedor.version_hash[:12],
                    "estrategia": "LWW+hash_tiebreak",
                })
                perdedor = remoto if vencedor is local else local
                self._sincronizados[rid] = vencedor
                logger.warning("Conflito LWW resolvido: %s", rid)
            else:
                self._sincronizados[rid] = local

        logger.info(
            "Sincronização unidade %s: enviados=%d recebidos=%d conflitos=%d",
            self.id_unidade_movel, report.enviados, report.recebidos,
            report.conflitos_resolvidos,
        )
        return report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _cns_valido(cns: str) -> bool:
    """Validação do CNS por pesos 15..2 (regra oficial DATASUS)."""
    if cns[0] in "012":
        return False
    soma = sum(int(c) * p for c, p in zip(cns, range(15, 0, -1)))
    return soma % 11 == 0


def _cpf_valido(cpf: str) -> bool:
    if cpf == cpf[0] * CPF_LENGTH:
        return False
    for offset in (10, 11):
        dv = sum(int(d) * w for d, w in zip(cpf[: offset - 1], range(offset, 1, -1)))
        resto = (dv * 10) % 11 % 10
        if resto != int(cpf[offset - 1]):
            return False
    return True
```

## `backend/tests/test_sync_offline.py`

```python
"""Cobertura de testes do protocolo C13 — pytest."""

from datetime import datetime, timezone, timedelta
from uuid import uuid4
import pytest

from app.services.sync_offline import (
    SOAPRecord, IdentificacaoCidadao, DeltaSyncEngine, DeltaRecord,
    ConflictResolver, empacotar_lote, desempacotar_lote, StatusSync,
)

T0 = datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc)

CNS_VALIDO = "700000000001915"  # valida pelo algoritmo DATASUS (peso 15..2)


def _cidadao() -> IdentificacaoCidadao:
    return IdentificacaoCidadao(nome="Maria Silva", metodo="CNS", valor=CNS_VALIDO)


def _soap(quando: datetime = T0, **kw) -> SOAPRecord:
    base = dict(
        id_unidade_movel="TAM-UM-01",
        identificacao=_cidadao(),
        subjetivo="Cefaleia há 2 dias",
        objetivo="PA 130/85, afebril",
        avaliacao="Cefaleia tensional",
        plano="Analgésico, orientações, retorno 7 dias",
        ciap2="N01",
        cid10="R51",
        profissional_cns=CNS_VALIDO,
        data_atendimento=quando,
    )
    base.update(kw)
    return SOAPRecord(**base)


# ------------------------- validação de domínio ---------------------------

class TestValidacao:
    def test_cns_invalido_rejeitado(self):
        with pytest.raises(ValueError, match="CNS"):
            IdentificacaoCidadao(nome="X Y Z", metodo="CNS", valor="123456789012345")

    def test_ciap2_formato(self):
        with pytest.raises(ValueError):
            _soap(ciap2="n1")

    def test_soap_vazio_rejeitado(self):
        with pytest.raises(ValueError, match="SOAP"):
            _soap(subjetivo="", objetivo="", avaliacao="", plano="")

    def test_hash_deterministico(self):
        assert _soap().hash_version() == _soap().hash_version()


# ------------------------- empacotamento ----------------------------------

class TestEmpacotamento:
    def test_roundtrip_lote(self):
        lote = [_soap(), _soap(quando=T0 + timedelta(minutes=5))]
        payload = empacotar_lote(lote)
        assert desempacotar_lote(payload) == lote

    def test_compression_efetiva(self):
        registros = [_soap(quando=T0 + timedelta(minutes=i)) for i in range(50)]
        import json
        bruto = len(json.dumps([r.model_dump(mode="json") for r in registros]))
        assert len(empacotar_lote(registros)) < bruto

    def test_lote_vazio_erro(self):
        with pytest.raises(ValueError):
            empacotar_lote([])


# ------------------------- conflitos LWW ----------------------------------

class TestConflitos:
    def test_lww_timestamp_recente_vence(self):
        antigo = DeltaRecord(_soap(quando=T0))
        novo = DeltaRecord(_soap(quando=T0 + timedelta(hours=1)))
        vencedor, conflito = ConflictResolver.resolver(antigo, novo)
        assert conflito and vencedor is novo
        assert vencedor.status == StatusSync.SINCRONIZADO
        assert antigo.status == StatusSync.CONFLITO

    def test_tiebreak_hash_deterministico(self):
        a = DeltaRecord(_soap(quando=T0))
        b = DeltaRecord(_soap(quando=T0, plano="Plano alterado"))
        v1, c1 = ConflictResolver.resolver(a, b)
        v2, c2 = ConflictResolver.resolver(b, a)
        assert c1 and c2
        assert v1.version_hash == v2.version_hash  # convergência

    def test_identicos_sem_conflito(self):
        a = DeltaRecord(_soap())
        b = DeltaRecord(_soap())
        vencedor, conflito = ConflictResolver.resolver(a, b)
        assert not conflito and vencedor.version_hash == a.version_hash


# ------------------------- engine de sincronização ------------------------

class TestEngine:
    def test_ciclo_completo_offline_para_sync(self):
        engine = DeltaSyncEngine("TAM-UM-01")
        r1 = engine.enfileirar(_soap())
        r2 = engine.enfileirar(_soap(quando=T0 + timedelta(minutes=10)))
        assert len(engine.pendentes) == 2

        payload = engine.criar_lote_upload()
        assert engine.pendentes[0].status == StatusSync.EM_TRANSITO

        # Servidor devolve um registro novo (download) e resolve o upload
        remoto = DeltaRecord(_soap(quando=T0 + timedelta(hours=2)))
        report = engine.reconciliar([remoto])

        assert report.enviados == 2
        assert report.recebidos == 1
        assert len(engine.pendentes) == 0
        ids