The user wants me to create a FastAPI module for pharmaceutical dispensing and prescription fulfillment (baixa de receita) for the MedIA project, related to SUS (Brazilian Unified Health System).

Let me think about what's needed:

1. **File**: `backend/app/api/v1/farmacia.py`
2. **Routes**:
   - `POST /dispensacao/consultar` - validates QR Code/hash of prescription
   - `POST /dispensacao/confirmar` - registers total or fractional dispensing of medications in SUS

3. **Requirements**:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me design this properly:

### Domain Model Considerations

**Receita (Prescription)**:
- Has a hash/QR code for validation
- Contains prescribed medications (itens)
- Has status: EMITIDA, PARCIALMENTE_DISPENSADA, DISPENSADA (total), CANCELADA, EXPIRADA, etc.
- Linked to patient via CNS/CPF
- Has CID-10 diagnosis code
- Has validity date

**Dispensação (Dispensing)**:
- Can be total (all items) or fractional (partial items/quantities)
- Records: pharmacist, items dispensed, quantities, date, unit (UBS/Unidade de Saúde)
- Updates prescription status accordingly

**Validation flow for /consultar**:
1. Receive hash from QR code
2. Look up prescription
3. Validate: exists, not expired, not fully dispensed, not canceled
4. Return prescription details: patient info (masked?), items with remaining quantities, status

**Confirmation flow for /confirmar**:
1. Receive hash + items to dispense (with quantities) + pharmacist info + unit
2. Validate again (idempotency concerns, concurrency)
3. Register dispensing record
4. Update remaining quantities per item
5. Update prescription status: total vs partial
6. Return confirmation with updated status

### SUS-specific considerations:
- CNS (Cartão Nacional de Saúde) - 15 digits, validate with algorithm
- CPF - 11 digits, validate with check digits
- CID-10 codes for diagnoses
- CIAP-2 codes for primary care (APS)
- Medications in SUS often follow Rename (Relação Nacional de Medicamentos Essenciais)
- Farmácia popular, Componente Básico da Assistência Farmacêutica

### Technical design:

**Pydantic v2 schemas**:
- `DispensacaoConsultaRequest`: hash (QR code content)
- `ReceitaConsultaResponse`: prescription data, items with quantities prescribed/dispensed/remaining, status, validity
- `DispensacaoConfirmarRequest`: hash, items (item_id, quantidade), farmaceutico info (CNS/CPF, nome, registro conselho - CRF), unidade (CNES)
- `DispensacaoResponse`: confirmation with dispensing ID, status update

**SQLAlchemy 2.0 models** (I should define them or reference existing ones — since the task says create the API file, but for completeness and testability, I might need to show models. The task says "crie backend/app/api/v1/farmacia.py com rotas FastAPI". I'll focus on the API file but need models. Let me create the API file that imports from a models module — but to make it self-contained and testable, maybe I should include the models in the response as well, or assume they exist.

Given the instruction "Manter conformidade total e cobertura de testes automatizados com pytest", I should also provide tests. Let me structure:

1. `backend/app/api/v1/farmacia.py` - the main deliverable
2. Supporting: models (maybe `backend/app/models/receita.py` and `backend/app/models/dispensacao.py`), schemas (`backend/app/schemas/farmacia.py`), service layer (`backend/app/services/farmacia_service.py`)
3. Tests: `backend/tests/api/v1/test_farmacia.py`

Actually, the task explicitly says to create `backend/app/api/v1/farmacia.py`. But to make it work, I need dependencies. Let me think about what's most useful: a complete, working implementation with the API file as the centerpiece, plus the necessary supporting files (schemas, service, models) and comprehensive tests.

Let me design the architecture:

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── farmacia.py          # Main deliverable
│   ├── models/
│   │   ├── receita.py               # Receita, ReceitaItem models
│   │   └── dispensacao.py           # Dispensacao, DispensacaoItem models
│   ├── schemas/
│   │   └── farmacia.py              # Pydantic v2 schemas
│   ├── services/
│   │   └── farmacia_service.py      # Business logic
│   ├── core/
│   │   ├── exceptions.py            # Custom exceptions
│   │   └── validators.py            # CNS/CPF validators
│   └── db/
│       └── session.py               # DB session dependency
└── tests/
    └── api/
        └── v1/
            └── test_farmacia.py     # pytest tests
```

### Detailed Design

**Status enum for Receita**:
```python
class StatusReceita(str, Enum):
    EMITIDA = "EMITIDA"
    PARCIALMENTE_DISPENSADA = "PARCIALMENTE_DISPENSADA"
    TOTALMENTE_DISPENSADA = "TOTALMENTE_DISPENSADA"
    CANCELADA = "CANCELADA"
    EXPIRADA = "EXPIRADA"
```

**Receita model**:
- id (UUID)
- hash_qr (unique, indexed) - the QR code content
- paciente_nome, paciente_cns, paciente_cpf
- cid10 (nullable), ciap2 (nullable)
- profissional_solicitante (nome), crm/coren
- unidade_cnes (emissão)
- data_emissao, data_validade
- status
- items (relationship)

**ReceitaItem model**:
- id
- receita_id (FK)
- medicamento_nome, medicamento_codigo (catmat or Rename code?)
- apresentacao (dosagem/forma: "Comprimido 500mg")
- quantidade_prescrita
- quantidade_dispensada (default 0)
- via_administracao? posologia?

**Dispensacao model**:
- id
- receita_id (FK)
- tipo: TOTAL / FRACIONADA
- farmaceutico_nome, farmaceutico_cpf, farmaceutico_crf
- unidade_cnes
- data_dispensacao
- observacoes
- items (relationship)

**DispensacaoItem**:
- id
- dispensacao_id (FK)
- receita_item_id (FK)
- quantidade_dispensada

**Business rules**:
1. `/consultar`: hash required; prescription must exist; if expired → status EXPIRADA (or error); if canceled → error; return items with remaining quantities. Even fully dispensed prescriptions can be consulted (returning status), but maybe with a warning. Let me allow consultation of any existing prescription, returning its status and remaining quantities. That's useful for the pharmacist to see.

2. `/confirmar`: 
   - Validate hash exists
   - Prescription must be EMITIDA or PARCIALMENTE_DISPENSADA (not CANCELADA, not EXPIRADA, not TOTALMENTE_DISPENSADA)
   - Not expired (data_validade >= today)
   - Items requested must belong to the prescription
   - Quantities must be > 0 and <= remaining
   - At least one item
   - After dispensing: if all items have quantidade_dispensada == quantidade_prescrita → TOTALMENTE_DISPENSADA, else PARCIALMENTE_DISPENSADA
   - Concurrency: use row locking (SELECT ... FOR UPDATE) or optimistic locking with version. SQLAlchemy 2.0: `select(...).with_for_update()`. With SQLite in tests, FOR UPDATE is a no-op but fine.
   - Idempotency: maybe accept an optional idempotency key? Could be overkill. Let me keep it simpler but mention it. Actually, for robustness, a unique idempotency key could be good. Hmm, the task doesn't require it. I'll keep the design focused but solid.

**Validators**:
- CPF: check digits algorithm
- CNS: 15 digits, validation algorithm (starts with 1, 2, 7, 8, 9)
- CNES: 7 digits
- CRF: pharmacy council registration

Let me write the CNS validation algorithm:
- CNS must have 15 digits
- If starts with 1 or 2 (definitive cards): use the "soma ponderada" algorithm: multiply digits by 15,14,13,...,2 (from left), sum, check sum % 11 == 0.
- If starts with 7, 8, 9 (temporary cards): sum of digits * weights must have... actually for temporary: the check is sum of (digit * weight) % 11 == 0 as well? Let me recall.

The standard CNS validation:
```
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    # only digits
    if not cns.isdigit():
        return False
    if cns[0] in '123456789':  # actually 1,2,7,8,9
        # weights 15 down to 2
        soma = sum(int(d) * w for d, w in zip(cns, range(15, 1, -1)))  # wait that's 15 weights for 15 digits
```

Hmm, let me be careful. The algorithm for definitive CNS (starting with 1 or 2):
- Take the first 15 digits
- Multiply each digit by weights 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1? No...

Actually the well-known algorithm:
```
def valida_cns(cns):
    cns = ''.join(filter(str.isdigit, cns))
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    if cns[0] in '12':
        # Ponderação: 15,14,13,...,2 applied to first 15 digits? 
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    else:
        # temporary: 7,8,9
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        resto = soma % 11
        if resto == 0:
            return True
        # alternative: soma = soma + (resto...)? 
```

Hmm, I remember the temporary CNS validation differently. Let me recall the official algorithm from DATASUS:

For CNS starting with 1 or 2:
```
soma = 0
peso = 15
for each digit:
    soma += digit * peso
    peso -= 1
resto = soma % 11
valid if resto == 0
```
That's 15 digits with weights 15 down to 1. Wait, 15 digits, weights 15,14,...,1. Yes.

For CNS starting with 7, 8, or 9 (temporary):
```
soma = 0
peso = 15
for each digit:
    soma += digit * peso
    peso -= 1
resto = soma % 11
if resto != 0:
    resto = 11 - resto  # ?
```

Hmm, actually I recall the temporary validation being: the sum must satisfy... Let me think. The commonly cited implementation:

```python
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] in '12':
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    elif cns[0] in '789':
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        resto = soma % 11
        if resto == 0:
            return True
        dv = 11 - resto
        # then check: soma + dv*1 ... hmm
```

Actually, I found it. The official DATASUS algorithm for temporary CNS (7/8/9):

```
rotina T:
  soma = sum(digit[i] * (15 - i) for i in 0..14)
  resto = soma % 11
  if resto == 0: valid
  else: 
    dv = 11 - resto
    # recalculate: soma2 = soma + dv (dv added as if it were...?)
```

Hmm, this is getting complicated. Let me look at it from a different angle. A widely used Python implementation:

```python
def valida_cns(cns: str) -> bool:
    cns = re.sub(r'[^0-9]', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] in '789':
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        resto = soma % 11
        if resto != 0:
            dv = 11 - resto
            soma = sum(int(cns[i]) * (15 - i) for i in range(14)) + dv
            resto = soma % 11
            if resto != 0:
                return False
        return True
    if cns[0] in '12':
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    return False
```

Hmm, I'm not 100% sure about the temporary algorithm. To be safe and pragmatic, I could implement the definitive (1/2) algorithm correctly and for temporary (7/8/9) use the same modulo check, which is what many implementations do. Actually many implementations just do the same check for all. Let me use a well-known valid test CNS to verify: "116 8198 7964 0004" or similar. 

Known valid CNS examples used in tests: 
- 700000000003008? Hmm.
- A commonly used valid CNS: "116819879640004"? Let me verify with the algorithm: digits 1,1,6,8,1,9,8,7,9,6,4,0,0,0,4 with weights 15,14,13,12,11,10,9,8,7,6,5,4,3,2,1:
  1*15=15, 1*14=14, 6*13=78, 8*12=96, 1*11=11, 9*10=90, 8*9=72, 7*8=56, 9*7=63, 6*6=36, 4*5=20, 0*4=0, 0*3=0, 0*2=0, 4*1=4
  Sum: 15+14=29, +78=107, +96=203, +11=214, +90=304, +72=376, +56=432, +63=439, +36=475, +20=495, +0+0+0=495, +4=499. 499 % 11 = 499 - 495 (45*11) = 4. Not 0. So that's not valid by this algorithm. Hmm, maybe my example is wrong.

Let me construct a valid one instead of guessing: I need sum % 11 == 0. Take CNS "111111111111111"? Sum = sum of digits 1..15 weights: (15+14+...+1) = 120. 120 % 11 = 10. Not valid.

Let me just compute one: digits d1..d15, sum = Σ d_i * (16-i). I want a valid CNS for tests. Common test CNS in Brazilian health systems: "000000000000000"? Starts with 0 → invalid.

Known valid CNS from documentation: "898764567891008"? Let me test: digits 8,9,8,7,6,4,5,6,7,8,9,1,0,0,8, weights 15..1:
8*15=120, 9*14=126, 8*13=104, 7*12=84, 6*11=66, 4*10=40, 5*9=45, 6*8=48, 7*7=49, 8*6=48, 9*5=45, 1*4=4, 0*3=0, 0*2=0, 8*1=8.
Sum: 120+126=246, +104=350, +84=434, +66=500, +40=540, +45=585, +48=633, +49=682, +48=730, +45=775, +4=779, +0+0=779, +8=787. 787 % 11: 11*71=781, remainder 6. Not valid.

OK, rather than guessing, let me generate one programmatically in my head. For a definitive CNS starting with 1: I want Σ d_i*(16-i) ≡ 0 mod 11 for i=1..15 (weights 15 down to 1).

Let me pick digits: 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5? Sum: 1*15+2*14+3*13+4*12+5*11+6*10+7*9+8*8+