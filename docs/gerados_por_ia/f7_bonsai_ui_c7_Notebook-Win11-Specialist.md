```html:backend/app/static/dashboard_analytics.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Executivo - Sistema MedIA</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #111827;
            --bg-card: #1a2235;
            --bg-card-hover: #222b45;
            --border-color: #2a3550;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --accent-blue: #3b82f6;
            --accent-blue-light: #60a5fa;
            --accent-green: #10b981;
            --accent-green-light: #34d399;
            --accent-red: #ef4444;
            --accent-red-light: #f87171;
            --accent-orange: #f59e0b;
            --accent-purple: #8b5cf6;
            --accent-purple-light: #c084fc;
            --accent-teal: #06b6d4;
            --accent-teal-light: #22d3ee;
            --gradient-blue: linear-gradient(135deg, #3b82f6, #8b5cf6);
            --gradient-green: linear-gradient(135deg, #10b981, #06b6d4);
            --gradient-red: linear-gradient(135deg, #ef4444, #f97316);
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
            --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.4), 0 2px 4px -1px rgba(0,0,0,0.3);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.5), 0 4px 6px -2px rgba(0,0,0,0.4);
            --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.5), 0 8px 10px -6px rgba(0,0,0,0.4);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 20px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Header */
        .dashboard-header {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            padding: 16px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(10px);
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
        }

        .logo-icon {
            width: 40px;
            height: 40px;
            background: var(--gradient-blue);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: 700;
            color: white;
        }

        .logo-text {
            font-size: 22px;
            font-weight: 700;
            color: var(--text-primary);
        }

        .logo-text span {
            color: var(--accent-blue);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .refresh-btn {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 8px 16px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 500;
            transition: var(--transition);
        }

        .refresh-btn:hover {
            background: var(--bg-card-hover);
            border-color: var(--accent-blue);
            color: var(--accent-blue-light);
        }

        .refresh-btn:active {
            transform: scale(0.98);
        }

        .user-profile {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 14px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: var(--transition);
        }

        .user-profile:hover {
            border-color: var(--accent-blue);
        }

        .user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--gradient-green);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 14px;
            color: white;
        }

        .user-info {
            display: flex;
            flex-direction: column;
        }

        .user-name {
            font-size: 13px;
            font-weight: 600;
        }

        .user-role {
            font-size: 11px;
            color: var(--text-secondary);
        }

        .live-indicator {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: var(--accent-green);
            font-weight: 500;
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
            50% { opacity: 0.5; }
        }

        /* Main Content */
        .main-content {
            padding: 24px 32px;
            max-width: 1400px;
            margin: 0 auto;
        }

        /* Page Header */
        .page-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
        }

        .page-title {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
        }

        .page-subtitle {
            font-size: 14px;
            color: var(--text-secondary);
            margin-top: 4px;
        }

        .period-selector {
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 4px;
        }

        .period-btn {
            padding: 8px 16px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 500;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: var(--transition);
            font-family: inherit;
        }

        .period-btn:hover {
            color: var(--text-primary);
            background: var(--bg-card-hover);
        }

        .period-btn.active {
            background: var(--gradient-blue);
            color: white;
            font-weight: 600;
        }

        /* KPI Cards Grid */
        .kpi-section {
            margin-bottom: 24px;
        }

        .kpi-section-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 16px;
        }

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
        }

        .kpi-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 20px;
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
            border-radius: var(--radius-md) var(--radius-md) 0 0;
        }

        .kpi-card:hover {
            border-color: var(--accent-blue);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .kpi-card.kpi-blue::before { background: var(--accent-blue); }
        .kpi-card.kpi-green::before { background: var(--accent-green); }
        .kpi-card.kpi-red::before { background: var(--accent-red); }
        .kpi-card.kpi-orange::before { background: var(--accent-orange); }
        .kpi-card.kpi-purple::before { background: var(--accent-purple); }
        .kpi-card.kpi-teal::before { background: var(--accent-teal); }

        .kpi-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .kpi-icon {
            width: 44px;
            height: 44px;
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }

        .kpi-blue .kpi-icon { background: rgba(59, 130, 246, 0.15); color: var(--accent-blue); }
        .kpi-green .kpi-icon { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); }
        .kpi-red .kpi-icon { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); }
        .kpi-orange .kpi-icon { background: rgba(245, 158, 11, 0.15); color: var(--accent-orange); }
        .kpi-purple .kpi-icon { background: rgba(139, 92, 246, 0.15); color: var(--accent-purple); }
        .kpi-teal .kpi-icon { background: rgba(6, 182, 212, 0.15); color: var(--accent-teal); }

        .kpi-trend {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 20px;
        }

        .trend-up { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); }
        .trend-down { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); }
        .trend-neutral { background: rgba(148, 163, 184, 0.15); color: var(--text-secondary); }

        .kpi-value {
            font-size: 32px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1;
        }

        .kpi-label {
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 8px;
            font-weight: 500;
        }

        .kpi-detail {
            margin-top: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            color: var(--text-secondary);
        }

        .kpi-detail .detail-icon {
            font-size: 14px;
        }

        /* Charts Section */
        .charts-section {
            margin-bottom: 24px;
        }

        .charts-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        .chart-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            overflow: hidden;
        }

        .chart-card-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .chart-card-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .chart-card-actions {
            display: flex;
            gap: 8