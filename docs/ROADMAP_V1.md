# Roadmap da v1 — MedIA Practice SaaS

Documento honesto sobre o que a v1 **é**, o que **foi corrigido** e o que
**ainda bloqueia** o uso com dados reais de pacientes.

Data de referência: commit `51714d2` (GitHub `jpversiani/Projeto_MedIA`).

---

## 1. O que a v1 permite fazer hoje

Após esta evolução, o projeto **sobe, migra, semeia e autentica** de ponta a
ponta em uma instalação nova:

```bash
git clone https://github.com/jpversiani/Projeto_MedIA.git
cd Projeto_MedIA
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
cd backend && uvicorn app.main:app --reload
```

- `http://localhost:8000/app` — Cockpit
- `http://localhost:8000/` — Landing
- `http://localhost:8000/docs` — OpenAPI **com botão Authorize**

Na primeira execução o schema é criado pelo Alembic (30 tabelas) e o banco é
populado com 2 unidades de saúde, profissionais, um cidadão de exemplo e as
terminologias CIAP-2/CID-10/CID-11. O login de demonstração passa a devolver
uma **clínica ativa** e 2 vínculos (antes vinha `null`).

Testes: **469 passando, 0 falhando**, em banco em memória e sem tocar no banco de
desenvolvimento.

```bash
pytest -q    # a partir da raiz do repositório
```

---

## 2. Correções aplicadas nesta evolução

### 2.1 Bugs que impediam o projeto de funcionar

| # | Defeito | Causa raiz | Efeito |
|---|---|---|---|
| 1 | 8 testes falhavam | `pytest.ini` sem `asyncio_mode` | Os 7 testes assíncronos do cliente SISAB nunca rodavam; o teste de login falhava |
| 2 | `clinica_ativa` sempre `null` | Vínculos criados só na primeira vez que o usuário existia | Workspace Switcher inutilizável |
| 3 | **Instalação nova nascia inutilizável** | Seeds só eram usados nos testes | Zero clínicas, zero usuários: o login devolvia `clinica_ativa: null` |
| 4 | **Servidor morria no boot no Windows** | `print("✔ ...")` no seed → `UnicodeEncodeError` no console cp1252, dentro do lifespan | `uvicorn` encerrava imediatamente |
| 5 | Alembic inerte | `upgrade()` era `pass` — o schema vinha de `create_all` | `alembic upgrade head` não criava nada; colunas novas nunca chegavam ao banco |
| 6 | Dois bancos diferentes | `DATABASE_URL` relativo ao diretório de trabalho | Rodar da raiz vs. de `backend/` criava bases distintas |
| 7 | Suíte sujava o banco de desenvolvimento | `TestClient(app)` sem `dependency_overrides` | 18 teleconsultas órfãs no `esus.db`; testes dependiam de estado residual |
| 8 | Logout não encerrava a sessão | Duas funções `fazerLogout`; o *hoisting* fazia a segunda prevalecer | Redirecionava para `/` mas deixava o token no `localStorage` |

### 2.2 Segurança

| # | Vulnerabilidade | Estado |
|---|---|---|
| 1 | **Chave JWT pública no código** e `.env` nunca lido (`.env.example` diz `SECRET_KEY`, o código lia `JWT_SECRET_KEY`) | `settings.effective_secret_key` aceita ambos; **produção recusa subir** sem chave |
| 2 | **88 de 91 rotas sem autenticação** — `curl /api/v1/cidadaos/` listava pacientes; `POST /api/v1/prescricao/emitir` emitia receita | Autenticação aplicada no nível do router. **Obrigatória** em staging/produção |
| 3 | **Backdoor de admin sem senha** — `{"demo_role":"admin"}` devolvia JWT de administrador | Bloqueado em produção |
| 4 | **SSO falso** — o callback nunca validava o `id_token` e fixava a identidade | `SSO_ENABLED` desligado e **recusado em produção** até existir validação JWKS |
| 5 | **CORS `*` com credenciais** | Origens explícitas via `CORS_ORIGINS` |
| 6 | **XSS armazenado na agenda** — nome do paciente interpolado em `innerHTML`, com `onclick='...${JSON.stringify(c)}'` em atributo de aspas simples | Linha montada com `createElement`/`textContent` e `addEventListener` |
| 7 | **Frontend nunca enviava o token** — `apiFetch` existia mas não era chamada em nenhuma das 24 requisições | Interceptor no `fetch` global injeta `Authorization: Bearer` |
| 8 | Trilha de auditoria vazava entre tenants | Filtrada pela clínica ativa do token; só superusuário vê tudo |
| 9 | `.env` ignorado, `securitySchemes` vazio no OpenAPI | `pydantic-settings` + `BearerAuth` declarado |
| 10 | Módulos mortos e duplicados (`app/database.py`, `app/models.py`, `backend/config.py`) | Removidos — ver nota sobre segredos abaixo |

Cobertura: `backend/tests/test_seguranca_v1.py` (22 testes) fixa esses
comportamentos.

### Sobre segredos no histórico do Git

Verificação feita nos 1.617 commits: **nenhuma credencial real de terceiros foi
versionada.** O que existe são placeholders cujo próprio nome avisa que são
fictícios — logo, **não há nada a rotacionar**.

| Onde (no histórico) | Valor | Situação |
|---|---|---|
| `auth_service.py:21` (HEAD) | `JWT_SECRET_KEY` com fallback `media_secret_jwt_sovereign_clinical_2026_key` | **Único que estava vivo.** Assinava tokens de verdade. Hoje exige chave própria em produção |
| `docker-compose.yml` (HEAD) | `media_pass`, `media-super-secret-jwt-key-change-in-prod`, `media-turn-secret-trocar` | Defaults de compose; sem uso real |
| `.env.example` (HEAD) | `POSTGRES_PASSWORD=media_pass`, `TURN_SECRET=…trocar-em-producao` | Placeholder |
| `app/database.py:14` (removido) | `postgresql+asyncpg://user:password@localhost:5432/…` | Placeholder — literalmente `user`/`password` em `localhost` |
| `backend/config.py:14` (removido) | `SECRET_KEY = "media-secret-key-change-in-production"` | Placeholder; módulo morto, nunca importado |
| `vidaas_signature_service.py:20-21` (ainda presente) | `media_practice_client_id` / `media_practice_secret` | Placeholder; código morto sem chamada de rede |

O único risco real era a **chave JWT**: como o `docker-compose.yml` definia
`SECRET_KEY` e o código lia `JWT_SECRET_KEY`, o valor do compose era ignorado e
o fallback público ficava valendo em qualquer deploy — qualquer pessoa que
clonasse o repositório poderia forjar um token de administrador. Isso está
corrigido (produção não sobe sem `JWT_SECRET_KEY`). Reescrever o histórico não é
necessário; basta gerar uma chave nova no primeiro deploy real, o que a
configuração agora exige.

---

## 3. Bloqueios que permanecem

Nenhum destes foi resolvido nesta evolução. Estão ordenados por gravidade.

### 🔴 P0 — impede uso com dados reais

**P0.1 — Não há controle de acesso no frontend nem verificação de tenant no backend.**
A autenticação agora é exigida, mas **nenhuma query filtra por `clinica_id`**.
Um médico autenticado da Clínica A que consulta o CNS de um paciente da Clínica B
recebe o prontuário: o isolamento é apenas lógico e depende de cada consulta
SQL lembrar do filtro. Também não há RBAC: `PapelUsuarioEnum` vai para o token
mas nenhum endpoint lê o papel de volta — médico, recepção e gestor veem a
mesma coisa.

> **Ação:** aplicar o filtro de tenant em todos os repositórios e adicionar
> `require_role(...)` por perfil. É a maior frente restante.

**P0.2 — Trilha de auditoria não registra acesso a dado sensível.**
`AuditService.registrar_evento` é chamado em 4 lugares, todos de login. Não há
registro de abertura de prontuário, emissão de prescrição ou exportação TISS —
justamente o que a LGPD Art. 11 exige para demonstrar controle de acesso. O
digest SHA-256 também **não cobre** `detalhes_json`, `ip_address` e
`user_agent`, e o encadeamento sofre condição de corrida (sem `FOR UPDATE`),
podendo bifurcar sob concorrência.

> **Ação:** auditar todo caminho que toca PHI; incluir o payload completo no
> digest; serializar a escrita da corrente.

**P0.3 — Não existe ciclo de vida do dado.**
Ausentes: retenção/eliminação (CFM 2.314/2022 Art. 8º), anonimização,
backup/restauração testado, criptografia em repouso, resposta a incidente
(Art. 48) e atendimento ao titular (Art. 18). CPF e CNS trafegam e são
armazenados em claro.

> **Conclusão honesta: o sistema ainda não deve receber prontuário real.**

**P0.4 — Assinatura ICP-Brasil/PAdES é fictícia.**
`vidaas_signature_service.py:61-112` não faz nenhuma chamada de rede: o
"carimbo" é um UUID, a URL do validador (`validador.iti.gov.br/validar`) não
existe e o `certificado_titular` tem o nome de uma pessoa real fixo no código.
Emitir uma receita que *parece* assinada no padrão ICP-Brasil sem estar é
exposição regulatória.

> **Ação:** implementar a integração real com o VIDAAS **ou** remover toda
> menção a ICP-Brasil/PAdES do README, da documentação, do modelo
> `ReciboAssinaturaVidaas` e do QR Code do PDF.

### 🟠 P1 — necessário antes de um piloto

- **Token de 24 h sem refresh, sem revogação e sem `jti`.** Um bearer vazado
  vale um dia inteiro contra prontuário. Migrar para 15–30 min + refresh
  rotativo. O schema ainda anuncia `expires_in: 900`, mentindo para o cliente.
- **Token no `localStorage`** — vulnerável a XSS. Preferir cookie
  `HttpOnly; Secure; SameSite=Strict`.
- **Sem CI.** Não existe `.github/workflows`, linter, type checker nem cobertura
  mínima. O selo "100% green" é autodeclarado e nada o garante. Um workflow com
  `pytest` + `ruff` + `mypy` + CodeQL deve ser o próximo commit.
- **Dependências não fixadas.** Os dois `requirements.txt` discordam (raiz com
  `>=`, `backend/` com `==`), não há lockfile, e `psycopg2-binary` nem
  `pydantic-settings` estão na lista da raiz. Consolidar em um arquivo fixado.
- **Docker inconsistente.** O `Dockerfile` copia só `backend/app` — sem
  `alembic/` nem `alembic.ini`, a imagem **não consegue rodar migrações**. Não
  há `.dockerignore` (o build envia `.git` e `.venv`), e o compose traz senha de
  Postgres padrão fraca.

### 🟡 P2 — qualidade e manutenção

- **68% do frontend é código morto.** 10.588 de 15.536 linhas nunca são
  carregadas por nenhuma página: Copiloto, fila, consentimento LGPD,
  acessibilidade, sincronização offline, gráficos. Foram escritos, testados e
  documentados — e nunca chegam ao usuário. Ligar ou remover.
- **Quatro abas mostram dados fictícios como se fossem reais** — Pacientes,
  Honorários, Convênios/TISS e Farmácia usam arrays literais no `app.js`. Um
  paciente falso com nome e CPF indistinguível de um real é passivo clínico e
  jurídico. `salvarNovaGuiaTISS()` só faz `alert()`: nada é persistido.
- **Seis chamadas do frontend apontam para endpoints inexistentes** —
  `POST /api/v1/atendimentos/anamnese`, `GET /api/copiloto/alertas` (sem `/v1`),
  `/api/v1/copiloto/exames`, `POST /api/copiloto/soap`,
  `POST /api/v1/consentimento` e `GET /api/v1/notificacoes/pendientes`. O
  consentimento LGPD grava em uma rota que dá 404: **nenhum termo de consentimento
  é persistido**.
- **XSS em outros pontos.** 28 atribuições a `innerHTML` com dados da API
  restantes; o autocomplete CID-11 (`app.js:1200-1212`) escapa só `'` dentro de
  atributo com aspas duplas.
- **Sem acessibilidade no Cockpit.** `index.html` (1.652 linhas) não tem um
  único `role`, `aria-*` ou `tabindex`. 10 modais sem `role="dialog"`, sem foco
  preso e sem `Escape`. Impeditivo em Pregão Eletrônico/SUS.
- **Service worker mente.** `sw.js:43-52` devolve **HTTP 200** com
  `{"offline": true}` quando a rede cai; como todo guard é `if (res.ok)`, a
  aplicação exibe "vazio" em vez de "offline". (Ele sequer é registrado.)
- **Agenda não é persistida.** `agenda_medica.py:64` usa um dict em memória:
  perde tudo a cada reinício e diverge entre workers.
- **Modelo de dados.** 32 FKs sem `ondelete` e `PRAGMA foreign_keys` nunca
  ligado; `atendimentos_soap.cidadao_id` sem índice (confirmado por
  `EXPLAIN QUERY PLAN`: `SCAN` + B-TREE temporário); timestamps `DateTime` sem
  timezone alimentados com valores UTC aware.
- **`prescricao_cfm.py`** tem `medico_nome`/`medico_crm` como padrão — a API
  assina no nome de um médico real sem autenticação. E `itens: List[Dict[str,str]]`
  não tipado causa 500 (`KeyError`) com `{"itens":[{}]}` — defeito já
  documentado no docstring do próprio teste e nunca corrigido.
- **Sem tratamento global de exceção** — qualquer `IntegrityError` vira 500 com
  traceback; `convenios.py` expõe a mensagem da exceção na resposta HTTP.
- **WebSocket de telemedicina sem autenticação** e com o papel declarado pelo
  cliente (`telemedicina_ws.py:202`).
- **`start.sh` é só Linux** (`ss`, `grep -P`, venv `bin/activate`); no macOS e
  no Windows não funciona. Documentar o caminho nativo como principal.
- **Documentação conflitante.** `docs/ESTADO_ATUAL.md` afirma que os testes
  não passam e que `pyjwt` não está instalado — ambos falsos — e cita caminhos
  `/home/jpversiani/...` e scripts inexistentes. O CHANGELOG tem 570 KB de
  saída automática e quatro números de versão diferentes entre arquivos.

---

## 4. Ordem sugerida

**Semana 1 — fechar o P0.1**
1. Extrair a dependência de tenant e aplicá-la em todos os repositórios.
2. `require_role(...)` por perfil (Médico, Enfermagem, ACS, Gestor).
3. Trocar o token do `localStorage` por cookie `HttpOnly` + refresh rotativo.

**Semana 2 — P0.2 e P0.4**
4. Auditar todo acesso a PHI; corrigir o digest e a corrida da corrente.
5. Decidir o destino do ICP-Brasil: implementar o VIDAAS ou remover as alegações.

**Semana 3 — operacional**
6. CI (`pytest` + `ruff` + `mypy` + CodeQL) e lockfile de dependências.
7. Corrigir `Dockerfile` (incluir `alembic/`), `.dockerignore` e segredos do compose.
8. Backup/restauração, retenção e um `SECURITY.md` para reporte de vulnerabilidade.

**Depois — produto**
9. Ligar ou remover o frontend morto (Copiloto, fila, consentimento,
   acessibilidade, sincronização offline, gráficos) — 68% do código de UI.
10. Trocar as quatro abas de dados fictícios por chamadas reais.
11. Acessibilidade do Cockpit (`index.html` não tem `role`, `aria-*` nem
    `tabindex`; 10 modais sem `role="dialog"` nem foco preso).

### Ainda pendente do front-end (parcialmente corrigido nesta iteração)

- **`anamnese_form.html` não fecha contrato com a API.** O caminho foi
  corrigido para `POST /api/v1/atendimentos/`, mas esse endpoint exige
  `cidadao_id` e o formulário só coleta CNS/CPF. Falta resolver o paciente
  para a chave primária antes de mapear anamnese → SOAP. Hoje o envio é
  rejeitado com 422 e a interface explica o motivo ao usuário.
- **`GET /api/copiloto/exames` não tem contraparte no backend.** O painel agora
  mostra "ainda não disponível" em vez de disparar um fetch que sempre daria
  404. Ou implementa a rota, ou o recurso permanece fora do produto.
- **`GET /api/v1/notificacoes/pendientes`** (`js/notificacoes_push.js`) segue
  sem endpoint correspondente.
- **Service worker mente.** `sw.js:43-52` devolve **HTTP 200** com
  `{"offline": true}` quando a rede cai; como todo guard é `if (res.ok)`, a
  aplicação exibe "vazio" em vez de "offline". Ele sequer é registrado por
  nenhuma página. Deve responder 503 e ser registrado (ou removido).
- **XSS em outros pontos.** Restam 28 atribuições a `innerHTML` com dados da
  API; o autocomplete CID-11 (`app.js:1200-1212`) escapa só `'` dentro de
  atributo com aspas duplas.
- **Rascunho de anamnese em `localStorage`** guarda CNS, CPF, alergias e
  medicamentos sem expiração nem criptografia — PHI persistente em máquina
  compartilhada.

### Prevenção adicionada

`backend/tests/test_contrato_frontend.py` (24 testes) varre todo o HTML/JS
estático, remove comentários e confere cada URL de API contra a tabela de
rotas real do OpenAPI — é o que impede o retorno dos endpoints divergentes.
Há ainda um teste que reprova qualquer `.html` que na verdade seja saída de
`tree` ou código-fonte: dois desses estavam sendo servidos publicamente em
`/static/` e foram removidos.

---

## 5. Nota sobre o texto do projeto

O `README.md` e a **landing page** foram reescritos para descrever o que o
código faz. Alegações que não se sustentam foram removidas ou rebaixadas:

| Alegação antiga | O que o código faz | Como ficou na landing |
|---|---|---|
| "estrita conformidade CFM 2.314/2022" | Sem retenção, auditoria de acesso ou ciclo de vida do dado | Aviso no hero + seção Status |
| "assinatura ICP-Brasil" | Sem chamada de rede; o carimbo é um UUID | "hash de integridade interno, **não** assinatura ICP-Brasil" |
| "criptografia ponta a ponta / E2E" | WebRTC com DTLS-SRTP; relay TURN encerra o transporte | Removido |
| "LGPD" em marquee de integrações | Não implementada | Removido |
| "70% menos tempo em prontuário", "0ms de latência" | Nenhuma medição feita | Removido; no lugar, números verificáveis do próprio repositório (85 rotas, 30 tabelas, 496 testes) |
| Depoimento de "Dra. Letícia Mendes, cofundadora" | Pessoa fictícia, sem dado real | Removido; no lugar, uma seção **Status** que lista o que funciona e o que não |

Números hoje publicados na landing (85 rotas, 30 tabelas, 496 testes) são
verificáveis no próprio repositório e conferidos por teste. A seção Status é
mantida junto do código: quando uma pendência for fechada, a landing e este
documento devem mudar juntos.
