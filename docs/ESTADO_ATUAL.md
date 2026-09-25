# 📋 Estado Atual do Projeto MedIA

> **Gerado em:** 25 de setembro de 2026  
> **Produzido por:** HierAgent — Framework de Orquestração Multi-Agente  
> **Modelos utilizados:** GLM 5.3 Flash (Cloud + OpenCode PC/NB), DeepSeek V4 Flash 0731, Qwen 3.6 35B A3B (local), Bonsai 27B (LAN)  
> **Duração da produção:** ~9+ horas contínuas (maratona de 8h + extensão)

---

## 1. Resumo Executivo

O Projeto MedIA foi desenvolvido com auxílio de um **cluster de 6 modelos de IA operando simultaneamente**:

- **GLM 5.3 Flash** (OpenRouter Cloud + OpenCode PC + OpenCode Notebook)
- **DeepSeek V4 Flash 0731** (OpenRouter Cloud)
- **Qwen 3.6 35B A3B** (PC Zorin OS, RTX 4060, custo zero)
- **Bonsai 27B** (Notebook Win 11, RTX 5060 via LAN, custo zero)

Foram produzidos **125 arquivos de código-fonte** (1.013 KB ≈ 1 MB) e **734 entregas markdown** de auditoria (~10 MB) em `docs/gerados_por_ia`.

---

## 2. Estrutura de Código Produzida

### Por diretório

| Diretório | Arquivos | Conteúdo |
|---|---|---|
| `backend/app/services/` | 18 | Regras de negócio e validações clínicas |
| `backend/tests/` | 21 | Testes automatizados (pytest) |
| `backend/app/models/` | 14 | Modelos SQLAlchemy 2.0 (tipagem Pydantic v2) |
| `backend/app/api/v1/` | 14 | Rotas FastAPI |
| `backend/app/schemas/` | 12 | Contratos de validação |
| `backend/app/static/js/` | 11 | Front-end JS ES Modules |
| `backend/app/static/` | 10 | Telas HTML5 + Tailwind CSS |
| `backend/app/repositories/` | 9 | Acesso a dados (SQLAlchemy 2.0) |
| `backend/app/core/` | 3 | Configuração, engine, database |
| `backend/app/seeds/` | 2 | Dados iniciais (UBS, profissionais, CID-10, CIAP-2) |
| Outros | 3 | `extrair_odt.py`, `brhealth_landing/`, `backend/` root |

### Por domínio funcional

**Backend SUS / APS (74 arquivos .py)**
- Telemedicina (WebRTC, signaling, salas, consentimento)
- CNS (validação dígito verificador)
- Triagem clínica (Manchester, MEWS, Glasgow, sinais vitais)
- Prontuário do cidadão (CRUD, histórico longitudinal, SOAP)
- Farmácia Popular (dispensação, receitas)
- Exportação SISAB/LEDI (FAI, Thrift, XML)
- Calendário vacinal, pré-natal, acompanhamento
- Repositórios SQLAlchemy 2.0 (outbox pattern, cache offline)

**Front-end Web (21 arquivos .js/.html)**
- Fila de espera virtual em tempo real
- Agenda do médico com drag-and-drop
- Consentimento LGPD com assinatura em canvas
- Teclado de sinais vitais com validação instantânea
- Compartilhamento de tela (WebRTC)
- Anamnese estruturada, player de gravação, acessibilidade WCAG

**Testes (21 arquivos .py)**
- API de telemedicina, farmácia, triagem, SISAB, sincronização offline, copiloto, análise de dados, notificações

---

## 3. Entregas dos Agentes (`docs/gerados_por_ia`)

A pasta `docs/gerados_por_ia/` contém **734 arquivos markdown** (~10 MB). Cada arquivo segue o padrão `{task_id}_c{onda}_entrega.md` e contém o **texto bruto retornado pela LLM** para aquela tarefa — incluindo os blocos de código com os caminhos dos arquivos (` ```python:backend/app/api/v1/telemedicina.py `).

**Para que servem:**
- **Rastro de auditoria** — histórico completo de todo prompt/resposta por agente e onda
- **Fallback de recuperação** — se a extração de código falhar, o código-fonte permanece no markdown
- **Review manual** — permite revisar o "pensamento" da LLM antes da geração dos arquivos fonte

> **Nota:** Os arquivos fonte efetivos (`.py`/`.html`/`.js`) também foram escritos diretamente na árvore do projeto (`backend/app/...`, `backend/app/static/...`). As entregas markdown são, portanto, uma duplicata de auditoria — podem ser removidas com segurança se o espaço em disco for necessário (`rm -rf docs/gerados_por_ia`).

---

## 4. Status Atual do Projeto

### ✅ Funcional
- Estrutura de diretórios bem organizada (`backend/app/` com subdomínios)
- `main.py` funcional com FastAPI, CORS, lifespan, roteadores incluídos
- Configuração tipada com Pydantic v2 (`core/config.py`)
- Models, schemas, repositórios e serviços com tipagem
- Interface web com HTML5 + Tailwind + ES Modules
- 103 arquivos `.py`, 10 `.html`, 12 `.js` com conteúdo real

### ⚠️ Precisa de Atenção
- **Dependências não instaladas:** `requirements.txt` não inclui `pyjwt`. A importação `import jwt` em `backend/app/api/v1/telemedicina_ws.py` causa `ModuleNotFoundError`.
- **Suíte de testes quebrada:** O `backend/tests/conftest.py` faz `import app.models` assumindo que `backend/` está no `sys.path`. Executar de fora de `backend/` causa falha. Além disso, houve contaminação com `Projeto_dados_tabnet_Sus` (referência em caminhos de conftest).
- **Entry-point:** O app roda com `uvicorn app.main:app` a partir de `backend/`. Não há `pyproject.toml` ou `setup.py` configurando o package `app` instalável.
- **README original desatualizado:** Apresentava a estrutura com `Projeto_dados_tabnet_Sus/` e badge falso "10 passed".

### ❌ Não Funcional
- `pip install -e .` / instalação completa não realizada
- Testes pytest não passam (dependências + conftest)
- Nenhuma execução end-to-end validada

---

## 5. Como Instalar e Rodar

```bash
# 1. Entre no backend
cd /home/jpversiani/Projeto_MedIA/backend

# 2. Ative o .venv existente
source /home/jpversiani/Projeto_MedIA/.venv/bin/activate

# 3. Instale dependências (incluindo pyjwt que falta no requirements.txt)
pip install -r requirements.txt
pip install "pyjwt[crypto]"

# 4. Rode a aplicação
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

> **Nota:** O `.venv` já existe em `/home/jpversiani/Projeto_MedIA/.venv` e contém as dependências base (fastapi, uvicorn, sqlalchemy, pydantic, pytest). Adicione `pyjwt` conforme acima.

---

## 6. Pipeline de Produção (HierAgent)

O projeto foi gerado pelo **HierAgent**, um framework de orquestração multi-agente localizado em `/home/jpversiani/projeto de multiplos agentes/`.

### Componentes do HierAgent
- **Pipeline hierárquico** (`src/hieragent/orchestrator/pipeline.py`): Nível Soberano → Esquadrão Tático → Matriz de Computação
- **Scheduler DAG** (`src/hieragent/orchestrator/scheduler.py`): 10 agentes concorrentes com retry e circuit breaker
- **OpenCode Runner** (`src/hieragent/opencode/runner.py`): Executa tarefas via CLI `opencode` com sandbox isolado
- **Live State** (`src/hieragent/live_state.py`): Telemetria em tempo real via JSON (`data/cluster_live_state.json`)
- **Web Dashboard** (`src/hieragent/web/server.py`): FastAPI + WebSocket em `http://localhost:8000`

### Scripts de Produção
- `scripts/continuous_marathon_8h.py` — maratona contínua de 8h, 4 modelos paralelos
- `scripts/glm_duo_marathon.py` — workers OpenCode GLM PC + Notebook, 8h contínuas
- `scripts/glm_coordinator.py` — coordenador de campo GLM 5.3 Flash
- `scripts/monitor_4_models.py` — monitor terminal em tempo real
- `scripts/continuous_sprint_15m.py` — sprint de 15 min contínuo

---

## 7. Métricas de Produção

| Métrica | Valor |
|---|---|
| Arquivos de código-fonte | 125 |
| Tamanho do código-fonte | 1.013 KB (≈ 1 MB) |
| Entregas markdown de auditoria | 734 |
| Tamanho das entregas | 10.293 KB (≈ 10 MB) |
| Modelos utilizados | 4 (GLM, DeepSeek, Qwen, Bonsai) |
| Tempo de produção contínua | ~9+ horas |
| Agentes concorrentes | 6 (maratona + duo) |
| Diretórios de código | 12 |

---

## 8. Próximos Passos

1. **Instalar dependências faltantes** (`pyjwt[crypto]` e possivelmente outras)
2. **Fixar `conftest.py`** para não referenciar projetos externos
3. **Rodar a suíte de testes** e garantir passagem
4. **Validar execução end-to-end** (`uvicorn app.main:app` + Swagger)
5. **Configurar entry-point** (`pyproject.toml` ou `setup.py`)
6. **Limpar `docs/gerados_por_ia/`** se o espaço em disco for necessário (opcional)
7. **Atualizar o roadmap** com base no estado real dos módulos
