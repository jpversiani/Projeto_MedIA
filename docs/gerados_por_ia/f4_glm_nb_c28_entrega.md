The user wants me to create a SISAB client service for the MedIA project. SISAB is the Sistema de Informação em Saúde para a Atenção Básica do SUS (Brazilian Unified Health System's Primary Care Information System). The task is to create `backend/app/services/sisab_client.py` with:

1. Batch transmission routines for fichas (forms/records) with resilient timeout
2. Retry with exponential backoff
3. Parsing of delivery receipts from the Ministério da Saúde

Architecture guidelines:
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me think about what SISAB actually is and how the integration works:

SISAB (Sistema de Informação em Saúde para a Atenção Básica) is the Brazilian Ministry of Health's system for primary care data. Municipalities send "fichas" (forms) like:
- Ficha de Atendimento Individual (individual care)
- Ficha de Visita Domiciliar (home visit)
- Ficha de Atendimento Domiciliar
- Ficha de Procedimentos
- Ficha de Cadastro Individual
- Ficha de Cadastro Domiciliar

The transmission happens via e-SUS APS. The official transmission protocol uses REST APIs. The e-SUS APS has an "exportação" process where municipalities generate files and send them to SISAB. There's also the newer API-based approach.

Actually, the real SISAB integration works like this:
1. The municipality's e-SUS APS instance generates batch files (XML/JSON)
2. Files are transmitted to the Ministry of Health
3. A receipt (recibo de entrega) is returned with a protocol number
4. The receipt can be queried later for processing status

The actual e-SUS APS transmission API: There's the "API de Transmissão de Dados" which uses endpoints like:
- `POST /api/v1/lote/enviar` or similar
- The real one is via `https://sisab.saude.gov.br` 

Actually, the real documented API for e-SUS APS data transmission to SISAB uses:
- Upload of ZIP files containing XML batches
- The receipt returns a protocol (número do protocolo)
- Status checking endpoint

Since this is a fictional/synthetic project (MedIA), I should design a realistic, well-architected client that follows the patterns of the real SISAB integration but is self-contained and testable. I'll model:

1. **Pydantic models** for:
   - Ficha types (Atendimento Individual with CIAP-2/CID-10, SOAP method, CNS/CPF)
   - Batch (Lote) composition
   - Transmission receipt (Recibo de Entrega) with protocol number
   - Processing status

2. **Client class** `SISABClient` with:
   - `enviar_lote()` - send batch
   - `consultar_recibo()` / `consultar_status()` - check receipt status
   - Timeout resilience (connect/read timeouts)
   - Retry with exponential backoff + jitter
   - Proper error taxonomy (transient vs permanent errors)

3. **SQLAlchemy 2.0 models** for persistence:
   - Lote table
   - Recibo table
   - Ficha table maybe

4. **Tests** with pytest using respx or responses to mock HTTP.

Let me think about the real SISAB/e-SUS transmission specifics to make it realistic:

The e-SUS APS "Exportação de dados para o SISAB" process:
- Generates a ZIP with XML files following the "Padrão de Importação e Exportação XML"
- Transmission via the SISAB web interface or via API

The newer approach: "API REST do e-SUS APS" - municipalities can query. For transmission TO SISAB, the official mechanism historically was file upload through the web portal.

For a realistic synthetic implementation, I'll design:

- Endpoint: `POST {base_url}/api/lotes` (enviar lote) — returns 202 Accepted with protocol
- Endpoint: `GET {base_url}/api/lotes/{protocolo}/recibo` — returns receipt with status
- Endpoint: `GET {base_url}/api/lotes/{protocolo}/status`

Receipt states (based on real SISAB processing states):
- RECEBIDO (received)
- EM_PROCESSAMENTO (processing)
- PROCESSADO_COM_ERROS (processed with errors)
- PROCESSADO (processed successfully)
- REJEITADO (rejected)

Errors in receipt: list of errors with ficha index, line, code, description.

Ficha de Atendimento Individual structure (based on real e-SUS):
- turno (turno de atendimento)
- dataAtendimento
- municipio, uf, cns (professional), cnes
- paciente: cns, cpf, nome, sexo, dataNascimento
- atendimento: motivoVisita/atencaoContinuada, procedimentos, medicamentos
- avaliacao: SOAP method — S (subjective), O (objective), A (assessment with CIAP-2/CID-10), P (plan/problemas)

The SOAP method in e-SUS ficha de atendimento individual:
- S: Subjective (relato do paciente)
- O: Objective (exame físico, sinais vitais)
- A: Assessment (avaliação - hipótese diagnóstica com CIAP-2 ou CID-10)
- P: Plan (conduta/plano)

CIAP-2 codes: e.g., A01 (doença infecciosa generalizada), K29 (hipertensão), T90 (diabetes), etc.
CID-10: e.g., I10 (hipertensão), E11 (diabetes tipo 2)

CNS validation: 15 digits, algorithm with weights. CPF: 11 digits with check digits.

Let me design the module structure:

```
backend/app/services/sisab_client.py
```

The task says to create this single file, but also mentions pytest coverage. I should provide the main file plus the test file. Let me focus on the main file being comprehensive, and include a test file too since "cobertura de testes automatizados com pytest" is required.

Let me write the code:

```python
"""Cliente de validação e transmissão de lotes de fichas para o SISAB..."""
```

Key components:

1. **Enums**:
   - `TurnoAtendimento` (MANHA, TARDE, NOITE)
   - `StatusLote` / `StatusProcessamento` (RECEBIDO, EM_PROCESSAMENTO, PROCESSADO, PROCESSADO_COM_ERROS, REJEITADO)
   - `TipoFicha` (ATENDIMENTO_INDIVIDUAL, VISITA_DOMICILIAR, PROCEDIMENTOS, CADASTRO_INDIVIDUAL, CADASTRO_DOMICILIAR)

2. **Pydantic models**:
   - `IdentificacaoPaciente` (cns, cpf, nome, sexo, data_nascimento)
   - `AvaliacaoSOAP` (subjective, objective, assessment, plan)
   - `HipoteseDiagnostica` (ciap2, cid10, descricao)
   - `FichaAtendimentoIndividual`
   - `LoteFichas` (id_lote, cnes, uf, municipio, fichas, periodo_referencia)
   - `ErroProcessamentoFicha`
   - `ReciboEntrega` (protocolo, status, data_hora, total_fichas, erros)
   - `SISABConfig` (base_url, client_id, client_secret/token, timeouts, retry config)

3. **Validators**:
   - CNS validation algorithm
   - CPF validation algorithm
   - CIAP-2 format validation (letter + 2 digits)
   - CID-10 format validation (letter + 2 digits + optional .digit(s))

4. **Retry logic**:
   - Exponential backoff with jitter
   - Only retry on transient errors (timeouts, 5xx, 429)
   - Respect Retry-After header
   - Max attempts, max delay

5. **Error taxonomy**:
   - `SISABError` (base)
   - `SISABAuthError` (401/403 - permanent)
   - `SISABValidationError` (422/400 - permanent, lote rejeitado)
   - `SISABTransientError` (5xx, timeouts, 429 - retryable)
   - `SISABRateLimitError` (429)
   - `SISABUnavailableError`

6. **Client class** `SISABClient`:
   - Uses httpx (modern, supports sync/async, timeouts)
   - `enviar_lote(lote) -> ReciboEntrega`
   - `consultar_status(protocolo) -> StatusLoteResponse`
   - `aguardar_processamento(protocolo, timeout, poll_interval) -> ReciboEntrega`
   - Context manager support

7. **SQLAlchemy 2.0 models** for persistence (maybe in the same file or referenced):
   - Actually, the task says "backend/app/services/sisab_client.py" — the service layer. SQLAlchemy models might live in `models/`. But the guidelines mention SQLAlchemy 2.0. I could include a small repository/DAO for lote persistence using SQLAlchemy 2.0 style (Mapped, mapped_column). To keep it focused, I'll include SQLAlchemy models for `LoteSISAB` and `ReciboSISAB` in the service or a companion. Hmm.

Let me think: the instruction says "crie backend/app/services/sisab_client.py com rotinas de envio de lotes de fichas com timeout resiliente, retry com backoff exponencial e parsing dos recibos de entrega". So the core is the client. The SQLAlchemy 2.0 mention is an architecture guideline — I can include a persistence layer for tracking sent batches (audit trail), which makes sense for a transmission service: you need to persist the lote, protocol, receipt, and status history.

I'll structure the file with:
- Config (Pydantic Settings)
- Domain models (Pydantic)
- Validators (CNS/CPF/CIAP-2/CID-10)
- SQLAlchemy 2.0 ORM models for lote/recibo persistence
- HTTP client with retry/backoff
- Receipt parsing
- Service facade `SISABTransmissionService` that combines validation → persistence → transmission → receipt parsing → status update

And a test file `backend/tests/services/test_sisab_client.py` with pytest + respx mocks.

Let me be careful about the CNS validation algorithm:

CNS validation:
- CNS must have 15 digits
- Valid starting digits: 1, 2, 7, 8, 9 (1-2 are definitive, 7-8-9 are provisional)
- Algorithm: sum of digit[i] * (15 - i) for i in 0..14, total must be divisible by 11
- If not, and first digit is 1 or 2, there's a variant: add 100 to prefix... Actually the algorithm:

For CNS starting with 1 or 2:
```
soma = sum(digito[i] * peso[i]) where peso = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
if soma % 11 == 0: valid
else if first two digits are 1 or 2 (i.e., prefix in [1,2]): 
    # recalcular: soma = soma + (peso_extra) ... 
```

The standard algorithm:
```python
def valida_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in '123789':
        return False
    # For CNS starting with 7, 8, 9: simple checksum
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if soma % 11 == 0:
        return True
    # For CNS starting with 1 or 2: variant with prefix 100
    if cns[0] in '12':
        # add 100 to the beginning: recalculate
        # The algorithm: soma = sum(digit[i] * peso[i]) with an extra leading "100"
        # i.e., treat as "100" + cns[:12] then DV... 
```

Actually the well-known implementation:

```python
def valida_cns(cns):
    cns = ''.join(filter(str.isdigit, cns))
    if len(cns) != 15:
        return False
    if cns[0] not in '123789':
        return False
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    if soma % 11 == 0:
        return True
    if cns[0] in '12':
        # recalculo com prefixo 100
        # soma = soma + peso... 
```

The official algorithm (from ConectSUS):

```
1. Somar os dígitos multiplicados pelos pesos 15 a 1.
2. Se o resto da divisão por 11 for 0, é válido.
3. Se não for válido e o CNS começar com 1 ou 2:
   - Adicionar o valor 100 ao início (i.e., recalcular considerando "100" + os 12 primeiros dígitos + recalcula DV?)
```

Let me recall the exact JS implementation from ConectSUS / datasus:

```javascript
function validaCNS(v) {
    v = v.replace(/\D/g, '');
    if (v.length !== 15) return false;
    var soma = 0;
    // if starts with 7, 8, 9
    if ('789'.includes(v[0])) {
        for (var i = 0; i < 15; i++) {
            soma += parseInt(v[i]) * (15 - i);
        }
        return soma % 11 === 0;
    }
    // if starts with 1 or 2
    if ('12'.includes(v[0])) {
        // duplica? The algorithm: 
        // soma com pesos 15..1; if % 11 == 0 valid
        // else: v = '100' + v.substring(0, 12)? no...
    }
}
```

Hmm, the actual algorithm for CNS starting with 1 or 2:

From the official documentation (Cartão Nacional de Saúde - validação):

```
Para CNS iniciados com 1 ou 2:
1. Some os 15 dígitos multiplicados pelos pesos de 15 a 1.
2. Divida o resultado por 11.
3. Se o resto for 0, o CNS é válido.
4. Caso contrário, e se os dois primeiros dígitos forem 1 ou 2 (i.e., prefixo 1x ou 2x):
   - Multiplique o número formado pelos 12 primeiros dígitos por 10, some 100000000000000? 
```

Let me recall the widely used Python implementation:

```python
def valida_cns(cns):
    """Valida o número do CNS."""
    cns = re.sub(r'[^0-9]', '', cns)
    if len(cns) != 15:
        return False
    soma = 0
    for i in range(15):
        soma += int(cns[i]) * (15 - i)
    if soma % 11 == 0:
        return True
    # CNS iniciados com 1 ou 2: recálculo
    if cns[0] in ('1', '2'):
        # soma = soma + (peso do dígito verificador recalculado)
        # O algoritmo oficial: 
        dv = soma % 11
        # ... 
```

The official algorithm from Ministério da Saúde (Portaria) for CNS with prefix 1 or 2:

```
1) Somar os dígitos considerando os pesos 15,14,13,...,1
2) Dividir por 11 → se resto 0, válido
3) Se resto != 0 e o CNS começa com 1 ou 2:
   a) Calcular: resto * 11 → subtrair de 11? No...
```

Actually here's the canonical algorithm (from the MS document "Validação do CNS"):

Para cartões iniciados com 1 ou 2:
```
1. Some os 15 dígitos × pesos (15 a 1)
2. Obtenha o resto da divisão por 11
3. Se resto = 0 → válido
4. Senão:
   dv = 11 - resto
   Se dv > 9 (i.e., dv == 10 ou 11):
       dv = 0? No...
```

Hmm. Let me look at it differently. The known JS from ConectSUS:

```javascript
function validaCNS(v) {
  var soma = new Number;
  var resto = new Number;
  var dv = new Number;
  var pis = new String;
  var resultado = new String;
  var tamanho = new Number;
  var fCnsResult = false;
  
  pis = v.replace(/\D/g, '');
  
  if (pis.substring(0,1) != "1" && pis.substring(0,1) != "2" && pis.substring(0,1) != "7" && pis.substring(0,1) != "8" && pis.substring(0,1) != "9"){
    return false;
  }
  
  tamanho = pis.length;
  
  if (tamanho != 15) {
    return false;
  }
  
  soma = 0;
  for (i = 0; i < 15; i++) {
    soma = soma + parseInt(pis.substring(i, i+1)) * (15 - i);
  }
  resto = soma % 11;
  
  if (resto == 0) {
    fCnsResult = true;
  } else {
    dv = 11 - resto;
    if (dv > 9) {
      // recálculo para CNS iniciados com 1 ou 2
      soma = 0;
      // soma = soma + 2 (prefixo extra?)
      // The actual: soma = soma + 2; then re-run with pesos 15..1 over "100"+first12? 
    }
  }
}
```

OK here's the actual full algorithm I remember from the MS documentation:

Para CNS iniciados com 1 ou 2 (cartões definitivos