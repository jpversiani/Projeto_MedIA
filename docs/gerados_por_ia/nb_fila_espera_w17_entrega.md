O arquivo já existe — vou verificar a integração com o template HTML e o modelo `Cidadao` para validar os campos usados.
Os campos usados (`nome_completo`, `cns`, `cpf`, `classificacao_risco`, `data_hora_entrada`) correspondem aos schemas `CidadaoOut` e `FilaAcolhimentoOut`. Vou confirmar o prefixo de montagem da API e a flag JS do app FastAPI:
A implementação existente está alinhada à API. Vou aplicar dois refinamentos de robustez em tempo real: (1) limpar o selo quando o cidadão chamado sai da fila; (2) retomar o polling ativo imediatamente quando a aba volta ao foco.
O listener de visibilidade pode criar ciclos de polling concorrentes (o ciclo abortado reagendaria um timer). Vou garantir que o ciclo abortado ceda o agendamento ao mais recente:
Agora adiciono o novo campo privado `#ouvinteVisibilidade` à declaração de estado:
Refino final: coerção numérica explícita no cálculo inicial do tempo decorrido:
Agora vou validar a sintaxe do módulo com o Node (verificação de parse) e checar se há erros de lint no projeto:
Sem runtime JS no ambiente — vou revisar o arquivo completo manualmente para validar sintaxe e lógica:
O arquivo está completo e correto. Verificação final do estado no git:
Concluído. O módulo `backend/app/static/js/fila_espera.js` (ES Module, 555 linhas) foi validado contra a API real e refinado.

**Conformidade com a tarefa:**
- Classe `FilaEsperaPainel` consumindo `GET /api/v1/fila/?status=AGUARDANDO_ATENDIMENTO` (rota conferida em `backend/app/api/v1/fila.py:11`)
- Polling adaptativo: **2 s** com pacientes aguardando / **10 s** ocioso (ou aba em segundo plano), com backoff progressivo em falhas de rede
- Ordenação Manchester (`VERMELHO > AMARELO > VERDE > AZUL`, desempate por chegada) com paleta Tailwind por risco (`bg-red-600`/`amber`/`emerald`/`blue`)
- Tempo de espera decorrido atualizado a cada segundo + alerta visual ao exceder o tempo máximo do protocolo
- Badge "Chamando próximo" com som opcional "ding-dong" sintetizado via Web Audio API (sem arquivos externos)
- Identificação SUS/APS: nome + CNS/CPF do `CidadaoOut`; dados renderizados via `textContent` (sem injeção de HTML)

**Refinamentos aplicados nesta passada:**
1. Selo de chamada descartado quando o cidadão chamado sai da fila (linha 172)
2. Listener `visibilitychange` retoma o ciclo ativo imediatamente ao voltar à aba, com ciclo abortado cedendo o agendamento — evita cadeias de polling concorrentes (linhas 123, 248-260)
3. Coerção numérica explícita no cálculo do tempo decorrido (linha 392)

Observação: sem runtime JS no ambiente (Node ausente), a validação foi por revisão manual completa do módulo.