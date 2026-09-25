/**
 * player_gravacao.js — Player de Revisão de Teleconsulta Gravada (Projeto MedIA — SUS/APS).
 *
 * Módulo ES que implementa a classe `PlayerTeleconsulta`, responsável por:
 *   1. Reproduzir a gravação de uma teleconsulta com controle de velocidade (0,5x a 2x);
 *   2. Inserir marcadores clínicos durante a revisão (ex.: 'exame físico', 'prescrição'),
 *      organizados segundo o método SOAP e com código opcional CIAP-2/CID-10;
 *   3. Exibir lista de marcadores clicáveis que saltam o vídeo para o instante marcado;
 *   4. Exportar o roteiro marcado em JSON (download e/ou callback `aoExportar`).
 *
 * Exemplo de uso:
 *   <div id="player-teleconsulta"></div>
 *   <script type="module">
 *     import { PlayerTeleconsulta } from '/static/js/player_gravacao.js';
 *     const player = new PlayerTeleconsulta('#player-teleconsulta', {
 *       fonte: '/media/teleconsultas/123/gravacao.mp4',
 *       metadados: {
 *         consultaId: 'tc-2026-000123',
 *         dataConsulta: '2026-09-25',
 *         unidade: 'UBS Jardim das Flores',
 *         paciente: { nome: 'Maria S.', cns: '700.0000.0000.008' },
 *         profissional: { nome: 'Dr. João P.', registro: 'CRM-SP 000000' },
 *       },
 *     });
 *   </script>
 *
 * Eventos CustomEvent disparados sobre o elemento raiz:
 *   'marcador-adicionado', 'marcador-removido', 'marcadores-limpos',
 *   'velocidade-alterada', 'roteiro-exportado'.
 */

'use strict';

/** Etapas do método SOAP (padrão de registro clínico adotado na APS). */
export const ETAPAS_SOAP = Object.freeze({
  S: 'S — Subjetivo',
  O: 'O — Objetivo',
  A: 'A — Avaliação',
  P: 'P — Plano',
});

/** Tipos de marcadores clínicos padrão, alinhados ao fluxo SUS/APS. */
export const TIPOS_MARCADOR_PADRAO = Object.freeze([
  { id: 'queixa-principal', rotulo: 'Queixa principal', etapaSoap: 'S' },
  { id: 'anamnese', rotulo: 'Anamnese', etapaSoap: 'S' },
  { id: 'exame-fisico', rotulo: 'Exame físico', etapaSoap: 'O' },
  { id: 'hipotese-diagnostica', rotulo: 'Hipótese diagnóstica', etapaSoap: 'A' },
  { id: 'conduta', rotulo: 'Conduta', etapaSoap: 'P' },
  { id: 'prescricao', rotulo: 'Prescrição', etapaSoap: 'P' },
  { id: 'encaminhamento', rotulo: 'Encaminhamento', etapaSoap: 'P' },
  { id: 'orientacao', rotulo: 'Orientação ao paciente', etapaSoap: 'P' },
]);

/** Velocidades de reprodução aceitas (faixa fixa de 0,5x a 2x). */
const VELOCIDADES = Object.freeze([0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]);

const VELOCIDADE_MINIMA = 0.5;
const VELOCIDADE_MAXIMA = 2;

/** Aviso de privacidade anexado à exportação (dados sensíveis — LGPD, Lei 13.709/2018). */
const AVISO_LGPD =
  'Roteiro contém dados pessoais sensíveis de saúde. Tratamento e compartilhamento sujeitos à LGPD (Lei nº 13.709/2018) e às normas do SUS.';

export class PlayerTeleconsulta {
  /**
   * Constrói o player dentro do elemento indicado.
   *
   * @param {HTMLElement|string} seletorOuElemento Seletor CSS ou elemento hospedeiro.
   * @param {object} [opcoes] Configurações opcionais.
   * @param {string|null} [opcoes.fonte] URL do vídeo da gravação.
   * @param {object} [opcoes.metadados] Dados da consulta (paciente, profissional, unidade...).
   * @param {Array<{id:string, rotulo:string, etapaSoap:'S'|'O'|'A'|'P'}>} [opcoes.tiposMarcadores]
   *     Tipos de marcadores disponíveis (por padrão, `TIPOS_MARCADOR_PADRAO`).
   * @param {number} [opcoes.velocidadeInicial=1] Velocidade inicial (0,5 a 2).
   * @param {string|null} [opcoes.chaveArmazenamento] Chave de persistência em localStorage.
   *     Padrão: `med-ia:marcadores:{consultaId}`.
   * @param {boolean} [opcoes.restaurarSessao=true] Restaura marcadores salvos ao iniciar.
   * @param {boolean} [opcoes.atalhosAtivos=true] Ativa atalhos de teclado.
   * @param {Function|null} [opcoes.aoExportar] Callback chamada com o roteiro (objeto) na exportação.
   */
  constructor(seletorOuElemento, opcoes = {}) {
    const hospedeiro =
      typeof seletorOuElemento === 'string'
        ? document.querySelector(seletorOuElemento)
        : seletorOuElemento;
    if (!(hospedeiro instanceof HTMLElement)) {
      throw new Error('PlayerTeleconsulta: elemento hospedeiro inválido ou não encontrado.');
    }

    this._hospedeiro = hospedeiro;
    this._opcoes = {
      fonte: opcoes.fonte ?? null,
      metadados: opcoes.metadados ?? {},
      tiposMarcadores: opcoes.tiposMarcadores ?? TIPOS_MARCADOR_PADRAO,
      velocidadeInicial: opcoes.velocidadeInicial ?? 1,
      chaveArmazenamento:
        opcoes.chaveArmazenamento ??
        `med-ia:marcadores:${opcoes.metadados?.consultaId ?? 'sem-id'}`,
      restaurarSessao: opcoes.restaurarSessao !== false,
      atalhosAtivos: opcoes.atalhosAtivos !== false,
      aoExportar: typeof opcoes.aoExportar === 'function' ? opcoes.aoExportar : null,
    };

    /** @type {Array<object>} Marcadores inseridos durante a revisão (ordenados por instante). */
    this._marcadores = [];
    /** @type {Map<string, {rotulo:string, etapaSoap:string}>} Mapa id -> definição do tipo. */
    this._tipos = new Map(this._opcoes.tiposMarcadores.map((t) => [t.id, t]));
    /** @type {number|null} Temporizador para limpeza automática da mensagem de status. */
    this._temporizadorMensagem = null;

    this._construirInterface();
    this._vincularEventos();
    this._restaurarSessaoSeHouver();
    this.definirVelocidade(this._opcoes.velocidadeInicial);
  }

  /* ------------------------------------------------------------------ */
  /* Construção da interface (HTML5 + Tailwind CSS)                      */
  /* ------------------------------------------------------------------ */

  /** Monta a estrutura visual do player no elemento hospedeiro. */
  _construirInterface() {
    this._hospedeiro.innerHTML = '';
    this._hospedeiro.classList.add(
      'w-full', 'max-w-5xl', 'mx-auto', 'bg-white', 'rounded-2xl', 'shadow-lg',
      'border', 'border-slate-200', 'p-4', 'sm:p-6', 'space-y-4', 'text-slate-800',
    );

    const cabecalho = this._criarCabecalho();
    const videoArea = this._criarAreaVideo();
    const controles = this._criarControles();
    const mensagem = this._criarMensagemStatus();
    const paineis = this._criarPaineis();

    this._hospedeiro.append(cabecalho, videoArea, controles, mensagem, paineis);
  }

  /** Cria o cabeçalho com título e metadados da consulta. */
  _criarCabecalho() {
    const m = this._opcoes.metadados;
    const secao = document.createElement('header');
    secao.className = 'space-y-1';

    const titulo = document.createElement('h2');
    titulo.className = 'text-lg sm:text-xl font-semibold text-slate-900';
    titulo.textContent = 'Revisão de Teleconsulta — Roteiro Marcado';

    const detalhes = document.createElement('p');
    detalhes.className = 'text-xs sm:text-sm text-slate-500';
    const partes = [
      m.dataConsulta && `Data: ${m.dataConsulta}`,
      m.unidade && `Unidade: ${m.unidade}`,
      m.profissional?.nome && `Profissional: ${m.profissional.nome}`,
      m.paciente?.nome &&
        `Paciente: ${m.paciente.nome}${m.paciente.cns ? ` (CNS ${m.paciente.cns})` : ''}`,
    ].filter(Boolean);
    detalhes.textContent = partes.join(' · ') || 'Gravação sem metadados cadastrados.';

    secao.append(titulo, detalhes);
    return secao;
  }

  /** Cria a área do vídeo com o elemento `<video>` HTML5. */
  _criarAreaVideo() {
    const area = document.createElement('div');
    area.className =
      'relative w-full rounded-xl overflow-hidden bg-slate-900 aspect-video';

    this._video = document.createElement('video');
    this._video.className = 'w-full h-full';
    this._video.preload = 'metadata';
    this._video.playsInline = true;
    this._video.setAttribute('aria-label', 'Vídeo da teleconsulta gravada');
    if (this._opcoes.fonte) {
      this._video.src = this._opcoes.fonte;
    }

    const aviso = document.createElement('p');
    aviso.className =
      'absolute inset-x-0 bottom-0 p-2 text-xs text-white/80 bg-slate-900/70';
    aviso.textContent =
      'Revisão assistida: marque os momentos clínicos relevantes durante a reprodução.';

    area.append(this._video, aviso);
    return area;
  }

  /** Cria os controles de reprodução: play/pause, buscar, velocidade e linha de tempo. */
  _criarControles() {
    const barra = document.createElement('div');
    barra.className = 'space-y-2';

    const linha = document.createElement('div');
    linha.className = 'flex flex-wrap items-center gap-2';

    this._botaoReproducao = document.createElement('button');
    this._configurarBotao(this._botaoReproducao, 'Reproduzir', 'toggle-reproducao', [
      'px-3', 'py-1.5', 'rounded-lg', 'bg-sky-600', 'text-white', 'font-medium',
      'hover:bg-sky-700', 'focus:outline-none', 'focus:ring-2', 'focus:ring-sky-400',
    ]);

    const botaoVoltar = document.createElement('button');
    this._configurarBotao(botaoVoltar, '−5 s', 'voltar-5s', ['px-3', 'py-1.5', 'rounded-lg', 'bg-slate-200', 'hover:bg-slate-300']);

    const botaoAvancar = document.createElement('button');
    this._configurarBotao(botaoAvancar, '+5 s', 'avancar-5s', ['px-3', 'py-1.5', 'rounded-lg', 'bg-slate-200', 'hover:bg-slate-300']);

    this._seletorVelocidade = document.createElement('select');
    this._seletorVelocidade.className =
      'px-2 py-1.5 rounded-lg border border-slate-300 bg-white text-sm';
    this._seletorVelocidade.setAttribute(
      'aria-label', 'Velocidade de reprodução (de 0,5x a 2x)',
    );
    for (const valor of VELOCIDADES) {
      const opcao = document.createElement('option');
      opcao.value = String(valor);
      opcao.textContent = `${String(valor).replace('.', ',')}×`;
      this._seletorVelocidade.append(opcao);
    }

    this._rotuloTempo = document.createElement('span');
    this._rotuloTempo.className =
      'ml-auto font-mono text-sm text-slate-600 tabular-nums';
    this._rotuloTempo.textContent = '00:00 / 00:00';

    linha.append(
      this._botaoReproducao, botaoVoltar, botaoAvancar,
      this._seletorVelocidade, this._rotuloTempo,
    );

    // Trilho visual dos marcadores + linha de tempo (input range).
    this._trilhoMarcadores = document.createElement('div');
    this._trilhoMarcadores.className = 'relative h-1.5 rounded bg-slate-300';

    this._linhaTempo = document.createElement('input');
    this._linhaTempo.type = 'range';
    this._linhaTempo.min = '0';
    this._linhaTempo.max = '0';
    this._linhaTempo.step = '0.1';
    this._linhaTempo.value = '0';
    this._linhaTempo.className = 'w-full accent-sky-600';
    this._linhaTempo.setAttribute('aria-label', 'Posição do vídeo');

    barra.append(linha, this._trilhoMarcadores, this._linhaTempo);
    return barra;
  }

  /** Cria a região de mensagens de status (acessível via aria-live). */
  _criarMensagemStatus() {
    this._mensagem = document.createElement('p');
    this._mensagem.className = 'text-sm text-slate-500 min-h-[1.25rem]';
    this._mensagem.setAttribute('aria-live', 'polite');
    this._mensagem.textContent = '';
    return this._mensagem;
  }

  /** Cria o painel de dois blocos: formulário de marcador e lista/exportação. */
  _criarPaineis() {
    const grade = document.createElement('div');
    grade.className = 'grid gap-4 md:grid-cols-2';

    grade.append(this._criarFormularioMarcador(), this._criarPainelLista());
    return grade;
  }

  /** Cria o formulário de inserção de marcador clínico. */
  _criarFormularioMarcador() {
    const formulario = document.createElement('section');
    formulario.className =
      'rounded-xl border border-slate-200 p-4 space-y-3 bg-slate-50';
    formulario.setAttribute('aria-label', 'Inserir marcador clínico');

    const titulo = document.createElement('h3');
    titulo.className = 'text-sm font-semibold text-slate-900';
    titulo.textContent = 'Inserir marcador clínico';
    formulario.append(titulo);

    const linhaTipos = document.createElement('div');
    linhaTipos.className = 'grid grid-cols-1 sm:grid-cols-2 gap-2';

    this._seletorTipo = document.createElement('select');
    this._seletorTipo.className = 'px-2 py-1.5 rounded-lg border border-slate-300 bg-white text-sm';
    this._seletorTipo.setAttribute('aria-label', 'Tipo de marcador clínico');
    for (const tipo of this._opcoes.tiposMarcadores) {
      const opcao = document.createElement('option');
      opcao.value = tipo.id;
      opcao.textContent = tipo.rotulo;
      this._seletorTipo.append(opcao);
    }

    this._campoCodigo = document.createElement('input');
    this._campoCodigo.type = 'text';
    this._campoCodigo.placeholder = 'Código CIAP-2/CID-10 (opcional)';
    this._campoCodigo.className = 'px-2 py-1.5 rounded-lg border border-slate-300 text-sm';
    this._campoCodigo.setAttribute('aria-label', 'Código CIAP-2 ou CID-10 (opcional)');

    linhaTipos.append(this._seletorTipo, this._campoCodigo);

    this._campoTitulo = document.createElement('input');
    this._campoTitulo.type = 'text';
    this._campoTitulo.placeholder = 'Título do marcador (opcional)';
    this._campoTitulo.className = 'w-full px-2 py-1.5 rounded-lg border border-slate-300 text-sm';
    this._campoTitulo.setAttribute('aria-label', 'Título do marcador');

    this._campoDescricao = document.createElement('textarea');
    this._campoDescricao.rows = 2;
    this._campoDescricao.placeholder = 'Anotação clínica da revisão (opcional)';
    this._campoDescricao.className =
      'w-full px-2 py-1.5 rounded-lg border border-slate-300 text-sm resize-y';
    this._campoDescricao.setAttribute('aria-label', 'Anotação clínica do marcador');

    this._botaoAdicionar = document.createElement('button');
    this._configurarBotao(this._botaoAdicionar, 'Adicionar marcador (M)', 'adicionar-marcador', [
      'w-full', 'py-2', 'rounded-lg', 'bg-emerald-600', 'text-white', 'font-medium',
      'hover:bg-emerald-700', 'focus:outline-none', 'focus:ring-2', 'focus:ring-emerald-400',
    ]);

    formulario.append(linhaTipos, this._campoTitulo, this._campoDescricao, this._botaoAdicionar);
    return formulario;
  }

  /** Cria o painel com a lista clicável de marcadores e o botão de exportação. */
  _criarPainelLista() {
    const painel = document.createElement('section');
    painel.className = 'rounded-xl border border-slate-200 p-4 space-y-3 bg-slate-50 flex flex-col';
    painel.setAttribute('aria-label', 'Marcadores da revisão');

    const titulo = document.createElement('h3');
    titulo.className = 'text-sm font-semibold text-slate-900';
    titulo.textContent = 'Marcadores registrados';

    this._listaMarcadores = document.createElement('ol');
    this._listaMarcadores.className = 'flex-1 space-y-2 overflow-y-auto max-h-72 text-sm';
    this._listaMarcadores.setAttribute('aria-label', 'Lista de marcadores clicáveis');

    this._rotuloVazio = document.createElement('li');
    this._rotuloVazio.className = 'text-slate-500 italic';
    this._rotuloVazio.textContent = 'Nenhum marcador registrado ainda.';
    this._listaMarcadores.append(this._rotuloVazio);

    this._botaoExportar = document.createElement('button');
    this._configurarBotao(this._botaoExportar, 'Exportar roteiro (JSON)', 'exportar-roteiro', [
      'w-full', 'py-2', 'rounded-lg', 'bg-indigo-600', 'text-white', 'font-medium',
      'hover:bg-indigo-700', 'focus:outline-none', 'focus:ring-2', 'focus:ring-indigo-400',
    ]);

    painel.append(titulo, this._listaMarcadores, this._botaoExportar);
    return painel;
  }

  /** Aplica rótulo, id de ação e classes utilitárias Tailwind a um botão. */
  _configurarBotao(botao, rotulo, acao, classes) {
    botao.type = 'button';
    botao.dataset.acao = acao;
    botao.textContent = rotulo;
    botao.className = `text-sm transition-colors ${classes.join(' ')}`;
  }

  /* ------------------------------------------------------------------ */
  /* Eventos                                                             */
  /* ------------------------------------------------------------------ */

  /** Registra os ouvintes de eventos do vídeo, da interface e do teclado. */
  _vincularEventos() {
    this._tratarCliqueInterface = (evento) => {
      const botao = evento.target.closest('[data-acao]');
      if (!botao) return;
      switch (botao.dataset.acao) {
        case 'toggle-reproducao': this.alternarReproducao(); break;
        case 'voltar-5s': this.irPara(this._video.currentTime - 5); break;
        case 'avancar-5s': this.irPara(this._video.currentTime + 5); break;
        case 'adicionar-marcador': this._adicionarMarcadorDoFormulario(); break;
        case 'exportar-roteiro': this.exportarRoteiro(); break;
      }
    };
    this._hospedeiro.addEventListener('click', this._tratarCliqueInterface);

    this._linhaTempo.addEventListener('input', () => {
      this._video.currentTime = Number(this._linhaTempo.value) || 0;
    });
    this._seletorVelocidade.addEventListener('change', () => {
      this.definirVelocidade(Number(this._seletorVelocidade.value));
    });

    this._aoTimeUpdate = () => {
      this._linhaTempo.value = String(this._video.currentTime);
      this._atualizarRotuloTempo();
    };
    this._video.addEventListener('timeupdate', this._aoTimeUpdate);

    this._aoCarregarMetadados = () => {
      this._linhaTempo.max = String(this._video.duration || 0);
      this._atualizarRotuloTempo();
      this._notificar('Gravação carregada — duração: ' + this._formatarTempo(this._video.duration));
    };
    this._video.addEventListener('loadedmetadata', this._aoCarregarMetadados);

    this._aoEncerrar = () => {
      this._botaoReproducao.textContent = 'Reproduzir';
      this._notificar('Reprodução encerrada.');
    };
    this._video.addEventListener('ended', this._aoEncerrar);

    this._aoErroCarregamento = () => {
      this._notificar('Falha ao carregar a gravação. Verifique o arquivo/fonte do vídeo.');
    };
    this._video.addEventListener('error', this._aoErroCarregamento);

    if (this._opcoes.atalhosAtivos) {
      this._tratarTeclado = (evento) => this._processarAtalhoTeclado(evento);
      document.addEventListener('keydown', this._tratarTeclado);
    }
  }

  /** Atalhos de teclado: Espaço (play/pause), M (marcador), ←/→ (±5 s). */
  _processarAtalhoTeclado(evento) {
    const alvo = evento.target;
    if (
      alvo instanceof HTMLInputElement || alvo instanceof HTMLSelectElement ||
      alvo instanceof HTMLTextAreaElement || alvo.isContentEditable
    ) {
      return;
    }
    switch (evento.key) {
      case ' ':
        evento.preventDefault();
        this.alternarReproducao();
        break;
      case 'm':
      case 'M':
        evento.preventDefault();
        this._adicionarMarcadorDoFormulario();
        break;
      case 'ArrowLeft':
        evento.preventDefault();
        this.irPara(this._video.currentTime - 5);
        break;
      case 'ArrowRight':
        evento.preventDefault();
        this.irPara(this._video.currentTime + 5);
        break;
    }
  }

  /* ------------------------------------------------------------------ */
  /* Controle de reprodução                                              */
  /* ------------------------------------------------------------------ */

  /** Alterna entre reprodução e pausa. */
  alternarReproducao() {
    if (this._video.paused) {
      this.reproduzir();
    } else {
      this.pausar();
    }
  }

  /** Inicia a reprodução da gravação. */
  reproduzir() {
    this._video.play()
      .then(() => {
        this._botaoReproducao.textContent = 'Pausar';
      })
      .catch(() => this._notificar('Não foi possível reproduzir o vídeo.'));
  }

  /** Pausa a reprodução da gravação. */
  pausar() {
    this._video.pause();
    this._botaoReproducao.textContent = 'Reproduzir';
  }

  /**
   * Define a velocidade de reprodução, limitada à faixa de 0,5x a 2x.
   * @param {number} valor Velocidade desejada.
   * @returns {number} Velocidade efetivamente aplicada.
   */
  definirVelocidade(valor) {
    const velocidade = Math.min(VELOCIDADE_MAXIMA, Math.max(VELOCIDADE_MINIMA, Number(valor) || 1));
    this._video.playbackRate = velocidade;
    if (this._seletorVelocidade.value !== String(velocidade)) {
      this._seletorVelocidade.value = String(velocidade);
    }
    this._dispararEvento('velocidade-alterada', { velocidade });
    return velocidade;
  }

  /**
   * Salta o vídeo para o instante informado (em segundos) e retoma a reprodução.
   * @param {number} segundos Instante alvo.
   */
  irPara(segundos) {
    const duracao = this._video.duration || Infinity;
    this._video.currentTime = Math.min(Math.max(0, Number(segundos) || 0), duracao);
    this.reproduzir();
  }

  /** Altera a fonte do vídeo dinamicamente.
   * @param {string} url URL da nova gravação.
   */
  definirFonte(url) {
    this._video.src = url;
    this._linhaTempo.value = '0';
  }

  /* ------------------------------------------------------------------ */
  /* Marcadores clínicos                                                 */
  /* ------------------------------------------------------------------ */

  /** Lê o formulário e registra um marcador no instante atual do vídeo. */
  _adicionarMarcadorDoFormulario() {
    const marcador = this.adicionarMarcador({
      tipo: this._seletorTipo.value,
      titulo: this._campoTitulo.value.trim(),
      descricao: this._campoDescricao.value.trim(),
      codigo: this._campoCodigo.value.trim(),
    });
    this._campoTitulo.value = '';
    this._campoDescricao.value = '';
    this._campoCodigo.value = '';
    this._campoTitulo.focus();
    return marcador;
  }

  /**
   * Registra um marcador clínico no instante atual do vídeo.
   * @param {object} [dados] Dados do marcador.
   * @param {string} [dados.tipo] Identificador do tipo (ex.: 'exame-fisico', 'prescricao').
   * @param {string} [dados.titulo=''] Título curto do marcador.
   * @param {string} [dados.descricao=''] Anotação clínica detalhada.
   * @param {string} [dados.codigo=''] Código CIAP-2 ou CID-10 associado.
   * @returns {object} Marcador criado.
   */
  adicionarMarcador({ tipo = 'conduta', titulo = '', descricao = '', codigo = '' } = {}) {
    const definicao = this._tipos.get(tipo) ?? this._tipos.get('conduta');
    const marcador = {
      id: this._gerarId(),
      instanteSegundos: Number(this._video.currentTime.toFixed(2)),
      tipo,
      tipoRotulo: definicao?.rotulo ?? tipo,
      etapaSoap: definicao?.etapaSoap ?? 'P',
      codigo,
      titulo,
      descricao,
      criadoEm: new Date().toISOString(),
    };

    this._marcadores.push(marcador);
    this._ordenarErenderizar();
    this._salvarSessao();
    this._notificar(`Marcador "${marcador.tipoRotulo}" registrado em ${this._formatarTempo(marcador.instanteSegundos)}.`);
    this._dispararEvento('marcador-adicionado', { marcador });
    return marcador;
  }

  /**
   * Remove um marcador pelo identificador.
   * @param {string} id Identificador do marcador.
   */
  removerMarcador(id) {
    const indice = this._marcadores.findIndex((m) => m.id === id);
    if (indice === -1) return;
    const [removido] = this._marcadores.splice(indice, 1);
    this._ordenarErenderizar();
    this._salvarSessao();
    this._notificar('Marcador removido.');
    this._dispararEvento('marcador-removido', { marcador: removido });
  }

  /** Remove todos os marcadores da sessão de revisão. */
  limparMarcadores() {
    this._marcadores = [];
    this._ordenarErenderizar();
    this._salvarSessao();
    this._notificar('Todos os marcadores foram removidos.');
    this._dispararEvento('marcadores-limpos', {});
  }

  /**
   * Retorna os marcadores ordenados pelo instante no vídeo.
   * @returns {Array<object>} Cópia da lista de marcadores.
   */
  obterMarcadores() {
    return [...this._marcadores].sort((a, b) => a.instanteSegundos - b.instanteSegundos);
  }

  /** Reordena os marcadores e redesenha a lista e a linha de tempo. */
  _ordenarErenderizar() {
    this._marcadores.sort((a, b) => a.instanteSegundos - b.instanteSegundos);
    this._renderizarLista();
    this._renderizarTrilho();
  }

  /** Desenha a lista clicável de marcadores (cada item salta o vídeo). */
  _renderizarLista() {
    this._listaMarcadores.innerHTML = '';

    if (this._marcadores.length === 0) {
      this._rotuloVazio = document.createElement('li');
      this._rotuloVazio.className = 'text-slate-500 italic';
      this._rotuloVazio.textContent = 'Nenhum marcador registrado ainda.';
      this._listaMarcadores.append(this._rotuloVazio);
      return;
    }

    this._marcadores.forEach((marcador, indice) => {
      const item = document.createElement('li');
      item.className =
        'rounded-lg bg-white border border-slate-200 p-2 cursor-pointer hover:border-sky-400 hover:ring-1 hover:ring-sky-300 focus:outline-none focus:ring-2 focus:ring-sky-400';
      item.tabIndex = 0;
      item.setAttribute('role', 'button');
      item.setAttribute(
        'aria-label',
        `Ir para ${this._formatarTempo(marcador.instanteSegundos)} — ${marcador.tipoRotulo}`,
      );
      item.dataset.id = marcador.id;

      const cabecalho = document.createElement('div');
      cabecalho.className = 'flex items-center gap-2';

      const tempo = document.createElement('span');
      tempo.className = 'font-mono text-xs text-sky-700 bg-sky-100 rounded px-1.5 py-0.5 tabular-nums';
      tempo.textContent = this._formatarTempo(marcador.instanteSegundos);

      const rotulo = document.createElement('span');
      rotulo.className = 'font-medium text-slate-800 flex-1 min-w-0 truncate';
      rotulo.textContent = `${indice + 1}. ${marcador.titulo || marcador.tipoRotulo}`;

      const chipSoap = document.createElement('span');
      chipSoap.className = 'text-[10px] font-semibold text-indigo-700 bg-indigo-100 rounded px-1.5 py-0.5 whitespace-nowrap';
      chipSoap.textContent = marcador.etapaSoap.split(' ')[0];

      const botaoRemover = document.createElement('button');
      botaoRemover.type = 'button';
      botaoRemover.textContent = 'Remover';
      botaoRemover.className =
        'text-xs text-rose-600 hover:text-rose-800 font-medium whitespace-nowrap';
      botaoRemover.setAttribute('aria-label', 'Remover marcador');

      cabecalho.append(tempo, rotulo, chipSoap, botaoRemover);

      const detalhes = [];
      if (marcador.codigo) detalhes.push(`Código: ${marcador.codigo}`);
      if (marcador.descricao) detalhes.push(marcador.descricao);
      const anotacao = document.createElement('p');
      anotacao.className = 'mt-1 text-xs text-slate-500';
      anotacao.textContent = detalhes.join(' — ') || marcador.tipoRotulo;

      item.append(cabecalho, anotacao);

      item.addEventListener('click', (evento) => {
        if (evento.target === botaoRemover) return;
        this.irPara(marcador.instanteSegundos);
      });
      item.addEventListener('keydown', (evento) => {
        if (evento.key === 'Enter' && evento.target !== botaoRemover) {
          evento.preventDefault();
          this.irPara(marcador.instanteSegundos);
        }
      });
      botaoRemover.addEventListener('click', (evento) => {
        evento.stopPropagation();
        this.removerMarcador(marcador.id);
      });

      this._listaMarcadores.append(item);
    });
  }

  /** Desenha os marcadores visuais sobre a linha de tempo do vídeo. */
  _renderizarTrilho() {
    this._trilhoMarcadores.innerHTML = '';
    const duracao = this._video.duration || 0;
    if (!duracao) return;
    for (const marcador of this._marcadores) {
      const marca = document.createElement('div');
      const percentual = Math.min(100, (marcador.instanteSegundos / duracao) * 100);
      marca.className = 'absolute top-0 h-full w-0.5 rounded bg-emerald-500 pointer-events-none';
      marca.style.left = `${percentual}%`;
      marca.title = `${marcador.tipoRotulo} em ${this._formatarTempo(marcador.instanteSegundos)}`;
      this._trilhoMarcadores.append(marca);
    }
  }

  /* ------------------------------------------------------------------ */
  /* Exportação do roteiro em JSON                                       */
  /* ------------------------------------------------------------------ */

  /**
   * Constrói o objeto de roteiro marcado com metadados e marcadores ordenados.
   * @returns {object} Roteiro pronto para serialização em JSON.
   */
  construirRoteiro() {
    const m = this._opcoes.metadados;
    return {
      formato: 'roteiro-marcado-teleconsulta',
      versao: '1.0',
      geradoEm: new Date().toISOString(),
      sistema: 'Projeto MedIA — SUS/APS',
      observacaoPrivacidade: AVISO_LGPD,
      consulta: {
        id: m.consultaId ?? null,
        data: m.dataConsulta ?? null,
        unidade: m.unidade ?? null,
        paciente: {
          nome: m.paciente?.nome ?? null,
          cns: m.paciente?.cns ?? null,
          cpf: m.paciente?.cpf ?? null,
        },
        profissional: {
          nome: m.profissional?.nome ?? null,
          registro: m.profissional?.registro ?? null,
        },
        fonteVideo: this._opcoes.fonte ?? this._video.currentSrc ?? null,
        duracaoVideoSegundos: Number((this._video.duration || 0).toFixed(2)),
      },
      marcadores: this.obterMarcadores().map((marcador, indice) => ({
        ordem: indice + 1,
        instanteSegundos: marcador.instanteSegundos,
        instante: this._formatarTempo(marcador.instanteSegundos),
        tipo: marcador.tipo,
        tipoRotulo: marcador.tipoRotulo,
        etapaSoap: marcador.etapaSoap,
        codigo: marcador.codigo || null,
        titulo: marcador.titulo || marcador.tipoRotulo,
        descricao: marcador.descricao || null,
        criadoEm: marcador.criadoEm,
      })),
    };
  }

  /**
   * Exporta o roteiro marcado: serializa em JSON, aciona download,
   * callback `aoExportar` e evento 'roteiro-exportado'.
   * @param {object} [opcoes] Opções de exportação.
   * @param {boolean} [opcoes.baixar=true] Se verdadeiro, dispara o download do arquivo.
   * @returns {object} Roteiro exportado.
   */
  exportarRoteiro({ baixar = true } = {}) {
    if (this._marcadores.length === 0) {
      this._notificar('Nenhum marcador para exportar. Registre marcadores antes de exportar.');
      return null;
    }
    const roteiro = this.construirRoteiro();
    if (baixar) this._baixarRoteiro(roteiro);
    this._opcoes.aoExportar?.(roteiro);
    this._dispararEvento('roteiro-exportado', { roteiro });
    this._notificar(`Roteiro exportado com ${roteiro.marcadores.length} marcador(es) em JSON.`);
    return roteiro;
  }

  /** Serializa o roteiro em JSON formatado.
   * @returns {string} Conteúdo JSON do roteiro.
   */
  serializarRoteiro() {
    return JSON.stringify(this.construirRoteiro(), null, 2);
  }

  /** Dispara o download do roteiro como arquivo `.json` nomeado pela consulta. */
  _baixarRoteiro(roteiro) {
    const blob = new Blob([JSON.stringify(roteiro, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = this._nomeArquivoExportacao();
    document.body.append(enlace);
    enlace.click();
    enlace.remove();
    URL.revokeObjectURL(url);
  }

  /** Gera o nome do arquivo de exportação, sanitize, com data curta. */
  _nomeArquivoExportacao() {
    const id = (this._opcoes.metadados?.consultaId ?? 'teleconsulta')
      .toString().toLowerCase().replace(/[^a-z0-9-]+/g, '-');
    const data = new Date().toISOString().slice(0, 10);
    return `roteiro-marcado-${id}-${data}.json`;
  }

  /* ------------------------------------------------------------------ */
  /* Persistência local (localStorage)                                   */
  /* ------------------------------------------------------------------ */

  /** Restaura marcadores salvos de uma sessão anterior de revisão, se houver. */
  _restaurarSessaoSeHouver() {
    if (!this._opcoes.restaurarSessao) return;
    try {
      const bruto = localStorage.getItem(this._opcoes.chaveArmazenamento);
      if (!bruto) return;
      const dados = JSON.parse(bruto);
      if (Array.isArray(dados.marcadores)) {
        this._marcadores = dados.marcadores.filter(
          (m) => m && Number.isFinite(m.instanteSegundos),
        );
        this._ordenarErenderizar();
        this._notificar(`Sessão restaurada: ${this._marcadores.length} marcador(es) recuperados.`);
      }
    } catch (erro) {
      console.warn('PlayerTeleconsulta: falha ao restaurar sessão anterior.', erro);
    }
  }

  /** Salva marcadores e velocidade na persistência local, quando disponível. */
  _salvarSessao() {
    try {
      localStorage.setItem(
        this._opcoes.chaveArmazenamento,
        JSON.stringify({
          marcadores: this._marcadores,
          velocidade: this._video.playbackRate,
        }),
      );
    } catch (erro) {
      console.warn('PlayerTeleconsulta: falha ao salvar a sessão localmente.', erro);
    }
  }

  /* ------------------------------------------------------------------ */
  /* Utilidades internas                                                 */
  /* ------------------------------------------------------------------ */

  /** Atualiza o rótulo de tempo "atual / duração" exibido nos controles. */
  _atualizarRotuloTempo() {
    const atual = this._formatarTempo(this._video.currentTime);
    const duracao = this._formatarTempo(this._video.duration || 0);
    this._rotuloTempo.textContent = `${atual} / ${duracao}`;
  }

  /** Formata segundos em mm:ss (ou h:mm:ss para gravações longas). */
  _formatarTempo(segundos) {
    if (!Number.isFinite(segundos) || segundos < 0) segundos = 0;
    const total = Math.floor(segundos);
    const horas = Math.floor(total / 3600);
    const minutos = Math.floor((total % 3600) / 60);
    const segundoss = String(total % 60).padStart(2, '0');
    if (horas > 0) {
      const mm = String(minutos).padStart(2, '0');
      return `${horas}:${mm}:${segundoss}`;
    }
    return `${String(minutos).padStart(2, '0')}:${segundoss}`;
  }

  /** Exibe mensagem de status acessível, limpa automaticamente após 4 s. */
  _notificar(texto) {
    this._mensagem.textContent = texto;
    clearTimeout(this._temporizadorMensagem);
    this._temporizadorMensagem = setTimeout(() => {
      this._mensagem.textContent = '';
    }, 4000);
  }

  /** Dispara um CustomEvent sobre o elemento hospedeiro.
   * @param {string} nome Nome do evento.
   * @param {object} detalhe Dados anexados ao evento.
   */
  _dispararEvento(nome, detalhe) {
    this._hospedeiro.dispatchEvent(new CustomEvent(nome, { detail: detalhe, bubbles: true }));
  }

  /** Gera identificador único para marcadores. */
  _gerarId() {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID();
    }
    return `marcador-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  /** Remove ouvintes e limpa a interface do player (uso ao desmontar a página). */
  destruir() {
    clearTimeout(this._temporizadorMensagem);
    if (this._opcoes.atalhosAtivos && this._tratarTeclado) {
      document.removeEventListener('keydown', this._tratarTeclado);
    }
    this._hospedeiro.replaceChildren();
  }
}

export default PlayerTeleconsulta;