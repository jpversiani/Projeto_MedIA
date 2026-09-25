/**
 * MedIA — Notificações Push (Web Notifications API)
 * Componente C32
 * ...
 */

{
  "tipo": "TELECONSULTA_LEMBRETE",
  "cns_paciente": "700000000000000" (or null),
  "cpf_paciente": "...",
  "teleconsulta_id": "...",
  "inicio_em": "2025-01-01T10:00:00-03:00",
  "profissional": "Dr. ...",
  "link_sala": "/teleconsulta/sala/..."
}

/* eslint-env browser */
/**
 * ============================================================================
 * MedIA · Componente C32 — Notificações e Agendamento Ativo
 * ============================================================================
 * ...
 */

(function (global) {
  'use strict';

  const TIPOS_EVENTO = Object.freeze({
    TELECONSULTA_LEMBRETE: 'TELECONSULTA_LEMBRETE',
    PACIENTE_EM_SALA: 'PACIENTE_EM_SALA',
    CONFIRMACAO_PRESENCA: 'CONFIRMACAO_PRESENCA',
  });

  const ANTECEDENCIA_LEMBRETE_MS = 15 * 60 * 1000; // 15 minutos

  // Campos clínicos sensíveis que NUNCA podem aparecer em notificações do SO (LGPD)
  const CAMPOS_SENSIVEIS = Object.freeze(['cid10', 'ciap2', 'descricao_clinica', 'soap', 'anamnese']);

  function agoraMs() { return Date.now(); }

  function sanitizar(dados) { ... shallow copy removing sensitive fields ... }

  function formatarIdentificacao(paciente) {
    // Prioriza CNS (padrão SUS); fallback CPF mascarado
  }

  function mascararCpf(cpf) { return `***.***.${cpf.slice(-3)}-${cpf.slice(-2)}`? }

class NotificacoesPush {
  constructor(opcoes = {}) {
    this.apiBase = opcoes.apiBase ?? '/api/v1';
    this.wsUrl = opcoes.wsUrl ?? null;
    this.antecedenciaMs = opcoes.antecedenciaMs ?? ANTECEDENCIA_LEMBRETE_MS;
    this.intervaloPollingMs = opcoes.intervaloPollingMs ?? 30000;
    this.canal = opcoes.canal ?? 'media-notificacoes';
    this._permissao = 'default';
    this._timers = new Set();
    this._agendamentos = new Map(); // teleconsulta_id -> timer
    this._idsProcessados = new Set(); // dedupe
    this._ws = null;
    this._pollingTimer = null;
    this._tentativaReconexao = 0;
    this._destruido = false;
    this._registroSW = opcoes.registroSW ?? null;
    this._onNotificacao = opcoes.onNotificacao ?? null; // hook para testes/telemetria
  }
  ...
}

function pedirPermissao() {
  if (!('Notification' in global)) return Promise.resolve('unsupported');
  if (global.Notification.permission !== 'default') return Promise.resolve(global.Notification.permission);
  return new Promise((resolve) => {
    const resultado = global.Notification.requestPermission((estado) => resolve(estado));
    if (resultado && typeof resultado.then === 'function') resultado.then(resolve);
  });
}

window.__notificacoesCriadas = [];
class FakeNotification {
  constructor(titulo, opcoes) { window.__notificacoesCriadas.push({ titulo, opcoes }); this.close = () => {}; }
  static get permission() { return window.__permissaoSimulada || 'granted'; }
  static requestPermission(cb) { const p = Promise.resolve(window.__permissaoSimulada || 'granted'); if (cb) p.then(cb); return p; }
}
window.Notification = FakeNotification;

window.__wsMensagens = [];
class FakeWebSocket {
  constructor(url) { this.url = url; FakeWebSocket.instancia = this; this.readyState = 0; }
  send() {}
  close() { this.readyState = 3; }
  // helper: servidor simula mensagem
  _servidorMensagem(dados) { this.onmessage && this.onmessage({ data: JSON.stringify(dados) }); }
  _servidorAberto() { this.readyState = 1; this.onopen && this.onopen(); }
}
window.WebSocket = FakeWebSocket;

/**
 * ============================================================================
 *  MedIA · Componente C32 — Notificações e Agendamento Ativo
 *  backend/app/static/js/notificacoes_push.js
 * ============================================================================
 *  Suporte a Web Notifications API para o fluxo de teleconsulta do SUS/APS:
 *
 *   1. TELECONSULTA_LEMBRETE  — lembrete disparado 15 minutos antes do início;
 *   2. PACIENTE_EM_SALA       — aviso ao profissional quando o paciente entra
 *                               na sala de espera virtual;
 *   3. CONFIRMACAO_PRESENCA   — confirmação de presença do paciente.
 *
 *  Conformidade:
 *   - LGPD/CFM: notificações carregam APENAS dados mínimos (nome, CNS/CPF
 *     mascarado, horário). Campos clínicos (CID-10, CIAP-2, SOAP) são
 *     removidos por lista de bloqueio antes de qualquer exibição.
 *   - Identificação prioriza CNS (padrão SUS) com fallback a CPF mascarado.
 *   - Transporte: WebSocket (tempo real) com fallback de polling REST.
 *
 *  Uso mínimo:
 *    <script src="/static/js/notificacoes_push.js"
 *            data-api-base="/api/v1"
 *            data-ws-url="wss://host/ws/notificacoes"></script>
 *  ou programático:
 *    const push = new MedIANotificacoes.NotificacoesPush({ wsUrl: '...' });
 *    await push.iniciar();
 * ============================================================================
 */
