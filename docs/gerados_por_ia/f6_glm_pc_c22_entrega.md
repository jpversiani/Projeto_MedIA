The user wants me to create a Clinical Decision Support Engine and Drug Interaction Alerts module (C22) for a medical system called MedIA. This is for a doctor working from Home Office.

Requirements:
1. Create `backend/app/services/copiloto_clinico.py`
2. Drug interaction analyzer (examples: Fluoxetine + Tramadol, Enalapril + Spironolactone)
3. Allergy alerts from patient records before prescribing
4. Automatic conduct suggestions based on Brazilian Ministry of Health / SUS protocols

Architecture guidelines:
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

The response should be in Portuguese since the request is in Portuguese.

Let me design this properly:

1. **Pydantic v2 models** for:
   - Medicamento (drug)
   - InteracaoMedicamentosa (drug interaction)
   - Alergia (allergy)
   - Paciente (patient with CNS/CPF validation)
   - Prescricao (prescription)
   - Alerta (alert)
   - SugestaoConduta (conduct suggestion)
   - AnaliseClinica (clinical analysis result)

2. **SQLAlchemy 2.0 models** for persistence:
   - PacienteModel
   - AlergiaModel
   - PrescricaoModel
   - InteracaoModel (catalog of interactions)

3. **CNS/CPF validation**:
   - CNS validation algorithm (Brazilian national health card number)
   - CPF validation algorithm

4. **Drug interaction engine**:
   - Knowledge base of interactions with severity levels
   - Fluoxetine + Tramadol (serotonin syndrome risk - major)
   - Enalapril + Spironolactone (hyperkalemia risk - major)
   - Other common interactions: warfarin + aspirin, MAOIs, etc.

5. **Allergy checking**:
   - Cross-reactivity (e.g., penicillin allergy → caution with cephalosporins)
   - Check before prescribing

6. **Conduct suggestions based on MS/SUS protocols**:
   - Hypertension protocol (CAD/Ministério da Saúde)
   - Diabetes protocol
   - Common conditions

7. **SOAP method support**

8. **CIAP-2 and CID-10 codes**

Let me write the code:

```python
# backend/app/services/copiloto_clinico.py
```

I'll structure it as a comprehensive service module. Since they want pytest coverage too, I should include a test file.

Let me think about CNS validation:
- CNS can start with 1, 2, 7, 8, or 9
- Algorithm: sum of digits multiplied by weights from 15 down to 2, mod 11, must equal 0
- For provisional CNS (7, 8, 9), there's a different algorithm

CNS validation algorithm:
```
def validar_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in '123789':
        return False
    # For definitive CNS (starting 1, 2): sum = sum(digit * weight) where weights go 15 to 2
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

For provisional (7,8,9), the algorithm is different - it uses a different calculation. Actually the standard algorithm:
- For CNS starting with 1, 2: sum of (digit * weight from 15 to 2) % 11 == 0
- For CNS starting with 7, 8, 9: convert letters... Actually provisional CNS uses a different scheme where you replace... Let me recall.

The provisional CNS validation: for numbers starting with 7, 8, or 9, the algorithm involves converting to a sequence... Actually the official algorithm:

```
soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
resto = soma % 11
if resto == 0: valid
```

This works for 1 and 2. For 7, 8, 9 (provisional), the algorithm is:
```
soma = sum(int(cns[i]) * (15 - i) for i in range(15))
if soma % 11 == 0: valid
```
Hmm, actually I believe the same weighted sum works for all. Let me check: the official Ministério da Saúde algorithm for CNS validation:

```python
def valida_cns(cns):
    if len(cns) != 15:
        return False
    if cns[0] not in ['1', '2', '7', '8', '9']:
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

Yes, this is the standard algorithm that works for both definitive and provisional. Some implementations handle provisional differently but this weighted-sum mod 11 is the commonly cited official one.

CPF validation:
- Standard check digit algorithm with weights 10..2 and 11..2

Now for the drug interaction knowledge base. Key interactions to include:

1. **Fluoxetina + Tramadol** - GRAVE (major) - Síndrome serotoninérgica - both increase serotonin. Mechanism: SSRI + opioid with SNRI activity. Conduct: avoid combination, monitor for agitation, hyperthermia, clonus, etc.

2. **Enalapril + Espironolactona** - GRAVE - Hipercalemia - ACE inhibitor + potassium-sparing diuretic. Conduct: monitor potassium, renal function.

3. **Warfarina + AAS** - GRAVE - bleeding risk

4. **Fluoxetina + IMAO** - CONTRAINDICADA - serotonin syndrome, hypertensive crisis

5. **Metformina + contraste iodado** - GRAVE - lactic acidosis risk

6. **Digoxina + Furosemida** - MODERADA - hypokalemia increases digoxin toxicity

7. **Sinvastatina + Claritromicina** - GRAVE - CYP3A4 inhibition → rhabdomyolysis

8. **AAS + Ibuprofeno** - MODERADA - reduced antiplatelet effect

9. **Levotiroxina + Omeprazol** - MODERADA - reduced absorption

10. **Lítio + IECA** - GRAVE - increased lithium levels

Severity levels: CONTRAINDICADA, GRAVE, MODERADA, LEVE

Allergy cross-reactivity:
- Penicilina → Cefalosporinas (cross-reactivity ~1-2%)
- Sulfas
- AINEs (aspirin → other NSAIDs)
- Iodine/contrast

Conduct suggestions based on MS/SUS protocols:
- Hipertensão arterial (CID-10 I10): protocol from Ministério da Saúde - CAD (Caderno de Atenção Básica 37)
- Diabetes (E11): CAD 36
- Depressão (F32/F33): CAD / Linha de Cuidado
- etc.

I'll build a protocol knowledge base with CIAP-2 codes mapped:
- K86 - Hipertensão não complicada (CIAP-2) → CID-10 I10
- T90 - Diabetes não complicado (CIAP-2) → E11
- P76 - Depressão (CIAP-2) → F32
- R05 - Tosse
- A77 - Vírus/síndrome viral

SOAP method: support structuring clinical notes in SOAP format (Subjetivo, Objetivo, Avaliação, Plano).

Let me now write the full module. I'll use Pydantic v2 with strict typing, SQLAlchemy 2.0 style (Mapped, mapped_column, DeclarativeBase).

Structure:

```python
"""..."""
from __future__ import annotations

import re
from datetime import date, datetime
from enum import Enum
from typing import Any, Final

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
```

Enums:
```python
class SeveridadeInteracao(str, Enum):
    CONTRAINDICADA = "CONTRAINDICADA"
    GRAVE = "GRAVE"
    MODERADA = "MODERADA"
    LEVE = "LEVE"

class TipoAlerta(str, Enum):
    INTERACAO_MEDICAMENTOSA = "INTERACAO_MEDICAMENTOSA"
    ALERGIA = "ALERGIA"
    REACAO_CRUZADA = "REACAO_CRUZADA"
    PROTOCOLO = "PROTOCOLO"

class NivelEvidencia(str, Enum):
    ...
```

Pydantic models:
- MedicamentoPrescrito: nome, dosagem, via, frequencia
- Alergia: substancia, tipo, gravidade, reacao
- PacienteContexto: id, nome, cns, cpf, alergias, comorbidades, medicamentos_atuais, idade, peso, funcao_renal...
- AnaliseResult: alertas, sugestoes_conduta, aprovada (bool), requer_justificativa

Validators for CNS and CPF.

Knowledge base as module-level constants (frozensets/tuples of dataclasses or dicts).

The service class:
```python
class CopilotoClinico:
    def __init__(self, session: Session | None = None): ...
    
    def analisar_prescricao(self, paciente, novos_medicamentos) -> ResultadoAnalise
    def verificar_alergias(...)
    def verificar_interacoes(...)
    def sugerir_conduta(ciap2 or cid10, contexto) -> list[SugestaoConduta]
    def estruturar_soap(...)
```

Also SQLAlchemy models for persistence: PacienteORM, AlergiaORM, PrescricaoORM, AlertaClinicoORM, InteracaoCatalogoORM.

Let me write the interaction catalog with detailed data:

```python
@dataclass(frozen=True)
class InteracaoCatalogo:
    medicamento_a: str
    medicamento_b: str
    severidade: SeveridadeInteracao
    mecanismo: str
    efeito_clinico: str
    conduta: str
    referencia: str  # e.g., "MS/SUS - Formulário Terapêutico Nacional 2024"
```

Normalization of drug names: lowercase, strip accents, remove spaces/hyphens. Use unicodedata.

```python
def _normalizar(nome: str) -> str:
    nfkd = unicodedata.normalize("NFKD", nome.strip().lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).replace(" ", "").replace("-", "")
```

Interaction lookup: normalize both names, check both orders (a+b, b+a).

Allergy check: normalize allergen and drug; direct match → alert; cross-reactivity map → REACAO_CRUZADA alert.

Cross-reactivity map:
```python
_REACOES_CRUZADAS: dict[str, frozenset[str]] = {
    "penicilina": frozenset({"amoxicilina", "ampicilina", "cefalexina", "ceftriaxona", ...}),
    "sulfametoxazol": ...,
    "aas": frozenset({"ibuprofeno", "naproxeno", "diclofenaco", ...}),
    "codeina": frozenset({"morfina", "tramadol", ...}),
    "iodo": ...
}
```

Protocol knowledge base (MS/SUS):
```python
@dataclass(frozen=True)
class ProtocoloClinico:
    ciap2: str
    cid10: str
    descricao: str
    condutas: tuple[str, ...]
    medicamentos_sugeridos: tuple[str, ...]
    exames: tuple[str, ...]
    referencia: str
    red_flag: tuple[str, ...]  # critérios de encaminhamento
```

Protocols:
1. K86 / I10 - Hipertensão arterial: CAD 37 / Diretrizes 2020 (SBC but MS adopted). Condutas: medidas não farmacológicas (redução sal <5g/dia, atividade física 150min/sem, perda ponderal, etilismo), captopril/enalapril/losartana/anlodipino/hidroclorotiazida (RENIFER - Relação Nacional de Medicamentos Essenciais). Red flags: PA ≥180/110 com sintomas, lesão de órgão-alvo → encaminhar urgência.

2. T90 / E11 - Diabetes tipo 2: CAD 36. Metformina primeira linha (RENIFER), HbA1c alvo <7%, rastreamento retinopatia, pé diabético. Red flags: cetoacidose, úlcera pé infectada.

3. P76 / F32 - Depressão: Linha de Cuidado Saúde Mental / CAD. Psicoterapia + sertralina/fluoxetina (RENIFER), avaliação risco de suicídio. Red flags: risco suicida iminente → encaminhar CAPS/urgência.

4. R05 / J06.9 - Infecção respiratória... Actually R05 is cough. URTI: A77 viral syndrome. Conduta: sintomático, não prescrever antibiótico (stewardship).

5. K29 - Dispepsia: omeprazol, teste H. pylori.

6. D73 - Anemia: ferro.

7. N39 - ITU: nitrofurantoína primeira linha (per protocol), ciprofloxacino alternatives.

Let me include maybe 6-8 protocols to keep it manageable but comprehensive.

Also include drug-condition contraindications? Maybe keep scope focused: interactions, allergies, protocols. Could add a simple renal function check for metformin (e.g., metformina contraindicada se TFG < 30). That's a nice touch — "alertas de segurança adicionais". Let me add a small check: if patient has TFG (eGFR) provided and drug is metformin with TFG < 30 → contraindicated alert. This adds value but also complexity. I'll include it as a compact feature.

SOAP structuring:
```python
class NotaSOAP(BaseModel):
    subjetivo: str
    objetivo: str
    avaliacao: str  # with CIAP-2/CID-10
    plano: str
```
Service method `gerar_rascunho_soap` that assembles a draft from inputs + analysis results.

Now SQLAlchemy 2.0 models:

```python
class Base(DeclarativeBase):
    pass

class PacienteORM(Base):
    __tablename__ = "pacientes"
    id: Mapped[int] = mapped_column(primary_key=True)
    cns: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    cpf: Mapped[str | None] = mapped_column(String(11), unique=True)
    nome_social/nome: Mapped[str] = mapped_column(String(200))
    data_nascimento: Mapped[date]
    alergias: Mapped[list[AlergiaORM]] = relationship(back_populates="paciente", cascade="all, delete-orphan")
    ...

class AlergiaORM(Base):
    __tablename__ = "alergias"
    id, paciente_id FK, substancia, tipo, gravidade, reacao, cid10_opcional

class PrescricaoORM(Base):
    __tablename__ = "prescricoes"
    id, paciente_id, profissional_id, data, medicamentos (JSON or Text), aprovada, justificativa

class AlertaClinicoORM(Base):
    __tablename__ = "alertas_clinicos"
    id, prescricao_id FK, tipo, severidade, mensagem, medicamento_envolvido, reconhecido (bool), data

class InteracaoORM(Base):  # catalog persisted, seeded from constant
    __tablename__ = "catalogo_interacoes"
```

Hmm, should the catalog be in DB or in code? For a decision-support engine, having the catalog seeded in DB allows updates. I'll include the ORM model and a `seed_catalogo` method, but the engine reads from the in-memory constant by default with optional DB overlay. Actually to keep it clean: the CopilotoClinico can accept an optional SQLAlchemy session; if provided, it loads interactions from DB, else uses built-in catalog. Or simpler: built-in catalog is the source of truth, DB persistence is for audit (alertas, prescrições). I'll do: built-in catalog + audit persistence of alerts/prescriptions when session provided.

The service methods:

```python
class CopilotoClinico:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session
        self._interacoes = _carregar_interacoes()

    def analisar_prescricao(self, paciente: PacienteContexto, medicamentos: Sequence[MedicamentoPrescrito], justificativa: str | None = None) -> ResultadoAnalise:
        alertas = []
        alertas += self.verificar_alergias(paciente, medicamentos)
        alertas += self.verificar_interacoes(medicamentos, paciente.medicamentos_atuais)
        alertas += self._verificar_seguranca_adicional(paciente, medicamentos)
        bloqueada = any(a.severidade in (CONTRAINDICADA, GRAVE) and a.tipo == ALERGIA for ...)
        # blocking rule: allergy direct → block unless justified; contraindicated interaction → block unless justified
```

Blocking logic: if alerta.bloqueia_prescricao and no justificativa → status = BLOQUEADA; if justificativa provided → status = PERMITIDA_COM_JUSTIFICATIVA; else LIBERADA.

```python
class StatusPrescricao(str, Enum):
    LIBERADA = "LIBERADA"
    LIBERADA_COM_RESSALVAS = "LIBERADA_COM_RESSALVAS"
    REQUER_JUSTIFICATIVA = "REQUER_JUSTIFICATIVA"
    BLOQUEADA = "BLOQUEADA"
```

Rules:
- Any CONTRAINDICADA interaction or direct allergy → REQUER_JUSTIFICATIVA (or BLOQUEADA if