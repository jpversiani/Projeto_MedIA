/**
 * CopilotoSidebar - Painel lateral do Copiloto para a tela do médico (home office).
 * 
 * Exibe alertas de risco/alergia, sugestões de exames complementares e dosagens usuais,
 * e permite preencher o SOAP com sugestão da IA.
 * 
 * Uso:
 *   const copiloto = new CopilotoSidebar({
 *     atendimentoId: 42,                       // obrigatório: identifica o atendimento
 *     pollingInterval: 30000,                  // ms
 *     targetSoapField: '#soap-textarea'        // seletor CSS do campo SOAP
 *   });
 *
 * NOTA SOBRE OS ENDPOINTS: os caminhos padrão usados aqui antes estavam errados
 * — faltava o prefixo `/v1` e o segmento `/atendimentos/{id}`, então toda
 * chamada retornava 404 e o painel nunca exibiu nada. Os caminhos reais estão
 * em `app/api/v1/copiloto.py` e conferem com a constante de versão da API.
 *
 * `examesUrl` ficou sem valor padrão: NÃO existe endpoint de exames no backend.
 * Deixá-lo configurável permite ligar quando o recurso for implementado, em vez
 * de disparar um fetch que sempre falha.
 */
const API_V1 = '/api/v1';

class CopilotoSidebar {
  /**
   * @param {Object} config - Configurações do widget.
   * @param {number|string} config.atendimentoId - ID do atendimento (obrigatório).
   * @param {string} [config.alertasUrl] - Sobrescreve o endpoint de alertas.
   * @param {string} [config.examesUrl] - Endpoint de exames. Sem padrão: não implementado no backend.
   * @param {string} [config.soapUrl] - Sobrescreve o endpoint de sugestão SOAP.
   * @param {number} [config.pollingInterval=30000] - Intervalo de atualização em ms.
   * @param {string} [config.targetSoapField='#soap-textarea'] - Seletor do campo SOAP.
   */
  constructor(config = {}) {
    const atendimentoId = config.atendimentoId;
    const base = atendimentoId != null ? `/atendimentos/${encodeURIComponent(atendimentoId)}` : '';

    this.config = {
      atendimentoId,
      alertasUrl: config.alertasUrl || `${API_V1}/copiloto${base}/alertas`,
      examesUrl: config.examesUrl || null,
      soapUrl: config.soapUrl || `${API_V1}/copiloto/ia/gerar-soap`,
      pollingInterval: config.pollingInterval || 30000,
      targetSoapField: config.targetSoapField || '#soap-textarea',
    };

    this.container = null;
    this.alertasList = null;
    this.examesList = null;
    this.soapButton = null;

    this._init();
  }

  /**
   * Inicializa o widget: cria o DOM, carrega dados e configura o polling.
   * @private
   */
  _init() {
    this._createDOM();
    this._attachEvents();
    this._loadAlertas();
    this._loadExames();

    // Atualização periódica
    setInterval(() => {
      this._loadAlertas();
      this._loadExames();
    }, this.config.pollingInterval);
  }

  /**
   * Cria a estrutura HTML do painel.
   * @private
   */
  _createDOM() {
    this.container = document.createElement('div');
    this.container.id = 'copiloto-sidebar';
    this.container.className = 'copiloto-sidebar';

    // Título
    const title = document.createElement('h2');
    title.textContent = 'Copiloto IA';
    this.container.appendChild(title);

    // Seção de alertas
    const alertasSection = document.createElement('div');
    alertasSection.className = 'copiloto-section';
    alertasSection.innerHTML = '<h3>Alertas de Risco/Alergia</h3>';
    this.alertasList = document.createElement('ul');
    this.alertasList.className = 'copiloto-alertas';
    alertasSection.appendChild(this.alertasList);
    this.container.appendChild(alertasSection);

    // Seção de exames
    const examesSection = document.createElement('div');
    examesSection.className = 'copiloto-section';
    examesSection.innerHTML = '<h3>Exames Complementares e Dosagens</h3>';
    this.examesList = document.createElement('ul');
    this.examesList.className = 'copiloto-exames';
    examesSection.appendChild(this.examesList);
    this.container.appendChild(examesSection);

    // Botão SOAP
    this.soapButton = document.createElement('button');
    this.soapButton.textContent = 'Preencher SOAP com Sugestão da IA';
    this.soapButton.className = 'copiloto-soap-btn';
    this.soapButton.disabled = false;
    this.container.appendChild(this.soapButton);

    // Adiciona ao DOM (assume que existe um elemento com id 'copiloto-container' ou cria no body)
    const parent = document.getElementById('copiloto-container') || document.body;
    parent.appendChild(this.container);
  }

  /**
   * Configura eventos do botão SOAP.
   * @private
   */
  _attachEvents() {
    this.soapButton.addEventListener('click', () => this._preencherSoap());
  }

  /**
   * Busca e exibe alertas de risco/alergia.
   * @private
   */
  async _loadAlertas() {
    try {
      const response = await fetch(this.config.alertasUrl);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const alertas = await response.json();

      // Limpa lista atual
      this.alertasList.innerHTML = '';

      if (!alertas || alertas.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'Nenhum alerta no momento.';
        li.className = 'sem-alerta';
        this.alertasList.appendChild(li);
        return;
      }

      alertas.forEach(alerta => {
        const li = document.createElement('li');
        li.className = 'alerta';
        li.textContent = `${alerta.tipo}: ${alerta.descricao}`;
        // Adiciona classe para animação piscante
        li.classList.add('piscante');
        this.alertasList.appendChild(li);
      });
    } catch (error) {
      console.error('Erro ao carregar alertas:', error);
      const li = document.createElement('li');
      li.textContent = 'Erro ao carregar alertas.';
      li.className = 'erro';
      this.alertasList.appendChild(li);
    }
  }

  /**
   * Busca e exibe sugestões de exames e dosagens.
   * @private
   */
  async _loadExames() {
    // Não existe endpoint de exames no backend. Sem `examesUrl` configurado,
    // mostramos o estado real em vez de disparar um fetch que sempre daria 404.
    if (!this.config.examesUrl) {
      this.examesList.innerHTML = '';
      const li = document.createElement('li');
      li.textContent = 'Sugestão de exames ainda não disponível.';
      li.className = 'sem-exame';
      this.examesList.appendChild(li);
      return;
    }

    try {
      const response = await fetch(this.config.examesUrl);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const exames = await response.json();

      this.examesList.innerHTML = '';

      if (!exames || exames.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'Nenhuma sugestão de exame no momento.';
        li.className = 'sem-exame';
        this.examesList.appendChild(li);
        return;
      }

      exames.forEach(exame => {
        const li = document.createElement('li');
        li.className = 'exame';
        // textContent em vez de innerHTML: `nome` e `dosagem` vêm da API e
        // interpolá-los em HTML é um sink de XSS.
        li.textContent = `${exame.nome} — ${exame.dosagem || 'dosagem não especificada'}`;
        this.examesList.appendChild(li);
      });
    } catch (error) {
      console.error('Erro ao carregar exames:', error);
      this.examesList.innerHTML = '';
      const li = document.createElement('li');
      li.textContent = 'Erro ao carregar exames.';
      li.className = 'erro';
      this.examesList.appendChild(li);
    }
  }

  /**
   * Solicita sugestão SOAP à IA e insere no campo de texto.
   * @private
   */
  async _preencherSoap() {
    this.soapButton.disabled = true;
    this.soapButton.textContent = 'Gerando sugestão...';

    try {
      const response = await fetch(this.config.soapUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Pode enviar dados do paciente se necessário, mas por simplicidade não enviamos nada
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const soapText = data.soap || data.texto || '';

      // Insere no campo SOAP
      const soapField = document.querySelector(this.config.targetSoapField);
      if (soapField) {
        soapField.value = soapText;
        // Dispara evento para que outros scripts possam reagir
        soapField.dispatchEvent(new Event('change', { bubbles: true }));
      } else {
        console.warn(`Campo SOAP não encontrado com seletor: ${this.config.targetSoapField}`);
        alert('Sugestão SOAP gerada, mas não foi possível inserir automaticamente. Copie o texto abaixo:\n\n' + soapText);
      }
    } catch (error) {
      console.error('Erro ao gerar sugestão SOAP:', error);
      alert('Erro ao gerar sugestão SOAP. Tente novamente.');
    } finally {
      this.soapButton.disabled = false;
      this.soapButton.textContent = 'Preencher SOAP com Sugestão da IA';
    }
  }
}

// Exporta para uso em módulos (se necessário)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CopilotoSidebar;
}
