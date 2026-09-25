The user wants me to create a FAI (Ficha de Atendimento Individual) serializer for the MedIA project, for integration with SISAB (Brazilian Ministry of Health). This is a legitimate healthcare software development task for the Brazilian Unified Health System (SUS).

Let me think about what's needed:

1. **FAI (Ficha de Atendimento Individual)** - This is a real document from e-SUS APS (Atenção Primária à Saúde). It's used to record individual consultations in primary care.

2. **Key components of FAI according to e-SUS APS specifications:**
   - Header: CNES (Código Nacional de Estabelecimento de Saúde), professional CNS, CBO, date, etc.
   - Patient identification: CNS or CPF, or "cidadão não identificado" (local ID)
   - Consultation data: CIAP-2 codes, SOAP method (Subjective, Objective, Assessment, Plan)
   - Procedures, medications, etc.

3. **Validation requirements:**
   - CNES: 7 digits
   - CNS (Cartão Nacional de Saúde): 15 digits with check digit validation algorithm
   - CPF: 11 digits with check digit validation
   - CBO: Brazilian Occupation Classification (e.g., "225125" for médico clínico)
   - CIAP-2 codes: 3-character alphanumeric (e.g., "A01", "K29")
   - CID-10: alphanumeric codes

4. **CNS validation algorithm:**
   The CNS has 15 digits. Validation:
   - If starts with 1, 2, 7, 8, 9: standard algorithm
   - If starts with 7, 8, 9: can also be validated with different weights
   
   Standard algorithm:
   ```
   Soma = (d1*15) + (d2*14) + ... + (d15*1)
   Resto = Soma mod 11
   Se resto != 0, DV = 11 - resto
   Se DV == 11, DV = 0
   ```
   Actually the correct algorithm:
   - Multiply digits by weights 15, 14, 13, ..., 1
   - Sum them
   - remainder = sum % 11
   - If remainder != 0: dv = 11 - remainder
   - If dv == 11: dv = 0
   - If dv == 10: invalid (need to regenerate with 7/8/9 prefix)
   
   For CNS starting with 7, 8, or 9:
   - Multiply by weights 15, 14, ..., 1
   - sum % 11
   - if remainder == 0: valid
   - else: dv = 11 - remainder, if dv > 9 then invalid... 
   
   Actually let me recall the exact algorithm:
   
   ```
   function validaCNS(cns):
       if length != 15: return false
       if only digits: 
           # First implementation: for CNS starting with 1, 2
           soma = sum(cns[i] * (15 - i) for i in range(15))
           if soma % 11 == 0: return true
       
       # Second implementation: for CNS starting with 7, 8, 9
       # multiply by 15,14,...,1
       soma = ...
       resto = soma % 11
       if resto != 0: return false
       return true
   ```
   
   The official algorithm from the Ministry of Health:
   
   ```
   Para CNS que iniciam com 1, 2, 7, 8 ou 9:
   
   1) Multiplicar cada dígito pelo peso correspondente (15, 14, 13, ..., 1)
   2) Somar os resultados
   3) Calcular o resto da divisão da soma por 11
   4) Se o resto for diferente de 0, o DV = 11 - resto
   5) Se o DV for igual a 11, o DV = 0
   6) Se o DV for igual a 10, o CNS é inválido (deve-se gerar novo número iniciando com 7, 8 ou 9)
   
   Para CNS que iniciam com 7, 8 ou 9 (segunda forma):
   1) Multiplicar cada dígito pelo peso (15, 14, ..., 1)
   2) Somar
   3) Se soma % 11 == 0, é válido
   ```
   
   Actually, the official algorithm (from the CNS validation document):
   
   ```
   function validaCNS(vCNS)
     if len(vCNS) != 15: return false
     
     # First check: standard
     soma = 0
     for i in 0..14:
       soma += int(vCNS[i]) * (15 - i)
     resto = soma % 11
     if resto == 0: return true
     
     # Second check (for CNS starting with 7, 8, 9)
     if vCNS[0] in '789':
       soma = 0
       for i in 0..14:
         soma += int(vCNS[i]) * (15 - i)
       resto = soma % 11
       if resto == 0: return true
     return false
   ```
   
   Hmm, that's not quite right. Let me recall the actual official algorithm from the Ministry of Health document "Validação do CNS":
   
   ```
   function validaCNS(vCNS) {
     // Formato: 15 dígitos
     if (vCNS.trim().length !== 15) return false;
     
     // Primeira rotina: CNS que iniciam com 1, 2 ou 7, 8, 9
     var soma = 0;
     for (var i = 0; i < 15; i++) {
       soma += parseInt(vCNS[i]) * (15 - i);
     }
     var resto = soma % 11;
     if (resto !== 0) {
       // Segunda rotina: CNS que iniciam com 7, 8 ou 9
       if (['7','8','9'].includes(vCNS[0])) {
         soma = 0;
         for (var i = 0; i < 15; i++) {
           soma += parseInt(vCNS[i]) * (15 - i);
         }
         resto = soma % 11;
         if (resto === 0) return true;
       }
       return false;
     }
     return true;
   }
   ```
   
   Hmm, that's redundant. Let me think again. The actual official algorithm:
   
   ```
   function validaCNS(vCNS) {
     if (vCNS.trim().length !== 15) return false;
     
     // Rotina para CNS iniciando com 1 ou 2
     var soma = 0;
     for (var i = 0; i < 15; i++) {
       soma += parseInt(vCNS[i], 10) * (15 - i);
     }
     var resto = soma % 11;
     if (resto === 0) return true;
     
     // Rotina para CNS iniciando com 7, 8 ou 9
     if (['7','8','9'].indexOf(vCNS[0]) !== -1) {
       soma = 0;
       for (var i = 0; i < 15; i++) {
         soma += parseInt(vCNS[i], 10) * (15 - i);
       }
       resto = soma % 11;
       if (resto === 0) return true;
     }
     return false;
   }
   ```
   
   That's still the same computation twice. The real algorithm is:
   
   From the official document (Manual de validação do CNS):
   
   ```
   Para validar o CNS:
   1. O número deve ter 15 dígitos
   2. Multiplicar cada dígito da direita para a esquerda pelos números 15 a 1 (dígito mais à esquerda × 15, próximo × 14, ..., último × 1)
   3. Somar todos os resultados
   4. Dividir a soma por 11
   5. Se o resto for 0, o número é válido
   
   Para números que não validam e iniciam com 7, 8 ou 9:
   6. Subtrair cada dígito de 9 (ou seja, dígito complementar)
   ... 
   ```
   
   Hmm, actually I remember now. The official algorithm has two routines:
   
   **Rotina 1** (CNS iniciando com 1, 2):
   - soma = Σ dígito[i] × peso[i], pesos de 15 a 1
   - válido se soma % 11 == 0
   
   **Rotina 2** (CNS iniciando com 7, 8, 9):
   - soma = Σ dígito[i] × peso[i], pesos de 15 a 1
   - resto = soma % 11
   - dv = 11 - resto
   - if dv == 11: dv = 0
   - válido se dv == último dígito... no wait.
   
   Let me look at this from memory of the actual JS implementation that's widely used:
   
   ```javascript
   function validaCNS(vCNS) {
     // Faz a validação pelo primeiro dígito
     if (vCNS.trim().length != 15) return false;
     
     var soma;
     var resto;
     var dv;
     var pis;
     var resultado;
     var digitos;
     var digitosVerificadores;
     
     // Validação CNS - Rotina padrão
     soma = 0;
     for (i = 0; i < 15; i++) {
       soma += parseInt(vCNS.substring(i, i + 1)) * (15 - i);
     }
     resto = soma % 11;
     
     if (resto != 0) {
       dv = 11 - resto;
     } else {
       dv = resto;
     }
     
     if (dv == 11) {
       dv = 0;
     }
     
     if (dv == 10) {
       // Validação CNS - Rotina de recuperação
       soma = 0;
       for (i = 0; i < 15; i++) {
         soma += parseInt(vCNS.substring(i, i + 1)) * (15 - i);
       }
       resto = soma % 11;
       if (resto == 0) {
         return true;
       } else {
         return false;
       }
     } else {
       pis = vCNS.substring(0, 14);
       resultado = pis + dv;
       if (resultado == vCNS) {
         return true;
       } else {
         return false;
       }
     }
   }
   ```
   
   Hmm, this is getting complicated. Let me just recall the widely-used Python implementation:
   
   ```python
   def valida_cns(cns: str) -> bool:
       """
       Valida o Cartão Nacional de Saúde (CNS).
       """
       cns = re.sub(r'\D', '', cns)
       
       if len(cns) != 15:
           return False
       
       # CNS deve começar com 1, 2, 7, 8 ou 9
       if cns[0] not in '12789':
           return False
       
       # Rotina padrão
       soma = sum(int(cns[i]) * (15 - i) for i in range(15))
       if soma % 11 == 0:
           return True
       
       # Rotina alternativa para CNS iniciando com 7, 8 ou 9
       if cns[0] in '789':
           # Transforma os dígitos: d -> 9 - d? No...
           ...
       
       return False
   ```
   
   OK here's the actual official algorithm from the Ministry of Health (I'm fairly confident now, having seen the official document "Validação do número CNS"):
   
   ```
   1. Verificar se o CNS possui 15 dígitos
   2. Multiplicar cada dígito pelo seu peso correspondente:
      posição 1 → peso 15, posição 2 → peso 14, ..., posição 15 → peso 1
   3. Somar todos os produtos
   4. Calcular o resto da divisão da soma por 11
   5. Se o resto for igual a 0 → CNS válido
   
   6. Se o resto for diferente de 0:
      a. Calcular DV = 11 - resto
      b. Se DV = 11 → DV = 0
      c. Se DV = 10 → aplicar a rotina de recuperação (apenas para CNS iniciando com 7, 8 ou 9):
         - Subtrair cada dígito (exceto o último) de... 
      d. Senão, comparar DV com o 15º dígito do CNS
   ```
   
   The recovery routine for DV = 10:
   ```
   soma = 0
   for each digit i (0 to 14):
       soma += int(cns[i]) * (15 - i)
   resto = soma % 11
   if resto == 0: valid
   ```
   
   Hmm no. The actual recovery routine from the official document:
   
   ```
   Rotina de recuperação (quando DV = 10):
   1. soma = 0
   2. Para cada dígito de 1 a 15: soma += dígito × (15 - posição + 1)
   3. resto = soma % 11
   4. Se resto == 0 → válido
   ```
   
   That's the same as the first routine... 
   
   OK, let me just go with the widely accepted implementation. The most common correct implementation (used in many government-adjacent projects) is:
   
   ```python
   def valida_cns(cns: str) -> bool:
       cns = ''.join(filter(str.isdigit, cns))
       if len(cns) != 15:
           return False
       if cns[0] not in '12789':
           return False
       
       # Rotina padrão
       soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
       resto = soma % 11
       if resto == 0:
           return True
       
       dv = 11 - resto
       if dv == 10:
           # Rotina de recuperação para CNS 7, 8, 9
           if cns[0] in '789':
               soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
               return soma % 11 == 0
           return False
       
       # Verifica DV
       return int(cns[14]) == dv
   ```
   
   Hmm, but the recovery routine being identical to the first check doesn't make sense unless... Actually wait. I remember now! The recovery routine uses different weights or a different transformation. Let me think...
   
   The official document says (from "Cartão Nacional de Saúde - Algoritmo de validação"):
   
   ```
   Rotina de recuperação:
   Quando o DV calculado for 10, o CNS deve ser reprocessado:
   1. Subtrair de 9 cada um dos dígitos do CNS (exceto o dígito verificador)
   ...no
   ```
   
   Actually, I found it in my memory. The official algorithm from the DATASUS document:
   
   ```
   function validaCNS(vCNS) {
     if ((vCNS.trim().length) != 15) { return (false); }
     
     var soma = new Number;
     var resto = new Number;
     var dv = new Number;
     var pis = new String;
     var resultado = new String;
     
     pis = vCNS.substring(0, 14);
     
     // Rotina padrão
     soma = 0;
     for (i = 0; i < 15; i++) {
       soma = soma + parseInt(vCNS.substring(i, i + 1)) * (15 - i);
     }
     resto = soma % 11;
     
     if (resto != 0) {
       dv = 11 - resto;
     } else {
       dv = resto;
     }
     
     if (dv == 11) dv = 0;
     
     if (dv == 10) {
       // Rotina de recuperação
       soma = 0;
       for (i = 0; i < 15; i++) {
         soma = soma + parseInt(vCNS.substring(i, i + 1)) * (15 - i);
       }
       resto = soma % 11;
       if (resto == 0) {
         return true;
       } else {
         return false;
       }
     } else {
       resultado = pis + dv;
       if (resultado != vCNS) {
         return false;
       } else {
         return true;
       }
     }
   }
   ```
   
   Hmm, the recovery routine here is identical to the standard routine. That seems like a bug in the original, but it's actually the official algorithm. Wait no — I think the recovery routine actually does something different. Let me think about what makes mathematical sense.
   
   Actually, I recall the recovery routine involves subtracting each digit from 9 or something similar. Here's the actual official algorithm from the Ministry of Health document (I'm now recalling it more clearly):
   
   ```
   Rotina de recuperação (quando DV = 10):
   1. Subtrair de 9 cada dígito do CNS, obtendo um novo número
   2. Aplicar a rotina padrão ao novo número
   3. Se o novo número validar, o CNS original é válido
   ```
   
   Hmm, that's the "complement to 9" approach. Actually yes! I remember now. The official document says:
   
   ```
   4.2. Rotina de recuperação:
   Quando o DV calculado for igual a 10, deve-se aplicar a rotina de recuperação:
   a) Subtrair de 9 cada um dos 15 dígitos do CNS;
   b) Aplicar a rotina padrão ao número obtido;
   c) Se o resultado for válido, o CNS original também é válido.
   ```
   
   Hmm, but if you subtract each digit from 9 and the weights are symmetric... Let's check: if d' = 9 - d, then Σ d'[