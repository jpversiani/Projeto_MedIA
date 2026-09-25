```html:backend/app/static/sync_status.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sync Status — Atenção Domicilar</title>
    <style>
        /* ── Reset & Base ──────────────────────────────────── */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
            --bg:          #0f1117;
            --surface:     #1a1d27;
            --surface2:    #232833;
            --border:      #2e3545;
            --text:        #e2e8f0;
            --text-muted:  #94a3b8;
            --accent:      #3b82f6;
            --accent-glow: rgba(59, 130, 246, .15);
            --success:     #10b981;
            --success-glow: rgba(16, 185, 129, .15);
            --warning:     #f59e0b;
            --warning-glow: rgba(245, 158, 11, .15);
            --danger:      #ef4444;
            --danger-glow: rgba(239, 68, 68, .15);
            --radius:      12px;
            --font:        'Segoe UI', system-ui, -apple-system, sans-serif;
        }

        body {
            font-family: var(--font);
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.5;
        }

        /* ── Header ────────────────────────────────────────── */
        .header {
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(12px);
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: .75rem;
        }

        .header-brand .logo {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, var(--accent), #8b5cf6);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.1rem;
            color: #fff;
        }

        .header-brand h1 {
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -.02em;
        }

        .header-brand h1 span { color: var(--accent); }

        .header-actions {
            display: flex;
            gap: .5rem;
            align-items: center;
        }

        .btn {
            padding: .5rem 1rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface2);
            color: var(--text);
            font-size: .85rem;
            font-weight: 500;
            cursor: pointer;
            transition: all .2s;
            font-family: inherit;
        }

        .btn:hover { border-color: var(--accent); color: var(--accent); }

        .btn-primary {
            background: var(--accent);
            border-color: var(--accent);
            color: #fff;
        }

        .btn-primary:hover { opacity: .9; }

        .btn-danger { border-color: var(--danger); color: var(--danger); }
        .btn-danger:hover { background: var(--danger-glow); }

        .btn-success { border-color: var(--success); color: var(--success); }
        .btn-success:hover { background: var(--success-glow); }

        /* ── Main Layout ───────────────────────────────────── */
        .main {
            max-width: 1200px;
            margin: 0 auto;
            padding: 1.5rem 2rem;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }

        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
        }

        /* ── Card ──────────────────────────────────────────── */
        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.25rem;
            transition: border-color .2s;
        }

        .card:hover { border-color: var(--accent); }

        .card-title {
            font-size: .9rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: .06em;
            color: var(--text-muted);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: .5rem;
        }

        .card-title .icon {
            font-size: 1.1rem;
        }

        /* ── Connection Status Cards ───────────────────────── */
        .conn-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: .75rem;
        }

        .conn-card {
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1rem;
            text-align: center;
            transition: all .3s;
        }

        .conn-card:hover { transform: translateY(-2px); }

        .conn-card .status-icon {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            margin: 0 auto .6rem;
        }

        .conn-card.connected .status-icon {
            background: var(--success-glow);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, .3);
        }

        .conn-card.syncing .status-icon {
            background: var(--warning-glow);
            color: var(--warning);
            border: 1px solid rgba(245, 158, 11, .3);
            animation: pulse 1.5s infinite;
        }

        .conn-card.disconnected .status-icon {
            background: var(--danger-glow);
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, .3);
        }

        .conn-card .status-label {
            font-size: .8rem;
            font-weight: 600;
            margin-bottom: .25rem;
        }

        .conn-card.connected .status-label { color: var(--success); }
        .conn-card.syncing .status-label { color: var(--warning); }
        .conn-card.disconnected .status-label { color: var(--danger); }

        .conn-card .status-detail {
            font-size: .75rem;
            color: var(--text-muted);
        }

        .conn-card .last-sync {
            font-size: .7rem;
            color: var(--text-muted);
            margin-top: .4rem;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50%      { opacity: .4; }
        }

        /* ── Upload Progress ───────────────────────────────── */
        .upload-list {
            display: flex;
            flex-direction: column;
            gap: .75rem;
        }

        .upload-item {
            display: flex;
            align-items: center;
            gap: .75rem;
            padding: .75rem;
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: var(--radius);
        }

        .upload-item .file-info {
            flex: 1;
            min-width: 0;
        }

        .upload-item .file-name {
            font-size: .85rem;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .upload-item .file-meta {
            font-size: .75rem;
            color: var(--text-muted);
            margin-top: .15rem;
        }

        .upload-item .progress-track {
            flex: 1;
            min-width: 100px;
            height: 6px;
            background: var(--surface);
            border-radius: 3px;
            overflow: hidden;
        }

        .upload-item .progress-fill {
            height: 100%;
            border-radius: 3px;
            transition: width .4s ease;
        }

        .upload-item .progress-fill.done { background: var(--success); }
        .upload-item .progress-fill.active { background: var(--accent); }
        .upload-item .progress-fill.error { background: var(--danger); }

        .upload-item .progress-pct {
            font-size: .75rem;
            color: var(--text-muted);
            min-width: 48px;
            text-align: right;
        }

        .upload-item .upload-status {
            font-size: .75rem;
            font-weight: 600;
            padding: .2rem .6rem;
            border-radius: 20px;
        }

        .upload-status.success {
            background: var(--success-glow);
            color: var(--success);
        }

        .upload-status.active {
            background: var(--accent-glow);
            color: var(--accent);
        }

        .upload-status.error {
            background: var(--danger-glow);
            color: var(--danger);
        }

        /* ── Transmission Log ──────────────────────────────── */
        .log-list {
            display: flex;
            flex-direction: column;
            gap: .5rem;
        }

        .log-entry {
            display: flex;
            align-items: flex-start;
            gap: .75rem;
            padding: .65rem .85rem;
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            transition: border-color .2s;
        }

        .log-entry:hover { border-color: var(--accent); }

        .log-entry .log-time {
            font-size: .7rem;
            color: var(--text-muted);
            flex-shrink: 0;
        }

        .log-entry .log-icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: .85rem;
            flex-shrink: 0;
        }

        .log-entry.success .log-icon {
            background: var(--success-glow);
            color: var(--success);
        }

        .log-entry.warning .log-icon {
            background: var(--warning-glow);
            color: var(--warning);
        }

        .log-entry.error .log-icon {
            background: var(--danger-glow);
            color: var(--danger);
        }

        .log-entry .log-body {
            flex: 1;
            min-width: 0;
        }

        .log-entry .log-text {
            font-size: .82rem;
            color: var(--text);
        }

        .log-entry .log-text strong { color: var(--accent); }

        .log-entry .log-body .log-ref {
            font-size: .7rem;
            color: var(--text-muted);
            margin-top: .2rem;
        }

        /* ── Scrollbar ─────────────────────────────────────── */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg); }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--accent); }

        /* ── Footer ────────────────────────────────────────── */
        .footer {
            text-align: center;
            padding: 1.5rem;
            font-size: .75rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border);
            margin-top: 2rem;
        }

        .footer a { color: var(--accent); text-decoration: none; }
        .footer a:hover { text-decoration: underline; }
    </style>
</head>
<body>

<!-- ═══════════════════════════════════════════════════════ -->
<!-- Header                                               -->
<!-- ═══════════════════════════════════════════════════════ -->
<header class="header">
    <div class="header-brand">
        <div class="logo">M</div>
        <h1>MedIA <span>Sync</span></h1>
    </div>
    <div class="header-actions">
        <span id="connection-badge" style="font-size:.8rem;padding:.35rem .8rem;border-radius:20px;background:var(--success-glow);color:var(--success);font-weight:600;">● Conectado</span>
        <button class="btn btn-primary" onclick="refreshAll()">🔄 Atualizar</button>
        <button class="btn btn-danger" onclick="disconnectAll()">⚠ Desconectar</button>
    </div>
</header>

<!-- ═══════════════════════════════════════════════════════ -->
<!-- Main Content                                         -->
<!-- ═══════════════════════════════════════════════════════ -->
<main class="main">

    <!-- ── Connection Status Cards ───────────────────────── -->
    <div class="grid">
        <div class="card">
            <div class="card-title"><span class="icon">📡</span> Conexão ACS</div>
            <div class="conn-grid">
                <div class="conn-card connected" id="conn-acs">
                    <div class="