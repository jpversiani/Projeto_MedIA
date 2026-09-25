```python:backend/app/static/monitor_sisab.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor SISAB C20 - Remessas</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        :root {
            --sisab-blue: #0056b3;
            --sisab-dark: #003d80;
            --sisab-light: #e6f0fa;
            --sisab-accent: #00c853;
            --sisab-error: #d32f2f;
            --sisab-warning: #f57c00;
            --sisab-info: #1976d2;
        }

        body {
            background-color: #f5f7fa;
            color: #333;
        }

        .navbar-brand {
            color: var(--sisab-blue);
            font-weight: 700;
            font-size: 1.5rem;
        }

        .navbar-brand i {
            margin-right: 10px;
        }

        .card-header {
            background: linear-gradient(135deg, var(--sisab-blue), var(--sisab-dark));
            color: white;
            padding: 15px 20px;
        }

        .stat-card {
            border: none;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }

        .stat-card.sisab-blue { border-left: 4px solid var(--sisab-blue); }
        .stat-card.sisab-accent { border-left: 4px solid var(--sisab-accent); }
        .stat-card.sisab-error { border-left: 4px solid var(--sisab-error); }
        .stat-card.sisab-warning { border-left: 4px solid var(--sisab-warning); }

        .stat-card .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
        }

        .stat-card .stat-label {
            color: #666;
            font-size: 0.875rem;
            margin: 5px 0 0 0;
        }

        .table-thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table tbody tr:hover {
            background-color: var(--sisab-light);
        }

        .badge {
            border-radius: 20px;
            font-size: 0.75rem;
            padding: 2px 8px;
        }

        .btn-retransmit {
            background-color: var(--sisab-error);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
            transition: all 0.2s;
        }

        .btn-retransmit:hover {
            background-color: #c62828;
            transform: scale(1.02);
        }

        .btn-retransmit:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }

        .btn-retransmit:disabled:hover {
            transform: none;
        }

        .chart-container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            padding: 20px;
        }

        .loading-spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--sisab-blue);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            display: inline-block;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .alert-sisab {
            border: 1px solid var(--sisab-blue);
            background-color: var(--sisab-light);
        }

        .alert-sisab-success {
            border: 1px solid var(--sisab-accent);
            background-color: #e8f5e9;
        }

        .alert-sisab-danger {
            border: 1px solid var(--sisab-error);
            background-color: #ffebee;
        }

        .alert-sisab-warning {
            border: 1px solid var(--sisab-warning);
            background-color: #fff3e0;
        }

        .alert-sisab-info {
            border: 1px solid var(--sisab-info);
            background-color: #e3f2fd;
        }

        .table-responsive {
            margin-bottom: 20px;
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
        }

        .table thead th {
            background-color: var(--sisab-blue);
            color: white;
            font-weight: 600;
        }

        .table thead th:first-child {
            background-color: var(--sisab-dark);
        }

        .table thead th:last-child {
            background-color: var(--sisab-dark);
       