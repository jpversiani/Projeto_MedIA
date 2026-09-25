The user wants me to create a backend service for offline delta synchronization protocol for mobile units, inspired by the TAM System architecture (Sistema de Atendimento Móvel - likely referring to mobile health units in remote areas). This is for a SUS (Brazilian Unified Health System) context with APS (Atenção Primária à Saúde - Primary Health Care).

Requirements:
1. Create `backend/app/services/sync_offline.py`
2. Implement bidirectional reconciliation protocol with conflict resolution (Last-Write-Wins with version hash)
3. Packaging of offline SOAP attendances in compressed batches
4. Synchronization when 4G/Satellite connection is reestablished
5. Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
6. SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification
7. Full compliance and automated test coverage with pytest

Let me design this carefully:

**Architecture Design:**

1. **Domain Models (Pydantic v2)**:
   - `SOAPAttendance`: SOAP-format attendance (Subjetivo, Objetivo, Avaliação, Plano)
   - `CIAP2Code`: CIAP-2 codes (3 chars, letter + 2 digits)
   - `CID10Code`: CID-10 codes
   - `PatientIdentifier`: CNS/CPF validation
   - `SyncBatch`: compressed batch of attendances
   - `SyncDelta`: delta package for sync
   - `ConflictResolution`: LWW with version hash

2. **Sync Protocol**:
   - Client sends delta with operations (create/update) with `client_version`, `updated_at`, `content_hash`
   - Server compares with `server_version`
   - Conflict resolution: Last-Write-Wins — compare timestamps; if equal timestamps, compare hash for determinism
   - Vector-ish versioning: monotonic version counter + hash

3. **Compression**:
   - Use zlib/gzip to compress batches of SOAP attendances
   - Base64 encoding for transport
   - Chunking for large batches

4. **Connection handling**:
   - Detect connectivity state
   - Queue offline operations
   - Retry with exponential backoff
   - Idempotency keys to avoid duplicates

Let me write the code:

```python
# backend/app/services/sync_offline.py
```

I'll structure it as a comprehensive module. Since the task says "crie backend/app/services/sync_offline.py", I should focus on that file, but also provide supporting pieces (models, schemas, tests) since they ask for full test coverage with pytest.

Let me think about the details:

**CNS validation**: CNS is 15 digits. Validation algorithm:
- Cards starting with 1, 2, 7, 8, 9 (7/8/9 are provisório)
- Algorithm for 1/2: sum with weights 15 down to 2, mod 11, check digit
- For 7/8/9: different algorithm with weights 15 down to 2 but using a different calc (subtract from 11...)

Actually the CNS validation:
- For CNS starting with 1 or 2: pesos = 15,14,13,...,2; soma = sum(digit * peso); resto = soma % 11; dv = 11 - resto; if dv == 11: dv = 0; if dv == 10: invalid (should be provisório format)
- For CNS starting with 7, 8, 9: same weights but dv = resto... Let me recall properly.

CNS validation algorithm (official):
```
For 15-digit CNS:
- First char must be 1, 2, 7, 8, or 9
- For 1/2: 
  soma = Σ (d[i] * (15 - i)) for i in 0..14
  resto = soma % 11
  if resto != 0: invalid
- For 7/8/9:
  soma = Σ (d[i] * (15 - i))
  resto = soma % 11
  if resto == 0: valid
  else:
    soma2 = soma + 2 * ... 
```

Hmm, let me recall the exact algorithm. The standard CNS validation:

```python
def valida_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    # ...
```

The definitive algorithm (from Ministério da Saúde):

```
Tipo 1 (inicia com 1 ou 2):
- soma = Σ peso * dígito, pesos = [15,14,13,12,11,10,9,8,7,6,5,4,3,2,1]
- resto = soma % 11
- válido se resto == 0

Tipo 2 (inicia com 7, 8 ou 9):
- soma = Σ peso * dígito, pesos = [15,14,...,1]
- resto = soma % 11
- if resto == 0: válido
- else: soma2 = soma - resto... 
```

Actually the official algorithm for provisório CNS:

```
1) Multiplicar cada dígito pelo peso (15 até 1)
2) Somar
3) resto = soma % 11
4) Se resto == 0 → válido
5) Senão: recalcular: soma = soma - resto... 
```

Let me look at the well-known implementation:

```python
def valida_cns(cns):
    cns = ''.join(filter(str.isdigit, cns))
    if len(cns) != 15 or cns[0] not in '12789':
        return False
    
    soma = sum(int(d) * p for d, p in zip(cns, range(15, 0, -1)))
    resto = soma % 11
    
    if cns[0] in '12':
        return resto == 0
    else:  # 7, 8, 9
        if resto == 0:
            return True
        # recálculo
        soma = sum(int(d) * p for d, p in zip(cns, range(15, 0, -1)))
        # Actually the algorithm: dv calculation differs
```

The official MS algorithm for CNS provisório (7/8/9):

```
Passo 1: pesos 15 a 1, soma
Passo 2: resto = soma % 11
Passo 3: se resto == 0, válido
Passo 4: senão, soma = soma - resto... no wait
```

Actually here's the official one from DATASUS:

Para CNS que inicia com 1 ou 2:
```
soma = Σ (dígito_i × peso_i), pesos = 15,14,...,1
resto = soma % 11
válido se resto == 0
```

Para CNS que inicia com 7, 8 ou 9:
```
soma = Σ (dígito_i × peso_i), pesos = 15,14,...,1
resto = soma % 11
se resto == 0 → válido
senão:
  dv = 11 - resto
  ... 
```

Hmm, I remember the implementation commonly used:

```python
def valida_cns(cns):
    cns = re.sub(r'[^0-9]', '', cns)
    if len(cns) != 15:
        return False
    if re.match(r'[1-2]', cns[0]):
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    elif re.match(r'[7-9]', cns[0]):
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        resto = soma % 11
        if resto == 0:
            return True
        # Recalculo: 
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        # dv = 11 - resto
        # check last digit == dv? No...
```

The actual official algorithm (Portaria MS):

CNS Provisório (inicia com 7, 8 ou 9):
1. Multiplica cada dígito pelo peso de 15 a 1
2. Soma os resultados
3. Divide por 11, obtém resto
4. Se resto == 0, CNS válido
5. Senão, subtrai o resto de 11 → dv
6. Se dv == 11 → dv = 0... 

Hmm, actually I recall the correct one now. The official validation from MS documentation:

```
Para CNS iniciando com 1 ou 2:
- soma = Σ dígito × peso (pesos 15→1)
- válido se soma % 11 == 0

Para CNS iniciando com 7, 8 ou 9:
- soma = Σ dígito × peso (pesos 15→1)
- resto = soma % 11
- se resto == 0: válido
- senão: 
    dv = 11 - resto
    se dv >= 10: inválido
    senão: verificar se o último dígito do CNS == dv... no
```

Hmm, that doesn't seem right either because the last digit is part of the sum.

Let me think about it differently. The commonly cited Python implementation:

```python
def valida_cns(cns):
    """Valida CNS conforme algoritmo do Ministério da Saúde."""
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15 or cns[0] not in '12789':
        return False

    def soma_ponderada(cns):
        return sum(int(d) * p for d, p in zip(cns, range(15, 0, -1)))

    soma = soma_ponderada(cns)
    resto = soma % 11

    if cns[0] in '12':
        return resto == 0

    # CNS provisório (7, 8, 9)
    if resto == 0:
        return True
    # Recalcula: dv = 11 - resto; soma2 = soma - resto + dv * ... 
```

OK here's the actual official algorithm from the MS manual (Manual de Instruções para preenchimento da CNS):

Para números iniciados com 7, 8 ou 9:
```
1. Some os produtos dos dígitos pelos pesos 15 a 1 → soma
2. resto = soma % 11
3. Se resto == 0 → válido
4. Senão:
   a. dv = 11 - resto
   b. soma2 = soma - resto  (remove contribution?) 
```

Honestly, I've seen this implementation which is widely accepted:

```python
def valida_cns(value: str) -> bool:
    cns = ''.join(re.findall(r'\d', value))
    if len(cns) != 15:
        return False
    if cns[0] not in {'1', '2', '7', '8', '9'}:
        return False

    pesos = range(15, 0, -1)
    soma = sum(int(d) * p for d, p in zip(cns, pesos))
    resto = soma % 11

    if cns[0] in {'1', '2'}:
        return resto == 0

    # Provisório
    if resto == 0:
        return True
    dv = 11 - resto
    # Recalcula com dv no lugar do último dígito
    soma2 = sum(int(d) * p for d, p in zip(cns[:14] + str(dv), pesos))
    return soma2 % 11 == 0
```

Hmm, that's one variant. Actually, the official algorithm per MS:

"Para os números de CNS iniciados com 7, 8 ou 9, o cálculo do dígito verificador é feito da seguinte forma:
1. Multiplica-se cada um dos 14 primeiros números pelo seu peso (15, 14, 13, ..., 2)
2. Somam-se os produtos
3. Divide-se a soma por 11
4. Subtrai-se o resto de 11 → resultado é o dígito verificador
5. Se o dígito verificador for maior que 9, soma-se 2 ao... "

Hmm no. Let me just recall from the actual DATASUS document "Validação do CNS":

```
CARTÃO PROVISÓRIO (inicia com 7, 8 ou 9):
1) Multiplicar cada dígito pelo peso: 15,14,13,12,11,10,9,8,7,6,5,4,3,2,1
2) Somar os produtos
3) Obter o resto da divisão da soma por 11
4) Se o resto for diferente de 0:
   - Subtrair o resto de 11 → dv
   - Se dv > 9 → CNS inválido? 
```

Actually, I found it in memory. The official algorithm from ConecteSUS/MS:

```
Para CNS iniciado com 7, 8 ou 9:
- soma = Σ (dígito × peso), pesos 15 a 1
- resto = soma % 11
- se resto == 0 → válido
- senão → dv = 11 - resto; se dv <= 9 e o CNS termina com dv... 
```

I'm going back and forth. Let me settle on the widely-used implementation from the `validate-docbr` library (brazilian docs validator), which is authoritative-ish:

From `docbr` CNS validation:

```python
def validate(self, doc: str) -> bool:
    inputs = re.findall(r'\d', doc)
    if len(inputs) != 15 or not self._validate_first_digit(inputs):
        return False
    return self._check(inputs)

def _check(self, inputs):
    weights = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    sum_ = sum(int(d) * w for d, w in zip(inputs, weights))
    remainder = sum_ % 11
    if remainder != 0:
        return False
    return True
```

Hmm, but that's only for 1/2. For provisório, docbr does:

```python
def _check(self, inputs):
    weights = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    sum_ = sum(int(d) * w for d, w in zip(inputs, weights))
    remainder = sum_ % 11
    if remainder != 0:
        # provisório: dv = 11 - remainder
        dv = 11 - remainder
        if dv > 9:
            return False
        # replace last digit with dv and recheck
        new_inputs = inputs[:-1] + [str(dv)]
        sum2 = sum(int(d) * w for d, w in zip(new_inputs, weights))
        return sum2 % 11 == 0
    return True
```

Hmm, I genuinely don't remember exactly. Let me simplify: for this task, the CNS validation is a supporting detail. I'll implement the well-known algorithm for 1/2 (definitive cards) and a reasonable provisório check. Actually, let me use the algorithm that I'm most confident about, which is documented in the MS "Manual do Cartão Nacional de Saúde":

Official (from MS document "Validação do número do CNS"):

**CNS Definitivo (inicia com 1 ou 2):**
- Soma = Σ (dígito × peso), pesos: 15, 14, ..., 1
- Resto = Soma % 11
- Válido se Resto == 0

**CNS Provisório (inicia com 7, 8 ou 9):**
- Soma = Σ (dígito × peso), pesos: 15, 14, ..., 1
- Resto = Soma % 11
- Se Resto == 0 → válido
- Senão: dv = 11 - Resto; se dv <= 9, substituir o último dígito pelo dv e refazer o cálculo; válido se novo resto == 0... 

Hmm, that substitution approach seems odd because then the original CNS wouldn't validate.

OK here's another authoritative source I remember — the algorithm from the "Banco de Dados do SUS" (CADSUS) validation pseudocode:

```
FUNÇÃO validaCNS(numCNS)
  SE tamanho <> 15 OU primeiro dígito NÃO ESTÁ EM [1,2,7,8,9] ENTÃO
    RETORNA FALSO
  FIM SE
  
  soma = 0
  PARA i DE 0 ATÉ 14 FAÇA
    soma = soma + dígito[i] × (15 - i)
  FIM PARA
  
  resto = soma MOD 11
  
  SE resto == 0 ENTÃO
    RETORNA VERDADEIRO
  SENÃO
    SE primeiro dígito EM [1,2] ENTÃO
      RETORNA FALSO
    SENÃO  // provisório
      dv = 11 - resto
      SE dv >= 10 ENTÃO
        RETORNA FALSO
      SENÃO
        // recalcula considerando dv
        soma = soma - resto + dv × ... 
```

I'll go with a pragmatic approach: implement the definitive validation (1/2) exactly, and for provisório use the "dv = 11 - resto, check last digit" approach that's most commonly cited:

Actually, you know what — I just remembered the correct official algorithm. It's from the MS:

```
Para CNS provisório (7, 8, 9):
1. Multiplicar cada dígito pelo peso (15 a 1) e somar
2. resto = soma % 11
3. Se resto == 0 → válido
4. Senão:
   dv = 11 - resto
   Se dv == 11 → dv = 0? 
   Se dv >= 10 → inválido
   Senão → válido se o 15º dígito == dv
```

Wait, that can't be right because the 15th digit already