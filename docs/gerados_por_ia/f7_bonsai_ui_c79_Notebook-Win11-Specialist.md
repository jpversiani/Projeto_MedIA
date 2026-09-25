```html
<!-- Arquivo: backend/app/static/dashboard_analytics.html -->
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Executivo — MedIA</title>
    <link href="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* ===== RESET & BASE ===== */
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --border-color: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent-blue: #3b82f6;
            --accent-blue-light: #60a5fa;
            --accent-green: #10b981;
            --accent-green-light: #34d399;
            --accent-red: #ef4444;
            --accent-red-light: #fca5a5;
            --accent-orange: #f59e0b;
            --accent-orange-light: #fbbf24;
            --accent-purple: #8b5cf6;
            --accent-purple-light: #c084fc;
            --accent-pink: #ec4899;
            --accent-pink-light: #f472b6;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
            --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.4), 0 2px 4px -1px rgba(0,0,0,0.3);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.5), 0 4px 6px -2px rgba(0,0,0,0.4);
            --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.5), 0 10px 10px -5px rgba(0,0,0,0.4);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 20px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
        }

        /* ===== HEADER / NAVBAR ===== */
        .navbar {
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-color);
            padding: 0 2rem;
            height: 64px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .navbar-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
        }

        .navbar-brand-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            font-weight: 700;
            color: white;
        }

        .navbar-brand-text {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .navbar-brand-text span {
            color: var(--accent-blue-light);
        }

        .navbar-actions {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .nav-link {
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            padding: 8px 16px;
            border-radius: var(--radius-sm);
            transition: var(--transition);
        }

        .nav-link:hover {
            color: var(--text-primary);
            background: rgba(255,255,255,0.05);
        }

        .nav-link.active {
            color: var(--accent-blue-light);
            background: rgba(59, 130, 246, 0.15);
        }

        .user-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent-purple), var(--accent-pink));
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.85rem;
            cursor: pointer;
        }

        .live-indicator {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.8rem;
            color: var(--accent-green);
            font-weight: 500;
            background: rgba(16, 185, 129, 0.1);
            padding: 4px 10px;
            border-radius: 20px;
        }

        .live-dot {
            width: 8px;
            height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        /* ===== MAIN LAYOUT ===== */
        .main-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        .page-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 2rem;
        }

        .page-header h1 {
            font-size: 1.75rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .page-header h1 .icon {
            font-size: 1.5rem;
        }

        .page-header .subtitle {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        .page-header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            border-radius: var(--radius-sm);
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            border: none;
            transition: var(--transition);
            font-family: inherit;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            color: white;
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, var(--accent-blue-light), var(--accent-purple-light));
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }

        .btn-secondary {
            background: var(--bg-card);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            background: var(--bg-card-hover);
            border-color: var(--text-secondary);
        }

        .btn-sm {
            padding: 6px 14px;
            font-size: 0.8rem;
        }

        .btn-icon {
            width: 36px;
            height: 36px;
            padding: 0;
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
        }

        /* ===== FILTER BAR ===== */
        .filter-bar {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .filter-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .filter-group label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .filter-select, .filter-input {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 8px 12px;
            border-radius: var(--radius-sm);
            font-size: 0.85rem;
            font-family: inherit;
            cursor: pointer;
            transition: var(--transition);
        }

        .filter-select:focus, .filter-input:focus {
            outline: none;
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
        }

        .filter-select option {
            background: var(--bg-secondary);
        }

        .period-toggle {
            display: flex;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            overflow: hidden;
        }

        .period-toggle button {
            background: none;
            border: none;
            color: var(--text-secondary);
            padding: 8px 16px;
            font-size: 0.85rem;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
            font-family: inherit;
        }

        .period-toggle button.active {
            background: var(--accent-blue);
            color: white;
        }

        .period-toggle button:hover:not(.active) {
            color: var(--text-primary);
        }

        /* ===== KPI CARDS GRID ===== */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .kpi-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            transition: var(--transition);
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
            border-radius: var(--radius-lg) var(--radius-lg) 0 0;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
            border-color: var(--text-secondary);
        }

        .kpi-card[data-accent="blue"]::before { background: linear-gradient(90deg, var(--accent-blue), var(--accent-blue-light)); }
        .kpi-card[data-accent="green"]::before { background: linear-gradient(90deg, var(--accent-green), var(--accent-green-light)); }
        .kpi-card[data-accent="red"]::before { background: linear-gradient(90deg, var(--accent-red), var(--accent-red-light)); }
        .kpi-card[data-accent="orange"]::before { background: linear-gradient(90deg, var(--accent-orange), var(--accent-orange-light)); }
        .kpi-card[data-accent="purple"]::before { background: linear-gradient(90deg, var(--accent-purple), var(--accent-purple-light)); }
        .kpi-card[data-accent="pink"]::before { background: linear-gradient(90deg, var(--accent-pink), var(--accent-pink-light)); }

        .kpi-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }

        .kpi-card-icon {
            width: 44px;
            height: 44px;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }

        .kpi-card-icon.blue { background: rgba(59, 130, 246, 0.15); color: var(--accent-blue-light); }
        .kpi-card-icon.green { background: rgba(16, 185, 129, 0.15); color: var(--accent-green-light); }
        .kpi-card-icon.red { background: rgba(239, 68, 68, 0.15); color: var(--accent-red-light); }
        .kpi-card-icon.orange { background: rgba(245, 158, 11, 0.15); color: var(--accent-orange-light); }
        .kpi-card-icon.purple { background: rgba(139, 92, 246, 0.15); color: var(--accent-purple-light); }
        .kpi-card-icon.pink { background: rgba(236, 72, 153, 0.15); color