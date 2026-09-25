# Dashboard de Monitoramento de Remessas do SISAB (C92)

## Arquivo: `backend/app/static/monitor_sisab.html`

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor SISAB (C92) - Remessas</title>
    <link href="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root {
            --sisab-blue: #0d6efd;
            --sisab-dark: #0a5697;
            --sisab-light: #e2e8f0;
            --sisab-accent: #1977f2;
            --sisab-success: #10b981;
            --sisab-danger: #dc2626;
            --sisab-warning: #f59e0b;
            --sisab-info: #06b6d4;
            --sisab-bg: #f8fafc;
            --sisab-card: #ffffff;
            --sisab-text: #1e293b;
            --sisab-text-light: #64748b;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: var(--sisab-bg);
            color: var(--sisab-text);
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            min-height: 100vh;
        }

        .navbar {
            background: linear-gradient(135deg, var(--sisab-blue) 0%, var(--sisab-dark) 100%);
            color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .navbar-brand {
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .navbar-brand i {
            margin-right: 0.5rem;
            font-size: 1.3rem;
        }

        .navbar-brand span {
            color: var(--sisab-accent);
        }

        .navbar-nav .nav-link {
            color: rgba(255,255,255,0.9);
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            transition: all 0.2s;
        }

        .navbar-nav .nav-link:hover {
            background: rgba(255,255,255,0.15);
        }

        .navbar-nav .nav-link.active {
            background: rgba(255,255,255,0.2);
            color: white;
        }

        .main-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }

        .page-header {
            background: var(--sisab-card);
            border-radius: 12px;
            padding: 1.5rem 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .page-header h1 {
            font-size: 1.75rem;
            color: var(--sisab-blue);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .page-header h1 i {
            font-size: 1.5rem;
        }

        .page-header .subtitle {
            font-size: 0.9rem;
            color: var(--sisab-text-light);
            margin-top: 0.25rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: var(--sisab-card);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            transition: transform 0.2s, box-shadow 0.2s;
            border: 1px solid rgba(0,0,0,0.05);
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }

        .stat-card .stat-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            margin-bottom: 1rem;
        }

        .stat-card .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--sisab-blue);
        }

        .stat-card .stat-label {
            font-size: 0.85rem;
            color: var(--sisab-text-light);
            margin-top: 0.25rem;
        }

        .stat-card .stat-change {
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 0.5rem;
            font-size: 0.75rem;
            font-weight: 600;
            margin-top: 0.5rem;
        }

        .stat-card .stat-change.positive {
            background: rgba(16, 185, 129, 0.1);
            color: var(--sisab-success);
        }

        .stat-card .stat-change.negative {
            background: rgba(220, 38, 38, 0.1);
            color: var(--sisab-danger);
        }

        .stat-card .stat-change.neutral {
            background: rgba(149, 160, 237, 0.1);
            color: #6366f1;
        }

        .stat-card .stat-change.positive i { color: var(--sisab-success); }
        .stat-card .stat-change.negative i { color: var(--sisab-danger); }
        .stat-card .stat-change.neutral i { color: #6366f1; }

        .card-icon-success { background: rgba(16, 185, 129, 0.1); color: var(--sisab-success); }
        .card-icon-danger { background: rgba(220, 38, 38, 0.1); color: var(--sisab-danger); }
        .card-icon-warning { background: rgba(245, 158, 11, 0.1); color: var(--sisab-warning); }
        .card-icon-info { background: rgba(6, 182, 212, 0.1); color: var(--sisab-info); }
        .card-icon-primary { background: rgba(13, 110, 253, 0.1); color: var(--sisab-blue); }

        .chart-container {
            background: var(--sisab-card);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            margin-bottom: 2rem;
            border: 1px solid rgba(0,0,0,0.05);
        }

        .chart-container h3 {
            font-size: 1.25rem;
            color: var(--sisab-blue);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .chart-container h3 i {
            color: var(--sisab-accent);
        }

        .chart-wrapper {
            position: relative;
            height: 350px;
        }

        .table-container {
            background: var(--sisab-card);
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            border: 1px solid rgba(0,0,0,0.05);
            overflow: hidden;
        }

        .table-container h3 {
            font-size: 1.25rem;
            color: var(--sisab-blue);
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--sisab-light);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .table-container h3 i {
            color: var(--sisab-accent);
        }

        .table-responsive {
            overflow-x: auto;
        }

        table thead th {
            background: var(--sisab-light);
            font-weight: 600;
            color: var(--sisab-text);
            padding: 0.75rem 1rem;
            text-align: left;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05px;
        }

        table tbody tr {
            transition: background 0.2s;
        }

        table tbody tr:hover {
            background: var(--sisab-light);
        }

        table tbody tr:last-child td {
            border-bottom: none;
        }

        table tbody td {
            padding: 0.75rem 1rem;
            font-size: 0.9rem;
            border-bottom: 1px solid rgba(0,0,0,0.04);
        }

        .badge {
            padding: 0.25rem 0.6rem;
            border-radius: 0.5rem;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .badge-success {
            background: rgba(16, 185, 129, 0.1);
            color: var(--sisab-success);
        }

        .badge-danger {
            background: rgba(220, 38, 38, 0.1);
            color: var(--sisab-danger);
        }

        .badge-warning {
            background: rgba(245, 158, 11, 0.1);
            color: var(--sisab-warning);
        }

        .badge-info {
            background: rgba(6, 182, 212, 0.1);
            color: var(--sisab-info);
        }

        .badge-primary {
            background: rgba(13, 110, 253, 0.1);
            color: var(--sisab-blue);
        }

        .badge-secondary {
            background: rgba(148, 163, 184, 0.1);
            color: #475569;
        }

        .badge-cyano {
            background: rgba(6, 182, 212, 0.1);
            color: var(--sisab-info);
        }

        .badge-purple {
            background: rgba(149, 160, 237, 0.1);
            color: #6366f1;
        }

        .badge-orange {
            background: rgba(249, 115, 22, 0.1);
            color: #ea580c;
        }

        .badge-red {
            background: rgba(220, 38, 38, 0.1);
            color: var(--sisab-danger);
        }

        .badge-green {
            background: rgba(16, 185, 129, 0.1);
            color: var(--sisab-success);
        }

        .badge-yellow {
            background: rgba(245, 158, 11, 0.1);
            color: var(--sisab-warning);
        }

        .badge-blue {
            background: rgba(13, 110, 253, 0.1);
            color: var(--sisab-blue);
        }

        .badge-teal {
            background: rgba(14, 162, 147, 0.1);
            color: #059669;
        }

        .badge-indigo {
            background: rgba(119, 130, 246, 0.1);
            color: #4338ca;
        }

        .badge-pink {
            background: rgba(236, 72, 153, 0.1);
            color: #db2777;
        }

        .badge-violet {
            background: rgba(168, 85, 247, 0.1);
            color: #7c3aed;
        }

        .badge-slate {
            background: rgba(148, 163, 184, 0.1);
            color: #475569;
        }

        .badge-bronze {
            background: rgba(249, 115, 22, 0.1);
            color: #ea580c;
        }

        .badge-silver {
            background: rgba(148, 163, 184, 0.1);
            color: #