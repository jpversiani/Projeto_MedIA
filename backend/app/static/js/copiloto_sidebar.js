/**
 * CopilotoSidebar - Painel lateral do Copiloto para a tela do médico (home office).
 * 
 * Exibe alertas de risco/alergia, sugestões de exames complementares e dosagens usuais,
 * e permite preencher o SOAP com sugestão da IA.
 * 
 * Uso:
 *   const copiloto = new CopilotoSidebar({
 *     alertasUrl: '/api/copiloto/alertas',
 *     examesUrl: '/api/copiloto/exames',
 *     soapUrl: '/api/copiloto/soap',
 *     pollingInterval: 30000, // ms
 *     targetSoapField: '#soap-textarea' // seletor CSS do campo SOAP
 *   });
 */
class CopilotoSidebar {
  /**
   * @param {Object} config - Configurações do widget.
   * @param {string} [config.alertasUrl='/api/copiloto/alertas'] - Endpoint para alertas.
   * @param {string} [config.examesUrl='/api/copiloto/exames'] - Endpoint para exames.
   * @param {string} [config.soapUrl='/api/copiloto/soap'] - Endpoint para sugestão SOAP.
   * @param {number} [config.pollingInterval=30000] - Intervalo de atualização em ms.
   * @param {string} [config.targetSoapField='#soap-textarea'] - Seletor do campo SOAP.
   */
  constructor(config = {}) {
    this.config = {
      alertasUrl: config.alertasUrl || '/api/copiloto/alertas',
      examesUrl: config.examesUrl || '/api/copiloto/exames',
      soapUrl: config.soapUrl || '/api/copiloto/soap',
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
        li.innerHTML = `<strong>${exame.nome}</strong> - ${exame.dosagem || 'Dosagem não especificada'}`;
        this.examesList.appendChild(li);
      });
    } catch (error) {
      console.error('Erro ao carregar exames:', error);
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
