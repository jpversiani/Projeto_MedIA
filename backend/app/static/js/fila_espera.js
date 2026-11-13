/**
 * Painel de Fila de Espera Virtual em Tempo Real — Projeto MedIA (SUS/APS).
 *
 * Consome o endpoint `GET /api/v1/fila/?status=AGUARDANDO_ATENDIMENTO`
 * (router com prefixo `/fila`, ver backend/app/api/v1/fila.py)
 * via polling adaptativo:
 *   - 2 s quando há pacientes aguardando;
 *   - 10 s quando a fila está ociosa (ou a aba está em segundo plano).
 *
 * Renderiza a lista ordenada pela prioridade Manchester
 * (VERMELHO > AMARELO > VERDE > AZUL, desempate por ordem de chegada),
 * exibe o tempo de espera decorrido de cada cidadão, mantém um selo
 * (badge) de "Chamando próximo" e oferece som opcional de chamada
 * sintetizado pela Web Audio API (sem arquivos externos).
 *
 * Exemplo de uso:
 *   <script type="module">
 *     import { FilaEsperaPainel } from "/static/js/fila_espera.js";
 *     const painel = new FilaEsperaPainel(); // IDs padrão de contêiner
 *     painel.iniciar();
 *   </script>
 */

/** Ordem de prioridade do Protocolo de Manchester (menor = mais urgente). */
const PRIORIDADE_MANCHESTER = Object.freeze({
  VERMELHO: 0,
  AMARELO: 1,
  VERDE: 2,
  AZUL: 3,
});

/** Paleta Tailwind CSS por classificação de risco. */
const CORES_RISCO = Object.freeze({
  VERMELHO: {
    badge: "bg-red-600 text-white",
    barra: "bg-red-600",
    fundo: "border-red-300 bg-red-50",
    texto: "text-red-700",
    /** Tempo máximo de espera recomendado (minutos) no protocolo Manchester. */
    esperaMaximaMinutos: 0,
    rotulo: "Emergência",
  },
  AMARELO: {
    badge: "bg-amber-500 text-white",
    barra: "bg-amber-500",
    fundo: "border-amber-300 bg-amber-50",
    texto: "text-amber-700",
    esperaMaximaMinutos: 15,
    rotulo: "Urgência",
  },
  VERDE: {
    badge: "bg-emerald-600 text-white",
    barra: "bg-emerald-600",
    fundo: "border-emerald-300 bg-emerald-50",
    texto: "text-emerald-700",
    esperaMaximaMinutos: 60,
    rotulo: "Pouco urgente",
  },
  AZUL: {
    badge: "bg-blue-600 text-white",
    barra: "bg-blue-600",
    fundo: "border-blue-300 bg-blue-50",
    texto: "text-blue-700",
    esperaMaximaMinutos: 120,
    rotulo: "Não urgente",
  },
});

export class FilaEsperaPainel {
  /**
   * @param {Object} [opcoes] Configurações do painel.
   * @param {string} [opcoes.urlApi] Endpoint da fila (padrão: cidadãos aguardando).
   * @param {number} [opcoes.intervaloAtivo] Polling com pacientes aguardando (ms).
   * @param {number} [opcoes.intervaloOcioso] Polling com fila vazia (ms).
   * @param {string} [opcoes.idLista] ID do elemento que recebe a lista.
   * @param {string} [opcoes.idContador] ID do elemento contador de espera.
   * @param {string} [opcoes.idChamada] ID do elemento do selo "Chamando próximo".
   * @param {string} [opcoes.idAtualizacao] ID do elemento "atualizado às".
   * @param {string} [opcoes.idBotaoSom] ID do botão que liga/desliga o som.
   * @param {boolean} [opcoes.somHabilitado] Estado inicial do som (padrão: falso).
   * @param {(proximo: Object|null) => void} [opcoes.aoChamar] Callback ao chamar próximo.
   */
  constructor(opcoes = {}) {
    this.#opcoes = {
      urlApi: "/api/v1/fila/?status=AGUARDANDO_ATENDIMENTO",
      intervaloAtivo: 2000,
      intervaloOcioso: 10000,
      idLista: "fila-espera-lista",
      idContador: "fila-espera-contador",
      idChamada: "fila-espera-chamada",
      idAtualizacao: "fila-espera-atualizacao",
      idBotaoSom: "fila-espera-som",
      somHabilitado: false,
      aoChamar: null,
      ...opcoes,
    };

    this.#elementoLista = document.getElementById(this.#opcoes.idLista);
    this.#elementoContador = document.getElementById(this.#opcoes.idContador);
    this.#elementoChamada = document.getElementById(this.#opcoes.idChamada);
    this.#elementoAtualizacao = document.getElementById(this.#opcoes.idAtualizacao);

    this.#filaOrdenada = [];
    this.#itemChamado = null;
    this.#timerPolling = null;
    this.#timerRelogio = null;
    this.#controladorBusca = null;
    this.#falhasConsecutivas = 0;
    this.#ultimoCarregamento = null;
    this.#audio = null;
    this.#ativo = false;
    this.somHabilitado = false;

    this.#prepararBotaoSom();
  }

  /** Inicia o polling adaptativo e o relógio de tempo de espera. */
  iniciar() {
    if (this.#ativo) return;
    this.#ativo = true;
    this.#timerRelogio = setInterval(() => this.#atualizarTemposDecorridos(), 1000);
    // Ao retornar à aba, retoma o ciclo ativo de imediato (sem aguardar o timer ocioso).
    this.#ouvinteVisibilidade = () => {
      if (this.#ativo && !document.hidden) this.#executarCiclo();
    };
    document.addEventListener("visibilitychange", this.#ouvinteVisibilidade);
    this.#executarCiclo();
  }

  /** Interrompe o painel (polling e relógio). */
  parar() {
    this.#ativo = false;
    document.removeEventListener("visibilitychange", this.#ouvinteVisibilidade);
    this.#ouvinteVisibilidade = null;
    if (this.#timerPolling) clearTimeout(this.#timerPolling);
    if (this.#timerRelogio) clearInterval(this.#timerRelogio);
    this.#timerPolling = null;
    this.#timerRelogio = null;
  }

  /** Encerra o painel e libera recursos de áudio. */
  destruir() {
    this.parar();
    this.#controladorBusca?.abort();
    this.#controladorBusca = null;
    this.#audio?.close().catch(() => {});
    this.#audio = null;
  }

  /**
   * Busca a fila na API, reordena por Manchester e re-renderiza.
   * Lança erro em falha de rede/HTTP para o ciclo de polling tratar.
   */
  async atualizar() {
    this.#controladorBusca?.abort();
    const controlador = new AbortController();
    this.#controladorBusca = controlador;

    try {
      const resposta = await fetch(this.#opcoes.urlApi, {
        signal: controlador.signal,
        headers: { Accept: "application/json" },
      });
      if (!resposta.ok) {
        throw new Error(`Falha ao consultar a fila (HTTP ${resposta.status}).`);
      }

      /** @type {Array<Object>} Itens de FilaAcolhimentoOut retornados pela API. */
      const itens = await resposta.json();
      this.#filaOrdenada = this.#ordenarPorPrioridade(itens);
      // Descarta a chamada ativa se o cidadão já não estiver mais na fila.
      if (this.#itemChamado && !this.#filaOrdenada.some((i) => i.id === this.#itemChamado.id)) {
        this.#itemChamado = null;
      }
      this.#ultimoCarregamento = new Date();
      this.#falhasConsecutivas = 0;

      this.#renderizarLista();
      this.#renderizarChamada();
    } finally {
      // Evita anular o controlador de uma busca mais recente em corrida.
      if (this.#controladorBusca === controlador) this.#controladorBusca = null;
    }
  }

  /**
   * Seleciona e anuncia o próximo cidadão (topo da fila ordenada).
   * @returns {Object|null} Item chamado ou nulo se a fila estiver vazia.
   */
  chamarProximo() {
    const proximo = this.#filaOrdenada[0] ?? null;
    this.#itemChamado = proximo;
    this.#renderizarChamada();
    if (proximo && this.somHabilitado) this.#tocarSomChamada();
    this.#opcoes.aoChamar?.(proximo);
    return proximo;
  }

  /**
   * Liga/desliga o som da chamada (gesto do usuário habilita o AudioContext).
   * @returns {boolean} Novo estado do som.
   */
  alternarSom() {
    this.somHabilitado = !this.somHabilitado;
    if (this.somHabilitado) {
      this.#audio ??= new (window.AudioContext ?? window.webkitAudioContext)();
      if (this.#audio.state === "suspended") this.#audio.resume().catch(() => {});
    }
    this.#refletirEstadoSom();
    return this.somHabilitado;
  }

  // ------------------------------------------------------------------ //
  // Estado interno                                                      //
  // ------------------------------------------------------------------ //

  #opcoes;
  #ativo;
  #elementoLista;
  #elementoContador;
  #elementoChamada;
  #elementoAtualizacao;
  #filaOrdenada;
  #itemChamado;
  #timerPolling;
  #timerRelogio;
  #ouvinteVisibilidade;
  #controladorBusca;
  #falhasConsecutivas;
  #ultimoCarregamento;
  #audio;

  /**
   * Ordena por prioridade Manchester e, no empate, por ordem de chegada.
   * @param {Array<Object>} itens Itens vindos da API.
   * @returns {Array<Object>} Itens ordenados.
   */
  #ordenarPorPrioridade(itens) {
    return [...(itens ?? [])].sort((a, b) => {
      const pA = PRIORIDADE_MANCHESTER[a.classificacao_risco] ?? 4;
      const pB = PRIORIDADE_MANCHESTER[b.classificacao_risco] ?? 4;
      if (pA !== pB) return pA - pB;
      return new Date(a.data_hora_entrada) - new Date(b.data_hora_entrada);
    });
  }

  /** Ciclo principal: busca, renderiza e agenda a próxima varredura. */
  async #executarCiclo() {
    // Cancela o timer pendente: este ciclo passa a ser o dono do agendamento.
    if (this.#timerPolling) clearTimeout(this.#timerPolling);
    this.#timerPolling = null;

    try {
      await this.atualizar();
    } catch (erro) {
      if (erro.name === "AbortError") return; // Suplantado por ciclo mais recente.
      this.#falhasConsecutivas += 1;
      console.error("[FilaEsperaPainel] Erro ao atualizar a fila:", erro);
      this.#renderizarErro();
    }

    if (!this.#ativo) return; // Painel parado durante a busca: não reagendar.

    const aguardando = this.#filaOrdenada.length > 0;
    const ocioso = !aguardando || document.hidden || this.#falhasConsecutivas > 0;
    let intervalo = ocioso ? this.#opcoes.intervaloOcioso : this.#opcoes.intervaloAtivo;
    // Recuo progressivo (backoff) em caso de falhas consecutivas de rede.
    if (this.#falhasConsecutivas > 0) {
      intervalo = Math.min(intervalo * (1 + this.#falhasConsecutivas), 30000);
    }

    this.#timerPolling = setTimeout(() => this.#executarCiclo(), intervalo);
  }

  // ------------------------------------------------------------------ //
  // Renderização                                                        //
  // ------------------------------------------------------------------ //

  /** Renderiza a lista de espera ordenada por prioridade. */
  #renderizarLista() {
    if (!this.#elementoLista) return;
    this.#elementoLista.replaceChildren();

    if (this.#elementoContador) {
      const aguardando = this.#filaOrdenada.length;
      this.#elementoContador.textContent = String(aguardando);
      this.#elementoContador.className =
        aguardando > 0
          ? "inline-flex items-center justify-center min-w-8 px-2 py-0.5 rounded-full text-sm font-bold bg-red-600 text-white animate-pulse"
          : "inline-flex items-center justify-center min-w-8 px-2 py-0.5 rounded-full text-sm font-bold bg-slate-300 text-slate-600";
    }

    if (this.#elementoAtualizacao && this.#ultimoCarregamento) {
      this.#elementoAtualizacao.textContent =
        `Atualizado às ${this.#formatarHora(this.#ultimoCarregamento)}`;
    }

    if (this.#filaOrdenada.length === 0) {
      const vazio = document.createElement("div");
      vazio.className = "px-5 py-10 text-center text-slate-400";
      vazio.textContent = "Nenhum cidadão aguardando na fila de espera no momento.";
      this.#elementoLista.append(vazio);
      return;
    }

    this.#filaOrdenada.forEach((item, indice) => {
      this.#elementoLista.append(this.#criarCartaoItem(item, indice));
    });
  }

  /**
   * Cria o cartão de um cidadão na fila (dados dinâmicos via textContent,
   * evitando injeção de HTML).
   * @param {Object} item Item de FilaAcolhimentoOut.
   * @param {number} indice Posição na fila já ordenada.
   * @returns {HTMLElement} Cartão renderizado.
   */
  #criarCartaoItem(item, indice) {
    const cor = CORES_RISCO[item.classificacao_risco] ?? CORES_RISCO.VERDE;
    const chamado = this.#itemChamado?.id === item.id;
    const cidadao = item.cidadao;

    const cartao = document.createElement("article");
    cartao.dataset.id = String(item.id);
    cartao.className = [
      "relative flex items-center gap-3 px-4 py-3 rounded-xl border-2 shadow-sm transition",
      chamado ? "ring-2 ring-offset-2 ring-blue-500" : "",
      cor.fundo,
    ].join(" ");

    // Barra lateral com a cor do risco.
    const barra = document.createElement("span");
    barra.className = `absolute left-0 top-0 bottom-0 w-1.5 rounded-l-xl ${cor.barra}`;
    cartao.append(barra);

    // Posição na fila + badge de classificação de risco (Manchester).
    const blocoRisco = document.createElement("div");
    blocoRisco.className = "flex flex-col items-center gap-1 min-w-20 shrink-0";

    const posicao = document.createElement("span");
    posicao.className = `text-xs font-bold ${cor.texto}`;
    posicao.textContent = `${indice + 1}º na fila`;
    blocoRisco.append(posicao);

    const badge = document.createElement("span");
    badge.className = `px-2.5 py-1 rounded text-[11px] font-bold uppercase tracking-wide ${cor.badge}`;
    badge.textContent = item.classificacao_risco;
    blocoRisco.append(badge);
    cartao.append(blocoRisco);

    // Identificação do cidadão (nome + CNS/CPF conforme padrão SUS).
    const blocoIdentificacao = document.createElement("div");
    blocoIdentificacao.className = "flex-1 min-w-0";

    const nome = document.createElement("div");
    nome.className = "font-semibold text-slate-800 truncate";
    nome.textContent = cidadao?.nome_completo ?? "Cidadão sem cadastro vinculado";
    blocoIdentificacao.append(nome);

    const motivo = document.createElement("div");
    motivo.className = "text-xs text-slate-500 truncate";
    motivo.textContent = item.motivo_acolhimento || "Sem queixa registrada no acolhimento";
    blocoIdentificacao.append(motivo);

    const documentos = document.createElement("div");
    documentos.className = "text-[11px] text-slate-400 font-mono";
    documentos.textContent = [
      cidadao?.cns ? `CNS: ${cidadao.cns}` : null,
      cidadao?.cpf ? `CPF: ${cidadao.cpf}` : null,
      item.tipo_demanda ? `Demanda: ${item.tipo_demanda}` : null,
    ]
      .filter(Boolean)
      .join("  •  ");
    blocoIdentificacao.append(documentos);
    cartao.append(blocoIdentificacao);

    // Tempo de espera decorrido (atualizado a cada segundo pelo relógio).
    const blocoEspera = document.createElement("div");
    blocoEspera.className = "shrink-0 text-right";

    const rotuloEspera = document.createElement("div");
    rotuloEspera.className = "text-[10px] uppercase tracking-wide text-slate-400";
    rotuloEspera.textContent = "Aguardando há";
    blocoEspera.append(rotuloEspera);

    const tempo = document.createElement("div");
    tempo.dataset.papel = "tempo-espera";
    tempo.dataset.entrada = String(new Date(item.data_hora_entrada).getTime());
    tempo.dataset.esperaMaxima = String(cor.esperaMaximaMinutos);
    tempo.dataset.risco = item.classificacao_risco;
    tempo.className = "font-mono text-sm font-bold text-slate-700";
    tempo.textContent = this.#formatarDuracao(Date.now() - Number(tempo.dataset.entrada));
    blocoEspera.append(tempo);

    const rotuloRisco = document.createElement("div");
    rotuloRisco.className = `text-[10px] ${cor.texto}`;
    rotuloRisco.textContent = cor.rotulo;
    blocoEspera.append(rotuloRisco);
    cartao.append(blocoEspera);

    return cartao;
  }

  /** Renderiza o selo de "Chamando próximo" (estado vazio ou chamada ativa). */
  #renderizarChamada() {
    if (!this.#elementoChamada) return;
    this.#elementoChamada.replaceChildren();

    const proximo = this.#itemChamado ?? this.#filaOrdenada[0] ?? null;
    if (!proximo) {
      this.#elementoChamada.className =
        "hidden items-center gap-3 px-4 py-2 rounded-xl bg-slate-100 border border-slate-200";
      return;
    }

    const cor = CORES_RISCO[proximo.classificacao_risco] ?? CORES_RISCO.VERDE;
    const cidadao = proximo.cidadao;

    this.#elementoChamada.className =
      "flex items-center gap-3 px-4 py-2 rounded-xl bg-white border shadow animate-pulse";

    const rotulo = document.createElement("span");
    rotulo.className = `px-2 py-0.5 rounded text-[11px] font-bold uppercase ${cor.badge}`;
    rotulo.textContent = "Chamando próximo";
    this.#elementoChamada.append(rotulo);

    const nome = document.createElement("span");
    nome.className = "font-semibold text-slate-800 truncate";
    nome.textContent = cidadao?.nome_completo ?? "Cidadão sem cadastro vinculado";
    this.#elementoChamada.append(nome);

    const risco = document.createElement("span");
    risco.className = `text-xs font-bold ${cor.texto}`;
    risco.textContent = proximo.classificacao_risco;
    this.#elementoChamada.append(risco);

    const botao = document.createElement("button");
    botao.type = "button";
    botao.className =
      "ml-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-lg text-xs font-semibold shadow-sm";
    botao.textContent = "Chamar de novo";
    botao.addEventListener("click", () => this.chamarProximo());
    this.#elementoChamada.append(botao);
  }

  /** Exibe aviso de falha de comunicação na lista (sem derrubar o painel). */
  #renderizarErro() {
    if (!this.#elementoLista || this.#filaOrdenada.length > 0) return;
    const aviso = document.createElement("div");
    aviso.className = "px-5 py-10 text-center text-sm text-amber-700 bg-amber-50 rounded-xl border border-amber-200";
    aviso.textContent =
      "Não foi possível atualizar a fila de espera. Nova tentativa em instantes...";
    this.#elementoLista.replaceChildren(aviso);
  }

  // ------------------------------------------------------------------ //
  // Relógio, tempos e formatação                                        //
  // ------------------------------------------------------------------ //

  /** Atualiza os tempos de espera decorridos a cada segundo, sem re-render total. */
  #atualizarTemposDecorridos() {
    const agora = Date.now();
    document.querySelectorAll("[data-papel='tempo-espera']").forEach((celula) => {
      const decorrido = agora - Number(celula.dataset.entrada);
      celula.textContent = this.#formatarDuracao(decorrido);

      // Alerta visual quando o tempo recomendado do Manchester é excedido.
      const limite = Number(celula.dataset.esperaMaxima) * 60000;
      if (limite > 0 && decorrido > limite) {
        celula.classList.add("text-red-600", "animate-pulse");
        celula.title = "Tempo máximo recomendado pela classificação de risco excedido!";
      } else {
        celula.classList.remove("text-red-600", "animate-pulse");
        celula.removeAttribute("title");
      }
    });
  }

  /**
   * Formata uma duração em forma legível (ex.: "45 s", "12 min", "1 h 05 min").
   * @param {number} milissegundos Duração decorrida.
   * @returns {string} Duração formatada.
   */
  #formatarDuracao(milissegundos) {
    if (!Number.isFinite(milissegundos) || milissegundos < 0) return "--";
    const segundos = Math.floor(milissegundos / 1000);
    if (segundos < 60) return `${segundos} s`;
    const minutos = Math.floor(segundos / 60);
    if (minutos < 60) return `${minutos} min`;
    const horas = Math.floor(minutos / 60);
    return `${horas} h ${String(minutos % 60).padStart(2, "0")} min`;
  }

  /**
   * Formata um instante como hora local curta (HH:MM:SS).
   * @param {Date} instante Instante a formatar.
   * @returns {string} Hora formatada.
   */
  #formatarHora(instante) {
    return instante.toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }

  // ------------------------------------------------------------------ //
  // Som (Web Audio API) e controles                                     //
  // ------------------------------------------------------------------ //

  /**
   * Emite um "ding-dong" de dois tons sintetizado pela Web Audio API.
   * Dois bipes servem de assinatura sonora da chamada de triagem.
   */
  #tocarSomChamada() {
    if (!this.#audio) return;
    const agora = this.#audio.currentTime;

    [[880, agora], [660, agora + 0.35]].forEach(([frequencia, inicio]) => {
      const oscilador = this.#audio.createOscillator();
      const ganho = this.#audio.createGain();

      oscilador.type = "sine";
      oscilador.frequency.setValueAtTime(frequencia, inicio);
      ganho.gain.setValueAtTime(0, inicio);
      ganho.gain.linearRampToValueAtTime(0.35, inicio + 0.03);
      ganho.gain.exponentialRampToValueAtTime(0.0001, inicio + 0.3);

      oscilador.connect(ganho).connect(this.#audio.destination);
      oscilador.start(inicio);
      oscilador.stop(inicio + 0.35);
    });
  }

  /** Vincula o botão de som (se existir) e reflete o estado inicial. */
  #prepararBotaoSom() {
    const botao = this.#opcoes.idBotaoSom
      ? document.getElementById(this.#opcoes.idBotaoSom)
      : null;
    botao?.addEventListener("click", () => this.alternarSom());
    this.#refletirEstadoSom();
  }

  /** Reflete o estado do som no botão de alternância. */
  #refletirEstadoSom() {
    const botao = this.#opcoes.idBotaoSom
      ? document.getElementById(this.#opcoes.idBotaoSom)
      : null;
    if (!botao) return;
    botao.textContent = this.somHabilitado ? "Som: ativado" : "Som: desativado";
    botao.className = this.somHabilitado
      ? "px-3 py-1 rounded-lg text-xs font-semibold bg-blue-600 text-white shadow-sm"
      : "px-3 py-1 rounded-lg text-xs font-semibold bg-slate-200 text-slate-600";
  }
}
