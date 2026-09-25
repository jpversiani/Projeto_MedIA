The user wants me to create a reactive electronic queue service for telehealth (teleatendimento) with voice calling for the MedIA project. Let me analyze the requirements:

1. **File**: `backend/app/services/fila_teleatendimento.py`
2. **Requirements**:
   - Priority queue in memory (heapq/asyncio)
   - Estimated waiting time calculation
   - WebSocket notification dispatch
   - Voice calling (chamada por voz)

3. **Architecture guidelines**:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me design this properly:

**Domain concepts (Brazilian SUS context)**:
- Fila de acolhimento (welcoming/triage queue) - this is the "acolhimento" in APS (Atenção Primária à Saúde)
- Classificação de risco (risk classification) - typically colors: Vermelho (red), Laranja (orange), Amarelo (yellow), Verde (green), Azul (blue) - Manchester protocol adapted
- Priority levels based on risk classification
- CNS (Cartão Nacional de Saúde) - 15 digits
- CPF - 11 digits
- CIAP-2 codes for primary care reasons for encounter
- CID-10 for diagnoses
- SOAP method (Subjective, Objective, Assessment, Plan)

**Priority queue design**:
- Use `asyncio` with `heapq` for priority queue
- Priority levels: 
  - 1 = VERMELHO (emergência) - atendimento imediato
  - 2 = LARANJA (muito urgente) - 10 min
  - 3 = AMARELO (urgente) - 60 min
  - 4 = VERDE (pouco urgente) - 120 min
  - 5 = AZUL (não urgente) - 240 min
- Tiebreaker: FIFO by entry time (heapq with tuple (priority, timestamp, sequence))

**Estimated waiting time**:
- Based on average consultation time per priority
- Position in queue × average service time
- Should account for number of active professionals

**WebSocket notifications**:
- Events: ENTRY (paciente entrou na fila), CALLED (paciente chamado), CONFIRMED, REMOVED, UPDATED (tempo estimado atualizado)
- Use a connection manager pattern (in-memory dict of websocket connections)
- Voice calling: generate text for TTS (text-to-speech) - the actual TTS could be via browser SpeechSynthesis on frontend, but backend can emit the message to be spoken

**Voice calling (chamada por voz)**:
- When a patient is called, generate a voice message like "Paciente João Silva, dirija-se ao consultório 3"
- LGPD consideration: avoid full name in public announcements? Actually in SUS they call names publicly. But for privacy, maybe use first name + initial. Let me include a masked name option.

**Structure**:

```python
# backend/app/services/fila_teleatendimento.py
```

Since it's a single file, I need to make it self-contained but well-organized. However, tests need to import it. Let me create:

1. `backend/app/services/fila_teleatendimento.py` - main service
2. `backend/tests/services/test_fila_teleatendimento.py` - tests

Let me think about the design:

```python
from __future__ import annotations

import asyncio
import heapq
import itertools
import re
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum, IntEnum
from typing import Any, Final

from pydantic import BaseModel, Field, field_validator, ConfigDict, computed_field
```

**Models (Pydantic v2)**:

```python
class ClassificacaoRisco(StrEnum):
    VERMELHO = "VERMELHO"
    LARANJA = "LARANJA"
    AMARELO = "AMARELO"
    VERDE = "VERDE"
    AZUL = "AZUL"

class Prioridade(IntEnum):
    VERMELHO = 1
    LARANJA = 2
    AMARELO = 3
    VERDE = 4
    AZUL = 5

TEMPO_ALVO_MINUTOS: dict[ClassificacaoRisco, int] = {
    VERMELHO: 0, LARANJA: 10, AMARELO: 60, VERDE: 120, AZUL: 240
}

TEMPO_MEDIO_CONSULTA_MINUTOS: Final[int] = 15  # configurable
```

**Entrada na fila**:

```python
class EntradaFila(BaseModel):
    model_config = ConfigDict(frozen=True)  # maybe not frozen since status changes
    
    id: uuid.UUID
    paciente_id: uuid.UUID
    nome_social: str  # nome social/civil
    documento: str  # CNS or CPF validated
    documento_tipo: Literal["CNS", "CPF"]
    classificacao_risco: ClassificacaoRisco
    queixa_ciap2: str | None  # CIAP-2 code
    unidade_id: uuid.UUID
    profissional_id: uuid.UUID | None
    consultorio: str | None
    status: StatusFila
    entrado_em: datetime
    chamado_em: datetime | None
    ...
```

Document validation:
- CNS: 15 digits, validation algorithm (starts with 1, 2, 7, 8, 9)
- CPF: 11 digits with check digits

Let me implement CNS validation:
CNS validation algorithm:
1. Must have 15 digits
2. First character must be 1, 2, 7, 8, or 9
3. Check digit calculation: sum of (digit * weight) where weights cycle 5,4,3,2,9,8,7,6,5,4,3,2 for first 12 digits... Actually the standard algorithm:

For CNS starting with 1, 2, 7, 8, 9:
- Take first 12 digits
- Multiply each digit by weights [5,4,3,2,9,8,7,6,5,4,3,2]
- Sum = S
- If S % 11 == 0, DV = 0... Actually:

The standard algorithm:
```
soma = 0
pesos = [5,4,3,2,9,8,7,6,5,4,3,2]  # wait, that's 12 weights for 12 digits? 
```

Actually the classic algorithm for CNS:
```
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    soma = sum(int(d) * w for d, w in zip(cns[:12], [5,4,3,2,9,8,7,6,5,4,3,2]))  # hmm
```

Wait, let me recall correctly. The CNS validation:

```
peso = 5
soma = 0
for i in range(12):
    soma += int(cns[i]) * peso
    peso -= 1
    if peso < 2:
        peso = 9
dv = 11 - (soma % 11)
if dv == 11: dv = 0
if dv == 10: return False  # invalid
return int(cns[12]) == dv and cns[13:] == '00'  # hmm no
```

Actually the full CNS has 15 digits: 12 base + DV + "00"? No. Let me think again.

CNS format: 15 digits. For cards starting with 1, 2: the last 3 digits... Actually:

The algorithm (from official sources):
1. CNS must have 15 digits
2. First digit in {1, 2, 7, 8, 9}
3. Calculation: multiply the first 12 digits by the sequence of weights 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2 (repeating 5,4,3,2 then 9,8,7,6,5,4,3,2)
4. Sum the results
5. DV = 11 - (sum % 11)
6. If DV == 11, DV = 0; if DV == 10, invalid
7. The 13th digit must equal DV, and the last two digits must be "00"? 

Hmm, no. Actually for CNS starting with 1 or 2, the check digit is the 13th digit and the last two are "00"? Let me recall: CNS numbers like "116 809 929 900 004" - yes, many CNS end in 00. But for provisory CNS starting with 7, 8, 9, the last digits vary.

Actually the correct algorithm per the Ministry of Health:

```
soma = 0
peso = 5
for i in range(12):
    soma += int(cns[i]) * peso
    peso -= 1
    if peso < 2:
        peso = 9
resto = soma % 11
dv = 11 - resto
if dv == 11:
    dv = 0
if dv == 10:
    return False
return int(cns[12]) == dv and cns[13:15] == "00"
```

Hmm, but that requires last two digits to be "00" which isn't right for all CNS. Let me check: Actually for the 15-digit CNS, the validation is:

The official algorithm validates the first 13 digits (12 + DV), and the last 2 digits must be "00" for regular CNS. Hmm, actually I recall that the check is: the 13th digit is the DV computed from the first 12, and digits 14-15 must be "00". Wait no...

Let me look at this differently. Common implementations found in Brazilian projects:

```python
def valida_cns(cns: str) -> bool:
    cns = ''.join(filter(str.isdigit, cns))
    if len(cns) != 15 or cns[0] not in '12789':
        return False
    soma = sum(int(d) * w for d, w in zip(cns[:12], [5,4,3,2,9,8,7,6,5,4,3,2]))
    dv = 11 - (soma % 11)
    if dv == 11:
        dv = 0
    if dv == 10:
        return False
    return int(cns[12]) == dv and cns[13:] == '00'
```

Hmm, but this fails for CNS like "700000000003598"? Let me test mentally... Actually there's another variant where the DV is computed over 14 digits with weights cycling. Let me recall the official document "Validação do CNS":

From the DATASUS documentation:
- The CNS check digit algorithm: weights 5,4,3,2,9,8,7,6,5,4,3,2 applied to the first 12 digits, sum, DV = 11 - (sum mod 11), if DV=11 → 0, if DV=10 → invalid. The 13th digit is the DV. The last two digits are "00" for definitive CNS (starting 1,2). For provisory (7,8,9), hmm.

Actually, I've seen implementations that check `cns[13:] == '00'` only for the 1/2 series. But many implementations just check the 13-digit DV and require last two "00" regardless. Hmm.

Actually wait — I recall the correct official algorithm validates all 15 digits:

```
pesos = [15,14,13,12,11,10,9,8,7,6,5,4,3,2,1]  # no...
```

Let me think about a known valid CNS: 116 809 929 900 004? Or "89800420859"? That's 11 digits, no.

Known test CNS values: "116.809.929.900.004" is commonly cited as valid. Let's verify with the algorithm:
Digits: 1 1 6 8 0 9 9 2 9 9 0 0 | 0 | 0 4
Weights: 5 4 3 2 9 8 7 6 5 4 3 2
Sum = 1*5 + 1*4 + 6*3 + 8*2 + 0*9 + 9*8 + 9*7 + 2*6 + 9*5 + 9*4 + 0*3 + 0*2
= 5 + 4 + 18 + 16 + 0 + 72 + 63 + 12 + 45 + 36 + 0 + 0 = 271
271 % 11 = 271 - 264 = 7
DV = 11 - 7 = 4
13th digit = 0? Hmm, the 13th digit of "116809929900004" is... positions: 1,1,6,8,0,9,9,2,9,9,0,0,0,0,4. 13th = 0. But DV computed = 4. Doesn't match. So my algorithm variant is wrong, OR the number is wrong.

Hmm. Let me try the other common algorithm where weights cycle differently:

Alternative: weights for 15 digits: 5,4,3,2,9,8,7,6,5,4,3,2,9,8,7? No...

Actually, I found it. The official CNS validation (from ConecteSUS / gov):

```
def validar_cns(cns):
    cns = re.sub("[^0-9]", "", cns)
    if len(cns) != 15:
        return False
    if cns[0] not in ['1','2','7','8','9']:
        return False
    soma = 0
    for i in range(15):
        # pesos: 5,4,3,2,9,8,7,6,5,4,3,2 repeating? 
```

Hmm, let me recall the actual official pseudo-code from the Ministry of Health document:

```
soma = 0
peso = 5
para i de 0 até 11:
    soma += cns[i] * peso
    peso--
    se peso < 2: peso = 9
dv = 11 - (soma % 11)
se dv == 11: dv = 0
se dv == 10: inválido
se cns[12] != dv: inválido
se cns[13:15] != "00": inválido
```

Hmm wait, but that requires the last two digits to be 00. And "116809929900004" ends in "04", not "00". So maybe that number isn't valid, or my recollection of it is wrong.

Let me construct a valid CNS with the algorithm: first 12 digits "116809929900", sum = 271 (computed above), DV = 4, so valid CNS = "116809929900" + "4" + "00" = "116809929900400". Hmm.

Actually, I've seen "116 809 929 900 004" cited... but maybe it's "116.809.929.900.400"? I'm not sure. Let me just generate valid CNS values using the algorithm for tests. E.g., base "116809929900" → DV=4 → CNS "116809929900400". That would be valid per the algorithm.

Hmm wait, actually I want to double check the weight cycle. The official algorithm from the Ministry of Health (Portaria) for CNS:

"Para obter o DV: multiplicar cada um dos 12 primeiros dígitos pelos pesos 5,4,3,2,9,8,7,6,5,4,3,2 respectivamente; somar os resultados; calcular 11 - (soma mod 11); se resultado = 11, DV = 0; se resultado = 10, número inválido."

Yes, that matches. And the last two digits: for the definitive CNS (starting with 1 or 2), the number is composed of: 1 digit (1 or 2) + 11 digits (Voter registration / others) + DV + "00"? Hmm, actually I believe the structure is: the 15-digit CNS = 13 significant digits + "00" filler for the definitive series. And provisory CNS (7,8,9) also ends with "00"? 

Hmm, actually I recall provisory CNS numbers like "701205610372004"? Not sure.

To be safe in implementation: validate DV over first 12 digits → 13th digit, and require last two digits "00". This is the widely used implementation. Actually, let me reconsider — many implementations do NOT require the last two to be "00". For example:

```python
def validate_cns(cns):
    ...
    soma = sum(int(d)*w for d,w in zip(cns[:12], [5,4,3,2,9,8,7,6,5,4,3,2]))
    dv = 11 - (soma % 11)
    if dv == 11: dv = 0
    if dv == 10: return False
    return int(cns[12]) == dv and cns[13:] == '00'
```

vs another one that computes over 14 digits:

```python
    soma = sum(int(d)*w for d,w in zip(cns[:14], [5,4,3,2,9,8,7,6,5,4,3,2,9,8]))
    dv = 11 - (soma % 11)
    ...
    return int(cns[14]) == dv
```

Hmm. I've definitely seen the version requiring "00" at the end. The official DATASUS doc says: "O CNS é composto por 15