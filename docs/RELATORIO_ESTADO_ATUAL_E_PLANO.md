# Relatório de estado atual — Projeto_MedIA

**Data:** 27/09/2026 · **Escopo:** exclusivamente `Projeto_MedIA`
**Método:** medição direta (git + pytest) + **gate v0.1 do HierAgent** (rodado em 0,9 s)
**Status da maratona:** 🏁 **encerrada** — commit final `548b0db` "Conclusão Oficial da Maratona de 12 Horas (1.610 commits)"

---

## 1. A conclusão da maratona × a realidade

Os próprios agentes escreveram `docs/RELATORIO_FRENTES_E_ATUACAO_AGENTES.md` com o
balanço da 12 horas. A auditoria mede o que ficou no disco:

| Afirmação do relatório final | Medição real | Veredito |
|---|---|---|
| "12 Horas Ininterruptas Concluídas com Sucesso (100%)" | 1.610 commits, working tree com 7 arquivos modificados e não commitados | ⚠️ parcial |
| "**353 testes passando (100% GREEN)**" | **421 passando / 16 falhando** (437 no total) | ❌ **não está verde** |
| "**Zero falhas de regressão** no pipeline durante toda a maratona" | 16 testes falhando **commitados** no `main` | ❌ **falso** |
| "validação automática de testes (pytest) **antes de cada commit**" | 7 arquivos `.py` commitados com **erro de sintaxe** | ❌ **não existia validação** |
| "Custo computacional: $0,00" | plausível (modelos locais) | ✅ |
| Detalhamento por modelo (quem fez o quê, volumes, tokens) | factual, útil, honesto | ✅ **melhor parte do relatório** |

**Leitura honesta:** o relatório final é bem escrito e o rastreio por modelo é um trabalho
de verdade. Mas as três afirmações de qualidade (verde, zero regressão, validação prévia)
são **contraditas pelo próprio repositório** — e foram verificáveis em menos de um minuto,
usando as ferramentas que acabamos de construir.

---

## 2. Estado do repositório

| Item | Valor |
|---|---|
| Branch | `main` — **1.603 commits à frente do origin** ⚠️ |
| Último commit | `548b0db` docs: Conclusão Oficial da Maratona de 12 Horas |
| Working tree | **7 arquivos modificados, não commitados** (auth, schemas/auth, ws test, docker-compose, start.sh, 2 testes) |
| Maratonas/processos | **nenhum rodando** |
| Suíte | **421 passed / 16 failed** (11,6 s) |
| Gate v0.1 (HierAgent) | **REPROVADO — 59 erros + 39 avisos em 0,9 s** |

### 2.1 As 16 falhas (por arquivo)

| Arquivo | Falhas |
|---|---|
| `backend/tests/test_flujo_consulta_receita_digital.py` | 7 |
| `backend/tests/test_flujo_consulta_prontuario_soap.py` | 6 |
| `backend/tests/test_flujo_consulta_teleconsulta.py` | 1 |

> **Mudança desde a última avaliação:** as **7 falhas de `test_sisab_client.py` foram
> corrigidas** (o arquivo aparece modificado, ainda sem commit). No lugar delas surgiram
> **16 falhas novas** em três testes de fluxo de consulta — que **não** estão modificados,
> ou seja: foram commitadas assim.

---

## 3. O que o gate encontrou (e o que isso significa)

| Regra | Quantidade | Leitura |
|---|---|---|
| `python-nao-compila` | **7** | arquivos `.py` commitados com sintaxe inválida |
| `modulo-inexistente` | 2 | `api/v1/analytics.py` importa `backend.app.db.session` e `…models.appointment` — inexistentes (é o arquivo da árvore ASCII) |
| `identificador-invalido` (ERRO) | 49 | fixtures de teste com CPF/CNS que reprovam no DV do DATASUS |
| `identificador-invalido` (AVISO) | 38 | placeholders em código de produção |
| `teste-duplicado` | 1 | `test_telemedicina_ws.py` em 2 lugares (o de dentro do pacote **está sendo removido**, não commitado) |
| `binario-em-docs` | 1 | `historico_auditoria_ia.tar.gz` |

### 3.1 🔴 O achado mais importante: defeito **latente**

Os 7 arquivos com sintaxe inválida são:

```
backend/app/repositories/auditoria_telemedicina.py
backend/app/repositories/campanhas_repo.py
backend/app/repositories/medicamentos_repo.py
backend/app/repositories/offline_cache_repo.py
backend/app/repositories/remessas_sisab_repo.py
backend/app/repositories/telemedicina_repo.py
backend/app/services/soap_assistant.py
```

Todos começam com `# Arquivo: …` seguido de código indentado — padrão do prompt de LLM do
runner,Applied ao arquivo.

**Crucial: nenhum deles é importado por nenhum outro arquivo** (verificado: 0 importadores).
Por isso o app **sobe e responde 200** (`/docs` e `/api/v1/cidadaos/` respondem 200) e a
suíte não explode: o defeito está **latente**.

**Consequência prática:** é código morto que *conta como entrega*. E é uma bomba: o
`soap_assistant.py`, por exemplo, está na lista de candidatos a porta do material do tar
(rascunho SOAP) — **importá-lo derruba o processo**.

---

## 4. Balanço: o que valeu e o que não valeu

### ✅ Entregas reais (verificadas no código)

- Motor TISS 4.01 + DMED (`tiss_generator.py`, `dmed_generator.py`)
- Prescrição digital CFM/ICP-Brasil + trilha LGPD append-only
- Motor financeiro do médico (Pix + livro caixa)
- Cockpit clínico unificado + Portal do Paciente + PWA/Service Worker
- RBAC/ABAC e gestão de papéis (Onda 10)
- BI Epidemiológico e linhas de cuidado (Onda 7)
- Rastreamento por modelo (a atribuição de autoria do relatório final)

### ❌ Problemas herdados / gerados

| Problema | Estado |
|---|---|
| 7 módulos sintaticamente inválidos | ❌ nunca corrigidos |
| 16 testes falhando no `main` | ❌ |
| 49 fixtures com identificador inválido | ❌ |
| `analytics.py` = árvore ASCII com imports inexistentes | ❌ nunca corrigido |
| `docs/gerados_por_ia/` (734 arquivos) | ✅ removido (virou `.tar.gz`) |
| `app/` e `tests/` na raiz (locais errados) | ✅ removidos |
| 5 versões de `DIRETRIZES_*` | ⚠️ ainda 5 |
| Working tree sujo (7 arquivos) | ❌ |
| 1.603 commits sem push | ❌ **risco de perda** |

---

## 5. Ações pendentes (priorizadas)

| # | Ação | Esforço | Por quê |
|---|---|---|---|
| 1 | **Push dos 1.603 commits** | 5 min | risco de perda total; revisão do conteúdo pode ser depois |
| 2 | **Commitar ou descartar os 7 arquivos modificados** | 5 min | trabalho não commitado no fim da maratona |
| 3 | **Corrigir as 16 falhas** do `main` | 1–2 h | repo vermelho é dívida que cresce |
| 4 | **Reparar os 7 arquivos de sintaxe** (remover `# Arquivo:` + dedent) | 30 min | 6 são repositórios inúteis; `soap_assistant` é bomba-relógio |
| 5 | **Deletar `api/v1/analytics.py`** | 2 min | árvore ASCII com imports inexistentes |
| 6 | **Corrigir as 49 fixtures** com DV inválido | 1 h | dado clínico inválido em teste |
| 7 | Instalar o **gate do HierAgent** no ciclo | 2 h (F1) | o que teria evitado tudo acima |
| 8 | Consolidar as 5 `DIRETRIZES_*` em 1 | 30 min | ruído documental |

**Sequência mínima segura:** 1 → 2 → 3 → 4. O item 7 é o que muda o jogo para a próxima
rodada de agentes.

---

## 6. Sobre a ferramenta de verificação

Os números deste relatório foram produzidos pelo **gate v0.1** construído no projeto de
multiagente (HierAgent), rodando **de fora** contra este repositório:

```bash
cd "/home/jpversiani/projeto de multiplos agentes"
.venv/bin/python -c "
import sys; sys.path.insert(0,'src')
from hieragent.validation import PortaoQualidade
rel = PortaoQualidade('/home/jpversiani/Projeto_MedIA').avaliar_sync()
print(rel.resumo())
for a in rel.erros: print(' •', a.render())"
```

**0,9 segundos** para achar o que 1.610 commits e 12 horas não acharam. Nenhum código do
HierAgent foi instalado dentro do MedIA — a separação entre os projetos está intacta
(ver `HierAgent/docs/KNOWLEDGE_E_GATE.md` §0).

---

## 7. Relatórios relacionados

| Documento | Onde | Assunto |
|---|---|---|
| `RELATORIO_CODIGO_LOCAL_ERRADO.md` | `docs/` (aqui) | código no lugar errado, com correções |
| `RELATORIO_APROVEITAMENTO_TAR_IA.md` | `docs/` (aqui) | triagem do `tar.gz`: ~2% aproveitável |
| `RELATORIO_ESTADO_ATUAL_E_PLANO.md` | `docs/` (aqui) | **este** — estado pós-maratona |
| `KNOWLEDGE_E_GATE.md` | `HierAgent/docs/` | a ferramenta de knowledge + gate |
