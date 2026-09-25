```html:backend/app/static/telemedicina.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleatendimento — SUS / APS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #0f172a; color: #e2e8f0; margin: 0; min-height: 100vh; }
        .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(148, 163, 184, 0.08); }
        .glass-card { background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px); border: 1px solid rgba(148, 163, 184, 0.06); border-radius: 12px; }
        .glass-card:hover { border-color: rgba(148, 163, 184, 0.14); }
        .glass-panel { background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(10px); border: 1px solid rgba(148, 163, 184, 0.08); border-radius: 12px; }
        .glass-panel:hover { border-color: rgba(148, 163, 184, 0.14); }
        .glass-input { background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(148, 163, 184, 0.12); border-radius: 8px; color: #e2e8f0; padding: 0.5rem 0.75rem; outline: none; transition: border-color 0.2s; }
        .glass-input:focus { border-color: rgba(59, 130, 246, 0.5); box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15); }
        .glass-input::placeholder { color: #64748b; }
        .glass-btn { background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); color: #60a5fa; border-radius: 8px; padding: 0.5rem 1rem; cursor: pointer; transition: all 0.2s; }
        .glass-btn:hover { background: rgba(59, 130, 246, 0.3); border-color: rgba(59, 130, 246, 0.6); }
        .glass-btn:active { transform: scale(0.97); }
        .glass-btn:disabled { opacity: 0.4; cursor: not-allowed; }
        .glass-btn-primary { background: rgba(16, 185, 129, 0.2); border-color: rgba(16, 185, 129, 0.4); color: #6ee7b7; }
        .glass-btn-primary:hover { background: rgba(16, 185, 129, 0.35); }
        .glass-btn-danger { background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.3); color: #fca5a5; }
        .glass-btn-danger:hover { background: rgba(239, 68, 68, 0.3); }
        .glass-btn-success { background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.3); color: #6ee7b7; }
        .glass-btn-success:hover { background: rgba(16, 185, 129, 0.3); }
        .glass-btn-warning { background: rgba(251, 191, 36, 0.15); border-color: rgba(251, 191, 36, 0.3); color: #fde047; }
        .glass-btn-warning:hover { background: rgba(251, 191, 36, 0.3); }
        .glass-btn-info { background: rgba(59, 130, 246, 0.15); border-color: rgba(59, 130, 246, 0.3); color: #60a5fa; }
        .glass-btn-info:hover { background: rgba(59, 130, 246, 0.3); }
        .glass-btn-outline { background: transparent; border: 1px solid rgba(148, 163, 184, 0.2); color: #94a3b8; }
        .glass-btn-outline:hover { border-color: rgba(148, 163, 184, 0.4); color: #e2e8f0; }
        .glass-btn-ghost { background: transparent; border: none; color: #94a3b8; cursor: pointer; padding: 0.5rem; transition: color 0.2s; }
        .glass-btn-ghost:hover { color: #e2e8f0; }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.5); }
        ::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.2); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(148, 163, 184, 0.35); }

        /* SVG Icons */
        .icon-svg { display: inline-block; width: 18px; height: 18px; fill: currentColor; }

        /* Video grid */
        .video-grid { display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 16px; }
        .video-grid .video-item { position: relative; border-radius: 12px; overflow: hidden; background: #000; cursor: pointer; }
        .video-grid .video-item.active { border: 2px solid rgba(59, 130, 246, 0.5); }
        .video-grid .video-item.active .video-overlay { background: rgba(59, 130, 246, 0.3); }
        .video-grid .video-item .video-overlay {
            position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
            background: rgba(0, 0, 0, 0.5); opacity: 0; transition: opacity 0.3s;
        }
        .video-grid .video-item:hover .video-overlay { opacity: 1; }
        .video-grid .video-item .video-overlay .info {
            background: rgba(15, 23, 42, 0.9); padding: 8px 14px; border-radius: 8px;
            font-size: 0.8rem; color: #e2e8f0; text-align: center;
        }
        .video-grid .video-item .video-overlay .info .name { font-weight: 600; font-size: 0.85rem; }
        .video-grid .video-item .video-overlay .info .role { font-size: 0.7rem; color: #94a3b8; }
        .video-grid .video-item .video-overlay .info .status {
            display: inline-block; width: 8px; height: 8px; border-radius: 50%;
            margin-left: 6px; background: #22c55e;
        }
        .video-grid .video-item .video-overlay .info .status.off { background: #ef4444; }
        .video-grid .video-item .video-overlay .info .status.muted { background: #f59e0b; }
        .video-grid .video-item .video-overlay .info .status.no-cam { background: #6b7280; }

        /* PIP */
        .pip { position: absolute; bottom: 16px; right: 16px; width: 140px; height: 100px;
            border-radius: 8px; overflow: hidden; border: 2px solid rgba(15, 23, 42, 0.8);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5); z-index: 10;
        }
        .pip .pip-label {
            position: absolute; bottom: -24px; left: 50%; transform: translateX(-50%);
            background: rgba(15, 23, 42, 0.95); padding: 4px 10px; border-radius: 6px;
            font-size: 0.7rem; color: #94a3b8; text-align: center;
        }

        /* SOAP Panel */
        .soap-section { margin-bottom: 20px; }
        .soap-section:last-child { margin-bottom: 0; }
        .soap-header {
            display: flex; align-items: center; justify-content: space-between;
            padding: 10px 14px; background: rgba(59, 130, 246, 0.1); border-radius: 8px;
            margin-bottom: 10px; font-size: 0.8rem; font-weight: 600; color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.2);
        }
        .soap-header .section-letter { font-size: 1.2rem; font-weight: 800; color: #60a5fa; }
        .soap-header .section-letter.S { color: #f59e0b; }
        .soap-header .section-letter.O { color: #3b82f6; }
        .soap-header .section-letter.A { color: #10b981; }
        .soap-header .section-letter.P { color: #f472b6; }
        .soap-header .section-letter.H { color: #f97316; }
        .soap-header .section-letter.I { color: #a78bfa; }
        .soap-header .section-letter.R { color: #ef4444; }
        .soap-header .section-letter.C { color: #38bdf8; }
        .soap-header .section-letter.L { color: #22d3ee; }
        .soap-header .section-letter.E { color: #fbbf24; }
        .soap-header .section-letter.C2 { color: #f472b6; }
        .soap-header .section-letter.C3 { color: #fbbf24; }
        .soap-header .section-letter.C4 { color: #a78bfa; }
        .soap-header .section-letter.C5 { color: #f59e0b; }
        .soap-header .section-letter.C6 { color: #3b82f6; }
        .soap-header .section-letter.C7 { color: #10b981; }
        .soap-header .section-letter.C8 { color: #f472b6; }
        .soap-header .section-letter.C9 { color: #fbbf24; }
        .soap-header .section-letter.C10 { color: #38bdf8; }
        .soap-header .section-letter.CIAP2 { color: #f59e0b; }
        .soap-header .section-letter.CID10 { color: #3b82f6; }
        .soap-header .section-letter.M { color: #a78bfa; }
        .soap-header .section-letter.D { color: #f97316; }
        .soap-header .section-letter.T { color: #22d3ee; }
        .soap-header .section-letter.E2 { color: #fbbf24; }
        .soap-header .section-letter.E3 { color: #38bdf8; }
        .soap-header .section-letter.E4 { color: #f472b6; }
        .soap-header .section-letter.E5 { color: #a78bfa; }
        .soap-header .section-letter.E6 { color: #f59e0b; }
        .soap-header .section-letter.E7 { color: #3b82f6; }
        .soap-header .section-letter.E8 { color: #10b981; }
        .soap-header .section-letter.E9 { color: #f472b6; }
        .soap-header .section-letter.E10 { color: #38bdf8; }
        .soap-header .section-letter.E11 { color: #fbbf24; }
        .soap-header .section-letter.E12 { color: #a78bfa; }
        .soap-header .section-letter.E13 { color: #3b82f6; }
        .soap-header .section-letter.E14 { color: #10b981; }
        .soap-header .section-letter.E15 { color: #f472b6; }
        .soap-header .section-letter.E16 { color: #38bdf8; }
        .soap-header .section-letter.E17 { color: #f59e0b; }
        .soap-header .section-letter.E18 { color: #a78bfa; }
        .soap-header .section-letter.E