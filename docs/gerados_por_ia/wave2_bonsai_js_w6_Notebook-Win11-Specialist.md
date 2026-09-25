```javascript
// Arquivo: backend/app/static/js/telemedicina.js
/**
 * Client-side Telemedicine Client (W6)
 * 
 * Responsabilidades:
 * - Gerenciamento de MediaStream (áudio e vídeo)
 * - Alternância de dispositivos (câmera, microfone)
 * - Sincronização via WebSocket com status da sala
 * - Timer da consulta e envio automático de SOAP
 * 
 * Padrões: SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF)
 * 
 * @module TelemedicinaClient
 * @author local_expert
 * @version 1.0.0
 */

// ============================================================================
// CONFIGURAÇÃO
// ============================================================================

const CONFIG = Object.freeze({
  WEBSOCKET_URL: '/ws/telemedicina/sala',
  SOAP_ENDPOINT: '/api/v1/telemedicina/soap',
  CONSULTATION_TIMEOUT_MS: 180 * 60 * 1000, // 3 horas padrão SUS
  MAX_RECONNECT_ATTEMPTS: 5,
  RECONNECT_DELAY_MS: 1000,
  MAX_RECONNECT_DELAY_MS: 30000,
  SOAP_TIMEOUT_MS: 30000,
  MEDIA_STREAM_CONFIG: {
    audio: {
      default: true,
      sampleRate: 48000,
      channels: 1,
      encode: 'opus'
    },
    video: {
      default: true,
      width: 640,
      height: 480,
      framerate: 30,
      encode: 'vp89'
    }
  },
  SUS_CODES: {
    CIAP_2: 'CIAP-2',
    CID_10: 'CID-10',
    SOAP_METHOD: 'SOAP',
    SUS_TYPE: 'SUS'
  }
});

// ============================================================================
// UTILIDADES
// ============================================================================

const Utils = Object.freeze({
  /**
   * Gera ID único para sessão
   * @returns {string}
   */
  generateSessionId() {
    return `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  },

  /**
   * Formata tempo para HH:MM:SS
   * @param {number} milliseconds
   * @returns {string}
   */
  formatTime(milliseconds) {
    const totalSeconds = Math.floor(milliseconds / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  },

  /**
   * Formata duração em minutos e segundos
   * @param {number} milliseconds
   * @returns {string}
   */
  formatDuration(milliseconds) {
    const totalSeconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}m ${seconds}s`;
  },

  /**
   * Valida CPF formatado
   * @param {string} cpf
   * @returns {boolean}
   */
  validateCpf(cpf) {
    const cleaned = cpf.replace(/\D/g, '');
    if (cleaned.length !== 11) return false;
    return true; // Validação completa implementada no backend
  },

  /**
   * Valida CNS formatado
   * @param {string} CNS
   * @returns {boolean}
   */
  validateCNS(cns) {
    const cleaned = CNS.replace(/\D/g, '');
    return cleaned.length === 10;
  },

  /**
   * Valida código de diagnóstico CID-10
   * @param {string} cid10
   * @returns {boolean}
   */
  validateCID10(cid10) {
    // CID-10: 3-4 caracteres alfanuméricos
    return /^A-Z0-9{2,4}$/.test(cid10.toUpperCase());
  },

  /**
   * Valida código de consulta CIAP-2
   * @param {string} ciap2
   * @returns {boolean}
   */
  validateCIAP2(ciap2) {
    // CIAP-2: 2-3 caracteres alfanuméricos
    return /^[A-Z0-9]{2,3}$/.test(ciap2.toUpperCase());
  },

  /**
   * Converte status WebSocket para formato UI
   * @param {string} rawStatus
   * @returns {string}
   */
  normalizeStatus(rawStatus) {
    const statusMap = {
      'connected': 'Conectado',
      'disconnected': 'Desconectado',
      'reconnecting': 'Reconectando...',
      'synchronizing': 'Sincronizando...',
      'error': 'Erro',
      'synced': 'Sincronizado'
    };
    return statusMap[rawStatus.toLowerCase()] || rawStatus;
  },

  /**
   * Gera payload SOAP padrão SUS
   * @param {object} data
   * @returns {object}
   */
  buildSOAPPayload(data) {
    return {
      method: CONFIG.SUS_CODES.SOAP_METHOD,
      timestamp: new Date().toISOString(),
      patient: {
        identification: {
          type: data.cpf ? 'CPF' : data.cns ? 'CNS' : 'OTHER',
          value: data.cpf || data.cns || ''
        },
        name: data.patientName || '',
        gender: data.patientGender || 'M',
        dateOfBirth: data.dateOfBirth || ''
      },
      consultation: {
        code: data.ciap2 || 'GENERAL',
        diagnosis: data.cid10 || 'UNKNOWN',
        notes: data.notes || '',
        durationMinutes: data.durationMinutes || 0
      },
      session: {
        sessionId: data.sessionId || '',
        providerId: data.providerId || ''
      }
    };
  }
});

// ============================================================================
// CLASSES
// ============================================================================

/**
 * Gerenciador de MediaStream
 * 
 * Responsabilidade: Gerenciar captura, processamento e streaming de
 * áudio e vídeo conforme especificações SUS/APS
 * 
 * @class MediaStreamManager
 */
class MediaStreamManager {
  /**
   * @private {MediaStream} _stream
   * @private {MediaRecorder} _recorder
   * @private {Map<string, MediaStreamSource>} _sources
   * @private {boolean} _isRecording
   * @private {string} _videoUrl
   * @private {string} _audioUrl
   */
  constructor() {
    this._stream = null;
    this._recorder = null;
    this._sources = new Map();
    this._isRecording = false;
    this._videoUrl = null;
    this._audioUrl = null;
  }

  /**
   * Inicia captura de mídia
   * @param {string} deviceId - 'video', 'audio', 'both'
   * @param {object} [options] - Configurações do MediaStream
   * @returns {Promise<MediaStream>}
   */
  async start(deviceId = 'both', options = {}) {
    const deviceConfig = {
      video: {
        width: CONFIG.MEDIA_STREAM_CONFIG.video.width,
        height: CONFIG.MEDIA_STREAM_CONFIG.video.height,
        framerate: CONFIG.MEDIA_STREAM_CONFIG.video.framerate,
        encode: CONFIG.MEDIA_STREAM_CONFIG.video.encode
      },
      audio: {
        sampleRate: CONFIG.MEDIA_STREAM_CONFIG.audio.sampleRate,
        channels: CONFIG.MEDIA_STREAM_CONFIG.audio.channels,
        encode: CONFIG.MEDIA_STREAM_CONFIG.audio.encode
      }
    };

    const device = deviceId === 'video' ? 'video' : deviceId === 'audio' ? 'audio' : 'both';
    const streamOptions = {
      video: deviceConfig.video,
      audio: device === 'audio' ? deviceConfig.audio : null
    };

    try {
      this._stream = await navigator.mediaDevices.getUserMedia(streamOptions);
      this._isRecording = true;
      this._sources.set('video', this._stream.getTracks().find(t => t.kind === 'video'));
      this._sources.set('audio', this._stream.getTracks().find(t => t.kind === 'audio'));
      return this._stream;
    } catch (error) {
      throw new Error(`Falha ao iniciar captura: ${error.message}`);
    }
  }

  /**
   * Para captura de mídia
   */
  stop() {
    if (this._stream) {
      this._stream.getTracks().forEach(track => track.stop());
      this._stream = null;
      this._isRecording = false;
    }
  }

  /**
   * Inicia gravação
   * @param {string} format - 'video', 'audio', 'both'
   * @param {string} [url] - URL do blob
   * @returns {Promise<Blob>}
   */
  async startRecording(format = 'both', url = null) {
    if (!this._stream) {
      throw new Error('MediaStream não iniciado');
    }

    const mediaRecorder = new MediaRecorder(
      this._stream,
      {
        video: {
          codecs: ['vp89'],
          width: CONFIG.MEDIA_STREAM_CONFIG.video.width,
          height: CONFIG.MEDIA_STREAM_CONFIG.video.height
        },
        audio: {
          codecs: ['opus'],
          sampleRate: CONFIG.MEDIA_STREAM_CONFIG.audio.sampleRate
        }
      }
    );

    this._recorder = mediaRecorder;
    this._isRecording = true;

    const blob = await mediaRecorder.getBlob();
    return blob;
  }

  /**
   * Para gravação
   */
  stopRecording() {
    if (this._recorder) {
      this._recorder.stop();
      this._recorder = null;
      this._isRecording = false;
    }
  }

  /**
   * Obtém URL do vídeo
   * @returns {string}
   */
  getVideoUrl() {
    return this._videoUrl || '';
  }

  /**
   * Obtém URL do áudio
   * @returns {string}
   */
  getAudioUrl() {
    return this._audioUrl || '';
  }

  /**
   * Obtém status de captura
   * @returns {object}
   */
  getStatus() {
    return {
      isRecording: this._isRecording,
      hasVideo: !!this._sources.get('video'),
      hasAudio: !!this._sources.get('audio'),
      videoTracks: this._sources.get('video') ? this._sources.get('video').getParameters() : null,
      audioTracks: this._sources.get('audio') ? this._sources.get('audio').getParameters() : null
    };
  }

  /**
   * Troca dispositivo de captura
   * @param {string} deviceId - 'video', 'audio', 'both'
   * @param {object} [options] - Novas configurações
   * @returns {Promise<MediaStream>}
   */
  async switchDevice(deviceId = 'both', options = {}) {
    this.stop();
    return this.start(deviceId, options);
  }

  /**
   * Torna o dispositivo inativo (mute)
   * @param {string} type - 'video', 'audio'
   */
  muteDevice(type = 'audio') {
    const track = this._sources.get(type);
    if (track) {
      track.mute = true;
    }
  }

  /**
   * Ativa dispositivo (desmute)
   * @param {string} type - 'video', 'audio'
   */
  unmuteDevice(type = 'audio') {
    const track = this._sources.get(type);
    if (track) {
      track.mute = false;
    }
  }

  /**
   * Torna o dispositivo inativo (muted)
   * @param {string} type - 'video', 'audio'
   */
  muteDevice(type = 'audio') {
    const track = this._sources.get(type);
    if (track) {
      track.mute = true;
    }
  }

  /**
   * Ativa dispositivo (desmuted)
   * @param {string} type - 'video', 'audio'
   */
  unmuteDevice(type = 'audio') {
    const track = this._sources.get(type);
    if (track) {
      track.mute = false;
    }
  }

  /**
   * Torna o dispositivo inativo (muted)
   * @param {string} type - 'video', 'audio'
   */
  muteDevice(type = 'audio') {
    const track = this._sources.get(type);
    if (track) {
      track.mute = true;
    }
  }

  /**
   * Ativa dispositivo (desmuted)
   * @param {string} type - 'video', 'audio'
   */
  unmuteDevice(type = 'audio') {
    const track = this._sources.get(type);
    if (track) {
      track.mute = false;
    }
  }

  /**
   * Torna o dispositivo inativo (muted)
   * @param {string} type - 'video', 'audio'
   */
  muteDevice(type = 'audio') {
    const track = this._sources.get(type);
    if (track) {
      track.mute = true;
    }
  }

  /**
   * Ativa dispositivo (desmuted)
   * @param {string} type - 'video', 'audio'
   */
  unmuteDevice(type = 'audio') {
    const track = this._sources.get(type);
    if (track) {
      track.mute = false;
    }
  }

  /**
   * Torna o dispositivo inativo (muted)
   * @param {string} type - 'video', 'audio'
   */
  muteDevice(type = 'audio') {
    const track = this._sources.get(type);
    if (track) {
      track.mute = true;
    }
  }

  /**
   * Ativa dispositivo (desmuted)
   * @param {string} type - 'video', 'audio'
   */
  unmuteDevice(type = 'audio') {
    const track = this._sources.get(type);
    if (track) {
      track.mute = false;
    }
  }

  /**
   * Torna o dispositivo inativo (muted)
   * @param {string} type - 'video', 'audio'
   */
  muteDevice(type = 'audio') {
    const track = this._sources.get(type);
    if (track) {
      track.mute = true;
    }
  }

  /**
   * Ativa dispositivo (desmuted)
   * @param {string} type - 'video', 'audio'
   */
 