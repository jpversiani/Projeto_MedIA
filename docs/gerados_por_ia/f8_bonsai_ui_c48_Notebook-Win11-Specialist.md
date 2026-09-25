```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Campanhas de Busca Ativa - MedIA</title>
    <style>
        /* ============================================
           CSS RESET & BASE STYLES
           ============================================ */
        *, *::before, *::after {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --color-primary: #0056b3;
            --color-primary-dark: #003d80;
            --color-primary-light: #e3f2fd;
            --color-accent: #2e7d32;
            --color-accent-light: #e8f5e9;
            --color-warning: #f57c00;
            --color-warning-light: #fff3e0;
            --color-danger: #c62828;
            --color-danger-light: #ffebee;
            --color-info: #1976d2;
            --color-info-light: #e3f2fd;
            --color-success: #4caf50;
            --color-success-light: #e8f5e9;
            --color-bg: #f5f5f5;
            --color-surface: #ffffff;
            --color-text: #212121;
            --color-text-secondary: #757575;
            --color-border: #e0e0e0;
            --color-shadow: rgba(0, 0, 0, 0.1);
            --color-shadow-lg: rgba(0, 0, 0, 0.15);
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
            --shadow-sm: 0 1px 3px var(--color-shadow);
            --shadow-md: 0 2px 8px var(--color-shadow);
            --shadow-lg: 0 4px 16px var(--color-shadow-lg);
            --transition: all 0.2s ease;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--color-bg);
            color: var(--color-text);
            line-height: 1.6;
            min-height: 100vh;
        }

        /* ============================================
           HEADER / NAVIGATION
           ============================================ */
        .app-header {
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
            color: white;
            padding: 0;
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 10px var(--color-shadow-lg);
        }

        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 70px;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.3rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .logo-icon {
            width: 40px;
            height: 40px;
            background: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .header-actions button {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            padding: 8px 16px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            font-size: 0.9rem;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .header-actions button:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        .user-badge {
            background: rgba(255, 255, 255, 0.2);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }

        /* ============================================
           MAIN CONTENT
           ============================================ */
        .main-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        /* ============================================
           PAGE HEADER
           ============================================ */
        .page-header {
            background: var(--color-surface);
            border-radius: var(--radius-lg);
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: var(--shadow-md);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 15px;
        }

        .page-header h1 {
            font-size: 1.5rem;
            color: var(--color-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .page-header h1 .icon {
            font-size: 1.8rem;
        }

        .page-header .subtitle {
            font-size: 0.9rem;
            color: var(--color-text-secondary);
            margin-top: 4px;
        }

        .page-header .stats-summary {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }

        .stat-card {
            background: var(--color-primary-light);
            padding: 10px 16px;
            border-radius: var(--radius-md);
            text-align: center;
            min-width: 80px;
        }

        .stat-card .stat-value {
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--color-primary);
        }

        .stat-card .stat-label {
            font-size: 0.75rem;
            color: var(--color-text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* ============================================
           FILTERS BAR
           ============================================ */
        .filters-bar {
            background: var(--color-surface);
            border-radius: var(--radius-md);
            padding: 16px 20px;
            margin-bottom: 20px;
            box-shadow: var(--shadow-sm);
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
        }

        .filters-bar .filter-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .filters-bar label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--color-text-secondary);
            min-width: 60px;
        }

        .filters-bar select,
        .filters-bar input[type="text"],
        .filters-bar input[type="date"] {
            padding: 8px 12px;
            border: 1px solid var(--color-border);
            border-radius: var(--radius-sm);
            font-size: 0.9rem;
            background: white;
            transition: var(--transition);
        }

        .filters-bar select:focus,
        .filters-bar input[type="text"]:focus,
        .filters-bar input[type="date"]:focus {
            outline: none;
            border-color: var(--color-primary);
            box-shadow: 0 0 0 3px var(--color-primary-light);
        }

        .filters-bar .filter-actions {
            margin-left: auto;
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: var(--radius-sm);
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            transition: var(--transition);
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
        }

        .btn-secondary {
            background: var(--color-bg);
            color: var(--color-text);
            border: 1px solid var(--color-border);
        }

        .btn-secondary:hover {
            background: var(--color-primary-light);
        }

        .btn-danger {
            background: var(--color-danger);
            color: white;
        }

        .btn-danger:hover {
            background: #b01f1f;
        }

        .btn-success {
            background: var(--color-success);
            color: white;
        }

        .btn-success:hover {
            background: #388e3c;
        }

        .btn-warning {
            background: var(--color-warning);
            color: white;
        }

        .btn-warning:hover {
            background: #f44336;
        }

        /* ============================================
           DASHBOARD CARDS
           ============================================ */
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .dashboard-card {
            background: var(--color-surface);
            border-radius: var(--radius-lg);
            padding: 20px;
            box-shadow: var(--shadow-md);
            transition: var(--transition);
        }

        .dashboard-card:hover {
            box-shadow: var(--shadow-lg);
        }

        .dashboard-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }

        .dashboard-card-header h2 {
            font-size: 1.1rem;
            color: var(--color-text);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .dashboard-card-header .badge {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .badge-priority {
            background: var(--color-danger-light);
            color: var(--color-danger);
        }

        .badge-confirmed {
            background: var(--color-success-light);
            color: var(--color-success);
        }

        .badge-pending {
            background: var(--color-warning-light);
            color: var(--color-warning);
        }

        .badge-completed {
            background: var(--color-info-light);
            color: var(--color-info);
        }

        .dashboard-card .card-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }

        .card-stat {
            background: var(--color-bg);
            padding: 10px;
            border-radius: var(--radius-sm);
            text-align: center;
        }

        .card-stat .value {
            font-size: 1.2rem;
            font-weight: 700;
        }

        .card-stat .label {
            font-size: 0.75rem;
            color: var(--color-text-secondary);
        }

        /* ============================================
           TABLES
           ============================================ */
        .table-container {
            background: var(--color-surface);
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-md);
        }

        .table-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px 20px;
            border-bottom: 1px solid var(--color-border);
            background: var(--color-bg);
        }

        .table-header h2 {
            font-size: 1.1rem;
            color: var(--color-text);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .table-header .table-actions {
            display: flex;
            gap: 8px;
        }

        .table-body {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }

        thead th {
            background: var(--color-primary-light);
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            color: var(--color-text-secondary);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
            border-bottom: 2px solid var(--color-border);
            white-space: nowrap;
        }

        tbody tr {
            border-bottom: 1px solid var(--color-border);
            transition: var(--transition);
        }

        tbody tr:hover {
            background: var(--color-primary-light);
        }

        tbody td {
            padding: 12px 15px;
            vertical-align: middle;
        }

        .patient-name {
            font-weight: 600;
            color: var(--color-text);
        }

        .patient-name