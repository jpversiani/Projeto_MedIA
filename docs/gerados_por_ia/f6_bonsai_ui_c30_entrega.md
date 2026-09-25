```python:backend/app/static/copiloto_card.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Copiloto Card — Prontuário Web</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
        }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(148, 163, 184, 0.08);
        }
        .glass-card {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(148, 163, 184, 0.06);
            transition: all 0.3s ease;
        }
        .glass-card:hover {
            border-color: rgba(148, 163, 184, 0.15);
            transform: translateY(-2px);
        }
        .gradient-border {
            border: 1px solid transparent;
            background-image: linear-gradient(
                90deg,
                transparent 0%,
                rgba(56, 189, 248, 0.15) 50%,
                transparent 100%
            );
            background-size: 200% 100%;
        }
        .card-pulse {
            animation: pulse-soft 3s ease-in-out infinite;
        }
        @keyframes pulse-soft {
            0%, 100% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.1); }
            50% { box-shadow: 0 0 0 10px rgba(56, 189, 248, 0); }
        }
        .hypothesis-card {
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.08) 0%, rgba(16, 185, 129, 0.06) 100%);
            border: 1px solid rgba(56, 189, 248, 0.12);
            transition: all 0.3s ease;
        }
        .hypothesis-card:hover {
            border-color: rgba(56, 189, 248, 0.3);
            transform: translateY(-3px);
        }
        .interaction-card {
            background: linear-gradient(135deg, rgba(248, 113, 113, 0.08) 0%, rgba(245, 158, 11, 0.06) 100%);
            border: 1px solid rgba(248, 113, 113, 0.12);
            transition: all 0.3s ease;
        }
        .interaction-card:hover {
            border-color: rgba(248, 113, 113, 0.3);
            transform: translateY(-3px);
        }
        .confidence-bar {
            background: linear-gradient(90deg, #3b82f6 0%, #0ea5e9 100%);
            border-radius: 9999px;
        }
        .confidence-bar.warning {
            background: linear-gradient(90deg, #f59e0b 0%, #f97316 100%);
        }
        .confidence-bar.critical {
            background: linear-gradient(90deg, #ef4444 0%, #f97316 100%);
        }
        .cns-badge {
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.15) 0%, rgba(16, 185, 129, 0.1) 100%);
            border: 1px solid rgba(56, 189, 248, 0.2);
        }
        .soap-section {
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid rgba(148, 163, 184, 0.05);
        }
        .stat-ring {
            position: relative;
            width: 48px;
            height: 48px;
        }
        .stat-ring svg {
            transform: rotate(-90deg);
        }
        .stat-ring .circle {
            fill: none;
            stroke-width: 6;
            stroke-linecap: round;
        }
        .stat-ring .circle.filled {
            stroke-dasharray: 125.66;
            stroke-dashoffset: 0;
            transition: stroke-dashoffset 1s ease;
        }
        .stat-ring .circle.empty {
            stroke-dasharray: 125.66;
            stroke-dashoffset: 125.66;
        }
        .stat-ring.warning .circle.filled {
            stroke: #f59e0b;
        }
        .stat-ring.warning .circle.empty {
            stroke: #f59e0b;
        }
        .stat-ring.critical .circle.filled {
            stroke: #ef4444;
        }
        .stat-ring.critical .circle.empty {
            stroke: #ef4444;
        }
        .scan-line {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.6), transparent);
            animation: scan 4s linear infinite;
            pointer-events: none;
        }
        @keyframes scan {
            0% { top: -2px; }
            100% { top: 100%; }
        }
        .fade-in {
            animation: fadeIn 0.5s ease-out forwards;
            opacity: 0;
            transform: translateY(10px);
        }
        @keyframes fadeIn {
            to { opacity: 1; transform: translateY(0); }
        }
        .stagger-1 { animation-delay: 0.1s; }
        .stagger-2 { animation-delay: 0.2s; }
        .stagger-3 { animation-delay: 0.3s; }
        .stagger-4 { animation-delay: 0.4s; }
        .stagger-5 { animation-delay: 0.5s; }
        .stagger-6 { animation-delay: 0.6s; }
        .stagger-7 { animation-delay: 0.7s; }
        .stagger-8 { animation-delay: 0.8s; }
        .stagger-9 { animation-delay: 0.9s; }
        .stagger-10 { animation-delay: 1.0s; }
        .cpi-score {
            font-variant-numeric: tabular-nums;
        }
        .medication-tag {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 8px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        .med-tag-antibiotic {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(34, 211, 137, 0.2);
        }
        .med-tag-antihypertensive {
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            border: 1px solid rgba(94, 165, 233, 0.2);
        }
        .med-tag-anti-inflammatory {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(251, 191, 36, 0.2);
        }
        .med-tag-antidepressant {
            background: rgba(168, 85, 247, 0.15);
            color: #c084fc;
            border: 1px solid rgba(192, 132, 252, 0.2);
        }
        .med-tag-sedative {
            background: rgba(248, 113, 113, 0.15);
            color: #fca5a5;
            border: 1px solid rgba(248, 113, 113, 0.2);
        }
        .med-tag-diuretic {
            background: rgba(148, 163, 184, 0.15);
            color: #94a3b8;
            border: 1px solid rgba(148, 163, 184, 0.2);
        }
        .med-tag-stimulant {
            background: rgba(236, 72, 153, 0.15);
            color: #f472b6;
            border: 1px solid rgba(244, 114, 182, 0.2);
        }
        .med-tag-nsaid {
            background: rgba(234, 179, 8, 0.15);
            color: #fde047;
            border: 1px solid rgba(251, 191, 36, 0.2);
        }
        .med-tag-opioid {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(251, 191, 36, 0.2);
        }
        .med-tag-anticholinergic {
            background: rgba(248, 113, 113, 0.15);
            color: #fca5a5;
            border: 1px solid rgba(248, 113, 113, 0.2);
        }
        .med-tag-anticholinergic::after {
            content: '⚠️';
            margin-left: 4px;
        }
        .interaction-severity {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .severity-high {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .severity-moderate {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(251, 191, 36, 0.3);
        }
        .severity-low {
            background: rgba(34, 197, 94, 0.15);
            color: #6ee7b7;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }
        .soap-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }
        .soap-item {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.05);
            padding: 10px 12px;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        .soap-item:hover {
            border-color: rgba(148, 163, 184, 0.15);
        }
        .soap-label {
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #94a3b8;
            margin-bottom: 4px;
        }
        .soap-value {
            font-size: 0.85rem;
            font-weight: 500;
        }
        .patient-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .patient-avatar {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.1rem;
            border: 2px solid rgba(56, 189, 248, 0.3);
        }
        .patient-details h3 {
            font-size: 0.9rem;
            font-weight: 600;
        }
        .patient-details p {
            font-size: 0.75rem;
            color: #94a3b8;
        }
        .cpi-card {
            background: rgba(15, 23, 