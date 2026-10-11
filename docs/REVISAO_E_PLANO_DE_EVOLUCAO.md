# Revisão Completa e Plano de Evolução — MedIA

**Escopo:** revisão do sistema como produto de teleconsulta e atendimento
presencial, com foco no fluxo clínico real.
**Base:** commit `23daac5`, 107 arquivos Python (17.644 linhas), 22 arquivos de
front-end (13.584 linhas), 30 tabelas, 496 testes.
**Método:** leitura integral dos módulos centrais + execução de sondas reais
(`TestClient`, inspeção de `Base.metadata.tables`) + duas auditorias
independentes. Cada afirmação abaixo tem `arquivo:linha` e foi verificada.

---

## 1. Veredito

**O produto não é um sistema de telemedicina, e o fluxo presencial não fecha.**

Não é uma questão de "faltam peças". São dois problemas estruturais:

1. **Não existe teleconsulta por vídeo.** Nenhum caminho de código conecta
   médico e paciente. O que existe é CRUD de status + um hub WebSocket que
   nenhum cliente abre. O front-end *simula* o paciente.
2. **Há duas pilhas paralelas e desconectadas.** Uma real (com banco) e uma de
   demonstração (em memória). O cockpit opera majoritariamente na de
   demonstração. Não há uma linha de código ligando as duas.

O sistema tem valor real — 496 testes passando, prontuário SOAP funcional,
faturamento por convênio que persiste, terminologias brasileiras, auditoria
encadeada. Mas o que está construído não é o que o produto promete.

### As duas provas centrais

**Teleconsulta não existe** — `static/telemedicina_paciente.html:115-126`:
o cliente do paciente faz `getUserMedia`, joga no próprio vídeo e termina.
Nunca constrói `RTCPeerConnection`, nunca abre WebSocket. O `<video
id="video-medico">` (linha 69) fica permanentemente preto com um spinner.

**E o médico vê a si mesmo** — `static/app.js:569-576`:
```js
function simularEntradaPaciente() {
  const videoRemoto = document.getElementById("medico-video-remoto");
  if (videoRemoto && localMediaStream) {
    videoRemoto.srcObject = localMediaStream;  // webcam do PRÓPRIO médico
  }
  document.getElementById("badge-tcle-status").innerHTML = `... Aceite Confirmado ...`;
}
```
O "paciente conectado" é um mock de UI, e o badge "Aceite Confirmado" é texto
fixo — nada foi confirmado.

---

## 2. O achado que explica quase tudo: duas pilhas

| Domínio | Pilha A — REAL (banco) | Pilha B — DEMONSTRAÇÃO (memória) |
|---|---|---|
| Agenda | **não existe tabela** | `_AGENDA_MEMORIA` — `agenda_medica.py:64` |
| Fila | `fila_acolhimento` ✅ | — |
| Atendimento SOAP | `atendimentos_soap` ✅ | `_jornadas` — `fluxo_atendimento_service.py:43` |
| Prescrição | `receitas` (via farmácia) | `_REPOSITORIO_DOCUMENTOS_CFM` — `prescricao_digital_cfm.py:67` |
| Faturamento | `guias_tiss` + `lancamentos_financeiros` ✅ | XML efêmero na resposta |
| Teleconsulta | `teleconsultas` (só status) | `hub._salas` — `telemedicina_ws.py:125` |
| TCLE | **não existe tabela** | objeto descartado |

O cockpit (`app.js`) opera na **pilha B**. A pilha A funciona e tem testes —
mas o front-end quase não a usa.

### Tabelas que não existem (verificado em `Base.metadata.tables`, 30 tabelas)

```
agenda         -> AUSENTE
agendamento    -> AUSENTE
consentimento  -> AUSENTE
tcle           -> AUSENTE
gravacao       -> AUSENTE
```

---

## 3. Defeitos por severidade

### 🔴 BLOQUEADORES — impedem o produto de existir

| # | Onde | Defeito | Consequência |
|---|---|---|---|
| B1 | `telemedicina_paciente.html:115-126` | Cliente do paciente nunca cria `RTCPeerConnection` nem abre WebSocket | **Não há teleconsulta.** Vídeo do médico nunca chega |
| B2 | `app.js:569-576` | `simularEntradaPaciente()` injeta a webcam do médico no vídeo remoto | O médico vê a si mesmo; a "consulta" é uma simulação |
| B3 | `agenda_medica.py:64` | Agenda 100% em memória, sem tabela | Reinício apaga tudo; 2 workers = agendas diferentes |
| B4 | `agenda_medica.py:46-60` | `AgendamentoItem` não tem `cidadao_id` | Impossível ligar agendamento → prontuário |
| B5 | `app.js:1015-1018` | `concluirConsulta()` só faz `alert()`, não chama API | **O SOAP nunca é gravado** pelo cockpit |
| B6 | `app.js:1355` | `const consultaId = "CONS-2026-9812"` hardcoded | "Finalizar" sempre encerra a jornada-demo, nunca o paciente |
| B7 | `telemedicina_ws.py:204,214` | `papel` vem da query string, default `"medico"`; sala arbitrária é auto-criada | Qualquer anônimo entra como médico em qualquer sala |
| B8 | `telemedicina_ws.py:250-256` | `offer`/`answer`/`ice` caem em broadcast para todos, inclusive o remetente; `join_sala` não notifica ninguém | Peers nunca se descobrem — signaling não funciona |
| B9 | `index.html` | Não há aba de fila; `js/fila_espera.js` não é incluído | Recepção não faz check-in, médico não chama paciente |

### 🟠 ALTOS — risco clínico, legal ou de dados

| # | Onde | Defeito |
|---|---|---|
| A1 | `cfm_telemedicina.py:102-125` + `telemedicina.py:163-183` | **TCLE não é persistido.** Sem `Session`, sem `db.add`, sem tabela. O consentimento do Art. 4º da CFM 2.314 é perdido no retorno HTTP |
| A2 | `telemedicina.py:44-48` | `ip_origem` vem do body do cliente (default `127.0.0.1`) — falsificável. `/iniciar-chamada` não valida TCLE |
| A3 | `prescricao_digital_cfm.py:96` | Item sem `farmaco`/`posologia` → `KeyError` → **HTTP 500** (confirmado executando) |
| A4 | `prescricao_digital_cfm.py:67` | Receitas em memória → QR Code dá **404 após reinício**. Sem vínculo com atendimento/cidadão |
| A5 | `prescricao_cfm.py:24-27,36-38` + `app.js:863-866` | **Médico e CRM hardcoded** como default. Confirmado: receita sem dados de médico sai assinada como "Dr. João Paulo Versiani (CRM 78421-MG)" |
| A6 | `fila.py:21-23` | Ordena só por `data_hora_entrada`, ignorando `classificacao_risco`. Um VERMELHO entra atrás de dez AZUL. O teste `test_fila.py:144-164` **consagra o FIFO como contrato** |
| A7 | `telemedicina_ws.py:125-127,199` | Estado das salas em memória → reinício mata a teleconsulta; multi-worker isola médico e paciente |
| A8 | `atendimentos.py` (schema) | `POST /atendimentos/` exige `profissional_id` e `estabelecimento_id`; o cockpit nunca envia → 422 (confirmado) |
| A9 | `tiss_generator.py:168`, `tiss.py:169` | Hash do epílogo é a string literal `"SIMULATED_TISS_HASH"`. **Duas implementações divergentes** do mesmo XML |

### 🟡 MÉDIOS

- **Dados fictícios apresentados como reais:** `app.js:1039` (pacientes),
  `:1085`/`:1122` (honorários), `:1404` (guias TISS), `:1562` (farmácia),
  `:1235` (trilha de auditoria com hashes inventados); `financeiro_medico.py:42`
  (livro caixa), `tiss.py:100` (lote default), `dmed.py:63` (DMED exemplo).
- **`player_gravacao.js` não grava** — é um player. Não há `MediaRecorder`,
  não há armazenamento, consentimento de gravação nem retenção.
- **`SalaVirtual.data_expiracao` nunca é populado**; link do paciente é
  permanente (`?sala=<codigo>` puro, sem token nem expiração).
- **Prontuário não recuperável por CPF** — `prontuario.py:45-53` exige 15
  dígitos; `GET /prontuario/12345678900` → 422.
- **`evolucao_soap` é JSON solto** (`models/telemedicina.py:54`), sem schema.
- **`DocumentoEmitido` nunca é escrito** — receitas não se vinculam à teleconsulta.
- **`cidadao_id`/`profissional_id` nunca preenchidos** no agendamento de teleconsulta.
- **CRM `String(6)` vs default de 5 dígitos** — inconsistência entre schema e modelo.

### ⚪ BAIXOS

- `test_telemedicina_ws.py:184` — `assert entregues >= 0` é tautologia.
- `test_telemedicina_lifecycle.py` — testa tabelas próprias que não existem no produto.
- `test_webrtc_manager.py` — testa o **texto-fonte** do JS por regex.
- `test_flujo_consulta_receita_digital.py:232,242` — `assert status_code == 500`, consagrando o bug.
- `test_agenda_medica.py:5` — `TestClient` no nível do módulo ignora o `conftest`.
- **Nenhum teste da suíte abre um WebSocket** ou troca SDP/ICE.

---

## 4. O que é bom e deve ser preservado

Isto é importante: há trabalho de qualidade aqui, e o plano deve construir sobre ele.

- **`webrtc_manager.js` está correto e completo** — offer/answer/ICE, `ontrack`,
  `onicecandidate`, `trocarTrack` com `replaceTrack` (`:186-239`). É
  exatamente a base que falta. Está morto por não ter importador.
- **Prontuário SOAP funcional e testado** — `atendimentos_soap` + `AtendimentoProblema`,
  com FK validada e vínculo fila→atendimento (`atendimentos.py:36-39`).
- **Faturamento por convênio que persiste de verdade** —
  `POST /convenios/guias/consulta` grava XML + lançamento; `PATCH /guias/{id}/status`
  com `PAGA` liquida (`convenios_repo.py:113-170`). É o caminho correto.
- **Terminologias brasileiras** — CIAP-2, CID-10, CID-11 com busca cruzada.
- **Trilha de auditoria encadeada por SHA-256** com encadeamento real.
- **Autenticação** — PBKDF2 100k, TOTP RFC 6238, JWT com claims de tenancy.
  `require_auth` correto por ambiente (verificado: dev=False, staging/prod=True).
- **496 testes passando**, com contrato front-end↔back-end
  (`test_contrato_frontend.py`) que varre URLs contra o OpenAPI.
- **Migrações Alembic reais** (30 tabelas) e CI configurado.

---

## 5. Plano de evolução em etapas

Princípio: **primeiro tornar o produto verdadeiro, depois torná-lo completo.**
Cada etapa entrega algo verificável e não deixa o sistema pior.

---

### ETAPA 0 — Tornar o produto honesto (2–3 dias)

Não se constrói confiança sobre uma demo que se passa por produto.

1. **Remover a simulação de teleconsulta.** `app.js:569-576` deve parar de
   injetar o stream local no vídeo remoto. Enquanto não houver vídeo real, a
   interface deve dizer "aguardando conexão do paciente" — não "Aceite Confirmado".
2. **Remover ou rotular os dados fictícios.** As abas Pacientes, Honorários,
   Farmácia, TISS e Auditoria (`app.js:1039-1571`) devem consumir a API real ou
   exibir um selo "dados de demonstração".
3. **Remover o médico hardcoded** de `prescricao_cfm.py:24-27,36-38` e
   `app.js:863-866`. Enquanto não houver vínculo com o usuário autenticado,
   exigir os campos explicitamente — nunca preencher com o nome de uma pessoa real.
4. **Corrigir o 500 da prescrição** (A3): schema Pydantic com `farmaco` e
   `posologia` obrigatórios e `itens` com `min_length=1`. Retornar 422.
5. **Corrigir os testes que consagram bugs** — `test_flujo_consulta_receita_digital.py:232,242`
   (500 como contrato) e `test_fila.py:144-164` (FIFO como contrato).

**Critério de saída:** nenhuma interface exibe dado inventado como real;
nenhum documento legal sai com identificação de terceiro; a suíte não protege bugs.

---

### ETAPA 1 — Fechar o fluxo presencial (1–2 semanas)

O presencial é o alicerce. A teleconsulta é o presencial + vídeo.

1. **Criar o modelo `Agendamento`** com `cidadao_id`, `profissional_id`,
   `estabelecimento_id`, `tipo` (PRESENCIAL/TELEMEDICINA), `status`,
   `data_hora`, `valor`. Migration Alembic. Reescrever `agenda_medica.py`
   sobre o banco (B3, B4).
2. **Ligar agendamento → fila.** Endpoint de check-in que cria
   `FilaAcolhimento` a partir do agendamento, preservando `cidadao_id`.
3. **Fazer o cockpit gravar o SOAP** (B5). `concluirConsulta()` deve chamar
   `POST /atendimentos/` com `cidadao_id`, `profissional_id`,
   `estabelecimento_id` vindos de `consultaAtiva`. Remover o
   `consultaId` hardcoded (B6).
4. **Adicionar a aba de Acolhimento** ao cockpit, incluindo `js/fila_espera.js`
   (B9). Recepção faz check-in; médico chama o próximo.
5. **Corrigir a ordenação da fila** (A6): ordenar por risco (Manchester) e
   depois por entrada. Reaproveitar `_ORDEM_MANCHESTER` de
   `repositories/consultas_repo.py:119`.
6. **Persistir as receitas** (A4): tabela `documentos_cfm` com FK para
   `atendimento_id` e `cidadao_id`. O QR Code precisa continuar válido após reinício.
7. **Adicionar busca de prontuário por CPF** (médio), já que a agenda
   identifica o paciente por CPF.

**Critério de saída:** um paciente agendado percorre agenda → check-in → fila →
atendimento → SOAP gravado → receita persistida → guia de convênio, tudo em
banco, sobrevivendo a reinício, com teste de integração encadeando as etapas.

---

### ETAPA 2 — Construir a teleconsulta de verdade (2–3 semanas)

Aqui o produto passa a existir como telemedicina.

1. **Autenticar o WebSocket** (B7). Token na query string ou header; derivar
   `papel` do usuário autenticado; validar que ele pertence à teleconsulta;
   nunca auto-criar sala a partir de string arbitrária.
2. **Corrigir o roteamento do signaling** (B8): `offer`/`answer`/`ice_candidate`
   roteados por peer, não em broadcast. Publicar `peer-joined`/`peer-left`.
   Usar `MensagemSDPSignal` (hoje código morto).
3. **Implementar o cliente WebRTC real** (B1) reaproveitando
   `webrtc_manager.js`. Tanto na página do paciente quanto no cockpit:
   `RTCPeerConnection`, `addTrack`, `ontrack` → elemento de vídeo remoto,
   troca de SDP e ICE pelo WebSocket.
4. **Resolver o estado compartilhado** (A7): Redis pub/sub para as salas, ou
   documentar e forçar single-worker com persistência de sessão. Sem isso a
   teleconsulta quebra em produção com mais de um worker.
5. **Heartbeat e reconexão**: ping/pong no servidor, timeout de conexão zumbi,
   `peer-left` quando alguém cai, backoff de reconexão no cliente.
6. **Tratar queda e encerramento**: o médico precisa saber que o paciente caiu.

**Critério de saída:** dois navegadores reais (médico e paciente) estabelecem
vídeo e áudio bidirecional através do backend; queda de um lado é sinalizada
ao outro; teste automatizado abre WebSocket e troca SDP.

---

### ETAPA 3 — Conformidade CFM 2.314/2022 e LGPD (1–2 semanas)

Só faz sentido depois que existe teleconsulta para registrar.

1. **Persistir o TCLE** (A1): tabela `consentimentos_tcle` com FK para
   teleconsulta, `cidadao_id`, texto integral, hash, método de aceite,
   timestamp e IP **capturado de `Request.client.host`**, não do body (A2).
2. **Bloquear o início da chamada sem TCLE válido** — `/iniciar-chamada`
   deve retornar 409/403 se não houver consentimento registrado.
3. **Registrar o acesso ao prontuário na trilha de auditoria.** Hoje só há
   eventos de login; a LGPD Art. 11 exige demonstrar controle de acesso.
4. **Isolamento entre clínicas** — filtrar toda query por `clinica_id` do token.
   É o P0.1 já registrado no `ROADMAP_V1.md`.
5. **RBAC de verdade** — `PapelUsuarioEnum` vai para o token mas nenhum
   endpoint lê o papel de volta. Médico, recepção e gestor veem a mesma coisa.
6. **Ciclo de vida do dado** — retenção (20 anos, Lei 13.787/2018), backup
   testado, criptografia em repouso, resposta a incidente (Art. 48).

**Critério de saída:** é possível provar, consultando o banco, que um paciente
consentiu, quando, de qual IP, e quem acessou o quê.

---

### ETAPA 4 — Faturamento e documentos corretos (2 semanas)

1. **Unificar o TISS** em uma única implementação (A9). Hoje há duas
   divergentes e ambas geram XML inválido contra o XSD ANS 4.01.00.
2. **Corrigir o XML**: `versaoPadrao` (não `<ans:padrao>`), hash SHA-256 real
   do lote (não `"SIMULATED_TISS_HASH"`), epílogo correto.
3. **Validar contra o XSD no CI** — baixar o XSD oficial e falhar o build se
   o XML não validar.
4. **DMED no leiaute posicional** da IN RFB 1.987/2020 (hoje usa pipes, que
   não é o formato).
5. **Remover os defaults fictícios** de `tiss.py:100` e `dmed.py:63`.
6. **Decidir o destino do ICP-Brasil**: implementar a integração real com o
   VIDAAS ou remover toda menção do produto e rotular o QR Code como hash de
   integridade interno.

**Critério de saída:** um lote TISS real valida contra o XSD oficial; o DMED
abre no validador da Receita; nenhuma alegação de assinatura sem lastro.

---

### ETAPA 5 — Produto e operação (contínuo)

1. **Gravação de teleconsulta** com consentimento explícito, armazenamento
   seguro e política de retenção (hoje `player_gravacao.js` não grava).
2. **Expiração de link do paciente** — token assinado com TTL, não
   `?sala=<codigo>` permanente.
3. **Acessibilidade do Cockpit** — `index.html` não tem `role`, `aria-*` nem
   `tabindex`; 10 modais sem `role="dialog"` nem foco preso. Impeditivo em
   compras públicas.
4. **Ligar ou remover o código morto** — 11 dos 12 módulos JS não são
   carregados por nenhuma página.
5. **Docker corrigido** — a imagem não copia `alembic/`, então não roda migrações.
6. **Lockfile de dependências** e `ruff`/`mypy` no CI.

---

## 6. Resumo executivo das etapas

| Etapa | Foco | Duração | Entrega |
|---|---|---|---|
| **0** | Honestidade | 2–3 dias | Nada é apresentado como real sem ser |
| **1** | Fluxo presencial | 1–2 semanas | Agenda em banco; SOAP gravado; check-in; receita persistida |
| **2** | Teleconsulta real | 2–3 semanas | Vídeo bidirecional funcionando |
| **3** | Conformidade | 1–2 semanas | TCLE persistido; auditoria; isolamento; RBAC |
| **4** | Faturamento | 2 semanas | TISS válido; DMED correto |
| **5** | Produto/operação | contínuo | Gravação; acessibilidade; limpeza |

**Caminho crítico:** Etapa 1 → Etapa 2. Sem agenda em banco não há como ligar
agendamento a prontuário; sem isso a teleconsulta não tem onde registrar nada.

**Recomendação de sequência:** não comece pela teleconsulta. A tentação é
atacar o vídeo primeiro, porque é o que está mais visivelmente ausente — mas
a teleconsulta é o fluxo presencial mais um canal de vídeo. Construir o vídeo
sobre uma agenda em memória produziria uma demo mais bonita e um produto ainda
quebrado.

---

## 7. Observação sobre a documentação

Os documentos em `docs/` descrevem um produto que não existe. Exemplos:

- `MANUAL_FLUXO_OPERACIONAL_MEDIA.md:124` — *"A chamada de vídeo WebRTC roda
  lado a lado com o prontuário em grade Picture-in-Picture"*. Não há chamada.
- `MANUAL_FLUXO_OPERACIONAL_MEDIA.md:105` — *"O paciente recebe um link direto
  no qual visualiza o TCLE e confirma sua ciência"*. Confirma, mas nada é gravado.
- `STATUS_ATUAL_E_RECURSOS_IMPLEMENTADOS.md:26` — *"WebRTC HD ponto a ponto e
  assinatura digital em nuvem com validade jurídica nacional"*.
- `docs/ESTADO_ATUAL.md` já recebeu aviso de documento histórico.

Recomendação: mover os documentos de intenção para `docs/planejado/` e manter
em `docs/` apenas o que descreve o sistema atual. Documentação que descreve um
produto inexistente é pior do que documentação ausente — ela cria confiança
injustificada, e foi o que permitiu que 1.617 commits acumulassem uma demo de
telemedicina sem que ninguém notasse que o vídeo nunca conectou.
