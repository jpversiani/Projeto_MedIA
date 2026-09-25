```python:backend/app/static/campanhas_saude.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Campanhas de Busca Ativa - Sistema MedIA</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #0056b3;
            --primary-light: #3a82d9;
            --success: #28a745;
            --warning: #ffc107;
            --danger: #dc3545;
            --info: #17a2b8;
            --bg: #f8f9fa;
            --card-bg: #ffffff;
            --text: #333333;
            --text-light: #666666;
            --border: #e0e0e0;
            --shadow: 0 2px 8px rgba(0,0,0,0.1);
            --radius: 8px;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }

        .header {
            background: var(--primary);
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
        }

        .header .subtitle {
            font-size: 0.85rem;
            opacity: 0.9;
        }

        .header .user-info {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .user-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--primary-light);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }

        .user-details {
            text-align: right;
        }

        .user-details .name {
            font-weight: 600;
        }

        .user-details .id {
            font-size: 0.8rem;
            opacity: 0.8;
        }

        .main-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: var(--card-bg);
            border-radius: var(--radius);
            padding: 1.5rem;
            box-shadow: var(--shadow);
            border-left: 4px solid var(--primary);
        }

        .stat-card:nth-child(2) { border-left-color: var(--success); }
        .stat-card:nth-child(3) { border-left-color: var(--warning); }
        .stat-card:nth-child(4) { border-left-color: var(--info); }

        .stat-card h3 {
            font-size: 0.9rem;
            color: var(--text-light);
            margin-bottom: 0.5rem;
        }

        .stat-card .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
        }

        .stat-card:nth-child(2) .stat-value { color: var(--success); }
        .stat-card:nth-child(3) .stat-value { color: var(--warning); }
        .stat-card:nth-child(4) .stat-value { color: var(--info); }

        .filters-bar {
            background: var(--card-bg);
            padding: 1rem;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            margin-bottom: 1.5rem;
            display: flex;
            gap: 1rem;
            align-items: center;
            flex-wrap: wrap;
        }

        .filters-bar .filter-group {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .filters-bar label {
            font-size: 0.9rem;
            font-weight: 500;
        }

        .filters-bar select,
        .filters-bar input[type="date"] {
            padding: 0.5rem;
            border: 1px solid var(--border);
            border-radius: 4px;
            font-size: 0.9rem;
        }

        .filters-bar button {
            padding: 0.5rem 1rem;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
        }

        .filters-bar button:hover {
            background: var(--primary-light);
        }

        .campaigns-table {
            background: var(--card-bg);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: hidden;
        }

        .campaigns-table thead {
            background: var(--primary);
            color: white;
        }

        .campaigns-table th {
            padding: 0.75rem 1rem;
            text-align: left;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .campaigns-table tbody tr {
            transition: background 0.2s;
        }

        .campaigns-table tbody tr:hover {
            background: #f0f7ff;
        }

        .campaigns-table td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border);
            font-size: 0.9rem;
        }

        .campaigns-table .priority-high {
            color: var(--danger);
            font-weight: 600;
        }

        .campaigns-table .priority-medium {
            color: var(--warning);
            font-weight: 600;
        }

        .campaigns-table .priority-low {
            color: var(--success);
            font-weight: 600;
        }

        .campaigns-table .status-active {
            background: #d4edda;
            color: var(--success);
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .campaigns-table .status-pending {
            background: #fff3cd;
            color: var(--warning);
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .campaigns-table .status-completed {
            background: #d1ecf1;
            color: var(--info);
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .campaigns-table .status-cancelled {
            background: #f8d7da;
            color: var(--danger);
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .campaign-actions {
            display: flex;
            gap: 0.5rem;
        }

        .campaign-actions button {
            padding: 0.25rem 0.5rem;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.75rem;
        }

        .btn-confirm {
            background: var(--success);
            color: white;
        }

        .btn-confirm:hover {
            background: #218838;
        }

        .btn-cancel {
            background: var(--danger);
            color: white;
        }

        .btn-cancel:hover {
            background: #c82333;
        }

        .btn-info {
            background: var(--info);
            color: white;
        }

        .btn-info:hover {
            background: #0d6efd;
        }

        .no-results {
            text-align: center;
            padding: 3rem;
            color: var(--text-light);
        }

        .no-results .icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }

        .loading {
            text-align: center;
            padding: 2rem;
            color: var(--text-light);
        }

        .loading .spinner {
            border: 4px solid var(--border);
            border-top-color: var(--primary);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .footer {
            text-align: center;
            padding: 2rem;
            color: var(--text-light);
            font-size: 0.85rem;
        }

        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: var(--radius);
            color: white;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        }

        .toast-success { background: var(--success); }
        .toast-error { background: var(--danger); }
        .toast-info { background: var(--info); }

        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .toast.removing {
            animation: slideOut 0.3s ease-in forwards;
        }

        @keyframes slideOut {
            to { transform: translateX(100%); opacity: 0; }
        }

        .badge-cianap2 {
            background: #e7f3ff;
            color: #0056b3;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .badge-cid10 {
            background: #f0f8ff;
            color: #0056b3;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .badge-soap {
            background: #fff3cd;
            color: #856404;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .badge-cns {
            background: #d4edda;
            color: #155724;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .badge-cpf {
            background: #d1ecf1;
            color: #0c5460;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .campaign-detail-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 200;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }

        .campaign-detail-modal.active {
            display: flex;
        }

        .modal-content {
            background: var(--card-bg);
            border-radius: var(--radius);
            padding: 2rem;
            max-width: 800px;
            width: 100%;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }

        .modal-content h2 {
            margin-bottom: 1rem;
            color: var(--primary);
        }

        .modal-content .detail-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
        }

        .modal-content .detail-item {
            background: var(--bg);
            padding: 1rem;
            border-radius: var(--radius);
            border: 1px solid var(--border);
        }

        .