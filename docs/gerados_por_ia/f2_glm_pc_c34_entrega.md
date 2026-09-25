The user wants me to create a FastAPI module for pharmaceutical dispensation and prescription fulfillment (baixa de receita) for the MedIA project, related to SUS (Brazilian Unified Health System).

Let me think about what's needed:

1. **File**: `backend/app/api/v1/farmacia.py`
2. **Routes**:
   - `POST /dispensacao/consultar` - validates QR Code/hash of the prescription
   - `POST /dispensacao/confirmar` - registers total or partial (fracionada) fulfillment of medications in SUS

3. **Requirements**:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me design this properly:

### Domain Model Considerations

**Prescrição (Prescription)**:
- Has a hash/QR code for validation
- Contains items (medications)
- Status: EMITIDA (issued), PARCIAL (partially dispensed), DISPENSADA (fully dispensed), CANCELADA, EXPIRADA
- Linked to patient (CNS/CPF)
- Has CID-10 diagnosis code
- Has validity date

**Dispensação (Dispensation)**:
- Can be total or partial (fracionada)
- Records: professional (farmacêutico) with CNS, unit (UBS/Unidade de Saúde), items dispensed with quantity
- Updates prescription status

**Validation logic for /consultar**:
- Receive hash (from QR Code)
- Look up prescription
- Validate: exists, not expired, not cancelled, not fully dispensed
- Return prescription data: patient info, items with remaining quantities, status

**Validation logic for /confirmar**:
- Receive hash + dispensation data (items with quantities, professional info, unit)
- Validate prescription again
- Check quantities don't exceed prescribed remaining
- Register dispensation
- Update prescription status (total or partial)

### SQLAlchemy 2.0 Models

I should define models. Since the task says "crie backend/app/api/v1/farmacia.py" — the main file is the API router. But for it to be complete and testable, I need models and schemas. Let me structure:

- `backend/app/api/v1/farmacia.py` — the router (main deliverable)
- Supporting: models, schemas, service layer

The instruction says to create the file `farmacia.py` with the routes. But to be complete, I should provide the supporting files too (models, schemas, service) so tests can run. Let me provide:

1. `backend/app/models/farmacia.py` (SQLAlchemy 2.0 models) — or maybe the models already exist in the project; but since I'm asked to create this feature, I'll provide them.
2. `backend/app/schemas/farmacia.py` (Pydantic v2 schemas)
3. `backend/app/api/v1/farmacia.py` (router)
4. `backend/tests/api/v1/test_farmacia.py` (pytest tests)

Actually, let me be careful about scope. The task says: "crie backend/app/api/v1/farmacia.py com rotas FastAPI". The primary deliverable is that file. But the guidelines say "Manter conformidade total e cobertura de testes automatizados com pytest" — so tests are needed. And "Use Pydantic v2 e SQLAlchemy" — so models/schemas are needed.

I'll deliver a cohesive set of files:

1. `backend/app/models/farmacia.py` — SQLAlchemy 2.0 models (Prescricao, ItemPrescricao, Dispensacao, ItemDispensacao)
2. `backend/app/schemas/farmacia.py` — Pydantic v2 schemas
3. `backend/app/api/v1/farmacia.py` — the router with the two endpoints
4. `backend/tests/api/v1/test_farmacia.py` — pytest tests with full coverage
5. Maybe a small `backend/app/services/farmacia.py` service layer to keep the router thin — good architecture practice.

Also validators for CNS and CPF (SUS standards). CNS validation algorithm:
- CNS can be 15 digits starting with 1, 2, 7, 8, or 9
- Validation: sum of digits multiplied by weights 15 down to 2, mod 11, check digit logic

CPF validation: standard check digits algorithm.

Let me write the CNS validation:

```python
def validar_cns(cns: str) -> bool:
    cns = re.sub(r"\D", "", cns)
    if len(cns) != 15:
        return False
    if cns[0] not in "12789":
        return False
    # For CNS starting with 7, 8, 9 there's a different algorithm (provably generated), 
    # but the common validation is the weighted sum
    soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
    return soma % 11 == 0
```

The standard CNS validation: peso = 15 for first digit down to 1 for last... Actually the classic algorithm:

```
soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
if soma % 11 == 0: valid
```

Yes, that's the classic one for CNS starting with 1 or 2. For 7/8/9 (temporary CNS), the algorithm is different (uses multiplication by 5,4,3,2... and mod 11 with subtraction). Let me recall:

For CNS starting with 7, 8 or 9:
```
soma = sum(int(cns[i]) * (15 - i) for i in range(15))  # same weights? 
```
Actually the official algorithm for 7/8/9:
```
soma = 0
peso = 5 (starts)... 
```
The official one:
```
soma = int(cns[0])*15 + int(cns[1])*14 + ... 
```
Hmm, let me recall the official Ministério da Saúde routine (from the "Validação do CNS" doc):

```python
def valida_cns(cns):
    if len(cns) != 15: return False
    if cns[0] in '12':
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    elif cns[0] in '789':
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        resto = soma % 11
        dv = 11 - resto
        if dv == 11: dv = 0
        if dv == 10:
            # soma += 2 and recompute
            soma = sum(int(cns[i]) * (15 - i) for i in range(15)) + 2
            resto = soma % 11
            dv = 11 - resto
            if dv == 11: dv = 0
            return cns[14] == str(dv)  # hmm not exactly
        return cns[14] == str(dv)
    return False
```

The official algorithm (from DATASUS):

```
soma = 0
for i in 0..14: soma += cns[i] * (15 - i)
resto = soma % 11
if resto != 0: dv = 11 - resto else dv = 0
if dv == 10:
    soma += 2
    resto = soma % 11
    dv = 11 - resto
    if resto == 0... 
```

Hmm, this is getting complicated. Let me just use the well-known implementation:

```python
def valida_cns(cns: str) -> bool:
    """Valida CNS conforme algoritmo do Ministério da Saúde."""
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15 or cns[0] not in '12789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if soma % 11 == 0:
        return True
    # CNS provisório (7, 8, 9): recalcula com ajuste
    if cns[0] in '789':
        soma += 2
        return soma % 11 == 0
    return False
```

Hmm, actually the official one from the MS document "Validação do Cartão Nacional de Saúde":

```
Rotina para validação do CNS:
1. Somar os 15 dígitos multiplicados pelos pesos 15, 14, 13, ..., 1
2. Se o resto da divisão da soma por 11 for 0 → válido
3. Senão, se o CNS começa com 7, 8 ou 9: soma = soma + 2, e verifica novamente resto == 0
```

Yes! That's the official algorithm. The MS pseudo-code:

```
soma = 0
para i de 1 até 15:
    soma = soma + digito(i) * (16 - i)
resto = soma mod 11
se resto == 0 então válido
senão se primeiro dígito in [7,8,9]:
    soma = soma + 2
    resto = soma mod 11
    se resto == 0 então válido
```

Wait, weights: for i=1, weight 15; i=2, weight 14... i=15, weight 1. So weight = 16 - i, or in 0-indexed: 15 - i. Good.

CPF validation:

```python
def valida_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for n in (9, 10):
        dv = sum(int(cpf[i]) * (n + 1 - i) for i in range(n)) % 11
        # hmm standard: 
    ...
```

Standard CPF:
```python
def _calc_dv(cpf_parcial: str, peso_inicial: int) -> int:
    soma = sum(int(d) * p for d, p in zip(cpf_parcial, range(peso_inicial, 1, -1)))
    resto = (soma * 10) % 11
    return 0 if resto == 10 else resto
```

Actually simpler:
```python
def valida_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    dv1 = (sum(int(cpf[i]) * (10 - i) for i in range(9)) * 10) % 11 % 10
    dv2 = (sum(int(cpf[i]) * (11 - i) for i in range(10)) * 10) % 11 % 10
    return cpf[-2:] == f"{dv1}{dv2}"
```

That's a compact known-correct implementation. Let me verify: for i in range(9), weights 10-i → 10,9,8,...,2. Sum * 10 % 11 % 10. Yes, that's the classic one-liner. Good.

### Models (SQLAlchemy 2.0)

```python
class Prescricao(Base):
    __tablename__ = "prescricoes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    hash_validacao: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    paciente_nome: Mapped[str]
    paciente_cns: Mapped[str]
    paciente_cpf: Mapped[str | None]
    cid10: Mapped[str | None]  # CID-10
    ciap2: Mapped[str | None]  # CIAP-2
    profissional_solicitante: Mapped[str]
    cns_profissional: Mapped[str]
    unidade_saude: Mapped[str]  # UBS
    cod_unidade: Mapped[str]  # CNES
    data_emissao: Mapped[datetime]
    data_validade: Mapped[datetime]
    status: Mapped[PrescricaoStatus] = mapped_column(SAEnum(PrescricaoStatus), default=...)
    itens: relationship
    dispensacoes: relationship

class ItemPrescricao(Base):
    id, prescricao_id FK, medicamento (nome), principio_ativo, apresentacao, quantidade_prescrita, quantidade_dispensada (default 0), posologia, via_administracao, uso_continuo bool

class Dispensacao(Base):
    id, prescricao_id FK, tipo (TOTAL/FRACIONADA), cns_farmaceutico, nome_farmaceutico, cnes_unidade, nome_unidade, data_hora, observacoes

class ItemDispensacao(Base):
    id, dispensacao_id FK, item_prescricao_id FK, quantidade_dispensada, lote, validade_lote
```

Status enum: EMITIDA, PARCIALMENTE_DISPENSADA, DISPENSADA_TOTAL, CANCELADA, EXPIRADA.

### Schemas (Pydantic v2)

```python
class ItemPrescricaoConsulta(BaseModel):
    id: UUID
    medicamento: str
    principio_ativo: str | None
    apresentacao: str | None
    posologia: str
    via_administracao: str
    quantidade_prescrita: int
    quantidade_dispensada: int
    quantidade_pendente: int
    uso_continuo: bool

class DispensacaoConsultaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    prescricao_id: UUID
    hash_validacao: str  # maybe masked
    status: PrescricaoStatus
    paciente: ...
    cid10, ciap2
    data_emissao, data_validade
    itens: list[ItemPrescricaoConsulta]
    dispensacoes_anteriores: list[...]
    mensagem: str
```

Request for consultar:
```python
class ConsultaReceitaRequest(BaseModel):
    hash_qrcode: str  # or qr_code payload
```

Maybe the QR code contains a payload like "MEDIA|<uuid>|<hash>" — but keep it simple: accept `hash_validacao` (the hash printed/encoded in the QR). Could also accept the full QR payload and extract. Let me support both: field `qrcode` or `hash`. Hmm, keep it clean: `hash_receita: str` with alias maybe. I'll accept `hash_validacao: str` with validation (hex, 64 chars for sha256, or 32 for md5... let's say 32-64 hex chars). Actually let me be flexible: min 16, max 128, hex chars.

Request for confirmar:
```python
class ItemDispensacaoRequest(BaseModel):
    item_prescricao_id: UUID
    quantidade: int = Field(gt=0)
    lote: str | None
    validade_lote: date | None

class DispensacaoConfirmarRequest(BaseModel):
    hash_validacao: str
    tipo: Literal["TOTAL", "FRACIONADA"]  # or enum
    itens: list[ItemDispensacaoRequest] = Field(min_length=1)
    cns_farmaceutico: str  # validated
    nome_farmaceutico: str
    cnes_unidade: str  # 7 digits
    nome_unidade: str
    observacoes: str | None
```

Response for confirmar:
```python
class DispensacaoConfirmarResponse(BaseModel):
    dispensacao_id: UUID
    prescricao_id: UUID
    status_prescricao: PrescricaoStatus
    tipo: TipoDispensacao
    itens: list[...]
    data_hora: datetime
    mensagem: str
```

### Business rules

**Consultar**:
1. Hash not found → 404 with message "Receita não encontrada"
2. Cancelled → 409/422 "Receita cancelada"
3. Expired → 409/422 "Receita expirada em ..."
4. Fully dispensed → 409 "Receita já totalmente dispensada"
5. Otherwise → 200 with data

**Confirmar**:
1. Same validations as consultar
2. Items must belong to the prescription
3. Quantity per item cannot exceed pending (quantidade_prescrita - quantidade_dispensada)
4. tipo consistency: if all pending quantities are fulfilled → TOTAL; if partial → FRACIONADA. Validate the declared tipo matches the computed result? Or derive it. Better: validate that if tipo=TOTAL, all items with pending quantity are fully dispensed; if FRACIONADA, at least one item is not fully dispensed. Actually simpler and safer: compute the resulting status server-side and reject inconsistency between declared tipo and actual effect. Hmm — but "baixa total ou fracionada" — the pharmacist declares intent. Let me validate:
   - If tipo == TOTAL: every item in the request must have quantidade == quantidade_pendente, AND all prescription items must be covered (or at least all items with pending > 0 must be included and fully dispensed). That makes TOTAL truly total.
   - If tipo == FRACIONADA: at least one included item must have quantidade < quantidade_pendente (i.e., not a full baixa). 
   
   Alternatively, derive tipo automatically and ignore the declared one. But explicit validation is better for auditability. I'll validate consistency and return 422 on mismatch.

5. Register Dispensacao + ItemDispensacao rows, update ItemPrescricao.quantidade_dispensada, update Prescricao.status:
   - If all items have quantidade_dispensada == quantidade_prescrita → DISPENSADA_TOTAL
   - Else → PARCIALMENTE_DISPENSADA
6. Idempotency/concurrency: use row lock (SELECT ... FOR UPDATE) on prescription to avoid race conditions. With SQLite in tests, `with_for_update` is a no-op but harmless. I'll include it.

Also: expired check should use `data_validade` vs now (timezone-aware). Use `datetime.now(UTC)` in Python 3.12 (datetime.UTC exists in 3.11+). Good — Python 3.12, so `from datetime import UTC`.

### Service layer

Put business logic in `backend/app/services/farmacia_service.py` so the router is thin and tests can target service + API