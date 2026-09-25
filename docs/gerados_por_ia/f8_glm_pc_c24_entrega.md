The user wants me to create a messaging and preventive alerts service for vaccines/consultations (C24 task). This is a Brazilian health system (SUS/APS - Atenção Primária à Saúde) context. Let me analyze the requirements:

1. **File to create**: `backend/app/services/mensageria_preventiva.py`
2. **Features**:
   - Automatic reminder generator for scheduled teleconsultations (WhatsApp/SMS mock)
   - Active search identifier for children with delayed vaccines
   - Active search for diabetics without follow-up for more than 90 days

3. **Architecture guidelines**:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me think about the domain:

**CIAP-2 codes relevant:**
- Teleconsulta: could use A97 (sem diagnóstico/consulta administrativa) or specific codes
- Vaccination: A95 (Imunização/vacinação)
- Diabetes: T90 (Diabetes não insulino-dependente) / T89 (Diabetes insulino-dependente) - in CIAP-2, T90 is "Diabetes não-insulino-dependente" and T89 is "Diabetes insulino-dependente"
- Actually in CIAP-2: T89 = Diabetes insulino-dependente, T90 = Diabetes não-insulino-dependente
- Child health check: A44? Actually "Exame de saúde/cheque-up" is A44? Let me recall: A44 = "Exame de saúde/cheque-up". Child development monitoring... 
- For vaccines delayed: A95 (Imunização/vacinação) is the CIAP-2 code for immunization

**CID-10 codes:**
- E10: Diabetes mellitus insulino-dependente (tipo 1)
- E11: Diabetes mellitus não insulino-dependente (tipo 2)
- Z24: Necessidade de imunização (Z23 in ICD-10 is "Necessidade de imunização contra doenças bacterianas únicas", Z24...). Actually Z23 = Necessidade de imunização. Z20-Z29 are persons with potential health hazards related to communicable diseases.

**CNS/CPF validation:**
- CNS (Cartão Nacional de Saúde): 15 digits, validation algorithm - starts with 1, 2, 7, 8, or 9. The validation: for cards starting with 1 or 2 (definitive) or 7/8/9 (provisional), there's a checksum algorithm.
- CPF: 11 digits with check digits algorithm.

**CNS validation algorithm:**
```
def validate_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    # CNS must start with 1, 2, 7, 8 or 9
    if cns[0] not in '12789':
        return False
    # For 1/2: standard checksum; for 7/8/9: same algorithm
    total = 0
    weights = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    for digit, weight in zip(cns, weights):
        total += int(digit) * weight
    return total % 11 == 0
```

Wait, the CNS validation: the sum of each digit multiplied by weights (15 down to 1) must be divisible by 11. Yes, that's the standard algorithm.

**CPF validation:**
Standard check digit algorithm.

**Vaccine schedule (PNI - Programa Nacional de Imunizações):**
Key vaccines for children:
- BCG: at birth
- Hepatite B: at birth
- Penta (DTP/Hib/HepB): 2, 3, 4 months, reforço 15 months
- VIP/VOP (polio): 2, 3, 4 months, reforços 15 months and 4 years
- Pneumo 10: 2, 4 months, reforço 12 months
- Rotavírus: 2, 3 months
- Meningo C: 3, 5 months, reforço 12 months
- Tríplice viral (SCR): 12 months, reforço 15 months (D2)
- Varicela: 15 months
- DTP reforço: 4 years
- Influenza: annual from 6 months

For the service, I'll create a simplified vaccine schedule with key milestones by age in months:
- 2 months: Penta D1, VIP D1, Pneumo10 D1, Rotavírus D1
- 3 months: Penta D2, VIP D2, MenC D1, Rotavírus D2
- 4 months: Penta D3, VIP D3, Pneumo10 D2, MenC D2
- 6 months: Influenza (annual)
- 9 months: Febre amarela (in endemic areas)
- 12 months: SCR D1, Pneumo10 reforço, MenC reforço
- 15 months: SCR D2, Varicela, Penta reforço (VOP?), VIP reforço
- 48 months (4 years): DTP reforço, VIP reforço, Varicela reforço (2 doses now recommended at 15m and 48m? Actually varicela: 1 dose at 15 months; in 2020+ schedule, varicela reforço at 4 years? Let me keep it simple)

I'll create a simplified but realistic schedule. The key point is the service logic, not perfect PNI fidelity, but I should be reasonably accurate.

**Diabetes follow-up:**
- CID-10: E10 (type 1), E11 (type 2), E12, E13, E14
- CIAP-2: T89 (insulin-dependent), T90 (non-insulin-dependent)
- Follow-up: consultations at least every 90 days (quarterly) per PCDT (Protocolo Clínico e Diretrizes Terapêuticas) - for diabetes, follow-up consultations typically every 3 months (90 days). The task says "diabéticos sem acompanhamento há mais de 90 dias" - so flag patients whose last diabetes-related consultation/record is > 90 days ago.

**Teleconsultation reminders:**
- Generate reminders at intervals: e.g., 48h before, 24h before, 1h before (or configurable)
- Channels: WhatsApp, SMS (mock)
- Message templates with LGPD-compliant content (no sensitive diagnosis info in messages, just appointment details)
- Include teleconsultation link, date/time, professional name

**LGPD considerations:**
- Consent tracking (consentimento) for messaging
- Data minimization: don't include diagnosis in messages
- Opt-out capability

**Architecture:**

Let me design the module:

```
backend/app/services/mensageria_preventiva.py
```

Components:
1. **Enums**: `CanalMensagem` (WHATSAPP, SMS), `TipoMensagem` (LEMBRETE_TELECONSULTA, ALERTA_VACINA_ATRASADA, ALERTA_DIABETES_SEGUIENTO), `StatusMensagem` (PENDENTE, ENVIADA, FALHA, CANCELADA), `PrioridadeAlerta` (BAIXA, MEDIA, ALTA, CRITICA)

2. **Pydantic models**:
   - `PacienteBase` / schemas: CNS, CPF, nome, data_nascimento, telefone, consentimento
   - `Teleconsulta`: id, paciente, data_hora, profissional, especialidade, link, status
   - `LembreteTeleconsulta`: generated reminder
   - `RegistroVacina`: vaccine name, dose, date
   - `AlertaVacinaAtrasada`: patient, missing vaccines, days delayed
   - `AlertaDiabetes`: patient, days since last consultation, CID/CIAP
   - `MensagemOutbox`: message to send

3. **SQLAlchemy 2.0 models** (typed with Mapped[]):
   - `PacienteModel`
   - `TeleconsultaModel`
   - `VacinacaoModel` (registro de vacinação)
   - `CondicaoCronicaModel` (diabetes diagnosis)
   - `MensagemModel` (outbox)
   - `RegistroContatoModel` (contact log)

4. **Service class**: `ServicoMensageriaPreventiva`
   - `gerar_lembretes_teleconsulta(janela_horas)` → finds teleconsultations in window, generates reminders
   - `identificar_vacinas_atrasadas(paciente)` / `varrer_criancas_vacinas_atrasadas()`
   - `identificar_diabeticos_sem_acompanhamento(dias=90)`
   - `enviar_mensagem(mensagem)` → mock dispatch (WhatsApp/SMS)
   - `executar_ciclo_preventivo()` → orchestrates everything

5. **Validators**: CNS, CPF, telefone E.164-ish for BR (+55)

6. **Message templates**: SOAP-ish? The task mentions SOAP method — SOAP is for clinical notes (Subjetivo, Objetivo, Avaliação, Plano). For messages, maybe the "Plano" part informs the message. I can include a SOAP reference in alerts: e.g., the alert includes a suggested "Plano" (P) for the healthcare team. That's a nice touch: alerts generated for the care team include SOAP-oriented fields, while patient messages are lay-language.

Let me think about how to structure this well. The task says "crie backend/app/services/mensageria_preventiva.py" — a single file. But tests need to be created too ("cobertura de testes automatizados com pytest"). I should provide:
- The main service file
- A test file (e.g., `backend/tests/test_mensageria_preventiva.py`)
- Maybe supporting files (models, schemas) — but the instruction says create the service file. To keep it self-contained and executable, I could put everything in the service file (SQLAlchemy models + Pydantic schemas + service), or reference existing app structure.

Given it's a "coder" agent task, I'll deliver:
1. `backend/app/services/mensageria_preventiva.py` — complete, self-contained (with imports from a hypothetical `app.core` for base? Better to make it self-contained but with clear extension points). Hmm — in a real project, there'd be `app/models/paciente.py`, `app/db/session.py`, etc. Since I don't know the existing structure, I'll make the file self-contained: define SQLAlchemy models inside (or import from `app.models` with fallback?). Self-contained is safer for tests to run. But mixing models into a service file is not great architecture... However, the task explicitly says create this one file. I'll structure it with clear sections and note that in production these would be split. Actually, let me reconsider: the guidelines say "SQLAlchemy 2.0" — I need models to query. I'll define them in the service module with `DeclarativeBase`, and tests will use in-memory SQLite.

Actually, a cleaner approach: define the SQLAlchemy models in the same file under a clear section "Modelos de persistência (ORM)" with a comment that they can be moved to `app/models/`. This keeps the deliverable runnable and testable.

Let me now design in detail.

### Constants / Domain data

```python
AGENDA_VACINAL_PNI: dict of age thresholds → required vaccines
```

Structure: list of `DoseVacinal` records: nome, dose (D1, D2, REFORCO), idade_meses (recommended age), janela? For simplicity: each vaccine dose has `idade_meses_limite` — the age by which it should be done (e.g., Penta D1 by 2 months, tolerable up to...). For "atrasada" determination: if child's age >= idade_recomendada + margem_atraso (e.g., 30 days grace), and no record of that vaccine dose → atrasada.

Let me define:

```python
@dataclass(frozen=True) or Pydantic model DoseVacinal:
    nome: str  # "Penta", "VIP", "Pneumo10", "MenC", "SCR", "Varicela", "Rotavírus", "BCG", "Hepatite B", "DTP", "Febre Amarela", "Influenza"
    dose: str  # "D1", "D2", "D3", "REFORCO"
    idade_meses: int  # recommended age
    margem_dias: int = 30  # grace period
```

Schedule (simplified PNI 2024 for < 5 years):
- Nascer: BCG Única (0m), Hepatite B D1 (0m)
- 2m: Penta D1, VIP D1, VOP D1?, Pneumo10 D1, Rotavírus D1
- 3m: Penta D2, VIP D2, MenC D1, Rotavírus D2
- 4m: Penta D3, VIP D3, Pneumo10 D2, MenC D2
- 6m: Influenza (anual, sazonal) — I'll skip influenza from "atrasada" logic since it's seasonal, or include with note. Better skip to avoid false positives; mention in comment.
- 9m: Febre Amarela D1
- 12m: SCR D1, Pneumo10 REFORCO, MenC REFORCO, Hepatite A D1
- 15m: SCR D2, Varicela D1, Penta REFORCO (D4), VIP REFORCO (D4?) — actually VOP reforço at 15m? PNI: 15 months: DTP reforço? No — 15 months: SCR D2, VOP reforço, Penta D4 (reforço), Varicela D1, MenC reforço is at 12m, Pneumo10 reforço at 12m. Let me check the official PNI calendar (Brazil, 2023-2024):

Official Calendário Nacional de Vacinação — Criança:
- Ao nascer: BCG (dose única), Hepatite B (dose única — actually dose ao nascer)
- 2 meses: Hepatite B 2ª dose? No — Hepatite B is now in Penta. Current: 2 months: Penta (D1), VIP (D1), Pneumo10 (D1), Rotavírus (D1), MenC? No, MenC at 3 and 5 months.
- 2 meses: Penta D1, VIP D1, Pneumo 10 D1, Rotavírus D1
- 3 meses: Penta D2, VIP D2, MenC D1, Rotavírus D2
- 4 meses: Penta D3, VIP D3, Pneumo 10 D2, MenC D2
- 5 meses: MenC D3? — In the current calendar: MenC (conjugada) 3 meses D1, 5 meses D2. Hmm, older calendar had 3 and 5 months. Newer: 3, 5 months + reforço 12 months. Some references say 3 and 5. Let me use 3 and 5.
- 6 meses: Influenza (anual/sazonal)
- 9 meses: Febre Amarela D1
- 12 meses: SCR (tríplice viral) D1, Pneumo 10 reforço, MenC reforço, Hepatite A D1
- 15 meses: SCR D2, VOP reforço? — Current: 15 meses: DTP (D1 reforço)? Let me recall the official: 
  - 15 meses: SCR D2, Varicela D1, Penta D4 (1º reforço), VIP D4? 
  - Official 2024: "15 meses: Penta (D4 – 1º reforço), VOP (reforço), SCR (D2), Varicela (D1)"
- 4 anos (48 meses): DTP (2º reforço), VIP (reforço), Varicela (D2? — added reforço at 4 years in recent calendar), SCR (reforço? no)

I'll use a reasonable simplified version and document it. The exact fidelity isn't the core of the task; the logic is. I'll include: BCG, HepB (0m), Penta D1-D3 (2,3,4), VIP D1-D3 (2,3,4), Pneumo10 D1-D2 (2,4), Rotavírus D1-D2 (2,3), MenC D1-D2 (3,5), Febre Amarela (9), Hepatite A (12), SCR D1 (12), Pneumo10 reforço (12), MenC reforço (12), Penta reforço (15), VOP reforço (15), SCR D2 (15), Varicela (15), DTP reforço (48), VIP reforço (48).

For matching administered vaccines: `RegistroVacinacao` has nome_vacina and dose; matching by normalized name + dose. I'll normalize (uppercase, strip accents).

### Diabetes logic

- Patient has chronic condition with CID-10 in {E10, E11, E12, E13, E14} (or CIAP T89/T90).
- Last follow-up: last consultation (Teleconsulta or atendimento) with those codes, or last `RegistroAcompanhamento` (e.g., HbA1c test, nursing visit). I'll model `RegistroAcompanhamento` with tipo (CONSULTA, EXAME, VISITA_DOMICILIAR) and data.
- If days since last > 90 → alert. Severity: >90 = ALTA, >180 = CRITICA? Task says "mais de 90 dias" — I'll add tiers: 91–180 ALTA, >180 CRITICA, and upcoming (75–90) MEDIA for proactive scheduling. Keep it simple: alert when >90; priority based on how late.

### Teleconsultation reminders

- `TeleconsultaModel`: agendada for datetime, status AGEND