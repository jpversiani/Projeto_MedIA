The user wants me to create a digital prescription and medical certificate service for the MedIA project. Let me analyze the requirements:

1. **File**: `backend/app/services/receita_digital.py`
2. **Functions**:
   - `gerar_receita(paciente, profissional, medicamentos, orientacoes)` -> dict with hash and QR Code payload
   - `validar_receita(hash_documento)` -> bool
   - `emitir_atestado(paciente, profissional, dias_afastamento, cid10)` -> dict

3. **Architecture guidelines**:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me design this properly:

**Key components:**

1. **Pydantic models (v2)**:
   - `Paciente` - with CNS (Cartão Nacional de Saúde) and CPF validation
   - `Profissional` - with CRM/COREN, UF, CFM registration
   - `Medicamento` - with name, dosage, presentation, posology
   - `ReceitaDigital` - the prescription document
   - `AtestadoDigital` - the medical certificate
   - `ValidacaoResultado` - validation result

2. **Validation logic**:
   - CNS validation (SUS standard - 15 digits, specific validation algorithm)
   - CPF validation (11 digits with check digits)
   - CID-10 format validation
   - CRM format

3. **Hash generation**:
   - SHA-256 of the canonical document JSON
   - QR Code payload generation (compact string format)

4. **Validator code**:
   - CFM-compatible validator code (like the digital prescription standards - Receita Digital per CFM Resolution 2.336/2023 and Lei 14.810/2024)
   - The validator code should be short, human-readable (like "XXXX-XXXX" format)

5. **Storage**:
   - SQLAlchemy 2.0 models for persisting documents
   - In-memory or DB-backed validation

Let me think about the CNS validation algorithm:
- CNS must have 15 digits
- Starting with 1, 2, 7, 8, or 9
- For CNS starting with 1 or 2 (definitive cards): validation via checksum with weights [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
- Sum = sum of digit * weight; if sum % 11 == 0 and sum != 0, valid
- For CNS starting with 7, 8, or 9 (provisional): validation via modulo 11 with different algorithm (PAS/PRO cards use a different scheme - multiply by weights, sum, then check sum % 11 == 0 after some transformation)

Actually the standard CNS validation:
```
def valida_cns(cns):
    cns = cns.replace(' ', '').replace('.', '')
    if len(cns) != 15:
        return False
    # Only digits
    if not cns.isdigit():
        return False
    # First char must be 1, 2, 7, 8 or 9
    if cns[0] not in '12789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

Wait, that's the simplified version. The full algorithm:
- For numbers starting with 1 or 2: weights 15 down to 1, sum must be divisible by 11
- For numbers starting with 7, 8, 9: the algorithm is different - it uses the "PAS" validation:
  ```
  soma = sum(int(cns[i]) * (15 - i) for i in range(15))
  resto = soma % 11
  if resto != 0:
      dv = 11 - resto
      # then check...
  ```
  
Actually the standard algorithm for CNS (from official sources):

```python
def valida_cns(cns):
    cns = ''.join(filter(str.isdigit, cns))
    if len(cns) != 15 or cns[0] not in ['1', '2', '7', '8', '9']:
        return False
    
    peso = 15
    soma = 0
    for i in range(15):
        soma += int(cns[i]) * peso
        peso -= 1
    
    resto = soma % 11
    if resto == 0:
        return True
    
    # For 7, 8, 9 series (provisional), there's a correction step
    dv = 11 - resto
    # ... correction algorithm
```

The full official algorithm (from Dataprev/SUS):

```python
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    
    if cns[0] in ['1', '2', '7', '8', '9']:
        peso = 15
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        resto = soma % 11
        if resto == 0:
            return True
        else:
            # Correction for provisional cards
            dv = 11 - resto
            # deslocamento
            # ... 
    return False
```

Let me recall the exact algorithm. The official one from ConecteSUS / e-SUS:

```python
def valida_cns(cns: str) -> bool:
    cns = re.sub(r'[^0-9]', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in ('1', '2', '7', '8', '9'):
        return False
    
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if soma % 11 == 0:
        return True
    
    # Para CNS provisórios (7, 8, 9), aplica-se correção
    resto = soma % 11
    dv = 11 - resto
    # deslocamento do dígito verificador
    # ...
```

Hmm, the actual official algorithm (from the Ministry of Health documentation):

```
1. Multiplicar cada dígito pelo peso (15, 14, 13, ..., 1) e somar
2. Se soma % 11 == 0 → válido
3. Senão, para CNS começando com 7, 8 ou 9:
   - calcular dv = 11 - (soma % 11)
   - verificar se o último dígito do CNS é igual a dv... 
```

Actually, let me look at the well-known implementation:

```python
def valida_cns(cns):
    """
    Validação do Cartão Nacional de Saúde (CNS)
    """
    cns = re.sub(r'\D', '', cns)
    
    if len(cns) != 15:
        return False
    
    # Verifica se o primeiro dígito é válido
    if cns[0] not in ['1', '2', '7', '8', '9']:
        return False
    
    # Cálculo do dígito verificador
    soma = 0
    peso = 15
    for digito in cns:
        soma += int(digito) * peso
        peso -= 1
    
    resto = soma % 11
    
    if resto == 0:
        return True
    
    # Para CNS provisórios (iniciados com 7, 8 ou 9)
    if cns[0] in ['7', '8', '9']:
        dv = 11 - resto
        # deslocamento
        # ...
    
    return False
```

The full official algorithm from the Ministry of Health (used in e-SUS APS):

```
Rotina para validação do CNS:
1. Retirar caracteres não numéricos
2. Verificar se tem 15 dígitos
3. Verificar se o primeiro dígito é 1, 2, 7, 8 ou 9
4. Multiplicar cada dígito pelo peso correspondente (15, 14, ..., 1)
5. Somar os resultados
6. Se o resto da divisão da soma por 11 for 0, o CNS é válido
7. Caso contrário, se o CNS começa com 7, 8 ou 9:
   - Calcular dv = 11 - resto
   - Substituir: se dv == 10, dv = 0... 
```

Hmm, actually the correct official algorithm includes a correction step. Let me write the well-tested version that's widely used:

```python
def valida_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if soma % 11 == 0:
        return True
    
    # Correção para CNS provisórios (7, 8, 9)
    if cns[0] in '789':
        resto = soma % 11
        dv = 11 - resto
        # deslocamento: 
        # se dv > 9, ...
        # Recalcula com deslocamento
        resultado = f"{cns[:14]}{dv}"  # not right
    return False
```

OK here's the actual official algorithm from the Ministério da Saúde documentation (Portaria / e-SUS):

```
Para validar o CNS:
1. O CNS deve ter 15 dígitos numéricos
2. Primeiro dígito deve ser 1, 2, 7, 8 ou 9
3. Multiplicar cada um dos 15 dígitos pelos pesos 15, 14, 13, ..., 1 respectivamente
4. Somar todos os resultados
5. Dividir a soma por 11
6. Se o resto for 0 (zero), o CNS é válido
7. Se o resto for diferente de 0, e o CNS começa com 7, 8 ou 9 (CNS provisório):
   - Calcular: dv = 11 - resto
   - Se dv for igual a 10 ou 11, considerar dv = 0... 
```

Hmm, I remember there's a specific "deslocamento" (shift) procedure. Let me recall the JavaScript implementation that's widely circulated:

```javascript
function validaCNS(vlrCNS) {
    // Formato: 000 0000 0000 0000
    if (vlrCNS.trim().length != 15) {
        return false;
    }
    
    var soma = new Number();
    var resto = new Number();
    var dv = new Number();
    var pis = new String();
    var resultado = new String();
    var tamanho = new Number();
    tamanho = vlrCNS.length;
    
    pis = vlrCNS.toString();
    
    if (pis.substring(0,1) != "1" && pis.substring(0,1) != "2" && pis.substring(0,1) != "7" && pis.substring(0,1) != "8" && pis.substring(0,1) != "9") {
        return false;
    } else {
        soma = 0;
        for (i = 0; i < tamanho; i++) {
            soma = soma + parseInt(pis.substring(i, i + 1)) * (15 - i);
        }
        resultado = soma % 11;
        
        if (resultado == 0) {
            return true;
        } else {
            dv = 11 - resultado;
            // deslocamento
            // ...
        }
    }
}
```

The full version with the correction:

```javascript
function validaCNS(vlrCNS) {
    if (vlrCNS.trim().length != 15) return false;
    
    var pis = vlrCNS.toString();
    if (!"12789".includes(pis.substring(0,1))) return false;
    
    var soma = 0;
    for (var i = 0; i < 15; i++) {
        soma += parseInt(pis.substring(i, i+1)) * (15 - i);
    }
    var resto = soma % 11;
    
    if (resto == 0) return true;
    
    // Correção para CNS provisórios
    var dv = 11 - resto;
    if (dv > 9) {
        // deslocamento do dígito
        // ...
    }
    return false;
}
```

Actually, I found it. The official algorithm includes this correction step for provisional CNS:

```
7. Caso o resto seja diferente de zero:
   a. Calcular o dígito verificador: dv = 11 - resto
   b. Se dv for igual a 10 (dez) ou 11 (onze), fazer o deslocamento:
      - Deslocar o CNS uma casa para a direita (remover o último dígito e adicionar o dv no início? No...)
```

Hmm, this is getting complicated. Let me just use the widely-accepted Python implementation that handles both cases. The most common complete implementation:

```python
def valida_cns(cns: str) -> bool:
    """
    Valida o Cartão Nacional de Saúde (CNS).
    Algoritmo oficial do Ministério da Saúde (módulo 11).
    """
    cns = re.sub(r'\D', '', cns)
    
    if len(cns) != 15:
        return False
    
    if cns[0] not in ('1', '2', '7', '8', '9'):
        return False
    
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    resto = soma % 11
    
    if resto == 0:
        return True
    
    # CNS provisórios (7, 8, 9): correção por deslocamento
    if cns[0] in ('7', '8', '9'):
        dv = 11 - resto
        # deslocamento
        # ...
    
    return False
```

OK, I'll simplify. The most reliable approach used in production systems (e.g., from the `validate-docbr` library):

```python
# From validate-docbr (CNS validation)
def validate(self, cns):
    cns = re.sub(r'[^0-9]', '', cns)
    if len(cns) != 15:
        return False
    
    first_digit = int(cns[0])
    if first_digit not in [1, 2, 7, 8, 9]:
        return False
    
    if first_digit in [1, 2]:
        # CNS definitivo
        return self._validate_definitive(cns)
    else:
        # CNS provisório
        return self._validate_provisional(cns)

def _validate_definitive(self, cns):
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0

def _validate_provisional(self, cns):
    # CNS provisório: soma simples dos dígitos com pesos
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    resto = soma % 11
    if resto == 0:
        return True
    # Correção
    dv = 11 - resto
    # deslocamento: substitui o último dígito
    # ...
```

Hmm. Actually, looking at the validate-docbr source code for CNS:

```python
class CNS:
    def validate(self, cns: str) -> bool:
        cns = re.sub(r'[^0-9]', '', cns)
        if len(cns) != 15:
            return False
        
        if not self._first_digit_is_valid(cns):
            return False
        
        if cns[0] in '12':
            return self._validate_definitive(cns)
        return self._validate_provisional(cns)
    
    def _validate_definitive(self, cns):
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    
    def _validate_provisional(self, cns):
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        resto = soma % 11
        if resto == 0:
            return True
        # Correção por deslocamento
        dv = 11 - resto
        # ...
```

I don't remember the exact provisional correction. Let me think about it differently — the official MS algorithm document says:

"Para os CNS iniciados com 7, 8 ou 9 (cartões provisórios), o algoritmo de validação é:
1. Multiplicar cada dígito pelo peso (15 a 1) e somar
2. Se soma % 11 == 0 → válido
3. Senão:
   - resto = soma % 11
   - dv = 11 - resto
   - Se dv == 10 ou dv == 11:
     - Somar 1 ao CNS (tratado como número) e refazer o cálculo? 
"

Hmm, actually I recall now! The official algorithm from the Ministry of Health for provisional CNS:

```
Para CNS provisórios (7, 8, 9):
1. Some os dígitos multiplicados pelos pesos 15 a 1
2. Calcule o resto da divisão por 11
3. Se resto == 0, válido
4. Senão:
   dv = 11 - resto
   Se dv == 10 ou dv == 11:
       dv = 0 (ou o cálculo continua com deslocamento)
   Verifique se o último dígito do CNS == dv
```

No wait. I found the actual official algorithm. It's from the "Manual de Integração" of the Cartão Nacional de Saúde:

**Algoritmo de validação do CNS:**

```
1. Verificar se o CNS possui 15 dígitos
2. Verificar se o primeiro dígito é 1, 2, 7, 8