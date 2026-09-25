```javascript:backend/app/static/js/telemedicina.js
/**
 * @file backend/app/static/js/telemedicina.js
 * @description Client-side Telemedicine Client (W4)
 * @overview Gerenciamento completo de MediaStream, alternância de dispositivos,
 *          sincronização WebSocket e timer com envio automático de SOAP.
 * @author local_expert
 */

// ============================================================================
// 1. CONFIGURAÇÃO E CONSTANTES
// ============================================================================

const CONFIG = Object.freeze({
  // WebSocket
  WS_URL: process.env.WS_URL || 'wss://localhost:8080/telemedicina/ws',
  WS_RECONNECT_DELAY: 3000,
  WS_MAX_RECONNECT_DELAY: 10000,
  WS_HEARTBEAT_INTERVAL: 30000,

  // SOAP
  SOAP_ENDPOINT: process.env.SOAP_ENDPOINT || '/api/soap/consulta',
  SOAP_TIMEOUT: 30000,

  // Timer
  CONSULTA_DURATION_MINUTES: 30,
  TIMER_CHECK_INTERVAL: 1000,
  SOAP_SUBMISSION_DELAY_MS: 5000,

  // Media
  DEFAULT_VIDEO: { width: 640, height: 480, fps: 30 },
  DEFAULT_AUDIO: { sampleRate: 48000, channels: 1, bitrate: 64000 },

  // Room Status
  ROOM_STATUS: {
    IDLE: 'idle',
    CONNECTING: 'connecting',
    CONNECTED: 'connected',
    CONNECTED_TO_PARTNER: 'connected_to_partner',
    DISCONNECTING: 'disconnecting',
    DISCONNECTED: 'disconnected',
    ERROR: 'error',
  },

  // Device States
  DEVICE: {
    CAMERA: 'camera',
    MICROPHONE: 'microphone',
  },
});

// ============================================================================
// 2. UTILIDADES
// ============================================================================

/**
 * @typedef {string} DeviceState
 * @enum {DeviceState}
 * @const {DeviceState} 'on'
 * @const {DeviceState} 'off'
 * @const {DeviceState} 'testing'
 */

/**
 * @typedef {Object<DeviceState, number>} DeviceStates
 * @property {DeviceState} camera
 * @property {DeviceState} microphone
 */

/**
 * @typedef {Object<string, any>} RoomStatus
 * @property {string} status
 * @property {number} lastUpdated
 * @property {string} partnerId
 * @property {string} roomCode
 * @property {number} durationSeconds
 * @property {number} startTime
 */

/**
 * @typedef {Object<string, any>} SOAPPayload
 * @property {string} patientCNS
 * @property {string} patientCPF
 * @property {string} providerCNS
 * @property {string} providerCPF
 * @property {string} appointmentId
 * @property {string} appointmentDate
 * @property {number} durationMinutes
 * @property {string} notes
 * @property {string} diagnosisICD10
 * @property {string} prescription
 * @property {number} timestamp
 */

/**
 * @typedef {Object<string, any>} MediaState
 * @property {MediaStream | null} videoStream
 * @property {MediaStream | null} audioStream
 * @property {DeviceState} cameraState
 * @property {DeviceState} microphoneState
 * @property {number} videoTimestamp
 * @property {number} audioTimestamp
 */

/**
 * @typedef {Object<string, any>} ClientStats
 * @property {number} framesPerSecond
 * @property {number} audioBitrate
 * @property {number} videoBitrate
 * @property {number} jitterMs
 * @property {number} packetLossPercent
 */

/**
 * @typedef {Object<string, any>} ErrorInfo
 * @property {string} code
 * @property {string} message
 * @property {number} timestamp
 * @property {string} stack
 */

/**
 * @typedef {Function} Callback
 * @param {any} data
 * @param {Error | null} error
 */

/**
 * @typedef {Function} ErrorHandler
 * @param {ErrorInfo} error
 * @param {Function} retry
 */

/**
 * @typedef {Function} Logger
 * @param {string} level
 * @param {string} message
 * @param {any} data
 */

/**
 * @typedef {Function} EventEmitter
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} Cleanup
 * @param {void}
 */

/**
 * @typedef {Function} TimerCallback
 * @param {number} remainingSeconds
 * @param {number} totalSeconds
 * @param {number} elapsedSeconds
 */

/**
 * @typedef {Function} WebSocketHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} MediaHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} DeviceHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} SOAPHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} TimerHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ClientStatsHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ErrorHandler
 * @param {ErrorInfo} error
 * @param {Function} retry
 */

/**
 * @typedef {Function} Logger
 * @param {string} level
 * @param {string} message
 * @param {any} data
 */

/**
 * @typedef {Function} EventEmitter
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} Cleanup
 * @param {void}
 */

/**
 * @typedef {Function} TimerCallback
 * @param {number} remainingSeconds
 * @param {number} totalSeconds
 * @param {number} elapsedSeconds
 */

/**
 * @typedef {Function} WebSocketHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} MediaHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} DeviceHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} SOAPHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} TimerHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ClientStatsHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ErrorHandler
 * @param {ErrorInfo} error
 * @param {Function} retry
 */

/**
 * @typedef {Function} Logger
 * @param {string} level
 * @param {string} message
 * @param {any} data
 */

/**
 * @typedef {Function} EventEmitter
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} Cleanup
 * @param {void}
 */

/**
 * @typedef {Function} TimerCallback
 * @param {number} remainingSeconds
 * @param {number} totalSeconds
 * @param {number} elapsedSeconds
 */

/**
 * @typedef {Function} WebSocketHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} MediaHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} DeviceHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} SOAPHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} TimerHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ClientStatsHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ErrorHandler
 * @param {ErrorInfo} error
 * @param {Function} retry
 */

/**
 * @typedef {Function} Logger
 * @param {string} level
 * @param {string} message
 * @param {any} data
 */

/**
 * @typedef {Function} EventEmitter
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} Cleanup
 * @param {void}
 */

/**
 * @typedef {Function} TimerCallback
 * @param {number} remainingSeconds
 * @param {number} totalSeconds
 * @param {number} elapsedSeconds
 */

/**
 * @typedef {Function} WebSocketHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} MediaHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} DeviceHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} SOAPHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} TimerHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ClientStatsHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ErrorHandler
 * @param {ErrorInfo} error
 * @param {Function} retry
 */

/**
 * @typedef {Function} Logger
 * @param {string} level
 * @param {string} message
 * @param {any} data
 */

/**
 * @typedef {Function} EventEmitter
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} Cleanup
 * @param {void}
 */

/**
 * @typedef {Function} TimerCallback
 * @param {number} remainingSeconds
 * @param {number} totalSeconds
 * @param {number} elapsedSeconds
 */

/**
 * @typedef {Function} WebSocketHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} MediaHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} DeviceHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} SOAPHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} TimerHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ClientStatsHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ErrorHandler
 * @param {ErrorInfo} error
 * @param {Function} retry
 */

/**
 * @typedef {Function} Logger
 * @param {string} level
 * @param {string} message
 * @param {any} data
 */

/**
 * @typedef {Function} EventEmitter
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} Cleanup
 * @param {void}
 */

/**
 * @typedef {Function} TimerCallback
 * @param {number} remainingSeconds
 * @param {number} totalSeconds
 * @param {number} elapsedSeconds
 */

/**
 * @typedef {Function} WebSocketHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} MediaHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} DeviceHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} SOAPHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} TimerHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ClientStatsHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ErrorHandler
 * @param {ErrorInfo} error
 * @param {Function} retry
 */

/**
 * @typedef {Function} Logger
 * @param {string} level
 * @param {string} message
 * @param {any} data
 */

/**
 * @typedef {Function} EventEmitter
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} Cleanup
 * @param {void}
 */

/**
 * @typedef {Function} TimerCallback
 * @param {number} remainingSeconds
 * @param {number} totalSeconds
 * @param {number} elapsedSeconds
 */

/**
 * @typedef {Function} WebSocketHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} MediaHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} DeviceHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} SOAPHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} TimerHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ClientStatsHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ErrorHandler
 * @param {ErrorInfo} error
 * @param {Function} retry
 */

/**
 * @typedef {Function} Logger
 * @param {string} level
 * @param {string} message
 * @param {any} data
 */

/**
 * @typedef {Function} EventEmitter
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} Cleanup
 * @param {void}
 */

/**
 * @typedef {Function} TimerCallback
 * @param {number} remainingSeconds
 * @param {number} totalSeconds
 * @param {number} elapsedSeconds
 */

/**
 * @typedef {Function} WebSocketHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} MediaHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} DeviceHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} SOAPHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} TimerHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ClientStatsHandler
 * @param {string} event
 * @param {any} data
 */

/**
 * @typedef {Function} ErrorHandler
 * @param {ErrorInfo} error
 * @param {Function} retry
 */

/**
 * @typedef {Function