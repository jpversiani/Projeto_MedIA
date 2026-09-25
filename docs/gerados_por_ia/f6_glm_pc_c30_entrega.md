The user wants me to create a Clinical Decision Support Engine and Drug Interaction Alerts system (C30) for the MedIA platform. This is for a doctor working from Home Office. I need to create `backend/app/services/copiloto_clinico.py` with:

1. Drug interaction analyzer (e.g., Fluoxetine + Tramadol, Enalapril + Spironolactone)
2. Allergy alerts from patient records before prescribing
3. Automatic conduct suggestions based on Brazilian Ministry of Health / SUS protocols

Architecture guidelines:
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Since this is a Portuguese request (Brazilian healthcare context), I should respond in Portuguese. The code should be production-quality with strict typing.

Let me design this carefully:

## Architecture Design

### Module: `backend/app/services/copiloto_clinico.py`

This is the main service file requested. However, to make it complete and testable, I should probably show:
1. The main service file (required)
2. Schemas (Pydantic v2 models)
3. SQLAlchemy 2.0 models (for interactions DB, allergies, prescriptions)
4. Tests with pytest

But the task says specifically "crie backend/app/services/copiloto_clinico.py". So the primary deliverable is that file. I can structure it as a comprehensive service module with:

- Pydantic v2 schemas for input/output
- SQLAlchemy 2.0 models (or at least imports/types)
- The interaction engine with a built-in knowledge base (since a real drug bank would be external, I'll create an embedded seed knowledge base with the examples given: Fluoxetina + Tramadol, Enalapril + Espironolactona, plus more common interactions)
- Allergy checking engine
- Conduct suggestion engine based on MS/SUS protocols
- CNS/CPF validation utilities
- CIAP-2 and CID-10 code support
- SOAP note structure support

Let me think about the structure:

```python
# backend/app/services/copiloto_clinico.py
"""Motor de Apoio à Decisão Clínica (CDS) e Alertas de Interação Medicamentosa — C30"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from functools import lru_cache
from typing import Annotated, Any, Final, Iterable, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, StringConstraints
from sqlalchemy import String, ForeignKey, Index, Text, Enum as SAEnum, select, func
from sqlalchemy.dialects.postgresql import JSONB  # maybe keep generic
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
```

Actually, for a service module, mixing SQLAlchemy models in the service file may be questionable, but the guidelines say SQLAlchemy 2.0. I could define the ORM models needed (AlergiaRegistro, MedicamentoCatalogo, InteracaoMedicamentosa, Prescricao...) in a models module and import. But since only one file is requested, I'll define everything needed in that file with clear section comments, or better: define minimal SQLAlchemy 2.0 models for the persistence layer within the service file's module (with a note that in production they'd live in `app/models/`). Hmm.

Let me think about what's cleanest for the answer: The user asked for one file. I'll deliver one comprehensive, self-contained file that includes:

1. **Tipos e constantes** — enums (SeveridadeInteração, OrigemAlerta, ViaAdministração, SexoBiologico, etc.)
2. **Validadores SUS** — CNS validator (with checksum algorithm — real algorithm), CPF validator (real algorithm), normalização de nomes de medicamentos
3. **Esquemas Pydantic v2** — PacienteContexto, MedicamentoPrescrito, AlergiaPaciente, ProtocoloMS, CondutaSugerida, AlertaClinico, AvaliacaoPrescricao, NotaSOAP
4. **Base de conhecimento (KB)** — interações medicamentosas (incluindo Fluoxetina+Tramadol = síndrome serotoninérgica; Enalapril+Espironolactona = hipercalemia), contraindicações por alergia (e.g., penicilina → amoxicilina, ampicilina cross-reactivity), protocolos MS/SUS
5. **SQLAlchemy 2.0 ORM models** — for persistence: AlergiaORM, InteracaoORM, PrescricaoORM, LogAlertaORM — used for loading allergies from prontuário and auditing alerts
6. **Motor principal** — `CopilotoClinico` class with methods:
   - `analisar_interacoes(medicamentos) -> list[AlertaInteracao]`
   - `verificar_alergias(paciente, medicamentos) -> list[AlertaAlergia]`
   - `sugerir_condutas(queixa, cid/ciap) -> list[CondutaSugerida]`
   - `avaliar_prescricao(contexto, medicamentos) -> AvaliacaoPrescricao` (orchestrates all, SOAP support)
   - `registrar_alerta_suprimido(...)` audit trail (LGPD compliance, CFM resolution 2.317/2022 for telemedicine)
7. **Protocolos** — e.g., HAS (hipertensão), DM (diabetes), dor, depressão based on MS protocols (LINHAIS DE CUIDADO, PCDT). I'll implement a small protocol dictionary with CID-10 and CIAP-2 codes.

Key real drug interactions to include in the KB:

- **Fluoxetina + Tramadol**: Major — risk of serotonin syndrome (serotonergic). Recommendation: avoid combination; if needed, monitor, reduce dose.
- **Enalapril + Espironolactona**: Major — hyperkalemia risk (ACE inhibitor + potassium-sparing diuretic). Monitor potassium, renal function.
- Others commonly seen in SUS:
  - Warfarina + AAS (bleeding)
  - Warfarina + Anti-inflamatórios (ibuprofeno/nimesulida)
  - Digoxina + Furosemida (hypokalemia → digoxin toxicity)
  - Metformina + contraste iodado (lactic acidosis — suspend before contrast)
  - IECA + AINE (renal function, reduce antihypertensive effect)
  - Sinvastatina + Claritromicina (CYP3A4 inhibition → myopathy/rhabdomyolysis)
  - ISRS + IMAO (serotonin syndrome, hypertensive crisis)
  - Fluoxetina + IMAO
  - Tramadol + ISRS
  - Lítio + IECA (lithium levels increase)
  - AAS + Ibuprofeno (reduces aspirin antiplatelet effect)
  - Metotrexato + AINE/trimetoprim
  - Espironolactona + suplemento de potássio
  - Anticonvulsivantes (carbamazepina) + anticoncepcional oral (enzyme induction → failure)
  - Ciprofloxacino + antiácidos (chelation — absorption)
  - Omeprazol + clopidogrel (CYP2C19 inhibition)

I'll include maybe 12-20 interactions with mechanism, severity, clinical effect, management recommendation, CID-10 codes for adverse effects (e.g., T88.7 efeito adverso não especificado, D69.5, R74.8...). For serotonin syndrome: G70.0? Actually serotonin syndrome doesn't have a clean CID; T43.2 (antidepressants adverse effect) — I'll use T43.2. Hyperkalemia: E87.5.

Allergy cross-reactivity mapping:
- Penicilina → contraindica: amoxicilina, ampicilina, penicilina benzatina, amoxicilina+clavulanato (same beta-lactam family). Cross-reactivity with cefalosporinas (~1-2%, use caution — "moderada").
- Sulfas (sulfametoxazol+trimetoprim) → contraindica sulfonamidas.
- AINEs (AAS) → contraindica ibuprofeno, naproxeno, diclofenaco (cross-reactivity in AERD).
- Iodo/contraste → cuidado com contraste.
- Látex.

Implementation approach for allergy matching: alias-based normalization (strip accents, lowercase) with "grupos" (classes terapêuticas). A drug belongs to groups; an allergy to a group or specific drug triggers an alert with severity depending on cross-reactivity level (direta vs cruzada).

Protocols (MS/SUS) — I'll encode a few:
- Hipertensão arterial (CID-10 I10, CIAP-2 K86/K87): eCAP/CD HAS — hidroclorotiazida as 1st line? Actually Brazilian PCDT for HAS: first line monotherapy options include diurético tiazídico, IECA, BRA, antagonista de cálcio. Enalapril 10mg... Let me keep it high-level: "segundo PCDT/DAH e Cartão HIPERDIA...". I'll provide conduct suggestions: medidas não farmacológicas, avaliar estratificação de risco cardiovascular, revisão a cada 3-6 meses.
- Diabetes Mellitus tipo 2 (E11, T90 — CIAP-2 T90): PCDT DM — metformina primeira linha, HbA1c alvo <7%.
- Depressão (F32, CIAP-2 P76): PCDT/Berlim — psicoterapia + fluoxetina/sertralina primeira linha (Lista Nacional de Medicamentos Essenciais — RENAME).
- Dor lombar inespecífica (M54.5, CIAP-2 L03): evitar repouso prolongado, paracetamol/AINE, exercícios.
- Infarto/precordalgia (K74/I21): protocolo SAMU, exames.
- Gripe/síndrome gripal (J11, CIAP-2 R80).
- Pré-natal...
- Ansiedade (F41, P74).

I'll implement maybe 5-7 protocols with SOAP-oriented conduct, CID-10, CIAP-2 mapping, and suggested "conduta" steps. Each conduct suggestion must cite the source (e.g., "PCDT/MS", "Protocolo APS/Ministério da Saúde 2021", "RENAME 2022"). Include a disclaimer that it supports, not replaces, clinical judgment (Resolução CFM 2.317/2022 for telemedicina; 1.821/2007 prontuário eletrônico).

CNS validation algorithm (real one):
- CNS can start with 1, 2, 7, 8, 9. 
- Algorithm: if 15 digits, sum = Σ (digit * weight) where weights cycle 15,14,...,2 for first 12? Let me recall the correct algorithm:

For CNS with 15 digits: take first 11 digits, compute sum of digit[i] * (15 - i) for i in 0..10. Then remainder = sum % 11; dv = 11 - remainder; if dv == 11, dv = 0; if dv == 10: then dv = 0 and sum += 2, recompute? The known algorithm:

```
def valida_cns(cns: str) -> bool:
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] not in "123789":
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

Yes! The correct algorithm: CNS is valid if the weighted sum with weights 15 down to 1 (i.e., 15 - i for i in 0..14) modulo 11 equals 0. Let me verify: weights are 15,14,...,1. Sum of digit × weight % 11 == 0. That's the standard "rotina do Ministério da Saúde para validação do CNS". Yes, that's correct.

CPF validation algorithm: standard mod 11 with weights 10..2 for first check digit, 11..2 for second.

Let me write:

```python
def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for n in (9, 10):
        d = sum(int(cpf[i]) * (n + 1 - i) for i in range(n))  # careful
        ...
```

Standard:

```python
def _dv_cpf(nove_digitos: str) -> int:
    soma = sum(int(d) * w for d, w in zip(nove_digitos, range(len(nove_digitos) + 1, 1, -1)))
```

Simpler explicit:

```python
def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf or "")
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    dv1 = (sum(int(cpf[i]) * (10 - i) for i in range(9)) * 10) % 11 % 10
    dv2 = (sum(int(cpf[i]) * (11 - i) for i in range(10))) % 11 % 10
    return cpf[-2:] == f"{dv1}{dv2}"
```

Check: dv1 = (sum(digit * weight 10..2) * 10) % 11 % 10. That's the classic formula. If result is 10 → 0 (handled by %10). Good.

Pydantic strict typing: use `ConfigDict(strict=True, frozen=True)` where sensible, `StringConstraints` with patterns, `field_validator`, `model_validator`.

Enums:
- `Severidade` (str, Enum): CONTRAINDICACAO = "contra-indicação absoluta", MAJOR, MODERADA, MENOR, INFO
- `MecanismoInteracao`: FARMACOCINETICO, FARMACODINAMICO, etc.
- `OrigemAlerta`: INTERACAO, ALERGIA, PROTOCOLO, DOSE, DUPLICIDADE
- `TipoAlergia`: MEDICAMENTOSA, ALIMENTAR, AMBIENTAL, OUTRA
- `ReacaoCruzada` level: DIRETA, CRUZADA, VIGILANCIA

Drug dataclass/Pydantic model: `MedicamentoInfo` — nome, dosagem, via, posologia. Normalization function `_normalizar(nome)` — uppercase, strip accents, collapse spaces.

Matching: map normalized names to canonical drug keys via alias table. E.g., "fluoxetina" → FLUOXETINA; "cloridrato de fluoxetina" → FLUOXETINA. Interactions keyed by frozenset of two canonical keys. Also same-drug duplication check (duplicidade terapêutica within same therapeutic class, e.g., two SSRIs — fluoxetina + sertralina → duplicidade de ISRS, contraindicated/major).

Interaction record:

```python
class InteracaoRegistrada(BaseModel):
    farmaco_a: str
    farmaco_b: str
    severidade: Severidade
    mecanismo: Mecanismo
    descricao: str  # efeito clínico
    conduta: str    # manejo recomendado
    efeitos: tuple[str, ...]
    cids_risco: tuple[str, ...]  # e.g., ("T43.2",)
    referencia: str  # "ANVISA BULA / Micromedex-like" — cite source type
```

Allergy model:

```python
class AlergiaRegistrada(BaseModel):
    substancia: str
    tipo: TipoAlergia
    reacao: str | None
    gravidade_previa: Literal["leve","moderada","grave","nao_informada"]
    cid_relacionado: str | None  # e.g., Z88 for history of allergy: Z88.0 penicillin... Actually Z88 = "História pessoal de alergia a medicamentos" Z88.0 penicilina, Z88.1 sulfas...
```

Z88 codes: Z88.0 Penicilina; Z88.1 outros antibióticos; Z88.2 sulfonamidas; Z88.3 outros anti-infecciosos; Z88.4 anestésicos; Z88.5 analgésicos/naróticos; Z88.6 serums/vacinas; Z88.7 outros; Z88.8... Actually Z88.8 "outras substâncias". Good detail for SUS standards.

Cross-reactivity KB:

```python
GRUPOS_FARMACOLOGICOS: dict[str, frozenset[str]] = {
    "PENICILINAS": {"AMOXICILINA","AMPICILINA","PENICILINA G BENZATINA","PENICILINA G PROCAÍNA","AMOXICILINA+CLAVULANATO"},
    "CEFALOSPORINAS": {"CEFLEX","CEFALEXINA","CEFUROXIMA","CEFTRIAXONA"},
    "SULFONAMIDAS": {"SULFAMETOXAZOL+TRIMETOPRIM","SULFADIAZINA","SULFASALAZINA"},
    "AINES": {"IBUPROFENO","DICLOFENACO","NIMESULIDA","NAPROXENO","CELECOXIB","ACIDO MEFENAMICO"},
    "ISRS": {"FLUOXETINA","SERTRALINA","PAROXETINA","CITALOPRAM","ESCITALOPRAM"},
    ...
}
```

Allergy match: if prescribed drug's canonical name in allergy alias set or in a group flagged by allergy → alert DIRETA (contra-indicação). If cross group (penicillin allergy vs cefalosporin prescribed) → alert CRUZ