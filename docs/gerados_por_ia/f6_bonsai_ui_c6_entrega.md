```html:backend/app/static/copiloto_card.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Card Copiloto — Prontuário Web</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        /* ─────────────────────────────────────────────
           GLOBAL & THEME
           ───────────────────────────────────────────── */
        :root {
            --color-primary: #0f172a;
            --color-accent: #3b82f6;
            --color-accent-light: #60a5fa;
            --color-success: #10b981;
            --color-warning: #f59e0b;
            --color-danger: #ef4444;
            --color-bg: #f8fafc;
            --color-card: #ffffff;
            --color-border: #e2e8f0;
            --color-text: #0f172a;
            --color-text-muted: #64748b;
            --color-gradient: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: var(--color-bg);
            color: var(--color-text);
            min-height: 100vh;
            line-height: 1.6;
        }

        .font-mono { font-family: 'JetBrains Mono', monospace; }

        /* ─────────────────────────────────────────────
           HEADER / NAV
           ───────────────────────────────────────────── */
        .header-bar {
            background: var(--color-primary);
            color: white;
            padding: 0.75rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .header-brand i {
            font-size: 1.5rem;
            color: var(--color-accent);
        }

        .header-brand span {
            font-weight: 800;
            font-size: 1.125rem;
            letter-spacing: -0.02em;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .patient-badge {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 999px;
            padding: 0.375rem 0.75rem;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .patient-badge .badge-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--color-success);
        }

        .header-actions {
            display: flex;
            gap: 0.5rem;
        }

        .btn-icon {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border: none;
            background: rgba(255,255,255,0.1);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.875rem;
            transition: all 0.2s;
        }

        .btn-icon:hover {
            background: rgba(255,255,255,0.2);
            transform: scale(1.05);
        }

        /* ─────────────────────────────────────────────
           MAIN LAYOUT
           ───────────────────────────────────────────── */
        .main-layout {
            max-width: 1280px;
            margin: 0 auto;
            padding: 1.5rem;
        }

        /* ─────────────────────────────────────────────
           PATIENT HEADER
           ───────────────────────────────────────────── */
        .patient-header {
            background: var(--color-card);
            border: 1px solid var(--color-border);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            display: flex;
            align-items: center;
            gap: 1.5rem;
            flex-wrap: wrap;
        }

        .patient-avatar {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: var(--color-gradient);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            color: white;
            font-weight: 700;
            flex-shrink: 0;
        }

        .patient-info {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            flex: 1;
        }

        .patient-name {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--color-primary);
        }

        .patient-id {
            font-size: 0.8rem;
            color: var(--color-text-muted);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .patient-id i {
            font-size: 0.7rem;
        }

        .patient-meta {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            align-items: flex-end;
            flex-shrink: 0;
        }

        .patient-meta-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8rem;
            color: var(--color-text-muted);
        }

        .patient-meta-item i {
            color: var(--color-accent);
        }

        .patient-meta-item .value {
            color: var(--color-primary);
            font-weight: 600;
        }

        .patient-meta-item .value.cidade { color: var(--color-accent); }
        .patient-meta-item .value.cep { color: var(--color-primary); }

        /* ─────────────────────────────────────────────
           DIAGNOSTIC HYPOTHESES SECTION
           ───────────────────────────────────────────── */
        .section-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--color-text-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .section-title i {
            color: var(--color-accent);
        }

        .hypotheses-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .hypothesis-card {
            background: var(--color-card);
            border: 1px solid var(--color-border);
            border-radius: 14px;
            padding: 1.25rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .hypothesis-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            border-radius: 14px 14px 0 0;
        }

        .hypothesis-card.h1::before { background: linear-gradient(90deg, #3b82f6, #2563eb); }
        .hypothesis-card.h2::before { background: linear-gradient(90deg, #10b981, #059669); }
        .hypothesis-card.h3::before { background: linear-gradient(90deg, #f59e0b, #d97706); }

        .hypothesis-card:hover {
            border-color: var(--color-accent);
            box-shadow: 0 4px 20px rgba(59,130,246,0.1);
            transform: translateY(-2px);
        }

        .hypothesis-card .card-number {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 700;
            color: white;
            margin-bottom: 0.75rem;
        }

        .hypothesis-card.h1 .card-number { background: linear-gradient(90deg, #3b82f6, #2563eb); }
        .hypothesis-card.h2 .card-number { background: linear-gradient(90deg, #10b981, #059669); }
        .hypothesis-card.h3 .card-number { background: linear-gradient(90deg, #f59e0b, #d97706); }

        .hypothesis-card .card-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--color-primary);
            margin-bottom: 0.25rem;
        }

        .hypothesis-card .card-description {
            font-size: 0.875rem;
            color: var(--color-text-muted);
            line-height: 1.7;
            margin-bottom: 0.75rem;
        }

        .hypothesis-card .card-signs {
            display: flex;
            flex-wrap: wrap;
            gap: 0.375rem;
            margin-bottom: 0.75rem;
        }

        .hypothesis-card .card-signs .tag {
            background: rgba(59,130,246,0.08);
            color: #2563eb;
            padding: 0.25rem 0.625rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 500;
        }

        .hypothesis-card .card-signs .tag.warning {
            background: rgba(245,158,11,0.12);
            color: #d97706;
        }

        .hypothesis-card .card-signs .tag.critical {
            background: rgba(239,68,68,0.12);
            color: #dc2626;
        }

        .hypothesis-card .card-signs .tag.success {
            background: rgba(16,185,129,0.12);
            color: #059669;
        }

        .hypothesis-card .card-score {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .hypothesis-card .card-score .score-bar {
            flex: 1;
            height: 4px;
            background: #e2e8f0;
            border-radius: 999px;
            overflow: hidden;
        }

        .hypothesis-card .card-score .score-fill {
            height: 100%;
            border-radius: 999px;
            transition: width 0.5s ease;
        }

        .hypothesis-card .card-score .score-label {
            min-width: 48px;
            text-align: right;
            font-size: 0.75rem;
        }

        .hypothesis-card .card-score .score-label .score-val {
            font-weight: 700;
        }

        .hypothesis-card .card-score .score-label .score-val.blue { color: #2563eb; }
        .hypothesis-card .card-score .score-label .score-val.green { color: #059669; }
        .hypothesis-card .card-score .score-label .score-val.orange { color: #d97706; }

        .hypothesis-card .card-action {
            display: inline-flex;
            align-items: center;
            gap: 0.375rem;
            padding: 0.375rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-decoration: none;
            color: white;
            transition: all 0.2s;
        }

        .hypothesis-card .card-action:hover {
            opacity: 0.9;
            transform: scale(1.02);
        }

        .hypothesis-card .card-action.btn-blue { background: linear-gradient(90deg, #3b82f6, #2563eb); }
        .hypothesis-card .card-action.btn-green { background: linear-gradient(90deg, #10b981, #059669); }
        .hypothesis-card .card-action.btn-orange { background: linear-gradient(90deg, #f59e0b, #d97706); }

        /* ─────────────────