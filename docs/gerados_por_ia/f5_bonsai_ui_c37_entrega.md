```html:backend/app/static/sync_status.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sincronização ACS C37 — MedIA</title>
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
            --color-primary: #004d40;
            --color-primary-light: #006b5c;
            --color-primary-dark: #003d2c;
            --color-accent: #e63946;
            --color-accent-light: #f472a6;
            --color-success: #059669;
            --color-success-light: #6ee7b7;
            --color-warning: #f59e0b;
            --color-warning-light: #fef3c7;
            --color-danger: #dc2626;
            --color-danger-light: #fee2e2;
            --color-info: #2563eb;
            --color-info-light: #dbeafe;
            --color-neutral: #6b7280;
            --color-neutral-light: #9ca3af;
            --color-surface: #ffffff;
            --color-surface-alt: #f8fafc;
            --color-border: #e2e8f0;
            --color-text: #1f2937;
            --color-text-secondary: #6b7280;
            --color-text-muted: #9ca3af;
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 24px;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06);
            --shadow-lg: 0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05);
            --shadow-xl: 0 20px 25px rgba(0,0,0,0.1), 0 8px 10px rgba(0,0,0,0.06);
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            --font-main: 'Segoe UI', system-ui, -apple-system, sans-serif;
        }

        body {
            font-family: var(--font-main);
            background: var(--color-surface-alt);
            color: var(--color-text);
            line-height: 1.6;
            min-height: 100vh;
        }

        /* ============================================
           HEADER / NAVBAR
           ============================================ */
        .app-header {
            background: var(--color-surface);
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

        .header-brand-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            color: white;
            font-weight: 700;
        }

        .header-brand-text {
            font-size: 18px;
            font-weight: 700;
            color: var(--color-primary);
            letter-spacing: -0.5px;
        }

        .header-brand-text span {
            color: var(--color-accent);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .header-status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--color-success);
            display: inline-block;
            animation: pulse-dot 2s infinite;
        }

        .header-status-dot.warning {
            background: var(--color-warning);
            animation: pulse-dot 1.5s infinite;
        }

        .header-status-dot.error {
            background: var(--color-danger);
            animation: pulse-dot 1s infinite;
        }

        @keyframes pulse-dot {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.8); }
        }

        .btn-header {
            padding: 8px 16px;
            border: 1px solid var(--color-border);
            border-radius: var(--radius-sm);
            background: var(--color-surface);
            color: var(--color-text);
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-header:hover {
            background: var(--color-surface-alt);
            border-color: var(--color-neutral-light);
        }

        .btn-header:active {
            transform: scale(0.98);
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
            margin-bottom: 24px;
        }

        .page-header h1 {
            font-size: 28px;
            font-weight: 800;
            color: var(--color-primary);
            margin-bottom: 4px;
            letter-spacing: -0.5px;
        }

        .page-header p {
            color: var(--color-text-secondary);
            font-size: 15px;
        }

        .page-header .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-top: 8px;
        }

        .badge-syncing {
            background: var(--color-success-light);
            color: var(--color-success);
        }

        .badge-syncing .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--color-success);
            animation: pulse-dot 1.5s infinite;
        }

        .badge-error {
            background: var(--color-danger-light);
            color: var(--color-danger);
        }

        .badge-error .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--color-danger);
            animation: pulse-dot 1s infinite;
        }

        /* ============================================
           STATS BAR
           ============================================ */
        .stats-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .stat-card {
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            padding: 20px;
            box-shadow: var(--shadow-sm);
            transition: var(--transition);
        }

        .stat-card:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }

        .stat-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .stat-card-title {
            font-size: 13px;
            font-weight: 600;
            color: var(--color-text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-card-icon {
            width: 36px;
            height: 36px;
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }

        .stat-card-icon.success {
            background: var(--color-success-light);
            color: var(--color-success);
        }

        .stat-card-icon.warning {
            background: var(--color-warning-light);
            color: var(--color-warning);
        }

        .stat-card-icon.error {
            background: var(--color-danger-light);
            color: var(--color-danger);
        }

        .stat-card-icon.info {
            background: var(--color-info-light);
            color: var(--color-info);
        }

        .stat-card-icon.sync {
            background: var(--color-primary-light);
            color: var(--color-primary);
        }

        .stat-card-value {
            font-size: 28px;
            font-weight: 800;
            color: var(--color-text);
            line-height: 1;
        }

        .stat-card-sub {
            font-size: 13px;
            color: var(--color-text-muted);
            margin-top: 4px;
        }

        /* ============================================
           GRID LAYOUT
           ============================================ */
        .grid-2 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 24px;
            margin-bottom: 24px;
        }

        .grid-3 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 24px;
            margin-bottom: 24px;
        }

        .grid-4 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 24px;
        }

        /* ============================================
           CARDS
           ============================================ */
        .card {
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-sm);
            overflow: hidden;
            transition: var(--transition);
        }

        .card:hover {
            box-shadow: var(--shadow-md);
        }

        .card-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--color-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .card-title {
            font-size: 16px;
            font-weight: 700;
            color: var(--color-text);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-title .icon {
            font-size: 18px;
        }

        .card-actions {
            display: flex;
            gap: 8px;
        }

        .btn-sm {
            padding: 6px 14px;
            border: 1px solid var(--color-border);
            border-radius: var(--radius-sm);
            background: var(--color-surface);
            color: var(--color-text-secondary);
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .btn-sm:hover {
            border-color: var(--color-neutral-light);
            color: var(--color-text);
        }

        .btn-sm:active {
            transform: scale(0.98);
        }

        .btn-sm.primary {
            background: var(--color-primary);
            color: white;
            border-color: var(--color-primary);
        }

        .btn-sm.primary:hover {
            background: var(--color-primary-light);
            border-color: var(--color-primary-light);
        }

        .btn-sm.success {
            background: var(--color-success);
            color: white;
            border-color: var(--color-success);
        }

        .btn-sm.success:hover {
            background: var(--color-success-light);
            border-color: var(--color-success-light);
        }

        .btn-sm.warning {
            background: var(--color-warning);
            color: white;
            border-color: var(--color-warning);
        }

        .btn-sm.warning:hover {
            background: var(--color-warning-light);
            border-color: var(--color-warning-light);
        }

        .btn-sm.error {
            background: var(--color-danger);
            color: white;
            border-color: var(--color-danger);
        }

        .btn-sm.error:hover {
            background: var(--color-danger-light);
            border-color: var(--color-danger-light);
        }

        .card-body {
            padding: 24px;
        }

        /* ============================================
           CONNECTION STATUS CARDS
           ============================================ */
        .connection-card {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .connection-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .connection-card-title {
            font-size: 16px;
            font-weight: 700;
            color: var(--color-text);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .connection-card-title .icon {
            font-size: 18px;
        }

        .connection-card-status {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .connection-card-status.connected {
            background: var(--color-success-light);
            color: var(--color-success);
        }

        .connection-card-status.connected .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--color-success);
           