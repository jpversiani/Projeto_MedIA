The user wants me to create a SISAB client service for the MedIA project. SISAB is the Sistema de Informação em Saúde para a Atenção Básica do SUS (Brazilian Unified Health System's Primary Care information system).

Key requirements:
1. Create `backend/app/services/sisab_client.py`
2. Batch transmission of fichas (eAPS - individual dental/health records)
3. Resilient timeout handling
4. Retry with exponential backoff
5. Parsing of delivery receipts from the Ministry of Health
6. Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
7. SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
8. Full compliance and pytest test coverage

Let me think about the SISAB context:

SISAB (Sistema de Informação em Saúde para a Atenção Básica) is the Brazilian Ministry of Health's system for primary care data. Municipalities send batches of "fichas" (forms/records) like:
- Ficha de Atendimento Individual (eAPS - individual care record)
- Ficha de Visita Domiciliar (home visit)
- Ficha de Atendimento Odontológico (dental care)
- Ficha de Procedimento Coletivo
- Ficha de Notificação Compulsória

The actual SISAB API uses REST endpoints. The real SISAB API (as documented in the "Manual de Integração SISAB" / e-Gestor AB) has endpoints like:
- `POST /api/atendimento/individual/enviar` (or similar)
- Authentication via OAuth2 bearer token (client_credentials flow) using credentials from CNES
- The actual production endpoint is something like `https://api-sisab.minsaude.gov.br/`

Actually, the real SISAB integration (from the "e-Gestor Atenção Básica" / SISAB REST API) works like this:
- Base URL: `https://sisab.saude.gov.br` (web) but the REST API for integration is at `https://api-sisab.minsaude.gov.br/`
- Authentication: POST to `/oauth/token` with client credentials (username = CNES code, password), getting a bearer token
- Then POST batches of fichas as JSON to specific endpoints per ficha type
- Response includes a "recibo" (receipt) with status per record

Since this is a fictional-ish project (MedIA), I should design a realistic, well-structured client that:
1. Handles authentication (OAuth2 client credentials with CNES)
2. Sends batches with timeout, retry with exponential backoff + jitter
3. Parses receipts (recibos de entrega)
4. Uses Pydantic v2 models for strict typing
5. Uses httpx (async) — modern choice for Python 3.12
6. SQLAlchemy 2.0 for persistence of transmission logs (maybe a model for batch transmission records)

The task says "crie backend/app/services/sisab_client.py" — the main file. But also mentions SQLAlchemy 2.0 and pytest coverage. I should probably deliver:
1. The main service file `backend/app/services/sisab_client.py`
2. Supporting models (Pydantic schemas) — could be in the same file or separate
3. SQLAlchemy model for transmission audit — maybe in `backend/app/models/`
4. Tests in `backend/tests/services/test_sisab_client.py`

The instruction says "Execute com precisão conforme as diretrizes" — so I should deliver a complete, production-quality implementation with tests.

Let me design the architecture:

**Pydantic Models (schemas):**

```python
class FichaTipo(StrEnum):  # Python 3.12 StrEnum
    ATENDIMENTO_INDIVIDUAL = "atendimentoIndividual"
    VISITA_DOMICILIAR = "visitaDomiciliar"
    ATENDIMENTO_ODONTOLOGICO = "atendimentoOdontologico"
    PROCEDIMENTO_COLETIVO = "procedimentoColetivo"
    NOTIFICACAO_COMPULSORIA = "notificacaoCompulsoria"
```

Ficha identifiers: CNS (15 digits, validated with SIS algorithm) or CPF (11 digits with check digits). I should implement CNS validation (the standard algorithm for CNS: 15 digits, starts with 1, 2, 7, 8, or 9; checksum with weights 15..2 mod 11).

CNS validation algorithm:
- CNS must have 15 digits
- For definitive CNS (starting with 1 or 2): sum = Σ digit[i] * (15 - i); if sum % 11 == 0, valid; else compute dv... Actually the standard algorithm:

```
def valida_cns(cns: str) -> bool:
    cns = cns.strip()
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] not in "123789":
        return False
    # For 1/2 (definitive) and 7/8/9 (provisional), checksum:
    soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
    return soma % 11 == 0
```

Wait, the actual algorithm for CNS:
- Definitive CNS (starts with 1 or 2): the last two digits are check digits computed via: sum of digit*weight (weights 15,14,...,1 for 15 digits), if sum % 11 == 0 → valid. Otherwise, dv = 11 - (sum % 11), then dv is added... Actually the full algorithm:

```
peso = 15
soma = 0
for i in range(15):
    soma += int(cns[i]) * peso
    peso -= 1
resto = soma % 11
if resto == 0:
    return True
else:
    dv = 11 - resto
    # if dv > 9, then the format is 1xx xxx xxx xxx dv0/dv1... 
```

Hmm, the complete algorithm for definitive CNS:
1. Take first 12 digits + "000" → compute sum with weights 15..1
2. resto = soma % 11
3. if resto == 0 → dv = 0... 

Let me recall the official algorithm (from DATASUS):

```
function validaCNS(vlrCNS) {
    // Formato definitivo: 1 ou 2
    if (vlrCNS.trim().length != 15) return false;
    var soma = 0;
    if (vlrCNS.charAt(0) == '1' || vlrCNS.charAt(0) == '2') {
        for (var i = 0; i < 15; i++) {
            var v = parseInt(vlrCNS.charAt(i));
            soma += v * (15 - i);
        }
        if (soma % 11 == 0) {
            return true;
        } else {
            // recalculate: dv = 11 - (soma % 11); if dv > 9, dv = 0... 
        }
    }
}
```

The full official JS from DATASUS:

```javascript
function validaCNS(vlrCNS) {
   // Formulário que contem o campo CNS
   var fmw = document.frmMain;
   // Validação que aceita apenas CNS com números
   if ((vlrCNS.charAt(0).toUpperCase() != '7') && (vlrCNS.charAt(0).toUpperCase() != '8') && (vlrCNS.charAt(0).toUpperCase() != '9')) {
      soma = 0;
      // Multiplica cada dígito pelo peso correspondente (15 a 1)
      for (i = 0; i < 15; i++) {
         vlr = parseInt(vlrCNS.charAt(i));
         soma = soma + (vlr * (15 - i));
      }
      resto = soma % 11;
      if (resto != 0) {
         resultado = 11 - resto;
      } else {
         resultado = 0;
      }
      if (resultado != parseInt(vlrCNS.charAt(14))) {
         return false;
      } else {
         return true;
      }
   } else {
      // CNS provisório (7, 8, 9)
      soma = 0;
      pis = vlrCNS.substring(0, 11);
      soma = (((parseInt(pis.substring(0, 1))) * 15) + ... );
      resto = soma % 11;
      ...
   }
}
```

Actually the official algorithm:

For CNS starting with 1 or 2 (definitive):
```
soma = Σ digit[i] * (15 - i) for i in 0..14
resto = soma % 11
if resto != 0: dv = 11 - resto else dv = 0
valid if dv == digit[14]
```

Hmm wait, that's not quite right either because the definitive CNS checksum uses a different method. Let me recall the actual official one from DATASUS (the "validaCNS" JavaScript):

```javascript
function validaCNS(vlrCNS) {
   if (vlrCNS == '') return false;
   if (vlrCNS.trim().length != 15) return false;
   
   // CNS definitivo (1 ou 2) e provisório (7, 8 ou 9)
   if ((vlrCNS.charAt(0) == '1') || (vlrCNS.charAt(0) == '2') || (vlrCNS.charAt(0) == '7') || (vlrCNS.charAt(0) == '8') || (vlrCNS.charAt(0) == '9')) {
      pis = vlrCNS.substring(0, 11);
      soma = 0;
      // pesos: 15, 14, 13, ..., 5 for the first 11 digits
      resto = 0;
      dv = 0;
      ...
   }
}
```

The official algorithm (from DATASUS documentation "Validação CNS"):

```
1) Somar os dígitos multiplicados pelos pesos 15, 14, 13, ..., 1 (para os 15 dígitos)
2) Se o resto da divisão por 11 for zero, CNS válido
3) Senão, calcular dv = 11 - resto
4) Se dv > 9, então: recalcular usando apenas os 11 primeiros dígitos + "000" + dv... 
```

Hmm, this is getting complicated. The actual official algorithm:

```
function validaCNS(vlrCNS) {
    // Formato: 15 dígitos
    if (vlrCNS.trim().length != 15) return false;
    
    var soma = new Number;
    var resto = 0;
    var dv = 0;
    var pis = new String;
    var resultado = new String;
    var fator = new Number;
    
    fator = 0;
    
    // Se não começa com 1, 2, 7, 8 ou 9 → inválido
    if ((vlrCNS.charAt(0) != "1") && (vlrCNS.charAt(0) != "2") && (vlrCNS.charAt(0) != "7") && (vlrCNS.charAt(0) != "8") && (vlrCNS.charAt(0) != "9")) {
        return false;
    }
    
    pis = vlrCNS.substring(0, 11);
    soma = 0;
    for (var i = 0; i < 11; i++) {
        soma += parseInt(pis.charAt(i)) * (15 - i);
    }
    resto = soma % 11;
    if (resto == 1) {
        fator = 1; // quando resto == 1, soma-se 1 ao... 
    }
    dv = 11 - resto;
    if (dv > 9) { // quando dv > 9, precisa ajustar
        ...
    }
}
```

OK, I remember now. The official DATASUS algorithm:

```javascript
function validaCNS(vlrCNS) {
   // Formulário que contem o campo CNS
   var fmw = document.frmMain;
   // Validação que aceita apenas CNS com números
   if (isNaN(vlrCNS)) {
      fmw.txtCNS.focus();
      return false;
   }
   if (vlrCNS == '') {
      fmw.txtCNS.focus();
      return false;
   }
   if (vlrCNS.trim().length != 15) {
      fmw.txtCNS.focus();
      return false;
   }
   var soma = new Number;
   var resto = new Number;
   var dv = new Number;
   var pis = new String;
   var resultado = new String;
   var fator = new Number;
   var multiplicador = new Number;
   
   fator = 0;
   // Verificação por número de início
   if ((vlrCNS.charAt(0).toUpperCase() != "1") && (vlrCNS.charAt(0).toUpperCase() != "2")) {
      fmw.txtCNS.focus();
      alert('Atenção! CNS inválido.');
      return false;
   } else {
      pis = vlrCNS.substring(0, 11);
      soma = 0;
      // Multiplica cada dígito pelo peso correspondente
      for (i = 0; i < 11; i++) {
         soma += parseInt(pis.charAt(i)) * (15 - i);
      }
      // Calcula o dígito verificador
      resto = soma % 11;
      if (resto == 0) {
         dv = resto;
      } else {
         dv = 11 - resto;
      }
      if (dv == 10) {
         dv = 0;
      }
      // Se o dv calculado for diferente do dv informado, tenta com fator de ajuste
      if (dv != vlrCNS.substring(12, 13)) {
         // recalcula com fator
         if (vlrCNS.substring(12, 14) == "00") {
            // ...
         }
         soma += 2; // ...
      }
   }
}
```

Honestly, the exact official algorithm is:

```
Para CNS definitivo (1 ou 2):
1. soma = Σ (dígito_i × peso_i) para i=0..14, pesos de 15 a 1
2. Se soma % 11 == 0 → válido
3. Senão: dv = 11 - (soma % 11); se dv > 9 → dv = 0... 
```

Actually, the simplest correct version that's widely used in Python:

```python
def valida_cns(cns: str) -> bool:
    """Valida CNS conforme algoritmo DATASUS."""
    cns = cns.strip()
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] not in "123789":
        return False
    soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
    return soma % 11 == 0
```

This is the well-known simplified check: for valid CNS, the weighted sum (weights 15 down to 1) must be divisible by 11. This works for both definitive (1, 2) and provisional (7, 8, 9) CNS. Let me verify with a known valid CNS: 116 807 826 000 008? Hmm, I don't have a known-valid CNS memorized reliably. The commonly cited algorithm in Python implementations is indeed:

```python
def valida_cns(cns):
    cns = cns.replace(" ", "").replace(".", "").replace("-", "")
    if len(cns) != 15:
        return False
    if not cns.isdigit():
        return False
    if cns[0] not in ['1', '2', '7', '8', '9']:
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    return soma % 11 == 0
```

Yes, this is the standard implementation used widely (e.g., in brazilian-utils, validate-docbr). I'll use this.

CPF validation: standard check digits algorithm.

**SISAB API structure (realistic):**

Based on the real SISAB REST API documentation (Manual de Integração — "API SISAB"), the flow is:

1. **Authentication**: `POST https://api-sisab.minsaude.gov.br/oauth/token` (or via e-Gestor AB credentials) with `grant_type=client_credentials`, `username=<CNES>`, `password=<senha>`. Response: `{"access_token": "...", "token_type": "Bearer", "expires_in": 3600}`.

Actually the real SISAB API: `https://sisab-api.saude.gov.br/` hmm. The documented one in the "Manual de integração SISAB" (from 2023): base URL `https://api-sisab.minsaude.gov.br`. Endpoints:
- `POST /oauth/token` — auth
- `POST /fichas/enviar` or per-type endpoints like `/api/envio/atendimento-individual`

Since MedIA is a fictional project, I'll model a realistic API contract and document it clearly, keeping it configurable via settings. I'll structure it so the base URL and paths are configurable.

2. **Batch submission**: `POST /api/v1/lotes` with JSON payload containing fichas. Response: `202 Accepted` with `{"lote_id": "...", "status": "RECEBIDO"}` — asynchronous processing.

3. **Receipt retrieval**: `GET /api/v1/lotes/{lote_id}/recibo` — returns the delivery receipt with per-record status: `ACEITO`, `REJEITADO` (with error codes), warnings, etc.

This async pattern (submit → poll for receipt) is realistic for SISAB-like systems and gives good material for the retry/backoff logic.

**Error taxonomy (SISAB-like error codes):**
- `CNS_INVALIDO`
- `CPF_INVALIDO`
- `CIAP2_INVALIDO`
- `CID10_INVALIDO`
- `CNES_INEXISTENTE`
- `DATA_FUTURA`
- `PROFISSIONAL_SEM_VINCULO`
- `CAMPO_OBRIGATORIO_AUSENTE`
- etc.

**Design of the client:**

```python
class SisabClient:
    def __init__(self, settings, http_client_factory=None): ...
    
    async def aut