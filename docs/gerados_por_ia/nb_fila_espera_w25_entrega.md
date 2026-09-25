The target file already exists with a complete implementation. Let me verify its syntax and conformance with the data contract.
O arquivo `backend/app/static/js/fila_espera.js` já existe completo (555 linhas) e foi validado — estrutura sintática balanceada e 100% dos requisitos atendidos.

**Conformidade verificada:**

| Requisito | Implementação |
|---|---|
| ES Module + classe | `export class FilaEsperaPainel` com campos privados `#` |
| Polling adaptativo | 2s ativo / 10s ocioso (`fila_espera.js:86-87`), com recuo em falhas e retomada imediata ao voltar à aba |
| Endpoint SUS | `GET /api/v1/fila/?status=AGUARDANDO_ATENDIMENTO` (contract match com `FilaAcolhimentoOut`) |
| Prioridade Manchester | `VERMELHO(0) > AMARELO(1) > VERDE(2) > AZUL(3)`, desempate por chegada (`fila_espera.js:238`) |
| Cores Tailwind | Paleta por risco (`fila_espera.js:33-67`) com limites de espera (0/15/60/120 min) |
| Tempo decorrido | Relógio de 1s via `data-papel='tempo-espera'` sem re-render total + alerta visual ao exceder limite |
| Badge "Chamando próximo" | `#renderizarChamada()` com anel de destaque no item chamado |
| Som opcional | "Ding-dong" de 2 tons via Web Audio API (`#tocarSomChamada()`), habilitado por gesto do usuário (resume do AudioContext suspenso) |

Também confere com o contrato de dados: `cidadao.nome_completo`, `cns`, `cpf` (padrão SUS/APS), `classificacao_risco`, `data_hora_entrada`, `motivo_acolhimento` — todos em pt-BR nos comentários e mensagens de UI.