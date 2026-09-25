The user wants me to implement a WebSocket Hub for Telemedicine and WebRTC Signaling (C17) for the MedIA project. This is a Brazilian SUS (Unified Health System) telemedicine application.

Requirements:
- File: `backend/app/api/v1/telemedicina_ws.py`
- WebSocket endpoint: `/ws/telemedicina/sala/{codigo_sala}`
- Message exchange: SDP (offer/answer), ICE candidates
- Medical/patient state synchronization in telehealth room
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and pytest test coverage

Let me design this properly:

1. **WebSocket Hub Architecture**:
   - Connection manager per room (sala)
   - Room state management
   - Message routing for WebRTC signaling
   - Authentication/authorization (CNS/CPF identification)
   - Role-based access (medico/paciente)

2. **Message Types**:
   - `join` / `join_ack` / `peer_joined` / `peer_left`
   - `offer` (SDP offer)
   - `answer` (SDP answer)
   - `ice_candidate`
   - `state_sync` (medical state - SOAP notes, CIAP-2, CID-10)
   - `heartbeat` / `ping` / `pong`
   - `end_call` / `sala_encerrada`
   - Error messages

3. **Pydantic v2 Models**:
   - Message envelope with discriminated unions
   - SDP models (offer/answer)
   - ICE candidate model
   - State sync models (SOAP, CIAP-2 codes, CID-10)
   - Participant info (with CNS/CPF validation)

4. **Security**:
   - Token validation (JWT)
   - CNS validation (Brazilian health card number - has check digit algorithm)
   - CPF validation (check digit algorithm)
   - Role-based message filtering (patient can't see certain medical data?)

5. **SQLAlchemy 2.0**:
   - Models for SalaTelemedicina, ParticipanteSala, RegistroTeleconsulta
   - Async session handling

6. **Connection Manager**:
   - Room-based connection tracking
   - Broadcast to room
   - Send to specific peer
   - Handle disconnections

Let me write the CNS validation algorithm:
- CNS must be 15 digits
- Starting with 1, 2 (definitive) or 7, 8, 9 (provisional)
- Check digit algorithm: sum of (digit * weight) where weights cycle 15,14,13,...,2; sum % 11; if remainder == 0, check digit is 0, else check digit = 11 - remainder. Actually the algorithm: 
  - For CNS: multiply each of first 14 digits by weights 15 down to 2, sum them, remainder = sum % 11, if remainder < 2 then pd = 0 else pd = 11 - remainder. Then check pd == 15th digit.

CPF validation:
- 11 digits, check digits with mod 11 algorithm.

Let me structure the code:

```
backend/app/api/v1/telemedicina_ws.py
```

The task says to write this file, but for completeness I might need supporting modules. The instruction says "implemente backend/app/api/v1/telemedicina_ws.py" - so the main file is that one. But I should probably also provide the tests file since "cobertura de testes automatizados com pytest" is required. Let me focus primarily on the main file but include tests.

Let me think about the structure of the main file:

```python
# backend/app/api/v1/telemedicina_ws.py
```

Components:

1. **Imports**: FastAPI WebSocket, WebSocketDisconnect, Pydantic, SQLAlchemy async, etc.

2. **Constants**: Message types enum, roles enum, timeouts.

3. **Validators**: CNS, CPF validation functions.

4. **Pydantic Models** (strict typing):
   - `ParticipanteInfo`: id, nome, papel (medico/paciente), cns (for patient), cpf, crm/uf for doctor
   - Message models with discriminated union on `tipo`:
     - `MensagemEntrar` (join)
     - `MensagemOfertaSDP` (offer)
     - `MensagemRespostaSDP` (answer)
     - `MensagemCandidatoICE` (ice)
     - `MensagemEstadoClinico` (SOAP sync)
     - `MensagemSincronizacaoEstado`
     - `MensagemEncerrar`
     - `MensagemHeartbeat`
   - `EnvelopeMensagem`: tipo + payload discriminated union

5. **SQLAlchemy Models** (2.0 style with Mapped/mapped_column):
   - `SalaTelemedicina`: id, codigo_sala, status, agendamento_id, criada_em, encerrada_em
   - `ParticipanteTeleconsulta`: id, sala_id, usuario_id, papel, entrou_em, saiu_em
   - `RegistroSOAP`: anamnese (S), exame fisico (O), avaliacao (A), conduta (P), ciap2, cid10

   Actually, maybe I should keep the DB models minimal and reference existing ones, but since this is standalone, I'll define them in the file or assume they exist. The task says implement the ws file. I'll define the models needed within the file (or import from a models module — but to make it self-contained and executable, I'll define them here with a note).

   Hmm, better approach: define SQLAlchemy models in the same file for self-containment, marked clearly. Or create a separate models file. The instruction says "Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo". So I can create multiple files. Let me create:
   
   - `backend/app/api/v1/telemedicina_ws.py` (main)
   - `backend/tests/api/v1/test_telemedicina_ws.py` (tests)
   
   Maybe also `backend/app/models/telemedicina.py` for DB models to keep separation. That's cleaner architecture. Let me do:
   
   - `backend/app/models/telemedicina.py` — SQLAlchemy 2.0 models
   - `backend/app/api/v1/telemedicina_ws.py` — WebSocket hub
   - `backend/tests/api/v1/test_telemedicina_ws.py` — pytest tests

   Possibly also schemas file: `backend/app/schemas/telemedicina.py` for Pydantic models. That's good separation. But the task emphasizes the ws file. I'll do 3-4 files with clear paths.

6. **ConnectionManager (Hub)**:
   - `GerenciadorSalas` class: dict of codigo_sala -> SalaRuntime
   - SalaRuntime: connections dict (participant_id -> WebSocket), participants info, state
   - Methods: connect, disconnect, broadcast, send_personal, route signaling

7. **WebSocket Endpoint**:
   - `/ws/telemedicina/sala/{codigo_sala}`
   - Query params or first message for auth: token, papel, identification
   - Validate room exists and is open
   - Register participant
   - Message loop: receive JSON, validate with Pydantic, route
   - Handle disconnect: notify peers, update DB

8. **Signaling Logic**:
   - offer: forward to the other peer (medico initiates typically)
   - answer: forward to offerer
   - ice: forward to peer
   - Renegotiation support
   - Prevent patient from sending offer? Actually in WebRTC, either can initiate. Typically doctor side initiates offer. I'll allow both but log.

9. **State Sync**:
   - SOAP notes sync: doctor sends clinical state updates; patient receives a sanitized version (maybe only "conduta" visible? Actually in telehealth, patient sees what doctor shares). I'll implement: doctor can send clinical state; patient receives read-only view. Patient cannot send clinical state (rejected with error).
   - CIAP-2 codes (e.g., "A01", "K29"...), CID-10 codes validated by regex.

10. **Security**:
    - Token-based auth on connect (query param `token`), decode JWT (use python-jose or just a stub function). To keep it executable without heavy deps, I'll implement a `validar_token` function that decodes JWT with `jose` if available... Better to implement with `python-jose` import but allow fallback? For tests, I can monkeypatch. Let me use a simple interface: `autenticar_conexao(token: str) -> IdentidadeUsuario` that decodes JWT using `jose.jwt`. I'll include it as dependency but tests can patch it.

    Actually, to keep tests self-contained without JWT lib, I could implement HMAC-based token validation using `hmac` + `hashlib` from stdlib. That's executable without extra deps. But real-world would use JWT. Hmm. Let me use `jose` since it's common with FastAPI, but make the import graceful? No — strict typing, clean code. I'll implement JWT with PyJWT? The project likely has python-jose for auth. I'll write `from jose import jwt, JWTError` and in tests, patch `telemedicina_ws.autenticar_token`.

    Alternatively, simpler: the endpoint accepts connection with query params: `token`, and the token contains user info. For testability, I'll have a dependency-like function `resolver_identidade(token)` that tests can override via `app.dependency_overrides`? WebSocket dependencies in FastAPI can use `Depends`. Yes! FastAPI supports dependencies in WebSockets. I can define:

    ```python
    async def obter_identidade_atual(
        websocket: WebSocket,
        token: str = Query(...),
    ) -> IdentidadeUsuario:
        ...
    ```

    And use `websocket: WebSocket = Depends(...)`? Actually you can do:

    ```python
    @router.websocket("/ws/telemedicina/sala/{codigo_sala}")
    async def sala_telemedicina(
        websocket: WebSocket,
        codigo_sala: str,
        identidade: IdentidadeUsuario = Depends(obter_identidade_por_token),
    ):
    ```

    That works in FastAPI. Tests can override the dependency. 

11. **Rate limiting / message size**: basic guards.

12. **Heartbeat**: ping/pong to keep alive.

Let me now write the CNS validator:

```python
def validar_cns(cns: str) -> bool:
    cns = "".join(ch for ch in cns if ch.isdigit())
    if len(cns) != 15:
        return False
    if cns[0] not in "123789":
        return False
    soma = sum(int(dig) * peso for dig, peso in zip(cns[:14], range(15, 1, -1)))
    resto = soma % 11
    dv = 0 if resto < 2 else 11 - resto
    return dv == int(cns[14])
```

Wait, the standard CNS algorithm: weights are 15,14,...,2 for the first 14 digits? Let me verify: The CNS check: take first 14 digits, multiply by weights 15 down to 2 respectively, sum. resto = soma % 11. If resto < 2, dv = 0 else dv = 11 - resto. Compare with 15th digit. Yes that's the standard algorithm.

Example valid CNS: 700000000000000? Let me compute: digits 7,0,0,...,0 (14 digits: 7 followed by 13 zeros). soma = 7*15 = 105. resto = 105 % 11 = 105 - 99 = 6. dv = 11-6 = 5. So 7000000000000005 would be valid. Hmm wait, first 14 digits are "70000000000000" (7 + 13 zeros = 14 digits), then check digit. soma = 7*15 + 0*14 + ... = 105. resto=6, dv=5. So CNS "7000000000000005"? That's 7, then 13 zeros? Let me count: "7000000000000005" has 16 chars. No: 7 + 13 zeros = 14 chars, + dv = 15 chars: "70000000000000" + "5" = "700000000000005". Let me count: 7,0,0,0,0,0,0,0,0,0,0,0,0,0 = 14 digits, then 5 = 15 total. So "700000000000005" is valid. Good, I'll use that in tests.

CPF validator:

```python
def validar_cpf(cpf: str) -> bool:
    cpf = "".join(ch for ch in cpf if ch.isdigit())
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for n in (9, 10):
        soma = sum(int(d) * (n + 1 - i) ... )
```

Standard: 
- dv1: sum(d[i] * (10 - i) for i in 0..8) % 11; dv1 = 0 if r < 2 else 11 - r
- dv2: sum(d[i] * (11 - i) for i in 0..9) % 11; dv2 = 0 if r < 2 else 11 - r

Test CPF: 111.444.777-35 is the classic valid test CPF. Also 529.982.247-25.

CIAP-2 validation: format is letter + 2 digits, e.g., "A01", "K29", "T90". Regex: `^[A-Z]\d{2}$`.

CID-10: letter + 2 digits optionally + . + 1-2 digits (or X). Regex: `^[A-Z]\d{2}(?:\.\d{1,2})?$`.

Now Pydantic models:

```python
class PapelParticipante(str, Enum):
    MEDICO = "medico"
    PACIENTE = "paciente"

class StatusSala(str, Enum):
    AGENDADA = "agendada"
    ABERTA = "aberta"
    EM_ANDAMENTO = "em_andamento"
    ENCERRADA = "encerrada"
    EXPIRADA = "expirada"
```

Message envelope with discriminated union:

```python
class TipoMensagem(str, Enum):
    ENTRAR = "entrar"
    ENTRADA_CONFIRMADA = "entrada_confirmada"
    PEER_ENTROU = "peer_entrou"
    PEER_SAIU = "peer_saiu"
    OFERTA_SDP = "oferta_sdp"
    RESPOSTA_SDP = "resposta_sdp"
    CANDIDATO_ICE = "candidato_ice"
    ESTADO_CLINICO = "estado_clinico"
    ESTADO_CLINICO_ATUALIZADO = "estado_clinico_atualizado"
    ENCERRAR_TELECONSULTA = "encerrar_teleconsulta"
    SALA_ENCERRADA = "sala_encerrada"
    ERRO = "erro"
    HEARTBEAT = "heartbeat"
```

Payload models:

```python
class CargaOfertaSDP(BaseModel):
    sdp: str  # description
    tipo: Literal["offer"]
    # maybe renegotiation flag

class CargaRespostaSDP(BaseModel):
    sdp: str
    tipo: Literal["answer"]

class CargaCandidatoICE(BaseModel):
    candidate: str
    sdpMid: str | None
    sdpMLineIndex: int | None
```

Hmm, WebRTC JSON typically: `{"candidate": "...", "sdpMid": "0", "sdpMLineIndex": 0, "usernameFragment": "..."}`. I'll use camelCase via alias to match browser RTCIceCandidateInit. Use `model_config = ConfigDict(populate_by_name=True)` with aliases.

SOAP state:

```python
class EstadoClinicoSOAP(BaseModel):
    subjetivo: str | None  # S - anamnese
    objetivo: str | None   # O - exame físico / aferições
    avaliacao: str | None  # A - hipótese diagnóstica
    plano: str | None      # P - conduta
    ciap2: str | None      # código CIAP-2
    cid10: str | None      # código CID-10
```

Envelope:

```python
class MensagemEntrada(BaseModel):
    tipo: Literal[TipoMensagem.OFERTA_SDP] = ...
    payload: ...
```

Better: use a tagged union:

```python
MensagemRecebida = Annotated[
    Union[
        MensagemOfertaSDP,
        MensagemRespostaSDP,
        MensagemCandidatoICE,
        MensagemEstadoClinico,
        MensagemEncerramento,
        MensagemHeartbeat,
    ],
    Field(discriminator="tipo"),
]
```

Each message model has `tipo: Literal[...]` and payload fields inline or nested. Inline is simpler for WS JSON.

Now the Hub:

```python
class SalaRuntime:
    def __init__(self, codigo: str):
        self.codigo = codigo
        self.conexoes: dict[UUID, ConexaoParticipante] = {}
        self.estado_clinico: EstadoClinicoSOAP | None = None
        self.encerrada = False
        self.lock = asyncio.Lock()

class ConexaoParticipante:
    def __init__(self, websocket, identidade, participante_id):
        ...
```

GerenciadorSalas (singleton):

```python
class HubTelemedicina:
    _salas: dict[str, SalaRuntime]
    _lock: asyncio.Lock

    async def obter_ou_criar_sala(...)
    async def conectar(...)
    async def desconectar(...)
    async def enviar_para_peer(...)
    async def transmitir(...)
```

WebSocket endpoint flow:

1. Accept connection (or validate before accept — FastAPI: you can validate in dependency; if dependency raises WebSocketException, connection closed with code).
2. First message must be `entrar` with participant info (or identity comes from token). Let me design: identity from token (JWT) — contains usuario_id, nome, papel, cns/cpf. The `entrar` message confirms and provides optional extra info. Actually simpler: token provides identity; the client sends `entrar` as handshake; server replies `entrada_confirmada` with room state (participants, current clinical state for doctor), and broadcasts `peer_entrou` to others.

3. Message routing:
   - `of