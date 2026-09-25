```python:backend/app/static/copiloto_card.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Card Copiloto — Prontuário Web</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #0f172a; color: #e2e8f0; }
        .glass {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.08);
        }
        .glass-card {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(148, 163, 184, 0.1);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .glass-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
            border-color: rgba(148, 163, 184, 0.2);
        }
        .hypothesis-card {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(59, 130, 246, 0.02));
            border-left: 4px solid #3b82f6;
        }
        .hypothesis-card:hover {
            border-color: #60a5fa;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.12), rgba(59, 130, 246, 0.04));
        }
        .interaction-card {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.08), rgba(239, 68, 68, 0.02));
            border-left: 4px solid #ef4444;
        }
        .interaction-card:hover {
            border-color: #fca5a5;
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.12), rgba(239, 68, 68, 0.04));
        }
        .warning-card {
            background: linear-gradient(135deg, rgba(234, 179, 8, 0.08), rgba(234, 179, 8, 0.02));
            border-left: 4px solid #f59e0b;
        }
        .warning-card:hover {
            border-color: #fbbf24;
            background: linear-gradient(135deg, rgba(234, 179, 8, 0.12), rgba(234, 179, 8, 0.04));
        }
        .confidence-bar {
            height: 6px;
            border-radius: 3px;
            background: rgba(148, 163, 184, 0.15);
            overflow: hidden;
        }
        .confidence-fill {
            height: 100%;
            border-radius: 3px;
            transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .ai-badge {
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: white;
            font-size: 0.65rem;
            padding: 0.15rem 0.5rem;
            border-radius: 999px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        .patient-badge {
            background: rgba(148, 163, 184, 0.15);
            color: #94a3b8;
            font-size: 0.75rem;
            padding: 0.25rem 0.6rem;
            border-radius: 999px;
        }
        .med-pill {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            border-radius: 12px;
            padding: 0.25rem 0.75rem;
            font-size: 0.8rem;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
        }
        .interaction-pair {
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }
        .interaction-pair .pill {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            border-radius: 8px;
            padding: 0.2rem 0.5rem;
            font-size: 0.7rem;
            font-weight: 500;
        }
        .interaction-pair .pill.danger {
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }
        .interaction-pair .pill.warning {
            background: linear-gradient(135deg, #f59e0b, #d97706);
        }
        .interaction-pair .pill.safe {
            background: linear-gradient(135deg, #10b981, #059669);
        }
        .interaction-pair .arrow {
            font-size: 0.85rem;
            color: #94a3b8;
        }
        .stat-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 600;
        }
        .stat-badge.high {
            background: rgba(239, 68, 68, 0.15);
            color: #fca5a5;
        }
        .stat-badge.medium {
            background: rgba(234, 179, 8, 0.15);
            color: #fbbf24;
        }
        .stat-badge.low {
            background: rgba(16, 185, 129, 0.15);
            color: #6ee7b7;
        }
        .stat-badge.critical {
            background: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
            animation: pulse-red 1.5s infinite;
        }
        @keyframes pulse-red {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        .card-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
        }
        .card-icon.blue { background: rgba(59, 130, 246, 0.12); color: #60a5fa; }
        .card-icon.red { background: rgba(239, 68, 68, 0.12); color: #fca5a5; }
        .card-icon.yellow { background: rgba(234, 179, 8, 0.12); color: #fbbf24; }
        .card-icon.green { background: rgba(16, 185, 129, 0.12); color: #6ee7b7; }
        .header-bar {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
            border-bottom: 1px solid rgba(148, 163, 184, 0.08);
        }
        .footer-bar {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(139, 92, 246, 0.05));
            border-top: 1px solid rgba(148, 163, 184, 0.08);
        }
        .tab-btn {
            transition: all 0.2s ease;
        }
        .tab-btn.active {
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            border-color: rgba(59, 130, 246, 0.3);
        }
        .tab-btn:not(.active) {
            background: rgba(148, 163, 184, 0.05);
            color: #94a3b8;
            border-color: rgba(148, 163, 184, 0.08);
        }
        .tab-btn:hover:not(.active) {
            background: rgba(148, 163, 184, 0.1);
            color: #cbd5e1;
        }
        .tab-btn:hover.active {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }
        .tab-btn.active:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
