The user wants me to create a FAI (Ficha de Atendimento Individual) serializer for the MedIA project, for integration with SISAB (Brazilian Ministry of Health). This is a real Brazilian health system requirement - the e-SUS APS (Estratégia e-SUS Atenção Primária à Saúde) uses specific XML schemas for exporting health records.

Let me think about what's needed:

1. **FAI (Ficha de Atendimento Individual)** - This is a real document from the Brazilian SUS system. The e-SUS APS system uses XML files to export data to SISAB. The FAI contains:
   - Header with professional info (CNS, CBO, CNES, UBS code)
   - Patient identification (CNS/CPF, name, birth date, sex, race/color, etc.)
   - Attendance data (date, CIAP-2 codes, procedures, SOAP notes)

2. **Key validations required:**
   - CNES (Código Nacional de Estabelecimento de Saúde) - 7 digits
   - CNS (Cartão Nacional de Saúde) - 15 digits with check digit validation
   - CBO (Classificação Brasileira de Ocupações) - 6 digits format like "225125"
   - CPF validation (11 digits with check digits)
   - CNS validation algorithm - this is a real algorithm

3. **CNS validation algorithm:**
   The CNS can be validated with a checksum. The CNS has 15 digits. There are two algorithms:
   - For CNS starting with 1, 2, 7, 8, 9: uses the "módulo 11" algorithm
   - For CNS starting with 7, 8, 9 (new format): different algorithm
   
   Actually, the standard algorithm:
   - CNS numbers starting with 1, 2: sum of digits multiplied by weights 15, 14, 13... down to 2, mod 11, check digit = 11 - remainder. If result is 10 or 11, add 100 to... actually the algorithm is:
   
   For CNS starting with 1 or 2:
   1. Multiply digits by weights 15, 14, 13, ..., 2 (from left to right)
   2. Sum all products
   3. remainder = sum % 11
   4. dv = 11 - remainder
   5. If dv in (10, 11): recalculate with sum + 2 (add 2 to the sum), i.e., dv = 11 - ((sum + 2) % 11)
   6. If dv == 10, dv = 0... 
   
   Let me recall the exact algorithm:
   
   ```
   def validate_cns(cns):
       cns = cns.replace(' ', '').replace('.', '')
       if len(cns) != 15:
           return False
       # CNS must start with 1, 2, 7, 8 or 9
       if cns[0] not in '12789':
           return False
       # For CNS starting with 1, 2: use módulo 11
       # For CNS starting with 7, 8, 9: also módulo 11 but different
       
       # Algorithm for 1,2 (definitive cards):
       soma = sum(int(cns[i]) * (15 - i) for i in range(15))
       # Actually the standard algorithm:
       # pis = first 11 digits, dv = last 4? No...
   ```
   
   The correct CNS validation algorithm (from DATASUS):
   
   For CNS with 15 digits:
   - First digit must be 1, 2, 7, 8, or 9
   - If starts with 1 or 2: definitive CNS
   - If starts with 7, 8, 9: provisional CNS (new format)
   
   Algorithm (módulo 11):
   ```
   def valida_cns(cns):
       cns = ''.join(filter(str.isdigit, cns))
       if len(cns) != 15:
           return False
       if cns[0] not in '12789':
           return False
       
       # Check with the standard algorithm
       soma = 0
       for i in range(15):
           soma += int(cns[i]) * (15 - i)
       resto = soma % 11
       dv = 11 - resto
       if dv == 11:
           dv = 0  # hmm, not exactly
       ...
   ```
   
   Actually the well-known Python implementation:
   
   ```python
   def valida_cns(cns):
       """
       Valida CNS conforme algoritmo do DATASUS.
       """
       cns = re.sub(r'\D', '', cns)
       if len(cns) != 15:
           return False
       
       # CNS provisório (7,8,9) usa outro cálculo
       if cns[0] in '789':
           # soma ponderada 1-15... 
       ...
   ```
   
   Let me recall the official algorithm from DATASUS documentation:
   
   **CNS Definitivo (inicia com 1 ou 2):**
   1. Multiplicar cada dígito pelos pesos 15, 14, 13, ..., 2 (da esquerda para direita)
   2. Somar todos os resultados
   3. Calcular o resto da divisão da soma por 11
   4. DV = 11 - resto
   5. Se DV = 11, DV = 0... no wait
   
   Hmm, actually the algorithm is:
   
   ```
   soma = Σ (dígito_i × peso_i) onde pesos = 15,14,13,...,2 para os 14 primeiros dígitos? 
   ```
   
   No. Let me think again. The CNS has 15 digits. The validation:
   
   From the official DATASUS algorithm (found in many implementations):
   
   ```python
   def valida_cns(cns: str) -> bool:
       cns = re.sub("[^0-9]", "", cns)
       if len(cns) != 15:
           return False
       
       # Verifica se começa com 1, 2, 7, 8 ou 9
       if cns[0] not in "12789":
           return False
       
       # Calcula o dígito verificador
       soma = 0
       for i in range(15):
           peso = 15 - i
           soma += int(cns[i]) * peso
       
       resto = soma % 11
       dv = 11 - resto
       
       if dv == 11:
           dv = 0  # ? 
       ...
   ```
   
   Hmm, I remember the actual algorithm better now. The official one:
   
   **Para CNS definitivos (1 ou 2):**
   - Pega os 15 dígitos
   - Multiplica cada dígito por seu peso: o primeiro dígito por 15, o segundo por 14, ..., o décimo quinto por 1? No...
   
   OK here's the actual known-good implementation (widely used):
   
   ```python
   def valida_cns(cns):
       # Remove caracteres não numéricos
       cns = ''.join(n for n in cns if n.isdigit())
       
       if len(cns) != 15:
           return False
       
       # Primeiro dígito deve ser 1, 2, 7, 8 ou 9
       if cns[0] not in '12789':
           return False
       
       # Cálculo do dígito verificador (módulo 11)
       soma = sum(int(digito) * peso for digito, peso in zip(cns, range(15, 0, -1)))
       resto = soma % 11
       dv = 11 - resto
       
       if dv > 9:  # dv == 10 or dv == 11
           # Soma novamente com fator 2
           soma2 = soma + 2
           resto2 = soma2 % 11
           dv2 = 11 - resto2
           # ...
   ```
   
   Hmm, this is getting complicated. Let me recall the exact official algorithm from the DATASUS document "Validação do CNS":
   
   The official algorithm (from ConecteSUS / DATASUS):
   
   ```
   Para validar o CNS:
   1. O CNS deve ter 15 dígitos
   2. O primeiro dígito deve ser 1, 2, 7, 8 ou 9
   3. Cálculo:
      a. Multiplicar cada um dos 15 dígitos pelos pesos 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1 (respectivamente)
      b. Somar todos os produtos
      c. Calcular o resto da divisão da soma por 11
      d. Se o resto for diferente de 0, o DV = 11 - resto
      e. Se o resto for 0 ou 1, o CNS é inválido? No...
   ```
   
   Actually, I found it in my memory. The correct algorithm is:
   
   ```python
   def valida_cns(cns: str) -> bool:
       cns = re.sub(r'\D', '', cns)
       if len(cns) != 15:
           return False
       if cns[0] not in '12789':
           return False
       
       # Algoritmo módulo 11
       soma = 0
       peso = 15
       for digito in cns:
           soma += int(digito) * peso
           peso -= 1
       
       resto = soma % 11
       dv = 11 - resto
       
       if dv == 11:
           dv = 0
       
       # Hmm, this doesn't match the 15-digit structure
   ```
   
   OK let me think about this differently. The CNS structure:
   - 15 digits total
   - For definitive CNS (starting 1 or 2): 1 + 8 digits + 4 check digits? No...
   
   Actually the CNS definitive format: "1" or "2" + 10 digits + 4 check digits? Hmm.
   
   The real algorithm from DATASUS documentation (I'm fairly confident about this one, it's widely implemented):
   
   ```python
   def valida_cns(cns):
       """
       Validação do Cartão Nacional de Saúde (CNS)
       Baseado no algoritmo oficial do DATASUS
       """
       cns = re.sub(r'\D', '', cns)
       
       if len(cns) != 15:
           return False
       
       if cns[0] not in '12789':
           return False
       
       # Para CNS definitivos (1, 2) e provisórios (7, 8, 9)
       # usa-se o mesmo algoritmo de módulo 11
       soma = sum(int(cns[i]) * (15 - i) for i in range(15))
       
       resto = soma % 11
       
       if resto == 0:
           return True  # ? 
   ```
   
   Hmm no. Let me recall from the actual official documentation. The DATASUS algorithm:
   
   **"Rotina para validação do CNS"**
   
   ```
   1. Calcular o somatório: multiplicar cada dígito do CNS (da esquerda para direita) 
      pelos pesos 15, 14, 13, ..., 2, 1 e somar os resultados.
   2. Dividir o somatório por 11 e obter o resto.
   3. O CNS é válido se o resto for 0.
   ```
   
   Wait, that's one version I've seen: "o número é válido quando o resto da divisão da soma ponderada por 11 é igual a zero". Hmm, but that doesn't work for all CNS...
   
   Actually yes! I remember now. The correct algorithm:
   
   ```
   soma = Σ (dígito_i × peso_i), pesos de 15 a 1
   resto = soma % 11
   válido se resto == 0
   ```
   
   Hmm, but that can't be right either because then the check digits would need to make the sum divisible by 11, which is possible with 4 check digits (0000-9999 range gives enough freedom). Actually with 4 check digits you have 10000 combinations, and you need sum ≡ 0 (mod 11), so about 1/11 of combinations work — plenty. So yes, this is plausible.
   
   Let me verify with a known valid CNS. A commonly used test CNS: "116 6907 8600 0240" or "700 0000 0000 0000"? 
   
   Known valid CNS examples used in tests:
   - 116690780000097? 
   - 700000000000000? Let me compute: digits 7,0,0,0,0,0,0,0,0,0,0,0,0,0,0 with weights 15,14,...,1: sum = 7×15 = 105. 105 % 11 = 105 - 99 = 6. Not 0. So 700000000000000 would be invalid under this rule.
   
   Hmm, let me check another known test value: "116 8182 8600 01" no...
   
   Common test CNS values I've seen in Brazilian test suites:
   - 116.6907.8600.00240? 
   - 700000000000000 (invalid)
   - 136945626400009?
   
   Let me try the algorithm on a real-looking CNS: 116690780000097? 
   digits: 1,1,6,6,9,0,7,8,0,0,0,0,0,9,7
   weights: 15,14,13,12,11,10,9,8,7,6,5,4,3,2,1
   products: 15, 14, 78, 72, 99, 0, 63, 64, 0, 0, 0, 0, 0, 18, 7
   sum: 15+14+78+72+99+0+63+64+0+0+0+0+0+18+7 = 430
   430 % 11 = 430 - 429 (39×11) = 1. Not 0. Invalid under "resto == 0" rule.
   
   Hmm. Let me try the other algorithm I remember:
   
   The official algorithm from the "Manual de integração" / Conecte SUS:
   
   ```
   Para o CNS definitivo (inicia com 1 ou 2):
   1. Multiplicar cada dígito pelos pesos 15 a 2 (apenas os 14 primeiros dígitos? ou 15 dígitos com pesos 15 a 1?)
   ```
   
   OK here's another version I'm quite sure about, from the official DATASUS pseudo-code:
   
   ```
   soma = 0
   para i de 0 até 14:
       soma = soma + dígito[i] × (15 - i)
   resto = soma % 11
   se resto != 0:
       resto = 11 - resto
   se resto != dígito[14]:  # ?
   ```
   
   No, that doesn't work with 15 digits either.
   
   Let me think about the actual structure. The CNS definitive: 15 digits. Format: "1" + 8-digit sequential + 4-digit check? That's 13. Hmm, 1+10+4 = 15. 
   
   The real algorithm (I'm now recalling the JavaScript implementation that's widely circulated):
   
   ```javascript
   function validaCNS(value) {
       var cns = value.replace(/\D/g, '');
       if (cns.length !== 15) return false;
       if (!/^[1-9]/.test(cns)) return false;
       if (/^[12]/.test(cns)) {
           // CNS definitivo
           var soma = 0;
           var peso = 15;
           for (var i = 0; i < 15; i++) {
               soma += parseInt(cns[i]) * peso;
               peso--;
           }
           var resto = soma % 11;
           var dv = 11 - resto;
           if (dv === 11) dv = 0;
           if (dv === 10) {
               // recalcula com soma + 2
               soma += 2;
               resto = soma % 11;
               dv = 11 - resto;
               if (dv === 11) dv = 0;
               // hmm
           }
           ...
       }
   }
   ```
   
   Hmm, I remember there's something about "se o resultado for 10 ou 11, soma-se 100 ao..." 
   
   OK, I found it. The actual official algorithm from DATASUS (this is the one used in the official documentation "Validação do número do CNS"):
   
   ```
   Passo 1: Multiplicar cada dígito do CNS, da esquerda para a direita, 
           pelos pesos 15, 14, 13, ..., 2, 1 (15 dígitos, pesos decrescentes de 15 a 1).
   Passo 2: Somar todos os produtos.
   Passo 3: Calcular o resto da divisão da soma por 11.
   Passo 4: O CNS é válido se o resto for igual a 0.
   ```
   
   Wait, but I computed 430 % 11 = 1 for that test CNS. Maybe my test CNS was wrong. Let me try a CNS that's widely cited as valid: "116 8182 8600 0" no...
   
   Known valid CNS examples from test suites:
   - 700000000000000 — I've seen this cited as INVALID
   - 116690780000097 — hmm
   - 136945626400009
   - 144289286300009
   - 154385626100019
   
   Let me test 144289286300009:
   digits: 1,4,4,2,8,9,2,8,6,