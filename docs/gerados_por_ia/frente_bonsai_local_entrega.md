```html:docs/gerados_por_ia/interface_telemedicina.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>MedIA — Sala de Teleatendimento | SUS Telemedicina</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <style>
    /* ── Custom Properties ──────────────────────────────────── */
    :root {
      --brand-primary: #0e7490;
      --brand-primary-dark: #02597a;
      --brand-primary-light: #7dd3fc;
      --brand-accent: #f59e0b;
      --brand-accent-dark: #d97706;
      --brand-sus: #167e3a;
      --brand-sus-light: #86efac;
      --bg-dark: #0f172a;
      --bg-card: #1e293b;
      --bg-card-hover: #334155;
      --text-primary: #f1f5f9;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --border-light: #334155;
      --border-focus: #0ea5e9;
      --radius-sm: 0.375rem;
      --radius-md: 0.5rem;
      --radius-lg: 0.75rem;
      --radius-xl: 1rem;
      --shadow-card: 0 4px 24px rgba(0, 0, 0, 0.35);
      --shadow-glow: 0 0 40px rgba(14, 116, 144, 0.15);
      --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
      --transition-smooth: 300ms cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* ── Base ───────────────────────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; }

    body {
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      background: var(--bg-dark);
      color: var(--text-primary);
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* ── Background Pattern ─────────────────────────────────── */
    .bg-pattern {
      position: fixed;
      inset: 0;
      z-index: -1;
      background:
        radial-gradient(ellipse at 20% 50%, rgba(14, 116, 144, 0.08) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 20%, rgba(245, 158, 11, 0.04) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 80%, rgba(22, 126, 58, 0.06) 0%, transparent 50%);
      pointer-events: none;
    }

    /* ── Glass Card ─────────────────────────────────────────── */
    .glass-card {
      background: rgba(30, 41, 59, 0.7);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-lg);
      transition: all var(--transition-smooth);
    }
    .glass-card:hover {
      border-color: var(--border-focus);
      box-shadow: var(--shadow-glow);
      transform: translateY(-2px);
    }

    /* ── Glass Card Active ──────────────────────────────────── */
    .glass-card.active {
      border-color: var(--brand-primary);
      box-shadow: 0 0 0 1px var(--brand-primary), var(--shadow-glow);
    }

    /* ── Gradient Text ──────────────────────────────────────── */
    .gradient-text {
      background: linear-gradient(135deg, var(--brand-primary), var(--brand-accent));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    /* ── Gradient Border ────────────────────────────────────── */
    .gradient-border {
      border: 1px solid linear-gradient(135deg, var(--brand-primary), var(--brand-accent));
    }

    /* ── Pulse Animation ────────────────────────────────────── */
    @keyframes pulse-ring {
      0%   { box-shadow: 0 0 0 0 rgba(14, 116, 144, 0.4); }
      70%  { box-shadow: 0 0 0 10px rgba(14, 116, 144, 0); }
      100% { box-shadow: 0 0 0 0 rgba(14, 116, 144, 0); }
    }
    .pulse-ring { animation: pulse-ring 2s infinite; }

    /* ── Fade-in ────────────────────────────────────────────── */
    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(16px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .fade-in-up {
      animation: fadeInUp 0.5s ease-out both;
    }

    /* ── Fade-in ────────────────────────────────────────────── */
    @keyframes fadeIn {
      from { opacity: 0; }
      to   { opacity: 1; }
    }
    .fade-in { animation: fadeIn 0.4s ease-out both; }

    /* ── Scrollbar ──────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
      background: var(--border-light);
      border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

    /* ── Video Container ────────────────────────────────────── */
    .video-container {
      position: relative;
      width: 100%;
      aspect-ratio: 16 / 9;
      background: #000;
      border-radius: var(--radius-md);
      overflow: hidden;
    }
    .video-container .video-placeholder {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      background:
        linear-gradient(135deg, rgba(14, 116, 144, 0.2), rgba(245, 158, 11, 0.1));
      color: var(--text-secondary);
    }
    .video-container .video-placeholder .icon {
      font-size: 4rem;
      margin-bottom: 1rem;
      opacity: 0.5;
    }

    /* ── Camera Toggle ──────────────────────────────────────── */
    .camera-toggle {
      position: absolute;
      bottom: 16px;
      right: 16px;
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(10px);
      border: 1px solid var(--border-light);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all var(--transition-fast);
      z-index: 10;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    .camera-toggle:hover {
      background: rgba(14, 116, 144, 0.8);
      border-color: var(--brand-primary);
      transform: scale(1.05);
    }
    .camera-toggle.active {
      background: rgba(245, 158, 11, 0.9);
      border-color: var(--brand-accent);
      color: #000;
    }
    .camera-toggle .icon {
      transition: transform var(--transition-fast);
    }
    .camera-toggle.active .icon { transform: rotate(180deg); }

    /* ── Waiting Room ───────────────────────────────────────── */
    .waiting-list {
      max-height: 280px;
      overflow-y: auto;
    }
    .waiting-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 16px;
      border-radius: var(--radius-md);
      margin-bottom: 4px;
      transition: all var(--transition-fast);
      cursor: pointer;
    }
    .waiting-item:hover {
      background: rgba(255, 255, 255, 0.04);
    }
    .waiting-item .avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      font-size: 0.85rem;
      flex-shrink: 0;
    }
    .waiting-item .name {
      flex: 1;
      min-width: 0;
    }
    .waiting-item .name .name-text {
      font-weight: 500;
      font-size: 0.9rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .waiting-item .name .role {
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    .waiting-item .status {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 0.7rem;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .status-queued {
      background: rgba(245, 158, 11, 0.15);
      color: var(--brand-accent);
    }
    .status-attending {
      background: rgba(22, 126, 58, 0.15);
      color: var(--brand-sus);
    }
    .status-canceled {
      background: rgba(239, 68, 68, 0.15);
      color: #ef4444;
    }

    /* ── SOAP Template ──────────────────────────────────────── */
    .soap-section {
      background: rgba(14, 116, 144, 0.05);
      border: 1px solid rgba(14, 116, 144, 0.15);
      border-radius: var(--radius-md);
      padding: 16px;
      margin-bottom: 12px;
    }
    .soap-section h3 {
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--brand-primary-light);
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .soap-section h3 .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--brand-primary);
    }
    .soap-input {
      width: 100%;
      padding: 10px 14px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      color: var(--text-primary);
      font-size: 0.9rem;
      font-family: 'Inter', sans-serif;
      transition: all var(--transition-fast);
      outline: none;
    }
    .soap-input:focus {
      border-color: var(--brand-primary);
      box-shadow: 0 0 0 3px rgba(14, 116, 144, 0.15);
    }
    .soap-input::placeholder {
      color: var(--text-muted);
    }

    /* ── Prescription ───────────────────────────────────────── */
    .prescription-card {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(14, 116, 144, 0.05));
      border: 1px solid rgba(245, 158, 11, 0.2);
      border-radius: var(--radius-md);
      padding: 16px;
      margin-bottom: 12px;
    }
    .prescription-card h3 {
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--brand-accent);
     