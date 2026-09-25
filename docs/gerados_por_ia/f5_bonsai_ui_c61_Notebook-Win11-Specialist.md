```html:backend/app/static/sync_status.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sincronização ACS — Atenção Domiciliar</title>
    <style>
        /* ===== CSS RESET & BASE ===== */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
            --bg-primary: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --accent-blue: #3b82f6;
            --accent-blue-light: #60a5fa;
            --accent-green: #10b981;
            --accent-green-light: #34d399;
            --accent-red: #ef4444;
            --accent-red-light: #fca5a5;
            --accent-yellow: #f59e0b;
            --accent-yellow-light: #fde047;
            --accent-purple: #8b5cf6;
            --accent-purple-light: #c084fc;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border-color: #334155;
            --radius: 12px;
            --shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
            --shadow-hover: 0 8px 32px rgba(0, 0, 0, 0.4);
            --transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
        }

        /* ===== HEADER ===== */
        .page-header {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-bottom: 1px solid var(--border-color);
            padding: 24px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 16px;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(10px);
        }

        .page-header h1 {
            font-size: 1.5rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .page-header h1 .icon {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
        }

        .page-header h1 span {
            color: var(--accent-blue-light);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-blue), #2563eb);
            color: white;
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, var(--accent-blue-light), #3b82f6);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }

        .btn-secondary {
            background: var(--bg-card);
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            background: var(--bg-card-hover);
            border-color: var(--accent-blue);
        }

        .btn-danger {
            background: linear-gradient(135deg, var(--accent-red), #dc2626);
            color: white;
        }

        .btn-danger:hover {
            background: linear-gradient(135deg, var(--accent-red-light), #ef4444);
            transform: translateY(-1px);
        }

        .btn-sm {
            padding: 6px 14px;
            font-size: 0.8rem;
        }

        /* ===== STAT BAR ===== */
        .stat-bar {
            background: var(--bg-card);
            border-bottom: 1px solid var(--border-color);
            padding: 16px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 16px;
        }

        .stat-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.9rem;
        }

        .stat-item .stat-icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
        }

        .stat-item .stat-value {
            font-weight: 700;
            font-size: 1.1rem;
        }

        .stat-item .stat-label {
            color: var(--text-muted);
            font-size: 0.8rem;
        }

        .stat-item.connected .stat-icon {
            background: rgba(16, 185, 129, 0.2);
            color: var(--accent-green);
        }

        .stat-item.disconnected .stat-icon {
            background: rgba(239, 68, 68, 0.2);
            color: var(--accent-red);
        }

        .stat-item.syncing .stat-icon {
            background: rgba(245, 158, 11, 0.2);
            color: var(--accent-yellow);
        }

        .stat-item.error .stat-icon {
            background: rgba(239, 68, 68, 0.2);
            color: var(--accent-red);
        }

        .stat-item.syncing .stat-value {
            color: var(--accent-yellow);
        }

        .stat-item.error .stat-value {
            color: var(--accent-red);
        }

        .stat-item.connected .stat-value {
            color: var(--accent-green);
        }

        /* ===== MAIN CONTENT ===== */
        .main-content {
            padding: 32px 40px;
            max-width: 1400px;
            margin: 0 auto;
        }

        /* ===== SECTION TITLE ===== */
        .section-title {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .section-title .section-icon {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
        }

        /* ===== GRID LAYOUT ===== */
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 32px;
        }

        @media (max-width: 900px) {
            .grid { grid-template-columns: 1fr; }
        }

        /* ===== CARD ===== */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 24px;
            transition: var(--transition);
            box-shadow: var(--shadow);
        }

        .card:hover {
            border-color: var(--accent-blue);
            box-shadow: var(--shadow-hover);
        }

        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }

        .card-title {
            font-size: 1.1rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-title .card-icon {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
        }

        .card-title .card-icon.blue {
            background: rgba(59, 130, 246, 0.2);
            color: var(--accent-blue-light);
        }

        .card-title .card-icon.green {
            background: rgba(16, 185, 129, 0.2);
            color: var(--accent-green-light);
        }

        .card-title .card-icon.red {
            background: rgba(239, 68, 68, 0.2);
            color: var(--accent-red-light);
        }

        .card-title .card-icon.yellow {
            background: rgba(245, 158, 11, 0.2);
            color: var(--accent-yellow-light);
        }

        .card-title .card-icon.purple {
            background: rgba(139, 92, 246, 0.2);
            color: var(--accent-purple-light);
        }

        .card-status {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .card-status .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }

        .card-status.connected .status-dot {
            background: var(--accent-green);
            animation: pulse-green 2s infinite;
        }

        .card-status.disconnected .status-dot {
            background: var(--accent-red);
        }

        .card-status.syncing .status-dot {
            background: var(--accent-yellow);
            animation: pulse-yellow 2s infinite;
        }

        .card-status.error .status-dot {
            background: var(--accent-red);
        }

        .card-status.success .status-dot {
            background: var(--accent-green);
        }

        .card-status.warning .status-dot {
            background: var(--accent-yellow);
        }

        .card-status .status-label {
            color: var(--text-secondary);
        }

        .card-status.connected .status-label { color: var(--accent-green); }
        .card-status.disconnected .status-label { color: var(--accent-red); }
        .card-status.syncing .status-label { color: var(--accent-yellow); }
        .card-status.error .status-label { color: var(--accent-red); }
        .card-status.success .status-label { color: var(--accent-green); }
        .card-status.warning .status-label { color: var(--accent-yellow); }

        @keyframes pulse-green {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        @keyframes pulse-yellow {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* ===== CONNECTION STATUS CARDS ===== */
        .connection-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        @media (max-width: 600px) {
            .connection-grid { grid-template-columns: 1fr; }
        }

        .connection-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            transition: var(--transition);
        }

        .connection-card:hover {
            border-color: var(--accent-blue);
            transform: translateY(-2px);
        }

        .connection-card .conn-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            flex-shrink: 0;
        }

        .connection-card .conn-icon.accent-blue {
            background: rgba(59, 130, 246, 0.15);
            color: var(--accent-blue-light);
        }

        .connection-card .conn-icon.accent-green {
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green-light);
        }

        .connection-card .conn-icon.accent-red {
            background: rgba(239, 68, 68, 0.15);
            color: var(--accent-red-light);
        }

        .connection-card .conn-icon.accent-yellow {
            background: rgba(245, 158, 11, 0.15);
            color: var(--accent-yellow-light);
        }

        .connection-card .conn-info {
            flex: 1;
        }

        .connection-card .conn-name {
            font-weight: 700;
            font-size: 