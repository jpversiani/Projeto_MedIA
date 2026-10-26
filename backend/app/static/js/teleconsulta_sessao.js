/**
 * MedIA — Sessão de teleconsulta (T3): WebSocket de sinalização + WebRTC real.
 *
 * Antes deste módulo o `webrtc_manager.js` existia e era correto, mas **morto**:
 * nenhuma tela o importava e não havia cliente de sinalização. A sala mostrava
 * "Aguardando conexão do paciente" para sempre, e o médico via a própria webcam
 * no lugar do paciente.
 *
 * O que este módulo faz:
 *  - abre o WebSocket de sinalização autenticado (token JWT na query string);
 *  - cria a oferta quando o servidor diz `deve_criar_oferta` (o segundo a
 *    entrar oferece, evitando as duas ofertas simultâneas);
 *  - troca SDP (`offer`/`answer`) e candidatos ICE pelo WebSocket e deixa o
 *    áudio/vídeo fluírem direto entre os navegadores (SRTP/P2P);
 *  - mantém a conexão viva com ping e reconecta com backoff;
 *  - avisa a UI de cada mudança de estado real (nunca "fingindo" que conectou).
 *
 * LGPD/CFM 2.314: o consentimento é pré-requisito para abrir a câmera/áudio e o
 * CNS/CPF nunca entram no SDP nem no tráfego de sinalização.
 */

import { WebRTCManager } from "./webrtc_manager.js";

const INTERVALO_PING_MS = 25000;
const MAX_TENTATIVAS_RECONEXAO = 5;

export class SessaoTeleconsulta extends EventTarget {
  #sala;
  #papel;
  #token;
  #nome;
  #iceServers;
  #ws = null;
  #rtc = null;
  #peerId = null;
  #estado = "inicial";
  #encerradaPeloUsuario = false;
  #tentativas = 0;
  #timerPing = null;
  #timerReconexao = null;
  #icePendente = [];
  #remotaDefinida = false;
  #telaCompartilhada = null;

  constructor({ sala, papel = "medico", token, nome = "Participante", iceServers = [] }) {
    super();
    if (!sala) throw new Error("Código da sala é obrigatório.");
    this.#sala = String(sala).trim();
    this.#papel = papel;
    this.#token = token || "";
    this.#nome = nome;
    this.#iceServers = Array.isArray(iceServers) ? iceServers : [];
  }

  // ---------------------------------------------------------------
  // Ligações expostas para a UI
  // ---------------------------------------------------------------
  get estado() {
    return this.#estado;
  }

  get sala() {
    return this.#sala;
  }

  get peerConectado() {
    return this.#_pcEstado() === "connected";
  }

  get streamLocal() {
    return this.#rtc?.streamLocal ?? null;
  }

  get audioMudo() {
    return this.#rtc?.isAudioMuted() ?? false;
  }

  get videoMudo() {
    return this.#rtc?.isVideoMuted() ?? false;
  }

  #_pcEstado() {
    return this.#rtc?.connectionState ?? null;
  }

  #publicar(novoEstado, detalhe = {}) {
    if (this.#estado === novoEstado) return;
    this.#estado = novoEstado;
    this.dispatchEvent(new CustomEvent("estado", { detail: { estado: novoEstado, ...detalhe } }));
  }

  // ---------------------------------------------------------------
  // Abertura
  // ---------------------------------------------------------------
  async iniciar() {
    if (this.#ws) return;
    this.#publicar("conectando");

    await this.#criarWebRTC();
    await this.#abrirWebSocket();
  }

  async #criarWebRTC() {
    if (this.#rtc) return;

    this.#rtc = new WebRTCManager({
      stun: this.#iceServers.find((s) => String(s.urls).startsWith("stun:"))?.urls ?? null,
      turn: this.#iceServers.find((s) => String(s.urls).startsWith("turn:")) ?? null,
    });

    // O consentimento é obrigatório no manager: sem isso ele recusa abrir a
    // câmera. A tela só chama `iniciar()` depois do aceite do TCLE.
    await this.#rtc.registrarConsentimento({ aceite: true });

    this.#rtc.addEventListener("icecandidate", (evento) => {
      const candidato = evento.detail;
      if (!candidato) return;
      this.#enviar({
        tipo: "ice_candidate",
        payload: { candidate: candidato.toJSON ? candidato.toJSON() : candidato },
      });
    });

    this.#rtc.addEventListener("track", (evento) => {
      this.dispatchEvent(new CustomEvent("stream-remoto", { detail: { stream: evento.detail } }));
    });

    this.#rtc.addEventListener("connectionstatechange", (evento) => {
      const estadoPc = evento.detail;
      if (estadoPc === "connected") {
        this.#tentativas = 0;
        this.#publicar("conectado");
      } else if (estadoPc === "failed") {
        this.#publicar("erro", { motivo: "Falha na conexão P2P (NAT/firewall)." });
      } else if (estadoPc === "disconnected") {
        this.#publicar("reconectando");
      }
    });

    await this.#rtc.iniciarCaptura();

    // A `RTCPeerConnection` NÃO é criada aqui de propósito. A lista de servidores
    // ICE (STUN/TURN) chega na mensagem `sala_ingressada`, e a conexão captura a
    // configuração no momento em que é criada — criar antes significaria subir
    // só com STUN e nunca usar o TURN que o servidor mandou. Em rede com
    // firewall, é exatamente o TURN que faz a chamada conectar.
    this.dispatchEvent(
      new CustomEvent("stream-local", { detail: { stream: this.#rtc.streamLocal } })
    );
  }

  /**
   * Cria a PeerConnection uma única vez, já com a lista de ICE do servidor.
   *
   * Chamada no `sala_ingressada` (quando a lista chega) e novamente antes de
   * responder uma oferta; o guarda evita uma segunda conexão após reconectar.
   */
  async #garantirPeerConnection() {
    if (!this.#rtc) return;

    const existente = this.#rtc.peerConnection;
    if (existente) {
      // Reconexão: reaproveita o par, mas força nova coleta de candidatos —
      // sem `restartIce` a rede pode ter mudado (Wi-Fi → 4G) e o par nunca
      // volta a subir.
      try {
        existente.restartIce();
      } catch (erro) {
        /* navegador antigo: segue sem restart */
      }
      return;
    }

    this.#rtc.definirIceServers(this.#iceServers);
    await this.#rtc.criarPeerConnection();
    this.#remotaDefinida = false;
    this.#icePendente = [];
  }

  #urlWebSocket() {
    const protocolo = window.location.protocol === "https:" ? "wss:" : "ws:";
    const params = new URLSearchParams({ papel: this.#papel });
    // O navegador não permite cabeçalhos em `new WebSocket()`, então o token
    // vai na query string (o servidor também aceita o header, se existir).
    if (this.#token) params.set("token", this.#token);
    return `${protocolo}//${window.location.host}/api/v1/ws/telemedicina/sala/${encodeURIComponent(
      this.#sala
    )}?${params.toString()}`;
  }

  #abrirWebSocket() {
    return new Promise((resolver, rejeitar) => {
      let resolvido = false;
      try {
        this.#ws = new WebSocket(this.#urlWebSocket());
      } catch (erro) {
        this.#publicar("erro", { motivo: "Não foi possível abrir o WebSocket." });
        rejeitar(erro);
        return;
      }

      this.#ws.onopen = () => {
        this.#tentativas = 0;
        this.#iniciarPing();
      };

      this.#ws.onmessage = (evento) => {
        let mensagem;
        try {
          mensagem = JSON.parse(evento.data);
        } catch (erro) {
          return;
        }
        this.#tratarMensagem(mensagem).then(() => {
          if (!resolvido && mensagem.tipo === "sala_ingressada") {
            resolvido = true;
            resolver();
          }
        });
      };

      this.#ws.onerror = () => {
        if (!resolvido) {
          resolvido = true;
          this.#publicar("erro", { motivo: "Erro no WebSocket de sinalização." });
          rejeitar(new Error("Erro no WebSocket de sinalização."));
        }
      };

      this.#ws.onclose = (evento) => {
        this.#pararPing();
        if (this.#encerradaPeloUsuario) {
          this.#publicar("encerrada");
          return;
        }
        this.#publicar("reconectando", { codigo: evento.code });
        this.#agendarReconexao();
      };
    });
  }

  // ---------------------------------------------------------------
  // Reconexão / heartbeat
  // ---------------------------------------------------------------
  #iniciarPing() {
    this.#pararPing();
    this.#timerPing = setInterval(() => {
      this.#enviar({ tipo: "ping", payload: {} });
    }, INTERVALO_PING_MS);
  }

  #pararPing() {
    if (this.#timerPing) {
      clearInterval(this.#timerPing);
      this.#timerPing = null;
    }
  }

  #agendarReconexao() {
    if (this.#tentativas >= MAX_TENTATIVAS_RECONEXAO) {
      this.#publicar("erro", {
        motivo: "Conexão perdida e não foi possível reconectar. Reabra a teleconsulta.",
      });
      return;
    }
    this.#tentativas += 1;
    const espera = Math.min(1000 * 2 ** (this.#tentativas - 1), 15000);
    this.#timerReconexao = setTimeout(() => {
      if (this.#encerradaPeloUsuario) return;
      this.#abrirWebSocket().catch(() => null);
    }, espera);
  }

  // ---------------------------------------------------------------
  // Sinalização
  // ---------------------------------------------------------------
  async #tratarMensagem(mensagem) {
    const { tipo, payload = {} } = mensagem || {};

    switch (tipo) {
      case "sala_ingressada": {
        this.#peerId = payload.seu_id ?? null;
        if (Array.isArray(payload.ice_servers) && payload.ice_servers.length) {
          this.#iceServers = payload.ice_servers;
        }
        this.dispatchEvent(
          new CustomEvent("sala", { detail: { sala: this.#sala, participantes: payload.participantes ?? [] } })
        );
        // Agora sim existe a lista de ICE: só então faz sentido abrir o par.
        await this.#garantirPeerConnection();
        if (payload.deve_criar_oferta) {
          await this.#ofertar();
        } else {
          this.#publicar("aguardando");
        }
        return;
      }

      case "peer_joined": {
        this.dispatchEvent(
          new CustomEvent("peer-entrou", { detail: { participante: payload.participante } })
        );
        // Quem já estava espera a oferta de quem chegou.
        if (this.#estado === "aguardando") this.#publicar("negociando");
        return;
      }

      case "offer": {
        await this.#responderOferta(payload);
        return;
      }

      case "answer": {
        await this.#aplicarResposta(payload);
        return;
      }

      case "ice_candidate": {
        await this.#aplicarIce(payload);
        return;
      }

      case "peer_left": {
        this.#publicar("aguardando", { motivo: "O outro participante saiu." });
        this.dispatchEvent(
          new CustomEvent("peer-saiu", { detail: { participante: payload.participante } })
        );
        return;
      }

      case "estado_medico":
      case "estado_paciente":
      case "consentimento": {
        this.dispatchEvent(new CustomEvent("mensagem", { detail: mensagem }));
        return;
      }

      case "pong":
        return;

      case "erro": {
        const motivo = payload.motivo || "Erro de sinalização.";
        this.#publicar("erro", { motivo });
        this.dispatchEvent(new CustomEvent("erro", { detail: { motivo } }));
        return;
      }

      default:
        return;
    }
  }

  async #ofertar() {
    if (!this.#rtc) return;
    this.#publicar("negociando");
    const oferta = await this.#rtc.criarOferta();
    await this.#rtc.definirDescricaoLocal(oferta);
    this.#enviar({ tipo: "offer", payload: { sdp: oferta.sdp, type: oferta.type } });
  }

  async #responderOferta(payload) {
    if (!this.#rtc) return;
    await this.#garantirPeerConnection();
    this.#publicar("negociando");
    const descricao = new RTCSessionDescription({ type: "offer", sdp: payload.sdp });
    const resposta = await this.#rtc.criarResposta(descricao);
    await this.#rtc.definirDescricaoLocal(resposta);
    this.#remotaDefinida = true;
    this.#enviar({ tipo: "answer", payload: { sdp: resposta.sdp, type: resposta.type } });
    await this.#despejarIce();
  }

  async #aplicarResposta(payload) {
    if (!this.#rtc) return;
    const descricao = new RTCSessionDescription({ type: "answer", sdp: payload.sdp });
    await this.#rtc.definirDescricaoRemota(descricao);
    this.#remotaDefinida = true;
    await this.#despejarIce();
  }

  async #aplicarIce(payload) {
    const bruto = payload.candidate;
    if (!bruto) return;
    if (!this.#remotaDefinida) {
      // Candidato chegou antes do SDP remoto: guarda e aplica depois.
      this.#icePendente.push(bruto);
      return;
    }
    try {
      await this.#rtc.adicionarCandidatoRemota(bruto);
    } catch (erro) {
      // Candidato inválido/atrasado não pode derrubar a chamada.
    }
  }

  async #despejarIce() {
    const pendentes = this.#icePendente;
    this.#icePendente = [];
    for (const candidato of pendentes) {
      try {
        await this.#rtc.adicionarCandidatoRemota(candidato);
      } catch (erro) {
        // ignora candidato inválido
      }
    }
  }

  #enviar(mensagem) {
    if (!this.#ws || this.#ws.readyState !== WebSocket.OPEN) return false;
    try {
      this.#ws.send(JSON.stringify(mensagem));
      return true;
    } catch (erro) {
      return false;
    }
  }

  // ---------------------------------------------------------------
  // Controles de mídia
  // ---------------------------------------------------------------
  alternarAudio() {
    return this.#rtc ? this.#rtc.alternarMuteAudio() : false;
  }

  alternarVideo() {
    return this.#rtc ? this.#rtc.alternarMuteVideo() : false;
  }

  /**
   * Compartilhamento de tela usa `replaceTrack` — sem renegociação, o que
   * evita uma nova troca de SDP no meio do atendimento.
   */
  async compartilharTela() {
    if (!this.#rtc) return null;
    const tela = await navigator.mediaDevices.getDisplayMedia({ video: true });
    const trilha = tela.getVideoTracks()[0];

    // Substitui a faixa de vídeo no sender: a tela vai para o paciente sem
    // renegociar o SDP e sem interromper o áudio.
    await this.#rtc.substituirTrackVideo(trilha);
    this.#telaCompartilhada = tela;

    // O usuário também pode encerrar pelo botão nativo do navegador.
    trilha.addEventListener("ended", () => {
      this.pararCompartilhamentoTela().catch(() => null);
    });

    this.dispatchEvent(new CustomEvent("tela-compartilhada", { detail: { stream: tela, trilha } }));
    return tela;
  }

  async pararCompartilhamentoTela() {
    if (this.#telaCompartilhada) {
      this.#telaCompartilhada.getTracks().forEach((t) => t.stop());
      this.#telaCompartilhada = null;
    }
    if (!this.#rtc) return null;
    // Volta para a câmera padrão (sem deviceId = dispositivo padrão).
    const camera = await this.#rtc.trocarTrack("video");
    this.dispatchEvent(new CustomEvent("tela-encerrada", { detail: { trilha: camera } }));
    return camera;
  }

  enviarEstadoClinico(status) {
    const tipo = this.#papel === "medico" ? "estado_medico" : "estado_paciente";
    return this.#enviar({ tipo, payload: { status, de: this.#nome } });
  }

  enviarConsentimento(escopo) {
    return this.#enviar({ tipo: "consentimento", payload: { escopo } });
  }

  // ---------------------------------------------------------------
  // Encerramento
  // ---------------------------------------------------------------
  encerrar() {
    this.#encerradaPeloUsuario = true;
    this.#pararPing();
    if (this.#timerReconexao) {
      clearTimeout(this.#timerReconexao);
      this.#timerReconexao = null;
    }
    if (this.#ws && this.#ws.readyState === WebSocket.OPEN) {
      this.#enviar({ tipo: "leave_sala", payload: {} });
      try {
        this.#ws.close(1000);
      } catch (erro) {
        /* já fechado */
      }
    }
    this.#ws = null;

    if (this.#rtc) {
      this.#rtc.fechar();
      this.#rtc = null;
    }
    this.#publicar("encerrada");
  }
}
