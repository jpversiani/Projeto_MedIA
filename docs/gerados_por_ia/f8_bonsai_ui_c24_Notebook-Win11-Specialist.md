# Panel de Campanhas de Busca Ativa da Comunidade (C24)

## Arquivo: `backend/app/static/campanhas_saude.html`

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel de Campanhas de Busca Ativa da Comunidade (C24)</title>
    <meta name="description" content="Dashboard para Agents Comunitários de Saúde - Visitas Domiciliares e Teleatendimento">
    <style>
        :root {
            --primary: #0056b3;
            --primary-dark: #003d80;
            --accent: #28a745;
            --warning: #ffc107;
            --danger: #dc3545;
            --light: #f8f9fa;
            --dark: #212529;
            --border: #dee2e6;
            --shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--light);
            color: var(--dark);
            line-height: 1.6;
        }

        .header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow);
        }

        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
        }

        .header .subtitle {
            font-size: 0.85rem;
            opacity: 0.9;
            margin-top: 4px;
        }

        .header .stats {
            display: flex;
            gap: 20px;
        }

        .stat-card {
            background: rgba(255,255,255,0.2);
            padding: 10px 15px;
            border-radius: 8px;
            text-align: center;
            min-width: 80px;
        }

        .stat-card .value {
            font-size: 1.2rem;
            font-weight: bold;
        }

        .stat-card .label {
            font-size: 0.75rem;
            opacity: 0.9;
        }

        .container {
            max-width: 1400px;
            margin: 20px auto;
            padding: 0 20px;
        }

        .controls {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: var(--shadow);
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }

        .control-group {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        label {
            font-weight: 600;
            font-size: 0.9rem;
            color: var(--dark);
        }

        select, input[type="text"], input[type="date"] {
            padding: 8px 12px;
            border: 2px solid var(--border);
            border-radius: 6px;
            font-size: 0.9rem;
            background: white;
            color: var(--dark);
            transition: border-color 0.3s;
        }

        select:focus, input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(0,86,179,0.1);
        }

        .btn {
            padding: 8px 20px;
            border: none;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background: var(--primary);
            color: white;
        }

        .btn-primary:hover {
            background: var(--primary-dark);
        }

        .btn-success {
            background: var(--accent);
            color: white;
        }

        .btn-success:hover {
            background: #1e8449;
        }

        .btn-danger {
            background: var(--danger);
            color: white;
        }

        .btn-danger:hover {
            background: #c82333;
        }

        .btn-outline {
            background: transparent;
            border: 2px solid var(--border);
            color: var(--dark);
        }

        .btn-outline:hover {
            border-color: var(--primary);
            color: var(--primary);
        }

        .table-container {
            background: white;
            border-radius: 10px;
            box-shadow: var(--shadow);
            overflow: hidden;
            margin-bottom: 20px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        thead {
            background: var(--primary);
            color: white;
        }

        th {
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 0.5px;
        }

        td {
            padding: 12px 15px;
            border-bottom: 1px solid var(--border);
            font-size: 0.9rem;
        }

        tbody tr:hover {
            background: #f8f9fa;
        }

        .status-badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-active {
            background: #d4edda;
            color: #155724;
        }

        .status-completed {
            background: #cce5ff;
            color: #004085;
        }

        .status-pending {
            background: #fff3cd;
            color: #856404;
        }

        .status-cancelled {
            background: #f8d7da;
            color: #721c24;
        }

        .status-scheduled {
            background: #d1ecf1;
            color: #0c5460;
        }

        .patient-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .patient-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--primary);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1rem;
        }

        .patient-details {
            flex: 1;
        }

        .patient-name {
            font-weight: 600;
        }

        .patient-id {
            font-size: 0.8rem;
            color: #666;
        }

        .priority-high {
            color: var(--danger);
            font-weight: bold;
        }

        .priority-medium {
            color: var(--warning);
            font-weight: bold;
        }

        .priority-low {
            color: var(--accent);
            font-weight: bold;
        }

        .actions {
            display: flex;
            gap: 5px;
        }

        .actions .btn {
            padding: 4px 10px;
            font-size: 0.8rem;
        }

        .section-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 15px;
            color: var(--dark);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .section-title::before {
            content: '';
            display: inline-block;
            width: 4px;
            height: 20px;
            background: var(--primary);
            border-radius: 2px;
        }

        .tab-container {
            background: white;
            border-radius: 10px;
            box-shadow: var(--shadow);
            margin-bottom: 20px;
            overflow: hidden;
        }

        .tabs {
            display: flex;
            border-bottom: 2px solid var(--border);
        }

        .tab {
            padding: 12px 20px;
            border-bottom: 2px solid transparent;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.3s;
            position: relative;
        }

        .tab:hover {
            background: var(--light);
        }

        .tab.active {
            background: var(--primary);
            color: white;
            border-bottom-color: var(--primary);
        }

        .tab-content {
            padding: 20px;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }

        .empty-state .icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }

        .empty-state p {
            font-size: 1.1rem;
        }

        .empty-state .subtitle {
            font-size: 0.9rem;
            margin-top: 5px;
        }

        .filter-chips {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }

        .filter-chip {
            padding: 6px 14px;
            border-radius: 20px;
            border: 2px solid var(--border);
            background: white;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.3s;
        }

        .filter-chip:hover {
            border-color: var(--primary);
            color: var(--primary);
        }

        .filter-chip.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: var(--primary);
        }

        .loading .spinner {
            font-size: 2rem;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .notification {
            padding: 12px 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .notification-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .notification-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeeba;
        }

        .notification-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .print-btn {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
        }

        .print-btn:hover {
            transform: scale(1.05);
        }

        .responsive {
            display: none;
        }

        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }

            .controls {
                flex-direction: column;
            }

            .control-group {
                width: 100%;
            }

            .stats {
                justify-content: center;
            }

            .tab-container, .table-container {
                overflow-x: auto;
            }

            .print-btn {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>🏥 Panel de Campanhas de Busca Ativa da Comunidade (C24)</h1>
            <p class="subtitle">Sistema de Saúde Comunitária - SUS/APS</p>
        </div>
        <div class="stats">
            <div class="stat-card">
                <div class="value" id="totalVisits">0</div>
                <div class="label">Total</div>
            </div>
            <div class="stat-card">
                <div class="value" id="activeVisits">0</div>
                <div class="label">Ativas</div>
            </div>
            <div class="stat-card">
                <div class="value" id="completedVisits">0</div>
                <div class="label">Concluídas</div>
            </div>
            <div class="stat-card">
                <div class="value" id="activeTeleconsult">0</div>
                <div class="label">Teleconsultas</div>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="print-btn">
            <button class="btn btn-outline" onclick="window.print()" title="Imprimir">
               