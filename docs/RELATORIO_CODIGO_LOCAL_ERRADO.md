# Relatório: código escrito no local errado — Projeto_MedIA

> **Escopo deste relatório: exclusivamente o Projeto_MedIA** (`/home/jpversiani/Projeto_MedIA`).
> Os problemas do OpenSUS têm relatório próprio: `OpenSUS/docs/RELATORIO_CODIGO_LOCAL_ERRADO.md`
> (não confundir os dois).
>
> **Aviso operacional:** as maratonas de IA (PIDs 1485863 e 2538884) **estão rodando agora e
> escrevendo neste repositório** (245 arquivos modificados não commitados, incluindo testes e
> serviços). Qualquer correção aqui precisa de um combinado com o dono: parar/congelar as
> maratonas, ou trabalhar em isolamento (branch/commit atômico) para não ser sobrescrito.
>
> Este relatório lista tudo que foi escrito no lugar errado (auditado nesta data), **as
> correções pendentes em ordem de execução** e as **regras para os agentes** produzirem código
> e scripts corretamente.

---

## 1. Suíte de testes **não roda** (estado inicial de tudo)

`python -m pytest` na raiz → **239 errors em ~43s**. Nenhum teste passa. O `pytest.ini` da raiz
coleta apenas `backend/tests` (`pythonpath = backend`). → **Primeiro diagnóstico:** capturar os
erros de import/conftest (muito provavelmente sujeira das edições não commitadas em
`backend/tests/conftest.py` e arquivos de serviço).

## 2. Testes em **três** locais diferentes (um deles triplicado)

| Local | Coletado? | Situação |
|---|---|---|
| `backend/tests/` (23 arquivos) | ✅ sim (`testpaths`) | local correto |
| `backend/app/tests/` (3 arquivos) | ❌ não | órfãos dentro do pacote de produção |
| `tests/` na raiz (3 arquivos) | ❌ não | terceiro local, paralelo |

- **`test_triagem_clinica.py` existe 3×** (`tests/`, `backend/tests/`, `backend/app/tests/`) —
  colisão de nome de módulo; impossível coletar os dois maiores juntos.
- `test_farmacia.py` só existe na raiz; `backend/tests/test_farmacia_dispensacao.py` é outro.
- `backend/app/tests/`: imports inconsistentes (`backend.app.*` em `test_fai_serializer.py` e
  `test_triagem_clinica.py` vs `app.*` em `test_fila_teleatendimento.py`) e **15 ocorrências
  de identificadores falsos** (CNS/CPF inventados) em `test_fila_teleatendimento.py`.

## 3. Árvore de aplicação **duplicada na raiz**

`app/` na raiz (só `app/main.py` e `app/api/v1/farmacia.py`) — **código morto**: com
`pythonpath = backend`, `import app` resolve para `backend/app`, então a raiz nunca é usada.
→ **Correção:** remover ou mover para o local certo (decidir com o dono).

## 4. Documentação salva como código

**`backend/app/api/v1/analytics.py`** — o arquivo **não é Python**: contém árvore ASCII
(`├── schemas/ analytics.py # main deliverable`). Um plano de entrega de IA salvo com extensão
`.py`; daria `SyntaxError` em qualquer import. → **Correção:** remover ou mover para `docs/`.

## 5. Arquivos com **nome lixo** na raiz (script que errou o redirect)

Dois arquivos na raiz (criados 25/09 14:50, ~1 KB) cujo **conteúdo virou nome de arquivo** —
fragmentos JSON tipo `","reasoning_details":[{"type":"reasoning.text"...`. Algum script de
maratona escreveu output no caminho errado. → **Correção:** apagar os dois arquivos e corrigir
o script que os criou (redirecionamento mal formado).

## 6. Código especulativo / defeitos conhecidos (auditando divergências)

- **`backend/app/api/v1/farmacia.py`** existe aqui, mas **diverge do OpenSUS** (sem o
  comentário `# Assuming these models exist`) — foi modificado pelas maratonas. → **Auditar
  antes de corrigir; não assumir os mesmos defeitos do OpenSUS.**
- **`backend/app/services/fai_serializer.py`** também **diverge** (sem os defeitos
  `Any`/`'cbs'` conhecidos do OpenSUS). → **Auditar.**
- Pista valiosa: o **OpenSUS corrigiu a versão original** desses arquivos (commits `84f0649`,
  `db611a4`) — usar como referência de contrato, **verificando o diff** antes de copiar, pois o
  MedIA evoluiu por fora.

## 7. Entregas de IA dentro do repo de produto

- **`docs/gerados_por_ia/`**: 734 entregas markdown, ~10 MB — produção das maratonas dentro do
  repositório de código. → Mover para repo/artefato separado ou arquivar fora do branch principal.
- **245 arquivos modificados não commitados** — inclui `backend/tests/test_analytics_kpis.py`,
  `backend/app/services/*`, `backend/app/static/*` e os próprios órfãos de `backend/app/tests/`:
  trabalho ao vivo não versionado; impossível auditar o que mudou.

## 8. Padrões que **já corrigimos no OpenSUS e não podem se repetir aqui**

(Copy-paste mental para os agentes — detalhes no relatório do OpenSUS)

1. Testes em `backend/app/` → mover para `backend/tests/`.
2. CNS/CPF "mutados" de um válido oficial quebram o validador DATASUS → usar exemplos de
   `app/services/validadores.py` ou recalcular DV (soma pesos 15→1 múltipla de 11).
3. Testes escritos contra API imaginada (assinaturas/atributos que não existem) → ler o serviço
   antes de escrever o teste.
4. Testes async com fila/hub em **dois event loops** → hang infinito da suíte inteira.
5. `from app.models import ... # Assuming these models exist` → nunca; criar o modelo junto.
6. Serviço que descarta id recebido e gera outro → inconsistência `KeyError` (ver
   `entrar_na_fila` do OpenSUS).

---

## Correções pendentes — ordem de execução

> Objetivo: MedIA com suíte **verde e auditável**. Executar nesta ordem:

1. **Decidir com o dono o trato das maratonas** (parar, ou branch isolado) — sem isso, qualquer
   correção pode ser sobrescrita.
2. **Diagnosticar os 239 errors** da suíte (`python -m pytest`, capturar imports/conftest) e
   voltar a 0 erros de coleta — mesma receita do OpenSUS (conftest + `pytest.ini`).
3. **Unificar os 3 locais de teste:** migrar `backend/app/tests/` e `tests/` (raiz) para
   `backend/tests/`, **eliminando a tripla duplicata** `test_triagem_clinica.py` (manter a
   versão canônica; portar testes únicos; apagar duplicatas).
4. **Remover árvore morta:** `app/` da raiz.
5. **Remover lixo:** `analytics.py` (árvore ASCII) e os 2 arquivos de nome JSON na raiz
   (localizar e corrigir o script-fonte do redirect).
6. **Auditar** `farmacia.py` e `fai_serializer.py` contra o diff do OpenSUS (item 6) — corrigir
   o lado que estiver errado.
7. **Limpar os 245 modificados:** revisar em grupos temáticos, commit atômico por tema — ou
   descartar sujeira de maratona que não deva ir ao versionado (decisão do dono).
8. **Rodar suíte completa até verde + smoke** `uvicorn` antes de qualquer merge.

## Regras para os agentes (produzir código e scripts do jeito correto)

1. **Local é contrato:** testes só em `backend/tests/`; docs só em `docs/`; nunca testes dentro
   de `app/`; nunca código de produto na raiz; nada de árvore de plano salva em `.py`.
2. **Rodar `pytest <arquivo>` antes de commitar** e deixar a suíte verde no próprio commit.
3. **Identificadores:** só CNS/CPF dos exemplos oficiais em `app/services/validadores.py` ou
   com DV calculado; **proibido "mutar dígitos"**.
4. **Testes importam a API real:** ler o serviço antes de escrever o teste; sem assinaturas
   imaginadas; sem duplicar nomes de módulo de teste.
5. **Nada especulativo** (`# Assuming...`): ou cria a dependência junto, ou não commita.
6. **Async:** teste com fila/hub WebSocket roda **num único event loop**; nunca misturar
   `new_event_loop()` solto com `run_until_complete` de outro loop.
7. **Scripts das maratonas:** output só para caminhos validados (nunca usar conteúdo como nome
   de arquivo); trabalho novo em diretório próprio; commit atômico com suíte verde — nada de
   245 arquivos sujos.

## Estado na data desta análise (Projeto_MedIA)

- Suíte: **239 errors — não roda** (vs OpenSUS: 185/185 ✓)
- 245 arquivos modificados não commitados (maratonas ao vivo)
- Testes em 3 locais; `test_triagem_clinica.py` triplicado
- Sujeira na raiz: `app/`, 2 arquivos-nome-JSON
- `docs/gerados_por_ia/`: 734 entregas (~10 MB)

## Referências

- Relatório do OpenSUS (não confundir): `OpenSUS/docs/RELATORIO_CODIGO_LOCAL_ERRADO.md`
- Estado do produto MedIA: `docs/ESTADO_ATUAL.md`
- Suíte de referência verde: OpenSUS `185/185` (commit `db611a4`)
