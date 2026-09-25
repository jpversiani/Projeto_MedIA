```python
# Arquivo: backend/app/static/campanhas_saude.html
"""
Dashboard de Campanhas de Busca Ativa da Comunidade (C96)
Para Agentes Comunitários de Saúde (ACS) - Sistema SUS/APS
Padrões: CIAP-2, CID-10, SOAP, Identificação por CNS/CPF
"""

<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard C96 - Campanhas de Busca Ativa - ACS</title>
    <style>
        /* ============================================
           CSS RESET & BASE
           ============================================ */
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        :root {
            --primary: #0056b3;
            --primary-dark: #003d80;
            --primary-light: #e6f0ff;
            --accent: #28a745;
            --accent-dark: #218838;
            --warning: #ffc107;
            --danger: #dc3545;
            --danger-dark: #c82333;
            --info: #17a2b8;
            --info-dark: #0d6efd;
            --bg: #f8f9fa;
            --bg-card: #ffffff;
            --text: #212529;
            --text-muted: #6c757d;
            --border: #dee2e6;
            --shadow: 0 2px 8px rgba(0,0,0,0.1);
            --shadow-lg: 0 4px 16px rgba(0,0,0,0.15);
            --radius: 8px;
            --transition: all 0.3s ease;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }

        /* ============================================
           HEADER & NAVIGATION
           ============================================ */
        .app-header {
            background: var(--primary);
            color: white;
            padding: 0 20px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: var(--shadow);
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .header-brand .logo {
            width: 40px;
            height: 40px;
            background: var(--accent);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: bold;
        }

        .header-brand h1 {
            font-size: 1.2rem;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .header-brand h1 span {
            color: var(--accent);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .header-actions button {
            background: transparent;
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 8px 16px;
            border-radius: var(--radius);
            cursor: pointer;
            font-size: 0.9rem;
            transition: var(--transition);
        }

        .header-actions button:hover {
            background: rgba(255,255,255,0.2);
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--accent);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 14px;
        }

        .user-details {
            display: flex;
            flex-direction: column;
        }

        .user-details .name {
            font-size: 0.85rem;
            font-weight: 600;
        }

        .user-details .role {
            font-size: 0.75rem;
            opacity: 0.8;
        }

        /* ============================================
           LAYOUT
           ============================================ */
        .app-layout {
            display: grid;
            grid-template-columns: 260px 1fr;
            min-height: calc(100vh - 60px);
        }

        /* ============================================
           SIDEBAR
           ============================================ */
        .sidebar {
            background: var(--primary-dark);
            color: white;
            padding: 20px;
            overflow-y: auto;
        }

        .sidebar-title {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.7;
            margin-bottom: 15px;
            font-weight: 600;
        }

        .sidebar-nav {
            list-style: none;
        }

        .sidebar-nav li {
            margin-bottom: 5px;
        }

        .sidebar-nav a {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 15px;
            color: rgba(255,255,255,0.8);
            text-decoration: none;
            border-radius: var(--radius);
            transition: var(--transition);
            font-size: 0.9rem;
        }

        .sidebar-nav a:hover,
        .sidebar-nav a.active {
            background: rgba(255,255,255,0.1);
            color: white;
        }

        .sidebar-nav a.active {
            background: rgba(255,255,255,0.15);
        }

        .sidebar-nav a .icon {
            width: 24px;
            text-align: center;
            font-size: 1.1rem;
        }

        .sidebar-divider {
            height: 1px;
            background: rgba(255,255,255,0.1);
            margin: 15px 0;
        }

        .sidebar-footer {
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }

        .sidebar-footer p {
            font-size: 0.75rem;
            opacity: 0.6;
            line-height: 1.5;
        }

        .sidebar-footer .susp-info {
            margin-top: 10px;
            padding: 8px;
            background: rgba(255,255,255,0.05);
            border-radius: var(--radius);
        }

        /* ============================================
           MAIN CONTENT
           ============================================ */
        .main-content {
            padding: 20px;
            overflow-y: auto;
        }

        .content-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 10px;
        }

        .content-header h2 {
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .content-header h2 .badge {
            background: var(--accent);
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .filters-bar {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 20px;
            background: var(--bg-card);
            padding: 12px 16px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
        }

        .filters-bar .filter-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .filters-bar label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
        }

        .filters-bar select,
        .filters-bar input[type="text"],
        .filters-bar input[type="date"] {
            padding: 6px 10px;
            border: 1px solid var(--border);
            border-radius: var(--radius);
            font-size: 0.9rem;
            background: white;
            transition: var(--transition);
        }

        .filters-bar select:focus,
        .filters-bar input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(0,86,179,0.1);
        }

        .filters-bar button {
            padding: 6px 16px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: var(--radius);
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            transition: var(--transition);
        }

        .filters-bar button:hover {
            background: var(--primary-dark);
        }

        /* ============================================
           STATS CARDS
           ============================================ */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 15px;
            box-shadow: var(--shadow);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .stat-card .stat-icon {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }

        .stat-card .stat-icon.red { background: rgba(220,53,69,0.1); color: var(--danger); }
        .stat-card .stat-icon.green { background: rgba(40,167,69,0.1); color: var(--accent); }
        .stat-card .stat-icon.blue { background: rgba(0,86,179,0.1); color: var(--primary); }
        .stat-card .stat-icon.yellow { background: rgba(255,193,7,0.1); color: #856404; }

        .stat-card .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text);
        }

        .stat-card .stat-label {
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        /* ============================================
           TABLES
           ============================================ */
        .table-container {
            background: var(--bg-card);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: hidden;
        }

        .table-header {
            padding: 15px 20px;
            background: var(--primary);
            color: white;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            user-select: none;
        }

        .table-header h3 {
            font-size: 1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .table-header .table-count {
            background: rgba(255,255,255,0.2);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
        }

        .table-body {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        thead {
            background: var(--primary-light);
        }

        th {
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            border-bottom: 2px solid var(--border);
            white-space: nowrap;
        }

        td {
            padding: 12px 15px;
            border-bottom: 1px solid var(--border);
            font-size: 0.9rem;
            vertical-align: middle;
        }

        tbody tr:hover {
            background: var(--primary-light);
        }

        tbody tr:last-child td {
            border-bottom: none;
        }

        /* ============================================
           STATUS BADGES
           ============================================ */
