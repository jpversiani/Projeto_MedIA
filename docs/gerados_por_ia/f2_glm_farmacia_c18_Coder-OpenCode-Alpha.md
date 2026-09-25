The user wants me to create a FastAPI backend module for pharmaceutical dispensing and prescription fulfillment (baixa de receita) for the MedIA project (Brazilian SUS healthcare system). Let me analyze the requirements:

1. **File**: `backend/app/api/v1/farmacia.py`
2. **Routes**:
   - `POST /dispensacao/consultar` - validates QR Code/hash of prescription
   - `POST /dispensacao/confirmar` - registers total or partial (fracionada) dispensing of medications in SUS
3. **Tech stack**: Python 3.12, Pydantic v2, SQLAlchemy 2.0, FastAPI
4. **SUS/APS standards**: CIAP-2, CID-10, SOAP method, CNS/CPF identification
5. **Test coverage**: pytest

Let me design this properly:

### Architecture considerations:

**Models needed** (SQLAlchemy 2.0 style with `Mapped` and `mapped_column`):
- `Receita` (Prescription) - with hash/QR code identifier, status, patient CNS/CPF, professional info, CID-10
- `ReceitaItem` (Prescription items) - medications with dosage, quantity, validity
- `Dispensacao` (Dispensing record) - linked to receita, type (total/fracionada), pharmacist info
- `DispensacaoItem` - items actually dispensed

**Schemas** (Pydantic v2):
- `DispensacaoConsultaRequest` - QR code hash or receita ID
- `DispensacaoConsultaResponse` - prescription details, patient, items with remaining quantities
- `DispensacaoConfirmarRequest` - items to dispense, pharmacist ID, unit (UBS/farmácia)
- `DispensacaoConfirmarResponse` - confirmation with receipt

**Business rules**:
- Validate prescription exists by hash (QR Code)
- Validate prescription status (ativa, not expired, not already fully dispensed)
- Validate patient CNS format (SUS card - 15 digits with validation algorithm)
- Validate CPF format
- Partial dispensing (fracionada): track remaining quantity per item
- Total dispensing: all items fully dispensed
- CID-10 validation
- Audit trail

**CNS validation algorithm** (Brazilian SUS card):
The CNS has 15 digits. Validation:
- First digit must be 1, 2, 7, 8, or 9
- For 1,2: sum with weights 15 to 2, mod 11, check digit = 11 - resto; if check digit == 11, check digit = 0
- For 7,8,9: different algorithm - sum weights 15 to 2, then add 100 to sum... Actually the algorithm for 7,8,9 starting digits:
  - soma = sum(digit[i] * (15-i))
  - resto = soma % 11
  - if resto == 0: invalid... Actually let me recall:
  
For CNS starting with 1 or 2:
```
soma = Σ (dígito[i] * peso[i]) where pesos = 15,14,13,...,1
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0
if dv != digit[14]: invalid
```

For CNS starting with 7, 8, or 9:
```
soma = Σ (dígito[i] * peso[i]) pesos 15..1
resto = soma % 11
if resto != 0: invalid
else: valid
```

Actually the standard algorithm:
```python
def valida_cns(cns: str) -> bool:
    cns = cns.strip().replace(' ', '')
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] not in '12789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if cns[0] in '12':
        resto = soma % 11
        dv = 11 - resto if resto != 0 else 0  # hmm
        # Actually: dv = 11 - resto; if dv == 11: dv = 0
        return dv == int(cns[14])  # wait this doesn't work because soma includes last digit
    ...
```

Let me recall the correct algorithm properly:

```python
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] in '12':
        # pesos 15 a 2 para os 14 primeiros dígitos
        soma = sum(int(cns[i]) * (15 - i) for i in range(14))
        resto = soma % 11
        dv = 11 - resto
        if dv == 11:
            dv = 0
        return dv == int(cns[14])
    elif cns[0] in '789':
        # soma com pesos 15 a 1 (todos os 15 dígitos) deve ser divisível por 11
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    return False
```

Hmm, actually for 7/8/9: the algorithm is:
```
soma = Σ dígito[i] * peso[i], pesos = 15,14,...,1
resto = soma % 11
if resto == 0: válido
else: inválido
```

Yes that's right. For 1/2: pesos 15..2 applied to first 14 digits, dv = 11 - resto (if resto != 0), if dv == 11 then dv = 0. Wait, if resto == 0, dv = 11 - 0 = 11, then dv = 0? Let me check: the rule is "se resto = 0, dv = 0"? Actually:

The official algorithm for CNS starting with 1 or 2:
- peso = 15 down to 2 for the first 14 digits
- soma = Σ
- resto = soma % 11
- dv = 11 - resto
- if dv == 11: dv = 0
- if dv == 10: invalid (this case means the number is invalid)

Hmm, actually if resto == 0 then dv = 11 which is set to 0. If resto == 1, dv = 10 which is invalid — in practice this doesn't happen for valid CNS. Let me just implement:

```python
resto = soma % 11
dv = 11 - resto
if dv > 9:
    dv = 0  # hmm, not exactly
```

The commonly used implementation:
```python
def valida_cns(cns):
    cns = ''.join(filter(str.isdigit, cns))
    if len(cns) != 15 or cns[0] not in '12789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if cns[0] in '12':
        resto = soma % 11
        dv = 11 - resto if resto >= 2 else resto  # ???
```

Let me look at a known correct implementation:

```python
def valida_cns(vCNS):
    # Fórmula: https://integracao.eps.gov.br/cns/documentos/ValidacaoCNS.pdf
    vCNS = vCNS.strip().replace('.', '').replace(' ', '')
    if len(vCNS) != 15:
        return False
    if vCNS[0] not in ['1', '2', '7', '8', '9']:
        return False
    soma = 0
    for i in range(15):
        peso = 15 - i
        soma += int(vCNS[i]) * peso
    resto = soma % 11
    if resto == 0:
        return True if vCNS[0] in ['7', '8', '9'] else False
    dv = 11 - resto
    if vCNS[0] in ['1', '2']:
        return dv == int(vCNS[14])
    else:
        return False
```

Hmm wait, that's not right either. Let me think again.

The official validation (from Ministério da Saúde):

**CNS starting with 1, 2:**
1. Multiply digits 1-14 by weights 15-2 (i.e., digit i by weight 15-i for i=0..13)
2. Sum results
3. resto = soma % 11
4. dv = 11 - resto
5. If dv == 11, dv = 0
6. If dv == 10, the CNS is invalid (shouldn't happen)
7. CNS valid if dv == digit 15

Wait, but there's a subtlety: if resto == 0, dv = 11 - 0 = 11, then dv = 0. Hmm, but actually the official doc says: "Caso o resto seja diferente de zero, o DV é obtido pela subtração (11 – resto). Caso o resto seja igual a zero, o DV é igual a zero." Hmm, or "se resto = 1, soma 100 ao número e refaz o cálculo"? 

Actually there's a variant: for CNS 1/2, if the DV calculation results in 10 or 11, you add 100 to the registration number and recalculate. But for validation purposes, the simpler check works:

```python
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] not in '12789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    resto = soma % 11
    if cns[0] in '789':
        return resto == 0
    else:  # 1 or 2
        dv = 11 - resto
        if dv == 11:
            dv = 0
        return dv == int(cns[14])
```

Hmm wait, for 1/2 the soma includes the 15th digit with weight 1. Let me verify with a known valid CNS: "000 0000 0000 0000"? No. A commonly used test CNS: "700000000000000"? Hmm.

Known valid CNS examples: 
- "00000000000000" no...
- Test CNS often used: 700 0000 0000 0000? 

Let me verify the 7/8/9 algorithm with a real example. A valid CNS example from docs: "898005026845989"? Not sure.

Actually, the widely-circulated correct implementation (from the official PDF "Validação do CNS"):

Para CNS iniciado em 1 ou 2:
```
1) Multiplicar cada um dos 14 primeiros dígitos pelo peso correspondente (15, 14, 13, ..., 2)
2) Somar os resultados
3) Calcular o resto da divisão da soma por 11
4) Subtrair o resto de 11: dv = 11 - resto
5) Se dv = 11, dv = 0
6) Se dv = 10, o CNS é inválido
7) Comparar dv com o 15º dígito
```

Hmm, but wait — there's the special case: "Caso o resto da divisão seja 1, deve-se somar 100 ao número CNS e refazer o cálculo" — this applies to generating, but for validation, if dv = 10 the CNS is invalid.

Hmm, actually no. Let me recheck. The official algorithm from the Ministry of Health PDF:

Para CNS com primeiro dígito 1, 2, 7, 8 ou 9:

Actually the PDF describes two cases:
- CNS starting with 1 or 2: uses the DV calculation described above
- CNS starting with 7, 8, 9: soma of all 15 digits × weights 15..1 must be divisible by 11 (resto = 0)

For validation of 1/2 CNS:
```
soma = Σ (d[i] × peso[i]) for i in 0..13, peso = 15-i
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0
if dv == 10: invalid
valid if dv == d[14]
```

Hmm, but many implementations include the 15th digit in the sum with weight 1 and check `soma % 11 == 0` for ALL cases. Let me check: if dv = 11 - resto where resto = (soma14 % 11), then soma15 = soma14 + d14*1. For the CNS to be valid: d14 = 11 - resto (mod 11, with 11→0). Then soma15 % 11 = (soma14 + d14) % 11 = (soma14 + 11 - resto) % 11 = (soma14 - resto) % 11 = 0. Yes! So including the 15th digit with weight 1 and checking soma % 11 == 0 works for 1/2 as well, EXCEPT when dv = 0 case: resto = 11? No wait: if resto = 0, dv = 11 → dv = 0. Then soma15 = soma14 + 0 = soma14, and soma14 % 11 = 0. So soma15 % 11 = 0. 

So actually the unified check `sum(d[i] * (15-i) for i in range(15)) % 11 == 0` works for all valid CNS (1,2,7,8,9)! That's the elegant version. Let me double check with the 7/8/9 case: yes, that's exactly the rule. And for 1/2: derived above. 

So:
```python
def _validar_cns(cns: str) -> bool:
    cns = re.sub(r"\D", "", cns)
    if len(cns) != 15 or cns[0] not in "12789":
        return False
    soma = sum(int(d) * peso for d, peso in zip(cns, range(15, 0, -1)))
    return soma % 11 == 0
```

Let me verify with a known valid CNS. Common test CNS: "000 0000 0000 0000"? That's all zeros — first digit 0, invalid. 

Known valid CNS examples used in Brazilian health systems: 
- 702 1025 6094 8724? Not sure.
- 898 0050 2684 5989?

Hmm, let me construct one. For a 7-series CNS: digits d0..d14 with d0=7, need Σ d[i]*(15-i) ≡ 0 mod 11.

Take "700000000000000": soma = 7*15 = 105. 105 % 11 = 105 - 99 = 6. Not valid.

Let me construct: d0=7, rest zeros except last digit d14 with weight 1: soma = 105 + d14. Need (105 + d14) % 11 == 0 → d14 = 1 (106 % 11 = 106-99=7, no)... 11*10 = 110, so d14 = 5: 110 % 11 = 0. Yes! So "700000000000005" is valid. Hmm, but is that a real format? The 7/8/9 series CNS are temporary ones. OK.

For 1/2 series: d0=1, d14 = dv. soma = 15 + d14. Need ≡ 0 mod 11 → 15 + d14 = 22 → d14 = 7. So "100000000000007" would be valid by this algorithm. 

Actually, let me double-check against a real-world known valid CNS. The CNS "116 620 877 500 008"? I can't verify offline. I'll trust the algorithm — it's the standard one widely used (e.g., in many GitHub implementations):

```python
def valida_cns(cns):
    cns = cns.replace(" ", "").replace(".", "")
    if len(cns) != 15 or not cns.isdigit() or cns[0] not in "12789":
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

Yes, this is a well-known correct implementation. Good.

**CPF validation**:
```python
def _validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for n in (9, 10):
        dv = sum(int(cpf[i]) * (n + 1 - i) for i in range(n)) % 11
        # wait, weights for first DV: 10,9,8,...,2 for digits 0..8
```

Standard CPF:
```python
def _validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    dv1 = (soma * 10 % 11) % 10
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    dv2 = (soma * 10 % 11) % 10
    return dv1 == int(cpf[9]) and dv2 == int(cpf[10])
```

The classic: dv1 = resto of Σ d[i]*(10-i) for i 0..8, mod 11; if resto < 2, dv = 0 else dv = 11 - resto. The `(soma * 10 % 11) % 10` trick is equivalent. Let me verify: soma*10 % 11 — hmm, the classic implementation:

```python
d1 = cpf[:9]
soma = sum(int(d1[i]) * (10