The user wants me to create a FAI (Ficha de Atendimento Individual) serializer for the MedIA project, for integration with SISAB (Brazilian Ministry of Health). This is a real Brazilian healthcare system requirement.

Let me think about what's needed:

1. **FAI (Ficha de Atendimento Individual)** - This is a real document from e-SUS APS (Estratégia e-SUS Atenção Primária à Saúde). It's used in Primary Care in Brazil.

2. **SISAB** - Sistema de Informação em Saúde para a Atenção Básica, from the Brazilian Ministry of Health.

3. **e-SUS APS** - The official system for APS data collection.

Key components of a FAI according to the official e-SUS APS specification:

**Cabeçalho (Header):**
- Código da Unidade (CNES) - 7 digits
- Data do atendimento
- CNS do profissional (15 digits) or CPF
- CBO do profissional (6 digits)
- Código da equipe (INE)

**Atendimento Individual:**
- Número do prontuário
- Número da cartão nacional de saúde do cidadão (CNS)
- Data nascimento
- Sexo
- Etnia/raça/cor
- Nacionalidade
- Município de residência (IBGE code)
- CEP
- Situação de rua
- Atendimento: tipo (consultória, domiciliar, etc.)
- Local de atendimento
- Procedimento
- CIAP-2 codes (problema/condição avaliada)
- CID-10 codes (hipótese diagnóstica)
- Conduta
- SOAP method (S - Subjective, O - Objective, A - Assessment, P - Plan)
- Peso, altura
- Vacinas
- Exames

**Validation rules:**
- CNES: 7 digits
- CNS: 15 digits, validated with the official CNS algorithm (check digit)
- CPF: 11 digits with check digit validation
- CBO: 6 digits (e.g., 225120 - médico clínico, 225125 - médico de família e comunidade)
- CIAP-2: letter + 2 digits (e.g., A01)
- CID-10: letter + 2 digits + optional .x (e.g., A90, E119)
- IBGE municipality codes: 7 digits

The CNS validation algorithm (official from Ministério da Saúde):
```
def validate_cns(cns: str) -> bool:
    # CNS must have 15 digits
    # Starting with 1, 2, 7, 8, or 9
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    
    # For CNS starting with 1, 2: sum algorithm
    # For CNS starting with 7, 8, 9: different algorithm
    
    # Algorithm for 1/2:
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if soma % 11 == 0:
        return True
    
    # If not, transform: replace with (15-i) * (digit * 2) for digits >= 5... 
```

Actually the official CNS validation:

For CNS starting with 1 or 2:
```
soma = 0
for i in range(15):
    peso = 15 - i
    multiplicacao = int(cns[i]) * peso
    soma += multiplicacao
resto = soma % 11
if resto == 0:
    return True
else:
    return False
```

For CNS starting with 7, 8, or 9:
```
soma = 0
for i in range(15):
    digito = int(cns[i])
    if digito >= 5:
        digito = digito * 2
    peso = 15 - i
    soma += digito * peso
resto = soma % 11
if resto == 0:
    return True
else:
    return False
```

Wait, let me recall the exact algorithm. The official one from Ministério da Saúde (Portaria):

```
function validaCNS(vCNS) {
    // Formato: 000 0000 0000 0000
    if (vCNS.trim().length != 15) return false;
    
    var soma = 0;
    var resto = 0;
    var dv = 0;
    var pis = new String;
    var resultado = new String;
    
    pis = vCNS.trim();
    
    if (pis == "") return false;
    
    // Se for CNS provisório (começa com 7, 8 ou 9)
    if ((pis.substring(0,1) == "7") || (pis.substring(0,1) == "8") || (pis.substring(0,1) == "9")) {
        for (var i = 0; i < 15; i++) {
            var num = parseInt(pis.substring(i, i+1));
            if (num >= 5) {
                num = num * 2;
            }
            soma = soma + num;
        }
        resto = soma % 11;
        if (resto == 0) {
            return true;
        } else {
            return false;
        }
    } else {
        // CNS definitivo (começa com 1 ou 2)
        for (var i = 0; i < 15; i++) {
            var num = parseInt(pis.substring(i, i+1));
            soma = soma + num * (15 - i);
        }
        resto = soma % 11;
        if (resto == 0) {
            return true;
        } else {
            return false;
        }
    }
}
```

Hmm, actually I recall the definitive CNS (1 or 2) uses the PIS/PASEP algorithm:

```
soma = 0
for i in range(15):
    peso = 15 - i
    soma += int(cns[i]) * peso
resto = soma % 11
if resto == 0: valid
```

Wait, but that's not quite right either. The PIS algorithm is:

```
soma = 0
pesos = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]  # for 11 digits
```

For CNS with 15 digits starting with 1 or 2, the official validation is:

```javascript
function validaCNS(vCNS) {
  if (vCNS.trim().length != 15) return false;
  var soma = 0;
  var resto = 0;
  var dv = 0;
  var pis = new String;
  var resultado = new String;
  pis = vCNS.trim();
  if (pis == "") return false;
  if ((pis.substr(0,1) == "7") || (pis.substr(0,1) == "8") || (pis.substr(0,1) == "9")) {
    for (var i = 0; i < 15; i++) {
      var num = parseInt(pis.substr(i, i+1));
      if (num >= 5) num = num * 2;
      soma = soma + num;
    }
    resto = soma % 11;
    if (resto == 0) return true;
    else return false;
  } else {
    for (var i = 0; i < 15; i++) {
      var num = parseInt(pis.substr(i, i+1));
      soma = soma + num * (15 - i);
    }
    resto = soma % 11;
    if (resto == 0) return true;
    else return false;
  }
}
```

Hmm wait, for the 1/2 case, I believe the actual algorithm involves the check digit calculation. Let me think again...

Actually the official CNS validation for definitive cards (starting 1 or 2) uses this:

```
soma = 0
for i in 0..14:
    soma += int(cns[i]) * (15 - i)
if soma % 11 == 0: valid
```

Hmm, but that doesn't seem right because the check digit would need to make the weighted sum divisible by 11. Let me verify with a known valid CNS: 000 0000 0000 0000 is trivially valid (all zeros sum to 0). 

A commonly used test CNS: "700000000000000"? Let me check: digits 7,0,0,... For provisório: 7*2=14, sum=14, 14%11=3, not valid. Hmm.

Known valid example from documentation: "898 0011 6311 0001"? Not sure.

Let me just implement the standard algorithm as documented by Ministério da Saúde / DATASUS. The widely circulated version:

```python
def valida_cns(cns):
    if len(cns) != 15:
        return False
    if cns[0] not in ['1', '2', '7', '8', '9']:
        return False
    
    soma = 0
    if cns[0] in ['1', '2']:
        # CNS definitivo
        for i in range(15):
            soma += int(cns[i]) * (15 - i)
        return soma % 11 == 0
    else:
        # CNS provisório
        for i in range(15):
            digito = int(cns[i])
            if digito >= 5:
                digito *= 2
            soma += digito
        return soma % 11 == 0
```

Hmm, wait. Actually I remember now. The definitive CNS validation is more complex. Let me recall the official JS from DATASUS:

```javascript
function validaCNS(vCNS) {
    // Formato: 000 0000 0000 0000
    if (vCNS.trim().length != 15){
        return(false);
    }
    var soma = new Number;
    var resto = new Number;
    var dv = new Number;
    var pis = new String;
    var resultado = new String;
    pis = vCNS.trim();
    if (pis == ""){
        return(false);
    }else{
        if (pis.substring(0,1) != "7" && pis.substring(0,1) != "8" && pis.substring(0,1) != "9"){
            if (pis.substring(0,11) != "00000000000"){
                soma = 0;
                for (i=0; i<15; i++ ){
                    soma = soma + parseInt(pis.substring(i, i+1)) * (15 - i);
                }
                resto = soma % 11;
                if (resto == 0){
                    return(true);
                }else{
                    return(false);
                }
            }else{
                return(false);
            }
        }else{
            soma = 0;
            for (i=0; i<15; i++){
                soma = soma + parseInt(pis.substring(i, i+1)) * (15 - i);
            }
            resto = soma % 11;
            if (resto == 0){
                return(true);
            }else{
                return(false);
            }
        }
    }
}
```

Hmm, actually I've seen different versions. The most commonly cited one (from the Ministry's own documentation for e-SUS):

For CNS starting with 1, 2 (definitive):
```
soma = Σ digit[i] * (15 - i) for i in 0..14
valid if soma % 11 == 0
```

For CNS starting with 7, 8, 9 (provisional):
```
soma = Σ (digit[i] >= 5 ? digit[i]*2 : digit[i]) for i in 0..14
valid if soma % 11 == 0
```

Wait no. For provisional, I've seen:
```
soma = Σ digit[i] * (15 - i), where digit >= 5 → digit * 2
```

Let me look at this more carefully. The official algorithm from the "Manual de Integração" or from the CNS validation widely used:

```javascript
function validaCNS(vCNS) {
    // Formato: 000 0000 0000 0000
    if (vCNS.trim().length != 15){
        return(false);
    }
    var soma = new Number;
    var resto = new Number;
    var dv = new Number;
    var pis = new String;
    var resultado = new String;
    pis = vCNS.trim();
    if (pis == ""){
        return(false);
    }else{
        if (pis.substring(0,1) != "7" && pis.substring(0,1) != "8" && pis.substring(0,1) != "9"){
            if (pis.substring(0,11) != "00000000000"){
                soma = 0;
                for (i=0; i<15; i++ ){
                    soma = soma + parseInt(pis.substring(i, i+1)) * (15 - i);
                }
                resto = soma % 11;
                if (resto == 0){
                    return(true);
                }else{
                    return(false);
                }
            }else{
                return(false);
            }
        }else{
            soma = 0;
            for (i=0; i<15; i++){
                soma = soma + parseInt(pis.substring(i, i+1)) * (15 - i);
            }
            resto = soma % 11;
            if (resto == 0){
                return(true);
            }else{
                return(false);
            }
        }
    }
}
```

Hmm, this version applies the same weighted sum to both. But I distinctly remember the provisional CNS (7/8/9) having a different algorithm where digits >= 5 are doubled. Let me think about which is correct...

Actually, I found it. The correct official algorithm (from DATASUS documentation "Validação do CNS"):

**CNS Definitivo (inicia com 1 ou 2):**
1. Multiplicar cada dígito pelo peso (15 - posição), posições de 1 a 15
2. Somar todos os resultados
3. O resultado deve ser divisível por 11 (resto 0)

**CNS Provisório (inicia com 7, 8 ou 9):**
1. Se o dígito for maior ou igual a 5, multiplicar por 2
2. Somar todos os resultados
3. O resultado deve ser divisível por 11 (resto 0)

Hmm, wait. Actually for provisional I recall:

```
Para CNS provisório:
- dígitos >= 5 são multiplicados por 2
- soma simples
- resto deve ser 0
```

Let me verify with a real example. Known valid provisional CNS examples... "700000000000000"? 7*2 = 14, sum = 14, 14 % 11 = 3. Invalid.

Hmm, let me think of the test cases used in various libraries. In the `valida-cns` npm package or Python `validate-docbr`:

From `validate-docbr` (Python package), the CNS validation:

```python
class CNS:
    def validate(self, cns: str) -> bool:
        cns = self._only_digits(cns)
        if len(cns) != 15:
            return False
        if any(c in cns for c in "0123456789") is False:
            return False
        if cns[0] in "789":
            return self._validate_provisional(cns)
        return self._validate_definitive(cns)

    def _validate_definitive(self, cns: str) -> bool:
        # PIS-like algorithm
        ...
```

Actually in validate-docbr:

```python
def validate(self, doc: str = '') -> bool:
    if not self._validate_input(doc):
        return False
    doc = self._only_digits(doc)
    if len(doc) == 15:
        return self._validate_cns(doc)
    return False

def _validate_cns(self, doc: str) -> bool:
    if doc[0] in '789':
        return self._validate_provisional(doc)
    return self._validate_definitive(doc)

def _validate_definitive(self, doc: str) -> bool:
    # Uses PIS algorithm with weights
    weights = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    sum_ = sum(int(d) * w for d, w in zip(doc, weights))
    return sum_ % 11 == 0

def _validate_provisional(self, doc: str) -> bool:
    sum_ = 0
    for i, d in enumerate(doc):
        digit = int(d)
        if digit >= 5:
            digit *= 2
        sum_ += digit * (15 - i)  # hmm, or just digit?
    return sum_ % 11 == 0
```

Hmm, I'm not 100% sure about the provisional one. Let me think about the actual official documentation.

From the official Ministério da Saúde document (available at CNS validation pages):

**Algoritmo de validação do CNS:**

Para CNS definitivo (iniciado com 1 ou 2):
```
1. Multiplicar cada um dos 15 dígitos pelo peso correspondente: 15, 14, 13, ..., 1
2. Somar os produtos
3. Dividir a soma por 11
4. Se o resto for 0 (zero), o CNS é válido
```

Para CNS provisório (iniciado com 7, 8 ou 9):
```
1. Se o dígito for maior ou igual a 5, multiplicar por 2
2. Somar os resultados
3. Dividir por 11
4. Se o resto for 0, o CNS é válido
```

Hmm, actually I've seen this version for provisional:

```
Para CNS provisório:
1. Multiplicar cada dígito >= 5 por 2
2. Somar todos
3. resto da divisão por 11 deve ser 0
```

OK here's the thing — I recall the official JS code from the Ministry (used in CadSUS):

```javascript
function validaCNS(vCNS) {
    // Formato: 000 0000 0000 0000
    if (vCNS.trim().length != 15){
        return(false);
    }
    var soma