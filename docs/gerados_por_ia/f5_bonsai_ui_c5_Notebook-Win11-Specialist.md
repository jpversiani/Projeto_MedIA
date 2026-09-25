# Projeto MedIA - Interface de Sincronização e Conectividade ACS (C5)

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── schemas.py
│   ├── routes.py
│   ├── static/
│   │   └── sync_status.html
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       ├── test_schemas.py
│       ├── test_routes.py
│       └── test_sync.py
├── requirements.txt
└── pytest.ini
```

---

## Arquivo: `backend/app/static/sync_status.html`

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sincronização ACS - MedIA</title>
    <style>
        :root {
            --color-primary: #0056b3;
            --color-primary-dark: #003d80;
            --color-success: #28a745;
            --color-warning: #ffc107;
            --color-danger: #dc3545;
            --color-info: #17a2b8;
            --color-light: #f8f9fa;
            --color-dark: #212529;
            --color-border: #dee2e6;
            --color-card-bg: #ffffff;
            --radius: 8px;
            --shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--color-light);
            color: var(--color-dark);
            min-height: 100vh;
        }

        .header {
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
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
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header h1 .logo {
            font-size: 1.8rem;
        }

        .header .status-badge {
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .status-badge.connected {
            background: rgba(40, 167, 69, 0.3);
            color: var(--color-success);
        }

        .status-badge.disconnected {
            background: rgba(220, 53, 69, 0.3);
            color: var(--color-danger);
        }

        .status-badge.syncing {
            background: rgba(255, 193, 7, 0.3);
            color: #856404;
        }

        .status-badge .pulse {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .controls {
            display: flex;
            gap: 15px;
            margin: 20px 0;
            flex-wrap: wrap;
        }

        .btn {
            padding: 10px 24px;
            border: none;
            border-radius: var(--radius);
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 600;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background: var(--color-primary);
            color: white;
        }

        .btn-primary:hover {
            background: var(--color-primary-dark);
            transform: translateY(-1px);
        }

        .btn-success {
            background: var(--color-success);
            color: white;
        }

        .btn-success:hover {
            background: #218838;
        }

        .btn-warning {
            background: var(--color-warning);
            color: #856404;
        }

        .btn-danger {
            background: var(--color-danger);
            color: white;
        }

        .btn-danger:hover {
            background: #c82333;
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .btn-sm {
            padding: 6px 14px;
            font-size: 0.85rem;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: var(--color-card-bg);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }

        .card-header {
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--color-border);
        }

        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--color-dark);
        }

        .card-title .icon {
            margin-right: 8px;
        }

        .card-body {
            padding: 16px 20px;
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--color-border);
        }

        .metric-label {
            font-size: 0.9rem;
            color: #6c757d;
        }

        .metric-value {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--color-dark);
        }

        .metric-value.success { color: var(--color-success); }
        .metric-value.warning { color: #856404; }
        .metric-value.danger { color: var(--color-danger); }
        .metric-value.info { color: var(--color-info); }

        .progress-container {
            margin-top: 12px;
        }

        .progress-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
        }

        .progress-label {
            font-size: 0.85rem;
            color: #6c757d;
        }

        .progress-value {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--color-dark);
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

        .progress-fill.success { background: var(--color-success); }
        .progress-fill.warning { background: var(--color-warning); }
        .progress-fill.danger { background: var(--color-danger); }
        .progress-fill.info { background: var(--color-info); }

        .log-section {
            background: var(--color-card-bg);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: hidden;
        }

        .log-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--color-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .log-header .title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--color-dark);
        }

        .log-header .title .icon {
            margin-right: 8px;
        }

        .log-actions {
            display: flex;
            gap: 8px;
        }

        .log-entry {
            padding: 12px 20px;
            border-bottom: 1px solid var(--color-border);
            display: flex;
            align-items: flex-start;
            gap: 12px;
            transition: background 0.2s;
        }

        .log-entry:hover {
            background: var(--color-light);
        }

        .log-entry:last-child {
            border-bottom: none;
        }

        .log-icon {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            flex-shrink: 0;
        }

        .log-icon.success { background: rgba(40, 167, 69, 0.15); color: var(--color-success); }
        .log-icon.warning { background: rgba(255, 193, 7, 0.15); color: #856404; }
        .log-icon.danger { background: rgba(220, 53, 69, 0.15); color: var(--color-danger); }
        .log-icon.info { background: rgba(23, 162, 184, 0.15); color: var(--color-info); }
        .log-icon.error { background: rgba(139, 69, 19, 0.15); color: #8b4513; }

        .log-content {
            flex: 1;
        }

        .log-time {
            font-size: 0.75rem;
            color: #6c757d;
            margin-bottom: 2px;
        }

        .log-message {
            font-size: 0.9rem;
            color: var(--color-dark);
        }

        .log-status {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 10px;
            margin-top: 4px;
        }

        .log-status.success {
            background: rgba(40, 167, 69, 0.1);
            color: var(--color-success);
        }

        .log-status.warning {
            background: rgba(255, 193, 7, 0.1);
            color: #856404;
        }

        .log-status.danger {
            background: rgba(220, 53, 69, 0.1);
            color: var(--color-danger);
        }

        .log-status.info {
            background: rgba(23, 162, 184, 0.1);
            color: var(--color-info);
        }

        .log-status.error {
            background: rgba(139, 69, 19, 0.1);
            color: #8b4513;
        }

        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #6c757d;
        }

        .empty-state .icon {
            font-size: 3rem;
            margin-bottom: 10px;
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

        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .badge-success { background: rgba(40, 167, 69, 0.1); color: var(--color-success); }
        .badge-warning { background: rgba(255, 193, 7, 0.1); color: #856404; }
        .badge-danger { background: rgba(220, 53, 69, 0.1); color: var(--color-danger); }
        .badge-info { background: rgba(23, 162, 184, 0.1); color: var(--color-info); }

        .badge-cns {
            background: var(--color-primary);
            color: white;
            font-size: 0.8rem;
        }

        .badge-cpf {
            background: var(--color-success);
            color: white;
            font-size: 0.8rem;
        }

        .badge-aps {
            background: var(--color-warning);
            color: #856404;
            font-size: 0.8rem;
        }

        .badge-soap {
            background: var(--color-info);
            color: white;
            font-size: 0.8rem;
        }

        .badge-ciap2 {
            background: #6c757d;
            color: white;
            font-size: 0.8rem;
        }

        .badge-cid10 {
            background: #28a