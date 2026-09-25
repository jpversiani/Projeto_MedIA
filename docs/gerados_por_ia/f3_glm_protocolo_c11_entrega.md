The user wants me to create a clinical risk inference engine (Manchester Triage System adapted) for Primary Health Care (APS - Atenção Primária à Saúde) in Brazil, as part of the MedIA project.

Requirements:
- File: `backend/app/services/triagem_clinica.py`
- Risk classification engine for APS (Primary Care)
- Evaluation of extreme vital signs
- Sentinel complaints (chest pain, severe dyspnea)
- Priority assignment (Vermelho/Red, Laranja/Orange, Amarelo/Yellow, Verde/Green, Azul/Blue)
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me design this properly:

1. **Pydantic models** for input/output:
   - `SinaisVitais` (vital signs): PA sistólica/diastólica, FC, FR, SpO2, temperatura, glicemia capilar, nível de consciência (AVPU), dor (escala 0-10)
   - `QueixaPrincipal` (chief complaint): texto, CIAP-2 code optional, CID-10 optional
   - `DadosPaciente`: CNS, CPF, idade, sexo, gestante
   - `TriagemEntrada`: aggregated input
   - `TriagemResultado`: output with cor/prioridade, justificativa, sinais de alerta, conduta sugerida, tempo máximo de espera

2. **Manchester Adapted logic**:
   - Vermelho (Red): immediate care - cardiorespiratory arrest, airway compromise, SpO2 < 90%, shock signs, unconsciousness (AVPU = U or P), severe respiratory distress
   - Laranja (Orange): very urgent - 10 minutes - extreme vitals, chest pain with risk factors, severe dyspnea, stroke signs (FAST), systolic > 180 or < 90, etc.
   - Amarelo (Yellow): urgent - 60 minutes - moderate abnormalities
   - Verde (Green): standard - 120 minutes
   - Azul (Blue): non-urgent - 240 minutes

3. **Vital signs thresholds** (adapted for APS):
   - SpO2: < 90% → Vermelho; 90-93% → Laranja; 94-95% → Amarelo
   - FC: < 40 or > 130 → Vermelho; < 50 or > 120 → Laranja; 50-59 or 100-119 → Amarelo
   - FR: < 10 or > 30 → Vermelho; 25-30 → Laranja; 21-24 → Amarelo
   - PA sistólica: < 90 → Vermelho (shock); > 200 or < 90 → ...; > 180 → Laranja (crise hipertensiva depends on symptoms)
   - Temperatura: > 40 or < 35 → Laranja; 39-40 or 35-36 → Amarelo
   - Glicemia: < 50 → Vermelho/Laranja (hypoglycemia); > 300 → Laranja; < 70 or > 250 → Amarelo
   - AVPU: U/P → Vermelho; V → Laranja

4. **Sentinel complaints**:
   - Dor torácica (chest pain) → at minimum Laranja, Vermelho if with hemodynamic instability
   - Dispneia grave → Laranja/Vermelho
   - AVC signs (FAST: face, arm, speech, time) → Vermelho (code stroke)
   - Convulsão → Vermelho
   - Hemorragia grave → Vermelho
   - Dor abdominal intensa → Amarelo/Laranja
   - Cefaleia súbita intensa ("pior dor de cabeça da vida") → Laranja
   - Ideação suicida → Laranja (saúde mental)
   - Gestante com sangramento → Vermelho/Laranja

5. **Special populations**: gestante, pediatria (age-based adjustments), idoso (>= 75 anos gets bumped up)

6. **CIAP-2 codes** for complaints:
   - A01 (dor generalizada), K01 (dor torácica), R01 (dispneia), R02 (sintomas respiratórios), N01 (cefaleia), D01 (dor abdominal), etc.

7. **SOAP method**: The output could include a suggested SOAP note structure (S: subjective, O: objective, A: assessment, P: plan)

8. **SQLAlchemy 2.0**: The service should be able to persist triage records. I'll include a SQLAlchemy model for `Triagem` record and repository functions. Since the task says "contendo motor de classificação de risco", the main focus is the engine, but architecture guidelines mention SQLAlchemy 2.0, so I should include the ORM model and persistence integration.

Let me structure:

```
backend/app/services/triagem_clinica.py
```

Should contain:
- Enums: `CorPrioridade` (VERMELHO, LARANJA, AMARELO, VERDE, AZUL), `NivelConsciencia` (AVPU)
- Pydantic models: `SinaisVitais`, `QueixaPrincipal`, `DadosPaciente`, `TriagemEntrada`, `SinalAlerta`, `TriagemResultado`, `NotaSOAP`
- Engine class: `MotorTriagemManchester` with methods:
  - `avaliar_sinais_vitais(sinais) -> list[SinalAlerta]`
  - `avaliar_queixas_sentinela(queixas, paciente) -> list[SinalAlerta]`
  - `classificar(triagem: TriagemEntrada) -> TriagemResultado`
- SQLAlchemy model: `TriagemRegistro` (table `triagens`)
- Repository: `RepositorioTriagem` with `salvar`, `obter_por_id`, `listar_por_paciente`
- Validators: CNS validation (algorithm), CPF validation (algorithm)

CNS validation algorithm:
- CNS must be 15 digits, starting with 1, 2, 7, 8, or 9
- For starting with 1 or 2: sum = Σ digit[i] * (15 - i), must be divisible by 11
- For starting with 7, 8, 9: algorithm with weights 15 down to 2, mod 11, DV = 11 - rest, if DV == 11 → DV = 0, if DV == 10 → repeat with weights 15 down to 2 starting... Actually the algorithm: 
  - soma = Σ d[i] * peso[i] where pesos = 15, 14, ..., 2
  - resto = soma % 11
  - dv = 11 - resto
  - if dv == 11: dv = 0
  - if dv == 10: recalculate with pesos 15..2 but... actually if dv == 10, the calculation is redone with soma = soma + 2... Let me recall correctly:
  
  CNS validation (first format, starts with 1 or 2):
  - pesos from 15 to 2 for 14 digits, then check: soma % 11 == 0 (including DV digit)
  
  Actually the standard algorithm:
  ```
  For CNS starting with 1 or 2:
    soma = Σ (digit[i] * (15 - i)) for i in 0..14
    if soma % 11 == 0: valid
  ```
  Wait, that includes the DV. Let me write it properly:
  
  ```
  def valida_cns_1_2(cns):
      soma = sum(int(cns[i]) * (15 - i) for i in range(15))
      return soma % 11 == 0
  ```
  
  For CNS starting with 7, 8, 9:
  ```
  def valida_cns_7_8_9(cns):
      soma = sum(int(cns[i]) * (15 - i) for i in range(15))
      resto = soma % 11
      dv = 11 - resto
      if dv == 11: dv = 0
      if dv == 10:
          # recalcula
          soma = sum(int(cns[i]) * (15 - i) for i in range(15))  # same
          resto = (soma + 2) % 11
          dv = 11 - resto
          if dv == 11: dv = 0
      return dv == int(cns[14])
  ```
  
  Hmm, actually the standard algorithm for 7/8/9:
  ```
  soma = Σ d[i] * peso[i], pesos 15..2 for first 14 digits
  resto = soma % 11
  dv = 11 - resto
  if dv == 11: dv = 0
  if dv == 10:
      soma += 2  # ??? 
  ```
  Let me recall the official algorithm from Cartão Nacional de Saúde:
  
  ```
  Para CNS iniciados em 7, 8 ou 9:
  soma = Σ (dígito[i] * peso[i]) para i = 0..13, pesos = 15, 14, ..., 2
  resto = soma % 11
  dv = 11 - resto
  se dv == 11 → dv = 0
  se dv == 10 → refazer cálculo: soma = soma + 2; resto = soma % 11; dv = 11 - resto; se dv == 11 → dv = 0
  válido se dv == dígito[14]
  ```
  
  Hmm, I think the "soma + 2" version is when dv == 10, you add 2 to the sum and recalculate. Actually I've seen implementations like:
  
  ```python
  def _valida_cns(cns: str) -> bool:
      cns = re.sub(r'\D', '', cns)
      if len(cns) != 15:
          return False
      if cns[0] not in '123789':
          return False
      # CNS provisório (7,8,9) usa outro algoritmo
      soma = sum(int(cns[i]) * (15 - i) for i in range(15))
      if cns[0] in '12':
          return soma % 11 == 0
      # 7, 8, 9
      soma14 = sum(int(cns[i]) * (15 - i) for i in range(14))
      resto = soma14 % 11
      dv = 11 - resto
      if dv == 11:
          dv = 0
      if dv == 10:
          soma14 += 2
          resto = soma14 % 11
          dv = 11 - resto
          if dv == 11:
              dv = 0
      return dv == int(cns[14])
  ```
  
  Hmm wait, for 1/2 the check is: soma over all 15 digits with pesos 15..1, and soma % 11 == 0. Let me verify with a known valid CNS: 700 0000 0000 0003? Not sure. Common test CNS: "116 5815 4155 0030"? Let me just implement the widely-used algorithm:
  
  ```python
  def valida_cns(cns: str) -> bool:
      cns = ''.join(filter(str.isdigit, cns))
      if len(cns) != 15 or cns[0] not in '123789':
          return False
      soma = sum(int(cns[i]) * (15 - i) for i in range(15))
      if cns[0] in '12':
          return soma % 11 == 0
      resto = (soma - int(cns[14])) % 11  # soma dos 14 primeiros com pesos 15..2
      dv = 11 - resto
      if dv == 11:
          dv = 0
      if dv == 10:
          resto = (soma - int(cns[14]) + 2) % 11
          dv = 11 - resto
          if dv == 11:
              dv = 0
      return dv == int(cns[14])
  ```
  
  Wait: sum over 15 digits with pesos 15..1 = sum over first 14 with pesos 15..2 + digit[14]*1. So soma14 = soma - digit[14]. Yes that's right.
  
  Known valid CNS examples: "116 809 446 500 041"? I'm not 100% sure of specific examples. A commonly cited valid CNS: 700000000000028? Let me test: digits 7,0,0,0,0,0,0,0,0,0,0,0,0,0,2,8 — that's 16 digits. No.
  
  Common test: CNS "798 0012 3412 0004"? Hard to verify by hand. Let me construct one: For 7/8/9 format: first 14 digits "79800123412000", compute soma14 = Σ d[i]*(15-i):
  - i=0: 7*15=105
  - i=1: 9*14=126
  - i=2: 8*13=104
  - i=3: 0*12=0
  - i=4: 0*11=0
  - i=5: 1*10=10
  - i=6: 2*9=18
  - i=7: 3*8=24
  - i=8: 4*7=28
  - i=9: 1*6=6
  - i=10: 2*5=10
  - i=11: 0*4=0
  - i=12: 0*3=0
  - i=13: 0*2=0
  - soma14 = 105+126+104+10+18+24+28+6+10 = 431
  - resto = 431 % 11 = 431 - 39*11 = 431-429 = 2
  - dv = 11-2 = 9
  So CNS "798001234120009" would be valid. Good, I can use that in tests.
  
  For 1/2 format: need soma % 11 == 0 over 15 digits with pesos 15..1. Take "116581541550030"? Let me instead construct: digits d0..d14. Choose "100000000000000"? soma = 1*15 = 15, 15%11=4 ≠ 0. Choose "100000000000006": soma = 15 + 6*1 = 21, %11 = 10. "100000000000003": 15+3=18, %11=7. "100000000000004": 19%11=8. "100000000000005": 20%11=9. "100000000000007": 22%11=0 ✓. So "100000000000007" is valid? soma = 1*15 + 7*1 = 22, 22%11=0. Yes! So CNS "100000000000007" passes the algorithm. Hmm, but is it a real CNS? Doesn't matter for algorithm validation. Actually wait — real CNS validation also requires... no, the algorithm is just that. But let me double check the 1/2 algorithm: some sources say pesos are 15,14,...,2 for the first 14 digits and then check (soma + dv) % 11 == 0 where dv is the 15th digit. That's the same as soma over 15 digits with pesos 15..1 % 11 == 0. Yes.
  
  Actually, hold on. Let me re-derive: pesos for i=0..14 are 15,14,13,...,1. soma = Σ d[i]*peso[i]. Valid if soma % 11 == 0. With "100000000000007": d0=1 peso 15 → 15; d14=7 peso 1 → 7; total 22; 22%11=0. Valid. OK.
  
  A real-world known valid CNS for tests: "116 831 933 200 004"? I can't verify. I'll use constructed ones and also test invalid ones.

CPF validation algorithm (standard mod 11):
```python
def valida_cpf(cpf: str) -> bool:
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) != 11 or cpf == cpf[0]*11:
        return False
    for n in (9, 10):
        soma = sum(int(cpf[i]) * (n + 1 - i) for i in range(n))
        d = ((soma * 10) % 11) % 10
        if d != int(cpf[n]):
            return False
    return True
```
Known valid CPF: 111.444.777-35 ✓, 529.982.247-25 ✓.

Now the Manchester engine design:

```python
class CorPrioridade(str, Enum):
    VERMELHO = "VERMELHO"   # Atendimento imediato (0 min)
    LARANJA = "LARANJA"     # Muito urgente (10 min)
    AMARELO = "AMARELO"     # Urgente (60 min)
    VERDE = "VERDE"         # Pouco urgente (120 min)
    AZUL = "AZUL"           # Não urgente (240 min)
```

With properties: `tempo_maximo_espera_min`, `ordem` (severity rank).

AVPU enum: ALERTA (A), RESPONDE_ESTIMULO_VERBAL (V), RESPONDE_ESTIMULO_DOLOROSO (P), INCONSCIENTE (U).

Pydantic models with strict typing:

```python
class SinaisVitais(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    
    pa_sistolica_mmhg: int | None = Field(None, ge=40, le=300)
    pa_diastolica_mmhg: int | None = Field(None, ge=20, le=