The user wants me to create a FastAPI module for pharmaceutical dispensing and prescription consumption (baixa de receita) for the MedIA project, related to SUS (Brazilian Unified Health System).

Let me think about what's needed:

1. **File**: `backend/app/api/v1/farmacia.py`
2. **Routes**:
   - `POST /dispensacao/consultar` - validates QR Code/hash of the prescription (receita)
   - `POST /dispensacao/confirmar` - registers total or fractional dispensing of medications in SUS

3. **Requirements**:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me design this properly:

**Domain concepts:**
- Receita (prescription) - issued by a professional, contains items (medications)
- Dispensação (dispensing) - the act of delivering medication at pharmacy
- Baixa (consumption/write-off) - marking the prescription items as dispensed
- Total vs Fracionada (total vs fractional dispensing)
- QR Code/hash validation - the prescription has a hash for validation
- CNS (Cartão Nacional de Saúde) - 15 digits
- CPF - 11 digits
- CID-10 - disease classification codes
- CIAP-2 - primary care classification

**Models (SQLAlchemy 2.0 style):**
Since I'm creating the API file, I should probably also define or reference models. The task says to create `backend/app/api/v1/farmacia.py` with the routes. But for completeness and testability, I might need to show the models too. Let me think about the scope.

The task says: "crie backend/app/api/v1/farmacia.py com rotas FastAPI". So the main deliverable is that file. But to make it work, I need:
- Schemas (Pydantic v2) - could be in `backend/app/schemas/farmacia.py` or inline
- Models (SQLAlchemy) - probably `backend/app/models/...` already exist or need to be defined
- Tests - pytest coverage

Given the instruction "Manter conformidade total e cobertura de testes automatizados com pytest", I should also provide tests. Let me create:

1. `backend/app/api/v1/farmacia.py` - main file (the deliverable)
2. Supporting files that it depends on (models, schemas) - I should define them or at least show them so the code is complete and runnable
3. `backend/tests/api/v1/test_farmacia.py` - tests

Let me think about the architecture:

**Receita model:**
- id (UUID)
- codigo_hash (unique string - the QR code content)
- paciente_id (FK)
- profissional_id (FK)
- unidade_saude_id (FK)
- cid10_codigo (nullable)
- ciap2_codigo (nullable)
- data_emissao
- data_validade
- status: EMITIDA, PARCIALMENTE_DISPENSADA, DISPENSADA (baixa total), EXPIRADA, CANCELADA, VENCIDA
- itens (relationship)

**ReceitaItem model:**
- id
- receita_id (FK)
- medicamento_id (FK) or medicamento description
- dosagem (e.g., "500mg")
- quantidade_prescrita
- quantidade_dispensada (accumulated)
- posologia (e.g., "1 comprimido a cada 8h por 7 dias")
- via_administracao (ORAL, TOPICA, etc.)
- status item: PENDENTE, PARCIAL, ATENDIDO

**Dispensacao model (registro de dispensação):**
- id
- receita_id
- item_id (or items)
- quantidade_dispensada
- farmaceutico_cns / farmaceutico_id
- data_dispensacao
- tipo: TOTAL, FRACIONADA
- observacoes

**Validation logic for consultar:**
1. Hash exists?
2. Receita not expired (data_validade >= today)
3. Status not CANCELADA/DISPENSADA
4. Patient CNS/CPF matches? (maybe optional verification)
5. Return prescription details with pending items

**Validation logic for confirmar:**
1. Same validations as consultar
2. For each item: quantidade solicitada <= quantidade restante
3. Update quantidade_dispensada
4. If all items fully dispensed → status DISPENSADA (baixa total)
5. If some dispensed → PARCIALMENTE_DISPENSADA
6. Create Dispensacao record(s) (audit)
7. Maybe check stock (estoque) - the task mentions "baixa de medicamentos no SUS" which could imply stock write-off too. Let me include stock check/write-off (baixa de estoque) as part of dispensing. Actually "baixa de receita" means closing the prescription. "Baixa de medicamentos" could mean dispensing. Let me include an Estoque model for completeness with stock validation and write-off.

Hmm, but I need to be careful about scope. The task is focused on:
- POST /dispensacao/consultar (validates QR Code/hash)
- POST /dispensacao/confirmar (registers total or fractional dispensing)

Let me keep it focused but complete. I'll include:
- Models: Receita, ReceitaItem, Dispensacao, DispensacaoItem (maybe), Estoque (optional)
- Schemas: Pydantic v2
- Service layer? Could keep logic in the router or a service. For clean architecture, a service layer is nice, but the task asks for the API file. I'll put business logic in a service class within the same file or a separate service file. Given "crie backend/app/api/v1/farmacia.py", I'll make the file self-contained-ish but import models/schemas from their modules. Actually, to make it truly runnable and testable, I should provide the full set of files.

Let me structure the answer:

1. `backend/app/models/farmacia.py` - SQLAlchemy models
2. `backend/app/schemas/farmacia.py` - Pydantic v2 schemas
3. `backend/app/api/v1/farmacia.py` - the router (main deliverable)
4. `backend/tests/test_farmacia.py` or `backend/tests/api/v1/test_farmacia.py` - pytest tests
5. Maybe `backend/app/core/validators.py` for CNS/CPF validation

Also need:
- `backend/app/db/session.py` or similar (I can assume it exists, but for tests I'll define fixtures)
- `backend/app/main.py` to include the router

Let me think about CNS validation:
- CNS must have 15 digits
- Starting with 1, 2, 7, 8, 9 (1/2 = cartões nacionais, 7/8/9 = provisórios/eletrônicos)
- Validation algorithm (mod 11):
  For CNS starting with 1, 2: 
  - Multiply digits by weights 15,14,13,...,2
  - Sum, check sum % 11 == 0
  For CNS starting with 7, 8, 9:
  - Different algorithm: sum = sum of digit * (15 - index)... Actually the algorithm: multiply digits alternately by 5 and 4... Let me recall.

CNS validation algorithm:
- Must be 15 digits
- First digit must be 1, 2, 7, 8, or 9

For CNS starting with 1 or 2:
- pesos = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1] applied to the 15 digits
- soma = sum(digit * weight)
- valid if soma % 11 == 0

For CNS starting with 7, 8, 9:
- The digits are validated with: soma = sum(digit_i * peso_i) where pesos alternate... Actually the standard algorithm:
  - Take first 15 digits
  - soma = d1*5 + d2*4 + d3*3 + d4*2 + d5*1 ... no.

Let me recall the official algorithm for provisório CNS (7,8,9):
```
soma = 0
for i in range(15):
    peso = 15 - i if ... 
```
Hmm. The official algorithm from Ministério da Saúde:

Para CNS que inicia com 1 ou 2:
- Multiplicar cada dígito pelo peso correspondente (15 para o primeiro, 14 para o segundo, ..., 1 para o último... wait, 15 digits with weights 15 down to 1)
- Se o resto da divisão da soma por 11 for 0, é válido.

Para CNS que inicia com 7, 8 ou 9:
- soma = d1*5 + d2*4 + d3*3 + d4*2 + d5*1 + d6*0... no that's not it either.

Actually the official algorithm for 7/8/9:
```
soma = 0
peso = 5
for each digit:
    soma += digito * peso
    peso -= 1
    if peso == 0: peso = 9? 
```
Hmm, let me think. The known implementation:

```python
def valida_cns(cns):
    cns = cns.strip()
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    # ...
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

Wait, that works for 1/2. For 7/8/9 the algorithm is different:

From the official documentation (Cartão Nacional de Saúde - validação):
Para números iniciados em 7, 8 ou 9:
- Multiplicar cada dígito, da esquerda para a direita, alternadamente por 5 e 4... no.

Let me recall the actual known Python implementation that's widely used:

```python
def valida_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] in '12':
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    elif cns[0] in '789':
        # pesos: 5,4,3,2,1,9,8,7,6,5,4,3,2,1,0? 
        ...
```

Hmm, actually I remember the algorithm for 7/8/9:

```
soma = 0
for i, digito in enumerate(cns):
    peso = 15 - i  # no...
```

Let me look at this from memory of the official spec:

"Para os números de CNS iniciados com 7, 8 ou 9, deve-se aplicar a seguinte fórmula:
- Multiplicar cada um dos 15 dígitos por 15 menos a posição (1-based)?"

Actually, I found it in memory. The official algorithm (from Ministério da Saúde / DATASUS):

Para CNS iniciado com 1 ou 2:
1. Multiplica cada dígito pelo peso (15, 14, 13, ..., 1)
2. Soma os resultados
3. Se soma % 11 == 0 → válido

Para CNS iniciado com 7, 8 ou 9:
1. Multiplica cada dígito alternadamente por 5 e 4? No...

The actual algorithm I remember from implementations:

```python
def _valida_cns_provisorio(cns: str) -> bool:
    soma = 0
    peso = 5
    for digito in cns:
        soma += int(digito) * peso
        peso -= 1
        if peso == 0:
            peso = 9  # ??? 
```

Hmm no. Let me think about the real one. I've seen this implementation:

```python
def valida_cns(cns):
    """Valida CNS conforme algoritmo do Ministério da Saúde."""
    cns = ''.join(filter(str.isdigit, cns))
    if len(cns) != 15 or cns[0] not in '12789':
        return False
    
    if cns[0] in '12':
        pesos = list(range(15, 0, -1))
    else:  # 7, 8, 9
        pesos = [5, 4, 3, 2, 1, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]  # ???
```

Hmm, I'm not 100% sure. Let me recall the official document "Validação do Cartão Nacional de Saúde":

The official algorithm (I'm fairly confident about this one now):

Para CNS iniciando com 1 ou 2:
- soma = Σ (dígito_i × peso_i), pesos = 15,14,...,1
- válido se soma % 11 == 0

Para CNS iniciando com 7, 8 ou 9:
- soma = Σ (dígito_i × peso_i), pesos = 5,4,3,2,1,9,8,7,6,5,4,3,2,1,0? That doesn't seem right either because the last weight 0 would ignore the last digit.

Actually! I remember now. The correct algorithm for 7/8/9:

```
soma = d1*5 + d2*4 + d3*3 + d4*2 + d5*1 + d6*9 + d7*8 + d8*7 + d9*6 + d10*5 + d11*4 + d12*3 + d13*2 + d14*1 + d15*0
```

No wait. Hmm.

Let me think about it differently. The widely-cited JavaScript implementation:

```javascript
function validaCNS(cns) {
    cns = cns.replace(/\D/g, '');
    if (cns.length !== 15) return false;
    if (/^[12]/.test(cns)) {
        let soma = 0;
        for (let i = 0; i < 15; i++) {
            soma += parseInt(cns[i]) * (15 - i);
        }
        return soma % 11 === 0;
    } else if (/^[789]/.test(cns)) {
        let soma = 0;
        let peso = 5;
        for (let i = 0; i < 15; i++) {
            soma += parseInt(cns[i]) * peso;
            peso--;
            if (peso === 0) peso = 9;  // ??? 
        }
        ...
    }
}
```

Hmm, I genuinely remember there's a version with pesos cycling. Let me recall the official MS document text:

"Para os números de CNS que se iniciam com os algarismos 7, 8 ou 9, a rotina de validação é:
1) Multiplicar cada dígito, da direita para a esquerda, alternadamente por 5 e 4..." 

Hmm no. OK here's another memory: the official algorithm from the "Manual de instruções - Cartão Nacional de Saúde":

Para CNS iniciado com 7, 8 ou 9:
- soma = Σ dígito_i × peso_i onde pesos são: 5, 4, 3, 2, 1, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0? 

Hmm, actually I think I remember now — I've seen this exact implementation in multiple Brazilian repos:

```python
def valida_cns(cns: str) -> bool:
    cns = re.sub(r"[^0-9]", "", cns)
    if len(cns) != 15:
        return False
    if cns[0] not in "12789":
        return False

    soma = 0
    if cns[0] in "12":
        for i in range(15):
            soma += int(cns[i]) * (15 - i)
        return soma % 11 == 0
    
    # CNS provisório (7, 8, 9)
    pesos = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    # não...
```

OK, let me just search my memory harder. The official algorithm from DATASUS document "Validação do número CNS":

**CNS definitivo (1 ou 2):**
- Peso: 15 14 13 12 11 10 09 08 07 06 05 04 03 02 01
- soma dos produtos deve ser divisível por 11.

**CNS provisório (7, 8 ou 9):**
- Peso: 05 04 03 02 01 09 08 07 06 05 04 03 02 01 00? 

Hmm, no. I recall it being:

- soma = d1×5 + d2×4 + d3×3 + d4×2 + d5×1 + d6×9 + d7×8 + d8×7 + d9×6 + d10×5 + d11×4 + d12×3 + d13×2 + d14×1 + d15×0

Hmm, that gives last digit weight 0 which seems wrong but... Actually wait, I think I remember the actual algorithm now:

For 7/8/9 CNS:
```
soma = 0
peso = 5
for i in range(15):
    soma += digito[i] * peso
    peso = peso - 1
    if peso == 0:
        peso = 9
```
Wait no, that would make pesos: 5,4,3,2,1,9,8,7,6,5,4,3,2,1,0? Let's trace: i=0 peso=5, then peso=4; i=1 peso=4, peso=3; i=2 peso=3→2; i=3 peso=2→1; i=