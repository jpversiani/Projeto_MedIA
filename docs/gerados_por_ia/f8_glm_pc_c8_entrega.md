The user wants me to create a preventive messaging and alerts service for vaccines/consultations (C8) in a healthcare system inspired by SUS/APS (Brazilian Unified Health System / Primary Health Care). Let me analyze the requirements:

1. **File to create**: `backend/app/services/mensageria_preventiva.py`

2. **Features needed**:
   - Automatic reminder generator for scheduled teleconsultations (WhatsApp/SMS mock)
   - Active search identifier for children with delayed vaccines
   - Active search for diabetics without follow-up for more than 90 days

3. **Architecture guidelines**:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me design this properly:

**Domain concepts:**
- CNS (Cartão Nacional de Saúde) - 15 digits, validated with algorithm
- CPF - 11 digits, validated with check digits
- CIAP-2 codes: 
  - A97? Let me think about relevant CIAP-2 codes:
    - Vaccination: A44 (Immunização/vacinação)
    - Diabetes: T90 (Diabetes não-insulino-dependente), T91 (Diabetes insulino-dependente)
    - Teleconsultation follow-up
  - Actually in CIAP-2:
    - A44 = Immunization/vaccination
    - T90 = Diabetes non-insulin dependent
    - T91 = Diabetes insulin dependent
- CID-10:
  - E10 = Diabetes mellitus insulin-dependente
  - E11 = Diabetes mellitus não-insulino-dependente
  - E14 = Diabetes mellitus não especificado
- PNI (Programa Nacional de Imunizações) - Brazilian vaccination calendar:
  - BCG: birth to 1st month (dose única)
  - Hepatite B: birth
  - Penta (DTP/Hib/HepB): 2, 3, 4 months
  - VIP/VOP (Pólio): 2, 3, 4, 15 months + 4 years
  - Pneumocócica: 2, 4, 6 months + reforço
  - Rotavírus: 2, 3 months
  - Meningocócica C: 3, 5 months + 12 months
  - Febre amarela: 9 months
  - Tríplice viral (SCR): 12 months
  - Varicela: 15 months
  - DTP reforço: 15 months
  
  For simplicity, I'll define a vaccination calendar model with key vaccines and their due ages in months.

- SOAP method: Subjective, Objective, Assessment, Plan - used in clinical notes. The messaging service might generate SOAP-like structured messages or reference SOAP notes.

**Service design:**

```python
# backend/app/services/mensageria_preventiva.py
```

Components:
1. **Enums**: CanalMensagem (WHATSAPP, SMS), StatusMensagem (PENDENTE, ENVIADA, ENTREGUE, FALHA, CANCELADA), TipoAlerta (LEMBRETE_TELECONSULTA, BUSCA_ATIVA_VACINA, BUSCA_ATIVA_DIABETES), PrioridadeAlerta

2. **Pydantic models**:
   - `Paciente` (or reference to existing model) - with CNS/CPF validation
   - `TeleconsultaNaoRespondida` / `AgendamentoTeleconsulta`
   - `LembreteTeleconsulta` - generated reminder
   - `AlertaBuscaAtiva` - active search alert
   - `VacinaAtrasada` - delayed vaccine detail
   - `ConfiguracaoMensageria` - settings (antecedência do lembrete, dias de atraso vacinal, dias sem acompanhamento diabético)
   - `ResultadoProcessamento` - batch result

3. **Validators**:
   - CNS validation (algorithm: starts with 1,2,7,8,9; checksum with weights 15 down to 2)
   - CPF validation (standard check digits)
   - Phone validation (E.164-ish for Brazil: +55DDDNUMERO)

4. **Repository/DAO layer** (SQLAlchemy 2.0 style with `select()`):
   - Query teleconsultas agendadas within reminder window
   - Query crianças (pacientes < X anos) with vacinas atrasadas
   - Query diabéticos (CID-10 E10-E14 / CIAP-2 T90-T91) sem atendimento há > 90 dias

5. **Mock channels**:
   - `CanalWhatsAppMock`, `CanalSMSMock` implementing a `CanalMensagemProtocol` - log messages, store in DB

6. **Templates**:
   - Message templates for each type, with SUS-appropriate language

7. **Main service class**: `ServicoMensageriaPreventiva`
   - `gerar_lembretes_teleconsulta(data_ref)` 
   - `identificar_busca_ativa_vacinal(data_ref)`
   - `identificar_busca_ativa_diabeticos(data_ref)`
   - `processar_ciclo_diario()` - runs all three
   - `enviar_mensagem(...)` - dispatch through channel mock
   - `registrar_entrega(...)`

8. **SOAP integration**: The active search alerts could include a SOAP-structured summary for the health professional (e.g., `resumo_soap` with S, O, A, P fields) so the community health agent / nurse has structured info. That's a nice touch tying SOAP method in.

Let me think about the SQLAlchemy models. Since the task says "crie backend/app/services/mensageria_preventiva.py" — the main deliverable is the service file. But for full test coverage, I should also provide:
- `backend/app/models/mensageria.py` (SQLAlchemy models) — or assume they exist? The task says create the service file. But to be complete and testable, I'll provide the models too, plus tests. Let me structure:

- `backend/app/models/mensageria.py` — SQLAlchemy 2.0 models: MensagemPreventiva, AlertaBuscaAtiva, RegistroEnvio (maybe combined)
- `backend/app/schemas/mensageria.py` — Pydantic v2 schemas
- `backend/app/services/mensageria_preventiva.py` — the service
- `backend/tests/test_mensageria_preventiva.py` — pytest tests

Actually, the instruction says specifically to create the service file. But "Manter conformidade total e cobertura de testes automatizados com pytest" implies tests. I'll deliver the service file as the core, with supporting schemas/models inline or in separate files. To keep it manageable, I could put Pydantic schemas inside the service module (it's a service, schemas could live there for cohesion) and SQLAlchemy models in the models package. Hmm.

Let me decide: I'll create:

1. `backend/app/models/mensageria_preventiva.py` — SQLAlchemy 2.0 ORM models (MensagemPreventiva, AlertaBuscaAtiva)
2. `backend/app/schemas/mensageria_preventiva.py` — Pydantic v2 schemas + enums + validators (CNS, CPF, telefone)
3. `backend/app/services/mensageria_preventiva.py` — the main service with mock channels, repository queries, generators
4. `backend/tests/test_mensageria_preventiva.py` — comprehensive pytest suite with in-memory SQLite

Actually, to reduce file sprawl and keep the "single deliverable" spirit while being complete, maybe I should put schemas in the service file? The guidelines say strict typing with Pydantic v2 and SQLAlchemy 2.0. A clean architecture separates them. I'll go with the 4-file structure but present it clearly. Actually, let me reconsider — the task explicitly says "crie backend/app/services/mensageria_preventiva.py". The other files are supporting. I think providing all four is the right call for "cobertura de testes automatizados". I'll present them in order: models → schemas → service → tests.

Hmm, but maybe simpler: put Pydantic schemas inside the service module since the task names only that file, and models in a separate models file needed for SQLAlchemy. Tests import from both. Let me think about what's cleanest for the reader.

Given the instruction emphasis on the service file, I'll make the service file self-contained regarding Pydantic schemas (enums, DTOs, validators) — that's defensible: the service owns its contracts. SQLAlchemy models go to `backend/app/models/mensageria_preventiva.py` because ORM models belong to the models layer. Tests in `backend/tests/test_mensageria_preventiva.py`.

Wait — but the service needs to query existing domain models (Paciente, Teleconsulta, Vacinacao/Imunizacao, Atendimento). Those presumably exist in the project. Since this is a fresh component, I need to define minimal versions of those too, or define the queries against models I define. To make tests runnable, I'll define the needed domain models in the models file: `Paciente`, `Teleconsulta`, `Imunizacao` (registro vacinal), `Atendimento` (consulta/registro clínico). And the mensageria models: `MensagemPreventiva`, `AlertaBuscaAtiva`.

Let me design the SQLAlchemy models:

```python
class Paciente(Base):
    __tablename__ = "paciente"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str]
    cns: Mapped[str]  # 15 dígitos validados
    cpf: Mapped[str | None]
    data_nascimento: Mapped[date]
    telefone_celular: Mapped[str | None]  # +55DDD9XXXXXXXX
    telefone_fixo: Mapped[str | None]
    micro_area: Mapped[str | None]  # área de atuação do ACS
    ativo: Mapped[bool]
```

```python
class Teleconsulta(Base):
    __tablename__ = "teleconsulta"
    id: Mapped[int]
    paciente_id: Mapped[int] (FK)
    profissional_nome: Mapped[str]
    profissional_cns? maybe
    data_horario: Mapped[datetime]
    status: Mapped[str]  # AGENDADA, CONFIRMADA, REALIZADA, CANCELADA, FALTA
    modalidade? 
    motivo_ciap2: Mapped[str | None]
    lembrete_enviado_em: Mapped[datetime | None]
```

```python
class Imunizacao(Base):
    __tablename__ = "imunizacao"
    id, paciente_id, vacina (str, e.g. "PENTA", "VIP"), dose (str: "1ª", "2ª", "REFORÇO"), data_aplicacao: date | None, data_prevista: date, status? 
```

Actually for vaccine delay detection: we need expected doses by age (PNI calendar) and applied doses. Two approaches:
a) Store `Imunizacao` records with `data_aplicacao` nullable — a scheduled/expected dose with no application date = pending.
b) Compute expected doses from birthdate against the PNI calendar and compare with applied records.

Approach (b) is more "active search"-like: the system computes what should have been taken by now per PNI calendar and checks which are missing. That's more robust and demonstrates domain logic. I'll implement a PNI calendar (simplified but faithful for < 2 years old, plus reforços up to 4-5 years) and a function `doses_previstas(data_nascimento, data_ref)` returning list of `DosePrevista(vacina, dose, idade_prevista_meses, data_prevista)`. Then compare against applied `Imunizacao` records keyed by (vacina, dose). A dose is "atrasada" if `data_prevista + tolerancia < data_ref` and not applied.

PNI calendar (childhood, simplified):
- Ao nascer (0 meses): BCG (dose única), Hepatite B (dose ao nascer)
- 2 meses: Penta 1ª, VIP/VOP 1ª, Pneumocócica 1ª, Rotavírus 1ª
- 3 meses: Penta 2ª, VIP/VOP 2ª, Pneumocócica 2ª, Rotavírus 2ª, Meningocócica C 1ª
- 4 meses: Penta 3ª, VIP/VOP 3ª, Pneumocócica 3ª
- 5 meses: Meningocócica C 2ª
- 6 meses: Influenza (anual — skip, campaign-based), Hepatite B? no... Actually 6 months: Influenza anual (campaign). Skip influenza.
- 9 meses: Febre Amarela (dose única)
- 12 meses: Tríplice Viral 1ª (SCR), Meningocócica C reforço, Pneumocócica reforço
- 15 meses: DTP/VOP reforço (Penta reforço? Actually 15 months: DTP reforço, VOP reforço, Varicela, Tríplice viral 2ª dose... let me check 2024 calendar:
  - 12 meses: SCR 1ª dose? Actually current calendar: 12 months — Tríplice viral D1, Meningo C reforço, Pneumo 10 reforço, Hepatite A
  - 15 meses: SCR D2, Varicela D1, DTP/VOP D1 reforço, MenACWY? (MenACWY at 11-14 years now)
  - 4 anos: DTP/VOP D2 reforço
  
Let me use a reasonable simplified calendar:
- 0 meses: BCG (única), Hepatite B (única ao nascer)
- 2 meses: Penta D1, VIP D1, Pneumocócica D1, Rotavírus D1
- 3 meses: Penta D2, VIP D2, Pneumocócica D2, Rotavírus D2, Meningocócica C D1
- 4 meses: Penta D3, VIP D3, Pneumocócica D3
- 5 meses: Meningocócica C D2
- 9 meses: Febre Amarela D1
- 12 meses: Tríplice Viral D1, Hepatite A D1, Meningocócica C Reforço, Pneumocócica Reforço
- 15 meses: Tríplice Viral D2, Varicela D1, DTP Reforço, VOP Reforço
- 48 meses (4 anos): DTP Reforço 2, VOP Reforço 2

That's faithful enough. I'll document it as "calendário simplificado PNI".

For matching applied doses: `Imunizacao(vacina, dose)` where vacina names normalized (uppercase, e.g. "PENTA", "VIP", "VOP" — hmm VIP/VOP equivalence: if either applied, count). To keep it simple, I'll normalize: VIP and VOP both map to "POLIOMIELITE"? Or accept equivalence list. I'll add a small equivalence map: {"VIP": "POLIO", "VOP": "POLIO", "PENTA": "PENTA", "TRIPLICE VIRAL": "SCR", "SCR": "SCR", ...}. Keep it simple: normalize vaccine name via alias map, dose via normalization ("1ª dose" → "D1", "reforço" → "REFORCO").

Hmm, this is getting complex. Balance: the core deliverable is the messaging service; the vaccine calendar logic is a supporting module. I'll keep the calendar logic inside the service module (or a small `calendario_vacinal.py`?). The task says the service should be the "identificador de busca ativa para crianças com vacinas atrasadas" — so the logic belongs in the service. I'll put the PNI calendar as a module-level constant + helper functions in the service file. Good.

Diabetics without follow-up > 90 days:
- Identify patients with CID-10 in {E10, E11, E12, E13, E14} or CIAP-2 in {T90, T91} from diagnoses/atendimentos.
- Last `Atendimento` (individual consultation, e.g., consulta de enfermagem/médica) date; if `data_ref - ultimo_atendimento > 90 dias` (or no attendance at all after diagnosis), generate alert.
- Alert includes SOAP summary for the professional: S (queixas do último registro), O (última HbA1c/PA/peso if available), A (risco), P (ação: agendar consulta, busca ativa domiciliar pelo ACS).

Teleconsultation reminders:
- Query `Teleconsulta` with status AGENDADA/CONFIRMADA, `data_horario` within window [data_ref + antecedencia_min, data_ref + antecedencia_max] (e.g., next 48h, default reminder 24h before), and `lembrete_enviado_em is None`.
- Generate message via template with patient first name, date/time formatted (pt-BR), professional name, link (mock), instructions.
- Channel selection: WhatsApp preferred if celular exists, else SMS if any phone, else mark SEM_CANAL (fallback: alerta para ACS / busca ativa).
- Mock channels: classes that "send" (log + return protocol result with message_id, status). Store `MensagemPreventiva` record with status ENVIADA (mock), payload, canal, idempotency key.

Idempotency: avoid duplicate reminders — check existing MensagemPreventiva with same `chave_idempotencia` (e.g., f"LEMBRETE_TELECONSULTA:{teleconsulta_id}:{data_horario.date()}"). Same for alerts: one active alert per patient per type per period.

Message templates (pt-BR, SUS-appropriate, LGPD-conscious — no sensitive data in messages! Important: messages should not contain diagnosis info (diabetes) — LGPD sensitive data. For vaccine alerts, the message goes to the family: "compareça à UBS para atualização do caderneta" without naming which vaccines? Actually naming missing vaccines in SMS is common in real systems but is health data; safer to say "cartão de vacinas da criança está com doses pendentes — procure a UBS". I'll note LGPD compliance: messages avoid diagnoses; details only in the professional-facing alert (SOAP). Good compliance point.

For the diabetes