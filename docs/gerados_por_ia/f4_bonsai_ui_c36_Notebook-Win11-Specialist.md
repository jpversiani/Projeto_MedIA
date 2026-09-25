# Dashboard de Monitoramento de Remessas do SISAB (C36)

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── static/
│   │   └── monitor_sisab.html
│   ├── api/
│   │   ├── __init__.py
│   │   └── sisab.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── sisab.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── sisab.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── sisab.py
│   └── config.py
├── tests/
│   ├── __init__.py
│   └── test_sisab.py
└── requirements.txt
```

---

## `backend/app/static/monitor_sisab.html`

```html:backend/app/static/monitor_sisab.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor SISAB - C36 - Remessas</title>
    <link href="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {
            --color-primary: #0056b3;
            --color-secondary: #003d80;
            --color-success: #28a745;
            --color-danger: #dc3545;
            --color-warning: #ffc107;
            --color-info: #17a2b8;
            --color-light: #f8f9fa;
            --color-dark: #212529;
        }

        body {
            background-color: var(--color-light);
            color: var(--color-dark);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        .navbar-brand {
            font-weight: 700;
            color: var(--color-primary);
        }

        .navbar-brand .badge {
            background-color: var(--color-success);
            color: white;
        }

        .card-header {
            background-color: var(--color-secondary);
            color: white;
        }

        .stat-card {
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .stat-card .stat-value {
            font-size: 1.8rem;
            font-weight: 700;
        }

        .stat-card .stat-label {
            font-size: 0.85rem;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-card.success .stat-value { color: var(--color-success); }
        .stat-card.error .stat-value { color: var(--color-danger); }
        .stat-card.warning .stat-value { color: var(--color-warning); }
        .stat-card.info .stat-value { color: var(--color-info); }

        .table-responsive {
            overflow-x: auto;
        }

        .table thead th {
            background-color: var(--color-secondary);
            color: white;
            font-weight: 600;
        }

        .table tbody tr:hover {
            background-color: #f8f9fa;
        }

        .table tbody tr.error-row {
            background-color: #f8d7da;
        }

        .table tbody tr.error-row td {
            color: var(--color-danger);
        }

        .btn-retransmit {
            background-color: var(--color-danger);
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .btn-retransmit:hover {
            background-color: #c82333;
        }

        .btn-retransmit:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
        }

        .btn-retransmit.active {
            background-color: var(--color-success);
        }

        .btn-retransmit.active:hover {
            background-color: #1f8754;
        }

        .chart-container {
            position: relative;
            height: 400px;
        }

        .chart-container .chart {
            max-height: 100%;
        }

        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(255, 255, 255, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
        }

        .loading-overlay.active {
            opacity: 1;
            pointer-events: all;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid var(--color-primary);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .alert-custom {
            border: none;
            border-radius: 4px;
            margin-bottom: 1rem;
        }

        .alert-custom.success {
            background-color: #d4edda;
            color: #155724;
        }

        .alert-custom.error {
            background-color: #f8d7da;
            color: #721c24;
        }

        .alert-custom.warning {
            background-color: #fff3cd;
            color: #856404;
        }

        .alert-custom.info {
            background-color: #d1ecf1;
            color: #0c5460;
        }

        .badge-cns {
            background-color: var(--color-secondary);
            color: white;
            font-weight: 600;
        }

        .badge-cpf {
            background-color: var(--color-primary);
            color: white;
            font-weight: 600;
        }

        .badge-aps {
            background-color: var(--color-warning);
            color: var(--color-dark);
            font-weight: 600;
        }

        .badge-ciap {
            background-color: var(--color-info);
            color: white;
            font-weight: 600;
        }

        .badge-soap {
            background-color: #6c757d;
            color: white;
            font-weight: 600;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
            background-color: var(--color-warning);
            color: var(--color-dark);
        }

        .badge-ciap .badge {
            background-color: var(--color-info);
            color: white;
        }

        .badge-soap .badge {
            background-color: #6c757d;
            color: white;
        }

        .badge-aps .badge {
