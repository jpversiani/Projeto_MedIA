The user wants me to implement a WebSocket Hub for telemedicine (teleconsultation) with WebRTC signaling for the MedIA project, targeting the Brazilian SUS (Unified Health System). Let me think about what's needed:

1. **File**: `backend/app/api/v1/telemedicina_ws.py`
2. **Endpoint**: WebSocket `/ws/telemedicina/sala/{codigo_sala}`
3. **Features**:
   - SDP message exchange (offer/answer)
   - ICE candidates exchange
   - State synchronization for médico/paciente roles
   - Telehealth room management

4. **Architecture guidelines**:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me design this properly:

### Architecture Design

**WebSocket Hub pattern**: A connection manager that tracks rooms, participants (médico/paciente), and routes signaling messages between them.

**Message types** (WebRTC signaling):
- `join` / `joined` / `peer_joined` / `peer_left`
- `offer` (SDP offer)
- `answer` (SDP answer)
- `ice_candidate` (ICE candidates)
- `state_update` (médico/paciente state sync - e.g., connection status, mic/cam status)
- `heartbeat` / `ping` / `pong`
- `leave` / `end_session`
- `error`

**SUS-specific considerations**:
- CNS (Cartão Nacional de Saúde) validation - 15 digits with check digit algorithm
- CPF validation - 11 digits with check digits
- Room codes
- Audit logging (LGPD compliance - healthcare data)
- Role-based access: `medico`, `paciente`, possibly `enfermeiro`, `acs` (Agente Comunitário de Saúde)
- CID-10 codes for diagnoses, CIAP-2 for reasons for encounter
- SOAP method notes

**Security**:
- Token authentication on WebSocket connect (query param or first message)
- Validate room existence and participant authorization
- LGPD: audit trail of connections/disconnections

Let me structure the code:

```python
# backend/app/api/v1/telemedicina_ws.py
```

Since this is a single file task, I should make it self-contained but realistic — importing from app modules that would exist. But to make it "complete and executable", I might need to either:
1. Assume the app structure exists (FastAPI app, database, models)
2. Provide the full file with reasonable imports

The instruction says "Forneça o código completo e executável" — provide complete executable code. For a single file, I'll write it assuming standard FastAPI project structure with imports from `app.core`, `app.models`, etc. But to be truly executable, maybe I should include the necessary supporting pieces inline or note them.

Given the task focuses on one file, I'll write the main file completely, and also provide a test file since "cobertura de testes automatizados com pytest" is required. Let me provide:

1. `backend/app/api/v1/telemedicina_ws.py` — the main WebSocket hub
2. `backend/tests/api/v1/test_telemedicina_ws.py` — pytest tests

Maybe also minimal supporting stubs if needed for tests to run. Let me think about what dependencies the main file needs:

- `fastapi` (WebSocket, WebSocketDisconnect)
- `pydantic` v2 (message models)
- `sqlalchemy` 2.0 (for audit logging / session persistence)
- `app.core.security` (token validation) — I'll define an interface
- `app.models.telemedicina` (SalaTelemedicina, ParticipanteSala, RegistroAuditoria) — SQLAlchemy 2.0 models

To keep it executable, I could define the models in the same file or in a models module. The task says implement `telemedicina_ws.py` containing the WebSocket endpoint. I think the cleanest approach: write the main file with clear imports from other app modules, and ALSO provide those supporting modules (models, schemas, security stub) so the whole thing is executable. But that might balloon the response. The instruction emphasizes the single file. Let me provide:

1. Main file: `backend/app/api/v1/telemedicina_ws.py` (complete)
2. Supporting: `backend/app/models/telemedicina.py` (SQLAlchemy 2.0 models) — needed for audit
3. Supporting: `backend/app/schemas/telemedicina_ws.py` (Pydantic v2 schemas) — or inline in main file
4. Tests: `backend/tests/test_telemedicina_ws.py`

Actually, to keep it focused and executable, I'll put Pydantic schemas inside the main file (it's the "hub" file), define SQLAlchemy models in a models file, and provide a minimal `app/core/security.py` and `app/core/database.py` reference. Hmm, but the user asked specifically for one file. Let me re-read:

"implemente backend/app/api/v1/telemedicina_ws.py contendo WebSocket endpoint..."

"Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo"

So multiple files are allowed. I'll provide:

1. `backend/app/api/v1/telemedicina_ws.py` — main hub (schemas inline, manager, endpoint)
2. `backend/app/models/telemedicina.py` — SQLAlchemy 2.0 models for sala/participante/auditoria
3. `backend/tests/api/v1/test_telemedicina_ws.py` — pytest with coverage of the flows

And maybe a small `backend/app/core/security.py` note — I'll assume it exists with `verificar_token_acesso`. To make tests runnable without the full app, I can make tests use dependency injection / monkeypatching. Actually, for WebSocket auth, FastAPI supports dependencies on WebSocket routes. I'll use a `WebSocket` dependency for token verification.

Let me design the message protocol carefully:

**Client → Server messages** (JSON):
```json
{"tipo": "entrar", "token": "...", "papel": "medico", "dados": {...}}
{"tipo": "offer", "sdp": "..."}
{"tipo": "answer", "sdp": "..."}
{"tipo": "ice_candidate", "candidate": {...}}
{"tipo": "estado", "dados": {"microfone": false, "camera": true, ...}}
{"tipo": "nota_clinica", "soap": {...}, "cid10": "...", "ciap2": "..."}  // médico only
{"tipo": "sinal_vital", ...} // maybe
{"tipo": "encerrar", "motivo": "..."}
{"tipo": "ping"}
{"tipo": "sair"}
```

**Server → Client messages**:
```json
{"tipo": "sala_entrou", "sala": {...}, "participantes": [...], "seu_id": "..."}
{"tipo": "participante_entrou", "participante": {...}}
{"tipo": "participante_saiu", "participante_id": "...", "motivo": "..."}
{"tipo": "offer", "de": "...", "sdp": "..."}
{"tipo": "answer", "de": "...", "sdp": "..."}
{"tipo": "ice_candidate", "de": "...", "candidate": {...}}
{"tipo": "estado_atualizado", "de": "...", "estado": {...}}
{"tipo": "nota_clinica_registrada", ...}
{"tipo": "sala_encerrada", "motivo": "..."}
{"tipo": "pong"}
{"tipo": "erro", "codigo": "...", "mensagem": "..."}
```

**Roles**: `medico`, `paciente`, `enfermeiro`, `acs` (Agente Comunitário de Saúde), `outro_profissional`. For teleconsulta in APS, typically médico + paciente. Rules:
- Only one `medico` per room (or allow multiple? Typically one). Let's enforce: max 1 médico, max N pacientes (usually 1 paciente + maybe acompanhante). Let me allow `paciente` and `acompanhante`.
- Médico controls ending session.

**Room state machine**:
- `agendada` → `aguardando` (aberta) → `em_andamento` → `encerrada`
- Médico joining opens the room; when both médico and paciente present → `em_andamento`.

**Validation**:
- CNS validation algorithm: CNS can start with 1, 2, 7, 8, 9. 15 digits. Check digit algorithm:
  - For CNS starting with 1, 2: sum = Σ(digit[i] * (15 - i)) for i in 0..14? Let me recall the actual algorithm:
    - CNS has 15 digits. For the first 11 digits, multiply by weights 15,14,13,...,5. Sum. Remainder mod 11. If remainder < 2, dv... Actually the standard algorithm:
    
    For CNS 1/2 format (7 first digits + random 8):
    - Take first 11 digits, weights from 15 down to 5: soma = d0*15 + d1*14 + ... + d10*5
    - resto = soma % 11
    - dv = 11 - resto
    - if dv == 11: dv = 0
    - if dv == 10: invalid (need recalculation with different approach)... Actually the standard: if dv == 10 or 11, then... hmm.
    
    Let me recall properly. The official algorithm (from Cartão Nacional de Saúde - CNS):
    
    ```
    soma = 0
    for i in range(15):
        soma += int(cns[i]) * (15 - i)
    if soma % 11 == 0: válido
    ```
    
    Hmm, that's one variant. Actually there are two known algorithms:
    
    Algorithm 1 (simpler, commonly cited):
    ```
    def valida_cns(cns):
        cns = cns.zfill(15)
        if len(cns) != 15: return False
        if cns[0] not in '12789': return False
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    ```
    
    This works for CNS where the check digits were computed to make the weighted sum divisible by 11. This is the widely used validation (e.g., from DATASUS). Yes, this is correct: the CNS check is that the sum of digits multiplied by weights 15,14,...,1 must be divisible by 11.
    
    For CNS starting with 7, 8, 9 (temporary CNS), the format is different: 7 first digits + 8 random + 2 check digits computed differently. The validation for those uses a different algorithm:
    
    ```
    # For 7/8/9 prefix:
    # digits 1-7 fixed, 8-14 random, 15-16... wait it's 15 digits total
    ```
    
    The temporary CNS (7/8/9) validation:
    ```
    soma = sum(int(cns[i]) * (15 - i) for i in range(11))  # first 11 digits
    resto = soma % 11
    dv = 11 - resto
    if dv == 11: dv = 0
    if dv == 10:
        soma += 2  # add 2 to first digit? Actually: soma = soma + 2
        resto = soma % 11
        dv = 11 - resto
    # check last two digits: str(dv) + '000'? 
    ```
    
    Hmm, the temporary CNS check: the last two digits are `dv` followed by... Let me recall: for temporary CNS, the check digits are computed as: pis-like. Actually the temporary CNS is derived from PIS/PASEP format. The algorithm:
    
    ```
    def valida_cns_temporario(cns):
        # cns starts with 7, 8, or 9
        soma = sum(int(cns[i]) * (15 - i) for i in range(11))
        resto = soma % 11
        dv = 11 - resto
        if dv == 11: dv = 0
        if dv == 10:
            soma += 2
            resto = soma % 11
            dv = 11 - resto
        return cns[11:13] == f"{dv}0"  # hmm not quite
    ```
    
    Actually I remember: for temporary CNS, the last 4 digits are: dv (1 digit) + "000"? No...
    
    Let me think. Temporary CNS format: 7XX PPPP DDDD DDCC? The commonly cited algorithm (from various Brazilian sources):
    
    ```python
    def _valida_cns(cns: str) -> bool:
        cns = re.sub(r'\D', '', cns)
        if len(cns) != 15:
            return False
        # Definitive CNS starts with 1 or 2
        if cns[0] in '12':
            soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
            return soma % 11 == 0
        # Temporary CNS starts with 7, 8 or 9
        if cns[0] in '789':
            soma = sum(int(d) * w for d, w in zip(cns[:11], range(15, 5, -1)))
            resto = soma % 11
            dv = 11 - resto
            if dv == 11:
                dv = 0
            if dv == 10:
                soma = soma + 2
                resto = soma % 11
                dv = 11 - resto
            return cns[11:] == f'{dv}000'
        return False
    ```
    
    Hmm wait, weights for first 11 digits: 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5. And the check is that digits 12-15 are `dv` + "000"? I believe temporary CNS ends with "000" plus... no. Let me recall: temporary CNS = 7 + 10 digits (PIS-like) + 4 check digits? 
    
    Actually the temporary CNS format: `7XX.XXXX.XXXX.XXXX` — 15 digits: first digit 7/8/9, then 14 more. The last 4 digits are check digits computed from the first 11. The check digits are: dv1 (computed as above) followed by "000"? That doesn't give 4 digits.
    
    Hmm. Let me look at this from memory of the actual algorithm published:
    
    ```
    Para CNS provisório (iniciado com 7, 8 ou 9):
    - Multiplicar os 11 primeiros dígitos pelos pesos 15 a 5
    - Somar
    - resto = soma % 11
    - dv = 11 - resto
    - se dv == 11, dv = 0
    - se dv == 10: soma += 2; resto = soma % 11; dv = 11 - resto
    - Os dígitos verificadores são: dv seguido de "000"? 
    ```
    
    No wait — I think the check is: `cns[11:15] == str(dv) + '000'`? That's only if dv is 1 digit and then "000" — total 4 digits: dv + 000. Hmm, but that means digits 12,13,14 are always 0? That doesn't sound right either.
    
    Actually, I recall now: the temporary CNS check digits are 4 digits where the first is dv and... Let me just check with a known example. A commonly used test CNS: "898 006 410 580 012"? Hmm.
    
    Known valid CNS examples used in tests:
    - "700 0000 0000 000" ... 
    - Common test CNS: `798006415795012`? 
    
    Let me think about the widely-circulated Python implementation (from the "valida_cns" gist widely used):
    
    ```python
    def valida_cns(cns: str) -> bool:
        """
        Valida CNS (Cartão Nacional de Saúde).
        Baseado no algoritmo oficial do DATASUS.
        """
        cns = ''.join(filter(str.isdigit, cns))
        if len(cns) != 15:
            return False
        if cns[0] not in '12789':
            return False
        # CNS definitivo (1 ou 2)
        if cns[0] in '12':
            soma = sum(int(cns[i]) * (15 - i) for i in range(15))
            return soma % 11 == 0
        # CNS provisório (7, 8 ou 9)
        soma = sum(int(cns[i]) * (15 - i) for i in range(11))
        resto = soma % 11
        dv = 11 - resto
        if dv == 11:
            dv = 0
        if dv == 10:
            soma += 2
            resto = soma % 11
            dv = 11 - resto
        return cns[11:] == f'{dv}000'
    ```
    
    Hmm, but `cns[11:]` is 4 digits and `f'{dv}000'` is 4 digits (dv + "000"). So temporary CNS would always have "000" in positions 13-15. I'm fairly confident this is the widely-circulated implementation. Let me verify with a real example: temporary CNS "798006415795012"? digits: 7 9 8 0 0 6 4 1 5 7 9 | 5 0 1 2. Last 4 = "5012", not "5000". So that example wouldn't match "dv000" pattern... unless dv=5 and then "012"? Hmm.
    
    Alternative: maybe the check is `cns[11:13] == f'{dv}0'`? No...
    
    Let me reconsider. Actually I recall the temporary CNS structure: 7 + PIS (11 digits total including the 7?) Hmm.
    
    OK here's another memory: The temporary CNS is generated from the PIS/PASEP number. PIS has 11 digits. Temporary CNS = "7" + PIS (11 digits) + 3 check digits? That's 15. The