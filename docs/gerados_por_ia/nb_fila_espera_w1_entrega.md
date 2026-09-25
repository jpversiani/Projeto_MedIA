Now I have the full context: the API returns `FilaAcolhimentoOut[]` (with `classificacao_risco`, `data_hora_entrada`, `cidadao`, sinais vitais) from `/api/v1/fila/?status=AGUARDANDO_ATENDIMENTO`. Creating the ES Module:
Corrigindo um erro de digitação na inicialização do campo privado:
Validating the syntax with Node:
Node isn't available; running a structural consistency check on private fields instead:
O verificador sinalizou métodos privados (o regex só correspondia a campos). Refinando a verificação:
Falso positivo do meu regex: `async #executarCiclo()` tem modificador antes de `#`. Ajustando o padrão:
`backend/app/static/js/fila_espera.js` criado no repositório do projeto (`Projeto_MedIA`), servido como `/static/js/fila_espera.js` pelo mount do `main.py:48`.

**Classe `FilaEsperaPainel` (ES Module, campos/métodos privados, ~100% pt-BR):**

- **Polling adaptativo** — 2 s com pacientes `AGUARDANDO_ATENDIMENTO`, 10 s ocioso; reduz para 10 s com aba oculta (`document.hidden`) e aplica *backoff* progressivo (até 30 s) em falhas de rede consecutivas; requisições concorrentes abortadas via `AbortController` (`iniciar()`, `parar()`, `destruir()`).
- **Ordenação Manchester** — `VERMELHO > AMARELO > VERDE > AZUL`, desempate por `data_hora_entrada` ascendente (linhas 95-104), com cores Tailwind por risco (badge, barra lateral e fundo do cartão) e rótulo clínico (Emergência/Urgência/Pouco urgente/Não urgente).
- **Tempo de espera decorrido** — relógio interno de 1 s atualiza só as células `[data-tempo-espera]` (sem re-render completo) e pulsa em vermelho quando excede o limite do protocolo (15/60/120 min).
- **Badge "Chamando próximo"** — destaque animado (`animate-pulse` + anel azul) com nome e risco; `chamarProximo()` anuncia o topo da fila, callback opcional `aoChamar(item)` para integração e botão "Chamar de novo".
- **Som opcional (Web Audio API)** — "ding-dong" de dois tons (880 Hz + 660 Hz) sintetizado por `OscillatorNode`/`GainNode`, sem arquivos externos; ativado por `alternarSom()` (o gesto do usuário resume o `AudioContext`) com botão de toggle refletindo o estado.
- **Segurança/convenções** — dados dinâmicos renderizados via `textContent`/`replaceChildren` (anti-XSS), CNS/CPF e tipo de demanda exibidos conforme padrão SUS/APS, contador de espera e selo "Atualizado às HH:MM:SS".

Verificado: balanceamento de chaves/strings e os 25 membros privados declarados e usados (Node indisponível no ambiente; checagem estrutural feita em Python). Integração mínima:

```html
<div id="fila-espera-chamada"></div>
<div id="fila-espera-lista"></div>
<button id="fila-espera-som" type="button"></button>
<script type="module">
  import { FilaEsperaPainel } from "/static/js/fila_espera.js";
  new FilaEsperaPainel().iniciar();
</script>
```