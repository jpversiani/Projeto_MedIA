The user wants me to create a FastAPI module for pharmaceutical dispensing and prescription fulfillment (baixa de receita) for the MedIA project, related to SUS (Brazilian Unified Health System).

Requirements:
- File: `backend/app/api/v1/farmacia.py`
- Routes:
  - `POST /dispensacao/consultar` — validates QR Code/hash of the prescription
  - `POST /dispensacao/confirmar` — registers total or partial (fracionada) dispensing of medications in SUS
- Pydantic v2 and SQLAlchemy
- Python 3.12, strict typing, SQLAlchemy 2.0 style
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

I should produce:
1. The main API file `backend/app/api/v1/farmacia.py`
2. Supporting models/schemas (probably need to reference or create them — I'll create the schemas in the same file or reference a schemas module; better to structure it well)
3. SQLAlchemy models (I should probably show the models needed, or assume they exist — but to be safe and complete, I'll include the models in a models file or inline reference). The task says "crie backend/app/api/v1/farmacia.py" — the main deliverable is that file. But for it to work, I need schemas and models. I'll provide:
   - `backend/app/api/v1/farmacia.py` (main)
   - `backend/app/schemas/farmacia.py` (Pydantic v2 schemas)
   - `backend/app/models/farmacia.py` (SQLAlchemy 2.0 models)
   - `backend/tests/api/v1/test_farmacia.py` (pytest tests)

Let me think about the domain:

**Dispensação Farmacêutica no SUS:**
- A prescription (receita) is issued by a professional (médico, dentista, etc.) with CRM/COREN etc.
- Patient identified by CNS (Cartão Nacional de Saúde) or CPF
- Prescription has medications (itens) with: nome do medicamento, apresentação, dose, quantidade, posologia
- QR Code contains a hash (e.g., HMAC-SHA256 or UUID) that identifies the receita
- Dispensing can be:
  - Total (baixa total): all items dispensed in full
  - Fracionada (parcial): some items dispensed partially — remaining quantities stay available for later dispensing
- Validation: receita exists, is valid (not expired — receitas have validity, typically 30 days for controlled, 90 days simple), not already fully dispensed, patient matches (CNS), professional valid
- Registration: record dispensação with items dispensed, quantities, pharmacist responsible (CRF — Conselho Regional de Farmácia), date, unit (UBS/farmácia municipal)
- For controlled medications (Portaria 344/1998 — lista A1, B1, etc.), special rules: retain receita, etc. I can include a flag `controlado` and maybe require retention.

**Data model:**

`Receita` (prescription):
- id (UUID)
- codigo_hash (unique) — the hash encoded in QR Code
- paciente_id / paciente_cns / paciente_cpf
- profissional_id, profissional_registro (CRM), profissional_uf_conselho
- cid10 (optional), ciap2 (optional — APS)
- data_emissao, data_validade
- status: EMITIDA, PARCIALMENTE_DISPENSADA, DISPENSADA, EXPIRADA, CANCELADA
- unidade_saude (CNES)
- observacoes / plano (SOAP — the "P" of SOAP is the plan, which includes the prescription)

`ReceitaItem`:
- id
- receita_id
- medicamento_nome, medicamento_id (catalog), apresentacao, concentracao
- quantidade_prescrita
- quantidade_dispensada (accumulated)
- posologia
- via_administracao
- controlado (bool), lista_controlada (e.g., "A1", "B1")

`Dispensacao`:
- id
- receita_id
- tipo: TOTAL | FRACIONADA
- farmacista_nome, farmacista_crf, farmacista_uf
- cnes_unidade
- data_dispensacao
- observacoes

`DispensacaoItem`:
- id
- dispensacao_id
- receita_item_id
- quantidade_dispensada

**Endpoints:**

1. `POST /dispensacao/consultar`
   - Request: `{ "codigo_qr": "..." }` or `{ "hash": "..." }` — validate QR code/hash. Maybe the QR contains a signed payload. I'll accept `codigo_hash` (string) and optionally `cns_farmaceutico`? Actually simpler: the QR contains the hash. Validate: exists, not expired, not fully dispensed, not cancelled. Return prescription details: patient (masked?), items with prescribed vs dispensed quantities, remaining, validity, status, whether controlled.
   - Response: dados da receita + itens + status de dispensação + validade.

2. `POST /dispensacao/confirmar`
   - Request: `{ "codigo_hash": "...", "tipo": "TOTAL"|"FRACIONADA", "itens": [{"receita_item_id": ..., "quantidade": ...}], "farmacista": {"nome", "crf", "uf"}, "cnes_unidade": ..., "observacoes": ... }`
   - Validation: hash valid, receita not expired/cancelled, quantities > 0 and <= remaining, for TOTAL: all items fully dispensed; for FRACIONADA: at least one item partial or subset.
   - Business rules:
     - TOTAL: all items must be dispensed in full remaining quantity → status becomes DISPENSADA
     - FRACIONADA: quantities can be partial → status becomes PARCIALMENTE_DISPENSADA; if after this dispensing all items are complete, status becomes DISPENSADA
     - Controlled meds: maybe require `receita_retida` flag for certain lists? I can add optional field `receita_retida: bool` for controlled. Keep it simple but present.
   - Response: dispensação registrada with id, status atualizado da receita, itens restantes.

**Security/compliance considerations:**
- LGPD: mask patient data in responses (e.g., CPF partially masked). CNS can be shown since it's needed for dispensing, but I'll mask partially maybe. Actually the pharmacist needs to confirm patient identity — showing full CNS is reasonable in this context. I'll show CNS but mask CPF.
- Audit: log entries.
- Idempotency? Could add but keep scope.

**Pydantic v2 specifics:**
- Use `BaseModel`, `Field`, `field_validator`, `model_validator`, `ConfigDict(from_attributes=True)`
- Strict typing: `Annotated[str, Field(...)]`
- Use `StrEnum` (Python 3.12) for enums — nice touch for Python 3.12: `from enum import StrEnum`

**SQLAlchemy 2.0 specifics:**
- `Mapped`, `mapped_column`, `DeclarativeBase`
- `relationship` with typed lists
- Use `Enum` column with native_enum or String + validation. I'll use String with enum values to avoid migration issues, or use SAEnum. I'll use `mapped_column(SAEnum(...))`? To keep it portable, use String(20) and validate in Pydantic. Hmm, better to use SQLAlchemy Enum with values_callable. I'll use String for simplicity and robustness, validated at schema level. Actually let me use `sqlalchemy.Enum` with native_enum=False for portability. I'll go with String + CheckConstraint maybe. Keep it clean: String columns with Pydantic validation.

**Dependencies:**
- `get_db` dependency (Session) — assume exists in `app.core.database` or `app.db.session`. I'll define imports from `app.db.session` with `get_db`. Since this is a module in a larger project, I'll assume `backend/app/core/database.py` provides `get_db`. I'll write it referencing `app.core.deps.get_db` and note it. To make the answer self-contained and testable, maybe I should include a minimal `deps` snippet in the test file with overrides. I'll create the tests with dependency overrides so they're self-contained.

Let me design the structure:

```
backend/
  app/
    api/
      v1/
        farmacia.py
    models/
      farmacia.py
    schemas/
      farmacia.py
    db/
      session.py (assumed: get_db)
  tests/
    api/v1/
      test_farmacia.py
```

I'll write:

1. `app/models/farmacia.py` — SQLAlchemy 2.0 models: ReceitaModel, ReceitaItemModel, DispensacaoModel, DispensacaoItemModel.
2. `app/schemas/farmacia.py` — Pydantic v2 schemas.
3. `app/api/v1/farmacia.py` — router with the two endpoints + service functions.
4. `tests/api/v1/test_farmacia.py` — pytest with in-memory SQLite, TestClient, fixtures, covering: consulta OK, hash inexistente (404), receita expirada (422/409), receita cancelada, já dispensada, confirmação total, fracionada, fracionada até completar, quantidade excedente (422), quantidade zero/negativa, farmacista sem CRF válido, item inexistente na receita, tipo TOTAL com itens faltando, LGPD masking, etc.

Let me think about error handling: use domain exceptions mapped to HTTPException with proper status codes:
- 404: receita não encontrada
- 409: conflito (já dispensada, cancelada)
- 422: validação (expirada, quantidade inválida, dados farmacista inválidos)

Or use 422 for business rule violations. I'll use:
- 404 NOT_FOUND
- 409 CONFLICT (já totalmente dispensada, cancelada)
- 422 UNPROCESSABLE (expirada, quantidade excede restante, tipo TOTAL incompleto)

**CNS validation:** CNS has a check digit algorithm (validação do CNS). I can implement it — nice compliance touch. CNS: 15 digits, starts with 1, 2, 7, 8, or 9. Algorithm: sum = Σ digit[i] * (15 - i); if sum % 11 == 0 → valid. Let me recall: For CNS validation:
- Must have 15 digits
- First digits: 1, 2, 7, 8, 9 (1/2 permanent; 7/8/9 provisional)
- Algorithm: multiply digits by weights 15,14,13,...,2 (from left), sum; if sum % 11 == 0, valid; else invalid.

Yes: soma = d1*15 + d2*14 + ... + d15*2? Wait, 15 digits with weights 15 down to 1? Let me verify: The standard algorithm: 
```
soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
if soma % 11 == 0: valid
```
Weights: 15, 14, 13, ..., 1. Hmm, some implementations use weights 15..1 (i.e., 15 - i for i in 0..14 gives 15..1). Let me check with a known valid CNS: "116 8094 4626 0009"? I'm not 100% sure of a test vector. Common test: CNS "700000000000000"? Let's compute: digits 7,0,0,...: soma = 7*15 = 105; 105 % 11 = 105 - 99 = 6 ≠ 0. Not valid.

Known valid example from documentation: "116809446260009"? Compute: digits: 1,1,6,8,0,9,4,4,6,2,6,0,0,0,9. Weights 15..1:
1*15=15
1*14=14 → 29
6*13=78 → 107
8*12=96 → 203
0*11=0 → 203
9*10=90 → 293
4*9=36 → 329
4*8=32 → 361
6*7=42 → 403
2*6=12 → 415
6*5=30 → 445
0*4=0 → 445
0*3=0 → 445
0*2=0 → 445
9*1=9 → 454
454 % 11 = 454 - 44*11=484? No, 44*11=484 > 454. 41*11=451. 454-451=3 ≠ 0. So that's not valid by this algorithm. Hmm.

Maybe the weights are 15..1 but the check is different. Let me look at the official algorithm (from DATASUS):

```
Para CNS com 15 dígitos:
soma = soma dos produtos dos dígitos pelos pesos 15,14,13,...,1 (da esquerda para direita)
Se soma % 11 == 0 → válido
```

Actually I recall the pseudo-code:
```
rotina valida_cns(vCNS)
  vSoma = 0
  for i = 0 to 14:
     vSoma = vSoma + (vCNS[i] * (15 - i))
  vResto = vSoma mod 11
  if vResto != 0 then invalid
```
And a test vector: "116 8094 4626 0009" is often cited as valid. Let me recompute carefully. CNS: 1 1 6 8 0 9 4 4 6 2 6 0 0 0 9? Hmm wait, maybe the number is "116809446260004" or similar. Let me instead find a vector I can verify.

Alternative known valid CNS examples: "700000000001789"? Not sure.

Let me just trust the algorithm and generate a valid CNS for tests programmatically. Actually, for tests, I can compute a valid CNS: take 14 digits and compute the 15th? The check digit is the last digit, and the algorithm validates the whole number. To generate: choose first 14 digits, then find d15 such that soma % 11 == 0. soma_partial = Σ_{i=0}^{13} d_i * (15-i). Then d15 * 1 must make total % 11 == 0 → d15 = (11 - (soma_partial % 11)) % 11. But d15 must be 0-9. If (11 - r) % 11 == 10, then no valid d15 — need to adjust. For test purposes, I can search over first-14-digit candidates until d15 ∈ 0..9. Simpler: in tests, use a helper function that generates a valid CNS by brute force over a counter.

Actually, let me verify the algorithm with a real known-valid CNS. Known example from many Brazilian validation libs: "116.8094.4626.0009" — hmm I computed 454, remainder 3. Maybe weights are 15..2 (14 weights for 15 digits?) No.

Let me check another source: The algorithm from "Cartão Nacional de Saúde" validation:

```
function validaCNS(vCNS) {
  // vCNS must have 15 digits, all numeric (or starts with 7/8/9 and can have letters? no)
  let soma = 0;
  for (let i = 0; i < 15; i++) {
    soma += parseInt(vCNS[i]) * (15 - i);
  }
  return soma % 11 === 0;
}
```

Test vector often used: "8980010490012"? That's 13 digits. Hmm.

Let me try "7980010490012" — no.

Let me try to construct: CNS starting with 7: "700000000000000" → 105 % 11 = 6. "70000000000000X": soma = 105 + X*1. Need 105 + X ≡ 0 mod 11 → X ≡ -105 mod 11. 105 mod 11 = 6 (99=9*11, 105-99=6). So X = 5. CNS "700000000000005" → soma = 105 + 5 = 110, 110 % 11 = 0. Valid! So "700000000000005" is a valid CNS by this algorithm. 

But wait — is the first digit constraint 1,2,7,8,9? Yes. 7 is fine (provisional). So for tests I can use "700000000000005" or generate others. Let me double check: digits: 7 followed by thirteen 0s and then 5: that's 15 digits: 7,0×13,5. Weights: 15 for the 7, then 14,13,...,2 for the thirteen zeros (all 0), then 1 for the final 5. soma = 105 + 0 + 5 = 110. 110/11 = 10 → remainder 0. Valid. 

Also "8980010490012..." whatever — I'll use the computed one.

CPF validation: standard check-digit algorithm. I'll implement a validator for CPF too (masking + validation). For tests, use a valid CPF like "529.982.247.25" (known valid test CPF). Yes, 52998224725 is a commonly cited valid CPF.

**QR Code/hash:** The receita has a `codigo_hash` — e.g., SHA-256 HMAC of the receita id + secret, or a UUID. The QR encodes something like `media://receita/<hash>` or just the hash. I'll accept both: the endpoint receives `codigo_qr` string; we parse it — if it matches a URI pattern, extract hash; else use raw. Keep simple: field `codigo_qr: str`, we normalize by stripping a prefix if present. I'll implement a small parser: patterns like `MEDIA-RECEITA://<hash>` or plain hash (64 hex chars or UUID). Let me define: hash is a 64-char hex (sha256). The QR content may be `mediasus://