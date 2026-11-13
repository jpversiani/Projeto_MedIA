# Índice da documentação

Este índice diz **o que cada documento vale hoje**. O projeto acumulou
relatórios gerados em várias sessões e alguns descrevem um estado que já não
existe; ler o documento errado leva a conclusões falsas sobre segurança e
conformidade.

Legenda:

* **ATUAL** — pode ser usado como fonte de verdade para o estado do código.
* **NORMATIVO** — descreve uma política ou diretriz que o produto deve seguir,
  não necessariamente o que já está implementado.
* **HISTÓRICO** — registro de uma etapa passada. Útil como contexto, perigoso
  como referência técnica.

| Documento | Situação | Observação |
|---|---|---|
| [`../README.md`](../README.md) | **ATUAL** | Visão geral, como executar, stack e limitações da v1. |
| [`PLANO_DE_FINALIZACAO_V1.md`](PLANO_DE_FINALIZACAO_V1.md) | **ATUAL** | Plano de execução da revisão de 13/11/2026: escopo (consultório privado vs APS), fases 0–8, definition of done. Substitui o HANDOFF como plano vigente. |
| [`STATUS_ATUAL_CONSOLIDADO.md`](STATUS_ATUAL_CONSOLIDADO.md) | **ATUAL** | Estado consolidado por frente (P0/P1/P2, T1–T8). |
| [`AUDITORIA_COMPLETA_2026-10-29.md`](AUDITORIA_COMPLETA_2026-10-29.md) | **ATUAL (datado)** | Auditoria de código e testes de 29/10/2026; os itens já corrigidos estão marcados no próprio texto. |
| [`ROADMAP_V1.md`](ROADMAP_V1.md) | **PARCIAL** | Os bloqueios P0.4 (ICP-Brasil) e P2 continuam válidos; o quadro de P0.1/P0.2/P0.3 foi superado pelo status consolidado. |
| [`POLITICA_RETENCAO_E_TRATAMENTO_DE_INCIDENTES.md`](POLITICA_RETENCAO_E_TRATAMENTO_DE_INCIDENTES.md) | **NORMATIVO** | Retenção, direitos do titular e runbook de incidente. |
| [`DIRETRIZES_CLINICAS_OFICIAL.md`](DIRETRIZES_CLINICAS_OFICIAL.md) | **NORMATIVO** | Diretrizes clínicas de APS; não descreve o estado do software. |
| [`MANUAL_FLUXO_OPERACIONAL_MEDIA.md`](MANUAL_FLUXO_OPERACIONAL_MEDIA.md) | **NORMATIVO (parcial)** | Fluxo operacional pretendido; confira no código antes de assumir que uma etapa existe. |
| [`HANDOFF_TRABALHO_RESTANTE.md`](HANDOFF_TRABALHO_RESTANTE.md) | **HISTÓRICO (superado)** | Plano de execução de sessão anterior (base `08d130a`); o plano vigente é o `PLANO_DE_FINALIZACAO_V1.md`. |
| [`ESTADO_ATUAL.md`](ESTADO_ATUAL.md) | **HISTÓRICO** | O próprio arquivo avisa que contém afirmações desmentidas. |
| [`RELATORIO_ESTADO_ATUAL_E_PLANO.md`](RELATORIO_ESTADO_ATUAL_E_PLANO.md), [`RELATORIO_FRENTES_E_ATUACAO_AGENTES.md`](RELATORIO_FRENTES_E_ATUACAO_AGENTES.md), [`RELATORIO_APROVEITAMENTO_TAR_IA.md`](RELATORIO_APROVEITAMENTO_TAR_IA.md) | **HISTÓRICO** | Relatórios de ondas de desenvolvimento. |
| [`SECOES_2_A_6_OFICIAL.md`](SECOES_2_A_6_OFICIAL.md), [`REVISAO_E_PLANO_DE_EVOLUCAO.md`](REVISAO_E_PLANO_DE_EVOLUCAO.md), [`RELATORIO_CODIGO_LOCAL_ERRADO.md`](RELATORIO_CODIGO_LOCAL_ERRADO.md) | **HISTÓRICO** | Diagnósticos de momentos anteriores. |
| [`STATUS_ATUAL_E_RECURSOS_IMPLEMENTADOS.md`](STATUS_ATUAL_E_RECURSOS_IMPLEMENTADOS.md) | **OBSOLETO** | Superado pelo status consolidado. |
| `HISTORICO_DESENVOLVIMENTO_MARATONA_MEDIA.md`, `historico_auditoria_ia.tar.gz` | **HISTÓRICO** | Registro bruto das sessões multiagente. |
| [`../CHANGELOG.md`](../CHANGELOG.md) | **HISTÓRICO** | Gerado automaticamente, com números divergentes; não use como fonte de status. |

## Regra prática

1. Para **saber o que funciona**, leia `README.md` e `STATUS_ATUAL_CONSOLIDADO.md`.
2. Para **saber o que falta para dados reais**, leia a seção P0 do status e o
   P0.4 do `ROADMAP_V1.md`.
3. Para **executar o trabalho restante**, use `PLANO_DE_FINALIZACAO_V1.md`
   (fases 0–8, com decisões de escopo pendentes marcadas ⚖️).
4. Antes de citar um relatório antigo em uma decisão, confirme no código e nos
   testes — a suíte é a fonte executável de verdade.
