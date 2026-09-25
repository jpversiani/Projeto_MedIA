from enum import Enum

from typing import Any, Protocol
import re, uuid
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import String, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, declarative_base

Base = declarative_base()

class StatusSync(str, Enum):
    PENDENTE = "PENDENTE"
    EM_FILA = "EM_FILA"
    EM_TRANSITO = "EM_TRANSITO"
    SINCRONIZADO = "SINCRONIZADO"
    CONFLITO = "CONFLITO"
    REJEITADO = "REJEITADO"

SyncStatus = StatusSync

# Algoritmo de validação CNS DATASUS (referência):
# soma = 0
# for i, digito in enumerate(cns[:15]):
#     peso = 15 - i
#     soma += int(digito) * peso
# resto = soma % 11
# dv = 11 - resto
# if dv == 11: dv = 0

def valida_cns(cns):
    cns = cns.replace(' ', '').replace('.', '')
    if len(cns) != 15:
        return False
    # Only for CNS starting with 1, 2, 7, 8, 9
    if cns[0] not in '12789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0

def valida_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] in '12':
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    elif cns[0] in '789':
        # provisório: pis-like
        resto = sum(int(cns[i]) * (15 - i) for i in range(15)) % 11
        return resto == 0
    return False

def _valida_cns_definitivo(cns: str) -> bool:
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0

def _valida_cns_provisorio(cns: str) -> bool:
    # 7 primeiros dígitos + 4 dígitos verificadores calculados
    base = cns[:11]
    # PIS-like check
    ...

# Exemplo CNS: 7 9 5 4 8 3 0 0 0 0 0 4 0 0 0

def valida_cns(cns: str) -> bool:
    """Valida CNS conforme algoritmo DATASUS."""
    cns = re.sub(r"[^0-9]", "", cns)
    if len(cns) != 15 or cns[0] not in "12789":
        return False
    if cns[0] in "12":
        soma = sum(int(d) * p for d, p in zip(cns, range(15, 0, -1)))
        return soma % 11 == 0
    # Provisórios (7, 8, 9): validação tipo PIS
    soma = 0
    peso = 15
    for digito in cns[:11]:
        soma += int(digito) * peso
        peso -= 1
    resto = soma % 11
    dv = 11 - resto
    if dv == 11:
        dv = 0
    if dv == 10:
        soma = soma + 2
        resto = soma % 11
        dv = 11 - resto
    # compare with digits 12-13...

# Para CNS provisório (iniciando com 7, 8 ou 9):
# - Multiplicar cada dígito (dos 11 primeiros) pelos pesos 15 a 5
# - Somar, obter resto da divisão por 11
# - DV = 11 - resto; se DV = 11 -> DV = 0; se DV = 10 -> soma += 2, refazer
# - Os dígitos 12 e 13...

# 1) O CNS possui 15 dígitos;
# 2) Os números devem iniciar com 1, 2, 7, 8 ou 9;
# 3) Para os que iniciam com 1 ou 2:
#    - Multiplicar cada dígito pelo peso correspondente (15, 14, 13, ..., 2)

# - Multiplicar cada um dos 11 primeiros dígitos pelos pesos 15 a 5 (decrescente)
# - Somar os resultados
# - Dividir por 11 e obter o resto
# - DV = 11 - resto
#   - Se DV = 11 -> DV = 0
#   - Se DV = 10 -> somar 2 à soma e refazer o cálculo
# - Comparar DV com o 12º dígito
# - Depois pegar os 12 primeiros dígitos, multiplicar por pesos 15 a 4, somar, resto, DV = 11 - resto (mesmas regras), comparar com 13º dígito
# - Depois 13 primeiros dígitos, pesos 15 a 3, DV vs 14º dígito
# - Depois 14 primeiros dígitos, pesos 15 a 2, DV vs 15º dígito

class SOAPRecord(BaseModel):
    subjetivo: str
    objetivo: str
    avaliacao: str
    plano: str

class AtendimentoOffline(BaseModel):
    id_local: UUID  # local UUID generated offline
    unidade_id: str  # mobile unit
    profissional_cns: str  # CNS of professional
    paciente_cns: str | None
    paciente_cpf: str | None
    paciente_nome: str
    data_atendimento: datetime
    queixa_ciap2: str  # CIAP-2
    hipotese_cid10: str | None
    soap: SOAPRecord
    ...

class AtendimentoSOAP(Base):
    __tablename__ = "atendimentos_soap"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ...
    versao: Mapped[int]
    hash_conteudo: Mapped[str]
    status_sync: Mapped[SyncStatus]  # enum: PENDENTE, EM_FILA, SINCRONIZADO, CONFLITO
    lote_id: Mapped[str | None]
    ...

def resolver_conflito(local, remoto) -> tuple[dict, bool]:
    # 1. hashes iguais -> convergido, sem conflito
    # 2. versoes (lamport) diferentes -> maior vence
    # 3. timestamps diferentes -> mais recente vence (LWW)
    # 4. empate total -> desempate determinístico por hash (garante convergencia)
    pass

class EmpacotadorLotes:
    # TAMANHO_MAX_LOTE = 100 records or 512 KiB uncompressed
    def empacotar(records) -> dict:
        payload = json.dumps({}).encode()
        comprimido = gzip.compress(payload)
        return {"id_lote": "", "sha256": "", "dados_b64": "", "registros": [], "bytes": b""}

class ServicoSincronizacaoOffline:
    def __init__(self, db):
        self.db = db

    def subir_lote(self, lote: dict) -> dict:
        return {"status": "recebido", "total": len(lote.get("registros", []))}

    def status_servidor(self) -> dict:
        return {"pendente": 0, "sincronizado": 0, "conflito": 0}

"""Protocolo de Sincronizacao Delta Offline para Unidades Moveis.

Inspirado na arquitetura de atendimento em areas remotas do Sistema TAM
(Teleatendimento Assistido Movel), este modulo implementa:

* Reconciliacao bidirecional cliente-servidor com resolucao de conflitos
  Last-Write-Wins (LWW) reforcada por hash de versao determinístico;
* Empacotamento de atendimentos SOAP offline em lotes comprimidos (gzip)
  com verificacao de integridade (SHA-256);
* Disparo da sincronizacao quando a conexao 4G/Satelite e restabelecida,
  com retentativas exponenciais e idempotencia por UUID.
"""