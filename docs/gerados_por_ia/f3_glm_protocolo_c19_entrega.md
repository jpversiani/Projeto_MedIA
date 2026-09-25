The user wants me to create a clinical risk inference engine (Manchester Triage System adapted for Brazilian Primary Health Care - APS/UBS context) for the MedIA project.

Requirements:
- File: `backend/app/services/triagem_clinica.py`
- Risk classification engine for APS (Atenção Primária à Saúde)
- Evaluation of extreme vital signs
- Sentinel complaints (chest pain, severe dyspnea)
- Priority assignment: Vermelho (Red), Laranja (Orange), Amarelo (Yellow), Verde (Green), Azul (Blue)
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me design this properly:

1. **Pydantic models** for input/output:
   - `SinaisVitais` (vital signs): PA sistólica/diastólica, FC, FR, SpO2, temperatura, glicemia capilar, nível de consciência (AVPU)
   - `QueixaPrincipal` with CIAP-2 codes
   - `DadosPaciente` with CNS/CPF validation
   - `EntradaTriagem` - the full triage input
   - `ResultadoTriagem` - output with priority, justification, SOAP elements

2. **Risk engine**:
   - Manchester adapted: Vermelho (immediate), Laranja (very urgent, ~10min), Amarelo (urgent, ~60min), Verde (standard, ~120min), Azul (non-urgent, ~240min)
   - Vital signs extreme thresholds:
     - SpO2 < 90% → Vermelho; 90-94% → Laranja/Amarelo
     - PAS < 90 → Vermelho (shock); PAS > 180 with symptoms → Laranja; PAS ≥ 200 → Laranja
     - FC < 40 or > 130 → Vermelho; 40-50 or 120-130 → Laranja
     - FR < 10 or > 30 → Vermelho; 25-30 → Laranja
     - Temp ≥ 39.5 with red flags → Laranja; ≥ 38.5 → Amarelo
     - Glicemia < 50 → Vermelho; < 70 → Laranja; > 300 → Laranja; > 250 → Amarelo
     - AVPU: only Alerta acceptable; V/P/U → Vermelho
   - Sentinel complaints (CIAP-2 codes):
     - Chest pain (L01, K74/K75) → at minimum Laranja
     - Severe dyspnea (R02) → at minimum Laranja/Vermelho
     - Sudden weakness/hemiplegia (N99, K90 stroke) → Vermelho/Laranja
     - Unconsciousness (A06) → Vermelho
     - Convulsion (N88) → Vermelho
     - Active bleeding (B02, D13) → Laranja
     - Suicidal ideation (P19) → Laranja/Vermelho
     - Anaphylaxis (S97/allergy) → Vermelho
     - Severe pain (score 8-10) → Laranja; 4-7 → Amarelo; 1-3 → Verde
   - Priority should be the highest (most severe) among all criteria
   - Red flags / alarm symptoms

3. **SOAP structure**: The output should include SOAP components (Subjetivo, Objetivo, Avaliação, Plano) to integrate with clinical records.

4. **CNS/CPF validation**: CNS has a known checksum algorithm (PACs and cards starting with 7,8,9). CPF has standard check digits. I should implement validators.

5. **CIAP-2 codes**: relevant codes for sentinel conditions.

6. **CID-10**: maybe map some sentinel conditions to CID-10 suggestions.

7. **SQLAlchemy 2.0**: The service should be able to persist triage records. I'll include a SQLAlchemy model for `TriagemRecord` and repository functions. Actually, the task says "crie backend/app/services/triagem_clinica.py" — a service. I should include the SQLAlchemy model (2.0 style with `Mapped`, `mapped_column`) for persistence, plus the Pydantic schemas and the engine. Maybe keep the SQLAlchemy model in the service file or reference models. To be self-contained and executable, I'll define the ORM model in the service file (or note it could be moved). Better: define it in the service file with a comment that in production it might live in models.py. Actually, to keep clean architecture, I could define the ORM model in the same file for completeness since only one file was requested.

8. **Tests**: pytest file `backend/tests/services/test_triagem_clinica.py` with comprehensive coverage:
   - CNS validation tests (valid/invalid)
   - CPF validation tests
   - Vital sign extremes → each color
   - Sentinel complaints → each color
   - Pain score → colors
   - Priority precedence (worst wins)
   - SOAP output structure
   - Persistence with SQLAlchemy (in-memory SQLite)
   - Pydantic validation errors

Let me write the code.

**CNS validation algorithm:**
CNS must be 15 digits. If it starts with 1, 2, 7, 8, or 9:
- For CNS starting with 1 or 2 (definitive): sum = Σ (digit_i * (15 - i)) for i=1..15, must be divisible by 11.
- For CNS starting with 7, 8, 9 (provisional): two-step checksum. First: sum with weights 15..1; if sum % 11 == 0, valid. Otherwise, compute rest = sum % 11, subtract from 11 to get dv... Actually the algorithm: 
  - soma = Σ digit_i * peso_i where pesos = 15,14,...,1
  - resto = soma % 11
  - if resto != 0: dv = 11 - resto; if dv in (10, 11): dv = 0... hmm, let me recall correctly.

The official algorithm for CNS (Cartão Nacional de Saúde):
```
1. Sum: soma = n1*15 + n2*14 + ... + n15*1
2. resto = soma % 11
3. If resto == 0 → valid
4. Else: dv = 11 - resto; if dv == 10 or 11 → dv = 0; replace last digit with dv and recompute? 
```
Actually the standard validation: For CNS starting with 1, 2, 7, 8, 9:
- Compute soma with weights 15 down to 1.
- resto = soma % 11
- If resto != 0, the CNS is invalid (for the simple check). But the full algorithm handles recalculation for provisional cards.

The commonly used validation function (from various sources):

```python
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if soma % 11 == 0:
        return True
    # For provisional (7,8,9): recalculate
    if cns[0] in '789':
        # dv = 11 - (soma % 11); if dv >= 10: dv = 0
        dv = 11 - (soma % 11)
        if dv >= 10:
            dv = 0
        # replace last digit and revalidate
        novo = cns[:14] + str(dv)
        soma2 = sum(int(novo[i]) * (15 - i) for i in range(15))
        return soma2 % 11 == 0
    return False
```

Hmm, actually the widely used implementation:

```python
def valida_cns(cns: str) -> bool:
    cns = re.sub("[^0-9]", "", cns)
    if len(cns) != 15:
        return False
    if cns[0] in "789" or cns[0] in "12":
        pis = cns
        soma = sum(int(pis[i]) * (15 - i) for i in range(15))
        if soma % 11 == 0:
            return True
        else:
            resto = soma % 11
            dv = 11 - resto
            if dv >= 10:
                dv = 0
            if pis[0:14] + str(dv) == pis:
                return True
            else:
                # try the full recalculation
                soma = sum(int(pis[i]) * (15 - i) for i in range(14)) + dv * 1
                ...
```

Let me just use the standard well-known implementation. The most common one found in Brazilian projects:

```python
def valida_cns(cns):
    """Valida CNS - Cartão Nacional de Saúde"""
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if re.match(r'[1-2]{1}\d{10}00[0-1]{1}\d{1}', cns) or re.match(r'[7-9]{1}\d{12}', cns):
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        if soma % 11 == 0:
            return True
    return False
```

Wait, that regex `[1-2]{1}\d{10}00[0-1]{1}\d{1}` — definitive cards have format like 700000000000000? No. Definitive CNS: starts with 1 or 2, followed by 10 digits, then "00", then 0 or 1, then a digit. Hmm, that's the old PIS/PASEP-derived format. Actually the definitive CNS format: `1XX XXXX XXXX XXXX` or `2XX...` where positions 12-13 are "00" and position 14 is 0 or 1? Let me think.

The official CNS validation from DATASUS:

```
Para CNS que inicia com 1, 2, 7, 8 ou 9:
1. Montar a soma: multiplicar cada dígito pelo peso (15 para o primeiro, decrescendo até 1 para o último)
2. resto = soma % 11
3. Se resto == 0, CNS válido
4. Caso contrário, calcular dv = 11 - resto; se dv >= 10, dv = 0; substituir o último dígito pelo dv e refazer o cálculo; se o resultado for válido, o CNS é válido (isso cobre o caso de dígito verificador 10/11)
```

Hmm, actually the official algorithm from the Ministry of Health document:

```
1) O número do CNS é composto por 15 dígitos.
2) Multiplicar cada dígito pelo peso correspondente: 15, 14, 13, ..., 1
3) Somar os resultados
4) Dividir por 11
5) Se o resto for 0, o CNS é válido
6) Se o resto for diferente de 0, recalcular: dv = 11 - resto; se dv = 10 ou 11, dv = 0; substituir o 15º dígito pelo dv calculado e refazer os passos 2-5; se agora resto = 0, válido.
```

Hmm, that's not quite right either. Let me look at the widely-cited implementation:

```python
def valida_cns(cns):
    # CNS validation
    cns = re.sub(r'[^0-9]', '', cns)
    if len(cns) != 15:
        return False
    # Verifica se começa com 1, 2, 7, 8 ou 9
    if cns[0] not in ['1', '2', '7', '8', '9']:
        return False
    soma = sum([int(cns[i]) * (15 - i) for i in range(15)])
    if soma % 11 == 0:
        return True
    return False
```

This simple version is the most commonly used and is correct for valid CNS numbers. The checksum with weights 15..1 must be divisible by 11. Valid example: CNS "700 0000 0000 0003"? Let me verify: digits 7,0,0,0,0,0,0,0,0,0,0,0,0,0,3 with weights 15..1: 7*15 = 105, 3*1 = 3, total 108, 108 % 11 = 108 - 99 = 9. Not valid.

Let me construct a valid CNS: We need sum % 11 == 0. Take "8 0000 0000 0000 X": 8*15 = 120. 120 % 11 = 10 (11*10=110, 120-110=10). Need X*1 such that (120 + X) % 11 == 0 → X = 1 (121 % 11 = 0). So "800000000000001" is valid. 

Another: "700000000000000": 7*15=105, 105%11 = 105-99=6. Need last digit X: (105+X)%11==0 → X=6 (111%11=11*10+1? 111 = 11*10 + 1, no; 11*10=110, 111-110=1). Hmm, 105+X ≡ 0 mod 11 → X ≡ -105 ≡ -105 + 110 = 5 mod 11. So X=5: 110 % 11 = 0. So "700000000000005" valid.

For a definitive card: "100000000000000"? 1*15=15, 15%11=4. Need X: 15+X ≡ 0 mod 11 → X ≡ -15 ≡ -15+22=7 mod 11. X=7: 22%11=0. So "100000000000007" valid. But real definitive CNS have the "00" at positions 12-13... The regex check `1\d{10}00[01]\d` would reject "100000000000007"? Let's check: positions: 1, then 10 digits (positions 2-11), then "00" (positions 12-13), then [01] (position 14), then digit (position 15). "100000000000007": position 1 = '1', positions 2-11 = '0000000000', positions 12-13 = '00', position 14 = '0', position 15 = '7'. Yes it matches! Great.

So I'll implement:
```python
def _validar_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

And maybe add the regex format check for definitive cards. I'll keep the simple checksum approach but also validate the format pattern. Actually, to be safe and match official behavior, I'll do: checksum divisibility only, plus first-digit check. That's the standard.

**CPF validation:**
Standard: 11 digits, check digits via mod 11.

```python
def _validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))  # weights
        dv = (soma * 10) % 11 % 10
        if dv != int(cpf[i]):
            return False
    return True
```

Standard implementation:
```python
def _validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False
    # primeiro dígito
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    dv1 = (soma * 10) % 11 % 10
    if dv1 != int(cpf[9]):
        return False
    # segundo dígito
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    dv2 = (soma * 10) % 11 % 10
    return dv2 == int(cpf[10])
```

Valid CPF example: 111.444.777-35 → dv1: digits 1,1,1,4,4,4,7,7,7 weights 10..2: 1*10+1*9+1*8+4*7+4*6+4*5+7*4+7*3+7*2 = 10+9+8+28+24+20+28+21+14 = 162. 162*10 = 1620. 1620 % 11 = 1620 - 11*147 = 1620-1617 = 3. 3 % 10 = 3. dv1 = 3 ✓. dv2: digits 1,1,1,4,4,4,7,7,7,3 weights 11..2: 162 + 3*2 = 168. 168*10 = 1680. 1680 % 11: 11*152 = 1672, remainder 8. 8 % 10 = 8. dv2 = 8 ✓. So "11144477735" is valid.

**CIAP-2 codes** (Classificação Internacional de Atenção Primária):
- A01: Dor generalizada
- A