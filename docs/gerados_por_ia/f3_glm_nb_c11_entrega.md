The user wants me to create a reactive electronic queue service for telehealth welcome and voice calling (C11) for the MedIA project. Let me analyze the requirements:

1. Create `backend/app/services/fila_teleatendimento.py` with:
   - In-memory priority queue (heapq/asyncio)
   - Estimated waiting time calculation
   - WebSocket notification dispatch

2. Architecture guidelines:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

This is a Brazilian public health system (SUS - Sistema Único de Saúde) context. Let me design this properly:

**Key components:**

1. **Priority Queue**: Using `asyncio` with `heapq` for priority management. Priority levels in SUS context:
   - Priority 1: Emergency/urgency (Protocolo de Manchester / Classificação de Risco)
   - Priority 2: Elderly (60+), pregnant women, people with disabilities, children
   - Priority 3: Normal cases
   - FIFO within same priority

2. **Estimated waiting time**: Based on average consultation time and position in queue, considering priorities.

3. **WebSocket notifications**: When patient is called, when queue position changes, etc.

4. **SUS compliance**:
   - CNS (Cartão Nacional de Saúde) validation - 15 digits
   - CPF validation - 11 digits with check digits
   - CIAP-2 codes for primary care (Atenção Primária à Saúde)
   - CID-10 for diagnoses
   - SOAP method (Subjective, Objective, Assessment, Plan)
   - LGPD compliance (Lei Geral de Proteção de Dados) - important for health data

Let me structure the code:

```python
# backend/app/services/fila_teleatendimento.py
```

**Models (Pydantic v2):**

```python
class PrioridadeEnum(str, Enum):
    EMERGENCIA = 1  # Vermelho - Manchester
    URGENTE = 2     # Laranja
    PRIORITARIO = 3 # Amarelo - gestantes, idosos, PCD, crianças
    NORMAL = 4      # Verde/Azul

class StatusFilaEnum(str, Enum):
    AGUARDANDO = "aguardando"
    CHAMADO = "chamado"
    EM_ATENDIMENTO = "em_atendimento"
    ATENDIDO = "atendido"
    DESISTIU = "desistiu"
    AUSENTE = "ausente"

class EntradaFila(BaseModel):
    id: UUID
    paciente_id: UUID
    nome_paciente: str  # masked for LGPD
    cns: str | None
    cpf: str | None
    prioridade: PrioridadeEnum
    motivo: str
    ciap2: str | None
    cid10: str | None
    timestamp_entrada: datetime
    status: StatusFilaEnum
    ...
```

**CNS validation algorithm:**
The CNS (Cartão Nacional de Saúde) validation:
- Must be 15 digits
- Starting with 1, 2 (regular cards), 7, 8, 9 (temporary cards)
- Check digit algorithm (Mod 11):
  - Multiply each digit by weights 15, 14, 13, ..., 2
  - Sum them
  - remainder = sum % 11
  - If remainder < 2: dv = 11 - remainder... actually let me recall the correct algorithm:

The CNS validation:
1. 15 digits
2. First digits: 1 or 2 (definitive) or 7, 8, 9 (provisional)
3. Algorithm: 
   - soma = sum of digit[i] * (15 - i) for i in 0..14
   - resto = soma % 11
   - if resto == 0: valid
   - else: dv = 11 - resto, and the last digit must equal dv... 

Actually the correct algorithm for CNS:
- Take the first 14 digits, multiply by weights from 15 down to 2
- Sum all
- resto = soma % 11
- If resto != 0, dv = 11 - resto
- If resto == 0, dv = 0
- The 15th digit must equal dv

Wait, let me be precise. The official CNS validation (from DATASUS):

```
Para validar o CNS:
1. O número deve ter 15 dígitos
2. Os números podem começar com: 1, 2, 7, 8 ou 9
3. Cálculo do dígito verificador:
   - Multiplicar cada dígito (dos 14 primeiros) pela sequência 15, 14, 13, ..., 2
   - Somar todos os resultados
   - resto = soma % 11
   - Se resto != 0, dv = 11 - resto
   - Se resto == 0, dv = 0
   - O 15º dígito deve ser igual a dv
```

Hmm, actually the standard algorithm is:

```
soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
resto = soma % 11
if resto != 0:
    dv = 11 - resto
else:
    dv = 0
valid = dv == 0 or ... 
```

Let me look at the well-known implementation:

```python
def valida_cns(cns):
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

Yes! That's the correct one. The sum of all 15 digits multiplied by weights 15 down to 1 must be divisible by 11. Wait, weights: 15, 14, 13, ..., 1? Let me verify with a known valid CNS.

Known valid CNS example: 700 0000 0000 0003? Hmm, I recall test CNS like "898 0000 0000 0001"? Let me think about the algorithm more carefully.

The official algorithm from DATASUS (Rotina de validação do CNS):

```
1. Somar os 15 dígitos, cada um multiplicado pelo peso:
   posição 1 → peso 15
   posição 2 → peso 14
   ...
   posição 15 → peso 1
2. Obter o resto da divisão da soma por 11
3. Se o resto for 0, o CNS é válido
```

So: `soma % 11 == 0` where weights go from 15 to 1.

Let me verify: CNS "700000000000003"? Hmm. Actually, let me construct one. Take 14 digits "70000000000000" and compute dv:
- soma = 7*15 + 0*14 + ... = 105
- resto = 105 % 11 = 105 - 99 = 6
- dv = 11 - 6 = 5
So CNS would be "700000000000005". Check: soma = 105 + 5*1 = 110. 110 % 11 = 0. ✓

So the algorithm: sum(digit[i] * (15 - i) for i in range(15)) % 11 == 0. With i from 0 to 14, weights 15 down to 1. Yes.

**CPF validation:**
Standard Brazilian CPF:
- 11 digits
- DV1: sum(digit[i] * (10 - i) for i in range(9)), resto = (soma * 10) % 11, if resto == 10 then 0
- DV2: sum(digit[i] * (11 - i) for i in range(10)), resto = (soma * 10) % 11, if resto == 10 then 0
- Reject sequences like 111.111.111-11

**CIAP-2 codes**: International Classification of Primary Care, 2nd edition. Codes like:
- A01: Tontura
- A02: Colapso/síncope
- R05: Tosse
- R06: Chiado no peito/sibilância
- F29: Sintoma/depressão
- P76: Alteração do comportamento
- etc.

Format: letter + 2 digits.

**CID-10 codes**: letter + 2 digits + optional .X (e.g., J45, E11.9). Format: `[A-Z]\d{2}(\.\d{1,2})?`

**Priority calculation (Classificação de Risco - adapted Manchester):**
- Vermelho (Emergência): atendimento imediato
- Laranja (Muito urgente): até 10 min
- Amarelo (Urgente): até 60 min
- Verde (Pouco urgente): até 120 min
- Azul (Não urgente): até 240 min

For teleatendimento, we can adapt. Also legal priorities (Estatuto do Idoso - Lei 10.741/2003, Lei 13.146/2015 - PCD, gestantes, lactantes, crianças de colo).

**Queue implementation with heapq:**

```python
import heapq
import itertools

heap: list[tuple[int, float, int, EntradaFila]] = []
# tuple: (priority, timestamp, counter, entry)
counter = itertools.count()  # tie-breaker for FIFO
```

Priority: lower number = higher priority. Use timestamp for FIFO within same priority.

**Estimated wait time:**
- Track average service duration (EWMA - exponentially weighted moving average)
- For each waiting entry: count how many entries ahead have higher or equal priority
- estimated_wait = position * avg_service_time / available_professionals

**WebSocket notifications:**
- Event types: `paciente_chamado`, `posicao_atualizada`, `paciente_removido`, `fila_atualizada`, `profissional_disponivel`
- Use a connection manager pattern (the service emits events; the WebSocket layer subscribes)

Since this is a service file, I should design it so it can dispatch to an event bus / callback system that the WebSocket layer consumes. I'll create an `EventBus` or use asyncio queues for subscribers.

**Voice calling (Chamada por Voz):**
The task mentions "Chamada por Voz" - voice calling. This is common in waiting rooms: "Senha X, guichê Y" announced via TTS. For teleatendimento, when a professional calls a patient, we generate a call event with the message text for TTS. I'll include a `gerar_mensagem_chamada` function and event payload with the text to be synthesized.

**LGPD considerations:**
- Mask names in notifications (e.g., "João S. Silva" → first name + initial)
- Don't expose full CPF/CNS in events
- Data retention: entries removed after attendance

**Structure of the file:**

Since the task asks for one file `fila_teleatendimento.py`, I'll put the service there, but I should also provide:
- Schemas (Pydantic) — could be in the same file or referenced. The task says create the service file. I'll keep schemas in the service file or import from a schemas module. To be self-contained but modular, I'll define Pydantic models in the service file (or better: reference `app/schemas/fila.py`). Hmm, the instruction says "crie backend/app/services/fila_teleatendimento.py" — the main deliverable. But tests need to import it. I'll make the service file self-contained with its models, and provide tests in `backend/tests/services/test_fila_teleatendimento.py`.

Also maybe a small `__init__.py` note. Let me also consider SQLAlchemy 2.0 — the service is in-memory, but persistence hooks could be mentioned. The guidelines say SQLAlchemy 2.0 — maybe provide an optional persistence adapter or at least typed models for persistence. To keep focus, I'll include an optional repository protocol (Protocol class) for persistence that can be implemented with SQLAlchemy, and show a SQLAlchemy 2.0 model in a comment or separate snippet? The task is primarily the in-memory queue. I'll include a `Protocol` for persistence and mention SQLAlchemy integration. Actually, to demonstrate SQLAlchemy 2.0 compliance, I could include a small SQLAlchemy model for persisting queue events (audit). But the file is a service... Let me include:

1. `fila_teleatendimento.py` — main service with:
   - Enums, Pydantic models (v2, strict typing)
   - Validators for CNS/CPF/CIAP-2/CID-10
   - `FilaTeleatendimento` class with asyncio + heapq
   - Wait time estimation
   - Event bus for WebSocket dispatch
   - Voice call message generation
   - Metrics

2. `test_fila_teleatendimento.py` — pytest tests with pytest-asyncio

Let me write the code.

```python
"""Serviço de Fila Eletrônica Reativa de Acolhimento e Chamada por Voz (C11).

Projeto MedIA — Teleatendimento SUS/APS.

Implementa fila de prioridades em memória (heapq + asyncio) para acolhimento
e classificação de risco, com cálculo de tempo estimado de espera e disparo
de notificações via WebSocket.

Conformidade:
- Classificação de Risco adaptada do Protocolo de Manchester (SUS).
- Prioridades legais: Lei 10.741/2003 (Estatuto do Idoso), Lei 13.146/2015
  (PCD), gestantes e lactantes, crianças de colo.
- Codificação CIAP-2 (APS) e CID-10.
- Identificação por CNS (validação módulo 11 DATASUS) ou CPF.
- LGPD (Lei 13.709/2018): minimização de dados, mascaramento de PII em
  eventos broadcast, trilha de auditoria.
"""
```

Now the models:

```python
from __future__ import annotations

import asyncio
import heapq
import itertools
import logging
import re
import time
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import IntEnum, StrEnum
from typing import Any, AsyncIterator, Callable, Final, Literal, Protocol, runtime_checkable
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
```

Python 3.12: `datetime.UTC` is available (3.11+). Use `from datetime import UTC`.

Enums:

```python
class Prioridade(IntEnum):
    """Níveis de prioridade — menor valor = maior prioridade (heap min)."""
    EMERGENCIA = 1      # Vermelho — risco de morte, atendimento imediato
    MUITO_URGENTE = 2   # Laranja — até 10 minutos
    URGENTE = 3         # Amarelo — até 60 minutos
    PRIORITARIO = 4     # Amarelo + prioridade legal (idoso 60+, PCD, gestante, lactante, criança < 2 anos)
    POUCO_URGENTE = 5   # Verde — até 120 minutos
    NAO_URGENTE = 6     # Azul — até 240 minutos
```

Hmm, mixing clinical risk and legal priority. Maybe better:

```python
class ClassificacaoRisco(StrEnum):
    VERMELHO = "vermelho"    # Emergência
    LARANJA = "laranja"      # Muito urgente
    AMARELO = "amarelo"      # Urgente
    VERDE = "verde"          # Pouco urgente
    AZUL = "azul"            # Não urgente
```

And priority computed from risk + flags (prioridade legal). The heap key: (priority_value, timestamp, seq).

Let me define:

```python
class Prioridade(IntEnum):
    EMERGENCIA = 1
    MUITO_URGENTE = 2
    URGENTE_PRIORITARIO = 3   # urgente + prioridade legal
    URGENTE = 4
    PRIORITARIO = 5           # prioridade legal, risco baixo
    POUCO_URGENTE = 6
    NAO_URGENTE = 7
```

Hmm, this gets complex. Simpler approach: base priority from risk classification, then legal priority bumps within same risk level. Actually a common approach: priority = risk_level, and tie-break by (legal_priority flag desc, timestamp asc). But legal priority should jump ahead of non-priority within same risk, and possibly ahead of lower risk levels.

Let me do: heap key = (prioridade_efetiva, timestamp, seq) where:

```python
PRIORIDADE_BASE: dict[ClassificacaoRisco, int] = {
    ClassificacaoRisco.VERMELHO: 1,
    ClassificacaoRisco.LARANJA: 2,
    ClassificacaoRisco.AMARELO: 3,
    ClassificacaoRisco.VERDE: 4,
    ClassificacaoRisco.AZUL: 5,
}

def prioridade_efetiva(risco, prioridade_legal):
    base = PRIORIDADE_BASE[risco]
    if prioridade_legal and base > 1:
        return base - 0.5  # entre seu nível e o nível acima
    return base
```

Using floats is fine for heapq. Or multiply by 2 and use ints: base*2, legal → base*2 - 1. Cleaner with ints:

```python
def chave_prioridade(risco: ClassificacaoRisco, prioridade_legal: bool) -> int:
    base = PRIORIDADE_BASE[risco] * 2
    return base - 1 if prioridade_legal else base
```

So VERMELHO=2 (or 1 with legal), LARANJA=4/3, AMARELO=6/5, VERDE=8/7, AZUL=10/9. Lower = first. Good.

Status:

```python
class StatusEntrada(StrEnum):
    AGUARDANDO = "aguardando"
    CHAMADO = "chamado"
    EM_ATENDIMENTO = "em_atendimento"
    ATENDIDO = "at