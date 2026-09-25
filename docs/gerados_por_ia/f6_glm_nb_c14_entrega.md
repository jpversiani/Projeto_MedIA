```javascript
/**
 * Copiloto Sidebar - Widget para teleatendimento médico.
 *
 * Exibe em tempo real:
 * - Alertas piscantes de risco/alergia do paciente.
 * - Botão para preencher o SOAP com sugestão da IA.
 * - Sugestões de exames complementares com dosagens usuais do SUS.
 *
 * Arquitetura:
 * - Projeto MedIA (atendimento particular e convênios - TISS ANS 4.01 / DMED).
 * - Não envia dados obrigatórios ao SUS/SISAB.
 * - Não integra periféricos IoT.
 * - Código limpo, sem dependências externas (vanilla JS).
 *
 * Uso:
 *   <div id="copiloto-sidebar"></div>
 *   <script>
 *     window.CopilotoSidebarConfig = {
 *       apiBaseUrl: 'http://localhost:8000',
 *       patientId: '123',
 *       refreshInterval: 30000
 *     };
 *   </script>
 *   <script src="/static/js/copiloto_sidebar.js"></script>
 */
class CopilotoSidebar {
  /**
   * @param {Object} config
   * @param {string} config.apiBaseUrl - URL base da API.
   * @param {string} config.patientId - ID do paciente.
   * @param {string} [config.containerId='copiloto-sidebar'] - ID do elemento DOM.
   * @param {number} [config.refreshInterval=30000] - Intervalo de atualização (ms).
   */
  constructor({ apiBaseUrl, patientId, containerId = 'copiloto-sidebar', refreshInterval = 30000 }) {
    this.apiBaseUrl = apiBaseUrl;
    this.patientId = patientId;
    this.containerId = containerId;
    this.refreshInterval = refreshInterval;
    this.timer = null;
    this.container = null;
    this.soapSuggestion = null;
  }

  /**
   * Inicializa o widget: cria o layout e inicia o polling.
   */
  init() {
    this.container = document.getElementById(this.containerId);
    if (!this.container) {
      console.error(`Container #${this.containerId} não encontrado.`);
      return;
    }
    this.injectStyles();
    this.renderLayout();
    this.startPolling();
  }

  /**
   * Injeta estilos CSS necessários para o widget (incluindo animação de alerta).
   */
  injectStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .copiloto-sidebar {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 16px;
        max-width: 320px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      }
      .copiloto-sidebar h3 {
        margin-top: 0;
        color: #343a40;
        font-size: 1.2rem;
        border-bottom: 2px solid #0d6efd;
        padding-bottom: 8px;
      }
      .copiloto-sidebar h4 {
        margin: 16px 0 8px;
        color: #495057;
        font-size: 1rem;
      }
      .alert {
        padding: 10px 12px;
        border-radius: 4px;
        margin-bottom: 8px;
        font-weight: 500;
      }
      .alert-risk {
        background-color: #f8d7da;
        color: #842029;
        border: 1px solid #f5c2c7;
      }
      .alert-allergy {
        background-color: #fff3cd;
        color: #664d03;
        border: 1px solid #ffecb5;
      }
      .no-alerts, .no-exams {
        color: #6c757d;
        font-style: italic;
        padding: 8px 0;
      }
      .blink {
        animation: copiloto-blink 1s step-start infinite;
      }
      @keyframes copiloto-blink {
        50% { opacity: 0.4; }
      }
      #copiloto-soap-btn {
        width: 100%;
        padding: 10px;
        background-color: #0d6efd;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 0.95rem;
        cursor: pointer;
        transition: background-color 0.2s;
      }
      #copiloto-soap-btn:hover {
        background-color: #0b5ed7;
      }
      #copiloto-soap-btn:disabled {
        background-color: #6c757d;
        cursor: not-allowed;
      }
      .copiloto-sidebar ul {
        padding-left: 20px;
        margin: 8px 0;
      }
      .copiloto-sidebar li {
        margin-bottom: 6px;
        font-size: 0.9rem;
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Cria a estrutura HTML do widget.
   */
  renderLayout() {
    this.container.innerHTML = `
      <div class="copiloto-sidebar">
        <h3>Copiloto Clínico</h3>
        <div id="copiloto-alerts"></div>
        <button id="copiloto-soap-btn" disabled>Preencher SOAP com Sugestão da IA</button>
        <div id="copiloto-exams"></div>
      </div>
    `;
    document.getElementById('copiloto-soap-btn').addEventListener('click', () => this.handleSoapClick());
  }

  /**
   * Busca dados do paciente na API (riscos, alergias, sugestão SOAP, exames).
   */
  async fetchData() {
    try {
      const endpoints = [
        `${this.apiBaseUrl}/api/patient/${this.patientId}/risks`,
        `${this.apiBaseUrl}/api/patient/${this.patientId}/allergies`,
        `${this.apiBaseUrl}/api/patient/${this.patientId}/soap-suggestion`,
        `${this.apiBaseUrl}/api/patient/${this.patientId}/exam-suggestions`
      ];

      const responses = await Promise.all(endpoints.map(url => fetch(url)));
      const data = await Promise.all(responses.map(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      }));

      const [risks, allergies, soap, exams] = data;
      this.soapSuggestion = soap;
      this.renderAlerts(risks, allergies);
      this.renderExams(exams);
      this.updateSoapButtonState();
    } catch (error) {
      console.error('Erro ao buscar dados do copiloto:', error);
    }
  }

  /**
   * Renderiza alertas de risco e alergia com efeito piscante.
   * @param {Array} risks - Lista de riscos.
   * @param {Array} allergies - Lista de alergias.
   */
  renderAlerts(risks, allergies) {
    const alertsContainer = document.getElementById('copiloto-alerts');
    let html = '';

    if (risks && risks.length) {
      const descriptions = risks.map(r => r.description || r.name).join(', ');
      html += `<div class="alert alert-risk blink">⚠️ Riscos: ${descriptions}</div>`;
    }
    if (allergies && allergies.length) {
      const descriptions = allergies.map(a => a.description || a.name).join(', ');
      html += `<div class="alert alert-allergy blink">⚠️ Alergias: ${descriptions}</div>`;
    }

    alertsContainer.innerHTML = html || '<div class="no-alerts">Sem alertas de risco/alergia</div>';
  }

  /**
   * Renderiza sugestões de exames complementares com dosagens do SUS.
   * @param {Array} exams - Lista de exames sugeridos.
   */
 