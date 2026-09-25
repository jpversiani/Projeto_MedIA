# Interface de Sincronização e Conectividade ACS (C5)

## Arquivo: `backend/app/static/sync_status.html`

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sincronização ACS - Atenção Domicilar</title>
    <style>
        :root {
            --color-primary: #0056b3;
            --color-primary-dark: #003d80;
            --color-success: #28a745;
            --color-warning: #ffc107;
            --color-danger: #dc3545;
            --color-info: #17a2b8;
            --color-bg: #f8f9fa;
            --color-card: #ffffff;
            --color-text: #333;
            --color-text-light: #666;
            --color-border: #dee2e6;
            --color-accent: #0d6efd;
            --radius: 12px;
            --shadow: 0 2px 8px rgba(0,0,0,0.1);
            --shadow-hover: 0 4px 16px rgba(0,0,0,0.15);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--color-bg);
            color: var(--color-text);
            min-height: 100vh;
            padding: 20px;
        }

        .header {
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
            color: white;
            padding: 24px 32px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }

        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .header h1 .icon {
            font-size: 1.8rem;
        }

        .header .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 20px;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--color-success);
            animation: pulse 2s infinite;
        }

        .status-dot.warning {
            background: var(--color-warning);
            animation: pulse 1.5s infinite;
        }

        .status-dot.error {
            background: var(--color-danger);
            animation: pulse 1s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.8); }
        }

        .controls {
            display: flex;
            gap: 12px;
            margin-top: 16px;
            flex-wrap: wrap;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background: var(--color-accent);
            color: white;
        }

        .btn-primary:hover {
            background: #0b5ed7;
            transform: translateY(-1px);
            box-shadow: var(--shadow-hover);
        }

        .btn-secondary {
            background: var(--color-border);
            color: var(--color-text);
        }

        .btn-secondary:hover {
            background: #ced4da;
        }

        .btn-danger {
            background: var(--color-danger);
            color: white;
        }

        .btn-danger:hover {
            background: #c82333;
        }

        .btn-sm {
            padding: 6px 12px;
            font-size: 0.8rem;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }

        .card {
            background: var(--color-card);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            padding: 20px;
            transition: all 0.2s;
        }

        .card:hover {
            box-shadow: var(--shadow-hover);
            transform: translateY(-2px);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .card-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--color-text);
        }

        .card-badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .badge-connected {
            background: #d4edda;
            color: var(--color-success);
        }

        .badge-disconnected {
            background: #f8d7da;
            color: var(--color-danger);
        }

        .badge-syncing {
            background: #fff3cd;
            color: var(--color-warning);
        }

        .badge-error {
            background: #f8d7da;
            color: var(--color-danger);
        }

        .badge-processing {
            background: #d1ecf1;
            color: var(--color-info);
        }

        .badge-completed {
            background: #d4edda;
            color: var(--color-success);
        }

        .badge-pending {
            background: #e2e3e5;
            color: var(--color-text-light);
        }

        .badge-failed {
            background: #f8d7da;
            color: var(--color-danger);
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--color-border);
        }

        .metric-row:last-child {
            border-bottom: none;
        }

        .metric-label {
            font-size: 0.85rem;
            color: var(--color-text-light);
        }

        .metric-value {
            font-size: 1.1rem;
            font-weight: 600;
            font-variant-numeric: tabular-nums;
        }

        .metric-value.success {
            color: var(--color-success);
        }

        .metric-value.warning {
            color: var(--color-warning);
        }

        .metric-value.error {
            color: var(--color-danger);
        }

        .metric-value.info {
            color: var(--color-info);
        }

        .progress-container {
            margin-top: 16px;
        }

        .progress-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }

        .progress-label {
            font-size: 0.85rem;
            font-weight: 500;
        }

        .progress-percent {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--color-primary);
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: var(--color-border);
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }

        .progress-fill.success {
            background: var(--color-success);
        }

        .progress-fill.warning {
            background: var(--color-warning);
        }

        .progress-fill.error {
            background: var(--color-danger);
        }

        .progress-fill.info {
            background: var(--color-info);
        }

        .batch-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 8px;
            transition: background 0.2s;
        }

        .batch-item:hover {
            background: var(--color-bg);
        }

        .batch-item.completed {
            background: #d4edda;
        }

        .batch-item.failed {
            background: #f8d7da;
        }

        .batch-item.syncing {
            background: #fff3cd;
        }

        .batch-item.pending {
            background: #e2e3e5;
        }

        .batch-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            flex-shrink: 0;
        }

        .batch-icon.success {
            background: #d4edda;
            color: var(--color-success);
        }

        .batch-icon.failed {
            background: #f8d7da;
            color: var(--color-danger);
        }

        .batch-icon.syncing {
            background: #fff3cd;
            color: var(--color-warning);
        }

        .batch-icon.pending {
            background: #e2e3e5;
            color: var(--color-text-light);
        }

        .batch-info {
            flex: 1;
        }

        .batch-name {
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 2px;
        }

        .batch-detail {
            font-size: 0.8rem;
            color: var(--color-text-light);
        }

        .batch-status {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 12px;
            white-space: nowrap;
        }

        .batch-status.success {
            background: #d4edda;
            color: var(--color-success);
        }

        .batch-status.failed {
            background: #f8d7da;
            color: var(--color-danger);
        }

        .batch-status.syncing {
            background: #fff3cd;
            color: var(--color-warning);
        }

        .batch-status.pending {
            background: #e2e3e5;
            color: var(--color-text-light);
        }

        .batch-status.completed {
            background: #d4edda;
            color: var(--color-success);
        }

        .log-section {
            margin-top: 24px;
        }

        .log-section h2 {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .log-entry {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 0.85rem;
            line-height: 1.5;
            border-left: 4px solid;
        }

        .log-entry.success {
            background: #d4edda;
            border-color: var(--color-success);
        }

        .log-entry.failed {
            background: #f8d7da;
            border-color: var(--color-danger);
        }

        .log-entry.warning {
            background: #fff3cd;
            border-color: var(--color-warning);
        }

        .log-entry.info {
            background: #d1ecf1;
            border-color: var(--color-info);
        }

        .log-entry.error {
            background: #f8d7da;
            border-color: var(--color-danger);
        }

        .log-entry .log-time {
            font-size: 0.75rem;
            color: var(--color-text-light);
            margin-bottom: 4px;
        }

        .log-entry .log-level {
            font-weight: 600;
            margin-bottom: 4px;
        }

        .log-entry .log-level.success {
            color: var(--color-success);
        }

        .log-entry .log-level.failed {
            color: var(--color-danger);
        }

        .log-entry .log-level.warning {
            color: var(--color-warning);
        }

        .log-entry .log-level.info {
            color: var(--color-info);
        }

        .log-entry .log-level.error {
            color: var(--color-danger);
        }

        .log-entry .log-message {
            color: var(--color-text);
        }

        .log-entry .log-message code {
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.8rem;
            color: var(--color-primary);
        }

        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: var(--color-text-light);
        }

        .empty-state .icon {
            font-size: 3rem;
            margin-bottom: 12px;
        }

        .empty-state p {
            font-size: 0.