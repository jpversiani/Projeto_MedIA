/**
 * MedIA — Módulo WebRTC de Gerenciamento de Mídia Local (C1)
 * Teleconsulta médica SUS/APS — LGPD + CFM Res. 2.314/2022
 *
 * Exporta WebRTCManager como módulo ES (navegadores modernos).
 * CNS/CPF são identificadores locais; nunca são enviados em SDP/ICE.
 */

'use strict';

const MediaKind = Object.freeze({ AUDIO: 'audio', VIDEO: 'video' });

const ErrorCodes = Object.freeze({
  NOT_INITIALIZED: 'WEBRTC_NOT_INITIALIZED',
  INSECURE_CONTEXT: 'WEBRTC_INSECURE_CONTEXT',
  UNSUPPORTED: 'WEBRTC_UNSUPPORTED',
  CONFIG_INVALID: 'WEBRTC_CONFIG_INVALID',
  CONSENT_DENIED: 'WEBRTC_CONSENT_DENIED',
  PERMISSION_DENIED: 'NotAllowedError',
  DEVICE_NOT_FOUND: 'NotFoundError',
  DEVICE_IN_USE: 'NotReadableError',
  OVERCONSTRAINED: 'OverconstrainedError',
  DEVICE_UNPLUGGED: 'WEBRTC_DEVICE_UNPLUGGED',
  SWITCH_FAILED: 'WEBRTC_SWITCH_FAILED',
  PEER_CONNECTION: 'WEBRTC_PEER_CONNECTION',
  SIGNALING: 'WEBRTC_SIGNALING',
  DESTROYED: 'WEBRTC_DESTROYED',
});

class WebRTCError extends Error {
  constructor(code, message, cause) {
    super(message);
    this.code = code;
    this.cause = cause ?? null;
  }
}

export class WebRTCManager extends EventTarget {
  #stream = null;
  #pc = null;
  #consentimentoRegistrado = false;
  #cns = '';
  #cpf = '';
  #muteAudio = false;
  #muteVideo = false;
  #dispositivos = { audioinput: [], videoinput: [] };
  #deviceChangeHandler = null;
  #config = {};
  #encerrado = false;

  constructor(options = {}) {
    super();
    this.#config = {
      stun: options.stun ?? 'stun:stun.l.google.com:19302',
      turn: options.turn ?? null,
      audioConstraints: options.audioConstraints ?? {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
      videoConstraints: options.videoConstraints ?? {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        frameRate: { ideal: 30 },
      },
    };
  }

  // ---- Consentimento LGPD ----

  async registrarConsentimento({ cns, cpf, aceite }) {
    if (!aceite) throw new WebRTCError(ErrorCodes.CONSENT_DENIED, 'Consentimento LGPD não concedido');
    this.#cns = String(cns ?? '').replace(/\D/g, '');
    this.#cpf = String(cpf ?? '').replace(/\D/g, '');
    this.#consentimentoRegistrado = true;
    this.dispatchEvent(new CustomEvent('consentimento', { detail: { registrado: true } }));
  }

  // ---- Dispositivos ----

  async listarDispositivos() {
    this.#garantirContextoSeguro();
    const devices = await navigator.mediaDevices.enumerateDevices();
    this.#dispositivos.audioinput = devices.filter(d => d.kind === 'audioinput');
    this.#dispositivos.videoinput = devices.filter(d => d.kind === 'videoinput');
    return { ...this.#dispositivos };
  }

  async alternarMicrofone(deviceId) {
    if (!this.#stream) throw new WebRTCError(ErrorCodes.NOT_INITIALIZED, 'Mídia local não iniciada');
    const track = this.#stream.getAudioTracks()[0];
    if (!track) throw new WebRTCError(ErrorCodes.DEVICE_NOT_FOUND, 'Microfone não encontrado');
    const muteEstadoAnterior = track.enabled === false;
    if (this.#pc && this.#pc.getSenders().length > 0) {
      const sender = this.#pc.getSenders().find(s => s.track?.kind === 'audio');
      if (sender) {
        await sender.replaceTrack(deviceId ? await this.#obterTrack(deviceId, MediaKind.AUDIO) : track);
      }
    }
    track.enabled = !muteEstadoAnterior;
    this.#muteAudio = muteEstadoAnterior; // preserva o estado de mute ao trocar de periférico
    this.dispatchEvent(new CustomEvent('microfone-trocado', { detail: { deviceId } }));
  }

  async alternarCamera(deviceId) {
    if (!this.#stream) throw new WebRTCError(ErrorCodes.NOT_INITIALIZED, 'Mídia local não iniciada');
    const track = this.#stream.getVideoTracks()[0];
    if (!track) throw new WebRTCError(ErrorCodes.DEVICE_NOT_FOUND, 'Câmera não encontrada');
    const muteEstadoAnterior = track.enabled === false;
    if (this.#pc && this.#pc.getSenders().length > 0) {
      const sender = this.#pc.getSenders().find(s => s.track?.kind === 'video');
      if (sender) {
        await sender.replaceTrack(deviceId ? await this.#obterTrack(deviceId, MediaKind.VIDEO) : track);
      }
    }
    track.enabled = !muteEstadoAnterior;
    this.#muteVideo = muteEstadoAnterior; // preserva o estado de mute ao trocar de periférico
    this.dispatchEvent(new CustomEvent('camera-trocada', { detail: { deviceId } }));
  }

  async #obterTrack(deviceId, kind) {
    const c = kind === MediaKind.AUDIO
      ? { ...this.#config.audioConstraints, deviceId: { exact: deviceId } }
      : { ...this.#config.videoConstraints, deviceId: { exact: deviceId } };
    const s = await navigator.mediaDevices.getUserMedia({ [kind === MediaKind.AUDIO ? 'audio' : 'video']: c });
    return s.getTracks()[0];
  }

  // ---- Captura de mídia ----

  async iniciarCaptura(constraintsOverride = {}) {
    if (this.#stream) await this.pararCaptura();
    if (!this.#consentimentoRegistrado) throw new WebRTCError(ErrorCodes.CONSENT_DENIED, 'Consentimento LGPD obrigatório');
    this.#garantirContextoSeguro();
    const audio = constraintsOverride.audio ?? this.#config.audioConstraints;
    const video = constraintsOverride.video ?? this.#config.videoConstraints;
    this.#stream = await navigator.mediaDevices.getUserMedia({ audio, video });
    this.#registrarDispositivosHotplug();
    this.dispatchEvent(new CustomEvent('captura-iniciada', { detail: { kind: 'local' } }));
    return this.#stream;
  }

  async pararCaptura() {
    if (!this.#stream) return;
    this.#stream.getTracks().forEach(t => t.stop());
    this.#stream = null;
    this.#removerDispositivosHotplug();
    this.dispatchEvent(new CustomEvent('captura-parada', { detail: { kind: 'local' } }));
  }

  // ---- Mute / Unmute ----

  alternarMuteAudio(force) {
    const proximo = force ?? !this.#muteAudio;
    this.definirMuteAudio(proximo);
    return this.#muteAudio;
  }

  definirMuteAudio(valor) {
    this.#muteAudio = Boolean(valor);
    if (this.#stream) {
      this.#stream.getAudioTracks().forEach(t => { t.enabled = !this.#muteAudio; });
    }
    this.dispatchEvent(new CustomEvent('mute-audio', { detail: { mute: this.#muteAudio } }));
  }

  alternarMuteVideo(force) {
    const proximo = force ?? !this.#muteVideo;
    this.definirMuteVideo(proximo);
    return this.#muteVideo;
  }

  definirMuteVideo(valor) {
    this.#muteVideo = Boolean(valor);
    if (this.#stream) {
      this.#stream.getVideoTracks().forEach(t => { t.enabled = !this.#muteVideo; });
    }
    this.dispatchEvent(new CustomEvent('mute-video', { detail: { mute: this.#muteVideo } }));
  }

  isAudioMuted() { return this.#muteAudio; }
  isVideoMuted() { return this.#muteVideo; }

  // ---- Peer Connection ----

  async criarPeerConnection() {
    this.#garantirContextoSeguro();
    const servers = [];
    if (this.#config.stun) servers.push({ urls: this.#config.stun });
    if (this.#config.turn) servers.push(this.#config.turn);
    this.#pc = new RTCPeerConnection({ iceServers: servers });
    this.#pc.onicecandidate = (e) => {
      this.dispatchEvent(new CustomEvent('icecandidate', { detail: e.candidate }));
    };
    this.#pc.ontrack = (e) => {
      this.dispatchEvent(new CustomEvent('track', { detail: e.streams[0] }));
    };
    this.#pc.onconnectionstatechange = () => {
      this.dispatchEvent(new CustomEvent('connectionstatechange', { detail: this.#pc.connectionState }));
    };
    if (this.#stream) {
      this.#stream.getTracks().forEach(t => this.#pc.addTrack(t, this.#stream));
    }
    return this.#pc;
  }

  async criarOferta() {
    if (!this.#pc) throw new WebRTCError(ErrorCodes.PEER_CONNECTION, 'PeerConnection não criada');
    return await this.#pc.createOffer();
  }

  async criarResposta(offerSdp) {
    if (!this.#pc) throw new WebRTCError(ErrorCodes.PEER_CONNECTION, 'PeerConnection não criada');
    await this.#pc.setRemoteDescription(offerSdp);
    return await this.#pc.createAnswer();
  }

  async definirDescricaoLocal(desc) {
    if (!this.#pc) throw new WebRTCError(ErrorCodes.PEER_CONNECTION, 'PeerConnection não criada');
    await this.#pc.setLocalDescription(desc);
  }

  async definirDescricaoRemota(desc) {
    if (!this.#pc) throw new WebRTCError(ErrorCodes.PEER_CONNECTION, 'PeerConnection não criada');
    await this.#pc.setRemoteDescription(desc);
  }

  async adicionarCandidatoRemota(candidate) {
    if (!this.#pc) throw new WebRTCError(ErrorCodes.PEER_CONNECTION, 'PeerConnection não criada');
    if (!this.#pc.remoteDescription) return; // ignora candidato antecessor à descrição remota
    await this.#pc.addIceCandidate(candidate);
  }

  // ---- Substituição de faixa (sem renegociação) ----

  async trocarTrack(kind, deviceId) {
    if (!this.#pc) throw new WebRTCError(ErrorCodes.PEER_CONNECTION, 'PeerConnection não criada');
    const track = await this.#obterTrack(deviceId, kind);
    const senders = this.#pc.getSenders();
    const sender = senders.find(s => s.track?.kind === kind);
    if (sender) await sender.replaceTrack(track);
    return track;
  }

  // ---- Registro de consentimento via dispositivos ----

  #registrarDispositivosHotplug() {
    this.#deviceChangeHandler = () => this.listarDispositivos();
    navigator.mediaDevices.addEventListener("devicechange", this.#deviceChangeHandler);
  }

  #removerDispositivosHotplug() {
    if (this.#deviceChangeHandler) {
      navigator.mediaDevices.removeEventListener("devicechange", this.#deviceChangeHandler);
      this.#deviceChangeHandler = null;
    }
  }

  #garantirContextoSeguro() {
    if (!window.isSecureContext && location.protocol !== 'https:' && location.hostname !== 'localhost') {
      throw new WebRTCError(ErrorCodes.INSECURE_CONTEXT, 'Contexto seguro obrigatório (LGPD/CFM)');
    }
  }

  // ---- Encerramento ----

  fechar() {
    if (this.#encerrado) return;
    this.#encerrado = true;
    if (this.#stream) {
      this.#stream.getTracks().forEach(t => t.stop());
      this.#stream = null;
    }
    this.#removerDispositivosHotplug();
    if (this.#pc) {
      this.#pc.close();
      this.#pc = null;
    }
    this.#consentimentoRegistrado = false;
    this.dispatchEvent(new CustomEvent('encerrado', { detail: {} }));
  }

  get connectionState() { return this.#pc?.connectionState ?? null; }
  get streamLocal() { return this.#stream; }
}
