/**
 * ============================================================================
 * Projeto MedIA (SUS/APS) — Módulo de Compartilhamento de Tela na Teleconsulta
 * ============================================================================
 *
 * Módulo ES responsável por compartilhar a tela/janela do médico com o
 * paciente durante a teleconsulta, usando a API `getDisplayMedia` (WebRTC).
 *
 * Estratégia de transmissão:
 *   - A trilha de vídeo da câmera do médico é SUBSTITUÍDA no RTCPeerConnection
 *     existente por meio de `RTCRtpSender.replaceTrack()`, SEM renegociação
 *     (SDP) e SEM interromper o áudio da consulta.
 *   - Ao encerrar o compartilhamento, a trilha original da câmera é restaurada.
 *
 * Diretrizes:
 *   - Interface HTML5 + Tailwind CSS (indicador de transmissão e avisos).
 *   - Mensagens amigáveis ao médico em Português do Brasil.
 *
 * Exemplo de uso:
 *   import { ScreenShareManager } from '/static/js/screen_share.js';
 *
 *   const gerenciador = new ScreenShareManager({
 *     peerConnection: pc,               // RTCPeerConnection já negociada
 *     cameraStream: fluxoCamaraLocal,   // MediaStream da câmera do médico
 *     elementoVideoLocal: videoLocal,   // <video> de pré-visualização local
 *     elementoIndicador: badgeTransmissao, // <span> do indicador (opcional)
 *     onAlteracaoEstado: (modo) => console.info('Modo atual:', modo),
 *     onErro: (erro) => console.error(erro),
 *   });
 *
 *   // Iniciar compartilhamento (deve ocorrer dentro de um gesto do usuário,
 *   // por exemplo, no clique de um botão "Compartilhar tela").
 *   await gerenciador.iniciar('tela');   // 'tela' (monitor) ou 'janela'
 *
 *   // Alternar entre câmera e tela:
 *   await gerenciador.alternar();
 *
 *   // Encerrar e restaurar a câmera:
 *   await gerenciador.parar();
 */

'use strict';

/** @typedef {'camera'|'tela'} ModoTransmissao Modo atual da trilha de vídeo enviada. */

/** @typedef {'tela'|'janela'} PreferenciaFonte Fonte preferida pelo médico (monitor ou janela). */

/** @typedef {'nenhum'|'permissao_negada'|'sem_fonte'|'fonte_indisponivel'|'cancelado'|'navegador_sem_suporte'|'erro_interno'} TipoErroCompartilhamento */

/**
 * @typedef {Object} OpcoesScreenShareManager
 * @property {RTCPeerConnection|null} [peerConnection] Conexão WebRTC existente da teleconsulta.
 * @property {MediaStream|null}       [cameraStream]   MediaStream local da câmera do médico.
 * @property {HTMLVideoElement|null}  [elementoVideoLocal] Elemento <video> de pré-visualização local.
 * @property {HTMLElement|null}       [elementoIndicador]  Elemento do indicador de transmissão ativa.
 * @property {HTMLElement|null}       [containerIndicador] Container onde o indicador será criado, se não informado.
 * @property {boolean}                [comAudioSistema=false] Capturar também o áudio do sistema.
 * @property {((modo: ModoTransmissao) => void)} [onAlteracaoEstado] Callback ao mudar o modo (câmera/tela).
 * @property {((erro: {tipo: TipoErroCompartilhamento, mensagem: string}) => void)} [onErro] Callback de erro amigável.
 * @property {((trilha: MediaStreamTrack|null, origem: ModoTransmissao) => void)} [onTrilhaSubstituida] Callback após `replaceTrack`.
 */

/** Textos amigáveis exibidos ao médico, conforme o tipo de falha. */
const MENSAGENS_ERRO = Object.freeze({
  permissao_negada:
    'Permissão negada pelo navegador. Para compartilhar sua tela na teleconsulta, ' +
    'clique no ícone de cadeado/câmera na barra de endereço, autorize o ' +
    'compartilhamento de tela e tente novamente.',
  sem_fonte:
    'Nenhuma tela ou janela foi selecionada. Escolha uma fonte de vídeo e clique em "Compartilhar".',
  fonte_indisponivel:
    'A tela ou janela selecionada não pôde ser capturada. Ela pode estar protegida ' +
    '(conteúdo com DRM) ou em uso por outro aplicativo. Tente compartilhar outra janela.',
  cancelado:
    'Compartilhamento de tela cancelado. Você pode tentar novamente quando desejar.',
  navegador_sem_suporte:
    'Este navegador não oferece suporte ao compartilhamento de tela. Utilize o ' +
    'Google Chrome, Microsoft Edge ou Firefox atualizados.',
  erro_interno:
    'Não foi possível iniciar o compartilhamento de tela. Verifique sua conexão ' +
    'e tente novamente. Se o problema persistir, acione o suporte técnico.',
});

/** Classe Tailwind do indicador de transmissão ativa. */
const CLASSES_INDICADOR =
  'inline-flex items-center gap-2 rounded-full bg-red-600 px-3 py-1.5 text-xs ' +
  'font-semibold text-white shadow-md transition-opacity duration-200';

/**
 * Gerenciador de compartilhamento de tela da teleconsulta (WebRTC).
 *
 * Substitui a trilha de vídeo da câmera pela trilha da tela via
 * `replaceTrack`, sem renegociação SDP, e cuida da alternância,
 * do indicador visual e dos erros de permissão.
 */
export class ScreenShareManager {
  /**
   * @param {OpcoesScreenShareManager} [opcoes={}] Configurações do gerenciador.
   */
  constructor(opcoes = {}) {
    /** @type {RTCPeerConnection|null} */
    this._peerConnection = opcoes.peerConnection ?? null;

    /** @type {MediaStream|null} Fluxo original da câmera (fonte de restauração). */
    this._cameraStream = opcoes.cameraStream ?? null;

    /** @type {HTMLVideoElement|null} */
    this._elementoVideoLocal = opcoes.elementoVideoLocal ?? null;

    /** @type {HTMLElement|null} */
    this._elementoIndicador = opcoes.elementoIndicador ?? null;

    /** @type {HTMLElement|null} */
    this._containerIndicador = opcoes.containerIndicador ?? null;

    /** @type {boolean} */
    this._comAudioSistema = opcoes.comAudioSistema === true;

    /** @type {ModoTransmissao} Modo atual da trilha de vídeo transmitida. */
    this._modo = 'camera';

    /** @type {MediaStream|null} Fluxo da tela obtido via getDisplayMedia. */
    this._telaStream = null;

    /** @type {MediaStreamTrack|null} Trilha de vídeo original da câmera. */
    this._trilhaCamera = this._cameraStream?.getVideoTracks()[0] ?? null;

    /** @type {MediaStreamTrack|null} Trilha de áudio original (microfone). */
    this._trilhaMicrofone = this._cameraStream?.getAudioTracks()[0] ?? null;

    /** @type {MediaStreamTrack|null} Trilha de áudio da tela (se capturada). */
    this._trilhaAudioTela = null;

    /** @type {boolean} Indica se existe áudio de sistema substituindo o microfone. */
    this._audioSistemaAtivo = false;

    /** @type {boolean} Indica se o indicador foi criado internamente pelo módulo. */
    this._indicadorProprio = false;

    /** @type {HTMLElement|null} Elemento de aviso (toast) em exibição. */
    this._toastErro = null;

    /** @type {number|null} Identificador do temporizador do toast. */
    this._temporizadorToast = null;

    /** @type {(modo: ModoTransmissao) => void} */
    this._onAlteracaoEstado = typeof opcoes.onAlteracaoEstado === 'function'
      ? opcoes.onAlteracaoEstado
      : () => {};

    /** @type {(erro: {tipo: TipoErroCompartilhamento, mensagem: string}) => void} */
    this._onErro = typeof opcoes.onErro === 'function'
      ? opcoes.onErro
      : () => {};

    /** @type {(trilha: MediaStreamTrack|null, origem: ModoTransmissao) => void} */
    this._onTrilhaSubstituida = typeof opcoes.onTrilhaSubstituida === 'function'
      ? opcoes.onTrilhaSubstituida
      : () => {};
  }

  /* ==========================================================================
   * Propriedades públicas (somente leitura)
   * ========================================================================== */

  /** @returns {ModoTransmissao} Modo atual: 'camera' ou 'tela'. */
  get modo() {
    return this._modo;
  }

  /** @returns {boolean} True se a tela do médico está sendo transmitida. */
  get compartilhando() {
    return this._modo === 'tela' && this._telaStream !== null;
  }

  /** @returns {MediaStream|null} Fluxo da tela compartilhada (ou null). */
  get telaStream() {
    return this._telaStream;
  }

  /* ==========================================================================
   * API pública
   * ========================================================================== */

  /**
   * Inicia o compartilhamento de tela e substitui a trilha de vídeo
   * da câmera na conexão WebRTC existente (sem renegociação).
   *
   * Deve ser chamado dentro de um gesto do usuário (clique em botão).
   *
   * @param {PreferenciaFonte} [preferencia='tela'] Fonte preferida: 'tela' (monitor) ou 'janela'.
   * @returns {Promise<boolean>} True em caso de sucesso; False se o usuário cancelou ou houve falha.
   */
  async iniciar(preferencia = 'tela') {
    if (this.compartilhando) {
      console.info('[ScreenShareManager] O compartilhamento já está ativo.');
      return true;
    }

    // Atualiza a referência da trilha da câmera (pode ter mudado na sessão).
    this._atualizarTrilhaCamera();

    const telaStream = await this._capturarTela(preferencia);
    if (!telaStream) {
      // A captura falhou ou foi cancelada; a mensagem já foi tratada.
      return false;
    }

    // Registra o fluxo antes das validações para garantir liberação dos recursos.
    this._telaStream = telaStream;

    const trilhaTela = telaStream.getVideoTracks()[0];
    if (!trilhaTela) {
      this._destruirFluxoTela();
      this._reportarErro('erro_interno', MENSAGENS_ERRO.erro_interno);
      return false;
    }

    this._trilhaAudioTela = telaStream.getAudioTracks()[0] ?? null;

    // Se o médico encerrar pelo botão nativo do navegador ("Parar
    // compartilhamento"), restaura a câmera automaticamente.
    trilhaTela.addEventListener('ended', () => {
      if (this.compartilhando) {
        void this.parar();
      }
    });

    // Pré-visualização local passa a exibir a tela compartilhada.
    this._exibirNaPrevisualizacao(telaStream);

    // Substituição da trilha de vídeo no remetente existente (sem renegociar).
    const substituicaoVideo = await this._substituirTrilhaVideo(trilhaTela, 'tela');

    // Áudio do sistema (opcional): substitui a trilha do microfone, se existir remetente.
    await this._substituirTrilhaAudio(this._trilhaAudioTela);

    if (substituicaoVideo) {
      this._modo = 'tela';
      this._exibirIndicador(true);
      this._notificarEstado();
      return true;
    }

    // Falha ao substituir: desfaz a captura para não vazar recursos.
    await this.parar();
    return false;
  }

  /**
   * Encerra o compartilhamento e restaura a transmissão da câmera,
   * substituindo novamente a trilha no remetente (sem renegociar).
   *
   * @returns {Promise<void>}
   */
  async parar() {
    // Restaura a trilha de vídeo da câmera no remetente (se houver).
    // Restauração silenciosa: sem avisos ao médico durante o encerramento.
    await this._substituirTrilhaVideo(this._trilhaCamera, 'camera', true);

    // Restaura a trilha de áudio do microfone, caso o áudio do sistema estivesse ativo.
    if (this._audioSistemaAtivo) {
      await this._substituirTrilhaAudio(null);
    }

    this._destruirFluxoTela();

    // Pré-visualização local volta a exibir a câmera.
    this._exibirNaPrevisualizacao(this._cameraStream);

    this._audioSistemaAtivo = false;
    this._modo = 'camera';
    this._exibirIndicador(false);
    this._notificarEstado();
  }

  /**
   * Alterna entre tela compartilhada e câmera, conforme o modo atual.
   *
   * @returns {Promise<boolean>} True se a operação surtiu efeito.
   */
  async alternar() {
    return this.compartilhando ? this.parar().then(() => true) : this.iniciar();
  }

  /**
   * Indica se o navegador oferece suporte à API `getDisplayMedia`.
   *
   * @returns {boolean} True se o compartilhamento de tela está disponível.
   */
  static suportado() {
    return typeof navigator !== 'undefined'
      && typeof navigator.mediaDevices?.getDisplayMedia === 'function';
  }

  /**
   * Libera todos os recursos e remove elementos visuais criados.
   * Chamar ao encerrar a teleconsulta.
   *
   * @returns {Promise<void>}
   */
  async destruir() {
    await this.parar();
    this._toastErro?.remove();
    this._toastErro = null;
    // Remove o indicador apenas quando foi criado pelo próprio módulo.
    if (this._indicadorProprio) {
      this._elementoIndicador?.remove();
      this._indicadorProprio = false;
    }
    this._elementoIndicador = null;
    this._elementoVideoLocal = null;
    this._peerConnection = null;
    this._cameraStream = null;
    this._trilhaCamera = null;
    this._trilhaMicrofone = null;
  }

  /* ==========================================================================
   * Métodos privados — captura e negociação
   * ========================================================================== */

  /**
   * Captura a tela/janela do médico com preferências declaradas.
   * Trata erros de permissão com mensagem amigável.
   *
   * @param {PreferenciaFonte} preferencia Fonte preferida pelo médico.
   * @returns {Promise<MediaStream|null>} Fluxo capturado ou null em falha/cancelamento.
   * @private
   */
  async _capturarTela(preferencia) {
    if (!ScreenShareManager.suportado()) {
      this._reportarErro('navegador_sem_suporte', MENSAGENS_ERRO.navegador_sem_suporte);
      return null;
    }

    const limitesVideo = {
      // Preferência de fonte: monitor inteiro ou janela específica.
      // O navegador pode não honrar o campo, mas o seletor inicia filtrado.
      displaySurface: preferencia === 'janela' ? 'window' : 'monitor',
      // Resolução e taxa de quadros moderadas: prioriza estabilidade e
      // economia de banda em redes típicas da APS.
      width: { ideal: 1920, max: 1920 },
      height: { ideal: 1080, max: 1080 },
      frameRate: { ideal: 10, max: 15 },
    };

    try {
      return await navigator.mediaDevices.getDisplayMedia({
        video: limitesVideo,
        audio: this._comAudioSistema,
      });
    } catch (erro) {
      this._tratarErroCaptura(erro);
      return null;
    }
  }

  /**
   * Substitui a trilha de vídeo no remetente existente do RTCPeerConnection,
   * sem renegociar o SDP (`RTCRtpSender.replaceTrack`).
   *
   * @param {MediaStreamTrack|null} trilha Nova trilha de vídeo (tela) ou trilha da câmera na restauração.
   * @param {ModoTransmissao} origem Modo que passa a ser transmitido.
   * @param {boolean} [silencioso=false] True para não exibir aviso ao médico (usado na restauração/encerramento).
   * @returns {Promise<boolean>} True se a substituição ocorreu (ou não era necessária).
   * @private
   */
  async _substituirTrilhaVideo(trilha, origem, silencioso = false) {
    const remetente = this._obterRemetente('video');

    if (!remetente) {
      // Sem remetente de vídeo: se há trilha e conexão, adiciona (pode exigir
      // renegociação pela aplicação — sinalizado via console).
      if (trilha && this._peerConnection) {
        try {
          this._peerConnection.addTrack(trilha, this._cameraStream ?? new MediaStream([trilha]));
          console.warn(
            '[ScreenShareManager] Trilha de vídeo adicionada via addTrack; ' +
            'pode ser necessária renegociação (onnegotiationneeded).',
          );
          this._onTrilhaSubstituida(trilha, origem);
          return true;
        } catch (erro) {
          console.error('[ScreenShareManager] Falha ao adicionar trilha de vídeo:', erro);
        }
      }
      if (!silencioso) {
        this._reportarErro(
          'erro_interno',
          'A trilha de vídeo não pôde ser transmitida. Verifique se a câmera está ativa e tente novamente.',
        );
      }
      return false;
    }

    try {
      await remetente.replaceTrack(trilha);
      this._modo = origem;
      this._onTrilhaSubstituida(trilha, origem);
      return true;
    } catch (erro) {
      console.error('[ScreenShareManager] Falha em replaceTrack:', erro);
      if (!silencioso) {
        this._reportarErro(
          'erro_interno',
          'Não foi possível alternar o vídeo da teleconsulta. Tente novamente ou continue apenas com áudio.',
        );
      }
      return false;
    }
  }

  /**
   * Substitui a trilha de áudio do remetente (áudio do sistema no lugar do
   * microfone, ou vice-versa), também sem renegociação.
   *
   * @param {MediaStreamTrack|null} trilhaAudioTela Trilha de áudio da tela; null restaura o microfone.
   * @returns {Promise<void>}
   * @private
   */
  async _substituirTrilhaAudio(trilhaAudioTela) {
    const remetente = this._obterRemetente('audio');

    if (trilhaAudioTela) {
      if (!remetente) {
        console.info(
          '[ScreenShareManager] Áudio do sistema capturado, mas sem remetente de áudio; será ignorado.',
        );
        return;
      }
      try {
        await remetente.replaceTrack(trilhaAudioTela);
        this._audioSistemaAtivo = true;
      } catch (erro) {
        console.warn('[ScreenShareManager] Falha ao compartilhar áudio do sistema:', erro);
      }
      return;
    }

    // Restauração: devolve o microfone ao remetente.
    if (this._audioSistemaAtivo && remetente) {
      try {
        await remetente.replaceTrack(this._trilhaMicrofone);
      } catch (erro) {
        console.warn('[ScreenShareManager] Falha ao restaurar o microfone:', erro);
      }
    }
  }

  /**
   * Localiza o remetente (sender) do tipo informado na conexão existente.
   *
   * @param {'video'|'audio'} tipo Tipo de trilha do remetente desejado.
   * @returns {RTCRtpSender|null} Remetente correspondente ou null.
   * @private
   */
  _obterRemetente(tipo) {
    if (!this._peerConnection) {
      return null;
    }
    return (
      // 1) Remetente já transmitindo uma trilha do tipo solicitado;
      this._peerConnection.getSenders().find((remetente) => remetente.track?.kind === tipo)
      // 2) Ou um remetente ainda sem trilha (não transmite nada).
      ?? this._peerConnection.getSenders().find((remetente) => remetente.track === null)
      ?? null
    );
  }

  /**
   * Reavalia a trilha de vídeo da câmera (ex.: após reconexão de mídia).
   * @private
   */
  _atualizarTrilhaCamera() {
    this._trilhaCamera = this._cameraStream?.getVideoTracks()[0] ?? null;
    if (!this._trilhaCamera) {
      console.warn(
        '[ScreenShareManager] Nenhuma trilha de câmera disponível para restauração posterior.',
      );
    }
  }

  /**
   * Interpreta falhas de `getDisplayMedia` e gera mensagem amigável ao médico.
   *
   * @param {unknown} erro Erro lançado pelo navegador.
   * @returns {void}
   * @private
   */
  _tratarErroCaptura(erro) {
    const nome = /** @type {DOMException} */ (erro)?.name ?? '';

    switch (nome) {
      case 'NotAllowedError':
      case 'PermissionDeniedError':
        // Caso mais relevante ao médico: permissão negada no seletor ou pelo SO.
        this._reportarErro('permissao_negada', MENSAGENS_ERRO.permissao_negada);
        break;
      case 'NotFoundError':
      case 'DevicesNotFoundError':
        this._reportarErro('sem_fonte', MENSAGENS_ERRO.sem_fonte);
        break;
      case 'NotReadableError':
      case 'TrackStartError':
        this._reportarErro('fonte_indisponivel', MENSAGENS_ERRO.fonte_indisponivel);
        break;
      case 'AbortError':
        // Médico fechou o seletor sem escolher: aviso leve, sem alarde.
        this._reportarErro('cancelado', MENSAGENS_ERRO.cancelado);
        break;
      case 'InvalidStateError':
        this._reportarErro(
          'erro_interno',
          'O documento não está ativo para iniciar o compartilhamento. Interaja com a página e tente novamente.',
        );
        break;
      default:
        console.error('[ScreenShareManager] Erro inesperado na captura de tela:', erro);
        this._reportarErro('erro_interno', MENSAGENS_ERRO.erro_interno);
    }
  }

  /* ==========================================================================
   * Métodos privados — interface (Tailwind) e notificações
   * ========================================================================== */

  /**
   * Exibe ou oculta o indicador de transmissão ativa (Tailwind CSS).
   * Reutiliza `elementoIndicador` informado ou cria um no container/body.
   *
   * @param {boolean} ativo True para exibir "transmitindo"; false para ocultar.
   * @returns {void}
   * @private
   */
  _exibirIndicador(ativo) {
    if (!this._elementoIndicador) {
      // Não há necessidade de criar o indicador apenas para mantê-lo oculto.
      if (!ativo) {
        return;
      }
      this._criarIndicador();
    }
    if (!this._elementoIndicador) {
      return;
    }

    this._elementoIndicador.classList.toggle('hidden', !ativo);
    this._elementoIndicador.setAttribute('aria-hidden', String(!ativo));
  }

  /**
   * Cria dinamicamente o indicador de transmissão ativa com Tailwind CSS.
   * @returns {void}
   * @private
   */
  _criarIndicador() {
    const container = this._containerIndicador ?? document.body;
    if (!container) {
      return;
    }

    const indicador = document.createElement('div');
    indicador.id = 'indicador-transmissao-ativa';
    indicador.className = CLASSES_INDICADOR;
    indicador.setAttribute('role', 'status');
    indicador.setAttribute('aria-live', 'polite');

    // Ponto pulsante de "ao vivo".
    const ponto = document.createElement('span');
    ponto.className = 'h-2 w-2 animate-pulse rounded-full bg-white';

    const texto = document.createElement('span');
    texto.textContent = 'Tela compartilhada com o paciente';

    indicador.append(ponto, texto);

    // Oculto até o início da transmissão.
    indicador.classList.add('hidden');

    container.appendChild(indicador);
    this._elementoIndicador = indicador;
    this._indicadorProprio = true;
  }

  /**
   * Define o fluxo exibido na pré-visualização local, se configurada.
   *
   * @param {MediaStream|null} fluxo Fluxo a exibir (tela ou câmera).
   * @returns {void}
   * @private
   */
  _exibirNaPrevisualizacao(fluxo) {
    if (!this._elementoVideoLocal) {
      return;
    }
    this._elementoVideoLocal.srcObject = fluxo ?? null;
  }

  /**
   * Encerra as trilhas e libera o fluxo da tela compartilhada.
   * @returns {void}
   * @private
   */
  _destruirFluxoTela() {
    this._telaStream?.getTracks().forEach((trilha) => trilha.stop());
    this._telaStream = null;
    this._trilhaAudioTela = null;
  }

  /**
   * Emite a alteração de estado para o callback e para o console.
   * @returns {void}
   * @private
   */
  _notificarEstado() {
    this._onAlteracaoEstado(this._modo);
  }

  /**
   * Reporta um erro amigável: registra no console, repassa ao callback
   * `onErro` e exibe um aviso (toast) para o médico.
   *
   * @param {TipoErroCompartilhamento} tipo Classificação do erro.
   * @param {string} mensagem Mensagem amigável em Português do Brasil.
   * @returns {void}
   * @private
   */
  _reportarErro(tipo, mensagem) {
    const erro = Object.freeze({ tipo, mensagem });
    console.error(`[ScreenShareManager] ${tipo}: ${mensagem}`);
    this._onErro(erro);
    this._exibirToastErro(mensagem);
  }

  /**
   * Exibe um aviso (toast) com Tailwind CSS, auto-dismissível, para o médico.
   *
   * @param {string} mensagem Mensagem amigável a ser exibida.
   * @returns {void}
   * @private
   */
  _exibirToastErro(mensagem) {
    // Evita empilhar múltiplos avisos simultâneos.
    this._toastErro?.remove();

    const toast = document.createElement('div');
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.className =
      'fixed top-4 right-4 z-50 max-w-md rounded-lg border border-red-200 ' +
      'bg-red-50 p-4 text-sm text-red-800 shadow-lg';

    const titulo = document.createElement('p');
    titulo.className = 'mb-1 font-semibold';
    titulo.textContent = 'Compartilhamento de tela';

    const conteudo = document.createElement('p');
    conteudo.textContent = mensagem;

    const botaoFechar = document.createElement('button');
    botao.type = 'button';
    botao.className =
      'mt-2 rounded px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-100 ' +
      'focus:outline-none focus:ring-2 focus:ring-red-400';
    botao.setAttribute('aria-label', 'Fechar aviso');
    botao.textContent = 'Fechar';
    botao.addEventListener('click', () => {
      toast.remove();
      if (this._temporizadorToast !== null) {
        clearTimeout(this._temporizadorToast);
        this._temporizadorToast = null;
      }
    });

    toast.append(titulo, conteudo, botao);
    document.body.appendChild(toast);
    this._toastErro = toast;

    // Remove automaticamente após 8 segundos.
    this._temporizadorToast = window.setTimeout(() => {
      toast.remove();
      this._toastErro = null;
      this._temporizadorToast = null;
    }, 8000);
  }
}

/** Exportação nomeada auxiliar para checagem de suporte no template. */
export const compartilhamentoTelaSuportado = ScreenShareManager.suportado;