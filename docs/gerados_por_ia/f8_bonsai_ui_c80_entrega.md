```html:backend/app/static/campanhas_saude.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Campanhas de Busca Ativa — MedIA | ACS</title>
    <style>
        /* ===== RESET & BASE ===== */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
            --color-primary: #0056b3;
            --color-primary-dark: #003d80;
            --color-primary-light: #e3f2fd;
            --color-accent: #1976d2;
            --color-success: #2e7d32;
            --color-success-light: #e8f5e9;
            --color-warning: #f57c00;
            --color-warning-light: #fff3e0;
            --color-danger: #c62828;
            --color-danger-light: #ffebee;
            --color-info: #1565c0;
            --color-info-light: #e3f2fd;
            --color-neutral: #757575;
            --color-neutral-light: #e0e0e0;
            --color-white: #ffffff;
            --color-gray-50: #f5f5f5;
            --color-gray-100: #e3e3e3;
            --color-gray-200: #d1d1d1;
            --color-gray-300: #b0b0b0;
            --color-gray-400: #787878;
            --color-gray-500: #525252;
            --color-gray-600: #374151;
            --color-gray-700: #292929;
            --color-gray-800: #1a1a1a;
            --color-gray-900: #0d0d0d;
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.12);
            --shadow-lg: 0 8px 24px rgba(0,0,0,0.16);
            --shadow-xl: 0 12px 40px rgba(0,0,0,0.2);
            --transition: all 0.2s ease;
            --font-sans: 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        }

        body {
            font-family: var(--font-sans);
            background: var(--color-gray-50);
            color: var(--color-gray-800);
            line-height: 1.6;
            min-height: 100vh;
        }

        /* ===== HEADER ===== */
        .header {
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
            color: var(--color-white);
            padding: 0 24px;
            height: 72px;
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
            gap: 12px;
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .header-brand .logo-icon {
            width: 36px;
            height: 36px;
            background: rgba(255,255,255,0.2);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }

        .header-brand span {
            white-space: nowrap;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .header-right .user-badge {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(255,255,255,0.15);
            padding: 8px 16px;
            border-radius: var(--radius-md);
            font-size: 0.9rem;
            backdrop-filter: blur(8px);
        }

        .header-right .user-badge .avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: var(--color-accent);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.85rem;
        }

        .header-right .user-badge .info {
            display: flex;
            flex-direction: column;
        }

        .header-right .user-badge .name {
            font-weight: 600;
            font-size: 0.85rem;
        }

        .header-right .user-badge .role {
            font-size: 0.75rem;
            opacity: 0.8;
        }

        .header-right .user-badge .cns-display {
            font-size: 0.7rem;
            color: rgba(255,255,255,0.7);
            margin-top: 2px;
        }

        .header-right .status-indicator {
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(255,255,255,0.15);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            backdrop-filter: blur(8px);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--color-success);
            animation: pulse 2s infinite;
        }

        .status-dot.warning { background: var(--color-warning); }
        .status-dot.danger { background: var(--color-danger); }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        /* ===== MAIN LAYOUT ===== */
        .main-layout {
            display: grid;
            grid-template-columns: 280px 1fr;
            min-height: calc(100vh - 72px);
        }

        /* ===== SIDEBAR ===== */
        .sidebar {
            background: var(--color-white);
            border-right: 1px solid var(--color-gray-200);
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        .sidebar-nav {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .sidebar-nav .nav-section {
            margin-bottom: 16px;
        }

        .sidebar-nav .nav-section-title {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--color-gray-400);
            font-weight: 600;
            padding: 0 12px;
            margin-bottom: 8px;
        }

        .sidebar-nav .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: var(--transition);
            font-size: 0.9rem;
            color: var(--color-gray-600);
            text-decoration: none;
        }

        .sidebar-nav .nav-item:hover {
            background: var(--color-gray-50);
            color: var(--color-primary);
        }

        .sidebar-nav .nav-item.active {
            background: var(--color-primary-light);
            color: var(--color-primary-dark);
            font-weight: 600;
        }

        .sidebar-nav .nav-item .nav-icon {
            width: 24px;
            text-align: center;
            font-size: 1.1rem;
        }

        .sidebar-nav .nav-item .nav-badge {
            margin-left: auto;
            background: var(--color-danger);
            color: white;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 20px;
        }

        .sidebar-nav .nav-item .nav-badge.warning {
            background: var(--color-warning);
        }

        .sidebar-nav .nav-item .nav-badge.info {
            background: var(--color-info);
        }

        .sidebar-nav .nav-item .nav-badge.success {
            background: var(--color-success);
        }

        .sidebar-actions {
            margin-top: auto;
            padding-top: 24px;
            border-top: 1px solid var(--color-gray-200);
        }

        .sidebar-actions .action-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 14px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: var(--transition);
            font-size: 0.85rem;
            color: var(--color-gray-600);
        }

        .sidebar-actions .action-item:hover {
            background: var(--color-gray-50);
        }

        .sidebar-actions .action-item .action-icon {
            width: 24px;
            text-align: center;
        }

        .sidebar-actions .action-item .action-text {
            flex: 1;
        }

        .sidebar-actions .action-item .action-text .action-label {
            font-weight: 500;
        }

        .sidebar-actions .action-item .action-text .action-sub {
            font-size: 0.75rem;
            opacity: 0.7;
        }

        /* ===== CONTENT AREA ===== */
        .content {
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 24px;
            overflow-y: auto;
        }

        /* ===== TOP BAR ===== */
        .top-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            flex-wrap: wrap;
        }

        .top-bar-title {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .top-bar-title .title-icon {
            width: 40px;
            height: 40px;
            background: var(--color-primary-light);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }

        .top-bar-title h1 {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--color-gray-800);
        }

        .top-bar-title .subtitle {
            font-size: 0.85rem;
            color: var(--color-gray-500);
            margin-top: 2px;
        }

        .top-bar-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .top-bar-actions .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            border: none;
            border-radius: var(--radius-md);
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            font-family: var(--font-sans);
        }

        .btn-primary {
            background: var(--color-primary);
            color: var(--color-white);
        }

        .btn-primary:hover {
            background: var(--color-primary-dark);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }

        .btn-secondary {
            background: var(--color-white);
            color: var(--color-gray-600);
            border: 1px solid var(--color-gray-200);
        }

        .btn-secondary:hover {
            border-color: var(--color-gray-300);
            background: var(--color-gray-50);
        }

        .btn-danger {
            background: var(--color-danger);
            color: var(--color-white);
        }

        .btn-danger:hover {
            background: #b01c1c;
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
            font-size: 1.1rem;
        }

        /* ===== FILTERS ===== */
        .filters-bar {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            background: var(--color-white);
            padding: 14px 20px;
            border-radius: var(--radius-md);
            border: 1px solid var(--color-gray-200);
        }

        .filters-bar .filter-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .filters-bar .filter-label {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--color-gray-500);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .filters-bar .filter-input {
            padding: 8px 12px;
            border: 1px solid var(--color-gray-200);
            border-radius: var(--radius-sm);
           