```python
# Arquivo: backend/app/static/monitor_sisab.html
"""
Dashboard de Monitoramento de Remessas do SISAB (C12)
Visualização em tempo real de fichas geradas, gráficos de envios mensais
e botões de retransmissão de lotes com erro.
Conforme padrões SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF).
"""

<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor Sisab - Remessas C12</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
    <style>
        :root {
            --sisab-blue: #003366;
            --sisab-light: #005599;
            --sisab-accent: #e74c3c;
            --sisab-success: #2ecc71;
            --sisab-warning: #f39c12;
            --sisab-bg: #f8f9fa;
            --sisab-card: #ffffff;
            --sisab-text: #333333;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--sisab-bg);
            color: var(--sisab-text);
            min-height: 100vh;
        }

        .navbar {
            background: linear-gradient(135deg, var(--sisab-blue) 0%, var(--sisab-light) 100%);
            padding: 0.75rem 2rem;
            box-shadow: 0 2px 10px rgba(0, 51, 102, 0.3);
        }

        .navbar-brand {
            color: #fff;
            font-weight: 700;
            font-size: 1.4rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .navbar-brand .logo {
            font-size: 1.8rem;
        }

        .navbar-brand .subtitle {
            font-size: 0.85rem;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .navbar-brand .badge-c12 {
            background: var(--sisab-accent);
            color: #fff;
            font-size: 0.7rem;
            padding: 0.15rem 0.5rem;
            border-radius: 12px;
        }

        .navbar-text {
            color: #fff;
        }

        .navbar-text a {
            color: #fff;
            text-decoration: none;
            transition: opacity 0.3s;
        }

        .navbar-text a:hover {
            opacity: 0.8;
        }

        .navbar-text a.active {
            color: var(--sisab-accent);
            font-weight: 600;
        }

        .container-fluid {
            padding: 2rem;
        }

        .dashboard-header {
            background: var(--sisab-card);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .dashboard-header h1 {
            font-size: 1.5rem;
            color: var(--sisab-blue);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .dashboard-header h1 .icon {
            font-size: 1.8rem;
        }

        .dashboard-header .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--sisab-success);
            animation: pulse 2s infinite;
        }

        .status-dot.error {
            background: var(--sisab-accent);
            animation: pulse-error 1s infinite;
        }

        .status-dot.warning {
            background: var(--sisab-warning);
            animation: pulse-warning 1.5s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        @keyframes pulse-error {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        @keyframes pulse-warning {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .refresh-btn {
            background: var(--sisab-blue);
            color: #fff;
            border: none;
            padding: 0.5rem 1.25rem;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 500;
        }

        .refresh-btn:hover {
            background: var(--sisab-accent);
            transform: translateY(-1px);
        }

        .refresh-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }

        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .summary-card {
            background: var(--sisab-card);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
            transition: transform 0.3s, box-shadow 0.3s;
            position: relative;
            overflow: hidden;
        }

        .summary-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.12);
        }

        .summary-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
        }

        .summary-card.total::before { background: var(--sisab-blue); }
        .summary-card.success::before { background: var(--sisab-success); }
        .summary-card.error::before { background: var(--sisab-accent); }
        .summary-card.pending::before { background: var(--sisab-warning); }

        .summary-card .card-title {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #666;
            margin-bottom: 0.5rem;
        }

        .summary-card .card-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--sisab-blue);
        }

        .summary-card.total .card-value { color: var(--sisab-blue); }
        .summary-card.success .card-value { color: var(--sisab-success); }
        .summary-card.error .card-value { color: var(--sisab-accent); }
        .summary-card.pending .card-value { color: var(--sisab-warning); }

        .summary-card .card-change {
            font-size: 0.85rem;
            margin-top: 0.5rem;
            font-weight: 500;
        }

        .summary-card.total .card-change { color: var(--sisab-blue); }
        .summary-card.success .card-change { color: var(--sisab-success); }
        .summary-card.error .card-change { color: var(--sisab-accent); }
        .summary-card.pending .card-change { color: var(--sisab-warning); }

        .chart-container {
            background: var(--sisab-card);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
        }

        .chart-container h2 {
            font-size: 1.2rem;
            color: var(--sisab-blue);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .chart-container h2 .icon {
            font-size: 1.4rem;
        }

        .chart-wrapper {
            position: relative;
            height: 350px;
        }

        .table-container {
            background: var(--sisab-card);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
            margin-bottom: 2rem;
        }

        .table-container .table-header {
            background: var(--sisab-blue);
            color: #fff;
        }

        .table-container .table-body tr:hover {
            background: #f8f9fa;
        }

        .table-container .table-body tr.error-row {
            background: #fff5f5;
        }

        .table-container .table-body tr.error-row td {
            color: var(--sisab-accent);
        }

        .table-container .table-body tr.error-row td:first-child {
            background: #ffebee;
        }

        .table-container .table-body tr.error-row td:last-child {
            background: #ffebee;
        }

        .table-container .table-body tr.warning-row {
            background: #fff3cd;
        }

        .table-container .table-body tr.warning-row td:first-child {
            background: #fff3cd;
        }

        .table-container .table-body tr.warning-row td:last-child {
            background: #fff3cd;
        }

        .table-container .table-body tr.pending-row {
            background: #fff8e1;
        }

        .table-container .table-body tr.pending-row td:first-child {
            background: #fff8e1;
        }

        .table-container .table-body tr.pending-row td:last-child {
            background: #fff8e1;
        }

        .table-container .table-body tr.success-row {
            background: #e8f5e9;
        }

        .table-container .table-body tr.success-row td:first-child {
            background: #e8f5e9;
        }

        .table-container .table-body tr.success-row td:last-child {
            background: #e8f5e9;
        }

        .table-container .table-body th {
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #666;
        }

        .table-container .table-body td {
            font-size: 0.9rem;
            color: #333;
        }

        .table-container .table-body td.cns-cpf {
            font-weight: 600;
            color: var(--sisab-blue);
        }

        .table-container .table-body td.amount {
            font-weight: 600;
            color: var(--sisab-blue);
        }

        .table-container .table-body td.date {
            font-size: 0.85rem;
            color: #666;
        }

        .table-container .table-body td.status {
            font-size: 0.85rem;
            font-weight: 600;
        }

        .table-container .table-body td.batch {
            font-size: 0.85rem;
            color: #666;
        }

        .table-container .table-body td.method {
            font-size: 0.85rem;
            color: #666;
        }

        .table-container .table-body td.action {
            text-align: center;
        }

        .table-container .table-body td.action .btn {
            font-size: 0.8rem;
            padding: 0.25rem 0.75rem;
        }

        .table-container .table-body td.action .btn-retransmit {
            background: var(--sisab-accent);
            color: #fff;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s;
        }

        .table-container .table-body td.action .btn-retransmit:hover {
            background: #c0392b;
            transform: translateY(-1px);
        }

        .table-container .table-body td.action .btn-retransmit:disabled {
            background: #ccc;
            cursor: not-allowed;
        }

        .table-container .table-body td.action