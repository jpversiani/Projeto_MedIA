The user wants me to create a FAI (Ficha de Atendimento Individual) serializer for the MedIA project, for integration with SISAB (Brazilian Ministry of Health) e-SUS APS. This is a legitimate healthcare software development task - creating a serializer for Brazilian public health system (SUS) data export.

Let me think about what's needed:

1. **FAI (Ficha de Atendimento Individual)** - This is a real document from e-SUS APS (Estratégia e-SUS Atenção Primária à Saúde). It's used to record individual care in primary care in Brazil.

2. **Key components of FAI according to e-SUS APS specifications:**
   - Identification header: CNES (Código Nacional de Estabelecimento de Saúde), professional data (CNS - Cartão Nacional de Saúde, CBO - Classificação Brasileira de Ocupações), data of attendance (dataAtendimento), código da unidade
   - Patient identification: CNS, CPF, nome social, nome completo, data de nascimento, sexo, raça/cor, etnia indígena, município de residência, etc.
   - Motivo do atendimento (CIAP-2 codes)
   - Problema/condição avaliada (CID-10 or CIAP-2)
   - Atendimento: SOAP method (S - Subjective, O - Objective, A - Assessment, P - Plan)
   - Procedimentos realizados
   - Condutas
   - Medicamentos prescritos
   - Exames solicitados

3. **Validation requirements:**
   - CNES: 7 digits
   - CNS: 15 digits with check digit validation (algorithm for CNS validation)
   - CBO: format like "225125" (6 digits)
   - CPF: 11 digits with check digit validation
   - CID-10: format like "A90" or "A90.1"
   - CIAP-2: format like "A01" (letter + 2 digits)

4. **CNS validation algorithm:**
   The CNS can be:
   - Starting with 1, 2: 15 digits, check digit using modulo 11 with weights 15 to 2
   - Starting with 7, 8, 9: provisional CNS, also validated with a different algorithm (sum with weights 15 down to 2, but with different handling)
   
   Standard algorithm for CNS (1, 2, 7, 8, 9):
   ```
   For CNS starting with 1 or 2:
   - 15 digits
   - Calculate: soma = sum(digit[i] * (15 - i)) for i in 0..13
   - resto = soma % 11
   - dv = 11 - resto
   - if dv == 11: dv = 0
   - if dv == 10: soma = soma + 2; resto = soma % 11; dv = 11 - resto; if dv == 11: dv = 0... 
   ```
   
   Actually the standard algorithm:
   ```
   def validate_cns(cns):
       cns = re.sub(r'\D', '', cns)
       if len(cns) != 15:
           return False
       if cns[0] in '12':
           # peso = 15 to 2
           soma = sum(int(cns[i]) * (15 - i) for i in range(15))
           return soma % 11 == 0
       elif cns[0] in '789':
           # provisional
           soma = sum(int(cns[i]) * (15 - i) for i in range(15))
           return soma % 11 == 0
       return False
   ```
   
   Actually the correct algorithm: For CNS, the check digit is calculated so that the weighted sum (weights 15, 14, ..., 1) is divisible by 11. Let me recall:
   
   The CNS validation: multiply each of the 15 digits by weights 15, 14, 13, ..., 1 (i.e., digit i multiplied by 15-i). Sum all. If sum % 11 == 0, valid.
   
   For generation: take first 14 digits, compute sum with weights 15..2, resto = 11 - (soma % 11). If resto == 11, dv = 0. If resto == 10, then add 2 to soma and recompute... Actually:
   
   ```
   soma = sum(digit[i] * peso[i]) where peso = [15, 14, ..., 2] for first 14 digits
   resto = soma % 11
   dv = 11 - resto
   if dv == 11: dv = 0
   if dv == 10: 
       soma = soma + 2
       resto = soma % 11
       dv = 11 - resto
       if dv == 11: dv = 0
   ```
   
   Hmm, that's the algorithm for generating. For validation, the simplest check: sum of all 15 digits weighted 15..1 must be divisible by 11. Wait, that's not quite right either because of the dv==10 case. Let me think again.
   
   The official algorithm (from DATASUS):
   
   ```
   Para CNS começando com 1 ou 2:
   1. Multiplicar cada dígito pelo peso (15, 14, 13, ..., 2) para os 14 primeiros dígitos
   2. Somar os resultados
   3. resto = soma % 11
   4. dv = 11 - resto
   5. Se dv == 11, dv = 0
   6. Se dv == 10, somar 2 à soma e recalcular: resto = soma % 11, dv = 11 - resto, se dv == 11, dv = 0
   7. Comparar dv com o 15º dígito
   ```
   
   For CNS starting with 7, 8, 9 (provisional):
   ```
   1. Multiplicar cada dígito pelo peso (15, 14, ..., 2) para os 14 primeiros
   2. Somar
   3. resto = soma % 11
   4. dv = 11 - resto
   5. Se dv == 11, dv = 0
   6. Se dv == 10, somar 2 à soma e recalcular
   ```
   
   Actually both use the same algorithm; the difference is just the first digit range. The validation via "sum of all 15 weighted by 15..1 divisible by 11" works when dv != 10 case didn't require adjustment... Hmm, actually let me verify: if dv is computed as 11 - (soma14 % 11) with adjustment, then the full sum with weights 15..1 would be soma14 * ... hmm.
   
   Full sum = sum(d[i] * (15-i)) for i=0..14 = sum(d[i]*(15-i) for i=0..13) + d[14]*1 = soma14 + dv.
   
   If dv = 11 - (soma14 % 11), then soma14 + dv = soma14 + 11 - (soma14 % 11). Let soma14 = 11q + r. Then full = 11q + r + 11 - r = 11(q+1). Divisible by 11. ✓
   
   If dv was adjusted to 0 because 11 - r == 11 (r == 0): full = soma14 + 0 = 11q. Divisible. ✓
   
   If dv == 10 case: soma14' = soma14 + 2, r' = soma14' % 11, dv = 11 - r'. full = soma14 + dv = soma14' - 2 + dv = 11q' + r' - 2 + 11 - r' = 11q' + 9. Not divisible by 11! So the simple "divisible by 11" check fails for the dv==10 case.
   
   Hmm wait, let me re-check the official algorithm. From the DATASUS documentation (Rotinas da validação do CNS):
   
   ```
   Para validar CNS:
   1. O CNS deve ter 15 dígitos
   2. Primeiro dígito deve ser 1, 2, 7, 8 ou 9
   3. Multiplicar cada dígito pelo peso correspondente (15, 14, 13, ..., 1)
   4. Somar todos os resultados
   5. O resultado da soma deve ser divisível por 11
   ```
   
   Hmm, but that contradicts my analysis above for the dv==10 case. Let me check with a real example. A known valid CNS: 700 0000 0000 0030? Hmm.
   
   Actually, let me look at this more carefully. The official validation routine from DATASUS (used in many implementations):
   
   ```javascript
   function validaCNS(cns) {
       cns = cns.replace(/\D/g, '');
       if (cns.length !== 15) return false;
       var soma = 0;
       for (var i = 0; i < 15; i++) {
           soma += parseInt(cns[i]) * (15 - i);
       }
       return soma % 11 === 0;
   }
   ```
   
   This is the widely used validation. And the generation algorithm handles the dv==10 case by adding 2 to the sum, which produces a CNS where... hmm, wait. Let me redo the math.
   
   Generation: soma14 = sum(d[i] * (15-i)) for i=0..13 (weights 15 down to 2).
   resto = soma14 % 11
   dv = 11 - resto
   if dv == 11: dv = 0
   if dv == 10: soma14 += 2; resto = soma14 % 11; dv = 11 - resto; if dv == 11: dv = 0
   
   Case dv==10: original soma14 = 11q + 10 (since resto = 10). New soma14 = 11q + 12 = 11(q+1) + 1, so resto' = 1, dv = 10. Hmm, that gives dv = 10 again? No wait: 11 - 1 = 10. That's still 10. Hmm, that can't be right.
   
   Let me reconsider. Maybe the adjustment is different. The official algorithm from the "Manual de Integração" or from the CNS generation:
   
   Actually, I recall the algorithm from the DATASUS "Rotinas de validação" document:
   
   ```
   Para o CNS definitivo (começa com 1 ou 2) e provisório (7, 8, 9):
   
   1. Some os produtos dos 14 primeiros dígitos pelos pesos 15 a 2
   2. Calcule o resto da divisão da soma por 11
   3. O DV = 11 - resto
   4. Se DV = 11, DV = 0
   5. Se DV = 10, some 2 à soma do passo 1 e repita os passos 2-4
   ```
   
   Hmm, but as I showed, if resto == 10, adding 2 gives resto' = 1, dv' = 10. That loops forever. So my recollection must be wrong.
   
   Let me think about it differently. Maybe the adjustment: "Se o resto for 10, o DV será 0 e soma-se 2 à soma"? Hmm.
   
   Actually, I found it. The correct algorithm (from the official DATASUS document "Rotinas gerais para validação do CNS"):
   
   ```
   Para CNS com primeiro dígito em {1, 2}:
   1. Multiplicar cada um dos 14 primeiros dígitos pelo peso (15, 14, ..., 2)
   2. Somar os produtos
   3. resto = soma % 11
   4. dv = 11 - resto
   5. Se dv == 11: dv = 0
   6. Se dv == 10: soma = soma + 2; resto = soma % 11; dv = 11 - resto; se dv == 11: dv = 0
   7. O CNS é válido se dv == 15º dígito
   ```
   
   Hmm, the dv==10 case: soma original had resto 10, so soma = 11q + 10. soma + 2 = 11q + 12. resto' = 12 % 11 = 1. dv = 11 - 1 = 10. Still 10. That's broken.
   
   OK here's the thing — I think the actual adjustment is different. Let me recall from actual working code. Here's a widely-circulated Python implementation:
   
   ```python
   def gera_cns(inicio='1'):
       # gera 14 dígitos aleatórios começando com inicio
       ...
       soma = sum(int(pesos[i]) * int(cns[i]) for i in range(14))  # pesos 15..2
       resto = soma % 11
       dv = 11 - resto
       if dv == 11:
           dv = 0
       if dv == 10:
           soma = soma + 2
           resto = soma % 11
           dv = 11 - resto
           if dv == 11:
               dv = 0
       return cns + str(dv)
   ```
   
   Hmm wait — if resto == 10 and we add 2: soma = 11q + 10 + 2 = 11q + 12 = 11(q+1) + 1. resto' = 1. dv = 10. Infinite loop... unless... hmm, 11 - 1 = 10. Yeah still 10.
   
   Hmm, maybe the adjustment is "soma = soma + 2" applied differently, or maybe it's "if dv > 9: dv = 0"? Let me think about what makes the "sum divisible by 11" validation work.
   
   For the validation "sum of 15 digits weighted 15..1 divisible by 11" to work, we need dv such that soma14 + dv ≡ 0 (mod 11), i.e., dv ≡ -soma14 (mod 11), i.e., dv = 11 - (soma14 % 11) when soma14 % 11 != 0, and dv = 0 when soma14 % 11 == 0. But dv must be a single digit (0-9). If 11 - resto == 10 (resto == 1), there's no valid single digit! So the "divisible by 11" validation cannot be complete — some CNS numbers would be impossible.
   
   Ah, I remember now! That's exactly why the dv==10 case exists: when the required dv would be 10, it's impossible, so the generation algorithm adds 2 to the sum (changing the number itself) and recomputes. But as shown, adding 2 to a sum with resto 1 gives resto 1 again... wait no.
   
   Hold on. dv == 10 means 11 - resto == 10, so resto == 1. soma14 = 11q + 1. soma14 + 2 = 11q + 3. resto' = 3. dv' = 11 - 3 = 8. 
   
   Wait, I made an arithmetic error before. dv == 10 ⟺ resto == 1 (not 10!). Let me redo: dv = 11 - resto. dv == 10 ⟹ resto == 1. Then soma14 + 2: resto' = (11q + 1 + 2) % 11 = 3. dv' = 11 - 3 = 8. ✓ That works!
   
   I confused myself earlier by saying "resto = 10". No: dv == 10 corresponds to resto == 1. Great, so the algorithm is consistent:
   
   - resto = soma14 % 11
   - dv = 11 - resto
   - if dv == 11 (resto == 0): dv = 0
   - if dv == 10 (resto == 1): soma14 += 2, resto = soma14 % 11 (= 3), dv = 11 - resto (= 8)
   
   And for validation, the "sum of all 15 weighted 15..1 divisible by 11" check: full = soma14 + dv. In the normal case, full = 11(q+1) ✓. In the dv==11→0 case, full = soma14 = 11q ✓. In the dv==10 case, full = soma14 + 8 = 11q + 1 + 2 + 8 = 11q + 11 ✓. 
   
   So the simple validation "sum of all 15 digits weighted 15,14,...,1 divisible by 11" works for all cases. And first digit must be in {1, 2, 7, 8, 9}.
   
   So CNS validation:
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
   
   That's the standard algorithm. 

5. **CPF validation**: standard mod-11 check digit algorithm.

6. **CNES validation**: 7 digits. There's no public check-digit algorithm for CNES (it's just a registry number), so typically validation is length + numeric. Some implementations check it's 7 digits.

7. **CBO validation**: 6 digits (format ####-# in older format, now 6 digits like "225125" - Médico Clínico). The e-SUS APS uses the CBO 2002 table. Validation: 6 digits, numeric. Could also validate against a known list, but for the serializer we can validate format and optionally check against a small set of common CBOs for APS. Better to validate format (6 numeric digits) and maybe provide a curated set of common APS CBOs as a constant for reference/validation.

8. **CID-10 validation**: format: letter + 2 digits, optionally "." +