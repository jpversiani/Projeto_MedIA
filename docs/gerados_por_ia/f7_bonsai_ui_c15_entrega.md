# Dashboard Executivo Interativo para MedIA

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── dashboard.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── appointment.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── dashboard.py
│   ├── static/
│   │   ├── dashboard_analytics.html
│   │   ├── dashboard_analytics.css
│   │   └── dashboard_analytics.js
│   └── config.py
├── tests/
│   ├── __init__.py
│   └── test_dashboard.py
└── requirements.txt
```

---

## Arquivo: `backend/app/static/dashboard_analytics.html`

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Executivo - MedIA</title>
    <link rel="stylesheet" href="dashboard_analytics.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
    <script src="dashboard_analytics.js"></script>
</head>
<body>
    <div class="dashboard-container">
        <header class="dashboard-header">
            <div class="header-left">
                <h1>🏥 Dashboard Executivo - MedIA</h1>
                <p class="subtitle">Monitoramento em Tempo Real de Atividade Clinica</p>
            </div>
            <div class="header-right">
                <div class="date-selector">
                    <label for="dateRange">Período:</label>
                    <select id="dateRange">
                        <option value="7">Últimos 7 dias</option>
                        <option value="14" selected>Últimos 14 dias</option>
                        <option value="30">Últimos 30 dias</option>
                        <option value="90">Últimos 90 dias</option>
                    </select>
                </div>
                <button id="refreshBtn" class="btn-refresh">🔄 Atualizar</button>
            </div>
        </header>

        <main class="dashboard-main">
            <!-- KPI Cards -->
            <section class="kpi-section">
                <h2>📊 KPIs em Tempo Real</h2>
                <div class="kpi-grid">
                    <div class="kpi-card" data-kpi="totalPatients">
                        <div class="kpi-icon">👥</div>
                        <div class="kpi-label">Pacientes Atendidos</div>
                        <div class="kpi-value" id="kpi-totalPatients">0</div>
                        <div class="kpi-change" id="kpi-totalPatientsChange">+0%</div>
                    </div>
                    <div class="kpi-card" data-kpi="appointmentsCompleted">
                        <div class="kpi-icon">✅</div>
                        <div class="kpi-label">Apoentamentos Completados</div>
                        <div class="kpi-value" id="kpi-appointmentsCompleted">0</div>
                        <div class="kpi-change" id="kpi-appointmentsCompletedChange">+0%</div>
                    </div>
                    <div class="kpi-card" data-kpi="noShowRate">
                        <div class="kpi-icon">⚠️</div>
                        <div class="kpi-label">Taxa de No-Show</div>
                        <div class="kpi-value" id="kpi-noShowRate">0%</div>
                        <div class="kpi-change" id="kpi-noShowRateChange">+0%</div>
                    </div>
                    <div class="kpi-card" data-kpi="doctorAvailability">
                        <div class="kpi-icon">🩺</div>
                        <div class="kpi-label">Disponibilidade Médicos</div>
                        <div class="kpi-value" id="kpi-doctorAvailability">0%</div>
                        <div class="kpi-change" id="kpi-doctorAvailabilityChange">+0%</div>
                    </div>
                    <div class="kpi-card" data-kpi="avgWaitTime">
                        <div class="kpi-icon">⏱️</div>
                        <div class="kpi-label">Tempo de Espera Médio</div>
                        <div class="kpi-value" id="kpi-avgWaitTime">0 min</div>
                        <div class="kpi-change" id="kpi-avgWaitTimeChange">+0%</div>
                    </div>
                    <div class="kpi-card" data-kpi="suspensionRate">
                        <div class="kpi-icon">📉</div>
                        <div class="kpi-label">Taxa de Suspensão</div>
                        <div class="kpi-value" id="kpi-suspensionRate">0%</div>
                        <div class="kpi-change" id="kpi-suspensionRateChange">+0%</div>
                    </div>
                </div>
            </section>

            <!-- Heatmap Section -->
            <section class="heatmap-section">
                <h2>🔥 Heatmap de Horários de Pico</h2>
                <div class="heatmap-container">
                    <div class="heatmap-header">
                        <span class="heatmap-day">Seg</span>
                        <span class="heatmap-day">Seg</span>
                        <span class="heatmap-day">Seg</span>
                        <span class="heatmap-day">Qua</span>
                        <span class="heatmap-day">Qua</span>
                        <span class="heatmap-day">Fri</span>
                        <span class="heatmap-day">Sb</span>
                    </div>
                    <div class="heatmap-body" id="heatmapBody">
                        <!-- Heatmap cells generated by JS -->
                    </div>
                </div>
            </section>

            <!-- Line Graph Section -->
            <section class="graph-section">
                <h2>📈 Evolução dos Últimos 30 Dias</h2>
                <div class="graph-container">
                    <div class="graph-toolbar">
                        <select id="graphFilter">
                            <option value="all">Todos os Especialidades</option>
                            <option value="cardiology">Cardiologia</option>
                            <option value="neurology">Neurologia</option>
                            <option value="pediatrics">Pedatria</option>
                            <option value="orthopedics">Ortedropia</option>
                            <option value="general">Geral</option>
                        </select>
                        <select id="graphType">
                            <option value="line">Gráfico de Linha</option>
                            <option value="area">Gráfico de Área</option>
                        </select>
                    </div>
                    <div class="graph-wrapper">
                        <canvas id="lineChart"></canvas>
                    </div>
                </div>
            </section>

            <!-- Activity Feed -->
            <section class="activity-section">
                <h2>📋 Atividade Recente</h2>
                <div class="activity-feed" id="activityFeed">
                    <!-- Activity items generated by JS -->
                </div>
            </section>
        </main>

        <footer class="dashboard-footer">
            <div class="footer-info">
                <span>⏰ Atualizado: <span id="lastUpdated">-</span></span>
                <span>📍 MedIA - Sistema de Gestão Clinica</span>
            </div>
            <div class="footer-links">
                <a href="#">Sobre</a>
                <a href="#">Suporte</a>
                <a href="#">Privacidade</a>
            </div>
        </footer>
    </div>
</body>
</html>
```

---

## Arquivo: `backend/app/static/dashboard_analytics.css`

```css
/* Arquivo: backend/app/static/dashboard_analytics.css */

:root {
    --primary: #2563eb;
    --primary-dark: #1d4ed8;
    --primary-light: #dbeafe;
    --success: #10b981;
    --success-light: #d1fae5;
    --warning: #f59e0b;
    --warning-light: #fef3c7;
    --danger: #ef4444;
    --danger-light: #fee2e2;
    --info: #3b82f6;
    --info-light: #dbeafe;
    --gray-50: #f9fafb;
    --gray-100: #f3f4f6;
    --gray-200: #e5e7eb;
    --gray-300: #d1d5db;
    --gray-400: #9ca3af;
    --gray-500: #6b7280;
    --gray-600: #4b5563;
    --gray-700: #374151;
    --gray-800: #1f2937;
    --gray-900: #111827;
    --white: #ffffff;
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
    --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04);
    --radius-sm: 0.375rem;
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
    --radius-xl: 1rem;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--gray-50);
    color: var(--gray-800);
    line-height: 1.6;
    min-height: 100vh;
}

.dashboard-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

/* Header */
.dashboard-header {
    background: var(--white);
    padding: 20px 24px;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    border: 1px solid var(--gray-200);
}

.dashboard-header h1 {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--gray-900);
}

.subtitle {
    font-size: 0.875rem;
    color: var(--gray-500);
    margin-top: 4px;
}

.header-right {
    display: flex;
    align-items: center;
    gap: 16px;
}

.date-selector {
    display: flex;
    align-items: center;
    gap: 8px;
}

.date-selector label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--gray-600);
}

.date-selector select {
    padding: 8px 12px;
    border: 1px solid var(--gray-300);
    border-radius: var(--radius-sm);
    background: var(--white);
    font-size: 0.875rem;
    cursor: pointer;
    transition: var(--transition);
}

.date-selector select:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px var(--primary-light);
}

.btn-refresh {
    padding: 8px 16px;
    background: var(--primary);
    color: var(--white);
    border: none;
    border-radius: var(--radius-sm);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: var(--transition);
    display: flex;
    align-items: center;
    gap: 8px;
}

.btn-refresh:hover {
    background: var(--primary-dark);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

.btn-refresh:active {
    transform: translateY(0);
}

/* Main Content */
.dashboard-main {
    display: grid;
    grid-template-columns: 1fr;
    gap: 24px;
}

@media (min-width: 768px) {
    .dashboard-main {
        grid-template-columns: 1fr 1fr;
        grid-template-rows: auto 1fr;
    }
}

@media (min-width: 1024px) {
    .dashboard-main {
        grid-template-columns: 1fr 1fr 1fr;
        grid-template-rows: auto 1fr 1fr;
    }
}

/* KPI Cards */
.kpi-section {
    background: var(--white);
    padding: 24px;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    border: 1px solid var(--gray-200);
}

.kpi-section h2 {
    font-size: 1.25rem;
