The user wants me to implement a WebSocket Hub for teleconsultation and WebRTC signaling for a healthcare project (MedIA) for the Brazilian SUS (Sistema Único de Saúde). Let me analyze the requirements:

1. **File**: `backend/app/api/v1/telemedicina_ws.py`
2. **WebSocket endpoint**: `/ws/telemedicina/sala/{codigo_sala}`
3. **Features**:
   - SDP message exchange (offer/answer)
   - ICE candidates
   - Medical/patient state synchronization in telehealth room
4. **Standards**:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS patterns (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me design this properly:

### Architecture Design

**WebSocket Hub for Telemedicine**:

1. **Connection Manager**: Manages active WebSocket connections per room
2. **Room State**: Tracks participants (medico/paciente), their roles, connection states
3. **Message Types**:
   - WebRTC signaling: `offer`, `answer`, `ice_candidate`
   - Room management: `join`, `leave`, `participant_joined`, `participant_left`
   - Medical state sync: SOAP notes updates, CIAP-2 codes, CID-10 codes
   - Control: `mute_audio`, `toggle_video`, `end_call`, etc.

4. **Security**:
   - Authentication via token (query param or first message)
   - CNS/CPF validation
   - Role-based access (medico vs paciente)
   - Audit logging (LGPD compliance for health data)

5. **Pydantic Models** (v2):
   - `WebSocketMessage` base with discriminated unions
   - `SDPOffer`, `SDPAnswer`, `ICECandidate`
   - `JoinRoom`, `LeaveRoom`
   - `SOAPUpdate`, `DiagnosticoUpdate` (CIAP-2, CID-10)
   - `EstadoSala` (room state)

6. **SQLAlchemy 2.0**:
   - Models for `SalaTelemedicina`, `ParticipanteSala`, `RegistroTeleconsulta`
   - Async engine/session

7. **Validation**:
   - CNS (Cartão Nacional de Saúde) validation - 15 digits with check digit algorithm
   - CPF validation - 11 digits with check digits
   - CIAP-2 codes: letter + 2 digits (e.g., "A01", "K29")
   - CID-10 codes: letter + 3-4 chars (e.g., "A90", "J45.0")

Let me write the CNS validation algorithm:
- CNS can start with 1, 2, 7, 8, or 9
- For CNS starting with 1 or 2 (definitive): sum with weights 15,14,13,...,2; the result must be divisible by 11
- For CNS starting with 7, 8, 9 (temporary): algorithm with weights 15 to 2, sum, mod 11, if result == 0 then... Actually the algorithm: soma = sum(digit[i] * (15-i)); if soma % 11 == 0 and last digit combination... Let me recall properly.

CNS validation:
```
def valida_cns(cns: str) -> bool:
    cns = ''.join(filter(str.isdigit, cns))
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    # Definitive cards (1,2) or temporary (7,8,9)
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if soma % 11 == 0:
        return True
    return False
```

Actually the standard algorithm:
- Weights: 15, 14, 13, ..., 1? No. Let me recall: pesos = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]? 

The official algorithm for CNS:
```
soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
resto = soma % 11
if resto == 0:
    return True
else:
    return False
```

Hmm, actually the official one is:
```
peso = 15
soma = 0
for each digit:
    soma += digito * peso
    peso -= 1
resto = soma % 11
if resto != 0: invalid
```

Yes, that's right - weights from 15 down to 1, sum must be divisible by 11. Wait, but there's a subtlety: for cards starting with 7, 8, 9, the validation is different. Let me check.

The official CNS validation (from DATASUS):

```
- Necessário possuir 15 dígitos;
- Os números pertencentes à sequência 1, 2, 7, 8 ou 9;
- O número deve ser validado através do algoritmo de módulo 11;

1) Multiplicar cada dígito pelo seu peso, considerando que o peso mais à esquerda é 15:
   15, 14, 13, ..., 2, 1? 
```

Actually the official routine from DATASUS (Rotinas de validação):

```
function ValidaCNS(vCNS: string): boolean;
var
  i, soma, resto, resultado: integer;
begin
  Result := False;
  if Length(vCNS) <> 15 then Exit;
  
  soma := 0;
  for i := 1 to 15 do
    soma := soma + StrToInt(vCNS[i]) * (16 - i);
  
  resto := soma mod 11;
  if resto <> 0 then
    resultado := 11 - resto
  else
    resultado := 0;
  
  if resultado = StrToInt(vCNS[15]) then... 
```

Hmm, no. Let me just recall the Python implementation commonly used:

```python
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15 or cns[0] not in '12789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

Wait, weights 15 down to 1? Let me verify with a known valid CNS. A commonly cited valid CNS: "000 0000 0000 0000"? No.

Common test: CNS "116 809 515 400 024"? Let me compute: digits: 1,1,6,8,0,9,5,1,5,4,0,0,0,2,4. Weights 15..1: 1*15 + 1*14 + 6*13 + 8*12 + 0*11 + 9*10 + 5*9 + 1*8 + 5*7 + 4*6 + 0*5 + 0*4 + 0*3 + 2*2 + 4*1 = 15+14+78+96+0+90+45+8+35+24+0+0+0+4+4 = 413. 413 % 11 = 413 - 37*11 = 413 - 407 = 6. Not divisible. Hmm.

Let me try another known valid CNS: "700 0000 0000 0000"? 

Actually, the official algorithm from DATASUS documentation (Manual de Rotinas e Procedimentos):

Para CNS definitivos (começam com 1 ou 2) e provisórios (7, 8, 9):

```
Soma = (15×d1) + (14×d2) + ... + (2×d14) + (1×d15)? 
```

Hmm, actually I recall the algorithm being:

```
pesos: 15,14,13,12,11,10,9,8,7,6,5,4,3,2,1? No wait.
```

Let me look at this from the actual DATASUS routine (I remember it from implementations):

```javascript
function validaCNS(cns) {
    cns = cns.replace(/\D/g, '');
    if (cns.length !== 15) return false;
    if ('12789'.indexOf(cns[0]) === -1) return false;
    
    let soma = 0;
    for (let i = 0; i < 15; i++) {
        soma += parseInt(cns[i]) * (15 - i);
    }
    return soma % 11 === 0;
}
```

Hmm, but I've also seen:

```javascript
let soma = 0;
let resto;
for (let i = 0; i < 12; i++) {
    soma += parseInt(cns[i]) * (15 - i);
}
resto = soma % 11;
if (resto !== 0) {
    resto = 11 - resto;
}
// then check dv
```

The official DATASUS algorithm (from "Rotinas de Validação" - CNS):

Actually here's the official one I'm fairly confident about now. From the DATASUS document:

```
Para validar o CNS:
1. O número deve ter 15 caracteres
2. Primeiro dígito: 1, 2, 7, 8 ou 9
3. Cálculo do dígito verificador (DV):
   - Multiplicar cada um dos 15 dígitos pelos pesos 15, 14, 13, ..., 1 (peso 15 para o primeiro dígito, peso 1 para o último)
   - Somar os resultados
   - O resultado da soma deve ser divisível por 11 (resto 0)
```

Hmm wait, but that doesn't work as a "check digit" algorithm because the DV is included in the sum. Actually yes it does — it's a mod-11 self-checking scheme like ISBN-10. The sum of all digits weighted must be ≡ 0 mod 11.

Let me verify with a real example. Known valid CNS examples from documentation: "116 515 856 900 024"? I don't remember exact ones. Let me construct one: take 14 digits and compute the 15th such that sum % 11 == 0.

Take base "1 0 0 0 0 0 0 0 0 0 0 0 0 0" with weights 15..2: sum = 15. Need total % 11 == 0, so DV*1 + 15 ≡ 0 (mod 11) → DV ≡ -15 ≡ -4 ≡ 7 (mod 11). DV = 7. So "100000000000007" should be valid. Sum = 15 + 7 = 22, 22 % 11 = 0. ✓. 

Hmm, but is "100000000000007" a real valid CNS format? The format for definitive cards is like "1XX XXXX XXXX XXXX". The check works mathematically. I'll go with this algorithm — it's the widely used one in Brazilian health software (e.g., pysus-validation, validate-docbr):

From validate-docbr (Python package for Brazilian docs), CNS validation:

```python
class CNS:
    def validate(self, cns):
        cns = self._only_digits(cns)
        if len(cns) != 15:
            return False
        # starting with 7, 8, 9 -> different handling? 
        ...
```

Actually validate-docbr CNS:

```python
def validate(self, cns: str = None) -> bool:
    cns = self._only_digits(cns)
    if len(cns) != 15:
        return False
    if cns[0] in "0123456":  # hmm no
```

Let me just recall the canonical implementation that's widely used:

```python
def validate_cns(cns: str) -> bool:
    """Valida CNS seguindo algoritmo do DATASUS."""
    cns = re.sub(r"[^0-9]", "", cns)
    if len(cns) != 15:
        return False
    if cns[0] not in {"1", "2", "7", "8", "9"}:
        return False
    soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
    return soma % 11 == 0
```

Hmm, wait — for temporary CNS (7, 8, 9), I believe the same mod-11 algorithm applies. Yes, the same algorithm applies to all.

Actually, I found it — the official DATASUS routine (from the "Rotinas gerais de validação - CNS" document):

```
Passos:
1. Formar uma sequência de 15 números, onde cada número ocupa uma posição de 1 a 15
2. Multiplicar cada dígito da sequência pelo seu peso, sendo que o peso da posição 1 é 15, posição 2 é 14, ..., posição 15 é 1
3. Somar todos os resultados
4. Calcular o resto da divisão da soma por 11
5. Se o resto for diferente de zero, o CNS é inválido
```

Yes, this confirms: sum of digit × weight (15 down to 1) must be divisible by 11. 

CPF validation is standard:
```python
def validate_cpf(cpf: str) -> bool:
    cpf = re.sub(r"[^0-9]", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in (9, 10):
        digito = sum(int(cpf[j]) * (i + 1 - j) for j in range(i)) % 11
        # standard: sum of first i digits * weights (i+1 down to 2), d = (soma * 10) % 11
```

Standard CPF:
```python
def _cpf_digito(nove_digitos: str) -> int:
    soma = sum(int(d) * w for d, w in zip(nove_digitos, range(10, 1, -1)))
    resto = (soma * 10) % 11
    return 0 if resto == 10 else resto
```

For 11 digits: first check digit from first 9, second from first 10.

CIAP-2 format: letter (A-Z) + 2 digits, e.g., "K29", "A01". Chapters: A (general), B (digestive), C/D (circulatory), E (endocrine), F (eye), H (ear), K (respiratory), L (musculoskeletal), N (neurological), P (psychological), R (respiratory... no wait). CIAP-2 chapters:
- A: General and unspecified
- B: Blood, blood-forming organs, lymphatic
- C: Cardiovascular (C and D share)
- D: Digestive
- E: Endocrine, metabolic, nutritional
- F: Eye
- H: Ear
- K: Respiratory
- L: Musculoskeletal
- N: Neurological
- P: Psychological
- R: Kidney/urinary... no wait, R is respiratory? No — K is respiratory, R is urology? Let me recall: 
  - A: General
  - B: Blood
  - C/D: Cardiovascular/Digestive
  - E: Endocrine
  - F: Eye
  - H: Ear
  - K: Respiratory (circulatório? no)
  - L: Musculoskeletal
  - N: Neurological
  - P: Psychological
  - R: Urogenital? Hmm, R in CIAP is "Respiratório"? No...

CIAP-2 chapters (WONCA):
- A — General and unspecified
- B — Blood, blood-forming organs and immune mechanism
- C — Cardiovascular... actually C and D: "Cardiovascular" is K? No.

WONCA ICPC-2 chapters:
- A: General and unspecified
- B: Blood, blood-forming organs, lymphatics
- C: Cardiovascular
- D: Digestive
- E: Eye
- F: Ear
- H: ... 

Hmm, ICPC-2: A, B, C, D, E, F, G, H, K, L, N, P, R, S, T, U, W, X, Y, Z.
- A: General and unspecified
- B: Blood, blood-forming organs, lymphatic system
- C: Cardiovascular
- D: Digestive
- E: Eye
- F: Ear
- G: ... no wait.

ICPC-2 chapters:
- A: General and unspecified
- B: Blood, blood-forming organs, lymphatics
- C: Cardiovascular
- D: Digestive
- E: Eye
- F: Ear
- H: ... hmm no, H doesn't exist? 

Let me be careful. ICPC-2 (International Classification of Primary Care, 2nd edition) chapters:
- A: General and unspecified
- B: Blood, blood-forming organs, lymphatic system
- C: Cardiovascular
- D: Digestive
- E: Eye
- F: Ear
- H: ... no. 

Actually: A, B, C, D, E, F, H, K, L, N, P, R, S, T, U, W, X, Y, Z. Where:
- A: General and unspecified
- B: Blood, blood-forming organs, lymphatics
- C: Cardiovascular
- D: Digestive
- E: Eye
- F: Ear
- H: ... hmm, H is missing? No — H doesn't exist in ICPC-2? Wait, K is circulatory? No...

ICPC-2:
- K: Circulatory
- R: Respiratory
- L: Musculoskeletal
- N: Neurological
- P: Psychological
- S: Skin
- T: Endocrine, metabolic, nutritional
- U: Urological
- W: Pregnancy, childbearing, family planning
- X