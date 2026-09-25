The user is asking me to create a SISAB client service for the MedIA project. SISAB is the Sistema de Informação em Saúde para a Atenção Básica (Health Information System for Primary Care) of Brazil's Ministry of Health. This is a legitimate healthcare software development task.

The task is to create `backend/app/services/sisab_client.py` with:
1. Batch submission routines for fichas (forms/records)
2. Resilient timeout handling
3. Retry with exponential backoff
4. Parsing of delivery receipts from the Ministry of Health

Architecture guidelines:
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me think about what SISAB actually is and how it works:

SISAB (Sistema de Informação em Saúde para a Atenção Básica) is the Brazilian Ministry of Health's system for primary care data. Municipalities send data about health encounters (consultations, visits, procedures) through:
1. Direct entry in the SISAB web system
2. e-SUS APS (PEC - Prontuário Eletrônico do Cidadão)
3. Batch transmission via REST API (the "envio de lotes" / batch submission)

The batch submission API for e-SUS APS uses a REST endpoint where you send FHIR-based or JSON bundles of "fichas" (individual forms like:
- Ficha de Atendimento Individual (FAI) - Individual Care Record
- Ficha de Visita Domiciliar
- Ficha de Atividade Coletiva
- Ficha de Procedimento
- Ficha de Cadastro Individual
- Ficha de Cadastro Domiciliar

The actual e-SUS APS batch transmission API (API REST de transmissão de dados) works like:
- Authentication: The system uses a token/key (usually obtained from the SISAB/e-SUS portal)
- Endpoint: something like `https://sisab.saude.gov.br/hrg-aluno/...` — actually the real one for e-SUS APS batch is via the "Transmissão de dados" API

Let me recall the actual e-SUS APS REST API structure:
- Base URL: `https://esus-aps-rest.prod.saude.gov.br` or similar
- Actually, the official one: `https://sisab.saude.gov.br` for SISAB web
- The e-SUS APS batch API: municipalities use the "API de Transmissão de Lotes" 

The real API (from e-SUS APS documentation):
- POST to send batches of fichas
- The batch is sent as JSON with a list of fichas
- Response includes a UUID for the batch (lote)
- Then you can query the status of the batch (processado, processado com erro, etc.)
- The receipt (recibo) contains the status of each ficha

From the e-SUS APS documentation (Manual de Transmissão de Dados):
- The API endpoint is something like: `https://esusaps-rest.saude.gov.br/api/lotes` (hypothetical)
- Authentication via Bearer token or via certificate

Actually, the real documented API for e-SUS APS batch transmission:
- URL: `https://sisab.saude.gov.br/hrg-aluno-jboss/...` no...

Let me think about what's publicly documented:

The "e-SUS APS - Transmissão de dados em lote" API:
- Base: `https://esus-aps.cloud.saude.gov.br` for PEC instances
- The REST API for batch: municipalities that use PEC can enable automatic transmission

Actually the documented REST API from the Ministry:
- `POST /api/lotes/fichas` - sends a batch
- `GET /api/lotes/{uuid}/recibo` - gets the receipt

Hmm, I recall the actual e-SUS APS API documentation (available at the Ministry's GitHub - https://github.com/HGBrasil/... no). There's the "API e-SUS APS" documented in the "Manual do PEC" and there's a public spec.

The real one I remember: The e-SUS APS batch transmission API is documented at:
- Endpoint: `https://sisab.saude.gov.br` requires gov.br login
- For developers: the "Transmissão de lotes" uses the endpoint pattern:
  - `POST {base_url}/api/lote/fichas/{tipo_ficha}` 

Since I can't be 100% sure of the exact production endpoints (they change and require credentials), the best engineering approach is to make the base URL and paths configurable, implement the client with httpx, retries with exponential backoff (tenacity or custom), timeout resilience (connect/read timeouts, circuit considerations), and Pydantic models for the fichas and receipts.

Given this is a code generation task for a project, I should:
1. Create `backend/app/services/sisab_client.py` — the main deliverable
2. Possibly include supporting models (Pydantic schemas) — but the task says create the service file. I could include the Pydantic models in the same file or reference a schemas module. To keep it self-contained and testable, I'll define the models in the service file or a companion file. The task says "crie backend/app/services/sisab_client.py" — so the main file. But tests are also required ("cobertura de testes automatizados com pytest"). I should provide the test file too.

Let me design:

**Domain models (Pydantic v2, strict typing):**

```python
class TipoFicha(str, Enum):
    ATENDIMENTO_INDIVIDUAL = "atendimentoIndividual"
    VISITA_DOMICILIAR = "visitaDomiciliar"
    ATIVIDADE_COLETIVA = "atividadeColetiva"
    PROCEDIMENTO = "procedimento"
    CADASTRO_INDIVIDUAL = "cadastroIndividual"
    CADASTRO_DOMICILIAR = "cadastroDomiciliar"
```

**Ficha identifiers:** CNS (15 digits, validate with algorithm), CPF (11 digits with check digits). I should implement CNS validation (the standard algorithm: starts with 1, 2, 7, 8, 9; checksum with weights 15..2 for the 15-digit ones).

CNS validation algorithm:
- CNS must have 15 digits
- If starts with 1 or 2 (definitive): sum = Σ digit[i] * weight(15-i), total must be divisible by 11
- If starts with 7, 8, 9 (provisional): different algorithm — first four digits are 798, 789, 879, 897, 978, 987... Actually provisional CNS: first 3 digits in {7,8,9} permutations, then 5 digits from the issuing institution, then 6 sequential + 1 check digit computed with weights 15..2 and mod 11, where if remainder > 1, subtract from 11.

Let me write the standard algorithm:

For definitive CNS (1 or 2):
```
soma = 0
for i, peso in zip(cns_digits, [15,14,13,...,2]):
    soma += int(digit) * peso
resto = soma % 11
if resto == 0: valid
```
Yes: the sum of digit*weight must be ≡ 0 mod 11.

For provisional (7,8,9):
```
soma = 0
for i, peso in zip(cns_digits, [15,14,...,2]):
    soma += int(digit)*peso
resto = soma % 11
dv = 11 - resto
if dv in (10, 11): dv = 0  # hmm, actually: if resto == 0 -> dv = 0? 
```
The standard algorithm: 
```
resto = soma % 11
if resto != 0:
    dv = 11 - resto
else:
    dv = 0
```
Wait, let me recall correctly. The official algorithm for CNS:

```
function validaCNS(cns) {
  if (cns.length !== 15) return false;
  // definitive
  if ("12".includes(cns[0])) {
    let soma = 0;
    for (let i = 0; i < 15; i++) {
      soma += parseInt(cns[i]) * (15 - i);
    }
    return soma % 11 === 0;
  }
  // provisional
  if ("789".includes(cns[0])) {
    let soma = 0, peso = 15;
    for (let i = 0; i < 15; i++) {
      soma += parseInt(cns[i]) * peso;
      peso--;
    }
    let resto = soma % 11;
    let dv = 11 - resto;
    if (dv === 11) dv = 0;  // hmm
    ...
  }
}
```

Actually the official provisional algorithm:
```
soma = Σ digit[i] * peso[i] where peso goes 15 down to 2
resto = soma % 11
if resto == 0: dv = 0? 
```
Hmm. The official documentation (Manual de validação CNS):

Para CNS provisório (iniciando com 7, 8 ou 9):
1. Multiplicar cada dígito pelos pesos 15, 14, 13, ..., 2 (da esquerda para a direita, os 15 dígitos... wait 15 digits with weights 15..1? No.

Let me be careful. The official algorithm from DATASUS:

```
CNS provisório:
- Os 15 dígitos: os 8 primeiros identificam (7/8/9 + 7 dígitos), os 6 seguintes são sequenciais, o último é o DV.
- Soma = Σ (dígito_i × peso_i), pesos = 15, 14, 13, ..., 1 (15 pesos para 15 dígitos)
- resto = Soma % 11
- Se resto == 0 → DV = 0? No...
- DV = 11 - resto; se DV ∈ {10, 11} → DV = 0 - R? 
```

Hmm, actually the official one:

```
function isValidCNS(cns) {
  cns = cns.replace(/\D/g, '');
  if (cns.length !== 15) return false;
  
  // Definitive CNS (starts with 1 or 2)
  if (/^[12]/.test(cns)) {
    let sum = 0;
    for (let i = 0; i < 15; i++) {
      sum += parseInt(cns[i]) * (15 - i);
    }
    return sum % 11 === 0;
  }
  
  // Provisional CNS (starts with 7, 8, or 9)
  if (/^[789]/.test(cns)) {
    // first 8 digits must be one of: 798, 789, 879, 897, 978, 987 followed by 5 digits (00000-99999? no, specific)
    const prefix = cns.substring(0, 3);
    if (!['798','789','879','897','978','987'].includes(prefix)) return false;
    
    let sum = 0, peso = 15;
    for (let i = 0; i < 15; i++) {
      sum += parseInt(cns[i]) * peso;
      peso--;
    }
    let resto = sum % 11;
    let dv = 11 - resto;
    if (dv === 11) dv = 0;
    if (dv === 10) return false; // hmm
    return dv === parseInt(cns[14]);
  }
  return false;
}
```

Hmm, I'm not 100% sure about the exact provisional algorithm. Let me recall the official DATASUS pseudo-code:

```
Algoritmo CNS provisório:
soma = 0
para i de 0 a 14:
    soma += cns[i] * (15 - i)
resto = soma % 11
se resto == 0 então
    dv = 0  ??? 
```

Actually I found in memory the official JS implementation widely used:

```javascript
function validaCNS(vlrCNS) {
    // Formulário
    var soma = new Number;
    var resto = new Number;
    var dv = new Number;
    var pis = new String;
    var resultado = new String;
    vlrCNS = vlrCNS.replace(" ","");
    vlrCNS = vlrCNS.replace(".","");
    vlrCNS = vlrCNS.replace(".","");
    vlrCNS = vlrCNS.replace(".","");
    vlrCNS = vlrCNS.replace(".","");
    
    if (vlrCNS.trim().length != 15){
        return(false);
    }
    
    pis = vlrCNS.substring(0,11);
    soma = (((parseInt(pis.substring(0,1),10)) * 15) +
    ((parseInt(pis.substring(1,2),10)) * 14) +
    ((parseInt(pis.substring(2,3),10)) * 13) +
    ((parseInt(pis.substring(3,4),10)) * 12) +
    ((parseInt(pis.substring(4,5),10)) * 11) +
    ((parseInt(pis.substring(5,6),10)) * 10) +
    ((parseInt(pis.substring(6,7),10)) * 9) +
    ((parseInt(pis.substring(7,8),10)) * 8) +
    ((parseInt(pis.substring(8,9),10)) * 7) +
    ((parseInt(pis.substring(9,10),10)) * 6) +
    ((parseInt(pis.substring(10,11),10)) * 5));
    resto = soma % 11;
    dv = 11 - resto;
    if (dv == 11) dv = 0;
    if (dv == 10) dv = 0;
    resultado = pis + dv;
    if (vlrCNS != resultado) {
        return(false);
    } else {
        return(true);
    }
}
```

Hmm wait, that's the NIT/PIS-PASEP style validation (11 digits + DV). That's for CNS definitive? Actually that's the classic "validaCNS" that treats CNS as PIS format. But CNS definitive numbers (1/2) use the mod 11 with weights 15..1 sum divisible by 11.

The official DATASUS validation for CNS:

1. CNS definitivo (inicia com 1 ou 2): 
   - soma = Σ dígito_i × peso_i, pesos 15,14,...,1
   - válido se soma % 11 == 0

2. CNS provisório (inicia com 7, 8 ou 9):
   - Os 8 primeiros dígitos: primeiro dígito 7/8/9, e a combinação dos 3 primeiros deve ser uma permutação de 7,8,9 (798, 789, 879, 897, 978, 987), seguidos de 5 dígitos da instituição emissora
   - soma = Σ dígito_i × peso_i, pesos 15,14,...,1
   - resto = soma % 11
   - se resto == 0 → dv = 0? No: "se o resto for diferente de zero, subtrair 11 - resto; se o resultado for 10 ou 11, o dígito verificador é 0" hmm...

Official text (from the CNS validation document):
```
Para CNS provisório:
- Multiplicar cada um dos 15 dígitos pelos pesos 15 a 1 (respectivamente)
- Somar os resultados
- Dividir por 11
- Se o resto for igual a 0, o número é inválido? 
```

Hmm, I really need to get this right. Let me think about the official algorithm published by DATASUS ("Validação do CNS"):

```
CNS Provisório:
1º passo: multiplicar cada dígito do CNS pelos pesos correspondentes: 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1
2º passo: somar tudo
3º passo: obter o resto da divisão por 11
4º passo: se o resto for diferente de 0, subtrair de 11 (11 - resto). Se o resultado da subtração for 10 ou 11, o DV é 0 - resto? 
```

Hmm. Actually I remember now — the official algorithm:

```
Para CNS provisório (7, 8, 9):
- soma = Σ dígito × peso (pesos 15..1)
- resto = soma % 11
- dv = 11 - resto
- se dv == 11 → dv = 0? 
- se dv == 10 → dv = 0 - resto? 
```

OK here's the actual official algorithm from the Ministry's documentation (I've seen this in multiple implementations):

```python
def valida_cns_provisorio(cns):
    soma = sum(int(d) * p for d, p in zip(cns, range(15, 0, -1)))
    resto = soma % 11
    if resto == 0:
        return False  # ??? 
    dv = 11 - resto
    if dv in (10, 11):
        dv = 0  # ??? 
    return dv == int(cns[-1])
```

Hmm, I've seen this version:

```javascript
// Validação CNS provisório
var soma = 0;
var peso = 15;
for (i = 0; i < 15; i++) {
    soma += parseInt(cns[i]) * peso;
    peso--;
}
var resto = soma % 11;
if (resto == 0) {
    return false; // hmm no
}
var dv = 11 - resto;
if (dv == 10 || dv == 11) {
    dv = 0;
}
return dv == parseInt(cns[14]);
```

Hmm wait, actually I recall the official one differently. Let me look at this from the perspective of the widely-used implementation in the e-SUS ecosystem:

From the official "Validador de CNS" documentation (Ministério da Saúde):

**CNS Definitivo (1 ou 2):**
- Número de 15 dígitos
