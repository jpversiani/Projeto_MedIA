The user wants me to create a FastAPI backend module for pharmaceutical dispensation and prescription consumption (baixa de receita) for the MedIA project, related to the Brazilian SUS (Unified Health System).

Let me think about what's needed:

1. **backend/app/api/v1/farmacia.py** - Main file with routes:
   - `POST /dispensacao/consultar` - validates QR Code/hash of the prescription
   - `POST /dispensacao/confirmar` - registers total or partial (fracionada) dispensation of medications in SUS

2. Requirements:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me design this properly:

### Domain Model (SQLAlchemy 2.0 style)

**Receita (Prescription)**:
- id (UUID)
- hash_qrcode (unique string) - the hash used in QR Code
- paciente_cns (CNS - Cartão Nacional de Saúde, 15 digits)
- paciente_cpf (CPF, 11 digits)
- paciente_nome
- profissional_cns (prescriber)
- profissional_cpf
- profissional_nome
- unidade_cnes (CNES - Código Nacional de Estabelecimento de Saúde)
- unidade_nome
- data_emissao
- data_validade
- cid10 (optional)
- ciap2 (optional)
- status: EMITIDA, PARCIALMENTE_DISPENSADA, DISPENSADA, CANCELADA, EXPIRADA, VENCIDA
- itens (relationship to ReceitaItem)

**ReceitaItem (Prescription Item)**:
- id
- receita_id
- medicamento_nome
- medicamento_codigo (could be CATMAT code)
- apresentacao / dosagem
- quantidade_prescrita
- quantidade_dispensada (accumulated)
- via_administracao
- posologia (instructions)
- status item: PENDENTE, PARCIAL, ATENDIDO

**Dispensacao (Dispensation record)**:
- id
- receita_id
- farmaceutico_cns / cpf / nome
- unidade_cnes (farmácia unit)
- data_dispensacao
- tipo: TOTAL, FRACIONADA
- observacoes
- itens (relationship to DispensacaoItem)

**DispensacaoItem**:
- id
- dispensacao_id
- receita_item_id
- quantidade_dispensada

### Pydantic v2 Schemas

- `ReceitaConsultaRequest`: hash_qrcode (or qr_code payload)
- `ReceitaConsultaResponse`: full prescription data with items, remaining quantities, status, validity
- `DispensacaoConfirmarRequest`: hash_qrcode, itens (list with receita_item_id + quantidade), farmaceutico data, unidade data, observacoes
- `DispensacaoConfirmarResponse`: dispensation record

### Validation logic

For `/dispensacao/consultar`:
- Hash must exist → 404 if not
- Prescription must not be expired → status EXPIRADA
- Must not be fully dispensed (DISPENSADA) → error or show status
- Must not be CANCELADA
- Return items with quantities remaining

For `/dispensacao/confirmar`:
- Validate hash exists
- Validate not expired, not cancelled, not fully dispensed
- Validate each item: quantity > 0, quantity <= remaining
- Validate CNS/CPF of pharmacist (checksum validation)
- Total dispensation: all items fully dispensed → status DISPENSADA
- Partial: some items partially → status PARCIALMENTE_DISPENSADA
- Use transaction, row locking (SELECT FOR UPDATE) to avoid race conditions

### CNS/CPF validation

CNS validation algorithm:
- CNS must have 15 digits
- Starting with 1, 2, 7, 8, 9 (or new formats 798, 898, 998... actually 7/8/9 starting are provisional cards)
- Algorithm: sum of digits multiplied by weights 15 down to 2, mod 11, check digit = 11 - remainder; if remainder == 1, special case (right operand 0 or 1, sum with weights 17 down to 2... let me recall)

CNS validation (DAC):
1. CNS has 15 digits
2. First digits: 1, 2, or 7, 8, 9 (provisional)
3. For CNS starting with 1 or 2: standard mod 11 with weights 15..2. If rest == 0 → DV = 0; else DV = 11 - rest. If rest == 1, DV must be 0 or 1 (PIS/PASEP format).
4. For CNS starting with 7, 8, 9: weights 15..2, sum mod 11, DV = 11 - rest. If DV == 10 or 11, then DV = 0? Actually for 7/8/9: sum = Σ digit × weight (15 to 2), rest = sum % 11, DV = 11 - rest; if DV in (10, 11) → DV = 0.

Let me write the standard algorithm:

```python
def validar_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    # Check for repeated digits
    if len(set(cns)) == 1:
        return False
    soma = sum(int(d) * w for d, w in zip(cns[:12], range(15, 4, -1)))
    # Actually weights 15,14,...,5 for first 12 digits? Let me think.
```

Standard CNS algorithm:
- Take first 12 digits, multiply by weights 15, 14, 13, ..., 5? No wait.

Actually the standard: multiply the first 12 digits by weights 15 down to 4? Let me recall properly.

The CNS check digit algorithm (from DATASUS):
1. Sum = Σ (digit_i × weight_i) where weights are 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2 for the first 14 digits, and the 15th is the DV.
2. rest = Sum % 11
3. If rest == 0 → DV = 0
4. Else DV = 11 - rest
5. If DV == 11 → DV = 0? Hmm.

Actually the official algorithm:

```
soma = 0
peso = 15
for i in 0..14:
    soma += digito[i] * peso
    peso -= 1
resto = soma % 11
if resto != 0:
    dv = 11 - resto
else:
    dv = resto
```

Wait, that uses all 15 digits including DV. Let me look at the known implementation:

```python
def valida_cns(cns):
    cns = cns.strip().replace('.', '').replace(' ', '')
    if len(cns) != 15:
        return False
    if cns[0] not in ['1', '2', '7', '8', '9']:
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

Yes! That's the simple version: sum of digit × weight (15 down to 1) must be divisible by 11. That's the well-known CNS validation. Weights: 15, 14, 13, ..., 1 for the 15 digits. soma % 11 == 0.

For CNS starting with 7, 8, 9 (provisional), the same algorithm applies.

CPF validation:
- 11 digits, not all same
- DV1: sum of first 9 digits × weights 10..2, rest = (sum * 10) % 11, if rest == 10 → 0
- DV2: sum of first 10 digits × weights 11..2, rest = (sum * 10) % 11, if rest == 10 → 0

### Structure

Since the task says "crie backend/app/api/v1/farmacia.py", the main deliverable is that file. But for it to be complete and executable, I should provide supporting files:

- `backend/app/schemas/farmacia.py` (Pydantic v2 schemas) — or keep schemas in the same file? Better to separate but the task focuses on the API file. I'll provide:
  - `backend/app/schemas/farmacia.py` — Pydantic v2 schemas
  - `backend/app/models/farmacia.py` — SQLAlchemy 2.0 models (or maybe models already exist; I'll create them)
  - `backend/app/core/validadores.py` — CNS/CPF validators
  - `backend/app/api/v1/farmacia.py` — the router
  - `backend/app/api/dependencies.py` — get_db dependency
  - `backend/app/core/exceptions.py` — custom exceptions + handlers
  - `backend/tests/test_farmacia.py` — pytest tests
  - Maybe `backend/app/db/base.py` for Base
  - `backend/app/main.py` to wire it up

I should be careful not to over-engineer but the instructions say "Forneça o código completo e executável" (provide complete executable code). So I'll provide a coherent set of files.

Let me design the models:

```python
# backend/app/models/farmacia.py
import enum
import uuid
from datetime import date, datetime
from sqlalchemy import (
    String, ForeignKey, Date, DateTime, Enum, Integer, Text, UniqueConstraint, Index, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

class Base(DeclarativeBase): ...

class StatusReceita(str, enum.Enum):
    EMITIDA = "EMITIDA"
    PARCIALMENTE_DISPENSADA = "PARCIALMENTE_DISPENSADA"
    DISPENSADA = "DISPENSADA"
    CANCELADA = "CANCELADA"
    EXPIRADA = "EXPIRADA"

class StatusItemReceita(str, enum.Enum):
    PENDENTE = "PENDENTE"
    PARCIALMENTE_DISPENSADO = "PARCIALMENTE_DISPENSADO"
    DISPENSADO = "DISPENSADO"

class TipoDispensacao(str, enum.Enum):
    TOTAL = "TOTAL"
    FRACIONADA = "FRACIONADA"

class Receita(Base):
    __tablename__ = "receitas"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    hash_qrcode: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    paciente_nome: Mapped[str] = mapped_column(String(200))
    paciente_cns: Mapped[str] = mapped_column(String(15))
    paciente_cpf: Mapped[str | None] = mapped_column(String(11))
    prescritor_nome: Mapped[str] = mapped_column(String(200))
    prescritor_cns: Mapped[str] = mapped_column(String(15))
    prescritor_cpf: Mapped[str | None]
    unidade_cnes: Mapped[str] = mapped_column(String(7))
    unidade_nome: Mapped[str]
    data_emissao: Mapped[date]
    data_validade: Mapped[date]
    cid10: Mapped[str | None] = mapped_column(String(6))
    ciap2: Mapped[str | None] = mapped_column(String(5))
    status: Mapped[StatusReceita] = mapped_column(Enum(StatusReceita, name="status_receita"), default=StatusReceita.EMITIDA)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    itens: Mapped[list["ReceitaItem"]] = relationship(back_populates="receita", cascade="all, delete-orphan", lazy="selectin")
    dispensacoes: Mapped[list["Dispensacao"]] = relationship(back_populates="receita")
```

ReceitaItem:
```python
class ReceitaItem(Base):
    __tablename__ = "receita_itens"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    receita_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("receitas.id", ondelete="CASCADE"), index=True)
    medicamento_nome: Mapped[str] = mapped_column(String(200))
    medicamento_catmat: Mapped[str | None] = mapped_column(String(12))  # código CATMAT
    apresentacao: Mapped[str | None] = mapped_column(String(200))
    dosagem: Mapped[str | None] = mapped_column(String(100))
    via_administracao: Mapped[str | None] = mapped_column(String(50))
    posologia: Mapped[str | None] = mapped_column(Text)
    quantidade_prescrita: Mapped[int] = mapped_column(Integer)
    quantidade_dispensada: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[StatusItemReceita] = ...
    receita: Mapped["Receita"] = relationship(back_populates="itens")
    dispensacao_itens: Mapped[list["DispensacaoItem"]] = relationship(back_populates="receita_item")
```

Dispensacao:
```python
class Dispensacao(Base):
    __tablename__ = "dispensacoes"
    id: Mapped[uuid.UUID] = ...
    receita_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("receitas.id"), index=True)
    tipo: Mapped[TipoDispensacao]
    farmaceutico_nome: Mapped[str]
    farmaceutico_cns: Mapped[str]
    farmaceutico_cpf: Mapped[str | None]
    unidade_cnes: Mapped[str]
    unidade_nome: Mapped[str | None]
    observacoes: Mapped[str | None] = mapped_column(Text)
    data_dispensacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    receita: Mapped["Receita"] = relationship(back_populates="dispensacoes")
    itens: Mapped[list["DispensacaoItem"]] = relationship(back_populates="dispensacao", cascade="all, delete-orphan", lazy="selectin")

class DispensacaoItem(Base):
    __tablename__ = "dispensacao_itens"
    id: Mapped[uuid.UUID]
    dispensacao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dispensacoes.id", ondelete="CASCADE"))
    receita_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("receita_itens.id"), index=True)
    quantidade_dispensada: Mapped[int]
    dispensacao: relationship
    receita_item: relationship
```

### Schemas (Pydantic v2)

```python
# backend/app/schemas/farmacia.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import date, datetime
import uuid

class ReceitaItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    medicamento_nome: str
    medicamento_catmat: str | None
    apresentacao: str | None
    dosagem: str | None
    via_administracao: str | None
    posologia: str | None
    quantidade_prescrita: int
    quantidade_dispensada: int
    quantidade_pendente: int
    status: StatusItemReceita

class ReceitaConsultaRequest(BaseModel):
    hash_qrcode: str = Field(..., min_length=16, max_length=128)
    # or qr_code payload

class ReceitaConsultaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    receita_id: uuid.UUID
    hash_qrcode: str
    paciente_nome: str
    paciente_cns: str (masked?)
    ...
    itens: list[ReceitaItemOut]
    status: StatusReceita
    dispensavel: bool
    motivo_indisponibilidade: str | None

class ItemDispensacaoRequest(BaseModel):
    receita_item_id: uuid.UUID
    quantidade: int = Field(gt=0)

class DispensacaoConfirmarRequest(BaseModel):
    hash_qrcode: str
    itens: list[ItemDispensacaoRequest] = Field(min_length=1)
    farmaceutico: ProfissionalFarmacia (nome, cns, cpf)
    unidade_cnes: str
    observacoes: str | None

class DispensacaoConfirmarResponse(BaseModel):
    dispensacao_id, receita_id, tipo, data, itens dispensados, status receita, itens pendentes...
```

For LGPD compliance, maybe mask CPF/CNS in responses: e.g., CPF "***.***.789-**". I'll include a masking helper. Actually for the pharmacy to confirm patient identity, they need to see some data. I'll return full CNS but mask CPF partially? Hmm. In a real SUS pharmacy flow, the pharmacist validates the patient's identity. Let me return the CNS masked partially and name. Actually, keep it simple: return name, CNS masked (e.g., first 3 and last 4?), and let the pharmacist confirm. I'll add a `mascarar_cns`/`mascarar_cpf` helper for LGPD. But the pharmacist needs to check the patient's CNS against their card... I'll provide both: full CNS is needed for dispensation validation in SUS. Hmm, LGPD-wise, the pharmacy operator is authorized to process this data. I'll return CNS unmasked (needed to conferir) but mask CPF. Or provide a query param? Keep it simple: mask CPF, show CNS. Actually let me just mask both partially and note it. Hmm.

Let me think about what's most defensible: The endpoint is used by pharmacy staff after the patient presents the QR code. The staff needs to verify patient identity (name + CNS/CPF + photo ID). Returning the full CNS is standard in e-SUS systems. I'll return CNS full, CPF masked (***.***.***-** last 2 digits visible? no...). I'll do: CPF masked except last 2? Common masking: `***.***.789-**`. I'll implement `mascarar_cpf` showing last 3 digits: `***.***.***-89`?