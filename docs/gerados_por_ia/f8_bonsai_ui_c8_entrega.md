# Painel de Campanhas de Busca Ativa da Comunidade (C8)

## Arquivo Principal: Template HTML

```html:backend/app/static/campanhas_saude.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel C8 - Campanhas de Busca Ativa - ACS</title>
    <style>
        /* ===== CSS Reset & Base ===== */
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        :root {
            --sus-blue: #003366;
            --sus-light: #005599;
            --sus-accent: #0088cc;
            --sus-green: #00aa44;
            --sus-orange: #cc8800;
            --sus-red: #aa0000;
            --sus-gray-100: #f0f4f8;
            --sus-gray-200: #e0e8f0;
            --sus-gray-300: #c0c8d8;
            --sus-gray-400: #9098a8;
            --sus-gray-500: #606878;
            --sus-gray-600: #303848;
            --sus-gray-700: #181c28;
            --sus-gray-800: #0c1018;
            --sus-white: #ffffff;
            --radius: 8px;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
            --shadow-md: 0 2px 8px rgba(0,0,0,0.12);
            --shadow-lg: 0 4px 20px rgba(0,0,0,0.16);
            --transition: all 0.2s ease;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--sus-gray-100);
            color: var(--sus-gray-700);
            line-height: 1.6;
            min-height: 100vh;
        }

        /* ===== Header ===== */
        .header {
            background: var(--sus-gray-800);
            color: var(--sus-white);
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: var(--shadow-md);
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .header-brand .logo {
            width: 40px;
            height: 40px;
            background: var(--sus-blue);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.25rem;
            color: white;
        }

        .header-brand h1 {
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }

        .header-brand h1 span {
            color: var(--sus-accent);
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .header-right .agent-info {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
        }

        .header-right .agent-info .badge {
            background: var(--sus-green);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .header-right .btn {
            background: var(--sus-blue);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: var(--radius);
            cursor: pointer;
            font-size: 0.875rem;
            transition: var(--transition);
        }

        .header-right .btn:hover {
            background: var(--sus-light);
        }

        /* ===== Main Layout ===== */
        .main {
            display: grid;
            grid-template-columns: 280px 1fr;
            min-height: calc(100vh - 70px);
        }

        /* ===== Sidebar ===== */
        .sidebar {
            background: var(--sus-gray-200);
            padding: 1.5rem;
            overflow-y: auto;
            border-right: 1px solid var(--sus-gray-300);
        }

        .sidebar h2 {
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--sus-gray-500);
            margin-bottom: 1rem;
            font-weight: 600;
        }

        .filter-group {
            margin-bottom: 1.5rem;
        }

        .filter-group label {
            display: block;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--sus-gray-600);
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .filter-group select,
        .filter-group input[type="date"],
        .filter-group input[type="text"] {
            width: 100%;
            padding: 0.5rem 0.75rem;
            border: 1px solid var(--sus-gray-300);
            border-radius: var(--radius);
            font-size: 0.875rem;
            background: white;
            transition: var(--transition);
        }

        .filter-group select:focus,
        .filter-group input:focus {
            outline: none;
            border-color: var(--sus-accent);
            box-shadow: 0 0 0 3px rgba(0, 136, 204, 0.15);
        }

        .filter-group .date-range {
            display: flex;
            gap: 0.5rem;
        }

        .filter-group .date-range input {
            flex: 1;
        }

        .filter-actions {
            display: flex;
            gap: 0.5rem;
        }

        .btn-primary {
            background: var(--sus-blue);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: var(--radius);
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 600;
            transition: var(--transition);
        }

        .btn-primary:hover {
            background: var(--sus-light);
        }

        .btn-secondary {
            background: var(--sus-gray-200);
            color: var(--sus-gray-600);
            border: 1px solid var(--sus-gray-300);
            padding: 0.5rem 1rem;
            border-radius: var(--radius);
            cursor: pointer;
            font-size: 0.875rem;
            transition: var(--transition);
        }

        .btn-secondary:hover {
            background: var(--sus-gray-300);
        }

        /* ===== Stats Cards ===== */
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .stat-card {
            background: white;
            border-radius: var(--radius);
            padding: 1rem;
            box-shadow: var(--shadow-sm);
            border-left: 4px solid var(--sus-blue);
        }

        .stat-card .stat-value {
            font-size: 1.75rem;
            font-weight: 800;
            color: var(--sus-blue);
        }

        .stat-card .stat-label {
            font-size: 0.8rem;
            color: var(--sus-gray-500);
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .stat-card .stat-sub {
            font-size: 0.75rem;
            color: var(--sus-gray-400);
            margin-top: 0.25rem;
        }

        /* ===== Tables ===== */
        .table-container {
            background: white;
            border-radius: var(--radius);
            box-shadow: var(--shadow-sm);
            overflow: hidden;
        }

        .table-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.75rem 1rem;
            background: var(--sus-gray-100);
            border-bottom: 1px solid var(--sus-gray-300);
        }

        .table-header h3 {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--sus-gray-700);
        }

        .table-header .table-actions {
            display: flex;
            gap: 0.5rem;
        }

        .table-body {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        thead th {
            background: var(--sus-gray-100);
            padding: 0.75rem 1rem;
            text-align: left;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--sus-gray-500);
            border-bottom: 2px solid var(--sus-gray-300);
            white-space: nowrap;
        }

        tbody tr {
            border-bottom: 1px solid var(--sus-gray-200);
            transition: var(--transition);
        }

        tbody tr:hover {
            background: var(--sus-gray-100);
        }

        tbody td {
            padding: 0.75rem 1rem;
            font-size: 0.875rem;
            color: var(--sus-gray-600);
        }

        /* Status Badges */
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .status-prioridade {
            background: #fff3cd;
            color: #856404;
        }

        .status-urgente {
            background: #fee2e2;
            color: #991b1b;
        }

        .status-confirmada {
            background: #d1fae5;
            color: #065f46;
        }

        .status-pendente {
            background: #e0e7ff;
            color: #3b82f6;
        }

        .status-completada {
            background: #fef3c7;
            color: #b45309;
        }

        .status-rejeitada {
            background: #fee2e2;
            color: #991b1b;
        }

        /* Priority Levels */
        .priority-high {
            color: var(--sus-red);
            font-weight: 700;
        }

        .priority-medium {
            color: var(--sus-orange);
            font-weight: 600;
        }

        .priority-low {
            color: var(--sus-gray-500);
        }

        /* CNS/CPF Display */
        .id-display {
            font-family: monospace;
            font-size: 0.8rem;
            color: var(--sus-gray-500);
            background: var(--sus-gray-100);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
        }

        /* Table Footer */
        .table-footer {
            padding: 0.75rem 1rem;
            background: var(--sus-gray-100);
            border-top: 1px solid var(--sus-gray-300);
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--sus-gray-500);
        }

        /* ===== Pagination ===== */
        .pagination {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.75rem;
            background: var(--sus-gray-100);
            border-top: 1px solid var(--sus-gray-300);
        }

        .pagination a {
            background: white;
            border: 1px solid var(--sus-gray-300);
            padding: 0.4rem 0.75rem;
            border-radius: var(--radius);
            text-decoration: none;
            color: var(--sus-gray-600);
            font-size: 0.875rem;
            transition: var(--transition);
        }

