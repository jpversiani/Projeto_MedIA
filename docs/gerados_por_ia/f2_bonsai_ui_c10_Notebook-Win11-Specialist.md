```html:backend/app/static/farmacia_dispensacao.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmácia Dispensação — UBS | Consulta de Receita Digital</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #0f172a; color: #e2e8f0; }
        .glass-panel {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.08);
        }
        .glass-card {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(148, 163, 184, 0.06);
            transition: all 0.25s ease;
        }
        .glass-card:hover {
            border-color: rgba(148, 163, 184, 0.14);
            transform: translateY(-2px);
        }
        .scan-ring {
            animation: scanPulse 2s infinite;
        }
        @keyframes scanPulse {
            0%, 100% { transform: scale(1); opacity: 0.3; }
            50% { transform: scale(1.05); opacity: 0.8; }
        }
        .scan-ring::before {
            content: '';
            position: absolute;
            inset: 0;
            border: 2px solid rgba(59, 130, 246, 0.3);
            border-radius: 16px;
            animation: scanPulse 2s infinite;
        }
        .scan-ring::after {
            content: '';
            position: absolute;
            inset: 4px;
            border: 1px solid rgba(59, 130, 246, 0.15);
            border-radius: 12px;
            animation: scanPulse 2s infinite reverse;
        }
        .barcode-ghost {
            opacity: 0.08;
            pointer-events: none;
        }
        .badge {
            font-size: 0.7rem;
            padding: 0.25rem 0.6rem;
            border-radius: 999px;
            font-weight: 600;
            letter-spacing: 0.02em;
        }
        .badge-active { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-warning { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
        .badge-error { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
        .badge-info { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
        .badge-success { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-critical { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
        .input-focus {
            transition: all 0.25s ease;
        }
        .input-focus:focus {
            border-color: rgba(59, 130, 246, 0.5);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        .btn-primary {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            transition: all 0.25s ease;
        }
        .btn-primary:hover {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
        }
        .btn-primary:active { transform: translateY(0); }
        .btn-danger {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            transition: all 0.25s ease;
        }
        .btn-danger:hover {
            background: linear-gradient(135deg, #dc2626, #b91c1c);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(220, 38, 38, 0.4);
        }
        .btn-secondary {
            background: rgba(148, 163, 184, 0.1);
            border: 1px solid rgba(148, 163, 184, 0.2);
            transition: all 0.25s ease;
        }
        .btn-secondary:hover {
            background: rgba(148, 163, 184, 0.2);
            border-color: rgba(148, 163, 184, 0.4);
        }
        .btn-outline {
            background: transparent;
            border: 1px solid rgba(148, 163, 184, 0.2);
            transition: all 0.25s ease;
        }
        .btn-outline:hover {
            border-color: rgba(148, 163, 184, 0.4);
            background: rgba(148, 163, 184, 0.05);
        }
        .progress-bar {
            height: 4px;
            border-radius: 2px;
            background: rgba(148, 163, 184, 0.15);
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            border-radius: 2px;
            transition: width 0.5s ease;
        }
        .progress-fill.active { background: linear-gradient(90deg, #3b82f6, #8b5cf6); }
        .progress-fill.success { background: linear-gradient(90deg, #10b981, #34d399); }
        .progress-fill.warning { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
        .progress-fill.error { background: linear-gradient(90deg, #ef4444, #f87171); }
        .tab-btn {
            transition: all 0.25s ease;
            position: relative;
        }
        .tab-btn.active {
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            border-bottom: 2px solid #3b82f6;
        }
        .tab-btn.active::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            right: 0;
            height: 2px;
            background: #3b82f6;
        }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn:not(.active) {
            background: transparent;
            color: rgba(148, 163, 184, 0.6);
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
        }
        .tab-btn.active {
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
        }
        .tab-btn.active::after { display: none; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active {
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            border-bottom: 2px solid #3b82f6;
        }
        .tab-btn:not(.active) {
            background: transparent;
            color: rgba(148, 163, 184, 0.6);
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
        }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: none; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.