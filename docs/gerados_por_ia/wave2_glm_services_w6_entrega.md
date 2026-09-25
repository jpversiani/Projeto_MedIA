The user wants me to create a digital prescription and medical certificate service for the MedIA project. Let me analyze the requirements:

1. Create `backend/app/services/receita_digital.py` with:
   - `gerar_receita(paciente, profissional, medicamentos, orientacoes)` -> dict with hash and QR Code payload
   - `validar_receita(hash_documento)` -> bool
   - `emitir_atestado(paciente, profissional, dias_afastamento, cid10)` -> dict

2. Architecture guidelines:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me design this properly:

**Key components:**

1. **Pydantic models (v2)** for:
   - Paciente (with CNS, CPF validation)
   - Profissional (with CRM/COREN, UF)
   - Medicamento (with dosage, posology)
   - Receita (document)
   - Atestado (document)

2. **Validators:**
   - CNS validation (SUS card - has a specific algorithm)
   - CPF validation (check digits algorithm)
   - CID-10 validation (format)
   - CRM format validation

3. **Hash generation:**
   - SHA-256 of canonical document JSON
   - QR Code payload generation

4. **Validation:**
   - `validar_receita(hash_documento)` - needs to check against stored hashes (database) or recompute

Let me think about the CNS validation algorithm (Brazilian SUS card):
- CNS can have 15 digits
- Starting with 1, 2 (definitive), 7, 8, 9 (provisional)
- Algorithm: sum of digits multiplied by weights [15,14,13,12,11,10,9,8,7,6,5,4,3,2,1] must be divisible by 11

Actually the CNS validation algorithm:
```
For CNS starting with 1, 2, 7, 8, 9:
- Multiply each of the 15 digits by weights 15,14,13,...,1
- Sum all products
- Sum must be divisible by 11
```

CPF validation:
- Standard check digit algorithm with weights 10..2 and 11..2

CID-10 format: Letter followed by 2 digits, optionally with dot and more digits (e.g., J45, E11.9, A09.X)

Let me structure the code:

```
backend/app/services/receita_digital.py
```

But I should also provide supporting files since the task says "complete and executable":
- `backend/app/schemas/receita_digital.py` - Pydantic schemas
- `backend/app/models/receita_digital.py` - SQLAlchemy models
- `backend/app/core/security.py` or hash utilities
- Tests: `backend/tests/test_receita_digital.py`

The main task is the service file, but for it to be complete and executable, I need the schemas and models. Let me create:

1. `backend/app/schemas/receita_digital.py` - Pydantic v2 schemas with strict typing
2. `backend/app/models/receita_digital.py` - SQLAlchemy 2.0 models
3. `backend/app/services/receita_digital.py` - Main service
4. `backend/tests/test_receita_digital.py` - pytest tests

Let me write the code:

**Schemas (Pydantic v2):**

```python
# backend/app/schemas/receita_digital.py
from __future__ import annotations

import re
from datetime import date, datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class UFBrasil(str, Enum):
    AC = "AC"
    AL = "AL"
    ...


def _validar_cpf(cpf: str) -> str:
    ...

def _validar_cns(cns: str) -> str:
    ...


class PacienteSchema(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)
    
    nome: Annotated[str, Field(min_length=3, max_length=150)]
    cpf: Annotated[str, Field(pattern=r"^\d{11}$")]
    cns: Annotated[str, Field(pattern=r"^\d{15}$")]
    data_nascimento: date
    sexo: Literal["M", "F", "I"]
    ...


class MedicamentoSchema(BaseModel):
    nome_comercial: str
    principio_ativo: str
    apresentacao: str  # e.g., "comprimido 500mg"
    posologia: str
    quantidade: int
    uso: Literal["contínuo", "temporário"]
    ...


class ProfissionalSchema(BaseModel):
    nome: str
    registro_conselho: str  # CRM/COREN
    uf_conselho: UFBrasil
    especialidade: str
    ...


class ReceitaSchema(BaseModel):
    ...


class AtestadoSchema(BaseModel):
    ...
```

**Service:**

```python
# backend/app/services/receita_digital.py
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

class ReceitaDigitalService:
    def gerar_receita(self, paciente, profissional, medicamentos, orientacoes) -> dict:
        # Build canonical document
        # Compute SHA-256 hash
        # Generate QR Code payload
        # Persist to DB
        ...
    
    def validar_receita(self, hash_documento: str) -> bool:
        # Look up in DB, check not revoked, check hash integrity
        ...
    
    def emitir_atestado(self, paciente, profissional, dias_afastamento, cid10) -> dict:
        ...
```

For the QR Code payload, a common pattern is a compact string or JSON with:
- Document type
- Document ID
- Hash (or first N chars)
- Validation URL

Something like:
```
https://valida.media.saude.gov.br/receita/{id}?h={hash[:16]}
```

Or a structured payload:
```json
{
  "t": "R",  # tipo
  "id": "...",
  "h": "...",
  "e": "2025-01-01"  # expiração
}
```

For CFM compliance, prescriptions must contain:
- Patient identification (name, and ideally CPF/CNS)
- Prescriber identification (name, professional registry CRM, UF)
- Medication name, dosage, quantity, posology
- Date and place of emission
- Signature (digital in this case)

For atestados (CFM Resolution 1.658/2002 and 2.207/2022):
- Patient identification
- CID (patient can request omission, but here it's required)
- Days of absence
- Date of emission
- Professional identification and signature

Let me also think about the database model:

```python
# backend/app/models/receita_digital.py
from sqlalchemy import String, ForeignKey, DateTime, Enum, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
```

SQLAlchemy 2.0 style with `Mapped` and `mapped_column`.

For the document storage, I'll create a `DocumentoDigital` table that stores:
- id (UUID)
- tipo (RECEITA / ATESTADO)
- hash_sha256
- payload_json (canonical JSON)
- qr_code_payload
- data_emissao
- data_expiracao
- revogado (bool)
- paciente_cpf, paciente_cns
- profissional_registro

The `validar_receita` function should:
1. Normalize hash (lowercase, strip)
2. Look up in DB
3. If not found -> False
4. If found, recompute hash from stored payload to verify integrity (tamper detection)
5. Check not revoked
6. Check not expired (receitas have validity - CFM: receita de controle especial has specific validity; simple receita typically valid, let's say 180 days default)

Let me think about hash computation. Canonical JSON serialization:

```python
def _canonical_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def _hash_documento(payload: dict) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
```

For the QR Code payload, I'll generate a compact base64url-encoded JSON or a URL. Let me do both: a URL for scanning plus embedded data. Actually, let me make it a compact pipe-delimited or JSON payload:

```python
qr_payload = f"MEDIA|RECEITA|{id}|{hash[:32]}|{data_emissao:%Y%m%d}"
```

Or better, a JSON with versioning:

```python
{
    "v": 1,
    "tipo": "RECEITA",
    "id": str(documento_id),
    "hash": hash_completo,
    "url": f"https://valida.mediasaude.gov.br/api/v1/receitas/{documento_id}"
}
```

Hmm, for QR codes, shorter is better. Let me use a compact format but include the full hash for offline validation capability. Actually a good design: QR contains the full hash so validators can check offline against a published hash list, plus a URL for online validation.

Let me write a `QRPayload` model:

```python
class QRPayload(BaseModel):
    versao: int = 1
    tipo: Literal["RECEITA", "ATESTADO"]
    documento_id: str
    hash_sha256: str
    validacao_url: str
```

And serialize compactly.

Now, about the service architecture — should it be a class or module-level functions? The task specifies function signatures:
- `gerar_receita(paciente, profissional, medicamentos, orientacoes) -> dict`
- `validar_receita(hash_documento) -> bool`
- `emitir_atestado(paciente, profissional, dias_afastamento, cid10) -> dict`

I'll implement a `ReceitaDigitalService` class with these methods, and also expose module-level convenience functions that use a default session. Actually, for testability and dependency injection, a class with a session parameter is better. Let me do:

```python
class ReceitaDigitalService:
    def __init__(self, session: Session):
        self._session = session
```

And the methods accept Pydantic models or dicts. The signature says `paciente, profissional, medicamentos, orientacoes` — I'll accept Pydantic schemas (with validation) and also handle dicts gracefully via `TypeAdapter`/model_validate.

Let me now think about CID-10 validation:
- Format: `[A-Z]\d{2}(\.\d{1,2})?` — e.g., "J45", "E11.9", "K35.8"
- Also validate the letter is a valid CID-10 chapter letter: A-R and S-Z (excluding some). CID-10 chapters: A-B (infectious), C-D (neoplasms... actually C00-D48), D (D50-D89 blood), E (endocrine), F (mental), G (nervous), H (eye/ear), I (circulatory), J (respiratory), K (digestive), L (skin), M (musculoskeletal), N (genitourinary), O (pregnancy), P (perinatal), Q (congenital), R (symptoms), S-T (injury), U (special codes), V-Y (external causes), Z (factors).

So letters A-Z are all valid in CID-10. I'll validate format with regex and optionally check against a small set of common codes... No, a full CID-10 table is too large. I'll validate format strictly and document that full table validation requires the DATASUS reference table. Maybe include a minimal set of the most common codes for sanity check? That could be nice for APS context (hipertensão I10, diabetes E11, etc.) but might cause false rejections. I'll do format validation only, with a comment.

Actually, let me include an optional curated list of common APS codes and validate the chapter letter. Format validation: `^[A-Z]\d{2}(\.\d{1,2})?$` — but CID-10 also has forms like "J45.0". Also "A09.X" exists in Brazilian tabulation? The Brazilian CID-10 uses "X" as placeholder in some codes (e.g., A09.X, J06.9). Yes! The Brazilian TAB CID-10 (DATASUS) uses X for unspecified 4th character, e.g., "A09.X", "B34.9"... So the regex should allow X as the 4th character: `^[A-Z]\d{2}(\.[0-9X]{1,2})?$`.

For CIAP-2 mention — the guidelines say standards include CIAP-2. CIAP-2 codes are letter + 2 digits (e.g., K86 hypertension, F15 depressive). I can add an optional `ciap2` field on the atestados/receitas for APS context. Let me add CIAP-2 validation (regex `^[A-Z]\d{2}$`) as an optional field. That shows compliance with the guideline.

SOAP method — the guidelines mention SOAP (Subjective, Objective, Assessment, Plan). I can include an optional `soap` structure in the clinical context of the document. Let me add an optional `ContextoClinico` schema with SOAP fields. That demonstrates compliance without overcomplicating.

CNS validation algorithm (official from DATASUS):

```python
def validar_cns(cns: str) -> bool:
    cns = re.sub(r"\D", "", cns)
    if len(cns) != 15:
        return False
    if cns[0] not in "123789":
        return False
    # For 1,2: standard algorithm
    # For 7,8,9: same algorithm
    soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
    return soma % 11 == 0
```

Wait, the actual algorithm: weights from 15 down to 1 for 15 digits. Sum must be divisible by 11. Let me verify with a known valid CNS: "000 0000 0000 0000"? Not valid. Known example: CNS "700 0000 0000 0000"? Let me compute a valid one.

Actually the official algorithm from DATASUS:

```
Para CNS com 15 dígitos:
- Os números devem começar com 1, 2, 7, 8 ou 9
- Multiplique cada dígito pelo peso correspondente (15, 14, 13, ..., 1)
- Some os resultados
- O resultado deve ser divisível por 11
```

Let me construct a valid CNS: digits d1..d15 with d1=1. Sum = Σ di * (16 - i). For it to be divisible by 11.

Take "111 1111 1111 1111": sum = 1 * (15+14+...+1) = 120. 120 % 11 = 10. Not valid.

Let me compute one properly. Weights: 15,14,13,12,11,10,9,8,7,6,5,4,3,2,1.

Try CNS = "100 0000 0000 0000" + check digit adjustments. Sum = 1*15 = 15. Need sum % 11 == 0. We can adjust last digits. Let's make "100 0000 0000 0004": sum = 15 + 4*1 = 19. No.

Let me just compute: we need sum ≡ 0 mod 11. With d1=1 (weight 15), contribution 15. We can set d15 (weight 1) to make total divisible: 15 + x ≡ 0 mod 11 → x ≡ -15 ≡ -4 ≡ 7 mod 11. So d15 = 7: CNS "100 0000 0000 0007" → sum = 15 + 7 = 22, divisible by 11. 

So "100000000000007" is a valid CNS by the algorithm. Good, I can use that in tests.

Another: "898 6782 3192 0004"? I recall test CNS examples like "898 6782 3192 0041"... Let me not guess; I'll generate valid ones in tests using the same algorithm or use the constructed one.

For provisional starting with 7: "700 0000 0000 000X": sum = 7*15 = 105. 105 % 11 = 6 (105 = 99 + 6). Need d15: 105 + x ≡ 0 mod 11 → x ≡ 6 mod 11 → x = 6. So "700000000000006" is valid.

CPF validation algorithm:

```python
def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    # First check digit
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    dv1 = (soma * 10) % 11 % 10
    # Second check digit
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    dv2 = (soma * 10) % 11 % 10
    return cpf[9] == str(dv1) and cpf[10] == str(dv2)
```

Standard: dv1 = (sum of first 9 digits * weights 10..2) * 10 % 11 % 10. dv2 = (sum of first 10 digits * weights 11..2) * 10 % 11 % 10.

Valid test CPF: "529.982.247-25" is a well-known valid test CPF. Let me verify: digits 529982247, dv 25.

dv1: weights 10..2 on 5,2,9,9,8,2,2,4,7:
5*10=50, 2*9=18, 9*8=72, 9*7=63, 8*6=48, 2*5