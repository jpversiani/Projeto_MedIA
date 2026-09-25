```html:backend/app/static/sync_status.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sincronização ACS — MedIA</title>
    <style>
        /* ===== RESET & BASE ===== */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
            --bg-primary: #0a0e17;
            --bg-card: #111827;
            --bg-card-hover: #1a2235;
            --bg-input: #1a2235;
            --border: #1e2a40;
            --border-light: #2a3a55;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-blue: #3b82f6;
            --accent-blue-light: #60a5fa;
            --accent-green: #10b981;
            --accent-green-light: #34d399;
            --accent-red: #ef4444;
            --accent-red-light: #fca5a5;
            --accent-yellow: #f59e0b;
            --accent-yellow-light: #fbbf24;
            --accent-purple: #8b5cf6;
            --accent-purple-light: #c084fc;
            --accent-orange: #f97316;
            --accent-orange-light: #fb923c;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
            --shadow-lg: 0 8px 30px rgba(0,0,0,0.5);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
        }

        /* ===== HEADER ===== */
        .header {
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            border-bottom: 1px solid var(--border);
            padding: 0 24px;
            height: 64px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(12px);
            background: rgba(13, 17, 23, 0.95);
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .header-brand-icon {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: 700;
            color: white;
        }

        .header-brand-text h1 {
            font-size: 18px;
            font-weight: 700;
            color: var(--text-primary);
        }

        .header-brand-text span {
            font-size: 11px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            background: var(--bg-card);
            color: var(--text-primary);
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
            font-family: inherit;
        }

        .btn:hover {
            background: var(--bg-card-hover);
            border-color: var(--border-light);
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-blue), #2563eb);
            border-color: transparent;
            color: white;
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, var(--accent-blue-light), #3b82f6);
        }

        .btn-success {
            background: linear-gradient(135deg, var(--accent-green), #059669);
            border-color: transparent;
            color: white;
        }

        .btn-success:hover {
            background: linear-gradient(135deg, var(--accent-green-light), #10b981);
        }

        .btn-danger {
            background: linear-gradient(135deg, var(--accent-red), #dc2626);
            border-color: transparent;
            color: white;
        }

        .btn-danger:hover {
            background: linear-gradient(135deg, var(--accent-red-light), #ef4444);
        }

        .btn-sm {
            padding: 6px 12px;
            font-size: 12px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }

        .status-dot.online { background: var(--accent-green); box-shadow: 0 0 6px var(--accent-green); }
        .status-dot.offline { background: var(--accent-red); box-shadow: 0 0 6px var(--accent-red); }
        .status-dot.syncing { background: var(--accent-yellow); box-shadow: 0 0 6px var(--accent-yellow); }
        .status-dot.error { background: var(--accent-orange); box-shadow: 0 0 6px var(--accent-orange); }

        /* ===== MAIN LAYOUT ===== */
        .main {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
        }

        .page-header {
            margin-bottom: 24px;
        }

        .page-header h2 {
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .page-header p {
            color: var(--text-secondary);
            font-size: 14px;
        }

        .page-header .meta {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-top: 8px;
            font-size: 13px;
            color: var(--text-muted);
        }

        .page-header .meta span {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        /* ===== GRID LAYOUT ===== */
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        @media (max-width: 900px) {
            .grid { grid-template-columns: 1fr; }
        }

        /* ===== CARDS ===== */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 20px;
            transition: var(--transition);
        }

        .card:hover {
            border-color: var(--border-light);
            transform: translateY(-1px);
        }

        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }

        .card-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .card-title .icon {
            font-size: 16px;
        }

        .card-subtitle {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 2px;
        }

        .card-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 16px;
            padding-top: 12px;
            border-top: 1px solid var(--border);
        }

        .card-footer-text {
            font-size: 12px;
            color: var(--text-muted);
        }

        .card-footer-actions {
            display: flex;
            gap: 8px;
        }

        /* ===== CONNECTION STATUS CARDS ===== */
        .connection-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
        }

        .connection-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 20px;
            transition: var(--transition);
            position: relative;
            overflow: hidden;
        }

        .connection-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            border-radius: var(--radius-md) var(--radius-md) 0 0;
        }

        .connection-card.acs::before { background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple)); }
        .connection-card.acs.status-online::before { background: linear-gradient(90deg, var(--accent-green), #059669); }
        .connection-card.acs.status-syncing::before { background: linear-gradient(90deg, var(--accent-yellow), var(--accent-orange)); }
        .connection-card.acs.status-error::before { background: linear-gradient(90deg, var(--accent-red), #dc2626); }
        .connection-card.c5::before { background: linear-gradient(90deg, var(--accent-purple), var(--accent-blue)); }
        .connection-card.c5.status-online::before { background: linear-gradient(90deg, var(--accent-green), #059669); }
        .connection-card.c5.status-syncing::before { background: linear-gradient(90deg, var(--accent-yellow), var(--accent-orange)); }
        .connection-card.c5.status-error::before { background: linear-gradient(90deg, var(--accent-red), #dc2626); }

        .connection-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }

        .connection-card-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .connection-card-status {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }

        .connection-card-status.online {
            background: rgba(16, 185, 129, 0.1);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.2);
        }

        .connection-card-status.syncing {
            background: rgba(245, 158, 11, 0.1);
            color: var(--accent-yellow);
            border: 1px solid rgba(245, 158, 11, 0.2);
        }

        .connection-card-status.error {
            background: rgba(239, 68, 68, 0.1);
            color: var(--accent-red);
            border: 1px solid rgba(239, 68, 68, 0.2);
        }

        .connection-card-status.offline {
            background: rgba(239, 68, 68, 0.1);
            color: var(--accent-red);
            border: 1px solid rgba(239, 68, 68, 0.2);
        }

        .connection-card-body {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .connection-detail {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
        }

        .connection-detail:last-child {
            border-bottom: none;
        }

        .connection-detail-label {
            font-size: 12px;
            color: var(--text-muted);
        }

        .connection-detail-value {
            font-size: 13px;
            font-weight: 500;
            color: var(--text-primary);
        }

        .connection-detail-value.success { color: var(--accent-green); }
        .connection-detail-value.warning { color: var(--accent-yellow); }
        .connection-detail-value.error { color: var(--accent-red); }

        .connection-card-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 16px;
            padding-top: 12px;
            border-top: 1px solid var(--border);
        }

        .connection-card-footer-text {
            font-size: 12px;
            color: var(--text-muted);
        }

        .connection-card-footer-actions {
            display: flex;
            gap: 8px;
        }

        .connection-card-status-bar {
            margin-top: 12px;
        }

        .status-bar-label {
            display: flex;
