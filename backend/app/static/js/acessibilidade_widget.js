/**
 * acessibilidade_widget.js — Camada de Acessibilidade (WCAG) para Pacientes
 * ==========================================================================
 * Projeto MedIA — SUS / Atenção Primária à Saúde (APS)
 *
 * Módulo responsável pela camada de acessibilidade das interfaces destinadas
 * ao cidadão, alinhada às diretrizes WCAG 2.1 (nível AA) e ao e-MAG
 * (Padrão de Acessibilidade do Governo Federal brasileiro):
 *
 *   1. Widget flutuante de ajustes de acessibilidade (sempre disponível,
 *      operável por teclado e com rótulos acessíveis);
 *   2. Aumento de fonte de 100% até 200%, em passos de 10%
 *      (WCAG 1.4.4 — Redimensionamento de texto), aplicado em <html> para
 *      escalar todo conteúdo baseado em rem (padrão do Tailwind CSS);
 *   3. Modo alto contraste combinando `filter` em CSS (raiz do documento)
 *      e classes utilitárias com overrides para as cores mais comuns do
 *      Tailwind (WCAG 1.4.11 — Contraste não textual);
 *   4. Atalhos de navegação por teclado ("skip links") para contornar
 *      blocos repetitivos (WCAG 2.4.1 — Blocos de bypass);
 *   5. Região `aria-live` para a chamada de sala da fila de espera
 *      (WCAG 4.1.3 — Mensagens de status), com narração opcional;
 *   6. Leitura do texto do Termo de Consentimento via SpeechSynthesis API
 *      para pacientes com baixa visão (WCAG 1.4.5 / 3.3.2), com controle
 *      de leitura, pausa e parada.
 *
 * Integração com a Fila de Espera (backend/app/static/js/fila_espera.js):
 *   Ao chamar o próximo cidadão, o painel pode despachar um evento global:
 *     window.dispatchEvent(new CustomEvent('media:chamada-sala', {
 *       detail: { nome: 'Maria', sala: 'Sala 3', profissional: 'Enfermeira Ana' },
 *     }));
 *   Este módulo escuta o evento e anuncia em `aria-live` (e narra, se habilitado).
 *
 * Exemplo de uso (ES Module):
 *   import { WidgetAcessibilidade } from '/static/js/acessibilidade_widget.js';
 *   const widget = new WidgetAcessibilidade();
 *   widget.iniciar();
 *   // Encerramento (SPA): widget.destruir();
 *
 * O módulo não possui efeitos colaterais na importação (import seguro).
 */

'use strict';

/* ==========================================================================
 * Constantes do módulo
 * ========================================================================== */

/** Versão do contrato de armazenamento das preferências (alterar ao migrar). */
const VERSAO_ARMAZENAMENTO = 'v1';

/** Chave padrão em localStorage para persistir as preferências do cidadão. */
export const CHAVE_ARMAZENAMENTO = `media:acessibilidade:${VERSAO_ARMAZENAMENTO}`;

/** Escala mínima de fonte (%) — base tipográfica do documento (WCAG 1.4.4). */
export const ESCALA_FONTE_MINIMA = 100;

/** Escala máxima de fonte (%) — requisito WCAG 1.4.4 (200% sem perda de conteúdo). */
export const ESCALA_FONTE_MAXIMA = 200;

/** Passo de incremento/decremento da escala de fonte (%). */
export const PASSO_ESCALA_FONTE = 10;

/** Escala padrão de fonte (%) — 100% não altera a apresentação original. */
export const ESCALA_FONTE_PADRAO = 100;

/** Limite de caracteres por bloco de fala (contorna limite do Chrome na TTS). */
const LIMITE_BLOCO_FALA = 220;

/** Nome do evento DOM de chamada de sala publicado pela Fila de Espera. */
export const EVENTO_CHAMADA_SALA = 'media:chamada-sala';

/** Estado inicial das preferências do usuário (objeto imutável). */
const ESTADO_PADRAO = Object.freeze({
  escalaFonte: ESCALA_FONTE_PADRAO,
  altoContraste: false,
  narrarChamadas: true,
  velocidadeLeitura: 1,
});

/** Rótulos dos atalhos de teclado exibidos no painel (padrão e-MAG/gov.br). */
const ATALHOS_TECLADO = Object.freeze([
  { tecla: 'Alt + A', descricao: 'Abrir ou fechar o painel de acessibilidade' },
  { tecla: 'Alt + 1', descricao: 'Ativar ou desativar o alto contraste' },
  { tecla: 'Alt + 2', descricao: 'Aumentar o tamanho da fonte' },
  { tecla: 'Alt + 3', descricao: 'Diminuir o tamanho da fonte' },
  { tecla: 'Alt + 0', descricao: 'Redefinir o tamanho da fonte para 100%' },
  { tecla: 'Alt + 4', descricao: 'Ler ou pausar a leitura do termo de consentimento' },
  { tecla: 'Alt + 5', descricao: 'Parar a leitura do termo de consentimento' },
  { tecla: 'Alt + C', descricao: 'Ir para o conteúdo principal' },
  { tecla: 'Alt + M', descricao: 'Ir para o menu de navegação' },
]);

/** Seletores padrão de conteúdo do termo de consentimento (ordem de prioridade). */
const SELETORES_TERMO_PADRAO = Object.freeze([
  '[data-termo-texto]',
  '#termo-consentimento',
  '#texto-termo',
  '#modal-consentimento .conteudo-termo',
]);

/* ==========================================================================
 * Estilos injetados (Tailwind não cobre: sr-only custom, skip links, alto contraste)
 * ========================================================================== */

/**
 * CSS injetado uma única vez pelo widget.
 * - Skip links visíveis apenas no foco (padrão gov.br: barra azul, texto branco);
 * - Regiões `aria-live` ocultas visualmente, mas perceptíveis por leitores de tela;
 * - Alto contraste: `filter` na raiz + classes com overrides das utilidades
 *   Tailwind mais frequentes (WCAG 1.4.11);
 * - Respeita `prefers-reduced-motion` (WCAG 2.3.3) e `forced-colors`.
 */
const ESTILOS_ACESSIBILIDADE = `
/* ---------- Utilitários visuais do módulo ---------- */
.media-sr-only {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: -1px !important;
  overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important;
  white-space: nowrap !important;
  border: 0 !important;
}

/* ---------- Skip links (WCAG 2.4.1) ---------- */
#media-ac-skip {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 2147483000;
}
#media-ac-skip a {
  position: absolute;
  transform: translateY(-200%);
  display: inline-block;
  background: #0b3fae;
  color: #ffffff;
  font-weight: 700;
  font-size: 1rem;
  padding: 0.75rem 1.25rem;
  border-radius: 0 0 0.5rem 0;
  text-decoration: underline;
  transition: transform 120ms ease-in;
  outline-offset: 2px;
}
#media-ac-skip a:focus {
  transform: translateY(0);
}
#media-ac-skip a + a { margin-left: 0; }

/* ---------- Alto contraste (WCAG 1.4.11) ---------- */
/* Filtro de contraste aplicado à raiz — beneficia mídias e conteúdo herdado. */
html.media-alto-contraste {
  filter: contrast(1.35) saturate(1.15);
}
/* Overrides explícitos das utilidades Tailwind mais comuns nas telas do MedIA. */
html.media-alto-contraste body {
  background-color: #000000 !important;
  color: #ffffff !important;
}
html.media-alto-contraste .bg-white,
html.media-alto-contraste .bg-slate-50,
html.media-alto-contraste .bg-slate-100,
html.media-alto-contraste .bg-gray-50,
html.media-alto-contraste .bg-gray-100,
html.media-alto-contraste .bg-blue-50,
html.media-alto-contraste .bg-emerald-50,
html.media-alto-contraste .bg-red-50,
html.media-alto-contraste .bg-amber-50 {
  background-color: #000000 !important;
}
html.media-alto-contraste .text-slate-400,
html.media-alto-contraste .text-slate-500,
html.media-alto-contraste .text-slate-600,
html.media-alto-contraste .text-slate-700,
html.media-alto-contraste .text-slate-900,
html.media-alto-contraste .text-gray-400,
html.media-alto-contraste .text-gray-500,
html.media-alto-contraste .text-gray-600,
html.media-alto-contraste .text-gray-700,
html.media-alto-contraste .text-gray-900,
html.media-alto-contraste .text-blue-700,
html.media-alto-contraste .text-emerald-700,
html.media-alto-contraste .text-red-700,
html.media-alto-contraste .text-amber-700 {
  color: #ffffff !important;
}
html.media-alto-contraste a {
  color: #ffd700 !important;
  text-decoration: underline !important;
}
html.media-alto-contraste .shadow,
html.media-alto-contraste .shadow-sm,
html.media-alto-contraste .shadow-md,
html.media-alto-contraste .shadow-lg,
html.media-alto-contraste .shadow-xl,
html.media-alto-contraste .shadow-2xl {
  box-shadow: none !important;
}
html.media-alto-contraste .border-slate-200,
html.media-alto-contraste .border-slate-300,
html.media-alto-contraste .border-gray-200,
html.media-alto-contraste .border-gray-300 {
  border-color: #ffffff !important;
}
html.media-alto-contraste .bg-blue-600,
html.media-alto-contraste .bg-blue-700,
html.media-alto-contraste .bg-emerald-600,
html.media-alto-contraste .bg-red-600,
html.media-alto-contraste .bg-amber-500 {
  background-color: #0b3fae !important;
  color: #ffffff !important;
}

/* ---------- Aparência própria do widget (prioridade via ID) ---------- */
/* Regras com ID para sobreviver aos overrides genéricos em alto contraste. */
#media-widget-acessibilidade {
  position: fixed;
  z-index: 2147482000;
  right: 1.5rem;
  bottom: 1.5rem;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
#media-widget-acessibilidade[data-posicao="inferior-esquerda"] {
  right: auto;
  left: 1.5rem;
}
#media-widget-acessibilidade button,
#media-widget-acessibilidade [role="switch"] {
  cursor: pointer;
}
#media-widget-acessibilidade .media-ac-botao {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  font-weight: 600;
  font-size: 0.875rem;
  line-height: 1.25rem;
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid #cbd5e1;
  background-color: #ffffff;
  color: #0f172a;
  min-width: 2.75rem;
  min-height: 2.75rem; /* Alvo tátil >= 44px (WCAG 2.5.8) */
}
#media-widget-acessibilidade .media-ac-botao:hover:not(:disabled) {
  background-color: #eff6ff;
  border-color: #0b3fae;
}
#media-widget-acessibilidade .media-ac-botao:focus-visible {
  outline: 3px solid #1d4ed8;
  outline-offset: 2px;
}
#media-widget-acessibilidade .media-ac-botao:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
#media-widget-acessibilidade .media-ac-botao-primario {
  background-color: #0b3fae;
  border-color: #0b3fae;
  color: #ffffff;
}
#media-widget-acessibilidade .media-ac-botao-primario:hover:not(:disabled) {
  background-color: #092f7f;
}
/* Interruptor (role="switch") em dois estados visuais inequívocos. */
#media-widget-acessibilidade .media-ac-chave {
  position: relative;
  width: 3.5rem;
  height: 1.75rem;
  border-radius: 9999px;
  border: 2px solid #334155;
  background-color: #e2e8f0;
  flex: none;
}
#media-widget-acessibilidade .media-ac-chave[aria-checked="true"] {
  background-color: #0b3fae;
  border-color: #0b3fae;
}
#media-widget-acessibilidade .media-ac-chave::after {
  content: "";
  position: absolute;
  top: 50%;
  left: 0.25rem;
  width: 1.25rem;
  height: 1.25rem;
  transform: translateY(-50%);
  border-radius: 9999px;
  background-color: #ffffff;
  transition: left 120ms ease-in;
}
#media-widget-acessibilidade .media-ac-chave[aria-checked="true"]::after {
  left: calc(100% - 1.5rem);
  background-color: #ffd700;
}
/* Em alto contraste, o painel mantém legibilidade própria (fundo preto/branco). */
html.media-alto-contraste #media-widget-acessibilidade .media-ac-painel {
  background-color: #000000 !important;
  color: #ffffff !important;
  border: 2px solid #ffd700 !important;
}
html.media-alto-contraste #media-widget-acessibilidade .media-ac-botao {
  background-color: #000000 !important;
  color: #ffd700 !important;
  border-color: #ffd700 !important;
}
html.media-alto-contraste #media-widget-acessibilidade .media-ac-botao-primario {
  background-color: #ffd700 !important;
  color: #000000 !important;
}
html.media-alto-contraste #media-widget-acessibilidade kbd {
  background-color: #000000 !important;
  color: #ffd700 !important;
  border-color: #ffd700 !important;
}

/* ---------- Movimento reduzido (WCAG 2.3.3) ---------- */
@media (prefers-reduced-motion: reduce) {
  #media-ac-skip a,
  #media-widget-acessibilidade .media-ac-chave::after {
    transition: none;
  }
}
`;

/* ==========================================================================
 * Marcação do widget (estática — dados dinâmicos sempre via textContent)
 * ========================================================================== */

const HTML_PAINEL = `
  <section
    data-painel
    class="media-ac-painel hidden w-80 max-w-[calc(100vw-3rem)] rounded-xl border border-slate-300 bg-white p-4 shadow-2xl"
    role="dialog"
    aria-modal="false"
    aria-labelledby="media-ac-titulo"
  >
    <div class="mb-3 flex items-start justify-between gap-2">
      <h2 id="media-ac-titulo" class="text-base font-bold text-slate-900">
        Acessibilidade
      </h2>
      <button
        data-fechar
        type="button"
        class="media-ac-botao"
        aria-label="Fechar painel de acessibilidade"
        title="Fechar (Esc)"
      >✕</button>
    </div>

    <!-- Tamanho da fonte (WCAG 1.4.4) -->
    <fieldset class="mb-3 rounded-lg border border-slate-200 p-3">
      <legend class="px-1 text-sm font-semibold text-slate-700">Tamanho da fonte</legend>
      <div class="flex items-center justify-center gap-2">
        <button data-fonte-menos type="button" class="media-ac-botao"
          aria-label="Diminuir tamanho da fonte em 10 por cento (Alt + 3)">A−</button>
        <output data-fonte-valor class="min-w-14 text-center text-sm font-bold text-slate-900"
          aria-live="polite" aria-atomic="true">100%</output>
        <button data-fonte-mais type="button" class="media-ac-botao"
          aria-label="Aumentar tamanho da fonte em 10 por cento (Alt + 2)">A+</button>
        <button data-fonte-reset type="button" class="media-ac-botao"
          aria-label="Redefinir tamanho da fonte para o padrão (Alt + 0)">Padrão</button>
      </div>
    </fieldset>

    <!-- Alto contraste (WCAG 1.4.11) -->
    <div class="mb-3 flex items-center justify-between gap-3 rounded-lg border border-slate-200 p-3">
      <span class="text-sm font-semibold text-slate-700">Alto contraste</span>
      <button data-contraste type="button" role="switch" aria-checked="false"
        class="media-ac-chave" aria-label="Ativar ou desativar alto contraste (Alt + 1)"></button>
    </div>

    <!-- Leitura do termo de consentimento (SpeechSynthesis) -->
    <fieldset class="mb-3 rounded-lg border border-slate-200 p-3">
      <legend class="px-1 text-sm font-semibold text-slate-700">Ouvir o termo de consentimento</legend>
      <div class="flex items-center justify-center gap-2">
        <button data-termo-ler type="button" class="media-ac-botao media-ac-botao-primario"
          aria-label="Ler o termo de consentimento em voz alta (Alt + 4)">▶ Ler</button>
        <button data-termo-pausar type="button" class="media-ac-botao" disabled
          aria-label="Pausar leitura do termo (Alt + 4)">⏸ Pausar</button>
        <button data-termo-parar type="button" class="media-ac-botao" disabled
          aria-label="Parar leitura do termo (Alt + 5)">⏹ Parar</button>
      </div>
    </fieldset>

    <!-- Narração da chamada de sala (aria-live + TTS) -->
    <div class="mb-3 flex items-center justify-between gap-3 rounded-lg border border-slate-200 p-3">
      <span class="text-sm font-semibold text-slate-700">Narrar chamadas de sala</span>
      <button data-narrar type="button" role="switch" aria-checked="true"
        class="media-ac-chave" aria-label="Ativar ou desativar narração da chamada de sala"></button>
    </div>

    <!-- Atalhos de navegação por teclado (WCAG 2.4.1) -->
    <nav aria-labelledby="media-ac-skip-titulo" class="mb-3 rounded-lg border border-slate-200 p-3">
      <h3 id="media-ac-skip-titulo" class="mb-2 text-sm font-semibold text-slate-700">
        Navegação rápida
      </h3>
      <div class="flex flex-col gap-2">
        <button data-ir-conteudo type="button" class="media-ac-botao w-full text-left"
          aria-label="Ir para o conteúdo principal (Alt + C)">Ir para o conteúdo</button>
        <button data-ir-menu type="button" class="media-ac-botao w-full text-left"
          aria-label="Ir para o menu de navegação (Alt + M)">Ir para o menu</button>
      </div>
    </nav>

    <!-- Lista de atalhos de teclado -->
    <details class="rounded-lg border border-slate-200 p-3">
      <summary class="cursor-pointer text-sm font-semibold text-slate-700">
        Atalhos de teclado
      </summary>
      <ul data-lista-atalhos class="mt-2 space-y-1"></ul>
    </details>

    <!-- Região de status do próprio painel (WCAG 4.1.3) -->
    <p data-status class="media-sr-only" aria-live="polite" role="status"></p>
  </section>
`;

const HTML_BOTAO_FLUTUANTE = `
  <button
    data-flutuante
    type="button"
    class="media-ac-botao rounded-full p-0 shadow-2xl"
    style="width:3.5rem;height:3.5rem;min-width:3.5rem;min-height:3.5rem;"
    aria-haspopup="dialog"
    aria-expanded="false"
    aria-controls="media-ac-painel"
    aria-label="Abrir painel de acessibilidade (Alt + A)"
    title="Acessibilidade (Alt + A)"
  >
    <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor" aria-hidden="true" focusable="false">
      <circle cx="12" cy="4.5" r="2.1"></circle>
      <path d="M12 7.6c-.6 0-4.9-.5-6.3-.7a1 1 0 0 0-1.2.9 1 1 0 0 0 .9 1.1l4.4.6v3l-2.2 6.6a1.1 1.1 0 0 0 .7 1.4 1.1 1.1 0 0 0 1.4-.7l1.9-5.4h.8l1.9 5.4a1.1 1.1 0 0 0 1.4.7 1.1 1.1 0 0 0 .7-1.4L14.2 12.4v-3l4.4-.6a1 1 0 0 0 .9-1.1 1 1 0 0 0-1.2-.9c-1.4.2-5.7.7-6.3.8z"></path>
    </svg>
  </button>
`;

/* ==========================================================================
 * Utilidades internas
 * ========================================================================== */

/** Armazenamento seguro de preferências (degrada silenciosamente em modo privado). */
const ArmazenamentoPreferencias = Object.freeze({
  /** @returns {object|null} Preferências salvas ou `null` se indisponíveis. */
  ler() {
    try {
      const bruto = localStorage.getItem(CHAVE_ARMAZENAMENTO);
      return bruto ? JSON.parse(bruto) : null;
    } catch {
      return null;
    }
  },
  /** @param {object} preferencias Preferências a persistir. */
  salvar(preferencias) {
    try {
      localStorage.setItem(CHAVE_ARMAZENAMENTO, JSON.stringify(preferencias));
    } catch {
      /* Modo privado/quota cheia: preferências apenas em memória. */
    }
  },
});

/**
 * Limita um valor numérico entre mínimo e máximo.
 * @param {number} valor Valor de entrada.
 * @param {number} minimo Limite inferior.
 * @param {number} maximo Limite superior.
 * @returns {number} Valor limitado.
 */
function limitar(valor, minimo, maximo) {
  return Math.min(maximo, Math.max(minimo, valor));
}

/**
 * Seleciona a primeira voz pt-BR disponível (preferência: pt-BR → pt-*).
 * @returns {SpeechSynthesisVoice|null} Voz selecionada, se existir.
 */
function selecionarVozPtBr() {
  if (!('speechSynthesis' in window)) return null;
  const vozes = window.speechSynthesis.getVoices();
  return (
    vozes.find((v) => v.lang?.replace('_', '-').toLowerCase() === 'pt-br') ||
    vozes.find((v) => v.lang?.toLowerCase().startsWith('pt')) ||
    null
  );
}

/**
 * Divide um texto longo em blocos curtos (respeitando pontuação), contornando
 * o limite prático de duração de enunciados na TTS do Chromium.
 * @param {string} texto Texto integral a narrar.
 * @returns {string[]} Lista de blocos (≤ LIMITE_BLOCO_FALA caracteres).
 */
function dividirEmBlocos(texto) {
  const frases = texto
    .replace(/\s+/g, ' ')
    .split(/(?<=[.!?;:…])\s+/)
    .map((f) => f.trim())
    .filter(Boolean);
  const blocos = [];
  let atual = '';
  for (const frase of frases) {
    if ((atual + ' ' + frase).trim().length <= LIMITE_BLOCO_FALA) {
      atual = (atual ? atual + ' ' : '') + frase;
    } else {
      if (atual) blocos.push(atual);
      // Frase singular maior que o limite: fatia agressivamente (sem cortar palavras).
      atual = frase;
      while (atual.length > LIMITE_BLOCO_FALA) {
        let corte = atual.lastIndexOf(' ', LIMITE_BLOCO_FALA);
        if (corte <= 0) corte = LIMITE_BLOCO_FALA;
        blocos.push(atual.slice(0, corte).trim());
        atual = atual.slice(corte).trim();
      }
    }
  }
  if (atual) blocos.push(atual);
  return blocos;
}

/* ==========================================================================
 * Leitor de Termo (SpeechSynthesis API)
 * ========================================================================== */

/**
 * Leitor de Termo de Consentimento via SpeechSynthesis API.
 *
 * Divide o texto do termo em blocos curtos (compatibilidade Chromium),
 * seleciona voz pt-BR automaticamente e expõe controle Ler/Pausar/Parar.
 * Sem suporte à API, opera em modo degradado (estado indisponível).
 */
export class LeitorTermo {
  /**
   * @param {object} [opcoes] Opções de configuração.
   * @param {number} [opcoes.velocidade] Velocidade de fala (0,5 a 2; padrão 1).
   * @param {(estado: string) => void} [opcoes.aoMudarEstado] Notificação de mudança
   *        de estado: 'indisponivel' | 'parado' | 'lendo' | 'pausado' | 'erro'.
   */
  constructor(opcoes = {}) {
    this._velocidade = limitar(opcoes.velocidade ?? 1, 0.5, 2);
    this._aoMudarEstado = opcoes.aoMudarEstado ?? null;
    this._blocos = [];
    this._indice = 0;
    this._estado = 'parado';
    this._pausadoPeloUsuario = false;

    this._disponivel = 'speechSynthesis' in window;
    if (!this._disponivel) {
      this._notificarEstado('indisponivel');
      return;
    }

    /* Vozes podem carregar de forma assíncrona (Chromium). */
    if (window.speechSynthesis.getVoices().length === 0) {
      window.speechSynthesis.addEventListener('voiceschanged', () => {}, { once: true });
    }

    /* Evita voz "fantasma" após navegar/recarregar a página (bug do Chromium). */
    window.addEventListener('beforeunload', () => window.speechSynthesis.cancel());
  }

  /** @returns {string} Estado atual da leitura. */
  get estado() {
    return this._estado;
  }

  /** @param {number} velocidade Nova velocidade (0,5 a 2). Aplica na próxima leitura. */
  definirVelocidade(velocidade) {
    this._velocidade = limitar(velocidade, 0.5, 2);
  }

  /**
   * Lê um texto em voz alta, ou o conteúdo textual do termo na página.
   * @param {string|{elemento?: Element, seletor?: string[]}} fonte Texto direto,
   *        elemento DOM ou lista de seletores CSS para localizar o termo.
   * @returns {boolean} `true` se a leitura foi iniciada.
   */
  ler(fonte) {
    if (!this._disponivel) return false;
    const texto = this._extrairTexto(fonte);
    if (!texto) return false;

    this.parar();
    this._blocos = dividirEmBlocos(texto);
    this._indice = 0;
    this._pausadoPeloUsuario = false;
    this._falarBlocoAtual();
    return true;
  }

  /** Pausa a leitura em andamento. */
  pausar() {
    if (!this._disponivel || this._estado !== 'lendo') return;
    this._pausadoPeloUsuario = true;
    window.speechSynthesis.pause();
    this._notificarEstado('pausado');
  }

  /** Retoma a leitura pausada. */
  retomar() {
    if (!this._disponivel || this._estado !== 'pausado') return;
    this._pausadoPeloUsuario = false;
    window.speechSynthesis.resume();
    this._notificarEstado('lendo');
  }

  /** Interrompe a leitura e descarta a fila. */
  parar() {
    if (!this._disponivel) return;
    window.speechSynthesis.cancel();
    this._blocos = [];
    this._indice = 0;
    this._notificarEstado('parado');
  }

  /**
   * Extrai o texto da fonte informada (string, elemento ou seletores).
   * @private
   */
  _extrairTexto(fonte) {
    if (typeof fonte === 'string') return fonte.trim();
    if (fonte?.elemento) return (fonte.elemento.textContent || '').trim();
    const seletores = fonte?.seletor ?? SELETORES_TERMO_PADRAO;
    for (const seletor of seletores) {
      const elemento = document.querySelector(seletor);
      if (elemento) return (elemento.textContent || '').trim();
    }
    return '';
  }

  /** Enuncia o bloco corrente e agenda o próximo ao término. @private */
  _falarBlocoAtual() {
    const bloco = this._blocos[this._indice];
    if (bloco === undefined) {
      this._notificarEstado('parado');
      return;
    }
    const enunciado = new SpeechSynthesisUtterance(bloco);
    const voz = selecionarVozPtBr();
    if (voz) enunciado.voice = voz;
    enunciado.lang = voz?.lang || 'pt-BR';
    enunciado.rate = this._velocidade;
    enunciado.onend = () => {
      if (this._pausadoPeloUsuario) return;
      this._indice += 1;
      if (this._indice < this._blocos.length) this._falarBlocoAtual();
      else this._notificarEstado('parado');
    };
    enunciado.onerror = () => this._notificarEstado('erro');
    window.speechSynthesis.speak(enunciado);
    this._notificarEstado('lendo');
  }

  /** Emite mudança de estado ao observador registrado. @private */
  _notificarEstado(estado) {
    this._estado = estado;
    this._aoMudarEstado?.(estado);
  }
}

/* ==========================================================================
 * Região viva — chamada de sala (WCAG 4.1.3)
 * ========================================================================== */

/**
 * Garante a existência da região viva singleton para chamadas de sala.
 * @returns {HTMLElement} Elemento `role="status"` (polite) ou `alert` (assertive).
 * @private
 */
function garantirRegiaoViva(assertivo) {
  const id = assertivo ? 'media-regiao-viva-assertiva' : 'media-regiao-viva-polida';
  let regiao = document.getElementById(id);
  if (!regiao) {
    regiao = document.createElement(assertivo ? 'div' : 'output');
    regiao.id = id;
    regiao.className = 'media-sr-only';
    if (assertivo) {
      regiao.setAttribute('role', 'alert');
      regiao.setAttribute('aria-live', 'assertive');
    } else {
      regiao.setAttribute('aria-live', 'polite');
    }
    regiao.setAttribute('aria-atomic', 'true');
    document.body.appendChild(regiao);
  }
  return regiao;
}

/**
 * Formata a mensagem de chamada de sala conforme o protocolo SUS/APS.
 * @param {object} detalhes Dados da chamada.
 * @param {string} detalhes.nome Nome do cidadão chamado.
 * @param {string} detalhes.sala Sala/consultório de destino.
 * @param {string} [detalhes.profissional] Profissional que realizará o atendimento.
 * @returns {string} Mensagem completa para exibição e narração.
 */
export function formatarMensagemChamada({ nome, sala, profissional }) {
  let mensagem = `Atenção, ${nome}! Sua vez chegou. Por favor, dirija-se à ${sala}`;
  if (profissional) mensagem += `, para atendimento com ${profissional}`;
  return `${mensagem}.`;
}

/**
 * Anuncia a chamada de sala na região `aria-live` e, opcionalmente, narra em voz alta.
 * Compatível com `fila_espera.js` (evento `media:chamada-sala`).
 * @param {object} detalhes Dados da chamada ({ nome, sala, profissional? }).
 * @param {object} [opcoes] Opções de anúncio.
 * @param {boolean} [opcoes.assertivo=true] Usa `role="alert"`/assertive para urgência.
 * @param {boolean} [opcoes.falar=true] Narra a mensagem via SpeechSynthesis.
 * @param {number} [opcoes.velocidade=1] Velocidade da narração (0,5 a 2).
 * @returns {string|null} Mensagem anunciada ou `null` se os dados forem inválidos.
 */
export function anunciarChamadaSala(detalhes, opcoes = {}) {
  const { assertivo = true, falar = true, velocidade = 1 } = opcoes;
  if (!detalhes?.nome || !detalhes?.sala) return null;

  const mensagem = formatarMensagemChamada(detalhes);
  const regiao = garantirRegiaoViva(assertivo);
  regiao.textContent = '';

  /* Microtask: garante que leitores de tela percebam a alteração de conteúdo. */
  window.setTimeout(() => {
    regiao.textContent = mensagem;
  }, 50);

  if (falar && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const enunciado = new SpeechSynthesisUtterance(mensagem);
    const voz = selecionarVozPtBr();
    if (voz) enunciado.voice = voz;
    enunciado.lang = voz?.lang || 'pt-BR';
    enunciado.rate = limitar(velocidade, 0.5, 2);
    window.speechSynthesis.speak(enunciado);
  }
  return mensagem;
}

/**
 * Escuta os eventos de chamada de sala publicados pela Fila de Espera.
 * @param {object} [opcoes] Opções repassadas a `anunciarChamadaSala`.
 * @returns {() => void} Função de limpeza (remove o ouvinte).
 */
export function escutarChamadasDeSala(opcoes = {}) {
  const ouvinte = (evento) => anunciarChamadaSala(evento.detail, opcoes);
  window.addEventListener(EVENTO_CHAMADA_SALA, ouvinte);
  return () => window.removeEventListener(EVENTO_CHAMADA_SALA, ouvinte);
}

/* ==========================================================================
 * Widget de acessibilidade
 * ========================================================================== */

/**
 * Widget flutuante de acessibilidade para telas do cidadão (paciente).
 *
 * Injeta na página: botão flutuante, painel de ajustes, skip links e as
 * regiões vivas. Persiste as preferências em `localStorage` e reaplica
 * automaticamente na próxima visita. Respeita `prefers-contrast: more`
 * como sugestão inicial quando não há preferência salva.
 */
export class WidgetAcessibilidade {
  /**
   * @param {object} [opcoes] Opções de configuração.
   * @param {string[]} [opcoes.seletoresConteudo] Seletores do conteúdo principal.
   * @param {string[]} [opcoes.seletoresMenu] Seletores do menu de navegação.
   * @param {string} [opcoes.idPainel] ID do painel (para `aria-controls`).
   * @param {string} [opcoes.posicao] Posição do widget: 'inferior-direita' | 'inferior-esquerda'.
   * @param {boolean} [opcoes.escutarChamadas] Habilita a escuta de `media:chamada-sala`.
   * @param {string} [opcoes.seletoresTermo] Lista de seletores CSS do texto do termo.
   * @param {(preferencias: object) => void} [opcoes.aoAplicarPreferencias] Callback após aplicar.
   */
  constructor(opcoes = {}) {
    this._opcoes = {
      seletoresConteudo: opcoes.seletoresConteudo ??
        ['main', '[role="main"]', '#conteudo-principal'],
      seletoresMenu: opcoes.seletoresMenu ??
        ['nav[aria-label]', 'nav', '[role="navigation"]', '#menu-principal'],
      idPainel: opcoes.idPainel ?? 'media-ac-painel',
      posicao: opcoes.posicao ?? 'inferior-direita',
      escutarChamadas: opcoes.escutarChamadas ?? true,
      seletoresTermo: opcoes.seletoresTermo ?? SELETORES_TERMO_PADRAO,
      aoAplicarPreferencias: opcoes.aoAplicarPreferencias ?? null,
    };

    this._estado = { ...ESTADO_PADRAO };
    this._iniciado = false;
    this._raiz = null;
    this._estilo = null;
    this._limparEscutaChamadas = null;

    this._leitor = new LeitorTermo({
      aoMudarEstado: (estado) => this._refletirEstadoLeitura(estado),
    });

    this._aoTeclar = this._aoTeclar.bind(this);
  }

  /* ------------------------- Ciclo de vida ------------------------- */

  /**
   * Inicializa o widget: injeta estilos, skip links, botão flutuante,
   * painel e região viva; aplica preferências salvas; registra atalhos.
   * Idempotente (chamadas repetidas não duplicam a interface).
   */
  iniciar() {
    if (this._iniciado) return;
    this._iniciarEstilos();
    this._iniciarEstrutura();
    this._iniciarPreferencias();
    this._registrarAtalhos();
    if (this._opcoes.escutarChamadas) this._registrarEscutaChamadas();
    this._iniciado = true;
  }

  /** (Re)registra o ouvinte de chamadas de sala com o estado atual da narração. @private */
  _registrarEscutaChamadas() {
    this._limparEscutaChamadas?.();
    this._limparEscutaChamadas = escutarChamadasDeSala({
      falar: this._estado.narrarChamadas,
      assertivo: true,
    });
  }

  /**
   * Encerra o widget: remove nós injetados, ouvintes e para a leitura.
   * Preferências salvas são preservadas.
   */
  destruir() {
    if (!this._iniciado) return;
    document.removeEventListener('keydown', this._aoTeclar);
    this._limparEscutaChamadas?.();
    this._leitor.parar();
    this._raiz?.remove();
    this._estilo?.remove();
    this._iniciado = false;
  }

  /** Monta estilos, raiz do widget e associa eventos da interface. @private */
  _iniciarEstilos() {
    if (!document.getElementById('media-ac-estilos')) {
      this._estilo = document.createElement('style');
      this._estilo.id = 'media-ac-estilos';
      this._estilo.textContent = ESTILOS_ACESSIBILIDADE;
      document.head.appendChild(this._estilo);
    }
  }

  /** Cria raiz (skip links + FAB + painel) e registra eventos. @private */
  _iniciarEstrutura() {
    this._raiz = document.createElement('div');
    this._raiz.id = 'media-widget-acessibilidade';
    this._raiz.dataset.posicao = this._opcoes.posicao;
    this._raiz.innerHTML = `
      <nav id="media-ac-skip" aria-label="Atalhos de navegação">
        <a href="#conteudo-principal" data-skip-conteudo>Pular para o conteúdo principal</a>
        <a href="#menu-principal" data-skip-menu>Pular para o menu de navegação</a>
      </nav>
      ${HTML_BOTAO_FLUTUANTE}
      ${HTML_PAINEL}
    `;
    document.body.prepend(this._raiz);

    /* IDs sincronizados com a marcação estática (aria-controls/aria-labelledby). */
    this._raiz.querySelector('[data-painel]').id = this._opcoes.idPainel;

    this._botaoFlutuante = this._raiz.querySelector('[data-flutuante]');
    this._painel = this._raiz.querySelector('[data-painel]');
    this._regiaoStatus = this._raiz.querySelector('[data-status]');

    this._botaoFlutuante.addEventListener('click', () => this.alternarPainel());
    this._raiz.querySelector('[data-fechar]').addEventListener('click', () => this.fecharPainel());
    this._raiz.querySelector('[data-fonte-mais]').addEventListener('click', () => this.aumentarFonte());
    this._raiz.querySelector('[data-fonte-menos]').addEventListener('click', () => this.diminuirFonte());
    this._raiz.querySelector('[data-fonte-reset]').addEventListener('click', () => this.redefinirFonte());
    this._raiz.querySelector('[data-contraste]').addEventListener('click', () => this.alternarContraste());
    this._raiz.querySelector('[data-narrar]').addEventListener('click', () => this.alternarNarracaoChamadas());
    this._raiz.querySelector('[data-termo-ler]').addEventListener('click', () => this.lerTermo());
    this._raiz.querySelector('[data-termo-pausar]').addEventListener('click', () => this._alternarPausaTermo());
    this._raiz.querySelector('[data-termo-parar]').addEventListener('click', () => this._leitor.parar());
    this._raiz.querySelector('[data-ir-conteudo]').addEventListener('click', () => this.irParaConteudo());
    this._raiz.querySelector('[data-ir-menu]').addEventListener('click', () => this.irParaMenu());

    /* Skip links visíveis no primeiro TAB (navegação por teclado). */
    this._raiz.querySelector('[data-skip-conteudo]').addEventListener('click', (e) => {
      e.preventDefault();
      this.irParaConteudo();
    });
    this._raiz.querySelector('[data-skip-menu]').addEventListener('click', (e) => {
      e.preventDefault();
      this.irParaMenu();
    });

    this._renderizarListaAtalhos();
  }

  /** Popula a lista de atalhos de teclado do painel. @private */
  _renderizarListaAtalhos() {
    const lista = this._raiz.querySelector('[data-lista-atalhos]');
    lista.textContent = '';
    for (const atalho of ATALHOS_TECLADO) {
      const item = document.createElement('li');
      item.className = 'flex items-center justify-between gap-2 text-xs text-slate-600';
      const tecla = document.createElement('kbd');
      tecla.className = 'rounded border border-slate-300 bg-slate-100 px-1.5 py-0.5 font-mono font-semibold text-slate-800';
      tecla.textContent = atalho.tecla;
      const descricao = document.createElement('span');
      descricao.textContent = atalho.descricao;
      item.append(tecla, descricao);
      lista.appendChild(item);
    }
  }

  /** Carrega preferências salvas e sugere alto contraste de `prefers-contrast`. @private */
  _iniciarPreferencias() {
    const salvas = ArmazenamentoPreferencias.ler();
    if (salvas) {
      this._estado.escalaFonte = limitar(
        Number(salvas.escalaFonte) || ESTADO_PADRAO.escalaFonte,
        ESCALA_FONTE_MINIMA,
        ESCALA_FONTE_MAXIMA,
      );
      this._estado.altoContraste = Boolean(salvas.altoContraste);
      this._estado.narrarChamadas = salvas.narrarChamadas !== false;
    } else if (window.matchMedia('(prefers-contrast: more)').matches) {
      /* Primeira visita com preferência do sistema operacional: respeitamos. */
      this._estado.altoContraste = true;
    }

    this._leitor.definirVelocidade(this._estado.velocidade ?? 1);
    this._aplicarPreferencias();
  }

  /** Aplica escala de fonte, contraste e refletem os controles no painel. @private */
  _aplicarPreferencias() {
    document.documentElement.style.fontSize = `${this._estado.escalaFonte}%`;
    document.documentElement.classList.toggle('media-alto-contraste', this._estado.altoContraste);

    this._raiz.querySelector('[data-fonte-valor]').textContent =
      `${this._estado.escalaFonte}%`;
    this._raiz.querySelector('[data-contraste]').setAttribute(
      'aria-checked',
      String(this._estado.altoContraste),
    );
    this._raiz.querySelector('[data-narrar]').setAttribute(
      'aria-checked',
      String(this._estado.narrarChamadas),
    );

    ArmazenamentoPreferencias.salvar(this._estado);
    this._opcoes.aoAplicarPreferencias?.({ ...this._estado });
  }

  /** Registra atalhos globais de teclado (padrão e-MAG/gov.br). @private */
  _registrarAtalhos() {
    document.addEventListener('keydown', this._aoTeclar);
  }

  /**
   * Trata atalhos de teclado globais do widget.
   * @private
   * @param {KeyboardEvent} evento Evento de tecla.
   */
  _aoTeclar(evento) {
    /* Esc fecha o painel independentemente do uso de modificadores. */
    if (evento.key === 'Escape' && !this._painelFechado()) {
      evento.preventDefault();
      this.fecharPainel();
      return;
    }
    if (!evento.altKey || evento.ctrlKey || evento.metaKey) return;

    const acoes = {
      a: () => this.alternarPainel(),
      1: () => this.alternarContraste(),
      2: () => this.aumentarFonte(),
      3: () => this.diminuirFonte(),
      0: () => this.redefinirFonte(),
      4: () => this.alternarLeituraTermo(),
      5: () => this._leitor.parar(),
      c: () => this.irParaConteudo(),
      m: () => this.irParaMenu(),
    };
    const acao = acoes[evento.key.toLowerCase()];
    if (!acao) return;

    evento.preventDefault();
    evento.stopPropagation();
    acao();
  }

  /* ------------------------- Painel flutuante ------------------------- */

  /** @returns {boolean} `true` quando o painel está fechado. @private */
  _painelFechado() {
    return !this._painel || this._painel.classList.contains('hidden');
  }

  /** Abre ou fecha o painel de acessibilidade (atalho Alt + A). */
  alternarPainel() {
    this._painelFechado() ? this.abrirPainel() : this.fecharPainel();
  }

  /** Abre o painel, foca o primeiro controle e anuncia o estado. */
  abrirPainel() {
    this._painel.classList.remove('hidden');
    this._botaoFlutuante.setAttribute('aria-expanded', 'true');
    this._botaoFlutuante.setAttribute(
      'aria-label', 'Fechar painel de acessibilidade (Alt + A)',
    );
    const primeiro = this._painel.querySelector('button:not([disabled])');
    primeiro?.focus();
    this._anunciarNoPainel('Painel de acessibilidade aberto.');
  }

  /** Fecha o painel e devolve o foco ao botão flutuante. */
  fecharPainel() {
    this._painel.classList.add('hidden');
    this._botaoFlutuante.setAttribute('aria-expanded', 'false');
    this._botaoFlutuante.setAttribute(
      'aria-label', 'Abrir painel de acessibilidade (Alt + A)',
    );
    this._botaoFlutuante.focus();
  }

  /** Emite mensagem na região de status do painel (WCAG 4.1.3). @private */
  _anunciarNoPainel(mensagem) {
    this._regiaoStatus.textContent = '';
    window.setTimeout(() => {
      this._regiaoStatus.textContent = mensagem;
    }, 50);
  }

  /* ------------------------- Tamanho da fonte (WCAG 1.4.4) ------------------------- */

  /** Aumenta a escala de fonte em 10% (máximo de 200%). */
  aumentarFonte() {
    if (this._estado.escalaFonte >= ESCALA_FONTE_MAXIMA) {
      this._anunciarNoPainel('Tamanho máximo já atingido (200%).');
      return;
    }
    this._estado.escalaFonte = limitar(
      this._estado.escalaFonte + PASSO_ESCALA_FONTE,
      ESCALA_FONTE_MINIMA,
      ESCALA_FONTE_MAXIMA,
    );
    this._aplicarPreferencias();
    this._anunciarNoPainel(
      `Tamanho da fonte aumentado para ${this._estado.escalaFonte} por cento.`,
    );
  }

  /** Diminui a escala de fonte em 10% (mínimo de 100%). */
  diminuirFonte() {
    if (this._estado.escalaFonte <= ESCALA_FONTE_MINIMA) {
      this._anunciarNoPainel('Tamanho mínimo já atingido (100%).');
      return;
    }
    this._estado.escalaFonte = limitar(
      this._estado.escalaFonte - PASSO_ESCALA_FONTE,
      ESCALA_FONTE_MINIMA,
      ESCALA_FONTE_MAXIMA,
    );
    this._aplicarPreferencias();
    this._anunciarNoPainel(
      `Tamanho da fonte reduzido para ${this._estado.escalaFonte} por cento.`,
    );
  }

  /** Redefine a escala de fonte para 100%. */
  redefinirFonte() {
    this._estado.escalaFonte = ESCALA_FONTE_PADRAO;
    this._aplicarPreferencias();
    this._anunciarNoPainel('Tamanho da fonte redefinido para o padrão.');
  }

  /* ------------------------- Alto contraste (WCAG 1.4.11) ------------------------- */

  /** Ativa ou desativa o modo de alto contraste (filter + classes). */
  alternarContraste() {
    this._estado.altoContraste = !this._estado.altoContraste;
    this._aplicarPreferencias();
    this._anunciarNoPainel(
      this._estado.altoContraste
        ? 'Alto contraste ativado.'
        : 'Alto contraste desativado.',
    );
  }

  /* ------------------------- Skip links (WCAG 2.4.1) ------------------------- */

  /**
   * Localiza o primeiro elemento correspondente à lista de seletores.
   * @param {string[]} seletores Lista de seletores CSS em ordem de prioridade.
   * @returns {HTMLElement|null} Elemento encontrado ou `null`.
   * @private
   */
  _localizar(seletores) {
    for (const seletor of seletores) {
      const alvo = document.querySelector(seletor);
      if (alvo) return alvo;
    }
    return null;
  }

  /** Move o foco/scroll para o conteúdo principal (Alt + C). */
  irParaConteudo() {
    this._navegarPara(
      this._localizar(this._opcoes.seletoresConteudo) ?? document.body,
      'Conteúdo principal.',
    );
  }

  /** Move o foco/scroll para o menu de navegação (Alt + M). */
  irParaMenu() {
    const alvo = this._localizar(this._opcoes.seletoresMenu);
    if (!alvo) {
      this._anunciarNoPainel('Nenhum menu de navegação encontrado nesta página.');
      return;
    }
    this._navegarPara(alvo, 'Menu de navegação.');
  }

  /**
   * Rola até o alvo, torna-o focável e move o foco (bypass de blocos).
   * @param {HTMLElement} alvo Elemento de destino.
   * @param {string} mensagem Mensagem anunciada no painel.
   * @private
   */
  _navegarPara(alvo, mensagem) {
    const tinhaTabindex = alvo.hasAttribute('tabindex');
    if (!tinhaTabindex) alvo.setAttribute('tabindex', '-1');
    alvo.scrollIntoView({ block: 'start', behavior: 'smooth' });
    alvo.focus({ preventScroll: true });
    if (!tinhaTabindex) {
      alvo.addEventListener(
        'blur',
        () => alvo.removeAttribute('tabindex'),
        { once: true },
      );
    }
    this._anunciarNoPainel(mensagem);
  }

  /* ------------------------- Termo via SpeechSynthesis ------------------------- */

  /** Inicia ou pausa/retoma a leitura do termo (Alt + 4). */
  alternarLeituraTermo() {
    if (this._leitor.estado === 'lendo') {
      this._leitor.pausar();
      return;
    }
    if (this._leitor.estado === 'pausado') {
      this._leitor.retomar();
      return;
    }
    const iniciou = this._leitor.ler({ seletor: this._opcoes.seletoresTermo });
    if (!iniciou) {
      this._anunciarNoPainel(
        'Não foi possível ler o termo: texto não encontrado ou síntese de voz indisponível neste navegador.',
      );
    }
  }

  /** Pausa ou retoma, conforme o estado atual da leitura. @private */
  _alternarPausaTermo() {
    this._leitor.estado === 'pausado' ? this._leitor.retomar() : this._leitor.pausar();
  }

  /** Sincroniza botões Ler/Pausar/Parar com o estado do leitor. @private */
  _refletirEstadoLeitura(estado) {
    if (!this._painel) return;
    const botaoLer = this._raiz.querySelector('[data-termo-ler]');
    const botaoPausar = this._raiz.querySelector('[data-termo-pausar]');
    const botaoParar = this._raiz.querySelector('[data-termo-parar]');

    if (estado === 'indisponivel') {
      botaoLer.disabled = true;
      botaoLer.title = 'Síntese de voz indisponível neste navegador.';
      botaoPausar.disabled = true;
      botaoParar.disabled = true;
      this._anunciarNoPainel(
        'Leitura em voz alta não é suportada por este navegador.',
      );
      return;
    }

    botaoPausar.disabled = estado !== 'lendo' && estado !== 'pausado';
    botaoParar.disabled = estado !== 'lendo' && estado !== 'pausado';
    botaoLer.textContent = estado === 'pausado' ? '▶ Retomar' : '▶ Ler';
    botaoPausar.textContent = estado === 'pausado' ? '⏸ Retomar' : '⏸ Pausar';

    const mensagens = {
      lendo: 'Leitura do termo iniciada.',
      pausado: 'Leitura do termo pausada.',
      parado: 'Leitura do termo encerrada.',
      erro: 'Falha na síntese de voz. Tente novamente.',
    };
    if (mensagens[estado]) this._anunciarNoPainel(mensagens[estado]);
  }

  /** Alterna o interruptor de narração das chamadas de sala. */
  alternarNarracaoChamadas() {
    this._estado.narrarChamadas = !this._estado.narrarChamadas;
    this._aplicarPreferencias();
    if (this._opcoes.escutarChamadas) this._registrarEscutaChamadas();
    this._anunciarNoPainel(
      this._estado.narrarChamadas
        ? 'Narração de chamadas de sala ativada.'
        : 'Narração de chamadas de sala desativada.',
    );
  }
}

/* ==========================================================================
 * Observações de integração (leia no cabeçalho do módulo)
 * ========================================================================== */