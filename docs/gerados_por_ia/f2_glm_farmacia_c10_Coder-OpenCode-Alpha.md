The user wants me to create a pharmacy dispensation API for the MedIA project (Brazilian SUS healthcare system). Let me analyze the requirements:

1. Create `backend/app/api/v1/farmacia.py` with FastAPI routes:
   - `POST /dispensacao/consultar` - validates QR Code/hash of prescription
   - `POST /dispensacao/confirmar` - registers total or partial dispensation of medications in SUS

2. Requirements:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Since this is a coder agent task, I need to provide complete, executable code. Let me think about the architecture:

**Files needed:**
1. `backend/app/api/v1/farmacia.py` - main API routes
2. `backend/app/schemas/farmacia.py` - Pydantic v2 schemas
3. `backend/app/models/farmacia.py` - SQLAlchemy 2.0 models
4. `backend/app/core/security.py` or similar - for hash validation
5. Tests: `backend/tests/test_farmacia.py`

Let me design the domain model:

**Prescription (Receita):**
- ID, hash/QR code token
- Patient (CNS/CPF)
- Professional who prescribed (CRM/COREN, CNS)
- CID-10 diagnosis
- Items (medications)
- Status: EMITIDA (issued), PARCIALMENTE_DISPENSADA (partially dispensed), DISPENSADA (fully dispensed), VENCIDA (expired), CANCELADA (cancelled)
- Validity date
- Issued at

**Dispensation (Dispensação):**
- ID
- Prescription reference
- Pharmacist info (CFP - Conselho Federal de Farmácia registration, CNS)
- UBS/Unidade (pharmacy unit - CNES)
- Date
- Items dispensed (quantities)
- Type: TOTAL or FRACIONADA (partial)

**Prescription Item:**
- Medication (name, presentation, concentration)
- Quantity prescribed
- Quantity already dispensed
- Remaining

**Business rules:**
- QR Code/hash validation: prescription must exist, be valid (not expired, not cancelled, not fully dispensed)
- Confirm dispensation: 
  - Total: all items fully dispensed
  - Fractioned: partial quantities, remaining quantities tracked
  - Cannot dispense more than prescribed
  - Cannot dispense expired prescription
  - Cannot dispense cancelled prescription
  - When all items reach full quantity, status becomes DISPENSADA
  - Audit trail

**Security:**
- Authentication (JWT) - pharmacist role
- Hash validation with HMAC signature to prevent tampering

Let me think about the hash/QR code. The QR code on a SUS prescription typically contains a token/hash. The validation should:
1. Parse the token (could be `receita:{uuid}:{signature}` format)
2. Verify HMAC signature using server secret
3. Look up prescription by UUID
4. Check status/validity

Let me write the code:

**Models (SQLAlchemy 2.0 with Mapped/mapped_column):**

```python
# backend/app/models/farmacia.py
import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import String, ForeignKey, DateTime, Date, Numeric, Enum, Integer, func, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base  # assumed Base class


class StatusReceita(StrEnum):
    EMITIDA = "EMITIDA"
    PARCIALMENTE_DISPENSADA = "PARCIALMENTE_DISPENSADA"
    DISPENSADA = "DISPENSADA"
    CANCELADA = "CANCELADA"
    VENCIDA = "VENCIDA"  # maybe computed instead
```

Actually, VENCIDA should probably be computed based on validade date, not stored. Let me keep statuses: EMITIDA, PARCIALMENTE_DISPENSADA, DISPENSADA, CANCELADA.

```python
class Receita(Base):
    __tablename__ = "receitas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)  # token in QR
    paciente_cns: Mapped[str] = mapped_column(String(15))
    paciente_cpf: Mapped[str | None] = mapped_column(String(11))
    paciente_nome: Mapped[str] = mapped_column(String(200))
    prescritor_nome: Mapped[str] = mapped_column(String(200))
    prescritor_cns: Mapped[str] = mapped_column(String(15))
    prescritor_registro: Mapped[str] = mapped_column(String(20))  # CRM/COREN
    cid10: Mapped[str | None] = mapped_column(String(6))
    ciap2: Mapped[str | None] = mapped_column(String(3))
    data_emissao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    data_validade: Mapped[date] = mapped_column(Date())
    status: Mapped[StatusReceita] = mapped_column(...)
    unidade_cnes: Mapped[str] = mapped_column(String(7))
    observacoes: Mapped[str | None]
    
    itens: Mapped[list["ReceitaItem"]] = relationship(back_populates="receita", cascade="all, delete-orphan")
    dispensacoes: Mapped[list["Dispensacao"]] = relationship(back_populates="receita")


class ReceitaItem(Base):
    __tablename__ = "receita_itens"
    
    id: Mapped[uuid.UUID]
    receita_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("receitas.id"))
    medicamento_nome: Mapped[str]
    medicamento_codigo: Mapped[str | None]  # CATMAT code maybe
    apresentacao: Mapped[str]
    concentracao: Mapped[str | None]
    via_administracao: Mapped[str]
    posologia: Mapped[str]
    quantidade_prescrita: Mapped[int]
    quantidade_dispensada: Mapped[int] = mapped_column(default=0)
    
    receita: Mapped["Receita"] = relationship(back_populates="itens")


class Dispensacao(Base):
    __tablename__ = "dispensacoes"
    
    id: Mapped[uuid.UUID]
    receita_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("receitas.id"))
    tipo: Mapped[TipoDispensacao]  # TOTAL, FRACIONADA
    farmaceutico_nome: Mapped[str]
    farmaceutico_crf: Mapped[str]  # registro CRF
    farmaceutico_cns: Mapped[str | None]
    unidade_cnes: Mapped[str]
    data_dispensacao: Mapped[datetime]
    observacoes: Mapped[str | None]
    
    itens: Mapped[list["DispensacaoItem"]] = relationship(...)


class DispensacaoItem(Base):
    __tablename__ = "dispensacao_itens"
    
    id, dispensacao_id, receita_item_id (FK), quantidade_dispensada, lote, validade_lote
```

**Schemas (Pydantic v2):**

```python
# backend/app/schemas/farmacia.py
from pydantic import BaseModel, Field, field_validator, ConfigDict

class ItemConsultaDispensavel(BaseModel):
    item_id: UUID
    medicamento: str
    apresentacao: str
    quantidade_prescrita: int
    quantidade_dispensada: int
    quantidade_pendente: int

class ConsultaReceitaResponse(BaseModel):
    receita_id: UUID
    status: StatusReceita
    paciente: ...
    prescritor: ...
    cid10, ciap2
    data_emissao, data_validade, valida: bool, motivo_invalidade: str | None
    itens: list[ItemConsultaDispensavel]

class ConsultaReceitaRequest(BaseModel):
    qr_code: str  # or hash

class ItemDispensacaoRequest(BaseModel):
    receita_item_id: UUID
    quantidade: int = Field(gt=0)
    lote: str | None
    validade_lote: date | None

class ConfirmarDispensacaoRequest(BaseModel):
    qr_code: str
    tipo: TipoDispensacao  # TOTAL | FRACIONADA
    farmaceutico: FarmaceuticoInfo
    itens: list[ItemDispensacaoRequest]
    observacoes: str | None

class ConfirmarDispensacaoResponse(BaseModel):
    dispensacao_id: UUID
    receita_id: UUID
    status_receita: StatusReceita
    itens: ...
    data_dispensacao: datetime
```

**Validators for CNS and CPF:**

CNS validation algorithm (Cartão Nacional de Saúde):
- Must be 15 digits
- Starting with 1, 2, 7, 8, or 9
- Check digit via modulo 11 algorithm

CNS validation:
```
Digits: n1..n15
sum = n1*15 + n2*14 + ... + n15*1
remainder = sum % 11
dv = 11 - remainder
if dv == 11: dv = 0
valid if dv == 0... 
```

Actually the correct algorithm: sum of weights 15 down to 1. If remainder == 0, invalid. Let me recall:

The CNS validation:
1. 15 digits, first char in {1,2,7,8,9}
2. Compute sum = Σ (digit_i × weight_i) where weights go 15,14,...,1
3. rest = sum % 11
4. dv = 11 - rest
5. If dv == 11 → dv = 0
6. If dv == 10 → invalid
7. Valid if dv equals... hmm, actually the algorithm is different.

The standard algorithm:
```
soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
resto = soma % 11
dv = 11 - resto
if dv == 11:
    dv = 0
if dv == 10:
    # invalid... actually need special handling
```

Hmm, let me recall properly. The official algorithm from DATASUS:

```
function validaCNS(vCNS) {
    // Formato: 15 dígitos, iniciando com 1, 2, 7, 8 ou 9
    if ([1, 2, 7, 8, 9].indexOf(vCNS[0]) == -1) return false;
    
    soma = 0;
    for (i = 0; i < 15; i++) {
        soma += parseInt(vCNS[i]) * (15 - i);
    }
    resto = soma % 11;
    dv = 11 - resto;
    if (dv == 11) dv = 0;
    if (dv == 10) {
        // Para CNS que começa com 7, 8 ou 9, o DV é calculado diferente
        soma = 0;
        for (i = 0; i < 15; i++) {
            pis = ... 
        }
    }
    return dv == parseInt(vCNS[14]) ... 
}
```

Hmm, actually the full algorithm for CNS starting with 7, 8, 9 uses a different formula (like PIS/PASEP):

```
if dv == 10:
    resto = soma % 11  # recompute?
```

Let me recall the exact DATASUS algorithm:

```javascript
function validaCNS(vCNS) {
  if (vCNS.trim().length != 15) return false;
  var soma = 0;
  var resto = 0;
  var dv = 0;
  var pis = "";
  var resultado = "";
  var tam = vCNS.length;
  var falso = false;
  
  if ((vCNS.substr(0,1) != "1") && (vCNS.substr(0,1) != "2") && (vCNS.substr(0,1) != "7") && (vCNS.substr(0,1) != "8") && (vCNS.substr(0,1) != "9")) {
    return false;
  }
  
  pis = vCNS.substring(0, 11);
  soma = 0;
  for (i = 0; i < 11; i++) {
    soma += parseInt(pis.charAt(i)) * (15 - i);
  }
  resto = soma % 11;
  dv = 11 - resto;
  if (dv == 11) dv = 0;
  if (dv == 10) {
    soma = 0;
    pis = vCNS.substring(0, 11);
    soma = soma + parseInt(pis.charAt(0)) * 3 + ... 
    // Actually: 
    soma = 2 * soma... 
  }
}
```

Hmm, this is getting complicated. The actual algorithm for dv == 10 case:

```
if (dv == 10) {
    soma = 0;
    for (i = 0; i < 11; i++) {
        soma += parseInt(pis.charAt(i)) * (15 - i);  // no...
    }
}
```

Let me look at the canonical implementation (from DATASUS / widely used):

```javascript
function validaCNS(vCNS) {
  // vCNS must have exactly 15 numeric chars
  if (vCNS.trim().length != 15) return (false);

  var soma = new Number;
  var resto = new Number;
  var dv = new Number;
  var pis = new String;
  var resultado = new String;
  var tam = vCNS.length;
  var i = new Number;
  pis = vCNS.substring(0,11);

  if ((tam != 15) || (pis == "00000000000")) {
    return (false);
  }

  for (i = 0; i < 11; i++) {
    soma += parseInt(pis.substring(i, i + 1)) * (15 - i);
  }

  resto = (soma % 11);
  dv = (11 - resto);

  if (dv == 11) {
    dv = "0";
  } else if (dv == 10) {
    soma = 2 * parseInt(pis.substring(0, 1)) +
           3 * parseInt(pis.substring(1, 2)) +
           4 * parseInt(pis.substring(2, 3)) +
           5 * parseInt(pis.substring(3, 4)) +
           6 * parseInt(pis.substring(4, 5)) +
           7 * parseInt(pis.substring(5, 6)) +
           8 * parseInt(pis.substring(6, 7)) +
           9 * parseInt(pis.substring(7, 8)) +
           10 * parseInt(pis.substring(8, 9)) +
           11 * parseInt(pis.substring(9, 10)) +
           12 * parseInt(pis.substring(10, 11));

    resto = (soma % 11);
    resto = 11 - resto;
    if (resto == 11 || resto == 10) {
      dv = "0";
    } else {
      dv = resto;
    }
  } else {
    dv = dv.toString();
  }

  resultado = pis + dv.toString();
  if (vCNS != resultado) {
    return (false);
  }
  return (true);
}
```

Wait, but this only validates 11 digits + DV = 12 digits? No — CNS has 15 digits. Hmm. Actually the CNS format: for numbers starting with 1 or 2 (cartão padrão), it's 15 digits where the check is done on... 

Actually the CNS is 15 digits. The algorithm above treats the first 11 digits as "pis" and computes dv, then resultado = pis + dv = 12 chars, comparing to 15-char vCNS would fail. That's wrong.

Let me reconsider. The correct CNS validation for 15 digits:

```
soma = 0
for i in 0..14:
    soma += cns[i] * (15 - i)
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0
if dv == 10: invalid? 
```

Hmm no. Let me think about known valid CNS: 700 0000 0000 00000? 

Known test CNS values: "898004027905022" is often cited as valid test CNS? Let me verify with the 15-digit weighted algorithm:

Weights: 15,14,13,12,11,10,9,8,7,6,5,4,3,2,1
Digits: 8,9,8,0,0,4,0,2,7,9,0,5,0,2,2

soma = 8*15 + 9*14 + 8*13 + 0*12 + 0*11 + 4*10 + 0*9 + 2*8 + 7*7 + 9*6 + 0*5 + 5*4 + 0*3 + 2*2 + 2*1
= 120 + 126 + 104 + 0 + 0 + 40 + 0 + 16 + 49 + 54 + 0 + 20 + 0 + 4 + 2
= 120+126=246; +104=350; +40=390; +16=406; +49=455; +54=509; +20=529; +4=533; +2=535

535 % 11 = 535 - 48*11 = 535 - 528 = 7. dv = 11 - 7 = 4. Last digit is 2, not 4. So that algorithm says invalid.

Hmm. Let me check the actual known algorithm more carefully. From the official documentation (Manual de Orientação para os desenvolvedores do CNS):

The CNS check digit algorithm:
1. CNS has 15 digits.
2. Multiply each digit by weights from left: 15, 14, 13, ..., 1.
3. Sum all results.
4. The sum plus the check digit must be divisible by 11.

So: soma (of first