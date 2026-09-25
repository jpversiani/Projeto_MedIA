The user wants me to create a FastAPI backend module for pharmaceutical dispensing and prescription fulfillment (baixa de receita) for the MedIA project, targeting the Brazilian SUS (Unified Health System).

Key requirements:
1. File: `backend/app/api/v1/farmacia.py`
2. Routes:
   - `POST /dispensacao/consultar` - validates QR Code/hash of prescription
   - `POST /dispensacao/confirmar` - registers total or partial dispensing of medications in SUS
3. Pydantic v2 and SQLAlchemy
4. Python 3.12, strict typing
5. SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
6. Full compliance and automated test coverage with pytest

Since this is a coder agent task, I should provide complete, executable code. I need to think about what files to create:

1. `backend/app/api/v1/farmacia.py` - main router
2. Schemas (Pydantic v2) - probably `backend/app/schemas/farmacia.py`
3. Models (SQLAlchemy 2.0) - probably `backend/app/models/farmacia.py` (or assume existing models)
4. Service layer - `backend/app/services/farmacia_service.py`
5. Tests - `backend/tests/test_farmacia.py`
6. Maybe database setup, security dependencies

Since the task says "crie backend/app/api/v1/farmacia.py", the main deliverable is that file, but to make it complete and executable, I should provide the supporting files too (schemas, models, service, tests). Let me design a coherent structure.

Let me think about the domain:

**Dispensação Farmacêutica no SUS:**
- A prescription (receita) is issued by a professional, has a QR Code/hash for validation
- Patient identified by CNS (Cartão Nacional de Saúde) or CPF
- Medications with CID-10 diagnosis codes
- Dispensing can be total (baixa total) or partial/fracionada (baixa fracionada)
- Need to track: quantity prescribed vs quantity dispensed, remaining balance
- Prescription validity (validade da receita)
- Audit trail (who dispensed, when, which pharmacy unit - CNES)

**Data model:**

`Receita` (Prescription):
- id (UUID)
- codigo_hash (unique hash for QR code validation) - e.g., SHA-256
- paciente_id / paciente_cns / paciente_cpf
- profissional_id (prescriber)
- unidade_cnes (CNES of the health unit)
- data_emissao
- data_validade
- status: EMITIDA, PARCIALMENTE_DISPENSADA, DISPENSADA, CANCELADA, EXPIRADA, VENCIDA
- cid10_principal (diagnosis)
- ciap2 (episode code for APS)
- itens (relationship to items)

`ReceitaItem` (Prescription item):
- id
- receita_id
- medicamento (nome, catalogo id - could reference CATMAT or local catalog)
- descricao
- apresentacao (e.g., "comprimido 500mg")
- quantidade_prescrita
- quantidade_dispensada (accumulated)
- quantidade_solicitada? For partial dispensing
- posologia (SOAP - could be part of prescription text)
- via_administracao
- status item: PENDENTE, PARCIAL, ATENDIDO

`Dispensacao` (Dispensing event):
- id
- receita_id
- farmaceutico_id (who dispensed)
- unidade_cnes (pharmacy CNES)
- data_dispensacao
- tipo: TOTAL, FRACIONADA
- observacoes
- itens (relationship)

`DispensacaoItem`:
- id
- dispensacao_id
- receita_item_id
- quantidade_dispensada
- lote (batch)
- validade_lote

**Business rules:**
1. Consultar: given hash/QR code, find prescription, validate:
   - exists
   - not expired (data_validade >= today)
   - not cancelled
   - not fully dispensed
   - return remaining quantities per item
2. Confirmar: given hash + items with quantities:
   - validate same as above
   - each item quantity > 0 and <= remaining
   - if all items fully dispensed → status DISPENSADA
   - if some → PARCIALMENTE_DISPENSADA
   - create Dispensacao record with tipo TOTAL or FRACIONADA
   - idempotency? Maybe a `idempotency_key` to avoid double-dispensing. Good practice.
   - Audit: farmaceutico CNS/CPF, CNES

**Security/Auth:**
- Professional identified by CNS or CPF
- Maybe a dependency `get_current_farmaceutico` — but to keep it self-contained, I'll accept credentials in the request or use a simple dependency. For a complete executable example, I could include a simple OAuth2-style dependency but that requires more infra. Better: include a dependency that reads a JWT or header, with a stub implementation that can be replaced. Hmm, "conformidade total" — let me include a simple auth dependency that validates a bearer token (could be stubbed/overridable in tests).

Actually, to keep it focused and executable, I'll create:
- `backend/app/core/config.py` (settings)
- `backend/app/core/database.py` (engine, session)
- `backend/app/models/` — receita models
- `backend/app/schemas/farmacia.py` — Pydantic v2 schemas
- `backend/app/services/farmacia_service.py` — business logic
- `backend/app/api/v1/farmacia.py` — router
- `backend/app/api/v1/__init__.py` maybe
- `backend/app/main.py` — app factory
- `backend/tests/conftest.py` — fixtures with in-memory SQLite
- `backend/tests/test_farmacia.py` — pytest tests

Also validators for CNS and CPF (Brazilian check digit algorithms) — that's important for SUS compliance. I'll implement CNS and CPF validation functions in `backend/app/utils/documentos.py` or within schemas.

CNS validation algorithm (Cartão Nacional de Saúde):
- CNS must be 15 digits
- Starting with 1, 2, 7, 8, or 9 (1/2 definitive, 7/8/9 provisional)
- Algorithm: sum = sum over i of digit[i] * (15 - i); if sum % 11 == 0 valid... Actually the algorithm: 
  - For CNS starting with 1,2: peso starting at 15 down to 2 for the first 15 digits? Let me recall properly.

The CNS validation (from DATASUS):
```
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15: return False
    if cns[0] not in '123789': return False
    # For 1/2 starting: 
    soma = 0
    for i in range(15):
        soma += int(cns[i]) * (15 - i)
    return soma % 11 == 0
```
Wait, that's not quite right. The official algorithm:

For CNS with 15 digits:
- If first char is '1' or '2': use the "Pis/Pasep" style check: multiply digits by weights 15,14,13,...,2 (for 14 digits?) Hmm.

Let me recall the actual algorithm from DATASUS documentation:

```
function validaCNS(valeur) {
  // 15 digits
  if (valeur.trim().length != 15) return false;
  // only numbers OR starting with 7/8/9 may contain letters? Actually provisory CNS can have letters in some formats... The classic: numbers only.
  ...
  soma = 0;
  for i = 0..14: soma += parseInt(valeur[i]) * (15 - i)
  if (soma % 11 == 0) return true else... 
```

Hmm, actually the standard algorithm:

```
function validaCNS(valeur) {
    if (valeur.trim().length != 15) { return false; }
    soma = 0;
    dv = 0;
    pis = new String;
    resultado = new String;
    resto = 0;
    if ((valeur.substr(0,1) == "7") || (valeur.substr(0,1) == "8") || (valeur.substr(0,1) == "9")) {
        pis = valeur.substr(0, 11);
        soma = ((Number(pis.substr(0,1)) * 15) + (Number(pis.substr(1,1)) * 14) + (Number(pis.substr(2,1)) * 13) +
                (Number(pis.substr(3,1)) * 12) + (Number(pis.substr(4,1)) * 11) + (Number(pis.substr(5,1)) * 10) +
                (Number(pis.substr(6,1)) * 9) + (Number(pis.substr(7,1)) * 8) + (Number(pis.substr(8,1)) * 7) +
                (Number(pis.substr(9,1)) * 6) + (Number(pis.substr(10,1)) * 5));
        resto = soma % 11;
        dv = 11 - resto;
        if (dv == 11) dv = 0;
        if (dv == 10) {
            soma = 2 + (Number(pis.substr(0,1)) * 15) + ... (same weights) 
            resto = soma % 11;
            dv = 11 - resto;
            resultado = pis + ".000." + dv + "-" + valeur.substr(12,2);
        } else {
            resultado = pis + "." + String(dv) + valeur.substr(11,2) + "-" + valeur.substr(13,2)... 
        }
        ...
    } else {
        // 1 or 2
        soma = (Number(valeur.substr(0,1)) * 15) + (Number(valeur.substr(1,1)) * 14) + ... (Number(valeur.substr(13,1)) * 2);
        resto = soma % 11;
        if (resto == 0) { return true; } else { return false; }
    }
}
```

So for CNS starting with 1 or 2: weighted sum with weights 15 down to 2 over all 15 digits, valid if sum % 11 == 0.

For CNS starting with 7, 8, 9 (provisory): different algorithm with DV computation. To keep it simpler, I can implement both:

For 7/8/9:
- Take first 11 digits, compute soma with weights 15..5
- resto = soma % 11; dv = 11 - resto; if dv == 11: dv = 0; if dv == 10: recompute with soma+2 and dv = 11 - resto... then check digits 12,13,14 match "000" + dv? Actually the format is: pis(11) + dv + 3 more digits? The full 15-digit provisory CNS: first 11 digits + DV + 3 digits where the 3 digits... hmm.

Actually for provisory CNS (7/8/9), the format is: 11 digits (like PIS) + 1 DV + 3 digits. The check: compute dv from first 11 digits; the 12th digit must equal dv; the last 3 digits... In the JS above, when dv==10, resultado = pis + ".000." + dv + "-" + valeur.substr(12,2) — meaning digits 12-14 are "000"? Hmm, this is getting complicated. 

Simplification: Many implementations validate CNS as:
- 15 digits, all numeric
- first digit in {1,2,7,8,9}
- For 1/2: weighted sum (15..2) % 11 == 0
- For 7/8/9: compute dv from first 11 digits (weights 15..5), dv = 11 - resto (if 11 → 0, if 10 → recompute with +2), then check that digits[11] == dv and digits[12:15] == "000"? No wait...

Let me look at a known Python implementation:

```python
def valida_cns(cns: str) -> bool:
    cns = ''.join(ch for ch in cns if ch.isdigit())
    if len(cns) != 15 or cns[0] not in '123789':
        return False
    if cns[0] in '12':
        soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
        return soma % 11 == 0
    # provisório 7/8/9
    pis = cns[:11]
    soma = sum(int(d) * w for d, w in zip(pis, range(15, 5, -1)))
    resto = soma % 11
    dv = 11 - resto
    if dv == 11:
        dv = 0
    if dv == 10:
        soma = 2 + sum(int(d) * w for d, w in zip(pis, range(15, 5, -1)))
        resto = soma % 11
        dv = 11 - resto
        resultado = pis + "000" + str(dv)
    else:
        resultado = pis + str(dv) + cns[12:15]
    return resultado == cns
```

Hmm, that's one common implementation. Let me verify: for dv==10 case, resultado = pis + "000" + str(dv) — that's 11 + 3 + 1 = 15 digits. And the check compares to cns. For dv != 10: resultado = pis + str(dv) + cns[12:15] — 11 + 1 + 3 = 15. So the 12th digit must be dv, and the last 3 digits are free? That seems odd but it's how the JS works (the last 3 digits are a sequence number). Actually in the JS, for dv != 10: resultado = pis + "." + dv + valeur.substr(11,2)... hmm the JS formats differently. 

Honestly, for this task, a reasonable CNS validator covering the 1/2 case strictly and the 7/8/9 case with the standard algorithm is fine. I'll implement the version above which is widely used.

CPF validation: standard check digits.

```python
def valida_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(0, i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if str(digito) != cpf[i]:
            return False
    return True
```

Now, the QR Code/hash: The prescription has a `codigo_hash` (e.g., SHA-256 hex of receita id + emissor + data). The consultar endpoint receives `codigo_hash` (or full QR payload) and returns prescription data with remaining quantities.

Let me design the API:

**POST /dispensacao/consultar**
Request:
```json
{
  "codigo_hash": "sha256hex...",
  "farmaceutico": {"nome": "...", "cns": "...", "cpf": "..."} // optional? 
}
```
Maybe simpler: `{"codigo_hash": "..."}`. Response:
```json
{
  "receita_id": "...",
  "status": "EMITIDA",
  "valida": true,
  "motivo_invalidade": null,
  "paciente": {"nome": "...", "cns": "...", "cpf": "..."},
  "prescritor": {"nome": "...", "registro_conselho": "CRM/SP 123456", "profissional": "..."},
  "cid10": "I10",
  "ciap2": "K86",
  "data_emissao": "...",
  "data_validade": "...",
  "unidade_emissora_cnes": "1234567",
  "itens": [
    {
      "item_id": "...",
      "medicamento": "Losartana potássica",
      "apresentacao": "comprimido 50 mg",
      "quantidade_prescrita": 30,
      "quantidade_dispensada": 0,
      "quantidade_pendente": 30,
      "posologia": "1 comprimido a cada 24h",
      "status": "PENDENTE"
    }
  ]
}
```

**POST /dispensacao/confirmar**
Request:
```json
{
  "codigo_hash": "...",
  "farmaceutico": {"nome": "Maria", "cns": "...", "cpf": "..."},
  "unidade_cnes": "7654321",
  "tipo": "TOTAL" | "FRACIONADA",
  "itens": [
    {"receita_item_id": "...", "quantidade_dispensada": 30, "lote": "ABC123", "validade_lote": "2026-01-31"}
  ],
  "observacoes": "..."
}
```
Response: dispensation receipt with id, timestamp, status of prescription after, items with quantities.

Validation rules for confirmar:
- Prescription valid (exists, not expired, not cancelled, not fully dispensed)
- Each item belongs to the prescription
- quantidade_dispensada >= 1 and <= pendente
- tipo must be consistent: if all items get full remaining → TOTAL; else FRACIONADA. Or the service determines tipo automatically. I'll validate: if tipo == TOTAL, then each item must dispense the full pending amount; if FRACIONADA, at least one item is partial (or some item omitted). Actually simpler: compute tipo from the operation and validate consistency — if declared TOTAL but quantities don't cover everything → 422. If declared FRACIONADA but covers everything → could auto-upgrade or error. I'll validate strictly and return 422 with clear message. Hmm, or auto-determine. Let me be pragmatic: the service computes the resulting status; the request's `tipo` must match the computed one, otherwise 422 with explanation. That's clean and testable.

- Idempotency: optional `idempotencia` UUID field; if the same key was