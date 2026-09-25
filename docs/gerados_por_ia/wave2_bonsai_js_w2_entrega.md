```javascript:backend/app/static/js/telemedicina.js
/**
 * Arquivo: backend/app/static/js/telemedicina.js
 * 
 * Módulo Client-Side para Sistema MedIA (SUS/APS).
 * Gerencia MediaStream, sinalização WebSocket e protocolo SOAP.
 * 
 * Requisitos:
 * - Browser moderno (Chrome, Firefox, Safari).
 * - Backend Python 3.12 com WebSocket (FastAPI/Socket.IO) e Endpoint SOAP.
 * - Estrutura de dados compatível com SUS (CNS/CPF, CID-10).
 */

class TeleMedicinaClient {
  /**
   * @private
   * Estado do cliente
   */
  constructor(options = {}) {
    this.options = {
      wsUrl: options.wsUrl || 'ws://localhost:8080/room_status',
      soapEndpoint: options.soapEndpoint || '/api/soap/consulta',
      duration: options.duration || 300, // Padrão 5 minutos (300s)
      ...options
    };

    this.mediaStream = null;
    this.videoElement = null;
    this.audioElement = null;
    this.isRecording = false;
    this.isCameraActive = false;
    this.isMicActive = false;
    this.ws = null;
    this.timerInterval = null;
    this.remainingTime = 0;
    this.clientId = this.generateClientId();
    this.roomId = this.options.roomId || 'consulta-default';
    this.cns = this.options.cns || ''; // CNS do paciente
    this.cid10 = this.options.cid10 || ''; // CID-10 do diagnóstico
  }

  /**
   * Gera um ID único para o cliente
   * @returns {string}
   */
  generateClientId() {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Inicializa o cliente e conecta ao WebSocket
   * @param {string} roomId - ID da sala de consulta
   * @param {string} cns - CNS do paciente
   * @param {string} cid10 - CID-10 do diagnóstico
   */
  init(roomId, cns, cid10) {
    this.roomId = roomId;
    this.cns = cns;
    this.cid10 = cid10;
    this.connectWebSocket();
    this.setupEventListeners();
    console.log(`[MedIA] Cliente iniciado: ${this.clientId} | Sala: ${roomId}`);
  }

  /**
   * Conecta ao WebSocket para sincronização de status da sala
   * @private
   */
  connectWebSocket() {
    try {
      this.ws = new WebSocket(this.options.wsUrl);
      this.ws.onopen = () => {
        console.log('[MedIA] Conexão WebSocket estabelecida');
        this.sendRoomStatus({
          type: 'join',
          clientId: this.clientId,
          roomId: this.roomId,
          timestamp: new Date().toISOString()
        });
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('[MedIA] Mensagem recebida:', data);
        this.handleWebSocketMessage(data);
      };

      this.ws.onclose = () => {
        console.warn('[MedIA] Conexão WebSocket fechada');
        this.stopTimer();
      };

      this.ws.onerror = (error) => {
        console.error('[MedIA] Erro WebSocket:', error);
      };
    } catch (error) {
      console.error('[MedIA] Falha ao conectar ao WebSocket:', error);
    }
  }

  /**
   * Lida com mensagens do WebSocket
   * @param {object} data - Dados recebidos
   */
  handleWebSocketMessage(data) {
    switch (data.type) {
      case 'room_status':
        this.updateRoomStatus(data);
        break;
      case 'consulta_finalizada':
        this.handleConsultaFinalizada();
        break;
      default:
        console.log('[MedIA] Tipo desconhecido:', data.type);
    }
  }

  /**
   * Atualiza o status da sala
   * @param {object} data - Novo status
   */
  updateRoomStatus(data) {
    console.log('[MedIA] Status da sala atualizado:', data);
    // Lógica para atualizar UI com base no status (ex: 'active', 'paused', 'ended')
  }

  /**
   * Inicia a consulta e inicia o timer
   * @param {object} options - Opções de consulta
   */
  startConsultation(options = {}) {
    this.startMedia();
    this.startTimer(options.duration || this.options.duration);
    this.isRecording = true;
    console.log('[MedIA] Consulta iniciada');
  }

  /**
   * Parada da consulta
   * @param {boolean} sendSOAP - Se enviar SOAP automaticamente
   */
  stopConsultation(sendSOAP = true) {
    this.stopMedia();
    this.stopTimer();
    this.isRecording = false;
    if (sendSOAP) {
      this.submitSOAP();
    }
    console.log('[MedIA] Consulta parada');
  }

  /**
   * Gerencia o MediaStream (Áudio e Vídeo)
   */
  async startMedia() {
    try {
      const options = {
        video: { width: 640, height: 480 },
        audio: true
      };

      this.mediaStream = await navigator.mediaDevices.getUserMedia(options);
      
      // Verifica se os elementos existem
      if (this.videoElement) {
        this.videoElement.srcObject = this.mediaStream;
      }
      if (this.audioElement) {
        this.audioElement.srcObject = this.mediaStream;
      }

      console.log('[MedIA] MediaStream iniciado');
    } catch (error) {
      console.error('[MedIA] Erro ao iniciar MediaStream:', error);
    }
  }

  /**
   * Parada do MediaStream
   */
  stopMedia() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
      console.log('[MedIA] MediaStream parado');
    }
  }

  /**
   * Alternância de dispositivos (Câmera/Microfone)
   * @param {string} device - 'camera' ou 'mic'
   */
  toggleDevice(device) {
    if (!this.mediaStream) {
      console.warn('[MedIA] MediaStream não iniciado');
      return;
    }

    const tracks = this.mediaStream.getTracks();
    const videoTrack = tracks.find(t => t.kind === 'video');
    const audioTrack = tracks.find(t => t.kind === 'audio');

    switch (device) {
      case 'camera':
        if (this.isCameraActive) {
          videoTrack.stop();
          this.isCameraActive = false;
        } else {
          videoTrack.start();
          this.isCameraActive = true;
        }
        break;
      case 'mic':
        if (this.isMicActive) {
          audioTrack.stop();
          this.isMicActive = false;
        } else {
          audioTrack.start();
          this.isMicActive = true;
        }
        break;
    }

    console.log(`[MedIA] Dispositivo ${device} ${this.isCameraActive ? 'ativo' : 'parado'}`);
  }

  /**
   * Inicia o timer da consulta
   * @param {number} duration - Duração em segundos
   */
  startTimer(duration) {
    this.remainingTime = duration;
    this.timerInterval = setInterval(() => {
      this.remainingTime--;
      console.log(`[MedIA] Tempo restante: ${this.remainingTime}s`);
      
      if (this.remainingTime <= 0) {
        this.stopTimer();
        this.handleConsultaFinalizada();
      }
    }, 1000);
  }

  /**
   * Parada do timer
   */
  stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  /**
   * Lida com a finalização da consulta
   */
  handleConsultaFinalizada() {
    console.log('[MedIA] Consulta finalizada automaticamente');
    // Lógica adicional para notificar o usuário ou atualizar UI
  }

  /**
   * Submete o SOAP (Structured Operational Audit Protocol)
   * Envia dados da consulta para o backend
   */
  async submitSOAP() {
    try {
      const payload = {
        type: 'SOAP_CONSULTA',
        clientId: this.clientId,
        roomId: this.roomId,
        timestamp: new Date().toISOString(),
        patient: {
          cns: this.cns,
          cid10: this.cid10
        },
        session: {
          duration: this.options.duration - this.remainingTime,
          isRecording: this.isRecording
        }
      };

      console.log('[MedIA] Enviando SOAP:', payload);
      
      // Simula envio via WebSocket ou Fetch
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(payload));
      } else {
        // Fallback para Fetch
        await fetch(this.options.soapEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }

      console.log('[MedIA] SOAP enviado com sucesso');
    } catch (error) {
      console.error('[MedIA] Erro ao enviar SOAP:', error);
    }
  }

  /**
   * Configura eventos de UI (ex: buttons)
   * @private
   */
  setupEventListeners() {
    // Exemplo de configuração de eventos
    // document.getElementById('btn-camera').addEventListener('click', () => this.toggleDevice('camera'));
    // document.getElementById('btn-mic').addEventListener('click', () => this.toggleDevice('mic'));
    // document.getElementById('btn-start').addEventListener('click', () => this.startConsultation());
    // document.getElementById('btn-stop').addEventListener('click', () => this.stopConsultation(true));
  }

  /**
   * Destrução do cliente
   */
  destroy() {
    this.stopConsultation(false);
    if (this.ws) {
      this.ws.close();
    }
    console.log('[MedIA] Cliente destruído');
  }
}

/**
 * Inicialização do cliente
 * Exemplo de uso:
 * const client = new Tele