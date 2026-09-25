```html:backend/app/static/monitor_sisab.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitoramento SISAB (C4) - Remessas</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary: #0056b3;
            --secondary: #003366;
            --success: #28a745;
            --warning: #ffc107;
            --danger: #dc3545;
            --light: #f8f9fa;
            --dark: #212529;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--light);
            color: var(--dark);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            background-color: var(--primary);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        header h1 {
            margin: 0;
            font-size: 24px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-card h3 {
            color: var(--primary);
            margin: 0;
            font-size: 18px;
        }
        .stat-card p {
            margin: 5px 0 0 0;
            color: #666;
        }
        .graph-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .graph-container h2 {
            color: var(--secondary);
            margin-top: 0;
        }
        .invoice-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .invoice-table th, .invoice-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .invoice-table th {
            background-color: var(--primary);
            color: white;
        }
        .invoice-table tr:hover {
            background-color: #f5f5f5;
        }
        .badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .badge-success {
            background-color: #d4edda;
            color: #155724;
        }
        .badge-warning {
            background-color: #fff3cd;
            color: #856404;
        }
        .badge-danger {
            background-color: #f8d7da;
            color: #721c24;
        }
        .action-buttons {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        button {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            transition: background-color 0.3s;
        }
        button:hover {
            opacity: 0.9;
        }
        button.retransmit {
            background-color: var(--danger);
            color: white;
        }
        button.retransmit:hover {
            background-color: #c82333;
        }
        button.refresh {
            background-color: var(--primary);
            color: white;
        }
        button.refresh:hover {
            background-color: #004494;
        }
        .status-bar {
            margin-top: 20px;
            padding: 10px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-size: 14px;
        }
        .status-bar .live {
            color: var(--success);
        }
        .status-bar .error {
            color: var(--danger);
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #666;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .filter-controls {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        select, input {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .error-message {
            background-color: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
            display: none;
        }
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px;
            border-radius: 8px;
            color: white;
            z-index: 1000;
            transform: translateX(150%);
            transition: transform 0.3s ease;
        }
        .notification.show {
            transform: translateX(0);
        }
        .notification.success {
            background-color: var(--success);
        }
        .notification.error {
            background-color: var(--danger);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Monitoramento SISAB (C4) - Remessas</h1>
            <p>Visualização em tempo real de fichas geradas e controle de retransmissão</p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <h3>Total Remessas</h3>
                <p id="totalRemessas">0</p>
            </div>
            <div class="stat-card">
                <h3>Em Processo</h3>
                <p id="emProcesso">0</p>
            </div>
            <div class="stat-card">
                <h3>Com Erro</h3>
                <p id="comErro">0</p>
            </div>
            <div class="stat-card">
                <h3>Último Atualizado</h3>
                <p id="lastUpdated">-</p>
            </div>
        </div>

        <div class="filter-controls">
            <select id="statusFilter">
                <option value="all">Todos os Estados</option>
                <option value="pending">Em Processo</option>
                <option value="completed">Concluídos</option>
                <option value="failed">Com Erro</option>
            </select>
            <select id="monthFilter">
                <option value="all">Todos os Mês</option>
                <option value="2024-01">Jan 2024</option>
                <option value="2024-02">Feb 2024</option>
                <option value="2024-03">Mar 2024</option>
                <option value="2024-04">Apr 2024</option>
                <option value="2024-05">May 2024</option>
                <option value="2024-06">Jun 2024</option>
                <option value="2024-07">Jul 2024</option>
                <option value="2024-08">Aug 2024</option>
                <option value="2024-09">Sep 2024</option>
                <option value="2024-10">Oct 2024</option>
                <option value="2024-11">Nov 2024</option>
                <option value="2024-12">Dec 2024</option>
            </select>
            <button class="refresh" onclick="refreshData()">🔄 Atualizar</button>
        </div>

        <div class="graph-container">
            <h2>Gráficos de Envios Mensais</h2>
            <canvas id="monthlyGraph"></canvas>
        </div>

        <div class="invoice-table">
            <table>
                <thead>
                    <tr>
                        <th>ID da Fatura</th>
                        <th>CNPJ/CNPJ</th>
                        <th>Valor</th>
                        <th>Estado</th>
                        <th>Data de Geração</th>
                        <th>Erro</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody id="invoiceTableBody">
                    <!-- Dados serão carregados aqui -->
                </tbody>
            </table>
        </div>

        <div class="error-message" id="errorMessage"></div>

        <div class="status-bar">
            <span class="live">● Sistema em tempo real - Atualização automática a cada 5 segundos</span>
        </div>
    </div>

    <div class="notification" id="notification"></div>

    <script>
        // Simulação de dados para demonstração
        const mockData = [
            { id: 'FAT-001', cnpj: '123456789000', value: 1500.00, status: 'completed', date: '2024-01-15', error: null, month: '2024-01' },
            { id: 'FAT-002', cnpj: '098765432100', value: 2300.50, status: 'pending', date: '2024-01-16', error: null, month: '2024-01' },
            { id: 'FAT-003', cnpj: '112233445566', value: 800.00, status: 'failed', date: '2024-01-17', error: 'Timeout na API', month: '2024-01' },
            { id: 'FAT-004', cnpj: '998877665544', value: 3200.00, status: 'completed', date: '2024-02-01', error: null, month: