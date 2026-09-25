The user wants me to implement a WebSocket Hub for Telemedicine and WebRTC Signaling (C21) for the MedIA project. This is a Brazilian SUS (Sistema Único de Saúde) telemedicine system.

Requirements:
- File: `backend/app/api/v1/telemedicina_ws.py`
- WebSocket endpoint: `/ws/telemedicina/sala/{codigo_sala}`
- Handle SDP messages (offer/answer), ICE candidates, and medical/patient state synchronization in telehealth rooms
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me design this comprehensively:

1. **WebSocket Hub Architecture**:
   - ConnectionManager class to manage active connections per room
   - Room-based message routing
   - WebRTC signaling: SDP offer/answer, ICE candidates
   - State synchronization: presence, medical state updates

2. **Message Types** (WebRTC signaling):
   - `join` / `join_accepted` / `join_rejected`
   - `offer` (SDP offer)
   - `answer` (SDP answer)
   - `ice_candidate`
   - `leave` / `peer_left`
   - `peer_joined`
   - `state_update` (medical state sync)
   - `heartbeat` / `ping` / `pong`
   - `error`

3. **Security/Compliance**:
   - Authentication via token (CNS/CPF identification)
   - Role validation (medico, paciente, etc.)
   - LGPD compliance considerations (audit logging)
   - Room access validation

4. **Pydantic v2 models**:
   - Message schemas with discriminated unions
   - SDP description models
   - ICE candidate models
   - State sync models

5. **SQLAlchemy 2.0**:
   - Models for teleconsultation sessions, participants, audit logs
   - Async session handling

6. **Tests with pytest**:
   - Using FastAPI TestClient with WebSocket support
   - Test signaling flow, room management, auth failures

Let me write the code:

```python
# backend/app/api/v1/telemedicina_ws.py
```

Key design decisions:
- Use FastAPI's WebSocket
- ConnectionManager singleton pattern with per-room connection tracking
- Pydantic v2 discriminated union for message types
- Audit logging for LGPD compliance
- Token-based auth on WebSocket connect (query param or first message)
- Heartbeat/ping-pong for connection health

Let me structure:

1. **Enums**: MessageType, PapelParticipante (role), StatusSala
2. **Pydantic models**: 
   - SDPDescription (type: offer/answer, sdp)
   - ICECandidateInit
   - Base WS message envelope with discriminated union
3. **ConnectionManager**: 
   - rooms: dict[str, Room]
   - Room: dict of participant_id -> Connection
   - broadcast, send_to_peer, etc.
4. **Auth**: validate token, extract CNS/CPF, role
5. **Endpoint**: `/ws/telemedicina/sala/{codigo_sala}`
6. **Message handlers**: offer, answer, ice, state_update, etc.

For the database part, I'll include SQLAlchemy 2.0 models (or reference them) - since the task says "contendo WebSocket endpoint", the main file is the WS endpoint, but I should include the models needed. Maybe I should create:
- `backend/app/api/v1/telemedicina_ws.py` - main file
- Maybe supporting files: schemas, models, tests

The instruction says "implemente backend/app/api/v1/telemedicina_ws.py" - so the main deliverable is that file. But for completeness and testability, I should provide:
- The main WS file
- Test file with pytest
- Possibly minimal supporting modules (models, security) - but I could define them inline or as separate files

Given the instruction "Forneça o código completo e executável. Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo", I should provide multiple files as needed for a complete executable solution.

Let me plan the files:

1. `backend/app/api/v1/telemedicina_ws.py` - Main WebSocket hub
2. `backend/app/db/models_telemedicina.py` (or `backend/app/models/telemedicina.py`) - SQLAlchemy 2.0 models
3. `backend/app/schemas/telemedicina_ws.py` - Pydantic v2 schemas (could be in main file, but separation is cleaner)
4. `backend/app/core/security.py` - auth helpers (token validation)
5. `backend/tests/test_telemedicina_ws.py` - pytest tests

Actually, to keep it focused but complete, let me put schemas in the main file or a schemas file. Let me think about what's most useful.

The task emphasizes the WS hub file. I'll create:

1. `backend/app/schemas/telemedicina_ws.py` - Pydantic v2 message schemas with discriminated unions
2. `backend/app/db/models.py` (telemedicine models) - SQLAlchemy 2.0
3. `backend/app/api/v1/telemedicina_ws.py` - the hub
4. `backend/tests/test_telemedicina_ws.py` - tests

Let me write detailed code.

### Pydantic Schemas (Pydantic v2)

```python
from enum import Enum
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict

class PapelParticipante(str, Enum):
    MEDICO = "MEDICO"
    PACIENTE = "PACIENTE"
    ENFERMEIRO = "ENFERMEIRO"
    ADMINISTRADOR = "ADMINISTRADOR"  # maybe not needed

class TipoMensagemWS(str, Enum):
    JOIN = "join"
    JOIN_ACCEPTED = "join_accepted"
    JOIN_REJECTED = "join_rejected"
    PEER_JOINED = "peer_joined"
    PEER_LEFT = "peer_left"
    OFFER = "offer"
    ANSWER = "answer"
    ICE_CANDIDATE = "ice_candidate"
    STATE_UPDATE = "state_update"
    STATE_SYNC = "state_sync"
    CHAT = "chat"  # maybe
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    LEAVE = "leave"
    ROOM_CLOSED = "room_closed"

class SDPDescription(BaseModel):
    type: Literal["offer", "answer", "pranswer", "rollback"]
    sdp: str

class ICECandidateInit(BaseModel):
    candidate: str
    sdpMid: str | None = None
    sdpMLineIndex: int | None = None
    usernameFragment: str | None = None
```

Message envelope with discriminated union:

```python
class MensagemBaseWS(BaseModel):
    tipo: TipoMensagemWS
    id_mensagem: str = Field(default_factory=...)
    timestamp: datetime

class MensagemOffer(MensagemBaseWS):
    tipo: Literal[TipoMensagemWS.OFFER]
    destino_id: str
    sdp: SDPDescription

...
```

Use `Annotated[Union[...], Field(discriminator="tipo")]`.

For state sync (medical state):
```python
class EstadoClinicoSOAP(BaseModel):
    # SOAP method fields
    subjetivo: str | None
    objetivo: str | None
    avaliacao: str | None  # with CID-10
    plano: str | None
    cid10: str | None
    ciap2: str | None
```

Hmm, state sync in the room is more about presence/UI state (e.g., mic on/off, screen sharing, vital signs being shared). But the task says "sincronização de estado médico/paciente em sala" - synchronization of medical/patient state in the room. This could include:
- Connection state (mic, camera, screen share)
- Clinical state (SOAP notes being drafted, CID-10 codes)

I'll implement a generic state sync with typed fields for both technical state (audio/video/screen) and clinical context (SOAP draft, CID-10, CIAP-2 codes). This aligns with SUS/APS standards.

### SQLAlchemy 2.0 Models

```python
class Teleconsulta(BaseModel/DeclarativeBase...):
    __tablename__ = "teleconsultas"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid4)
    codigo_sala: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    status: Mapped[str]
    agendamento_id: ...
    iniciada_em, encerrada_em
    cid10_principal, ciap2_principal
    ...

class ParticipanteTeleconsulta:
    __tablename__ = "teleconsulta_participantes"
    id, teleconsulta_id, papel, nome, cns, cpf, entrou_em, saiu_em

class EventoAuditoriaTeleconsulta (LGPD audit):
    __tablename__ = "teleconsulta_auditoria"
    id, teleconsulta_id, participante_id, evento, payload_json, criado_em, ip
```

### ConnectionManager

```python
class ConexaoSala:
    websocket: WebSocket
    participante_id: str
    papel: PapelParticipante
    nome: str
    conectado_em: datetime

class SalaTeleatendimento:
    codigo: str
    conexoes: dict[str, ConexaoSala]
    estado_compartilhado: dict
    lock: asyncio.Lock

class GerenciadorSalas:
    _salas: dict[str, SalaTeleatendimento]
    def obter_sala(codigo) -> Sala
    async def conectar(...)
    async def desconectar(...)
    async def enviar_para_participante(...)
    async def transmitir(sala, mensagem, excluir=...)
    ...
```

### Auth

WebSocket auth: token via query param `?token=...` or header. For simplicity, accept `token` query param, decode JWT with payload containing: sub (participante id), papel, nome, cns/cpf, codigo_sala claim. Validate that the token's sala matches the URL path sala.

I'll write a `validar_token_ws` function that decodes JWT (using python-jose or manually with hmac). To avoid external dependency issues, I can implement a minimal HMAC-signed token verification using `hashlib`/`hmac` and `base64` — but realistically the project would use python-jose or PyJWT. I'll use PyJWT-style code but implement with a fallback? Better: use `jose.jwt` since it's common in FastAPI projects. Actually, to keep the code self-contained and executable, I could implement a simple HMAC token signer/verifier in `core/security.py` without external deps. That makes tests executable without mocking JWT libs. Let me do that: a small token module using `hmac`, `hashlib`, `base64`, `json` — deterministic and testable.

Actually, let me use standard JWT format (header.payload.signature) with HS256 implemented via hmac+hashlib+base64url. That's ~40 lines and fully self-contained. Good for executability.

### Database session

For the WS endpoint, DB access for: validating teleconsulta exists and is open, registering participant entry/exit, audit logging. Use async SQLAlchemy. In tests, we can override the dependency. But WebSocket dependencies in FastAPI work with `Depends` too.

To keep it robust, I'll design the endpoint to:
1. Accept WS connection
2. Validate token (dependency)
3. Load teleconsulta from DB (dependency or inside)
4. Accept socket, register in manager
5. Loop receiving messages, parse with Pydantic, dispatch
6. On disconnect, cleanup, broadcast peer_left, persist audit

For testability without a real DB, I'll make DB operations best-effort with try/except and allow dependency overrides. Hmm, but "cobertura de testes automatizados" — tests should cover the WS logic. I'll structure so the manager and message handling are unit-testable, and integration tests use FastAPI's TestClient with dependency overrides for DB (using in-memory SQLite async or even faking the session dependency).

Let me use `sqlite+aiosqlite` for tests. That requires aiosqlite installed. Alternatively, override `get_session` dependency with a fake. I'll write tests that:
- Unit test Pydantic schemas (validation of SDP, ICE, discriminated union)
- Unit test GerenciadorSalas (connect, broadcast, routing, disconnect)
- Integration test WS flow with TestClient: join, offer/answer relay, ICE relay, state sync, leave, unauthorized token, wrong room token, duplicate participant

For DB in integration tests, I'll override the `get_db` dependency to yield a fake session or use aiosqlite in-memory. Let me create the app factory in the test with dependency_overrides.

To make the endpoint DB-optional-ish, I'll have a dependency `get_teleconsulta_repo` or just use `Depends(get_db)`. In tests, override with a stub that returns a fake teleconsulta. Let me define a small repository class:

```python
class RepositorioTeleconsulta:
    def __init__(self, session: AsyncSession): ...
    async def obter_por_codigo(self, codigo) -> Teleconsulta | None
    async def registrar_entrada(...)
    async def registrar_saida(...)
    async def registrar_evento(...)
```

In tests, override `Depends(RepositorioTeleconsulta)`? FastAPI dependencies with class + Depends(get_db) as default... I can do:

```python
def obter_repositorio_teleconsulta(session: SessionDep) -> RepositorioTeleconsulta:
    return RepositorioTeleconsulta(session)
```

And in tests override `obter_repositorio_teleconsulta` with a fake. That's clean.

Alternatively, make DB operations wrapped in try/except so tests can run without DB. But better to properly override.

Let me now write the actual code.

#### File 1: `backend/app/schemas/telemedicina_ws.py`

Pydantic v2 schemas:

```python
"""Schemas Pydantic v2 do hub WebSocket de telemedicina (C21)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, StringConstraints

# --- Identificação SUS ---
CNS = Annotated[str, StringConstraints(pattern=r"^\d{15}$", ...)]
CPF = Annotated[str, StringConstraints(pattern=r"^\d{11}$")]
CID10 = Annotated[str, StringConstraints(pattern=r"^[A-Z]\d{2}(\.\d{1,2})?$")]
CIAP2 = Annotated[str, StringConstraints(pattern=r"^[A-Z]\d{2}$")]
```

CNS validation: CNS has a check digit algorithm (soma ponderada). I can implement a validator for CNS using the official algorithm. That's a nice SUS-compliance touch. CNS algorithm: 15 digits, multiply weights 15..2, sum mod 11, etc. Let me recall: For CNS "provissório" starting with 7, 8, 9 or 1,2,3,4,5 (definitivo starts with 1 or 2? Actually definitive CNS starts with 1 or 2; provisional with 7, 8, 9). The check: sum of digit[i] * (15 - i) for i in 0..14 must be divisible by 11. Let me implement:

```python
def _validar_cns(cns: str) -> bool:
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] not in "123456789":  # actually 1,2,7,8,9,5,6? 
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

The standard CNS validation: peso starts at 15 decreasing to 1; sum % 11 == 0. And first char in {1,2,7,8,9} (also 5,6 for CNS of professionals? Actually 5 and 6 are for... hmm). Common implementation: `if cns[0] not in ['1','2','7','8','9']` return False. Some include 5,6 for professional CNS? Let me keep {1,2,7,8,9} as the classic algorithm, but maybe accept 5/6 too? The classic "valida CNS" algorithm from SUS: first digit must be 1, 2, 7, 8 or 9. I'll go with that.

CPF validation with check digits — implement standard algorithm.

These validators add SUS compliance flavor. Good.

Message models:

```python
class TipoMensagem(str, Enum):
    ...

class MensagemBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

Discriminated union:

```python
MensagemWS = Annotated[
    MensagemOffer | MensagemAnswer | MensagemICE | ...,
    Field(discriminator="tipo"),
]
```

Note: with Pydantic v2, discriminated union on Literal fields works.

#### File 2: `backend/app/db/models.py` (telemedicine models)

SQLAlchemy 2.0 style with Mapped/mapped_column. I'll create a separate module `backend/app/models/telemedicina.py` to avoid clashing with existing models. Since we don't know the project's Base, I'll define `Base = declarative_base()` or import from a canonical place. For self-containedness, define in the file with a comment that in the real project it should import from app.db.base. I'll create `backend/app/db/base.py` minimal with DeclarativeBase, then models file.

Actually to keep file count reasonable: 
- `backend/app/db/base.py` — DeclarativeBase + naming convention
- `backend/app/models/telemedicina.py` — Teleconsulta, ParticipanteTeleconsulta, EventoAuditoriaTeleconsulta

#### File 3: `backend/app/core/seguranca_ws.py` — token HMAC + CNS/CPF validators? 

Validators go in schemas. Security file: token creation/verification.

```python
# backend/app/core/seguranca.py
import base64, hashlib, hmac, json, time

def _b64url(data: bytes) -> str: ...
def criar_token(payload: dict, segredo: str, expira_em: int = 3600) -> str
def verificar_token(token: