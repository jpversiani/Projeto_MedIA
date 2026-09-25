The user wants me to create a FastAPI backend module for pharmaceutical dispensing and prescription fulfillment (C6) for the MedIA project. This is for the Brazilian SUS (Unified Health System).

Requirements:
- `backend/app/api/v1/farmacia.py` with FastAPI routes:
  - `POST /dispensacao/consultar` (validates QR Code/hash of prescription)
  - `POST /dispensacao/confirmar` (registers total or fractional dispensing of medications in SUS)
- Pydantic v2 and SQLAlchemy
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me design this properly:

1. **Schemas (Pydantic v2)**: `backend/app/schemas/farmacia.py`
   - `ReceitaConsultaRequest`: hash/QR code validation
   - `ReceitaConsultaResponse`: prescription details, patient info (CNS/CPF masked), medications with status
   - `DispensacaoItem`: medication item with quantity
   - `DispensacaoConfirmarRequest`: prescription hash + items (total or fractional)
   - `DispensacaoConfirmarResponse`: confirmation with dispensation record

2. **Models (SQLAlchemy 2.0)**: `backend/app/models/farmacia.py`
   - `Receita` (prescription): id, hash/uuid, patient CNS, CID-10, CIAP-2, professional info, status, validity dates
   - `ReceitaItem`: medication items with prescribed quantity, dispensed quantity
   - `Dispensacao`: dispensation record
   - `DispensacaoItem`: items dispensed per dispensation

3. **Service layer**: `backend/app/services/farmacia_service.py`
   - Business logic: validate hash, check expiry, check status, validate fractional dispensing quantities, register dispensation

4. **API routes**: `backend/app/api/v1/farmacia.py`
   - Router with the two endpoints

5. **Tests**: `backend/tests/api/v1/test_farmacia.py`
   - pytest with fixtures, covering success cases, validation errors, edge cases (expired prescription, already fully dispensed, fractional exceeding prescribed, etc.)

Let me think about the domain logic:

**Dispensação (Dispensing) flow:**
1. Pharmacist scans QR code → gets hash → `POST /dispensacao/consultar` with the hash
2. System validates: hash exists, prescription not expired, not revoked, not fully dispensed
3. Returns prescription details: patient (masked CNS/CPF), prescriber, medications with prescribed qty and remaining qty
4. Pharmacist selects items and quantities → `POST /dispensacao/confirmar`
5. System validates: quantities ≤ remaining, at least one item > 0
6. Registers dispensation (total if all items fully dispensed, fractional otherwise)
7. Updates remaining quantities; if all items fully dispensed, marks prescription as DISPENSADA_TOTAL

**Status of prescription:**
- `ATIVA` - active, can be dispensed
- `DISPENSADA_PARCIAL` - partially dispensed
- `DISPENSADA_TOTAL` - fully dispensed
- `EXPIRADA` - expired (validity date passed)
- `CANCELADA` - cancelled by prescriber

**Validation rules:**
- Hash must be valid (exists in DB)
- Prescription must be within validity period
- Status must allow dispensing
- CNS validation (16 digits, check digit algorithm) — I can implement CNS validation
- CPF validation (check digits)
- Quantity must be positive integer
- Fractional dispensing: quantity ≤ prescribed - already dispensed

**CNS validation algorithm (Brazilian SUS card):**
The CNS has 16 digits. Validation:
- If first digit is 1, 2, 7, 8, or 9: standard checksum (Powers of 10 from 15 down to 2... actually the algorithm: sum of digit[i] * (15 - i), total must be divisible by 11)
- If starts with 7, 8, 9: can also be validated with mod 11 using weights... Let me recall the standard algorithm:

```
CNS validation:
- Must have 16 digits
- If first char in "12": sum = Σ digit[i] * (15 - i) for i in 0..15; sum % 11 == 0
- If first char in "789": convert to "000" + first 11 digits... Actually the algorithm for 7/8/9: 
  - Take first 11 digits, prepend "000", then compute two check digits via DAC mod 11
  - Simpler: sum = Σ digit[i] * (15 - i), if sum % 11 == 0 valid
```

Actually the standard algorithm:
```python
def validar_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 16:
        return False
    if cns[0] not in '123789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(16))
    return soma % 11 == 0
```

Wait, that's not quite right. The correct algorithm:

For CNS starting with 1 or 2:
- Weights: 15, 14, 13, ..., 2, 1 (16 digits, weights from 15 down to 1... hmm)
- Actually: pesos = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1] — that's 15 weights for 15 digits, and the 16th is the check digit.

Let me recall properly. The CNS validation:

```
1. CNS must have 16 numeric digits
2. First digit must be 1, 2, 7, 8 or 9
3. Calculation:
   - For CNS starting with 1 or 2:
     soma = Σ (digit[i] * peso[i]) where peso = [15,14,13,12,11,10,9,8,7,6,5,4,3,2,1] applied to first 15 digits
     resto = soma % 11
     dv = 11 - resto
     if dv == 11: dv = 0
     if dv == 10: dv = 0 and soma += 2, then check (soma % 11) == 0... 
```

Hmm, this is getting complicated. The official algorithm:

```
Para CNS que inicia com 1 ou 2:
- Multiplica cada dígito pelos pesos 15,14,13,...,2,1 (da esquerda para direita, 15 dígitos)
- Soma os resultados
- Resto = soma % 11
- DV = 11 - resto
- Se DV == 11 → DV = 0
- Se DV == 10 → número inválido (ou ajusta: soma = soma + 2; resto = soma % 11; DV = 11 - resto; se DV == 11 → DV = 0)
- CNS válido se DV calculado == 16º dígito

Para CNS que inicia com 7, 8 ou 9:
- Formato: 7/8/9 + 3 dígitos (município/ano) + 8 dígitos sequenciais + 2 DVs calculados via módulo 11 (DAC)
- Primeiro DV: soma ponderada dos 12 primeiros dígitos com pesos 15..4, resto = soma % 11, DV1 = 11 - resto (se resto < 2, DV1 = 0)
- Segundo DV: soma ponderada dos 13 primeiros dígitos com pesos 15..3, resto = soma % 11, DV2 = 11 - resto (se resto < 2, DV2 = 0)
```

For simplicity in this project, I'll implement a reasonable CNS validation. Actually, a commonly used simplified version that works for both:

```python
def validar_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns or '')
    if len(cns) != 16 or not cns.isdigit():
        return False
    if cns[0] not in '123789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(16))
    return soma % 11 == 0
```

Wait — this version: weights 15 down to 1 for 16 digits? Let me check: i from 0 to 15, weight = 15 - i gives weights 15, 14, ..., 0. Hmm, weight 0 for the last digit means the check digit doesn't contribute. That's wrong.

The actual universal check used in many implementations:

```python
def validar_cns(cns):
    # Gera pesos de 15 até 2 (para os 15 primeiros dígitos)? 
```

Let me look at a known implementation (from Brazilian gov / common repos):

```python
def valida_cns(cns):
    if len(cns) != 16:
        return False
    pis = cns[:11]
    soma = sum(int(pis[i]) * (15 - i) for i in range(11))
    ...
```

OK here's the official algorithm from DATASUS:

**CNS starting with 1 or 2:**
```
soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
dv = 11 - (soma % 11)
if dv == 11: dv = 0
if dv == 10:
    soma = soma + 2
    dv = 11 - (soma % 11)
    if dv == 11: dv = 0
valid if dv == int(cns[15])
```

**CNS starting with 7, 8, 9:**
```
# 12 digits + 2 DVs
soma = 0
for i in range(12):
    soma += int(cns[i]) * (15 - i)
resto = soma % 11
dv1 = 0 if resto <= 1 else 11 - resto
soma = 0
for i in range(13):
    soma += int(cns[i]) * (15 - i)
resto = soma % 11
dv2 = 0 if resto <= 1 else 11 - resto
valid if dv1 == int(cns[12]) and dv2 == int(cns[13])
```

I'll implement this properly. For tests, I need valid CNS examples. Known valid test CNS: "700000000000000" — hmm, let me think. A commonly used valid CNS for tests: `8980010203040506`? I'm not sure. Let me compute one.

Actually, let me compute a valid CNS starting with 1:
Take 15 digits: "100000000000000" (1 followed by 14 zeros).
soma = 1*15 + 0*14 + ... = 15
soma % 11 = 4
dv = 11 - 4 = 7
So CNS = "1000000000000007" is valid.

Check: digits: 1,0,0,...,0,7. soma = 15. 15 % 11 = 4. dv = 7. Yes! "1000000000000007" is a valid CNS.

Another: "123456789012345" → soma = 1*15 + 2*14 + 3*13 + 4*12 + 5*11 + 6*10 + 7*9 + 8*8 + 9*7 + 0*6 + 1*5 + 2*4 + 3*3 + 4*2 + 5*1
= 15 + 28 + 39 + 48 + 55 + 60 + 63 + 64 + 63 + 0 + 5 + 8 + 9 + 8 + 5
= 15+28=43; 43+39=82; 82+48=130; 130+55=185; 185+60=245; 245+63=308; 308+64=372; 372+63=435; 435+0=435; 435+5=440; 440+8=448; 448+9=457; 457+8=465; 465+5=470
soma = 470. 470 % 11 = 470 - 462 = 8. dv = 11 - 8 = 3. So "1234567890123453" is valid.

For 7/8/9 starting: take "7000000000000" (12 digits: 7 + 11 zeros).
soma = 7*15 = 105. resto = 105 % 11 = 105 - 99 = 6. dv1 = 11 - 6 = 5.
Then 13 digits: "70000000000005". soma = 7*15 + 5*2 = 105 + 10 = 115. resto = 115 % 11 = 115 - 110 = 5. dv2 = 11 - 5 = 6.
So "7000000000000" + "5" + "6" = "700000000000056" — that's 15 digits. Wait, CNS is 16 digits. Let me recount.

CNS format for 7/8/9: 1 digit (7/8/9) + 3 digits (region/municipality) + 6 digits sequential + 2 DVs? That's 12 digits total. Hmm no.

Actually: CNS with 7/8/9 has 16 digits: 7/8/9 + 3 (município) + 8 (sequencial) + 2 (DVs)? 1+3+8+2 = 14. Not 16.

Let me recheck: The provisory CNS (starting 7, 8, 9) format: 7/8/9 + 3 digits + 8 digits + 2 DVs = 14 digits? No, CNS is always 16 digits.

Hmm. Actually the provisory CNS: "7 000 00 00 0000 00" — Let me think again. The structure for 7/8/9: first digit (7/8/9), then 3 digits for municipality code, then 6 digits sequential, then 2 DVs... that's 12. 

OK from DATASUS documentation: "CNS provisório: inicia com 7, 8 ou 9, seguido de 3 dígitos que identificam o município, 8 dígitos sequenciais e 2 dígitos verificadores (DV)". 1 + 3 + 8 + 2 = 14. That's only 14 digits, but CNS is 16 digits...

Hmm, actually I recall the provisory CNS is: 7/8/9 + 3 (município) + 8 (sequencial) + 2 (DV) = 14 digits? No wait.

Let me just recall the validation algorithm from the official DATASUS PDF "Validação do CNS":

```
Para CNS com primeiro dígito 7, 8 ou 9:
- O CNS tem 15 dígitos + ... 
```

Actually here's the algorithm I've seen in multiple implementations:

```python
def validar_cns_provisorio(cns):
    # cns has 16 digits
    soma = 0
    for i in range(12):
        soma += int(cns[i]) * (15 - i)
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    if dv1 != int(cns[12]):
        return False
    soma = 0
    for i in range(13):
        soma += int(cns[i]) * (15 - i)
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    return dv2 == int(cns[13])
```

So for 7/8/9: digits 0-11 (12 digits) are the base, digit 12 is DV1, digit 13 is DV2, digits 14-15 are... hmm, that leaves 2 digits unaccounted. 

Hmm wait, maybe the provisory CNS is 15 digits? No — CNS is definitively 16 digits.

Let me reconsider: maybe for 7/8/9, the structure is: 7/8/9 + 3 (município) + 8 (sequencial) + 2 (DV) = 14... 

OK here's another thought — from the official spec:

"CNS Provisório: 7/8/9 + 3 dígitos (município) + 8 dígitos (sequencial) + 2 DVs" — hmm that's 14.

Actually no! I remember now: the provisory CNS structure is: 7/8/9 + 3 (município) + 6 (sequencial) + 2 (DV) = 12 digits? No...

Let me just go with the algorithm that validates 16 digits where the last two digits are DVs computed over the first 14:

```python
def _validar_cns_provisorio(cns: str) -> bool:
    soma = sum(int(cns[i]) * (15 - i) for i in range(14))
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    if dv1 != int(cns[14]):
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    return dv2 == int(cns[15])
```

This treats the CNS as 14 base digits + 2 DVs, which fits 16 digits. This is a reasonable interpretation. Since the exact official algorithm for provisory CNS is ambiguous in my memory, and the tests are what matter, I'll implement it