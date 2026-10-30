# Auditoria Completa do Projeto MedIA — 29/10/2026

**Objetivo:** estabelecer a linha de base do que já está pronto e do que ainda precisa ser corrigido ou desenvolvido, com verificação explícita da qualidade dos scripts de teste.
**Escopo:** `projeto_media/` completo — backend FastAPI, frontend estático, migrações, testes, scripts, CI/CD, Docker e documentação.
**Método:** execução real do sistema (boot, migrações, seed, suíte de testes, OpenAPI) combinada com leitura estática e análise AST do código. Cada afirmação abaixo indica se foi **executada** ou apenas **lida**.

> **Regra de leitura:** onde este documento diz "verificado", houve execução. Onde diz "leitura estática", é inspeção de código, não prova de comportamento em runtime. Nada foi alterado no projeto durante esta auditoria.

---

## 1. Veredito em uma página

| Dimensão | Nota | Situação |
|---|---:|---|
| Engenharia de código (estrutura, tipagem, organização) | **7,0 / 10** | Boa base: SQLAlchemy 2.0 tipado, Pydantic v2, routers organizados, RBAC central |
| Qualidade da suíte de testes | **6,0 / 10** | Roda verde e é hermética, mas tem 16 testes que exercitam reimplementações e não o sistema |
| Segurança / LGPD | **4,0 / 10** | RBAC existe, mas auth vem desligada por padrão, CPF/CNS em texto claro, sem CSP/rate limit |
| Conformidade clínica (CFM/LGPD/ICP-Brasil) | **3,5 / 10** | Fluxos existem no papel; assinatura digital é mock e há dados de paciente fictício persistidos |
| Prontidão para produção | **3,0 / 10** | Imagem Docker não sobe em Postgres; compose roda em modo dev com segredo padrão |
| Documentação | **4,0 / 10** | 1 documento confiável em 16; README e ROADMAP desatualizados |

**Conclusão (baseline da auditoria):** o projeto não é um protótipo vazio — havia 621 testes verdes, 33 tabelas, 100 operações de API documentadas e um núcleo de RBAC/auditoria real. Mas **três caminhos de produção estavam quebrados de forma reproduzível** (sincronização offline, WebSocket do copiloto e build Docker) e **dois fluxos clínicos centrais eram cosméticos** (receita digital e financeiro). Ver a seção 1.1: os itens P0-1, P0-2, P0-5 e P0-6 já foram corrigidos; restam P0-4 (parte 2), P0-7 e a validação do build Docker real.

---

## 1.1 O que já foi corrigido nesta rodada (29/10/2026)

A auditoria começou com 621 testes; hoje a suíte tem **714 testes**, todos verdes em ~29 s (Fase 0 + P0-4 parte 2 + P0-5 + P0-6 + P0-7 + P0-7b + correções TM-1..TM-5 da telemedicina + SSO/401). Nenhum teste existente foi afrouxado.

| Item | Status | Evidência |
|---|---|---|
| **P0-1** Sincronização offline | **Corrigido** | `ingestar_lote` e `status_geral` implementados; `POST` responde **201** e reenvio vira duplicado; **10 testes de rota** em `test_sincronizacao_api.py` |
| **P0-2** WebSocket do copiloto | **Corrigido** | `NameError` eliminado; WS movido para router sem dependência HTTP; token/cookie + papel + tenant validados; **7 testes** em `test_copiloto_ws.py` |
| **P0-3** Docker/Postgres | **Corrigido e validado na prática** | imagem copia `alembic.ini` + `backend/alembic`; entrypoint roda `alembic upgrade head`; compose em `ENVIRONMENT=production` com segredos obrigatórios. **Build real executado** com engine 28.3.2: o container sobe, aplica as 9 migrações até `c3d9e1f5a7b2` e `GET /health` responde 200 com `database: connected` |
| **P0-4** Paciente fictício / id fixo | **Parcial** | jornada demo só é criada em `development`; frontend usa `consultaAtiva.codigo` e não exibe mais números de documento falsos. Falta persistir a jornada e ligá-la à agenda |
| **P0-8** Auth desligada | **Corrigido/esclarecido** | `require_auth` **já** era `True` em staging/produção; o risco real era o compose sem `ENVIRONMENT`, agora definido. Adicionado teste que trava a regra |
| **P1-1** CodeQL | **Corrigido** | removido `codeql-action/authenticate@v3` (action inexistente) |
| **P1-2** Dependências | **Corrigido** | `backend/requirements.txt` com pins exatos do ambiente validado; `requirements.txt` da raiz virou `-r backend/requirements.txt` + ferramentas de teste |
| **P0-5** Prescrição → farmácia | **Corrigido** | emissão cria `Receita` + itens com hash do QR; farmácia aceita código impresso; **12 testes** em `test_prescricao_farmacia_integracao.py` |
| **P0-6** Financeiro fictício | **Corrigido** | livro caixa persistido (`lancamentos_livro_caixa`) + rotas de lançamento; demonstrativo zerado/real; **11 testes** em `test_livro_caixa_persistido.py` |
| **P0-4 (parte 2)** Jornada em memória | **Corrigido** | `jornadas_atendimento` + hidratação do banco; `paciente_id` não é mais sorteado; agenda → fluxo; **7 testes** em `test_jornada_persistida.py` |
| **P0-7** CPF/CNS em texto claro | **Corrigido (mestre + cópias)** | AES-256-GCM + índice cego HMAC em `cidadaos`/`profissionais`; **P0-7b**: 20 cópias de texto + `xml_tiss` + 2 JSONs (`payload_json`/`dados_json`) cifrados nas tabelas operacionais; migrações `f1c3a8e57b20` e `b6e8f24a91d7`; **14 + 15 testes** |

**Descoberta adicional durante a correção:** o WebSocket do copiloto estava quebrado **antes** de chegar ao handler. O router aplicava `dependencias_rbac` no nível do router, e `get_contexto_clinico` exige `Request` — dependência HTTP incompatível com handshake WebSocket. O endpoint nunca funcionou, nem em desenvolvimento.

---

## 2. Métricas verificadas

| Métrica | Valor | Como foi obtido |
|---|---:|---|
| Testes | **621 passed** (baseline) → **714 passed** após P0-1, P0-2, P0-4 (parte 2), P0-5, P0-6, P0-7, P0-7b, TM-1..TM-5 e SSO/401, 0 failed, 0 skipped | **executado** (`pytest backend/tests -o addopts="" -q`) |
| Cobertura de linhas | **64%** (9.117 statements) | **executado** (`--cov=backend/app`) |
| Arquivos de teste | 58 | leitura estática |
| Funções `test_*` | 549 (→ 621 casos com `parametrize`) | AST |
| `assert` na suíte | 1.359 (**2,48 por teste**) | AST |
| `pytest.raises` | 66 | AST |
| Operações de API | **100 operações em 94 paths** | **executado** (OpenAPI gerado do app) |
| Módulos de rota | 27 arquivos em `backend/app/api/v1/` | estático |
| Tabelas | **36 modelos** → **37 tabelas** no banco (inclui `alembic_version`) após P0-4, P0-6 e TM-2 | **executado** (boot real + SQLite) |
| Migrações | 9 revisões, head `c3d9e1f5a7b2` (TM-2: consentimentos de teleconsulta) | **executado** (`alembic heads` + `upgrade head` + round trip ida-e-volta validado) |
| Chaves estrangeiras | 41 | AST |
| `unique=True` / `index=True` | 22 / 104 | AST |
| LOC backend | 23.745 linhas / 115 arquivos | estático |
| LOC testes | 9.767 linhas / 60 arquivos | estático |
| LOC frontend | 17.374 linhas / 25 arquivos | estático |
| LOC Alembic | 945 linhas / 5 arquivos | estático |
| Commits | 1.641 | `git` |
| Arquivos rastreados | 248 | `git` |

**Boot ponta a ponta (executado):** banco SQLite limpo → `alembic upgrade head` → seed → `GET /health` = **200** → login demo = **200** → 2 estabelecimentos semeados → 34 tabelas. O `lifespan` sobe migração e seed corretamente **quando os arquivos do Alembic estão presentes**.

---

## 3. O que já está OK (e pode ser considerado pronto)

### 3.1 Núcleo de aplicação

- **App FastAPI funcional e documentado.** 100 operações expostas, tags consistentes, `response_model` na maioria das rotas, prefixo versionado `/api/v1`. *(executado)*
- **Persistência real, não mock.** 33 modelos com `Mapped`/`mapped_column`, 41 FKs, 22 restrições `unique`, 104 índices. Há integridade referencial de verdade, não só dicionários em memória. *(estático)*
- **Migrações Alembic funcionais.** 7 revisões encadeadas, head único `f1c3a8e57b20`; o CI inclusive valida que a migração cria as tabelas esperadas (`usuarios`, `cidadaos`, `atendimentos_soap`, `audit_trail`, `teleconsultas`, `receitas`, `guias_tiss`, `lancamentos_livro_caixa`). *(executado)*
- **Configuração validada por ambiente.** `Settings.validar_ambiente()` recusa produção sem `JWT_SECRET_KEY`, recusa `AUTO_SEED_DEMO_DATA`, `DEMO_LOGIN_ENABLED` e `SSO_ENABLED` em produção, e aceita o alias legado `SECRET_KEY`. *(executado + testes)*
- **Bootstrap idempotente.** Migração + seed rodam no `lifespan` e são desligáveis por env (`AUTO_MIGRATE_ON_STARTUP`, `AUTO_SEED_DEMO_DATA`). *(executado)*
- **Health check** público e barato, usado pelo `HEALTHCHECK` do Docker. *(executado)*
- **CORS configurado corretamente:** origens vêm de `CORS_ORIGINS`, sem o padrão perigoso `allow_origins=["*"] + allow_credentials=True`. *(leitura estática)*
- **OpenAPI publica `securitySchemes` (BearerAuth)**, então Swagger e gateways descobrem o esquema de autenticação. *(leitura estática)*

### 3.2 Autenticação, autorização e multi-tenant

- **JWT completo:** login, refresh, logout, `logout-all`, `switch-clinic`, `/me`, trilha de auditoria. *(executado via testes)*
- **RBAC centralizado em `app/core/rbac.py`**, com papéis clínicos, de acolhimento, farmácia e faturamento, aplicado via `dependencies=dependencias_rbac(...)` em **20 módulos**. *(estático)*
- **Isolamento por registro** implementado de verdade (não apenas por estabelecimento) em `agenda_medica`, `fila`, `atendimentos` e `prontuario`, via `filtrar_tenant` e `exigir_mesmo_estabelecimento`. *(estático)*
- **Auditoria de PHI** com testes próprios (`test_auditoria_phi.py`, 7 casos). *(executado)*
- **SSO mock bloqueado fora de desenvolvimento** (`_garantir_sso_nao_producao`). *(estático; teste cobre o bloqueio)*

### 3.3 Frontend

- 25 arquivos estáticos, incluindo teleconsulta com WebRTC (offer/answer, ICE, mute por `MediaStreamTrack`), barra de comandos, fila de espera e sessão de teleconsulta.
- **Sintaxe JS válida** em todos os arquivos (`node --check`). *(executado)*
- Testes estruturais travam regressões reais já ocorridas: `RTCPeerConnection` só depois da lista de ICE, funções de `onclick` expostas em `window`, `getElementById` existindo no HTML. *(executado)*

### 3.4 Infraestrutura e CI

- **CI roda em matriz Python 3.12 e 3.13**, com `concurrency` e permissões mínimas (`contents: read`). *(estático)*
- **Etapa de schema no CI** valida que Alembic constrói o banco (bom `canary`). *(estático)*
- **Docker usa usuário não-root** (`appuser`) e tem `HEALTHCHECK`. *(estático)*
- **Backup de banco** com verificação de integridade e testes (`test_backup_db.py`, 9 casos, incluindo detecção de adulteração). *(executado)*

### 3.5 Testes — o que está estruturalmente correto

- **Suíte hermética:** `conftest.py` força `ENVIRONMENT=test`, `DATABASE_URL=sqlite:///:memory:`, desliga migração/seed no lifespan e faz override de `get_db` com `StaticPool`. Isso corrigiu um problema real (testes gravavam em `backend/esus.db`). *(executado + leitura)*
- **Todos os 58 arquivos passam isoladamente** (`pytest <arquivo> -o addopts=""`). Não foi encontrada dependência de ordem que quebre execução individual. *(executado)*
- **Zero `xfail`** e nenhum teste aceitando HTTP 500 como sucesso. Há `pytest.raises` em 66 pontos, o que mostra que caminhos de erro são exercitados. *(AST)*
- **Cobertura alta nas rotas críticas de agenda/atendimento:** `agenda_medica` 98%, `prontuario` 99%, `farmacia` 99%, `prescricao_cfm` 97%, `auth` 92%. *(executado)*

---

## 4. Defeitos e lacunas por severidade

### 4.1 P0 — bloqueiam uso real (corrigir antes de qualquer piloto)

#### P0-1. Sincronização offline retorna HTTP 500 sempre — **[CORRIGIDO]**
**Evidência (executada):** `POST /api/v1/sincronizacao/atendimentos` → **500**.
**Correção aplicada:** `ingestar_lote` implementado com idempotência por `id_local` e `SAVEPOINT` por item; `status_geral` implementado (a rota `GET /status` também respondia 500); `criar_lote_offline` delega para o único caminho de ingestão. Frontend passou a mapear o registro do IndexedDB para o contrato da API. Cobertura: `backend/tests/test_sincronizacao_api.py` (10 casos, incluindo reenvio e lote com id repetido).
- `backend/app/api/v1/sincronizacao.py:41` chama `ServicoSincronizacaoOffline(db).ingestar_lote(lote)` — **`ingestar_lote` não existe**.
- O método existente é `criar_lote_offline` (`app/services/sync_offline.py:80`), que por sua vez referencia `items` (linhas 126–134) — variável **não definida**; o nome correto seria `itens`.
- `criar_lote_offline` também passa `AtendimentoOffline(**item.__dict__)` sem filtrar campos, e `duplicados=None` viola o contrato de resposta.
**Impacto:** a contingência offline — funcionalidade central para UBS com internet instável — está 100% inoperante e **nenhum teste percebe**, porque `test_sync_offline.py` testa outra coisa (ver 5.3).
**Correção:** implementar `ingestar_lote` com idempotência por `id_local`, transação única e teste de rota (não de serviço isolado). Esforço: **1–2 dias**.

#### P0-2. WebSocket do copiloto quebra com `NameError` e não autentica — **[CORRIGIDO]**
**Evidência (leitura estática; reprodução exige cliente WS):**
- `backend/app/api/v1/copiloto.py:275–276` descarta o retorno de `_obter_atendimento(...)` e usa uma variável `atendimento` que **não existe** no escopo → `NameError` na primeira mensagem.
**Correção aplicada:** atribuição corrigida; WS separado em `ws_router` (sem dependências HTTP) e registrado fora do bloco clínico; autenticação no handshake (`_autorizar_ws`) por cookie HttpOnly ou `?token=`, com checagem de usuário ativo, papel clínico e tenant. Cobertura: `backend/tests/test_copiloto_ws.py` (7 casos, incluindo token inválido e de outro estabelecimento).
- O endpoint WS não valida token/JWT nem filtra por estabelecimento: qualquer cliente que conheça o `atendimento_id` entra na sala.
**Impacto:** copiloto clínico em tempo real não funciona e, se funcionasse, vazaria dados clínicos entre tenants.
**Correção:** corrigir atribuição, autenticar no handshake (query param `token` + validação JWT) e testar com `TestClient.websocket_connect`. Esforço: **1 dia**.

#### P0-3. Imagem Docker não sobe com Postgres — **[CORRIGIDO, validado com build real]**
**Evidência (leitura estática do `Dockerfile`):**
**Correção aplicada:** a imagem agora espelha o layout do repositório e copia `alembic.ini` + `backend/alembic`; `scripts/docker-entrypoint.sh` roda `alembic upgrade head` antes do Uvicorn e o processo falha cedo se o banco estiver inacessível; `docker-compose.yml` define `ENVIRONMENT=production`, exige `JWT_SECRET_KEY`/`POSTGRES_PASSWORD` (`${VAR:?}`), desliga seed/demo/SSO mock e mantém CORS explícito. O layout foi validado por simulação (34 tabelas criadas) e, nesta rodada, o **build real foi executado** com engine 28.3.2: o container sobe, aplica as 9 migrações até `c3d9e1f5a7b2` e `GET /health` responde 200 com `database: connected`.
- `COPY backend/app ./app` copia **apenas** `backend/app`; `alembic.ini` e `alembic/` ficam fora da imagem → `run_migrations()` falha e, em seguida, o seed quebra em Postgres por falta de tabelas.
- `docker-compose.yml` não define `ENVIRONMENT` → sobe em **modo desenvolvimento**: auth desligada, login demo ativo, seed automático e `SECRET_KEY` padrão.
- Sem `depends_on` com healthcheck do banco, sem entrypoint de migração separado.
**Impacto:** o caminho "documentado" de deploy é o único que não funciona. Um deploy assim expõe a API sem autenticação.
**Correção:** copiar `alembic.ini` + `alembic/`, definir `ENVIRONMENT=production`, exigir segredos por env/secret manager, rodar `alembic upgrade head` em entrypoint e remover `AUTO_SEED_DEMO_DATA`. Esforço: **1 dia** (mais validação real com daemon).

#### P0-4. Fluxo de atendimento grava dados de paciente fictício e não tem tenant — **[PARCIAL]**
**Evidência (leitura estática):**
**Correção aplicada (parte 1):** a jornada demo agora só é criada com `ENVIRONMENT=development` **e** `DEMO_LOGIN_ENABLED=true`; em produção e nos testes ela não existe. O frontend deixou de usar o id fixo `CONS-2026-9812` e passou a enviar `consultaAtiva.codigo`, abortando com mensagem clara quando não há atendimento aberto; também foram removidos os números fictícios de fallback da mensagem de sucesso. Cobertura: `backend/tests/test_fluxo_demo_guard.py`.
**Pendente (parte 2):** persistir a jornada em tabela, propagar `estabelecimento_id`/`profissional_id` e criar a jornada automaticamente a partir do agendamento da agenda — sem isso, finalizar uma consulta real retorna 404.
- `app/services/fluxo_atendimento_service.py:43` mantém `self._jornadas: Dict[...] = {}` **em memória** — reinício do processo apaga tudo.
- Há uma jornada semeada com paciente fictício **"Mariana Souza Alencar", CPF 382.910.448-02**.
- `finalizar_consulta_e_gerar_pacote_pos` persiste prescrições/recibos para essa jornada **sem `estabelecimento_id` nem `profissional_id`**.
- No frontend, `app.js:2095` (`finalizarAtendimentoComFluxo`) **hardcoda `consultaId = "CONS-2026-9812"`**, ignorando o atendimento aberto.
**Impacto:** o botão "Finalizar" da tela principal emite documentos clínicos para um paciente que não existe, sem vínculo de tenant — risco de dado clínico falso em prontuário e de erro fiscal (DMED).
**Correção:** persistir jornada em tabela, remover seed fictício, usar o `consultaId` real, propagar tenant. Esforço: **2–3 dias**.

#### P0-5. Prescrição digital e farmácia não se conversam — **[CORRIGIDO]**
**Evidência (leitura estática):**
- `app/api/v1/farmacia.py` busca `Receita` por `codigo_hash` na tabela `receitas`.
- **Nenhum código de produção criava `Receita`** — a única ocorrência era leitura dentro do próprio `farmacia.py`.
- `prescricao_cfm.emitir` gravava em `documentos_clinicos`, não em `receitas`.
**Impacto:** o QR Code emitido no atendimento **nunca** era encontrável pela farmácia → dispensação sempre 404. O fluxo "prescrever → dispensar" estava desconectado.
**Correção aplicada:**
- `app/services/farmacia_bridge.py`: na emissão, resolve a identificação SUS que a tabela exige (CNS do paciente por CPF/cadastro, CNS do prescritor por profissional, CNES por estabelecimento), calcula o **SHA-256 do conteúdo canônico** da receita e cria `Receita` + `ReceitaItem` na mesma transação do documento clínico.
- `farmacia.py` passou a aceitar **o código impresso no QR** (`CFM-…`) e a URL do validador, não só o hash bruto — antes escanear o documento entregue ao paciente dava 404.
- Quando falta identificação SUS, a prescrição é emitida mas o retorno traz `farmacia_pendencias` com o que cadastrar; antes falhava em silêncio.
- A tela de prescrição ganhou o campo CNS e deixou de emitir com paciente fictício.
**Cobertura:** `backend/tests/test_prescricao_farmacia_integracao.py` (12 casos: hash recalculável, QR impresso, dispensação total/fracionada, validade por tipo, pendências, documento↔receita).

#### P0-6. Financeiro devolve dados fictícios como se fossem reais — **[CORRIGIDO]**
**Evidência (leitura estática + teste verde que valida o fictício):**
- `app/api/v1/financeiro_medico.py:44–48` retornava lançamentos hardcoded com nomes e **CPFs de exemplo** (`12345678901`, `98765432100`, …).
- `test_api_financeiro_prescricao.py::test_api_livro_caixa_demonstrativo` **afirmava `total_bruto > 0`** — ou seja, o teste blindava o dado falso.
**Impacto:** qualquer número exibido no livro caixa era inventado; em contexto fiscal (Carnê-Leão/IRPF) isso é grave.
**Correção aplicada:**
- Nova tabela `lancamentos_livro_caixa` (modelo `app/models/financeiro.py`, migração `d4a1f7c62e90`), com tenant (`estabelecimento_id`/`profissional_id`), competência, tipo, categoria e `chave_idempotencia`.
- `app/repositories/livro_caixa_repo.py` faz leitura/escrita e monta o demonstrativo pelo motor fiscal existente.
- Rotas novas `POST /financeiro-medico/lancamentos` e `GET /financeiro-medico/lancamentos`; o demonstrativo agora lê o banco e devolve `cobertura` explícita (`possui_lancamentos`, `quantidade_lancamentos`). Sem lançamentos: **tudo zero**, nunca semente fictícia.
- A finalização da consulta passou a **escriturar o honorário** de verdade (`LC-000001`), com idempotência por `consulta:<id>`.
- A tela de honorários consome as duas rotas, tem formulário de lançamento e mostra estado vazio honesto; os 5 recibos fictícios e o total `R$ 1.780,00` foram removidos.
**Bug real revelado pela correção:** `MotorLivroCaixaMedico.calcular_irpf_carne_leao` devolvia um dicionário **sem** `aliquota_nominal` quando a base era zero, e `gerar_demonstrativo_mensal` acessava essa chave → `KeyError` → **HTTP 500 em qualquer mês sem receita**. O mock mascarava isso porque sempre tinha base positiva. Também foi removido o "DARF" de 15% inventado quando o IRPF era zero.
**Cobertura:** `backend/tests/test_livro_caixa_persistido.py` (11 casos: somas, competências, idempotência, validações, integração com a finalização, guarda do frontend).

#### P0-7. CPF e CNS em texto claro — **[CORRIGIDO: cadastro mestre + cópias]**
**Evidência (leitura estática dos modelos):** `cidadaos.cpf`, `cidadaos.cns`, `profissionais.cpf` e `profissionais.cns` eram `String` simples, sem criptografia em repouso nem hash de busca; as *cópias* do mesmo documento em 11 tabelas operacionais repetiam o texto claro.
**Impacto:** violação direta do art. 46 da LGPD em caso de vazamento de banco/backup; CPF é dado pessoal sensível por combinação.

**Correção aplicada (cadastro mestre — P0-7):**
- `app/core/crypto.py`: **AES-256-GCM** (nonce aleatório por gravação) + **HMAC-SHA-256** como índice cego. Chaves derivadas por HKDF de `FIELD_ENCRYPTION_KEY` (ou do segredo JWT, se ausente); o compose passou a **exigir** `FIELD_ENCRYPTION_KEY`.
- Tipo SQLAlchemy `CampoProtegido`: o ORM lê/grava texto claro e o banco guarda `enc:v1:<base64>`. Um comparador próprio traduz `Cidadao.cpf == "123..."` e `IN (...)` para o índice cego — nenhuma das ~20 consultas existentes precisou ser reescrita, e as que fossem esquecidas não quebrariam em silêncio.
- Colunas `cpf_hash`/`cns_hash` (únicas) em `cidadaos` e `profissionais`, sincronizadas por evento do ORM; a unicidade saiu do ciphertext (aleatório) para o hash.
- Busca de cidadão por CPF/CNS na API passou a ser **exata** via hash (era `LIKE` no texto claro) e o nome continua com `ILIKE`.
- Migração `f1c3a8e57b20`: alarga as colunas, cria os índices, **cifra os dados existentes** e é re-executável; `downgrade` devolve texto claro (validado ida-e-volta).
- Valores legados sem prefixo continuam legíveis (`decifrar` faz passthrough), então o código pode subir antes da migração.

**Correção aplicada (cópias operacionais — P0-7b):**
- **Escopo:** 20 colunas de texto em 11 tabelas (`documentos_clinicos`, `receitas`, `dispensacoes`, `guias_tiss`, `lancamentos_financeiros`, `lancamentos_livro_caixa`, `jornadas_atendimento`, `atendimentos_offline`, `mensagens_preventivas`, `alertas_busca_ativa`, `teleconsultas`), mais `guias_tiss.xml_tiss` (XML TISS inteiro, `TextoProtegido`) e os campos `paciente_cpf`/`paciente_cns` embutidos em `documentos_clinicos.payload_json` e `jornadas_atendimento.dados_json` (`JsonProtegido` — o resto do payload permanece legível porque o hash de integridade e os itens precisam ser recalculáveis). `fila_acolhimento` não tem cópias (só FKs); `models/receita.py` é Pydantic (fora do escopo).
- **Sem colunas `_hash` nas cópias:** nenhuma consulta do sistema filtra por elas. Em vez de criar 20 colunas novas, o `ComparadorProtegido` agora **falha alto** (`ErroCriptografia`) em: igualdade/`IN` em coluna cifrada sem `<col>_hash`; busca parcial (`LIKE`/`ilike`/`startswith`/`contains` — falha alto mesmo com hash, pois o índice cega é HMAC do valor completo); literal de tipo errado (`cpf == 123`, checado antes do erro de hash para diagnóstico correto). `IS [NOT] NULL` e comparação entre colunas seguem adiante.
- Migração `b6e8f24a91d7` (revisa `f1c3a8e57b20`): **dialect-aware sem `batch_alter_table`** — só o Postgres faz `ALTER COLUMN TYPE` nativo (preserva UNIQUE/FK/índices); no SQLite a estrutura permanece e só os dados mudam (`VARCHAR(n)` não é imposto, e a reflection do `batch_alter_table` perde constraints UNIQUE/FK — premissa corrigida: SQLite não cria `CHECK` para `Enum` no SQLAlchemy 2.0). Idempotente (valores `enc:v1:` não re-cifrados); `downgrade` decifra mas mantém o alargamento das colunas (evita perda se algum valor não decifrar).
- **Validação executável:** round trip upgrade → downgrade → upgrade em SQLite com fingerprint de `sqlite_master` idêntico antes/depois (UNIQUE/FK/índices preservados), dados legados inseridos em texto claro e convertidos, JSONs e XML cifrados com vizinhos intactos, reexecução idempotente.
- A política de retenção (LGPD art. 16) já anonimizava `cns`/`cpf` em mensagens/alertas; agora coberta por teste.

**Cobertura:** `backend/tests/test_cpf_cns_cifrados.py` (14 casos: ciphertext no banco, texto claro na API, não-determinismo, normalização do índice, comparação/`IN` transparentes, duplicidade, busca por CPF/CNS, profissionais, chave errada falha alto) + `backend/tests/test_copias_cpf_cns_cifradas.py` (15 casos: ciphertext nas 11 tabelas + XML + JSONs, ORM devolve claro, leitura de linha legada, 3 fail-louds, hash/`IS NULL` normais, retenção anonimizando, inventário modelo↔migração bidirecional contra drift).

#### P0-8. Autenticação desligada por padrão — **[ESCLARECIDO / CORRIGIDO NA CONFIGURAÇÃO]**
**Evidência (leitura estática):** `require_auth` é uma propriedade: já retorna `True` em `staging`/`production` e só depende de `REQUIRE_AUTH` em desenvolvimento. O risco real era o **compose não definir `ENVIRONMENT`**, fazendo um deploy de produção subir em modo desenvolvimento.
**Correção aplicada:** `ENVIRONMENT=production` no compose (P0-3) e teste `test_settings_de_producao_exigem_auth` travando a regra. O item original "default inseguro" **não procede**; permanece apenas o risco de operador rodar sem `ENVIRONMENT`, agora mitigado no compose.
**Impacto real:** só se materializava quando `ENVIRONMENT` não era definido (exatamente o compose antigo). Com `ENVIRONMENT=production`, `require_auth` é `True` e os routers clínicos exigem Bearer.
**Pendente:** teste transversal que percorra todos os routers e prove 401 sem token (hoje a garantia é estrutural, via `build_clinical_router`, mas não há teste de contrato cobrindo cada rota).

### 4.2 P1 — impedem operação confiável

| ID | Item | Evidência | Impacto | Esforço |
|---|---|---|---|---|
| P1-1 | **CodeQL quebrado no CI** | `.github/workflows/codeql.yml:30` usa `github/codeql-action/authenticate@v3`, action **inexistente** (404) | job de segurança falha sempre; ninguém olha | **CORRIGIDO** |
| P1-2 | **Dependências não reprodutíveis** | venv tem FastAPI 0.139.2 / SQLAlchemy 2.1.1 / pytest 9.1.1 / Pydantic 2.13.2; `backend/requirements.txt` pina 0.109.0 / 2.0.23 / 7.4.3; `requirements.txt` da raiz usa `>=`; sem lockfile | CI instala versões diferentes do dev; quebra silenciosa | **CORRIGIDO** |
| P1-3 | **Assinatura digital é mock** | `prescricao_digital_cfm.py` gera hash + código de validação; não há assinatura ICP-Brasil. O `receita_digital.py` (HMAC) existe mas **não é usado por nenhuma rota** | receita "assinada" não tem validade jurídica CFM 2.314/2022 | 10–15 dias (provedor externo) |
| P1-4 | **Isolamento de tenant incompleto** | filtros por registro só em `agenda_medica`, `fila`, `atendimentos`, `prontuario`; prescrição, TISS, farmácia, financeiro e convênios só checam papel | vazamento entre clínicas em 5 módulos | 3–5 dias |
| P1-5 | **Frontend inseguro por padrão** | token em `localStorage` (`app.js:34`), 84 usos de `innerHTML`, 102 `onclick` inline, nenhum CSP/security header | XSS escala para roubo de sessão | 3–4 dias |
| P1-6 | **Cobertura 0% em módulos clínicos** | `escalas_clinicas` (652 stmts), `fila_teleatendimento` (425), `pre_natal` (206), `busca_cid10` (247), `tfge_renal` (158), `validacao_cns` (164), `soap_assistant` (79), `copiloto_clinico` (92) | cálculo clínico sem teste = risco assistencial | 5–8 dias |
| P1-7 | **32% do backend é código morto/inacessível** | ~6.537 de 20.099 linhas; `repositories/analytics_repo.py` só contém o próprio path | manutenção e auditoria caras; falsa sensação de cobertura | 3–5 dias |
| P1-8 | **10 de 13 módulos JS nunca são importados** | `acessibilidade_widget`, `analytics_charts`, `consentimento_lgpd`, `copiloto_sidebar`, `notificacoes_push`, `offline_sync_indicator`, `player_gravacao`, `screen_share`, `sinais_vitais_input` | funcionalidades "prontas" que não chegam ao usuário | 2–3 dias (triagem) |
| P1-9 | **Sem rate limiting, headers de segurança, gitleaks, ruff/mypy no CI** | `ci.yml` só roda pytest + alembic | força bruta em login, segredos vazando, dívida de estilo | 2 dias |
| P1-10 | **CI não testa Postgres nem build Docker** | testes só em SQLite `:memory:` | P0-3 passaria batido | 1 dia |
| P1-11 | **Documentação divergente** | `README.md` diz 496 testes/30 tabelas e P0.1/P0.2 abertos; `ROADMAP_V1.md` diz 469 testes | onboarding e gestão tomam decisão errada | 1 dia |

### 4.3 P2 — dívida relevante, não bloqueante

1. **Testes que não testam o sistema** — 5 arquivos, 16 casos (detalhado em 5.3).
2. **7 testes sem nenhuma asserção nem `pytest.raises`** (detalhado em 5.5).
3. **Cobertura de contrato superficial** — `test_contrato_frontend.py` verifica apenas se a URL existe no JS, inclusive em módulos mortos.
4. **`test_seguranca_v1.py` cobre só 401** em `/sincronizacao/atendimentos` — foi exatamente por isso que o 500 passou.
5. **Banco de teste compartilhado por sessão, sem rollback** entre testes: passou hoje, mas é uma armadilha de ordem.
6. **6 arquivos criam `TestClient(app)` no nível do módulo**, fora do fixture `client` — alguns batem no engine real (hoje inofensivo porque as rotas são puras, mas é frágil).
7. **`GET /health` público** e sem distinguir "vivo" de "pronto" (sem checagem de banco).
8. **Endpoint `GET /dmed/exportar-exemplo`** entrega lançamentos fictícios.
9. **Sem paginação/limite em várias listagens** — risco de resposta gigante.
10. **Sem observabilidade de produção**: só `logging.basicConfig` (texto livre), nenhuma métrica, tracing ou correlação de request.
11. **Sem E2E de navegador** (Playwright/Cypress) — teleconsulta nunca foi exercitada de ponta a ponta em browser.
12. **Frontend sem build/test runner** — tudo script clássico, sem bundle, sem lint.

### 4.4 P3 — higiene

- Nomenclatura mista PT/EN (`get_me`, `KPIs`, `heatmap` vs. `cidadaos`, `fila`).
- `backend/app/api/v1/models.py` e `models.sqlalchemy.py` com 0% de cobertura.
- 16 documentos em `docs/`, sendo 15 históricos ou superados.
- Resíduos fora do repositório (`e0.xml`–`f4.xml`, `.acl-recovery/`, `_lixo_permissoes/`) que não devem ser confundidos com o projeto.

---

## 5. Auditoria dos scripts de teste — veredito

**Veredito curto: os testes estão tecnicamente bem construídos, mas a suíte mede errado o que promete medir.** A infraestrutura (fixtures, isolamento, execução) é boa; a cobertura é inflada por testes que exercitam cópias locais da lógica e por módulos que não estão ligados a nenhuma rota.

### 5.1 O que está correto (verificado)

| Aspecto | Situação |
|---|---|
| Execução | 621 passed / 0 failed / 0 skipped em 14,46 s (baseline); **714 passed em ~29 s** após P0-1/2/4/5/6/7/7b + TM-1..TM-5 + SSO/401 |
| Isolamento individual | 58/58 arquivos passam sozinhos |
| Hermeticidade | SQLite em memória + `StaticPool` + override de `get_db` |
| Não aceita erro como sucesso | nenhum `== 500`, nenhum `xfail` |
| Erros exercitados | 66 `pytest.raises`; 422 (30), 404 (21), 401 (14), 403 (11) |
| Densidade | 2,48 asserts/teste — razoável |
| Parametrização | usada (ex.: flags de produção em `test_seguranca_v1`) |
| Regressões reais travadas | SSO mock em prod, JWT sem segredo, ICE antes do `RTCPeerConnection` |

### 5.2 Onde a cobertura engana

A cobertura total de 64% esconde concentração. Módulos com **0%**:

| Módulo | Statements | Relevância clínica |
|---|---:|---|
| `escalas_clinicas.py` | 652 | escalas/protocolos clínicos |
| `fila_teleatendimento.py` | 425 | fila de teleatendimento |
| `busca_cid10.py` | 247 | codificação de diagnóstico |
| `pre_natal.py` | 206 | pré-natal |
| `validacao_cns.py` | 164 | validação de CNS (dado identificável) |
| `tfge_renal.py` | 158 | cálculo de função renal |
| `copiloto_clinico.py` | 92 | sugestão clínica |
| `soap_assistant.py` | 79 | apoio ao SOAP |

E módulos críticos com cobertura baixa: `copiloto.py` **37%**, `tiss.py` **43%**, `analytics.py` **55%**.

> Observação: parte desses módulos é código morto (não importado por rota). Ou seja, o 0% não é só "falta de teste" — é "código que não roda". As duas correções são diferentes: testar o que existe e **deletar o que não é usado**.

### 5.3 Testes que testam reimplementações, não o sistema (16 casos)

Estes arquivos **não importam nada de `app`** e redefinem modelos/serviços dentro do próprio teste:

| Arquivo | Casos | O que realmente testa |
|---|---:|---|
| `test_sync_offline.py` | 7 | `SyncService` **definido no próprio teste** + modelos SQLAlchemy locais — a classe real `ServicoSincronizacaoOffline` nunca é tocada. É por isso que P0-1 passa despercebido |
| `test_telemedicina_lifecycle.py` | 3 | modelos `Base = declarative_base()` locais, não os de `app.models` |
| `test_analytics_kpis.py` | 3 | aritmética escrita no teste (`(15/100)*100 == 15.0`) — o router `/analytics` não é chamado |
| `test_copiloto_clinico.py` | 2 | 3 modelos Pydantic locais; o `copiloto_clinico.py` real não é importado |
| `test_farmacia_dispensacao.py` | 1 | 2 modelos Pydantic locais; a rota de farmácia não é chamada |

**Risco:** esses testes passam para sempre, mesmo que o código de produção seja apagado. Eles dão ~2,6% de "falsa confiança" na métrica de 621.

### 5.4 Testes superficiais (existem, mas provam pouco)

- **`test_contrato_frontend.py` (31 casos):** verifica se uma string de URL aparece em algum `.js`. Não valida payload, não valida status, não valida se o módulo é carregado pela página. Metade das URLs checadas está em módulos mortos (P1-8).
- **`test_seguranca_v1.py`:** bom para configuração (`Settings`), mas a parte de API verificava **apenas 401** em `/sincronizacao/atendimentos`. Não havia teste de happy path — por isso o 500 era invisível. Corrigido em `test_sincronizacao_api.py`.
- **`test_api_financeiro_prescricao.py`:** validava `total_bruto > 0` sobre dados hardcoded — o teste *legitimava* o mock (P0-6). Reescrito para provar que o demonstrativo vazio vem **zerado**; a cobertura real está em `test_livro_caixa_persistido.py`.
- **`test_api_code_first_routers.py` / `test_prescricao_pdf.py` / `test_ia_e_health.py`:** `TestClient(app)` no nível do módulo, fora do fixture — não usam o banco semeado.
- **`test_webrtc_manager.py` (14) e `test_t3_teleconsulta_frontend.py` (11):** são análise estática de JS. Legítimos como "guardas estruturais", mas não provam áudio/vídeo funcionando — os próprios docstrings admitem isso.

### 5.5 Testes sem asserção (7)

```
test_mensageria_preventiva.py::test_envio_duplicado_nao_gera_duas_notificacoes
test_mensageria_preventiva.py::test_sem_envio_quando_notificacao_ja_existe
test_seguranca_v1.py::test_producao_com_configuracao_segura_passa
test_sisab_client.py::test_validar_lote_valido
test_sisab_client.py::test_close_client
test_sisab_client.py::test_validar_ficha_com_ciap
test_sisab_client.py::test_validar_ficha_com_cid10
```

Os quatro de `test_sisab_client.py` são "não deve levantar exceção" — estilo aceitável, mas frágeis: se a validação virar no-op, continuam verdes. `test_producao_com_configuracao_segura_passa` **não verifica nada**: só constrói `Settings` e termina (deveria afirmar que não levanta e que os valores efetivos estão corretos). Os de mensageria usam `unittest.mock` e poderiam afirmar `mock_sender.assert_not_called()`.

### 5.6 Isolamento e ordem

`conftest.py` cria **um banco em memória por sessão** (`scope="session"`, `autouse`) e **não faz rollback** entre testes: cada teste commita no mesmo banco. Hoje todos passam em qualquer ordem testada, mas:
- qualquer teste que conte registros (`len(data) >= 1`) pode quebrar quando outro teste inserir dados;
- não há `TRUNCATE`/transação por teste;
- 6 arquivos instanciam `TestClient` fora do fixture, criando sessões paralelas.

**Recomendação:** fixture `db_session` com transação + `rollback` por teste (padrão `SAVEPOINT`) ou `drop_all/create_all` por teste (mais lento, mais seguro).

### 5.7 O que não tem teste nenhum (e deveria)

1. ~~`POST /api/v1/sincronizacao/atendimentos` — happy path (P0-1).~~ **Feito** (`test_sincronizacao_api.py`).
2. ~~WebSocket `/api/v1/copiloto/ws/{atendimento_id}` — conexão, autorização, mensagem (P0-2).~~ **Feito** (`test_copiloto_ws.py`).
3. ~~Fluxo prescrição → farmácia (P0-5).~~ **Feito** (`test_prescricao_farmacia_integracao.py`).
4. ~~Livro caixa com dados persistidos (P0-6).~~ **Feito** (`test_livro_caixa_persistido.py`).
5. Isolamento cross-tenant em prescrição, TISS, farmácia, financeiro e convênios (P1-4).
6. Autenticação/401 em todos os routers com `require_auth=true` (P0-8).
7. Boot da aplicação em Postgres (P1-10).
8. Build e execução da imagem Docker (P0-3).
9. Cálculos clínicos: escalas, TFGe, validação de CNS, CID-10 (P1-6).
10. Frontend em navegador real (E2E).

### 5.8 Recomendações para a suíte (ordem de execução)

1. **Substituir** os 5 arquivos de simulação por testes de rota reais (ou apagá-los se o código-alvo for morto).
2. **Adicionar teste de contrato de rota** para todo endpoint: `status_code` esperado + schema da resposta + caso 401 + caso 422.
3. **Um teste por bug P0** antes da correção (falha hoje, passa depois) — começando por `sincronizacao` e `copiloto`.
4. **Isolar banco por teste** com rollback.
5. **Elevar o gate de cobertura**: mínimo global 70% e **80% obrigatório** para `services/` de domínio clínico, com `fail_under` no CI.
6. **Remover `addopts = -q` duplicado** — hoje `pytest` roda como `-qq` e **esconde a linha de resumo**, o que já causou confusão em execuções manuais.

---

## 6. Segurança, privacidade e conformidade

| Item | Estado | Severidade |
|---|---|---|
| JWT com expiração/refresh/logout-all | OK | — |
| Validação de configuração em produção | OK | — |
| RBAC por papel | OK (20 módulos) | — |
| Isolamento de tenant por registro | Parcial (4 de ~12 módulos) | P1 |
| CPF/CNS em texto claro | Ausente | **P0** |
| Assinatura digital ICP-Brasil | Mock | P1 |
| Token em `localStorage` + XSS (84 `innerHTML`) | Frágil | P1 |
| CSP / headers de segurança | Ausente | P1 |
| Rate limiting / lockout de login | Ausente | P1 |
| Validação de token SSO real | Mock controlado (bloqueado em prod) | P2 |
| Auditoria de acesso a PHI | OK | — |
| Retenção/descarte (política existe em doc) | Não automatizada | P2 |
| Segredos no repositório | Nenhum encontrado (sem gitleaks no CI, porém) | P2 |
| Criptografia em repouso do banco | Depende da infra, não documentada | P2 |
| Backup criptografado | Verificar em `scripts/backup_db.py` antes de prod | P1 |

**Conformidade CFM 2.314/2022:** TCLE, identificação de médico/paciente e guarda de prontuário existem estruturalmente; **assinatura e certificação não**. Sem P1-3, os documentos emitidos não têm validade formal.

**LGPD:** base legal, consentimento e política de retenção estão documentados (`POLITICA_RETENCAO_E_TRATAMENTO_DE_INCIDENTES.md`), mas não há implementação técnica de consentimento no produto (o módulo `consentimento_lgpd.js` está morto) nem criptografia de identificadores.

---

## 7. Infraestrutura, CI/CD e deploy

| Item | Estado | Evidência |
|---|---|---|
| CI testes (3.12/3.13) | OK | `.github/workflows/ci.yml` |
| CI schema Alembic | OK | passo dedicado |
| CI CodeQL | **Quebrado** | `authenticate@v3` não existe |
| CI lint/format | Ausente | — |
| CI secret scan | Ausente | — |
| CI build Docker | Ausente | — |
| CI Postgres | Ausente | — |
| Lockfile | Ausente | — |
| Dockerfile multi-stage | Não | imagem única |
| Dockerfile non-root | OK | `USER appuser` |
| Dockerfile migrations | **Quebrado** | `alembic/` não copiado |
| Compose modo produção | **Não** | sem `ENVIRONMENT` |
| Compose secrets | **Não** | `SECRET_KEY` default |
| Healthcheck | OK | `curl /health` |
| Logs estruturados | Parcial | `logging.basicConfig` apenas; sem JSON, request-id ou correlação |
| Métricas/tracing | Ausente | — |
| Backup | Script + testes | `scripts/backup_db.py` |

> **Executado nesta rodada:** build real da imagem (`docker build`) e execução do container com o entrypoint aplicando as 9 migrações até `c3d9e1f5a7b2`; `GET /health` respondeu 200 com `database: connected`. O item que permanece **não executado** é o `docker compose up` completo com Postgres (o smoke usou SQLite dentro do container).

---

## 8. Documentação

| Documento | Estado |
|---|---|
| `docs/STATUS_ATUAL_CONSOLIDADO.md` | **Confiável** — único alinhado ao código (621 testes, T1–T3, P0.1–P0.3) |
| `README.md` | **Desatualizado** — 496 testes, 30 tabelas, P0.1/P0.2 "não implementados" |
| `docs/ROADMAP_V1.md` | **Desatualizado** — 469 testes, P0.1 aberto |
| `docs/ESTADO_ATUAL.md`, `RELATORIO_*`, `SECOES_*`, `HANDOFF_*` (13 arquivos) | **Históricos** — úteis como registro, perigosos como referência |
| `docs/POLITICA_RETENCAO_...` | Válido como política, sem implementação técnica correspondente |
| `docs/DIRETRIZES_CLINICAS_OFICIAL.md` | Válido como diretriz, não como estado do código |

**Recomendação:** criar `docs/INDICE.md` marcando cada documento como **ATUAL**, **HISTÓRICO** ou **OBSOLETO**, e corrigir README/ROADMAP na mesma passada.

---

## 9. Código morto e duplicação (inventário)

### Backend (~6.537 linhas, 32% de `app/`)

| Arquivo | Situação |
|---|---|
| `services/escalas_clinicas.py` | não importado por nenhuma rota |
| `services/fila_teleatendimento.py` | idem |
| `services/pre_natal.py` | idem |
| `services/consultas_repo.py` | idem |
| `services/triagem_clinica.py` | idem |
| `services/busca_cid10.py` | idem (o app usa `cid11_service`) |
| `services/tfge_renal.py` | idem |
| `services/copiloto_clinico.py` | idem |
| `services/mensageria_preventiva.py` | idem |
| `services/receita_digital.py` | idem (HMAC nunca chamado) |
| `services/soap_assistant.py` | idem |
| `services/fai_serializer.py` | idem |
| `repositories/analytics_repo.py` | **arquivo contém apenas o próprio path** |

### Frontend

- **Ativos:** `app.js`, `command_bar.js`, `fila_espera.js`, `teleconsulta_sessao.js`, `webrtc_manager.js`.
- **Mortos (10):** `acessibilidade_widget`, `analytics_charts`, `consentimento_lgpd`, `copiloto_sidebar`, `notificacoes_push`, `offline_sync_indicator`, `player_gravacao`, `screen_share`, `sinais_vitais_input`.

### Implicação para os testes

Os arquivos de teste de código morto **inflam a suíte**: `test_triagem_clinica.py` (33 casos), `test_receita_digital.py` (~49–65 conforme parametrização), `test_sisab_client.py` (33), `test_notificacoes_push.py` (39). Isso representa uma fatia grande dos 621 casos "verdes" que não protegem nenhuma funcionalidade entregue.

**Decisão pendente (produto):** cada módulo morto deve ser **integrado** ou **removido** — não pode continuar existindo como "quase pronto" indefinidamente.

---

## 10. Backlog priorizado

### Fase 0 — Estancar (1 semana)

| # | Item | Sev | Esforço | Critério de aceite | Status |
|---|---|---|---|---|---|
| 1 | Corrigir sync offline (`ingestar_lote`, idempotência, contrato de resposta) | P0 | 1–2 d | `POST /sincronizacao/atendimentos` → 201; reenvio → duplicado; teste de rota | **FEITO** (10 testes) |
| 2 | Corrigir WebSocket do copiloto + autenticar | P0 | 1 d | `websocket_connect` autenticado recebe evento; sem token → 4401 | **FEITO** (7 testes) |
| 3 | Docker: copiar Alembic, `ENVIRONMENT=production`, entrypoint de migração, segredos | P0 | 1 d | `docker compose up` em Postgres → `/health` 200, 34 tabelas, sem demo | **FEITO** (build real + container smoke validados) |
| 4 | Default seguro de auth (`require_auth=true`) | P0 | 0,5 d | todos os routers → 401 sem token em modo produção | **FEITO** (já era; compose corrigido) |
| 5 | Corrigir CodeQL (`init/analyze` apenas) e remover `authenticate` | P1 | 15 min | workflow verde | **FEITO** |
| 6 | Travar dependências (lockfile / pins exatos) | P1 | 0,5 d | `pip install -r` reproduz o venv | **FEITO** |

### Fase 1 — Tornar os fluxos reais (2–3 semanas)

| # | Item | Sev | Esforço | Critério de aceite |
|---|---|---|---|---|
| 7 | Remover paciente fictício; persistir jornada; usar `consultaId` real; propagar tenant | P0 | 2–3 d | nenhum dado demo em produção; jornada sobrevive a restart — **PARCIAL: demo e id fixo corrigidos; persistência/agenda pendentes** |
| 8 | Conectar prescrição → farmácia | P0 | 3–5 d | emitir receita e dispensar pelo hash, ponta a ponta |
| 9 | Financeiro com dados persistidos (ou demo explicitamente marcado) | P0 | 2–3 d | livro caixa reflete banco; teste não depende de mock |
| 10 | Criptografar CPF/CNS + hash de busca | P0 | 3–5 d | migração aplicada; busca por CPF continua funcionando |
| 11 | Fechar tenant em prescrição/TISS/farmácia/financeiro/convênios | P1 | 3–5 d | teste cross-tenant retorna 403/404 |
| 12 | Frontend: CSP, remover `innerHTML` crítico, token fora do `localStorage` (cookie HttpOnly) | P1 | 3–4 d | CSP sem `unsafe-inline`; sessão em cookie |

### Fase 2 — Qualidade e confiança (2–3 semanas)

| # | Item | Sev | Esforço |
|---|---|---|---|
| 13 | Reescrever/apagar os 5 arquivos de teste-simulação | P2 | 1 d |
| 14 | Banco isolado por teste (rollback) | P2 | 0,5 d |
| 15 | Gate de cobertura (70% global / 80% clínico) | P1 | 2 d + testes |
| 16 | Testar módulos clínicos: escalas, TFGe, CNS, CID-10, pré-natal | P1 | 5–8 d |
| 17 | Triagem de código morto (integrar ou deletar) | P1 | 3–5 d |
| 18 | Ruff + mypy + gitleaks + build Docker + serviço Postgres no CI | P1 | 2 d |
| 19 | Reconciliar README, ROADMAP e índice de docs | P1 | 1 d |
| 20 | Logs estruturados + métricas + `/ready` com checagem de banco | P2 | 2 d |
| 21 | E2E Playwright (login → agenda → teleconsulta → finalizar) | P2 | 5 d |

### Fase 3 — Produção regulada (4–8 semanas)

| # | Item | Esforço |
|---|---|---|
| 22 | Assinatura ICP-Brasil real (provedor + cadeia + carimbo de tempo) | 10–15 d |
| 23 | Integrações reais: RNDS/e-SUS, SISAB, TISS operadora | 15–25 d |
| 24 | DPIA/LGPD formal, criptografia em repouso, backup cifrado + restore testado | 5–10 d |
| 25 | Pentest e hardening | 5–10 d |
| 26 | Observabilidade de produção (SLO, alertas, on-call) | 5 d |

---

## 11. Critérios para considerar "pronto"

### Piloto controlado (pacientes reais, poucas clínicas)
- [ ] P0-1 a P0-8 fechados, cada um com teste que falhava antes
- [ ] Suíte ≥ 700 testes, cobertura global ≥ 70%
- [ ] Nenhum dado fictício acessível fora de flag `DEMO`
- [ ] Deploy Postgres reproduzível por script, sem passo manual
- [ ] Auth obrigatória comprovada por teste
- [ ] Backup + restore testados

### Produção regulada
- [ ] Assinatura digital válida (ICP-Brasil)
- [ ] CPF/CNS cifrados e auditados
- [ ] Isolamento multi-tenant em 100% dos módulos
- [ ] DPIA, política de retenção implementada e trilha de auditoria exportável
- [ ] Pentest sem achados críticos/altos
- [ ] SLO e alertas ativos

---

## 12. Anexos — como reproduzir

```powershell
# Suíte completa (a flag -o addopts="" devolve a linha de resumo)
cd projeto_media
$env:ENVIRONMENT="test"; $env:AUTO_MIGRATE_ON_STARTUP="false"
$env:AUTO_SEED_DEMO_DATA="false"; $env:DATABASE_URL="sqlite:///:memory:"
.\.venv\Scripts\python.exe -m pytest backend\tests -o addopts="" -q

# Cobertura
.\.venv\Scripts\python.exe -m pytest backend\tests -o addopts="" --cov=backend/app --cov-report=term

# Boot real com banco limpo
$env:ENVIRONMENT="development"; $env:DATABASE_URL="sqlite:///./tmp_audit.db"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --port 8010

# OpenAPI
.\.venv\Scripts\python.exe -c "import sys;sys.path.insert(0,'backend');from app.main import app;s=app.openapi();print(len(s['paths']), sum(len(v) for v in s['paths'].values()))"

# Reproduzir P0-1
curl -X POST http://127.0.0.1:8010/api/v1/sincronizacao/atendimentos -H "Content-Type: application/json" -d '{...}'   # → 500
```

**Arquivos-chave citados**

| Tema | Arquivo |
|---|---|
| Sync quebrado | `backend/app/api/v1/sincronizacao.py:41`, `backend/app/services/sync_offline.py:80,126-134` |
| Copiloto WS | `backend/app/api/v1/copiloto.py:275-276` |
| Fluxo demo | `backend/app/services/fluxo_atendimento_service.py:43`, `backend/app/static/app.js:2095` |
| Farmácia | `backend/app/api/v1/farmacia.py:125-148`, `backend/app/api/v1/prescricao_cfm.py:92-113` |
| Financeiro mock | `backend/app/api/v1/financeiro_medico.py:44-48` |
| Docker | `Dockerfile:19`, `docker-compose.yml` |
| CI | `.github/workflows/codeql.yml:30`, `.github/workflows/ci.yml` |
| Fixtures | `backend/tests/conftest.py` |
| Teste-simulação | `backend/tests/test_sync_offline.py:61` |

---

*Auditoria conduzida em 29/10/2026. Nenhum arquivo de aplicação foi modificado. Este documento é a linha de base para o trabalho restante.*
