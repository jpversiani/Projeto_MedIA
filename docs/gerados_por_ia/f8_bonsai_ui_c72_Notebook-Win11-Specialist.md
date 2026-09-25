```html:backend/app/static/campanhas_saude.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard ACS - Campanhas Saude (C72)</title>
    <meta name="description" content="Visualização de visitas domiciliares e teleatendimento para Agentes Comunitários de Saúde.">
    
    <!-- 
    ARQUITETURA:
    - Frontend: HTML5, CSS3, Vanilla JS (Simulação de API)
    - Backend Contexto (Referencial): Python 3.12, Pydantic v2, SQLAlchemy 2.0
    - Padrões: SUS/APS, CIAP-2, CID-10, CNS/CPF
    - Padrão SOAP: Estrutura de dados para confirmação de teleatendimento
    -->
    <style>
        :root {
            --primary: #0056b3;
            --secondary: #003366;
            --accent: #e74c3c;
            --success: #27ae60;
            --bg: #f4f6f8;
            --text: #333;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--bg);
            color: var(--text);
        }

        .header {
            background-color: var(--secondary);
            color: white;
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }

        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            overflow: hidden;
        }

        .card-header {
            background-color: var(--primary);
            color: white;
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title {
            font-size: 1.2rem;
            font-weight: bold;
        }

        .badge {
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: bold;
        }

        .badge-prioridade {
            background-color: var(--accent);
            color: white;
        }

        .badge-tele {
            background-color: #3498db;
            color: white;
        }

        .badge-confirmado {
            background-color: var(--success);
            color: white;
        }

        .badge-pendiente {
            background-color: #f39c12;
            color: white;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }

        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }

        th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: var(--secondary);
        }

        tr:hover {
            background-color: #f1f1f1;
        }

        .patient-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background-color: var(--primary);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9rem;
        }

        .patient-details {
            flex: 1;
        }

        .patient-name {
            font-weight: bold;
        }

        .patient-id {
            font-size: 0.85rem;
            color: #666;
        }

        .status {
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }

        .status-prioridade { background-color: #ffeaea; color: var(--accent); }
        .status-tele { background-color: #e8f4f8; color: #3498db; }
        .status-confirmado { background-color: #e6ffe6; color: var(--success); }
        .status-pendente { background-color: #fff3e0; color: #f39c12; }

        .btn {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            transition: background-color 0.3s;
        }

        .btn-primary {
            background-color: var(--primary);
            color: white;
        }

        .btn-primary:hover {
            background-color: var(--secondary);
        }

        .btn-success {
            background-color: var(--success);
            color: white;
        }

        .btn-success:hover {
            background-color: #219a52;
        }

        .btn-warning {
            background-color: var(--accent);
            color: white;
        }

        .btn-warning:hover {
            background-color: #c0392b;
        }

        .btn-outline {
            border: 1px solid #ddd;
            background-color: white;
            color: var(--secondary);
        }

        .btn-outline:hover {
            background-color: #f0f0f0;
        }

        .grid-info {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .stat-card {
            background-color: var(--primary);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }

        .stat-number {
            font-size: 2rem;
            font-weight: bold;
        }

        .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }

        .filter-bar {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            align-items: center;
        }

        .filter-bar input {
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
        }

        .filter-bar select {
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
        }

        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }

        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
            }
            .header {
                flex-direction: column;
                gap: 1rem;
            }
        }
    </style>
</head>
<body>

    <header class="header">
        <div>
            <h1>🏥 Sistema MedIA - Dashboard ACS</h1>
            <p>Visualização de Campanhas Saude (C72) | Padrão SUS/APS</p>
        </div>
        <div>
            <span id="user-info">Agente: [CNPJ/CPF]</span>
            <span id="date-info">Data: <span id="current-date">2023-10-27</span></span>
        </div>
    </header>

    <div class="container">
        <!-- KPIs -->
        <div class="grid-info">
            <div class="stat-card">
                <div class="stat-number" id="total-visits">0</div>
                <div class="stat-label">Visitas Prioritárias</div>
            </div>
            <div class="stat-card" style="background-color: #3498db;">
                <div class="stat-number" id="total-tele">0</div>
                <div class="stat-label">Teleatendimento</div>
            </div>
            <div class="stat-card" style="background-color: #27ae60;">
                <div class="stat-number" id="total-confirmed">0</div>
                <div class="stat-label">Confirmados</div>
            </div>
        </div>

        <!-- Visits Section -->
        <div class="card">
            <div class="card-header">
                <div>
                    <div class="card-title">🏠 Visitas Domiciliares Prioritárias</div>
                    <div style="font-size: 0.8rem; color: #666;">Listagem por Prioridade (CNS/CPF)</div>
                </div>
                <div>
                    <button class="btn btn-primary" onclick="fetchVisits()">Carregar Dados</button>
                </div>
            </div>
            <div class="filter-bar">
                <input type="text" id="search-visits" placeholder="Buscar por Nome ou CNS..." oninput="filterVisits()">
                <select id="filter-visits-status">
                    <option value="all">Todos os Status</option>
                    <option value="prioridade">Prioridade</option>
                    <option value="pendente">Pendente</option>
                </select>
            </div>
            <div id="visits-container">
                <div class="loading">Carregando lista de visitas...</div>
            </div>
        </div>

        <!-- Telemedicine Section -->
        <div class="card">
            <div class="card-header">
                <div>
                    <div class="card-title">📡 Teleatendimento - Confirmações</div>
                    <div style="font-size: 0.8rem; color: #666;">Método SOAP / CIAP-2</div>
                </div>
                <div>
                    <button class="btn btn-primary" onclick="fetchTele()">Carregar Dados</button>
                </div>
            </div>
            <div class="filter-bar">
                <input type="text" id="search-tele" placeholder="Buscar por CPF..." oninput="filterTele()">
                <select id="filter-tele-status">
                    <option value="all">Todos os Status</option>
                    <option value="confirmado">Confirmado</option>
                    <option value="pendente">Pendente</option>
                </select>
            </div>
            <div id="tele-container">
                <div class="loading">Carregando lista de teleatendimento...</div>
            </div>
        </div>
    </div>

    <script>
        // Simulação de Backend (Pydantic v2 / SQLAlchemy 2.0)
        // Estrutura de Dados:
        // - Patient: { id, name, cns, cpf, gender, age, condition, priority }
        // - TeleAppointment: { id, patient_id, date, time, status, notes, soap_structure }

        const mockData = {
            visits: [
                {
                    id: 1,
                    name: "Maria Silva",
                    cns: "123456789",
                    cpf: "123.456.789-00",
                    gender: "F",
                    age: 65,
                    condition: "Hipertensão",
                    priority: "Alta",
                    status: "Prioridade",
                    notes: "Monitoramento de pressão arterial"
                },
                {
                    id: 2,
                    name: "João Oliveira",
                    cns: "987654321",
                    cpf