The user wants me to create a clinical risk inference engine (Manchester Triage System adapted) for Primary Health Care (APS - Atenção Primária à Saúde) in Brazil, as part of the MedIA project.

Requirements:
- File: `backend/app/services/triagem_clinica.py`
- Risk classification engine for APS (Primary Health Care)
- Evaluation of extreme vital signs
- Sentinel complaints (chest pain, severe dyspnea)
- Priority assignment (Vermelho/Red, Laranja/Orange, Amarelo/Yellow, Verde/Green, Azul/Blue)
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me design this properly:

1. **Pydantic models** for input/output:
   - `SinaisVitais` (vital signs): PA sistólica/diastólica, FC, FR, SpO2, temperatura, glicemia, nível de consciência (AVPU ou Glasgow)
   - `QueixaPrincipal` (chief complaint): with CIAP-2 codes
   - `DadosPaciente` (patient data): CNS, CPF, age, sex
   - `EntradaTriagem` (triage input)
   - `ResultadoTriagem` (triage result): priority level, justification, SOAP notes, recommended actions, time-to-care

2. **Manchester Adapted classification**:
   - Vermelho (Red): immediate care (0 min) - emergency
   - Laranja (Orange): very urgent (10 min)
   - Amarelo (Yellow): urgent (60 min)
   - Verde (Green): standard (120 min)
   - Azul (Blue): non-urgent (240 min)

3. **Rules engine**:
   - Vital signs extremes:
     - SpO2 < 90% → Red (or < 94% with respiratory complaint → Orange)
     - SBP < 90 → Red (shock); SBP > 180 or DBP > 110 → Orange (hypertensive crisis); SBP > 200 → Red maybe
     - HR < 40 or > 130 → Red; 40-50 or 120-130 → Orange
     - RR < 10 or > 30 → Red; > 24 → Orange
     - Temp < 35 (hypothermia) → Red; >= 39.5 with signs → Orange; >= 38 with fever + red flags
     - Glucose < 50 → Red (hypoglycemia); < 70 symptomatic → Orange; > 300 → Orange; > 400 → Red
     - AVPU: only responsive to pain/unresponsive → Red; confused → Orange
   - Sentinel complaints:
     - Chest pain (dor torácica) → at least Orange, Red if with vital signs alterations or radiation/sweating
     - Severe dyspnea (dispneia grave) → Orange/Red
     - Others: sudden severe headache, convulsion, unconsciousness, active major bleeding, anaphylaxis signs, stroke signs (FAST), suicidal ideation
   - Age adjustments: neonates/infants and elderly have different thresholds

4. **CIAP-2 codes** for complaints:
   - Chest pain: L04 (L01 actually - heart pain; L04 chest pain)
   - Actually CIAP-2: L01 = heart pain, L04 = chest pain
   - Dyspnea: R02
   - Fever: A03
   - Headache: N01
   - etc.

5. **SOAP method**: generate subjective/objective/assessment/plan notes

6. **SQLAlchemy 2.0**: model for storing triage records (TriagemRecord) — the task says the service file, but architecture mentions SQLAlchemy 2.0. I should include a SQLAlchemy model for persistence, maybe in the same file or reference. Since the task says create `backend/app/services/triagem_clinica.py`, I'll focus on that file but can include the SQLAlchemy model there or create a separate models file. To keep it self-contained and executable, I'll include the SQLAlchemy table model in the service file (or a models module). Better: include the SQLAlchemy model in the service file so it's complete, with `DeclarativeBase`.

Actually, let me structure:
- `backend/app/services/triagem_clinica.py` — main engine (Pydantic schemas + rules engine + service class with persistence via SQLAlchemy)
- `backend/tests/test_triagem_clinica.py` — pytest tests

The instructions say "Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo". So I should provide the main file and tests.

Let me write the code:

```python
# Arquivo: backend/app/services/triagem_clinica.py
"""
Motor de Inferência de Risco Clínico — Manchester Adaptado (C15)
Projeto MedIA — Atenção Primária à Saúde (APS/SUS)
...
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Final, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, StringConstraints
from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
```

Wait — should I use PostgreSQL UUID or generic? To be safe and DB-agnostic, I could use String(36) for UUID. Let me use a portable approach: `String(36)` with default uuid4 hex. Or use `sqlalchemy.Uuid` type (SQLAlchemy 2.0 has `Uuid` type). Yes, SQLAlchemy 2.0 introduced `sqlalchemy.Uuid`. I'll use that for portability.

Enums:

```python
class Prioridade(str, Enum):
    VERMELHO = "VERMELHO"
    LARANJA = "LARANJA"
    AMARELO = "AMARELO"
    VERDE = "VERDE"
    AZUL = "AZUL"
```

With metadata: max wait time, description.

Vital signs model with validation ranges:

```python
class SinaisVitais(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    pa_sistolica: float | None = Field(None, ge=40, le=300, description="Pressão arterial sistólica (mmHg)")
    pa_diastolica: float | None = Field(None, ge=20, le=200)
    frequencia_cardiaca: float | None = Field(None, ge=0, le=300)
    frequencia_respiratoria: float | None = Field(None, ge=0, le=80)
    saturacao_oxigenio: float | None = Field(None, ge=0, le=100)
    temperatura: float | None = Field(None, ge=30, le=45)
    glicemia_capilar: float | None = Field(None, ge=0, le=2000)
    nivel_consciencia: NivelConsciencia | None = None  # AVPU
    dor_escala: int | None = Field(None, ge=0, le=10)
```

NivelConsciencia AVPU: ALERTA, RESPONDE_VOZ, RESPONDE_DOR, INCONSCIENTE.

Patient data with CNS/CPF validation:

CNS validation algorithm: CNS can start with 1, 2, 7, 8, 9. Validation uses mod 11 with weights 15 down to 2. Let me implement:

```python
def _validar_cns(cns: str) -> bool:
    cns_digits = re.sub(r"\D", "", cns)
    if len(cns_digits) != 15:
        return False
    if cns_digits[0] not in {"1", "2", "7", "8", "9"}:
        return False
    # For CNS starting with 7, 8, 9 (temporary), the check differs? Actually the standard algorithm:
    soma = sum(int(d) * w for d, w in zip(cns_digits, range(15, 0, -1)))
    return soma % 11 == 0
```

The standard CNS validation: weights 15..2, sum % 11 == 0. This works for all CNS (1/2 and 7/8/9). Yes, that's the standard algorithm used in Brazil.

CPF validation:

```python
def _validar_cpf(cpf: str) -> bool:
    digits = re.sub(r"\D", "", cpf)
    if len(digits) != 11 or digits == digits[0] * 11:
        return False
    for n in (9, 10):
        check = sum(int(d) * (n + 1 - i) for i, d in enumerate(digits[:n]))  # weights descending
        d = (check * 10) % 11 % 10
        if d != int(digits[n]):
            return False
    return True
```

Standard CPF: dv1 = (sum(weights 10..2 for first 9 digits) * 10) % 11, if 11 → 0. dv2 similar with weights 11..2 for first 10 digits. Let me write it carefully:

```python
def _validar_cpf(cpf: str) -> bool:
    digits = re.sub(r"\D", "", cpf)
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    # DV1
    soma = sum(int(digits[i]) * (10 - i) for i in range(9))
    dv1 = (soma * 10) % 11 % 10
    if dv1 != int(digits[9]):
        return False
    # DV2
    soma = sum(int(digits[i]) * (11 - i) for i in range(10))
    dv2 = (soma * 10) % 11 % 10
    return dv2 == int(digits[10])
```

Check: (soma*10) % 11 gives 0..10; if result 10 → 0, hence % 10. Correct.

Complaints model with CIAP-2:

```python
class QueixaPrincipal(BaseModel):
    descricao: str
    ciap2: CodigoCIAP2 | None
    cid10: str | None
    inicio_sintomas: str | None (or timedelta)
    intensidade_dor: int 0-10
    sintomas_associados: list[str]
```

CIAP-2 relevant codes:
- A03: Fever
- L01: Heart pain (dor precordial/cardíaca)
- L04: Chest pain (dor torácica)
- R02: Dyspnea (falta de ar)
- R05: Cough
- N01: Headache
- K29: Stroke? Actually K90 = stroke/cerebrovascular accident... CIAP-2: K90 = Stroke/cerebrovascular accident. K29? No. Let me recall CIAP-2 codes:
  - K29: Elevated blood pressure (hipertensão arterial sem outras queixas) — yes, K29 is "Elevated blood pressure".
  - K90: Stroke.
  - K74: Acute myocardial infarction? Actually K75 = acute myocardial infarction; K74 = acute ischemic heart disease? CIAP-2: K75 "Acute myocardial infarction", K74 "Acute ischemic heart disease", K76 "Angina pectoris"? Hmm. K76 is "Angina pectoris"? Let me recall: K68 = hypertension? No...

CIAP-2 chapter K (cardiovascular):
- K01: Chest pain? No, that's L04? Actually chest pain is L04 in chapter L? Hmm. CIAP-2: Chapter L is "Digestive"? No wait.

CIAP-2 chapters:
- A: General, unspecified
- B: Blood
- C: Digestive
- D: Digestive? No...

Let me recall properly: CIAP-2 chapters:
- A — General and unspecified
- B — Blood, blood-forming organs, lymphatics
- C — Digestive
- D — Digestive? No. 

Actually: A General/unspecified; B Blood; C Digestive; D Eye? No, F is Eye. Let me list: A General, B Blood, C Digestive, D Eye? Hmm, I think:
- A: General and unspecified
- B: Blood, blood-forming organs and immune mechanisms
- C: Digestive
- D: Eye
- E: Ear
- F: Circulatory
- G: Respiratory? 

No wait. CIAP-2: 
- A General and unspecified
- B Blood, blood-forming organs, lymphatic and immune mechanisms
- C Digestive
- D Eye
- E Ear
- F Circulatory
- G Respiratory
- H Digestive? no...

Hmm, I recall: F = Circulatory, K = ... no. Let me think again. CIAP-2 has 17 chapters: A, B, C, D, E, F, G, H, K, L, N, P, R, S, T, U, W, X, Y, Z. That's 20? Chapters:
- A General and unspecified
- B Blood, blood-forming organs, lymphatics and immune mechanism
- C Digestive
- D Eye
- E Ear
- F Circulatory
- G Respiratory
- H Digestive?? no — H is... 

Actually the correct list:
A — General and unspecified
B — Blood, blood-forming organs, lymphatic and immune mechanisms
C — Digestive
D — Eye
E — Ear
F — Circulatory
G — Respiratory
H — Digestive? No, H doesn't exist? 

Hmm. The 17 chapters of ICPC-2: A, B, C, D, E, F, G, H, K, L, N, P, R, S, T, U, W, X, Y, Z — that's 20 letters but some are missing. ICPC-2 chapters:
1. A — General and unspecified
2. B — Blood, blood-forming organs, lymphatics, immune mechanism
3. C — Digestive
4. D — Eye
5. E — Ear
6. F — Circulatory
7. G — Respiratory
8. H — Digestive? No! H is... 

OK here's the real list (ICPC-2):
- A: General and unspecified
- B: Blood, blood-forming organs, lymphatics and immune mechanism
- C: Digestive
- D: Eye
- E: Ear
- F: Circulatory
- G: Respiratory
- H: Digestive — no...

I'm confusing myself. The actual ICPC-2 chapters are:
A, B, C, D, E, F, G, H, K, L, N, P, R, S, T, U, W, X, Y, Z (20 chapters? no, 17).

Real ICPC-2:
- A General and unspecified
- B Blood, blood-forming organs, lymphatics and immune mechanism
- C Digestive
- D Eye
- E Ear
- F Circulatory
- G Respiratory
- H Digestive? — NO. H is not used? Actually ICPC-2 does NOT have H? Hmm, ICPC-2 chapters: A, B, C, D, E, F, G, H, K, L, N, P, R, S, T, U, W, X, Y, Z. H = "Digestive"? No, C is Digestive.

Let me just recall specific codes I know:
- A01: Pain, generalized
- A03: Fever
- A04: Weakness
- A06: Fainting/syncope
- A11: Chest pain, NOS? No — A11 is "Chest pain NOS"? Hmm, actually A11 = "Chest pain, NOS" exists in ICPC-2! Yes: A11 Chest pain NOS.
- B80: Anemia
- C01? 
- D01? 
- F01? 
- K29: Elevated blood pressure — yes, K is Circulatory! K chapter = Circulatory. F = Eye? No, D = Eye.

OK so: K = Circulatory (K29 hypertension, K74 acute ischemic heart disease, K75 AMI, K76 angina? K76 = "Angina pectoris"? I think K76 is "Angina pectoris". K90 = stroke, K91 = TIA? K91 = "Cerebrovascular disease"? Hmm. K90 = "Stroke/cerebrovascular accident", K91 = "Cerebrovascular disease"? Not sure. K89 = "Transient cerebral ischaemia"? Hmm.

- L = Musculoskeletal
- N = Neurological (N01 headache, N02? N03?)
- P = Psychological (P76 depression, P19? suicidal: P19 "Suicide attempt"? Hmm, P19 = "Suicide/suicide attempt"? Not sure. There's P98? Let me think: P19 = "Suicide/suicide attempt" — I believe that's right? Hmm, ICPC-2 P19 = "Suicide/suicide attempt". Yes I'm fairly confident.
- R = Respiratory (R02 dyspnea? R02 = "Shortness of breath/dyspnoea"? Hmm, R02 = "Shortness of breath/dyspnoea"? Actually R02 = "Shortness of breath/dyspnoea". Yes. R05 = cough. R74 = upper respiratory infection? R74 = "Acute upper respiratory infection". R96 = asthma.
- S = Skin
- T = Endocrine/metabolic (T89 = diabetes? T90 = "Diabetes non-insulin dependent", T91 = "Diabetes insulin-dependent"? Hmm: T90 = "Diabetes non-insulin dependent", T91 = "Diabetes insulin-dependent". T10? T04? Hypoglycemia: T11? Hmm. Actually T89 = "Diabetes unspecified"? I recall T89 = "Diabetes mellitus, unspecified"? Not sure. Let me not overreach.
- U = Urinary
- W = Pregnancy
- X = Female genital
- Y = Male genital
- Z = Social

And L = Musculoskeletal (L04 = "Chest pain"? No! L04 = "Chest pain" is in... hmm. Actually L04 = "Chest pain" —