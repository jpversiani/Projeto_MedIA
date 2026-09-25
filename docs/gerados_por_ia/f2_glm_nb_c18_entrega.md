The user wants me to create a cryptographic validation service for digital prescriptions (Receita Digital) for the MedIA project. This is a Brazilian healthcare context (SUS/APS - Primary Health Care), so I need to consider:

1. Brazilian healthcare regulations:
- CFM (Conselho Federal de Medicina) resolution 2299/2021 allows telemedicine and digital prescriptions
- Digital signatures must comply with ICP-Brasil (Infraestrutura de Chaves Públicas Brasileira)
- CFM Resolução 2.314/2022 on digital prescription
- The prescription must have hash integrity, digital signature, timestamp

2. Requirements:
- `backend/app/services/receita_digital.py`
- SHA-256 canonical hash of the prescription
- Digital signature and integrity verification against tampering of dosages or dispensed medications
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me design this properly:

**Architecture:**

1. **Pydantic models (v2)** for:
   - `MedicamentoPrescrito` - medication with dosage, posology
   - `PrescricaoDigital` - the prescription itself (patient CNS/CPF, professional, medications, CID-10, CIAP-2, SOAP context)
   - `AssinaturaDigital` - signature envelope
   - `ResultadoVerificacao` - verification result

2. **Canonical hash generation:**
   - Need a canonical JSON serialization (sorted keys, no whitespace, normalized decimal representations) to ensure deterministic hashing
   - SHA-256

3. **Digital signature:**
   - Use `cryptography` library with RSA or ECDSA (P-256)
   - Sign the canonical hash
   - Support key loading from PEM files
   - ICP-Brasil compliance considerations (the actual ICP-Brasil certificates use RSA with specific OIDs; for the service layer we implement the cryptographic primitives with hooks for HSM/token)

4. **Verification:**
   - Recompute canonical hash from received prescription
   - Compare with signed hash
   - Verify signature
   - Detect tampering: specifically what fields changed (dosage, medication)

5. **Tamper detection:**
   - Field-by-field diff to identify what was modified
   - Specific detection for dosage changes and medication substitution

6. **SQLAlchemy 2.0 models:**
   - `PrescricaoDigitalModel` - persistence
   - `RegistroAuditoriaIntegridade` - audit trail

7. **Tests with pytest:**
   - Test canonical hash determinism
   - Test signature/verification roundtrip
   - Test tampering detection (dosage change, medication swap)
   - Test edge cases

Let me think about the canonical serialization carefully. For a prescription:

```json
{
  "versao_esquema": "1.0",
  "id_prescricao": "...",
  "data_emissao": "...",
  "paciente": {"cns": "...", "cpf": "...", "nome": "..."},
  "profissional": {"cns": "...", "cpf": "...", "nome": "...", "registro_conselho": {"tipo": "CRM", "numero": "...", "uf": "..."}},
  "contexto_clinico": {"cid10": [...], "ciap2": [...], "soap": {"subjetivo": ..., "objetivo": ..., "avaliacao": ..., "plano": ...}},
  "medicamentos": [
    {
      "nome_comercial": ...,
      "principio_ativo": ...,
      "apresentacao": ...,
      "dosagem": {"valor": "500", "unidade": "mg"},
      "posologia": {"via": "oral", "frequencia": ..., "duracao_dias": ..., "instrucoes": ...},
      "quantidade_dispensada": ...
    }
  ]
}
```

For canonical JSON:
- Sort keys
- No whitespace (separators=(',', ':'))
- ensure_ascii=False with UTF-8 encoding
- Normalize numbers: use strings for dosage values to avoid float issues, or normalize Decimal to string
- Normalize whitespace in strings (collapse multiple spaces, strip)
- Normalize unicode (NFC)

The dosage value should be a string to avoid "500" vs "500.0" issues. Or normalize Decimal properly.

For the signature, I'll use ECDSA P-256 (fast, small signatures) or RSA-2048/3072. ICP-Brasil typically uses RSA, but for internal service we can support both. Let me use RSA-SHA256 (PKCS1v15) as default since ICP-Brasil A1/A3 certificates are RSA-based, with option for ECDSA.

Actually, let me make it flexible with an enum for algorithm.

Key components:

```python
class ReceitaDigitalService:
    def gerar_hash_canonico(self, prescricao: PrescricaoDigital) -> str
    def assinar(self, prescricao, chave_privada) -> AssinaturaDigital
    def verificar(self, prescricao, assinatura, chave_publica) -> ResultadoVerificacao
    def detectar_adulteracao(self, prescricao_original_hash, prescricao_recebida) -> RelatorioAdulteracao
```

For tampering detection, I need to compare the received prescription against the signed payload. The approach:
1. Recompute hash of received prescription
2. Compare with hash stored in signature
3. If different, do a deep diff between the canonical structures to identify changed fields
4. Classify the tampering type (dosage, medication, patient, etc.)

But wait — to do the diff, we need the original prescription. In practice, the signature only covers the hash. So the service should store the canonical payload (or the original prescription) alongside. For the audit trail, we store the original canonical JSON. When verifying, if hash mismatch, we can diff against the stored original.

Let me design the verification flow:
- `verificar_integridade(prescricao_recebida, assinatura, chave_publica, prescricao_original: Optional[...])` 
- If we have the original, diff and report what changed
- The service also persists verification attempts in audit table

Let me also think about the SQLAlchemy 2.0 model. The task says "crie backend/app/services/receita_digital.py" — the main file is the service. But guidelines mention SQLAlchemy 2.0. I could include the persistence models in the service file or reference them. To keep it self-contained but well-organized, I'll include the SQLAlchemy models in the service file (or a models section), plus the Pydantic schemas.

Actually, for a clean architecture, maybe I should put everything needed in one file as requested, but structure it well:
- Section 1: Pydantic schemas (v2)
- Section 2: Canonical serialization
- Section 3: Hash generation
- Section 4: Digital signature
- Section 5: Verification & tamper detection
- Section 6: SQLAlchemy 2.0 models for persistence/audit
- Section 7: Service class

And a separate test file `backend/tests/services/test_receita_digital.py`.

Let me write the code.

**Pydantic models:**

```python
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
    StrictStr,
    StringConstraints,
)
```

CNS validation: CNS has 15 digits, validated with the standard algorithm (modulo 11). Let me implement it:

CNS validation algorithm:
- Must be 15 digits
- Starting digits: 1, 2, 7, 8, 9 (7,8,9 for provisional)
- Check digit calculation:
  - For CNS starting with 1 or 2: sum = Σ (digit[i] * (15 - i)) for i=0..14, sum % 11 == 0
  - For CNS starting with 7, 8, 9: different algorithm (weights cycle 1-6 repeating... actually the algorithm: multiply digits by weights 15,14,...,2 for first 14 digits, add check digit... let me recall)

Standard CNS validation:
```
def valida_cns(cns):
    cns = cns.strip()
    if len(cns) != 15 or not cns.isdigit():
        return False
    # first char must be 1,2,7,8,9
    if cns[0] not in '12789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

Wait, that's the unified algorithm. Let me verify: For CNS definitive (1 or 2 start):
- pis = "700 0000 0000 000" style... 

The common implementation:
```python
def valida_cns(v):
    """Valida CNS."""
    v = v.replace(" ", "").replace(".", "")
    if len(v) != 15:
        return False
    if v[0] in "0123456789" and v[0] not in "12789":
        return False
    soma = 0
    for i in range(15):
        soma += int(v[i]) * (15 - i)
    return soma % 11 == 0
```

Hmm, actually the standard algorithm for CNS 1/2 series:
- Multiply each of the first 14 digits by weights 15 down to 2, sum, compute dv = 11 - (soma % 11), if dv == 11 then dv = 0... 

Let me just use the well-known implementation:

```python
def _validar_cns(cns: str) -> bool:
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] not in {"1", "2", "7", "8", "9"}:
        return False
    soma = sum(int(digito) * peso for digito, peso in zip(cns, range(15, 0, -1)))
    return soma % 11 == 0
```

This is the widely used Python implementation (from pysus etc.). Let me double check with a known valid CNS: "000 0000 0000 0000" is invalid (starts with 0). A known valid one: 700000000000008? Let me compute: digits 7,0,0,0,0,0,0,0,0,0,0,0,0,0,0 with weights 15..1: 7*15 = 105, rest 0. 105 % 11 = 105 - 99 = 6. Not 0. So that's not valid.

Try 798456118412004? Hard to verify by hand. The algorithm soma % 11 == 0 is the standard one used in many implementations. Actually let me recall the official one:

Official CNS check digit (for 1/2 series, based on PIS):
1. Multiply digits 1-11 by weights 15,14,13,...,5
2. Sum
3. remainder = soma % 11
4. dv = 11 - remainder; if dv in {10, 11}, dv = remainder - 1... no.

Hmm, the official algorithm from DATASUS:
```
soma = (num[0] * 15) + (num[1] * 14) + ... (num[10] * 5)
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0
if dv == 10: invalid
```
Then CNS = first 11 digits + dv + 3 more digits? No wait, CNS is 15 digits: 7 digits + DV + ... hmm.

Actually CNS format: 7 00 0000 0000 000 — first digit 7/8/9 for provisional cards, 1/2 for definitive. The definitive CNS is derived from NIT/PIS.

The commonly used full validation in many Brazilian systems:

```python
def valida_cns(cns):
    cns = cns.strip()
    if len(cns) != 15:
        return False
    if not cns.isdigit():
        return False
    if cns[0] not in ['1','2','7','8','9']:
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if soma % 11 != 0:
        return False
    return True
```

This is the version from the "valida_cns" gist widely circulated. I'll use that. It's the accepted standard implementation.

CPF validation: standard mod-11 algorithm.

```python
def _validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for n in (9, 10):
        soma = sum(int(cpf[i]) * (n + 1 - i % ... 
```

Standard:
```python
def _validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    for i in range(9, 11):
        digito = sum((int(cpf[num]) * ((i + 1) - num)) for num in range(0, i)) % 11
        if digito >= 10:
            digito = 0
        if str(digito) != cpf[i]:
            return False
    return True
```

Hmm wait, weights: for first DV (position 9), weights are 10..2 for digits 0..8: sum(int(cpf[num]) * (10 - num) for num in range(9)) % 11, if >= 10 then 0. For second DV (position 10), weights 11..2 for digits 0..9.

Let me write it cleanly:
```python
def _validar_cpf(cpf: str) -> bool:
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    for posicao in (9, 10):
        peso_inicial = posicao + 1
        soma = sum(int(digitos[i]) * (peso_inicial - i) for i in range(posicao))
        resto = (soma * 10) % 11
        dv = 0 if resto == 10 else resto
        if int(digitos[posicao]) != dv:
            return False
    return True
```

The classic: dv1 = (sum(d[i]*w) * 10) % 11 where w = 10..2. Using (soma * 10) % 11 gives the same as 11 - (soma % 11) except when resto == 0 → dv = 0. Yes, that's the standard trick.

**Canonical JSON:**

```python
def _canonizar_valor(valor: Any) -> Any:
    if isinstance(valor, BaseModel):
        return _canonizar_valor(valor.model_dump(mode="python"))
    if isinstance(valor, dict):
        return {str(k): _canonizar_valor(v) for k, v in sorted(valor.items())}
    if isinstance(valor, (list, tuple)):
        return [_canonizar_valor(item) for item in valor]
    if isinstance(valor, bool) or valor is None:
        return valor
    if isinstance(valor, Decimal):
        return formatar decimal normalized
    if isinstance(valor, float):
        return repr normalized
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str):
        return normalizar texto
    if isinstance(valor, datetime):
        return ISO UTC
    return str(valor)
```

For Decimal normalization: use `format(d, 'f')` then strip trailing zeros but keep at least one decimal? Actually for dosage, better to store as string in the model with a pattern. But to be safe, normalize: `Decimal` → string via quantize? Let me do: normalize to remove trailing zeros: `d = valor.normalize()`, then `format(d, 'f')` to avoid scientific notation. E.g., Decimal("500.00").normalize() → Decimal("5E+2"), format 'f' → "500". Good. Decimal("0.500").normalize() → Decimal("0.5") → "0.5". Good. Decimal("0").normalize() → Decimal("0") → "0". Good.

For strings: NFC unicode normalization, collapse whitespace, strip.

Canonical dump: `json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)` encoded UTF-8.

Hash: SHA-256 of the UTF-8 bytes, hex digest.

**Signature:**

Use `cryptography` library:

```python
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, ec
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from cryptography.exceptions import InvalidSignature
```

Support:
- RSA 2048+ with PSS or PKCS1v15 (ICP-Brasil uses PKCS1v15 with SHA-256 typically for A1; PSS is more modern). I'll implement both, default PKCS1v15 for ICP-Brasil compatibility.
- ECDSA P-256.

Key loading from PEM bytes (with optional password).

Signature envelope:
```python
class AlgoritmoAssinatura(str, Enum):
    RSA_SHA256_PKCS1V15 = "RSA-SHA256-PKCS1v15"
    RSA_SHA256_PSS = "RSA-SHA256-PSS"
    ECDSA_SHA256_P256 = "ECDSA-SHA256-P256"

class AssinaturaDigital(BaseModel):
    algoritmo: AlgoritmoAssinatura
    hash_canonico: str (hex, 64 chars)
    assinatura: str (base64)
    certificado: str | None (PEM base64) — for ICP-Brasil chain
    carimbo_tempo: datetime | None — TSA timestamp
    serie_certificado / emissor: for ICP-Brasil metadata
``