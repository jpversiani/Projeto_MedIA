The user wants me to implement a WebSocket Hub for telemedicine and WebRTC signaling (C1) for the MedIA project. This is a Brazilian SUS (Unified Health System) telemedicine project.

Requirements:
- File: `backend/app/api/v1/telemedicina_ws.py`
- WebSocket endpoint: `/ws/telemedicina/sala/{codigo_sala}`
- Exchange SDP messages (offer/answer), ICE candidates
- Sync medical/patient state in telehealth room
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me design this properly:

1. **WebSocket endpoint** for telemedicine rooms
2. **Connection manager** to handle multiple connections per room
3. **Message types**: SDP offer/answer, ICE candidates, state sync, presence, chat maybe
4. **Room validation** - check if room exists, user authorization (medico/paciente)
5. **Pydantic models** for messages with strict typing
6. **SQLAlchemy 2.0** models for telemedicine sessions
7. **CNS/CPF validation** - Brazilian health identifiers
8. **Audit logging** - important for medical compliance (LGPD)
9. **Tests with pytest**

Let me structure the code:

```
backend/app/api/v1/telemedicina_ws.py - main WebSocket hub
```

I should also probably provide supporting files since the task says "Forneça o código completo e executável" (provide complete executable code). Let me think about what's needed:

- `backend/app/api/v1/telemedicina_ws.py` - the main file requested
- Supporting: schemas, models, dependencies might be needed
- Tests: `backend/tests/api/v1/test_telemedicina_ws.py`

Since the task focuses on the WebSocket hub file, I'll make it self-contained but well-structured. I'll include:

1. The main WebSocket file with:
   - Pydantic v2 message schemas (strict typing)
   - ConnectionManager class
   - Room state management
   - WebRTC signaling relay (offer, answer, ICE)
   - State sync (SOAP notes status, patient state, etc.)
   - Authentication via token (query param or first message)
   - CNS validation
   - Audit trail

2. Test file with pytest covering:
   - Connection/disconnection
   - SDP offer/answer relay
   - ICE candidates
   - State sync
   - Authorization failures
   - Room not found

Let me write the code:

```python
# backend/app/api/v1/telemedicina_ws.py
```

Key design decisions:

**Message protocol** (JSON over WebSocket):
```json
{
  "tipo": "sdp_offer" | "sdp_answer" | "ice_candidate" | "estado_sala" | "presenca" | "sinalizacao" | "erro" | "heartbeat",
  "cns_origem": "...",
  "papel": "medico" | "paciente",
  "payload": {...},
  "timestamp": "..."
}
```

**Roles**: MEDICO, PACIENTE (maybe also RESIDENTE/ACADEMICO for teaching, but keep it to the two main ones plus maybe SUPERVISOR)

**Room states**: AGENDADA, AGUARDANDO, EM_ATENDIMENTO, FINALIZADA, etc.

**State sync**: SOAP method fields - the doctor may update subjective/objective/assessment/plan during the call; patient state (connection quality, etc.)

Let me think about the architecture:

```python
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated, Any, Literal

import jwt  # for token auth
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
```

For SQLAlchemy 2.0 models, I'll define the Teleconsulta model (or assume it exists — but for "complete executable code" I should define it or import it). Since the task is specifically the WS hub, I'll define the models in a models file and import, OR define minimal models inline. To keep it executable, maybe I should provide:

1. `backend/app/models/teleconsulta.py` - SQLAlchemy models
2. `backend/app/schemas/telemedicina.py` - Pydantic schemas (or keep in the WS file)
3. `backend/app/api/v1/telemedicina_ws.py` - the hub
4. `backend/tests/test_telemedicina_ws.py` - tests

Actually, the instruction says "implemente backend/app/api/v1/telemedicina_ws.py" — the main deliverable. But "Forneça o código completo e executável" suggests providing everything needed. I'll provide the main file plus supporting modules it depends on, and tests. Let me be pragmatic: put the message schemas in the WS file itself (they're protocol-specific), import DB models from a models module which I'll also provide, and provide tests.

Let me design the message protocol carefully with Pydantic v2 discriminated unions:

```python
class TipoMensagemWS(StrEnum):
    # Sinalização WebRTC
    SDP_OFFER = "sdp_offer"
    SDP_ANSWER = "sdp_answer"
    ICE_CANDIDATE = "ice_candidate"
    # Estado
    ENTRADA = "entrada"
    SAIDA = "saida"
    ESTADO_SALA = "estado_sala"
    ESTADO_CLINICO = "estado_clinico"  # SOAP sync
    QUALIDADE_CONEXAO = "qualidade_conexao"
    # Controle
    HEARTBEAT = "heartbeat"
    ENCERRAR_TELECONSULTA = "encerrar_teleconsulta"
    ERRO = "erro"
```

Message envelope:

```python
class MensagemWSBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id_mensagem: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cns_origem: str  # CNS do remetente

class SDPOfferMsg(MensagemWSBase):
    tipo: Literal[TipoMensagemWS.SDP_OFFER]
    sdp: str  # SDP description
    ...

class ICECandidateMsg(MensagemWSBase):
    tipo: Literal[TipoMensagemWS.ICE_CANDIDATE]
    candidate: str
    sdp_mid: str | None
    ...
```

Then a discriminated union:

```python
MensagemWS = Annotated[
    SDPOfferMsg | SDPAnswerMsg | ICECandidateMsg | ...,
    Field(discriminator="tipo")
]
```

**Connection Manager**:

```python
class GerenciadorSalas:
    def __init__(self):
        self._salas: dict[str, dict[str, ConexaoSala]] = {}
        self._lock = asyncio.Lock()
    
    async def conectar(self, codigo_sala, conexao) -> None: ...
    async def desconectar(self, codigo_sala, cns) -> None: ...
    async def transmitir(self, codigo_sala, mensagem, excluir=None) -> None: ...
    async def enviar_para(self, codigo_sala, cns_destino, mensagem) -> None: ...
```

**Room participant**:

```python
class ParticipanteConectado:
    cns: str
    papel: PapelParticipante
    websocket: WebSocket
    conectado_em: datetime
    nome: str
```

**Auth**: For WebSocket, common pattern is token in query param or subprotocol. I'll accept a `token` query param with a JWT containing CNS, papel, codigo_sala. I'll implement a decoder with configurable secret. For tests, I can generate tokens.

**DB validation**: On connect, verify the room exists in DB, is not finalized, and the CNS is authorized (matches the scheduled medico or paciente). I'll use SQLAlchemy 2.0 async session.

**Audit**: Log all signaling events (without storing SDP content in audit — actually for medical compliance, we log metadata: who connected, when, message types, but not content of SDP/ICE which is ephemeral transport data). Actually LGPD requires care; SDP content is not clinical data, so we log types only.

**CNS validation**: CNS is 15 digits; validation algorithm: first digit in {1,2,7,8,9}; if starts with 1,2 → format NNN NNN NNN NNN NN with check digits via mod 11; if 7,8,9 → different algorithm (sum with weights 15..2, mod 11, dv = 11 - resto). Let me implement the standard CNS validator:

```python
def validar_cns(cns: str) -> bool:
    cns = "".join(filter(str.isdigit, cns))
    if len(cns) != 15:
        return False
    if cns[0] not in "12789":
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

That's the standard algorithm — the checksum works for both ranges: sum of digit * weight (15 down to 1) must be divisible by 11. Yes, that's the classic CNS validation.

**CPF validation** too maybe for identification. The task says "identificação por CNS/CPF". I'll include both validators.

**Room state sync**: The room has estado (AGUARDANDO, EM_ATENDIMENTO, etc.). When both participants connected → EM_ATENDIMENTO. State messages broadcast to all.

**SOAP sync**: The doctor can broadcast updates to SOAP fields (subjetivo, objetivo, avaliacao, plano) plus CIAP-2 code and CID-10. Patient sees read-only view. I'll validate CIAP-2 format (letter + 2 digits) and CID-10 format (letter + 2 digits + optional digits).

CIAP-2: e.g., "A01", "K99" — one uppercase letter (excluding some?) + two digits. Regex: `^[A-Z]\d{2}$`.

CID-10: `^[A-Z]\d{2}(\.\d{1,2})?$` — e.g., "J45", "E11.9".

**Heartbeat/ping**: to keep connection alive and detect dead peers.

**Encerrar teleconsulta**: only medico can end; broadcasts final state, updates DB.

Let me now think about the actual FastAPI WebSocket endpoint:

```python
@router.websocket("/ws/telemedicina/sala/{codigo_sala}")
async def ws_telemedicina_sala(
    websocket: WebSocket,
    codigo_sala: str,
    token: Annotated[str, Query()],
    session: AsyncSession = Depends(get_async_session),
):
    ...
```

Note: FastAPI WebSocket dependencies work with Depends. For DB session in websocket, need an async session dependency. I'll define `get_session` dependency.

Flow:
1. Decode token → claims (cns, cpf, papel, nome, codigo_sala expected)
2. Validate codigo_sala matches token claim (prevent joining other rooms)
3. Load teleconsulta from DB by codigo_sala; check status allows connection
4. Check authorization: medico CNS == teleconsulta.medico_cns; paciente CNS == teleconsulta.paciente_cns
5. Accept connection, register in manager
6. Broadcast presence (entrada) to others; send estado_sala snapshot to newcomer
7. Loop: receive_json → validate with Pydantic → route by type:
   - SDP offer/answer: relay to the other participant (target = the other role)
   - ICE: relay
   - estado_clinico: only medico; broadcast to room (patient gets read-only); persist to DB (SOAP draft)
   - qualidade_conexao: broadcast stats
   - encerrar: only medico; set DB status FINALIZADA, broadcast, close all
   - heartbeat: reply pong
8. On disconnect: remove, broadcast saida; if room empty, cleanup; update DB presence

Error handling: send `erro` messages with codes; close with appropriate WS close codes (4401 unauthorized, 4404 room not found, etc.)

**Concurrency**: use asyncio.Lock per room for state mutations.

Now, tests with pytest: use `fastapi.testclient.TestClient` with `websocket_connect`. Need to override DB dependency with a fake/in-memory session. Since SQLAlchemy async session in TestClient is tricky (TestClient runs in a portal thread with its own event loop), I'll design the endpoint so DB access is behind a dependency that can be overridden with a fake. For tests, I'll override `get_session` with a fake session object implementing the minimal interface (`execute`, `commit`, `rollback`). Or simpler: make the DB validation a function `validar_acesso_sala(session, codigo_sala, claims)` and in tests override the dependency `get_session` with a stub that returns a fake session whose `execute` returns a preset result.

Alternative: use `asgi_testclient` or starlette's TestClient which supports websockets well. I'll use starlette TestClient.

For the fake DB: I can create a `FakeAsyncSession` class with `async def execute(self, stmt)` returning a result object with `.scalar_one_or_none()`. And `async def commit()`, `async def rollback()`. That works if my code only uses those.

Also need JWT tokens for tests — I'll use `python-jose` or `pyjwt`. I'll use PyJWT (`import jwt`). Generate tokens in tests with the same secret from settings.

Settings: I'll define a simple `Configuracoes` via pydantic-settings or just module-level constants with env override. To keep it self-contained, I'll create a small settings object in the file with `SECRET_KEY`, `ALGORITHM`, etc., reading from env with defaults. Actually better to import from `app.core.config` but for self-containment define locally with fallback. Hmm — the instruction says complete executable code. I'll provide a minimal `backend/app/core/config.py` too? That might balloon. Let me structure:

Files I'll deliver:
1. `backend/app/api/v1/telemedicina_ws.py` — main hub (schemas + manager + endpoint). Self-contained protocol logic.
2. `backend/app/models/teleconsulta.py` — SQLAlchemy 2.0 models (Teleconsulta, ParticipanteTeleconsulta, RegistroAuditoriaTeleconsulta).
3. `backend/app/db/session.py` — async engine/session factory (minimal).
4. `backend/app/core/seguranca.py` — JWT encode/decode + CNS/CPF validators. (Or put validators in the WS file; better separate for reuse.)
5. `backend/app/main.py` — app factory wiring router (minimal).
6. `backend/tests/test_telemedicina_ws.py` — pytest tests.

Hmm, that's a lot. The task explicitly says implement `telemedicina_ws.py`. I think providing the main file plus the essential supporting modules and tests is right. But I should be careful not to over-bloat. Let me consolidate:

- Put CNS/CPF validators + JWT helpers in `backend/app/core/identificacao.py` (or keep validators in the ws file since they're used in schemas). Actually validators are used by Pydantic schemas in the WS file — I could keep them there. But tests also use them. Fine either way. I'll create `backend/app/core/identificacao.py` with CNS/CPF validation, and JWT in `backend/app/core/seguranca.py`.

Actually, let me reconsider: to keep the answer focused and manageable, I'll do:

1. **`backend/app/api/v1/telemedicina_ws.py`** — the complete hub: message schemas (Pydantic v2), room manager, endpoint, DB integration. Imports models and security from other modules.
2. **`backend/app/models/teleconsulta.py`** — SQLAlchemy 2.0 models.
3. **`backend/app/core/seguranca.py`** — JWT + CNS/CPF validators.
4. **`backend/app/db/session.py`** — async session dependency.
5. **`backend/tests/test_telemedicina_ws.py`** — comprehensive pytest suite.

And maybe a brief note on `main.py` wiring.

Let me write the code now.

### Models (SQLAlchemy 2.0)

```python
# backend/app/models/teleconsulta.py
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass
```

Wait — Base should probably live in `app/models/base.py`. For self-containment I'll define Base in the models file... but other model files would need it too. For this deliverable, defining it in `teleconsulta.py` is acceptable, or I create `backend/app/models/base.py`. I'll create base.py quickly — it's 5 lines. Hmm, to reduce file count, I'll put Base in `teleconsulta.py` and note it. Actually cleaner: `backend/app/models/base.py`. Let me just include it; it's tiny.

Actually, let me minimize: I'll define `Base` inside `teleconsulta.py` with a comment that in the full project it lives in `app/models/base.py`. That keeps file count down. Hmm, but "complete and executable" — as long as imports resolve, it's executable. I'll do a separate small base.py to be clean. Let me decide: I'll include it in teleconsulta.py to reduce files. Fine.

Model `Teleconsulta`:
- id: UUID pk
- codigo_sala: str unique (e.g., "TC-20250101-ABCD")
- paciente_cns: str(15)
- paciente_nome: str
- medico_cns: str(15)
- medico_nome: str
- medico_cpf: str | None
- status: enum (AGENDADA, AGUARDANDO, EM_ATENDIMENTO, FINALIZADA, CANCELADA, FALHA)
- inicio_em, fim_em, criado_em, atualizado_em
- unidade_saude: str (CNES?) — add cnes_unidade
- motivo / queixa principal
- SOAP fields: subjetivo, objetivo, avaliacao, plano (Text, nullable) — draft synced during call
- ciap2: str(3)
- cid10: str(8)

Model `EventoAuditoriaTeleconsulta`:
- id, teleconsulta_id FK, cns_particip