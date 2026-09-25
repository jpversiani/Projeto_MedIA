The user wants me to create a FastAPI telemedicine API file for the MedIA project (Brazilian SUS Primary Healthcare and Telemedicine context). Let me analyze the requirements:

1. **POST /agendamentos**: receives `TeleconsultaCreate`, generates room code, persists `Teleconsulta`
2. **GET /salas/{codigo_sala}**: returns virtual room data and consultation status
3. **POST /iniciar-chamada**: changes status to `EM_ANDAMENTO`
4. **POST /finalizar-chamada**: receives SOAP data and finalizes

Requirements:
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Use `Depends(get_db)` from `app.core.database`
- Import models from `app.models.telemedicina` and schemas from `app.schemas.telemedicina`
- Complete, executable code
- Test coverage with pytest

Since the task says "importe os modelos de app.models.telemedicina e schemas de app.schemas.telemedicina", I should assume those exist, but to make the code complete and executable, I might need to also provide those files (or at least show them). The instruction says "Forneça o código completo e executável. Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo".

The main task is to create `backend/app/api/v1/telemedicina.py`. But to be complete and executable, I should probably also provide the supporting files: models, schemas, and maybe the database module, plus tests. However, the task says "importe os modelos de app.models.telemedicina e schemas de app.schemas.telemedicina" — implying those exist. But to be truly executable, providing them makes sense. Let me think about the balance.

The primary deliverable is the API file. But the instruction "Forneça o código completo e executável" suggests I should provide everything needed. I'll provide:

1. `backend/app/api/v1/telemedicina.py` — the main file (primary deliverable)
2. `backend/app/models/telemedicina.py` — SQLAlchemy models (needed for imports)
3. `backend/app/schemas/telemedicina.py` — Pydantic v2 schemas (needed for imports)
4. `backend/app/core/database.py` — get_db dependency (referenced)
5. Tests: `backend/tests/test_telemedicina_api.py` — pytest coverage

Actually, let me be careful. The task says "importe os modelos de app.models.telemedicina e schemas de app.schemas.telemedicina" — this implies these files exist in the project. But since I'm the coder agent and the instruction says "código completo e executável", I should provide them to ensure executability. I'll provide all supporting files with a note that if they already exist in the project, the API file is the main deliverable and the others are reference implementations matching the expected contracts.

Let me design the system:

### Domain: Telemedicina no SUS / APS

**Teleconsulta** (teleconsultation) model:
- `id`: UUID or int PK
- `codigo_sala`: unique room code (e.g., generated with secrets)
- `paciente_id`: FK to patient
- `profissional_id`: FK to professional
- `data_agendamento`: scheduled datetime
- `status`: enum — AGENDADA, EM_ANDAMENTO, FINALIZADA, CANCELADA, NAO_COMPARECEU
- `motivo_consulta`: reason
- `cid10`: optional CID-10 code
- `ciap2`: optional CIAP-2 code
- SOAP fields: `soap_subjetivo`, `soap_objetivo`, `soap_avaliacao`, `soap_plano`
- `cns_paciente` (Cartão Nacional de Saúde), `cpf_paciente` maybe
- timestamps: `criado_em`, `atualizado_em`, `iniciada_em`, `finalizada_em`
- `duracao_minutos` maybe computed

**Enums**:
- `StatusTeleconsulta`: AGENDADA, EM_ANDAMENTO, FINALIZADA, CANCELADA, NAO_COMPARECEU
- Maybe `ModalidadeTeleconsulta`: VIDEO, AUDIO, CHAT

**Schemas (Pydantic v2)**:
- `TeleconsultaCreate`: paciente_id, profissional_id, data_agendamento, motivo_consulta, modalidade, cns_paciente (validated), cpf_paciente (validated)
- `TeleconsultaResponse`: full response
- `SalaVirtualResponse`: codigo_sala, status, data_agendamento, participantes, links (maybe)
- `IniciarChamadaRequest` / `IniciarChamadaResponse`
- `FinalizarChamadaRequest`: SOAP data — soap_subjetivo, soap_objetivo, soap_avaliacao, soap_plano, cid10, ciap2, duracao_minutos, condutas, prescricao?
- Validators: CNS validation (algorithm), CPF validation (check digits), CID-10 format, CIAP-2 format (letter + 2 digits)

**CNS validation algorithm** (Brazilian Cartão Nacional de Saúde):
The CNS must have 15 digits starting with 1, 2, 7, 8, or 9. Validation via checksum:
- For CNS starting with 1 or 2 (definitive): sum of digits with weights [1,2,3,4,5,6,7,8,9,1,2,3,4,5,6]... Actually the standard algorithm:

CNS validation (pseudocode):
```
soma = 0
for i, digit in enumerate(cns):
    if i % 2 == 0:  # positions 0,2,4...
        soma += int(digit) * 1  # hmm
```

The official algorithm:
```
soma = 0
for i in range(15):
    if i % 2 == 0:
        peso = 1  # hmm no
```

Let me recall the correct CNS validation algorithm:

```
def valida_cns(cns):
    cns = cns.replace('.', '').replace(' ', '')
    if len(cns) != 15:
        return False
    if cns[0] not in '123789':  # actually 1,2,7,8,9
        return False
    # ...
    soma = 0
    for i in range(15):
        digito = int(cns[i])
        if i % 2 == 0:
            peso = 1  # hmm
```

The official algorithm from DATASUS:

```
function validaCNS(cns) {
  if (cns.trim().length !== 15) return false;
  if (!/^[1-9]/.test(cns)) ... 
```

Actually the standard algorithm:

```
soma = 0
for i in 0..14:
    if i % 2 == 0:
        soma += int(cns[i]) * 1  # no...
```

Let me recall properly. The CNS check digit algorithm (from DATASUS documentation):

For CNS with 15 digits:
```
soma = 0;
for (i = 0; i < 15; i++) {
    if (i % 2 == 0) {  // even positions (0-based)
        peso = 1;  // hmm no
```

The actual algorithm:

```
function validaCNS(vCNS) {
    var soma = 0;
    var resto = 0;
    var dv = 0;
    var pis = new String;
    pis = vCNS.toString();
    if (pis.trim().length != 15) {
        return (false);
    }
    // ...
    soma = 0;
    for (i = 0; i < 15; i++) {
        if (i % 2 == 0) {  // hmm
```

OK let me recall the real one. The DATASUS JavaScript validation:

```javascript
function validaCNS(vCNS) {
	var soma = new Number;
	var resto = new Number;
	var dv = new Number;
	var pis = new String;
	var resultado = new String;
	var tamCNS;
	pis = vCNS.toString();
	if (pis.trim().length != 15) {
		return (false);
	}
	// ...
	soma = 0;
	for (i = 0; i < 15; i++) {
		if (i % 2 == 0) {  // hmm no
```

Actually here's the canonical algorithm:

```javascript
function validaCNS(vCNS) {
	var soma = 0;
	var resto = 0;
	var dv = 0;
	var pis = "";
	var resultado = "";
	var tamCNS = "";
	pis = vCNS.toString();
	if (pis.trim().length != 15) {
		return (false);
	}
	// Se não estiver no intervalo [1,2,7,8,9]
	if (("123789".indexOf(pis.substr(0,1),0) == -1)) {
		return (false);
	}
	// Cálculo do dígito verificador
	soma = 0;
	for (i = 0; i < 15; i++) {
		if (i % 2 == 0) {  // hmm
```

Hmm, I remember the algorithm uses multiplication alternating: for CNS, the weights are: multiply digits at odd positions... Let me think about the actual known algorithm:

The CNS validation (from DATASUS):

```
soma = 0
for i in range(len(cns)):
    if i % 2 == 0:  # posição par (0, 2, 4, ...)
        peso = 1  # hmm
```

No wait. The actual algorithm is:

```
function validaCNS(cns) {
  if (cns.length !== 15) return false;
  if (!"123789".includes(cns[0])) return false;
  
  let soma = 0;
  for (let i = 0; i < 15; i++) {
    if (i % 2 === 0) {
      soma += parseInt(cns[i]) * 1;  // hmm no
```

I recall the real algorithm multiplies by weights that alternate: 1, 2, 1, 2, ... Actually:

The official algorithm (from the DATASUS document "Validação do CNS"):

```
Para validar o CNS:
1. O CNS deve ter 15 caracteres numéricos
2. O primeiro dígito deve ser 1, 2, 7, 8 ou 9
3. Cálculo do DV:
   soma = 0
   para cada dígito i (de 0 a 14):
       se i é par: multiplica por 1... 
```

Hmm, actually I remember it now. The algorithm:

```
soma = 0;
for (i = 0; i < 15; i++) {
    if (i % 2 == 0) {
        // posição par: multiplica o dígito por 1 e soma cada algarismo do produto? 
```

No — here's the real one, I'm fairly confident:

```javascript
function validaCNS(vCNS) {
	var soma = new Number;
	var resto = new Number;
	var dv = new Number;
	var pis = new String;
	var resultado = new String;
	var tamCNS;
	pis = vCNS.toString();
	if (pis.trim().length != 15) {
		return (false);
	}
	switch (pis.substr(0,1)) {
		case '1':
		case '2':
		case '7':
		case '8':
		case '9':
			break;
		default:
			return (false);
	}
	// Calcula o dígito verificador
	soma = 0;
	for (i = 0; i < 15; i++) {
		if (i % 2 == 0) {  // hmm
```

OK, I'll reconstruct from the known mathematical description instead. The CNS checksum: 

The algorithm is: take the first 11 digits (for the 15-digit CNS, the base is 15 digits where the last is DV... actually the CNS has 15 digits where the last one is the check digit).

The known algorithm (from multiple implementations):

```python
def valida_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in '123789':
        return False
    soma = 0
    for i, digito in enumerate(cns):
        if i % 2 == 0:  # hmm
```

The actual algorithm from DATASUS (I've seen this in multiple repos):

```python
def valida_cns(cns):
    """Valida o Cartão Nacional de Saúde."""
    cns = ''.join(filter(str.isdigit, cns))
    if len(cns) != 15 or cns[0] not in '123789':
        return False
    
    soma = 0
    for i in range(15):
        digito = int(cns[i])
        if i % 2 == 0:  # hmm
            soma += digito * 1  # ???
```

Let me think about it differently. The known algorithm is:

```
soma = 0
for i in range(15):
    if i % 2 == 0:
        peso = 1
    else:
        peso = 2
    produto = int(cns[i]) * peso
    # se produto > 9, soma os algarismos do produto
    soma += produto // 10 + produto % 10  # hmm
```

Hmm, that resembles the Luhn-like algorithm. Actually yes! The CNS validation is similar to a mod-11 with alternating weights 1 and 2, where products > 9 have their digits summed:

The official DATASUS algorithm:

```
function validaCNS(vCNS) {
    ...
    soma = 0;
    for (i = 0; i < 15; i++) {
        if (i % 2 == 0) {  // hmm, no
```

OK here's what I actually remember clearly from implementations I've seen:

```javascript
function validaCNS(vCNS) {
	var soma = new Number;
	var resto = new Number;
	var dv = new Number;
	var pis = new String;
	var resultado = new String;
	var tamCNS;
	pis = vCNS.toString();
	if (pis.trim().length != 15) {
		return (false);
	}
	switch (pis.substr(0, 1)) {
		case '1':
		case '2':
		case '7':
		case '8':
		case '9':
			break;
		default:
			return (false);
	}
	pis = pis.trim();
	soma = 0;
	for (var i = 0; i < 15; i++) {
		soma += parseInt(pis.substr(i, 1)) * (15 - i);  // ??? no
	}
```

Hmm no. Let me recall the actual documented algorithm from the Ministry of Health:

**Algoritmo de validação do CNS (Documento oficial MS/DATASUS):**

```
1. O número do CNS deve possuir 15 dígitos;
2. Os dígitos devem ser numéricos;
3. O primeiro dígito deve estar entre 1, 2, 7, 8 e 9;
4. Para calcular o dígito verificador:
   - Multiplicar cada um dos 15 dígitos pela sequência de pesos 15, 14, 13, ..., 1
   - Somar os resultados
   - O resultado deve ser divisível por 11
```

Yes! That's it. The CNS validation: sum of each digit multiplied by its weight (15 for the first digit, 14 for the second, ..., 1 for the last) must be divisible by 11. That's the well-known algorithm:

```python
def valida_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in '123789':
        return False
    soma = sum(int(d) * peso for d, peso in zip(cns, range(15, 0, -1)))
    return soma % 11 == 0
```

Yes, this is the correct official algorithm. I'm confident about this one — the "pesos de 15 a 1, soma divisível por 11" is the documented CNS validation.

**CPF validation**: standard mod-11 check digits. I'll implement it.

**CID-10 format**: letter followed by 2 digits, optionally .X (e.g., "I10", "J45.0"). Regex: `^[A-Z]\d{2}(\.\d{1,2})?$`

**CIAP-2 format**: letter followed by 2 digits (e.g., "A01", "K29"). Regex: `^[A-Z]\d{2}$` — actually CIAP-2 codes are chapter letter + 2 digits, e.g., "A01", "R05", "K29". Some have 3 digits? CIAP-2 codes are letter + 2 digits (e.g., A01, B02... K86). Yes, letter + 2 digits.

**Room code generation**: use `secrets.token_urlsafe` or a readable format like "TC-XXXXXXXX". For telemedicine rooms, something like `secrets.token_hex(4).upper()` → 8 hex chars, or a format like "MED-XXXX-XXXX". I'll generate something like `f"TC-{secrets.token_hex(4).upper()}"` → e.g., "TC-A1B2C3D4". Or use `secrets.choice` with alphabet excluding ambiguous chars. Let me do: 8 chars from alphabet "ABCDEFGHJKLMNPQRSTUVWXYZ23456789" (no 0/O, 1/I) in format "XXXX-XXXX". That's professional.

**Endpoints**:

1. `POST /agendamentos` — body: `TeleconsultaCreate`. Generates room code, persists, returns `TeleconsultaResponse` with status 201. Validate: patient exists? Since we may not have patient model, we can validate CNS/CPF format via schema validators. Business rules: data_agendamento must be future. Maybe check for scheduling conflicts for the professional. I'll add a conflict check (same professional, overlapping time, status not CANCELADA) — that's good engineering. Hmm, but that requires querying. Let me include a simple conflict check: same professional with data_agendamento within ±30 min window and