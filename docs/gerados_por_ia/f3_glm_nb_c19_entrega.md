The user wants me to create a reactive electronic queue service for telehealth reception and voice calling (C19) for the MedIA project. Let me analyze the requirements:

1. **File**: `backend/app/services/fila_teleatendimento.py`
2. **Requirements**:
   - Priority queue in memory (heapq/asyncio)
   - Estimated waiting time calculation
   - WebSocket notification dispatch
3. **Architecture guidelines**:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me design this properly:

**Domain context**: This is a Brazilian public health system (SUS) telehealth queue. Key concepts:
- **Acolhimento** (reception/triage) - the first contact where risk classification happens
- **Classificação de Risco** (risk classification) - Manchester protocol or similar, with priorities like:
  - Vermelho (Red) - Emergência
  - Laranja (Orange) - Muito Urgente
  - Amarelo (Yellow) - Urgente
  - Verde (Green) - Pouco Urgente
  - Azul (Blue) - Não Urgente
- **CNS** (Cartão Nacional de Saúde) - National Health Card
- **CPF** - Brazilian tax ID
- **CIAP-2** - International Classification of Primary Care
- **CID-10** - ICD-10

**Priority queue design**:
- Use `asyncio` with `heapq` for thread-safe async priority queue
- Priority levels based on risk classification
- Tie-breaking by arrival time (FIFO within same priority)
- Aging mechanism to prevent starvation (important for SUS equity!)

**Estimated waiting time**:
- Based on average consultation time per priority
- Position in queue × average service time
- Should account for number of active professionals

**WebSocket notifications**:
- Events: patient added, patient called, queue updated, estimated time updated
- Voice calling (chamada por voz) - TTS integration point

Let me structure the code:

```python
# backend/app/services/fila_teleatendimento.py
```

Key components:
1. **Enums**: PrioridadeAcolhimento (Manchester colors), StatusFila, EventoFila
2. **Pydantic models**: 
   - `PacienteFila` (patient in queue with CNS/CPF validation)
   - `EntradaFila` (queue entry)
   - `ChamadaTeleatendimento` (call event)
   - `TempoEstimadoResponse`
3. **Validators**: CNS validation (algorithm), CPF validation (algorithm)
4. **Service class**: `FilaTeleatendimentoService`
   - Async priority queue with heapq
   - Aging mechanism
   - Estimated time calculation
   - WebSocket manager integration
   - Voice call dispatch

Let me write the CNS validation algorithm:
- CNS must be 15 digits
- Valid starting numbers: 1, 2, 7, 8, 9
- Algorithm: sum of digits with weights [15,14,13,12,11,10,9,8,7,6,5,4,3,2,1], result must be divisible by 11

CPF validation:
- Standard check digits algorithm

Let me think about the priority system for SUS acolhimento:

Manchester classification adapted for telehealth (APS):
- `VERMELHO` = 1 (Emergência - atendimento imediato)
- `LARANJA` = 2 (Muito urgente - até 10 min)
- `AMARELO` = 3 (Urgente - até 60 min)
- `VERDE` = 4 (Pouco urgente - até 120 min)
- `AZUL` = 5 (Não urgente - até 240 min)

Also should consider:
- Idosos (elderly, 60+), gestantes (pregnant), PCD, lactantes have legal priority in Brazil (Estatuto do Idoso, Lei 10.741/2003)
- So priority score = base priority from risk + legal priority adjustments

Aging: increase priority score over time to prevent starvation of lower priorities.

**Estimated time calculation**:
- `tempo_estimado = posição_efetiva × tempo_médio_atendimento / profissionais_ativos`
- Track moving average of actual consultation durations (EWMA - exponentially weighted moving average)

**WebSocket notifications**:
- Event types: `ENTRADA_FILA`, `CHAMADA`, `CONFIRMACAO_CHAMADA`, `SAIDA_FILA`, `ATUALIZACAO_FILA`, `TEMPO_ESTIMADO_ATUALIZADO`
- Voice call: `CHAMADA_VOZ` with text for TTS

Let me also think about SQLAlchemy 2.0 integration - the service should be able to persist events. But since the queue is in-memory, maybe I should have optional repository hooks. The guidelines say SQLAlchemy 2.0, so I should include models or at least type hints for session usage. Let me include a lightweight persistence hook pattern.

Actually, let me design it as:
- The service is in-memory (as requested)
- It emits domain events via WebSocket
- It has optional async callbacks/persistence hooks for SQLAlchemy integration
- Pydantic v2 models for all data transfer

Let me write comprehensive code with strict typing:

```python
"""Fila eletrônica reativa de acolhimento e chamada por voz (C19)."""

from __future__ import annotations

import asyncio
import heapq
import itertools
import logging
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from enum import StrEnum, IntEnum
from typing import Any, AsyncIterator, Callable, Coroutine, Final, Literal, Self
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, computed_field
```

For Python 3.12, I can use:
- `type` statements for type aliases
- `StrEnum`
- `Self`
- Modern generics

Let me define the models:

```python
class ClassificacaoRisco(StrEnum):
    VERMELHO = "VERMELHO"
    LARANJA = "LARANJA"
    AMARELO = "AMARELO"
    VERDE = "VERDE"
    AZUL = "AZUL"

class PrioridadeLegal(StrEnum):
    NENHUMA = "NENHUMA"
    GESTANTE = "GESTANTE"
    LACTANTE = "LACTANTE"
    IDOSO = "IDOSO"
    PCD = "PCD"
    CRIANCA = "CRIANCA"  # criança de colo
```

Priority weights:
```python
PESO_RISCO: dict[ClassificacaoRisco, int] = {
    VERMELHO: 100,
    LARANJA: 80,
    AMARELO: 60,
    VERDE: 40,
    AZUL: 20,
}
PESO_PRIORIDADE_LEGAL = {
    NENHUMA: 0,
    GESTANTE: 5,
    ...
}
```

Max wait targets (Manchester):
```python
TEMPO_MAXIMO_ESPERA_MINUTOS = {
    VERMELHO: 0,  # imediato
    LARANJA: 10,
    AMARELO: 60,
    VERDE: 120,
    AZUL: 240,
}
```

CNS validation:
```python
def validar_cns(cns: str) -> bool:
    cns_digits = re.sub(r"\D", "", cns)
    if len(cns_digits) != 15:
        return False
    if cns_digits[0] not in "123789":
        return False
    soma = sum(int(d) * w for d, w in zip(cns_digits, range(16, 1, -1)))  # weights 15..1
    return soma % 11 == 0
```

Wait, the CNS algorithm: weights are 15, 14, 13, ..., 2, 1 for the 15 digits. Sum must be divisible by 11. Let me verify: for CNS "116 8074 2698 0001" (a known valid test CNS):
Digits: 1,1,6,8,0,7,4,2,6,9,8,0,0,0,1
Weights: 15,14,13,12,11,10,9,8,7,6,5,4,3,2,1
Sum = 1*15 + 1*14 + 6*13 + 8*12 + 0*11 + 7*10 + 4*9 + 2*8 + 6*7 + 9*6 + 8*5 + 0*4 + 0*3 + 0*2 + 1*1
= 15 + 14 + 78 + 96 + 0 + 70 + 36 + 16 + 42 + 54 + 40 + 0 + 0 + 0 + 1
= 462
462 / 11 = 42. Yes, divisible. 

CPF validation:
```python
def validar_cpf(cpf: str) -> bool:
    digits = re.sub(r"\D", "", cpf)
    if len(digits) != 11 or digits == digits[0] * 11:
        return False
    # first check digit
    soma = sum(int(d) * w for d, w in zip(digits[:9], range(10, 1, -1)))
    dv1 = (soma * 10) % 11 % 10
    ...
```

Standard algorithm:
```python
def _dv_cpf(nove_digitos: str) -> int:
    soma = sum(int(d) * peso for d, peso in zip(nove_digitos, range(10, 1, -1)))
    resto = (soma * 10) % 11
    return 0 if resto == 10 else resto
```

Actually the standard: dv = 11 - (soma % 11); if dv >= 10, dv = 0. Equivalent formulations exist. Let me use:
```python
soma = sum(int(d) * peso for d, peso in zip(digits, pesos))
resto = soma % 11
dv = 0 if resto < 2 else 11 - resto
```

For CPF first DV: digits 1-9, weights 10..2. Second DV: digits 1-10, weights 11..2.

Now the queue entry:

```python
class EntradaFila(BaseModel):
    model_config = ConfigDict(frozen=True)  # maybe not frozen since we update status
    
    id_entrada: str = Field(default_factory=lambda: uuid.uuid4().hex)
    paciente: PacienteAcolhimento
    classificacao_risco: ClassificacaoRisco
    prioridade_legal: PrioridadeLegal = PrioridadeLegal.NENHUMA
    ciap2: str | None = None  # CIAP-2 code e.g. "A01"
    cid10: str | None = None
    queixa_principal: str
    registrado_em: datetime
    ...
```

Paciente:
```python
class PacienteAcolhimento(BaseModel):
    nome_social: str | None
    nome_civil: str
    cns: str  # validated
    cpf: str | None  # validated
    data_nascimento: date
    telefone: str
    ...
    
    @property
    def idade(self) -> int: ...
```

Heap entry:
```python
class _ItemHeap:
    __slots__ = ("chave_prioridade", "selo_desempate", "entrada")
    def __init__(...): ...
    def __lt__(self, other): ...
```

Priority score calculation:
```python
def _pontuacao(entrada, agora) -> float:
    base = PESO_RISCO[entrada.classificacao_risco]
    bonus_legal = PESO_LEGAL[entrada.prioridade_legal]
    espera_min = (agora - entrada.registrado_em).total_seconds() / 60
    envelhecimento = FATOR_ENVELHECIMENTO * espera_min  # e.g. 0.5 points per minute
    # cap aging so it doesn't override risk entirely? Or allow it (equity)?
    return base + bonus_legal + envelhecimento
```

Hmm, but with heapq, scores change over time. Options:
1. Lazy re-heapify: recompute scores periodically (background task) and heapify
2. Compute score at insertion and use aging only via periodic re-push

A common pattern: keep entries in heap with insertion-time score, and run a periodic "aging" task that rebuilds the heap with updated scores. Or simpler: when popping, we pop the highest score at that moment — but heapq doesn't support dynamic priorities.

Best approach: maintain the heap, and a periodic task (or on each operation) recalculates. Actually, a cleaner approach for correctness: since we need "peek next" and estimated times for everyone, we can:
- Store all entries in a dict by id
- Maintain heap of (score, tiebreak, id) 
- On each mutation (enqueue/dequeue/call), rebuild heap if aging threshold passed, or use a periodic asyncio task every N seconds

Let me implement with a periodic aging task using asyncio, plus lazy rebuild on access. Actually, simpler and robust: rebuild the heap on every state-changing operation (enqueue, dequeue, call). Queue sizes in UBS telehealth are small (hundreds), so O(n log n) rebuild is trivial. Also provide a background task for time-based updates (estimated time refresh).

Let me design the service API:

```python
class FilaTeleatendimentoService:
    def __init__(self, notificador: NotificadorWebSocket | None = None, ...): ...
    
    async def ingressar(self, payload: IngressoFilaPayload) -> EntradaFila
    async def chamar_proximo(self, profissional: Profissional) -> Chamada | None
    async def confirmar_atendimento(self, id_entrada: str) -> bool  # patient answered
    async def registrar_ausencia(self, id_entrada: str) -> bool  # no-show -> requeue with penalty or mark absent
    async def concluir(self, id_entrada: str, resumo_soap: ResumoSOAP | None) -> bool
    async def remover(self, id_entrada: str, motivo: str) -> bool
    async def snapshot(self) -> EstadoFila
    async def tempo_estimado(self, id_entrada: str) -> TempoEstimado
    def _reconstruir_heap(self) -> None
```

No-show handling: after N call attempts without confirmation, mark as absent (saída). Between attempts, re-queue with priority preserved but moved to front? In SUS practice, called patient who doesn't answer gets re-called up to 3 times, then goes to end of queue or is marked absent. Let me implement: `max_tentativas` (default 3), each call increments tentativas; if not confirmed and tentativas exhausted → status AUSENTE and removed. If requeued before exhaustion, keeps position priority with small penalty.

SOAP: The conclusion can include SOAP notes (Subjetivo, Objetivo, Avaliação, Plano) with CIAP-2/CID-10. Let me include a `RegistroSOAP` Pydantic model.

WebSocket notifier: define a protocol/interface:

```python
class NotificadorFila(Protocol):
    async def publicar(self, canal: str, evento: EventoFila) -> None: ...
```

And provide a concrete in-memory implementation that holds websocket connections per room (e.g., `fila:{id_unidade}`), designed to plug into FastAPI's WebSocket. I'll implement a `GerenciadorWebSocket` class that manages connections and serializes events, but keep it decoupled so tests can inject a fake.

Voice call: `ChamadaVoz` event with formatted text: "Paciente {nome}, compareça à sala virtual {sala}. Sua chamada é a número {n}." Include `repetir` count. The event includes `texto_voz` for TTS.

Estimated time:
- `tempo_medio_atendimento` per risk class (default values, EWMA updated on conclusion)
- For each waiting entry: effective position = number of entries with strictly higher current score (+ maybe same score earlier timestamp)
- `tempo_estimado_min = posicao_efetiva * tempo_medio / max(1, num_profissionais_ativos)`
- Also `previsao_chamada = agora + tempo_estimado`

Also SLA breach detection: if `espera_atual > tempo_maximo_espera` for the risk class → flag `violacao_sla=True`, and emit event. This is important for SUS monitoring.

Let me also add metrics: total enqueued, attended, average wait, etc.

Now, structure of the file. It's a service module, so it should be self-contained but importable. Let me write it:

```python
"""
Serviço C19 — Fila eletrônica reativa de acolhimento e chamada por voz.

Projeto MedIA — Telessaúde / APS (SUS).
...
"""
```

Sections:
1. Module docstring with context (SUS, Manchester, CIAP-2, SOAP)
2. Imports
3. Constants
4. Validators (CNS, CPF, CIAP-2 format)
5. Enums
6. Pydantic models
7. Heap item
8. Notifier protocol + WebSocket manager
9. Service
10. Factory/dependency

CIAP-2 format: letter + 2 digits (e.g., "A01", "R05", "K29"). Validate with regex `^[A-Z]\d{2}$`.

CID-10 format: letter + 2 digits, optional dot + 1+ digit (e.g., "J45", "E11.9"). Regex `^[A-Z]\d{2}(?:\.\d{1,2})?$`.

Let me now write the actual code carefully.

```python
from __future__ import annotations

import asyncio
import heapq
import itertools
import logging
import math
import re
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from enum import IntEnum, StrEnum
from typing import Any, Final, Protocol, Self, runtime_checkable

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
```

Constants:

```python
FUSO_PADRAO: