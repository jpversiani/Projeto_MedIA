The user wants me to implement a WebSocket Hub for teleconsultation and WebRTC signaling for a Brazilian SUS (Unified Health System) telemedicine project called MedIA. This is task C17.

Requirements:
- File: `backend/app/api/v1/telemedicina_ws.py`
- WebSocket endpoint: `/ws/telemedicina/sala/{codigo_sala}`
- Exchange SDP messages (offer/answer), ICE candidates
- Sync medical/patient state in telehealth room
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me design this properly:

1. **Message models (Pydantic v2)**: 
   - `TipoMensagemWS` enum: `offer`, `answer`, `ice_candidate`, `join`, `leave`, `estado_medico`, `estado_paciente`, `ping`, `pong`, `erro`, `sala_cheia`, `participante_entrou`, `participante_saiu`, `sinalizacao_pronta`, `fim_teleconsulta`, etc.
   - `MensagemEntrada` (incoming message base)
   - `MensagemSaida` (outgoing)
   - SDP offer/answer payloads
   - ICE candidate payloads
   - Medical state sync (SOAP notes, CIAP-2 codes, CID-10)

2. **Connection manager**: 
   - `GerenciadorSalasTelemedicina` (Room Manager) - manages rooms by `codigo_sala`, tracks participants (medico/paciente), handles broadcast
   - Role-based: `PapelParticipante` enum: `MEDICO`, `PACIENTE`
   - Limit 2 participants per room (1 doctor + 1 patient), or maybe allow a few observers? Keep it simple: 1 médico + 1 paciente.

3. **Authentication**: 
   - Token-based auth via query param or first message. For SUS, identification via CNS/CPF. Let's do JWT token in query string `?token=...` and role. Validate CNS (Cartão Nacional de Saúde) with check digit algorithm, CPF too.

4. **Room state persistence** (SQLAlchemy 2.0):
   - `SalaTelemedicina` model with `codigo_sala`, status, participants, started_at, ended_at
   - Maybe `EventoTelemedicina` for audit log (LGPD compliance - important for health data in Brazil)
   - Actually the task says implement the WS file; models might live elsewhere, but I should include what's needed. I'll define SQLAlchemy models in the same file or import from `app.models`. To make it self-contained but realistic, I'll import from `app.db.session` and `app.models.telemedicina`. Hmm, but the task says "implemente backend/app/api/v1/telemedicina_ws.py". I should focus on that file but can reference other modules. To make it runnable/testable, maybe include minimal model definitions with a note, or define them in the file. Better practice: define Pydantic schemas in the file, and import SQLAlchemy models from `app.models.telemedicina`. But since only this file is requested, I could include the SQLAlchemy models in the file for completeness... That's not great architecture. Let me think.

   The instruction: "implemente backend/app/api/v1/telemedicina_ws.py contendo WebSocket endpoint". The deliverable is one file. I'll write that file with imports from the project's modules (auth, db, models, services). To make it self-contained enough for review and testing, I can include:
   - Pydantic v2 message schemas (in-file)
   - Connection/room manager (in-file)
   - The WS endpoint (in-file)
   - Helper functions for CNS/CPF validation (in-file)
   - Audit logging via SQLAlchemy session (import models from app.models.telemedicina)

   And then provide a pytest test file as well (the guidelines mention "cobertura de testes automatizados com pytest"). I should include tests too — probably a second code block with `backend/tests/api/v1/test_telemedicina_ws.py`.

5. **WebRTC signaling flow**:
   - Client connects with `codigo_sala` + token + role
   - Server validates token, role, room existence/status
   - On join: register connection, notify other participant, send current room state
   - Relay SDP offer/answer to the other participant (medico usually creates offer to paciente, or either)
   - Relay ICE candidates
   - Handle `estado_medico` / `estado_paciente` sync messages (e.g., doctor updates SOAP note status, patient reports symptoms) — broadcast to room, persist to DB
   - Handle `fim_teleconsulta` (only medico can end) — persist end time, CID-10/CIAP-2 codes, close room, notify participants
   - Heartbeat/ping-pong
   - Disconnect handling: notify other participant, mark room state

6. **Security/compliance**:
   - LGPD: audit log of events, no PHI in logs (mask), TLS assumed
   - Validate CNS with check-digit algorithm (portaria SAES/MS validation)
   - Validate CPF check digits
   - Rate limiting messages (simple token bucket or max per second) to prevent abuse
   - Message size limits
   - Room code format validation (e.g., UUID or 8-char alphanumeric)

7. **Python 3.12 features**: use `type` statements? Modern syntax like `X | None`, `Self`, `@override`? Use `asyncio.TaskGroup`? Could use `typing` PEP 695 generics. Keep it reasonable.

Let me now write the code.

Architecture of the file:

```python
"""
WebSocket Hub de Teleconsulta e Signaling WebRTC (C17)
...
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated, Any, Literal, Self

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationError, model_validator
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decodificar_token_acesso  # returns payload with sub, papel, cns...
from app.db.session import AsyncSessionLocal (or get_session factory)
from app.models.telemedicina import SalaTelemedicina, EventoTelemedicina, ParticipanteSala
```

Hmm, since I can't guarantee those modules exist, maybe I should make the file as self-contained as reasonable while noting integration points. A common approach in these tasks: write the main file with imports from project modules, and also provide the test file that stubs/mocks those. Alternatively, define everything needed inside the file (models included) so tests can run. Given "cobertura de testes automatizados com pytest", I'll provide:

1. `backend/app/api/v1/telemedicina_ws.py` — the main deliverable (with imports from app modules; I'll define the SQLAlchemy models inline? No...).

Actually, let me reconsider. To maximize usefulness and testability, I'll structure:

- Main file contains: enums, Pydantic schemas, validators (CNS/CPF), room manager, WS endpoint, and DB persistence hooks that import models from `app.models.telemedicina` and session from `app.db.session`. I'll write those imports clearly so the team knows the dependencies.

But then the test file would need those modules... I can make tests use dependency injection: the manager and auth function can be injected/overridden. FastAPI WebSocket dependencies: we can use `Depends` with websockets. Let me design with dependency injection:

```python
router = APIRouter()

def get_servico_autenticacao_ws(...)  # overridden in tests
```

For DB, use `Depends(get_db_session)` — FastAPI supports dependencies in WebSocket endpoints.

Let me design the message protocol carefully.

### Protocol

Incoming message (from client):
```json
{
  "tipo": "offer|answer|ice_candidate|estado_medico|estado_paciente|fim_teleconsulta|ping|sair_sala",
  "carga": { ... },  // payload
  "id_mensagem": "uuid opcional"
}
```

Outgoing:
```json
{
  "tipo": "...",
  "de": {"papel": "medico", "id_usuario": "..."},
  "carga": {...},
  "timestamp": "...",
  "id_mensagem": "..."
}
```

Payloads:
- offer: `{"sdp": "...", "tipo_sdp": "offer"}` — actually tipo already says offer. Payload: `{"sdp": "v=0..."}`
- answer: `{"sdp": "..."}`
- ice_candidate: `{"candidate": "...", "sdp_mid": "0", "sdp_mline_index": 0, "username_fragment": null}`
- estado_medico: SOAP fields: `{"queixa_principal": ..., "historia": ..., "avaliacao": ..., "conduta": ..., "ciap2": "F29", "cid10": "F41.9", "status": "em_avaliacao"}`
- estado_paciente: `{"sintomas": [...], "nivel_dor": 0-10, "observacoes": ...}`
- fim_teleconsulta: `{"cid10": "...", "ciap2": "...", "resumo": ...}` (medico only)

System messages to clients: `participante_conectado`, `participante_desconectado`, `sala_encerrada`, `erro`, `pong`, `estado_sala` (on join).

### Roles and room rules

- `PapelParticipante`: MEDICO, PACIENTE
- Room: max 1 médico + 1 paciente. If role slot taken → reject with error and close (code 4003? use close codes: 1008 policy violation, or custom 4000-range).
- Room code: 8-12 chars alphanumeric (e.g., generated as `TELE-XXXXXXXX`). Validate with regex.

### CNS validation

CNS is 15 digits. Validation algorithm (for CNS starting with 1, 2, 7, 8, 9):
- For CNS starting with 1 or 2 (definitive cards): sum = Σ (digit_i * (15 - i)) for i=1..15; sum % 11 == 0.
- For CNS starting with 7, 8, 9 (temporary): algorithm: multiply digits by weights 15..2, sum; if sum % 11 == 0 ok else subtract? Let me recall the official algorithm:

Official CNS validation:
```
Para CNS começando com 1, 2: 
  soma = Σ d[i] * peso[i], pesos = 15,14,...,1
  se soma % 11 == 0 → válido
Para CNS começando com 7, 8, 9:
  soma = Σ d[i] * peso[i], pesos = 15,...,2 (14 weights? no)
```

Let me recall properly. The standard algorithm (from DATASUS):

```
function validaCNS(vCNS) {
  // vCNS must have 15 digits
  if ([1,2,7,8,9].indexOf(Number(vCNS[0])) == -1) return false;
  let soma = 0;
  for (let i = 0; i < 15; i++) {
    soma += Number(vCNS[i]) * (15 - i);
  }
  if (soma % 11 == 0) return true; // for 1,2
  // for 7,8,9:
  ...
}
```

Actually the full algorithm for 7/8/9:
```
soma = Σ d[i] * (15 - i) for i = 0..14
resto = soma % 11
if resto != 0: dv = 11 - resto else dv = 0
if dv != Number(vCNS[14])? 
```
Hmm no. Let me recall the canonical JS implementation:

```javascript
function validaCNS(vCNS) {
	var vFator = [15,14,13,12,11,10,9,8,7,6,5,4,3,2,1]; // hmm
}
```

The widely used implementation:

```javascript
function validaCNS(vCNS) {
  // Formulário que será postado
  var vFator = 0;
  var vSoma = 0;
  var vResto = 0;
  var vDV = 0;
  var vPiso = 0;
  var vPeso = 0;
  var vCNSValido = false;
  
  if (vCNS.trim().length != 15) return false;
  
  vPiso = Math.floor(vCNS.substring(0,1));
  
  switch (vPiso) {
    case 7: case 8: case 9:
      vPeso = 275;
      break;
    default:
      vPeso = 0;
  }
  
  vSoma = vPeso;
  for (var i = 0; i < 15; i++) {
    vSoma += parseInt(vCNS.substring(i, i+1)) * (15 - i);
  }
  vResto = vSoma % 11;
  vDV = 11 - vResto;
  if (vDV == 11) vDV = 0;
  if (vDV == 10) {
    vPiso = Math.floor(vCNS.substring(0,1));
    switch (vPiso) {
      case 7: case 8: case 9:
        vPeso = 391;
        break;
      default:
        vPeso = 0;
    }
    vSoma = vPeso;
    for (var i = 0; i < 15; i++) {
      vSoma += parseInt(vCNS.substring(i, i+1)) * (17 - i);
    }
    vResto = vSoma % 11;
    vDV = 11 - vResto;
    if (vDV == 11) vDV = 0;
    if (vDV == 10) return false;
  }
  if (vDV == parseInt(vCNS.substring(14,15))) {
    vCNSValido = true;
  } else {
    vCNSValido = false;
  }
  return vCNSValido;
}
```

Yes, that's the canonical algorithm. For CNS starting with 1/2: weights 15..1, sum%11==0 means valid (equivalently DV computed as 11 - resto where if DV==11 → 0 and check equals last digit... actually for 1/2 the check is soma % 11 == 0 directly). The unified algorithm above handles both: for 1/2, vPeso=0, sum with weights 15-i, resto = soma%11, dv = 11-resto; if dv==11 → 0; if dv==10 → recompute with weights 17-i and peso 0; then compare dv to last digit. For 1/2 cards, valid CNS have soma%11==0, so resto=0, dv=11 → 0... wait that gives dv=0 but last digit isn't necessarily 0. Hmm.

Wait: for 1/2, if soma % 11 == 0, then resto = 0, dv = 11 - 0 = 11 → set to 0? That would require last digit 0. That's wrong. Let me re-check: the canonical algorithm says `if (vDV == 11) vDV = 0;` Hmm, but for 1/2 cards the rule is soma % 11 == 0. Let me test with a known valid CNS: "700000000000003" is a commonly cited valid test CNS. Let's verify with the algorithm: digits 7,0,0,0,0,0,0,0,0,0,0,0,0,0,3. vPiso=7 → vPeso=275. vSoma = 275 + 7*15 + 3*1 = 275 + 105 + 3 = 383. 383 % 11 = 383 - 374 = 9. vDV = 11 - 9 = 2. vDV != 10, compare with last digit 3 → invalid? Hmm that contradicts.

Let me recompute: weights are (15 - i) for i=0..14 → 15,14,13,...,1. Digit 7 at position 0 → 7*15 = 105. Digit 3 at position 14 → 3*1 = 3. Sum = 275 + 105 + 3 = 383. 383 mod 11: 11*34 = 374, remainder 9. DV = 11-9 = 2. Last digit is 3. So "700000000000003" would be invalid by this computation. Maybe the known valid test CNS is different. Common test CNS: "7980000000000064"? That's 16 digits. Hmm.

Known valid CNS examples: "000000000000000"? No, first digit must be 1,2,7,8,9.

Let me just trust the canonical algorithm (it's the one from the "Manual de Instruções do Cartão Nacional de Saúde" implemented widely). Actually let me verify with a generated valid CNS. The algorithm to GENERATE a CNS: for prefix 7/8/9: take 14 random digits, compute sum with weights 15..2 (14 digits), resto = soma % 11, dv = 11 - resto; if dv == 11 → 0; if dv == 10 → peso becomes 391 and weights 17..3, recompute. Then append dv.

Hmm wait — generation uses weights 15..2 for the 14 digits (not 15..1 for 15 digits). Validation uses weights 15..1 for all 15 digits including DV. These are consistent: if dv = 11 - (soma14 % 11), then soma15 = soma14 + dv*1. soma15 % 11 = (soma14 + dv) % 11 = (soma14 + 11 - resto14) % 11 = (soma14 - resto14 + 11) % 11 = (0 + 11) % 11 = 0 when resto14 != 0. If resto14 == 0, dv