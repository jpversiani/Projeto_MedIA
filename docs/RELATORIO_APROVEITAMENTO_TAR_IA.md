# Relatório de análise e proposta de aproveitamento — `docs/historico_auditoria_ia.tar.gz`

**Projeto:** MedIA · **Data da análise:** 26/09/2026 · **Fase:** somente análise (nada foi
alterado no repositório)

---

## Sumário executivo

O `docs/historico_auditoria_ia.tar.gz` (3,3 MB) é o **arquivo mortuário das 9+ horas de
maratona de IA** (25/09). Contiene **788 arquivos `.md`, 419.375 linhas, 78.948 linhas de
código embutido** — mas **não é documentação nem biblioteca**: é o registro bruto do processo
de geração automática, com os mesmos 8–13 domínios executados **24 a 32 vezes** cada, por 4
modelos diferentes.

**Conclusões principais:**

1. **~85% já foi aproveitado** na aplicação atual (repositórios, motor de triagem, JS de
   frontend, farmácia, salas WebRTC, TISS/DMED) — não há o que reextrair.
2. **O ativo de maior valor são 141 testes de regras de negócio** que nunca foram
   commitados como código (viviam como texto dentro dos `.md`) e, portanto, **nunca
   executaram**. Eles revelam lacunas reais na aplicação atual:
3. **A análise revelou 3 lacunas reais na aplicação** que esses testes documentam:
   - **MEWS incompleto + duplicado** (duas implementações divergentes; falta pontuação de
     faixa baixa e AVPU "V" na do motor de triagem);
   - **Interoperabilidade e-SUS/SISAB incompleta** (10 campos ausentes no exportador FAI);
   - **Dispensação parcial com saldo remanescente não implementada** (feature real de
     farmácia, com cobertura de teste de 25 linhas).
4. **O material restante (logs de agente, auditorias, ciclos duplicados, alucinações) deve ser
   arquivado** — valor histórico, não de produto.
5. **Rendimento do material: ~2%** (≈5–8 mil linhas de 419 mil) tem aproveitamento real.

---

## 1. Método

| Passo | O que foi feito | Onde |
|---|---|---|
| Extração integral | `tar -xzf` do tar.gz | `/tmp/opencode/tar_audit/docs/gerados_por_ia/` |
| Inventário | parser de nomes + contagem de linhas/blocos por arquivo | `/tmp/opencode/inv.json`, `inv2.json` |
| Extração de código | blocos fenced (python/js/html/xml/json/bash) + 2 `.md` que são Python cru | `/tmp/opencode/tar_code/{domínio}/` |
| Classificação | 788 arquivos por papel (entrega/log/auditoria) e domínio | seção 2 |
| Cruzamento | dif de símbolos e de regras de negócio contra `backend/app` da MedIA | seção 4–5 |
| Verificação clínica | leitura da implementação de MEWS da app vs. os testes do tar | seção 5.2 |

**Nomenclatura dos arquivos:** `{wave}{frente}_{modelo}_{domínio}_c{ciclo}_{papel}.md`
Ex.: `f2_qwen_estoque_c82_entrega.md` = frente 2, modelo Qwen, domínio estoque, ciclo 82,
entrega do agente. Papéis: `entrega` (implementação), `Tester-Local-PC`,
`Notebook-Win11-Specialist`, `Coder-OpenCode-Alpha/Beta` (logs de execução), `*_cpu`
(auditorias).

---

## 2. Inventário completo

### 2.1 Visão geral

| Métrica | Valor |
|---|---|
| Arquivos | **788** (100% `.md`; nenhum `.py`/`.sh` como arquivo) |
| Linhas totais | **419.375** |
| Linhas de código embutido | **78.948** (18,8%) — python 70.037, js 2.538, html 1.119, xml 207, json 183 |
| Arquivos com código | 483 (61%) |
| Python cru com extensão `.md` | 2 (`auditoria_prescricao_cpu.md`, `auditoria_copiloto_etico_cpu.md` — começam com `import os...`) |
| Tamanho extraído | 48 MB |
| Código extraído para análise | **38.577 linhas em 1.280 arquivos** |

### 2.2 Por papel (entrega = implementação; log = transcrição de agente)

| Papel | Arquivos | Linhas | Código |
|---|---|---|---|
| **entrega** | **368** | 312.608 | 39.356 |
| log (Tester/Notebook/Coder) | 404 | 104.514 | 39.117 |
| auditoria (`*_cpu`) | 16 | 2.253 | 1.325 |

### 2.3 Por domínio (tarefa) — a mesma tarefa repetida 24–32×

| Domínio | Arquivos | Linhas | Natureza |
|---|---|---|---|
| `qwen_db` | 160 | 52.130 | repositórios (SQLAlchemy) — **já incorporado** |
| `bonsai_ui` | 212 | 72.240 | telas/componentes — **já incorporado** |
| `deepseek_test` | 117 | 133.421 | **testes** — maior alvo de aproveitamento |
| `glm_pc` | 41 | 42.981 | prontuário, agenda, validações, calculadoras |
| `glm_nb` | 37 | 63.688 | features web (fila, gravação, consentimento) |
| `qwen_estoque` | 30 | 9.246 | **farmácia/estoque** — regras de dispensação |
| `qwen_soap_ai` | 24 | 7.612 | rascunho SOAP por IA |
| `glm_api` | 12 | 4.154 | salas WebRTC, mensageria |
| `glm_farmacia` | 12 | 4.006 | receita/dispensação |
| `glm_protocolo` | 11 | 3.056 | motor de triagem (Manchester C15) |
| `glm_export` | 10 | 3.494 | **XML FAI/SISAB**, TISS |
| `nemotron_ui/ux` | 7 | 975 | UX/visão de produto |
| `auditoria_cpu` | 4–16 | — | auditorias (2 com Python cru) |

### 2.4 Por modelo

| Modelo | Arquivos |
|---|---|
| Qwen | 214 |
| Bonsai | 212 |
| GLM | 123 |
| DeepSeek | 117 |
| Nemotron | 11 |
| CPU-Ryzen-Auditor | 16 |

**Redundância:** 8 domínios × 24–32 ciclos × 4 modelos = a mesma tasked entregue centenas de
vezes com variações. Só 8 de 926 arquivos `.py` extraídos são **duplicatas exatas** (md5), mas
a duplicação **semântica** é muito maior (mesma classe/regra com nomes diferentes).

---

## 3. Diagnóstico: o que JÁ foi aproveitado (não reextrair)

Verificado arquivo a arquivo contra a aplicação atual:

| Conteúdo do tar | Estado na MedIA |
|---|---|
| `triagem_clinica.py` — motor Manchester Adaptado C15 (entregue no domínio `protocolo`) | `services/triagem_clinica.py` ✔ |
| Repositórios: AuditoriaTelemedicina, OfflineCache, SinaisVitais, Campanhas, Analytics, RemessaSISAB | `repositories/*.py` (6) ✔ |
| JS: acessibilidade, consentimento LGPD, fila de espera, player de gravação, screen share, sinais vitais | `static/js/*.js` (6) ✔ |
| Modelos Receita/ReceitaItem/Dispensacao, TeleSala/Participante | `models/farmacia.py`, `api/v1/telemedicina_ws.py` ✔ |
| TISS, DMED, Framingham, CKD-EPI, Rename/Anvisa, CommandBar, PWA | commits pós-pivot (`b045397`…`71bd0b3`) ✔ |
| SOAP, MEWS, escalas, validadores CNS/CPF | `services/copiloto_clinico.py`, `triagem_clinica.py`, `escalas_clinicas.py`, `validadores.py` ✔ |

**Conclusão:** ~85% do tar é histórico de trabalho já incorporado. Reextrair qualquer coisa
desses domínios é retrabalho.

---

## 4. O ativo de valor: os 141 testes de regras de negócio

O domínio `deepseek_test` (117 arquivos) contém **141 funções de teste distintas** que
especificam regras de negócio reais. **Nunca foram commitados como código — viviam como texto
dentro dos `.md` — logo, nunca executaram.** Sua área funcional:

| Área | Testes | Regra especificada | Situação na app |
|---|---|---|---|
| **Alergia/contraindicação** | 8 | bloquear medicamento com alergia declarada; permitir não-alérgico | app tem base de conhecimento de alergias no copiloto; **falta teste** |
| **Dispensação parcial** | 4 | `quantidade_restante` decrementa; saldo remanescente; acumulação sequencial; bloquear após zerar | **regra NÃO implementada** (app só acumula `quantidade_dispensada`) |
| **Hash/integridade** | 8 | rejeitar receita/lote com hash adulterado; hash bate com payload | app tem `codigo_hash` SHA-256; **falta validação/teste** |
| **MEWS** | 12 | faixas baixas (SBP 70→3), AVPU "V"→2, pediátrico por faixa etária | **parcial** — ver 5.2 |
| **Escore de risco** | 7 | zero p/ sinais normais; sobe com taquicardia/bradicardia/temperatura/rebaixamento de consciência | app tem; **falta teste** |
| **CIS/CID e operadoras** | 13 | ficha válida com CIAP **ou** CID; inválida sem ambos; múltiplas operadoras; ignora nulos/anos | app tem `sisab_client`/`fai_exporter`; **parcial** |
| **SOAP** | 9 | rascunho com 4 componentes; avaliação reflete diagnóstico; plano reflete conduta | app tem SOAP no motor de triagem; **falta teste** |
| **Prescrição** | 8 | interação grave gera alerta; sem interação não gera | app tem copiloto; **falta teste** |

**Ressalva crítica:** os testes **não são drop-in**. Importam uma API paralela/antiga que não
existe mais na app: `app.services.triagem` (hoje `triagem_clinica`), `app.services.farmacia_service`
(hoje `farmacia`), `app.schemas.paciente`, `app.utils.hash_utils`, `app.services.exceptions`
(hoje `core.exceptions`). Além disso, há **redundância interna**: das 8+8+9 listas de
alergia/hash/SOAP, são a mesma regra com 6–8 nomes diferentes. Valor real = **8–10 regras
únicas**, portadas na mão.

Exemplo real (baixa parcial, `estoque`/`farmacia`):

```python
def test_baixa_parcial_registra_saldo_remanescente(db_session, service):
    prescricao = create_prescricao(quantidade_total=10)
    service.dispensar(prescricao.id, 4)
    db_session.refresh(prescricao)
    assert prescricao.quantidade_restante == 6
    dispensacao = db_session.query(Dispensacao).filter_by(prescricao_id=prescricao.id).one()
    assert dispensacao.quantidade == 4
```

Exemplo real (MEWS, `deepseek_test`):

```python
def test_adult_mews_low_sbp(self):
    """Pressão sistólica muito baixa deve pontuar 3."""
    score = calculate_mews_adult(hr=80, sbp=70, rr=16, temp=36.5, avpu="A")
    assert score == 3

def test_adult_mews_avpu_voice(self):
    """Resposta ao chamado (V) deve pontuar 2."""
    score = calculate_mews_adult(hr=80, sbp=120, rr=16, temp=36.5, avpu="V")
```

---

## 5. Achados técnicos: 3 lacunas reais reveladas pelo material

### 5.1 🔴 MEWS — duas implementações divergentes, uma incompleta

A app tem **duas** implementações de MEWS:

| Onde | Escopo | Problema |
|---|---|---|
| `services/escalas_clinicas.py` (1.868 linhas) | `EscalaMEWS` completa: escore 0–14, **AVPU com pontos por nível** (A/V/P/U), gatilhos NICE (PAS ≤ 90, FR ≥ 30), faixas pediátricas | — (referência) |
| `services/triagem_clinica.py` (754 linhas) | `SinaisVitais.calcular_escore_mews()` simplificado | **pontua só faixas ALTAS**; falta SBP baixa, FC baixa, FR baixa, temp baixa; **AVPU "V" não pontua** (só "P"/"U" = 3) |

Comparando com o MEWS de Subbe et al. e com os testes do tar, o motor de triagem **perde
pontuação em deterioração clínica** (bradicardia, hipotensão, confusão) — justamente os
sinais de piora que a triagem de APS deve capturar. **Proposta:** unificar, usando
`EscalaMEWS` como implementação canônica e fazendo o motor de triagem consumi-la (elimina a
duplicação e o risco clínico). Impacto em testes: os testes canônicos atuais
(`pa=185, fc=135, temp=39.5 → 8`; pediátrico `fc=200, fr=40, temp=39 → 9`) usam apenas faixas
altas e **permanecem válidos**.

### 5.2 🔴 Interoperabilidade e-SUS APS / SISAB — 10 campos ausentes no exportador FAI

Comparando o XML do tar (`export`) com `services/fai_exporter.py`:

| Campo no XML do tar | No exportador da app? |
|---|---|
| `cabecalho/cnesUnidade` | ✔ (`cnes`) |
| `dadosDoCidadao/cnsCidadao`, `nomeCidadao`, `sexoCidadao` | ✔ |
| `dadosDoCidadao/dataNascimento` | ✘ |
| `dadosDoCidadao/racaCorCidadao` | ✘ |
| `dadosDoCidadao/etniaCidadao` | ✘ |
| `dadosDoCidadao/nacionalidadeCidadao` | ✘ |
| `dadosDoCidadao/codigoMunicipioResidencia` | ✘ |
| `dadosDoCidadao/cepCidadao` | ✘ |
| `cabecalho/codigoProfissionalCNS` | ✘ |
| `cabecalho/cboProfissional` | ✘ |
| `cabecalho/numeroLote` | ✘ |
| `atendimentoIndividual/problemas` (lista) | parcial (condutas) |
| `atendimentoIndividual/procedimentos` | ✘ |
| `atendimentoIndividual/exames` | parcial |
| `atendimentoIndividual/evolucao` | ✘ |
| `atendimentoIndividual/registroSOAP` | ✘ |

**Sem esses campos, a FAI não é aceita pelo validador e-SUS/SISAB** — é o que define
interoperabilidade real com o SUS. O XML do tar é um **esqueleto com `...`** (não é
implementação), mas serve de **checklist de conformidade**.

### 5.3 🟡 Dispensação parcial com saldo — feature ausente

Evidência: `models/farmacia.py` tem `quantidade_dispensada` (acumulado) e
`api/v1/farmacia.py:239` incrementa — mas **não existe `quantidade_restante`/saldo**, e o
teste atual (`test_farmacia_dispensacao.py`) tem **25 linhas** para uma feature com 2.5k
linhas de histórico. Dispensação parcial (entregar 4 de 10, saldo 6; novas dispensações
somam ao saldo; bloquear após zerar) é regra real de farmácia de SUS.

### 5.4 🟡 Visita domiciliar / saúde comunitária — decisão de produto

O tar traz modelos `HomeVisit` (com `campaign_id`, dados do paciente, prioridade clínica por
gravidade/idade/comorbidades) e `CommunityHealthAgent` (ACS) em
`ui/f8_bonsai_ui_c16_entrega__01.py`. A app **não tem** essa feature (só menções a
"domicil"). Visita domiciliar núcleo do SUS (e-SUS APS tem o módulo) — mas é decisão de escopo,
não de reaproveitamento.

### 5.5 🟢 Itens de menor porte

- **Integridade/hash de receita e lote** (8 testes): app tem `codigo_hash` SHA-256; falta a
  validação de adulteração + teste.
- **Bloqueio por alergia/contraindicação** (8 testes): app tem a base de conhecimento no
  copiloto; falta a regra de bloqueio + teste.
- **SOAP** (9 testes): app gera SOAP no motor de triagem; falta a rede de testes dos 4
  componentes.
- **Regras de risco** (7 testes): escore zero para sinais normais e incremento por deterioração.

---

## 6. O que deve ser arquivado ou descartado

### 6.1 Arquivar (valor histórico, zero valor de produto) — ~94% do material

- **404 logs de agente** (Tester-Local-PC, Notebook-Win11-Specialist, Coder-*): 104.514
  linhas de transcrição de execução. São idênticos às entregas em volume de código — mesmo
  conteúdo, papel diferente.
- **16 auditorias `*_cpu`**, incluindo os 2 arquivos que são Python cru com `.md`.
- **Ciclos duplicados**: das 24–32 execuções de cada domínio, manter **1 melhor variante**.

### 6.2 Descartar (erro de agente / alucinação)

| Item | Motivo |
|---|---|
| `test_chave_webrtc`, `test_documentacao` | testam rotas **inexistentes** (`client.get('/chave_webrtc')` → 200) — alucinação de auditor |
| Fragmentos de model sem imports | `class Receita(Base):` solto; `id, sala_id, usuario_id, papel, cns...` como tupla — não compilam |
| Templates XML/JS com `...` | placeholder, não implementação |
| Testes com API inexistente sem equivalente | `calculate_mews_adult`/`calculate_mews_pediatric` (funções modulares) — a app usa método na classe; portar ou descartar |

---

## 7. Proposta de aproveitamento (o que fazer com o material)

### Princípio: colheita cirúrgica, não rejeição

Não "importar o tar". Extrair **8–10 regras de negócio + 1 checklist de conformidade**,
portá-las à API atual, e **arquivar o resto** (o histórico já está no git — o tar é redundante
para isso).

### Fase 1 — Gain rápido, risco baixo (1 a 2 dias)

| # | Ação | Origem | Destino | Esforço | Risco |
|---|---|---|---|---|---|
| 1.1 | Portar os **8 testes de MEWS/escore** para a API atual (`SinaisVitais.calcular_escore_mews`) | `deepseek_test` | `backend/tests/test_mews_regras.py` | 2h | baixo (só testes) |
| 1.2 | Portar os **7 testes de escore de risco** | `deepseek_test` | idem | 1h | baixo |
| 1.3 | Portar **3–4 testes de SOAP** (4 componentes, diagnóstico→avaliação, conduta→plano) | `deepseek_test` | `backend/tests/test_soap_regras.py` | 2h | baixo |
| 1.4 | Extrair o **checklist de campos e-SUS** do XML para um documento normativo | `glm_export` | `docs/INTEROPERABILIDADE_E_SUS.md` | 1h | nenhum |

**Entrega:** +15–18 testes reais (cobertura que hoje não existe) + 1 doc de conformidade.
**Aceite:** `pytest` verde; testes passam **sem alterar** código de produção.

### Fase 2 — Ganho de produto, risco médio (3 a 5 dias)

| # | Ação | Origem | Detalhe | Esforço | Risco |
|---|---|---|---|---|---|
| 2.1 | **Unificar MEWS**: motor de triagem passa a usar `EscalaMEWS` (ou replicar faixas baixas + AVPU V) | seção 5.1 | corrigir lacuna clínica + eliminar duplicação | 1–2 dias | **médio** — validar os testes canônicos (OpenSUS: 185/185) antes/depois |
| 2.2 | **Implementar dispensação parcial com saldo** (`quantidade_restante`) | seção 5.3 | modelo + serviço + 4 testes portados | 1 dia | médio (regra nova) |
| 2.3 | **Hash/integridade**: rejeitar receita/lote adulterado | seção 5.5 | validação + 3 testes portados | 4h | baixo |
| 2.4 | **Bloqueio por alergia** na prescrição | seção 5.5 | regra usando a KB do copiloto + 3 testes portados | 6h | médio (clínico) |

**Entrega:** 3 lacunas fechadas + ~10 testes de regra.

### Fase 3 — Decisão de produto (depende do dono)

| # | Ação | Dependência |
|---|---|---|
| 3.1 | **Completar a FAI** com os 10 campos ausentes (dataNascimento, raca, etnia, nacionalidade, município, CEP, CNS do profissional, CBO, nº lote, procedimentos, exames, evolução, SOAP) | escopo + validação com o validador e-SUS |
| 3.2 | **Visita domiciliar** (`HomeVisit` como ponto de partida) | decisão de escopo do MVP |

### Fase 4 — Higiene do repositório

| # | Ação |
|---|---|
| 4.1 | Mover o tar.gz **para fora de `docs/`** (artefato de processo, não documentação): storage de release/CI ou `audit-history/` explicitamente rotulado |
| 4.2 | Ou remover do histórico Git (custa reescrita — decisão do dono) |
| 4.3 | Consolidar as **5 versões** das diretrizes clínicas em 1 (histórico no git) |
| 4.4 | Guardar, em `/tmp/opencode/tar_code`, o subconjunto aproveitável até a portagem ser feita |

---

## 8. Esforço total e rendimento

| Fase | Esforço | Ganho |
|---|---|---|
| 1 (quick) | 1–2 dias | 15–18 testes + doc de conformidade |
| 2 (produto) | 3–5 dias | 3 lacunas fechadas (MEWS clínico, saldo, integridade) + 10 testes |
| 3 (escopo) | a definir | FAI conforme + (ou não) visita domiciliar |

**Rendimento do material:** de 419.375 linhas arquivadas, **≈5–8 mil linhas (2%)** têm
aproveitamento real — mas o **rendimento em cobertura de teste e conformidade é alto**,
porque os 141 testes nunca rodaram e as regras que documentam (MEWS, saldo, integridade,
alergia) são exatamente as áreas mais fracas da app hoje.

---

## 9. Riscos e lições (para as próximas maratonas)

| Armadilha encontrada no material | Regra para os agentes |
|---|---|
| Testes contra **API imaginada** (`app.services.triagem`, `farmacia_service`) | Ler o serviço antes de escrever o teste |
| Testes de **rotas inexistentes** (`/chave_webrtc` → 200) | Gerar teste a partir da rota real, nunca inventar |
| **141 testes** que nunca rodaram (só texto em `.md`) | Código só em arquivo de código; rodar `pytest` antes de commitar |
| Mesma tarefa 24–32× por 4 modelos | Uma entrega por tarefa, com aceite (teste/suíte verde) |
| Fragmentos sem imports / templates com `...` | Entrega compilável, ou issue — não arquivo "quase pronto" |
| Regras clínicas divergentes entre 2 implementações (MEWS) | Uma fonte canônica por regra clínica + testes que a fixem |

---

## Anexos (paths de trabalho)

- Material extraído: `/tmp/opencode/tar_audit/docs/gerados_por_ia/` (788 `.md`)
- Código extraído por domínio: `/tmp/opencode/tar_code/{ui,db,test,pc,nb,estoque,soap_ai,api,farmacia,protocolo,export,audit}/`
- Inventário machine-readable: `/tmp/opencode/inv.json`, `/tmp/opencode/inv2.json`
- Análise resumida: `/tmp/opencode/ANALISE_TAR_IA.md`
- Aplicação comparada: `/home/jpversiani/Projeto_MedIA/backend/app/` (101 `.py`, 16 HTML, 11 JS)
