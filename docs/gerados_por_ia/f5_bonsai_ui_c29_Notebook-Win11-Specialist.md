# Projeto MedIA - Interface de Sincronização e Conectividade ACS (C29)

## Estrutura do Projeto

```
media/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── sync.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── sync_status.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── sync_schemas.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── sync_service.py
│   │   ├── static/
│   │   │   └── sync_status.html
│   │   └── main.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_sync_schemas.py
│   │   ├── test_sync_models.py
│   │   ├── test_sync_service.py
│   │   └── test_sync_api.py
│   └── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Arquivo: `backend/app/static/sync_status.html`

```html:backend/app/static/sync_status.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sincronização ACS - Atenção Domicilar</title>
    <style>
        :root {
            --primary: #0056b3;
            --primary-dark: #003d80;
            --success: #008c3f;
            --warning: #d97706;
            --danger: #dc2626;
            --info: #1d4ed8;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --text-light: #64748b;
            --border: #e2e8f0;
            --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
            --shadow-lg: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
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
            box-shadow: var(--shadow-lg);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header h1 span {
            font-size: 1.2rem;
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

        .status-dot.danger {
            background: var(--danger);
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px 30px;
        }

        .controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 10px;
        }

        .search-bar {
            position: relative;
            flex: 1;
            min-width: 200px;
            max-width: 400px;
        }

        .search-bar input {
            width: 100%;
            padding: 10px 15px 10px 40px;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 0.95rem;
            transition: border-color 0.3s;
        }

        .search-bar input:focus {
            outline: none;
            border-color: var(--primary);
        }

        .search-bar .search-icon {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-light);
            font-size: 1.1rem;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 0.95rem;
            font-weight: 500;
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

        .btn-secondary {
            background: var(--card-bg);
            color: var(--text);
            border: 2px solid var(--border);
        }

        .btn-secondary:hover {
            border-color: var(--primary);
        }

        .btn-danger {
            background: var(--danger);
            color: white;
        }

        .btn-danger:hover {
            background: #b91c1c;
        }

        .btn-sm {
            padding: 6px 12px;
            font-size: 0.85rem;
        }

        .btn-icon {
            width: 36px;
            height: 36px;
            padding: 0;
            border-radius: 50%;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-title .icon {
            font-size: 1.3rem;
        }

        .card-title .icon.primary {
            color: var(--primary);
        }

        .card-title .icon.success {
            color: var(--success);
        }

        .card-title .icon.warning {
            color: var(--warning);
        }

        .card-title .icon.danger {
            color: var(--danger);
        }

        .card-title .icon.info {
            color: var(--info);
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
        }

        .metric-label {
            font-size: 0.9rem;
            color: var(--text-light);
        }

        .metric-value {
            font-size: 1.1rem;
            font-weight: 600;
        }

        .metric-value.primary {
            color: var(--primary);
        }

        .metric-value.success {
            color: var(--success);
        }

        .metric-value.warning {
            color: var(--warning);
        }

        .metric-value.danger {
            color: var(--danger);
        }

        .metric-value.info {
            color: var(--info);
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
            font-size: 0.85rem;
            color: var(--text-light);
        }

        .progress-percent {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--primary);
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: var(--border);
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }

        .progress-fill.primary {
            background: linear-gradient(90deg, var(--primary), var(--primary-dark));
        }

        .progress-fill.success {
            background: linear-gradient(90deg, var(--success), #166534);
        }

        .progress-fill.warning {
            background: linear-gradient(90deg, var(--warning), #b45309);
        }

        .progress-fill.danger {
            background: linear-gradient(90deg, var(--danger), #b91c1c);
        }

        .progress-fill.info {
            background: linear-gradient(90deg, var(--info), #0f172a);
        }

        .log-section {
            margin-top: 20px;
        }

        .log-list {
            list-style: none;
            max-height: 300px;
            overflow-y: auto;
        }

        .log-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 8px;
            transition: background 0.2s;
        }

        .log-item:hover {
            background: var(--bg);
        }

        .log-item.success {
            background: #dcfce7;
            border-left: 4px solid var(--success);
        }

        .log-item.warning {
            background: #fef3c7;
            border-left: 4px solid var(--warning);
        }

        .log-item.danger {
            background: #fee2e2;
            border-left: 4px solid var(--danger);
        }

        .log-item.info {
            background: #dbeafe;
            border-left: 4px solid var(--info);
        }

        .log-item.error {
            background: #fef2f2;
            border-left: 4px solid var(--danger);
        }

        .log-icon {
            font-size: 1.2rem;
            flex-shrink: 0;
            margin-top: 2px;
        }

        .log-content {
            flex: 1;
        }

        .log-title {
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .log-message {
            font-size: 0.85rem;
            color: var(--text-light);
            line-height: 1.4;
        }

        .log-meta {
            font-size: 0.75rem;
            color: var(--text-light);
            margin-top: 6px;
            display: flex;
            gap: 8px;
        }

        .log-meta span {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .badge {
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .badge-primary {
            background: #dbeafe;
            color: var(--primary);
        }

        .badge-success {
            background: #dcfce7;
            color: var(--success);
        }

        .badge-warning {
            background: #fef3c7;
            color: var(--warning);
        }

        .badge-danger {
            background: #fee2e2;
            color: var(--danger);
        }

        .badge-info {
            background: #dbeafe;
            color: var(--info);
        }

        .badge-error {
            background: #fef2f2;
            color: var(--danger);
        }

        .badge-cns {
            background: #f1f5f9;
            color: var(--text);
        }

        .badge-cpif {
            background: #f1f5f9;
            color: var(--text);
        }

        .badge-aps {
            background: #f1f5f9;
            color: var(--text);
        }

        .badge-aps-cit {
            background: #f1f5f9;
            color: var(--text);
        }

        .badge-aps-cit-10 {
            background: #f1f5f9;
            color: var(--text);
        }

        .badge-aps-cit-10-2 {
            background: #f1f5f9;
            color: var(--text);
        }

        .badge-aps-cit