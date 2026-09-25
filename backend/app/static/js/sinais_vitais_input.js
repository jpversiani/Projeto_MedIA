/**
 * @file Teclado de Sinais Vitais com validação instantânea — Projeto MedIA (SUS/APS).
 * @module backend/app/static/js/sinais_vitais_input
 *
 * @description
 * Componente de interface para inserção rápida de sinais vitais em atendimentos
 * da Atenção Primária à Saúde (APS), otimizado para telas de toque (tablets e
 * terminais de acolhimento da unidade básica).
 *
 * Funcionalidades:
 * - Campos: PA sistólica, PA diastólica, FC, FR, temperatura, SpO₂ e glicemia capilar;
 * - Steppers grandes (+/−) com repetição automática ao manter pressionado, adequados ao toque;
 * - Validação instantânea por faixas: destaque vermelho fora dos limites vitais e
 *   destaque âmbar fora da faixa de normalidade;
 * - Cálculo automático da PAM (PAS médio / Pressão Arterial Média): PAM = (PAS + 2 × PAD) ÷ 3,
 *   com destaque quando abaixo de 65 mmHg (risco de hipoperfusão);
 * - Alerta de choque: SpO₂ < 92% combinada com FC > 120 bpm;
 * - Emissão de CustomEvent com o estado completo a cada alteração e ao confirmar o registro.
 *
 * Eventos emitidos (no elemento raiz do componente, com bubbling):
 * - "{prefixo}:alteracao"  — a cada mudança de valor (padrão: "sinais-vitais:alteracao");
 * - "{prefixo}:confirmado" — ao registrar o conjunto completo de sinais (padrão:
 *   "sinais-vitais:confirmado").
 *
 * O `detail` dos eventos contém: `valores`, `status`, `pam`, `pamCritica`,
 * `completo`, `valido`, `alertaChoque`, `origem` e `momento` (ISO 8601).
 *
 * Uso:
 *   import { TecladoSinaisVitais } from './sinais_vitais_input.js';
 *   const teclado = new TecladoSinaisVitais({ container: '#sinais-vitais' });
 *   document.addEventListener('sinais-vitais:confirmado', (evento) => {
 *     console.log(evento.detail.valores, evento.detail.pam, evento.detail.alertaChoque);
 *   });
 *
 * Alternativamente, qualquer elemento com o atributo `data-teclado-sinais-vitais`
 * é inicializado automaticamente na importação deste módulo.
 *
 * Requer Tailwind CSS disponível na página hospedeira (arquitetura HTML5 + Tailwind).
 */

/** Prefixo padrão dos eventos emitidos pelo componente. */
const PREFIXO_EVENTO_PADRAO = 'sinais-vitais';

/** Limiar do alerta de choque: SpO₂ abaixo deste valor (em %). */
const CHOQUE_SPO2_LIMITE = 92;

/** Limiar do alerta de choque: FC acima deste valor (em bpm). */
const CHOQUE_FC_LIMITE = 120;

/** PAM abaixo deste valor (mmHg) indica risco de hipoperfusão tecidual. */
const PAM_LIMITE_CRITICO = 65;

/** Atraso (ms) antes de iniciar a repetição do stepper ao manter pressionado. */
const ATRASO_REPETICAO_MS = 450;

/** Intervalo (ms) entre repetições do stepper durante a pressão contínua. */
const INTERVALO_REPETICAO_MS = 90;

/**
 * Status possíveis de validação de um campo.
 * - VAZIO: nenhum valor informado;
 * - NORMAL: dentro da faixa clínica de normalidade;
 * - ATENCAO: fora da faixa normal, porém dentro dos limites vitais (destaque âmbar);
 * - CRITICO: fora dos limites vitais (destaque vermelho).
 * @type {Readonly<{VAZIO: string, NORMAL: string, ATENCAO: string, CRITICO: string}>}
 */
export const STATUS = Object.freeze({
  VAZIO: 'vazio',
  NORMAL: 'normal',
  ATENCAO: 'atencao',
  CRITICO: 'critico',
});

/**
 * Catálogo dos campos de sinais vitais aceitos pelo teclado.
 * - `min`/`max`: limites absolutos de entrada (valores fora também são críticos);
 * - `faixaNormal`: intervalo clínico de normalidade (destaque âmbar fora dele);
 * - `faixaCritica`: limites vitais — valores fora deste intervalo recebem destaque vermelho.
 * @type {ReadonlyArray<Object>}
 */
export const CAMPOS = Object.freeze([
  {
    id: 'pas',
    rotulo: 'PA sistólica',
    unidade: 'mmHg',
    passo: 5,
    decimais: 0,
    min: 50,
    max: 260,
    faixaNormal: [90, 139],
    faixaCritica: [80, 200],
    descricaoFaixa: 'Faixa normal: 90–139 mmHg',
  },
  {
    id: 'pad',
    rotulo: 'PA diastólica',
    unidade: 'mmHg',
    passo: 5,
    decimais: 0,
    min: 30,
    max: 160,
    faixaNormal: [50, 89],
    faixaCritica: [40, 120],
    descricaoFaixa: 'Faixa normal: 50–89 mmHg',
  },
  {
    id: 'fc',
    rotulo: 'FC (pulso)',
    unidade: 'bpm',
    passo: 2,
    decimais: 0,
    min: 20,
    max: 240,
    faixaNormal: [60, 100],
    faixaCritica: [45, 130],
    descricaoFaixa: 'Faixa normal: 60–100 bpm',
  },
  {
    id: 'fr',
    rotulo: 'FR (respiração)',
    unidade: 'irpm',
    passo: 1,
    decimais: 0,
    min: 4,
    max: 80,
    faixaNormal: [12, 20],
    faixaCritica: [8, 30],
    descricaoFaixa: 'Faixa normal: 12–20 irpm',
  },
  {
    id: 'temperatura',
    rotulo: 'Temperatura',
    unidade: '°C',
    passo: 0.5,
    decimais: 1,
    min: 30,
    max: 45,
    faixaNormal: [35.0, 37.7],
    faixaCritica: [34.0, 39.5],
    descricaoFaixa: 'Faixa normal: 35,0 a 37,7 °C',
  },
  {
    id: 'spo2',
    rotulo: 'SpO₂ (saturação)',
    unidade: '%',
    passo: 1,
    decimais: 0,
    min: 50,
    max: 100,
    faixaNormal: [95, 100],
    faixaCritica: [92, 100],
    descricaoFaixa: 'Faixa normal: 95–100 %',
  },
  {
    id: 'glicemia',
    rotulo: 'Glicemia capilar',
    unidade: 'mg/dL',
    passo: 5,
    decimais: 0,
    min: 10,
    max: 600,
    faixaNormal: [70, 140],
    faixaCritica: [50, 300],
    descricaoFaixa: 'Jejum: 70–99 mg/dL · Pós-prandial: até 140 mg/dL',
  },
]);

/** Mapa de acesso rápido aos campos por identificador. */
const CAMPO_POR_ID = new Map(CAMPOS.map((campo) => [campo.id, campo]));

/**
 * Classes Tailwind aplicadas conforme o status de validação do campo.
 * CRITICO produz o destaque vermelho exigido para valores fora dos limites vitais.
 */
const CLASSES_STATUS = Object.freeze({
  [STATUS.VAZIO]: {
    cartao: 'border-slate-200 bg-white',
    entrada: 'border-slate-200 text-slate-800 focus:border-sky-500',
    dica: 'text-slate-400',
  },
  [STATUS.NORMAL]: {
    cartao: 'border-slate-200 bg-white',
    entrada: 'border-slate-200 text-slate-800 focus:border-sky-500',
    dica: 'text-slate-500',
  },
  [STATUS.ATENCAO]: {
    cartao: 'border-amber-400 bg-amber-50',
    entrada: 'border-amber-400 text-amber-700 focus:border-amber-500',
    dica: 'text-amber-700',
  },
  [STATUS.CRITICO]: {
    cartao: 'border-red-500 bg-red-50',
    entrada: 'border-red-400 text-red-700 focus:border-red-500',
    dica: 'text-red-700',
  },
});

/** Cores das mensagens de retorno exibidas no rodapé do componente. */
const CLASSES_MENSAGEM = Object.freeze({
  info: 'text-slate-500',
  sucesso: 'text-emerald-600',
  atencao: 'text-amber-600',
  erro: 'text-red-600',
});

/** Classe base dos cartões de campo (combinada com as classes do status). */
const CLASSE_BASE_CARTAO = 'flex flex-col gap-3 rounded-2xl border-2 p-4 shadow-sm transition-colors';

/** Classe base do campo de digitação (borda/foco definidos por status). */
const CLASSE_BASE_ENTRADA =
  'h-20 w-24 min-w-0 rounded-xl border-2 bg-white text-center text-3xl font-bold tabular-nums placeholder:text-slate-300 focus:outline-none touch-manipulation';

/** Classe base do texto de dica sob cada campo. */
const CLASSE_BASE_DICA = 'text-xs font-medium leading-snug';

/** Botões de stepper grandes, otimizados para toque (mínimo de ~80 px). */
const CLASSE_BOTAO_PASSO =
  'flex h-20 w-20 shrink-0 select-none touch-manipulation items-center justify-center rounded-2xl bg-slate-200 text-4xl font-bold text-slate-700 shadow-sm transition active:scale-95 active:bg-slate-300';

/**
 * Componente de inserção rápida de sinais vitais com validação instantânea.
 * Renderiza o próprio markup no contêiner informado e emite CustomEvents
 * a cada alteração e no registro confirmado dos sinais.
 */
export class TecladoSinaisVitais {
  /** Elemento raiz renderizado pelo componente. */
  #elemento;
  /** Prefixo dos nomes dos eventos emitidos. */
  #prefixoEvento;
  /** Identificadores obrigatórios para liberar o registro. */
  #obrigatorios;
  /** Callback opcional disparado a cada alteração. */
  #onAlteracao;
  /** Callback disparado quando o registro é confirmado com sucesso. */
  #onConfirmar;
  /** Estado atual: Map<id, {valor: number|null, status: string}>. */
  #estado = new Map();
  /** Referências de DOM por campo: cartões, entradas e dicas. */
  #cartoes = new Map();
  #entradas = new Map();
  #dicas = new Map();
  /** Referências de regiões dinâmicas do componente. */
  #regiaoAlerta = null;
  #regiaoPam = null;
  #pamValor = null;
  #pamDica = null;
  #mensagemEl = null;
  /** Temporizador da repetição do stepper (timeout/intervalo). */
  #timerRepeticao = null;
  /** Manipuladores vinculados (guardados para remoção em destruir()). */
  #handlerInput = null;
  #handlerChange = null;
  #handlerClick = null;
  #handlerPointerDown = null;
  #handlerKeydown = null;
  #handlerFimToque = null;

  /**
   * Cria e renderiza o teclado de sinais vitais.
   * @param {Object} [opcoes={}]
   * @param {HTMLElement|string} [opcoes.container] Elemento ou seletor CSS do contêiner. Obrigatório.
   * @param {string} [opcoes.prefixoEvento='sinais-vitais'] Prefixo dos CustomEvents emitidos.
   * @param {string[]} [opcoes.obrigatorios] IDs obrigatórios para confirmar (padrão: todos).
   * @param {(dados: Object) => void} [opcoes.onAlteracao] Callback a cada alteração.
   * @param {(dados: Object) => void} [opcoes.onConfirmar] Callback ao confirmar o registro.
   * @throws {Error} Se o contêiner não for um elemento válido.
   */
  constructor(opcoes = {}) {
    const {
      container,
      prefixoEvento = PREFIXO_EVENTO_PADRAO,
      obrigatorios,
      onAlteracao = null,
      onConfirmar = null,
    } = opcoes;

    const alvo = typeof container === 'string' ? document.querySelector(container) : container;
    if (!(alvo instanceof HTMLElement)) {
      throw new Error('TecladoSinaisVitais: contêiner inválido ou não encontrado.');
    }

    const idsPermitidos = CAMPOS.map((campo) => campo.id);
    this.#obrigatorios = Array.isArray(obrigatorios)
      ? obrigatorios.filter((id) => idsPermitidos.includes(id))
      : idsPermitidos;
    if (this.#obrigatorios.length === 0) {
      throw new Error('TecladoSinaisVitais: informe ao menos um campo obrigatório válido.');
    }

    this.#prefixoEvento = String(prefixoEvento || PREFIXO_EVENTO_PADRAO);
    this.#onAlteracao = typeof onAlteracao === 'function' ? onAlteracao : null;
    this.#onConfirmar = typeof onConfirmar === 'function' ? onConfirmar : null;

    for (const campo of CAMPOS) {
      this.#estado.set(campo.id, { valor: null, status: STATUS.VAZIO });
    }

    this.#renderizar();
    this.#coletarReferencias();
    this.#vincularEventos();
  }

  /**
   * Renderiza a estrutura completa do componente no contêiner.
   * @private
   */
  #renderizar() {
    const cartoes = CAMPOS.map((campo) => this.#montarCartaoCampo(campo)).join('\n');
    this.#elemento = document.createElement('section');
    this.#elemento.className =
      'mx-auto w-full max-w-4xl rounded-3xl border border-slate-200 bg-slate-50 p-4 shadow-lg sm:p-6';
    this.#elemento.setAttribute('aria-label', 'Inserção de sinais vitais');
    this.#elemento.innerHTML = `
      <header class="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 class="text-lg font-bold text-slate-800 sm:text-xl">Sinais Vitais</h2>
          <p class="text-sm text-slate-500">
            Toque em &minus; / + ou digite o valor. Destaque vermelho indica limite vital ultrapassado.
          </p>
        </div>
        <button type="button" data-papel="limpar"
          class="min-h-12 shrink-0 touch-manipulation rounded-xl border-2 border-slate-300 bg-white px-4 text-sm font-semibold text-slate-600 shadow-sm transition active:bg-slate-100">
          Limpar
        </button>
      </header>

      <div data-regiao-alerta role="alert"
        class="mb-4 hidden items-center gap-3 rounded-2xl border-2 border-red-500 bg-red-50 p-4 animate-pulse">
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-600 text-lg font-black text-white">!</span>
        <p class="text-sm font-semibold text-red-700">
          <strong class="block text-base uppercase">Alerta de choque</strong>
          SpO&#8322; abaixo de 92% combinada com FC acima de 120 bpm.
          Avalie o paciente imediatamente e considere acionar a urgência.
        </p>
      </div>

      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        ${cartoes}
        <article data-regiao-pam class="${CLASSE_BASE_CARTAO} bg-slate-100">
          <div class="flex items-baseline justify-between">
            <h3 class="text-sm font-semibold uppercase tracking-wide text-slate-600">PAM</h3>
            <span class="text-xs font-medium text-slate-400">mmHg</span>
          </div>
          <div class="flex h-20 items-center justify-center rounded-xl bg-white text-3xl font-bold tabular-nums text-slate-800">
            <span data-pam-valor>--</span>
          </div>
          <p data-pam-dica class="text-xs font-medium leading-snug text-slate-500">
            Pressão Arterial Média = (PAS + 2 &times; PAD) &divide; 3. Requer PAS e PAD preenchidas.
          </p>
        </article>
      </div>

      <footer class="mt-4 flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p data-mensagem aria-live="polite" class="min-h-5 text-sm font-medium text-slate-500"></p>
        <button type="button" data-papel="confirmar"
          class="min-h-14 touch-manipulation rounded-2xl bg-emerald-600 px-8 text-base font-bold uppercase tracking-wide text-white shadow-md transition active:scale-[0.98] active:bg-emerald-700">
          Registrar sinais
        </button>
      </footer>
    `;
  }

  /**
   * Monta o markup de um cartão de campo com steppers grandes e campo de digitação.
   * @param {Object} campo Definição do campo (item de {@link CAMPOS}).
   * @returns {string} Markup HTML do cartão.
   * @private
   */
  #montarCartaoCampo(campo) {
    return `
      <article data-campo-id="${campo.id}" class="${CLASSE_BASE_CARTAO} border-slate-200 bg-white">
        <div class="flex items-baseline justify-between gap-2">
          <h3 class="text-sm font-semibold uppercase tracking-wide text-slate-600">${campo.rotulo}</h3>
          <span class="text-xs font-medium text-slate-400">${campo.unidade}</span>
        </div>
        <div class="flex items-center justify-between gap-2">
          <button type="button" data-campo-id="${campo.id}" data-acao="decrementar"
            aria-label="Diminuir ${campo.rotulo}" class="${CLASSE_BOTAO_PASSO}">&minus;</button>
          <input type="text" inputmode="decimal" data-campo-id="${campo.id}" value="" placeholder="--"
            autocomplete="off" aria-label="${campo.rotulo} em ${campo.unidade}"
            class="${CLASSE_BASE_ENTRADA} border-slate-200 text-slate-800 focus:border-sky-500" />
          <button type="button" data-campo-id="${campo.id}" data-acao="incrementar"
            aria-label="Aumentar ${campo.rotulo}" class="${CLASSE_BOTAO_PASSO}">+</button>
        </div>
        <p data-dica class="${CLASSE_BASE_DICA} text-slate-400">${campo.descricaoFaixa}</p>
      </article>
    `;
  }

  /**
   * Coleta as referências de DOM geradas na renderização.
   * @private
   */
  #coletarReferencias() {
    for (const campo of CAMPOS) {
      const cartao = this.#elemento.querySelector(`article[data-campo-id="${campo.id}"]`);
      this.#cartoes.set(campo.id, cartao);
      this.#entradas.set(campo.id, cartao.querySelector('input[data-campo-id]'));
      this.#dicas.set(campo.id, cartao.querySelector('[data-dica]'));
    }
    this.#regiaoAlerta = this.#elemento.querySelector('[data-regiao-alerta]');
    this.#regiaoPam = this.#elemento.querySelector('[data-regiao-pam]');
    this.#pamValor = this.#elemento.querySelector('[data-pam-valor]');
    this.#pamDica = this.#elemento.querySelector('[data-pam-dica]');
    this.#mensagemEl = this.#elemento.querySelector('[data-mensagem]');
  }

  /**
   * Vincula os eventos do componente (delegação no elemento raiz e janela).
   * @private
   */
  #vincularEventos() {
    // Digitação direta: interpreta e valida a cada tecla (validação instantânea).
    this.#handlerInput = (evento) => {
      const alvo = evento.target;
      if (!(alvo instanceof HTMLInputElement)) return;
      const id = alvo.dataset.campoId;
      if (!id || !CAMPO_POR_ID.has(id)) return;
      const valor = this.#interpretar(alvo.value, CAMPO_POR_ID.get(id));
      this.#definirValor(id, valor);
    };
    this.#elemento.addEventListener('input', this.#handlerInput);

    // Normaliza a formatação (ex.: vírgula decimal) ao concluir a edição.
    this.#handlerChange = (evento) => {
      const alvo = evento.target;
      const id = alvo instanceof HTMLInputElement ? alvo.dataset.campoId : null;
      if (!id || !CAMPO_POR_ID.has(id)) return;
      const estado = this.#estado.get(id);
      alvo.value = estado.valor === null ? '' : this.#formatar(CAMPO_POR_ID.get(id), estado.valor);
    };
    this.#elemento.addEventListener('change', this.#handlerChange);

    // Cliques de botões: steppers via teclado (detail === 0) e papéis (limpar/confirmar).
    // Toques e cliques de mouse são tratados no pointerdown, evitando duplo incremento.
    this.#handlerClick = (evento) => {
      const alvo = evento.target.closest('[data-acao], [data-papel]');
      if (!alvo) return;
      if (alvo.dataset.papel === 'limpar') {
        this.limpar();
        return;
      }
      if (alvo.dataset.papel === 'confirmar') {
        this.#confirmar();
        return;
      }
      const acao = alvo.dataset.acao;
      if (acao && evento.detail === 0) {
        this.#aplicarPasso(alvo.dataset.campoId, acao === 'incrementar' ? 1 : -1);
      }
    };
    this.#elemento.addEventListener('click', this.#handlerClick);

    // Pressão contínua nos steppers: aplica um passo imediato e repete enquanto mantido.
    this.#handlerPointerDown = (evento) => {
      const alvo = evento.target.closest('button[data-acao]');
      if (!alvo) return;
      evento.preventDefault();
      const id = alvo.dataset.campoId;
      const direcao = alvo.dataset.acao === 'incrementar' ? 1 : -1;
      this.#aplicarPasso(id, direcao);
      this.#iniciarRepeticao(() => this.#aplicarPasso(id, direcao));
    };
    this.#elemento.addEventListener('pointerdown', this.#handlerPointerDown);

    // Teclado nos campos: setas incrementam/decrementam; Enter confirma o registro.
    this.#handlerKeydown = (evento) => {
      const alvo = evento.target;
      const id = alvo instanceof HTMLInputElement ? alvo.dataset.campoId : null;
      if (!id || !CAMPO_POR_ID.has(id)) return;
      if (evento.key === 'ArrowUp') {
        evento.preventDefault();
        this.#aplicarPasso(id, 1);
      } else if (evento.key === 'ArrowDown') {
        evento.preventDefault();
        this.#aplicarPasso(id, -1);
      } else if (evento.key === 'Enter') {
        evento.preventDefault();
        this.#confirmar();
      }
    };
    this.#elemento.addEventListener('keydown', this.#handlerKeydown);

    // Encerra a repetição do stepper em qualquer fim de toque/clique na janela.
    this.#handlerFimToque = () => this.#pararRepeticao();
    window.addEventListener('pointerup', this.#handlerFimToque);
    window.addEventListener('pointercancel', this.#handlerFimToque);
  }

  /**
   * Interpreta o texto digitado, aceitando vírgula decimal (padrão pt-BR).
   * @param {string} texto Texto bruto do campo.
   * @param {Object} campo Definição do campo.
   * @returns {number|null} Valor numérico arredondado ou null quando inválido/vazio.
   * @private
   */
  #interpretar(texto, campo) {
    if (!texto || !texto.trim()) return null;
    const numero = Number.parseFloat(texto.trim().replace(',', '.'));
    if (!Number.isFinite(numero)) return null;
    return this.#arredondar(numero, campo.decimais);
  }

  /**
   * Arredonda o valor para a quantidade de decimais do campo.
   * @param {number} valor Valor numérico.
   * @param {number} decimais Quantidade de casas decimais.
   * @returns {number} Valor arredondado.
   * @private
   */
  #arredondar(valor, decimais) {
    const fator = 10 ** decimais;
    return Math.round(valor * fator) / fator;
  }

  /**
   * Formata o valor para exibição no campo de digitação.
   * @param {Object} campo Definição do campo.
   * @param {number} valor Valor numérico.
   * @returns {string} Valor formatado conforme a unidade do campo.
   * @private
   */
  #formatar(campo, valor) {
    return campo.decimais > 0 ? valor.toFixed(campo.decimais) : String(Math.round(valor));
  }

  /**
   * Avalia o status de validação de um valor conforme as faixas do campo.
   * @param {Object} campo Definição do campo.
   * @param {number|null} valor Valor a avaliar.
   * @returns {string} Um dos valores de {@link STATUS}.
   * @private
   */
  #avaliarStatus(campo, valor) {
    if (valor === null || valor === undefined) return STATUS.VAZIO;
    const foraDosLimitesVitais =
      valor < campo.min ||
      valor > campo.max ||
      valor < campo.faixaCritica[0] ||
      valor > campo.faixaCritica[1];
    if (foraDosLimitesVitais) return STATUS.CRITICO;
    const [minNormal, maxNormal] = campo.faixaNormal;
    if (valor < minNormal || valor > maxNormal) return STATUS.ATENCAO;
    return STATUS.NORMAL;
  }

  /**
   * Define o valor de um campo, valida instantaneamente e notifica ouvintes.
   * @param {string} id Identificador do campo.
   * @param {number|null} valor Valor numérico (null para limpar o campo).
   * @private
   */
  #definirValor(id, valor) {
    const campo = CAMPO_POR_ID.get(id);
    const estado = this.#estado.get(id);
    estado.valor = valor;
    estado.status = this.#avaliarStatus(campo, valor);
    this.#renderizarCampo(id);
    this.#notificarAlteracao();
  }

  /**
   * Aplica um passo do stepper (+/−) ao campo informado, respeitando os limites.
   * Campos vazios partem do centro da faixa normal no primeiro toque.
   * @param {string} id Identificador do campo.
   * @param {number} direcao 1 para incrementar, -1 para decrementar.
   * @private
   */
  #aplicarPasso(id, direcao) {
    const campo = CAMPO_POR_ID.get(id);
    const estado = this.#estado.get(id);
    const [minNormal, maxNormal] = campo.faixaNormal;
    const atual = estado.valor ?? this.#arredondar((minNormal + maxNormal) / 2, campo.decimais);
    const novo = Math.min(
      campo.max,
      Math.max(campo.min, this.#arredondar(atual + direcao * campo.passo, campo.decimais)),
    );
    this.#entradas.get(id).value = this.#formatar(campo, novo);
    this.#definirValor(id, novo);
  }

  /**
   * Calcula a PAM (PAS médio) a partir de PAS e PAD preenchidas.
   * Fórmula: PAM = (PAS + 2 × PAD) ÷ 3.
   * @returns {{valor: number, critica: boolean}|null} PAM arredondada ou null quando incompleta.
   * @private
   */
  #calcularPAM() {
    const pas = this.#estado.get('pas').valor;
    const pad = this.#estado.get('pad').valor;
    if (pas === null || pad === null) return null;
    const valor = Math.round((pas + 2 * pad) / 3);
    return { valor, critica: valor < PAM_LIMITE_CRITICO };
  }

  /**
   * Atualiza o cartão da PAM com o valor calculado e o destaque de hipoperfusão.
   * @private
   */
  #atualizarPAM() {
    if (!this.#regiaoPam) return;
    const pam = this.#calcularPAM();
    if (pam === null) {
      this.#pamValor.textContent = '--';
      this.#regiaoPam.className = `${CLASSE_BASE_CARTAO} bg-slate-100`;
      this.#pamDica.textContent = 'Pressão Arterial Média = (PAS + 2 × PAD) ÷ 3. Requer PAS e PAD preenchidas.';
      this.#pamDica.className = `${CLASSE_BASE_DICA} text-slate-500`;
      return;
    }
    this.#pamValor.textContent = String(pam.valor);
    if (pam.critica) {
      this.#regiaoPam.className = `${CLASSE_BASE_CARTAO} border-red-500 bg-red-50`;
      this.#pamDica.textContent = 'PAM abaixo de 65 mmHg — risco de hipoperfusão tecidual.';
      this.#pamDica.className = `${CLASSE_BASE_DICA} text-red-700`;
    } else {
      this.#regiaoPam.className = `${CLASSE_BASE_CARTAO} bg-slate-100`;
      this.#pamDica.textContent = 'PAM dentro da faixa de perfusão adequada (≥ 65 mmHg).';
      this.#pamDica.className = `${CLASSE_BASE_DICA} text-slate-500`;
    }
  }

  /**
   * Avalia e exibe o alerta de choque: SpO₂ < 92% combinada com FC > 120 bpm.
   * @private
   */
  #atualizarAlertaChoque() {
    const spo2 = this.#estado.get('spo2').valor;
    const fc = this.#estado.get('fc').valor;
    const emChoque = spo2 !== null && fc !== null && spo2 < CHOQUE_SPO2_LIMITE && fc > CHOQUE_FC_LIMITE;
    this.#regiaoAlerta.classList.toggle('hidden', !emChoque);
    this.#regiaoAlerta.classList.toggle('flex', emChoque);
  }

  /**
   * Atualiza o markup de um campo conforme o status de validação corrente.
   * @param {string} id Identificador do campo.
   * @private
   */
  #renderizarCampo(id) {
    const campo = CAMPO_POR_ID.get(id);
    const estado = this.#estado.get(id);
    const classes = CLASSES_STATUS[estado.status];

    this.#cartoes.get(id).className = `${CLASSE_BASE_CARTAO} ${classes.cartao}`;
    this.#entradas.get(id).className = `${CLASSE_BASE_ENTRADA} ${classes.entrada}`;

    let textoDica;
    switch (estado.status) {
      case STATUS.ATENCAO:
        textoDica = `Atenção: fora da faixa normal (${campo.faixaNormal[0]}–${campo.faixaNormal[1]} ${campo.unidade}).`;
        break;
      case STATUS.CRITICO:
        textoDica = 'FORA DOS LIMITES VITAIS — revise o valor.';
        break;
      default:
        textoDica = campo.descricaoFaixa;
    }
    this.#dicas.get(id).textContent = textoDica;
    this.#dicas.get(id).className = `${CLASSE_BASE_DICA} ${classes.dica}`;
  }

  /**
   * Exibe uma mensagem de retorno no rodapé do componente.
   * @param {string} texto Conteúdo da mensagem.
   * @param {'info'|'sucesso'|'atencao'|'erro'} [tipo='info'] Tipo visual da mensagem.
   * @private
   */
  #mensagem(texto, tipo = 'info') {
    this.#mensagemEl.textContent = texto;
    this.#mensagemEl.className = `min-h-5 text-sm font-medium ${CLASSES_MENSAGEM[tipo] ?? CLASSES_MENSAGEM.info}`;
  }

  /**
   * Recalcula indicadores (PAM e alerta de choque) e emite o CustomEvent de alteração.
   * @private
   */
  #notificarAlteracao() {
    this.#atualizarPAM();
    this.#atualizarAlertaChoque();
    const dados = this.getDados();
    const evento = new CustomEvent(`${this.#prefixoEvento}:alteracao`, {
      detail: { ...dados, origem: 'alteracao' },
      bubbles: true,
      composed: true,
    });
    this.#elemento.dispatchEvent(evento);
    if (this.#onAlteracao) this.#onAlteracao(evento.detail);
  }

  /**
   * Inicia a repetição do stepper durante a pressão contínua.
   * @param {() => void} acao Função executada a cada repetição.
   * @private
   */
  #iniciarRepeticao(acao) {
    this.#pararRepeticao();
    this.#timerRepeticao = window.setTimeout(() => {
      this.#timerRepeticao = window.setInterval(acao, INTERVALO_REPETICAO_MS);
    }, ATRASO_REPETICAO_MS);
  }

  /** Encerra a repetição do stepper, limpando os temporizadores. @private */
  #pararRepeticao() {
    if (this.#timerRepeticao === null) return;
    window.clearTimeout(this.#timerRepeticao);
    window.clearInterval(this.#timerRepeticao);
    this.#timerRepeticao = null;
  }

  /**
   * Registra o conjunto de sinais vitais após validar completude e limites.
   * Emite o evento "{prefixo}:confirmado" somente quando todos os campos
   * obrigatórios estão preenchidos e nenhum valor está fora dos limites vitais.
   * @returns {boolean} true quando o registro foi emitido.
   * @private
   */
  #confirmar() {
    const dados = this.getDados();
    if (!dados.completo) {
      this.#mensagem('Preencha todos os campos obrigatórios antes de registrar.', 'atencao');
      return false;
    }
    if (!dados.valido) {
      this.#mensagem('Existem valores fora dos limites vitais. Corrija-os antes de registrar.', 'erro');
      return false;
    }
    this.#mensagem('Sinais vitais registrados com sucesso.', 'sucesso');
    const evento = new CustomEvent(`${this.#prefixoEvento}:confirmado`, {
      detail: { ...dados, origem: 'confirmado' },
      bubbles: true,
      composed: true,
    });
    this.#elemento.dispatchEvent(evento);
    if (this.#onConfirmar) this.#onConfirmar(evento.detail);
    return true;
  }

  /**
   * Gera uma fotografia do estado atual do teclado, incluindo valores, status,
   * PAM calculada e o indicador de alerta de choque.
   * @returns {Object} Estado consolidado do componente.
   */
  getDados() {
    const valores = {};
    const status = {};
    for (const campo of CAMPOS) {
      const estado = this.#estado.get(campo.id);
      valores[campo.id] = estado.valor;
      status[campo.id] = estado.status;
    }

    const pam = this.#calcularPAM();
    const spo2 = valores.spo2;
    const fc = valores.fc;
    const alertaChoque = spo2 !== null && fc !== null && spo2 < CHOQUE_SPO2_LIMITE && fc > CHOQUE_FC_LIMITE;
    const completo = this.#obrigatorios.every((id) => status[id] !== STATUS.VAZIO);
    const valido = CAMPOS.every((campo) => status[campo.id] !== STATUS.CRITICO);

    return {
      valores,
      status,
      pam: pam === null ? null : pam.valor,
      pamCritica: pam === null ? false : pam.critica,
      completo,
      valido,
      alertaChoque,
      momento: new Date().toISOString(),
    };
  }

  /**
   * Limpa todos os campos do teclado e reemite o evento de alteração.
   * @returns {void}
   */
  limpar() {
    for (const campo of CAMPOS) {
      this.#estado.set(campo.id, { valor: null, status: STATUS.VAZIO });
      this.#entradas.get(campo.id).value = '';
      this.#renderizarCampo(campo.id);
    }
    this.#mensagem('Campos limpos.', 'info');
    this.#notificarAlteracao();
  }

  /**
   * Remove o componente do DOM, encerra temporizadores e desvincula ouvintes.
   * @returns {void}
   */
  destruir() {
    this.#pararRepeticao();
    this.#elemento.removeEventListener('input', this.#handlerInput);
    this.#elemento.removeEventListener('change', this.#handlerChange);
    this.#elemento.removeEventListener('click', this.#handlerClick);
    this.#elemento.removeEventListener('pointerdown', this.#handlerPointerDown);
    this.#elemento.removeEventListener('keydown', this.#handlerKeydown);
    window.removeEventListener('pointerup', this.#handlerFimToque);
    window.removeEventListener('pointercancel', this.#handlerFimToque);
    this.#elemento.remove();
  }
}

// Instanciação automática de contêineres declarados com o atributo dedicado.
function inicializarAutomaticamente() {
  document.querySelectorAll('[data-teclado-sinais-vitais]').forEach((elemento) => {
    if (!elemento.dataset.tecladoInstanciado) {
      elemento.dataset.tecladoInstanciado = 'true';
      new TecladoSinaisVitais({ container: elemento });
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', inicializarAutomaticamente, { once: true });
} else {
  inicializarAutomaticamente();
}

export default TecladoSinaisVitais;