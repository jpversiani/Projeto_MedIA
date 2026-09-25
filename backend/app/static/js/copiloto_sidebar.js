/**
 * ============================================================================
 * MedIA — Copiloto Clínico (Painel Lateral) — Tela de Teleatendimento Médico
 * Card C14 — Home Office / Teleatendimento (APS / SUS)
 * ============================================================================
 *
 * Widget de painel lateral exibido na tela do médico durante teleconsulta:
 *   - Alertas piscantes de risco/alergia/interação medicamentosa
 *     (CSS próprio com `prefers-reduced-motion` — WCAG 2.3.3);
 *   - Botão "Preencher SOAP com Sugestão da IA" (auditado — CFM 2.314/2022);
 *   - Sugestões de exames complementares SUS (Sisreg/SIGTAP/PCDT);
 *   - Dosagens usuais SUS (RENAME 2022 / PCDT MS);
 *   - Conexão WebSocket em tempo real com snapshot + heartbeat.
 *
 * Segurança assistencial: campos SOAP já preenchidos pelo médico nunca são
 * sobrescritos pelo preenchimento automático (mesma regra do backend).
 *
 * Conformidade SUS/APS: CIAP-2, CID-10, método SOAP, identificação CNS/CPF.
 *
 * Uso:
 *   import { CopilotoSidebar } from '/static/js/copiloto_sidebar.js';
 *   const sidebar = new CopilotoSidebar('#copiloto-sidebar', {
 *     atendimentoId: 42,
 *     wsBase: '/api/v1/copiloto/ws',
 *     apiBase: '/api/v1/copiloto',
 *     profissionalId: 7,
 *   });
 *   sidebar.iniciar();
 *
 * Eventos escutados pelo componente hospedeiro (bubbling):
 *   - 'copiloto:soap-aplicado'  —{detail: {atendimento_id, campos_preenchidos}}
 *   - 'copiloto:alertas'        —{detail: {atendimento_id, alertas}}
 *   - 'copiloto:estado'         —{detail: CopilotoSnapshot}
 *   - 'copiloto:erro'           —{detail: {mensagem}}
 *
 * Exporta: CopilotoSidebar, CopilotoStore, validaCNS, validaCPF, validaCIAP2, validaCID10
 */

"use strict";

// ---------------------------------------------------------------------------
// Validações SUS/APS (reutilizáveis)
// ---------------------------------------------------------------------------

/**
 * Validação CNS pelo algoritmo DATASUS (15 dígitos).
 * @param {string} cns
 * @returns {boolean}
 */
function validaCNS(cns) {
  const d = String(cns ?? "").replace(/\D/g, "");
  if (d.length !== 15) return false;
  if (!["1", "2", "7", "8", "9"].includes(d[0])) return false;
  if (d[0] === "1" || d[0] === "2") {
    const soma = d.split("").reduce((acc, digit, i) => acc + parseInt(digit) * (15 - i), 0);
    return soma % 11 === 0;
  }
  // Provisório (7/8/9): validação PIS-style
  let soma = 0;
  for (let i = 0; i < 11; i++) soma += parseInt(d[i]) * (15 - i);
  let resto = soma % 11;
  let dv = 11 - resto;
  if (dv === 11) dv = 0;
  if (dv === 10) {
    soma += 2;
    resto = soma % 11;
    dv = 11 - resto;
  }
  return parseInt(d[11]) === dv;
}

/**
 * Validação CPF (11 dígitos).
 * @param {string} cpf
 * @returns {boolean}
 */
function validaCPF(cpf) {
  const d = String(cpf ?? "").replace(/\D/g, "");
  if (d.length !== 11 || /^(\d)\1{10}$/.test(d)) return false;
  for (let j = 9; j < 11; j++) {
    let soma = 0;
    for (let i = 0; i <= j; i++) soma += parseInt(d[i]) * (j + 2 - i);
    const resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) {
      if (parseInt(d[j + 1]) !== 0) return false;
    } else if (parseInt(d[j + 1]) !== resto) return false;
  }
  return true;
}

/**
 * Validação CIAP-2 (letra + 2 dígitos).
 * @param {string} ciap
 * @returns {boolean}
 */
function validaCIAP2(ciap) {
  return /^[A-Z]\d{2}$/i.test(ciap ?? "");
}

/**
 * Validação CID-10 (letra + até 4 caracteres alfanuméricos).
 * @param {string} cid
 * @returns {boolean}
 */
function validaCID10(cid) {
  return /^[A-Z]\d([A-Z]\d{0,2})?$/i.test(cid ?? "");
}

// ---------------------------------------------------------------------------
// Constantes visuais
// ---------------------------------------------------------------------------

/** Cores por severidade (Tailwind + variáveis CSS).
 *  Chaves em minúsculas para casar exatamente com `SeveridadeAlerta` do
 *  backend (`app.schemas.copiloto`) — enum serializado em minúsculas. */
const ESTILO_ALERTA = Object.freeze({
  critico: {
    border: "border-red-600",
    bg: "bg-red-50",
    text: "text-red-900",
    badge: "bg-red-600 text-white",
    label: "CRÍTICO",
    piscar: true,
  },
  alto: {
    border: "border-orange-500",
    bg: "bg-orange-50",
    text: "text-orange-900",
    badge: "bg-orange-500 text-white",
    label: "ALTO",
    piscar: true,
  },
  moderado: {
    border: "border-amber-500",
    bg: "bg-amber-50",
    text: "text-amber-900",
    badge: "bg-amber-400 text-white",
    label: "MODERADO",
    piscar: false,
  },
  info: {
    border: "border-blue-500",
    bg: "bg-blue-50",
    text: "text-blue-900",
    badge: "bg-blue-500 text-white",
    label: "INFO",
    piscar: false,
  },
});

/** Tipos de alerta que SEMPRE piscam, independentemente da severidade
 *  (alergia e risco são falhas de segurança assistencial — UI de alta saliência). */
const TIPOS_SEM_PRESCA_PISCANTE = Object.freeze(["alergia", "risco"]);

/** Mapeia TipoAlerta → ícone ARIA. */
const ICONE_ALERTA = Object.freeze({
  alergia: "⚠️",
  risco: "🔴",
  interacao_medicamentosa: "💊",
  dose_maxima_excedida: "💉",
  red_flag_clinica: "🚨",
  info: "ℹ️",
});

/**
 * CSS do painel (injetado uma única vez por documento).
 * Garante o estado PISCANTE dos alertas de risco/alergia mesmo quando o
 * Tailwind não injeta as animações, respeitando WCAG 2.3.3 e alto contraste.
 */
const CSS_COPILOTO = `
.copiloto-alerta--piscante {
  animation: copiloto-piscar-borda 1.2s ease-in-out infinite;
}
.copiloto-alerta--piscante .copiloto-badge-piscante {
  animation: copiloto-piscar-badge 1.2s ease-in-out infinite;
}
@keyframes copiloto-piscar-borda {
  0%, 100% { border-left-color: #dc2626; }
  50%      { border-left-color: #fecaca; }
}
@keyframes copiloto-piscar-badge {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%      { opacity: .45; transform: scale(1.08); }
}
@media (prefers-reduced-motion: reduce) {
  .copiloto-alerta--piscante,
  .copiloto-alerta--piscante .copiloto-badge-piscante { animation: none; }
}
@media (forced-colors: active) {
  .copiloto-alerta--piscante { border-left-color: Highlight; }
}
`;

/** Injeta (uma vez) o CSS do painel no documento hospedeiro. */
function injetarEstilosCopiloto() {
  if (document.getElementById("copiloto-sidebar-estilos")) return;
  const style = document.createElement("style");
  style.id = "copiloto-sidebar-estilos";
  style.textContent = CSS_COPILOTO;
  document.head.appendChild(style);
}

/** Tipos de evento WS aceitos (devem coincidir com backend EventoWS). */
const TIPO_WS = Object.freeze({
  SNAPSHOT_ALERTAS: "snapshot_alertas",
  ALERTA_NOVO: "alerta_novo",
  SOAP_ACEITO: "soap_aceito",
  PONG: "pong",
});

/** Seletores dos campos SOAP no formulário hospedeiro (tentativa sequencial). */
const SELETORES_SOAP = Object.freeze({
  subjetivo: [
    '#soap-subjetivo', '[name="soap_subjetivo"]', '#id_soap_subjetivo',
    'textarea[name="subjetivo"]', '[data-campo="subjetivo"]',
  ],
  objetivo: [
    '#soap-objetivo', '[name="soap_objetivo"]', '#id_soap_objetivo',
    'textarea[name="objetivo"]', '[data-campo="objetivo"]',
  ],
  avaliacao: [
    '#soap-avaliacao', '[name="soap_avaliacao"]', '#id_soap_avaliacao',
    'textarea[name="avaliacao"]', '[data-campo="avaliacao"]',
  ],
  plano: [
    '#soap-plano', '[name="soap_plano"]', '#id_soap_plano',
    'textarea[name="plano"]', '[data-campo="plano"]',
  ],
});

// ---------------------------------------------------------------------------
// Utilidades
// ---------------------------------------------------------------------------

/** Cria elemento DOM seguro (textContent evita XSS). */
function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "className") node.className = v;
    else if (k === "dataset") Object.entries(v).forEach(([dk, dv]) => { node.dataset[dk] = dv; });
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === "style" && typeof v === "object") Object.assign(node.style, v);
    else node.setAttribute(k, v);
  }
  for (const child of children) {
    if (child == null) continue;
    node.append(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return node;
}

/** Formata ISO 8601 para pt-BR. */
function formatarPtBr(iso) {
  try {
    return new Date(iso).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
  } catch {
    return iso;
  }
}

/** Debounce. */
function debounce(fn, ms = 200) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

// ---------------------------------------------------------------------------
// Estado (store reativo)
// ---------------------------------------------------------------------------

class CopilotoStore {
  /** @type {Map<string, Function[]>} */
  #ouvintes = new Map();

  constructor() {
    /** @type {{alertas: Array, soap: Object|null, exames: Array, dosagens: Array, paciente: Object|null, atualizado_em: string|null}} */
    this.estado = { alertas: [], soap: null, exames: [], dosagens: [], paciente: null, atualizado_em: null };
  }

  /** @param {string} chave */
  _inscrito(chave, fn) {
    if (!this.#ouvintes.has(chave)) this.#ouvintes.set(chave, []);
    this.#ouvintes.get(chave).push(fn);
  }

  /** @param {string} chave @param {*} dado */
  _emitir(chave, dado) {
    for (const fn of this.#ouvintes.get(chave) ?? []) fn(dado);
  }

  /** @param {Partial<Object>} patch */
  atualizar(patch) {
    Object.assign(this.estado, patch, { atualizado_em: new Date().toISOString() });
    this._emitir("estado", this.estado);
  }

  /** @param {Array} alertas */
  definirAlertas(alertas) {
    this.estado.alertas = alertas;
    this._emitir("alertas", alertas);
    this._emitir("estado", this.estado);
  }

  /** @param {Object|null} soap */
  definirSOAP(soap) {
    this.estado.soap = soap;
    this._emitir("soap", soap);
    this._emitir("estado", this.estado);
  }

  /** @param {Array} exames */
  definirExames(exames) {
    this.estado.exames = exames;
    this._emitir("exames", exames);
    this._emitir("estado", this.estado);
  }

  /** @param {Array} dosagens */
  definirDosagens(dosagens) {
    this.estado.dosagens = dosagens;
    this._emitir("dosagens", dosagens);
    this._emitir("estado", this.estado);
  }

  /** @param {Object|null} paciente */
  definirPaciente(paciente) {
    this.estado.paciente = paciente;
    this._emitir("paciente", paciente);
    this._emitir("estado", this.estado);
  }
}

// ---------------------------------------------------------------------------
// Widget principal
// ---------------------------------------------------------------------------

class CopilotoSidebar {
  /**
   * @param {string|HTMLElement} raiz Seletor CSS ou elemento.
   * @param {Object} opcoes
   * @param {number} opcoes.atendimentoId  ID do atendimento (obrigatório).
   * @param {string} [opcoes.wsBase='/api/v1/copiloto/ws']
   * @param {string} [opcoes.apiBase='/api/v1/copiloto']
   * @param {number|null} [opcoes.profissionalId=null]
   * @param {number} [opcoes.heartbeatMs=30000]
   * @param {number} [opcoes.reconnectMs=3000]
   */
  constructor(raiz, opcoes = {}) {
    if (!opcoes.atendimentoId) throw new Error("CopilotoSidebar: atendimentoId é obrigatório.");
    this._raiz = typeof raiz === "string" ? document.querySelector(raiz) : raiz;
    if (!(this._raiz instanceof HTMLElement)) throw new Error("CopilotoSidebar: raiz inválida.");
    this._atendimentoId = Number(opcoes.atendimentoId);
    this._wsBase = opcoes.wsBase ?? "/api/v1/copiloto/ws";
    this._apiBase = opcoes.apiBase ?? "/api/v1/copiloto";
    this._profissionalId = opcoes.profissionalId ?? null;
    this._heartbeatMs = opcoes.heartbeatMs ?? 30_000;
    this._reconnectMs = opcoes.reconnectMs ?? 3_000;

    /** @type {CopilotoStore} */
    this._store = new CopilotoStore();
    /** @type {WebSocket|null} */
    this._ws = null;
    /** @type {number|null} */
    this._timerHeartbeat = null;
    /** @type {number|null} */
    this._timerReconnect = null;
    /** @type {boolean} */
    this._destruido = false;
    /** @type {AbortController|null} */
    this._ctrlFetch = null;
  }

  // ------------------------------------------------------------------ //
  // Ciclo de vida                                                       //
  // ------------------------------------------------------------------ //

  /** Inicia o widget: carrega snapshot, conecta WS e renderiza. */
  async iniciar() {
    this._destruido = false;
    this._renderizar();
    await this._carregarSnapshot();
    this._conectarWS();
  }

  /** Destrói o widget, encerra WS e listeners. */
  destruir() {
    this._destruido = true;
    this._desconectarWS();
    if (this._timerHeartbeat) { clearInterval(this._timerHeartbeat); this._timerHeartbeat = null; }
    if (this._timerReconnect) { clearTimeout(this._timerReconnect); this._timerReconnect = null; }
    this._ctrlFetch?.abort();
    this._raiz.innerHTML = "";
  }

  // ------------------------------------------------------------------ //
  // API pública (observadores)                                         //
  // ------------------------------------------------------------------ //

  /** @param {Function} fn */
  onAlertas(fn) { this._store._inscrito("alertas", fn); }
  /** @param {Function} fn */
  onSOAP(fn) { this._store._inscrito("soap", fn); }
  /** @param {Function} fn */
  onEstado(fn) { this._store._inscrito("estado", fn); }

  // ------------------------------------------------------------------ //
  // Renderização                                                        //
  // ------------------------------------------------------------------ //

  /** Renderiza o esqueleto do painel. */
  _renderizar() {
    injetarEstilosCopiloto();
    this._raiz.innerHTML = `
      <aside class="copiloto-sidebar flex flex-col h-full bg-white border-l border-slate-200 shadow-lg"
             role="complementary" aria-label="Painel do Copiloto Clínico MedIA" data-copiloto-sidebar>
        <header class="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-slate-50">
          <h2 class="text-sm font-bold text-slate-800 flex items-center gap-2">
            <span class="copiloto-logo select-none" aria-hidden="true">🧠</span> Copiloto Clínico
          </h2>
          <span class="copiloto-status inline-flex items-center gap-1 text-xs text-slate-500" data-papel="status">
            <span class="w-2 h-2 rounded-full bg-slate-300" data-regiao="indicador"></span>
            <span data-regiao="status-texto">Conectando…</span>
          </span>
        </header>

        <section class="flex-1 overflow-y-auto p-3 space-y-3" data-regiao="conteudo">
          <div data-regiao="alertas" class="space-y-2" aria-live="polite" aria-atomic="true"></div>
          <div data-regiao="soap" class="space-y-2"></div>
          <div data-regiao="exames" class="space-y-2"></div>
          <div data-regiao="dosagens" class="space-y-2"></div>
        </section>

        <footer class="px-4 py-3 border-t border-slate-200 bg-slate-50 text-xs text-slate-500" data-regiao="rodape">
          MedIA CDS v1.0 — Sugestão apenas; decisão clínica é do médico.
        </footer>
      </aside>
    `;
  }

  /** @param {Array} alertas */
  _renderAlertas(alertas) {
    const container = this._raiz.querySelector('[data-regiao="alertas"]');
    if (!container) return;
    container.innerHTML = "";
    if (!alertas.length) {
      container.innerHTML = `<div class="text-xs text-slate-400 italic">Sem alertas no momento.</div>`;
      return;
    }
    for (const a of alertas) {
      const severidade = String(a.severidade ?? "info").toLowerCase();
      const s = ESTILO_ALERTA[severidade] ?? ESTILO_ALERTA.info;
      const icon = ICONE_ALERTA[a.tipo] ?? "🔔";
      const piscante = s.piscar === true || TIPOS_SEM_PRESCA_PISCANTE.includes(a.tipo);
      const descricao = a.descricao ?? "";
      const titulo = a.titulo || descricao.substring(0, 40) || "Alerta clínico";
      const card = el("div", {
        className: [
          "copiloto-alerta",
          `copiloto-alerta--${severidade}`,
          piscante ? "copiloto-alerta--piscante" : "",
          "border-l-4 rounded-r-lg p-3",
          s.bg, s.border, s.text, "text-xs shadow-sm",
        ].filter(Boolean).join(" "),
        dataset: { tipo: a.tipo, severidade, alertaId: a.id, piscar: String(piscante) },
        role: "alert",
      }, [
        el("div", { className: "flex items-start justify-between gap-2" }, [
          el("strong", { className: "flex items-center gap-1" }, [
            el("span", { "aria-hidden": "true" }, [icon]),
            el("span", {}, [titulo]),
          ]),
          el("span", {
            className: `copiloto-badge ${piscante ? "copiloto-badge-piscante" : ""} text-[10px] font-bold px-1.5 py-0.5 rounded ${s.badge}`,
          }, [s.label]),
        ]),
        a.cid10 ? el("p", { className: "mt-1 font-mono text-[10px] opacity-70" }, [`CID-10: ${a.cid10}`]) : null,
        a.ciap2 ? el("p", { className: "mt-1 font-mono text-[10px] opacity-70" }, [`CIAP-2: ${a.ciap2}`]) : null,
        el("p", { className: "mt-1 opacity-90" }, [descricao]),
        el("p", { className: "mt-1 font-medium" }, [`Conduta: ${a.conduta_recomendada ?? "—"}`]),
        el("p", { className: "mt-1 opacity-60" }, [
          `Fonte: ${a.fonte ?? "—"} · ${formatarPtBr(a.criado_em)}`,
        ]),
      ]);
      container.appendChild(card);
    }
    this._emitirEvento("alertas", { atendimento_id: this._atendimentoId, alertas });
  }

  /** @param {Object|null} soap */
  _renderSOAP(soap) {
    const container = this._raiz.querySelector('[data-regiao="soap"]');
    if (!container) return;
    container.innerHTML = "";
    if (!soap) {
      container.innerHTML = `<div class="text-xs text-slate-400 italic">Sem sugestão de SOAP disponível.</div>`;
      return;
    }
    const card = el("div", { className: "border border-slate-200 rounded-lg p-3 bg-white shadow-sm" });
    card.appendChild(el("h3", { className: "text-xs font-bold text-slate-700 mb-2" }, ["📋 Sugestão SOAP — IA"]));
    const campo = (rotulo, valor) => {
      const wrapper = el("div", { className: "mb-1.5" });
      wrapper.appendChild(el("p", { className: "text-[10px] uppercase font-bold text-slate-400" }, [rotulo]));
      wrapper.appendChild(el("p", { className: "text-xs text-slate-700 whitespace-pre-wrap" }, [valor?.substring(0, 300) ?? ""]));
      return wrapper;
    };
    card.appendChild(campo("S", soap.subjetivo));
    card.appendChild(campo("O", soap.objetivo));
    card.appendChild(campo("A", soap.avaliacao));
    card.appendChild(campo("P", soap.plano));
    const meta = el("p", { className: "mt-2 text-[10px] text-slate-400" }, [
      `Confiança: ${(soap.confianca * 100).toFixed(0)}% · ${soap.modelo} · ${formatarPtBr(soap.gerado_em)}`,
    ]);
    card.appendChild(meta);
    container.appendChild(card);
  }

  /** @param {Array} exames */
  _renderExames(exames) {
    const container = this._raiz.querySelector('[data-regiao="exames"]');
    if (!container) return;
    container.innerHTML = "";
    if (!exames.length) return;
    container.appendChild(el("h3", { className: "text-xs font-bold text-slate-700" }, ["🔬 Exames complementares SUS"]));
    for (const ex of exames) {
      const tag = ex.prioridade === "urgente" ? "urgente" : "rotina";
      container.appendChild(el("div", {
        className: "text-xs border border-slate-200 rounded px-2 py-1 flex items-center justify-between",
        dataset: { exameId: ex.id },
      }, [
        el("span", {}, [`${ex.nome} (${ex.justificativa?.substring(0, 60) ?? ""})`]),
        el("span", { className: `text-[10px] font-bold px-1 rounded ${tag === "urgente" ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-600"}` }, [tag]),
      ]));
    }
  }

  /** @param {Array} dosagens */
  _renderDosagens(dosagens) {
    const container = this._raiz.querySelector('[data-regiao="dosagens"]');
    if (!container) return;
    container.innerHTML = "";
    if (!dosagens.length) return;
    container.appendChild(el("h3", { className: "text-xs font-bold text-slate-700" }, ["💊 Dosagens usuais SUS (RENAME)"]));
    for (const d of dosagens) {
      container.appendChild(el("div", {
        className: "text-xs border border-slate-200 rounded px-2 py-1",
        dataset: { dosagemId: d.id },
      }, [
        el("strong", {}, [d.medicamento]),
        el("p", { className: "text-slate-500" }, [`${d.apresentacao} · ${d.posologia}`]),
        el("p", { className: "text-[10px] text-slate-400" }, [d.referencia]),
      ]));
    }
  }

  /** Renderiza o botão SOAP + sugestão. */
  _renderBotaoSOAP(soapDisponivel) {
    const container = this._raiz.querySelector('[data-regiao="soap"]');
    if (!container) return;
    const btn = el("button", {
      type: "button",
      className: "w-full rounded-lg bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white text-sm font-bold py-2 px-4 shadow transition disabled:opacity-50",
      disabled: !soapDisponivel,
      "aria-label": "Preencher SOAP com Sugestão da IA",
      dataset: { papel: "btn-soap" },
    }, [soapDisponivel ? "📝 Preencher SOAP com Sugestão da IA" : "⏳ Carregando sugestão…"]);
    btn.addEventListener("click", () => this._aplicarSugestaoSOAP());
    container.appendChild(btn);
  }

  // ------------------------------------------------------------------ //
  // Dados (REST)                                                       //
  // ------------------------------------------------------------------ //

  async _carregarSnapshot() {
    this._ctrlFetch = new AbortController();
    try {
      const [alertasRes, sugestoesRes] = await Promise.all([
        fetch(`${this._apiBase}/atendimentos/${this._atendimentoId}/alertas`, { signal: this._ctrlFetch.signal }),
        fetch(`${this._apiBase}/atendimentos/${this._atendimentoId}/sugestoes`, { signal: this._ctrlFetch.signal }),
      ]);
      if (!alertasRes.ok || !sugestoesRes.ok) throw new Error(`HTTP ${alertasRes.status}/${sugestoesRes.status}`);
      const alertas = await alertasRes.json();
      const sugestoes = await sugestoesRes.json();
      this._store.definirAlertas(alertas);
      this._store.definirSOAP(sugestoes.soap ?? null);
      this._store.definirExames(sugestoes.exames_complementares ?? []);
      this._store.definirDosagens(sugestoes.dosagens_sus ?? []);
      this._renderAlertas(alertas);
      this._renderSOAP(sugestoes.soap ?? null);
      this._renderExames(sugestoes.exames_complementares ?? []);
      this._renderDosagens(sugestoes.dosagens_sus ?? []);
      this._renderBotaoSOAP(!!sugestoes.soap);
    } catch (err) {
      if (this._destruido) return;
      console.error("[Copiloto] Erro no snapshot:", err);
      this._emitirEvento("erro", { mensagem: err.message });
    }
  }

  // ------------------------------------------------------------------ //
  // WebSocket                                                           //
  // ------------------------------------------------------------------ //

  _conectarWS() {
    if (this._ws?.readyState === WebSocket.OPEN) return;
    const url = `${this._wsBase}/${this._atendimentoId}`;
    try {
      this._ws = new WebSocket(url.replace(/^http/, "ws"));
    } catch (err) {
      console.warn("[Copiloto] WS indisponível:", err.message);
      this._agendarReconnect();
      return;
    }
    this._ws.onopen = () => {
      this._setStatus("online", "Conectado");
      this._iniciarHeartbeat();
      this._limparReconnect();
    };
    this._ws.onmessage = (evt) => this._aoMensagemWS(evt.data);
    this._ws.onclose = () => {
      this._setStatus("offline", "Desconectado");
      this._pararHeartbeat();
      if (!this._destruido) this._agendarReconnect();
    };
    this._ws.onerror = () => { this._ws?.close(); };
  }

  _desconectarWS() {
    this._pararHeartbeat();
    if (this._ws) {
      try { this._ws.close(1000, "destruir"); } catch {}
      this._ws = null;
    }
  }

  _agendarReconnect() {
    if (this._destruido) return;
    this._timerReconnect = setTimeout(() => this._conectarWS(), this._reconnectMs);
  }

  _limparReconnect() {
    if (this._timerReconnect) { clearTimeout(this._timerReconnect); this._timerReconnect = null; }
  }

  _iniciarHeartbeat() {
    this._pararHeartbeat();
    this._timerHeartbeat = setInterval(() => {
      if (this._ws?.readyState === WebSocket.OPEN) this._ws.send("ping");
    }, this._heartbeatMs);
  }

  _pararHeartbeat() {
    if (this._timerHeartbeat) { clearInterval(this._timerHeartbeat); this._timerHeartbeat = null; }
  }

  /** @param {string} raw */
  _aoMensagemWS(raw) {
    try {
      const msg = JSON.parse(raw);
      switch (msg.tipo) {
        case TIPO_WS.SNAPSHOT_ALERTAS:
          this._store.definirAlertas(msg.dados?.alertas ?? []);
          this._renderAlertas(msg.dados?.alertas ?? []);
          break;
        case TIPO_WS.ALERTA_NOVO:
          this._store.definirAlertas([...(this._store.estado.alertas ?? []), msg.dados?.alerta].filter(Boolean));
          this._renderAlertas(this._store.estado.alertas);
          break;
        case TIPO_WS.SOAP_ACEITO:
          this._setStatus("online", `SOAP aceito (${msg.dados?.campos_preenchidos?.length ?? 0} campos)`);
          this._carregarSnapshot();
          break;
        case TIPO_WS.PONG:
          this._setStatus("online", "Conectado");
          break;
      }
    } catch { /* mensagem não-JSON ignorada */ }
  }

  /** @param {'online'|'offline'} estado @param {string} texto */
  _setStatus(estado, texto) {
    const indicador = this._raiz.querySelector('[data-regiao="indicador"]');
    const textoEl = this._raiz.querySelector('[data-regiao="status-texto"]');
    if (indicador) {
      indicador.className = `w-2 h-2 rounded-full ${estado === "online" ? "bg-green-500" : "bg-slate-300"}`;
    }
    if (textoEl) textoEl.textContent = texto;
  }

  // ------------------------------------------------------------------ //
  // Ações                                                               //
  // ------------------------------------------------------------------ //

  async _aplicarSugestaoSOAP() {
    const soap = this._store.estado.soap;
    if (!soap) return;
    const camposPreenchidos = [];
    for (const [campo, seletores] of Object.entries(SELETORES_SOAP)) {
      const valor = soap[campo];
      if (!valor) continue;
      for (const sel of seletores) {
        const target = this._raiz.closest("main, .teleatendimento, #app") ?? document;
        const elCampo = target.querySelector(sel);
        if (elCampo && (elCampo.tagName === "TEXTAREA" || elCampo.tagName === "INPUT" || elCampo.isContentEditable)) {
          elCampo.value = valor;
          elCampo.dispatchEvent(new Event("input", { bubbles: true }));
          camposPreenchidos.push(campo);
          break;
        }
      }
    }
    this._registrarAuditoria("soap_aceito", { campos: camposPreenchidos });
    this._emitirEvento("soap-aplicado", { atendimento_id: this._atendimentoId, campos_preenchidos: camposPreenchidos });
    try {
      await fetch(`${this._apiBase}/atendimentos/${this._atendimentoId}/soap/aceitar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subjetivo: soap.subjetivo,
          objetivo: soap.objetivo,
          avaliacao: soap.avaliacao,
          plano: soap.plano,
          cid10: soap.cid10_sugerido,
          ciap2: soap.ciap2_sugerido,
          profissional_id: this._profissionalId,
          origem: "IA_ACEITA",
        }),
      });
    } catch (err) {
      console.warn("[Copiloto] Erro ao registrar aceite:", err);
    }
  }

  /** @param {string} acao @param {*} detalhe */
  _registrarAuditoria(acao, detalhe) {
    try {
      fetch(`${this._apiBase}/atendimentos/${this._atendimentoId}/auditoria`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ acao, detalhe, profissional_id: this._profissionalId, origem: "WIDGET_JS" }),
      }).catch(() => {});
    } catch {}
  }

  /** @param {string} nome @param {*} detail */
  _emitirEvento(nome, detail) {
    this._raiz.dispatchEvent(new CustomEvent(`copiloto:${nome}`, { detail, bubbles: true, composed: true }));
  }
}

// ---------------------------------------------------------------------------
// Auto-inicialização via atributo data-copiloto-sidebar
// ---------------------------------------------------------------------------

function _autoIniciar() {
  document.querySelectorAll("[data-copiloto-sidebar]").forEach((node) => {
    if (node.dataset.copilotoInstanciado) return;
    const atendimentoId = Number(node.dataset.atendimentoId);
    const profissionalId = node.dataset.profissionalId ? Number(node.dataset.profissionalId) : null;
    const wsBase = node.dataset.wsBase ?? undefined;
    const apiBase = node.dataset.apiBase ?? undefined;
    try {
      const inst = new CopilotoSidebar(node, { atendimentoId, profissionalId, wsBase, apiBase });
      node.dataset.copilotoInstanciado = "true";
      inst.iniciar();
      node._copilotoInstancia = inst;
    } catch (err) {
      console.error("[Copiloto] Falha ao iniciar:", err);
    }
  });
}
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", _autoIniciar);
} else {
  _autoIniciar();
}

// ---------------------------------------------------------------------------
// Exportações ES Module
// ---------------------------------------------------------------------------

export { CopilotoSidebar, CopilotoStore, validaCNS, validaCPF, validaCIAP2, validaCID10 };
export default CopilotoSidebar;