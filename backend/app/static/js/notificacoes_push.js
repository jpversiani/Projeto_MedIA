/**
 * MedIA — Notificações Push (Web Notifications API)
 * Componente C8 — Notificações e Agendamento Ativo
 * ==================================================
 * Projeto MedIA — SUS / Atenção Primária à Saúde (APS)
 *
 * Suporte a Web Notifications API para o fluxo de teleconsulta:
 *
 *   1. TELECONSULTA_LEMBRETE   — lembrete disparado 15 min antes do início;
 *   2. PACIENTE_EM_SALA        — aviso ao profissional quando o paciente
 *                                  entra na sala de espera virtual;
 *   3. CONFIRMACAO_PRESENCA    — confirmação de presença do paciente.
 *
 * Conformidade:
 *   - LGPD/CFM: notificações carregam APENAS dados mínimos (nome, CNS/CPF
 *     mascarado, horário). Campos clínicos (CID-10, CIAP-2, SOAP) são
 *     removidos por lista de bloqueio antes de qualquer exibição.
 *   - Identificação prioriza CNS (padrão SUS) com fallback a CPF mascarado.
 *   - Transporte: WebSocket (tempo real) com fallback de polling REST.
 *   - Pydantic v2 / SQLAlchemy 2.0 no backend; Python 3.12.
 *
 * Uso:
 *   <script src="/static/js/notificacoes_push.js"></script>
 *   <script>
 *     const push = new MedIANotificacoes.NotificacoesPush({
 *       wsUrl: 'wss://host/ws/notificacoes',
 *       apiBase: '/api/v1',
 *     });
 *     await push.iniciar();
 *   </script>
 */

/* eslint-env browser */

(function (global) {
  'use strict';

  // ---------------------------------------------------------------------------
  // Constantes
  // ---------------------------------------------------------------------------

  /** Tipos de evento suportados pelo componente. */
  const TIPOS_EVENTO = Object.freeze({
    TELECONSULTA_LEMBRETE: 'TELECONSULTA_LEMBRETE',
    PACIENTE_EM_SALA: 'PACIENTE_EM_SALA',
    CONFIRMACAO_PRESENCA: 'CONFIRMACAO_PRESENCA',
  });

  /** Antecedência do lembrete em relação ao início da teleconsulta (15 min). */
  const ANTECEDENCIA_LEMBRETE_MS = 15 * 60 * 1000;

  /** Intervalo padrão de polling REST (30 s). */
  const INTERVALO_POLLING_PADRAO_MS = 30_000;

  /** Campos clínicos sensíveis que NUNCA devem aparecer em notificações do SO (LGPD). */
  const CAMPOS_SENSIVEIS = Object.freeze([
    'cid10', 'ciap2', 'descricao_clinica', 'soap', 'anamnese',
    'evolucao_soap', 'motivo_consulta', 'diagnostico_ciap2', 'diagnostico_cid10',
  ]);

  /** Prefixo usado para armazenar timers e agendamentos no escopo do módulo. */
  const PREFIXO_STORAGE = 'media_notificacao_';

  // ---------------------------------------------------------------------------
  // Utilitários
  // ---------------------------------------------------------------------------

  /** Retorna o timestamp atual em milissegundos. */
  function agoraMs() { return Date.now(); }

  /**
   * Mascara o CPF no formato ***.***.XXX-XX.
   * @param {string} cpf CPF com 11 dígitos.
   * @returns {string} CPF mascarado.
   */
  function mascararCpf(cpf) {
    const limpo = String(cpf ?? '').replace(/\D/g, '');
    if (limpo.length < 3) return '***.***.**';
    return `***.***.${limpo.slice(-3)}-${limpo.slice(-2)}`;
  }

  /**
   * Retorna a identificação do paciente priorizando CNS (SUS) com fallback CPF mascarado.
   * @param {{cns?: string|null, cpf?: string|null, nome?: string}} paciente
   * @returns {string} Identificação formatada.
   */
  function formatarIdentificacao(paciente) {
    const cns = (paciente?.cns ?? '').replace(/\D/g, '');
    if (cns.length >= 15) return `CNS: ${cns}`;
    const cpf = (paciente?.cpf ?? '').replace(/\D/g, '');
    if (cpf.length >= 11) return `CPF: ${mascararCpf(cpf)}`;
    return paciente?.nome ?? 'Paciente não identificado';
  }

  /**
   * Remove campos sensíveis de um objeto de dados (cópia rasa).
   * @param {Object} dados Objeto original.
   * @returns {Object} Cópia sem campos sensíveis.
   */
  function sanitizar(dados) {
    const limpo = { ...dados };
    for (const campo of CAMPOS_SENSIVEIS) {
      delete limpo[campo];
    }
    return limpo;
  }

  /**
   * Formata um instante ISO ou Date para string local legível (pt-BR).
   * @param {string|Date} instante
   * @returns {string} Horários formatados.
   */
  function formatarHorario(instante) {
    const d = instante instanceof Date ? instante : new Date(instante);
    if (Number.isNaN(d.getTime())) return '--:--';
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  /**
   * Calcula o delta em ms entre agora e o instante informado.
   * @param {string|Date} instante
   * @returns {number} Delta em ms (negativo se já passou).
   */
  function deltaAte(instante) {
    const d = instante instanceof Date ? instante : new Date(instante);
    return d.getTime() - Date.now();
  }

  // ---------------------------------------------------------------------------
  // Classe principal
  // ---------------------------------------------------------------------------

  class NotificacoesPush {
    /**
     * @param {Object} [opcoes]
     * @param {string}  [opcoes.apiBase='/api/v1']          Base da API REST.
     * @param {string}  [opcoes.wsUrl=null]                  URL WebSocket (opcional).
     * @param {number}  [opcoes.antecedenciaMs=900000]       Antecedência do lembrete (ms).
     * @param {number}  [opcoes.intervaloPollingMs=30000]    Intervalo de polling (ms).
     * @param {string}  [opcoes.canal='media-notificacoes']  Canal de notificação.
     * @param {ServiceWorkerRegistration} [opcoes.registroSW=null] Registro do Service Worker.
     * @param {Function} [opcoes.onNotificacao=null]         Hook para testes/telemetria.
     */
    constructor(opcoes = {}) {
      this.apiBase = opcoes.apiBase ?? '/api/v1';
      this.wsUrl = opcoes.wsUrl ?? null;
      this.antecedenciaMs = opcoes.antecedenciaMs ?? ANTECEDENCIA_LEMBRETE_MS;
      this.intervaloPollingMs = opcoes.intervaloPollingMs ?? INTERVALO_POLLING_PADRAO_MS;
      this.canal = opcoes.canal ?? 'media-notificacoes';
      this._permissao = 'default';
      this._timers = new Set();
      this._agendamentos = new Map();
      this._idsProcessados = new Set();
      this._ws = null;
      this._pollingTimer = null;
      this._tentativaReconexao = 0;
      this._destruido = false;
      this._registroSW = opcoes.registroSW ?? null;
      this._onNotificacao = opcoes.onNotificacao ?? null;
    }

    // ------------------------------------------------------------------ //
    // Ciclo de vida
    // ------------------------------------------------------------------ //

    /**
     * Solicita permissão de notificação e inicia transporte (WS ou polling).
     * @returns {Promise<string>} Estado da permissão ('granted'|'denied'|'unsupported').
     */
    async iniciar() {
      this._permissao = await pedirPermissao();
      if (this._permissao !== 'granted') {
        console.warn('[NotificacoesPush] Permissão não concedida:', this._permissao);
      }
      this._conectarTransporte();
      return this._permissao;
    }

    /** Encerra todos os listeners, timers e conexões. */
    destruir() {
      this._destruido = true;
      for (const timer of this._timers) {
        clearTimeout(timer);
        clearInterval(timer);
      }
      this._timers.clear();
      this._agendamentos.clear();
      this._idsProcessados.clear();
      this._desconectarWS();
      if (this._pollingTimer) {
        clearTimeout(this._pollingTimer);
        this._pollingTimer = null;
      }
    }

    // ------------------------------------------------------------------ //
    // Transporte
    // ------------------------------------------------------------------ //

    /** Conecta WebSocket se disponível; senão inicia polling. */
    _conectarTransporte() {
      if (this.wsUrl && typeof WebSocket !== 'undefined') {
        this._conectarWS();
      } else {
        this._iniciarPolling();
      }
    }

    /** Estabelece conexão WebSocket com reconexão automática. */
    _conectarWS() {
      try {
        this._ws = new WebSocket(this.wsUrl);
      } catch {
        this._iniciarPolling();
        return;
      }

      this._ws.addEventListener('open', () => {
        this._tentativaReconexao = 0;
        this._ws.send(
          JSON.stringify({ tipo: 'inscricao', canal: this.canal })
        );
      });

      this._ws.addEventListener('message', (evento) => {
        try {
          const dados = JSON.parse(evento.data);
          this._processarMensagem(dados);
        } catch {
          // Mensagem malformada — ignorar.
        }
      });

      this._ws.addEventListener('close', () => {
        if (this._destruido) return;
        this._tentativaReconexao = Math.min(this._tentativaReconexao + 1, 10);
        const atraso = Math.min(1000 * 2 ** this._tentativaReconexao, 30_000);
        const t = setTimeout(() => this._conectarWS(), atraso);
        this._timers.add(t);
      });

      this._ws.addEventListener('error', () => {
        this._ws?.close();
        this._iniciarPolling();
      });
    }

    /** Encerra a conexão WebSocket ativa. */
    _desconectarWS() {
      if (this._ws) {
        this._ws.close();
        this._ws = null;
      }
    }

    /** Inicia polling REST periódico para notificações pendentes. */
    _iniciarPolling() {
      if (this._pollingTimer) return;
      const executar = async () => {
        if (this._destruido) return;
        try {
          const resposta = await fetch(
            `${this.apiBase}/notificacoes/pendientes?canal=${encodeURIComponent(this.canal)}`,
            { headers: { Accept: 'application/json' } }
          );
          if (!resposta.ok) return;
          const lista = await resposta.json();
          if (Array.isArray(lista)) {
            for (const item of lista) {
              this._processarMensagem(item);
            }
          }
        } catch {
          // Falha de rede — silently retry no próximo ciclo.
        }
        this._pollingTimer = setTimeout(executar, this.intervaloPollingMs);
        this._timers.add(this._pollingTimer);
      };
      executar();
    }

    // ------------------------------------------------------------------ //
    // Processamento de mensagens
    // ------------------------------------------------------------------ //

    /**
     * Roteia a mensagem recebida ao handler correspondente ao tipo.
     * @param {Object} dados Dados da mensagem.
     */
    _processarMensagem(dados) {
      if (!dados || typeof dados !== 'object') return;
      const id = dados.id ?? dados.teleconsulta_id ?? dados.hash;
      if (id && this._idsProcessados.has(id)) return;
      if (id) this._idsProcessados.add(id);

      switch (dados.tipo) {
        case TIPOS_EVENTO.TELECONSULTA_LEMBRETE:
          this._aoLembrete(dados);
          break;
        case TIPOS_EVENTO.PACIENTE_EM_SALA:
          this._aoPacienteEmSala(dados);
          break;
        case TIPOS_EVENTO.CONFIRMACAO_PRESENCA:
          this._aoConfirmacaoPresenca(dados);
          break;
        default:
          this._aoGenerico(dados);
      }
    }

    /**
     * Handler para TELECONSULTA_LEMBRETE — agenda notificação 15 min antes.
     * @param {Object} dados { teleconsulta_id, inicio_em, paciente, profissional, link_sala, ... }
     */
    _aoLembrete(dados) {
      const inicio = new Date(dados.inicio_em);
      if (Number.isNaN(inicio.getTime())) return;

      const delta = deltaAte(inicio) - this.antecedenciaMs;
      const agora = agoraMs();

      // Se já passou o janela, ignora.
      if (delta <= 0 && agora > inicio.getTime()) return;

      // Cancela agendamento anterior se existir.
      this._cancelarTimer(dados.teleconsulta_id);

      const timer = setTimeout(() => {
        this._exibirNotificacao({
          titulo: `Lembrete: ${dados.profissional ?? 'Teleconsulta'}`,
          corpo: `Início em ${formatarHorario(inicio)} — ${formatarIdentificacao(dados.paciente)}`,
          dados: sanitizar(dados),
          tag: `lembrete-${dados.teleconsulta_id}`,
        });
        this._agendamentos.delete(dados.teleconsulta_id);
      }, Math.max(delta, 0));

      this._timers.add(timer);
      this._agendamentos.set(dados.teleconsulta_id, timer);
    }

    /**
     * Handler para PACIENTE_EM_SALA — notificação imediata ao profissional.
     * @param {Object} dados { teleconsulta_id, paciente, sala, ... }
     */
    _aoPacienteEmSala(dados) {
      this._exibirNotificacao({
        titulo: 'Paciente na sala de espera',
        corpo: `${formatarIdentificacao(dados.paciente)} — Sala: ${dados.sala?.codigo ?? '—'}`,
        dados: sanitizar(dados),
        tag: `sala-${dados.teleconsulta_id}`,
      });
    }

    /**
     * Handler para CONFIRMACAO_PRESENCA — confirmação de presença do paciente.
     * @param {Object} dados { teleconsulta_id, paciente, data_hora, ... }
     */
    _aoConfirmacaoPresenca(dados) {
      this._exibirNotificacao({
        titulo: 'Presença confirmada',
        corpo: `${formatarIdentificacao(dados.paciente)} confirmou presença às ${formatarHorario(dados.data_hora)}`,
        dados: sanitizar(dados),
        tag: `presenca-${dados.teleconsulta_id}`,
      });
    }

    /** Handler genérico para tipos não mapeados. */
    _aoGenerico(dados) {
      this._exibirNotificacao({
        titulo: dados.tipo ?? 'Notificação',
        corpo: dados.mensagem ?? dados.texto ?? '',
        dados: sanitizar(dados),
        tag: `gen-${dados.teleconsulta_id ?? ''}`,
      });
    }

    // ------------------------------------------------------------------ //
    // Exibição de notificação
    // ------------------------------------------------------------------ //

    /**
     * Exibe notificação via Web Notifications API (ou Service Worker push).
     * @param {{titulo: string, corpo: string, dados: Object, tag: string}} opts
     */
    _exibirNotificacao({ titulo, corpo, dados, tag }) {
      if (this._permissao !== 'granted' && this._permissao !== 'default') return;

      // Tenta Service Worker Push registration primeiro.
      if (this._registroSW?.showNotification) {
        try {
          this._registroSW.showNotification(titulo, {
            body: corpo,
            tag,
            data: dados,
            requireInteraction: false,
            silent: false,
          });
        } catch {
          // Fallback para Notification nativo.
        }
      }

      if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
        try {
          const notif = new Notification(titulo, { body: corpo, tag });
          notif.onclick = () => {
            global.dispatchEvent(new CustomEvent('media-notificacao-click', { detail: { dados } }));
            notif.close();
          };
          notif.onerror = () => { /* silencioso */ };
        } catch {
          // Navegador sem suporte a Notification constructor.
        }
      }

      // Dispara hook para testes/telemetria.
      if (typeof this._onNotificacao === 'function') {
        this._onNotificacao({ tipo: 'notificacao', titulo, corpo, dados, tag, timestamp: new Date().toISOString() });
      }

      // Mantém histórico em memória para inspeção.
      if (!global.__notificacoesCriadas) global.__notificacoesCriadas = [];
      global.__notificacoesCriadas.push({ titulo, corpo, dados, tag, timestamp: Date.now() });
    }

    // ------------------------------------------------------------------ //
    // Utilidades internas
    // ------------------------------------------------------------------ //

    /** Cancela o timer de agendamento de uma teleconsulta. */
    _cancelarTimer(teleconsultaId) {
      const timer = this._agendamentos.get(teleconsultaId);
      if (timer) {
        clearTimeout(timer);
        this._timers.delete(timer);
        this._agendamentos.delete(teleconsultaId);
      }
    }

    /**
     * Agenda manualmente um lembrete para uma teleconsulta.
     * @param {Object} dados { teleconsulta_id, inicio_em, paciente, profissional }
     * @returns {boolean} true se agendado com sucesso.
     */
    agendarLembrete(dados) {
      if (!dados?.teleconsulta_id || !dados?.inicio_em) return false;
      this._aoLembrete(dados);
      return true;
    }

    /**
     * Processa uma mensagem recebida (API pública para testes).
     * @param {Object} dados
     */
    receberMensagem(dados) {
      this._processarMensagem(dados);
    }

    /** Retorna a quantidade de notificações já processadas (deduplicação). */
    get idsProcessados() { return new Set(this._idsProcessados); }

    /** Retorna a permissão atual. */
    get permissao() { return this._permissao; }
  }

  // ---------------------------------------------------------------------------
  // Polyfills para ambiente de teste
  // ---------------------------------------------------------------------------

  /** FakeNotification para ambientes sem DOM (testes unitários). */
  class FakeNotification {
    static #permissao = 'granted';
    static #instancias = [];

    constructor(titulo, opcoes = {}) {
      this.titulo = titulo;
      this.corpo = opcoes.body ?? '';
      this.tag = opcoes.tag ?? '';
      this.data = opcoes.data ?? null;
      FakeNotification.#instancias.push(this);
      this.closed = false;
    }
    close() { this.closed = true; }
    static get permission() { return FakeNotification.#permissao; }
    static set permission(v) { FakeNotification.#permissao = v; }
    static get instancias() { return [...FakeNotification.#instancias]; }
    static clearInstancias() { FakeNotification.#instancias = []; }
    static requestPermission(cb) {
      const p = Promise.resolve(FakeNotification.#permissao);
      if (cb) p.then(cb);
      return p;
    }
  }

  /** FakeWebSocket para ambientes sem WebSocket (testes unitários). */
  class FakeWebSocket {
    static #instancia = null;
    static #mensagens = [];

    constructor(url) {
      this.url = url;
      this.readyState = 0; // CONNECTING
      FakeWebSocket.#instancia = this;
      this.onopen = null;
      this.onmessage = null;
      this.onclose = null;
      this.onerror = null;
    }
    send(_data) {}
    close() { this.readyState = 3; this.onclose?.(); }
    /** Simula abertura do WebSocket pelo servidor. */
    _servidorAberto() { this.readyState = 1; this.onopen?.(); }
    /** Simula recebimento de mensagem do servidor. */
    _servidorMensagem(dados) {
      FakeWebSocket.#mensagens.push(dados);
      this.onmessage?.({ data: JSON.stringify(dados) });
    }
    /** Simula fechamento pelo servidor. */
    _servidorFechar() { this.readyState = 3; this.onclose?.(); }
    static get instancia() { return FakeWebSocket.#instancia; }
    static get mensagens() { return [...FakeWebSocket.#mensagens]; }
    static clearMensagens() { FakeWebSocket.#mensagens = []; }
  }

  // Substitu globals apenas se não nativos (ambiente Node/teste).
  if (typeof globalThis.Notification === 'undefined') {
    globalThis.Notification = FakeNotification;
  }
  if (typeof globalThis.WebSocket === 'undefined') {
    globalThis.WebSocket = FakeWebSocket;
  }

  // ---------------------------------------------------------------------------
  // Exportação
  // ---------------------------------------------------------------------------

  const modulo = {
    NotificacoesPush,
    FakeNotification,
    FakeWebSocket,
    TIPOS_EVENTO,
    ANTECEDENCIA_LEMBRETE_MS,
    INTERVALO_POLLING_PADRAO_MS,
    CAMPOS_SENSIVEIS,
    mascararCpf,
    formatarIdentificacao,
    sanitizar,
    formatarHorario,
    pedirPermissao: () => Promise.resolve('granted'),
  };

  // Expõe como namespace global para uso sem módulo.
  global.MedIANotificacoes = modulo;

  // Export ES Module quando disponível.
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = modulo;
  }

})(typeof window !== 'undefined' ? window : globalThis);
