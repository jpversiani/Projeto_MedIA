```html:backend/app/static/campanhas_saude.html
<!-- Arquivo: backend/app/static/campanhas_saude.html -->
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Campanhas de Busca Ativa da Comunidade (C8) - ACS</title>
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
            --color-primary-light: #e0f0ff;
            --color-success: #28a745;
            --color-success-light: #d4edda;
            --color-warning: #ffc107;
            --color-warning-light: #fff3cd;
            --color-danger: #dc3545;
            --color-danger-light: #f8d7da;
            --color-info: #17a2b8;
            --color-info-light: #d1ecf1;
            --color-secondary: #6c757d;
            --color-secondary-light: #ced4da;
            --color-border: #dee2e6;
            --color-bg: #f8f9fa;
            --color-white: #ffffff;
            --color-text: #212529;
            --color-text-light: #6c757d;
            --color-shadow: rgba(0, 0, 0, 0.1);
            --radius: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
            --shadow-sm: 0 1px 3px var(--color-shadow);
            --shadow-md: 0 4px 6px var(--color-shadow);
            --shadow-lg: 0 10px 15px var(--color-shadow);
            --shadow-xl: 0 20px 25px var(--color-shadow);
            --transition: all 0.3s ease;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: var(--color-bg);
            color: var(--color-text);
            line-height: 1.6;
            min-height: 100vh;
        }

        /* ============================================
           HEADER / NAVBAR
           ============================================ */
        .app-header {
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
            color: var(--color-white);
            padding: 0;
            box-shadow: var(--shadow-md);
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .header-inner {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 70px;
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .header-brand .logo-icon {
            width: 40px;
            height: 40px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }

        .header-brand .logo-text span {
            display: block;
            font-size: 0.75rem;
            opacity: 0.8;
            font-weight: 400;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .header-right .agent-badge {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            padding: 8px 16px;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .header-right .agent-badge .badge-dot {
            width: 10px;
            height: 10px;
            background: var(--color-success);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .header-right .header-actions {
            display: flex;
            gap: 8px;
        }

        .btn-header {
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: var(--color-white);
            padding: 8px 16px;
            border-radius: var(--radius);
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-header:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: translateY(-1px);
        }

        .btn-header.active {
            background: rgba(255, 255, 255, 0.3);
        }

        /* ============================================
           MAIN CONTENT
           ============================================ */
        .main-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px 20px;
        }

        /* ============================================
           PAGE HEADER
           ============================================ */
        .page-header {
            background: var(--color-white);
            border-radius: var(--radius-lg);
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: var(--shadow-sm);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 16px;
        }

        .page-header h1 {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--color-primary);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .page-header h1 .icon {
            font-size: 1.75rem;
        }

        .page-header .subtitle {
            font-size: 0.9rem;
            color: var(--color-text-light);
            margin-top: 4px;
        }

        .page-header .stats-summary {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }

        .stat-card {
            background: var(--color-primary-light);
            border-radius: var(--radius);
            padding: 12px 18px;
            text-align: center;
            min-width: 100px;
        }

        .stat-card .stat-value {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--color-primary);
        }

        .stat-card .stat-label {
            font-size: 0.75rem;
            color: var(--color-text-light);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* ============================================
           FILTER BAR
           ============================================ */
        .filter-bar {
            background: var(--color-white);
            border-radius: var(--radius-lg);
            padding: 20px 24px;
            margin-bottom: 24px;
            box-shadow: var(--shadow-sm);
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }

        .filter-group {
            display: flex;
            align-items: center;
            gap: 8px;
            flex: 1;
            min-width: 200px;
        }

        .filter-group label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--color-text);
            white-space: nowrap;
        }

        .filter-group select,
        .filter-group input[type="text"],
        .filter-group input[type="date"] {
            padding: 10px 14px;
            border: 2px solid var(--color-border);
            border-radius: var(--radius);
            font-size: 0.9rem;
            color: var(--color-text);
            background: var(--color-white);
            transition: var(--transition);
            outline: none;
        }

        .filter-group select:focus,
        .filter-group input:focus {
            border-color: var(--color-primary);
            box-shadow: 0 0 0 3px var(--color-primary-light);
        }

        .filter-group input[type="text"] {
            flex: 1;
        }

        .filter-group .filter-icon {
            font-size: 1.1rem;
        }

        .filter-actions {
            display: flex;
            gap: 8px;
            align-items: center;
            flex-shrink: 0;
        }

        .btn-filter {
            padding: 10px 20px;
            border: 2px solid var(--color-primary);
            border-radius: var(--radius);
            background: var(--color-white);
            color: var(--color-primary);
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-filter:hover {
            background: var(--color-primary);
            color: var(--color-white);
        }

        .btn-filter.primary {
            background: var(--color-primary);
            color: var(--color-white);
        }

        .btn-filter.primary:hover {
            background: var(--color-primary-dark);
        }

        .btn-clear {
            padding: 10px 20px;
            border: 2px solid var(--color-border);
            border-radius: var(--radius);
            background: var(--color-white);
            color: var(--color-text-light);
            font-size: 0.85rem;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
        }

        .btn-clear:hover {
            border-color: var(--color-danger);
            color: var(--color-danger);
        }

        /* ============================================
           DASHBOARD GRID
           ============================================ */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }

        @media (max-width: 900px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }

        /* ============================================
           CARDS
           ============================================ */
        .card {
            background: var(--color-white);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
            overflow: hidden;
            transition: var(--transition);
        }

        .card:hover {
            box-shadow: var(--shadow-md);
        }

        .card-header {
            background: var(--color-primary-light);
            padding: 16px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--color-border);
        }

        .card-header h2 {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--color-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-header .card-icon {
            font-size: 1.25rem;
        }

        .card-header .card-count {
            background: var(--color-primary);
            color: var(--color-white);
            padding: 4px 12px;
            border-radius: 50px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .card-body {
            padding: 20px;
        }

        /* ============================================
           TABLES
           ============================================ */
        .table-wrapper {
            overflow-x: auto;
        }

        .table-responsive {
            width: 100%;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }

        thead {
            background: var(--color-primary-light);
        }

        thead th {
            padding: 12px 16px;
            text-align: left;
            font-weight: 600;
            color: var(--color-text);
            border-bottom: 2px solid var(--color-border);
            white-space: nowrap;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        thead th:first-child {
            border-radius: var(--radius) 0 0 0;
        }

        thead th:last-child {
            border-radius: 0 var(--radius) 0 0;
        }

        tbody tr {
            border-bottom: 1px solid var(--color-border);
            transition: var(--transition);
        }

        tbody tr:hover {
            background: var(--color-primary-light);
        }

        tbody td {
            padding: 12px 16px;
            vertical-align: middle;
        }

        tbody tr:last-child td {
            border-bottom: none;
        }

        /* ============================================
           STATUS BADGES
           ============================================ */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px