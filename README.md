# ⚡ MedIA Practice SaaS — Sistema Clínico para Atenção Primária

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/Pytest-570%20passing-success.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Plataforma de prontuário eletrônico, telemedicina, prescrição e faturamento
para consultórios e clínicas de atenção primária, com código em português e
terminologias brasileiras (CIAP-2, CID-10, CID-11, CNES, CNS).

> ### ⚠️ Status da v1 — leia antes de usar
>
> Esta v1 **sobe, migra, semeia e autentica** de ponta a ponta e está pronta
> para **testes funcionais em ambiente de desenvolvimento**.
>
> **Ainda não use com dados reais de pacientes.** A assinatura digital
> ICP-Brasil é um *mock* (P0.4); a auditoria de PHI não cobre todas as leituras
> (cadastro, receita e exportação TISS) e a checagem de tenant ainda falta em
> receitas, TISS e farmácia. O token SSO também é um mock, bloqueado fora de
> desenvolvimento.
>
> O estado atual por frente está em
> **[`docs/STATUS_ATUAL_CONSOLIDADO.md`](docs/STATUS_ATUAL_CONSOLIDADO.md)**.
> Para saber quais documentos são confiáveis, use
> **[`docs/INDICE.md`](docs/INDICE.md)**. O único bloqueio P0 aberto é
> **P0.4 — assinatura digital**; o restante são pendências P1/P2.

---

## O que existe de fato

### Prontuário e clínico
* Registro SOAP estruturado (subjetivo, objetivo, avaliação, plano).
* Busca e codificação cruzada entre **CIAP-2**, **CID-10** e **CID-11 (OMS)**.
* Fila de acolhimento, agenda médica e fluxo de atendimento.
* Calculadoras clínicas (Framingham, TFGe/CKD-EPI) e escalas.
* Copiloto de SOAP com IA, com verificação de interações Rename/Anvisa.
* Checagem cruzada de alergias e dispensação farmacêutica.

### Telemedicina
* Agendamento de teleconsultas, salas virtuais e fluxo de chamada.
* Consentimento livre e esclarecido (TCLE) com registro de IP e user-agent.
* Módulos de WebRTC para vídeo e compartilhamento de tela.

### Receita, documento e faturamento
* Prescrição e atestados médicos em PDF com **QR Code de verificação de
  integridade** (hash SHA-256 do documento — **não** é assinatura ICP-Brasil).
* Faturamento TISS com exportação de lotes XML e guias de consulta/SADT.
* Motor fiscal DMED e controle financeiro.
* Integração SISAB com retentativa de envio.

### Plataforma
* Autenticação JWT com MFA/TOTP (RFC 6238) e PBKDF2-HMAC-SHA256 para senhas.
* Multi-tenancy por unidade de saúde, com troca de contexto ativo.
* Trilha de auditoria com encadeamento SHA-256.
* Sincronização offline-first com fila de contingência.

---

## Como executar

### Requisitos
* Python 3.12 ou superior
* (Opcional) PostgreSQL 16 — o padrão de desenvolvimento é SQLite

### 1. Instalação

```bash
git clone https://github.com/jpversiani/Projeto_MedIA.git
cd Projeto_MedIA

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env               # Windows: copy .env.example .env
```

### 2. Subir

```bash
cd backend
uvicorn app.main:app --reload
```

Na primeira execução o aplicativo, sozinho:

1. aplica as migrações do Alembic criando as 34 tabelas;
2. popula o banco com 2 unidades de saúde, profissionais, um cidadão de
   exemplo e as terminologias;
3. passa a atender em `http://localhost:8000`.

| Endereço | O quê |
|---|---|
| http://localhost:8000/app | Cockpit Clínico |
| http://localhost:8000/ | Landing page |
| http://localhost:8000/docs | OpenAPI / Swagger (com botão **Authorize**) |

### 3. Entrar

Em desenvolvimento, o login de demonstração não exige senha:

```json
POST /api/v1/auth/login
{ "demo_role": "medico_titular" }
```

Papéis disponíveis: `medico_titular`, `medica_familia`, `secretaria`, `admin`.

> Em `staging`/`production` o login de demonstração e o mock de SSO são
> **recusados**, e a aplicação **não sobe** se a chave JWT não estiver definida
> ou se flags de demonstração estiverem ligadas. Ver
> [`backend/app/core/config.py`](backend/app/core/config.py).

---

## Testes

```bash
pytest -q          # a partir da raiz do repositório
```

**570 testes, todos passando.** A suíte roda em SQLite em memória e é
hermética: não toca no banco de desenvolvimento, e o seed e as migrações são
desligados durante os testes.

```bash
pytest -q backend/tests/test_seguranca_v1.py    # apenas as regressões de segurança
```

### Lint

O CI roda um gate mínimo de análise estática com [Ruff](https://docs.astral.sh/ruff/),
configurado em [`pyproject.toml`](pyproject.toml): erros de sintaxe/import
(`E4`, `E7`, `E9`) e pyflakes (`F`), que pegam nomes indefinidos, imports
duplicados e variáveis mortas. Regras puramente estilísticas ficam fora para
não gerar um diff histórico enorme.

```bash
ruff check backend
```

---

## Configuração

Tudo é lido de variáveis de ambiente e do arquivo `.env`.

| Variável | Padrão | Observação |
|---|---|---|
| `ENVIRONMENT` | `development` | `production` ativa validações obrigatórias |
| `JWT_SECRET_KEY` | — | **Obrigatória em produção** (`SECRET_KEY` também é aceita) |
| `FIELD_ENCRYPTION_KEY` | derivada do JWT | Chave AES-256-GCM de CPF/CNS; trocá-la invalida os dados já cifrados |
| `DATABASE_URL` | `sqlite:///backend/esus.db` | Ancorado em `backend/`, não no diretório atual |
| `CORS_ORIGINS` | `http://localhost:8000,http://127.0.0.1:8000` | Lista separada por vírgula |
| `PUBLIC_BASE_URL` | `http://localhost:8000` | Base dos links de teleconsulta enviados ao paciente |
| `REQUIRE_AUTH` | `true` fora de dev | Exige `Bearer` em todas as rotas clínicas |
| `AUTO_MIGRATE_ON_STARTUP` | `true` | Aplica `alembic upgrade head` no boot |
| `AUTO_SEED_DEMO_DATA` | `true` | **Sempre `false` em produção** |
| `DEMO_LOGIN_ENABLED` | `true` | **Sempre `false` em produção** |
| `SSO_ENABLED` | `true` | Mock; **recusado em produção** |
| `LOG_LEVEL` | `info` | |

---

## Arquitetura

```
Projeto_MedIA/
├── backend/
│   ├── alembic/            # Migrações (schema versionado e reprodutível)
│   │   └── versions/       # cbe75db02199_initial_schema.py — 30 tabelas
│   ├── app/
│   │   ├── api/v1/         # ~99 rotas: auth, prontuário, agenda, telemedicina,
│   │   │                   #   copiloto, prescrição, TISS, DMED, farmácia…
│   │   ├── core/           # config, database, bootstrap
│   │   ├── models/         # 34 tabelas SQLAlchemy 2.0
│   │   ├── schemas/        # Contratos Pydantic v2
│   │   ├── repositories/   # Camada de persistência
│   │   ├── seeds/          # Dados iniciais (idempotentes)
│   │   ├── services/       # Regras clínicas, CFM, ANS, SHA-256
│   │   ├── static/         # Cockpit, landing e módulos JS
│   │   └── main.py         # Entrada FastAPI
│   ├── tests/              # 62 arquivos, 570 testes
│   └── requirements.txt
├── docs/                   # ROADMAP_V1.md e demais documentos
├── scripts/
├── alembic.ini
├── pytest.ini
├── requirements.txt
└── docker-compose.yml
```

O schema é aplicado **exclusivamente pelo Alembic**. O antigo
`Base.metadata.create_all()` foi removido do startup: ele só executa
`CREATE TABLE IF NOT EXISTS`, nunca altera colunas existentes e não versiona o
schema — o que fazia uma coluna nova sumir silenciosamente em bancos já
instalados.

Para gerenciar o schema manualmente:

```bash
alembic upgrade head            # aplica
alembic downgrade -1            # reverte
alembic revision --autogenerate -m "descricao"
```

---

## Stack

* **Backend** — Python 3.12+, FastAPI, SQLAlchemy 2.0 (ORM tipado), Pydantic v2,
  Alembic, PyJWT, Uvicorn
* **Banco** — SQLite (desenvolvimento), PostgreSQL 16 (produção)
* **Frontend** — HTML5 + JavaScript ES2020 sem framework, Tailwind via CDN
* **Documentos** — ReportLab (PDF com QR Code)
* **Testes** — pytest + pytest-asyncio

---

## Licença

Distribuído sob a licença [MIT](LICENSE).
