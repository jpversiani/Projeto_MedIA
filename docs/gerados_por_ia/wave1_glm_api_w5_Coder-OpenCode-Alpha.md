The user wants me to create a FastAPI telemedicine API file for the MedIA project (Primary Health Care and Telemedicine for SUS - Brazilian Unified Health System). Let me analyze the requirements:

1. **POST /agendamentos**: receives TeleconsultaCreate, generates room code and persists Teleconsulta
2. **GET /salas/{codigo_sala}**: returns virtual room data and consultation status
3. **POST /iniciar-chamada**: changes status to EM_ANDAMENTO
4. **POST /finalizar-chamada**: receives SOAP data and finalizes

Requirements:
- Use `Depends(get_db)` from `app.core.database`
- Import models from `app.models.telemedicina`
- Import schemas from `app.schemas.telemedicina`
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Test coverage with pytest

Since the task says "crie o arquivo backend/app/api/v1/telemedicina.py", I should focus on that file, but to make it complete and executable, I should probably also provide the supporting files (models, schemas, database) since they're referenced. The instruction says "Forneça o código completo e executável. Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo".

Let me think about what files I need:

1. `backend/app/api/v1/telemedicina.py` - the main file requested
2. `backend/app/models/telemedicina.py` - SQLAlchemy models (referenced)
3. `backend/app/schemas/telemedicina.py` - Pydantic schemas (referenced)
4. `backend/app/core/database.py` - database setup with get_db (referenced)
5. Maybe tests: `backend/tests/test_telemedicina.py` - pytest tests

The task explicitly asks for the telemedicina.py API file, but mentions importing from models and schemas. To be "complete and executable", I should provide the supporting files too. Let me create them all.

Let me design the domain:

**Teleconsulta model** (SQLAlchemy 2.0 style):
- id: int (PK)
- codigo_sala: str (unique, generated)
- paciente_id / paciente_cns: str (CNS - Cartão Nacional de Saúde)
- profissional_id / profissional_cpf: str
- unidade_saude_id (UBS - Unidade Básica de Saúde)
- status: enum (AGENDADA, EM_ANDAMENTO, FINALIZADA, CANCELADA, NO_SHOW)
- data_agendamento: datetime
- data_inicio: datetime nullable
- data_fim: datetime nullable
- motivo_consulta / queixa_principal
- SOAP fields: subjetivo, objetivo, avaliacao (with CID-10, CIAP-2), plano
- cid10_principal: str nullable
- ciap2_principal: str nullable
- created_at, updated_at

**Status enum**:
- AGENDADA
- EM_ANDAMENTO
- FINALIZADA
- CANCELADA

**Schemas (Pydantic v2)**:
- TeleconsultaCreate: paciente_cns, profissional_cpf (or IDs), data_agendamento, motivo, modalidade
- TeleconsultaResponse: full data
- SalaVirtualResponse: codigo_sala, status, data_agendamento, participants info
- ChamadaIniciarRequest / response
- FinalizarChamadaRequest: SOAP data (subjetivo, objetivo, avaliacao, plano), cid10, ciap2
- SOAP validation

**Room code generation**: Use `secrets` module to generate a secure code, e.g., 10-char alphanumeric avoiding ambiguous characters (no 0/O, 1/I/L). Format like "MED-XXXXXX-XXXX" or just a token. Let me use secrets.token_hex or a custom alphabet.

**Validators**:
- CNS validation: CNS has a known check-digit algorithm (either starting with 1/2 or 7/8/9). Let me implement it.
- CPF validation: standard check digits.
- CID-10 format: letter followed by 2 digits, optionally dot and more chars. Regex: `^[A-Z]\d{2}(\.\d{1,2})?$`
- CIAP-2: letter followed by 2 digits: `^[A-Z]\d{2}$`

CNS validation algorithm:
For CNS starting with 1, 2, 7, 8, or 9:
- Sum: for first 15 digits, multiply each digit by weight (15 - position index), sum all, mod 11. If remainder == 0, valid.
Actually the algorithm: The CNS has 15 digits. For the first type (1/2): sum = Σ digit[i] * (15 - i) for i in 0..14; if sum % 11 == 0, valid.
For the second type (7/8/9): the digits after the first are transformed: each digit d in positions 1-14 is converted... Actually the standard algorithm:

```
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15 or not cns.isdigit():
        return False
    # Type 1: starts with 1 or 2
    if cns[0] in '12':
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    # Type 2: starts with 7, 8, 9
    if cns[0] in '789':
        # convert: each digit after first... 
        # The algorithm: take the 15 digits, transform: 
        # peso = 15 for first... Actually:
        # For CNS type 2: soma = Σ int(dig[i]) * peso where the digits are transformed
        # Standard implementation:
        soma = 0
        peso = 15
        for i in range(15):
            digito = int(cns[i])
            # transform for type 2
            ...
```

Let me recall the correct algorithm for CNS type 2 (7/8/9):
The validation: multiply digits by weights 15 down to 1, but first transform digits: for each digit d in the CNS (except handling), the transformation is: d' = d if... Hmm.

Actually the standard algorithm (from DATASUS):
```
soma = 0
for i in range(15):
    if i == 0:
        soma += int(cns[i]) * 15  # no...
```

Let me look at a known Python implementation:

```python
def valida_cns(cns: str) -> bool:
    cns = ''.join(filter(str.isdigit, cns))
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    
    if cns[0] in '12':
        soma = sum(int(digito) * peso for digito, peso in zip(cns, range(15, 0, -1)))
        return soma % 11 == 0
    
    # CNS tipo 2 (7, 8, 9)
    # Converte os dígitos: 
    # d' = 0->0? No...
```

The type 2 algorithm: The CNS numbers starting with 7, 8, 9 are validated by converting each digit: the digits are transformed using the mapping where each digit d is replaced by... Actually:

From DATASUS documentation: For CNS starting with 7, 8, 9:
1. Take the 15 digits.
2. Transform each digit: d' = d for... no.

The known algorithm:
```
Para CNS iniciando com 7, 8 ou 9:
- Multiplicar cada dígito pelo peso (15 - posição)
- Antes disso, converter cada dígito: se o dígito for... 
```

Hmm, let me recall the actual implementation from a reliable source:

```python
def _valida_cns(cns):
    """Valida CNS."""
    cns = re.sub(r'[^0-9]', '', cns)
    if len(cns) != 15:
        return False
    
    soma = 0
    for i in range(15):
        digito = int(cns[i])
        if cns[0] in '789':
            # transformação
            digito = ... 
```

Actually, I remember now. The type 2 CNS validation:

```
1. Multiplica cada dígito (da direita para esquerda? não...) 
```

The official algorithm from DATASUS (Rotina de validação do CNS):

Para números que começam com 1 ou 2:
- soma = Σ (dígito_i × peso_i), onde peso vai de 15 a 1
- válido se soma % 11 == 0

Para números que começam com 7, 8 ou 9:
- Primeiro converte cada dígito: dígito convertido = dígito (mas os dígitos são transformados: 0→0? no...)

Hmm, actually I recall: for type 2, the transformation is applied to each digit: multiply by 2 and if result > 9, subtract 9? No, that's Luhn.

Let me think again. The actual DATASUS algorithm for CNS type 2 (7/8/9):

"Para os números que iniciam com 7, 8 ou 9, a rotina de validação é:
1. Multiplicar cada dígito, da direita para a esquerda, alternadamente por 5 e 4? ..."

Hmm no. Let me recall from actual code I've seen:

```python
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15 or len(set(cns)) == 1:
        return False
    if cns[0] in ['1', '2']:
        peso = 15
        soma = 0
        for i in range(15):
            soma += int(cns[i]) * peso
            peso -= 1
        if soma % 11 == 0:
            return True
    elif cns[0] in ['7', '8', '9']:
        # converte cada dígito
        conv = ''
        for digito in cns:
            d = int(digito)
            # transformação: d' = d * 2? 
```

I found it — the actual algorithm for type 2:

"Para os CNS iniciados com 7, 8 ou 9:
- Converter cada dígito do CNS: multiplicar por 2? No...

OK here's the real algorithm from DATASUS documentation (I'm fairly confident now):

Para CNS tipo 2 (iniciados em 7, 8, 9):
1. Cada dígito é convertido: d' = d, mas... 

The actual documented algorithm:
```
Rotina para validação do CNS (7, 8, 9):
1. Multiplicar cada dígito por seu peso correspondente (15, 14, 13, ..., 1)? No — that's the same as type 1 but it doesn't work because type 2 numbers wouldn't validate.

Actually, the correct algorithm:
1. Transformar cada dígito: d' = d × 2, se d' > 9, então d' = d' - 9
2. Somar os dígitos transformados com pesos...
```

Hmm, I genuinely remember there's a digit-doubling step. Let me reconstruct from a known implementation (from the `validate-docbr` Python package):

```python
class CNS:
    def validate(self, cns):
        cns = self._only_digits(cns)
        if len(cns) != 15 or len(set(cns)) == 1:
            return False
        if cns[0] in "12":
            return self._validate_first_type(cns)
        return self._validate_second_type(cns)

    def _validate_first_type(self, cns):
        soma = sum(int(digito) * peso for digito, peso in zip(cns, range(15, 0, -1)))
        return soma % 11 == 0

    def _validate_second_type(self, cns):
        soma = 0
        for digito, peso in zip(cns, range(15, 0, -1)):
            digito_int = int(digito)
            # transformação
            soma += (digito_int * peso) ... 
```

From validate-docbr source:

```python
def _validate_second_type(self, entry: str) -> bool:
    sum = 0
    for position in range(15):
        digit = int(entry[position])
        # multiply odd positions by ... 
```

Actually here's the validate-docbr implementation:

```python
def _validate_second_type(self, cns: str) -> bool:
    soma = 0
    for i in range(15):
        digito = int(cns[i])
        # transforma o dígito
        if ... 
```

OK let me just recall the DATASUS official routine text:

"Rotina de validação do Cartão Nacional de Saúde:

1. Os números do CNS são compostos por 15 dígitos.
2. Para verificar se o número é válido:
   a) Multiplicar cada um dos 15 dígitos pelo peso correspondente: o primeiro dígito por 15, o segundo por 14, e assim sucessivamente até o décimo quinto dígito por 1.
   b) Somar todas as multiplicações.
   c) Dividir o resultado por 11.
   d) Se o resto da divisão for 0, o número é válido.
3. Para os números que iniciam com 7, 8 ou 9:
   a) Antes de aplicar a rotina acima, converter cada dígito: multiplicar o dígito por 2 e, se o resultado for maior que 9, subtrair 9? ..."

Hmm no. The actual conversion for type 2:

From the official documentation (Cartão Nacional de Saúde - Rotina de validação):

"Para os números que iniciam com 7, 8 ou 9, deve-se antes converter cada dígito do número, usando a seguinte tabela:
0 → 0
1 → 2
2 → 4
3 → 6
4 → 8
5 → 0? ..."

Hmm, I think the conversion is: d' = (d × 2) mod 9? Let me think...

Actually! I remember now. The conversion is: multiply each digit by 2, and if the result has two digits, sum them (or subtract 9). So:
0→0, 1→2, 2→4, 3→6, 4→8, 5→10→1, 6→12→3, 7→14→5, 8→16→7, 9→18→9.

So d' = (2d) mod 9, with 9→0? Wait: 2×9=18, 1+8=9. So 9→9. And 2×0=0→0. So d' = (2d) mod 9 except 9 maps to 9 (since 18 mod 9 = 0, but digit-sum gives 9). Hmm, (2d) mod 9: 0→0, 1→2, 2→4, 3→6, 4→8, 5→1, 6→3, 7→5, 8→7, 9→0. But digit-sum: 9→9. So it's not exactly mod 9.

Actually the standard "doubling" from Luhn: d' = 2d if 2d ≤ 9 else 2d - 9. That gives: 0→0, 1→2, 2→4, 3→6, 4→8, 5→1, 6→3, 7→5, 8→7, 9→9. Yes! That matches digit-sum for all: 18→1+8=9 ✓, 16→7 ✓, 14→5 ✓, 12→3 ✓, 10→1 ✓. So d' = 2d if 2d ≤ 9 else 2d - 9.

Then after conversion, apply the same weighted sum (15 down to 1) and check mod 11 == 0.

Let me verify with a known valid CNS type 2. Hmm, I don't have one memorized. Let me just trust this algorithm — it's the one used in validate-docbr:

```python
def _validate_second_type(self, entry: str) -> bool:
    sum = 0
    for position in range(len(entry)):
        digit = int(entry[position])
        # multiply by weight
        weight = 15 - position
        # transform digit
        digit = digit * 2 if digit * 2 <= 9 else digit * 2 - 9
        sum += digit * weight
    return sum % 11 == 0
```

Hmm wait, actually I need to double check the order: transform first, then multiply by weight? Or multiply then transform? Let me think about the official doc:

Official DATASUS routine (I'm now recalling more precisely):

"Para os números que iniciam com 7, 8 ou 9:
1. Multiplicar cada dígito por 2.
2. Se o resultado for maior que 9, subtrair 9.
3. Multiplicar cada dígito convertido pelo peso (15 a 1).
4. Somar e verificar se módulo 11 == 0."

Hmm, actually I've seen the implementation differently. Let me look at what I remember from validate-docbr's actual source code:

```python
def _validate(self, cns: str) -> bool:
    ...
def _validate_cns(self, cns: str) -> bool:
    weight = 15
    sum = 0
    for digit in cns:
        sum += int(digit) * weight
        weight -= 1
    return sum % 11 == 0

def _validate_cns_second_type(self, cns: str) -> bool:
    # first convert
    converted = ""
    for digit in cns:
        d = int(digit)
        converted += str(d * 2) if d * 2 <= 9 else str(d * 2 - 9)
    ...
```

Hmm, wait. Actually I recall the validate-docbr implementation:

```python
def _validate_second_type(self, entry