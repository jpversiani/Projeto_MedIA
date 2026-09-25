The user wants me to create a backend service for preventive messaging and alerts for vaccines/consultations (C16 - likely a capability/feature code in a health system project). This is a Brazilian SUS (Sistema Único de Saúde) / APS (Atenção Primária à Saúde) context.

Requirements:
1. Create `backend/app/services/mensageria_preventiva.py`
2. Features:
   - Automatic reminder generator for scheduled teleconsultations (WhatsApp/SMS mock)
   - Active search identifier for children with delayed vaccines
   - Active search for diabetics without follow-up for more than 90 days
3. Architecture guidelines:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me think about the domain:

**SUS/APS Context:**
- CNS (Cartão Nacional de Saúde) - 15 digits
- CPF - 11 digits
- CIAP-2 codes: 
  - A23 (fever child?), actually let me recall CIAP-2 codes:
    - A: General/Unspecified
    - B: Blood
    - D: Digestive
    - F: Eye
    - H: Ear
    - K: Circulatory
    - L: Musculoskeletal
    - N: Neurological
    - P: Psychological
    - R: Respiratory
    - S: Skin
    - T: Endocrine/Metabolic (T90 - Diabetes!)
    - U: Urological
    - W: Pregnancy
    - X: Female genital
    - Y: Male genital
    - Z: Social
  - T90 = Diabetes non-insulin dependent (Type 2)
  - T91 = Diabetes insulin-dependent (Type 1)... Actually in CIAP-2: T90 is "Diabetes não insulino-dependente" and T91 is "Diabetes insulino-dependente". Let me double check: CIAP-2 T90 = Diabetes não-insulino-dependente, T91 = Diabetes insulino-dependente. Yes.
- CID-10:
  - E10 = Diabetes mellitus insulinodependente (tipo 1)
  - E11 = Diabetes mellitus não-insulino-dependente (tipo 2)
  - E12, E13, E14 variants
  - Z22 = contact/follow-up for infectious disease? Actually Z codes for vaccination: Z23 = "Necessidade de imunização" (Need for immunization against certain diseases)
  - Z00-Z13 for general exams
- PNI (Programa Nacional de Imunizações) - Brazilian vaccination calendar:
  - BCG: at birth
  - Hepatite B: at birth
  - Penta (DTP/HepB/Hib): 2, 4, 6 months
  - VIP/VOP (Poliomielite): 2, 4, 6 months, 15 months, 4 years
  - Pneumocócica 10V (PCV10): 2, 4, 12 months
  - Rotavírus: 2, 4 months
  - Meningocócica C: 3, 5 months, 12 months
  - Febre amarela: 9 months, 4 years
  - Tríplice viral (SCR/MMR): 12 months, 15 months (tetra viral)
  - DTP: 15 months, 4 years
  - Varicela: 15 months
  - Hepatite A: 12 months

For simplicity, I'll model a simplified vaccination schedule with key milestones and tolerance windows. The "atrasada" (delayed) logic: if the child's age exceeds the recommended age + grace period without the vaccine dose registered.

**SOAP method** - for clinical notes; here maybe used for structuring the alert message? SOAP = Subjetivo, Objetivo, Avaliação, Plano. The alert generation could produce a SOAP-structured summary for the professional. I can include a SOAP-structured "avaliação" record for the active search case.

**Teleconsultation reminders:**
- Teleconsulta scheduled → generate reminder at T-24h and T-1h (or configurable), via WhatsApp/SMS mock.
- Message templates with patient name, date/time, professional, link (mock), instructions.
- Idempotency: avoid duplicate sends (dedupe key).
- Consent (LGPD): patient must have consent flag for messaging.

**Active search (busca ativa):**
- Children with delayed vaccines: compare vaccination records vs PNI calendar.
- Diabetics without follow-up > 90 days: last consultation/registration with CIAP-2 T90/T91 or CID-10 E10-E14, check days since last contact (consultation, exam like HbA1c, nursing visit).

**Architecture:**
- SQLAlchemy 2.0 models: I should define models (or reference them). Since the task says "crie backend/app/services/mensageria_preventiva.py", the main deliverable is the service file. But for tests to work, I need models and schemas. I should provide:
  - `backend/app/services/mensageria_preventiva.py` (main)
  - Possibly supporting: `backend/app/models/` entities, `backend/app/schemas/mensageria.py` (Pydantic), `backend/app/core/config.py`? The instruction says create the service file, but to be complete and testable, I'll provide the service plus minimal models/schemas it depends on, and tests. I should keep it focused: the primary file is the service; I'll include the models/schemas needed inline or in adjacent modules.

Let me design:

```
backend/app/
  services/
    mensageria_preventiva.py
  models/
    paciente.py (Paciente, Vacinacao, Teleconsulta, RegistroClinico?)
  schemas/
    mensageria.py
  tests/
    test_mensageria_preventiva.py
```

To keep it manageable, maybe define models in the service module? No — better practice: separate models module. But the task explicitly says create the service file. I'll create the service file plus the minimal supporting files (models, schemas, enums) and tests, clearly organized. Actually, to reduce sprawl, I could put Pydantic schemas in the service file... but guidelines say strict typing with Pydantic v2 — schemas in a schemas module is cleaner. Hmm. The instruction: "crie backend/app/services/mensageria_preventiva.py: gerador de lembretes automáticos..." — the deliverable is that file. I'll deliver:

1. `backend/app/schemas/mensageria_preventiva.py` — Pydantic v2 schemas (strict).
2. `backend/app/models/mensageria_preventiva.py` — SQLAlchemy 2.0 models (Paciente, Teleconsulta, RegistroVacinal, ContatoClinico, NotificacaoEnviada / LogMensagem).
3. `backend/app/services/mensageria_preventiva.py` — the service with:
   - `ServicoMensageriaPreventiva` class
   - `gerar_lembretes_teleconsulta(...)` 
   - `identificar_criancas_vacinas_atrasadas(...)`
   - `identificar_diabeticos_sem_acompanhamento(...)`
   - Mock channel adapters: `CanalWhatsAppMock`, `CanalSMSMock` implementing a `CanalMensagem` protocol.
4. `backend/tests/test_mensageria_preventiva.py` — pytest with in-memory SQLite, high coverage.

Let me think about details.

**CNS validation:** CNS has a check algorithm. CNS can start with 1, 2, 7, 8, 9. Validation algorithm:
- For CNS starting with 1, 2, 7, 8, 9: sum with weights 15..2 (15,14,...,2) over the first 11 digits? Actually the algorithm: take 15 digits, multiply first 15? Let me recall the official algorithm:

CNS validation (definitive cards starting with 1, 2, 7, 8, 9):
```
soma = 0
for i, digito in enumerate(cns[:15]):
    peso = 15 - i
    soma += int(digito) * peso
resto = soma % 11
dv = 11 - resto if resto != 0 else 0  # hmm
```
Actually the standard algorithm:

```
def valida_cns(cns: str) -> bool:
    cns = cns.replace('.', '').replace(' ', '')
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    soma = sum(int(c) * (15 - i) for i, c in enumerate(cns[:12]))
    resto = soma % 11
    dv = 11 - resto
    if dv == 11:
        dv = 0
    if dv == 10:
        soma = sum(int(c) * (15 - i) for i, c in enumerate(cns[:11])) + 2  # hmm
```

Let me recall precisely. The official algorithm from DATASUS:

```
rotina para validação do CNS:

soma = 0
para i de 0 a 14:
  se i < 12: multiplica = 15 - i
  ...
```

The known Python implementation:

```python
def valida_cns(cns: str) -> bool:
    cns = ''.join(ch for ch in cns if ch.isdigit())
    if len(cns) != 15 or cns[0] not in '12789':
        return False
    soma = sum(int(digito) * peso for digito, peso in zip(cns[:12], range(15, 3, -1)))
    resto = soma % 11
    dv = 11 - resto
    if dv == 11:
        dv = 0
    if dv == 10:
        soma = sum(int(digito) * peso for digito, peso in zip(cns[:11], range(15, 4, -1))) + 2
        resto = soma % 11
        dv = 11 - resto
        if dv == 11:
            dv = 0
        resultado = cns[:11] + '000' + str(dv)  # hmm no
```

Hmm, this is getting complicated. Let me recall the actual DATASUS pseudocode:

```
rotina_valida_cns
  tam := tamanho(cns)
  se tam <> 15 então retorna falso
  soma := 0
  para i = 1 até 15 faça
    se i <= 11 então
      soma := soma + (15 - i) * valor(cns[i])
    senão
      soma := soma + (17 - i) * valor(cns[i])
  fim-para
  resto := soma mod 11
  se resto <> 0 então retorna falso
  ...
```

Hmm, actually there's a simpler formulation: multiply digits by weights 15,14,13,...,1 (i.e., weight = 15 - index for all 15 digits) and the sum must be divisible by 11. Let me verify with a known valid CNS: "116 807 626 000 010" — hmm I don't remember a known-valid example by heart.

Known algorithm (from DATASUS "Validação do CNS"):

```
soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
if soma % 11 == 0: válido
```

Wait, that's for the provisional? Let me think. The commonly cited algorithm:

Para CNS provisórios (começando com 7, 8 ou 9) e definitivos (1 ou 2):

```
pesos = [15,14,13,12,11,10,9,8,7,6,5,4,3,2,1]
soma = Σ digito[i] * pesos[i]
válido se soma % 11 == 0
```

Yes! I believe that's the correct one: the check is that the weighted sum with weights 15 down to 1 is divisible by 11. Let me verify with a commonly used test CNS: "700000000000000"? soma = 7*15 = 105, plus zeros = 105. 105 % 11 = 105 - 99 = 6 ≠ 0. Not valid.

Another known example: "898004100043004"? I can't verify from memory. Let me construct one: digits d0..d14 with weights 15..1. Choose CNS "100000000000000": soma = 15. Not divisible by 11. 

Let me construct a valid one: start with 1, then pick digits so sum ≡ 0 mod 11. Take "10000000000" + dv... With weights 15..1 over 15 digits: if digits are 1 followed by 13 zeros and last digit x: soma = 15*1 + 1*x = 15 + x. Need (15+x) % 11 == 0 → x = 7 (22 % 11 = 0). So "100000000000007" would be valid under this algorithm. Hmm, but is that the real algorithm? 

The DATASUS official algorithm (I recall from the "Manual de validação do CNS"):

```
1. Multiplicar cada dígito do CNS pelos pesos 15, 14, 13, ..., 2 (para os 14 primeiros?) 
```

Hmm. Let me look at this from memory of implementations I've seen:

```python
# Fonte: https://github.com/.../valida_cns.py
def valida_cns(cns):
    cns = cns.strip().replace('.', '').replace('-', '').replace(' ', '')
    if len(cns) != 15:
        return False
    if any(c in '.,-/' for c in cns):  # no
    if cns[0] not in ['1','2','7','8','9']:
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

Yes, I'm fairly confident this is the widely used implementation: weights 15 down to 1, sum divisible by 11. There's also a variant where the first 11 digits get weights 15..5 and the last 4 (DV) get weights... no.

Actually, I now recall the official algorithm more precisely from DATASUS documentation "Como validar o Cartão Nacional de Saúde":

```
Para validar o CNS:
1. O CNS deve ter 15 dígitos;
2. Os números devem começar com 1, 2, 7, 8 ou 9;
3. Multiplicar cada um dos 15 dígitos pelos pesos 15, 14, 13, ..., 1 (da esquerda para a direita);
4. Somar todos os resultados;
5. O resultado da soma deve ser divisível por 11.
```

Yes — this matches. Good, I'll implement that.

**CPF validation:** standard check digits algorithm. I'll implement it.

**PNI calendar (simplified):** I'll model doses with recommended age in days and max delay tolerance. For "atrasada": child's current age > recommended age + tolerance and no record of that dose.

Simplified calendar (doses essenciais):
- BCG: birth (0 days), tolerance 30 days? Actually BCG can be until... For busca ativa purposes, define: recommended_age_days and grace_days.
- Hepatite B (dose natal): 0 days
- Penta 1ª: 60 days, grace 15
- Penta 2ª: 120 days, grace 15
- Penta 3ª: 180 days, grace 15
- VIP 1ª: 60, VIP 2ª: 120, VIP 3ª: 180
- VOP reforço: 15 months (450 days) + 4 years
- Pneumo 1: 60, Pneumo 2: 120, Reforço: 365 (12 months)
- Rotavírus 1: 60, 2: 120
- Meningo C 1: 90, 2: 150, Reforço: 365
- Febre amarela: 270 (9 months)
- Tríplice viral D1: 365 (12 months), D2: 450 (15 months)
- Hepatite A: 365
- Varicela: 450
- DTP reforço: 1460 (4 anos)

I'll include a reasonable subset with a dataclass/dict. Keep it configurable.

**Diabetics without follow-up > 90 days:**
- Identify patients with CIAP-2 T90/T91 or CID-10 E10–E14 in their problem list / last registrations.
- Last follow-up = max(data of: consulta, teleconsulta realizada, exame HbA1c, dispensação?) — I'll model `ContatoClinico` (registro clínico) with tipo (CONSULTA, TELECONSULTA, EXAME, VISITA_DOMICILIAR, ACOMPANHAMENTO_ENFERMAGEM) and data.
- If days since last contact > 90 → generate alert (busca ativa). Also severity tiers: >90 = "atenção", >180 = "urgente"? I can add priority levels.

**SOAP:** For each active-search case, generate a structured SOAP note (Subjetivo/Objetivo/Avaliação/Plano) to attach to the alert for the professional. That satisfies "método SOAP" usage.

**CIAP-2 codes for the alerts:**
- Vacina atrasada: CIAP-2 A44? Hmm. CIAP-2 codes: "A44 - Imunização/Vacinação" — actually in CIAP-2, A44 is "Imunização/vacinação". Let me recall: Chapter A (General, unspecified): A44 = Immunization/vaccination procedure? In CIAP-2, procedures are coded with... Actually CIAP-2 includes codes like A44 "Imunização/vacinação". Yes, A44 exists in CIAP-2 as "Imunização/vacinação" under chapter A. 
- Diabetes follow-up: T90 (diabetes não-insulino-dependente), T91 (insulino-dependente).
- Teleconsulta reminder: maybe D? Not needed; but I can tag the reminder