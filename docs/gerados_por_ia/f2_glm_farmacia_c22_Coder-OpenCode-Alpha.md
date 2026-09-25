The user wants me to create a FastAPI backend module for pharmaceutical dispensing and prescription fulfillment (baixa de receita) for the MedIA project, which is a Brazilian SUS (Sistema Único de Saúde) healthcare system.

Requirements:
- File: `backend/app/api/v1/farmacia.py`
- Routes:
  - `POST /dispensacao/consultar` - validates QR Code/hash of prescription
  - `POST /dispensacao/confirmar` - registers full or fractional dispensing of medications in SUS
- Pydantic v2 and SQLAlchemy
- Python 3.12, strict typing
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me design this properly:

1. **Schemas (Pydantic v2)**: I'll need to define request/response models. Since the task says to create `farmacia.py`, but for a complete executable solution, I should probably include the schemas either in the same file or in a schemas module. The instruction says "Forneça o código completo e executável" (provide complete executable code). Let me create:
   - `backend/app/api/v1/farmacia.py` - main API routes
   - `backend/app/schemas/farmacia.py` - Pydantic v2 schemas
   - `backend/app/models/farmacia.py` - SQLAlchemy models
   - `backend/app/db/session.py` - database session (maybe assume exists, but for completeness)
   - `backend/tests/test_farmacia.py` - pytest tests

Actually, the task says "crie backend/app/api/v1/farmacia.py" - so the main deliverable is that file. But to make it executable, I need supporting files. Let me provide a complete, well-organized solution with all necessary files, clearly marking each.

Let me think about the domain:

**Dispensação Farmacêutica no SUS:**
- A prescription (receita) is issued by a professional, has a QR Code/hash for validation
- Patient identified by CNS (Cartão Nacional de Saúde) or CPF
- Medications have: name, presentation, dosage, quantity prescribed, quantity dispensed
- Dispensing can be:
  - Total (baixa total): all medications dispensed in full
  - Fracionada (partial/fractional): some medications dispensed partially or some items not dispensed
- Validation: prescription must exist, not expired, not already fully dispensed, patient matches
- CID-10 for diagnosis, CIAP-2 for primary care reason for encounter
- Audit trail: who dispensed (farmacêutico), when, where (UBS/unidade)

**Models:**

1. `Receita` (Prescription):
   - id (UUID)
   - codigo_hash (unique hash for QR Code validation)
   - paciente_id / paciente_cns / paciente_cpf
   - profissional_id (prescriber)
   - unidade_id (UBS)
   - data_emissao
   - data_validade
   - cid10 (optional)
   - ciap2 (optional)
   - status: EMITIDA, PARCIALMENTE_DISPENSADA, DISPENSADA, CANCELADA, EXPIRADA, VENCIDA
   - items: relationship to ReceitaItem

2. `ReceitaItem`:
   - id
   - receita_id
   - medicamento_id / medicamento_nome
   - apresentacao
   - dosagem
   - quantidade_prescrita
   - quantidade_dispensada (accumulated)
   - via_administracao
   - posologia

3. `Dispensacao`:
   - id
   - receita_id
   - farmaceutico_id
   - farmaceutico_cns? / nome
   - unidade_id
   - data_dispensacao
   - tipo: TOTAL, PARCIAL
   - observacoes
   - items: relationship

4. `DispensacaoItem`:
   - id
   - dispensacao_id
   - receita_item_id
   - quantidade_dispensada
   - lote
   - validade_lote

**Schemas (Pydantic v2):**

- `DispensacaoConsultarRequest`: `codigo_receita: str` (hash/QR content)
- `ReceitaConsultaResponse`: prescription details, items with remaining quantities, status, validity
- `DispensacaoConfirmarRequest`: codigo_receita, items (list of {receita_item_id, quantidade}), farmaceutico info, tipo (TOTAL/PARCIAL), observacoes
- `DispensacaoResponse`: confirmation with dispensation details

**Business rules:**
- Validate hash exists → 404 if not found
- Validate prescription not expired → 422 or 409
- Validate not cancelled
- Validate not already fully dispensed
- For confirmation:
  - Quantities must be > 0
  - Quantities cannot exceed remaining (prescribed - already dispensed)
  - If all items fully dispensed → status DISPENSADA (baixa total)
  - If partial → status PARCIALMENTE_DISPENSADA
  - tipo TOTAL: all items dispensed in full remaining quantities
  - tipo PARCIAL: at least one item partially dispensed
- CNS validation: CNS must be valid (15 digits, validation algorithm)
- CPF validation: check digit algorithm

**CNS validation algorithm:**
CNS can start with 1, 2, 7, 8, 9. The algorithm for the first type (1, 2 or 7, 8, 9):
- For CNS starting with 1 or 2: 15 digits, use "peso" 15 down to 1... Actually the standard algorithm:
  - Multiply each of the first 14 digits by weights 15, 14, 13, ..., 2, sum, compute: 11 - (soma % 11), if result != 11 and != 10, that's the check digit... Actually let me recall properly.

The CNS validation:
- Must have 15 digits
- First digit must be 1, 2, 7, 8, or 9
- For CNS starting with 1 or 2 (definitive):
  - Digits d1..d15
  - soma = d1*15 + d2*14 + ... + d14*2 + d15*1
  - rest = soma % 11
  - dv = 11 - rest
  - if dv == 11: dv = 0... hmm, actually the rule: if dv is 10 or 11, the CNS is invalid for this calculation? Let me recall.

Actually the official algorithm (from Cartão Nacional de Saúde):
```
Para CNS começando com 1 ou 2:
1. Multiplicar cada dígito (dos 15) pelos pesos 15, 14, 13, ..., 1 (da esquerda para direita)
2. Somar todos os resultados
3. resto = soma % 11
4. Se resto == 0, o CNS é válido
```
Wait, that's one version. Let me recall the correct one:

The correct algorithm for CNS (definitive, starting with 1 or 2):
- Take the 15 digits
- Compute sum of digit[i] * (15 - i) for i from 0 to 14, i.e., weights 15 down to 1
- If sum % 11 == 0, valid

For provisional CNS (starting with 7, 8, 9):
- Different: sum of digit[i] * (15 - i), then dv = 11 - (sum % 11); if dv >= 10, dv = 0 - ... hmm.

Actually the provisional algorithm:
```
soma = d1*15 + d2*14 + ... + d15*1
dv = 11 - (soma % 11)
if dv == 11: dv = 0
if dv == 10: dv = 0, and soma += 2, then recompute... 
```
Hmm, this is getting complicated. Let me look at the widely used implementation:

```python
def valida_cns(cns: str) -> bool:
    cns = ''.join(filter(str.isdigit, cns))
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    soma = sum(int(d) * (15 - i) for i, d in enumerate(cns))
    return soma % 11 == 0
```

Yes! This is the standard implementation that works for both definitive (1,2) and provisional (7,8,9) CNS. The check is: sum of digit * weight (15 down to 1) must be divisible by 11. This is the well-known algorithm. Let me verify with a known valid CNS: 116 8074 6260 0100? Hmm, I don't have one memorized. Let me construct one:

Take 14 digits: 11680746260010, compute sum with weights 15..2:
d1=1*15=15
d2=1*14=14
d3=6*13=78
d4=8*12=96
d5=0*11=0
d6=7*10=70
d7=4*9=36
d8=6*8=48
d9=2*7=14
d10=6*6=36
d11=0*5=0
d12=0*4=0
d13=1*3=3
d14=0*2=0
sum = 15+14+78+96+0+70+36+48+14+36+0+0+3+0 = 410
410 % 11 = 410 - 37*11 = 410 - 407 = 3. Need dv such that (410 + dv*1) % 11 == 0 → dv = 11 - 3 = 8. So CNS = 116807462600108 would be valid. 

For the test, I can generate a valid CNS programmatically in the test helper.

**CPF validation:**
Standard check digit algorithm.

**QR Code/hash:**
The prescription has a `codigo_hash` (e.g., SHA-256 based). The QR Code contains this hash. The consultar endpoint receives the hash (or full QR content), validates format, looks up the prescription.

Let me design the hash format: e.g., `MED-<uuid>` or a base64/hex string. I'll accept a flexible format: the QR content might be like `MEDIARECEITA|<hash>` or just the hash. I'll normalize by extracting the hash.

**Status flow:**
- EMITIDA → PARCIALMENTE_DISPENSADA → DISPENSADA
- CANCELADA (terminal)
- EXPIRADA (computed or set by validation)

**Endpoints:**

1. `POST /dispensacao/consultar`
   - Request: `{"codigo_receita": "<hash or QR content>"}`
   - Validates hash format
   - Looks up prescription by hash
   - Checks: exists (404), not cancelled (409), not expired (409), not fully dispensed (409)
   - Returns: prescription data (patient CNS masked?, prescriber, unit, dates, CID-10, CIAP-2, items with prescribed/dispensed/remaining quantities, status, tipo_dispensacao_permitida)

2. `POST /dispensacao/confirmar`
   - Request: codigo_receita, items [{receita_item_id, quantidade_dispensada, lote?, validade_lote?}], farmaceutico {nome, cns, registro_conselho?}, unidade_id, tipo (TOTAL/PARCIAL), observacoes?
   - Validates same as consultar
   - Validates each item: belongs to prescription, quantity > 0, quantity <= remaining
   - If tipo == TOTAL: all items must be dispensed to full remaining quantity (or the request auto-fills? Better: require explicit quantities; validate that all items reach full)
   - Updates receita_item.quantidade_dispensada
   - Creates Dispensacao + DispensacaoItem records
   - Updates receita.status
   - Returns dispensation receipt (comprovante)

**Architecture decisions:**
- Use SQLAlchemy 2.0 style with `Mapped`, `mapped_column`
- Use Pydantic v2 with `field_validator`, `model_validator`, `ConfigDict`
- Dependency injection for DB session via `Annotated[Session, Depends(get_db)]`
- Service layer inside the router module or separate? To keep it focused, I'll put business logic in a service class within the module or a `services/farmacia.py`. The task says create `backend/app/api/v1/farmacia.py` — I'll put the router there, with schemas and models in their own modules, and a service layer. Actually, to keep the deliverable focused but complete, I'll structure:

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py (minimal, to run)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py (Base declarative)
│   │   └── session.py (engine, get_db)
│   ├── models/
│   │   ├── __init__.py
│   │   └── farmacia.py (SQLAlchemy models)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── farmacia.py (Pydantic v2 schemas)
│   ├── services/
│   │   ├── __init__.py
│   │   └── farmacia.py (business logic)
│   └── api/
│       ├── __init__.py
│       └── v1/
│           ├── __init__.py
│           └── farmacia.py (router)
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_farmacia.py
```

That's a lot of files but makes it executable. The instruction says "Forneça o código completo e executável" — so yes, provide all files needed.

Hmm, but maybe I should be more economical. The core deliverable is `backend/app/api/v1/farmacia.py`. Supporting files: models, schemas, service, db session, tests. I think providing all is right given "código completo e executável" and "cobertura de testes automatizados com pytest".

Let me write the code.

**Enums:**

```python
class StatusReceita(str, Enum):
    EMITIDA = "EMITIDA"
    PARCIALMENTE_DISPENSADA = "PARCIALMENTE_DISPENSADA"
    DISPENSADA = "DISPENSADA"
    CANCELADA = "CANCELADA"
    EXPIRADA = "EXPIRADA"

class TipoDispensacao(str, Enum):
    TOTAL = "TOTAL"
    PARCIAL = "PARCIAL"
```

**Models (SQLAlchemy 2.0):**

```python
class Receita(Base):
    __tablename__ = "receitas"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    paciente_nome: Mapped[str] = mapped_column(String(200))
    paciente_cns: Mapped[str] = mapped_column(String(15), index=True)
    paciente_cpf: Mapped[str | None] = mapped_column(String(11), nullable=True)
    profissional_prescritor: Mapped[str]
    profissional_cns: Mapped[str]
    unidade_id: Mapped[uuid.UUID]
    unidade_nome: Mapped[str]
    data_emissao: Mapped[datetime]
    data_validade: Mapped[datetime]
    cid10: Mapped[str | None]
    ciap2: Mapped[str | None]
    status: Mapped[StatusReceita] = mapped_column(SAEnum(StatusReceita), default=...)
    itens: relationship(...)

class ReceitaItem(Base):
    __tablename__ = "receita_itens"
    id, receita_id (FK), medicamento_id, medicamento_nome, apresentacao, dosagem, via_administracao, posologia, quantidade_prescrita (int), quantidade_dispensada (int, default 0)

class Dispensacao(Base):
    __tablename__ = "dispensacoes"
    id, receita_id (FK), tipo, farmaceutico_nome, farmaceutico_cns, farmaceutico_registro, unidade_id, data_dispensacao, observacoes
    itens: relationship

class DispensacaoItem(Base):
    __tablename__ = "dispensacao_itens"
    id, dispensacao_id (FK), receita_item_id (FK), medicamento_nome (denormalized for audit), quantidade_dispensada, lote, validade_lote
```

**Schemas (Pydantic v2):**

```python
class DispensacaoConsultarRequest(BaseModel):
    codigo_receita: str  # conteúdo do QR Code ou hash

class ItemReceitaOut(BaseModel):
    id: UUID
    medicamento_id: UUID | None
    medicamento_nome: str
    apresentacao: str
    dosagem: str
    via_administracao: str | None
    posologia: str | None
    quantidade_prescrita: int
    quantidade_dispensada: int
    quantidade_pendente: int

class ReceitaConsultaOut(BaseModel):
    receita_id: UUID
    codigo_hash: str
    status: StatusReceita
    paciente_nome: str
    paciente_cns: str (masked? For pharmacy they need full CNS... I'll return masked partially? Actually the pharmacy needs to confirm identity. I'll return CNS masked like "116***********08"? Hmm, LGPD. Let me return masked CNS and CPF in the response, since the pharmacist should compare with the physical card. Actually for usability, return masked: first 3 and last 2 digits? Let me do a simple mask: keep first 3 and last 2.)
    paciente_cpf: str | None (masked)
    profissional_prescritor: str
    unidade_nome: str
    data_emissao: datetime
    data_validade: datetime
    cid10: str | None
    ciap2: str | None
    itens: list[ItemReceitaOut]
    dispensavel: bool
    motivo_indisponivel: str | None
```

Hmm, wait — should consultar return 409 for expired/cancelled, or return 200 with `dispensavel=False`? For a pharmacy workflow, returning