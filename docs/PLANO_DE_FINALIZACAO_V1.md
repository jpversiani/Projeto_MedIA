# 🏁 Plano de Finalização da v1 — MedIA Practice

> **Documento de execução.** Consolida a revisão de 13/11/2026 (branch
> `integracao/t4`, suíte executada: **715 passed / 0 failed em 17,7 s**) e
> define o caminho até um produto finalizado para o posicionamento real:
> **gestão de consultas para médicos — presenciais e telemedicina**.
>
> Diferente dos documentos históricos, cada afirmação abaixo foi verificada
> no código ou executada nesta revisão.
>
> **Decisões de produto tomadas em 13/11/2026 (registradas na §2.1):**
> escopo = consultório privado (cortar SUS); assinatura = **VIDAAS**;
> marca = **MedIA**; DMED = **corrigir agora**; lembretes = **WhatsApp
> Business API**; PIX = reconhecido como mock, entra na Fase 6.

---

## 1. Veredito da revisão

O projeto **não é um protótipo vazio**: backend sólido (FastAPI + SQLAlchemy 2.0
tipado, 9 migrações Alembic, 36 modelos, ~100 rotas), autenticação JWT com
refresh rotativo, RBAC, auditoria encadeada, CPF/CNS cifrados (AES-256-GCM),
teleconsulta WebRTC com sinalização autenticada, TCLE persistido e bloqueante,
retenção/backup com política escrita, Docker validado com build real e
**715 testes verdes**.

O que impede de chamar de "finalizado":

| # | Lacuna | Severidade | Evidência |
|---|---|---|---|
| 1 | **Aba Acolhimento quebrada em runtime** (regressão do merge T4) | 🔴 bug | `app.js:434` importa `/static/js/fila_espera.js`, **arquivo deletado** no merge `bbb1450`. A aba abre vazia; o erro só aparece no console. `test_aba_acolhimento.py` passa porque testa só o backend. |
| 2 | **Assinatura digital é mock** (P0.4) | 🔴 legal | `vidaas_signature_service.py` não faz chamada de rede; carimbo = UUID; nome de médica fixo (`:111`). O PDF imprime "DOCUMENTO MÉDICO ASSINADO ELETRONICAMENTE (CFM 2.314/2022)" (`pdf_generator_cfm.py:275`) sem assinatura jurídica. |
| 3 | **Paciente não entra na teleconsulta em produção** | 🔴 fluxo | Com auth ligada, `telemedicina_paciente.html:153` exige token de `localStorage` — paciente não tem conta. O link é `?sala=<codigo>` permanente, sem token de uso único nem TTL (`cfm_telemedicina.py:159`). |
| 4 | **CRM/UF/RQE não existem no cadastro** (T5) | 🔴 legal | `models/profissional.py` só tem `cns/cpf/nome/cbo`. O CRM exibido é hardcoded em `auth_service.py:293-300` (`"78421-MG"` etc.). CFM 2.314/2022 Art. 5º exige identificação real. |
| 5 | **TURN não chega à API no deploy** | 🟠 fluxo | `docker-compose.yml` não repassa `TURN_URL`/`TURN_USERNAME`/`TURN_CREDENTIAL` nem `PUBLIC_BASE_URL`. Sem TURN, chamada só conecta em rede local/NAT não simétrico — paciente no 4G atrás de NAT simétrico não conecta. |
| 6 | **Tenant incompleto em 5 módulos** | 🟠 segurança | Prescrição, TISS, farmácia, convênios e financeiro checam papel, mas não filtram registro a registro por clínica (auditoria P1-4). |
| 7 | **3 abas com dados fictícios** | 🟠 produto | Pacientes (`app.js:1815`), Convênios/TISS (`:2426`) e Farmácia (`:2590`) usam arrays literais — hoje com aviso de demo, mas não são o produto. |
| 8 | **TISS/DMED/PIX incorretos ou mock** (T6) | 🟠 fiscal | `tiss_generator.py:170` ainda grava `"SIMULATED_TISS_HASH"`; DMED usa pipes (`dmed_generator.py:63`) em vez do leiaute posicional da IN RFB 1.987/2020; `GET /dmed/exportar-exemplo` entrega dados fictícios. **PIX é mock de produto:** a rota `pix/gerar-cobranca` não persiste cobrança, não vincula à consulta, aceita qualquer chave Pix do body (não a do médico), não tem conciliação/webhook/PSP — e o frontend nunca a chama. O docstring promete "conciliação de pagamentos" que não existe. |
| 9 | **Landing com alegações falsas** | 🟠 legal | `brhealth_landing/index.html:493,508,527,539` promete "E2E", "ICP-Brasil", "gravação conforme a norma" e "RNDS" — nada existe. |
| 10 | **Frontend inseguro por padrão** | 🟠 segurança | Access token em `localStorage`, ~84 `innerHTML`, sem CSP, sem rate limit de login (auditoria P1-5/P1-9). |
| 11 | **9 módulos JS mortos (~270 KB) + SW não registrado** | 🟡 dívida | `acessibilidade_widget`, `analytics_charts`, `consentimento_lgpd`, `copiloto_sidebar`, `notificacoes_push`, `offline_sync_indicator`, `player_gravacao`, `screen_share`, `sinais_vitais_input` nunca são carregados; `sw.js` não é registrado por nenhuma página. |
| 12 | **Sem lembretes/confirmação de consulta** | 🟡 produto | "WhatsApp" é deep-link manual (`api.whatsapp.com/send`). Não há disparo automático, confirmação, nem API real — o maior redutor de no-show de um gestor de consultas não existe. |
| 13 | **Branch e árvore sujas** | 🟡 higiene | `integracao/t4` está ~150 commits à frente da `main` com 43 arquivos não commitados (gate Ruff + limpeza). Raiz do workspace tem 10 XMLs de JUnit antigos + `routes.txt`. |
| 14 | **Fallback fictício no analytics** | 🟡 honestidade | `app.js:2686`: `total_atendimentos || total_acolhimentos || 32` — exibe "32" quando o total real é zero. |

**O que já está pronto e não precisa de trabalho:** boot/migração/seed,
auth+refresh+RBAC, auditoria encadeada com verificação, cifra de CPF/CNS
(mestre + 11 tabelas de cópias), fluxo presencial completo (agenda → check-in
→ fila → SOAP → finalizar com honorário escriturado), teleconsulta WebRTC
(sinalização provada com 2 clientes reais), TCLE persistido com bloqueio 409,
prescrição persistida com QR validável + bridge farmácia, livro caixa real,
retenção/backup/política de incidente, Docker com migração no entrypoint,
CI (pytest 3.12/3.13 + schema + CodeQL + Ruff no WIP).

---

## 2. Escopo decidido — o que entra e o que não entra

O sistema nasceu inspirado no **e-SUS/APS pública** (SISAB, FAI, CIAP-2,
CNES/INE, equipes eSF, campanhas, busca ativa). O posicionamento declarado é
**gestão de consultas para médicos (consultório privado, presencial +
telemedicina)**. São produtos diferentes. **Decisão confirmada em 13/11/2026:
o alvo da v1 é o consultório privado**; o SUS sai do núcleo (pode virar módulo
futuro, não é prioridade).

### ✅ Deve entrar (núcleo da v1)

| Funcionalidade | Situação | Observação |
|---|---|---|
| Agenda unificada presencial + tele, com status/check-in/encaixe | ✅ existe | Conectar aba Pacientes ao cadastro real. |
| Prontuário eletrônico (SOAP, evoluções, alergias, problemas, histórico) | ✅ existe | É o coração do produto. |
| Telemedicina: sala WebRTC, TCLE, convite assinado com TTL, TURN | 🟡 quase | Faltam convite assinado p/ paciente e TURN no deploy (Fase 2). |
| Prescrição e atestado digitais com **assinatura ICP-Brasil real (VIDAAS)** | 🔴 mock | Obrigatório para telemedicina comercial (Lei 14.063/2020, CFM 2.299/2021 e 2.314/2022). Provedor decidido: **VIDAAS**. Fase 3. |
| Identificação do médico (CRM/UF/RQE) em todo documento | 🔴 ausente | T5 — Fase 3. |
| Cadastro de pacientes com busca e ficha | ✅ backend / 🔴 tela | Ligar a aba ao `GET /cidadaos/`. |
| Faturamento: TISS (convênios) + particular (**PIX real**, livro caixa, recibos) | 🟡 parcial | TISS precisa XSD/hash reais; **PIX hoje é mock** (não persiste, não concilia, não é chamado pela UI) — torna-se cobrança real na Fase 6. |
| DMED (declaração anual à Receita) | 🟡 leiaute errado | **Decidido: corrigir agora** (leiaute posicional IN RFB 1.987/2020). Fase 6. |
| **Lembretes e confirmação de consulta** (24–48 h antes) | 🔴 ausente | Maior impacto em no-show; hoje só deep-link manual. **Canal decidido: WhatsApp Business API.** Fase 7. |
| Portal do paciente: link da teleconsulta + documentos emitidos | 🟡 parcial | `telemedicina_paciente.html` existe; falta entrega de documentos pós-consulta. Fase 7. |
| Analytics (no-show, espera, resolutividade, heatmap) | ✅ existe | Remover fallback `|| 32`. |
| Multi-clínica (médico com vários consultórios) + RBAC | ✅ existe | Diferencial real; manter. |
| Copiloto de IA (sugestão de SOAP, interações) | ✅ existe | Manter como **beta opcional** — a regra CFM já está certa (IA só sugere, médico aceita, auditoria). Não é bloqueio. |
| Acessibilidade + LGPD (consentimento, retenção, direitos do titular) | 🟡 parcial | Requisito de mercado; Fase 5/8. |

### ❌ Não deve entrar na v1 (cortar, remover ou adiar)

| Funcionalidade | Por quê | Ação recomendada |
|---|---|---|
| **SISAB / FAI / e-SUS / RNDS** | Envio ao Ministério de Saúde é obrigação de UBS/APS pública, não de consultório privado. | Remover rotas/serviços (`fai_exporter`, `sisab_client`, `exportar-fai`) ou isolar atrás de flag `MODULO_SUS=false`. Remover "RNDS" da landing. |
| **Campanhas de saúde pública / busca ativa** (HIV, tuberculose) | Programa de APS; `mensageria_preventiva` já é código morto. | Remover (modelos `Campanha`/`Disparo` podem ficar se forem base dos lembretes da Fase 7 — reaproveitar a mecânica, não o propósito). |
| **Pré-natal, triagem Manchester/MEWS/Glasgow, escalas clínicas** | Protocolos de UBS/pronto-atendimento; todos já são código morto sem rota. | Remover serviços + testes (inflam a suíte sem proteger nada). |
| **Estoque/dispensação de farmácia** | Consultório não dispensa medicamento. A aba é fictícia. | Remover a aba/estoque. **Manter** a validação pública de receita por QR (a farmácia do paciente consulta — isso tem valor). |
| **CNES / INE / equipes eSF** | Identificadores do SUS. | Simplificar modelo para "clínica/consultório + profissional"; manter campos só se o módulo SUS existir. |
| **CIAP-2** | Terminologia de APS; útil para medicina de família, não essencial. | Manter como busca opcional (já existe, custo zero); prioridade é CID-10/11. |
| **Offline-first para UBS sem internet** | Consultório privado tem internet estável; sync já funciona pós-correção. | Manter como contingência silenciosa, sem investir mais; não é argumento de venda. |
| **Gravação de teleconsulta** | CFM não obriga gravar (obriga registrar em prontuário); gravar exige consentimento específico, armazenamento cifrado e retenção — custo alto. | **Adiado para v1.1+ (confirmado).** Remover `player_gravacao.js` morto e a alegação "gravação conforme a norma" da landing. |
| **SSO Google/Microsoft real** | Mock já bloqueado em produção; login próprio + MFA basta na v1. | Adiar; remover botões da UI de produção ou rotular "em breve". |
| **App mobile nativo** | Web responsivo + PWA cobre o paciente (link no navegador). | v2. |
| **Agendamento online pelo paciente (self-booking)** | Diferencial forte, mas superfície grande (disponibilidade, pagamento, cancelamento). | **v1.1 — logo após o piloto (confirmado).** |

### ✅ Decisões tomadas (13/11/2026)

| Tema | Decisão | Consequência no plano |
|---|---|---|
| **Escopo** | Consultório privado (presencial + telemedicina). Cortar SUS. | Fase 1 remove SISAB/FAI/campanhas/pré-natal/triagem/estoque; CIAP-2 fica como busca opcional. |
| **Assinatura ICP-Brasil** | Provedor **VIDAAS** (assinatura em nuvem). | Fase 3 integra a API real do VIDAAS; iniciar contrato/certificado já na Fase 0 (lead time externo). |
| **Marca** | **MedIA**. | `brhealth_landing/` é aposentada ou reescrita como MedIA; uma landing só, honesta. |
| **DMED** | **Corrigir agora** (declaração anual). | Fase 6 inclui leiaute posicional IN RFB 1.987/2020 gerado do livro caixa real. |
| **Lembretes** | **WhatsApp Business API** como primeiro canal. | Fase 7 usa Cloud API (Meta) ou BSP; exige verificação Meta + aprovação de templates — iniciar cadastro na Fase 0/1. |
| **PIX** | Reconhecido como **mock** (gerador de string sem persistência, conciliação ou uso pela UI). | Fase 6 torna o PIX cobrança real: persistida, vinculada à consulta, com a chave do médico e conciliação. |
| **Credenciais externas (VIDAAS + Meta/WhatsApp)** | **Adiadas** (decisão de 13/11/2026): negociação/certificado e verificação Meta levam semanas e não bloqueiam o resto. | Construir o código **agora** contra sandbox/abstração, com "modo honesto" como padrão. As credenciais reais só plugam depois. Piloto roda em modo honesto; lançamento comercial aguarda as credenciais. |

Pendências menores que não bloqueiam (decidir durante a execução): gravação de
teleconsulta e self-booking permanecem adiados para v1.1+ conforme §2; canal
fallback de lembrete (e-mail/SMS) caso a aprovação do WhatsApp atrase.

### 🔌 Como o adiamento funciona (desacoplar código de credencial)

A regra é separar **o que é código** (fazemos agora) **do que é credencial/aprovação
externa** (entra depois, sem retrabalho):

- **VIDAAS (Fase 3):** escrever o cliente HTTP real + o fluxo de assinatura +
  recibo persistido, testável contra o ambiente `HOMOLOGACAO`/mock. **Sem
  credencial configurada, o sistema opera em "modo honesto"**: o PDF diz
  "verificação de integridade (hash SHA-256)", nunca "assinado ICP-Brasil".
  Quando o certificado chegar, basta setar as envs `VIDAAS_*` — o código já está
  pronto e testado. O passo de honestidade (Fase 3.3) é o que destrava o piloto.
- **WhatsApp (Fase 7):** construir o motor de lembretes/confirmação (agendamento,
  opt-in LGPD, link assinado, baixa de status, registro de envio) atrás de uma
  **abstração de canal** (`EnviadorMensagem`). Adaptadores: `dev` (log/console),
  `email`/`sms` (fallback real) e `whatsapp` (Cloud API/BSP). O adaptador WhatsApp
  fica **inativo sem credencial**; o motor roda com o fallback. Quando a Meta
  aprovar, pluga o token e os templates — sem reescrever o motor.

**Consequência nos marcos:** o **piloto** deixa de depender das duas credenciais
(roda em modo honesto + fallback de canal). Só o **lançamento comercial**
(documento com validade jurídica plena + WhatsApp oficial) aguarda VIDAAS e Meta.

---

## 3. Plano por fases

Convenções: esforço em **dias úteis de 1 dev focado**; cada fase termina com
`pytest -q` verde + teste de regressão para cada bug corrigido; nunca inventar
dado clínico; validar em servidor real, não só `TestClient`.

### Fase 0 — Consolidar a linha de base (1–2 d)

**Objetivo:** árvore limpa, `main` atualizada, regressão do merge corrigida.

1. Commitar o WIP atual (gate Ruff + `pyproject.toml` + limpeza de
   `mensageria_preventiva` + `pytest.ini` sem `-qq` + README) em `integracao/t4`.
2. **Corrigir a aba Acolhimento** (bug #1): restaurar `fila_espera.js` do
   histórico (`git show bbb1450^:backend/app/static/js/fila_espera.js` — era a
   implementação do T1, não a "alternativa" que o merge supôs) **ou** reescrever
   o painel inline em `app.js`. Adicionar teste de contrato que falhe se um
   `import()` apontar para arquivo inexistente (varrer `static/` e conferir
   cada caminho importado — pega a classe inteira do bug, não só o caso).
3. Merge `integracao/t4` → `main`; push; apagar branches já mergeadas.
4. Higiene do workspace: mover `e*.xml`/`f*.xml`/`routes.txt` da raiz
   `App_Media` para arquivo morto ou apagar (são JUnit de 12/10 com 496 testes).
5. Remover o fallback `|| 32` do analytics (`app.js:2686`).

**Aceite:** `main` = HEAD da revisão; aba Acolhimento abre e mostra a fila em
servidor real; teste novo reprova import quebrado; 715+ testes verdes.

### Fase 1 — Escopo e honestidade (1–2 d)

**Objetivo:** o produto promete só o que entrega.

1. Aplicar a decisão de escopo da §2 (confirmado: consultório privado).
2. Remover/ocultar módulos SUS conforme decisão (SISAB, FAI, campanhas,
   pré-natal, triagem, escalas, estoque de farmácia) — **deletar código morto
   e seus testes** em vez de manter "quase pronto".
3. **Marca MedIA (decidido):** aposentar `brhealth_landing/` (ou reescrever
   como MedIA) e manter uma landing só — a servida em `/` — sem "E2E",
   "gravação conforme norma" ou "RNDS"; "ICP-Brasil" só volta quando a Fase 3
   entregar assinatura real.
4. Remover `GET /dmed/exportar-exemplo` (dado fictício) e o seed de paciente
   fictício remanescente fora de flag demo.
5. Atualizar `README`, `INDICE.md` e a landing servida com os números reais.
6. **Credenciais externas adiadas (13/11/2026):** VIDAAS e Meta/WhatsApp não
   bloqueiam esta fase nem o piloto. O código das Fases 3 e 7 é construído contra
   sandbox/abstração (modo honesto + canal fallback); a negociação/cadastro pode
   ser disparada em paralelo, quando conveniente, sem travar o desenvolvimento.

**Aceite:** nenhuma rota/tela entrega dado fictício fora de `DEMO`; nenhuma
alegação não implementada em página pública; suíte verde após remoções.

### Fase 2 — Telemedicina plena em produção (4–6 d) 🔴 caminho crítico

**Objetivo:** paciente real, no celular dele, em qualquer rede, entra na sala.

1. **Convite assinado para o paciente:** token JWT curto (ex.: 24 h, `jti`
   persistido, escopo `teleconsulta:<id>`, papel `paciente`) entregue no link
   (`?convite=<token>`); WS e página do paciente aceitam esse token sem conta
   prévia. **Reutilizável até expirar/revogar** (não uso único estrito): se a
   conexão do paciente cair, ele precisa conseguir voltar pelo mesmo link.
   Revogável ao finalizar/cancelar a consulta.
2. **Expiração do link:** popular `SalaVirtual.data_expiracao` na criação;
   recusar sala expirada no WS (já recusa encerrada); job/CLI de expurgo.
3. **TURN no deploy:** gerar credenciais efêmeras a partir de `TURN_SECRET`
   (coturn `use-auth-secret` já está no compose) e repassar
   `TURN_URL`/`TURN_USERNAME`/`TURN_CREDENTIAL` + `PUBLIC_BASE_URL` ao serviço
   `media-api`; documentar portas (3478 udp/tcp, 49152–65535 udp).
4. **E2E em navegador real** (Playwright, 2 contextos com câmera fake):
   médico cria teleconsulta → link → paciente entra sem conta → oferta/answer
   → `peer_left` ao sair. É a prova que o T3 nunca teve (mídia de ponta a ponta).
5. Teste de regressão: link sem convite válido → 401/403; convite expirado →
   403; sala de outra clínica → 404.

**Aceite:** chamada funciona com auth ligada, paciente sem conta, atrás de NAT
simétrico (TURN); E2E verde no CI; link morto após expiração/finalização.

### Fase 3 — Identificação e validade jurídica dos documentos (6–15 d) 🔴

**Objetivo:** receita/atestado emitidos têm o valor legal que o texto alega.

1. **T5 — CRM/UF/RQE:** colunas em `Profissional` + migração; `auth_service`
   lê do cadastro (remover os CRM hardcoded `:293-300`); seed demo com CRM
   fictício rotulado; PDF usa o CRM do profissional autenticado; bloquear
   emissão sem CRM cadastrado (422 com mensagem clara).
2. **P0.4 — assinatura real com VIDAAS (provedor decidido):** integrar a API
   de assinatura em nuvem ICP-Brasil do VIDAAS — o `vidaas_signature_service.py`
   vira cliente HTTP de verdade (`httpx`), com `VIDAAS_CLIENT_ID`/
   `VIDAAS_CLIENT_SECRET`/`VIDAAS_ENDPOINT` por env, tratamento de erro,
   timeout e recibo persistido vinculado ao documento. Fluxo: emitir PDF →
   solicitar assinatura → médico autoriza no app VIDAAS (push/biometria/PIN) →
   PDF assinado (PAdES) + carimbo do tempo → QR aponta para validação própria
   **e** do provedor. Ambiente `HOMOLOGACAO` para testes, `PRODUCAO` só com
   certificado real.
3. **Passo intermediário de honestidade (fazer de qualquer forma):** enquanto
   não houver assinatura real, o PDF **não** pode dizer "ASSINADO
   ELETRONICAMENTE (CFM 2.314/2022)" — trocar para "Documento com verificação
   de integridade (hash SHA-256) — assinatura digital ICP-Brasil pendente" e
   remover a alegação do docstring/README/landing.
4. Testes: emissão sem CRM → 422; recibo de assinatura persistido sobrevive a
   restart; QR validável publicamente; mock de provedor nunca ativo em produção.

**Aceite:** nenhum documento alega assinatura que não tem; com provedor
configurado, o PDF sai assinado e verificável; CRM do PDF = CRM do usuário logado.

### Fase 4 — Isolamento total + segurança de sessão (4–6 d)

1. Tenant registro a registro em **prescrição, TISS, farmácia, convênios e
   financeiro** (mesmo padrão `filtrar_tenant`/`exigir_mesmo_estabelecimento`
   dos 4 módulos já prontos); testes cross-tenant → 403/404 em cada rota.
2. Auditar as leituras de PHI restantes: cadastro de cidadão, atendimento
   avulso, emissão de receita, exportação TISS.
3. **CSP + headers** (sem `unsafe-inline` onde possível), sanitizar os
   `innerHTML` restantes (trocar por `createElement`/`textContent`),
   **rate limit + lockout no login**.
4. Access token: migrar para **cookie HttpOnly puro** (alvo decidido;
   `localStorage` é vulnerável a XSS). Exige ajustar o interceptor `fetch` e o
   WS que hoje lê `?token=` — o refresh já está em cookie HttpOnly, falta o
   access. CSRF mitigado com `SameSite=Strict` + token anti-CSRF nas mutações.
5. WS de telemedicina e copiloto: validar tenant da sala/atendimento (já
   autenticam; falta o vínculo registro a registro).

**Aceite:** teste transversal prova 401 sem token e 403/404 cross-tenant em
100% das rotas clínicas; CSP ativa; login com força bruta bloqueado.

### Fase 5 — Frontend real e acessível (6–10 d)

1. **Aba Pacientes** → `GET/POST/PUT /cidadaos/` com busca, ficha e histórico
   (backend pronto; remover `pacientesExemplo`).
2. **Aba Convênios** → guias reais (`GET /convenios/guias` + operadoras/planos);
   `salvarNovaGuiaTISS()` passa a persistir via `POST /convenios/guias/consulta`.
3. **Aba Farmácia** → remover estoque (fora de escopo); manter tela de
   **validação de receita** por QR/código (backend pronto).
4. **Triagem dos 9 módulos JS mortos:** ligar os que entram no escopo
   (`acessibilidade_widget`, `analytics_charts`, `consentimento_lgpd`,
   `copiloto_sidebar`, `sinais_vitais_input`) e **deletar** os que não entram
   (`player_gravacao`, `notificacoes_push` até a Fase 7, `offline_sync_indicator`
   se a contingência ficar silenciosa, `screen_share` se não for ligar — ou
   ligar, pois compartilhamento de tela em teleconsulta tem valor clínico).
5. `sw.js`: corrigir (responder 503 offline, não 200 com JSON) e registrar,
   **ou** remover junto com a promessa offline-first da v1.
6. Acessibilidade: `role="dialog"` + foco preso + Escape nos modais,
   `aria-*`/`tabindex` no Cockpit (o widget morto ajuda, mas não substitui).
7. `anamnese_form.html`: resolver paciente por CPF/CNS → `cidadao_id` antes do
   POST (hoje 422); remover rascunho com PHI de `localStorage` sem expiração.
8. Rascunhos de SOAP: autosave no servidor por atendimento, não em
   `localStorage` compartilhado.

**Aceite:** nenhuma aba mostra array literal; contrato frontend verde;
navegação por teclado funciona nos fluxos principais; zero módulo JS órfão.

### Fase 6 — Faturamento correto (TISS/DMED/PIX) (7–11 d)

1. **TISS:** uma única implementação de XML; `versaoPadrao` correto; hash
   SHA-256 real do lote (remover `"SIMULATED_TISS_HASH"` e `TISS-HASH-LOTE-`);
   validação contra **XSD oficial da ANS no CI**; unificar no caminho que
   persiste (`convenios_repo`), aposentando os endpoints `/tiss/*` que só
   devolvem XML na resposta.
2. **DMED (decidido: corrigir agora):** leiaute posicional de tamanho fixo
   conforme IN RFB 1.987/2020 (substituir pipes); gerar a partir dos
   lançamentos reais do livro caixa (receitas de consulta com paciente/CPF/
   modalidade); remover o exemplo fictício; validar contra o leiaute oficial
   e o programa gerador da Receita.
3. **PIX real (hoje é mock):** a cobrança deixa de ser string solta e vira
   registro persistido (`cobrancas_pix`), vinculado à consulta/paciente e ao
   tenant, usando **a chave Pix cadastrada do médico/clínica** (nunca uma chave
   arbitrária do body). Estados: `PENDENTE → PAGA → CANCELADA/EXPIRADA`.
   - **v1 (piloto):** BR Code estático com a chave do médico + **conciliação
     manual** (médico/secretaria marca "paga", com auditoria) — honesto e
     funcional sem contrato de PSP. O QR/copia-e-cola é gerado do registro, e
     a baixa escritura o livro caixa automaticamente.
   - **v1.1:** PSP com Pix dinâmico + webhook de confirmação automática
     (Efí/Gerencianet, Mercado Pago, Pagar.me, Inter — ⚖️ escolher quando
     houver volume que justifique). O desenho da tabela já prevê `txid` do PSP.
   - Remover a alegação "conciliação de pagamentos" do docstring enquanto for
     manual; ligar a cobrança à tela de honorários/finalização da consulta.
4. Testes: lote XML valida no XSD; hash recalculável; DMED com campos em
   posição correta; cobrança Pix persistida sobrevive a restart, vinculada ao
   tenant, baixa gera lançamento no livro caixa; nenhum nome/CPF de exemplo
   em produção.

**Aceite:** XML aceito por validador XSD da ANS; DMED conferido contra leiaute
oficial; guias persistidas e vinculadas ao tenant; cobrança Pix real (persistida,
com a chave do médico, conciliável) e não mais um gerador de string órfão.

### Fase 7 — Gestão de consultas de verdade: lembretes, confirmação, portal (6–10 d)

**Objetivo:** a funcionalidade que mais reduz no-show e que hoje não existe.

1. **Lembretes automáticos** 24–48 h antes via **WhatsApp Business API
   (canal decidido)** — Cloud API da Meta (direto) ou um BSP (Twilio,
   Z-API, Gupshup, 360dialog). Exige: número dedicado, verificação do negócio
   Meta e **templates aprovados** (lembrete de consulta, confirmação, link da
   teleconsulta) — iniciar cadastro na Fase 1 por causa do lead time. Opt-in
   do paciente (LGPD) e registro de envio/entrega/leitura. Reaproveitar a
   mecânica `Campanha`/`Disparo` se ela sobreviver à Fase 1. **Fallback:**
   e-mail/SMS se a aprovação do WhatsApp atrasar (não bloqueia o piloto).
2. **Confirmação/cancelamento pelo paciente** via link assinado (mesmo padrão
   de convite da Fase 2): confirma → status na agenda; cancela → libera horário
   + notifica a clínica; não responde → lembrete final.
3. **Pacote pós-consulta no portal do paciente:** documentos emitidos
   (receita/atestado com QR), orientações e próxima consulta — hoje o
   "envio por WhatsApp" é deep-link manual do médico.
4. **Pré-consulta:** enviar anamnese dirigida ao paciente antes da teleconsulta
   (o `anamnese_form.html` corrigido na Fase 5 vira o formulário do paciente).
5. No-show: marcar automaticamente quem não compareceu (alimenta o KPI que já
   existe) e oferecer lista de espera/encaixe.

**Aceite:** consulta agendada dispara lembrete sem intervenção manual;
paciente confirma por link e a agenda reflete; documentos chegam ao paciente
sem o médico abrir WhatsApp manualmente.

### Fase 8 — Qualidade de produção (5–8 d)

1. CI: serviço **Postgres** nos testes + **build Docker** + gitleaks +
   gate de cobertura (70% global / 80% serviços clínicos mantidos).
2. Suíte: substituir os 5 arquivos de teste-simulação por testes de rota
   (ou apagá-los junto com o código morto da Fase 1); isolamento por teste
   com rollback; remover testes sem asserção.
3. **E2E Playwright completo:** login → agenda → check-in → SOAP → receita →
   teleconsulta (2 contextos) → finalizar → documentos no portal.
4. Observabilidade: logs estruturados com request-id, `/ready` com checagem
   de banco, métricas básicas; handler global de exceção (nada de traceback
   em resposta HTTP).
5. Backup **cifrado** + teste de restore agendado; rotação de
   `FIELD_ENCRYPTION_KEY` documentada.
6. LGPD: endpoints de direitos do titular (Art. 18 — acesso/correção/exportação),
   DPIA formal, trilha exportável; pentest/hardening antes do piloto aberto.
7. `start.sh`: versão Windows/PowerShell ou documentar caminho nativo como
   principal (hoje só Linux).

**Aceite:** deploy reproduzível em Postgres por um comando; E2E verde no CI;
restore de backup provado; nenhum achado crítico/altos em pentest.

---

## 4. Sequência e marcos

```
Fase 0 ──► Fase 1 ──► Fase 2 ──► Fase 3 ──► Fase 4 ──► Fase 5 ──► PILOTO
 (base)   (escopo)   (tele real) (VIDAAS)  (segurança) (UI real)   │
                                                                 ▼
                                              Fase 6 (TISS/DMED/PIX) ──► Fase 7 (WhatsApp)
                                                                 ──► Fase 8 (produção) ──► v1 FINAL
```

- **Marco "piloto controlado"** (poucos médicos, pacientes reais): Fases 0–5
  fechadas ≈ **4–6 semanas**, **sem depender das credenciais externas** (adiadas).
  Roda em **modo honesto** (PDF sem alegação de assinatura) + canal de lembrete
  fallback (e-mail/dev). O passo de honestidade (Fase 3.3) é o que o destrava.
- **Marco "v1 finalizada / vendável"**: + Fases 6–8 ≈ **+3–5 semanas** de código,
  **mais o lead time externo** de VIDAAS (certificado) e Meta (WhatsApp) quando
  forem contratados/aprovados. O código já estará pronto para plugá-los.
- Esforço de código estimado: **40–63 dias úteis** (1 dev). Fase 6 cresceu (PIX
  real + DMED posicional). O lead time externo corre **em paralelo**, fora desse
  esforço, e não bloqueia o piloto.
- Fase 6 e 7 podem correr em paralelo à 8 se houver 2 devs.
- **Credenciais externas (VIDAAS + Meta/WhatsApp): adiadas por decisão de
  13/11/2026.** Disparar a negociação/cadastro quando conveniente; o código é
  construído contra sandbox/abstração e só recebe a credencial depois.

### Definition of done da v1

- [ ] Fluxo presencial e teleconsulta completos **em modo produção** (auth
      ligada, sem demo), provados por E2E em navegador real.
- [ ] Paciente entra na teleconsulta por convite assinado com TTL, sem conta,
      em rede móvel (TURN).
- [ ] Todo documento médico sai com CRM real do profissional e assinatura
      **VIDAAS/ICP-Brasil** verificável (ou sem alegação de assinatura).
- [ ] Zero dado fictício fora de flag `DEMO`; zero alegação falsa em página pública.
- [ ] Tenant 100% + auditoria de toda leitura de PHI + CSP + rate limit.
- [ ] TISS valida no XSD da ANS; DMED posicional correto; **PIX é cobrança real**
      (persistida, chave do médico, conciliável) — nada de mock financeiro.
- [ ] Lembretes e confirmação automáticos via **WhatsApp Business API** funcionando.
- [ ] Backup cifrado com restore testado; deploy Postgres reproduzível; CI
      com E2E, Postgres e Docker.

---

## 5. Riscos

| Risco | Mitigação |
|---|---|
| Lead time de contrato/certificado **VIDAAS** (semanas) — **adiado** | Não bloqueia o piloto: modo honesto (Fase 3.3) + cliente testado em homologação. A credencial de produção só pluga nas envs `VIDAAS_*` quando o certificado sair; lançamento comercial aguarda. |
| **WhatsApp Business API** exige verificação Meta + templates — **adiado** | Não bloqueia o piloto: motor de lembretes roda com canal fallback (e-mail/dev). Adaptador WhatsApp fica inativo sem credencial e pluga quando a Meta aprovar, sem reescrever o motor. |
| Escopo SUS "quase pronto" tenta voltar | Fase 1 deleta em vez de gaveta; teste de contrato impede rota órfã. |
| Regressões de merge (como a da Acolhimento) | Teste de contrato de imports (Fase 0.2) + E2E (Fase 8) pegam a classe do problema. |
| Hub de sinalização em memória (1 worker) | Documentar single-worker na v1; Redis pub/sub só quando houver escala (código já isolado em `SignalingHub`). |
| PIX manual sujeito a erro de baixa | Auditoria em toda baixa + idempotência; PSP com webhook na v1.1 elimina o passo manual quando houver volume. |
| Documentação voltar a divergir | `INDICE.md` como porteiro; status só no `STATUS_ATUAL_CONSOLIDADO.md`, atualizado a cada fase. |

---

*Plano gerado na revisão de 13/11/2026. Fonte executável de verdade:
`pytest -q` (715 passed). Este documento entra no `INDICE.md` como **ATUAL**
e substitui o `HANDOFF_TRABALHO_RESTANTE.md` como plano de execução.*