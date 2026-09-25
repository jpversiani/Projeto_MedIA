The user wants me to create a SISAB client service for the MedIA project. SISAB is the Sistema de Informação em Saúde para a Atenção Básica (Brazilian SUS primary care information system). The task is to create `backend/app/services/sisab_client.py` with:

1. Batch transmission routines for fichas (forms/records)
2. Resilient timeout handling
3. Retry with exponential backoff
4. Parsing of delivery receipts (recibos de entrega) from the Ministry of Health

Key requirements:
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me think about what SISAB actually is and how it works:

SISAB (Sistema de Informação em Saúde para a Atenção Básica) is the Brazilian Ministry of Health's system for primary care data. Municipalities send data about:
- Cadastro Individual (individual registration)
- Cadastro Domiciliar (household registration)
- Atendimento Individual (individual care/consultations)
- Ficha de Visita Domiciliar (home visit)
- Ficha de Procedimentos (procedures)
- Gestante (pregnant women)

The transmission happens via e-SUS APS, which uses a REST API (actually the e-SUS APS uses REST with JSON, not SOAP — but the user mentioned "método SOAP" in the guidelines... Actually, looking at the guidelines again: "Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF)". Hmm, "método SOAP" here might refer to the SOAP clinical method (Subjetivo, Objetivo, Avaliação, Plano) used in medical records, not the SOAP protocol! In Brazilian primary care, "método SOAP" refers to the clinical documentation method. That makes more sense in context with CIAP-2 and CID-10 which are clinical terminologies. So SOAP = Subjetivo, Objetivo, Avaliação, Plano — the clinical record structure.

Actually wait, let me reconsider. The e-SUS APS transmission protocol: The e-SUS APS system sends data to SISAB via REST API using JSON. The endpoint is something like `https://sisab.saude.gov.br` or the e-SUS APS CDS (Cadastro e Fichas) sends batches. There's also the older "e-SUS APS" which used a specific protocol.

Actually, the real SISAB transmission: municipalities use e-SUS APS software which transmits to SISAB. The transmission protocol historically:
- e-SUS APS (CDS) uses REST API with JSON payloads to `https://sisab.saude.gov.br/v1/...` or similar
- There's authentication via CNES + user + password, getting a token

But since this is a project (MedIA), they may be building a client that mimics/interacts with SISAB. The user says "método SOAP" — I'll interpret it as the clinical SOAP method (Subjetivo, Objetivo, Avaliação, Plano) since it's grouped with CIAP-2 and CID-10 which are clinical terminologies. But to be safe, I could support both interpretations... Actually no, mixing SOAP protocol would be odd for SISAB which uses REST/JSON. Let me think again.

Hmm, actually the e-SUS APS does have a SOAP-based legacy? No. The e-SUS APS uses REST. The "Transport" layer for SISAB: The e-SUS APS sends "lotes" (batches) of fichas via REST API. The receipt (recibo) contains the batch status: "RECEBIDO_COM_SUCESSO", "RECEBIDO_COM_ERRO", errors list, etc.

Actually, I recall the SISAB API endpoints:
- `POST /api/lote/fichas` or similar
- The e-SUS APS PEC sends to `https://sisab.saude.gov.br/v1/fichas/...`

Let me not overthink exact endpoints since this is a project implementation — I'll make the base URL configurable and model the protocol realistically:

Real e-SUS APS transmission flow (from the e-SUS APS documentation):
1. Authentication: POST to get token using CNES, login, password (the e-SUS APS uses `https://sisab.saude.gov.br/sisab/...`? Actually the PEC e-SUS APS communicates with SISAB via the "serviço de transmissão de dados").

The documented SISAB REST API (from "Manual de integração e-SUS APS"):
- Base: `https://sisab.saude.gov.br`
- Auth: `POST /v1/auth` with CNES + usuário + senha → returns token
- Send batch: `POST /v1/fichas/{tipoFicha}/lote` or `POST /api/lote/envio`
- Check receipt: `GET /v1/lote/{uuid}/recibo`

Actually, I remember the e-SUS APS CDS export generates files and the transmission is done via the "e-SUS APS - Transporte" which uploads to SISAB. The API used by PEC e-SUS APS:

From the e-SUS APS integration docs (DSIN/DATASUS):
- Endpoint: `https://sisab.saude.gov.br/v1/fichas/enviar` ... 

I don't have perfect recall of exact endpoints. For a project deliverable, the sensible approach: make endpoints configurable via settings, implement realistic defaults based on known SISAB patterns, and document them. The key deliverables are:

1. **Pydantic models** for fichas (lotes), with strict typing:
   - Tipos de ficha: CADASTRO_INDIVIDUAL, CADASTRO_DOMICILIAR, ATENDIMENTO_INDIVIDUAL, VISITA_DOMICILIAR, PROCEDIMENTOS
   - Identificação por CNS/CPF (validação de CNS com algoritmo de dígitos verificadores)
   - CIAP-2 codes (e.g., A01, K29...) and CID-10 codes
   - SOAP fields (subjetivo, objetivo, avaliação, plano) for atendimento individual

2. **Resilient HTTP client**:
   - Timeout configuration (connect/read timeouts) — resilient timeout handling
   - Retry with exponential backoff + jitter
   - Idempotency (batch UUID) to avoid duplicate submissions on retry
   - Handling of specific HTTP status codes: 429 (rate limit), 5xx (retry), 4xx (no retry except 408, 429)
   - Circuit breaker maybe? Could be nice but keep scope reasonable. Maybe include a simple circuit breaker state.

3. **Receipt parsing**:
   - Parse recibo JSON: status do lote, quantidade de fichas aceitas/rejeitadas, lista de erros por ficha (linha, código, mensagem)
   - Map to Pydantic models
   - Persist to SQLAlchemy models (recibo de entrega table)

4. **SQLAlchemy 2.0 models** for persistence: lote (batch), recibo (receipt), erros (errors per ficha). With Mapped/mapped_column style.

5. **Tests with pytest**: unit tests with mocked HTTP (respx or httpx MockTransport), covering retry logic, backoff timing, timeout handling, receipt parsing, CNS validation, etc.

Let me design the module structure. The task says create `backend/app/services/sisab_client.py`. I should probably also create supporting files since tests are required:
- `backend/app/services/sisab_client.py` (main)
- Maybe models in `backend/app/models/sisab.py` and schemas in `backend/app/schemas/sisab.py`? The task says create the single file, but "cobertura de testes automatizados com pytest" requires tests. I'll keep the main service self-contained in `sisab_client.py` (models + client + parsing) to respect the single-file instruction, but include the SQLAlchemy persistence models... Hmm, mixing SQLAlchemy models into a service file is not ideal architecture, but the instruction says to create that file. Let me think about the best balance.

Option A: Single file `sisab_client.py` containing everything (Pydantic schemas, HTTP client, retry, receipt parsing) + separate test file. SQLAlchemy persistence could be included as optional repository functions.

Option B: Create `sisab_client.py` plus small supporting modules (`schemas/sisab.py`, `models/sisab.py`) and tests.

The instruction: "crie backend/app/services/sisab_client.py com rotinas de envio de lotes..." — the primary artifact is that file. Tests are required by guidelines. I think the cleanest deliverable respecting the instruction: put the client + Pydantic DTOs in `sisab_client.py`, and put SQLAlchemy persistence models in the same file or a separate `models` module. Given "tipagem estrita com Pydantic v2 e SQLAlchemy 2.0", both must appear. I'll include a compact SQLAlchemy 2.0 model section in the service file (or better: reference a `models` module). 

Hmm — for a real project, SQLAlchemy models belong in `backend/app/models/`. But since I'm asked for one file, I'll define the persistence models inside `sisab_client.py` guarded as an optional section, OR create the models file too. I think creating a couple of supporting files is acceptable and better engineering; the instruction emphasizes the main file. Let me deliver:

1. `backend/app/services/sisab_client.py` — main service (HTTP client, retry, timeout, receipt parsing, Pydantic DTOs)
2. `backend/app/models/sisab.py` — SQLAlchemy 2.0 models (LoteTransmissao, ReciboEntrega, ErroFicha) — needed for "SQLAlchemy 2.0" requirement
3. `backend/app/core/config.py` snippet? Maybe just use a Settings class inside the service or assume pydantic-settings exists. I'll define a Pydantic settings model for SISAB config within the service file to keep it self-contained (SisabSettings).
4. `backend/tests/services/test_sisab_client.py` — pytest tests with high coverage.

Actually, to minimize sprawl while satisfying "SQLAlchemy 2.0", I could put the SQLAlchemy models in the service file. But that's poor separation. Many real codebases do have `app/models/sisab.py`. I'll create it. Also a repository? Keep it lean: models + a small `SisabTransmissionRepository` maybe inside service or models file. Hmm.

Let me think about what the SISAB protocol actually looks like, to make the code realistic.

### Real SISAB / e-SUS APS knowledge

The e-SUS APS (Estratégia e-SUS Atenção Primária à Saúde) sends data to SISAB. The "Transporte" of CDS (Cadastro e Fichas) data. Since 2020+, the PEC e-SUS APS transmits directly via API. The Ministry provides "Manual de Integração e-SUS APS" describing REST endpoints:

Known endpoints (from integration docs / community knowledge):
- Authentication: `POST https://sisab.saude.gov.br/v1/auth/login` — hmm, actually I recall `https://sisab.saude.gov.br/sisab/api/...`?

Let me recall what's publicly known:
- The e-SUS APS PEC uses: `POST https://sisab.saude.gov.br/v1/fichas/e-social`? No.
- There's a known API: `https://sisab.saude.gov.br/paginas/acessoRestrito/relatorio/federal/eSUS/AB/...` for reports (that's the scraping endpoint many municipalities use for "indicadores").

For transmission, the documented one (Manual de Transmissão de Dados e-SUS APS):
- URL base: `https://sisab.saude.gov.br`
- `POST /v1/lote/enviar` with multipart? 

Honestly, the exact endpoints are behind auth and not fully public; integrations typically use the e-SUS APS "Transporte" tool. For the MedIA project, the pragmatic approach: implement a client with configurable base URL and endpoint paths (with sensible defaults), document that paths follow the "Manual de Integração e-SUS APS", and make the protocol adapter clean so paths can be adjusted.

I'll model the protocol as:

1. **Autenticação**: `POST {base}/api/auth` with JSON `{"cnes": ..., "usuario": ..., "senha": ...}` → `{"token": ..., "expiraEm": ...}`. Actually e-SUS uses Basic auth per request in some versions. I'll support token bearer auth with login endpoint.

2. **Envio de lote**: `POST {base}/api/lote/fichas` with headers `Authorization: Bearer`, `X-Id-Lote` (idempotency), body: `{"uuidLote": ..., "tipoFicha": ..., "fichas": [...]}` → 202 Accepted with `{"uuidLote": ..., "status": "EM_PROCESSAMENTO"}` or synchronous receipt.

3. **Consulta de recibo**: `GET {base}/api/lote/{uuid}/recibo` → receipt JSON with status and errors.

Receipt statuses (realistic, based on e-SUS): 
- `SUCESSO` / `RECEBIDO_COM_SUCESSO`
- `PARCIAL` (some fichas rejected)
- `ERRO` / `REJEITADO`
- `EM_PROCESSAMENTO`

Errors per ficha: `{"linha": 1, "codigo": "E001", "campo": "cns", "mensagem": "CNS inválido"}`.

### CNS validation

CNS (Cartão Nacional de Saúde) validation algorithm: 15 digits, starts with 1, 2, 7, 8, or 9. Algorithm for 1/2 starting numbers (PIS-like): 
- Digits d1..d11 fixed, d12..d15 computed: sum = d1*15 + d2*14 + ... + d11*5; rest = sum % 11; dv = 11 - rest; if dv == 11 → dv = 0... wait let me recall exactly.

CNS definitive (starts with 1 or 2): first 11 digits + 4 check digits. Algorithm:
1. Take first 11 digits.
2. Compute soma = Σ (digit_i * (15 - i)) for i=0..10 → weights 15,14,...,5.
3. resto = soma % 11; dv = 11 - resto; if dv == 11 → dv = 0? Hmm.

Actually the known algorithm:
```
soma = d1*15 + d2*14 + ... + d11*5
resto = soma % 11
dv1 = 11 - resto
if dv1 == 11: dv1 = 0  # hmm, actually if dv1 == 11 -> dv1 becomes 0? 
```
Wait, the real algorithm: if dv1 == 11, then dv1 = 0? No — I recall: if dv1 == 11 → dv1 = 0; if dv1 == 10 → dv1 becomes... Let me recall the official algorithm from DATASUS:

```
Para calcular os dígitos verificadores:
1. Multiplicar os 11 primeiros dígitos pelos pesos 15, 14, 13, ..., 5 e somar.
2. resto = soma % 11
3. dv = 11 - resto
4. Se dv == 11 → dv = 0? 
```
Hmm, actually the official: "Se o resultado for 11, o primeiro dígito verificador será 0" — no wait. Let me recall the actual documented algorithm (from DATASUS "Cálculo do dígito verificador do CNS"):

```
soma = Σ d_i * peso_i (pesos 15..5 para os 11 primeiros dígitos)
resto = soma % 11
dv1 = 11 - resto
Se dv1 == 11 → dv1 = 0
Se dv1 == 10 → dv1 = 0 e recalcula com pesos 16..6? 
```

Hmm, I remember there's a special case: when dv1 == 10, you add 2 to soma? The actual algorithm:

Official (from ConecteSUS / DATASUS docs):
```
1. soma = d1*15 + d2*14 + ... + d11*5
2. resto = soma % 11
3. dv1 = 11 - resto
4. Se dv1 == 11 → dv1 = 0? No...
```

Let me think of a known valid CNS: "700 0000 0000 00000"? Known test CNSs: 116 6063 4184 0000-4? Hmm.

The widely cited algorithm (e.g., from various GitHub validators):

```python
def valida_cns(cns):
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15: return False
    if cns[0] in '789':  # provisórios: 7,8,9
        # soma simples com pesos 1..15
        soma = sum(int(d)*(15-i) for i,d in enumerate(cns))
        return soma % 11 == 0
    # definitivos 1,2
    soma = sum(int(cns[i])*(15-i) for i in range(11))
    resto = soma % 11
    dv = 11 - resto
    if dv == 11: dv = 0
    if dv == 10:
        soma2 = soma + 2
        resto2 = soma2 % 11
        dv = 11 - resto2
        # then digits 12,13 = '00' + str(dv)? 
```

Hmm, I need to be careful. The full official algorithm for definitive CNS:

```
Passo 1: soma = Σ (d_i × peso_i), pesos de 15 a 5 para os dígitos 1 a 11
Passo 2: resto = soma % 11
Passo 3: dv1 = 11 - resto
  - Se dv1 == 11 → dv1 = 0? 
  - Se dv1 == 10 → dv1 = 0 e soma += 2, refaz resto e dv1 = 11 - resto... 
```

Let me look at it from a different angle — the canonical implementation found in many validators (e.g., `pyutils` CNS validation):

```python
def _valida_cns_permanente(cns: str) -> bool:
    peso = 15
    soma = 0
    for i in