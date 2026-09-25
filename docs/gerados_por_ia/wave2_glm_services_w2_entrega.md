The user wants me to create a digital prescription and medical certificate service for a healthcare project called MedIA. This is a legitimate healthcare software development task - creating backend services for digital prescriptions (receita digital) and medical certificates (atestado digital) with SHA-256 hashing and QR code validation, following Brazilian SUS/CFM standards.

Let me think about what's needed:

1. **File: `backend/app/services/receita_digital.py`** - main service file with:
   - `gerar_receita(paciente, profissional, medicamentos, orientacoes)` -> dict with hash and QR Code payload
   - `validar_receita(hash_documento)` -> bool
   - `emitir_atestado(paciente, profissional, dias_afastamento, cid10)` -> dict

2. **Architecture guidelines:**
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me design this properly:

**Domain models (Pydantic v2):**
- `Paciente` - with CNS (Cartão Nacional de Saúde), CPF, nome, data_nascimento
- `Profissional` - with CRM, UF, nome, especialidade (CFM registration)
- `Medicamento` - with nome, dosagem, via_administracao, posologia, quantidade
- `Receita` - generated prescription with hash, QR code payload
- `Atestado` - medical certificate with CID-10, days off, hash

**Validation logic:**
- CNS validation (the SUS card number has a validation algorithm - check digit)
- CPF validation (standard Brazilian check digits)
- CRM format validation
- CID-10 format validation (e.g., A09, J45.9)
- SHA-256 hash generation over canonical document content
- QR Code payload generation (structured string or JSON)

**CNS validation algorithm:**
The CNS can be in format 1, 2, 7, 8, 9 starting digits. Algorithm:
- Must have 15 digits
- Starting with 1, 2: use sum with weights 15 down to 2 (like the classic algorithm)
- Starting with 7, 8, 9: different algorithm

Classic CNS validation:
```
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] in '12':
        # soma ponderada
        soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
        return soma % 11 == 0
    elif cns[0] in '789':
        # algorithm with multiplication
        soma = 0
        peso = 15
        for digito in cns:
            soma += int(digito) * peso
            peso -= 1
        resto = soma % 11
        if resto == 0:
            return True
        dv = 11 - resto
        # if dv > 9, need special handling... actually the algorithm for 7/8/9:
        # soma = sum of digits * weights 15..2
        # resto = soma % 11
        # if resto != 0: dv = 11 - resto; if dv > 9: dv = 0... 
```

Let me recall the correct CNS validation algorithm:

For CNS starting with 1 or 2:
- Multiply each digit by weights 15, 14, 13, ..., 2 (left to right)
- Sum all results
- The sum must be divisible by 11

For CNS starting with 7, 8 or 9:
- Multiply each digit by weights 15 to 2
- Sum
- resto = soma % 11
- if resto == 0 → valid
- else dv = 11 - resto; if dv > 9 → invalid... 

Actually the official algorithm for 7/8/9:
```
soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
resto = soma % 11
if resto != 0:
    dv = 11 - resto
    if dv > 9:
        # soma += 2 and recompute? 
```

The official algorithm (from DATASUS):
```
function validaCNS(vlrCNS) {
  // Formato provisório - 15 dígitos, iniciando com 7, 8 ou 9
  var soma = new Number();
  var resto = new Number();
  var dv = new Number();
  var pis = new String();
  var resultado = new String();
  var tamCNS = vlrCNS.length;
  if ((tamCNS) != 15) return false;
  // ...
  if (vlrCNS.charAt(0) == '1' || vlrCNS.charAt(0) == '2') {
    pis = vlrCNS.substring(0, 11);
    soma = 0;
    for (i = 0; i < 11; i++) {
      soma += parseInt(vlrCNS.charAt(i)) * (15 - i);
    }
    resto = soma % 11;
    if (resto == 0) { dv = resto; } else { dv = 11 - resto; }
    resultado = pis + dv.toString() + vlrCNS.substring(12, 15);
    if (vlrCNS != resultado) return false;
    return true;
  } else {
    soma = 0;
    for (i = 0; i < 15; i++) {
      soma += parseInt(vlrCNS.charAt(i)) * (15 - i);
    }
    resto = soma % 11;
    if (resto == 0) { dv = resto; } else { dv = 11 - resto; }
    if (dv != parseInt(vlrCNS.charAt(14))) return false;
    return true;
  }
}
```

Hmm, actually for 7/8/9 the algorithm is:
```
soma = 0
for i in 0..14: soma += digit[i] * (15 - i)
resto = soma % 11
if resto != 0:
    dv = 11 - resto
    if dv > 9:
        soma = soma + 2  # then recompute resto
        resto = soma % 11
        dv = 11 - resto
```

Wait, let me get this right. The official DATASUS algorithm for provisory CNS (7,8,9):

```
soma = 0;
for (i = 0; i < 15; i++) {
    soma += parseInt(vlrCNS.charAt(i)) * (15 - i);
}
resto = soma % 11;
if (resto != 0) {
    dv = 11 - resto;
    if (dv > 9) {
        soma = soma + 2;
        resto = soma % 11;
        dv = 11 - resto;
    }
}
if (dv != parseInt(vlrCNS.charAt(14))) return false;
```

Hmm, that's not quite right either. Let me think about the actual algorithm. The provisory CNS uses a different check digit calculation:

Actually the correct one for 7/8/9:
```
soma = 0
peso = 15
for each digit:
    soma += digit * peso
    peso -= 1
resto = soma % 11
if resto != 0:
    dv = 11 - resto
    if dv > 9:
        # add 2 to soma and recompute
        soma += 2
        resto = soma % 11
        dv = 11 - resto
```

Hmm, but that doesn't make sense mathematically for validation. Let me look at it differently. The validation function should just verify. For validation purposes:

For 1/2 CNS: 
- soma = Σ digit[i] * (15-i) for i=0..14
- valid if soma % 11 == 0

For 7/8/9 CNS:
- soma = Σ digit[i] * (15-i) for i=0..14
- resto = soma % 11
- if resto == 0: dv = 0... 

Hmm wait. Actually for validation of 7/8/9, the common implementation is:

```python
def valida_cns_provisorio(cns):
    soma = sum(int(d) * p for d, p in zip(cns, range(15, 0, -1)))
    resto = soma % 11
    if resto == 0:
        return int(cns[14]) == 0  # hmm no
    ...
```

Let me just recall from a reliable Python implementation:

```python
def valida_cns(cns: str) -> bool:
    cns = ''.join(filter(str.isdigit, cns))
    if len(cns) != 15:
        return False
    if cns[0] not in '123789':
        return False
    
    if cns[0] in '12':
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    else:  # 7, 8, 9
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        resto = soma % 11
        if resto != 0:
            dv = 11 - resto
            if dv > 9:
                soma += 2
                resto = soma % 11
                dv = 11 - resto
        return dv == int(cns[14])
```

Hmm, this is getting complicated. Actually, I remember the official JS from DATASUS for provisory:

```javascript
// Rotina para validação padrão do CNS (Cartão Nacional de Saúde)
function validaCNS(vlrCNS) {
	var soma = new Number();
	var resto = new Number();
	var dv = new Number();
	var pis = new String();
	var resultado = new String();
	var tamCNS = vlrCNS.length;
	if ((tamCNS) != 15) {
		return (false);
	}
	for (i = 0; i < tamCNS; i++) {
		if ((vlrCNS.charAt(i) < '0') || (vlrCNS.charAt(i) > '9')) {
			return (false);
		}
	}
	pis = vlrCNS.substring(0, 11);
	soma = 0;
	for (i = 0; i < 11; i++) {
		soma += parseInt(vlrCNS.charAt(i)) * (15 - i);
	}
	resto = soma % 11;
	if (resto == 0) {
		dv = resto;
	} else {
		dv = 11 - resto;
	}
	resultado = pis + dv.toString() + vlrCNS.substring(12, 15);
	if (vlrCNS != resultado) {
		return (false);
	} else {
		return (true);
	}
}
```

Wait, this version validates all CNS with the first-11-digits approach. Hmm, but that's for the definitive ones (1, 2). For provisory (7, 8, 9), there's another function:

```javascript
function validaCNSProvisorio(vlrCNS) {
	if (vlrCNS.trim().length != 15) {
		return (false);
	}
	var soma = 0;
	for (var i = 0; i < 15; i++) {
		var digit = parseInt(vlrCNS.charAt(i));
		soma += digit * (15 - i);
	}
	var resto = soma % 11;
	if (resto != 0) {
		var dv = 11 - resto;
		if (dv > 9) {
			soma = soma + 2;
			resto = soma % 11;
			dv = 11 - resto;
		}
	}
	if (vlrCNS.charAt(14) != dv.toString()) {
		return false;
	}
	return true;
}
```

Hmm, but there's a subtlety: if resto == 0, dv = 0? Actually in the code above, if resto == 0, dv remains undefined... Let me think. Actually I've seen implementations where:

```python
def _valida_cns_provisorio(cns):
    soma = sum(int(d) * (15 - i) for i, d in enumerate(cns))
    resto = soma % 11
    if resto != 0:
        dv = 11 - resto
        if dv > 9:
            soma += 2
            resto = soma % 11
            dv = 11 - resto
    else:
        dv = 0  # hmm
    return dv == int(cns[14])
```

Hmm, actually I recall the correct algorithm differently. Let me look at a well-known Python implementation (from the `validate-docbr` package):

```python
class CNS:
    def validate(self, cns):
        cns = self._only_digits(cns)
        if len(cns) != 15 or not all(c in "0123456789" for c in cns):
            return False
        if cns[0] in "789":
            return self._validate_provisional(cns)
        return self._validate_definitive(cns)

    def _validate_definitive(self, cns):
        # First 11 digits + check digit via mod 11
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0

    def _validate_provisional(self, cns):
        # weights 15..2 for first 14 digits? 
```

Hmm. Let me actually recall the validate-docbr implementation:

```python
def validate(self, cns):
    cns = self.only_digits(cns)
    if len(cns) != 15:
        return False
    if cns[0] in "789":
        return self.validate_provisional(cns)
    return self.validate_definitive(cns)

def validate_definitive(self, cns):
    soma = 0
    for i in range(15):
        soma += int(cns[i]) * (15 - i)
    return soma % 11 == 0

def validate_provisional(self, cns):
    soma = 0
    for i in range(15):
        soma += int(cns[i]) * (15 - i)
    resto = soma % 11
    if resto != 0:
        dv = 11 - resto
        if dv > 9:
            soma = soma + 2
            resto = soma % 11
            dv = 11 - resto
    else:
        dv = 0  # ??? 
    return dv == int(cns[14])
```

Hmm, I'm not 100% sure about the resto==0 case. Let me think mathematically. 

Actually, I found it. The official algorithm from DATASUS (documented in the "Manual de validação do CNS"):

For provisory cards (starting with 7, 8, 9):
1. soma = Σ (digit_i × peso_i) where peso goes from 15 to 1 (15 digits, weights 15,14,...,1)
2. resto = soma % 11
3. If resto != 0: dv = 11 - resto; if dv > 9: soma = soma + 2; resto = soma % 11; dv = 11 - resto
4. If resto == 0: dv = resto (= 0)
5. The last digit must equal dv

Wait, but if resto == 0 then dv = 0 and the last digit must be 0. Hmm, but actually with weights 15..1, if resto == 0, then... the check digit is 0? That seems odd but plausible.

Hmm, actually I've seen this implementation which handles it:

```python
def validate_provisional(cns):
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    resto = soma % 11
    if resto == 0:
        return int(cns[14]) == 0  # hmm no...
```

OK here's the thing — I should be careful. Since I can't verify the exact algorithm with certainty, let me use the most commonly cited implementation. The most widely cited Python implementation of CNS validation:

```python
def valida_cns(cns):
    """Valida o Cartão Nacional de Saúde (CNS)."""
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    
    # CNS definitivo começa com 1 ou 2; provisório com 7, 8 ou 9
    if cns[0] not in '123789':
        return False
    
    if cns[0] in '12':
        # CNS definitivo: soma ponderada deve ser múltiplo de 11
        soma = sum(int(digito) * peso for digito, peso in zip(cns, range(15, 0, -1)))
        return soma % 11 == 0
    
    # CNS provisório (7, 8, 9)
    soma = sum(int(digito) * peso for digito, peso in zip(cns, range(15, 0, -1)))
    resto = soma % 11
    if resto == 0:
        dv = 0
    else:
        dv = 11 - resto
        if dv > 9:
            soma += 2
            resto = soma % 11
            dv = 11 - resto
    return dv == int(cns[-1])
```

Hmm wait, but there's an issue: if dv > 9 after adding 2 to soma... could dv still be > 9? soma += 2 changes resto by +2 mod 11, so dv = 11 - resto changes by -2. If dv was 10 or 11, after adding 2, dv becomes 8 or 9. So it works.

Actually, hold on. Let me reconsider. I've seen this exact algorithm in the official DATASUS JavaScript:

```javascript
function validaCNS(vlrCNS) {
	var soma = new Number();
	var resto = new Number();
	var dv = new Number();
	var pis = new String();
	var resultado = new String();
	var tamCNS = vlrCNS.length;
	if ((tamCNS) != 15) {
		return (false);
	}
	for (i = 0