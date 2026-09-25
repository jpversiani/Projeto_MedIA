# Módulo WebRTC de Gerenciamento de Mídia Local (C1) — Projeto MedIA

Criei o arquivo `backend/app/static/js/webrtc_manager.js` conforme solicitado. Como se trata de um módulo **frontend (JavaScript)**, as diretrizes de tipagem Python/Pydantic/SQLAlchemy não se aplicam diretamente — em vez disso, apliquei tipagem via **JSDoc** e padrões de código limpo equivalentes, preservando a arquitetura do projeto (sem integrações SUS/SISAB e sem periféricos IoT).

```javascript
/**
 * ============================================================================
 * Projeto MedIA — Módulo WebRTC de Gerenciamento de Mídia Local (C1)
 * ============================================================================
 * Responsabilidade: captura de mídia local (áudio/vídeo) para teleconsulta
 * médica, seleção dinâmica de dispositivos, controle de mute/unmute e
 * manipulação de RTCPeerConnection em navegadores modernos.
 *
 * Escopo: atendimento particular e convênios (TISS ANS 4.01 / DMED).
 * Método clínico: Atenção Primária / Saúde da Família.
 *
 * Este módulo NÃO realiza gravação clínica nem integra periféricos IoT
 * (estetoscópios/otoscópios digitais). A captura é estritamente local,
 * respeitando consentimento explícito do paciente antes de getUserMedia.
 * ============================================================================
 */

'use strict';

/**
 * Estados possíveis do gerenciador de mídia.
 * @enum {string}
 */
const MediaState = Object.freeze({
  IDLE: 'idle',
  REQUESTING: 'requesting',
  READY: 'ready',
  IN_CALL: 'in_call',
  ENDED: 'ended',
  ERROR: 'error',
});

/**
 * Configuração de servidores ICE (STUN/TURN) para atravessar NATs,
 * essencial em teleconsultas residenciais (Atenção Primária).
 * @typedef {Object} IceServerConfig
 * @property {string[]} urls
 * @property {string} [username]
 * @property {string} [credential]
 */

/**
 * Opções de inicialização do WebRTCManager.
 * @typedef {Object} WebRTCManagerOptions
 * @property {IceServerConfig[]} [iceServers] Servidores ICE (padrão: STUN público).
 * @property {HTMLVideoElement} [localVideoElement] Elemento para preview local.
 * @property {HTMLVideoElement} [remoteVideoElement] Elemento para vídeo remoto.
 * @property {HTMLAudioElement} [remoteAudioElement] Elemento para áudio remoto.
 * @property {boolean} [videoEnabled=true] Solicitar vídeo na captura inicial.
 * @property {boolean} [audioEnabled=true] Solicitar áudio na captura inicial.
 * @property {{width: number, height: number}} [idealResolution] Resolução ideal.
 * @property {function(string, Object=): void} [onStateChange] Callback de mudança de estado.
 * @property {function(Error): void} [onError] Callback de erros de mídia/conexão.
 * @property {function(MediaStreamTrack): void} [onRemoteTrack] Callback para tracks remotas.
 */

/**
 * Gerenciador de mídia local para teleconsulta médica (C1).
 *
 * Ciclo de vida:
 *   1. `initialize()`      — enumera dispositivos disponíveis.
 *   2. `requestMedia()`    — solicita permissão e captura getUserMedia.
 *   3. `switchDevice()`    — troca dinâmica de microfone/câmera (hot-swap).
 *   4. `startCall()`       — cria RTCPeerConnection e negocia com o par.
 *   5. `toggleAudio()` / `toggleVideo()` — mute/unmute granular.
 *   6. `endCall()`         — encerra conexão e libera tracks locais.
 */
class WebRTCManager {
  /**
   * @param {WebRTCManagerOptions} [options={}]
   */
  constructor(options = {}) {
    const {
      iceServers = [{ urls: 'stun:stun.l.google.com:19302' }],
      localVideoElement = null,
      remoteVideoElement = null,
      remoteAudioElement = null,
      videoEnabled = true,
      audioEnabled = true,
      idealResolution = { width: 1280, height: 720 },
      onStateChange = null,
      onError = null,
      onRemoteTrack = null,
    } = options;

    /** @type {RTCIceServer[]} */
    this._iceServers = iceServers;
    /** @type {HTMLVideoElement|null} */
    this._localVideoEl = localVideoElement;
    /** @type {HTMLVideoElement|null} */
    this._remoteVideoEl = remoteVideoElement;
    /** @type {HTMLAudioElement|null} */
    this._remoteAudioEl = remoteAudioElement;
    /** @type {{width: number, height: number}} */
    this._idealResolution = idealResolution;

    /** @type {function(string, Object=): void} */
    this._onStateChange = typeof onStateChange === 'function' ? onStateChange : () => {};
    /** @type {function(Error): void} */
    this._onError = typeof onError === 'function' ? onError : () => {};
    /** @type {function(MediaStreamTrack): void} */
    this._onRemoteTrack = typeof onRemoteTrack === 'function' ? onRemoteTrack : () => {};

    /** @type {MediaState} */
    this._state = MediaState.IDLE;
    /** @type {MediaStream|null} */
    this._localStream = null;
    /** @type {RTCPeerConnection|null} */
    this._peerConnection = null;
    /** @type {MediaStream|null} */
    this._remoteStream = null;

    /** @type {MediaDeviceInfo[]} */
    this._audioInputs = [];
    /** @type {MediaDeviceInfo[]} */
    this._videoInputs = [];
    /** @type {string|null} */
    this._selectedMicId = null;
    /** @type {string|null} */
    this._selectedCameraId = null;

    /** @type {boolean} */
    this._audioEnabled = audioEnabled;
    /** @type {boolean} */
    this._videoEnabled = videoEnabled;

    /** @type {string|null} */
    this._deviceIdCache = null;

    this._bindDeviceChangeListener();
  }

  // ==========================================================================
  // API pública
  // ==========================================================================

  /**
   * Enumera dispositivos de mídia disponíveis no navegador.
   * Requer permissão prévia para labels precisos (comportamento do navegador).
   * @returns {Promise<{audioInputs: MediaDeviceInfo[], videoInputs: MediaDeviceInfo[]}>}
   */
  async initialize() {
    if (!this._isSupported()) {
      const err = new Error('WebRTC não é suportado neste navegador.');
      this._setState(MediaState.ERROR);
      this._onError(err);
      throw err;
    }

    await this._enumerateDevices();
    this._setState(MediaState.IDLE, {
      audioInputs: this._audioInputs.length,
      videoInputs: this._videoInputs.length,
    });

    return { audioInputs: this._audioInputs, videoInputs: this._videoInputs };
  }

  /**
   * Solicita permissão e captura a mídia local via getUserMedia.
   * Deve ser chamada após consentimento explícito do paciente (LGPD/CFM).
   * @param {Object} [overrides] Restrições adicionais (ex.: deviceId específico).
   * @returns {Promise<MediaStream>}
   */
  async requestMedia(overrides = {}) {
    if (this._localStream) {
      this._stopLocalStream();
    }

    this._setState(MediaState.REQUESTING);

    const constraints = {
      audio: this._buildAudioConstraints(overrides.audio),
      video: this._buildVideoConstraints(overrides.video),
    };

    try {
      this._localStream = await navigator.mediaDevices.getUserMedia(constraints);
      this._cacheSelectedDeviceIds();
      this._attachLocalStream();
      await this._enumerateDevices(); // Re-enumera com labels agora visíveis.
      this._setState(MediaState.READY, { stream: this._localStream });
      return this._localStream;
    } catch (err) {
      this._setState(MediaState.ERROR);
      this._onError(err);
      throw err;
    }
  }

  /**
   * Troca dinamicamente o microfone em uso (hot-swap, sem encerrar a chamada).
   * @param {string} deviceId ID do dispositivo de áudio (device.deviceId).
   * @returns {Promise<void>}
   */
  async switchMicrophone(deviceId) {
    await this._switchTrack('audio', deviceId);
    this._selectedMicId = deviceId;
  }

  /**
   * Troca dinamicamente a câmera em uso (hot-swap, sem encerrar a chamada).
   * @param {string} deviceId ID do dispositivo de vídeo (device.deviceId).
   * @returns {Promise<void>}
   */
  async switchCamera(deviceId) {
    await this._switchTrack('video', deviceId);
    this._selectedCameraId = deviceId;
  }

  /**
   * Ativa/desativa o microfone (mute/unmute) da track local de áudio.
   * @param {boolean} [force] Estado desejado; se omitido, alterna (toggle).
   * @returns {boolean} Novo estado: true = áudio ativo (unmuted).
   */
  toggleAudio(force) {
    const track = this._getLocalTrack('audio');
    if (!track) return false;

    const target = typeof force === 'boolean' ? force : track.enabled === false;
    track.enabled = target;
    this._audioEnabled = target;

    this._setState(MediaState.READY, { audioEnabled: target, videoEnabled: this._videoEnabled });
    return target;
  }

  /**
   * Ativa/desativa a câmera (mute/unmute) da track local de vídeo.
   * @param {boolean} [force] Estado desejado; se omitido, alterna (toggle).
   * @returns {boolean} Novo estado: true = vídeo ativo.
   */
  toggleVideo(force) {
    const track = this._getLocalTrack('video');
    if (!track) return false;

    const target = typeof force === 'boolean' ? force : track.enabled === false;
    track.enabled = target;
    this._videoEnabled = target;

    this._setState(MediaState.READY, { audioEnabled: this._audioEnabled, videoEnabled: target });
    return target;
  }

  /**
   * Inicia a sessão de teleconsulta: cria RTCPeerConnection,
   * adiciona tracks locais e prepara handlers de mídia remota.
   * @returns {Promise<RTCPeerConnection>}
   */
  async startCall() {
    if (!this._localStream) {
      throw new Error('Mídia local não capturada. Chame requestMedia() antes de startCall().');
    }
    if (this._peerConnection) {
      throw new Error('Já existe uma sessão ativa. Chame endCall() antes de iniciar outra.');
    }

    this._peerConnection = new RTCPeerConnection({ iceServers: this._iceServers });
    this._remoteStream = new MediaStream();

    // Adiciona todas as tracks locais à conexão.
    for (const track of this._localStream.getTracks()) {
      this._peerConnection.addTrack(track, this._localStream);
    }

    this._bindPeerConnectionEvents();
    this._setState(MediaState.IN_CALL);
    return this._peerConnection;
  }

  /**
   * Cria e retorna uma oferta SDP (lado do profissional de saúde).
   * @returns {Promise<RTCSessionDescriptionInit>}
   */
  async createOffer() {
    this._assertPeerConnection();
    const offer = await this._peerConnection.createOffer({
      offerToReceiveAudio: true,
      offerToReceiveVideo: true,
    });
    await this._peerConnection.setLocalDescription(offer);
    return offer;
  }

  /**
   * Cria e retorna uma resposta SDP (lado do paciente).
   * @param {RTCSessionDescriptionInit} remoteOffer Oferta recebida do par.
   * @returns {Promise<RTCSessionDescriptionInit>}
   */
  async createAnswer(remoteOffer) {
    this._assertPeerConnection();
    await this._peerConnection.setRemoteDescription(new RTCSessionDescription(remoteOffer));
    const answer = await this._peerConnection.createAnswer();
    await this._peerConnection.setLocalDescription(answer);
    return answer;
  }

  /**
   * Aplica uma resposta SDP remota (lado do profissional).
   * @param {RTCSessionDescriptionInit} remoteAnswer Resposta do par.
   * @returns {Promise<void>}
   */
  async applyRemoteAnswer(remoteAnswer) {
    this._assertPeerConnection();
    await this._peerConnection.setRemoteDescription(new RTCSessionDescription(remoteAnswer));
  }

  /**
   * Adiciona um candidato ICE remoto recebido via sinalização.
   * @param {RTCIceCandidateInit} candidate
   * @returns {Promise<void>}
   */
  async addRemoteIceCandidate(candidate) {
    this._assertPeerConnection();
    await this._peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
  }

  /**
   * Encerra a sessão de teleconsulta e libera todos os recursos de mídia.
   * @returns {void}
   */
  endCall() {
    if (this._peerConnection) {
      this._peerConnection.close();
      this._peerConnection = null;
    }

    this._remoteStream = null;
    this._detachRemoteStream();
    this._stopLocalStream();
    this._setState(MediaState.ENDED);
  }

  // ==========================================================================
  // Getters de estado (para integração com UI/Python via templates)
  // ==========================================================================

  /** @returns {MediaState} Estado atual do gerenciador. */
  get state() {
    return this._state;
  }

  /** @returns {MediaStream|null} Stream local ativo. */
  get localStream() {
    return this._localStream;
  }

  /** @returns {MediaStream|null} Stream remoto ativo. */
  get remoteStream() {
    return this._remoteStream;
  }

  /** @returns {boolean} Áudio local está ativo (unmuted). */
  get isAudioEnabled() {
    return this._audioEnabled;
  }

  /** @returns {boolean} Vídeo local está ativo. */
  get isVideoEnabled() {
    return this._videoEnabled;
  }

  /** @returns {MediaDeviceInfo[]} Microfones disponíveis. */
  get audioInputs() {
    return [...this._audioInputs];
  }

  /** @returns {MediaDeviceInfo[]} Câmeras disponíveis. */
  get videoInputs() {
    return [...this._videoInputs];
  }

  // ==========================================================================
  // Métodos privados
  // ==========================================================================

  /**
   * Verifica suporte a WebRTC no navegador atual.
   * @private
   * @returns {boolean}
   */
  _isSupported() {
    return Boolean(
      navigator.mediaDevices &&
      typeof navigator.mediaDevices.getUserMedia === 'function' &&
      typeof RTCPeerConnection === 'function'
    );
  }

  /**
   * Constrói restrições de áudio com deviceId selecionado, se houver.
   * @private
   * @param {boolean|MediaTrackConstraints|undefined} [override]
   * @returns {boolean|MediaTrackConstraints}
   */
  _buildAudioConstraints(override) {
    if (override === false) return false;
    if (override && typeof override === 'object') {
      return { echoCancellation: true, noiseSuppression: true, autoGainControl: true, ...override };
    }
    return {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
      ...(this._selectedMicId ? { deviceId: { exact: this._selectedMicId } } : {}),
    };
  }

  /**
   * Constrói restrições de vídeo com resolução ideal e deviceId selecionado.
   * @private
   * @param {boolean|MediaTrackConstraints|undefined} [override]
   * @returns {boolean|MediaTrackConstraints}
   */
  _buildVideoConstraints(override) {
    if (override === false) return false;
    if (override && typeof override === 'object') {
      return { ...override };
    }
    return {
      width: { ideal: this._idealResolution.width },
      height: { ideal: this._idealResolution.height },
      facingMode: 'user',
      frameRate: { ideal: 30 },
      ...(this._selectedCameraId ? { deviceId: { exact: this._selectedCameraId } } : {}),
    };
  }

  /**
   * Enumera dispositivos e classifica por tipo.
   * @private
   * @returns {Promise<void>}
   */
  async _enumerateDevices() {
    const devices = await navigator.mediaDevices.enumerateDevices();
    this._audioInputs = devices.filter((d) => d.kind === 'audioinput');
    this._videoInputs = devices.filter((d) => d.kind === 'videoinput');
  }

  /**
   * Cachê dos deviceIds em uso a partir do stream ativo.
   * @private
   * @returns {void}
   */
  _cacheSelectedDeviceIds() {
    if (!this._localStream) return;

    const audioTrack = this._getLocalTrack('audio');
    const videoTrack = this._getLocalTrack('video');

    if (audioTrack?.getSettings().deviceId) {
      this._selectedMicId = /** @type {string} */ (audioTrack.getSettings().deviceId);
    }
    if (videoTrack?.getSettings().deviceId) {
      this._selectedCameraId = /** @type {string} */ (videoTrack.getSettings().deviceId);
    }
  }

  /**
   * Anexa o stream local ao elemento de vídeo de preview.
   * @private
   * @returns {void}
   */
  _attachLocalStream() {
    if (this._localVideoEl && this._localStream) {
      this._localVideoEl.srcObject = this._localStream;
      this._localVideoEl.muted = true; // Evita feedback (eco) no preview local.
      this._localVideoEl.playsInline = true;
      this._localVideoEl.play().catch(() => { /* autoplay bloqueado: UI deve sinalizar */ });
    }
