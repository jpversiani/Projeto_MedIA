```python:backend/app/static/sync_status.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sincronização ACS - MedIA</title>
    <style>
        :root {
            --primary: #0056b3;
            --primary-dark: #003d82;
            --success: #2ecc71;
            --warning: #f39c12;
            --danger: #e74c3c;
            --info: #3498db;
            --bg: #f5f7fa;
            --card-bg: #ffffff;
            --text: #2c3e50;
            --text-light: #7f8c8d;
            --border: #ecf0f1;
            --shadow: 0 2px 8px rgba(0,0,0,0.1);
            --radius: 8px;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
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

        .header .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--success);
            animation: pulse 2s infinite;
        }

        .status-dot.warning {
            background: var(--warning);
        }

        .status-dot.error {
            background: var(--danger);
            animation: pulse-error 1s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        @keyframes pulse-error {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .stats-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: var(--card-bg);
            padding: 15px 20px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            text-align: center;
            border-left: 4px solid var(--primary);
        }

        .stat-card.warning {
            border-left-color: var(--warning);
        }

        .stat-card.error {
            border-left-color: var(--danger);
        }

        .stat-card.info {
            border-left-color: var(--info);
        }

        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: var(--primary);
        }

        .stat-label {
            font-size: 0.85rem;
            color: var(--text-light);
            margin-top: 4px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: var(--card-bg);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: hidden;
        }

        .card-header {
            padding: 15px 20px;
            background: var(--primary);
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-header h2 {
            font-size: 1.1rem;
            font-weight: 600;
        }

        .card-header .badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: bold;
        }

        .badge-success {
            background: rgba(46, 204, 113, 0.2);
            color: var(--success);
        }

        .badge-warning {
            background: rgba(243, 156, 18, 0.2);
            color: var(--warning);
        }

        .badge-error {
            background: rgba(231, 76, 60, 0.2);
            color: var(--danger);
        }

        .badge-info {
            background: rgba(52, 152, 219, 0.2);
            color: var(--info);
        }

        .card-body {
            padding: 20px;
        }

        .connection-status {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }

        .connection-icon {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }

        .connection-icon.connected {
            background: rgba(46, 204, 113, 0.1);
            color: var(--success);
        }

        .connection-icon.disconnected {
            background: rgba(231, 76, 60, 0.1);
            color: var(--danger);
        }

        .connection-icon.connecting {
            background: rgba(243, 156, 18, 0.1);
            color: var(--warning);
        }

        .connection-info {
            flex: 1;
        }

        .connection-info .label {
            font-size: 0.8rem;
            color: var(--text-light);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .connection-info .value {
            font-size: 1.1rem;
            font-weight: 600;
        }

        .connection-info .value.connected {
            color: var(--success);
        }

        .connection-info .value.disconnected {
            color: var(--danger);
        }

        .connection-info .value.connecting {
            color: var(--warning);
        }

        .connection-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 10px;
        }

        .detail-item {
            background: var(--bg);
            padding: 8px 12px;
            border-radius: 4px;
        }

        .detail-item .label {
            font-size: 0.7rem;
            color: var(--text-light);
            text-transform: uppercase;
        }

        .detail-item .value {
            font-size: 0.85rem;
            font-weight: 500;
        }

        .batch-progress {
            margin-bottom: 15px;
        }

        .batch-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 12px;
            background: var(--bg);
            border-radius: 4px;
            margin-bottom: 8px;
        }

        .batch-item .batch-number {
            font-weight: bold;
            color: var(--primary);
            min-width: 40px;
        }

        .batch-item .batch-info {
            flex: 1;
        }

        .batch-item .batch-name {
            font-size: 0.9rem;
            font-weight: 500;
        }

        .batch-item .batch-date {
            font-size: 0.75rem;
            color: var(--text-light);
        }

        .batch-item .batch-status {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: bold;
        }

        .batch-item .batch-status.completed {
            background: rgba(46, 204, 113, 0.1);
            color: var(--success);
        }

        .batch-item .batch-status.in-progress {
            background: rgba(243, 156, 18, 0.1);
            color: var(--warning);
        }

        .batch-item .batch-status.failed {
            background: rgba(231, 76, 60, 0.1);
            color: var(--danger);
        }

        .batch-item .batch-status.pending {
            background: rgba(52, 152, 219, 0.1);
            color: var(--info);
        }

        .progress-bar-container {
            width: 100%;
            height: 8px;
            background: var(--bg);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }

        .progress-bar {
            height: 100%;
            background: var(--primary);
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        .progress-bar.warning {
            background: var(--warning);
        }

        .progress-bar.error {
            background: var(--danger);
        }

        .progress-bar.success {
            background: var(--success);
        }

        .progress-info {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            margin-top: 4px;
        }

        .log-section {
            margin-top: 15px;
        }

        .log-section h3 {
            font-size: 0.9rem;
            color: var(--text-light);
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .log-entry {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 8px 12px;
            background: var(--bg);
            border-radius: 4px;
            margin-bottom: 6px;
            font-size: 0.8rem;
        }

        .log-entry .log-time {
            font-size: 0.7rem;
            color: var(--text-light);
            min-width: 80px;
            flex-shrink: 0;
        }

        .log-entry .log-icon {
            font-size: 1.2rem;
            flex-shrink: 0;
        }

        .log-entry .log-icon.success {
            color: var(--success);
        }

        .log-entry .log-icon.warning {
            color: var(--warning);
        }

        .log-entry .log-icon.error {
            color: var(--danger);
        }

        .log-entry .log-icon.info {
            color: var(--info);
        }

        .log-entry .log-message {
            flex: 1;
        }

        .log-entry .log-message .detail {
            display: block;
            font-size: 0.7rem;
            color: var(--text-light);
            margin-top: 2px;
        }

        .log-entry .log-message .detail.cns {
            color: var(--primary);
            font-weight: bold;
        }

        .log-entry .log-message .detail.cip {
            color: var(--info);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log-entry .log-message .detail.ipcid {
            color: var(--warning);
        }

        .log