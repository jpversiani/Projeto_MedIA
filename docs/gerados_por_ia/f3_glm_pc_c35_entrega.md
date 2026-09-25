The user wants me to create a clinical risk inference engine (Manchester Triage adapted) for the MedIA project, in Brazilian Primary Health Care (APS - Atenção Primária à Saúde) context, following SUS standards.

Let me plan the file: `backend/app/services/triagem_clinica.py`

Requirements:
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Manchester Triage adapted: Red, Orange, Yellow, Green, Blue priorities
- Vital signs extremes evaluation
- Sentinel complaints (chest pain, severe dyspnea)
- Test coverage with pytest

Let me design this carefully:

**Manchester Triage System (MTS) adapted for Brazil:**
- Vermelho (Red): Emergência - immediate care (0 min)
- Laranja (Orange): Muito urgente - 10 minutes
- Amarelo (Yellow): Urgente - 60 minutes
- Verde (Green): Pouco urgente - 120 minutes
- Azul (Blue): Não urgente - 240 minutes

**Key components:**

1. **Enums:**
   - `NivelRisco` (RiskLevel): VERMELHO, LARANJA, AMARELO, VERDE, AZUL with max wait times
   - `CategoriaFluxo` maybe

2. **Pydantic models:**
   - `SinaisVitais` (Vital signs): PA sistólica/diastólica, FC, FR, Temp, SpO2, glicemia capilar, nível de consciência (AVPU or Glasgow), dor (escala 0-10)
   - `QueixaSentinela`: chest pain, dyspnea, etc.
   - `PacienteTriagem`: identification (CNS/CPF), age, sex, vital signs, complaints, symptoms
   - `ResultadoTriagem`: priority level, score, justifications, discriminators triggered, recommended actions, CIAP-2 codes

3. **Engine logic:**
   - Vital signs extremes:
     - SpO2 < 90% → Red; 90-93% → Orange (with dyspnea)
     - SBP < 90 → Red; 90-100 → Orange
     - SBP > 180 with symptoms → Orange; > 200 → Orange/Red
     - HR < 40 or > 130 → Red; 40-50 or 120-130 → Orange
     - RR < 8 or > 30 → Red; > 24 → Orange
     - Temp < 35 or > 39.5 with red flags → Orange; > 40 → Orange
     - Glasgow < 9 → Red; 9-12 → Orange; 13-14 → Yellow
     - AVPU: P/U → Red, V → Orange
     - Glucose < 50 → Red (hypoglycemia); < 70 with symptoms → Orange; > 300 → Orange/Yellow
   - Sentinel complaints:
     - Chest pain: with characteristics (crushing, radiating, sweating) → Red/Orange
     - Severe dyspnea: SpO2, inability to speak → Red
     - Stroke signs (FAST): facial droop, arm weakness, speech → Red
     - Active major bleeding → Red
     - Anaphylaxis signs → Red
     - Seizure active → Red
     - Pregnancy complications
   - Age adjustments: neonates/infants have different thresholds
   - Pain scale: 8-10 with red flags

4. **CIAP-2 codes** for complaints:
   - Chest pain: K01, K02 (K74 ischemia)
   - Dyspnea: R02
   - Fever: A03
   - etc.

5. **SOAP method**: The result should include an "S" (Subjective) summary and suggested assessment notes.

6. **SQLAlchemy 2.0**: A model to persist triage records — `TriagemRegistro` table with typed columns (Mapped, mapped_column).

7. **Pydantic strict typing**: use `Field`, validators, `model_config = ConfigDict(strict=True)` maybe, frozen models.

8. **Tests**: pytest file `backend/tests/services/test_triagem_clinica.py` with comprehensive coverage.

Let me write the code.

Structure:

```python
"""Motor de Inferência de Risco Clínico — Manchester Adaptado (C35)."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, StringConstraints
from sqlalchemy import ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
```

Wait — the base. The project likely has its own Base. Since we don't know, I'll define a local DeclarativeBase or import from app.db. To be safe and self-contained, I'll define `class Base(DeclarativeBase)` guarded — actually better to try importing from `app.db.base` and fallback. Hmm, that's fragile. Common pattern in these generated projects: `backend/app/db/session.py` with Base. I'll do a try/except import with fallback local Base. Actually, cleaner: define the model with a local Base class but document that it can be swapped. Let me do a defensive import:

```python
try:
    from app.db.base import Base  # type: ignore[attr-defined]
except ImportError:
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass
```

That's reasonable for a service module.

**Enums:**

```python
class NivelRisco(str, Enum):
    VERMELHO = "VERMELHO"
    LARANJA = "LARANJA"
    AMARELO = "AMARELO"
    VERDE = "VERDE"
    AZUL = "AZUL"
```

With properties: `tempo_maximo_espera_min` (0, 10, 60, 120, 240) and `descricao`.

**Vital signs model:**

```python
class SinaisVitais(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    pa_sistolica: int | None = Field(None, ge=40, le=300, description="mmHg")
    pa_diastolica: int | None = Field(None, ge=20, le=200)
    frequencia_cardiaca: int | None = Field(None, ge=0, le=300, description="bpm")
    frequencia_respiratoria: int | None = Field(None, ge=0, le=80, description="irpm")
    temperatura: float | None = Field(None, ge=30.0, le=45.0, description="°C")
    saturacao_o2: float | None = Field(None, ge=0.0, le=100.0, description="%")
    glicemia_capilar: int | None = Field(None, ge=0, le=1000, description="mg/dL")
    escala_glasgow: int | None = Field(None, ge=3, le=15)
    nivel_consciencia: Literal["A", "V", "P", "U"] | None = None  # AVPU
    escala_dor: int | None = Field(None, ge=0, le=10)

    @model_validator(mode="after")
    def _validar_pa(self) -> Self:
        if self.pa_sistolica is not None and self.pa_diastolica is not None and self.pa_diastolica >= self.pa_sistolica:
            raise ValueError(...)
        return self
```

**Sentinel complaints:**

```python
class QueixaSentinela(str, Enum):
    DOR_TORACICA = "DOR_TORACICA"
    DISPNEIA = "DISPNEIA"
    DEFICIT_NEUROLOGICO = "DEFICIT_NEUROLOGICO"  # AVC
    SANGRAMENTO_GRAVE = "SANGRAMENTO_GRAVE"
    REACAO_ALERGICA = "REACAO_ALERGICA"  # anafilaxia
    CONVULSAO = "CONVULSAO"
    PERDA_CONSCIENCIA = "PERDA_CONSCIENCIA"
    FEBRE_PERSISTENTE = "FEBRE_PERSISTENTE"
    VOMITO_PERSISTENTE = "VOMITO_PERSISTENTE"
    CEFALEIA_BRUSCA = "CEFALEIA_BRUSCA"
    DOR_ABDOMINAL_INTENSA = "DOR_ABDOMINAL_INTENSA"
    GESTACAO_COMPLICACAO = "GESTACAO_COMPLICACAO"
```

Each with CIAP-2 code mapping.

**Patient model:**

```python
class PacienteTriagem(BaseModel):
    nome: str
    cns: str | None  # validated with algorithm
    cpf: str | None  # validated with algorithm
    idade_anos: int | None
    idade_meses: int | None  # for infants
    sexo: Literal["M", "F"]
    gestante: bool = False
    sinais_vitais: SinaisVitais | None
    queixas: list[QueixaSentinela]
    caracteristicas_dor_toracica: ... 
```

CNS validation algorithm (Cartão Nacional de Saúde): 15 digits, starts with 1, 2, 7, 8, or 9. Validation: for numbers starting with 1 or 2 (user cards) or 7/8/9 (temporary), use modulo 11 with weights 15 down to 2. The standard algorithm:

CNS validation:
- Must have 15 digits
- First digit must be 1, 2, 7, 8, or 9
- Sum: for i in 0..14: peso = 15 - i; soma += digito * peso; if soma % 11 == 0 → valid.

Actually the standard algorithm: multiply each of the 15 digits by weights 15,14,...,1? Let me recall. The official algorithm:

```
soma = 0
for i, digito in enumerate(cns):
    peso = 15 - i
    soma += int(digito) * peso
resto = soma % 11
valid = resto == 0
```

Yes, that's the common implementation for CNS (weights 15 down to 1). Let me verify with a known valid CNS: 116 6458 7435 0001? Hmm, I don't have a memorized valid CNS. The commonly cited algorithm:

```python
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    soma = sum(int(d) * (15 - i) for i, d in enumerate(cns))
    return soma % 11 == 0
```

Yes, this is the widely used algorithm. Good.

CPF validation: standard mod 11 with weights 10..2 for first DV and 11..2 for second.

**Discriminators (Manchester):** Each discriminator has a level. The engine evaluates all and takes the highest (most severe) priority.

Design: a list of rules, each rule = (condition function, NivelRisco, discriminator name, justification, recommended action, CIAP-2 code optional).

I'll implement as dataclass-like rule objects:

```python
@dataclass(frozen=True, slots=True)
class RegraDiscriminador:
    nome: str
    nivel: NivelRisco
    descricao: str
    condicao: Callable[[PacienteTriagem], bool]
    conduta: str
    ciap2: str | None = None
```

Then engine iterates rules, collects triggered, picks max severity.

**Severity ordering:** define `ORDEM_SEVERIDADE: dict[NivelRisco, int]` or use enum ordering. I'll add a method `peso` property.

**Engine class:**

```python
class MotorTriagemManchester:
    def __init__(self, regras: tuple[RegraDiscriminador, ...] = REGRAS_PADRAO): ...
    def classificar(self, paciente: PacienteTriagem) -> ResultadoTriagem: ...
```

**ResultadoTriagem:**

```python
class ResultadoTriagem(BaseModel):
    nivel: NivelRisco
    tempo_maximo_espera_min: int
    discriminadores: list[DiscriminadorAtendido]
    justificativa: str
    condutas: list[str]
    ciap2_sugeridos: list[str]
    soap_subjetivo: str
    soap_avaliacao: str
    requer_reavaliacao_min: int | None
    pontuacao: float  # risk score
```

**Vital sign rules (adults):**

- SpO2 < 90 → VERMELHO ("Hipoxemia grave")
- SpO2 90–93 → LARANJA ("Hipoxemia")
- SpO2 94–95 with dyspnea → AMARELO
- SBP < 90 → VERMELHO (choque)
- SBP 90–99 → LARANJA (hipotensão)
- SBP ≥ 180 or DBP ≥ 110 with symptoms (chest pain, neuro deficit, headache) → LARANJA (crise hipertensiva); without symptoms → AMARELO
- SBP ≥ 220 → LARANJA/VERMELHO
- HR < 40 → VERMELHO; 40–49 → LARANJA; > 130 → VERMELHO; 120–130 → LARANJA
- RR < 8 → VERMELHO; > 30 → VERMELHO; 25–30 → LARANJA
- Temp < 35 → LARANJA (hipotermia); ≥ 41 → LARANJA; 39.5–41 with red flags → AMARELO/LARANJA
- Glasgow ≤ 8 → VERMELHO; 9–12 → LARANJA; 13 → AMARELO
- AVPU: U → VERMELHO; P → VERMELHO; V → LARANJA
- Glucose < 50 → VERMELHO; 50–69 → LARANJA; > 300 → LARANJA; 250–300 → AMARELO
- Pain ≥ 8 → at least AMARELO; 7 with sentinel → LARANJA

**Sentinel complaint rules:**

- DOR_TORACICA + (sudorese/irradiação/dor em aperto + SpO2<95 or age>40...) → VERMELHO if unstable vitals, LARANJA baseline. Actually classic MTS: chest pain — "Pain in chest" discriminator: Red if hemodynamically unstable; Orange if "pain radiating to arm/shoulder, sweating, nausea" (typical of ACS); Yellow otherwise.
- DISPNEIA grave: cannot speak full sentences / SpO2 < 92 → VERMELHO; severe but stable → LARANJA; mild → AMARELO/VERDE.
- DEFICIT_NEUROLOGICO (FAST positive) → VERMELHO (janela terapêutica AVC).
- SANGRAMENTO_GRAVE → VERMELHO; moderate → LARANJA.
- REACAO_ALERGICA with airway involvement → VERMELHO.
- CONVULSAO ativa → VERMELHO.
- PERDA_CONSCIENCIA → VERMELHO.
- CEFALEIA_BRUSCA ("pior dor de cabeça da vida") → LARANJA/VERMELHO.
- GESTACAO: gestante with bleeding/pain → VERMELHO; gestante with BP ≥ 140/90 + proteinuria symptoms → LARANJA (pré-eclâmpsia).

For chest pain characteristics, I'll add a sub-model:

```python
class CaracteristicasDorToracica(BaseModel):
    em_aperto: bool = False
    irradia_braco_mandibula: bool = False
    sudorese: bool = False
    nausea: bool = False
    inicio_brusco: bool = False
    esforco: bool = False
    duracao_min: int | None
```

And dyspnea severity:

```python
class CaracteristicasDispneia(BaseModel):
    fala_entrecortada: bool = False
    uso_musculatura_acessoria: bool = False
    cianose: bool = False
    inicio_brusco: bool = False
    ortopneia: bool = False
```

**Age adjustments:** For infants (idade_meses < 60 i.e. < 5 years), thresholds differ: HR higher normal, RR higher, temp ≥ 38 in <3 months → LARANJA/VERMELHO. I'll implement a simplified pediatric adjustment: if age < 2 months and temp ≥ 38 → VERMELHO (fever in neonate). If < 5 years, HR > 180 or < 80 → LARANJA/VERMELHO. Keep it manageable but present.

I'll implement pediatric rules as separate rule set applied when `idade_meses` provided and < 60.

**CIAP-2 mapping:**

- DOR_TORACICA → K01 (K01 "Pain/tension in chest" — actually K01 is "Chest pain"), K74 (Ischemic heart disease/infarction)
- DISPNEIA → R02 (Shortness of breath/dyspnea), R72 (heart failure)
- DEFICIT_NEUROLOGICO → N99 (Stroke), K90 (TIA)
- SANGRAMENTO_GRAVE → depends; use A99? Hmm. CIAP-2: B80 "Blood disorder, other"? For bleeding: D80? Let me use generic: A80? Actually CIAP-2 codes: 
  - A03 fever
  - K01 chest pain
  - K74 acute myocardial infarction
  - R02 dyspnea
  - R05 cough
  - N01 headache
  - N99 stroke
  - D01 abdominal pain
  - U71 urinary tract infection
  - F... eye
  - S... skin
  - T... endocrine
  - B... blood
  - B80 "Blood disorder, other