The user wants me to implement a WebSocket Hub for Telemedicine (Teleconsulta) with WebRTC signaling for the MedIA project. This is for a Brazilian SUS (Sistema Único de Saúde) telemedicine system.

Requirements:
1. File: `backend/app/api/v1/telemedicina_ws.py`
2. WebSocket endpoint: `/ws/telemedicina/sala/{codigo_sala}`
3. Message exchange: SDP (offer/answer), ICE candidates
4. Medical/patient state synchronization in telemedicine room
5. Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
6. SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
7. Full compliance and automated test coverage with pytest

Let me design this properly:

**Architecture:**

1. **WebSocket Hub** - Connection manager for rooms
2. **Signaling messages** - SDP offer/answer, ICE candidates
3. **State synchronization** - medical state in the room
4. **Authentication** - CNS/CPF based identification
5. **Pydantic v2 models** for message validation
6. **SQLAlchemy 2.0** models for teleconsulta persistence

Let me structure the code:

```python
# backend/app/api/v1/telemedicina_ws.py
```

Key components:

1. **Pydantic Models (v2)**:
   - `MensagemWSBase` - base message
   - `SDPOffer`, `SDPAnswer` - SDP messages
   - `ICECandidate` - ICE candidate
   - `EstadoSala` - room state
   - `SinalizacaoMedica` - medical signals
   - Message types enum

2. **Connection Manager**:
   - `GerenciadorSalas` (Room Manager)
   - Track connections per room
   - Role-based (medico/paciente)
   - Broadcast to room

3. **WebSocket Endpoint**:
   - `/ws/telemedicina/sala/{codigo_sala}`
   - Auth via token (query param or first message)
   - Message routing

4. **Message Types**:
   - `offer`, `answer`, `ice-candidate`
   - `join`, `leave`, `estado-sala`
   - Medical state: SOAP notes, CIAP-2 codes, CID-10
   - Heartbeat/ping

5. **Security**:
   - Token validation
   - CNS/CPF validation (check digits)
   - Room access control

Let me write comprehensive code:

```python
# Arquivo: backend/app/api/v1/telemedicina_ws.py
"""
WebSocket Hub de Teleconsulta e Signaling WebRTC (C9)
...
"""
```

For CNS validation - the Brazilian CNS (Cartão Nacional de Saúde) has a validation algorithm:
- 15 digits
- First digit: 1, 2, 7, 8, 9
- Check digit algorithm (modulo 11)

For CPF validation - standard check digit algorithm.

Let me think about the message protocol:

```json
{
  "tipo": "offer" | "answer" | "ice" | "estado" | "chat" | "sinal-vital" | ...
  "de": "medico" | "paciente",
  "para": "medico" | "paciente" | "todos",
  "payload": {...},
  "timestamp": "..."
}
```

Message types:
- `autenticar` - initial auth
- `entrar` - join room
- `offer` - SDP offer
- `answer` - SDP answer
- `ice` - ICE candidate
- `estado-sala` - room state sync
- `soap` - SOAP note update (medical)
- `ciap` - CIAP-2 code
- `cid10` - CID-10 code
- `sinal-vital` - vital signs
- `chat` - text messages
- `prescricao` - prescription
- `encaminhamento` - referral
- `finalizar` - end teleconsulta
- `ping`/`pong` - heartbeat
- `erro` - error

Room state:
```python
class EstadoSala(BaseModel):
    codigo_sala: str
    participantes: list[ParticipanteInfo]
    medico_conectado: bool
    paciente_conectado: bool
    teleconsulta_iniciado: datetime | None
    status: StatusSala
```

Let me also think about the SQLAlchemy 2.0 model for persistence:

```python
class Teleconsulta(Base):
    __tablename__ = "teleconsultas"
    id: Mapped[uuid.UUID] = mapped_column(...)
    codigo_sala: Mapped[str]
    paciente_cns: Mapped[str]
    medico_cns: Mapped[str]
    cid10_principal: Mapped[str | None]
    ciap2_principal: Mapped[str | None]
    soap_subjetivo: ...
    soap_objetivo: ...
    soap_avaliacao: ...
    soap_plano: ...
    iniciado_em: ...
    finalizado_em: ...
    status: ...
```

For the WebSocket endpoint with FastAPI:

```python
@router.websocket("/ws/telemedicina/sala/{codigo_sala}")
async def websocket_telemedicina(
    websocket: WebSocket,
    codigo_sala: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    ...
```

Let me write the complete implementation. I'll structure it as:

1. Module docstring
2. Imports
3. Constants and enums
4. Pydantic models (messages)
5. Validators (CNS, CPF, CIAP-2, CID-10)
6. Connection manager (GerenciadorSalasTelemedicina)
7. SQLAlchemy model (or import from models)
8. WebSocket endpoint
9. Helper functions

Since the task says "contendo WebSocket endpoint", I should make it self-contained but reference the app structure. I'll include the SQLAlchemy model in the file or import it. To be safe and complete, I'll define what's needed within the file, with clear separation, and also provide a test file.

Let me write the code:

```python
# Arquivo: backend/app/api/v1/telemedicina_ws.py
"""
C9 — WebSocket Hub de Teleconsulta e Signaling WebRTC
=====================================================

Endpoint WebSocket: ``/ws/telemedicina/sala/{codigo_sala}``

Hub central de sinalização WebRTC (SDP offer/answer, ICE candidates) e
sincronização de estado clínico (SOAP, CIAP-2, CID-10) em salas de
teleatendimento do SUS, conforme padrões da Atenção Primária à Saúde (APS).

Protocolo de mensagens (JSON):
...
"""
```

Now the enums:

```python
class PapelParticipante(str, Enum):
    MEDICO = "medico"
    PACIENTE = "paciente"

class TipoMensagem(str, Enum):
    AUTENTICAR = "autenticar"
    ENTRAR = "entrar"
    SAIR = "sair"
    OFFER = "offer"
    ANSWER = "answer"
    ICE = "ice"
    ESTADO_SALA = "estado_sala"
    PARTICIPANTE_ENTROU = "participante_entrou"
    PARTICIPANTE_SAIU = "participante_saiu"
    SOAP = "soap"
    CIAP2 = "ciap2"
    CID10 = "cid10"
    SINAL_VITAL = "sinal_vital"
    CHAT = "chat"
    PRESCRICAO = "prescricao"
    ENCAMINHAMENTO = "encaminhamento"
    FINALIZAR = "finalizar"
    PING = "ping"
    PONG = "pong"
    ERRO = "erro"
    SISTEMA = "sistema"
```

Pydantic models:

```python
class MensagemEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    tipo: TipoMensagem
    payload: dict[str, Any] = Field(default_factory=dict)
    seq: int | None = None

class MensagemSaida(BaseModel):
    ...
```

SDP models:

```python
class SDPOffer(BaseModel):
    sdp: str
    type: Literal["offer"]
    ...

class SDPAnswer(BaseModel):
    sdp: str
    type: Literal["answer"]

class ICECandidate(BaseModel):
    candidate: str
    sdp_m_line_index: int | None
    sdp_mid: str | None
    username_fragment: str | None
```

Validators:

```python
def validar_cns(cns: str) -> bool:
    """Valida CNS (Cartão Nacional de Saúde) — 15 dígitos, módulo 11."""
    ...

def validar_cpf(cpf: str) -> bool:
    ...

def validar_ciap2(codigo: str) -> bool:
    """CIAP-2: letra + 2 dígitos (ex: A01, R05, T90, K29...)."""
    ...

def validar_cid10(codigo: str) -> bool:
    """CID-10: letra + 3 dígitos + opcional .1-2 dígitos (ex: E11.9, I10)."""
    ...
```

CNS validation algorithm:
- Must be 15 digits
- First char must be 1, 2, 7, 8, or 9
- Algorithm: sum = sum of (digit[i] * (15 - i)) for i in 0..14; sum % 11 == 0

Actually the CNS algorithm: 
- The number has 15 digits
- Multiply each digit by weights 15, 14, 13, ..., 1 (from left to right)
- Sum must be divisible by 11

Let me verify: For CNS "700000000000003":
7*15 + 0*14 + ... + 3*1 = 105 + 3 = 108. 108 % 11 = 108 - 99 = 9. Hmm, that doesn't work.

Let me recall the correct algorithm. The CNS validation:
- 15 digits
- First digit: 1, 2, 7, 8, 9
- Sum of (digit * weight) where weights go from 15 down to 1... 

Actually the standard algorithm:
```
soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
return soma % 11 == 0
```

Let me test with a known valid CNS: "700000000000003" — is this valid? Common test CNS values: 700000000000003, 700000000000831, 701403491980052, 702000000000407...

Let me compute 700000000000003:
digits: 7,0,0,0,0,0,0,0,0,0,0,0,0,0,3
weights: 15,14,13,12,11,10,9,8,7,6,5,4,3,2,1
sum = 7*15 + 3*1 = 105 + 3 = 108
108 % 11 = 9 ≠ 0. So that's not valid with this algorithm.

Hmm, maybe the algorithm is different. Let me recall... The CNS check digit algorithm (from DATASUS):

Actually, the correct algorithm for CNS:
1. The CNS has 15 digits
2. First digit must be 1, 2, 7, 8, or 9
3. Calculate: sum each digit multiplied by weights 15, 14, 13, ..., 1
4. The result must be divisible by 11

Let me check "898009178820004" (a commonly cited valid CNS):
digits: 8,9,8,0,0,9,1,7,8,8,2,0,0,0,4
weights: 15,14,13,12,11,10,9,8,7,6,5,4,3,2,1
sum = 8*15 + 9*14 + 8*13 + 0*12 + 0*11 + 9*10 + 1*9 + 7*8 + 8*7 + 8*6 + 2*5 + 0*4 + 0*3 + 0*2 + 4*1
= 120 + 126 + 104 + 0 + 0 + 90 + 9 + 56 + 56 + 48 + 10 + 0 + 0 + 0 + 4
= 120+126=246; 246+104=350; 350+90=440; 440+9=449; 449+56=505; 505+56=561; 561+48=609; 609+10=619; 619+4=623
623 % 11 = 623 - 55*11 = 623 - 605 = 18... wait 55*11 = 605, 623-605 = 18, that's > 11. 56*11 = 616, 623-616 = 7. So 623 % 11 = 7 ≠ 0.

Hmm. Let me reconsider. Maybe the weights are different.

The actual DATASUS algorithm for CNS:
```
soma = 0
peso = 15
for each digit:
    soma += digit * peso
    peso -= 1
resto = soma % 11
valid if resto == 0
```

That's what I did. Let me check another known valid CNS: "000000000000000" is trivially valid (sum=0). 

Known valid CNS examples from DATASUS docs: 
- 700 0000 0000 003 — hmm
- Let me search memory: The example in official docs is "898 0016 6559 0004"? 

Actually, I recall the algorithm might be: sum with weights 15..1, and check sum % 11 == 0. Let me verify with a generated CNS. The generation process: pick first 11 digits (starting with 1, 2, or 7,8,9), then compute 2 check digits (DV) such that the total weighted sum is divisible by 11.

For "700000000000003": first 13 digits are 7000000000000, and DV is "03". 
sum of first 13 digits with weights 15..3: 7*15 = 105.
Then DV: we need to find d14, d15 such that 105 + d14*2 + d15*1 ≡ 0 (mod 11).
105 % 11 = 105 - 99 = 6. So d14*2 + d15 ≡ -6 ≡ 5 (mod 11).
If d14=0, d15=5 → "05". If d14=1, d15=3 → "13". If d14=2, d15=1 → "21". Hmm "03" gives 0*2+3 = 3, 6+3 = 9 ≠ 0.

So "700000000000003" would not be valid under this algorithm. Maybe my memory of test CNS values is wrong.

Let me think about the official algorithm again. From the DATASUS "Validação do CNS" documentation:

```
O número do CNS é composto por 15 dígitos...
Para validar:
1. Multiplicar cada dígito pelo peso correspondente (15, 14, 13, ..., 1)
2. Somar todos os resultados
3. O resultado da soma deve ser divisível por 11
```

Yes, I'm fairly confident this is the algorithm. Let me find a valid example CNS. 

A commonly used valid CNS in tests: "000 0000 0000 0000" (all zeros) — valid trivially.

Another: "798 0097 5430 1153"? Let me compute: 7*15+9*14+8*13+0*12+0*11+9*10+7*9+5*8+4*7+3*6+0*5+1*4+1*3+5*2+3*1
= 105 + 126 + 104 + 0 + 0 + 90 + 63 + 40 + 28 + 18 + 0 + 4 + 3 + 10 + 3
= 105+126=231; +104=335; +90=425; +63=488; +40=528; +28=556; +18=574; +4=578; +3=581; +10=591; +3=594
594 % 11 = 594 - 54*11 = 594 - 594 = 0. ✓ Valid!

So "798009754301153" is a valid CNS under this algorithm. I'll use that in tests.

Also "898009178820004" gave 623, not divisible. Let me not use that one.

Let me double check "798009754301153" digit by digit:
7 9 8 0 0 9 7 5 4 3 0 1 1 5 3
weights: 15 14 13 12 11 10 9 8 7 6 5 4 3 2 1
7*15 = 105
9*14 = 126
8*13 = 104
0*12 = 0
0*11 = 0
9*10 = 90
7*9 = 63
5*8 = 40
4*7 = 28
3*6 = 18
0*5 = 0
1*4 = 4
1*3 = 3
5*2 = 10
3*1 = 3
Sum: 105+126 = 231; 231+104 = 335; 335+0+0 = 335; +90 = 425; +63 = 488; +40 = 528; +28 = 556; +18 = 574; +0 = 574; +4 = 578; +3 = 581; +10 = 591; +3 = 594.
59