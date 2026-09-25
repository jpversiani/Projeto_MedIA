```html:backend/app/static/dashboard_analytics.html
<!DOCTYPE html>
<html lang="pt-BR" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Executivo - MedIA | Análise de Performance</title>
    <style>
        /* ============================================
           CSS CUSTOM PROPERTIES & RESET
           ============================================ */
        :root {
            --primary: #0066cc;
            --primary-dark: #0052a3;
            --primary-light: #e6f0ff;
            --secondary: #2ecc71;
            --secondary-dark: #27ae60;
            --warning: #f39c12;
            --danger: #e74c3c;
            --danger-dark: #c0392b;
            --info: #3498db;
            --info-dark: #2980b9;
            --bg-light: #f8f9fa;
            --bg-dark: #1a1a2e;
            --card-bg-light: #ffffff;
            --card-bg-dark: #16213e;
            --text-light: #2d3748;
            --text-dark: #ffffff;
            --border-light: #e2e8f0;
            --border-dark: #2a3a5c;
            --shadow-light: 0 2px 8px rgba(0,0,0,0.08);
            --shadow-dark: 0 4px 20px rgba(0,0,0,0.3);
            --radius: 12px;
            --transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        [data-theme="dark"] {
            --bg-light: #1a1a2e;
            --card-bg-light: #16213e;
            --text-light: #e2e8f0;
            --text-dark: #ffffff;
            --border-light: #2a3a5c;
            --shadow-light: 0 2px 8px rgba(0,0,0,0.2);
            --shadow-dark: 0 4px 20px rgba(0,0,0,0.4);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-light);
            color: var(--text-light);
            transition: background var(--transition), color var(--transition);
            min-height: 100vh;
        }

        /* ============================================
           HEADER & NAVIGATION
           ============================================ */
        .header {
            background: var(--card-bg-light);
            border-bottom: 1px solid var(--border-light);
            padding: 0 24px;
            height: 72px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: var(--shadow-light);
            transition: background var(--transition), box-shadow var(--transition);
        }

        [data-theme="dark"] .header {
            background: var(--card-bg-dark);
            box-shadow: var(--shadow-dark);
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
        }

        .logo-icon {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            color: white;
            font-weight: 700;
        }

        .logo-text {
            font-size: 20px;
            font-weight: 700;
            color: var(--primary);
        }

        .logo-text span {
            color: var(--secondary);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .theme-toggle {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            border: 1px solid var(--border-light);
            background: var(--card-bg-light);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all var(--transition);
            color: var(--text-light);
        }

        [data-theme="dark"] .theme-toggle {
            background: var(--card-bg-dark);
            border-color: var(--border-dark);
        }

        .theme-toggle:hover {
            transform: rotate(15deg);
            border-color: var(--primary);
        }

        .user-profile {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--info));
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 14px;
        }

        .user-info {
            display: none;
        }

        .user-info .user-name {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-light);
        }

        .user-info .user-role {
            font-size: 11px;
            color: #64748b;
        }

        .user-info .user-cns {
            font-size: 11px;
            color: #64748b;
        }

        .notification-badge {
            position: absolute;
            top: -4px;
            right: -4px;
            background: var(--danger);
            color: white;
            font-size: 10px;
            font-weight: 700;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* ============================================
           MAIN LAYOUT
           ============================================ */
        .main-container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 24px;
        }

        .page-header {
            margin-bottom: 24px;
        }

        .page-header h1 {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-light);
            margin-bottom: 4px;
        }

        .page-header .subtitle {
            font-size: 14px;
            color: #64748b;
        }

        .page-header .subtitle span {
            color: var(--primary);
            font-weight: 600;
        }

        /* ============================================
           FILTER BAR
           ============================================ */
        .filter-bar {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }

        .filter-group {
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--card-bg-light);
            border: 1px solid var(--border-light);
            padding: 8px 16px;
            border-radius: 8px;
            transition: all var(--transition);
        }

        [data-theme="dark"] .filter-group {
            background: var(--card-bg-dark);
            border-color: var(--border-dark);
        }

        .filter-group:hover {
            border-color: var(--primary);
        }

        .filter-group label {
            font-size: 13px;
            font-weight: 500;
            color: #64748b;
        }

        .filter-group select,
        .filter-group input {
            border: none;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 13px;
            color: var(--text-light);
            background: transparent;
            cursor: pointer;
        }

        [data-theme="dark"] .filter-group select,
        [data-theme="dark"] .filter-group input {
            color: var(--text-dark);
            background: var(--card-bg-dark);
        }

        .filter-group select:focus,
        .filter-group input:focus {
            outline: 2px solid var(--primary);
            border-radius: 6px;
        }

        .date-range-selector {
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--card-bg-light);
            border: 1px solid var(--border-light);
            padding: 8px 16px;
            border-radius: 8px;
            transition: all var(--transition);
        }

        [data-theme="dark"] .date-range-selector {
            background: var(--card-bg-dark);
            border-color: var(--border-dark);
        }

        .date-range-selector select {
            border: none;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 13px;
            color: var(--text-light);
            background: transparent;
            cursor: pointer;
        }

        [data-theme="dark"] .date-range-selector select {
            color: var(--text-dark);
            background: var(--card-bg-dark);
        }

        .date-range-selector select:focus {
            outline: 2px solid var(--primary);
            border-radius: 6px;
        }

        .refresh-btn {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            border: 1px solid var(--border-light);
            background: var(--card-bg-light);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all var(--transition);
            color: var(--text-light);
        }

        [data-theme="dark"] .refresh-btn {
            background: var(--card-bg-dark);
            border-color: var(--border-dark);
        }

        .refresh-btn:hover {
            background: var(--primary-light);
            border-color: var(--primary);
            transform: rotate(15deg);
        }

        .refresh-btn:active {
            transform: rotate(0deg);
        }

        /* ============================================
           KPI CARDS GRID
           ============================================ */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }

        .kpi-card {
            background: var(--card-bg-light);
            border: 1px solid var(--border-light);
            border-radius: var(--radius);
            padding: 20px;
            transition: all var(--transition);
            position: relative;
            overflow: hidden;
        }

        [data-theme="dark"] .kpi-card {
            background: var(--card-bg-dark);
            border-color: var(--border-dark);
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-dark);
            border-color: var(--primary);
        }

        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            border-radius: var(--radius) var(--radius) 0 0;
        }

        .kpi-card .kpi-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .kpi-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
        }

        .kpi-card .kpi-title {
            font-size: 13px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .kpi-card .kpi-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-light);
            line-height: 1.2;
        }

        .kpi-card .kpi-change {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-top: 8px;
        }

        .kpi-card .kpi-change.up {
            background: #d1fae5;
            color: #065f46;
        }

        .kpi-card .kpi-change.down {
            background: #fee2e2;
            color: #991b1b;
        }

        .kpi-card .kpi-change.neutral {
            background: #e0e7ff;
            color: #1e40af;
        }

        .kpi-card .kpi-sub {
            font-size: 11px;
            color: #64748b;
            margin-top: 8px;
        }

        /* ============================================
           CHARTS GRID
           ============================================ */
        .charts-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }

        .chart-card {
            background: var(--card-bg-light);
            border: 1px solid