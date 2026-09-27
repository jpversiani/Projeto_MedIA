# Relatório de estado atual e plano de ação

**Data:** 26/09/2026 · **Natureza:** fotografia do momento + plano. Documento de
**dois projetos** — cada bloco indica explicitamente a qual repositório pertence.
Gerado em `/tmp/opencode/`; cópia em `MedIA/docs/`.

---

## ⚠️ 0. Aviso de validade

As maratonas de IA **estão rodando neste momento** (2 processos) e o MedIA já tem
**1528 commits à frente do origin**. Este relatório é um **snapshot**: o estado do MedIA
muda a cada hora. Decisões aqui precisam ser reconferidas antes de agir.

---

## 1. OpenSUS (`/home/jpversiani/OpenSUS`)

### Estado do repositório

| Item | Estado |
|---|---|
| Branch | `main` sincronizado com `origin/main` (nada pendente de push) |
| Último commit | `7b7e294` docs: status atualizado |
| Commits desta sessão | `84f0649` (coleta 7→0) · `db611a4` (43→0 falhas) · `7b7e294` (docs) |

### Trabalho em andamento, **ainda não commitado** (5 itens)

| # | Item | Situação |
|---|---|---|
| 1 | Migração dos 3 testes órfãos: `app/tests/*` → `backend/tests/` | **feita** (git já mostra os renames no índice) |
| 2 | `fai_serializer.py`: 3 defeitos corrigidos (imports `Any`/`Dict`, typo `cbs`, validator de campo inexistente) | **feita** |
| 3 | `test_fai_serializer.py`: contradições internas do teste reconciliadas | **feita — 11/11 ✅** |
| 4 | `docs/RELATORIO_CODIGO_LOCAL_ERRADO.md` | **criado, untracked** |
| 5 | `test_fila_teleatendimento.py` (73) e `test_triagem_clinica_unidade.py` (29) | **pendentes: 11 falhas + 15 falhas + 1 hang** |

### Estado da suíte

- **185/185 ✅** verificado no commit `7b7e294` (antes da migração dos órfãos)
- **11/11 ✅** FAI após a migração
- ❌ **`test_publicar` (fila) trava a suíte inteira** — não rodar `pytest` completo até corrigir
- 15 falhas mapeadas na triagem-unidade (contrato antigo — ver checklist do relatório)

### Bloqueio para commit

> A migração **não deve ser commitada ainda**: com o hang da fila, `pytest` no `main`
> ficaria travado. Ordem: corrigir hang → CNS fixtures → `entrar_na_fila` → triagem → só
> então commitar.

### Documentos no repo

- `docs/ESTADO_ATUAL.md` ✅ versionado (atualizado em `7b7e294`)
- `docs/RELATORIO_CODIGO_LOCAL_ERRADO.md` ⚠️ **untracked** (falta commit)

---

## 2. Projeto_MedIA (`/home/jpversiani/Projeto_MedIA`)

### Estado do repositório — **movimento intenso**

| Item | Estado |
|---|---|
| Working tree | **limpo** |
| Branch | `main` **1528 commits à frente** do `origin` (⚠️ não enviado) |
| Últimos commits | `b6c4de3` Frente 9: Trilha Criptográfica LGPD · `26fb955` Frente 8: PWA/Offline-First · `db84477` Frente 7: BI Epidemiológico |
| Fase das maratonas | **Onda 9 de 12** — ainda há 3 ondas por vir |
| Suíte | **346 passed / 7 failed** (era 290/7 há ~30 min — cresce a cada onda) |
| Falhas | as mesmas **7** em `test_sisab_client.py` (`enviar_lote_*`, `close_client`, `context_manager`) — **não sãoNovas** |

### O que as maratonas construíram recentemente

- **Frente 7** — BI Epidemiológico, rastreamento ativo, linhas de cuidado
- **Frente 8** — PWA, Service Worker, sincronização offline-first
- **Frente 9** — trilha criptográfica de alto throughput + stress test LGPD

### Higiene do repo (verificada)

| Item | Estado |
|---|---|
| `docs/gerados_por_ia/` (734 arquivos) | ✅ removido pelas maratonas (virou `historico_auditoria_ia.tar.gz`) |
| `app/` e `tests/` na raiz (locais errados) | ✅ removidos — testes unificados em `backend/tests` |
| `docs/RELATORIO_CODIGO_LOCAL_ERRADO.md` | ✅ **versionado** (commit `b5c8aed`) |
| `docs/historico_auditoria_ia.tar.gz` (3,3 MB) | ⚠️ ainda em `docs/` — não é documentação |

### Alertas

1. **1528 commits não pushados** — risco de perda se a máquina falhar; push é o primeiro item
2. **Suíte com 7 falhas** não resolvidas desde a auditoria anterior
3. **1528 commits** também significam que relatórios/estado envelhecem muito rápido

---

## 3. Análise do `historico_auditoria_ia.tar.gz` (material de maratona)

Análise completa em `/tmp/opencode/RELATORIO_APROVEITAMENTO_TAR_IA.md` (358 linhas) —
**ainda não salvo no repo** (risco: `/tmp`). Resumo executivo:

### O que é

788 arquivos `.md`, 419.375 linhas, 78.948 de código embutido (python 70.037), 2 arquivos
que são Python cru com `.md`. É o **registro bruto da maratona** (368 entregas + 404 logs de
agente + 16 auditorias), com 12 tarefas repetidas **24–32 vezes** por 4 modelos.

### ~85% já foi aproveitado

Repositórios (6), motor de triagem, 6 JS de frontend, farmácia, salas WebRTC, TISS/DMED,
calculadoras Framingham/CKD-EPI — todos já incorporados. **Não reextrair.**

### 🔴 3 lacunas reais reveladas pelo material

| # | Lacuna | Evidência | Risco |
|---|---|---|---|
| 1 | **MEWS duplicado e incompleto** | `escalas_clinicas.EscalaMEWS` (completo: AVPU com pontos, gatilhos NICE PAS≤90) vs `triagem_clinica.calcular_escore_mews` (só faixas altas; **não pontua SBP/FC/FR baixas nem AVPU "V"**) | **clínico** — perda de deterioração na triagem |
| 2 | **Interoperabilidade e-SUS incompleta** | 10 campos ausentes no `fai_exporter.py` (dataNascimento, raca, etnia, nacionalidade, município, CEP, CNS do profissional, CBO, nº lote, procedimentos/evolução/registroSOAP) | **conformance** — a FAI não passa no validador |
| 3 | **Dispensação parcial sem saldo** | existe `quantidade_dispensada`, **não existe** `quantidade_restante`; teste atual tem 25 linhas para a feature | **produto** — falta regra de farmácia |

### 🔶 Maior ativo: 141 testes que nunca executaram

Viveram como texto dentro dos `.md` (nunca commitados como código) e especificam 8–10
**regras de negócio reais**: alergia/contraindicação (8), dispensação parcial (4),
hash/integridade de receita e lote (8), MEWS (12), escore de risco (7), CIAP/CID e
operadoras (13), SOAP (9), prescrição (8).
⚠️ Importam API antiga (`app.services.triagem`, `farmacia_service`) → **portar**, não
drop-in.

### Arquivar / descartar

- **Arquivar** — 404 logs de agente, 16 auditorias, ciclos duplicados (94% do material)
- **Descartar** — `test_chave_webrtc`/`test_documentacao` (rotas inexistentes), fragmentos sem
  import, templates com `...`

### Plano de colheita (4 fases)

| Fase | Ação | Esforço | Ganho |
|---|---|---|---|
| **1** | Portar 15–18 testes (MEWS, escore, SOAP) + extrair checklist e-SUS | 1–2 dias | cobertura que não existe, sem tocar em produção |
| **2** | Unificar MEWS · saldo de dispensação · hash/integridade · bloqueio por alergia | 3–5 dias | fecha as 3 lacunas |
| **3** | Completar a FAI · decidir visita domiciliar | a definir | conformidade + escopo |
| **4** | Tirar o tar de `docs/` · consolidar as 5 versões de diretrizes clínicas | 1 dia | higiene |

**Rendimento:** ~2% do material (5–8 mil de 419 mil linhas) — mas alto em cobertura,
porque cobre exatamente as áreas mais fracas da app.

---

## 4. Decisões pendentes do dono

| # | Decisão | Projeto | Impacto |
|---|---|---|---|
| 1 | **Push dos 1528 commits do MedIA** — agora ou depois das 12 ondas? | MedIA | alto (risco de perda) |
| 2 | Autorizar commit do relatório + da migração **após** corrigir a suíte | OpenSUS | médio |
| 3 | Corrigir as 7 falhas de `test_sisab_client.py` | MedIA | médio (traz a suíte a 353/353) |
| 4 | Aprovar a **Fase 1** da colheita do tar (portar 141 testes) | MedIA | alto valor, baixo risco |
| 5 | **Unificar MEWS** (decisão clínica: qual implementação é a canônica) | ambos | alto |
| 6 | **Dispensação parcial** entra no escopo? | MedIA | médio |
| 7 | Visita domiciliar no MVP? | MedIA | produto |
| 8 | Destino do `tar.gz`: fora do `docs/` ou remover do histórico git | MedIA | higiene |

---

## 5. Recomendações imediatas (ordem)

1. **Push MedIA** — 1528 commits sem backup remoto é o maior risco da casa
2. **Não commitar a migração do OpenSUS** até a suíte passar (hang trava tudo)
3. **Salvar os 2 relatórios** no repo antes que o `/tmp` se loses
4. **Corrigir o hang da fila** (1 arquivo, 1 teste) — libera a suíte OpenSUS
5. **Aprovar Fase 1** da colheita (ganho alto, risco baixo)

---

*Anexos de trabalho (voláteis, `/tmp`): `tar_audit/` (788 .md), `tar_code/` (1.280 arquivos
de código extraídos), `inv.json`, `inv2.json`, `ANALISE_TAR_IA.md`,
`RELATORIO_APROVEITAMENTO_TAR_IA.md`.*
