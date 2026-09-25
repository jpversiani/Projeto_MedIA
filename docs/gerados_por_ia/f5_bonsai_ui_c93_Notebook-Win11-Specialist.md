```html:backend/app/static/sync_status.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sincronização ACS — MedIA</title>
    <style>
        /* ===== CSS RESET & VARIABLES ===== */
        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #111827;
            --bg-card: #1a2236;
            --bg-card-hover: #222b44;
            --border-color: #2a3350;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --accent-blue: #3b82f6;
            --accent-blue-light: #60a5fa;
            --accent-green: #10b981;
            --accent-green-light: #34d399;
            --accent-red: #ef4444;
            --accent-red-light: #fca5a5;
            --accent-yellow: #f59e0b;
            --accent-yellow-light: #fef3c7;
            --accent-purple: #8b5cf6;
            --accent-purple-light: #c084fc;
            --accent-orange: #f97316;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
            --shadow-md: 0 4px 20px rgba(0,0,0,0.4);
            --shadow-lg: 0 8px 40px rgba(0,0,0,0.5);
            --radius: 12px;
            --radius-sm: 8px;
            --transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
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
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
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

        .header-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .header-brand-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: 700;
            color: white;
        }

        .header-brand-text h1 {
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .header-brand-text h1 span {
            color: var(--accent-blue);
        }

        .header-brand-text p {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .btn {
            padding: 8px 16px;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            background: var(--bg-card);
            color: var(--text-primary);
            font-size: 0.85rem;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn:hover {
            background: var(--bg-card-hover);
            border-color: var(--accent-blue);
            color: var(--accent-blue-light);
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            border: none;
            color: white;
            font-weight: 600;
        }

        .btn-primary:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }

        .btn-danger {
            border-color: var(--accent-red);
            color: var(--accent-red-light);
        }

        .btn-danger:hover {
            background: rgba(239, 68, 68, 0.1);
        }

        .live-indicator {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 20px;
            font-size: 0.75rem;
            color: var(--accent-green);
        }

        .live-indicator .dot {
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
        .main {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px 32px;
        }

        .page-header {
            margin-bottom: 24px;
        }

        .page-header h2 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .page-header p {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        /* ===== STATS BAR ===== */
        .stats-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 20px;
            transition: var(--transition);
        }

        .stat-card:hover {
            border-color: var(--accent-blue);
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .stat-card .stat-label {
            font-size: 0.8rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }

        .stat-card .stat-value {
            font-size: 1.8rem;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
        }

        .stat-card .stat-sub {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }

        .stat-card .stat-change {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 12px;
            margin-top: 8px;
        }

        .stat-change.up {
            color: var(--accent-green);
            background: rgba(16, 185, 129, 0.1);
        }

        .stat-change.down {
            color: var(--accent-red);
            background: rgba(239, 68, 68, 0.1);
        }

        /* ===== GRID LAYOUT ===== */
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }

        @media (max-width: 1024px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }

        /* ===== CARDS ===== */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            overflow: hidden;
            transition: var(--transition);
        }

        .card:hover {
            border-color: rgba(59, 130, 246, 0.3);
        }

        .card-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .card-header h3 {
            font-size: 1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-header h3 .icon {
            font-size: 1.2rem;
        }

        .card-header .badge {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .badge-online {
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
        }

        .badge-offline {
            background: rgba(239, 68, 68, 0.15);
            color: var(--accent-red-light);
        }

        .badge-pending {
            background: rgba(245, 158, 11, 0.15);
            color: var(--accent-yellow);
        }

        .badge-error {
            background: rgba(239, 68, 68, 0.15);
            color: var(--accent-red-light);
        }

        .card-body {
            padding: 20px;
        }

        /* ===== CONNECTION STATUS CARDS ===== */
        .connection-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
        }

        .connection-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
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
            border-radius: var(--radius) var(--radius) 0 0;
        }

        .connection-card.online::before {
            background: var(--accent-green);
        }

        .connection-card.offline::before {
            background: var(--accent-red);
        }

        .connection-card.pending::before {
            background: var(--accent-yellow);
        }

        .connection-card.error::before {
            background: var(--accent-red);
        }

        .connection-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .connection-card .conn-status {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }

        .connection-card .conn-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .connection-card .conn-status-icon {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }

        .connection-card.online .conn-status-icon {
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
        }

        .connection-card.offline .conn-status-icon {
            background: rgba(239, 68, 68, 0.15);
            color: var(--accent-red-light);
        }

        .connection-card.pending .conn-status-icon {
            background: rgba(245, 158, 11, 0.15);
            color: var(--accent-yellow);
        }

        .connection-card.error .conn-status-icon {
            background: rgba(239, 68, 68, 0.15);
            color: var(--accent-red-light);
        }

        .connection-card .conn-details {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .connection-card .conn-detail {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }

        .connection-card .conn-detail:last-child {
            border-bottom: none;
        }

        .connection-card .conn-detail-label {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        .connection-card .conn-detail-value {
            font-size: 0.85rem;
            font-weight: 500;
        }

        .connection-card .conn-detail-value.cns {
            color: var(--accent-blue);
            font-family: monospace;
        }

        .connection-card .conn-detail-value.cid {
            color: var(--accent-purple);
        }

        .connection-card .conn-detail-value.cip {
            color: var(--accent-orange);
        }

        .connection-card .conn-detail-value.cpf {
           