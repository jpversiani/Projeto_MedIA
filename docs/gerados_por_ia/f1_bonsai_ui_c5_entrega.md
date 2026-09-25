```javascript
// Arquivo: backend/app/static/js/webrtc_manager.js

/**
 * Módulo WebRTC de Gerenciamento de Mídia Local (C5)
 * Classe WebRTCManager para captura de mídia, controle de muting e gerenciamento de PeerConnection.
 *
 * @class WebRTCManager
 * @description Gerencia a sessão WebRTC para teleconsulta médica, incluindo captura de áudio/vídeo,
 *              seleção dinâmica de dispositivos e controle de mutação.
 */
class WebRTCManager {
  /**
   * @param {Object} options - Configurações iniciais da conexão.
   * @param {string} [options.peerId] - Identificador único do peer.
   * @param {string} [options.sdpUrl] - URL do servidor de sinalização (STUN/TURN/SIG).
   * @param {string} [options.csn] - Código do Sistema Nacional de Identidade (CNS) para rastreamento.
   * @param {string} [options.cpf] - CPF do paciente para identificação no sistema SUS/APS.
   */
  constructor(options = {}) {
    this.peerId = options.peerId || this.generateId();
    this.csn = options.csn || '';
    this.cpf = options.cpf || '';
    this.sdpUrl = options.sdpUrl || 'https://stun.l.google.com:19302';

    this.peerConnection = null;
    this.audioTrack = null;
    this.videoTrack = null;
    this.isMuted = false;
    this.isRecording = false;
    this.mediaRecorder = null;
    this.onMediaChange = null;
    this.onConnectionStateChange = null;
    this.onTrackChange = null;

    this._init();
  }

  /**
   * Gera um ID único para o peer.
   * @returns {string}
   */
  generateId() {
    return `peer-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Inicializa o gerenciador de WebRTC.
   */
  _init() {
    this.peerConnection = new RTCPeerConnection({
      iceServers: [
        { urls: this.sdpUrl },
        { urls: 'stun:stun.l.google.com:19302' }
      ]
    });

    this.peerConnection.ontrackchange = (event) => {
      if (this.onTrackChange) {
        this.onTrackChange(event);
      }
    };

    this.peerConnection.ontrack = (event) => {
      if (this.onMediaChange) {
        this.onMediaChange(event);
      }
    };

    this.peerConnection.onconnectionstatechange = (event) => {
      if (this.onConnectionStateChange) {
        this.onConnectionStateChange(event);
      }
    };

    this.peerConnection.oniceconnectionstatechange = (event) => {
      if (this.onConnectionStateChange) {
        this.onConnectionStateChange(event);
      }
    };
  }

  /**
   * Inicia a captura de mídia (áudio e vídeo) com seleção dinâmica.
   * @param {Object} options - Configurações de captura.
   * @param {boolean} [options.useVideo] - Se true, captura vídeo.
   * @param {boolean} [options.useAudio] - Se true, captura áudio.
   * @param {string} [options.deviceId] - ID do dispositivo específico (ex: '0', '1').
   * @returns {Promise<void>}
   */
  async startCapture(options = {}) {
    const { useVideo = true, useAudio = true, deviceId } = options;

    if (!this.peerConnection || this.peerConnection.state !== 'initialized') {
      throw new Error('WebRTCManager não inicializado');
    }

    const mediaOptions = {
      audio: {
        deviceIndex: useAudio ? (deviceId ? parseInt(deviceId) : 0) : -1,
        enableMicrophone: useAudio
      },
      video: {
        deviceIndex: useVideo ? (deviceId ? parseInt(deviceId) : 0) : -1,
        audio: useAudio
      }
    };

    try {
      const stream = await navigator.mediaDevices.getUserMedia(mediaOptions);

      if (useVideo) {
        this.videoTrack = stream.getTracksByType('video')[0];
        this.peerConnection.addTrack(this.videoTrack, {
          local: {
            canSend: true,
            canReceive: true,
            maxBandwidth: 1000000
          }
        });
      }

      if (useAudio) {
        this.audioTrack = stream.getTracksByType('audio')[0];
        this.peerConnection.addTrack(this.audioTrack, {
          local: {
            canSend: true,
            canReceive: true,
            maxBandwidth: 100000
          }
        });
      }

      this.peerConnection.state = 'connecting';
      this.onMediaChange?.({ type: 'media_started', tracks: { video: useVideo, audio: useAudio } });
    } catch (error) {
      console.error('Erro ao iniciar captura de mídia:', error);
      throw error;
    }
  }

  /**
   * Para a captura de mídia.
   * @returns {Promise<void>}
   */
  async stopCapture() {
    if (this.mediaRecorder) {
      this.mediaRecorder.stop();
      this.mediaRecorder = null;
    }

    if (this.videoTrack) {
      this.videoTrack.stop();
      this.videoTrack = null;
    }

    if (this.audioTrack) {
      this.audioTrack.stop();
      this.audioTrack = null;
    }

    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }

    this.onMediaChange?.({ type: 'media_stopped' });
  }

  /**
   * Toggles o estado de mutação do áudio.
   * @returns {boolean} Novo estado de mutação.
   */
  toggleMute() {
    if (!this.audioTrack) {
      throw new Error('Rastreamento de áudio não encontrado');
    }

    this.isMuted = !this.isMuted;
    this.audioTrack.mute = this.isMuted;

    if (this.isMuted) {
      console.log('Audio mutado');
    } else {
      console.log('Audio desmutado');
    }

    return this.isMuted;
  }

  /**
   * Inicia a gravação local da mídia.
   * @param {string} [options.filename] - Nome do arquivo de saída.
   * @param {string} [options.format] - Formato de saída (ex: 'mp4', 'webm').
   * @returns {Promise<void>}
   */
  async startRecording(options = {}) {
    if (!this.videoTrack || !this.audioTrack) {
      throw new Error('Mídia não está sendo capturada');
    }

    if (this.mediaRecorder) {
      this.mediaRecorder.stop();
    }

    const options = {
      audio: { codec: 'opus' },
      video: { codec: 'vp89' }
    };

    this.mediaRecorder = new MediaRecorder(
      [this.videoTrack, this.audioTrack],
      options
    );

    this.mediaRecorder.ondataavailable = (event) => {
      console.log('Dados de gravação disponíveis');
    };

    this.mediaRecorder.onstop = () => {
      console.log('Gravação finalizada');
    };

    this.mediaRecorder.start();
    this.isRecording = true;
  }

  /**
   * Para a gravação local.
   * @returns {Promise<URL>}
   */
  async stopRecording() {
    if (!this.mediaRecorder) {
      throw new Error('Gravação não está ativa');
    }

    this.mediaRecorder.stop();
    this.isRecording = false;

    const blob = await this.mediaRecorder.getMedia();
    const url = URL.createObjectURL(blob);
    this.mediaRecorder = null;

    return url;
  }

  /**
   * Seleciona dinamicamente o dispositivo de mídia.
   * @param {string} [deviceId] - ID do dispositivo.
   * @returns {Promise<void>}
   */
  async selectDevice(deviceId) {
    if (!this.mediaRecorder) {
      throw new Error('Gravação não está ativa');
    }

    const devices = await navigator.mediaDevices.getUserDevices();
    const device = devices.find(d => d.id === deviceId);

    if (!device) {
      throw new Error('Dispositivo não encontrado');
    }

    // Para reconfigurar o stream, é necessário parar e reiniciar
    await this.stopRecording();
    await this.stopCapture();

    const options = {
      audio: { deviceIndex: parseInt(deviceId) },
      video: { deviceIndex: parseInt(deviceId) }
    };

    const stream = await navigator.mediaDevices.getUserMedia(options);
    this.videoTrack = stream.getTracksByType('video')[0];
    this.audioTrack = stream.getTracksByType('audio')[0];

    this.peerConnection.addTrack(this.videoTrack, { local: { canSend: true, canReceive: true } });
    this.peerConnection.addTrack(this.audioTrack, { local: { canSend: true, canReceive: true } });

    this.peerConnection.state = 'connecting';
    this.onMediaChange?.({ type: 'media_device_changed', deviceId });
  }

  /**
   * Obtém a lista de dispositivos disponíveis.
   * @returns {Promise<Array>}
   */
  async getDevices() {
    return navigator.mediaDevices.getUserDevices();
  }

  /**
   * Obtém o estado atual da conexão.
   * @returns {string}
   */
  getConnectionState() {
    return this.peerConnection ? this.peerConnection.state : 'initialized';
  }

  /**
   * Obtém o estado de mutação.
   * @returns {boolean}
   */
  isAudioMuted() {
    return this.isMuted;
  }

  /**
   * Obtém o ID do peer.
   * @returns {string}
   */
  getPeerId() {
    return this.peerId;
  }

  /**
   * Obtém o CNS do peer.
   * @returns {string}
   */
  getCsn() {
    return this.csn;
  }

  /**
   * Obtém o CPF do peer.
   * @returns {string}
   */
  getCpf() {
    return this.cpf;
  }
}

// Exporta a classe para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
  module.exports = WebRTCManager;
} else {
  window.WebRTCManager = WebRTCManager;
}
```