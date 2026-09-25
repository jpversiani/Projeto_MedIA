```python:backend/app/static/campanhas_saude.html
# Arquivo: backend/app/static/campanhas_saude.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Campanhas de Busca Ativa - ACS</title>
    <style>
        /* ============================================
           CSS RESET & VARIABLES
           ============================================ */
        :root {
            --color-primary: #0056b3;
            --color-primary-dark: #003d80;
            --color-primary-light: #e6f2ff;
            --color-accent: #28a745;
            --color-accent-dark: #1e8439;
            --color-warning: #ffc107;
            --color-warning-dark: #e6a800;
            --color-danger: #dc3545;
            --color-danger-dark: #c82333;
            --color-info: #17a2b8;
            --color-info-dark: #00707a;
            --color-bg: #f8f9fa;
            --color-surface: #ffffff;
            --color-text: #212529;
            --color-text-secondary: #6c757d;
            --color-border: #dee2e6;
            --color-shadow: rgba(0, 0, 0, 0.1);
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
            --shadow-sm: 0 1px 3px var(--color-shadow);
            --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
            --transition: all 0.2s ease;
            --font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--font-family);
            background: var(--color-bg);
            color: var(--color-text);
            line-height: 1.6;
            min-height: 100vh;
        }

        /* ============================================
           HEADER / NAVBAR
           ============================================ */
        .app-header {
            background: var(--color-primary);
            color: white;
            padding: 0 2rem;
            height: 64px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: var(--shadow-md);
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .app-header .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .app-header .logo .icon {
            width: 40px;
            height: 40px;
            background: var(--color-accent);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }

        .app-header .logo span {
            color: white;
        }

        .app-header .nav-links {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .app-header .nav-links a {
            color: rgba(255, 255, 255, 0.85);
            text-decoration: none;
            font-size: 0.95rem;
            font-weight: 500;
            padding: 8px 16px;
            border-radius: var(--radius-sm);
            transition: var(--transition);
        }

        .app-header .nav-links a:hover {
            background: rgba(255, 255, 255, 0.15);
            color: white;
        }

        .app-header .user-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .app-header .user-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--color-accent);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 0.9rem;
        }

        .app-header .user-details {
            display: flex;
            flex-direction: column;
        }

        .app-header .user-name {
            font-size: 0.85rem;
            font-weight: 600;
            color: white;
        }

        .app-header .user-id {
            font-size: 0.75rem;
            color: rgba(255, 255, 255, 0.7);
        }

        /* ============================================
           MAIN CONTENT
           ============================================ */
        .main-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        /* ============================================
           PAGE HEADER
           ============================================ */
        .page-header {
            background: var(--color-surface);
            border-radius: var(--radius-lg);
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-sm);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 2rem;
            flex-wrap: wrap;
        }

        .page-header h1 {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--color-primary-dark);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .page-header h1 .badge {
            background: var(--color-primary-light);
            color: var(--color-primary);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .page-header .stats-summary {
            display: flex;
            gap: 1.5rem;
            align-items: center;
        }

        .stat-card {
            background: var(--color-primary-light);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            padding: 12px 20px;
            text-align: center;
            min-width: 120px;
        }

        .stat-card .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--color-primary-dark);
        }

        .stat-card .stat-label {
            font-size: 0.75rem;
            color: var(--color-text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* ============================================
           FILTER BAR
           ============================================ */
        .filter-bar {
            background: var(--color-surface);
            border-radius: var(--radius-md);
            padding: 1.25rem 1.5rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-sm);
            display: flex;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .filter-bar .filter-group {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .filter-bar label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--color-text-secondary);
            white-space: nowrap;
        }

        .filter-bar select,
        .filter-bar input[type="text"],
        .filter-bar input[type="date"] {
            padding: 8px 12px;
            border: 1px solid var(--color-border);
            border-radius: var(--radius-sm);
            font-size: 0.9rem;
            font-family: inherit;
            background: white;
            transition: var(--transition);
        }

        .filter-bar select:focus,
        .filter-bar input:focus {
            outline: none;
            border-color: var(--color-primary);
            box-shadow: 0 0 0 3px var(--color-primary-light);
        }

        .filter-bar .btn {
            padding: 8px 20px;
            border: none;
            border-radius: var(--radius-sm);
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            display: inline-flex;
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
            background: var(--color-surface);
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
            background: var(--color-danger-dark);
        }

        .btn-success {
            background: var(--color-accent);
            color: white;
        }

        .btn-success:hover {
            background: var(--color-accent-dark);
        }

        .filter-bar .search-box {
            flex: 1;
            min-width: 200px;
        }

        .filter-bar .search-box input {
            width: 100%;
        }

        .filter-bar .search-box .icon {
            color: var(--color-text-secondary);
            font-size: 1rem;
        }

        /* ============================================
           TABLES
           ============================================ */
        .table-container {
            background: var(--color-surface);
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-sm);
            margin-bottom: 2rem;
        }

        .table-wrapper {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }

        thead {
            background: var(--color-primary-light);
        }

        th {
            padding: 14px 16px;
            text-align: left;
            font-weight: 600;
            color: var(--color-text-secondary);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
            border-bottom: 2px solid var(--color-border);
            white-space: nowrap;
        }

        th.sortable {
            cursor: pointer;
            user-select: none;
        }

        th.sortable:hover {
            color: var(--color-primary);
        }

        th.sortable .sort-icon {
            margin-left: 4px;
            opacity: 0.4;
            font-size: 0.7rem;
        }

        th.sortable.active .sort-icon {
            opacity: 1;
            color: var(--color-primary);
        }

        td {
            padding: 12px 16px;
            border-bottom: 1px solid var(--color-border);
            vertical-align: middle;
        }

        tbody tr {
            transition: var(--transition);
        }

        tbody tr:hover {
            background: var(--color-primary-light);
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
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }

        .status-urgente {
            background: #ffebee;
            color: var(--color-danger);
        }

        .status-prioridade {
            background: #fff3e0;
            color: #e65100;
        }

        .status-estandar {
            background: #e8f5e9;
            color: var(--color-accent-dark);
        }

        .status-pendente {
            background: #fff3e0;
            color: #e65100;
        }

        .status-confirmada {
            background: #e8f5e9;
            color: var(--color-accent-dark);
        }

        .status-completada {
            background: #fff3e0;
            color: #e65100;
        }

        .status-em-agendamento {
            background: #e3f2fd;
            color: var(--color-info-dark);
        }

        .status-errou {
            background: #ffebee;
            color: var(--color-danger);
        }

        /* ============================================
           ACTION BUTTONS
           ============================================ */
        .action-buttons {
            display: flex;
            gap: 6px;
        }

        .action-btn {
            padding: 4px 10px;
            border: none;
            border-radius: var(--radius-sm);
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .action-btn:hover {
            opacity: 0.8;
        }

        .action-btn-confirm {
            background: var(--color-accent);
            color: white;
        }

        .action-btn-confirm:hover {
            background: var(--color-accent-dark);
        }

        .action-btn-visit {
            background: var(--color-primary);
            color: white;
        }

        .action-btn-visit:hover {
            background: var(--color-primary-dark);
        }

        .action