```html:backend/app/static/dashboard_analytics.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Executivo — MedIA Clinic</title>
    <style>
        /* ============================================
           CSS RESET & VARIABLES
           ============================================ */
        *, *::before, *::after {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --color-primary: #0a6c5a;
            --color-primary-light: #1a9ea3;
            --color-primary-dark: #054a3a;
            --color-accent: #f5a623;
            --color-accent-light: #f7c94e;
            --color-surface: #f8fafc;
            --color-surface-card: #ffffff;
            --color-text: #1e293b;
            --color-text-secondary: #64748b;
            --color-border: #e2e8f0;
            --color-success: #10b981;
            --color-success-light: #dcfce7;
            --color-warning: #f59e0b;
            --color-warning-light: #fef3c7;
            --color-danger: #ef4444;
            --color-danger-light: #fef2f2;
            --color-info: #3b82f6;
            --color-info-light: #dbeafe;
            --color-neutral: #94a3b8;
            --color-neutral-light: #e2e8f0;
            --color-gradient-1: #0a6c5a;
            --color-gradient-2: #1a9ea3;
            --color-gradient-3: #3b82f6;
            --color-gradient-4: #f5a623;
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 20px;
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.04);
            --transition-fast: 150ms ease;
            --transition-normal: 300ms ease;
            --transition-slow: 500ms ease;
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-mono: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
        }

        body {
            font-family: var(--font-sans);
            background: var(--color-surface);
            color: var(--color-text);
            line-height: 1.6;
            min-height: 100vh;
        }

        /* ============================================
           HEADER / NAVBAR
           ============================================ */
        .app-header {
            background: var(--color-surface-card);
            border-bottom: 1px solid var(--color-border);
            padding: 0 24px;
            height: 64px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: var(--shadow-sm);
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
        }

        .header-brand-logo {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 18px;
        }

        .header-brand-text {
            font-size: 20px;
            font-weight: 700;
            color: var(--color-text);
        }

        .header-brand-text span {
            color: var(--color-primary);
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .header-user {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 14px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: var(--transition-fast);
        }

        .header-user:hover {
            background: var(--color-neutral-light);
        }

        .header-user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 14px;
        }

        .header-user-info {
            display: flex;
            flex-direction: column;
        }

        .header-user-name {
            font-size: 13px;
            font-weight: 600;
            color: var(--color-text);
        }

        .header-user-role {
            font-size: 11px;
            color: var(--color-text-secondary);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-icon {
            width: 40px;
            height: 40px;
            border: none;
            border-radius: var(--radius-sm);
            background: var(--color-surface);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--color-text-secondary);
            transition: var(--transition-fast);
            font-size: 18px;
        }

        .btn-icon:hover {
            background: var(--color-neutral-light);
            color: var(--color-text);
        }

        .btn-icon.active {
            background: var(--color-primary);
            color: white;
        }

        /* ============================================
           MAIN LAYOUT
           ============================================ */
        .app-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
        }

        .page-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
            flex-wrap: wrap;
            gap: 12px;
        }

        .page-header h1 {
            font-size: 28px;
            font-weight: 700;
            color: var(--color-text);
        }

        .page-header h1 .subtitle {
            font-size: 13px;
            color: var(--color-text-secondary);
            font-weight: 400;
            margin-top: 2px;
        }

        .page-header-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 18px;
            border: none;
            border-radius: var(--radius-sm);
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition-fast);
            font-family: var(--font-sans);
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
            color: white;
            box-shadow: 0 2px 8px rgba(10, 108, 90, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(10, 108, 90, 0.4);
        }

        .btn-secondary {
            background: var(--color-surface-card);
            color: var(--color-text);
            border: 1px solid var(--color-border);
        }

        .btn-secondary:hover {
            background: var(--color-neutral-light);
        }

        .btn-sm {
            padding: 6px 12px;
            font-size: 12px;
        }

        .btn-icon-btn {
            width: 36px;
            height: 36px;
            padding: 0;
            border: 1px solid var(--color-border);
            border-radius: var(--radius-sm);
            background: var(--color-surface-card);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--color-text-secondary);
            transition: var(--transition-fast);
            font-size: 16px;
        }

        .btn-icon-btn:hover {
            border-color: var(--color-primary);
            color: var(--color-primary);
        }

        /* ============================================
           KPI CARDS GRID
           ============================================ */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }

        .kpi-card {
            background: var(--color-surface-card);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            padding: 20px;
            box-shadow: var(--shadow-sm);
            transition: var(--transition-normal);
            position: relative;
            overflow: hidden;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
        }

        .kpi-card[data-color="primary"]::before {
            background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light));
        }

        .kpi-card[data-color="accent"]::before {
            background: linear-gradient(90deg, var(--color-accent), var(--color-accent-light));
        }

        .kpi-card[data-color="info"]::before {
            background: linear-gradient(90deg, var(--color-info), #60a5fa);
        }

        .kpi-card[data-color="success"]::before {
            background: linear-gradient(90deg, var(--color-success), #34d399);
        }

        .kpi-card[data-color="warning"]::before {
            background: linear-gradient(90deg, var(--color-warning), var(--color-warning-light));
        }

        .kpi-card[data-color="danger"]::before {
            background: linear-gradient(90deg, var(--color-danger), #fca5a5);
        }

        .kpi-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .kpi-card-icon {
            width: 44px;
            height: 44px;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }

        .kpi-card[data-color="primary"] .kpi-card-icon {
            background: var(--color-success-light);
            color: var(--color-success);
        }

        .kpi-card[data-color="accent"] .kpi-card-icon {
            background: var(--color-warning-light);
            color: var(--color-warning);
        }

        .kpi-card[data-color="info"] .kpi-card-icon {
            background: var(--color-info-light);
            color: var(--color-info);
        }

        .kpi-card[data-color="success"] .kpi-card-icon {
            background: var(--color-success-light);
            color: var(--color-success);
        }

        .kpi-card[data-color="warning"] .kpi-card-icon {
            background: var(--color-warning-light);
            color: var(--color-warning);
        }

        .kpi-card[data-color="danger"] .kpi-card-icon {
            background: var(--color-danger-light);
            color: var(--color-danger);
        }

        .kpi-card-title {
            font-size: 13px;
            font-weight: 600;
            color: var(--color-text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .kpi-card-value {
            font-size: 32px;
            font-weight: 700;
            color: var(--color-text);
            line-height: 1;
            margin-bottom: 4px;
        }

        .kpi-card-change {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .kpi-card-change.up {
            background: var(--color-success-light);
            color: var(--color-success);
        }

        .kpi-card-change.down {
            background: var(--color-danger-light);
            color: