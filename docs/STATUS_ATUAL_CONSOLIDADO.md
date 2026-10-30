# 📋 Status Atual Consolidado — MedIA Practice SaaS (v1)

> **Documento vivo e autoritário sobre o estado atual do repositório.**
> Branch `main` · T1, P0.1 (RBAC/tenant), P0.2 (auditoria), T2 (receitas persistidas),
> P1 (sessão com refresh rotativo), **T3 (teleconsulta WebRTC real)** e **P0.3
> (retenção/anonimização/backup)** **commitados**.
> Gerado pela sessão de evolução do workspace `App_Media`.

---

## 0. Atualização de 29/10/2026 — Fase 0 da auditoria

> A auditoria completa está em [`AUDITORIA_COMPLETA_2026-10-29.md`](AUDITORIA_COMPLETA_2026-10-29.md).
> Desde o snapshot abaixo, a suíte passou de **621 para 714 testes** e foram
> corrigidos, com teste de regressão:

| Correção | Arquivo principal | Teste |
|---|---|---|
| `POST/GET /sincronizacao/*` respondiam 500 | `app/services/sync_offline.py` | `test_sincronizacao_api.py` (10) |
| WebSocket do copiloto quebrava no handshake e não autenticava | `app/api/v1/copiloto.py`, `router.py` | `test_copiloto_ws.py` (7) |
| Imagem Docker sem `alembic.ini`/`alembic`; compose em modo dev | `Dockerfile`, `docker-compose.yml`, `scripts/docker-entrypoint.sh` | `docker compose config` + simulação de layout |
| Jornada com paciente fictício e id fixo no frontend | `fluxo_atendimento_service.py`, `static/app.js` | `test_fluxo_demo_guard.py` (5) |
| CodeQL com action inexistente | `.github/workflows/codeql.yml` | — |
| Dependências divergentes do ambiente validado | `backend/requirements.txt`, `requirements.txt` | — |
| **Prescrição nunca criava `Receita` → farmácia sempre 404** | `app/services/farmacia_bridge.py`, `prescricao_digital_cfm.py`, `farmacia.py` | `test_prescricao_farmacia_integracao.py` (12) |
| **Livro caixa com lançamentos e demonstrativo fictícios** | `app/models/financeiro.py`, `app/repositories/livro_caixa_repo.py`, `financeiro_medico.py` | `test_livro_caixa_persistido.py` (11) |
| **Jornada do fluxo em memória (sumia no restart) e sem vínculo com o cidadão/agenda** | `app/models/jornada.py`, `fluxo_atendimento_service.py`, `api/v1/fluxo_atendimento.py` | `test_jornada_persistida.py` (7) |
| **CPF/CNS em texto claro no banco (LGPD art. 46)** | `app/core/crypto.py`, 8 arquivos em `models/`, migrações `f1c3a8e57b20` + `b6e8f24a91d7` | `test_cpf_cns_cifrados.py` (14) + `test_copias_cpf_cns_cifradas.py` (15) |
| **Telemedicina não plena em produção: sala da agenda não existia em `salas_virtuais` (WS recusava com auth ligada), TCLE não persistia/não bloqueiava, encerramento não notificava o hub, `teleconsulta_id: 1` fixo no frontend e link do paciente com host/código errados** | `agenda_medica.py`, `telemedicina.py`, `models/telemedicina.py`, migração `c3d9e1f5a7b2`, `fluxo_atendimento_service.py`, `core/config.py`, `static/app.js` | `test_agenda_medica.py` + `test_flujo_consulta_teleconsulta.py` (19) + `test_api_telemedicina.py` + `test_fluxo_atendimento.py` (2) + `test_t3_teleconsulta_frontend.py` (1) |

**P0-4 (parte 2) fechado:** `jornadas_atendimento` guarda estado + `cidadao_id`/
`profissional_id`/`estabelecimento_id`/`agendamento_id`; o serviço hidrata do
banco fora do cache; `paciente_id` não é mais sorteado com `uuid4`; uma consulta
criada na agenda pode ser finalizada pelo fluxo (antes: 404).

**P0-7 (mestre + cópias) fechado:** `cidadaos` e `profissionais` guardam CPF/CNS
com AES-256-GCM e índice cego HMAC; as **cópias** do mesmo documento em 11
tabelas operacionais (20 colunas de texto + `xml_tiss` + CPF/CNS embutidos em
`payload_json`/`dados_json`) também são cifradas pela migração `b6e8f24a91d7`.
A API continua devolvendo texto claro e o `ComparadorProtegido` falha alto se
alguém tentar comparar texto claro com coluna cifrada sem índice cego. A
**produção agora exige `FIELD_ENCRYPTION_KEY`** no compose (guardar a chave
junto com o backup — perdê-la torna os dados ilegíveis).

**TM-1..TM-5 (telemedicina em produção) fechado:** a teleconsulta só funcionava
no ambiente de demonstração. As cinco correções:

1. **TM-1 — sala da agenda persistida.** `POST /agenda/novo` com
   `TELEMEDICINA` cria a `SalaVirtual` real em `salas_virtuais` (status
   AGENDADA) e a `Teleconsulta` vinculada (sala, cidadão, profissional). Antes
   o código da sala só existia no `Agendamento`, o WebSocket recusava a conexão
   dos dois lados com `require_auth` (4404 "Sala não encontrada") e o link do
   paciente apontava para uma sala inexistente. `AgendamentoOut` ganhou
   `teleconsulta_id` (resolvido pela sala).
2. **TM-2 — TCLE persistido e bloqueante.** Novo modelo
   `ConsentimentoTeleconsulta` (`consentimentos_teleconsulta`, migração
   `c3d9e1f5a7b2`, CPF cifrado): grava texto integral + hash SHA-256 + método +
   IP. `POST /tcle/registrar` persiste (antes morria num dataclass em memória)
   e `POST /iniciar-chamada` **recusa com 409** sem consentimento vigente para
   aquela teleconsulta — o Art. 4º da Resolução CFM nº 2.314/2022 exige
   consentimento prévio, livre e esclarecido. Dois testes que documentavam a
   lacuna passam a provar o bloqueio.
3. **TM-3 — encerramento real da sala.** `finalizar-chamada` e
   `converter-presencial` agora encerram a sala no hub de sinalização
   (`hub_signaling.encerrar_sala`) e gravam `status` (CONCLUIDA/CANCELADA) +
   `data_expiracao` — antes as filas WebSocket ficavam abertas para sempre e a
   sala continuava aceitando conexões após o fim da consulta (o `_validar_sala`
   do WS passa a recusá-la).
4. **TM-4 — fim do `teleconsulta_id: 1` fixo.** A conversão para presencial
   resolve o id real (`resolverTeleconsultaAtiva`: campo do agendamento, com
   fallback pela sala); sem id, avisa o usuário em vez de registrar a conversão
   na teleconsulta errada. Teste estático impede o literal fixo de voltar.
5. **TM-5 — links do paciente utilizáveis.** Nova config `PUBLIC_BASE_URL`
   (default `http://localhost:8000`; em produção, o domínio real). A
   `sala_virtual_url` da jornada usa o `codigo_sala` real do agendamento em
   `/static/telemedicina_paciente.html` (antes: host errado, sem `/static/` e o
   `consulta_id` no lugar do código da sala); sem código real, o campo fica
   `None` em vez de gerar link morto. `gerar_link_paciente` e o link do portal
   pós-consulta também usam `PUBLIC_BASE_URL`.

**Ainda pendente:** provisionar `TURN_URL`/`TURN_USERNAME`/`TURN_CREDENTIAL`
(sem TURN, a chamada só conecta em rede local ou NAT não simétrico); P1
(tenant nos módulos restantes — prescrição/TISS/farmácia/convênios — e
tenant/estabelecimento no WS e em `SalaVirtual`; endurecimento do frontend:
CSP + cookie HttpOnly em vez de `localStorage`; hub de sinalização
single-instance — escalar para Redis com múltiplos workers; convite de paciente
de uso único).

**Fechado nesta rodada:** o **build Docker real** foi executado e validado
(`docker build` + container: entrypoint aplica as 9 migrações até
`c3d9e1f5a7b2` e `/health` responde 200 com `database: connected`); o
**redirect do SSO** deixou de fixar `localhost` e passou a usar
`PUBLIC_BASE_URL` (percent-encoded); e há **varredura transversal de 401**
sobre todas as rotas GET do router clínico (não só a lista manual anterior).

---

## 1. Resumo executivo

| Dimensão | Valor verificado | Fonte |
|---|---|---|
| Testes (`pytest -q`) | **714 passed, 0 failed** (~29 s), após P0-1/2/4/5/6/7/7b + TM-1..TM-5 + SSO/401 | Execução real na raiz |
| Teste de contrato frontend | **28 passed** | `test_contrato_frontend.py` |
| Testes novos desta sessão | **98** (16 RBAC/tenant + 7 auditoria + 7 persistência + 11 sessão + 19 teleconsulta + 11 teleconsulta-frontend + 18 retenção + 9 backup) + **67 da auditoria** | `test_*.py` correspondentes |
| Migrações Alembic | **9** (head `c3d9e1f5a7b2`) | `alembic upgrade head` |
| Tabelas SQLAlchemy (`Base.metadata.tables`) | **36** (37 no banco, com `alembic_version`) | Execução real |
| Operações OpenAPI registradas | **102** (95 paths) sob `/api/v1` (+ health/docs/static/root) + 2 rotas WebSocket | `app.openapi()` |
| Git | branch `main`, árvore limpa, 9 commits novos (`ad53e58` → `e8953c1`) | `git status` |
| Commit do T3 | `9c4f957` — `feat(telemedicina): teleconsulta WebRTC real com sinalizacao autenticada (T3)` | `git log` |
| Commit do P0.3 | `d722b1b` — `feat(conformidade): retencao, anonimizacao, backup verificado e politica de incidente (P0.3)` | `git log` |
| Correção da teleconsulta | `e8953c1` — `fix(telemedicina): aplica os servidores ICE do servidor antes de criar a PeerConnection` | `git log` |

**Veredito:** o backend sobe, migra, semeia, autentica, **autoriza por papel**,
**isola dados por clínica**, **audita leitura de PHI** e **transmite teleconsulta
de verdade** (áudio/vídeo ponto a ponto com sinalização autenticada), com
**621 testes verdes**. Nesta sessão foram fechados o **T1 (Acolhimento)**, o
**P0.1 (RBAC + tenant)**, o **P0.2 (auditoria verificável)**, o **T2 (receitas
persistidas)**, o núcleo do **P1 (sessão revogável)**, o **T3 (teleconsulta real)**
e a parte de código do **P0.3 (retenção/backup)**.

**Sobre a teleconsulta — o que está provado e o que não está:** a sinalização
(handshake, presença, SDP, ICE, `peer_left`, códigos de recusa) é verificada por
testes automatizados e por dois clientes WebSocket reais conversando com o
servidor; a ligação entre o HTML e os módulos JS é verificada por contrato
(ID existente, função global, módulo ES carregado). **Não** foi executada em
navegador real: a mídia saindo do alto-falante depende de câmera, microfone e
rede — e o `TURN` só existe quando `TURN_URL` é configurado. Ver §5.
O que resta para uso clínico com paciente real é **ciclo de vida do dado (P0.3)** e
**assinatura ICP-Brasil real (P0.4)** — ambos exigem decisão de política e
certificado, não apenas código.

---

## 2. O que já foi concluído recentemente (commits `e3d6fa7` → `b8d94bd`)

### ✅ Etapa 0 — Honestidade (concluída em `e3d6fa7`)
- Remoção da **simulação de teleconsulta** (`app.js:569-576` deixou de injetar a
  webcam do médico no vídeo remoto; badge de "Aceite Confirmado" deixou de ser texto fixo).
- Remoção do **médico hardcoded** (`prescricao_digital_cfm.py`) — receita não sai
  assinada com nome/CNPJ de pessoa real sem autenticação.
- Correção da **validação** que devolvia **500** em item de prescrição inválido → passa a
  **422** (falha alto).

### ✅ Etapa 1 — Fecho do fluxo presencial (concluída em `08d130a`)
- Criação da tabela `agendamentos` (migração `09250669ac4f`, +77 linhas).
- Agenda movida do **dicionário em memória** para **banco** (`agenda_medica.py`).
- **Check-in** com classificação de risco e persistência na `fila_acolhimento`.
- **SOAP persistido** via `POST /api/v1/atendimentos/` (FKs fila → atendimento).
- Testes: `test_agenda_medica.py` (+347 linhas) e `test_fluxo_presencial_completo.py`
  (+229 linhas) — **fluxo agenda → check-in → fila → SOAP** com teste de integração.

### ✅ Correções de identidade e compat (últimos commits)
- `1e7fd13` — fallback para `typing_extensions.Self` (compat Python 3.10).
- `3850abd` — remove aspas aninhadas em f-string (compat Python 3.10).
- `dda54f3` / `b8d94bd` — profissional titular passa a ser a **Dra. Francelli Neves
  Versiani**; autoria do software ao **Dr. João Paulo Versiani Ladeia**; expansão de demo
  roles e higienização de sessão.

### ✅ T1 — Aba de Acolhimento no Cockpit (implementada nesta sessão, não commitada)

Fecha o elo que faltava entre **check-in na agenda** e **fila de espera** na
interface: `static/js/fila_espera.js` já existia, correto e testado, mas **nunca
era incluído por nenhuma tela**.

| Arquivo | Alteração |
|---|---|
| `backend/app/static/index.html` | +70/−6 linhas: botão de menu `Acolhimento` (ícone `fa-triage`) e `<section id="aba-acolhimento">` com fila em tempo real, contador, painel de chamada e card de check-in (`fila-espera-lista`, `fila-espera-contador`, `fila-espera-chamada`, `fila-espera-atualizacao`, `select-checkin-consulta`, `select-checkin-risco`, `status-checkin-acolhimento`). Renumeração das abas comentadas para 1–9. |
| `backend/app/static/app.js` | +78/−1 linhas: `"acolhimento"` incluído em `abas`; loader no `trocarAba`; novas funções `obterPainelFilaEspera()` (import dinâmico de `fila_espera.js`), `carregarAcolhimento()`, `carregarConsultasCheckin()` e `realizarCheckinAcolhimento()` (POST idempotente em `/api/v1/agenda/{codigo}/checkin`). |

**Contratos usados (todos já existentes no backend):**
`GET /api/v1/fila/?status=AGUARDANDO_ATENDIMENTO` (polling 2 s ativo / 10 s ocioso) e
`GET /api/v1/agenda/` + `POST /api/v1/agenda/{consulta_id}/checkin?classificacao_risco=…`.

**Validação executada:**
- `node --check app.js` → **exit 0**; `node --check js/fila_espera.js` → **exit 0** (sintaxe).
- `test_contrato_frontend.py` → **28 passed** (nenhuma URL nova aponta para endpoint inexistente).
- Suíte completa → **520 passed, 0 failed** (exit 0).
- Estrutura HTML: 9 `<section>` / 9 `</section>` (abas 1–9), IDs únicos.
- Chaves do `app.js`: 510 `{` / 510 `}` (balanceado).

**Pendência conhecida do T1:** o painel inicia o polling ao abrir a aba e **não é
parado ao sair dela** (`parar()` existe na classe, mas não é chamado) — custo baixo,
mas convém ligar no `trocarAba`. Também não há botão de som na seção (opção
`idBotaoSom` é opcional e fica inativa).

### ✅ T3 — Teleconsulta real (WebRTC) — nesta sessão

Antes: `js/webrtc_manager.js` estava **pronto e correto, mas morto** — nenhuma tela
o importava, não havia cliente de sinalização e o hub WebSocket **republicava**
cada mensagem para todos os participantes, inclusive para quem a enviou (o `offer`
voltava ao ofertante e a negociação nunca fechava). O médico via a própria webcam
no lugar do paciente e a tela exibia, em letras claras, "A transmissão de vídeo
bidirecional ainda não está implementada".

| Arquivo | Alteração |
|---|---|
| `backend/app/services/signaling_hub.py` | **Novo.** `SignalingHub` com presença por sala, `entrar`/`sair`, limite de participantes, roteamento `enviar_para_outros` (nunca devolve ao remetente) e `estatisticas`. |
| `backend/app/api/v1/telemedicina_ws.py` | **Reescrito** (266 → 630 linhas). Autenticação por JWT (`?token=`), validação da sala em `salas_virtuais`, recusa de sala encerrada/expirada (4404), sala cheia (4409), conexão duplicada (4408), presença (`peer_joined`/`peer_left`), `deve_criar_oferta` apenas para o segundo, ping/pong, timeout ocioso e auditoria `ENTRAR_TELECONSULTA`/`SAIR_TELECONSULTA`. As classes legadas e o `HubTelemedicinaWS` foram preservados para os testes existentes. |
| `backend/app/api/v1/router.py` | Rota WS movida para o bloco **público**: `Depends(get_current_user)` é uma dependência HTTP e derrubava o handshake do WebSocket. A autenticação acontece dentro do handler. |
| `backend/app/api/v1/telemedicina.py` | +2 endpoints: `GET /telemedicina/ice-servers` (configuração STUN/TURN com aviso quando não há TURN) e `GET /telemedicina/salas/{codigo}/participantes` (presença em tempo real). |
| `backend/app/core/config.py` | `STUN_URLS`, `TURN_URL`, `TURN_USERNAME`, `TURN_CREDENTIAL`, `WS_SALA_MAX_PARTICIPANTES`, `WS_TIMEOUT_OCIOSO_SEGUNDOS` e a propriedade `ice_servers` (credenciais TURN nunca vão ao JavaScript, só a lista montada). |
| `backend/app/static/js/teleconsulta_sessao.js` | **Novo** (~400 linhas). Orquestrador: abre o WS autenticado, cria a oferta quando o servidor manda, troca SDP/ICE, enfileira candidatos que chegam antes do SDP remoto, ping de 25 s, reconexão com backoff (5 tentativas), eventos de estado reais para a UI, mute e compartilhamento de tela. |
| `backend/app/static/js/webrtc_manager.js` | `substituirTrackVideo()` (tela sem renegociar SDP), getter `peerConnection` e correção de `#obterTrack` — sem `deviceId` o código montava `{exact: null}` e o navegador recusava voltar para a câmera. |
| `backend/app/static/app.js` | `iniciarTeleconsultaWebRTC()` / `encerrarTeleconsultaWebRTC()`; `resolverSalaTeleconsulta()` cria a sala **real** no servidor (antes o código era inventado no navegador e não existia no banco); mute e "compartilhar tela" agora falam com a sessão; `finalizarTeleconsulta()` encerra o par e libera câmera/microfone. A webcam **deixou de abrir sozinha** ao trocar de aba (sem consentimento). |
| `backend/app/static/index.html` | O aviso "não implementada" virou botão **"Iniciar câmera e conectar"** + status ao vivo + nota de consentimento (LGPD Art. 11 / CFM 2.314). |
| `backend/app/static/telemedicina_paciente.html` | Script reescrito como módulo: entra na mesma sala, mostra o vídeo do médico, exibe o nome real do profissional e trata permissão negada/quedas. |
| `backend/tests/test_t3_teleconsulta_ws.py` | **Novo**, 19 testes (ver §1). |

**Validação executada:**
- Suíte completa → **583 passed, 0 failed**.
- `node --check` em `app.js`, `teleconsulta_sessao.js` e `webrtc_manager.js` → **exit 0**.
- **Teste real com dois clientes**: `uvicorn` na porta 8011 + dois WebSockets
  independentes negociando `offer`/`answer`/ICE e `peer_left` — **6/6 etapas OK**,
  incluindo a prova de que o servidor **não** devolve a oferta ao remetente.
- Trilha de auditoria conferida no banco: `ENTRAR_TELECONSULTA`/`SAIR_TELECONSULTA`
  gravados com sala, papel e nº de participantes; todos os elos escritos pelo código
  atual verificam pelo hash canônico.

**Correção encontrada ao auditar a teleconsulta (commit `e8953c1`):** a
`RTCPeerConnection` era criada em `#criarWebRTC`, **antes** de a mensagem
`sala_ingressada` chegar com a lista de ICE. Como a conexão copia a configuração no
construtor e nunca a relê, a chamada subia **só com STUN** — o `TURN` configurado no
servidor jamais era usado. Em rede hospitalar com firewall, o sintoma seria "a
chamada conecta para um lado e não passa mídia", sem erro visível. Agora o par é
criado em `#garantirPeerConnection`, chamado no `sala_ingressada` e antes de
responder oferta; reconexão reaproveita o par com `restartIce()`.
`test_t3_teleconsulta_frontend.py` (11 testes) trava essa ordem e as demais
fragilidades estruturais.

**Limitações conhecidas (honestas) do T3:**
- **Não houve teste em navegador real.** A sinalização é provada por testes e por
  dois clientes WebSocket reais; a ligação HTML↔JS é provada por contrato. O que
  **não** foi verificado de ponta a ponta é a mídia saindo do alto-falante: isso exige
  duas máquinas com câmera/microfone e rede real (e um `TURN` para o caso ruim).
- O hub de sinalização vive **na memória do processo**: funciona em um único
  worker/instância. Múltiplas instâncias exigem backplane (Redis pub/sub) — o código
  está isolado no `SignalingHub` para permitir essa troca.
- **Sem TURN** a chamada só conecta quando os dois lados conseguem se alcançar
  (mesma rede ou NAT não simétrico). `GET /telemedicina/ice-servers` devolve o aviso
  quando `TURN_URL` não está configurado; em rede hospitalar com firewall é obrigatório.
- Com `require_auth` ligado, o **paciente precisa estar autenticado** para entrar na
  sala (o token vem do `localStorage`). Um convite assinado de uso único para o
  paciente ainda não existe.
- A teleconsulta **não é gravada** (decisão de produto, não pendência técnica).

### ✅ P0.3 — Ciclo de vida do dado (parte executável em código) — nesta sessão

Antes: nada era apagado nunca. Refresh tokens expirados, cópias de contingência
já sincronizadas, telefone e nome de paciente em campanhas de dois anos atrás e
salas com link vencido ficavam no banco para sempre — risco desnecessário sob a
LGPD (Art. 15/16) e impacto maior em qualquer vazamento. Não havia backup, nem
política escrita, nem `SECURITY.md`.

| Arquivo | Entrega |
|---|---|
| `backend/app/services/retencao_dados.py` | **Novo.** Sete regras declarativas com prazo, base legal e ação (`EXPURGAR`, `ENCERRAR`, `ANONIMIZAR`, `REVISAR`). `plano()` nunca altera nada; `executar()` exige `confirmar=True`, é idempotente e grava `EXECUTAR_RETENCAO_DADOS` na trilha. |
| `backend/app/tools/retencao.py` | **Novo.** CLI `python -m app.tools.retencao [--executar] [--regra X] [--json]`, com o modo somente-leitura como padrão. |
| `backend/app/api/v1/conformidade.py` | **Novo.** `GET /conformidade/retencao` (plano) e `POST /conformidade/retencao/executar` (ADMIN + `confirmar: true`). |
| `scripts/backup_db.py` | **Novo.** Backup por API do SQLite (consistente com o banco em uso) ou `pg_dump`; SHA-256 em manifesto, `PRAGMA integrity_check`, poda das cópias antigas e restauração que exige `--forcar`. |
| `SECURITY.md` | **Novo.** Como reportar falha, prazos de resposta, o que está implementado e **as 8 lacunas reais** (CPF em claro, PAdES simulado, token em `localStorage`, sem rate limit, hub em memória, sem lockfile…), além do checklist mínimo de implantação. |
| `docs/POLITICA_RETENCAO_E_TRATAMENTO_DE_INCIDENTES.md` | **Novo.** Tabela de retenção espelhando o código, direitos do titular (Art. 18), contorno obrigatório enquanto não houver criptografia de campo, runbook de incidente (Art. 48) e desenho da criptografia futura. |
| `backend/app/static/app.js` | Painel da fila agora chama `parar()` ao sair da aba — antes o polling de 2 s continuava em toda aba aberta. |

**O que foi decidido de propósito:** registro clínico **não** é apagado nem
anonimizado automaticamente. A guarda mínima de 20 anos (CFM 1.821/2007 e
2.314/2022) e a anonimização de dado clínico são decisão humana — a regra
correspondente é `REVISAR` e só relata números.

**Validação executada:**
- Suíte → **610 passed** (18 testes de retenção + 9 de backup).
- CLI executada contra o banco de desenvolvimento: plano, execução (0 afetados) e
  evento `EXECUTAR_RETENCAO_DADOS` gravado (elo 13 da trilha).
- Backup real do banco de dev: 630 KB, **34 tabelas, `integrity_check = ok`**,
  SHA-256 conferido contra o manifesto; restauração recusada sem `--forcar`.

**O que continua aberto no P0.3:** CPF/CNS seguem em claro (o desenho está na
§9 da política: `cpf_hash` para busca + `cpf_cifrado` AES-256-GCM, migração em
duas etapas); não há criptografia de backup nem rotação de chave.

### ✅ CI
- `.github/workflows/ci.yml` (testes Python 3.12/3.13 + migration check) e
  `codeql.yml` (análise de segurança) **existentes**.

---

## 3. Estado por frente — o que falta (priorizado)

### 🔴 P0 — impede uso com dados reais (aberto)

| # | Frente | Estado | Evidência |
|---|---|---|---|
| P0.1 | **Isolamento de tenant / RBAC** | 🟢 **RESOLVIDO em grande parte** (`c56f318`) | `app/core/rbac.py` (novo) com `ContextoClinico`, `requer_papeis`, `filtrar_tenant` e `exigir_mesmo_estabelecimento`; **19 módulos** de `api/v1` declaram os papéis aceitos. Fila, agenda e atendimentos filtram pela clínica ativa e bloqueiam escrita cruzada (403). **Pendente:** receitas/TISS/farmácia ainda não verificam tenant registro a registro, e `cidadaos` é registro de pessoa compartilhado (decisão de modelagem). |
| P0.2 | **Auditoria de acesso a PHI** | 🟢 **RESOLVIDO em grande parte** (`922b426`) | Digest agora cobre `ip_address`, `user_agent` e `detalhes_json`; leitura do último elo com `FOR UPDATE`; `AuditService.verificar_cadeia()` audita a própria corrente; `auditar_acesso_phi()` registra leitura de prontuário (resumo e evoluções) com IP/UA. **Pendente:** auditar também leitura de cadastro, atendimento avulso, emissão de receita e exportação TISS; retenção/rotação da trilha. |
| P0.3 | **Ciclo de vida do dado** | 🟢 **RESOLVIDO na parte que é código** | Retenção/anonimização com 7 regras (`app/services/retencao_dados.py`), CLI e API restrita a ADMIN, backup verificado (`scripts/backup_db.py`), `SECURITY.md` e política de retenção/incidente escritas. **Aberto:** CPF/CNS ainda em claro (desenho na §9 da política) e backup sem criptografia própria. |
| P0.4 | **Assinatura ICP-Brasil/PAdES** | **ABERTO (mock)** | `vidaas_signature_service.py` sem chamada de rede; carimbo = UUID; URL do validador
(`validador.iti.gov.br/validar`) não é endpoint real; cert titular fixo no código. QR Code do PDF
entrega **hash de integridade SHA-256**, não assinatura jurídica. |

### 🟠 P1 — sessão e distribuição

| Item | Situação | Evidência |
|---|---|---|
| Token JWT de 24 h sem refresh/revogação | 🟢 **RESOLVIDO** (`7a1ace6`) | Access de **15 min** + refresh de **7 dias** com `jti` no banco, rotação a cada uso e revogação em cascata ao detectar reutilização. `expires_in` agora vem da mesma constante do token. |
| Token em `localStorage` | 🟡 **MITIGADO** | Refresh token em **cookie `HttpOnly`** (JS nunca o lê); access token ainda em `localStorage` por causa das 24 chamadas de `fetch` — migrar para cookie puro exige ajustar o interceptor. |
| Sem lockfile / `requirements` divergentes | ⬜ **ABERTO** | `requirements.txt` raiz (`>=`) ≠ `backend/` (`==`). |
| Docker não roda migração | ⬜ **ABERTO** | Imagem copia só `backend/app` (sem `alembic/`/`alembic.ini`). |
| Falta `SECURITY.md` | 🟢 **RESOLVIDO** | `SECURITY.md` na raiz: canal de reporte, prazos, controles implementados e as 8 lacunas assumidas. |

### 🟡 P2 — qualidade e manutenção (aberto)

- Frontend: **68% de código morto** (11/12 módulos JS não carregados); abas com dados
  **fictícios** (Pacientes, Honorários, TISS, Farmácia); 6 chamadas para endpoints inexistentes;
  XSS restante; acessibilidade ausente; service worker mentira; drafts em `localStorage`.
- Backend: FKs sem `ondelete`, `PRAGMA foreign_keys` off, índice ausente em `atendimentos_soap.cidadao_id`;
  sem tratamento global de exceção; `start.sh` só Linux. ~~WS de telemedicina sem
  autenticação~~ → **resolvido no T3**.
- **Documentação conflitante** — ver §4.

---

## 4. Frentes pendentes definidas no handoff (T1–T8)

Documento vivo: `docs/HANDOFF_TRABALHO_RESTANTE.md` (777 linhas, base `08d130a`).

| Tarefa | Escopo | Status |
|---|---|---|
| **T1** | Aba **Acolhimento** no Cockpit (`js/fila_espera.js` existe, nunca incluído) | ✅ **Concluída** (`ad53e58`) |
| **T2** | **Persistir receitas/CTE em banco** — antes em dicionário em memória (`_REPOSITORIO_DOCUMENTOS_CFM`) → QR Code dava 404 após restart | ✅ **Concluída** (`d57a982`) — tabela `documentos_clinicos`, migração `b7c31d9e4a02`, validação pública sem login |
| **T3** | **Teleconsulta real (WebRTC)** — `webrtc_manager.js` pronto e correto, mas **morto**; hub WS com roteamento/broadcast/join/quebra de estado | ✅ **Concluída** — `signaling_hub.py`, WS autenticado com presença e roteamento por destino, `teleconsulta_sessao.js`, UI do médico e do paciente, 19 testes + smoke com dois clientes reais |
| **T4** | Conformidade CFM/LGPD — persistir **TCLE**, auditar PHI, tenant, RBAC, lifecycle | 🟡 **Parcial** — TCLE ainda em memória; tenant/RBAC (P0.1), auditoria (P0.2) e lifecycle (P0.3) entregues |
| **T5** | Identificação de profissional (CRM/UF/RQE) — **parcialmente saneado** nos commits de identidade | 🟡 Parcial |
| **T6** | TISS (XML inválido, hash fake, XSD) e DMED (leiaute errado) | ⬜ Não iniciada |
| **T7** | ICP-Brasil — decisão: implementar VIDAAS ou remover alegações | ⬜ Não iniciada |
| **T8** | Operação/produto — gravação de teleconsulta, expiração de link, acessibilidade, código morto, Docker, lockfile, handler global, SW, drafts, WS copiloto auth | ⬜ Não iniciada |

**Sequência recomendada pelo handoff:** T1 → T2 → T3 → T4 → T6 → T7 → T8, com caminho
crítico Etapa 1 → Etapa 2 (fluxo presencial antes do vídeo).

---

## 5. Documentação — o que está desatualizado/confuso

| Documento | Situação |
|---|---|
| `docs/ROADMAP_V1.md` | **Fonte técnica confiável** para bloqueios (P0.1–P0.4, P1, P2). Data: 01/10/2026. |
| `docs/REVISAO_E_PLANO_DE_EVOLUCAO.md` | Diagnóstico detalhado (base `23daac5`). Confiável como evidência histórica. |
| `docs/HANDOFF_TRABALHO_RESTANTE.md` | **Documento de execução** para outro LLM (base `08d130a`). Atualizado pós-Etapa 1. |
| `docs/ESTADO_ATUAL.md` | ⚠️ **HISTÓRICO — NÃO CONFIÁVEL** (aviso no topo; afirmações desmentidas; mojibake). |
| `docs/STATUS_ATUAL_E_RECURSOS_IMPLEMENTADOS.md` | Relatório de auditoria anterior — tratado como não confiável no handoff. |
| `docs/RELATORIO_*`, `docs/MANUAL_FLUXO_OPERACIONAL_MEDIA.md`, `docs/DIRETRIZES_CLINICAS_OFICIAL.md`, `docs/SECOES_2_A_6_OFICIAL.md` | Descrevem **produto/fluxo que não existe** (ex.: "WebRTC roda lado a lado com o prontuário"). |
| `CHANGELOG.md` | ~570 KB / 9.580 linhas, saída automática multi-agente; **números de versão/testes divergentes** — não usar como fonte de status. |
| `INVENTARIO_DO_PROJETO.md` | Inventário automatizado do workspace (12/10/2026). Útil como mapa; não como status técnico. |

---

## 6. Conclusão e próximo passo sugerido

1. **Estado geral:** projeto funcional em desenvolvimento ativo; o núcleo (boot, migração,
   seed, auth, autorização, sessão, fluxo presencial, teleconsulta, retenção de dados)
   está verde com **610 testes passando**. Concluídos: **T1 (aba Acolhimento)**, **P0.1
   (RBAC + isolamento entre clínicas)**, **P0.2 (auditoria de PHI verificável)**, **T2
   (receitas persistidas)**, o núcleo do **P1 (sessão revogável com refresh rotativo)**,
   o **T3 (teleconsulta WebRTC real)** e a parte de código do **P0.3 (retenção,
   anonimização, backup e política de incidente)**.
2. **O que ainda impede piloto com paciente real:** **P0.4 (assinatura ICP-Brasil real:
   hoje é um UUID, não uma assinatura jurídica)** e a **criptografia de CPF/CNS em
   repouso** — esta última já tem desenho definido (§9 da política), falta executar a
   migração em duas etapas. P0.4 depende de certificado e decisão de fornecedor, não só
   de código.
3. **Sequência recomendada:** criptografia de campo (CPF/CNS) → `P0.4` → `T6`
   (TISS/DMED) → distribuição (`lockfile`, Docker com migração) → `T8` (gravação,
   expiração de link, acessibilidade).
4. **Ajustes pequenos herdados:** estender o RBAC de tenant para receitas/TISS/farmácia;
   auditar as demais leituras de PHI; mover o access token de `localStorage` para cookie
   puro; backplane Redis para o hub de sinalização quando houver mais de uma instância;
   rate limiting no gateway.

---

*Fim do status consolidado.*
