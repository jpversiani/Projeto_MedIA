The user wants me to create a messaging and preventive alerts service (C32) for a healthcare system inspired by SUS/APS (Atenção Primária à Saúde) in Brazil. Let me analyze the requirements:

1. **File**: `backend/app/services/mensageria_preventiva.py`
2. **Features**:
   - Automatic reminder generator for scheduled teleconsultations (WhatsApp/SMS mock)
   - Active search identifier for children with overdue vaccines
   - Active search for diabetics without follow-up for more than 90 days
3. **Architecture guidelines**:
   - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
   - SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
   - Full compliance and automated test coverage with pytest

Let me think about the domain:

**SUS/APS Context:**
- CNS (Cartão Nacional de Saúde) - 15 digits
- CPF - 11 digits
- CIAP-2 codes: 
  - A97 - "Sem doença" / preventive
  - Vaccination related: A45? Let me recall CIAP-2 codes:
    - A44 - Imunização/vacinação
    - A45 - "Vacinação" actually A44 is "Imunização/vacinação"
    - T90 - Diabetes (CIAP-2: T90 = Diabetes não insulinodependente? Actually T90 is "Diabetes" in CIAP-2)
    - In CIAP-2: T90 = Diabetes (both types). W90? No.
    - Actually CIAP-2: T90 - Diabetes não-insulino-dependente? Let me recall: CIAP-2 T90 = "Diabetes" (covers both). Some references: T90 Diabetes (não insulinodependente), T91? No... CIAP-2 has T90 for diabetes. Hmm, actually CIAP-2 codes: T90 = Diabetes. There's only one code for diabetes in CIAP-2 (T90).
  - CID-10:
    - E10 - Diabetes mellitus insulinodependente (tipo 1)
    - E11 - Diabetes mellitus não insulinodependente (tipo 2)
    - E14 - Diabetes mellitus não especificado
  - Vaccines for children (PNI - Programa Nacional de Imunizações):
    - BCG (at birth)
    - Hepatite B (at birth)
    - Penta (DTP/Hib/HepB) - 2, 4, 6 months
    - VIP/VOP (Poliomielite) - 2, 4, 6 months, 15 months, 4 years
    - Pneumocócica (PCV10) - 2, 4, 6 months, 12 months
    - Meningocócica conjugada C - 3, 5 months, 12 months
    - Tríplice viral (SCR) - 12 months, 15 months
    - Febre amarela - 9 months
    - Varicela - 15 months
    - Influenza (annual)
    - COVID-19

**Key concepts:**
- Busca ativa (active search) - a core APS strategy
- Teleconsulta reminders
- SOAP method (Subjetivo, Objetivo, Avaliação, Plano)
- e-SUS APS, PEC (Prontuário Eletrônico do Cidadão)

**Design:**

I'll create:
1. `backend/app/services/mensageria_preventiva.py` - the main service
2. Supporting schemas (Pydantic v2)
3. SQLAlchemy 2.0 models (or at least reference them)
4. Tests with pytest

Since the task says "crie backend/app/services/mensageria_preventiva.py", the main deliverable is that file, but for it to work I need to define the models and schemas. I should probably create:

- `backend/app/models/` - SQLAlchemy models (paciente, vacinacao, teleconsulta, mensagem, alerta)
- `backend/app/schemas/mensageria.py` - Pydantic schemas
- `backend/app/services/mensageria_preventiva.py` - the service
- `backend/tests/test_mensageria_preventiva.py` - tests

Let me design the service:

**Core components:**

1. **Validadores CNS/CPF** - validate CNS (15 digits with algorithm) and CPF (11 digits with check digits)

2. **CanalMensagem** (enum): WHATSAPP, SMS

3. **ServicoMensageriaMock** - mock gateway for WhatsApp/SMS that logs messages

4. **GeradorLembretesTeleconsulta**:
   - Find teleconsultas scheduled in the next N hours (e.g., 24h and 2h before)
   - Generate reminder messages with patient name, date/time, professional, link
   - Send via mock channel
   - Record message in DB (auditoria)

5. **BuscaAtivaVacinal**:
   - For children (0-<5 years or up to some age), compare vaccination schedule vs applied vaccines
   - Identify overdue vaccines (based on PNI calendar with grace period, e.g., 30 days)
   - Generate alerts for healthcare workers (ACS - Agente Comunitário de Saúde)
   - CIAP-2: A44 (Imunização/vacinação)

6. **BuscaAtivaDiabeticos**:
   - Diabetics (CID-10: E10, E11, E14; CIAP-2: T90) without consultation/registro in >90 days
   - Generate alerts for the equipe de saúde da família
   - Priority levels

7. **SOAP note generation** for the alerts? The directive mentions SOAP method - maybe the alert includes a "plano" (plan) section. I can generate a structured SOAP-oriented summary for the professional.

Let me think about the PNI vaccination calendar for children. I'll implement a simplified but realistic schedule:

```
Calendário PNI (simplificado):
- Ao nascer: BCG, Hepatite B
- 2 meses: Penta (1ª), VIP (1ª), PCV10 (1ª), Rotavírus (1ª)
- 3 meses: Meningocócica C (1ª), Penta (2ª)? 
```

Actually the current PNI calendar (2024):
- Ao nascer: BCG, Hepatite B
- 2 meses: Penta (1ª dose), VIP (1ª), VOP?, PCV10 (1ª), Rotavírus (1ª)
- 3 meses: Meningocócica C (1ª), Penta (2ª), VIP (2ª), PCV10 (2ª), Rotavírus (2ª)
- 4 meses: Penta (3ª), VIP (3ª), PCV10 (3ª)
- 5 meses: Meningocócica C (2ª)
- 6 meses: Influenza (annual from 6 months), COVID-19
- 9 meses: Febre Amarela (1ª)
- 12 meses: Tríplice Viral (1ª), Pneumocócica (reforço), Meningocócica C (reforço), Hepatite A (1ª), Varicela (1ª)
- 15 meses: Tríplice Viral (2ª) [SCR2], DTP (reforço), VIP (reforço), Varicela (2ª)? Actually varicela reforço at 15 months? Hmm.
- 4 anos: DTP (reforço), VIP (reforço), Tríplice viral (2ª), Febre amarela?

I'll simplify to a representative subset with doses and age windows. The key logic: for each vaccine-dose in the calendar, compute the due date (birth date + age threshold). If not applied and due date + grace period (e.g., 30 days) < today → overdue (atrasada).

**Models (SQLAlchemy 2.0):**

```python
class Paciente(Base):
    __tablename__ = "pacientes"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid4)
    cns: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    cpf: Mapped[str | None] = mapped_column(String(11), unique=True)
    nome_completo: Mapped[str]
    data_nascimento: Mapped[date]
    telefone_celular: Mapped[str | None]
    telefone_whatsapp: Mapped[bool]  # aceita whatsapp
    opt_out_mensageria: Mapped[bool] = mapped_column(default=False)  # LGPD consent
    ...
```

LGPD compliance is important here - consent for messaging (opt-in/opt-out), data minimization. I should include that.

```python
class Vacinacao(Base):  # registro de dose aplicada
    __tablename__ = "vacinacoes"
    id, paciente_id, vacina (nome/codigo), dose (1ª/2ª/reforço), data_aplicacao, lote, estrategia
    
class Teleconsulta(Base):
    __tablename__ = "teleconsultas"
    id, paciente_id, profissional_nome, profissional_cns?, data_hora_inicio, data_hora_fim, status (AGENDADA, CONFIRMADA, REALIZADA, CANCELADA, FALTOU), link_sala, motivo_cid10?, ciap2?
    
class MensagemEnviada(Base):
    __tablename__ = "mensagens"
    id, paciente_id, teleconsulta_id?, canal, tipo (LEMBRETE_TELECONSULTA, ...), texto, status_envio (ENVIADA, FALHA, SIMULADA), criada_em, enviada_em
    
class AlertaBuscaAtiva(Base):
    __tablename__ = "alertas_busca_ativa"
    id, paciente_id, tipo (VACINA_ATRASADA, DIABETES_SEM_ACOMPANHAMENTO), prioridade, descricao, detalhe (JSON), status (ABERTO, EM_ATENDIMENTO, RESOLVIDO), responsavel?, criado_em, resolvido_em
```

**Pydantic schemas:**

- `PacienteResumo` (id, cns mascarado?, nome, idade)
- `LembreteTeleconsulta` (teleconsulta_id, paciente, canal, texto, quando_enviar)
- `AlertaVacinal` (paciente, vacinas_atrasadas: list[VacinaAtrasada], dias_atraso_max, prioridade)
- `VacinaAtrasada` (vacina, dose, data_prevista, dias_atraso)
- `AlertaDiabetes` (paciente, cid10, dias_sem_acompanhamento, ultima_consulta, prioridade)
- `ResultadoBuscaAtiva` (aggregated)
- `MensagemOut`, `AlertaOut`

**CNS validation algorithm:**
CNS can start with 1, 2 (users), 7, 8, 9 (professionals/managers). Validation: 15 digits, checksum with weights 15 down to 2, mod 11. If remainder == 0 or 1... Actually the algorithm:

For CNS starting with 1, 2, 7, 8, 9:
- Multiply digits by weights 15, 14, ..., 2 (left to right)
- Sum = S
- remainder = S % 11
- If remainder == 0: valid
- If remainder == 1: invalid (need to recompute with sum + 100? Actually the algorithm: if remainder is 0 or 1, the number is invalid unless... hmm)

Let me recall the correct CNS validation:

```
soma = sum(digit[i] * (15 - i) for i in range(15))
resto = soma % 11
if resto != 0:
    # recompute: soma += 100? No...
```

The official algorithm (from Cartão Nacional de Saúde):

```
function validaCNS(cns):
    if len(cns) != 15: return false
    if cns has non-digits: return false (or handle with [0-1] for letters? There's a variant with letters but let's keep digits)
    if cns[0] not in "123789": return false
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    resto = soma % 11
    if resto == 0: return true
    else: return false
```

Wait, that's not quite right. The actual algorithm:

```
soma = Σ (digit × weight) where weights = 15,14,13,...,1? 
```

Let me look at it more carefully. The standard CNS validation (from DATASUS):

```javascript
function validaCNS(vCNS) {
  // Formatos: 1, 2, 7, 8 ou 9
  if ((vCNS.trim().length != 15) || (vCNS.charAt(0) != '1' && vCNS.charAt(0) != '2' && vCNS.charAt(0) != '7' && vCNS.charAt(0) != '8' && vCNS.charAt(0) != '9')) {
    return false;
  } else {
    var soma;
    var resto;
    ...
    soma = (Number(vCNS.charAt(0)) * 15) + (Number(vCNS.charAt(1)) * 14) + ... + (Number(vCNS.charAt(14)) * 1);
    resto = soma % 11;
    if (resto != 0) {
      soma = soma + (11 - resto) * 100? 
```

Hmm, no. Let me recall properly. The actual algorithm from DATASUS:

```javascript
soma = (Number(vCNS.charAt(0)) * 15) + (Number(vCNS.charAt(1)) * 14) + (Number(vCNS.charAt(2)) * 13) + (Number(vCNS.charAt(3)) * 12) + (Number(vCNS.charAt(4)) * 11) + (Number(vCNS.charAt(5)) * 10) + (Number(vCNS.charAt(6)) * 9) + (Number(vCNS.charAt(7)) * 8) + (Number(vCNS.charAt(8)) * 7) + (Number(vCNS.charAt(9)) * 6) + (Number(vCNS.charAt(10)) * 5) + (Number(vCNS.charAt(11)) * 4) + (Number(vCNS.charAt(12)) * 3) + (Number(vCNS.charAt(13)) * 2) + (Number(vCNS.charAt(14)) * 1);
resto = soma % 11;
if (resto != 0) {
  soma = soma + (11 - resto) * 100;  // ??? no
```

Hmm, I remember there's a step: if resto != 0, then dv = 11 - resto, and you recompute... Actually I recall:

```javascript
resto = soma % 11;
if (resto != 0) {
  soma = soma + (11 - resto) * 100;  // no this doesn't make sense
```

Let me think again. The real algorithm I've seen:

```python
def valida_cns(cns):
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] not in '123789':
        return False
    soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
    resto = soma % 11
    if resto == 0:
        return True
    # Se resto != 0, soma = soma + (11 - resto) * 100? 
```

Hmm no. I found it — the actual DATASUS pseudo-code:

```
soma = Σ digit_i * peso_i (pesos 15..1)
resto = soma % 11
se resto != 0:
    soma = soma + (11 - resto) * 100  # ??? 
```

No wait. I think the correct one is:

```
dv = 11 - resto
if dv in (10, 11): dv = 0  # ?
```

Hmm, that's CPF-like. Let me recall the actual implementation that's widely used:

```javascript
function validaCNS(vCNS) {
  if ((vCNS.trim().length != 15) || ...) return false;
  var soma = 0;
  for (var i = 0; i < 15; i++) {
    soma += Number(vCNS.charAt(i)) * (15 - i);
  }
  var resto = soma % 11;
  if (resto != 0) {
    resto = 11 - resto;
    // recompute with the last digit replaced?
  }
}
```

OK here's the actual official algorithm (I'm fairly confident now, from the DATASUS document "Validação do Cartão Nacional de Saúde"):

1. CNS has 15 digits, first digit in {1, 2, 7, 8, 9}.
2. Compute soma = Σ (digit_i × peso_i), pesos = 15, 14, ..., 1.
3. resto = soma % 11.
4. If resto == 0 → valid.
5. If resto != 0 → recompute: soma2 = soma + (11 - resto) × 100? No...

Hmm, actually I remember now! The trick is:

```
resto = soma % 11
if resto != 0:
    soma = soma + (11 - resto) * 100
    resto = soma % 11
    if resto == 0: valid else invalid
```

Wait, that doesn't work either because adding (11-resto)*100 changes soma... Let me test with a known valid CNS. A commonly used test CNS: `798 5564 2264 0008`? Or `000 0000 0000 0000`? Known valid examples: "116 8094 7661 4401"? Hmm.

Let me just derive: The CNS check digit is computed such that soma % 11 == 0 where soma includes the check digit with weight 1. So for a valid CNS, soma % 11 == 0. That's the whole validation for the 1/2/7/8/9 series. I believe the "recompute" step is for *generating* the check digit when the initial computation gives resto in {0, 1}:

