# Interface de Sincronização e Conectividade ACS (C21) - Projeto MedIA

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── static/
│   │   └── sync_status.html
│   ├── models/
│   │   ├── __init__.py
│   │   └── sync_status.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── sync_status.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── sync_service.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── sync_status.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_sync_status.py
│   └── test_sync_service.py
└── requirements.txt
```

---

## Arquivo: `backend/app/static/sync_status.html`

```html
<!-- Arquivo: backend/app/static/sync_status.html -->
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
            --radius: 12px;
            --shadow: 0 2px 8px rgba(0,0,0,0.1);
            --shadow-lg: 0 4px 16px rgba(0,0,0,0.15);
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

        .app-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background: var(--color-primary);
            color: white;
            padding: 20px 30px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
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

        .header-actions {
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.2s;
        }

        .btn-primary {
            background: var(--color-primary);
            color: white;
        }

        .btn-primary:hover {
            background: var(--color-primary-dark);
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
            color: var(--color-dark);
        }

        .btn-warning:hover {
            background: #e0a800;
        }

        .btn-danger {
            background: var(--color-danger);
            color: white;
        }

        .btn-danger:hover {
            background: #c82333;
        }

        .btn-info {
            background: var(--color-info);
            color: white;
        }

        .btn-info:hover {
            background: #0f8899;
        }

        .btn-outline {
            background: transparent;
            border: 2px solid var(--color-primary);
            color: var(--color-primary);
        }

        .btn-outline:hover {
            background: var(--color-primary);
            color: white;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: white;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .card-header {
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--color-border);
        }

        .card-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--color-dark);
        }

        .card-status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            animation: pulse 2s infinite;
        }

        .status-dot.offline {
            background: var(--color-danger);
        }

        .status-dot.connecting {
            background: var(--color-warning);
            animation: pulse 1s infinite;
        }

        .status-dot.online {
            background: var(--color-success);
        }

        .status-dot.syncing {
            background: var(--color-info);
            animation: pulse 1s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .card-body {
            padding: 20px;
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--color-border);
        }

        .stat-label {
            font-size: 0.85rem;
            color: #6c757d;
        }

        .stat-value {
            font-weight: 600;
            font-size: 0.95rem;
        }

        .stat-value.success {
            color: var(--color-success);
        }

        .stat-value.warning {
            color: var(--color-warning);
        }

        .stat-value.danger {
            color: var(--color-danger);
        }

        .stat-value.info {
            color: var(--color-info);
        }

        .stat-value.primary {
            color: var(--color-primary);
        }

        .progress-container {
            margin-top: 15px;
        }

        .progress-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }

        .progress-label {
            font-size: 0.8rem;
            color: #6c757d;
        }

        .progress-value {
            font-size: 0.8rem;
            font-weight: 600;
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

        .progress-fill.danger {
            background: var(--color-danger);
        }

        .progress-fill.info {
            background: var(--color-info);
        }

        .progress-fill.primary {
            background: var(--color-primary);
        }

        .log-section {
            margin-top: 20px;
        }

        .log-entry {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 10px 12px;
            margin-bottom: 8px;
            border-radius: 8px;
            background: var(--color-light);
        }

        .log-entry.error {
            background: #f8d7da;
            border-left: 3px solid var(--color-danger);
        }

        .log-entry.warning {
            background: #fff3cd;
            border-left: 3px solid var(--color-warning);
        }

        .log-entry.success {
            background: #d4edda;
            border-left: 3px solid var(--color-success);
        }

        .log-entry.info {
            background: #d1ecf1;
            border-left: 3px solid var(--color-info);
        }

        .log-entry.primary {
            background: #e7f3ff;
            border-left: 3px solid var(--color-primary);
        }

        .log-icon {
            font-size: 1.2rem;
            flex-shrink: 0;
        }

        .log-content {
            flex: 1;
        }

        .log-time {
            font-size: 0.75rem;
            color: #6c757d;
            margin-bottom: 2px;
        }

        .log-message {
            font-size: 0.85rem;
            line-height: 1.4;
        }

        .log-message strong {
            color: var(--color-dark);
        }

        .batch-info {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
            padding: 10px 12px;
            background: var(--color-light);
            border-radius: 8px;
        }

        .batch-icon {
            font-size: 1.2rem;
        }

        .batch-name {
            font-weight: 600;
            font-size: 0.9rem;
        }

        .batch-detail {
            font-size: 0.8rem;
            color: #6c757d;
        }

        .footer {
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.85rem;
        }

        .footer a {
            color: var(--color-primary);
            text-decoration: none;
        }

        .footer a:hover {
            text-decoration: underline;
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

        .empty-state .subtitle {
            font-size: 0.8rem;
            margin-top: 5px;
        }

        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.3);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid var(--color-border);
            border-top-color: var(--color-primary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .alert {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .alert-success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }

        .alert-warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }

        .alert-danger {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }

        .alert-info {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
        }

        .alert-icon {
            font-size: 1.2rem;
        }

        .alert-message {
            font-size: 0.9rem;
        }

        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .badge-ciap2 {
            background: #e7f3ff;
            color: var(--color-primary);
        }

        .badge-cid10 {
            background: #d4edda;
            color: var(--color-success);
        }

        .badge-soap {