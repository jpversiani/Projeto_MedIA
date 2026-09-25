```python:backend/app/static/dashboard_analytics.html
# Arquivo: backend/app/static/dashboard_analytics.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Executivo — MedIA | Atenção Primária</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #0d6efd;
            --primary-dark: #0b5ed7;
            --primary-light: #e9f0ff;
            --success: #198754;
            --success-light: #d1fae5;
            --warning: #d97706;
            --danger: #dc2626;
            --danger-light: #fee2e2;
            --info: #0ea5e9;
            --info-light: #dbeafe;
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border: #334155;
            --gradient-hero: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            --gradient-accent: linear-gradient(135deg, #0d6efd 0%, #0ea5e9 100%);
            --gradient-success: linear-gradient(135deg, #198754 0%, #059669 100%);
            --gradient-warning: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
            --gradient-danger: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
            --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
            --shadow-glow: 0 0 20px rgba(13,110,253,0.15);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-dark); }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

        /* Header */
        .dashboard-header {
            background: var(--gradient-hero);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(20px);
            background: rgba(15, 23, 42, 0.95);
        }

        .header-inner {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            text-decoration: none;
        }

        .logo-icon {
            width: 44px;
            height: 44px;
            background: var(--gradient-accent);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            box-shadow: var(--shadow-glow);
        }

        .logo-text {
            font-size: 1.5rem;
            font-weight: 800;
            background: var(--gradient-accent);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .logo-sub {
            font-size: 0.75rem;
            color: var(--text-muted);
            font-weight: 500;
            letter-spacing: 0.5px;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .date-filter {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 0.5rem 1rem;
        }

        .date-filter select {
            background: transparent;
            border: none;
            color: var(--text-primary);
            padding: 0.35rem 0.5rem;
            font-size: 0.85rem;
            font-family: inherit;
            cursor: pointer;
        }

        .date-filter select:focus {
            outline: none;
            border-color: var(--primary);
        }

        .refresh-btn {
            background: var(--gradient-accent);
            border: none;
            border-radius: 10px;
            padding: 0.5rem 1rem;
            color: white;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.2s;
        }

        .refresh-btn:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-glow);
        }

        .refresh-btn:active {
            transform: translateY(0);
        }

        /* Main content */
        .main-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        /* Stats bar */
        .stats-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 2rem;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .stats-summary {
            display: flex;
            align-items: center;
            gap: 1.5rem;
            flex-wrap: wrap;
        }

        .stat-badge {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 0.6rem 1rem;
            font-size: 0.85rem;
        }

        .stat-badge .stat-icon {
            width: 28px;
            height: 28px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
        }

        .stat-badge .stat-value {
            font-weight: 700;
            font-size: 0.95rem;
        }

        .stat-badge .stat-label {
            color: var(--text-muted);
            font-size: 0.75rem;
        }

        .period-selector {
            display: flex;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 3px;
        }

        .period-selector button {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.5rem 1.25rem;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
        }

        .period-selector button:hover {
            color: var(--text-primary);
            background: var(--bg-card-hover);
        }

        .period-selector button.active {
            background: var(--gradient-accent);
            color: white;
        }

        /* KPI Cards Grid */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .kpi-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            border-radius: 16px 16px 0 0;
        }

        .kpi-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-xl);
            border-color: var(--text-muted);
        }

        .kpi-card.primary {
            --kpi-header: var(--gradient-accent);
        }
        .kpi-card.primary::before { background: var(--gradient-accent); }

        .kpi-card.success {
            --kpi-header: var(--gradient-success);
        }
        .kpi-card.success::before { background: var(--gradient-success); }

        .kpi-card.warning {
            --kpi-header: var(--gradient-warning);
        }
        .kpi-card.warning::before { background: var(--gradient-warning); }

        .kpi-card.danger {
            --kpi-header: var(--gradient-danger);
        }
        .kpi-card.danger::before { background: var(--gradient-danger); }

        .kpi-card.info {
            --kpi-header: var(--gradient-info);
        }
        .kpi-card.info::before { background: var(--gradient-info); }

        .kpi-card .card-icon {
            width: 48px;
            height: 48px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            margin-bottom: 1rem;
        }

        .kpi-card.primary .card-icon { background: rgba(13,110,253,0.15); color: var(--primary); }
        .kpi-card.success .card-icon { background: rgba(25,135,84,0.15); color: var(--success); }
        .kpi-card.warning .card-icon { background: rgba(217,119,6,0.15); color: var(--warning); }
        .kpi-card.danger .card-icon { background: rgba(220,38,38,0.15); color: var(--danger); }
        .kpi-card.info .card-icon { background: rgba(14,165,233,0.15); color: var(--info); }

        .kpi-card .card-title {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: var(--text-muted);
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .kpi-card .card-value {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
            line-height: 1.2;
        }

        .kpi-card .card-change {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.6rem;
            border-radius: 20px;
        }

        .kpi-card .card-change.up {
            color: var(--success);
            background: rgba(25,135,84,0.1);
        }

        .kpi-card .card-change.down {
            color: var(--