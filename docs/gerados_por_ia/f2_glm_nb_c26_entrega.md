The user wants me to create a cryptographic validation service for digital prescriptions (Receita Digital) for the MedIA project. This is a Brazilian healthcare system (SUS/APS - Atenção Primária à Saúde).

Requirements:
1. Create `backend/app/services/receita_digital.py`
2. Functions for:
   - Generate canonical SHA-256 hash of the prescription
   - Digital signature
   - Verify integrity against tampering of dosages or dispensed medications
3. Guidelines:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me design this properly:

**Architecture considerations:**

1. **Canonical hash**: Need a deterministic serialization (JSON canonical form) of the prescription so the same prescription always produces the same hash. This means sorting keys, normalizing whitespace, using ISO timestamps, etc.

2. **Digital signature**: Use RSA or ECDSA via the `cryptography` library. For healthcare in Brazil, ICP-Brasil certificates are the standard (A1/A3), but for a service-level implementation, we can use Ed25519 or RSA-PSS with SHA-256. RSA-PSS is a good choice for compatibility. Actually, Ed25519 is simpler and modern, but RSA-PSS with SHA-256 aligns better with ICP-Brasil conventions. Let me use RSA-PSS.

3. **Pydantic v2 models**: 
   - `PrescricaoDigital` (the prescription model)
   - `MedicamentoPrescrito` (medication with dosage)
   - `ProfissionalPrescritor` (prescriber with CNS/CPF)
   - `PacienteIdentificado` (patient with CNS/CPF)
   - `ResultadoVerificacao` (verification result)

4. **SQLAlchemy 2.0**: The service should probably work with ORM models for persistence of signatures/hashes. I could include a SQLAlchemy model for `ReceitaDigitalRegistro` or at least show how the service integrates. The task says "crie backend/app/services/receita_digital.py" — a service file. But guidelines mention SQLAlchemy 2.0. I should probably include:
   - The service file with Pydantic models and crypto functions
   - Maybe a SQLAlchemy model for audit/persistence (could be in the same file or referenced)
   - Tests with pytest

Let me think about what a complete, high-quality deliverable looks like:

**File 1: `backend/app/services/receita_digital.py`**
- Pydantic v2 models with strict typing
- Canonical serialization function (JSON with sorted keys, normalized)
- SHA-256 hash generation
- RSA key loading/generation
- Sign function (RSA-PSS)
- Verify function
- Tamper detection (compare recomputed hash vs stored hash, verify signature)
- Integration with SQLAlchemy 2.0 for persistence (maybe a model + repository functions)

**File 2: `backend/app/services/receita_digital.py` tests** — `backend/tests/services/test_receita_digital.py`

Let me think about the domain model for a Brazilian prescription (Receita Digital):

```python
class ProfissionalPrescritor(BaseModel):
    nome_completo: str
    cpf: str  # validated
    cns: str  # validated (Cartão Nacional de Saúde)
    registro_conselho: str  # CRM/COREN etc
    uf_conselho: str
    especialidade: str | None

class PacienteReceita(BaseModel):
    nome_completo: str
    cns: str
    cpf: str | None
    data_nascimento: date

class MedicamentoPrescrito(BaseModel):
    nome_medicamento: str  # or principio_ativo (DCB - Denominação Comum Brasileira)
    concentracao: str
    forma_farmaceutica: str
    via_administracao: str  # VO, IM, IV, etc
    dose: str  # "500 mg"
    frequencia: str  # "8/8h"
    duracao_dias: int
    quantidade_dispensar: int
    observacoes: str | None

class PrescricaoDigital(BaseModel):
    id_prescricao: UUID
    data_emissao: datetime
    cid10_principal: str | None  # CID-10
    ciap2_episodio: str | None  # CIAP-2
    profissional: ProfissionalPrescritor
    paciente: PacienteReceita
    medicamentos: list[MedicamentoPrescrito]
    orientacoes_gerais: str | None
    metodo_soap: ... # maybe not needed in hash, but could include
```

For canonical serialization:
- Convert to JSON with `model_dump(mode="json")`
- Sort keys recursively
- Normalize strings (NFC unicode normalization, strip whitespace)
- Serialize with separators `(",", ":")` no spaces
- Encode UTF-8
- SHA-256

For signature:
- RSA-PSS with SHA-256, MGF1-SHA256, salt length = digest size (maximal)
- Or Ed25519. Let me go with RSA-PSS since it's more standard in healthcare/HSM contexts and aligns with ICP-Brasil (which uses RSA). I'll make the algorithm configurable but default RSA-PSS.

Actually, let me think about what's most defensible: The `cryptography` library supports both. RSA-PSS:
```python
signature = private_key.sign(
    data,
    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
    hashes.SHA256(),
)
```
Verification:
```python
public_key.verify(signature, data, padding.PSS(...), hashes.SHA256())
```

For key management: The service should accept keys via environment/config. I'll create a `KeyProvider` protocol or simple functions to load PEM keys, plus a dev-only key generator.

For SQLAlchemy 2.0 integration: A model `ReceitaDigitalORM` storing:
- id (UUID)
- prescricao_id
- hash_canonico (String 64 hex)
- assinatura (LargeBinary)
- algoritmo (String)
- certificado/assinante info
- created_at
- status

And a repository class with async or sync session. MedIA — I don't know if they use async SQLAlchemy. SQLAlchemy 2.0 supports both. Given "SQLAlchemy 2.0" strict typing, I'll use `Mapped[]` and `mapped_column` declarative style. For the service, I'll keep DB persistence optional/separate — the core service is pure crypto (easier to test), and provide a repository class that takes a Session.

Hmm, but the task says "crie backend/app/services/receita_digital.py" — one file. I should deliver that file as the main artifact, plus tests. I can include the SQLAlchemy model in the same file or note it belongs in models. To keep it self-contained and respect the single-file instruction, I'll include:
- Pydantic schemas
- Crypto core
- SQLAlchemy 2.0 ORM model + repository (in the same file, clearly sectioned) — or maybe better to keep the ORM model in the service file since that's what was asked. Actually services usually shouldn't define ORM models... but the instruction says create this file with functions for hash/sign/verify. The SQLAlchemy mention in guidelines suggests they want the stack respected. I'll include a small ORM model and repository in the service file with a comment that it could be moved to `app/models/`. Alternatively, I can make the repository generic over the Session and define the model in the same file for cohesion.

Let me decide: I'll put everything in `receita_digital.py` with clear sections, since the task explicitly asks for that file. I'll note in comments that the ORM model may be relocated.

Actually, let me reconsider — cleaner architecture: the service file contains the domain logic (Pydantic + crypto). Persistence via SQLAlchemy is a separate concern. But the guidelines say "tipagem estrita com Pydantic v2 e SQLAlchemy 2.0" — meaning the codebase uses these. The service should at least integrate with SQLAlchemy for storing signatures. I'll include a `ReceitaDigitalRegistro` ORM model and a `ReceitaDigitalRepository` in the same file (or I could split). Given the explicit single-file instruction, same file it is, with a note.

**Verification flow (anti-tampering):**

1. Recompute canonical hash from the received prescription data.
2. Compare with the stored/registered hash → detects any field modification (dosage, medication swap, quantity).
3. Verify RSA-PSS signature over the canonical hash (or over canonical bytes) with the prescriber's public key → proves authenticity and non-repudiation.
4. Return a structured `ResultadoVerificacao` with:
   - `hashes_conferem: bool`
   - `assinatura_valida: bool`
   - `integridade_ok: bool`
   - `campos_alterados: list[str]` (diff detection — nice touch: identify which fields changed, e.g., dosage)
   - `motivo` details

Diff detection: compare canonical JSON of received vs original to list changed paths (e.g., `medicamentos[0].dose`). That's a great feature for "verificar integridade contra adulteração de dosagens ou medicamentos dispensados" — pinpointing that `medicamentos[0].dose` changed from "500 mg" to "50 mg".

**Canonicalization details:**
- Unicode NFC normalization
- Strip strings
- Dates → ISO 8601
- Floats: avoid floats entirely; use Decimal serialized as string, or integers. For dosages, strings are fine. `quantidade_dispensar: int`.
- Sort keys recursively
- Compact separators
- Exclude None? No — keep None as null for determinism, but consistent either way. Keep them.

Pydantic v2: `model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)` — frozen for immutability of signed data. `str_strip_whitespace=True` helps canonicalization.

**CNS validation**: CNS has a check digit algorithm (PIS-like). I can implement validation:
- CNS format: 15 digits. Valid prefixes: 1, 2 (cartão nacional de saúde), 7, 8, 9 (provisórios). Algorithm:
  ```
  Soma = soma de (n[i] * (15 - i))
  resto = soma % 11
  if resto != 0: dv = 11 - resto else dv = 0
  ```
  Actually the CNS validation algorithm: For numbers starting with 1, 2: 
  - pesos = 15,14,13,...,2 for first 14 digits
  - soma = Σ d[i] * peso[i]
  - resto = soma % 11
  - if resto < 2: dv = 0? Hmm, let me recall correctly.

The standard CNS validation (from DATASUS):
```
n = CNS as 15 digits
soma = 0
for i in range(15): soma += int(n[i]) * (15 - i)
resto = soma % 11
if resto != 0:
    resultado = 11 - resto
else:
    resultado = resto
if resultado != 11:  # hmm
```
Let me recall the actual algorithm. The commonly used one:

```python
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15: return False
    if cns[0] not in '123456789': return False  # actually 1,2,7,8,9
    # defnitive: 1,2 ; provisório: 7,8,9
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

Yes! The correct check: the weighted sum with weights 15 down to 1 must be divisible by 11. Wait, weights: for i in 0..14, weight = 15 - i, so weights 15,14,...,1. Sum must be ≡ 0 mod 11. That's the well-known CNS validation. Let me verify with a known valid CNS: "89800451977" — no that's 11 digits (that's a PIS). Known valid CNS example: 700000000000031? Hmm. Let me test the algorithm mentally with a generated one... I'll trust the standard: `soma % 11 == 0` with weights 15..1. This is the widely used implementation (e.g., from various Brazilian validation libs). Also digits must be 15 length, first char in {1,2,7,8,9}.

Actually there's a subtlety: for CNS starting with 1 or 2 (definitive), there's a different construction, but the mod-11 check with weights 15..1 works for all. I'll implement that.

**CPF validation**: standard check-digit algorithm. Implement `validar_cpf`.

**CID-10 format**: letter + digits, e.g., "I10", "E11.9". Regex: `^[A-Z]\d{2}(\.\d{1,2})?$`.

**CIAP-2 format**: letter + 2 digits, e.g., "K29", "A01". Regex: `^[A-Z]\d{2}$`.

**Via de administração**: enum — VO (oral), IM, IV, SC, SL, TOP, INH, OFT, OT, RET, NASAL...

**Signature payload**: Sign the canonical bytes directly (or the hash). Signing the hash bytes is standard (RSA-PSS over SHA-256 digest). I'll sign the canonical bytes — the library hashes internally with SHA-256 anyway. Actually signing the raw canonical bytes with RSA-PSS+SHA-256 is equivalent to signing the digest. I'll sign canonical bytes.

Hmm, but for storage efficiency and to make verification independent of re-serialization, storing hash + signature-of-hash is common. I'll sign the canonical bytes (32-byte digest is what gets signed internally). Let me sign the canonical bytes directly — cleaner semantics: "assinatura sobre a representação canônica".

Wait — one design decision: should the signature cover the hash hex string or the raw bytes? If we sign raw canonical bytes, verification requires re-serializing identically. If we sign the digest bytes, verification requires only the digest. Both fine. I'll sign the raw canonical bytes and store the hash for quick integrity checks. Verification: recompute canonical bytes → verify signature over them → compare hash.

**Key management**: 
- `ReceitaDigitalService` class taking a private key (for signing) and/or public key (for verification).
- Load from PEM strings/bytes or files.
- `gerar_par_chaves_dev()` for tests/dev only, with a warning.
- Support key rotation? Maybe `key_id` in the record. Nice touch: include `key_id` (fingerprint of public key, e.g., SHA-256 of public key DER, first 16 hex chars) in the signature envelope for rotation support.

**Signature envelope (Pydantic)**:
```python
class EnvelopeAssinatura(BaseModel):
    versao: Literal["1.0"]
    algoritmo: Literal["RSA-PSS-SHA256"]
    key_id: str
    hash_canonico: str  # hex
    assinatura: str  # base64
    assinado_em: datetime
    assinante_cpf: str  # or registro
```

**Service API**:
```python
class ReceitaDigitalService:
    def __init__(self, chave_privada: rsa.RSAPrivateKey | None = None, chave_publica: rsa.RSAPrivateKey | None = None): ...
    
    def gerar_hash_canonico(self, prescricao: PrescricaoDigital) -> str  # hex
    def serializar_canonico(self, prescricao) -> bytes
    def assinar(self, prescricao) -> EnvelopeAssinatura
    def verificar(self, prescricao: PrescricaoDigital, envelope: EnvelopeAssinatura, *, chave_publica=None) -> ResultadoVerificacao
    def detectar_adulteracao(self, original: PrescricaoDigital, recebida: PrescricaoDigital) -> list[AlteracaoCampo]
```

**Repository (SQLAlchemy 2.0)**:
```python
class ReceitaDigitalRegistro(Base):
    __tablename__ = "receita_digital_registros"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    prescricao_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    hash_canonico: Mapped[str] = mapped_column(String(64))
    algoritmo: Mapped[str] = mapped_column(String(32))
    key_id: Mapped[str] = mapped_column(String(32))
    assinatura: Mapped[bytes] = mapped_column(LargeBinary)
    assinado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    prescritor_cpf: Mapped[str] = mapped_column(String(11))
    prescritor_cns: Mapped[str] = mapped_column(String(15))
    created_at: ...
```

And `ReceitaDigitalRepository` with `registrar`, `obter_por_prescricao`, sync Session (SQLAlchemy 2.0 style with `select()`).

Should I use async? MedIA backend — unknown. I'll go sync for simplicity and broad compatibility, noting async adaptation. Actually many modern FastAPI projects use async SQLAlchemy. Hmm. The task doesn't specify. I'll provide sync repository (SQLAlchemy 2.0 typed style) — it's the safest default and tests can use in-memory SQLite. I could mention async adaptation in comments.

**Tests** (`backend/tests/services/test_receita_digital.py`):
- Test canonical serialization determinism (same input → same bytes; different key order in JSON input → same hash)
- Test hash changes when dosage changes
- Test hash changes when medication list changes
- Test sign/verify roundtrip
- Test verification fails on tampered dosage
- Test verification fails on tampered medication (swapped drug)
- Test verification fails on tampered quantity to dispense
- Test verification fails with wrong key
- Test detection lists changed fields precisely
- Test CPF/CNS validators (valid/invalid)
- Test CID-10/CIAP-2 validators
- Test repository roundtrip with SQLite in-memory
- Test unicode normalization in canonical form
- Test whitespace normalization

Use fixtures: generate RSA key once per session.

**Dependencies**: `cryptography`,