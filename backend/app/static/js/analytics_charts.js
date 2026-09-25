/**
 * analytics_charts.js — Componente Gráfico de Linha e Heatmap Interativo
 * ======================================================================
 * Projeto MedIA — SUS / APS (Telemedicina / Teletrabalho Médico)
 *
 * Renderiza Canvas/Chart.js do mapa de calor de agendamentos por turno
 * e gráficos temporais de demanda do médico em teletrabalho.
 *
 * Conformidade: LGPD (minimização CNS/CPF), SUS (CIAP-2, CID-10, SOAP).
 *
 * Uso (ES Module):
 *   import { AnalyticsCharts, HeatmapTurnos, SerieTemporal } from '/static/js/analytics_charts.js';
 *
 *   const dashboard = new AnalyticsCharts('#analytics-dashboard', {
 *     heatmap: { height: 260, paleta: 'verde' },
 *     linha:   { height: 220, corLinha: '#0f766e' },
 *   });
 *   dashboard.renderar(dadosAnalytics);
 *
 * Exporta: AnalyticsCharts, HeatmapTurnos, SerieTemporal, ErroAnalytics
 */

"use strict";

/* ==========================================================================
 * Constantes e paletas
 * ========================================================================== */

/** Paletas de cor para o heatmap (Daltonismo-amigável — seqüência de luminância). */
const PALETAS = Object.freeze({
  verde: {
    nome: "Verde (SUS)",
    paradas: [
      [0, 240, 230],
      [0, 200, 160],
      [60, 180, 110],
      [120, 150, 70],
      [190, 120, 30],
      [240, 80, 40],
      [220, 40, 40],
    ],
  },
  azul: {
    nome: "Azul (Telemedicina)",
    paradas: [
      [220, 235, 250],
      [180, 210, 240],
      [100, 175, 230],
      [50, 135, 210],
      [25, 90, 170],
      [15, 55, 130],
      [5, 25, 80],
    ],
  },
  tons_cinza: {
    nome: "Escala de cinza",
    paradas: [
      [255, 255, 255],
      [220, 220, 220],
      [170, 170, 170],
      [115, 115, 115],
      [65, 65, 65],
      [30, 30, 30],
      [0, 0, 0],
    ],
  },
  laranja: {
    nome: "Laranja (Demanda)",
    paradas: [
      [255, 240, 220],
      [255, 210, 160],
      [255, 175, 100],
      [245, 135, 50],
      [220, 90, 30],
      [185, 50, 25],
      [140, 20, 15],
    ],
  },
});

/** Cores de fallback quando o navegador não suporta canvas ou DPR. */
const FALLBACK_DPR = 1;

/** Marcador de dados ausentes em células sem informação. */
const VAZIO = "\u2014";

/* ==========================================================================
 * Classe de erro específica do módulo
 * ========================================================================== */

class ErroAnalytics extends Error {
  /**
   * @param {string} mensagem Mensagem legível em Português do Brasil.
   * @param {string} [codigo] Código do erro para tratamento pelo chamador.
   */
  constructor(mensagem, codigo = "ERRO_ANALYTICS") {
    super(mensagem);
    this.name = "ErroAnalytics";
    this.codigo = codigo;
  }
}

/* ==========================================================================
 * Utilitários
 * ========================================================================== */

/**
 * Interpola linearmente entre duas cores RGB.
 * @param {number[]} corA RGB [r, g, b].
 * @param {number[]} corB RGB [r, g, b].
 * @param {number} t Fração 0..1.
 * @returns {number[]} RGB interpolado.
 */
function interpolarCor(corA, corB, t) {
  const f = Math.max(0, Math.min(1, t));
  return corA.map((v, i) => Math.round(v + (corB[i] - v) * f));
}

/**
 * Retorna a cor da paleta para um valor normalizado 0..1.
 * @param {number} normalizado Valor 0..1.
 * @param {number[][]} paradas Array de [r, g, b].
 * @returns {number[]} RGB.
 */
function corDaPaleta(normalizado, paradas) {
  if (paradas.length === 0) return [200, 200, 200];
  if (paradas.length === 1) return paradas[0];
  const idx = normalizado * (paradas.length - 1);
  const inferior = Math.min(Math.floor(idx), paradas.length - 2);
  const superior = inferior + 1;
  const fr = idx - inferior;
  return interpolarCor(paradas[inferior], paradas[superior], fr);
}

/**
 * Formata data ISO (YYYY-MM-DD) para exibição curta (DD/MM).
 * @param {string} iso Data ISO.
 * @returns {string} Data formatada.
 */
function formatarDataCurta(iso) {
  const [ano, mes, dia] = iso.slice(0, 10).split("-");
  return `${dia}/${mes}`;
}

/**
 * Formata número como percentual.
 * @param {number} valor Fração 0..1.
 * @returns {string} Percentual.
 */
function formatarPercentual(valor) {
  return `${(valor * 100).toFixed(1)}%`;
}

/**
 * Escapa HTML para prevenir XSS ao injetar texto em innerHTML.
 * @param {string} texto Texto a escapar.
 * @returns {string} Texto escapado.
 */
function escaparHTML(texto) {
  const mapa = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(texto).replace(/[&<>"']/g, (c) => mapa[c]);
}

/**
 * Cria elemento HTML com atributos e filhos de forma declarativa.
 * @param {string} tag Nome da tag.
 * @param {Record<string, string|boolean>} [atributos] Atributos a aplicar.
 * @param {(Node|string)[]} [filhos] Nós ou textos filhos.
 * @returns {HTMLElement} Elemento construído.
 */
function criarElemento(tag, atributos = {}, filhos = []) {
  const el = document.createElement(tag);
  for (const [chave, valor] of Object.entries(atributos)) {
    if (valor === null || valor === undefined) continue;
    if (chave === "texto") el.textContent = String(valor);
    else if (chave === "html") el.innerHTML = String(valor);
    else el.setAttribute(chave, String(valor));
  }
  for (const filho of filhos) {
    el.append(typeof filho === "string" ? document.createTextNode(filho) : filho);
  }
  return el;
}

/**
 * Exibe um toast temporário na tela.
 * @param {string} mensagem Texto do toast.
 * @param {"info"|"erro"|"sucesso"} [tipo] Tipo do toast.
 * @param {number} [duracao] Duração em ms.
 */
function exibirToast(mensagem, tipo = "info", duracao = 3500) {
  const existing = document.querySelector(".toast-analytics");
  if (existing) existing.remove();

  const cores = {
    info: "bg-blue-600 text-white",
    erro: "bg-red-600 text-white",
    sucesso: "bg-emerald-600 text-white",
  };

  const toast = criarElemento("div", {
    class: `toast-analytics fixed bottom-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg text-sm font-medium ${cores[tipo] ?? cores.info} transition-opacity duration-300`,
    role: "status",
    "aria-live": "polite",
    texto: mensagem,
  });
  document.body.append(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, duracao);
}

/* ==========================================================================
 * HeatmapTurnos — Mapa de calor de agendamentos por turno
 * ========================================================================== */

/**
 * Renderiza um heatmap Canvas interativo de agendamentos por turno (MANHA/TARDE/NOITE).
 *
 * Exemplo de dado aceito (compatível com `CelulaHeatmap` do schema Pydantic):
 * @typedef {Object} CelulaHeatmapDado
 * @property {string} data Date ISO (YYYY-MM-DD).
 * @property {"MANHA"|"TARDE"|"NOITE"} turno Turno do dia.
 * @property {number} total Total de agendamentos.
 * @property {number} [teleconsultas] Teleconsultas no turno.
 * @property {number} [faltas] Faltas no turno.
 *
 * @typedef {Object} DadosHeatmap
 * @property {string[]} colunas Lista de datas ISO.
 * @property {string[]} turnos Lista de turnos.
 * @property {CelulaHeatmapDado[]} celulas Células do heatmap.
 */
export class HeatmapTurnos {
  /** @type {HTMLCanvasElement} */
  #canvas;
  /** @type {CanvasRenderingContext2D} */
  #ctx;
  /** @type {DadosHeatmap|null} */
  #dados = null;
  /** @type {HTMLElement|null} */
  #tooltip = null;
  /** @type {((celula: CelulaHeatmapDado|null) => void)|null} */
  #onSelecionar = null;
  /** @type {number[][]} Matriz normalizada [turno][data] -> valor 0..1 */
  #matriz = [];
  /** @type {number} */
  #maximo = 0;
  /** @type {number|null} */
  #indiceAtivo = null;
  /** @type {ResizeObserver|null} */
  #observador = null;
  /** @type {string} */
  #paletaNome;
  /** @type {number} */
  #altura;
  /** @type {number} */
  #largura;
  /** @type {boolean} */
  #destruido = false;

  /**
   * @param {HTMLCanvasElement|string} canvas Canvas element ou seletor CSS.
   * @param {Object} [opcoes]
   * @param {HTMLElement} [opcoes.tooltipEl] Elemento para tooltip personalizado.
   * @param {(celula: CelulaHeatmapDado|null) => void} [opcoes.onSelecionar] Callback ao selecionar célula.
   * @param {keyof typeof PALETAS} [opcoes.paleta] Nome da paleta (padrão: 'verde').
   * @param {number} [opcoes.altura] Altura do canvas em CSS pixels (padrão: 220).
   */
  constructor(canvas, opcoes = {}) {
    if (typeof canvas === "string") {
      const el = document.querySelector(canvas);
      if (!el) throw new ErroAnalytics(`Canvas não encontrado: ${canvas}`, "CANVAS_NAO_ENCONTRADO");
      this.#canvas = /** @type {HTMLCanvasElement} */ (el);
    } else {
      this.#canvas = canvas;
    }
    const ctx = this.#canvas.getContext("2d");
    if (!ctx) throw new ErroAnalytics("Canvas 2D indisponível.", "CANVAS_SEM_CONTEXTO");
    this.#ctx = ctx;
    this.#tooltip = opcoes.tooltipEl ?? null;
    this.#onSelecionar = opcoes.onSelecionar ?? null;
    this.#paletaNome = opcoes.paleta ?? "verde";
    this.#altura = opcoes.altura ?? 220;
    this.#largura = opcoes.largura ?? 0;

    this.#canvas.setAttribute("role", "grid");
    this.#canvas.setAttribute("aria-label", "Heatmap de agendamentos por turno");
    this.#canvas.setAttribute("tabindex", "0");

    this.#canvas.addEventListener("mousemove", (e) => this.#aoMoverMouse(e));
    this.#canvas.addEventListener("mouseleave", () => this.#aoSairMouse());
    this.#canvas.addEventListener("click", (e) => this.#aoClicar(e));
    this.#canvas.addEventListener("keydown", (e) => this.#aoTeclado(e));
    this.#canvas.addEventListener("touchstart", (e) => this.#aoTouch(e), { passive: false });

    this.#observador = new ResizeObserver(() => this.#redesenhar());
    this.#observador.observe(this.#canvas);
  }

  /**
   * Renderiza os dados no heatmap.
   * @param {DadosHeatmap} dados Dados do heatmap.
   */
  renderar(dados) {
    if (this.#destruido) throw new ErroAnalytics("Componente destruído.", "COMPONENTE_DESTUIDO");
    this.#dados = this.#normalizar(dados);
    this.#calcularMatriz();
    this.#redesenhar();
  }

  /** Normaliza dados de entrada, preenchendo células ausentes com 0. */
  #normalizar(dados) {
    if (!dados || !dados.colunas || !dados.turnos || !dados.celulas) {
      throw new ErroAnalytics("Dados de heatmap inválidos (faltam colunas/turnos/celulas).", "DADOS_INVALIDOS");
    }
    const mapa = new Map();
    for (const c of dados.celulas) {
      mapa.set(`${c.data}|${c.turno}`, c);
    }
    const celulasCompletas = [];
    for (const turno of dados.turnos) {
      for (const data of dados.colunas) {
        const existente = mapa.get(`${data}|${turno}`);
        if (existente) {
          celulasCompletas.push(existente);
        } else {
          celulasCompletas.push({ data, turno, total: 0, teleconsultas: 0, faltas: 0 });
        }
      }
    }
    return { ...dados, celulas: celulasCompletas };
  }

  /** Calcula a matriz normalizada e o máximo para escala de cor. */
  #calcularMatriz() {
    const dados = this.#dados;
    if (!dados) return;
    const nTurnos = dados.turnos.length;
    const nDatas = dados.colunas.length;
    this.#matriz = Array.from({ length: nTurnos }, () => new Float32Array(nDatas));
    this.#maximo = 0;
    for (const celula of dados.celulas) {
      const iTurno = dados.turnos.indexOf(celula.turno);
      const iData = dados.colunas.indexOf(celula.data);
      if (iTurno < 0 || iData < 0) continue;
      const valor = celula.total;
      this.#matriz[iTurno][iData] = valor;
      if (valor > this.#maximo) this.#maximo = valor;
    }
    if (this.#maximo === 0) this.#maximo = 1; // evita divisão por zero
  }

  /** Redesenha o canvas considerando DPR e tamanho atual. */
  #redesenhar() {
    const ctx = this.#ctx;
    const rect = this.#canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || FALLBACK_DPR;
    const largura = rect.width;
    const altura = rect.height || this.#altura;
    this.#canvas.width = Math.round(largura * dpr);
    this.#canvas.height = Math.round(altura * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, largura, altura);

    if (!this.#dados || this.#maximo === 0) {
      this.#desenharVazio(largura, altura);
      return;
    }

    this.#desenharHeatmap(largura, altura);
    this.#desenharLegendas(largura, altura);
  }

  /** Desenha o estado "sem dados". */
  #desenharVazio(largura, altura) {
    const ctx = this.#ctx;
    ctx.fillStyle = "#94a3b8";
    ctx.font = "14px ui-sans-serif, system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("Sem dados de agendamento", largura / 2, altura / 2);
  }

  /** Desenha o heatmap com células coloridas. */
  #desenharHeatmap(largura, altura) {
    const dados = this.#dados;
    if (!dados) return;
    const ctx = this.#ctx;
    const paleta = PALETAS[this.#paletaNome]?.paradas ?? PALETAS.verde.paradas;

    const margemEsquerda = 72;
    const margemDireita = 12;
    const margemTopo = 32;
    const margemBase = 28;
    const espacoDisponivelLargura = largura - margemEsquerda - margemDireita;
    const espacoDisponivelAltura = altura - margemTopo - margemBase;

    const nTurnos = dados.turnos.length;
    const nDatas = dados.colunas.length;
    const celulaLargura = Math.max(1, espacoDisponivelLargura / nDatas);
    const celulaAltura = Math.max(1, espacoDisponivelAltura / nTurnos);
    const gap = 2;

    for (let iT = 0; iT < nTurnos; iT++) {
      for (let iD = 0; iD < nDatas; iD++) {
        const valor = this.#matriz[iT][iD];
        const normalizado = valor / this.#maximo;
        const [r, g, b] = corDaPaleta(normalizado, paleta);
        const x = margemEsquerda + iD * celulaLargura + gap / 2;
        const y = margemTopo + iT * celulaAltura + gap / 2;
        const w = Math.max(1, celulaLargura - gap);
        const h = Math.max(1, celulaAltura - gap);

        ctx.fillStyle = `rgb(${r},${g},${b})`;
        ctx.beginPath();
        ctx.roundRect(x, y, w, h, 3);
        ctx.fill();

        if (w >= 28 && h >= 16) {
          ctx.fillStyle = normalizado > 0.55 ? "#ffffff" : "#1e293b";
          ctx.font = `bold ${Math.min(11, h * 0.45)}px ui-monospace, monospace`;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(String(valor), x + w / 2, y + h / 2);
        }
      }
    }

    // Rótulos dos turnos (esquerda)
    ctx.fillStyle = "#475569";
    ctx.font = "11px ui-sans-serif, system-ui, sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (let iT = 0; iT < nTurnos; iT++) {
      const y = margemTopo + iT * celulaAltura + celulaAltura / 2;
      ctx.fillText(dados.turnos[iT], margemEsquerda - 8, y);
    }

    // Rótulos das datas (base)
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const passo = Math.max(1, Math.floor(nDatas / 12));
    for (let iD = 0; iD < nDatas; iD += passo) {
      const x = margemEsquerda + iD * celulaLargura + celulaLargura / 2;
      ctx.fillText(formatarDataCurta(dados.colunas[iD]), x, margemTopo + espacoDisponivelAltura + 6);
    }

    // Célula ativa (destaque)
    if (this.#indiceAtivo !== null) {
      const iT = Math.floor(this.#indiceAtivo / nDatas);
      const iD = this.#indiceAtivo % nDatas;
      if (iT >= 0 && iT < nTurnos && iD >= 0 && iD < nDatas) {
        const x = margemEsquerda + iD * celulaLargura;
        const y = margemTopo + iT * celulaAltura;
        ctx.strokeStyle = "#0f172a";
        ctx.lineWidth = 2;
        ctx.strokeRect(x + 1, y + 1, celulaLargura - 2, celulaAltura - 2);
      }
    }
  }

  /** Desenha a legenda de cores à direita do heatmap. */
  #desenharLegendas(largura, altura) {
    const ctx = this.#ctx;
    const paleta = PALETAS[this.#paletaNome]?.paradas ?? PALETAS.verde.paradas;
    const legendax = largura - 16;
    const legenday = 10;
    const legendaltura = altura - 20;
    const barralargura = 10;

    for (let i = 0; i < paleta.length; i++) {
      const t = paleta.length === 1 ? 0 : i / (paleta.length - 1);
      const [r, g, b] = paleta[i];
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fillRect(legendax - barralargura, legenday + t * legendaltura, barralargura, Math.ceil(legendaltura / paleta.length) + 1);
    }

    ctx.fillStyle = "#475569";
    ctx.font = "10px ui-sans-serif, system-ui, sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText(String(this.#maximo), legendax + 4, legenday);
    ctx.textBaseline = "bottom";
    ctx.fillText("0", legendax + 4, legenday + legendaltura);
  }

  /** Calcula a célula sob as coordenadas do mouse. */
  #celulaSobCoordenadas(clientX, clientY) {
    const dados = this.#dados;
    if (!dados) return null;
    const rect = this.#canvas.getBoundingClientRect();
    const mx = clientX - rect.left;
    const my = clientY - rect.top;

    const margemEsquerda = 72;
    const margemTopo = 32;
    const margemBase = 28;
    const espacoDisponivelLargura = rect.width - margemEsquerda - 12;
    const espacoDisponivelAltura = rect.height - margemTopo - margemBase;
    const nTurnos = dados.turnos.length;
    const nDatas = dados.colunas.length;
    const celulaLargura = Math.max(1, espacoDisponivelLargura / nDatas);
    const celulaAltura = Math.max(1, espacoDisponivelAltura / nTurnos);

    const iD = Math.floor((mx - margemEsquerda) / celulaLargura);
    const iT = Math.floor((my - margemTopo) / celulaAltura);

    if (iD < 0 || iD >= nDatas || iT < 0 || iT >= nTurnos) return null;

    const celula = dados.celulas.find(
      (c) => c.data === dados.colunas[iD] && c.turno === dados.turnos[iT]
    );
    return celula ?? null;
  }

  /** Handler de mousemove — exibe tooltip. */
  #aoMoverMouse(evento) {
    const celula = this.#celulaSobCoordenadas(evento.clientX, evento.clientY);
    this.#canvas.style.cursor = celula ? "pointer" : "default";
    this.#exibirTooltip(celula, evento.clientX, evento.clientY);
  }

  /** Handler de mouseleave — oculta tooltip. */
  #aoSairMouse() {
    this.#ocultarTooltip();
    this.#indiceAtivo = null;
    this.#redesenhar();
  }

  /** Handler de click — invoca callback de seleção. */
  #aoClicar(evento) {
    const celula = this.#celulaSobCoordenadas(evento.clientX, evento.clientY);
    if (celula && this.#onSelecionar) {
      this.#onSelecionar(celula);
    }
  }

  /** Handler de teclado — navegação com setas. */
  #aoTeclado(evento) {
    const dados = this.#dados;
    if (!dados) return;
    const nTurnos = dados.turnos.length;
    const nDatas = dados.colunas.length;
    const total = nTurnos * nDatas;

    if (this.#indiceAtivo === null) {
      if (evento.key === "Enter" || evento.key === " ") {
        this.#indiceAtivo = 0;
        evento.preventDefault();
        this.#redesenhar();
      }
      return;
    }

    let iT = Math.floor(this.#indiceAtivo / nDatas);
    let iD = this.#indiceAtivo % nDatas;

    switch (evento.key) {
      case "ArrowRight":
        iD = Math.min(iD + 1, nDatas - 1);
        evento.preventDefault();
        break;
      case "ArrowLeft":
        iD = Math.max(iD - 1, 0);
        evento.preventDefault();
        break;
      case "ArrowDown":
        iT = Math.min(iT + 1, nTurnos - 1);
        evento.preventDefault();
        break;
      case "ArrowUp":
        iT = Math.max(iT - 1, 0);
        evento.preventDefault();
        break;
      case "Enter":
      case " ": {
        const celula = dados.celulas.find(
          (c) => c.data === dados.colunas[iD] && c.turno === dados.turnos[iT]
        );
        if (celula && this.#onSelecionar) this.#onSelecionar(celula);
        evento.preventDefault();
        return;
      }
      case "Escape":
        this.#indiceAtivo = null;
        this.#redesenhar();
        return;
      default:
        return;
    }

    this.#indiceAtivo = iT * nDatas + iD;
    this.#redesenhar();
    const celula = dados.celulas.find(
      (c) => c.data === dados.colunas[iD] && c.turno === dados.turnos[iT]
    );
    this.#exibirTooltip(celula);
  }

  /** Handler de touch. */
  #aoTouch(evento) {
    if (evento.touches.length !== 1) return;
    evento.preventDefault();
    const touch = evento.touches[0];
    const celula = this.#celulaSobCoordenadas(touch.clientX, touch.clientY);
    if (celula) this.#exibirTooltip(celula, touch.clientX, touch.clientY);
  }

  /** Exibe tooltip na posição do mouse. */
  #exibirTooltip(celula, x, y) {
    if (this.#tooltip) {
      if (!celula) {
        this.#tooltip.classList.add("hidden");
        return;
      }
      this.#tooltip.classList.remove("hidden");
      this.#tooltip.innerHTML = `
        <div class="font-semibold text-slate-800">${escaparHTML(celula.turno)} — ${formatarDataCurta(celula.data)}</div>
        <div class="text-sm text-slate-600">Total: <b>${celula.total}</b></div>
        <div class="text-sm text-slate-600">Teleconsultas: <b>${celula.teleconsultas ?? VAZIO}</b></div>
        <div class="text-sm text-slate-600">Faltas: <b>${celula.faltas ?? VAZIO}</b></div>
      `;
      this.#tooltip.style.left = `${(x ?? 0) + 12}px`;
      this.#tooltip.style.top = `${(y ?? 0) - 10}px`;
    }
  }

  /** Oculta tooltip. */
  #ocultarTooltip() {
    if (this.#tooltip) this.#tooltip.classList.add("hidden");
  }

  /** Redesenha mantendo estado atual (sem normalizar novamente). */
  #redesenhar() {
    const ctx = this.#ctx;
    const rect = this.#canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || FALLBACK_DPR;
    const largura = rect.width;
    const altura = rect.height || this.#altura;
    this.#canvas.width = Math.round(largura * dpr);
    this.#canvas.height = Math.round(altura * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, largura, altura);
    if (!this.#dados || this.#maximo === 0) {
      this.#desenharVazio(largura, altura);
      return;
    }
    this.#desenharHeatmap(largura, altura);
    this.#desenharLegendas(largura, altura);
  }

  /** Retorna os dados normalizados. */
  get dados() {
    return this.#dados;
  }

  /** Destroi o componente e libera recursos. */
  destruir() {
    this.#destruido = true;
    this.#observador?.disconnect();
    this.#observador = null;
    this.#canvas.removeEventListener("mousemove", this.#aoMoverMouse);
    this.#canvas.removeEventListener("mouseleave", this.#aoSairMouse);
    this.#canvas.removeEventListener("click", this.#aoClicar);
    this.#canvas.removeEventListener("keydown", this.#aoTeclado);
    this.#canvas.removeEventListener("touchstart", this.#aoTouch);
    this.#dados = null;
    this.#matriz = [];
  }
}

/* ==========================================================================
 * SerieTemporal — Gráfico de linha de demanda temporal
 * ========================================================================== */

/**
 * Renderiza um gráfico de linha Canvas para série temporal de demanda.
 *
 * Dado aceito (compatível com `PontoSerieTemporal`):
 * @typedef {Object} PontoSerieTemporalDado
 * @property {string} data Date ISO (YYYY-MM-DD).
 * @property {number} agendamentos Total de agendamentos.
 * @property {number} teleconsultas Teleconsultas.
 * @property {number} presenciais Atendimentos presenciais.
 * @property {number} faltas Faltas/no-shows.
 * @property {number} taxaOcupacao Taxa de ocupação 0..1.
 *
 * @typedef {Object} DadosSerieTemporal
 * @property {"DIA"|"SEMANA"|"MES"} granularidade Granularidade dos dados.
 * @property {PontoSerieTemporalDado[]} pontos Pontos da série.
 */
export class SerieTemporal {
  /** @type {HTMLCanvasElement} */
  #canvas;
  /** @type {CanvasRenderingContext2D} */
  #ctx;
  /** @type {DadosSerieTemporal|null} */
  #dados = null;
  /** @type {HTMLElement|null} */
  #tooltip = null;
  /** @type {number|null} */
  #indiceAtivo = null;
  /** @type {ResizeObserver|null} */
  #observador = null;
  /** @type {string} */
  #corLinha;
  /** @type {boolean} */
  #destruido = false;

  /**
   * @param {HTMLCanvasElement|string} canvas Canvas element ou seletor CSS.
   * @param {Object} [opcoes]
   * @param {HTMLElement} [opcoes.tooltipEl] Elemento para tooltip personalizado.
   * @param {string} [opcoes.corLinha] Cor da linha principal (hex, padrão: '#0f766e').
   * @param {number} [opcoes.altura] Altura do canvas em CSS pixels (padrão: 220).
   */
  constructor(canvas, opcoes = {}) {
    if (typeof canvas === "string") {
      const el = document.querySelector(canvas);
      if (!el) throw new ErroAnalytics(`Canvas não encontrado: ${canvas}`, "CANVAS_NAO_ENCONTRADO");
      this.#canvas = /** @type {HTMLCanvasElement} */ (el);
    } else {
      this.#canvas = canvas;
    }
    const ctx = this.#canvas.getContext("2d");
    if (!ctx) throw new ErroAnalytics("Canvas 2D indisponível.", "CANVAS_SEM_CONTEXTO");
    this.#ctx = ctx;
    this.#tooltip = opcoes.tooltipEl ?? null;
    this.#corLinha = opcoes.corLinha ?? "#0f766e";

    this.#canvas.setAttribute("role", "img");
    this.#canvas.setAttribute("aria-label", "Gráfico de série temporal de demanda");
    this.#canvas.setAttribute("tabindex", "0");

    this.#canvas.addEventListener("mousemove", (e) => this.#aoMoverMouse(e));
    this.#canvas.addEventListener("mouseleave", () => this.#aoSairMouse());
    this.#canvas.addEventListener("keydown", (e) => this.#aoTeclado(e));

    this.#observador = new ResizeObserver(() => this.#redesenhar());
    this.#observador.observe(this.#canvas);
  }

  /**
   * Renderiza os dados no gráfico de linha.
   * @param {DadosSerieTemporal} dados Dados da série temporal.
   */
  renderar(dados) {
    if (this.#destruido) throw new ErroAnalytics("Componente destruído.", "COMPONENTE_DESTUIDO");
    this.#dados = this.#normalizar(dados);
    this.#redesenhar();
  }

  /** Normaliza dados, ordenando por data e preenchendo lacunas. */
  #normalizar(dados) {
    if (!dados || !dados.pontos || dados.pontos.length === 0) {
      throw new ErroAnalytics("Dados de série temporal inválidos.", "DADOS_INVALIDOS");
    }
    const pontos = [...dados.pontos].sort(
      (a, b) => new Date(a.data).getTime() - new Date(b.data).getTime()
    );
    return { ...dados, pontos };
  }

  /** Redesenha o canvas considerando DPR e tamanho atual. */
  #redesenhar() {
    const ctx = this.#ctx;
    const rect = this.#canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || FALLBACK_DPR;
    const largura = rect.width;
    const altura = rect.height || 220;
    this.#canvas.width = Math.round(largura * dpr);
    this.#canvas.height = Math.round(altura * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, largura, altura);

    if (!this.#dados || this.#dados.pontos.length === 0) {
      this.#desenharVazio(largura, altura);
      return;
    }

    this.#desenharGrafico(largura, altura);
  }

  /** Desenha o estado "sem dados". */
  #desenharVazio(largura, altura) {
    const ctx = this.#ctx;
    ctx.fillStyle = "#94a3b8";
    ctx.font = "14px ui-sans-serif, system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("Sem dados temporais", largura / 2, altura / 2);
  }

  /** Calcula os limites dos eixos. */
  #calcularLimites() {
    const pontos = this.#dados?.pontos ?? [];
    if (pontos.length === 0) return { yMin: 0, yMax: 10, xMin: 0, xMax: 1 };

    const valores = pontos.flatMap((p) => [p.agendamentos, p.teleconsultas, p.presenciais]);
    const yMin = 0;
    const yMax = Math.max(...valores, 1) * 1.15;
    return { yMin, yMax, xMin: 0, xMax: pontos.length - 1, pontos };
  }

  /** Desenha o gráfico de linha com área preenchida. */
  #desenharGrafico(largura, altura) {
    const { yMin, yMax, xMin, xMax, pontos } = this.#calcularLimites();
    const ctx = this.#ctx;

    const margemEsquerda = 48;
    const margemDireita = 16;
    const margemTopo = 16;
    const margemBase = 32;
    const espacoLargura = largura - margemEsquerda - margemDireita;
    const espacoAltura = altura - margemTopo - margemBase;

    const escalaX = (i) => margemEsquerda + (i / Math.max(1, xMax)) * espacoLargura;
    const escalaY = (v) => margemTopo + espacoAltura - ((v - yMin) / Math.max(1, yMax - yMin)) * espacoAltura;

    // Grade horizontal
    ctx.strokeStyle = "#e2e8f0";
    ctx.lineWidth = 1;
    const passosY = 4;
    for (let i = 0; i <= passosY; i++) {
      const v = yMin + ((yMax - yMin) * i) / passosY;
      const y = escalaY(v);
      ctx.beginPath();
      ctx.moveTo(margemEsquerda, y);
      ctx.lineTo(largura - margemDireita, y);
      ctx.stroke();
      ctx.fillStyle = "#64748b";
      ctx.font = "10px ui-monospace, monospace";
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText(String(Math.round(v)), margemEsquerda - 6, y);
    }

    // Rótulos X (datas)
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const passoX = Math.max(1, Math.floor(pontos.length / 8));
    for (let i = 0; i < pontos.length; i += passoX) {
      const x = escalaX(i);
      ctx.fillText(formatarDataCurta(pontos[i].data), x, margemTopo + espacoAltura + 8);
    }

    // Função para desenhar uma linha
    const desenharLinha = (extrairValor, cor, larguraLinha = 2) => {
      ctx.strokeStyle = cor;
      ctx.lineWidth = larguraLinha;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
      ctx.beginPath();
      for (let i = 0; i < pontos.length; i++) {
        const x = escalaX(i);
        const y = escalaY(extrairValor(pontos[i]));
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    };

    // Área preenchida para agendamentos
    ctx.fillStyle = "rgba(15, 118, 110, 0.08)";
    ctx.beginPath();
    for (let i = 0; i < pontos.length; i++) {
      const x = escalaX(i);
      const y = escalaY(pontos[i].agendamentos);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.lineTo(escalaX(pontos.length - 1), escalaY(0));
    ctx.lineTo(escalaX(0), escalaY(0));
    ctx.closePath();
    ctx.fill();

    // Linhas
    desenharLinha((p) => p.agendamentos, this.#corLinha, 2.5);
    desenharLinha((p) => p.teleconsultas, "#0ea5e9", 2);
    desenharLinha((p) => p.presenciais, "#a855f7", 2);
    desenharLinha((p) => p.faltas, "#ef4444", 1.5);

    // Pontos ativos
    if (this.#indiceAtivo !== null && this.#indiceAtivo >= 0 && this.#indiceAtivo < pontos.length) {
      const p = pontos[this.#indiceAtivo];
      const x = escalaX(this.#indiceAtivo);
      ctx.fillStyle = this.#corLinha;
      ctx.beginPath();
      ctx.arc(x, escalaY(p.agendamentos), 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Legenda
    const legendaX = largura - margemDireita - 140;
    const legendaY = margemTopo + 4;
    const itensLegenda = [
      { label: "Agendamentos", cor: this.#corLinha },
      { label: "Teleconsultas", cor: "#0ea5e9" },
      { label: "Presenciais", cor: "#a855f7" },
      { label: "Faltas", cor: "#ef4444" },
    ];
    ctx.font = "10px ui-sans-serif, system-ui, sans-serif";
    itensLegenda.forEach((item, idx) => {
      const iy = legendaY + idx * 16;
      ctx.fillStyle = item.cor;
      ctx.fillRect(legendaX, iy, 10, 10);
      ctx.fillStyle = "#475569";
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.fillText(item.label, legendaX + 14, iy);
    });
  }

  /** Calcula o ponto sob as coordenadas do mouse. */
  #pontoSobCoordenadas(clientX, clientY) {
    const pontos = this.#dados?.pontos ?? [];
    if (pontos.length === 0) return null;
    const rect = this.#canvas.getBoundingClientRect();
    const mx = clientX - rect.left;
    const margemEsquerda = 48;
    const margemDireita = 16;
    const espacoLargura = rect.width - margemEsquerda - margemDireita;
    const idx = Math.round(((mx - margemEsquerda) / espacoLargura) * Math.max(1, pontos.length - 1));
    if (idx < 0 || idx >= pontos.length) return null;
    return { ponto: pontos[idx], indice: idx };
  }

  #aoMoverMouse(evento) {
    const resultado = this.#pontoSobCoordenadas(evento.clientX, evento.clientY);
    this.#canvas.style.cursor = resultado ? "crosshair" : "default";
    this.#indiceAtivo = resultado?.indice ?? null;
    this.#exibirTooltip(resultado?.ponto ?? null, evento.clientX, evento.clientY);
    this.#redesenhar();
  }

  #aoSairMouse() {
    this.#ocultarTooltip();
    this.#indiceAtivo = null;
    this.#redesenhar();
  }

  #aoTeclado(evento) {
    const pontos = this.#dados?.pontos ?? [];
    if (pontos.length === 0) return;
    if (this.#indiceAtivo === null) {
      if (evento.key === "ArrowRight" || evento.key === "ArrowLeft") {
        this.#indiceAtivo = evento.key === "ArrowRight" ? 0 : pontos.length - 1;
        evento.preventDefault();
      } else if (evento.key === "Escape") {
        this.#indiceAtivo = null;
        this.#redesenhar();
      }
      return;
    }
    let idx = this.#indiceAtivo;
    switch (evento.key) {
      case "ArrowRight":
        idx = Math.min(idx + 1, pontos.length - 1);
        evento.preventDefault();
        break;
      case "ArrowLeft":
        idx = Math.max(idx - 1, 0);
        evento.preventDefault();
        break;
      case "Escape":
        this.#indiceAtivo = null;
        this.#redesenhar();
        return;
      default:
        return;
    }
    this.#indiceAtivo = idx;
    this.#exibirTooltip(pontos[idx]);
    this.#redesenhar();
  }

  #exibirTooltip(ponto, x, y) {
    if (this.#tooltip) {
      if (!ponto) {
        this.#tooltip.classList.add("hidden");
        return;
      }
      this.#tooltip.classList.remove("hidden");
      this.#tooltip.innerHTML = `
        <div class="font-semibold text-slate-800">${formatarDataCurta(ponto.data)}</div>
        <div class="text-sm text-slate-600">Agendamentos: <b>${ponto.agendamentos}</b></div>
        <div class="text-sm text-slate-600">Teleconsultas: <b>${ponto.teleconsultas}</b></div>
        <div class="text-sm text-slate-600">Presenciais: <b>${ponto.presenciais}</b></div>
        <div class="text-sm text-slate-600">Faltas: <b>${ponto.faltas}</b></div>
        <div class="text-sm text-slate-600">Ocupação: <b>${formatarPercentual(ponto.taxaOcupacao)}</b></div>
      `;
      this.#tooltip.style.left = `${(x ?? 0) + 12}px`;
      this.#tooltip.style.top = `${(y ?? 0) - 10}px`;
    }
  }

  #ocultarTooltip() {
    if (this.#tooltip) this.#tooltip.classList.add("hidden");
  }

  get dados() {
    return this.#dados;
  }

  destruir() {
    this.#destruido = true;
    this.#observador?.disconnect();
    this.#observador = null;
    this.#canvas.removeEventListener("mousemove", this.#aoMoverMouse);
    this.#canvas.removeEventListener("mouseleave", this.#aoSairMouse);
    this.#canvas.removeEventListener("keydown", this.#aoTeclado);
    this.#dados = null;
  }
}

/* ==========================================================================
 * AnalyticsCharts — Orquestrador principal
 * ========================================================================== */

/**
 * Componente principal de analytics: heatmap + série temporal + KPIs.
 *
 * @typedef {Object} DadosAnalytics
 * @property {{id:number, nome:string, cns:string|null, cpf_masked:string}} medico Dados do médico (LGPD: CNS/CPF mascarados).
 * @property {{inicio:string, fim:string}} periodo Período da análise.
 * @property {DadosHeatmap} heatmap Dados do heatmap.
 * @property {DadosSerieTemporal} seriesTemporais Dados da série temporal.
 * @property {Object} [kpis] KPIs opcionais.
 */
export class AnalyticsCharts {
  /** @type {HTMLElement} */
  #container;
  /** @type {HeatmapTurnos|null} */
  #heatmap = null;
  /** @type {SerieTemporal|null} */
  #linha = null;
  /** @type {DadosAnalytics|null} */
  #dados = null;
  /** @type {boolean} */
  #destruido = false;
  /** @type {Object} */
  #opcoes;

  /**
   * @param {HTMLElement|string} container Container ou seletor CSS.
   * @param {Object} [opcoes]
   * @param {Object} [opcoes.heatmap] Opções para HeatmapTurnos.
   * @param {Object} [opcoes.linha] Opções para SerieTemporal.
   * @param {boolean} [opcoes.mostrarKPIs] Exibir cards de KPIs (padrão: true).
   * @param {boolean} [opcoes.exportavel] Habilitar botão de exportação PNG (padrão: true).
   */
  constructor(container, opcoes = {}) {
    if (typeof container === "string") {
      const el = document.querySelector(container);
      if (!el) throw new ErroAnalytics(`Container não encontrado: ${container}`, "CONTAINER_NAO_ENCONTRADO");
      this.#container = el;
    } else {
      this.#container = container;
    }
    this.#opcoes = {
      mostrarKPIs: true,
      exportavel: true,
      ...opcoes,
    };
    this.#construirUI();
  }

  /** Construi a estrutura DOM do dashboard. */
  #construirUI() {
    this.#container.innerHTML = "";
    this.#container.classList.add("analytics-dashboard");

    // Cabeçalho
    const cabecalho = criarElemento("div", { class: "flex items-center justify-between mb-4" });
    cabecalho.append(
      criarElemento("h3", { class: "text-lg font-bold text-slate-800", texto: "Análise de Demanda — Teletrabalho" }),
      criarElemento("span", { class: "text-xs text-slate-400", texto: "SUS / APS — Conforme LGPD" })
    );
    this.#container.append(cabecalho);

    // Área de KPIs
    if (this.#opcoes.mostrarKPIs) {
      this.#container.append(this.#criarGridKPIs());
    }

    // Grid: heatmap + linha temporal
    const grid = criarElemento("div", { class: "grid grid-cols-1 lg:grid-cols-2 gap-4" });

    // Painel do heatmap
    const painelHeatmap = criarElemento("div", { class: "bg-white rounded-xl border border-slate-200 p-4 shadow-sm" });
    const tituloHeatmap = criarElemento("h4", { class: "text-sm font-semibold text-slate-700 mb-2", texto: "Agendamentos por Turno" });
    const canvasHeatmap = criarElemento("canvas", {
      id: "analytics-heatmap",
      class: "w-full rounded-lg border border-slate-100",
      style: "height:260px;",
    });
    painelHeatmap.append(tituloHeatmap, canvasHeatmap);
    grid.append(painelHeatmap);

    // Painel da série temporal
    const painelLinha = criarElemento("div", { class: "bg-white rounded-xl border border-slate-200 p-4 shadow-sm" });
    const tituloLinha = criarElemento("h4", { class: "text-sm font-semibold text-slate-700 mb-2", texto: "Evolução Temporal da Demanda" });
    const canvasLinha = criarElemento("canvas", {
      id: "analytics-serie",
      class: "w-full rounded-lg border border-slate-100",
      style: "height:220px;",
    });
    painelLinha.append(tituloLinha, canvasLinha);
    grid.append(painelLinha);

    this.#container.append(grid);

    // Tooltip flutuante
    this.#tooltip = criarElemento("div", {
      class: "hidden fixed z-50 px-3 py-2 bg-slate-900 text-white text-xs rounded-lg shadow-lg pointer-events-none max-w-xs",
      style: "transition: opacity 0.15s;",
    });
    document.body.append(this.#tooltip);

    // Botão de exportação
    if (this.#opcoes.exportavel) {
      const btnExportar = criarElemento("button", {
        type: "button",
        class: "mt-3 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors",
        texto: "Exportar PNG",
      });
      btnExportar.addEventListener("click", () => this.#exportarPNG());
      this.#container.append(btnExportar);
    }

    // Inicializa subcomponentes
    try {
      this.#heatmap = new HeatmapTurnos("#analytics-heatmap", {
        tooltipEl: this.#tooltip,
        paleta: this.#opcoes.heatmap?.paleta ?? "verde",
      });
      this.#linha = new SerieTemporal("#analytics-serie", {
        tooltipEl: this.#tooltip,
        corLinha: this.#opcoes.linha?.corLinha ?? "#0f766e",
      });
    } catch (erro) {
      console.error("[AnalyticsCharts] Erro ao inicializar subcomponentes:", erro);
      exibirToast("Erro ao inicializar gráficos.", "erro");
    }
  }

  /** Cria o grid de cards de KPIs. */
  #criarGridKPIs() {
    const grid = criarElemento("div", { class: "grid grid-cols-2 md:grid-cols-4 gap-3 mb-4" });
    const kpis = [
      { id: "kpi-total", label: "Total Agendamentos", valor: "--", cor: "bg-blue-50 text-blue-700 border-blue-200" },
      { id: "kpi-tele", label: "Teleconsultas", valor: "--", cor: "bg-emerald-50 text-emerald-700 border-emerald-200" },
      { id: "kpi-faltas", label: "Faltas", valor: "--", cor: "bg-amber-50 text-amber-700 border-amber-200" },
      { id: "kpi-ocupacao", label: "Ocupação Média", valor: "--", cor: "bg-purple-50 text-purple-700 border-purple-200" },
    ];
    for (const kpi of kpis) {
      const card = criarElemento("div", { class: `rounded-lg border p-3 ${kpi.cor}` });
      card.innerHTML = `
        <div class="text-[11px] uppercase tracking-wide font-medium opacity-70">${kpi.label}</div>
        <div class="text-2xl font-bold mt-1" id="${kpi.id}">${kpi.valor}</div>
      `;
      grid.append(card);
    }
    this.#kpisElements = kpis.map((k) => document.getElementById(k.id));
    return grid;
  }

  /**
   * Renderiza os dados completos no dashboard.
   * @param {DadosAnalytics} dados Dados de analytics.
   */
  renderar(dados) {
    if (this.#destruido) throw new ErroAnalytics("Componente destruído.", "COMPONENTE_DESTUIDO");
    this.#dados = dados;

    // Atualiza KPIs
    this.#atualizarKPIs(dados);

    // Renderiza heatmap
    try {
      this.#heatmap?.renderar(dados.heatmap);
    } catch (erro) {
      console.error("[AnalyticsCharts] Erro ao renderizar heatmap:", erro);
      exibirToast("Erro ao renderizar heatmap.", "erro");
    }

    // Renderiza série temporal
    try {
      this.#linha?.renderar(dados.seriesTemporais);
    } catch (erro) {
      console.error("[AnalyticsCharts] Erro ao renderizar série temporal:", erro);
      exibirToast("Erro ao renderizar série temporal.", "erro");
    }
  }

  /** Atualiza os cards de KPI com os dados. */
  #atualizarKPIs(dados) {
    if (!this.#opcoes.mostrarKPIs || !this.#kpisElements) return;
    const celulas = dados.heatmap?.celulas ?? [];
    const pontos = dados.seriesTemporais?.pontos ?? [];

    const total = celulas.reduce((s, c) => s + c.total, 0);
    const teleconsultas = celulas.reduce((s, c) => s + (c.teleconsultas ?? 0), 0);
    const faltas = celulas.reduce((s, c) => s + (c.faltas ?? 0), 0);
    const ocupacao = pontos.length > 0
      ? pontos.reduce((s, p) => s + p.taxaOcupacao, 0) / pontos.length
      : 0;

    const valores = [String(total), String(teleconsultas), String(faltas), formatarPercentual(ocupacao)];
    this.#kpisElements?.forEach((el, i) => {
      if (el) el.textContent = valores[i] ?? "--";
    });
  }

  /** Exporta o heatmap e a série temporal como PNG. */
  #exportarPNG() {
    try {
      const links = [];
      if (this.#heatmap?.canvas) {
        const link = criarElemento("a", {
          download: "heatmap_agendamentos.png",
          href: this.#heatmap.canvas.toDataURL("image/png"),
        });
        link.click();
      }
      if (this.#linha?.canvas) {
        const link = criarElemento("a", {
          download: "serie_temporal.png",
          href: this.#linha.canvas.toDataURL("image/png"),
        });
        link.click();
      }
      exibirToast("Exportação concluída.", "sucesso");
    } catch (erro) {
      console.error("[AnalyticsCharts] Erro ao exportar:", erro);
      exibirToast("Erro ao exportar gráficos.", "erro");
    }
  }

  /** Retorna o elemento tooltip (acesso por subcomponentes). */
  get tooltip() {
    return this.#tooltip;
  }

  /** Retorna os dados atuais. */
  get dados() {
    return this.#dados;
  }

  /** Destroi o componente e libera recursos. */
  destruir() {
    this.#destruido = true;
    this.#heatmap?.destruir();
    this.#linha?.destruir();
    this.#tooltip?.remove();
    this.#container.innerHTML = "";
  }
}

/* ==========================================================================
 * Backward compatibility — exportar como module default + named
 * ========================================================================== */

export default { AnalyticsCharts, HeatmapTurnos, SerieTemporal, ErroAnalytics };