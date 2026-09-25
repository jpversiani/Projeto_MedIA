The user wants me to implement a WebSocket hub for telemedicine and WebRTC signaling for the MedIA project (Brazilian SUS healthcare system). Let me analyze the requirements:

1. **File**: `backend/app/api/v1/telemedicina_ws.py`
2. **Endpoint**: WebSocket `/ws/telemedicina/sala/{codigo_sala}`
3. **Features**:
   - SDP message exchange (offer/answer)
   - ICE candidates
   - Medical/patient state synchronization in telemedicine room
   - SUS compliance (CIAP-2, CID-10, SOAP method, CNS/CPF identification)

Architecture guidelines:
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me design this properly:

### Components needed:

1. **Pydantic models for WebSocket messages**:
   - Message types: `offer`, `answer`, `ice-candidate`, `join`, `leave`, `state-sync`, `heartbeat`, etc.
   - Validation for CNS (Cartão Nacional de Saúde) - 15 digits with check digit
   - Validation for CPF - 11 digits with check digits
   - CID-10 code validation
   - CIAP-2 code validation (letter + 2 digits)

2. **Connection manager**:
   - Room-based connection management
   - Track roles (medico/paciente)
   - Broadcast messages
   - Handle disconnections

3. **WebSocket endpoint**:
   - Authentication (token-based, since WebSocket can't easily use headers in browser)
   - Room validation
   - Message routing
   - State synchronization

4. **Database models** (SQLAlchemy 2.0 style):
   - TeleSala (telemedicine room)
   - TeleSalaParticipante (participants)
   - Registro de eventos (audit log - important for SUS compliance)

5. **Tests with pytest**:
   - Test WebSocket connections
   - Test SDP exchange
   - Test ICE candidates
   - Test validation
   - Test authorization

Let me think about the CNS validation algorithm:
- CNS can start with 1, 2, 7, 8, or 9
- For CNS starting with 1 or 2: sum = (digit * weight) where weights are 15,14,13,...,2. The sum plus check digit must be divisible by 11.
- Actually the algorithm: For CNS 1/2 series: multiply each of first 14 digits by weights 15 down to 2, sum them, then check: rest = sum % 11; if rest == 0, pf = 11 - rest... Let me recall correctly.

CNS validation (15 digits):
- First digit must be 1, 2, 7, 8, or 9
- For 1/2 series: sum = Σ(digit[i] * (15 - i)) for i in 0..13. Then dv calculation: rest = sum % 11; dv = 11 - rest; if dv == 11: dv = 0. The 15th digit must equal dv. Actually the standard algorithm:

```
soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
if soma % 11 == 0:
    return True
```

Yes, for the 1/2 series, the total sum of all 15 digits multiplied by weights 15 down to 1 must be divisible by 11. Let me verify: weights are 15, 14, 13, ..., 2, 1 for the 15 digits. Sum must be % 11 == 0.

For 7/8/9 series (temporary CNS), the check is different - they use a different validation (mod 11 with specific weights). Actually for 7, 8, 9 series, the validation is the same multiplicative scheme but... Let me recall. The temporary CNS (starting with 7, 8, 9) uses the same algorithm as CPF-like check digits. Actually:

For CNS 7/8/9: it's validated like a mod 11 check with weights 15..2 on first 14 digits, dv = 11 - (sum % 11), if dv >= 10 then dv = 0... Hmm, actually the official algorithm from DATASUS:

```
def valida_cns(cns):
    cns = cns.replace('.', '').replace(' ', '')
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    # Série 1 e 2
    if cns[0] in '12':
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    # Série 7, 8, 9
    # valida como módulo 11 padrão
    soma = sum(int(cns[i]) * (15 - i) for i in range(14))
    resto = soma % 11
    dv = 11 - resto
    if dv == 11:
        dv = 0
    if dv == 10:
        # precisa recalcular com soma + 2? 
        ...
```

Actually the official DATASUS pseudo-code for 7/8/9 series:

```
soma = soma dos 14 primeiros dígitos * pesos (15 a 2)
resto = soma % 11
resultado = 11 - resto
se resultado == 11: resultado = 0
se resultado == 10: soma = soma + 2; resto = soma % 11; resultado = 11 - resto
dv = resultado
```

Hmm, that's the algorithm. Let me write it properly:

```python
def _valida_cns(cns: str) -> bool:
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] not in {"1", "2", "7", "8", "9"}:
        return False
    pesos = list(range(15, 0, -1))
    if cns[0] in {"1", "2"}:
        soma = sum(int(d) * p for d, p in zip(cns, pesos))
        return soma % 11 == 0
    # séries 7, 8, 9
    soma = sum(int(d) * p for d, p in zip(cns[:14], pesos[:14]))
    resto = soma % 11
    dv = 11 - resto
    if dv == 11:
        dv = 0
    if dv == 10:
        soma += 2
        resto = soma % 11
        dv = 11 - resto
    return int(cns[14]) == dv
```

CPF validation:
```python
def _valida_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for n in (9, 10):
        soma = sum(int(cpf[i]) * (n + 1 - i) for i in range(n))
        dv = (soma * 10) % 11 % 10
        if int(cpf[n]) != dv:
            return False
    return True
```

CID-10 validation: format like "A00" to "Z99", letter followed by 2 digits, optionally with a dot and more digits (subcategory). Regex: `^[A-Z]\d{2}(\.\d{1,2})?$`

CIAP-2 validation: letter (A-Z, excluding some?) followed by 2 digits. Regex: `^[A-Z]\d{2}$`. CIAP-2 codes are like A01, B02, etc. Actually CIAP-2 chapters: A (general), B (digestive), D (circulatory), etc. Note there's no K... wait, K exists (respiratory). The chapters are A, B, D, F, H, K, L, N, P, R, S, T, U, W, X, Y, Z. Missing: C, E, G, I, J, M, O, Q, V. Hmm, to be safe I could validate against the valid chapter letters. Let me include the valid CIAP-2 chapter letters: A, B, D, F, H, K, L, N, P, R, S, T, U, W, X, Y, Z.

Actually, let me keep it simpler but still correct: validate format `^[A-Z]\d{2}$` and optionally check chapter letters. I'll include the chapter check as it shows SUS domain knowledge.

### Message protocol design:

```python
class TipoMensagem(str, Enum):
    # Sinalização WebRTC
    OFFER = "offer"
    ANSWER = "answer"
    ICE_CANDIDATE = "ice_candidate"
    # Sala
    ENTRADA = "entrada"          # join
    SAIDA = "saida"              # leave
    PARTICIPANTE_ENTROU = "participante_entrou"
    PARTICIPANTE_SAIU = "participante_saiu"
    # Estado clínico
    ESTADO_CLINICO = "estado_clinico"   # SOAP sync
    ESTADO_SALA = "estado_sala"
    # Controle
    PING = "ping"
    PONG = "pong"
    ERRO = "erro"
    ENCERRAR_SALA = "encerrar_sala"
    PERMISSAO_CONCEDIDA = ...
```

Message envelope:
```python
class MensagemWS(BaseModel):
    tipo: TipoMensagem
    payload: dict[str, Any]  # or discriminated union
    timestamp: datetime
```

Better: use Pydantic v2 discriminated unions for typed payloads:

```python
class PayloadOffer(BaseModel):
    sdp: str
    tipo_sdp: Literal["offer"]

class PayloadAnswer(BaseModel):
    sdp: str
    tipo_sdp: Literal["answer"]

class PayloadICE(BaseModel):
    candidate: str
    sdp_mid: str | None
    sdp_mline_index: int | None

class PayloadEstadoClinico(BaseModel):
    soap_subjetivo: str | None
    soap_objetivo: str | None
    soap_avaliacao: str | None
    soap_plano: str | None
    cid10: str | None
    ciap2: str | None
```

Then use a discriminated union with `tipo` as discriminator.

### Connection Manager:

```python
class GerenciadorSalas:
    def __init__(self):
        self._salas: dict[str, dict[UUID, ConexaoSala]] = {}
    
    async def conectar(self, codigo_sala, conexao) -> ...
    async def desconectar(self, codigo_sala, id_conexao) -> ...
    async def enviar_para(self, codigo_sala, destino_id, mensagem) -> ...
    async def transmitir(self, codigo_sala, mensagem, excluir=None) -> ...
    def participantes(self, codigo_sala) -> list[...]
```

Connection dataclass:
```python
@dataclass
class ConexaoSala:
    id_conexao: UUID
    websocket: WebSocket
    usuario_id: UUID
    nome: str
    papel: PapelParticipante  # MEDICO | PACIENTE
    cns: str | None
    conectado_em: datetime
```

### Authentication:

WebSocket auth via query param token or first message. Common pattern: `?token=...`. I'll implement a dependency that validates a JWT-like token. Since we don't know the exact auth system of MedIA, I'll create a reasonable interface with a function `autenticar_websocket(token)` that decodes a JWT (using python-jose or PyJWT). To keep it self-contained, I'll use PyJWT-style decoding with settings. Actually, to avoid too many external dependencies, I could implement it with `jose` since FastAPI docs commonly use it. Let me use `python-jose` with HS256.

Hmm, but the task says "contendo WebSocket endpoint" - the main file. I should also provide supporting files: schemas, models, service, tests. The instruction says "Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo". So multiple files are expected/allowed.

Let me structure:

1. `backend/app/api/v1/telemedicina_ws.py` - main WebSocket endpoint (required)
2. `backend/app/schemas/telemedicina_ws.py` - Pydantic v2 schemas for messages
3. `backend/app/models/telemedicina.py` - SQLAlchemy 2.0 models (TeleSala, TeleSalaParticipante, TeleEventoAuditoria)
4. `backend/app/core/validadores_sus.py` - CNS/CPF/CID-10/CIAP-2 validators (could be in schemas file, but separate is cleaner)
5. `backend/app/services/gerenciador_salas_ws.py` - connection manager (could be in the ws file)
6. `backend/tests/api/test_telemedicina_ws.py` - pytest tests

Actually, to keep it focused, maybe I should put the manager and validators in the main file or in clearly separated modules. The task says "implemente backend/app/api/v1/telemedicina_ws.py contendo WebSocket endpoint". The primary deliverable is that file. But for it to work, it needs schemas and models. I'll provide:

- `backend/app/core/validadores_sus.py` (CNS, CPF, CID-10, CIAP-2)
- `backend/app/schemas/telemedicina_ws.py` (Pydantic v2 message schemas)
- `backend/app/models/telemedicina.py` (SQLAlchemy 2.0 models)
- `backend/app/api/v1/telemedicina_ws.py` (the endpoint + room manager)
- `backend/tests/api/test_telemedicina_ws.py` (pytest with WebSocket test client)

Let me think about the database models:

```python
class PapelParticipante(str, Enum):
    MEDICO = "medico"
    PACIENTE = "paciente"

class StatusSala(str, Enum):
    AGENDADA = "agendada"
    ABERTA = "aberta"
    EM_ATENDIMENTO = "em_atendimento"
    ENCERRADA = "encerrada"
    EXPIRADA = "expirada"

class TeleSala(Base):
    __tablename__ = "tele_salas"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_sala: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    agendamento_id: Mapped[uuid.UUID | None]
    ubs_id: Mapped[uuid.UUID]  # unidade básica de saúde
    profissional_id: Mapped[uuid.UUID]
    paciente_id: Mapped[uuid.UUID]
    status: Mapped[StatusSala]
    iniciada_em: Mapped[datetime | None]
    encerrada_em: Mapped[datetime | None]
    motivo_encerramento: Mapped[str | None]
    criada_em: Mapped[datetime]

class TeleSalaParticipante(Base):
    __tablename__ = "tele_salas_participantes"
    id, sala_id, usuario_id, papel, cns, entrou_em, saiu_em, tempo_conectado_segundos

class TeleEventoAuditoria(Base):
    __tablename__ = "tele_eventos_auditoria"
    id, sala_id, usuario_id, tipo_evento, detalhe (JSON), criado_em
```

Audit logging is important for LGPD/SUS compliance.

### The WebSocket endpoint flow:

1. Client connects to `/ws/telemedicina/sala/{codigo_sala}?token=JWT`
2. Server validates token → gets user identity (id, nome, papel, cns)
3. Server validates room exists and is open, user is authorized participant
4. Server accepts connection, registers in manager
5. Server sends `estado_sala` message with current participants and clinical state
6. Broadcasts `participante_entrou` to others
7. Loop: receive JSON → validate with Pydantic → route:
   - `offer` → forward to other participant (medico→paciente or vice versa)
   - `answer` → forward
   - `ice_candidate` → forward
   - `estado_clinico` → only médico can update; validate CID-10/CIAP-2/SOAP; persist; broadcast
   - `ping` → respond `pong`
   - `encerrar_sala` → only médico; close room, notify all, close connections
8. On disconnect: unregister, broadcast `participante_saiu`, persist participant exit

Error handling: send `erro` messages with codes, close with appropriate WebSocket close codes (4403 unauthorized, 4404 not found, etc.)

### WebRTC signaling specifics:

- SDP offer/answer: just validate it's a non-empty string starting with "v=0" (SDP must start with v=0 line). Good validation touch.
- ICE candidates: validate structure (candidate string, sdpMid, sdpMLineIndex).

### State sync (estado clínico):

The "sincronização de estado médico/paciente" - I interpret this as:
- Clinical state (SOAP notes, CID-10, CIAP-2) maintained by médico, mirrored to paciente view
- Connection state of participants
- Maybe patient-side state like "aguardando", "em consulta"

I'll implement `estado_clinico` (SOAP + CID-10 + CIAP-2) updated by médico, and broadcast to all. Also `estado_sala` snapshot message on join.

### Tests:

Using FastAPI's TestClient with websocket_connect. Need to mock auth and DB. I'll design the endpoint with dependency injection so tests can override:

- `get_db` dependency
- `autenticar_ws` dependency (token validation)

For tests, I'll create fixtures with SQLite in-memory, override dependencies, and use `TestClient.websocket_connect`.

Testing WebRTC signaling between two clients: connect médico and paciente, médico sends offer, paciente receives it, etc.

Let me now think about how to structure the code for testability:

```python
router = APIRouter()

@router.websocket("/ws/telemedicina/sala/{codigo_sala}")
async def ws_telemedicina(
    websocket: WebSocket,
    codigo_sala: str,
    token: str = Query(...),
    db: Session = Depends(get_db),
    gerenciador: GerenciadorSalas = Depends(get_gerenciador_salas),
) ->