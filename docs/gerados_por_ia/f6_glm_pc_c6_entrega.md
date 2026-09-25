The user wants me to create a clinical decision support engine (C6) for a medical system called MedIA. This is a Brazilian healthcare context (SUS/APS protocols, CNS/CPF identification, CIAP-2, CID-10, SOAP method).

Requirements:
1. Create `backend/app/services/copiloto_clinico.py`
2. Drug interaction analyzer (e.g., Fluoxetine + Tramadol, Enalapril + Spironolactone)
3. Allergy alerts from patient records before prescribing
4. Automatic conduct suggestions based on Brazilian Ministry of Health / SUS protocols
5. Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
6. SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
7. Full compliance and automated test coverage with pytest

Let me design this properly:

**Architecture:**
- `backend/app/services/copiloto_clinico.py` - main service
- Supporting modules: schemas (Pydantic v2), models (SQLAlchemy 2.0), repository layer
- Tests with pytest

Let me think about the structure:

```
backend/
├── app/
│   ├── __init__.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── copiloto.py          # Pydantic v2 schemas
│   ├── models/
│   │   ├── __init__.py
│   │   ├── paciente.py          # SQLAlchemy models (paciente, alergias, prescrições)
│   │   └── farmaco.py           # medicamentos, interações
│   ├── services/
│   │   ├── __init__.py
│   │   └── copiloto_clinico.py  # Main service
│   └── db/
│       └── base.py
└── tests/
    ├── conftest.py
    └── services/
        └── test_copiloto_clinico.py
```

**Key components:**

1. **Pydantic v2 schemas** (`schemas/copiloto.py`):
   - `CNSType` - validated CNS (Cartão Nacional de Saúde) with check digit validation
   - `CPFType` - validated CPF with check digits
   - `Medicamento` - drug with active ingredient (princípio ativo), dose, route
   - `Alergia` - allergy record (substance, type, severity, reaction)
   - `SolicitacaoAnalise` - request for analysis
   - `AlertaInteracao` - interaction alert with severity
   - `AlertaAlergia` - allergy alert
   - `SugestaoConduta` - conduct suggestion with protocol reference
   - `ResultadoAnalise` - full analysis result
   - Severity enum: CONTRAINDICADO, GRAVE, MODERADA, LEVE
   - CIAP-2 codes, CID-10 codes

2. **SQLAlchemy 2.0 models**:
   - `Paciente` - with CNS, CPF, allergies relationship
   - `Alergia` - substance, tipo (medicamentosa/alimentar/ambiental), severidade, reacao
   - `Medicamento` - nome comercial, principio_ativo, classe_terapeutica
   - `InteracaoMedicamentosa` - drug A, drug B, severity, mechanism, clinical effect, management
   - `Prescricao` - prescriptions with items

3. **Interaction database** (seed data / knowledge base):
   - Fluoxetina + Tramadol: GRAVE - serotonin syndrome risk (both serotonergic - SSRI + tramadol inhibits serotonin reuptake)
   - Enalapril + Espironolactone: MODERADA/GRAVE - hyperkalemia risk (ACE inhibitor + potassium-sparing diuretic)
   - Others: AAS + Varfarina, Ciprofloxacino + Varfarina, IMAO + ISRS, Sibutramina + ISRS, Claritromicina + Estatinas, Metformina + contraste iodado, AINEs + IECA, Digoxina + Amiodarona, etc.

4. **Allergy checking**:
   - Cross-reactivity knowledge (e.g., penicillin allergy → caution with cephalosporins; sulfas → sulfonamides)
   - Check against patient's registered allergies before prescribing

5. **Conduct suggestions (protocolos MS/SUS)**:
   - Based on CID-10 / CIAP-2 codes
   - Examples: 
     - Hipertensão arterial (I10) - Protocolo Linhas de Cuidado / Diretrizes Brasileiras de Hipertensão
     - Diabetes (E11) - Protocolo MS
     - Síndrome serotoninérgica management
     - Hipercalemia management
   - SOAP method support

6. **CNS validation algorithm**:
   CNS has 15 digits. Validation: for CNS starting with 1, 2, 7, 8, 9: sum = Σ digit_i * (15 - i), result must be divisible by 11. For CNS starting with 7, 8, 9 there's also the alternative format. Let me recall the exact algorithm:
   
   For CNS with first digit 1 or 2 (cartão provisório? no...): Actually:
   - CNS definitive cards start with 1, 2, 7, 8, or 9
   - Validation: multiply each of the 15 digits by weights 15, 14, 13, ..., 1 (i.e., digit i by 15-i for i=0..14), sum them. The sum must be divisible by 11.
   - For cards starting with 7, 8, 9: these use a different format where the last 5 digits are derived... Actually the standard algorithm:
   
   ```
   soma = 0
   for i in range(15):
       soma += int(cns[i]) * (15 - i)
   resto = soma % 11
   if resto == 0: valid
   ```
   
   For CNS starting with 7, 8, 9: the validation is the same but these are "cartões provisórios" formatted differently. Actually, the official algorithm from DATASUS:
   
   ```
   If CNS starts with [1-2] or [7-9]:
     If starts with 1 or 2: standard validation (peso 15 to 1, sum % 11 == 0)
     If starts with 7, 8, or 9: 
       soma = sum of digit[i] * (15 - i)
       if soma % 11 == 0: valid
       else: there's a special case where you subtract... 
   ```
   
   Let me recall properly. The DATASUS algorithm:
   
   ```
   rotina de validação do CNS:
   - Números com 15 dígitos
   - Primeiro dígito: 1, 2, 7, 8 ou 9
   - Multiplicar cada dígito pelo peso (15 - posição), somar
   - Se soma % 11 == 0 → válido
   - Para CNS iniciados em 7, 8 ou 9: se soma % 11 != 0, subtrair o resto de 11 e verificar se o resultado... 
   ```
   
   Actually the well-known implementation:
   
   ```python
   def valida_cns(cns: str) -> bool:
       cns = re.sub(r'\D', '', cns)
       if len(cns) != 15:
           return False
       if cns[0] not in '12789':
           return False
       soma = sum(int(cns[i]) * (15 - i) for i in range(15))
       return soma % 11 == 0
   ```
   
   Hmm, but there's a subtlety for 7/8/9 cards. The official DATASUS routine:
   
   ```
   Para CNS iniciados com 7, 8 ou 9:
   soma = Σ dígito[i] * (15 - i)
   resto = soma % 11
   if resto != 0:
       resultado = 11 - resto
       # verificar se resultado é 0 ou 1... 
   ```
   
   Actually, I remember the official validation from DATASUS (from the "Rotina de validação do CNS" document):
   
   ```
   1. Os números do CNS são compostos por 15 algarismos.
   2. Somente são válidos os números iniciados por 1, 2, 7, 8 ou 9.
   3. A validação é feita pela multiplicação de cada algarismo pelo seu peso (15 para o primeiro, 14 para o segundo, ..., 1 para o décimo quinto) e a soma dos resultados deve ser divisível por 11.
   ```
   
   For cards starting with 7, 8, 9 (provisórios), there's an additional rule: if the sum is not divisible by 11, subtract the remainder from 11 and check if... no wait.
   
   Let me look at the known Python implementation widely used:
   
   ```python
   def valida_cns(cns):
       """Valida o CNS."""
       cns = ''.join(filter(str.isdigit, cns))
       if len(cns) != 15 or cns[0] not in '12789':
           return False
       soma = sum(int(cns[i]) * (15 - i) for i in range(15))
       if soma % 11 == 0:
           return True
       # Para CNS iniciados com 7, 8 ou 9
       if cns[0] in '789':
           resto = soma % 11
           resultado = 11 - resto
           dv = int(cns[14])  # ?
           ...
       return False
   ```
   
   Hmm, actually the official algorithm for 7/8/9 cards:
   
   From DATASUS documentation "Validação do CNS":
   ```
   Para os números iniciados com [7|8|9]
   soma = 0
   para i de 1 até 15:
       soma = soma + dígito[i] * (16 - i)  # pesos 15..1
   resto = soma mod 11
   se resto == 0 então válido
   senão:
       resultado = 11 - resto
       se resultado == 11 ou resultado >= 10... 
   ```
   
   I recall the actual official routine is:
   
   ```
   Rotina para validação do CNS (Cartão Nacional de Saúde)
   
   Para CNS iniciados com 1 ou 2:
   - soma = Σ dígito[i] × (15 − i), i = 0..14
   - válido se soma mod 11 == 0
   
   Para CNS iniciados com 7, 8 ou 9:
   - soma = Σ dígito[i] × (15 − i)
   - resto = soma mod 11
   - se resto == 0 → válido
   - senão → subtrair 11 do... 
   ```
   
   OK here's the actual official one I'm fairly confident about (from the DATASUS "Rotina de validação do CNS" PDF):
   
   ```
   Para os números do CNS iniciados com os algarismos [7|8|9]
   
   1º passo: multiplicar cada um dos 15 algarismos por seu peso (15, 14, 13, ..., 1) e somar.
   2º passo: obter o resto da divisão da soma por 11.
   3º passo: se o resto for diferente de zero, subtrair 11 do resto... não.
   ```
   
   Actually I found it in memory — the official routine:
   
   ```
   soma = 0
   for i in 0..14: soma += digito[i] * (15 - i)
   resto = soma % 11
   if resto == 0: válido
   else if CNS começa com 7, 8 ou 9:
       resultado = 11 - resto
       if resultado == 11 or resultado == 10: inválido? 
   ```
   
   Hmm. Let me think about the widely-cited implementation from the "valida-docs" or similar Python packages:
   
   ```python
   def validate_cns(value: str) -> bool:
       cns = re.sub(r'[^0-9]', '', value)
       if len(cns) != 15:
           return False
       if re.match(r'[1-2]{1}\d{10}00[0|1][0-9]', cns) or re.match(r'[7-9]{1}\d{14}', cns):
           soma = sum(int(cns[i]) * (15 - i) for i in range(15))
           return soma % 11 == 0
       return False
   ```
   
   Yes! This is the well-known implementation. The regex `[1-2]{1}\d{10}00[0|1][0-9]` matches cards starting with 1 or 2 where positions 12-13 are "00" or "01", and `[7-9]{1}\d{14}` matches cards starting with 7, 8, 9. Then the sum check with weights 15..1 must be divisible by 11.
   
   Actually the more complete official version also handles the case for 7/8/9 where the sum check differs. But the widely used one is as above. Let me use a robust version:
   
   ```python
   def _validar_cns(cns: str) -> bool:
       digitos = re.sub(r"\D", "", cns)
       if len(digitos) != 15:
           return False
       if digitos[0] not in {"1", "2", "7", "8", "9"}:
           return False
       soma = sum(int(d) * peso for d, peso in zip(digitos, range(15, 0, -1)))
       return soma % 11 == 0
   ```
   
   This is the standard. Good enough — I'll document it references DATASUS routine.

   **CPF validation**: standard mod-11 check digits.

7. **CIAP-2 codes**: International Classification of Primary Care. Examples:
   - K86 - Hipertensão arterial sem complicações / K85 - pressão arterial elevada sem diagnóstico de hipertensão
   - T90 - Diabetes não insulinodependente
   - K78 - arritmia cardíaca
   - R95 - infecção aguda respiratória
   - A04 - fraqueza generalizada
   - D73 - hiperglicemia
   - K74 - isquemia cardíaca com angina de peito
   - N01 - dor de cabeça
   - U71 - UTI sem complicações
   - U70 - pielonefrite
   - H71 - conjuntivite aguda/infecciosa
   - R05 - tosse
   - R74 - perda de voz
   - F29 - sintomas de depressão
   - P76 - depressão
   - P74 - ansiedade
   - L03 - dor lombar sem irradiação (lombalgia)
   - D01 - náusea
   - D10 - vômito
   - D93 - dispepsia
   - K29 - doença isquêmica do tronco cerebral ou ACV
   - N05 - dor no ombro
   - S18 - corte/laceracao
   - A97 - neoplasia sem diagnóstico? 
   - B29 - neoplasia benigna da pele
   - T93 - escaldadura/queimadura térmica
   - R72 - dor de garganta
   - R21 - sintomas de garganta
   - A77 - vírus da imunodeficiência humana (HIV)/SIDA
   - A78 - malária
   - A79 - doença tropical
   - A90 - neurose
   - A91 - personalidade perturbada
   - A92 - psicose
   - P15 - abuso de drogas
   - P16 - abuso de medicamentos
   - P19 - dependência de drogas
   - P20 - dependência de medicamentos
   - P25 - transtorno de personalidade esquizotípico
   - P71 - transtorno de personalidade esquizoide/antissocial
   - P72 - transtorno de personalidade obsessivo-compulsivo
   - P73 - transtorno de personalidade histriônico
   - P75 - transtorno de ansiedade
   - P77 - transtorno de somatização
   - P78 - transtorno de personalidade narcisista
   - P79 - neurastenia/surmenage
   - P80 - transtorno do sono
   - P82 - transtorno de identidade sexual
   - P85 - retardo mental
   - P86 - transtorno de aprendizagem
   - P99 - transtornos psicológicos outros
   
   I'll include a reasonable subset relevant to the protocols.

8. **CID-10 codes** for protocols:
   - I10 - Hipertensão essencial (primária)
   - E11 - Diabetes mellitus não insulinodependente
   - E10 - DM tipo 1
   - J45 - Asma
   - J44 - DPOC
   - I21 - Infarto agudo do miocárdio
   - F32 - Episódio depressivo
   - F33 - Transtorno depressivo recorrente
   - F41 - Transtornos de ansiedade
   - A09 - Diarreia e gastroenterite de origem infecciosa presumível
   - J06 - Infecções agudas do trato respiratório superior
   - J03 - Amigdalite aguda
   - N39.0 - Infecção do trato urinário sem complicações
   - K29 - Gastrite e duodenite
   - M54.5 - Lombalgia
   - O80/O81 - parto
   - Z32 - exame/conselho contraceptivo
   - B34.9 / U07.1 - COVID
   - I63 - AVC
   - E16/E87 - etc.

9. **Protocols (MS/SUS)** — I'll build a knowledge base of conduct suggestions:
   - Hip