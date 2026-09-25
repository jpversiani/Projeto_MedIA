The user wants me to create a Python file `backend/app/services/sync_offline.py` implementing an offline delta synchronization protocol for mobile units, inspired by the TAM System architecture (Sistema de Atendimento Móvel - likely referring to telehealth/mobile health units in Brazil).

Key requirements:
1. Bidirectional reconciliation protocol with conflict resolution (Last-Write-Wins with version hash)
2. Packaging of offline SOAP-format care records (atendimentos) into compressed batches
3. Synchronization when 4G/Satellite connection is re-established
4. Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
5. SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
6. Test coverage with pytest

Let me design this carefully:

**Architecture Overview:**

The sync protocol needs:
1. **Delta tracking**: Track changes since last sync (version vectors / timestamps + hashes)
2. **Conflict resolution**: Last-Write-Wins (LWW) with version hash comparison
3. **Batch packaging**: Compress SOAP records into batches (gzip + maybe msgpack/json)
4. **Reconnection handling**: Queue management, retry with backoff
5. **SUS compliance**: CNS/CPF validation, CIAP-2 codes, CID-10 codes, SOAP structure

**Data Model (SQLAlchemy 2.0):**

- `AtendimentoSOAP` (SOAP care record): id, patient identifiers (CNS/CPF), SOAP sections (S, O, A, P), CIAP-2 code, CID-10 code, timestamps, sync metadata (version, hash, sync_status, device_id, etc.)

**Pydantic Models:**

- `SOAPRecord` - the SOAP note structure
- `DeltaEnvelope` - what gets sent/received
- `SyncBatch` - compressed batch
- `ConflictResolution` - conflict info
- `SyncResult` / `SyncReport`

**Core Components:**

1. `VersionHash` - compute content hash for LWW
2. `OfflineQueue` / `SyncJournal` - local tracking of pending changes
3. `BatchCompressor` - gzip compression of batches
4. `ConflictResolver` - LWW with hash verification
5. `SyncProtocol` / `DeltaSyncService` - orchestrator

Let me think about the LWW with version hash:
- Each record has `updated_at` timestamp and `content_hash` (SHA-256 of canonical content)
- When merging: if local hash == remote hash → no conflict, already synced
- If timestamps differ → newer timestamp wins (LWW)
- If timestamps equal but hashes differ → tiebreaker (e.g., device_id lexicographic, or deterministic hash comparison) to ensure convergence
- Track `sync_version` (monotonic counter or Lamport clock)

For delta sync:
- Client sends: list of local changes since `last_sync_cursor` + current cursor
- Server responds: server changes since client's cursor + ack of client changes
- Client applies server changes with conflict resolution
- New cursor = server's current watermark

**SOAP structure (método SOAP):**
- S = Subjetivo (patient's subjective report)
- O = Objetivo (objective findings: vital signs, exam)
- A = Avaliação (assessment - diagnosis, CIAP-2/CID-10)
- P = Plano (plan - prescriptions, referrals, follow-up)

**CIAP-2**: 3-character alphanumeric codes (letter + 2 digits), e.g., "R05" for cough
**CID-10**: letter + 2 digits + optional dot + 1-2 digits, e.g., "J06.9"
**CNS**: Cartão Nacional de Saúde - 15 digits, validatable with SISREG algorithm
**CPF**: 11 digits with check digits

Let me write validators for CNS and CPF since SUS compliance is required.

CNS validation algorithm (definitivo/provisório):
- CNS must be 15 digits
- Starting with 1, 2, 7, 8, 9
- Algorithm: sum of digits with weights 15 down to 2, mod 11, check digit = 11 - resto; if resto == 1, check digit is 'P' or 'Q'... Actually the standard algorithm:

For CNS starting with 1, 2 (definitivos) or 7, 8, 9 (provisórios):
```
soma = 0
for i, digito in enumerate(cns[:15]):
    peso = 15 - i
    soma += int(digito) * peso
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0
```
Hmm, actually the standard algorithm is different. Let me recall the official one:

The official CNS validation (from DATASUS):
```
def valida_cns(cns):
    cns = cns.replace(' ', '').replace('.', '')
    if len(cns) != 15:
        return False
    # Only for CNS starting with 1, 2, 7, 8, 9
    if cns[0] not in '12789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```
Yes, that's the correct algorithm: weighted sum with weights 15,14,...,1 must be divisible by 11. This works for the "definitive" format. For provisórios (7,8,9) there's a different checksum with the format 7XX XXXX XXXX XXXX where the last 4 digits are check digits computed differently, but the mod-11 weighted sum works for 1/2 and also there's an algorithm for 7/8/9:

Actually the full official algorithm:
- For CNS starting with 1 or 2: sum(i * peso) % 11 == 0
- For CNS starting with 7, 8, 9: different validation (the last 4 digits are derived)

The commonly used implementation:
```python
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
```

Hmm, actually for 7/8/9 the algorithm is: take first 11 digits as if PIS, compute check digits. Let me just implement the standard one used widely:

```python
def _valida_cns_definitivo(cns: str) -> bool:
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0

def _valida_cns_provisorio(cns: str) -> bool:
    # 7 primeiros dígitos + 4 dígitos verificadores calculados
    base = cns[:11]
    # PIS-like check
    ...
```

The official DATASUS algorithm for provisório:
```
7 9 5 4 8 3 0 0 0 0 0 4 0 0 0  -> example
```
The provisório CNS: first 11 digits follow PIS/PASEP check digit calculation, then 3 more digits + 1 check digit.

Full algorithm from DATASUS documentation:
1. If starts with 1 or 2: use weighted sum mod 11 == 0
2. If starts with 7, 8, or 9:
   - Fill with zeros to 15 digits
   - Compute: soma = sum(digito * peso) where pesos = 15..2 for first 14 digits... 

Actually, let me use the well-known implementation:

```python
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
```

Hmm, this is getting complicated. The official provisório algorithm:

```
Para CNS provisório (iniciando com 7, 8 ou 9):
- Multiplicar cada dígito (dos 11 primeiros) pelos pesos 15 a 5
- Somar, obter resto da divisão por 11
- DV = 11 - resto; se DV = 11 → DV = 0; se DV = 10 → soma += 2, refazer
- Os dígitos 12 e 13... 
```

Actually the official one (from DATASUS "Validação do CNS"):

```
1) O CNS possui 15 dígitos;
2) Os números devem iniciar com 1, 2, 7, 8 ou 9;
3) Para os que iniciam com 1 ou 2: 
   - Multiplicar cada dígito pelo peso correspondente (15, 14, 13, ..., 2 - o primeiro dígito da esquerda é multiplicado por 15, o segundo por 14, e assim por diante até o último dígito que é multiplicado por 1... wait no.
```

Hmm, the standard: pesos de 15 até 1? Let me check: 15 digits, weights 15,14,...,1. Sum must be divisible by 11. Yes that's the classic algorithm.

For 7, 8, 9 (provisório):
```
- Multiplicar cada um dos 11 primeiros dígitos pelos pesos 15 a 5 (decrescente)
- Somar os resultados
- Dividir por 11 e obter o resto
- DV = 11 - resto
  - Se DV = 11 → DV = 0
  - Se DV = 10 → somar 2 à soma e refazer o cálculo
- Comparar DV com o 12º dígito
- Depois pegar os 12 primeiros dígitos, multiplicar por pesos 15 a 4, somar, resto, DV = 11 - resto (mesmas regras), comparar com 13º dígito
- Depois 13 primeiros dígitos, pesos 15 a 3, DV vs 14º dígito
- Depois 14 primeiros dígitos, pesos 15 a 2, DV vs 15º dígito
```

Yes! That's the correct provisório algorithm — it's iterative, computing 4 check digits. Let me implement that properly.

CPF validation: standard mod-11 check digits.

**CIAP-2 validation**: format is a letter (A-Z) followed by 2 digits, optionally with a dot and more digits for specificity (e.g., "R05", "A01", "K29"). Actually CIAP-2 codes are letter + 2 digits (like "R05"). Some systems use extended like "R05.1"? No — CIAP-2 is chapter letter + 2 digits. Let me validate: `^[A-Z]\d{2}$`.

**CID-10 validation**: `^[A-Z]\d{2}(?:\.\d{1,2})?$`.

**SOAP record structure:**

```python
class SOAPRecord(BaseModel):
    subjetivo: str
    objetivo: str
    avaliacao: str
    plano: str
```

**Atendimento (care encounter):**

```python
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
```

**SQLAlchemy model:**

```python
class AtendimentoSOAP(Base):
    __tablename__ = "atendimentos_soap"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ...
    versao: Mapped[int]
    hash_conteudo: Mapped[str]
    status_sync: Mapped[SyncStatus]  # enum: PENDENTE, EM_FILA, SINCRONIZADO, CONFLITO
    lote_id: Mapped[str | None]
    ...
```

**Sync protocol flow:**

1. **Offline phase**: Records created locally with UUID, version=1, status=PENDING, content_hash computed.
2. **Reconnection detected**: `sincronizar()` triggered.
3. **Packaging**: Collect pending records → group into batches (by size limit) → serialize (JSON) → compress (gzip) → base64 for transport.
4. **Push**: Send batches to server (via injected transport callable — dependency inversion so tests can mock).
5. **Server response**: acks + server-side deltas since client cursor.
6. **Pull & reconcile**: Apply server deltas locally with LWW conflict resolution.
7. **Update cursor**: persist new sync cursor (watermark).

**Conflict resolution (LWW + hash):**

```python
def resolver_conflito(local, remoto) -> tuple[RecordVencedor, bool houve_conflito]:
    # 1. hashes iguais → convergido, sem conflito
    # 2. versões (lamport) diferentes → maior vence
    # 3. timestamps diferentes → mais recente vence (LWW)
    # 4. empate total → desempate determinístico por hash (garante convergência)
```

Using a Lamport-like logical clock (`versao_logica`) plus wall clock `atualizado_em` gives robust LWW. Tiebreaker: lexicographic comparison of content hash ensures all replicas converge to the same winner (deterministic).

**Delta computation:**

Each record tracks `sincronizado_em` / `cursor_origem`. Delta = records with `atualizado_em > cursor` or status pending. Server watermark: monotonic sequence number. Client stores `cursor_servidor` (last server seq received).

**Batch compression:**

```python
class EmpacotadorLotes:
    TAMANHO_MAX_LOTE = 100 records or 512 KiB uncompressed
    def empacotar(records) -> LoteComprimido:
        payload = json.dumps(...).encode()
        comprimido = gzip.compress(payload)
        return LoteComprimido(id_lote, sha256, dados_b64, registros, bytes)
```

Include integrity hash (SHA-256) of uncompressed payload for verification after decompression.

**Transport abstraction:**

```python
class TransporteSync(Protocol):
    def enviar_lote(self, lote: LoteComprimido) -> ReciboLote: ...
    def buscar_deltas(self, cursor: int, limite: int) -> EnvelopeDeltas: ...
```

The service receives a transport implementation (HTTP client in production, mock in tests).

**Retry with backoff**: exponential backoff with jitter for transient failures; batches marked EM_FILA → PENDENTE on failure.

**Idempotency**: batch IDs + record IDs (UUIDs) make server application idempotent; receipts confirm which records were accepted.

Now, structure of the file. The task says create `backend/app/services/sync_offline.py`. I should provide the complete file plus tests. Given "cobertura de testes automatizados com pytest", I should also provide a test file `backend/tests/services/test_sync_offline.py` (or similar). Let me produce both.

Let me now write the code carefully with Python 3.12 strict typing.

```python
"""Protocolo de Sincronização Delta Offline para Unidades Móveis.

Inspirado na arquitetura de atendimento em áreas remotas do Sistema TAM
(Teleatendimento Assistido Móvel), este módulo implementa:

* Reconciliação bidirecional cliente-servidor com resolução de conflitos
  Last-Write-Wins (LWW) reforçada por hash de versão determinístico;
* Empacotamento de atendimentos SOAP offline em lotes comprimidos (gzip)
  com verificação de integridade (SHA-256);
* Disparo da sincronização quando a conexão 4G/Satélite é restabelecida,
  com retentativas exponenciais e idempotência por UUID.
"""
```

Let me define the components:

1. **Enums & constants**
```python
class StatusSync(str, Enum):
    PENDENTE = "PENDENTE"
    EM_FILA = "EM_FILA"
    EM_TRANSITO = "EM_TRANSITO"
    SINCRONIZADO = "SINCRONIZADO"
    CONFLITO = "CONFLITO"
    REJEITADO = "REJEITADO"
```

2. **Validators** (CNS, CPF, CIAP-2, CID-10) — module-level functions, used by Pydantic field validators.

3. **Pydantic domain models**:
```python
class SOAP(BaseModel):  # frozen
    subjetivo: str
    objetivo: str
    avaliacao: str
    plano: str

class AtendimentoSOAPEntrada(BaseModel):  # what the app creates offline
    id_local: UUID
    unidade_id: str
    profissional_cns: CnsStr
    paciente_cns / paciente_cpf (optional, at least one)
    paciente_nome
    data_atendimento
    ciap2
   