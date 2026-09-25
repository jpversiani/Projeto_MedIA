```python:backend/app/static/sync_status.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sincronização ACS — Atenção Domicilar</title>
    <style>
        :root {
            --color-primary: #0056b3;
            --color-primary-light: #1a73e8;
            --color-success: #28a745;
            --color-warning: #ffc107;
            --color-danger: #dc3545;
            --color-info: #17a2b8;
            --color-bg: #f8f9fa;
            --color-card: #ffffff;
            --color-text: #212529;
            --color-text-light: #6c757d;
            --color-border: #dee2e6;
            --color-header: #0d47a1;
            --radius: 12px;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.12);
            --shadow-lg: 0 8px 30px rgba(0,0,0,0.15);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--color-bg);
            color: var(--color-text);
            min-height: 100vh;
            line-height: 1.6;
        }

        .page-header {
            background: linear-gradient(135deg, var(--color-header), var(--color-primary));
            color: white;
            padding: 24px 32px;
            box-shadow: var(--shadow-md);
        }

        .page-header h1 {
            font-size: 1.5rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .page-header h1 .icon {
            font-size: 1.8rem;
        }

        .page-header .subtitle {
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 4px;
        }

        .page-header .badge-cns {
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-family: monospace;
            font-weight: 600;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px;
        }

        .header-actions {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
            flex-wrap: wrap;
            gap: 12px;
        }

        .header-actions .search-bar {
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--color-card);
            border: 1px solid var(--color-border);
            border-radius: 50px;
            padding: 8px 16px;
        }

        .search-bar input {
            border: none;
            outline: none;
            padding: 8px 12px;
            font-size: 0.9rem;
            width: 200px;
        }

        .search-bar .icon {
            color: var(--color-text-light);
        }

        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .btn-primary {
            background: var(--color-primary);
            color: white;
        }

        .btn-primary:hover {
            background: var(--color-primary-light);
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: var(--color-card);
            color: var(--color-text);
            border: 1px solid var(--color-border);
        }

        .btn-secondary:hover {
            background: var(--color-bg);
        }

        .btn-danger {
            background: var(--color-danger);
            color: white;
        }

        .btn-danger:hover {
            background: #c82333;
        }

        .btn-success {
            background: var(--color-success);
            color: white;
        }

        .btn-success:hover {
            background: #1e8439;
        }

        .btn-sm {
            padding: 4px 10px;
            font-size: 0.75rem;
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }

        .status-card {
            background: var(--color-card);
            border-radius: var(--radius);
            padding: 20px;
            box-shadow: var(--shadow-sm);
            border-left: 4px solid var(--color-primary);
            transition: all 0.3s;
        }

        .status-card:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }

        .status-card.success {
            border-left-color: var(--color-success);
        }

        .status-card.warning {
            border-left-color: var(--color-warning);
        }

        .status-card.danger {
            border-left-color: var(--color-danger);
        }

        .status-card.info {
            border-left-color: var(--color-info);
        }

        .status-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .status-card-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--color-text);
        }

        .status-card-status {
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-card-status.success {
            background: rgba(40,167,69,0.1);
            color: var(--color-success);
        }

        .status-card-status.warning {
            background: rgba(255,193,7,0.1);
            color: #856404;
        }

        .status-card-status.danger {
            background: rgba(220,53,69,0.1);
            color: var(--color-danger);
        }

        .status-card-status.info {
            background: rgba(23,162,184,0.1);
            color: var(--color-info);
        }

        .status-card-body {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }

        .status-card-item {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .status-card-item .label {
            font-size: 0.75rem;
            color: var(--color-text-light);
            font-weight: 500;
        }

        .status-card-item .value {
            font-size: 0.9rem;
            font-weight: 600;
        }

        .status-card-item .value.cns {
            font-family: monospace;
            color: var(--color-primary);
        }

        .status-card-item .value.cpf {
            font-family: monospace;
            color: var(--color-primary);
        }

        .progress-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }

        .progress-card {
            background: var(--color-card);
            border-radius: var(--radius);
            padding: 20px;
            box-shadow: var(--shadow-sm);
        }

        .progress-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .progress-card-title {
            font-size: 0.95rem;
            font-weight: 600;
        }

        .progress-card-title .badge {
            background: var(--color-primary);
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 600;
        }

        .progress-card .progress-bar {
            width: 100%;
            height: 8px;
            background: var(--color-border);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 12px;
        }

        .progress-card .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }

        .progress-card .progress-fill.success { background: var(--color-success); }
        .progress-card .progress-fill.warning { background: var(--color-warning); }
        .progress-card .progress-fill.danger { background: var(--color-danger); }
        .progress-card .progress-fill.info { background: var(--color-info); }

        .progress-card .progress-info {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--color-text-light);
        }

        .progress-card .progress-info .value {
            color: var(--color-text);
            font-weight: 600;
        }

        .logs-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .log-card {
            background: var(--color-card);
            border-radius: var(--radius);
            padding: 20px;
            box-shadow: var(--shadow-sm);
        }

        .log-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }

        .log-card-title {
            font-size: 0.95rem;
            font-weight: 600;
        }

        .log-card-title .icon {
            font-size: 1.2rem;
            margin-right: 8px;
        }

        .log-entry {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 12px 0;
            border-bottom: 1px solid var(--color-border);
        }

        .log-entry:last-child {
            border-bottom: none;
        }

        .log-entry .log-icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
            flex-shrink: 0;
        }

        .log-entry .log-icon.success {
            background: rgba(40,167,69,0.1);
            color: var(--color-success);
        }

        .log-entry .log-icon.warning {
            background: rgba(255,193,7,0.1);
            color: #856404;
        }

        .log-entry .log-icon.danger {
            background: rgba(220,53,69,0.1);
            color: var(--color-danger);
        }

        .log-entry .log-icon.info {
            background: rgba(23,162,184,0.1);
            color: var(--color-info);
        }

        .log-entry .log-body {
            flex: 1;
        }

        .log-entry .log-time {
            font-size: 0.75rem;
            color: var(--color-text-light);
        }

        .log-entry .log-message {
            font-size: 0.85rem;
            margin-top: 2px;
        }

        .log-entry .log-message .detail {
            display: inline-block;
            background: var(--color-bg);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-family: monospace;
            color: var(--color-text-light);
            margin-left: 6px;
        }

        .log-entry .log-message .detail.cns {
            color: var(--color-primary);
        }

        .log-entry .log-message .detail.cpf {
            color: var(--color-primary);
        }

        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: var(--color-text-light);
        }

        .empty-state .icon {
            font-size: 2rem;
            margin-bottom: 12px;
        }

        .empty-state p {
            font-size: 0.9rem;
        }

        .empty-state a {
            color: var(--color-primary);
            text-decoration: none;
            font-weight: 600;
        }

        .empty-state a:hover {
            text-decoration: underline;
        }

        .refresh-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 12px;
        }

        .refresh-btn .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid var(--color-border);
            border-top-color: var(--color-primary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .toast {
            position: fixed;
            bottom