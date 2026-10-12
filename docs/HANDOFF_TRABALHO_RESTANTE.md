# Handoff — Trabalho Restante no Projeto MedIA

**Documento para execução por outro LLM.**
**Base:** commit `08d130a` · 517 testes passando · 31 tabelas · Python 3.12+/FastAPI

---

## 0. Como usar este documento

Este é um documento de **execução**, não de leitura. Ele assume que você vai
mexer no código. Antes de começar:

1. **Leia a seção 1 inteira.** Ela explica o estado real do sistema e as duas
   armadilhas que já custaram tempo neste projeto.
2. **Escolha uma tarefa** da seção 4. Cada uma é autocontida, com arquivos,
   contrato e critério de aceite.
3. **Rode `pytest -q` da raiz antes e depois.** A suíte leva ~12s. Se ela estava
   verde e você quebrou algo, o problema é seu, não do teste.
4. **Não confie em `docs/` para descrever o sistema.** Vários documentos ali
   descrevem um produto que não existe. A seção 3 diz quais.

### Estado verificado

```bash
git log --oneline -1     # 08d130a
pytest -q                # 517 passed
```

---

## 1. Contexto que você precisa ter

### 1.1 O que este sistema é

PEP/telemedicina para atenção primária brasileira: prontuário SOAP, agenda,
fila de acolhimento, teleconsulta, prescrição digital, faturamento TISS/DMED.
Código e terminologias em português (CIAP-2, CID-10, CID-11, CNES, CNS).

### 1.2 O problema estrutural (leia isto)

O sistema tem **duas pilhas paralelas**:

| | Pilha A — REAL (banco) | Pilha B — DEMONSTRAÇÃO (memória) |
|---|---|---|
| Agenda | `agendamentos` ✅ *(novo)* | — |
| Fila | `fila_acolhimento` ✅ | — |
| Atendimento SOAP | `atendimentos_soap` ✅ | `_jornadas` |
| Prescrição | `receitas` (via farmácia) | `_REPOSITORIO_DOCUMENTOS_CFM` |
| Teleconsulta | `teleconsultas` (só status) | `hub._salas` |
| TCLE | **não existe tabela** | objeto descartado |

**Regra de ouro:** se você for implementar algo, implemente na **pilha A**.
Se encontrar um dicionário de módulo guardando dado clínico, isso é dívida —
não replique o padrão.

A pilha B não é lixo: `fluxo_atendimento_service.py` tem máquina de estados
útil. Mas ela **não persiste** e não deve ser a fonte de verdade.

### 1.3 Três armadilhas que já custaram tempo

**Armadilha 1 — Testes que consagram bugs.**
Existem testes que afirmam o comportamento defeituoso. Dois exemplos reais que
já corrigi: `assert response.status_code == 500` para um item de prescrição
inválido, e um teste que fixava FIFO puro como "contrato atual" da fila,
quando o correto é priorizar por risco.

*Se um teste falhar quando você corrige um bug, leia o teste antes de assumir
que você errou.* Ele pode estar descrevendo o defeito como se fosse contrato.

**Armadilha 2 — Limpar estado global em teste.**
A suíte compartilha **um único banco SQLite em memória** entre todos os
arquivos. Um teste que faz `db.query(Modelo).delete()` derruba outros testes
que contam registros. Use dados próprios (um cidadão exclusivo, um CNS único)
em vez de apagar tabelas. Eu errei assim e quebrei `test_prontuario.py`.

**Armadilha 3 — Documentação que descreve produto inexistente.**
`docs/MANUAL_FLUXO_OPERACIONAL_MEDIA.md:124` afirma que "a chamada de vídeo
WebRTC roda lado a lado com o prontuário". **Não há chamada de vídeo.** Isso
permitiu que 1.617 commits acumulassem uma demo de telemedicina sem que
ninguém notasse que o vídeo nunca conectou.

### 1.4 Convenções do projeto

- **Idioma:** código, comentários e mensagens de erro em português.
- **Comentários explicam o *porquê*, não o *quê*.** Vários comentários no
  repositório registram o defeito que a linha corrige. Mantenha esse padrão.
- **Falhar alto:** validação devolve 422, nunca 500. Ausência de dado é
  declarada, nunca preenchida com valor fictício.
- **Nunca invente dado clínico.** Se falta um campo, mostre "não informado".

---

## 2. Estado atual por etapa

| Etapa | Status | O que foi feito |
|---|---|---|
| **0** Honestidade | ✅ Concluída | Simulação de vídeo removida; CRM hardcoded removido; 500→422; dados fictícios rotulados |
| **1** Fluxo presencial | 🟡 5 de 7 | Agenda em banco, check-in, SOAP gravado, teste de fluxo completo |
| **2** Teleconsulta real | ⬜ Não iniciada | — |
| **3** Conformidade CFM/LGPD | ⬜ Não iniciada | — |
| **4** Faturamento | ⬜ Não iniciada | — |
| **5** Produto/operação | ⬜ Não iniciada | — |

Detalhamento do que foi feito está em `docs/REVISAO_E_PLANO_DE_EVOLUCAO.md`
(diagnóstico) e nos commits `e3d6fa7` (etapa 0) e `08d130a` (etapa 1).

---

## 3. Documentos em que confiar (e nos que não)

**Confie:**

- `docs/REVISAO_E_PLANO_DE_EVOLUCAO.md` — diagnóstico com evidência, linha a linha
- `docs/ROADMAP_V1.md` — bloqueios por severidade
- `README.md` — descreve o que o código faz
- Este documento

**Não confie (descrevem produto inexistente):**

- `docs/MANUAL_FLUXO_OPERACIONAL_MEDIA.md`
- `docs/STATUS_ATUAL_E_RECURSOS_IMPLEMENTADOS.md`
- `docs/DIRETRIZES_CLINICAS_OFICIAL.md`
- `docs/ESTADO_ATUAL.md` — já tem aviso no topo
- `CHANGELOG.md` — 570 KB de saída automática, com números de versão e de testes
  que nunca corresponderam à realidade

---

## 4. Tarefas

Ordenadas por dependência. **A ordem importa:** T1 e T2 fecham a Etapa 1 e são
pequenas; T3 é a maior e depende do padrão de persistência que T2 estabelece.

---

### T1 — Aba de Acolhimento no Cockpit

**Etapa:** 1 · **Tamanho:** pequeno · **Depende de:** nada

#### Problema

O backend tem fila e check-in funcionando, mas **não há como a recepção usá-los
pela tela**. `js/fila_espera.js` (203 linhas, bem escrito) existe e nunca é
carregado por nenhuma página. O Cockpit tem 8 abas e nenhuma de acolhimento.

#### O que fazer

1. **Adicionar a aba.** Em `backend/app/static/index.html`:

   - **Botão de menu.** Copie o de pacientes (`btn-menu-pacientes`, **linha 275**)
     e crie `btn-menu-acolhimento`:
     ```html
     <button onclick="trocarAba('acolhimento')" id="btn-menu-acolhimento"
             class="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-all">
       <i class="fa-solid fa-triage w-4 text-center text-slate-300"></i>
       <span>Acolhimento</span>
     </button>
     ```

   - **Seção da aba.** Copie a estrutura de `aba-pacientes` (**linha 821**,
     `<section id="aba-pacientes" class="space-y-6 hidden">`) e crie
     `id="aba-acolhimento"`. Ela precisa conter os **4 elementos** que
     `fila_espera.js:88-91` procura — nenhum existe hoje:

     | ID exigido | Uso |
     |---|---|
     | `fila-espera-lista` | container da lista de pacientes |
     | `fila-espera-contador` | número de pessoas aguardando |
     | `fila-espera-chamada` | paciente chamado no momento |
     | `fila-espera-atualizacao` | timestamp da última atualização |

2. **Registrar a aba em `app.js`**, na função `trocarAba`:
   - Inclua `"acolhimento"` no array `abas` (hoje:
     `["agenda","telemedicina","prontuario","pacientes","convenios","farmacia","analytics","honorarios"]`).
   - Adicione `if (aba === "acolhimento") carregarAcolhimento();` junto dos
     outros `if (aba === ...)` no fim da função.

3. **Instanciar o painel.** `fila_espera.js` é um **ES Module**
   (`export class FilaEsperaPainel`), e `app.js` é script clássico. Duas opções:
   - **Recomendada:** adicione `<script type="module">` no `index.html` que
     importa o módulo e instancia o painel, expondo o objeto em `window` para o
     `app.js` chamar.
   - Alternativa: converta `app.js` para module. **Não faça isso** — `app.js`
     tem 2000+ linhas e usa funções globais chamadas por `onclick` no HTML.

4. **Conectar o check-in.** A aba precisa de um botão "Fazer check-in" que
   chame `POST /api/v1/agenda/{codigo}/checkin`. O contrato:

   ```
   POST /api/v1/agenda/{codigo_ou_id}/checkin?classificacao_risco=AMARELO
   → 201 {"agendamento_id":1,"fila_id":1,"cidadao_id":2,
          "status_agendamento":"SALA_DE_ESPERA","mensagem":"..."}
   → 409 se o agendamento estiver cancelado
   → 422 se a classificação de risco for inválida
   ```

   É idempotente: repetir devolve a mesma `fila_id`.

#### Critério de aceite

- A aba aparece no menu e abre.
- A lista mostra os pacientes com `status=AGUARDANDO_ATENDIMENTO`, ordenados
  por **risco** (VERMELHO → AMARELO → VERDE → AZUL) e, dentro do mesmo risco,
  por chegada. Isso já funciona no backend (`api/v1/fila.py`, usa uma
  expressão `case`).
- O botão de check-in coloca o paciente na fila e a lista atualiza.
- `pytest -q backend/tests/test_contrato_frontend.py` continua passando. Esse
  teste varre **todo** HTML/JS sob `static/` (usa `rglob`, então pega o
  subdiretório `js/`), remove comentários e confere cada URL `/api/v1/...`
  contra a tabela de rotas real do OpenAPI. Se você inventar um endpoint, ele
  falha — o que é o comportamento desejado.

#### Armadilha

O `fila_espera.js` faz `fetch(this.#opcoes.urlApi)` direto, **sem o header de
autorização**. Se `ENVIRONMENT` for `staging`/`production`, a rota exige Bearer
e vai dar 401. Veja como `app.js` resolve isso: há um interceptor global de
`fetch` instalado no topo do arquivo (`instalarInterceptorDeToken`) que injeta
o header em chamadas `/api/`. Confirme que o módulo se beneficia dele — se for
carregado como module separado, o interceptor global **já está ativo** (ele
substitui `window.fetch`), então deve funcionar.

---

### T2 — Persistir as receitas e atestados

**Etapa:** 1 · **Tamanho:** médio · **Depende de:** nada

#### Problema

`services/prescricao_digital_cfm.py:67` guarda os documentos emitidos em um
dicionário de módulo:

```python
_REPOSITORIO_DOCUMENTOS_CFM: Dict[str, Dict] = {}
```

**Consequência grave:** ao reiniciar o servidor, **a farmácia que escanear o QR
Code recebe 404**. Uma receita com validade legal "desaparece". A linha 130 e a
187 gravam, e as linhas 207/215 leem para a validação pública.

Além disso, o documento não se vincula ao atendimento nem ao cidadão — o
request não aceita `atendimento_id`.

#### O que fazer

1. **Criar o modelo** `backend/app/models/documento_cfm.py`:

   ```python
   class DocumentoCFM(Base):
       __tablename__ = "documentos_cfm"

       id = Column(Integer, primary_key=True, index=True)
       codigo_validacao = Column(String(30), unique=True, nullable=False, index=True)
       tipo = Column(String(20), nullable=False)          # RECEITA | ATESTADO
       status = Column(String(20), nullable=False)         # VALIDA | ...
       hash_integridade_sha256 = Column(String(64), nullable=False)

       # Vínculos — é o que faltava
       atendimento_id = Column(Integer, ForeignKey("atendimentos_soap.id"), nullable=True, index=True)
       cidadao_id = Column(Integer, ForeignKey("cidadaos.id"), nullable=True, index=True)

       # Identificação do profissional (ver T5 — hoje não há coluna de CRM)
       medico_nome = Column(String(200), nullable=False)
       medico_crm = Column(String(20), nullable=False)
       medico_uf = Column(String(2), nullable=False)
       medico_rqe = Column(String(20), nullable=True)

       paciente_nome = Column(String(200), nullable=False)
       paciente_cpf = Column(String(11), nullable=False, index=True)

       conteudo = Column(JSON, nullable=False)   # itens, instruções, texto
       data_emissao = Column(DateTime, nullable=False)
       created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
   ```

   Registre em `backend/app/models/__init__.py`.

2. **Gerar a migração.** Receita que funciona:

   ```bash
   # A partir da RAIZ do repositório. O banco precisa estar em head antes.
   DATABASE_URL="sqlite:///./gen.db" python -m alembic -c alembic.ini upgrade head
   DATABASE_URL="sqlite:///./gen.db" python -m alembic -c alembic.ini revision \
       --autogenerate -m "add_documentos_cfm"
   ```

   **Cuidado:** se você autogerar contra um banco vazio, a migração vai recriar
   as 31 tabelas. Sempre aplique `upgrade head` primeiro. Confira o arquivo
   gerado — ele deve conter **apenas** `documentos_cfm`. Depois apague `gen.db`.

3. **Trocar o repositório por persistência.** Em
   `services/prescricao_digital_cfm.py`, `MotorPrescricaoCFM` é uma classe com
   métodos `@classmethod` que **não recebem `Session`**. São quatro métodos a
   alterar:

   | Método | Linha | Chamadores |
   |---|---|---|
   | `emitir_prescricao` | 74 | `api/v1/prescricao_cfm.py:78` |
   | `emitir_atestado` | 148 | `api/v1/prescricao_cfm.py:110` |
   | `validar_documento_publico` | 205 | `prescricao_cfm.py:181` |
   | `obter_documento` | 213 | `prescricao_cfm.py:137,159,190` |

   **Armadilha — 10 chamadas diretas em testes.** Dois arquivos chamam o motor
   sem passar por HTTP e vão quebrar quando a assinatura mudar:

   - `backend/tests/test_prescricao_digital_cfm.py` — linhas 2, 6, 32, 40, 52, 59
   - `backend/tests/test_flujo_consulta_receita_digital.py` — linhas 12, 26, 280, 297

   Esses testes precisarão de uma sessão de banco. Opções: injetar a sessão via
   fixture do `conftest.py` (que já expõe `db_session`) ou criar uma dependência
   opcional. **Não** deixe o motor com fallback silencioso para o dicionário em
   memória — isso manteria o bug vivo em produção.

   No endpoint, basta adicionar `db: Session = Depends(get_db)` — ele já recebe
   `Request`.

4. **Vincular ao atendimento.** Adicione `atendimento_id` e `cidadao_id` como
   campos **opcionais** em `EmitirPrescricaoRequest` e `EmitirAtestadoRequest`.
   Quando vierem, grave o vínculo. O Cockpit já tem `consultaAtiva` em memória
   com esses dados — passe-os.

#### Critério de aceite

- Emitir receita, **reiniciar o servidor**, e o QR Code continua validando.
- Teste novo: `test_receita_sobrevive_ao_reinicio` — emite, expira a sessão
  (`db.expire_all()`), consulta a validação pública e confirma 200.
- `GET /api/v1/prescricao/validar-html/{codigo}` funciona após reinício.
- Documento emitido durante um atendimento fica com `atendimento_id` preenchido.

---

### T3 — Teleconsulta real (vídeo bidirecional)

**Etapa:** 2 · **Tamanho:** grande · **Depende de:** T2 (padrão de persistência)

#### Problema

**Não existe teleconsulta por vídeo.** Duas provas:

`static/telemedicina_paciente.html:115-126` — o cliente do paciente faz
`getUserMedia`, joga no próprio vídeo e termina. **Nunca constrói
`RTCPeerConnection`, nunca abre WebSocket.** O `<video id="video-medico">`
(linha 69) fica permanentemente preto.

E o lado do médico também não conecta: a função que "recebia" o paciente
(`simularEntradaPaciente`) foi **removida** na Etapa 0 — ela injetava a webcam
do próprio médico no vídeo remoto. Hoje a sala mostra um aviso honesto de que a
transmissão não existe.

#### O que já existe e deve ser reaproveitado

**`static/js/webrtc_manager.js` está correto e completo.** É a base que falta.
Ele implementa:

```js
export class WebRTCManager extends EventTarget {
  async iniciarCaptura(constraintsOverride)   // getUserMedia
  async criarPeerConnection()                 // com STUN/TURN, ontrack, onicecandidate
  async criarOferta()                         // createOffer
  async criarResposta(offerSdp)               // setRemoteDescription + createAnswer
  async definirDescricaoLocal(desc)
  async definirDescricaoRemota(desc)
  async adicionarCandidatoRemota(candidate)
  async trocarTrack(kind, deviceId)           // replaceTrack, sem renegociar
  alternarMuteAudio/Video, isAudioMuted/VideoMuted
  async listarDispositivos()
}
```

Ele emite eventos `icecandidate`, `track` e `connectionstatechange`. STUN padrão
é `stun:stun.l.google.com:19302`; TURN é `null` por padrão.

**Ninguém importa este módulo.** Foi escrito e nunca integrado.

**O hub de signaling existe:** `api/v1/telemedicina_ws.py`, endpoint
`/ws/telemedicina/sala/{codigo_sala}`. Mas tem defeitos (abaixo).

#### Defeitos a corrigir no backend

Arquivo `backend/app/api/v1/telemedicina_ws.py`:

1. **Sem autenticação** (linha 204): `papel: str = "medico"` é o **valor padrão
   da query string**. Basta conectar em qualquer sala sem parâmetro para entrar
   como médico. Não há token, não há verificação de posse da sala.
   Dependências de router **não se aplicam a rotas WebSocket** — a checagem
   precisa ser feita dentro do handler.

2. **Sala arbitrária é auto-criada** (linhas 214-215):
   `if codigo_sala not in hub._salas: hub.criar_sala(codigo_sala)` — qualquer
   string vira sala. Precisa validar contra `salas_virtuais` no banco.

3. **Roteamento quebrado** (linhas 115-120 e 250-256): `_papeis_alvo()` só
   mapeia `estado_medico`/`estado_paciente`. Para `offer`, `answer` e
   `ice_candidate` retorna `None`, o que faz **broadcast para todos, inclusive
   o remetente**. O signaling não funciona.

4. **`join_sala` não notifica ninguém** (linhas 237-249): faz `continue` sem
   publicar. Os peers nunca descobrem que o outro entrou. Falta um evento
   `peer-joined` / `peer-left`.

5. **`MensagemSDPSignal`** (linhas 78-83) é código morto — define
   `sala_codigo`, `paciente_id`, `prestador_id`, mas `EnvelopeEntrada` só tem
   `tipo` e `payload`. Use essa classe para o roteamento.

6. **Sem heartbeat** — conexões zumbis só morrem no TCP keepalive.

7. **Queda não é sinalizada** — o `finally` (linhas 264-266) remove a fila e não
   avisa o outro participante.

8. **Estado em memória** (`self._salas`, linha 125): reiniciar o servidor mata
   a teleconsulta; com 2+ workers do uvicorn, médico e paciente ficam em
   universos separados. Precisa de Redis pub/sub, ou documentar e forçar
   single-worker.

#### O que implementar

1. **Autenticar o WebSocket.** Token via query string (`?token=...`) ou
   primeiro frame. Derive o papel do usuário autenticado; valide que ele tem
   vínculo com a teleconsulta daquela sala.
2. **Corrigir o roteamento.** `offer`/`answer`/`ice_candidate` vão para o peer,
   não em broadcast. Publique `peer-joined` quando alguém entra e `peer-left`
   quando sai.
3. **Implementar os dois clientes WebRTC:**
   - `static/telemedicina_paciente.html` — importar `webrtc_manager.js`, criar
     PeerConnection, `ontrack` → `#video-medico`, trocar SDP/ICE pelo WS.
   - Cockpit (`app.js` + `index.html`) — o mesmo do lado do médico, com
     `#medico-video-remoto` recebendo o track remoto.
4. **Heartbeat** (ping/pong) e reconexão com backoff.
5. **Resolver o estado compartilhado** — Redis, ou single-worker documentado.

#### Contrato de mensagens (sugestão)

```json
// Cliente → servidor
{"tipo":"join_sala","payload":{}}
{"tipo":"offer","payload":{"sdp":"...","para":"paciente"}}
{"tipo":"answer","payload":{"sdp":"...","para":"medico"}}
{"tipo":"ice_candidate","payload":{"candidate":{...},"para":"paciente"}}

// Servidor → cliente
{"tipo":"ok","de_papel":"medico","payload":{"evento":"sala_ingressada",...}}
{"tipo":"peer-joined","de_papel":"sistema","payload":{"papel":"paciente"}}
{"tipo":"offer","de_papel":"paciente","payload":{"sdp":"..."}}
```

#### Critério de aceite

- **Dois navegadores reais** (médico e paciente) estabelecem vídeo e áudio
  bidirecional através do backend.
- Queda de um lado é sinalizada ao outro (`peer-left`).
- Um cliente anônimo **não consegue** entrar na sala.
- Teste automatizado que abre o WebSocket (`TestClient.websocket_connect`),
  envia `offer` e verifica que o outro participante recebe. Hoje **nenhum teste
  da suíte abre um WebSocket**.

#### Armadilha

`test_telemedicina_ws.py:184` tem `assert entregues >= 0` — tautologia, passa
sempre. E `test_telemedicina_lifecycle.py` testa tabelas próprias
(`telemedicina_rooms`, `consultas`) que **não existem no produto**. Não use
esses arquivos como referência de comportamento.

---

### T4 — Conformidade CFM 2.314/2022 e LGPD

**Etapa:** 3 · **Tamanho:** grande · **Depende de:** T3

Só faz sentido depois que existe teleconsulta para registrar.

#### T4.1 — Persistir o TCLE (Art. 4º)

**O consentimento não é gravado em lugar nenhum.** Verificado:

- `services/cfm_telemedicina.py:102-125` — `registrar_aceite_tcle()` monta um
  `dataclass` e retorna. Não há `db.add`, não há `commit`. O arquivo **não
  importa Session nem referencia banco**.
- `api/v1/telemedicina.py:163-183` — o endpoint não recebe `Depends(get_db)`,
  então é fisicamente incapaz de gravar.
- O schema não tem tabela de consentimento (confirmado em
  `Base.metadata.tables`).

**Fazer:**

1. Modelo `ConsentimentoTCLE` com: `teleconsulta_id`, `cidadao_id`, texto
   integral, `hash_tcle`, método de aceite, `data_hora_aceite`, `ip_origem`,
   `user_agent`, versão do termo.
2. Migração Alembic (mesmo cuidado da T2).
3. `POST /telemedicina/tcle/registrar` passa a persistir.
4. **IP deve vir de `Request.client.host`, não do body.** Hoje
   `TCLERegistrarRequest.ip_origem` (linha 48) tem default `"127.0.0.1"` e é
   escolhido livremente pelo requerente — falsificável.
5. **`POST /telemedicina/iniciar-chamada` deve exigir TCLE válido** e devolver
   409/403 se não houver. Hoje a chamada inicia sem consentimento algum.

**Aceite:** é possível provar, consultando o banco, que um paciente consentiu,
quando, de qual IP e com qual versão do termo.

#### T4.2 — Auditoria de acesso a PHI

`AuditService.registrar_evento` é chamado em **4 lugares, todos de login**
(`auth.py`). Não há registro de abertura de prontuário, emissão de prescrição
ou exportação TISS — justamente o que a LGPD Art. 11 exige para demonstrar
controle de acesso.

Além disso, o digest SHA-256 **não cobre** `detalhes_json`, `ip_address` e
`user_agent` (`audit_service.py:23-27`), então adulterar o conteúdo clínico de
um evento não quebra a corrente. E a leitura do topo da corrente não usa
`FOR UPDATE` (`:46-47`), o que **bifurca a cadeia** sob concorrência.

**Fazer:** auditar todo caminho que toca PHI; incluir o payload completo no
digest; serializar a escrita da corrente (`pg_advisory_xact_lock` ou tabela de
contador com `FOR UPDATE`).

#### T4.3 — Isolamento entre clínicas (P0.1 do ROADMAP)

**A autenticação é exigida, mas nenhuma query filtra por `clinica_id`.** Um
médico autenticado da Clínica A que conheça o CNS de um paciente da Clínica B
recebe o prontuário. O isolamento é apenas lógico e depende de cada consulta SQL
lembrar do filtro.

**Fazer:** extrair uma dependência de tenant e aplicá-la em todos os
repositórios. Considerar RLS no PostgreSQL como defesa em profundidade.

#### T4.4 — RBAC

`PapelUsuarioEnum` vai para o token mas **nenhum endpoint lê o papel de volta**.
Médico, recepção e gestor veem a mesma coisa. Criar `require_role(...)` por
perfil e aplicar nas rotas sensíveis.

#### T4.5 — Ciclo de vida do dado

Ausentes: retenção (CFM 2.314 Art. 8º / Lei 13.787/2018 — 20 anos),
anonimização, backup/restauração testado, criptografia em repouso, resposta a
incidente (LGPD Art. 48) e atendimento ao titular (Art. 18). CPF e CNS trafegam
e são armazenados em claro.

---

### T5 — Identificação do profissional (CRM)

**Etapa:** 3 · **Tamanho:** pequeno · **Depende de:** nada

#### Problema

**A tabela `profissionais` não tem coluna de CRM nem de UF.** Verificado em
`backend/app/models/profissional.py` — só tem `cns`, `cpf`, `nome`, `cbo`,
`cbo_descricao`.

O Art. 5º da CFM 2.314/2022 exige identificação do médico com CRM. O sistema
não tem onde guardar isso.

**Bug relacionado, já corrigido parcialmente:** `auth_service.py` preenchia o
campo `crm` do vínculo com `prof.cbo` — o **Código Brasileiro de Ocupações**,
que identifica a ocupação (ex.: "225142") e não o registro profissional. O
front-end exibia esse código como se fosse CRM. Na Etapa 0 troquei por `None`
e a interface passou a dizer "não informado".

#### O que fazer

1. Adicionar `crm` e `uf_crm` (e opcionalmente `rqe`) ao modelo `Profissional`.
2. Migração Alembic.
3. `auth_service.py` volta a preencher `crm=prof.crm` e `uf_crm=prof.uf_crm`.
4. Atualizar `VinculoClinicaOut` (`schemas/auth.py`) para expor `uf_crm` e `rqe`.
5. Seed (`seeds/seed_multiclinica_auth.py`) com CRM dos profissionais de
   demonstração.
6. O front-end já lê `vinculo.crm` e `vinculo.rqe` — passa a funcionar sozinho.

**Aceite:** emitir receita com o usuário logado e conferir que o CRM no PDF é o
do profissional autenticado.

---

### T6 — Faturamento TISS e DMED corretos

**Etapa:** 4 · **Tamanho:** médio-grande · **Depende de:** nada

#### T6.1 — O XML TISS é inválido

- `services/tiss_generator.py:168` — o hash do epílogo é a **string literal**
  `"SIMULATED_TISS_HASH"`. Não é hash.
- `api/v1/tiss.py:169` — `f"TISS-HASH-LOTE-{numero_lote}"`. Idem.
- Usa elemento inexistente `<ans:padrao>` em vez de `versaoPadrao`.
- **Duas implementações divergentes** do mesmo XML: `tiss_generator.py:100-178`
  e `:208-276`, que nomeiam elementos de forma diferente (`cpf` vs
  `cpfBeneficiario`; `conselhoProfissional` como texto `"06"` vs elemento com
  `codigoConselho`).

**Fazer:** uma única implementação; `versaoPadrao` correto; hash SHA-256 real do
lote; validar contra o XSD oficial da ANS **no CI**.

**Nota importante:** o único caminho TISS que **persiste** é
`POST /convenios/guias/consulta` (`repositories/convenios_repo.py:113-145`), que
grava `GuiaTISS.xml_tiss` + `LancamentoFinanceiro`. Os endpoints `/tiss/*`
**não persistem nada** — o XML só existe na resposta HTTP. Considere unificar
tudo no caminho que já funciona.

#### T6.2 — DMED no formato errado

`services/dmed_generator.py:53-92` usa pipes (`DMED|...|ROP|...|T9`). O leiaute
da IN RFB 1.987/2020 é **posicional de tamanho fixo**. E
`api/v1/dmed.py:63-94` é hardcoded.

#### T6.3 — Remover defaults fictícios do backend

- `api/v1/tiss.py:100-137` — lote default com "Maria Silva"/"João Santos"
- `api/v1/dmed.py:63-94` — DMED de exemplo
- `api/v1/financeiro_medico.py:42-53` — 5 receitas e 3 despesas hardcoded

---

### T7 — Decisão sobre ICP-Brasil

**Etapa:** 4 · **Tamanho:** depende da decisão

`services/vidaas_signature_service.py:61-112` **não faz nenhuma chamada de
rede** — o arquivo não importa `httpx` nem `requests`. O "carimbo" é um UUID
(`:99`), a URL do validador `https://validador.iti.gov.br/validar` (`:100`)
**não é um endpoint real do ITI**, e `certificado_titular` (`:107`) tem o nome
de uma pessoa real fixo no código.

Emitir uma receita que *parece* assinada no padrão ICP-Brasil sem estar é
exposição regulatória, não bug de documentação.

**Duas opções:**

- **(A) Implementar de verdade** — integração REST com o VIDAAS, com
  credenciais, tratamento de erro e validação de resposta.
- **(B) Remover as alegações** — apagar menções a ICP-Brasil/PAdES do README,
  docs, modelo `ReciboAssinaturaVidaas` e payload do QR Code; rotular como
  "hash de integridade interno, sem valor legal".

**Recomendação: (B) agora, (A) depois.** O QR Code atual já entrega verificação
de integridade real (SHA-256 do documento). Chamar isso de assinatura
ICP-Brasil é o problema, não o hash.

---

### T8 — Operação e produto

**Etapa:** 5 · Vários itens independentes

- **Gravação de teleconsulta.** `js/player_gravacao.js` é um *player*, não um
  gravador — não usa `MediaRecorder`. Não há armazenamento, consentimento
  específico para gravação (Art. 9º) nem política de retenção.
- **Expiração do link do paciente.** `gerar_link_paciente`
  (`cfm_telemedicina.py:140-173`) chama o link de "efêmero" no docstring, mas
  ele é `?sala=<codigo>` puro — permanente, sem token nem TTL.
  `SalaVirtual.data_expiracao` existe (`models/telemedicina.py:34`) e **nunca é
  populado**; não há job de expurgo.
- **Acessibilidade do Cockpit.** `index.html` não tem um único `role`, `aria-*`
  ou `tabindex`. 10 modais sem `role="dialog"`, sem foco preso e sem `Escape`.
  Impeditivo em compras públicas.
- **Código morto.** 11 dos 12 módulos JS não são carregados por nenhuma página.
  Decidir: ligar ou remover.
- **Docker.** A imagem copia só `backend/app` — sem `alembic/` nem
  `alembic.ini`, **não consegue rodar migrações**. Não há `.dockerignore`.
- **Lockfile.** Os dois `requirements.txt` discordam (raiz com `>=`, backend com
  `==`). Não há lockfile. Adicionar `ruff` e `mypy` ao CI.
- **Tratamento global de exceção.** `main.py` não tem handler; qualquer
  `IntegrityError` vira 500 com traceback. `convenios.py:132-133` expõe a
  mensagem da exceção na resposta HTTP.
- **Service worker mente.** `sw.js:43-52` devolve **HTTP 200** com
  `{"offline": true}` quando a rede cai. Como todo guard é `if (res.ok)`, a
  aplicação exibe "vazio" em vez de "offline". Ele sequer é registrado.
- **Rascunho de anamnese em `localStorage`** (`anamnese_form.html:518`)
  guarda CNS, CPF, alergias e medicamentos sem expiração nem criptografia.
- **`anamnese_form.html` não fecha contrato.** O caminho foi corrigido para
  `POST /api/v1/atendimentos/`, mas o endpoint exige `cidadao_id` e o formulário
  só coleta CNS/CPF. Falta resolver o paciente para a chave primária.
- **WebSocket do Copiloto sem autenticação** (`copiloto.py:263`).

---

## 5. Itens conhecidos que ainda existem

Coisas que **não** estão nas tarefas acima mas você vai encontrar:

| Item | Onde | Observação |
|---|---|---|
| `_jornadas` em memória | `services/fluxo_atendimento_service.py:43` | Guarda SOAP, diagnósticos e prescrições. Duplica `atendimentos_soap`. Decidir: persistir ou remover. |
| `_entradas` em memória | `services/fila_teleatendimento.py:399` | Fila de teleatendimento |
| `agenda_medica` legado | — | O antigo `_AGENDA_MEMORIA` foi removido; se encontrar referência, é código morto |
| `test_telemedicina_lifecycle.py` | `backend/tests/` | Testa tabelas que não existem no produto. Candidato a remoção. |
| `test_webrtc_manager.py` | `backend/tests/` | Testa o **texto-fonte** do JS por regex, não executa nada |
| `test_telemedicina_ws.py:184` | `backend/tests/` | `assert entregues >= 0` é tautologia |
| `INVENTARIO_DO_PROJETO.md` | raiz | Não faz parte do plano; pode ignorar |

---

## 6. Comandos úteis

```bash
# Testes (da RAIZ — o pytest.ini define pythonpath=backend)
pytest -q
pytest -q backend/tests/test_fluxo_presencial_completo.py   # um arquivo
pytest -q -k "checkin"                                       # por nome

# Subir o servidor (migra e semeia sozinho no primeiro boot)
cd backend && uvicorn app.main:app --reload
# → http://localhost:8000/app   Cockpit
# → http://localhost:8000/docs  OpenAPI

# Login de demonstração (só em development)
curl -X POST localhost:8000/api/v1/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"demo_role":"medico_titular"}'

# Migrações (sempre da RAIZ)
python -m alembic -c alembic.ini upgrade head
python -m alembic -c alembic.ini revision --autogenerate -m "descricao"
python -m alembic -c alembic.ini downgrade -1

# Validar sintaxe do JS depois de mexer no front
node --check backend/app/static/app.js
```

### Banco

SQLite em `backend/esus.db` por padrão (ancorado, não relativo ao CWD). Para
zerar: apague o arquivo e reinicie — migra e semeia de novo.

### Ambientes

`ENVIRONMENT` aceita `development` (padrão), `test`, `staging`, `production`.

- `development`/`test`: sem autenticação obrigatória, login demo ativo
- `staging`/`production`: **exige** `JWT_SECRET_KEY`, recusa subir com flags de
  demonstração ligadas, autenticação obrigatória em todas as rotas clínicas

A validação está em `Settings.validar_ambiente()` (`core/config.py`).

---

## 7. Como eu verificaria cada entrega

Padrão que usei e recomendo manter:

1. **Escreva o teste que falha primeiro.** Se ele passa antes da correção, ou o
   bug não é o que você pensa, ou o teste não testa o que você pensa.
2. **Rode a suíte inteira**, não só o arquivo novo. A suíte é rápida e o banco é
   compartilhado — interferência entre testes é real.
3. **Verifique end-to-end com servidor de verdade.** Vários bugs deste projeto
   só apareceram com o servidor rodando (o `UnicodeEncodeError` que matava o
   boot no Windows, por exemplo). `TestClient` não pega tudo.
4. **Verifique o estado final no banco**, não só o código HTTP da resposta.
5. **Se um teste antigo falhar, leia-o antes de mudá-lo.** Pode ser um teste que
   consagra o bug que você acabou de corrigir.

---

## 8. Se você só puder fazer uma coisa

Faça a **T3 (teleconsulta real)**.

É a ausência mais grave: o produto se chama telemedicina e não faz vídeo. O
`webrtc_manager.js` já está pronto e correto — falta integrá-lo e consertar o
roteamento do WebSocket.

Mas **não comece por ela** se for mexer em persistência antes: a T2 estabelece o
padrão de migração e de injeção de `Session` que a T3 e a T4 vão reusar.

---

## 9. Nota final

Este projeto tem trabalho de qualidade real: prontuário SOAP funcional,
faturamento por convênio que persiste, terminologias brasileiras, trilha de
auditoria encadeada, autenticação sólida, 517 testes. O problema nunca foi
capacidade técnica — foi **acumular interface antes de fechar o fluxo**.

A tentação, ao pegar este repositório, é construir o vídeo primeiro, porque é o
que está mais visivelmente ausente. Resista. Teleconsulta é o fluxo presencial
mais um canal de vídeo. Construir vídeo sobre um fluxo quebrado produz uma demo
mais bonita e um produto ainda quebrado — foi exatamente o que aconteceu nas
1.617 commits anteriores.
