The user wants me to create a clinical decision support engine and drug interaction alert system for a telemedicine platform called MedIA, specifically for doctors working from home office. This is for the Brazilian SUS (Unified Health System) context.

Let me plan the implementation:

1. **File to create**: `backend/app/services/copiloto_clinico.py`

2. **Requirements**:
   - Drug interaction analyzer (e.g., Fluoxetine + Tramadol, Enalapril + Spironolactone)
   - Allergy alerts from patient records before prescribing
   - Automatic conduct suggestions based on Ministry of Health / SUS protocols
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and pytest test coverage

Let me design this properly:

**Architecture:**

1. **Pydantic models (schemas)**:
   - `Medicamento` (drug with active ingredient, dose, route)
   - `PacienteContexto` (patient with CNS, CPF, allergies, conditions, age, weight, renal function)
   - `PrescricaoContexto` (prescription context)
   - `AlertaInteracao` (interaction alert with severity)
   - `AlertaAlergia` (allergy alert)
   - `SugestaoConduta` (conduct suggestion with protocol reference)
   - `ResultadoAnalise` (full analysis result)

2. **Severity levels** (following standard drug interaction classification):
   - `CONTRAINDICADA` (contraindicated)
   - `GRAVE` (severe)
   - `MODERADA` (moderate)
   - `LEVE` (mild)

3. **Interaction database**: A curated knowledge base of common interactions in Brazilian primary care:
   - Fluoxetina + Tramadol → Serotonin syndrome risk (GRAVE/CONTRAINDICADA)
   - Enalapril + Espironolactona → Hyperkalemia risk (GRAVE/MODERADA)
   - Warfarina + AAS → bleeding
   - Metformina + contraste iodado
   - IECA + AINE
   - Sinvastatina + Claritromicina (CYP3A4)
   - ISRS + IMAO
   - Digoxina + Furosemida (hypokalemia)
   - Lítio + AINE/ISRS
   - Carbamazepina + anticoncepcionais
   - etc.

4. **Allergy checking**: Cross-reference prescribed drug class/active ingredient against patient's recorded allergies (e.g., allergy to penicillin → alert for amoxicilina)

5. **Conduct suggestions**: Based on MS/SUS protocols:
   - Hipertensão (CADERNOS DA ATENÇÃO BÁSICA)
   - Diabetes
   - Depression (PCDT)
   - etc.

6. **SOAP method support**: The analysis should integrate with SOAP notes.

7. **SQLAlchemy 2.0 models**: For persisting alerts/audit trail.

8. **Validation**: CNS validation (algorithm), CPF validation.

Let me write the code:

```python
# backend/app/services/copiloto_clinico.py
```

I need to think about the structure. Since this is a service module, I'll include:

- Pydantic schemas (v2 with strict typing)
- SQLAlchemy 2.0 models (Mapped, mapped_column style)
- The interaction knowledge base
- The allergy checker
- The conduct suggestion engine
- CNS/CPF validators
- Enum types

For SQLAlchemy 2.0 style:
```python
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
```

For Pydantic v2:
```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
```

Let me think about the interaction knowledge base structure:

```python
@dataclass(frozen=True)
class InteracaoMedicamentosa:
    substancias: frozenset[str]  # active ingredients (lowercase)
    severidade: SeveridadeInteracao
    mecanismo: str
    descricao: str
    conduta: str
    referencia: str  # source like ANVISA, bula, etc.
```

The matching should be by active ingredient (substância), normalized (lowercase, strip accents).

Key interactions to include (with real clinical basis):

1. **Fluoxetina + Tramadol**: Both increase serotonin → serotonin syndrome. Severe. Fluoxetine inhibits CYP2D6 which metabolizes tramadol, increasing tramadol levels. CONTAINDICADA/GRAVE.

2. **Enalapril + Espironolactona**: ACE inhibitor reduces aldosterone + potassium-sparing diuretic → hyperkalemia. GRAVE. Monitor potassium.

3. **ISRS + IMAO** (e.g., fluoxetina + tranilcipromina): serotonin syndrome, contraindicated, need washout period (2 weeks, 5 weeks for fluoxetine).

4. **Warfarina + AAS/AINS**: bleeding risk. GRAVE.

5. **Metformina + contraste iodado**: lactic acidosis risk, suspend metformin 48h before/after.

6. **IECA/AARA + AINE**: reduced antihypertensive effect + renal function risk. MODERADA.

7. **Sinvastatina + claritromicina/eritromicina/itraconazol**: CYP3A4 inhibition → rhabdomyolysis. GRAVE.

8. **Digoxina + furosemida**: hypokalemia → digoxin toxicity. MODERADA/GRAVE.

9. **Lítio + AINE / IECA / tiazídicos**: increased lithium levels. GRAVE.

10. **Lítio + ISRS**: serotonin/lithium toxicity. MODERADA/GRAVE.

11. **Carbamazepina + anticoncepcionais hormonais**: enzyme induction → contraceptive failure. GRAVE.

12. **AINE + anticoagulante oral direto (DOAC)**: bleeding.

13. **Ciprofloxacino + corticoide**: tendon rupture risk. MODERADA.

14. **Metformina + álcool**: lactic acidosis.

15. **Benzodiazepínico + opioides**: respiratory depression. GRAVE (FDA black box).

16. **Espironolactona + suplemento de potássio**: hyperkalemia.

17. **Rifampicina + anticoncepcional / warfarina**: enzyme induction.

18. **AAS + ibuprofeno**: ibuprofen reduces aspirin cardioprotective effect. MODERADA/LEVE.

19. **Levotiroxina + cálcio/ferro**: reduced absorption. LEVE/MODERADA.

20. **Omeprazol + clopidogrel**: CYP2C19 inhibition. MODERADA.

Allergy classes:
- Penicilinas (amoxicilina, ampicilina, penicilina benzatina/procaína) → cross-reactivity with cefalosporinas (partial)
- Sulfas (sulfametoxazol-trimetoprim)
- AINEs
- Iodo/contraste

Conduct suggestions based on MS protocols (Protocolos da Atenção Básica / Linhas de Cuidado):
- Hipertensão arterial sistêmica: measure BP, classify, lifestyle, losartana/enalapril per PCDT
- Diabetes mellitus tipo 2: metformina first line, HbA1c targets
- Depressão: PHQ-9, fluoxetina/sertralina first line per PCDT de Saúde Mental
- Dor crônica
- Faringite/amigdalite: Centor score
- etc.

The conduct suggestion engine should take a diagnosis (CID-10 or CIAP-2) + patient context and return protocol-based suggestions.

Let me also include SOAP integration: the analysis result can be attached to a SOAP note (S: subjective, O: objective, A: assessment, P: plan). The copiloto primarily supports "A" (assessment) and "P" (plan).

CNS validation algorithm:
- CNS must be 15 digits
- First digit: 1, 2, 7, 8, 9 (or starts with 7,8,9 for temporary)
- Validation: if starts with 1 or 2: sum of digits × weights (15,14,13...) mod 11 == 0
- If starts with 7, 8, 9: different algorithm (multiply by weights, sum, mod 11, check)

Actually the CNS validation:
- For cards starting with 1, 2: peso = (15 - position), sum = Σ digit × peso, if sum % 11 == 0 → valid
- For cards starting with 7, 8, 9: sum = Σ digit × (15 - position), resto = sum % 11, dv = 11 - resto, if dv == 11 → dv = 0, if dv == 10 → dv = 'P'... Actually the last digit can be P or... Let me recall.

The CNS validation algorithm (official from DATASUS):
1. Must have 15 digits
2. First character must be 1, 2, 7, 8, or 9
3. If first is 1 or 2: 
   - soma = Σ (digit_i × peso_i) where peso = 15, 14, 13, ..., 1
   - valid if soma % 11 == 0
4. If first is 7, 8, or 9:
   - soma = Σ (digit_i × peso_i), peso = 15..1
   - resto = soma % 11
   - dv = 11 - resto
   - if dv == 11: dv = 0
   - if dv == 10: dv = 'P' (last char must be P)
   - check last char matches

CPF validation: standard mod-11 check digits.

Now for the SQLAlchemy models — I'll create an audit/alert persistence model:

```python
class AlertaClinicoRegistro(Base):
    __tablename__ = "alertas_clinicos"
    id: Mapped[uuid.UUID] = mapped_column(...)
    paciente_id: Mapped[str]
    cns: Mapped[str | None]
    tipo_alerta: Mapped[str]
    severidade: Mapped[str]
    descricao: Mapped[str]
    ...
```

And a prescription record model maybe.

Let me structure the module:

```python
"""
copiloto_clinico.py — Motor de Apoio à Decisão Clínica (CDS) e Alertas de Interação Medicamentosa
...
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import StrEnum
from typing import Any, Final, Iterable, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import String, Text, DateTime, Enum as SAEnum, Index, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
```

Wait — should I put SQLAlchemy models in the service file? The task says create `backend/app/services/copiloto_clinico.py` with the analyzer. The architecture guidelines say SQLAlchemy 2.0. I think including the persistence models for the audit trail in this file is acceptable for a self-contained deliverable, but typically models go in `models/`. Given the instruction is to create this single file, I'll include the SQLAlchemy models needed for the service (audit trail) in the file, or import them. To keep it self-contained and testable, I'll define them in the file with a note. Actually, better practice: define the ORM models in the service module since the task only asks for this file. I'll make it self-contained but organized.

Hmm, but a cleaner approach: the service file contains schemas + knowledge base + engine + ORM models for audit. Tests will cover validators, interaction detection, allergy detection, conduct suggestions.

Let me now write the full implementation.

```python
from __future__ import annotations

import re
import unicodedata
import uuid
from collections.abc import Iterable, Sequence
from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Any, ClassVar, Final

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
```

**Enums:**

```python
class SeveridadeInteracao(StrEnum):
    CONTRAINDICADA = "contraindicada"
    GRAVE = "grave"
    MODERADA = "moderada"
    LEVE = "leve"


class TipoAlerta(StrEnum):
    INTERACAO_MEDICAMENTOSA = "interacao_medicamentosa"
    ALERGIA = "alergia"
    CONTRAINDICACAO_CLINICA = "contraindicacao_clinica"
    DOSE_ALERTA = "dose_alerta"
    PROTOCOLO = "protocolo"


class OrigemRecomendacao(StrEnum):
    PCDT_MS = "pcdt_ministerio_da_saude"
    CADERNOS_AB = "cadernos_atencao_basica"
    PROTOCOLO_AP = "protocolo_aps_sus"
    BULA_ANVISA = "bula_anvisa"
    UP_TO_DATE_CONSENSO = "consenso_nacional"
```

**Normalization helper:**

```python
def _normalizar(texto: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto.strip().lower())
```

**Pydantic schemas:**

```python
class MedicamentoPrescrito(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    nome_comercial: str | None = None
    substancia: str  # active ingredient
    concentracao: str | None = None
    via: str = "oral"
    dose: str | None = None
    posologia: str | None = None
```

```python
class AlergiaRegistrada(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    substancia_ou_classe: str
    tipo_reacao: str | None = None
    gravidade_previa: str | None = None  # leve/moderada/grave/anafilaxia
    cid10_relacionada: str | None = None  # e.g. Z88.0
```

```python
class PacienteContexto(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    id_paciente: str
    nome: str
    cns: str | None = None
    cpf: str | None = None
    data_nascimento: date
    sexo: str  # 'M' | 'F' | 'I'
    peso_kg: float | None = Field(default=None, gt=0)
    alergias: tuple[AlergiaRegistrada, ...] = ()
    comorbidades_cid10: tuple[str, ...] = ()
    medicamentos_em_uso: tuple[MedicamentoPrescrito, ...] = ()
    tfge_estimada: float | None = None  # mL/min/1.73m²
    gestante: bool = False
    lactante: bool = False
```

Validators for CNS/CPF.

```python
class PrescricaoContexto(BaseModel):
    medicamentos: tuple[MedicamentoPrescrito, ...]
    indicacao_cid10: str | None
    indicacao_ciap2: str | None
    ...
```

**Alerts:**

```python
class AlertaClinico(BaseModel):
    tipo: TipoAlerta
    severidade: SeveridadeInteracao | None
    titulo: str
    descricao: str
    conduta_recomendada: str
    referencia: str
    substancias_envolvidas: tuple[str, ...] = ()
```

**Conduct suggestion:**

```python
class SugestaoConduta(BaseModel):
    diagnostico_cid10: str | None
    diagnostico_ciap2: str | None
    titulo_protocolo: str
    conduta: str  # SOAP "P" (plan)
    farmacoterapia: tuple[str, ...]
    nao_farmacologica: tuple[str, ...]
    exames_complementares: tuple[str, ...]
    sinais_alerta_encaminhamento: tuple[str, ...]
    referencia: str
```

**Result:**

```python
class ResultadoAnaliseClinica(BaseModel):
    id_analise: uuid.UUID
    momento: datetime
    paciente: PacienteContexto
    alertas: tuple[AlertaClinico, ...]
    sugestoes_conduta: tuple[SugestaoConduta, ...]
    aprovado_para_prescricao: bool  # False if contraindicated/severe unresolved
    resumo_soap: str | None
```

**Knowledge base — interactions:**

I'll define a frozen dataclass or Pydantic frozen model for each interaction. Matching by normalized active ingredient names, including synonyms (e.g., "aas" ↔ "acido acetilsalicilico", "ieca" class...). Actually class-based matching is complex; I'll use explicit ingredient pairs plus a class map for some (e.g., any NSAID: ibuprofeno, nimesulida, cetoprofeno, diclofenaco, naproxeno, piroxicam, meloxicam, etoricoxibe; any SSRI: fluoxetina, sertralina, paroxetina, escitalopram, citalopram, fluvoxamina).

Design: each interaction rule has groups of "termos" — sets of substances that satisfy the group. An interaction triggers when substances from ≥2 distinct groups are present. E.g., ISRS group + opioid group (tramadol, petidina...). This handles Fluoxetina + Tramadol via ISRS group + tramadol.

```python
@dataclass(frozen=True, slots=True)
class RegraInteracao:
    id_regra: str
    grupos: tuple[frozens