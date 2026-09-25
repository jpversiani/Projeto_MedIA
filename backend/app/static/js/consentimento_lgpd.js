/**
 * consentimento_lgpd.js — Captura de Consentimento LGPD com Assinatura
 * ====================================================================
 * Projeto MedIA — SUS / Atenção Primária à Saúde (APS)
 *
 * Módulo responsável por:
 *   1. Exibir modal com o Termo de Sigilo e o Consentimento para teleconsulta,
 *      em conformidade com a Resolução CFM nº 2.314/2022 e a Lei nº 13.709/2018 (LGPD);
 *   2. Capturar a assinatura do paciente/responsável em <canvas> (toque/mouse/caneta),
 *      com suavização de traço por curvas quadráticas;
 *   3. Gerar o hash SHA-256 do aceite (Web Crypto API) para integridade do registro;
 *   4. Registrar metadados de auditoria: IP, User-Agent e data/hora (ISO 8601);
 *   5. Enviar o registro via POST /api/v1/consentimento.
 *
 * Uso (ES Module):
 *   import { abrirModalConsentimento } from '/static/js/consentimento_lgpd.js';
 *   const resultado = await abrirModalConsentimento({ cpf: '000.000.000-00' });
 *   if (!resultado) { /* usuário cancelou * / return; }
 *
 * O módulo não possui efeitos colaterais na importação (import seguro).
 */

'use strict';

/* ==========================================================================
 * Constantes do módulo
 * ========================================================================== */

/** Versão vigente do termo de consentimento (alterar a cada revisão jurídica). */
export const VERSAO_TERMO = '1.0-2026';

/** Finalidade padrão do tratamento de dados registrada no aceite. */
export const FINALIDADE_PADRAO = 'teleconsulta-aps';

/**
 * Endpoint do backend responsável por persistir o consentimento.
 * O servidor DEVE registrar também o IP real da conexão (comparando com o
 * IP informado pelo cliente, que é apenas complementar/auditoria).
 */
const ENDPOINT_PADRAO = '/api/v1/consentimento';

/** Cor do traço da assinatura (azul-grafite da paleta Tailwind slate-900). */
const COR_TINTA = '#0f172a';

/** Largura mínima/máxima do traço em pixels CSS (dinâmica pela velocidade). */
const LARGURA_MIN = 1.1;
const LARGURA_MAX = 3.2;

/* ==========================================================================
 * Erros e utilitários
 * ========================================================================== */

/** Erro específico do fluxo de consentimento, para tratamento pelo chamador. */
export class ErroConsentimento extends Error {
  /**
   * @param {string} mensagem Mensagem legível em Português do Brasil.
   */
  constructor(mensagem) {
    super(mensagem);
    this.name = 'ErroConsentimento';
  }
}

/**
 * Gera o hash SHA-256 (hexadecimal) de um texto utilizando a Web Crypto API.
 * Requer contexto seguro (HTTPS ou localhost).
 *
 * @param {string} texto Conteúdo a ser resumido criptograficamente.
 * @returns {Promise<string>} Hash SHA-256 em hexadecimal minúsculo (64 caracteres).
 * @throws {ErroConsentimento} Quando a Web Crypto API não está disponível.
 */
export async function calcularHashSha256(texto) {
  if (!(globalThis.crypto && typeof globalThis.crypto.subtle?.digest === 'function')) {
    throw new ErroConsentimento(
      'A Web Crypto API está indisponível. Acesse o sistema via HTTPS (ou localhost) para gerar o registro de consentimento.'
    );
  }
  const dados = new TextEncoder().encode(texto);
  const resumo = await globalThis.crypto.subtle.digest('SHA-256', dados);
  return Array.from(new Uint8Array(resumo))
    .map((octeto) => octeto.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Obtém o endereço IP público do cliente para compor a trilha de auditoria.
 * Falha de rede não bloqueia o fluxo: retorna um marcador e o backend deve
 * registrar o IP real da conexão HTTP como fonte autoritativa.
 *
 * @returns {Promise<string>} Endereço IP ou marcador 'indisponivel'.
 */
async function obterIpPublico() {
  const controlador = new AbortController();
  const temporizador = setTimeout(() => controlador.abort(), 4000);
  try {
    const resposta = await fetch('https://api.ipify.org/?format=json', {
      signal: controlador.signal,
      cache: 'no-store',
      credentials: 'omit',
    });
    if (!resposta.ok) return 'indisponivel';
    const dados = await resposta.json();
    return typeof dados?.ip === 'string' && dados.ip.length > 0 ? dados.ip : 'indisponivel';
  } catch {
    return 'indisponivel';
  } finally {
    clearTimeout(temporizador);
  }
}

/**
 * Cria um elemento HTML com atributos e filhos de forma declarativa.
 *
 * @param {string} etiqueta Nome da tag (ex.: 'div', 'button').
 * @param {Object} [atributos] Atributos a aplicar no elemento.
 * @param {Node[]|string[]} [filhos] Nós ou textos filhos.
 * @returns {HTMLElement} Elemento construído.
 */
function criarElemento(etiqueta, atributos = {}, filhos = []) {
  const elemento = document.createElement(etiqueta);
  for (const [chave, valor] of Object.entries(atributos)) {
    if (valor === null || valor === undefined) continue;
    if (chave === 'texto') elemento.textContent = valor;
    else if (chave === 'html') elemento.innerHTML = valor; // Conteúdo interno controlado pelo módulo.
    else elemento.setAttribute(chave, String(valor));
  }
  for (const filho of filhos) {
    elemento.append(typeof filho === 'string' ? document.createTextNode(filho) : filho);
  }
  return elemento;
}

/* ==========================================================================
 * Termo de Sigilo e Consentimento (conteúdo exibido no modal)
 * ========================================================================== */

/**
 * Monta o HTML do termo exibido ao paciente.
 * @returns {string} Marcação HTML do termo.
 */
function montarTextoTermo() {
  return `
    <p class="mb-2"><strong>1. Identificação e finalidade.</strong>
      Você está iniciando uma <strong>teleconsulta</strong> na Atenção Primária à Saúde (SUS).
      Os dados coletados serão utilizados exclusivamente para registro clínico, continuidade
      do cuidado e cumprimento de obrigações legais e sanitárias.</p>
    <p class="mb-2"><strong>2. Sigilo profissional (Resolução CFM nº 2.314/2022).</strong>
      A teleconsulta será realizada por profissional médico inscrito no CRM, que registrará
      os atendimentos em prontuário eletrônico, identificando-se com nome, CRM e horário.
      O sigilo das informações de saúde é garantido pelo Código de Ética Médica e pela
      legislação vigente. A teleconsulta não será gravada sem sua autorização expressa e específica.</p>
    <p class="mb-2"><strong>3. Proteção de dados pessoais (Lei nº 13.709/2018 — LGPD).</strong>
      Seus dados pessoais e dados sensíveis de saúde serão tratados com base legal na tutela
      da saúde (art. 11, II, "f") e no consentimento (art. 7º, I), observados os princípios
      da finalidade, adequação, necessidade, segurança e boa-fé. Não haverá compartilhamento
      com terceiros sem base legal, ressalvadas as hipóteses legais e as trocas assistenciais
      no SUS (ex.: Rede Nacional de Dados em Saúde).</p>
    <p class="mb-2"><strong>4. Direitos do titular.</strong>
      Você pode solicitar, a qualquer momento, acesso, correção, portabilidade e informação
      sobre o compartilhamento dos seus dados, por meio do canal da unidade de saúde ou do
      Encarregado de Proteção de Dados (DPO) do município.</p>
    <p class="mb-0"><strong>5. Registro do consentimento.</strong>
      Ao assinar este termo, você manifesta o <strong>aceite do compromisso de sigilo</strong> e o
      <strong>consentimento livre, informado e inequívoco</strong> para a teleconsulta. O aceite,
      a assinatura, o carimbo de data/hora e metadados de auditoria serão armazenados de forma
      íntegra (hash SHA-256) e vinculados ao seu prontuário.</p>
  `;
}

/* ==========================================================================
 * Captura de assinatura em canvas com suavização
 * ========================================================================== */

/**
 * Controla um <canvas> para captura de assinatura por toque, mouse ou caneta.
 * O traço é suavizado com curvas quadráticas pelos pontos médios e a espessura
 * responde à velocidade do gesto, aproximando a sensação de escrita real.
 */
class AssinaturaCanvas {
  /** @type {HTMLCanvasElement} Canvas da assinatura. */
  #canvas;

  /** @type {CanvasRenderingContext2D} Contexto 2D (já com escala por DPR). */
  #contexto;

  /** @type {Array<Array<{x:number, y:number, l:number}>>} Traços em coordenadas normalizadas (0–1). */
  #tracos = [];

  /** @type {Array<{x:number, y:number, l:number}>|null} Traço em andamento. */
  #tracoAtual = null;

  /** @type {{x:number, y:number, l:number}|null} Último ponto médio desenhado (segmento vivo). */
  #ultimoPontoMedio = null;

  /** @type {number} Instante do último evento de movimento (ms). */
  #ultimoInstante = 0;

  /** @type {ResizeObserver|null} Observador de redimensionamento do canvas. */
  #observadorTamanho = null;

  /**
   * @param {HTMLCanvasElement} canvas Elemento canvas preparado pelo modal.
   */
  constructor(canvas) {
    this.#canvas = canvas;
    this.#contexto = canvas.getContext('2d');
    this.#configurarContexto();
    this.#vincularEventos();

    this.#observadorTamanho = new ResizeObserver(() => this.#redimensionar());
    this.#observadorTamanho.observe(canvas);
  }

  /** Aplica estilo de traço e escala por densidade de pixels (DPR). */
  #configurarContexto() {
    const retangulo = this.#canvas.getBoundingClientRect();
    const proporcaoPixels = Math.max(1, window.devicePixelRatio || 1);
    this.#canvas.width = Math.max(1, Math.round(retangulo.width * proporcaoPixels));
    this.#canvas.height = Math.max(1, Math.round(retangulo.height * proporcaoPixels));
    const contexto = this.#contexto;
    contexto.setTransform(proporcaoPixels, 0, 0, proporcaoPixels, 0, 0);
    contexto.lineCap = 'round';
    contexto.lineJoin = 'round';
    contexto.strokeStyle = COR_TINTA;
  }

  /** Converte um evento de ponteiro em coordenadas normalizadas (0–1). */
  #paraCoordenadasNormalizadas(evento) {
    const retangulo = this.#canvas.getBoundingClientRect();
    return {
      x: (evento.clientX - retangulo.left) / retangulo.width,
      y: (evento.clientY - retangulo.top) / retangulo.height,
    };
  }

  /** Converte coordenadas normalizadas para pixels CSS atuais. */
  #paraPixels(ponto) {
    const retangulo = this.#canvas.getBoundingClientRect();
    return { x: ponto.x * retangulo.width, y: ponto.y * retangulo.height };
  }

  /** Vincula os eventos de ponteiro (mouse, toque e caneta) ao canvas. */
  #vincularEventos() {
    this.#canvas.addEventListener('pointerdown', (evento) => {
      if (evento.button !== 0 && evento.pointerType === 'mouse') return;
      evento.preventDefault();
      this.#canvas.setPointerCapture(evento.pointerId);
      const ponto = this.#paraCoordenadasNormalizadas(evento);
      this.#tracoAtual = [{ ...ponto, l: LARGURA_MAX * 0.8 }];
      this.#ultimoPontoMedio = { ...ponto, l: LARGURA_MAX * 0.8 };
      this.#ultimoInstante = performance.now();
      this.#desenharBase(false);
      this.#desenharPontoInicial(this.#tracoAtual[0]);
    });

    this.#canvas.addEventListener('pointermove', (evento) => {
      if (!this.#tracoAtual) return;
      evento.preventDefault();
      // Eventos coalescidos entregam todos os pontos intermediários do hardware,
      // o que melhora a suavização em telas de alta taxa de amostragem.
      const eventosCoalescidos =
        typeof evento.getCoalescedEvents === 'function' ? evento.getCoalescedEvents() : [evento];
      for (const eventoPonto of eventosCoalescidos) {
        this.#acrescentarPonto(eventoPonto);
      }
    });

    const finalizar = (evento) => {
      if (!this.#tracoAtual) return;
      evento.preventDefault?.();
      this.#finalizarTraco();
    };
    this.#canvas.addEventListener('pointerup', finalizar);
    this.#canvas.addEventListener('pointercancel', finalizar);
    this.#canvas.addEventListener('lostpointercapture', finalizar);
  }

  /**
   * Acrescenta um ponto ao traço em andamento desenhando o segmento suavizado.
   * @param {PointerEvent} evento Evento de movimento do ponteiro.
   */
  #acrescentarPonto(evento) {
    const traco = this.#tracoAtual;
    if (!traco) return;
    const ponto = this.#paraCoordenadasNormalizadas(evento);
    const anterior = traco[traco.length - 1];
    const distancia = Math.hypot(ponto.x - anterior.x, ponto.y - anterior.y);
    if (distancia < 0.0015) return; // Filtra micro-ruído do sensor.

    const agora = performance.now();
    const intervalo = Math.max(1, agora - this.#ultimoInstante);
    this.#ultimoInstante = agora;
    const velocidade = distancia / intervalo;

    // Espessura alvo inversamente proporcional à velocidade, com suavização
    // exponencial para evitar "degraus" perceptíveis no traço. A velocidade é
    // medida em coordenadas normalizadas por milissegundo (gesto rápido ≈ 0,004).
    const alvo = Math.min(LARGURA_MAX, Math.max(LARGURA_MIN, LARGURA_MAX - velocidade * 500));
    const largura = anterior.l * 0.65 + alvo * 0.35;
    traco.push({ ...ponto, l: largura });

    this.#desenharSegmentoSuavizado(anterior, traco[traco.length - 1]);
  }

  /**
   * Desenha um segmento do traço em andamento: curva quadrática do último
   * ponto médio até o ponto médio atual, usando o ponto novo como controle.
   * @param {{x:number,y:number,l:number}} controle Ponto de controle da curva.
   * @param {{x:number,y:number,l:number}} atual Ponto recém-adicionado.
   */
  #desenharSegmentoSuavizado(controle, atual) {
    const contexto = this.#contexto;
    const meio = {
      x: (controle.x + atual.x) / 2,
      y: (controle.y + atual.y) / 2,
      l: (controle.l + atual.l) / 2,
    };
    const inicio = this.#ultimoPontoMedio ?? this.#paraPixels(controle);
    const controlePx = this.#paraPixels(controle);
    const meioPx = this.#paraPixels(meio);

    contexto.beginPath();
    contexto.lineWidth = meio.l;
    contexto.moveTo(inicio.x, inicio.y);
    contexto.quadraticCurveTo(controlePx.x, controlePx.y, meioPx.x, meioPx.y);
    contexto.stroke();
    this.#ultimoPontoMedio = meioPx;
  }

  /** Finaliza o traço em andamento, fechando o segmento até o último ponto. */
  #finalizarTraco() {
    const traco = this.#tracoAtual;
    if (!traco) return;
    if (traco.length === 1) {
      this.#desenharPontoInicial(traco[0]); // Toque único: ponto de assinatura.
    } else {
      const ultimo = traco[traco.length - 1];
      const inicio = this.#ultimoPontoMedio ?? this.#paraPixels(ultimo);
      const fim = this.#paraPixels(ultimo);
      const contexto = this.#contexto;
      contexto.beginPath();
      contexto.lineWidth = ultimo.l;
      contexto.moveTo(inicio.x, inicio.y);
      contexto.lineTo(fim.x, fim.y);
      contexto.stroke();
    }
    this.#tracos.push(traco);
    this.#tracoAtual = null;
    this.#ultimoPontoMedio = null;
  }

  /** Desenha um ponto circular (gesto de toque único, sem arraste). */
  #desenharPontoInicial(ponto) {
    const contexto = this.#contexto;
    const centro = this.#paraPixels(ponto);
    contexto.beginPath();
    contexto.fillStyle = COR_TINTA;
    contexto.arc(centro.x, centro.y, ponto.l / 2, 0, Math.PI * 2);
    contexto.fill();
  }

  /**
   * Desenha a base do canvas: fundo branco, linha-guia e texto de apoio
   * quando ainda não há assinatura.
   * @param {boolean} comEspacoAssinatura Quando falso, omite o texto de apoio.
   */
  #desenharBase(comEspacoAssinatura = true) {
    const retangulo = this.#canvas.getBoundingClientRect();
    const contexto = this.#contexto;
    contexto.clearRect(0, 0, retangulo.width, retangulo.height);

    // Linha-guia tracejada para posicionar a assinatura.
    contexto.save();
    contexto.setLineDash([6, 5]);
    contexto.lineWidth = 1;
    contexto.strokeStyle = '#cbd5e1';
    contexto.beginPath();
    contexto.moveTo(16, retangulo.height * 0.72);
    contexto.lineTo(retangulo.width - 16, retangulo.height * 0.72);
    contexto.stroke();
    contexto.restore();

    if (comEspacoAssinatura && this.#tracos.length === 0 && !this.#tracoAtual) {
      contexto.save();
      contexto.fillStyle = '#94a3b8';
      contexto.font = '500 15px ui-sans-serif, system-ui, sans-serif';
      contexto.textAlign = 'center';
      contexto.textBaseline = 'middle';
      contexto.fillText('Assine aqui com o dedo, mouse ou caneta', retangulo.width / 2, retangulo.height / 2);
      contexto.restore();
    }
  }

  /** Reexecuta todos os traços armazenados (usado após redimensionamento). */
  #redesenharTudo() {
    this.#desenharBase();
    const tracos = this.#tracos;
    this.#tracos = [];
    for (const traco of tracos) {
      this.#ultimoPontoMedio = this.#paraPixels(traco[0]);
      this.#desenharPontoInicial(traco[0]);
      for (let indice = 1; indice < traco.length; indice += 1) {
        this.#desenharSegmentoSuavizado(traco[indice - 1], traco[indice]);
      }
      // Fecha o traço do último ponto médio até o ponto final, como no traço vivo.
      const ultimo = traco[traco.length - 1];
      const fim = this.#paraPixels(ultimo);
      const contexto = this.#contexto;
      contexto.beginPath();
      contexto.lineWidth = ultimo.l;
      contexto.moveTo(this.#ultimoPontoMedio.x, this.#ultimoPontoMedio.y);
      contexto.lineTo(fim.x, fim.y);
      contexto.stroke();
      this.#tracos.push(traco);
      this.#ultimoPontoMedio = null;
    }
  }

  /** Ajusta o tamanho do canvas à área visível preservando a assinatura. */
  #redimensionar() {
    const anterior = { width: this.#canvas.width, height: this.#canvas.height };
    this.#configurarContexto();
    if (this.#canvas.width !== anterior.width || this.#canvas.height !== anterior.height) {
      this.#redesenharTudo();
    } else {
      this.#desenharBase();
    }
  }

  /** Limpa todas as assinaturas registradas. */
  limpar() {
    this.#tracos = [];
    this.#tracoAtual = null;
    this.#ultimoPontoMedio = null;
    this.#desenharBase();
  }

  /**
   * Indica se há algum traço registrado.
   * @returns {boolean} Verdadeiro quando existe assinatura desenhada.
   */
  estaVazia() {
    return this.#tracos.length === 0;
  }

  /**
   * Exporta a assinatura como URL de dados PNG.
   * @returns {string} Conteúdo no formato 'data:image/png;base64,...'.
   */
  paraDataUrl() {
    return this.#canvas.toDataURL('image/png');
  }

  /** Libera recursos associados (observador de tamanho). */
  destruir() {
    this.#observadorTamanho?.disconnect();
    this.#observadorTamanho = null;
  }
}

/* ==========================================================================
 * Montagem do modal (HTML5 + Tailwind CSS)
 * ========================================================================== */

/**
 * Constrói a árvore DOM do modal de consentimento.
 *
 * @param {OpcoesConsentimento} opcoes Opções informadas pelo chamador.
 * @returns {{raiz: HTMLDivElement, assinatura: AssinaturaCanvas, elementos: Object<string, HTMLElement>}}
 *          Referências para controle do modal.
 */
function montarModal(opcoes) {
  const raiz = criarElemento('div', {
    class: 'fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4',
    role: 'dialog',
    'aria-modal': 'true',
    'aria-labelledby': 'consentimento-lgpd-titulo',
  });

  const cortina = criarElemento('div', {
    class: 'absolute inset-0 bg-slate-900/60 backdrop-blur-sm',
    'aria-hidden': 'true',
  });

  const cartao = criarElemento('div', {
    class: 'relative w-full sm:max-w-2xl max-h-[92vh] flex flex-col bg-white sm:rounded-2xl shadow-2xl overflow-hidden',
  });

  // Cabeçalho
  const cabecalho = criarElemento('div', {
    class: 'flex items-start justify-between gap-4 px-5 py-4 bg-gradient-to-r from-teal-700 to-emerald-600 text-white',
  });
  cabecalho.append(
    criarElemento('div', {}, [
      criarElemento('h2', {
        id: 'consentimento-lgpd-titulo',
        class: 'text-lg sm:text-xl font-semibold leading-tight',
        texto: 'Termo de Sigilo e Consentimento — Teleconsulta',
      }),
      criarElemento('p', {
        class: 'mt-1 text-xs sm:text-sm text-teal-50',
        texto: `Resolução CFM nº 2.314/2022 · LGPD (Lei nº 13.709/2018) · Versão do termo ${opcoes.versaoTermo}`,
      }),
    ])
  );

  // Área de conteúdo rolável
  const conteudo = criarElemento('div', { class: 'flex-1 overflow-y-auto px-5 py-4 space-y-4' });

  const termo = criarElemento('div', {
    id: 'consentimento-lgpd-termo',
    class: 'max-h-56 overflow-y-auto rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700 leading-relaxed',
    html: montarTextoTermo(),
  });
  termo.setAttribute('tabindex', '0');
  termo.setAttribute('aria-label', 'Texto integral do termo de sigilo e consentimento');

  const identificacao = criarElemento('p', {
    class: 'text-xs text-slate-500',
    texto: [
      opcoes.nomePaciente ? `Paciente: ${opcoes.nomePaciente}` : null,
      opcoes.cpf ? `CPF: ${opcoes.cpf}` : null,
      opcoes.cns ? `CNS: ${opcoes.cns}` : null,
      opcoes.profissional?.nome ? `Profissional: ${opcoes.profissional.nome}` : null,
      opcoes.profissional?.registro ? `${opcoes.profissional.registro}` : null,
    ]
      .filter(Boolean)
      .join('  ·  '),
  });

  // Aceites obrigatórios
  const campoSigilo = criarElemento('label', {
    class: 'flex items-start gap-3 rounded-lg border border-slate-200 p-3 text-sm text-slate-700 cursor-pointer hover:bg-slate-50 transition-colors',
  });
  const caixaSigilo = criarElemento('input', {
    type: 'checkbox',
    class: 'mt-0.5 h-4 w-4 shrink-0 accent-teal-600',
  });
  campoSigilo.append(
    caixaSigilo,
    criarElemento('span', {
      texto: 'Declaro que li e aceito o compromisso de sigilo exigido para a teleconsulta (Resolução CFM nº 2.314/2022).',
    })
  );

  const campoLgpd = criarElemento('label', {
    class: 'flex items-start gap-3 rounded-lg border border-slate-200 p-3 text-sm text-slate-700 cursor-pointer hover:bg-slate-50 transition-colors',
  });
  const caixaLgpd = criarElemento('input', {
    type: 'checkbox',
    class: 'mt-0.5 h-4 w-4 shrink-0 accent-teal-600',
  });
  campoLgpd.append(
    caixaLgpd,
    criarElemento('span', {
      texto: 'Consinto o tratamento dos meus dados pessoais e de saúde para a finalidade descrita, nos termos da LGPD.',
    })
  );

  // Assinatura
  const blocoAssinatura = criarElemento('div', { class: 'space-y-2' });
  const rotuloAssinatura = criarElemento('div', { class: 'flex items-center justify-between' });
  rotuloAssinatura.append(
    criarElemento('span', { class: 'text-sm font-medium text-slate-700', texto: 'Assinatura do paciente ou responsável legal' }),
    criarElemento('button', {
      type: 'button',
      id: 'consentimento-lgpd-limpar',
      class: 'text-xs font-medium text-teal-700 hover:text-teal-800 hover:underline',
      texto: 'Limpar assinatura',
    })
  );
  const telaAssinatura = criarElemento('canvas', {
    id: 'consentimento-lgpd-canvas',
    class: 'w-full h-40 rounded-lg border-2 border-dashed border-slate-300 bg-white touch-none select-none cursor-crosshair',
    'aria-label': 'Área de assinatura. Desenhe sua assinatura com o dedo, mouse ou caneta.',
  });
  telaAssinatura.style.touchAction = 'none';
  blocoAssinatura.append(rotuloAssinatura, telaAssinatura);

  conteudo.append(termo, identificacao, campoSigilo, campoLgpd, blocoAssinatura);

  // Mensagens de erro/aviso
  const areaMensagem = criarElemento('div', {
    id: 'consentimento-lgpd-mensagem',
    class: 'hidden px-5',
    role: 'alert',
    'aria-live': 'assertive',
  });

  // Rodapé com ações
  const rodape = criarElemento('div', {
    class: 'flex flex-col-reverse sm:flex-row sm:items-center justify-end gap-2 px-5 py-4 border-t border-slate-200 bg-slate-50',
  });
  const botaoCancelar = criarElemento('button', {
    type: 'button',
    class: 'inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-100 transition-colors',
    texto: 'Cancelar',
  });
  const botaoConfirmar = criarElemento('button', {
    type: 'button',
    class: 'inline-flex items-center justify-center gap-2 rounded-lg bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-teal-800 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
    texto: 'Confirmar aceite e assinar',
  });
  rodape.append(botaoCancelar, botaoConfirmar);

  cartao.append(cabecalho, conteudo, areaMensagem, rodape);
  raiz.append(cortina, cartao);

  return {
    raiz,
    assinatura: new AssinaturaCanvas(telaAssinatura),
    elementos: {
      caixaSigilo,
      caixaLgpd,
      botaoCancelar,
      botaoConfirmar,
      botaoLimpar: raiz.querySelector('#consentimento-lgpd-limpar'),
      areaMensagem,
      cartao,
    },
  };
}

/**
 * Exibe uma mensagem de erro dentro do modal.
 * @param {HTMLElement} areaMensagem Container com papel 'alert'.
 * @param {string} texto Mensagem a exibir.
 */
function mostrarMensagem(areaMensagem, texto) {
  areaMensagem.classList.remove('hidden');
  areaMensagem.replaceChildren(
    criarElemento('p', {
      class: 'mt-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700',
      texto,
    })
  );
}

/** Oculta mensagens de erro do modal. */
function limparMensagem(areaMensagem) {
  areaMensagem.classList.add('hidden');
  areaMensagem.replaceChildren();
}

/**
 * Mantém o foco do teclado dentro do modal enquanto estiver aberto.
 * @param {HTMLElement} raiz Elemento raiz do modal.
 * @returns {() => void} Função para remover o tratamento de foco.
 */
function prenderFoco(raiz) {
  const focaveis = 'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])';
  const tratador = (evento) => {
    if (evento.key !== 'Tab') return;
    const elementos = Array.from(raiz.querySelectorAll(focaveis)).filter((el) => el.offsetParent !== null);
    if (elementos.length === 0) return;
    const primeiro = elementos[0];
    const ultimo = elementos[elementos.length - 1];
    if (evento.shiftKey && document.activeElement === primeiro) {
      evento.preventDefault();
      ultimo.focus();
    } else if (!evento.shiftKey && document.activeElement === ultimo) {
      evento.preventDefault();
      primeiro.focus();
    }
  };
  raiz.addEventListener('keydown', tratador);
  return () => raiz.removeEventListener('keydown', tratador);
}

/* ==========================================================================
 * Fluxo principal
 * ========================================================================== */

/**
 * @typedef {Object} OpcoesConsentimento
 * @property {string}  [cpf] CPF do paciente (com ou sem máscara).
 * @property {string}  [cns] CNS do paciente (Cartão Nacional de Saúde).
 * @property {string}  [nomePaciente] Nome completo do paciente.
 * @property {string}  [idAgendamento] Identificador do agendamento da teleconsulta.
 * @property {{nome?: string, registro?: string}} [profissional] Médico responsável (nome e CRM).
 * @property {string}  [endpoint] Endpoint de registro (padrão: /api/v1/consentimento).
 * @property {string}  [versaoTermo] Versão do termo exibido.
 * @property {string}  [finalidade] Finalidade do tratamento de dados.
 */

/**
 * @typedef {Object} ResultadoConsentimento
 * @property {true}  aceito Indica que o consentimento foi registrado.
 * @property {string} hash Hash SHA-256 do aceite (integridade).
 * @property {string} assinaturaBase64 Assinatura em PNG (data URL).
 * @property {string} ip Endereço IP capturado no cliente (complementar).
 * @property {string} userAgent User-Agent do navegador.
 * @property {string} dataHora Data/hora do aceite em ISO 8601 (UTC).
 * @property {Object|null} resposta Corpo da resposta do backend, se houver.
 */

/**
 * Exibe o modal de consentimento, captura a assinatura, gera o hash SHA-256
 * do aceite e envia o registro ao backend.
 *
 * A promessa resolve com o {@link ResultadoConsentimento} em caso de sucesso,
 * ou com `null` quando o usuário cancela o fluxo.
 *
 * @param {OpcoesConsentimento} [opcoes] Dados contextuais do paciente e do atendimento.
 * @returns {Promise<ResultadoConsentimento|null>} Resultado do consentimento registrado.
 */
export async function abrirModalConsentimento(opcoes = {}) {
  const {
    cpf = '',
    cns = '',
    nomePaciente = '',
    idAgendamento = '',
    profissional = {},
    endpoint = ENDPOINT_PADRAO,
    versaoTermo = VERSAO_TERMO,
    finalidade = FINALIDADE_PADRAO,
  } = opcoes;

  if (typeof document === 'undefined') {
    throw new ErroConsentimento('Este módulo deve ser executado em um navegador (DOM indisponível).');
  }

  // O IP é buscado em paralelo enquanto o usuário lê o termo e assina.
  const promessaIp = obterIpPublico();
  const elementoFocoAnterior = document.activeElement instanceof HTMLElement ? document.activeElement : null;

  const { raiz, assinatura, elementos } = montarModal({ versaoTermo, nomePaciente, cpf, cns, profissional });
  document.body.append(raiz);
  const anteriorEstouro = document.body.style.overflow;
  document.body.style.overflow = 'hidden';

  let resolvido = false;
  let enviando = false;
  let liberarFoco = () => {};

  /**
   * Fecha o modal, restaura o estado da página e resolve a promessa.
   * @param {ResultadoConsentimento|null} resultado Resultado final do fluxo.
   */
  const encerrar = (resultado) => {
    if (resolvido) return;
    resolvido = true;
    liberarFoco();
    raiz.remove();
    document.body.style.overflow = anteriorEstouro;
    elementoFocoAnterior?.focus?.();
    assinatura.destruir();
    finalizar(resultado);
  };

  let finalizar = () => {};
  const promessa = new Promise((resolver) => {
    finalizar = resolver;
  });

  /** Aplica/retira o estado de envio nos controles do modal. */
  const alternarEstadoEnvio = (ativo) => {
    enviando = ativo;
    elementos.botaoConfirmar.disabled = ativo;
    elementos.botaoCancelar.disabled = ativo;
    elementos.botaoLimpar.disabled = ativo;
    elementos.caixaSigilo.disabled = ativo;
    elementos.caixaLgpd.disabled = ativo;
    elementos.botaoConfirmar.textContent = ativo ? 'Registrando consentimento…' : 'Confirmar aceite e assinar';
  };

  /**
   * Valida o formulário, gera o hash e envia o registro ao backend.
   */
  const confirmar = async () => {
    if (enviando || resolvido) return;
    limparMensagem(elementos.areaMensagem);

    if (!elementos.caixaSigilo.checked || !elementos.caixaLgpd.checked) {
      mostrarMensagem(
        elementos.areaMensagem,
        'Para prosseguir, marque os dois aceites: compromisso de sigilo (CFM 2.314/2022) e consentimento LGPD.'
      );
      return;
    }
    if (assinatura.estaVazia()) {
      mostrarMensagem(elementos.areaMensagem, 'A assinatura é obrigatória para registrar o consentimento.');
      return;
    }

    alternarEstadoEnvio(true);
    try {
      const ip = await promessaIp;
      const dataHora = new Date().toISOString();
      const assinaturaBase64 = assinatura.paraDataUrl();

      // Objeto com ordem de chaves fixa para gerar hash determinístico.
      const cargaUtil = {
        versao_termo: versaoTermo,
        finalidade,
        id_agendamento: idAgendamento,
        paciente: { nome: nomePaciente, cpf, cns },
        profissional: { nome: profissional.nome ?? '', registro: profissional.registro ?? '' },
        aceite_termo_sigilo: elementos.caixaSigilo.checked,
        aceite_consentimento_lgpd: elementos.caixaLgpd.checked,
        data_hora_aceite: dataHora,
        ip: ip,
        user_agent: navigator.userAgent,
        assinatura: assinaturaBase64,
      };

      // Hash SHA-256 cobre todo o registro (inclusive a assinatura), garantindo
      // integridade verificável no backend: qualquer alteração invalida o aceite.
      const hash = await calcularHashSha256(JSON.stringify(cargaUtil));

      const cabecalhos = { 'Content-Type': 'application/json' };
      const metaCsrf = document.querySelector('meta[name="csrf-token"]');
      if (metaCsrf?.content) cabecalhos['X-CSRF-Token'] = metaCsrf.content;

      const respostaHttp = await fetch(endpoint, {
        method: 'POST',
        headers: cabecalhos,
        credentials: 'same-origin',
        body: JSON.stringify({ ...cargaUtil, hash_integridade: hash, algoritmo_hash: 'SHA-256' }),
      });

      if (!respostaHttp.ok) {
        throw new ErroConsentimento(
          `O servidor recusou o registro do consentimento (código ${respostaHttp.status}). Tente novamente ou procure a recepção da unidade.`
        );
      }

      let corpo = null;
      try {
        corpo = await respostaHttp.json();
      } catch {
        corpo = null; // Resposta sem corpo JSON é aceitável (HTTP 204, por exemplo).
      }

      encerrar({
        aceito: true,
        hash,
        assinaturaBase64,
        ip,
        userAgent: navigator.userAgent,
        dataHora,
        resposta: corpo,
      });
    } catch (erro) {
      alternarEstadoEnvio(false);
      const mensagem =
        erro instanceof ErroConsentimento
          ? erro.message
          : 'Não foi possível registrar o consentimento. Verifique sua conexão e tente novamente.';
      mostrarMensagem(elementos.areaMensagem, mensagem);
    }
  };

  // Ligações de interface
  elementos.botaoLimpar.addEventListener('click', () => assinatura.limpar());
  elementos.botaoCancelar.addEventListener('click', () => encerrar(null));
  elementos.botaoConfirmar.addEventListener('click', confirmar);
  raiz.addEventListener('keydown', (evento) => {
    if (evento.key === 'Escape' && !enviando) encerrar(null);
  });

  // Abertura: foco no primeiro aceite para leitura imediata do termo.
  liberarFoco = prenderFoco(raiz);
  elementos.caixaSigilo.focus();

  return promessa;
}

/**
 * Vínculo padrão do módulo: exibe o modal de consentimento.
 * @param {OpcoesConsentimento} [opcoes] Dados contextuais do paciente e do atendimento.
 * @returns {Promise<ResultadoConsentimento|null>} Resultado do consentimento registrado.
 */
export default abrirModalConsentimento;
