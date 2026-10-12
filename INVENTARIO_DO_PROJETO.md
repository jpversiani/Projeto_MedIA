# 📦 Inventário do Projeto MedIA — Visão Geral, Scripts e Artefatos

> **Documento gerado por análise automatizada do workspace `App_Media`.**
> Este arquivo é um **inventário/mapeamento** do repositório `projeto_media`,
> apresentando tudo o que foi encontrado: descrição do produto, arquitetura,
> scripts, artefatos, configurações, testes e documentação.

---

## 1. Identificação do Projeto

| Campo | Valor |
|---|---|
| **Nome** | MedIA Health OS / MedIA Practice SaaS |
| **GitHub** | `jpversiani/Projeto_MedIA` |
| **Descrição** | Plataforma de **prontuário eletrônico (PEC)**, telemedicina, prescrição digital e faturamento para atenção primária à saúde (APS), inspirada no e-SUS. |
| **Linguagens** | Python 3.12+, JavaScript/HTML5 (frontend sem framework), Bash |
| **Licença** | MIT — © 2026 Dr. João Paulo Versiani Ladeia (Desenvolvedor do Software) |
| **Status v1** | Sobe, migra, semeia e autentica de ponta a ponta. **Não pronto para dados reais** (sem isolamento de tenant aplicado às queries, auditoria de prontuário e ciclo de vida do dado pendentes). |

> ⚠️ **Importante:** o README e o ROADMAP deixam explícito que **não deve ser
> usado com dados reais de pacientes**. LGPD, CFM 2.314/2022, SSO e assinatura
> ICP-Brasil ainda são, em grande parte, *mocks*. Prioridades P0.1–P0.4 pendentes.

---

## 2. Stack Tecnológica

- **Backend:** Python 3.12+, FastAPI 0.109, SQLAlchemy 2.0 (ORM tipado),
  Pydantic v2, Alembic, PyJWT, Uvicorn.
- **Banco:** SQLite (desenvolvimento, `backend/esus.db`), PostgreSQL 16
  (produção, via Docker).
- **Frontend:** HTML5 + JavaScript ES2020 sem framework, Tailwind via CDN.
- **Documentos:** ReportLab (PDFs com QR Code de verificação SHA-256).
- **Telemedicina:** WebRTC + servidor TURN (coturn) auto-hospedado.
- **Testes:** pytest + pytest-asyncio.
- **IA:** Copiloto clínico via Google Gemini (`GEMINI_API_KEY`).

---

## 3. Arquitetura (Estrutura de Diretórios)

```
projeto_media/
├── backend/                      # Aplicação FastAPI
│   ├── alembic/                  # Migrações de schema (versionado)
│   │   └── versions/cbe75db02199_initial_schema.py   # cria 30 tabelas
│   ├── app/
│   │   ├── api/v1/               # ~91 rotas (auth, prontuário, agenda, TISS…)
│   │   ├── core/                 # config, database, bootstrap
│   │   ├── models/               # 30 modelos SQLAlchemy 2.0
│   │   ├── schemas/              # Contratos Pydantic v2
│   │   ├── repositories/         # Camada de persistência
│   │   ├── seeds/                # Dados iniciais idempotentes
│   │   ├── services/             # Regras clínicas, CFM, ANS, auditoria
│   │   ├── static/               # Cockpit, landing e módulos JS
│   │   └── main.py               # Entrada FastAPI
│   ├── tests/                    # 50+ arquivos, 496 testes
│   └── requirements.txt
├── brhealth_landing/             # Landing page pública (index.html)
├── docs/                         # ROADMAP_V1.md e demais relatórios
├── scripts/healthcheck.sh        # Health check standalone
├── alembic.ini
├── pytest.ini
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── start.sh
├── extrair_odt.py
├── dados-sistema-E-sus.md        # Guia conceitual "Como construir um e-SUS"
└── CHANGELOG.md                  # Histórico de ondas de desenvolvimento
```

---

## 4. Scripts e Arquivos Executáveis

### 4.1 `start.sh` — Inicializador portável
- `BASE_DIR` dinâmico (sem caminhos legados).
- `HOST`/`PORT` parametrizáveis (`PORT=8010`, `HOST=127.0.0.1`, `RELOAD=0`).
- **Idempotente:** se já há uvicorn saudável na porta, valida e sai;
  `FORCE_RESTART=1` mata e sobe de novo.
- Health check pós-start em `/docs` com timeout ajustável.
- Ativa `.venv` da raiz e tem `trap` de limpeza em Ctrl+C/falha.

### 4.2 `scripts/healthcheck.sh` — Verificação de saúde standalone
- Checa: (1) `/docs` responde 200; (2) porta em `LISTEN`; (3) handshake
  WebSocket de telemedicina (`/api/v1/ws/telemedicina/sala/healthcheck`).
- `Uso: ./scripts/healthcheck.sh [PORT]` — exit 0 = saudável, 1 = degradado.

### 4.3 `extrair_odt.py` — Conversor ODT → Markdown
- Extrai um arquivo ODT (texto, títulos, listas, tabelas) para Markdown.
- `Uso: python extrair_odt.py dados-sistema-E-sus.odt dados-sistema-E-sus.md`
  (foi o gerador de `dados-sistema-E-sus.md`).

### 4.4 `Dockerfile` + `docker-compose.yml` — Infraestrutura
- **Imagem:** `python:3.12-slim`, usuário não-root `appuser`, healthcheck em `/health`.
- **docker-compose:** serviços `media-api` (FastAPI) e `db` (PostgreSQL 16),
  com o perfil opcional `turn` (coturn 4.6 para TURN/STUN em NAT assimétrico).
- Variáveis de ambiente para `DATABASE_URL`, `SECRET_KEY`/`JWT_SECRET_KEY`,
  `GEMINI_API_KEY`, `TURN_SECRET`, credenciais OAuth.

---

## 5. Backend — Pontos Principais

### 5.1 Entrada (`backend/app/main.py`)
- Aplica **Alembic** no startup (substituiu o antigo `create_all`,
  que não versionava nem alterava colunas).
- `settings.validar_ambiente()`: **recusa subir em produção** com chave JWT
  padrão ou flags de demo ligadas.
- Reinjeção automática de `Authorization: Bearer` e `securitySchemes` no
  OpenAPI (botão Authorize no Swagger).
- Monta `/static`, `/`, `/app` e `/cockpit`.
- Corrige encoding UTF-8 no console Windows (evita crash do boot por `cp1252`).

### 5.2 Configuração (`backend/app/core/config.py`)
- Fonte única, via `pydantic-settings`; lê `.env` da raiz e/ou de `backend/`.
- Aceita `JWT_SECRET_KEY` **ou** `SECRET_KEY` legada.
- `DATABASE_URL` padrão ancorado em `backend/esus.db`.
- Validação de ambiente: produção exige chave JWT; flags de demo recusadas.

### 5.3 Bootstrap (`backend/app/core/bootstrap.py`)
- `run_migrations()`: aplica `alembic upgrade head`.
- `bootstrap_demo_data()`: popula banco vazio de forma idempotente
  (2 unidades de saúde, profissionais, cidadão de exemplo e terminologias);
  **ignorado em produção** por questão de LGPD.

### 5.4 Rotas (`backend/app/api/v1/router.py`)
- Conjunto de routers clínicos **protegido por autenticação JWT** no nível do
  router (antes ~88 rotas eram abertas).
- Inclui: cidadãos, fila, atendimentos, terminologias, estabelecimentos,
  telemedicina, agenda, prescrição, financeiro, prontuário, copiloto, farmácia,
  convênios, TISS, DMED, clínica, fluxo de atendimento, analytics,
  sincronização offline.

> **Telemetria/analytics** (`api/v1/analytics.py`): `GET /analytics/heatmap`
> devolve uma matriz 7×24 de densidade de acolhimentos (dia da semana × hora)
> e `GET /analytics/kpis` devolve taxa de no-show, tempo médio de espera,
> taxa de resolutividade e totais de acolhimentos/atendimentos.

### 5.5 Banco (`backend/app/core/database.py`)
- Engine SQLAlchemy 2.0, `Base` tipada, `SessionLocal` e dependência `get_db`.

---

## 6. Modelos de Dados (SQLAlchemy 2.0)

Registrados em `backend/app/models/__init__.py`:
- `Cidadao`, `Estabelecimento`/`Equipe`, `Profissional`, `FilaAcolhimento`
- `AtendimentoSOAP` (alias `Atendimento`), `AtendimentoProblema`
- `AtendimentoOffline`/`StatusSincronizacao`/`SyncState` (offline-first)
- `ProntuarioProblema`, `CIAP2`/`CID10`/`CID11` (terminologias)
- `SalaVirtual`/`Teleconsulta`/`DocumentoEmitido` (telemedicina)
- `Receita`/`ReceitaItem`/`Dispensacao`/`DispensacaoItem` (farmácia)
- `CopilotoAuditoria`, `MensagemPreventiva`/`AlertaBuscaAtiva`
- `Operadora`/`Plano`/`GuiaTISS`/`LancamentoFinanceiro` (convênios)
- `Usuario`/`VinculoClinica`/`PapelUsuarioEnum`/`AuditTrail` (multi-tenancy + auditoria)

> A migração inicial cria **30 tabelas** com encadeamento de auditoria
> `hash = SHA256(hash_anterior + timestamp + dados)`.

---

## 7. Serviços de Regra de Negócio (`backend/app/services/`)

Principais (por nome e domínio):
- **Clínicas/APS:** `pre_natal.py`, `triagem_clinica.py` (Manchester/MEWS/Glasgow),
  `busca_cid10.py`, `cid11_service.py`, `calculadoras_clinicas.py`
  (Framingham, TFGe/CKD-EPI), `escalas_clinicas.py`, `tfge_renal.py`,
  `templates_especialidades.py`, `soap_assistant.py`.
- **Prescrição/Receita:** `prescricao_digital_cfm.py`, `receita_digital.py`,
  `pdf_generator_cfm.py`, `interacoes_medicamentosas.py`, `validacao_cns.py`.
- **Telemedicina:** `cfm_telemedicina.py`, `fila_teleatendimento.py`.
- **Copiloto IA:** `copiloto_clinico.py`, `copiloto_ia_generativa.py`,
  `copiloto_sugestoes.py`. O contrato (módulo C22) expõe alertas, sugestões,
  aceite de SOAP com auditoria e um **hub WebSocket** por atendimento
  (`/api/v1/copiloto/ws/{id}`). Regra de conformidade CFM 2.314/2022/LGPD:
  a IA **só sugere** — o aceite exige revisão do médico, gera registro de
  auditoria e **nunca sobrescreve** campos SOAP já preenchidos.
- **Validação sanitária:** `validacao_cns.py` implementa o algoritmo oficial
  DATASUS do CNS (15 dígitos, prefixo 1/2/7/8/9, pesos 15→1, soma múltipla de
  11), com formatação canônica e tipo Pydantic `CNS`.
- **Messageria preventiva:** `repositories/campanhas_repo.py` modela
  `Campanha` (rascunho/ativa/pausada/concluida) e `Disparo`
  (pendente/enviado/falha/lido) — base para campanhas de saúde pública e
  busca ativa de pacientes (ex.: HIV, tuberculose).
- **Faturamento:** `tiss_generator.py`, `dmed.py`/`dmed_generator.py`,
  `livro_caixa.py`, `pix_cobranca.py`, `fai_exporter.py`/`fai_serializer.py`.
- **Integrações:** `sisab_client.py` (envio SISAB com retentativa),
  `sync_offline.py`, `mensageria_preventiva.py`, `vidaas_signature_service.py`.
- **Segurança/Auditoria:** `audit_service.py`, `auth_service.py`, `validadores.py`.

---

## 8. Frontend / Artefatos Web (`backend/app/static/`)

- **Telas HTML:** `index.html` (Cockpit Clínico, ~104 KB), `landing.html`,
  `agenda_medico.html`, `anamnese_form.html`, `copiloto_card.html`,
  `painel_convenios.html`, `telemedicina_paciente.html`, `manual_operacional.html`.
- **CSS:** `css/theme.css`, `css/landing.css`.
- **JS (ES Modules):** `app.js`, `js/copiloto_sidebar.js`,
  `js/webrtc_manager.js`, `js/screen_share.js`, `js/player_gravacao.js`,
  `js/consentimento_lgpd.js` (assinatura em canvas), `js/fila_espera.js`,
  `js/sinais_vitais_input.js`, `js/analytics_charts.js`,
  `js/notificacoes_push.js`, `js/acessibilidade_widget.js` (WCAG),
  `js/offline_sync_indicator.js`, `js/command_bar.js`.
- **Service Worker:** `sw.js` (suporte offline-first).
- **Landing pública separada:** `brhealth_landing/index.html` — "BRHealth —
  Telemedicina Inteligente" (página de marketing com copiloto de IA,
  WebRTC HD + E2E, prescrição digital, etc.).

---

## 9. Terminologias Brasileiras (Seed)

O seed (`backend/app/seeds/init_data.py`) popula:
- Unidade ESF "Cidade Cristo Rei" — Montes Claros/MG (CNES 3180115, IBGE 3143302).
- Equipe eSF (INE 0001452361), profissionais (médica + enfermeiro).
- Cidadão exemplo "Sebastião Ferreira Santos".
- **CIAP-2** (ex.: A03, K86, K87, R96, T90, P76…) e **CID-10** (ex.: I10, E11,
  J06, F32, M54, N39.0…).
- Outros seeds: `seed_multiclinica_auth.py` (2 clínicas, multi-tenancy/SSO) e
  `seed_300_pacientes_norte_mg.py` (dados sintéticos de pacientes).

---

## 10. Testes (`backend/tests/`, 496 testes verdes)

Cobrem: autenticação e segurança (`test_seguranca_v1.py`, 22 testes),
telemedicina (WS, lifecycle, WebRTC), TISS/DMED/convenios, prescrição/receita
digital em PDF, farmácia/dispensação, prontuário e fluxos de consulta
(SOAP, teleconsulta, receita, interações), SISAB (async), sync offline,
templates de especialidades, triagem clínica, calculadoras, notificações push,
PIX, livro caixa, mensageria preventiva, contrato frontend (bounds de API).

- **Config:** `pytest.ini` com `pythonpath=backend`, `asyncio_mode=strict` e
  exclusão de `media_env_*` (pastas residuais vazias).

---

## 11. CI/CD (`.github/workflows/`)

- **`ci.yml`:** testa Python 3.12 e 3.13, roda `pytest -q --cov`, verifica
  que a migração inicial constrói o schema completo (tabelas obrigatórias) e
  que `app.main` importa.
- **`codeql.yml`:** análise de segurança CodeQL (Python, `security-extended`),
  disparada em push/PR e semanalmente (cron).

---

## 12. Documentação em `docs/`

- `ROADMAP_V1.md` — o que a v1 é, correções aplicadas (8 bugs de bloqueio,
  10 itens de segurança) e prioridades P0.1–P0.4.
- `ESTADO_ATUAL.md` — **relatório histórico marcado como não-confiável**
  (afirmações desmentidas; use ROADMAP/README como referência técnica).
- `STATUS_ATUAL_E_RECURSOS_IMPLEMENTADOS.md`, `RELATORIO_ESTADO_ATUAL_E_PLANO.md`
- Relatórios de auditoria IA: `RELATORIO_APROVEITAMENTO_TAR_IA.md`,
  `RELATORIO_FRENTES_E_ATUACAO_AGENTES.md`, `RELATORIO_CODIGO_LOCAL_ERRADO.md`
- `HISTORICO_DESENVOLVIMENTO_MARATONA_MEDIA.md`,
  `MATRIZ_PERFIS_MODELOS_CLUSTER.md` (cluster multi-agente),
  `RESOLUCAO_E_DIRECIONAMENTO_MVP_PARETO.md`,
  `DIRETRIZES_CLINICAS_OFICIAL.md`, `SECOES_2_A_6_OFICIAL.md`
- Guias operacionais: `MANUAL_FLUXO_OPERACIONAL_MEDIA.md`
- `ARQUITETURA_ANALYTICS_ASCII.txt` (desenho original do módulo de analytics)
- `historico_auditoria_ia.tar.gz` (3,45 MB).

---

## 13. Dados e Artefatos Bancários

- `backend/esus.db` (SQLite, ~520 KB) — banco de desenvolvimento.
- `backend/v1_check.db`, `backend/tests/…/media_env_*` — bancos/artefatos de
  verificação e resíduos de testes.
- O `CHANGELOG.md` (~570 KB, 9.580 linhas) relata ondas de desenvolvimento
  multi-agente com versionamento SemVer e Conventional Commits.

---

## 14. Segurança (resumo das correções)

Conforme `docs/ROADMAP_V1.md`, esta evolução corrigiu:
1. Chave JWT pública no código + `.env` ignorado → produção **recusa subir**
   sem chave; aceita `SECRET_KEY`/`JWT_SECRET_KEY`.
2. **88 de 91 rotas sem autenticação** → autenticação obrigatória no router.
3. Backdoor de admin sem senha → bloqueado em produção.
4. SSO falso (sem validação de `id_token`) → recusado em produção.
5. CORS `*` com credenciais → origens explícitas.
6. XSS armazenado na agenda → `createElement`/`textContent`.
7. Frontend não enviava token → interceptor global `fetch`.
8. Trilha de auditoria vazando entre tenants → filtrada pela clínica ativa.
9. `.env` ignorado + `securitySchemes` ausente → resolvidos.
10. Módulos mortos/duplicados → removidos.

---

## 15. Artefatos do Workspace Fora do Repositório

- `.acl-recovery/acl-report-*.jsonl` — relatório de reparo de ACL de
  permissões (diagnóstico do sandbox sobre pastas `media_env_*`).
- `_lixo_permissoes/` — contém 4 pastas vazias `media_env_*` residuais,
  criadas por uma versão antiga de `test_seguranca_v1.py` via
  `tempfile.mkdtemp`, cujas permissões do Windows impediam a remoção
  (podem ser apagadas manualmente). **Não fazem parte do código.**

---

*Fim do inventário.*