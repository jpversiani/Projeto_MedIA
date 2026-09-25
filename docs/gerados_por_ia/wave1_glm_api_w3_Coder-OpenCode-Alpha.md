The user wants me to create a FastAPI telemedicine API file for the MedIA project (Primary Health Care and Telemedicine for SUS - Brazilian Unified Health System). Let me analyze the requirements:

1. **POST /agendamentos**: receives TeleconsultaCreate, generates room code, persists Teleconsulta
2. **GET /salas/{codigo_sala}**: returns virtual room data and consultation status
3. **POST /iniciar-chamada**: changes status to EM_ANDAMENTO
4. **POST /finalizar-chamada**: receives SOAP data and finalizes

Requirements:
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Use `Depends(get_db)` from `app.core.database`
- Import models from `app.models.telemedicina` and schemas from `app.schemas.telemedicina`
- Complete, executable code
- Test coverage with pytest

Since the task says to create the file `backend/app/api/v1/telemedicina.py`, but for it to be complete and executable, I should probably also provide the supporting files (models, schemas, database) since they're referenced. The instruction says "Forneça o código completo e executável" (provide complete and executable code). Let me think about what's the scope here.

The main task is to create `backend/app/api/v1/telemedicina.py`. But the imports reference:
- `app.core.database` with `get_db`
- `app.models.telemedicina` with Teleconsulta model
- `app.schemas.telemedicina` with TeleconsultaCreate and related schemas

To make it truly executable and testable, I should provide:
1. `backend/app/api/v1/telemedicina.py` (main deliverable)
2. `backend/app/models/telemedicina.py` (SQLAlchemy 2.0 model)
3. `backend/app/schemas/telemedicina.py` (Pydantic v2 schemas)
4. `backend/app/core/database.py` (get_db dependency)
5. Tests: `backend/tests/test_telemedicina_api.py` (pytest)

The user explicitly asked for the main file, but the system prompt says "Forneça o código completo e executável. Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo". This suggests multiple files are expected. The guidelines mention "Manter conformidade total e cobertura de testes automatizados com pytest" — so tests are expected too.

Let me design the solution:

### Models (SQLAlchemy 2.0)

```python
# backend/app/models/telemedicina.py
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StatusTeleconsulta(str, enum.Enum):
    AGENDADA = "AGENDADA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"
    NAO_COMPARECEU = "NAO_COMPARECEU"


class Teleconsulta(Base):
    __tablename__ = "teleconsultas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_sala: Mapped[str] = mapped_column(String(12), unique=True, index=True, nullable=False)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id"), nullable=False)
    profissional_id: Mapped[int] = mapped_column(ForeignKey("profissionais.id"), nullable=False)
    ...
```

Hmm, but if I reference `pacientes.id` and `profissionais.id`, I'd need those tables too. To keep it self-contained and executable, maybe I should simplify: store CNS/CPF as strings directly, or use simple integer IDs without FK constraints to other tables (or define minimal related tables). 

Actually, for SUS compliance, identification by CNS/CPF is required. Let me design the model to store:
- `paciente_cns` (or paciente_id + cns)
- `profissional_cns` / profissional info

To keep it executable without needing other modules, I'll design Teleconsulta as a self-contained table with:
- id
- codigo_sala (unique)
- paciente_nome, paciente_cns, paciente_cpf
- profissional_nome, profissional_cns (or profissional_id)
- data_agendamento (scheduled datetime)
- status (enum)
- motivo / queixa principal
- CIAP-2 code (codigo_ciap2)
- CID-10 (cid10)
- SOAP fields: subjetivo, objetivo, avaliacao (avaliação), plano
- timestamps: criado_em, atualizado_em, iniciada_em, finalizada_em
- duracao_minutos maybe

This is self-contained and SUS-compliant (CNS/CPF, CIAP-2, CID-10, SOAP).

### Schemas (Pydantic v2)

```python
# backend/app/schemas/telemedicina.py
from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
```

Validators:
- CNS validation (SUS CNS has 15 digits, with check digit algorithm)
- CPF validation (11 digits with check digits)
- CIAP-2 format: letter + 2 digits (e.g., "A01", "K29", "L03")
- CID-10 format: letter + 2 digits + optional .x (e.g., "I10", "J18.9")

CNS validation algorithm:
CNS is 15 digits. First digit must be 1, 2, 7, 8, or 9. Check digit via sum with weights: for the first 11 digits, weights 5,4,3,2,1,9,8,7,6,5,4... Actually the standard algorithm:

The CNS validation: 
- 15 digits
- If starts with 1 or 2 (definitive cards), the sum with weights [15,14,13,12,11,10,9,8,7,6,5,4,3,2,1]... Let me recall the correct algorithm.

Standard CNS validation (from SUS):
```
soma = 0
for i, digito in enumerate(cns):
    soma += int(digito) * (15 - i)
resto = soma % 11
dv = 11 - resto if resto != 0 else 0
```
Hmm, that's not quite it either. Let me recall properly.

The official algorithm for CNS (Cartão Nacional de Saúde):
1. CNS must have 15 digits.
2. For definitive CNS (starting with 1, 2): 
   - Multiply each of the first 15 digits by weights: 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1
   - Sum all products
   - The result must be divisible by 11 (soma % 11 == 0)

Wait, that's for the full 15-digit check. Actually the common implementation:

```python
def valida_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in '123789':
        return False
    soma = sum(int(d) * w for d, w in zip(cns, [15,14,13,12,11,10,9,8,7,6,5,4,3,2,1]))
    return soma % 11 == 0
```

Yes, this is the standard algorithm — the sum of digits multiplied by weights 15 down to 1 must be divisible by 11. This works for provisional cards (7,8,9) too.

CPF validation:
```python
def valida_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    # first check digit
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11 % 10
    # second check digit
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11 % 10
    return cpf[9] == str(d1) and cpf[10] == str(d2)
```

CIAP-2: format is one letter (chapter) + two digits, e.g., A01, B05, K29, L03, T90, etc. Valid chapters: A-Z (all letters used except maybe some). CIAP-2 chapters: A (General), B (Blood), D (Digestive), F (Eye), H (Ear), K (Circulatory), L (Musculoskeletal), N (Neurological), R (Respiratory), S (Skin), T (Endocrine), U (Urological), W (Pregnancy), X (Female genital), Y (Male genital), Z (Social). Regex: `^[A-Z]\d{2}$`.

CID-10: format letter + 2 digits + optional dot + 1-2 alphanumerics. Regex: `^[A-Z]\d{2}(?:\.\d{1,2})?$`.

### Room code generation

Generate a unique room code, e.g., 8-character alphanumeric (uppercase, excluding ambiguous chars like 0/O, 1/I/L). Use `secrets` module for cryptographic randomness:

```python
import secrets
import string

ALFABETO_SALA = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sem O, I, L, 0, 1

def gerar_codigo_sala(tamanho: int = 8) -> str:
    return "".join(secrets.choice(ALFABETO_SALA) for _ in range(tamanho))
```

With retry on unique constraint collision (loop with a few attempts, checking DB for existence).

### API Router

```python
# backend/app/api/v1/telemedicina.py
from __future__ import annotations

import logging
import secrets
import string
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
```

Wait — should the DB be async or sync? The task says use `Depends(get_db)` from `app.core.database`. I need to decide. SQLAlchemy 2.0 supports both. For a modern FastAPI stack, async with `AsyncSession` is common. But sync is simpler and more testable. Given "Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0", I'll go with async SQLAlchemy 2.0 (`AsyncSession`) since it's the modern pattern, and provide `get_db` as an async generator yielding `AsyncSession`.

Hmm, but tests with pytest then need pytest-asyncio and httpx AsyncClient. That's fine — I'll include tests using `httpx.AsyncClient` with `ASGITransport` and `pytest-asyncio`, with an in-memory SQLite (aiosqlite) database.

Actually, let me reconsider: sync might be simpler and fewer dependencies. But async is the more "modern" pattern for FastAPI + SQLAlchemy 2.0. The guidelines say "SQLAlchemy 2.0" without specifying. I'll go async — it's the standard for telemedicine/video call APIs which are I/O bound. I'll document dependencies.

Let me structure:

**backend/app/core/database.py**:
```python
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

Hmm, committing in get_db is one pattern; committing in the route is another. For clarity and explicitness in routes, I'll commit in the routes (explicit `await db.commit()`), and get_db just yields the session and closes it. Actually, a common pattern is commit-on-success in the dependency. Let me keep the dependency simple (just yield session) and do explicit commits in routes — clearer for tests and for the reviewer.

**backend/app/core/config.py** (settings):
```python
from functools import lru_cache
from pydantic_settings import BaseSettings
```

Hmm, that adds another dependency (pydantic-settings). To keep it minimal, I could just define DATABASE_URL directly in database.py with a default `sqlite+aiosqlite:///./media_telemedicina.db` and allow env override via `os.getenv`. That avoids pydantic-settings dependency. Let me do that — simpler and executable.

Actually, for the tests, I'll override `get_db` dependency with a test database, so the default URL doesn't matter much. But the app must be importable, so database.py must create an engine at import time. With SQLite aiosqlite, that's fine.

**backend/app/models/telemedicina.py**:

```python
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StatusTeleconsulta(str, enum.Enum):
    AGENDADA = "AGENDADA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"
    NAO_COMPARECEU = "NAO_COMPARECEU"


class Teleconsulta(Base):
    __tablename__ = "teleconsultas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_sala: Mapped[str] = mapped_column(String(12), unique=True, index=True, nullable=False)

    # Identificação do paciente (padrão SUS: CNS/CPF)
    paciente_nome: Mapped[str] = mapped_column(String(200), nullable=False)
    paciente_cns: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    paciente_cpf: Mapped[Optional[str]] = mapped_column(String(11), nullable=True, index=True)

    # Profissional de saúde
    profissional_nome: Mapped[str] = mapped_column(String(200), nullable=False)
    profissional_cns: Mapped[str] = mapped_column(String(15), nullable=False)
    profissional_cpf: Mapped[Optional[str]] = ...
    unidade_saude (CNES?) — maybe cnes: Mapped[Optional[str]] = mapped_column(String(7))

    data_agendada: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[StatusTeleconsulta] = mapped_column(
        Enum(StatusTeleconsulta, name="status_teleconsulta", native_enum=False),
        default=StatusTeleconsulta.AGENDADA, nullable=False
    )

    # Motivo do atendimento
    motivo: Mapped[Optional[str]] = mapped_column(String(500))
    codigo_ciap2: Mapped[Optional[str]] = mapped_column(String(3))
    cid10: Mapped[Optional[str]] = mapped_column(String(5))

    # Registro SOAP
    soap_subjetivo: Mapped[Optional[str]] = mapped_column(Text)
    soap_objetivo: Mapped[Optional[str]] = mapped_column(Text)
    soap_avaliacao: Mapped[Optional[str]] = mapped_column(Text)
    soap_plano: Mapped[Optional[str]] = mapped_column(Text)

    iniciada_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finalizada_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

CNES is 7 digits — the code of the health unit in SUS. Nice touch for SUS compliance.

**backend/app/schemas/telemedicina.py**:

Pydantic v2 schemas:

```python
class StatusTeleconsultaSchema(str, Enum):  # or reuse model enum
    ...
```

Actually I can reuse the model's enum in schemas (Pydantic handles str enums fine). To avoid circular imports: schemas import from models? models import from database. schemas importing models enum is fine (no cycle). Or define the enum in schemas and have models import from schemas — that creates models→schemas dependency. Better: define enum in models, schemas import it. Or define in a shared module. I'll define `StatusTeleconsulta` in the models module and import it in schemas. Hmm, actually cleaner: define it in schemas and models import from schemas? No — standard is models own the DB enum. Let me just have schemas import from models: `from app.models.telemedicina import StatusTeleconsulta`. That's fine, no circularity (models doesn't import schemas).

Wait, but there's a subtlety: `app.api.v1.telemedicina` imports both models and schemas; models imports `app.core.database`; schemas imports models. No cycles. Good.

Schemas:

```python
class TeleconsultaCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    paciente_nome: str = Field(min_length=3, max_length=200)
    paciente_cns: str = Field(min_length=15, max_length=15)
    paciente_cpf: str | None = None
    profissional_nome: str = Field(min_length=3, max_length=200)
    profissional_cns: str
    profissional_cpf: str | None = None
    cnes_unidade: str | None = Field(default=None, max_length=7)
    data_agendada: datetime
    motivo: str | None = Field(default=None, max_length=500)
    codigo_ciap2: str |