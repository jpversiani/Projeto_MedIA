The user wants me to create a cryptographic validation service for digital prescriptions (Receita Digital) for the MedIA project. This is a Brazilian healthcare system project (SUS/APS standards).

Requirements:
1. Create `backend/app/services/receita_digital.py` with functions for:
   - Generate canonical SHA-256 hash of the prescription
   - Digital signature
   - Verify integrity against tampering of dosages or dispensed medications

2. Architecture guidelines:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me think about the design:

**Canonical Hash Generation:**
- Need a canonical JSON serialization (sorted keys, no whitespace, normalized numbers/dates) so the hash is deterministic
- SHA-256 over the canonical bytes

**Digital Signature:**
- Use Ed25519 (modern, fast, secure) or RSA/ECDSA. Ed25519 is a good choice with `cryptography` library. Actually, for healthcare compliance in Brazil, ICP-Brasil uses RSA typically, but for internal service integrity, Ed25519 is fine. Let me use Ed25519 from the `cryptography` library — it's simple and secure. Alternatively, use HMAC for symmetric... but digital signature implies asymmetric. Let me use Ed25519.

Actually, let me think about what's most appropriate. The task says "assinar digitalmente e verificar integridade contra adulteração de dosagens ou medicamentos dispensados" — sign digitally and verify integrity against tampering of dosages or dispensed medications.

So the flow:
1. Prescription created → canonical hash computed → signed with private key → signature + hash stored
2. Verification: recompute canonical hash from current data, compare with stored hash, verify signature against public key
3. Detect tampering: if dosage or medication changed, hash changes → mismatch detected → report which fields differ (dosage, medication)

**Pydantic v2 models:**
- `PrescricaoDigital` (prescription data): patient CNS/CPF, professional, CID-10, items (medication, dosage, quantity, instructions)
- `ItemPrescricao`: medicamento, dosagem, via, frequência, duração, quantidade
- `AssinaturaDigital`: hash, signature, algorithm, key id, timestamp
- `ResultadoVerificacao`: valid, errors, tampered fields

**SQLAlchemy 2.0:**
- Model `ReceitaDigitalORM` storing the prescription, hash, signature
- Use `Mapped` / `mapped_column` declarative style

**Compliance considerations:**
- LGPD: sensitive health data — hash should be over canonical data; maybe avoid logging sensitive data
- CNS validation (15 digits, DV check), CPF validation (11 digits, DV check)
- CID-10 format validation
- CFM norms for digital prescription (Resolução CFM nº 2.323/2022 allows digital prescriptions with digital signature ICP-Brasil or qualified electronic signature)

Let me design the module:

```python
# backend/app/services/receita_digital.py
```

Structure:
1. Constants and enums
2. Pydantic models (strict typing)
3. Canonical serialization function
4. Hash generation (SHA-256)
5. Key management (load/generate Ed25519 keys)
6. Sign function
7. Verify function with tamper detection (field-level diff)
8. SQLAlchemy ORM model
9. Repository/service class integrating with DB

Also need tests: `backend/tests/services/test_receita_digital.py`

Let me write the canonical JSON:
- Convert datetime to ISO 8601 UTC
- Decimal for dosages (avoid float issues) — serialize as string with normalized representation
- Sort keys recursively
- Separators (",", ":")
- ensure_ascii=False? For determinism, better ensure_ascii=True (NFC normalization for strings). Let me apply Unicode NFC normalization to strings and use ensure_ascii=False with UTF-8 encoding... Actually to be safe: normalize to NFC, then encode UTF-8, ensure_ascii=False. Or ensure_ascii=True which escapes non-ASCII — deterministic either way. I'll use NFC normalization + ensure_ascii=False + UTF-8, documented.

Hmm, simpler and robust: `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` after recursive normalization (Decimal → str, datetime → ISO, strings NFC).

**Field-level tamper detection:**
Compare canonical forms of original (signed) payload vs current payload; produce list of `DivergenciaIntegridade` with JSON path, expected vs actual, and classification (DOSAGEM, MEDICAMENTO, etc.). Focus on dosage/medication tampering detection as required.

**Signature:**
Ed25519 via `cryptography`. Private key loaded from env/PEM. Provide `ReceitaDigitalSigner` class encapsulating key. Sign the hash bytes (or canonical bytes). Sign the canonical bytes directly is fine; store hash too for quick checks.

Key ID: SHA-256 fingerprint of public key (first 16 hex chars) for rotation support.

**SQLAlchemy 2.0 model:**

```python
class ReceitaDigitalORM(Base):
    __tablename__ = "receita_digital"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paciente_cns: Mapped[str] = mapped_column(String(15), index=True)
    ...
    hash_canonico: Mapped[str] = mapped_column(String(64))
    assinatura: Mapped[str] = mapped_column(String(128))  # base64
    algoritmo: Mapped[str]
    chave_id: Mapped[str]
    assinado_em: Mapped[datetime]
    payload_canonico: Mapped[str]  # canonical JSON stored for audit
    status: Mapped[StatusReceita]
```

The service class `ServicoReceitaDigital`:
- `emitir(prescricao, session) -> ReceitaDigitalORM`
- `verificar(session, receita_id, payload_atual) -> ResultadoVerificacao`
- `registrar_dispensacao(...)` — when medications are dispensed, verify integrity of dispensed items vs prescribed

Actually the requirement: "verificar integridade contra adulteração de dosagens ou medicamentos dispensados" — verify integrity against tampering of dosages or dispensed medications. So verification compares the signed prescription against what's being dispensed (or current DB state). I'll implement:

- `verificar_integridade(prescricao_assinada, payload_atual)` → detects divergences, classifying by field type (dosagem, medicamento, etc.)
- `verificar_dispensacao(receita, itens_dispensados)` → checks each dispensed item matches a prescribed item (medication + dosage), flags substitutions

**CNS validation algorithm:**
CNS: 15 digits. First digit 1,2 (prov), 7,8,9 (cartão nacional). DV calculation: sum = Σ digit_i * (15 - i); DV such that (sum + dv*?) ... The standard algorithm:

For CNS starting with 1, 2: peso from 15 down to 2 for first 14 digits; soma = Σ d[i] * peso[i]; resto = soma % 11; dv = 11 - resto; if dv == 11: dv = 0; if dv > 9 → invalid (need recomputation with different approach — actually for CNS the DV must be 0-9; if dv==10 or 11 invalid... hmm). Let me recall the correct algorithm:

CNS validation (standard):
```
soma = 0
for i in range(15): soma += int(cns[i]) * (15 - i)
resto = soma % 11
if resto == 0: valid
else: dv = 11 - resto ... 
```
No wait. The common implementation:

```python
def valida_cns(cns):
    cns = cns.strip().replace('.', '').replace(' ', '')
    if len(cns) != 15: return False
    if cns[0] not in '123789': return False
    # for 1,2: must have all digits... 
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

Yes! The correct check: sum of digit * weight (15 down to 1) must be divisible by 11. That's the standard CNS validation. For CNS starting with 7, 8, 9, there's a different DV scheme (the last 12 digits...). Actually for 7/8/9 cards: the check is done differently — the standard implementation:

```python
if cns[0] in '789':
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if soma % 11 == 0: return True
    # else try the alternative: 
    dv = 11 - (soma % 11)
    ...
```

The widely used algorithm for 7/8/9:
```
peso = 15..2 for first 14 digits
soma = Σ
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0
if dv == 10: dv = 0 and soma += 2, recompute resto... 
```
Hmm, the actual algorithm for 7/8/9 CNS:

```
soma = Σ (d[i] * (15 - i)) for i in 0..13
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0
if dv == 10:
    soma += 2  # add 2 to sum
    resto = soma % 11
    dv = 11 - resto
    if dv == 11: dv = 0
# check dv == int(cns[14])
```

Wait, that's not right either. Let me recall the official implementation from DATASUS:

```python
def valida_cns(cns):
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] in '12':
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    elif cns[0] in '789':
        # Definitive cards 7/8/9 use a different DV
        soma = sum(int(cns[i]) * (15 - i) for i in range(14))
        resto = soma % 11
        dv = 11 - resto
        if dv == 11: dv = 0
        if dv == 10:
            soma += 2
            resto = soma % 11
            dv = 11 - resto
            if dv == 11: dv = 0
        return dv == int(cns[14])
    return False
```

Hmm, I've seen this variant. Actually the official DATASUS pseudo-code:

```
Para CNS com primeiro dígito 1 ou 2:
  soma = Σ (i=0..14) d[i] * (15 - i)
  válido se soma % 11 == 0

Para CNS com primeiro dígito 7, 8 ou 9:
  soma = Σ (i=0..13) d[i] * (15 - i)
  resto = soma % 11
  dv = 11 - resto
  se dv == 11: dv = 0
  se dv == 10: soma = soma + 2; resto = soma % 11; dv = 11 - resto; se dv == 11: dv = 0
  válido se dv == d[14]
```

Hmm, I believe the "soma + 2" trick is real for the 7/8/9 cards. Let me just implement it that way — it's the commonly cited algorithm. Actually wait, I recall the official one differently. Let me think again...

The official DATASUS routine (from the "Rotina de validação do CNS"):

```
rotina valida_CNS(numCNS)
  se tamanho != 15 → inválido
  se numCNS[0] ∈ {1,2}:
     soma = Σ_{i=0}^{14} numCNS[i] * (15 - i)
     se soma % 11 == 0 → válido
  se numCNS[0] ∈ {7,8,9}:
     soma = Σ_{i=0}^{13} numCNS[i] * (15 - i)
     resto = soma % 11
     dv = 11 - resto
     se dv == 11: dv = 0
     se dv == 10:
        soma = soma + 2
        resto = soma % 11
        dv = 11 - resto
        se dv == 11: dv = 0
     se dv == numCNS[14] → válido
```

Yes, this is the documented algorithm. I'll implement that.

**CPF validation:** standard mod-11 DV check for both digits.

**CID-10 validation:** format letter + 2 digits (+ optional .digit). Regex: `^[A-Z]\d{2}(\.\d{1,2})?$`.

**CIAP-2:** format letter+digit+letter (e.g., "K29", "A01"? CIAP-2 codes are like "A01", "K29", "L03" — letter digit digit? Actually CIAP-2 codes are chapter letter + 2 digits, e.g., A01, K29, T90. Wait no — ICPC-2 codes are letter + 2 digits: "A01", "K29". Hmm, but some write "K29" yes. CIAP-2 = Portuguese version of ICPC-2. Format: 1 letter (A–Z, excluding some?) + 2 digits. Regex `^[A-Z]\d{2}$`.

The prescription service mainly needs patient ID (CNS/CPF), prescriber info (CRM/COREN + UF), CID-10 (diagnosis) — CIAP-2 could be the reason for encounter. I'll include both as optional validated fields to align with SUS/APS guidelines.

**SOAP method**: the prescription is part of "P" (Plano) in SOAP. I can include a reference field `soap_plano` or note. Maybe include `avaliacao_soap` optional field with S/O/A/P components? That might be overkill. I'll include an optional `plano` text and reference that prescription belongs to the Plan component. Keep it light: a field `cid10_codigo` (required for prescription per CFM? Actually CID is recommended), `ciap2_codigo` optional.

**Pydantic v2 strict typing:**
Use `model_config = ConfigDict(strict=True, frozen=True)` for immutability of signed payloads. Use `Field(pattern=...)`, `StringConstraints`, `Annotated` types.

**Dosage representation:** Use `Decimal` with quantization to avoid float issues. Canonical serialization of Decimal → string normalized (e.g., "10.500" → "10.5"? or keep as given?). For canonical form, normalize: strip trailing zeros? Decimal("10.50") vs "10.5" are equal values; canonical should normalize. Use `decimal.normalize()` but careful: Decimal("10").normalize() → "1E+1". Need to handle: use `format(d, 'f')` after normalize, or quantize. I'll write a helper `_decimal_canonico(d: Decimal) -> str` that normalizes and formats without exponent:

```python
def _decimal_para_canonico(d: Decimal) -> str:
    normalizado = d.normalize()
    if normalizado == normalizado.to_integral_value():
        # avoid exponent for integers
        return f"{normalizado.quantize(Decimal(1)):f}"  # hmm
    return format(normalizado, 'f')
```

Simpler: `format(d.normalize(), 'f')` — for Decimal("1E+1"), format(..., 'f') gives "10". Yes! `format(Decimal('1E+1'), 'f')` → '10'. And Decimal('10.50').normalize() → Decimal('10.5') → '10.5'. Decimal('0').normalize() → Decimal('0') → '0'. Good. Edge: Decimal('0.000').normalize() → Decimal('0') → '0'. Good.

**Canonicalization function:**

```python
def _canonizar(obj: Any) -> Any:
    match obj:
        case BaseModel(): return _canonizar(obj.model_dump(mode="python", exclude_none=True))
        case datetime(): return obj.astimezone(timezone.utc).isoformat()  # with timezone
        case Decimal(): return _decimal_para_canonico(obj)
        case str(): return unicodedata.normalize("NFC", obj)
        case dict(): return {str(k): _canonizar(v) for k, v in sorted(obj.items())}
        case list() | tuple(): return [_canonizar(v) for v in obj]
        case None | bool() | int(): return obj
        case float(): raise TypeError (strict: no floats)
        case UUID(): return str(obj)
        case Enum(): return _canonizar(obj.value)
        case _: raise TypeError
```

exclude_none=True to keep canonical form stable regardless of optional fields. Hmm — but that means adding a None field doesn't change hash; that's fine and desirable (None == absent).

**Hash:**

```python
def gerar_hash_canonico(prescricao: PrescricaoDigital) -> str:
    payload = _canonizar(prescricao)
    json_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
```

**Signer:**

```python
class AssinadorReceitaDigital:
    def __init__(self, chave_privada_pem: bytes, senha: bytes | None = None): ...
    @classmethod
    def gerar_par_chaves(cls) -> tuple[bytes, bytes]  # private, public PEM
    def assinar(self, dados: bytes) -> str  # base64
    def verificar(self, dados: bytes, assinatura_b64: str) -> bool
    @property
    def chave_id(self) -> str  # fingerprint
```

Use Ed25519PrivateKey. Sign the canonical JSON bytes (not just hash) — or sign the hash. I'll sign the canonical bytes; hash stored separately for quick integrity check. Actually signing the hash is also fine. Let me sign the