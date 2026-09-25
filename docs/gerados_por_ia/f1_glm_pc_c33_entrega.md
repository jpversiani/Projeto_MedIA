The user wants a WebSocket hub for telemedicine with WebRTC signaling. I need to write backend/app/api/v1/telemedicina_ws.py with WebSocket endpoint '/ws/telemedicina/sala/{codigo_sala}', SDP offer/answer, ICE candidates, medical/patient state sync. Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS patterns (CIAP-2, CID-10, SOAP, CNS/CPF), pytest tests.

I should write a complete module: message models (Pydantic v2), connection manager (hub), room management, JWT auth via query token, validation of CNS/CPF, message types enum, persistence hooks (SQLAlchemy async), and pytest tests with fastapi TestClient websocket.

Let me design:

- Enums: TipoMensagem (offer, answer, ice_candidate, estado_medico, estado_paciente, join, leave, chat, ping/pong, erro)
- Models Pydantic: MensagemSignaling base with discriminated union? Keep simpler: MensagemWS with tipo, payload, remetente_id, papel (medico/paciente), timestamp.
- Validadores CNS (algoritmo oficial), CPF.
- RoomManager: dict[codigo_sala -> Sala], Sala holds connections: dict[websocket -> Participante], lock (asyncio.Lock), max 2 participants (medico + paciente), heartbeat.
- Auth: token JWT via query param, decode with jose, get papel and sub (user id / CNS).
- DB: SQLAlchemy 2.0 async models for SalaTeleatendimento and RegistroAtendimento (SOAP fields: ciap2, cid10, subjetivo, objetivo, avaliacao, plano). Persist on state sync / end of session.
- Message relay: offer/answer/ice forwarded to the other participant only.
- State sync: estado_medico (e.g., medico editing SOAP record, sharing CID/CIAP), estado_paciente (connection quality, consent).
- LGPD: consentimento required before joining (termo de consentimento LGPD).
- Logging audit without PHI in logs.

Tests: pytest with httpx/TestClient websocket, fake JWT, two clients exchange offer/answer/ice, rejection of third participant, invalid token, invalid CNS.

Keep code reasonably complete but not insanely long. Write in Portuguese comments/docstrings.

Let me write the code.

Key components:

```python
from __future__ import annotations
import asyncio, json, logging, uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Literal

import jwt  # pyjwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field, field_validator, ValidationError
from sqlalchemy import String, ForeignKey, DateTime, Enum as SAEnum, select
from sqlalchemy.ext.asyncio import AsyncSession
```

CNS validation algorithm: CNS must be 15 digits starting with 1,2,7,8,9. Checksum: for 1/2: sum with weights 15..1 mod 11 == 0. For 7/8/9: different algorithm (multiply, sum, mod 11, remainder must equal last digit computed via 11 - resto). I'll implement standard.

CPF validation standard.

Room manager with asyncio.Lock per room.

Message schema:

```python
class PapelParticipante(str, Enum): MEDICO, PACIENTE
class TipoMensagemWS(str, Enum):
    OFERTA_SDP = "offer"
    RESPOSTA_SDP = "answer"
    CANDIDATO_ICE = "ice_candidate"
    ESTADO_MEDICO = "estado_medico"
    ESTADO_PACIENTE = "estado_paciente"
    ENTRADA = "entrada"
    SAIDA = "saida"
    CONSENTIMENTO = "consentimento"
    FIM_ATENDIMENTO = "fim_atendimento"
    ERRO = "erro"
    HEARTBEAT = "heartbeat"
```

Payload models: OfertaSDP(sdp: str, tipo: Literal["offer"]), RespostaSDP, CandidatoICE(candidate, sdp_mid), EstadoMedico (editando_registro: bool, ciap2: str|None, cid10: str|None, soap fields?), EstadoPaciente (qualidade_conexao, consentimento_gravacao).

CIAP-2 format: letter + 2 digits. CID-10: letter + 2 digits + optional .x.

DB models (SQLAlchemy 2.0 declarative): SalaTeleatendimento(codigo_sala pk, agendamento_id, medico_id, paciente_id, cns_paciente, status, iniciada_em, encerrada_em), RegistroSOAP(id, sala_fk, subjetivo, objetivo, avaliacao, plano, ciap2, cid10, atualizado_em).

I'll assume a get_db_session dependency and settings with JWT secret. To keep module self-contained-ish, define placeholders importing from app.core (config, security, db). But tests need to run — I'll write tests with dependency overrides.

Auth: token in query param `?token=...`. Decode JWT: claims sub, papel, codigo_sala, cns (for paciente). Validate CNS if papel==PACIENTE.

Manager:

```python
class Participante:
    ws, papel, identificador (medico_id or cns), consentiu: bool
class Sala:
    codigo, participantes: dict[PapelParticipante, Participante], lock, criada_em, registro_soap...
```

Broadcast helper, send_json with pydantic serialization.

Handle messages: validate with Pydantic, route:
- offer/answer/ice: forward to other participant, tagging remetente papel.
- estado_medico: only medico can send; persist SOAP fields to DB; broadcast to room.
- estado_paciente: only paciente; broadcast.
- fim_atendimento: only medico; persist, close room, notify.
- heartbeat: pong.

Audit log: logger without PHI.

Tests file: tests/test_telemedicina_ws.py using TestClient, overriding get_db with sqlite aiosqlite? Simpler: override dependency to a fake session that records. Actually to keep testable, I'll make DB persistence optional via dependency `get_db` that tests override with a stub. Use TestClient websocket_connect with token generated via jwt.encode with test secret.

Write tests:
1. test_conexao_e_troca_sdp: medico connects, paciente connects, medico sends offer, paciente receives; paciente answers, medico receives; ice both ways.
2. test_rejeita_terceiro_participante
3. test_token_invalido_rejeitado
4. test_cns_invalido_rejeitado
5. test_estado_medico_persistido (with fake session capturing)
6. test_fim_atendimento_encerra_sala

For DB: I'll define `get_session` dependency returning AsyncSession; in WS endpoint use it. In tests override with a FakeSession object with async add/flush no-ops. Since we call `await session.execute(...)` maybe for loading sala — I'll design so sala lookup is via manager (in-memory) and DB persistence is best-effort with try/except, so fake session only needs `add` and `flush`. Actually loading sala record from DB to validate existence: I'll do it but wrap in try. Hmm, simpler: endpoint receives codigo_sala, validates via DB query `select(SalaTeleatendimento).where(codigo==...)`; if not found, close with error. Tests override get_session to return a fake that returns a sala. FakeSession.execute returns object with scalar_one_or_none -> SalaTeleatendimento instance. I can construct the SQLAlchemy model without a real DB (instances work detached).

Let me write the code now, being careful with length but complete.

Structure of telemedicina_ws.py:

- imports
- logger
- constants (MAX_PARTICIPANTES=2, etc.)
- validators: validar_cns, validar_cpf, validar_ciap2, validar_cid10
- Pydantic schemas
- SQLAlchemy models
- Dependencies: get_session (imported), settings
- Hub: Participante, Sala, GerenciadorSalas (singleton)
- Router with websocket endpoint
- helper: autenticar_ws(token) -> IdentidadeWS
- message handling loop

For JWT use pyjwt. Settings: from app.core.config import settings (SECRET_KEY, ALGORITHM). I'll import with fallback? Better to just import and in tests override settings attribute. I'll do `from app.core.config import settings`.

DB: `from app.core.database import get_session_async` — I'll define dependency name `get_db`. In tests, override router.dependency_overrides? FastAPI dependency_overrides works on app level: app.dependency_overrides[get_db] = ...

Write it.

Message envelope:

```python
class MensagemEntrada(BaseModel):
    tipo: TipoMensagemWS
    payload: dict[str, Any] = {}
```

Then dispatch by tipo parsing payload into specific model. Or use discriminated union:

```python
class EnvelopeEntrada(BaseModel):
    tipo: TipoMensagemWS
    payload: dict[str, Any]
```

Simpler dispatch.

Envelope saída:

```python
class EnvelopeSaida(BaseModel):
    tipo: TipoMensagemWS
    de_papel: PapelParticipante | None
    payload: dict
    timestamp: datetime
```

Now the endpoint flow:

```python
@router.websocket("/ws/telemedicina/sala/{codigo_sala}")
async def ws_telemedicina(websocket: WebSocket, codigo_sala: str, token: str, db: AsyncSession = Depends(get_db)):
    # authenticate
    identidade = autenticar_token(token)  # raises
    ...
```

On invalid token: accept then send erro and close with code 4401.

Room join: manager.entrar_sala(...) with lock; checks sala exists in DB (status agendada/em_andamento), papel matches (medico claim vs paciente claim), participant not duplicated, room capacity.

Consentimento LGPD: paciente must send consentimento before receiving medico's media? For signaling simplicity: require both to send `consentimento` message before any SDP relay? That could complicate tests. I'll require consentimento message with `termo_aceito: true` before relaying SDP; send erro otherwise. Tests include consent step. Good for SUS/LGPD compliance narrative.

Actually to keep tests manageable: yes, include consent in test 1.

fim_atendimento: medico sends; persist encerrada_em, status; broadcast fim; close all sockets.

Heartbeat: respond pong.

Also handle WebSocketDisconnect -> manager.sair_sala, notify other.

Audit logging: logger.info("SALA %s: evento=%s papel=%s", ...) no PHI.

Now write tests with TestClient (sync) — websocket_connect context managers. Need two threads? TestClient websocket_connect is sync and blocking within context; to have two sockets open simultaneously, use nested with blocks — that works in same thread since receive is explicit. Yes: nested `with client.websocket_connect(...) as ws1, client.websocket_connect(...) as ws2:` works.

Fake DB session:

```python
class FakeResult:
    def __init__(self, val): self._val = val
    def scalar_one_or_none(self): return self._val

class FakeDB:
    def __init__(self, sala): self.sala = sala; self.added = []
    async def execute(self, stmt): return FakeResult(self.sala)
    def add(self, obj): self.added.append(obj)
    async def flush(self): pass
    async def commit(self): pass
    async def rollback(self): pass
```

But the endpoint uses `Depends(get_db)` — override: `app.dependency_overrides[get_db] = lambda: fake_db`. For async dependency, FastAPI handles sync callable fine.

Hmm — but the module imports get_db from app.core.database. In the test I import it from the module. Fine.

Sala model instance: SalaTeleatendimento(codigo_sala="SALA-123", status=StatusSala.EM_ANDAMENTO, medico_id="med-1", cns_paciente="..."). Detached instance fine.

JWT tokens: jwt.encode({"sub": ..., "papel": "MEDICO", "codigo_sala": "SALA-123"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM). Tests set settings attributes directly.

CNS válido para teste: compute one. CNS starting with 7: algorithm — for 7,8,9: soma = sum(digit_i * (15 - i) for i in 0..14)? Actually the standard: pesos 15 down to 1 over 15 digits? Let me recall the official algorithm:

For CNS starting with 1 or 2: pesos 15,14,...,1 applied to the 15 digits; soma % 11 must == 0.

For 7, 8, 9: take first 11 digits, pesos 15..5? The known algorithm: 
- Multiply digits by weights 15,14,...,1? No. The known algorithm for 7/8/9: soma = sum(d[i] * (15 - i)) for i in 0..10 (11 digits, weights 15..5), resto = soma % 11; dv = 11 - resto; if dv == 11: dv = 0; if dv == 10: dv = 0? Hmm.

Standard implementation (from ibge/saude):

```
soma = 0
for i in range(11): soma += int(cns[i]) * (15 - i)
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0
if dv >= 10: dv = 0  # actually if dv == 11 -> 0, if dv == 10 -> recalc? 
```

Actually the known algorithm: if resto == 0? Let me recall properly. Common Python implementation:

```python
def valida_cns(cns):
    cns = cns.strip()
    if len(cns) != 15 or cns[0] not in '123789': return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if cns[0] in '12':
        return soma % 11 == 0
    # 7,8,9
    soma = sum(int(cns[i]) * (15 - i) for i in range(11))
    resto = soma % 11
    dv = 11 - resto
    if dv == 11: dv = 0
    if dv == 10:
        soma = sum(int(cns[i]) * (15 - i) for i in range(11)) + 2  # peso extra? 
```

Hmm, the real algorithm for 7/8/9: if dv == 10, then soma += 2 and recompute resto = soma % 11, dv = 11 - resto. Then check dv == int(cns[12])? Wait the check digits: cns has 15 digits; for 7/8/9, first 11 are base, digits 12-15 are check? Actually check: dv computed compared to... Let me recall the canonical JS:

```js
function validaCNS(v) {
  ...
  if (v.charAt(0) == '1' || v.charAt(0) == '2') {
    soma = sum(v[i] * (15 - i)) for i 0..14
    return soma % 11 == 0
  } else {
    soma = sum(v[i] * (15 - i)) for i 0..10
    dv = 11 - (soma % 11)
    if (dv == 11) dv = 0
    if (dv == 10) {
      soma = soma + 2
      dv = 11 - (soma % 11)
    }
    resultado = String(dv) + v.substring(11, 15)  // hmm
```

Actually the canonical: pis/pasest style. The known JS:

```js
soma = 0;
for (i = 0; i < 11; i++) soma += parseInt(v[i]) * (15 - i);
dv = 11 - (soma % 11);
if (dv == 11) dv = 0;
if (dv == 10) { soma = soma + 2; dv = 11 - (soma % 11); }
resultado = dv * 10 + parseInt(v[11]);  // no...
```

Hmm, I remember: for 7/8/9, the check is: `resultado = (dv * 10) + parseInt(v[11]); if resultado != 11... ` no.

Let me look at it differently — the widely used Python version:

```python
def _validar_cns(cns: str) -> bool:
    if len(cns) != 15 or not cns.isdigit() or cns[0] not in "123789":
        return False
    soma = sum(int(d) * p for d, p in zip(cns, range(15, 0, -1)))
    if cns[0] in "12":
        return soma % 11 == 0
    resto = (soma % 11)  # using full 15? no
```

Alternative widely used approach for 7/8/9 that avoids ambiguity: generate a valid CNS in test instead of hand-computing. I can write a helper in tests that generates a valid CNS for the 7/8/9 family by brute force: fix 12 digits, brute force last 3? That's 1000 combos — fine, or brute force check digits by trying.

Simpler: in tests, generate valid CNS by brute force over last digits until validator returns True. But validator is in the module under test — using it to generate test data is circular but acceptable pragmatically? Better: implement generation independently in test using the official algorithm.

Official algorithm (from Ministério da Saúde / known correct implementation):

For CNS starting with 7, 8 or 9:
```
soma = 0
for i in 0..14: peso? 
```
No — the correct known algorithm:

```
soma = sum(int(cns[i]) * (15 - i) for i in range(15))
if cns[0] in '12': return soma % 11 == 0
# else:
soma = sum(int(cns[i]) * (15 - i) for i in range(11))
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0
if dv == 10:
    soma += 2
    resto = soma % 11
    dv = 11 - resto
return dv == int(cns[11])  # ??? 
```

Hmm, but that only checks one digit. Actually I recall the check: `resultado = f"{dv}{cns[11:]}"`? 

Let me