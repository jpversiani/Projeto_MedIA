The user wants me to create a Python service for offline delta synchronization protocol for mobile units (C5), inspired by the TAM System architecture (Sistema de Atendimento Móvel - likely referring to Telemedicine/Atendimento Móvel in remote areas of Brazil, related to SUS).

Requirements:
- File: `backend/app/services/sync_offline.py`
- Bidirectional reconciliation protocol with conflict resolution (Last-Write-Wins with version hash)
- Packaging of offline SOAP attendments in compressed batches
- Synchronization when 4G/Satellite connection is re-established
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me design this carefully:

1. **Domain Model** (SQLAlchemy 2.0):
   - `AtendimentoSOAP` (SOAP attendance record) - with SOAP fields (Subjetivo, Objetivo, Avaliação, Plano)
   - `SyncBatch` - batch of records to sync
   - `SyncOperation` - individual operation in a batch
   - `SyncConflict` - conflict record

2. **Pydantic v2 Schemas**:
   - `AtendimentoSOAPCreate/Read`
   - `SyncBatchRequest/Response`
   - `ConflictResolution`
   - `SyncManifest`

3. **Sync Protocol**:
   - Delta sync: only changes since last sync (using `updated_at` watermark / cursor)
   - LWW conflict resolution with version hash (hash of content + version counter)
   - Compression: gzip/zlib of batches
   - Idempotency: client-generated UUIDs
   - Tombstones for deletions

4. **CIAP-2 codes**: e.g., R29 (symptom), A01, etc. Validation of CIAP-2 and CID-10 formats.

5. **CNS validation**: CNS has a check digit algorithm (PIS-like). CPF too.

Let me write the code:

```python
# backend/app/services/sync_offline.py
```

Structure:

- Constants: CIAP-2 chapter validation, CID-10 regex
- Validators: CNS (check digit), CPF (check digits), CID-10 regex, CIAP-2 regex
- `VersionHash`: compute content hash (SHA-256 truncated) + monotonic version counter
- `SyncOperationType` enum: CREATE, UPDATE, DELETE (tombstone)
- `SyncStatus` enum: PENDING, IN_FLIGHT, SYNCED, CONFLICT, REJECTED
- SQLAlchemy models:
  - `AtendimentoSOAPModel`: id (UUID), patient identifiers (cns, cpf), professional, unit (UBS/mobile unit), SOAP fields, ciap2_codes, cid10_codes, version, content_hash, updated_at, deleted (tombstone), sync_status, device_id, origin
  - `SyncBatchModel`: batch id, device_id, operations count, payload (compressed), status, checksum, created_at, applied_at
  - `SyncConflictModel`: entity id, base_version, server_version, client_version, resolution, resolved_at
- Pydantic schemas with strict validation
- `SyncService` class:
  - `push(batch)`: apply client operations with LWW
  - `pull(device_id, since_cursor, limit)`: return delta envelope
  - `create_batch(...)`: compress operations into gzip batch
  - `resolve_conflict(...)`: manual or automatic resolution
- LWW logic: compare (version, updated_at, content_hash); if client version > server version → apply; if equal version but different hash → conflict; if client version <= server → reject (stale) unless idempotent replay (same hash → no-op success)

Also need:
- Delta computation: `since` watermark (Lamport-like or timestamp + sequence)
- Compression: zlib/gzip with base64 for transport
- Checksum: SHA-256 of payload for integrity
- Envelope with manifest: batch_id, device_id, sequence, operations, checksum, compressed payload

Tests: pytest with in-memory SQLite, covering:
- CNS/CPF validation
- LWW conflict resolution scenarios (client newer, server newer, concurrent conflict, idempotent replay)
- Compression round-trip
- Pull delta with cursor
- Tombstone deletion
- Batch integrity (checksum mismatch)
- Full sync cycle

Let me write the code with strict typing (Python 3.12: use `X | None`, `list[...]`, etc.)

CNS validation algorithm:
CNS can start with 1, 2, 7, 8, 9. For 1/2 (definitive), it's PIS format: 7 digits + check digits via mod 11 weights 15..2? Actually the CNS validation:

For CNS starting with 1, 2: 
- Digits: 7 first digits, then DV computed with weights 15,14,13,...,9? Let me recall the algorithm:

CNS definitive (starts with 1 or 2): 15 digits. Validation:
```
soma = sum(digit[i] * (15 - i) for i in range(11))  # weights 15..5 for first 11 digits
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0
if dv == 10: dv = 0; soma += 2; resto = soma % 11; dv = 11 - resto  # special case
```
Hmm, the actual algorithm:

```
pesos = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5]
soma = sum(peso * digito for ...)
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0
if dv == 10:
    soma = soma + 2
    resto = soma % 11
    dv = 11 - resto
```
Then compare dv with digits 12-13? Actually the CNS has 15 digits: first 11 + 2 check digits + 1? Let me recall properly.

CNS: 15 digits. Format for definitive cards (starting 1 or 2): 7 digits (NDS) + 4 digits (origin/date?) + 2 DV + ... Actually it's: 1st to 7th digits, 8th-11th, then 12th-13th are DV, 14th-15th... Hmm.

The standard algorithm (from DATASUS):

```
def valida_cns(cns: str) -> bool:
    cns = cns.replace('.', '').replace(' ', '')
    if len(cns) != 15: return False
    if cns[0] not in '123789': return False
    # For 1,2: use weights
    soma = 0
    for i in range(15):
        # ...
```

Actually the well-known algorithm:

```python
def valida_cns(vlrCNS):
    # Fórmula para validação do CNS
    if len(vlrCNS) != 15:
        return False
    # ...
    pis = vlrCNS[0:11]
    soma = 0
    resto = 0
    # weights 15,14,13,12,11,10,9,8,7,6,5 for first 11 digits
    peso = 15
    for i in range(11):
        soma += int(pis[i]) * peso
        peso -= 1
    resto = soma % 11
    if resto == 0:
        dv = 0
    else:
        dv = 11 - resto
    if dv == 10:
        soma = 0
        peso = 15
        for i in range(11):
            soma += int(pis[i]) * peso
            peso -= 1
        resto = (soma + 2) % 11
        if resto == 0:
            dv = 0
        else:
            dv = 11 - resto
    if vlrCNS[11:13] != f"{dv}0"? 
```

Hmm, let me recall the canonical JS implementation:

```javascript
function validaCNS(vlrCNS) {
   // Formulário que contém o CNS
   var cns = vlrCNS;
   var soma = new Number;
   var resto = new Number;
   var dv = new Number;
   var pis = new String;
   var resultado = new String;
   var faltam = new String;
   if (vlrCNS.trim().length != 15){
      return(false);
   }   
   pis = vlrCNS.substring(0,11);
   soma = (((parseInt(pis.substring(0,1),10)) * 15) +
   ((parseInt(pis.substring(1,2),10)) * 14) +
   ((parseInt(pis.substring(2,3),10)) * 13) +
   ((parseInt(pis.substring(3,4),10)) * 12) +
   ((parseInt(pis.substring(4,5),10)) * 11) +
   ((parseInt(pis.substring(5,6),10)) * 10) +
   ((parseInt(pis.substring(6,7),10)) * 9) +
   ((parseInt(pis.substring(7,8),10)) * 8) +
   ((parseInt(pis.substring(8,9),10)) * 7) +
   ((parseInt(pis.substring(9,10),10)) * 6) +
   ((parseInt(pis.substring(10,11),10)) * 5)) + ((parseInt(vlrCNS.substring(11,12),10)) * 4) +
   ((parseInt(vlrCNS.substring(12,13),10)) * 3) +
   ((parseInt(vlrCNS.substring(13,14),10)) * 2) +
   ((parseInt(vlrCNS.substring(14,15),10)) * 1);
   resto = soma % 11;
   if (resto != 0) {
      dv = 11 - resto;
   } else {
      dv = 0;
   }
   if (dv == 10) {
      soma = (((parseInt(pis.substring(0,1),10)) * 15) +
      ((parseInt(pis.substring(1,2),10)) * 14) +
      ((parseInt(pis.substring(2,3),10)) * 13) +
      ((parseInt(pis.substring(3,4),10)) * 12) +
      ((parseInt(pis.substring(4,5),10)) * 11) +
      ((parseInt(pis.substring(5,6),10)) * 10) +
      ((parseInt(pis.substring(6,7),10)) * 9) +
      ((parseInt(pis.substring(7,8),10)) * 9) +  // hmm
      ...
```

Actually the dv==10 case: soma += 2 then recompute resto = soma % 11, dv = 11 - resto. And the check: dv must equal the 15th digit? No wait.

Let me look at the canonical algorithm again (from DATASUS documentation "Validação do CNS"):

The CNS is 15 digits: A B C D E F G H I J K L M N O
- Weights: 15 14 13 12 11 10 9 8 7 6 5 4 3 2 1 applied to all 15 digits
- soma = Σ digito_i * peso_i
- resto = soma % 11
- if resto != 0 → dv = 11 - resto else dv = 0
- The CNS is valid if dv == 0? No...

Hmm, actually the algorithm: sum all 15 digits with weights 15..1, resto = soma % 11; if resto == 0, valid. That's one variant. Let me recall the JS from DATASUS:

```javascript
function validaCNS(vlrCNS) {
   var soma = 0;
   var resto = 0;
   var dv = 0;
   var pis = "";
   var resultado = "";
   var faltam = "";
   if (vlrCNS.trim().length != 15) return false;
   pis = vlrCNS.substring(0,11);
   soma = parseInt(pis.substring(0,1)) * 15 + ... + parseInt(pis.substring(10,11)) * 5
        + parseInt(vlrCNS.substring(11,12)) * 4 + parseInt(vlrCNS.substring(12,13)) * 3
        + parseInt(vlrCNS.substring(13,14)) * 2 + parseInt(vlrCNS.substring(14,15)) * 1;
   resto = soma % 11;
   if (resto != 0) dv = 11 - resto; else dv = 0;
   if (dv == 10) {
      soma = soma + 2;
      resto = soma % 11;
      if (resto != 0) dv = 11 - resto; else dv = 0;
   }
   resultado = pis + dv.toString();  // hmm no
   ...
}
```

Hmm, this is getting complicated. Actually the canonical one I remember:

```javascript
function validaCNS(vlrCNS) {
   ...
   if (vlrCNS.trim().length != 15) return false;
   // soma com pesos 15..1 sobre os 15 dígitos
   soma = 0;
   for (i = 0; i < 15; i++) {
       peso = 15 - i;
       soma += parseInt(vlrCNS.substring(i, i+1)) * peso;
   }
   resto = soma % 11;
   if (resto != 0) { dv = 11 - resto; } else { dv = 0; }
   if (dv == 10) {
       soma = soma + 2;
       resto = soma % 11;
       if (resto != 0) { dv = 11 - resto; } else { dv = 0; }
   }
   // valida: o dv calculado deve ser igual ao último dígito? 
```

Hmm no. Let me think about the actual known-good Python implementation:

```python
def valida_cns(cns: str) -> bool:
    """
    Valida CNS conforme algoritmo do DATASUS.
    """
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in '123789':
        return False
    
    # Soma com pesos
    soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
    dv = 11 - (soma % 11)
    if dv == 11:
        dv = 0
    if dv == 10:
        soma += 2
        dv = 11 - (soma % 11)
        if dv == 11:
            dv = 0
    # compara com os dois últimos dígitos? 
```

Hmm. Actually, I recall the definitive CNS (1 or 2 prefix) validation: the last digit is the check digit computed over the first 14? No — the algorithm above computes a single dv and the CNS is valid if... 

Let me look at this from a different angle. The well-known JS function from DATASUS (used widely):

```javascript
function validaCNS(vlrCNS) {
   // Fórmula para validação do CNS
   var cns = vlrCNS;
   var soma = new Number;
   var resto = new Number;
   var dv = new Number;
   var pis = new String;
   var resultado = new String;
   var faltam = new String;
   if (vlrCNS.trim().length != 15){
      return(false);
   }   
   pis = vlrCNS.substring(0,11);
   soma = (((parseInt(pis.substring(0,1),10)) * 15) +
   ((parseInt(pis.substring(1,2),10)) * 14) +
   ((parseInt(pis.substring(2,3),10)) * 13) +
   ((parseInt(pis.substring(3,4),10)) * 12) +
   ((parseInt(pis.substring(4,5),10)) * 11) +
   ((parseInt(pis.substring(5,6),10)) * 10) +
   ((parseInt(pis.substring(6,7),10)) * 9) +
   ((parseInt(pis.substring(7,8),10)) * 8) +
   ((parseInt(pis.substring(8,9),10)) * 7) +
   ((parseInt(pis.substring(9,10),10)) * 6) +
   ((parseInt(pis.substring(10,11),10)) * 5)) + ((parseInt(vlrCNS.substring(11,12),10)) * 4) +
   ((parseInt(vlrCNS.substring(12,13),10)) * 3) +
   ((parseInt(vlrCNS.substring(13,14),10)) * 2) +
   ((parseInt(vlrCNS.substring(14,15),10)) * 1);
   resto = soma % 11;
   if (resto != 0) {
      dv = 11 - resto;
   } else {
      dv = 0;
   }
   if (dv == 10) {
      soma = (((parseInt(pis.substring(0,1),10)) * 15) +
      ((parseInt(pis.substring(1,2),10)) * 14) +
      ((parseInt(pis.substring(2,3),10)) * 13) +
      ((parseInt(pis.substring(3,4),10)) * 12) +
      ((parseInt(pis.substring(4,5),10)) * 11) +
      ((parseInt(pis.substring(5,6),10)) * 10) +
      ((parseInt(pis.substring(6,7),10)) * 9) +
      ((parseInt(pis.substring(7,8),10)) * 8) +
      ((parseInt(pis.substring(8,9),10)) * 7) +
      ((parseInt(pis.substring(9,10),10)) * 6) +
      ((parseInt(pis.substring(10,11),10)) * 5)) + 2;
      resto = soma % 11;
      if (resto != 0) {
         dv = 11 - resto;
      } else {
         dv = 0;
      }
   }
   resultado = pis + dv;
   if (resultado != cns) {
      return(false);
   } else {
      return(true);
   }
}
```

Hmm wait, that