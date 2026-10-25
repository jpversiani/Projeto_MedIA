# 📋 Status Atual Consolidado — MedIA Practice SaaS (v1)

> **Documento vivo e autoritário sobre o estado atual do repositório.**
> Branch `main` · T1, P0.1 (RBAC/tenant), P0.2 (auditoria), T2 (receitas persistidas) e
> P1 (sessão com refresh rotativo) **commitados**.
> Gerado pela sessão de evolução do workspace `App_Media`.

---

## 1. Resumo executivo

| Dimensão | Valor verificado | Fonte |
|---|---|---|
| Testes (`pytest -q`) | **563 passed, 0 failed** (~14 s) | Execução real na raiz (pós-P1) |
| Teste de contrato frontend | **28 passed** | `test_contrato_frontend.py` |
| Testes novos desta sessão | **41** (16 RBAC/tenant + 7 auditoria + 7 persistência + 11 sessão) | `test_rbac_tenant.py`, `test_auditoria_phi.py`, `test_t2_persistencia_documentos.py`, `test_p1_sessao_refresh.py` |
| Migrações Alembic | **4** (head `c8d42e1f7b33`) | `alembic current` |
| Tabelas SQLAlchemy (`Base.metadata.tables`) | **31** | Execução real |
| Operações OpenAPI registradas | **93** (87 paths) sob `/api/v1` (+ health/docs/static/root) | `app.openapi()` |
| Git | branch `main`, árvore limpa, 5 commits novos (`ad53e58` → `7a1ace6`) | `git status` |
| HEAD | `7a1ace6` — `feat(auth): sessao revogavel com refresh rotativo (P1)` | `git log -1` |

**Veredito:** o backend sobe, migra, semeia, autentica, **autoriza por papel**,
**isola dados por clínica** e **audita leitura de PHI**, com **543 testes verdes**.
Nesta sessão foram fechados o **T1 (Acolhimento)**, o **P0.1 (RBAC + tenant)** e o
**P0.2 (auditoria verificável)**. O que resta para uso clínico é **ciclo de vida
do dado (P0.3)**, **assinatura ICP-Brasil real (P0.4)**, **sessão/JWT (P1)** e os
fluxos **T2 (receitas persistidas)** e **T3 (teleconsulta real)**.

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
| P0.3 | **Ciclo de vida do dado** | **ABERTO** | Sem retenção/anonimização/backup/criptografia/ resposta a incidente (LGPD Art. 18/48, CFM 2.314 Art. 8º).
CPF e CNS trafegam e armazenam em claro. |
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
| Falta `SECURITY.md` | ⬜ **ABERTO** | — |

### 🟡 P2 — qualidade e manutenção (aberto)

- Frontend: **68% de código morto** (11/12 módulos JS não carregados); abas com dados
  **fictícios** (Pacientes, Honorários, TISS, Farmácia); 6 chamadas para endpoints inexistentes;
  XSS restante; acessibilidade ausente; service worker mentira; drafts em `localStorage`.
- Backend: FKs sem `ondelete`, `PRAGMA foreign_keys` off, índice ausente em `atendimentos_soap.cidadao_id`;
  sem tratamento global de exceção; WS de telemedicina **sem autenticação**; `start.sh` só Linux.
- **Documentação conflitante** — ver §4.

---

## 4. Frentes pendentes definidas no handoff (T1–T8)

Documento vivo: `docs/HANDOFF_TRABALHO_RESTANTE.md` (777 linhas, base `08d130a`).

| Tarefa | Escopo | Status |
|---|---|---|
| **T1** | Aba **Acolhimento** no Cockpit (`js/fila_espera.js` existe, nunca incluído) | ✅ **Concluída** (`ad53e58`) |
| **T2** | **Persistir receitas/CTE em banco** — antes em dicionário em memória (`_REPOSITORIO_DOCUMENTOS_CFM`) → QR Code dava 404 após restart | ✅ **Concluída** (`d57a982`) — tabela `documentos_clinicos`, migração `b7c31d9e4a02`, validação pública sem login |
| **T3** | **Teleconsulta real (WebRTC)** — `webrtc_manager.js` pronto e correto, mas **morto**; hub WS com roteamento/broadcast/join/quebra de estado | ⬜ Não iniciada |
| **T4** | Conformidade CFM/LGPD — persistir **TCLE**, auditar PHI, tenant, RBAC, lifecycle | ⬜ Não iniciada (partes P0) |
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
   seed, auth, autorização, sessão, fluxo presencial) está verde com **563 testes passando**.
   Concluídos: **T1 (aba Acolhimento)**, **P0.1 (RBAC + isolamento entre clínicas)**,
   **P0.2 (auditoria de PHI verificável)**, **T2 (receitas persistidas)** e o núcleo do
   **P1 (sessão revogável com refresh rotativo)**.
2. **O que ainda impede piloto com paciente real:** **P0.3 (ciclo de vida do dado)** —
   CPF/CNS em claro, sem retenção/anonimização/backup — e **P0.4 (assinatura ICP-Brasil
   real: hoje é um UUID, não uma assinatura jurídica)**. Nenhum dos dois é resolvível só
   com código: exigem certificado ICP-Brasil e definição de política de retenção.
3. **Sequência recomendada:** `P0.3` → `P0.4` → `T3` (teleconsulta WebRTC real) → `T6`
   (TISS/DMED) → distribuição (`lockfile`, Docker com migração, `SECURITY.md`).
4. **Ajustes pequenos herdados:** ligar `parar()` do painel de fila ao trocar de aba;
   estender o RBAC de tenant para receitas/TISS/farmácia; auditar as demais leituras de PHI;
   mover o access token de `localStorage` para cookie puro.

---

*Fim do status consolidado.*
