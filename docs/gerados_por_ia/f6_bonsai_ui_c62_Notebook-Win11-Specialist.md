```python:backend/app/static/copiloto_card.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prontuário Web — Copiloto — Hipóteses Diagnósticas</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #0f172a; color: #e2e8f0; }
        .card-glow {
            box-shadow: 0 0 40px rgba(59, 130, 246, 0.15),
                        0 0 80px rgba(59, 130, 246, 0.05);
        }
        .gradient-border {
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .hypothesis-card {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .hypothesis-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 60px rgba(59, 130, 246, 0.2);
        }
        .risk-badge {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        .cns-badge {
            background: linear-gradient(135deg, #1e3a8a, #3b82f6);
        }
        .cpifield {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .diagnosis-bar {
            transition: width 1s ease;
        }
        .diagnosis-bar.medium { width: 50%; }
        .diagnosis-bar.high { width: 75%; }
        .diagnosis-bar.critical { width: 100%; }
        .diagnosis-bar.low { width: 25%; }
        .diagnosis-bar.critical { background: linear-gradient(90deg, #ef4444, #dc2626); }
        .diagnosis-bar.medium { background: linear-gradient(90deg, #f59e0b, #d97706); }
        .diagnosis-bar.high { background: linear-gradient(90deg, #eab308, #f59e0b); }
        .diagnosis-bar.low { background: linear-gradient(90deg, #16a34a, #22c55e); }
        .interaction-badge {
            transition: all 0.3s ease;
        }
        .interaction-badge:hover {
            transform: scale(1.05);
        }
        .ai-confidence {
            background: linear-gradient(90deg, #3b82f6, #2563eb);
        }
        .medication-pill {
            border-radius: 9999px;
            padding: 4px 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .medication-pill.sus { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
        .medication-pill.aps { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; }
        .medication-pill.danger { background: rgba(239, 68, 68, 0.2); color: #fca5a5; }
        .medication-pill.warning { background: rgba(234, 179, 8, 0.2); color: #fde047; }
        .medication-pill.safe { background: rgba(34, 197, 94, 0.2); color: #6ee7b7; }
        .patient-info {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(59, 130, 246, 0.2);
        }
        .soap-section {
            transition: max-height 0.4s ease;
        }
        .soap-section.open {
            max-height: 500px;
        }
        .soap-section.collapsed {
            max-height: 0;
            overflow: hidden;
        }
        .stat-ring {
            position: relative;
        }
        .stat-ring svg {
            transform: rotate(-90deg);
        }
        .stat-ring .circle {
            fill: none;
            stroke-width: 8;
            stroke-linecap: round;
        }
        .stat-ring .circle.fill {
            stroke-dasharray: 251.32;
            stroke-dashoffset: 0;
            transition: stroke-dashoffset 1s ease;
        }
        .stat-ring .circle.stroke {
            stroke-dasharray: 251.32;
            stroke-dashoffset: 251.32;
        }
        .stat-ring .circle.fill {
            stroke: #3b82f6;
        }
        .stat-ring .circle.stroke {
            stroke: rgba(59, 130, 246, 0.2);
        }
        .ai-badge {
            background: linear-gradient(135deg, #8b5cf6, #6366f1);
        }
        .ai-badge::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%);
            animation: rotate 8s linear infinite;
            z-index: -1;
        }
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .cns-display {
            font-family: 'Courier New', monospace;
            letter-spacing: 2px;
            font-weight: 700;
        }
        .cpf-display {
            font-family: 'Courier New', monospace;
            letter-spacing: 1px;
            font-weight: 600;
        }
        .diagnosis-card {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(59, 130, 246, 0.15);
        }
        .diagnosis-card:hover {
            border-color: rgba(59, 130, 246, 0.4);
        }
        .interaction-card {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(59, 130, 246, 0.15);
        }
        .interaction-card:hover {
            border-color: rgba(239, 68, 68, 0.4);
        }
        .method-tag {
            background: rgba(59, 130, 246, 0.1);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.2);
        }
        .method-tag.aps {
            background: rgba(16, 185, 129, 0.1);
            color: #6ee7b7;
            border-color: rgba(16, 185, 129, 0.2);
        }
        .method-tag.ciap2 {
            background: rgba(239, 68, 68, 0.1);
            color: #fca5a5;
            border-color: rgba(239, 68, 68, 0.2);
        }
        .method-tag.soap {
            background: rgba(234, 179, 8, 0.1);
            color: #fde047;
            border-color: rgba(234, 179, 8, 0.2);
        }
        .method-tag.cid10 {
            background: rgba(139, 92, 246, 0.1);
            color: #c084fc;
            border-color: rgba(139, 92, 246, 0.2);
        }
        .method-tag.cns {
            background: rgba(59, 130, 246, 0.1);
            color: #60a5fa;
            border-color: rgba(59, 130, 246, 0.2);
        }
        .method-tag.cpf {
            background: rgba(16, 185, 129, 0.1);
            color: #6ee7b7;
            border-color: rgba(16, 185, 129, 0.2);
        }
        .ai-pulse {
            animation: pulse 2s infinite;
        }
        .ai-pulse-slow {
            animation: pulse 3s infinite;
        }
        .diagnosis-card .diagnosis-bar {
            height: 6px;
            border-radius: 3px;
        }
        .ai-score {
            font-family: 'Courier New', monospace;
        }
        .ai-score.high { color: #22c55e; }
        .ai-score.medium { color: #f59e0b; }
        .ai-score.low { color: #ef4444; }
        .ai-score.critical { color: #f87171; }
        .ai-score.critical::after {
            content: ' ⚠️';
        }
        .ai-score.medium::after {
            content: ' ⚡';
        }
        .ai-score.low::after {
            content: ' ⚡';
        }
        .ai-score.high::after {
            content: ' ✓';
        }
        .ai-score.critical::after {
            content: ' ⚠️';
        }
        .ai-score.medium::after {
            content: ' ⚡';
        }
        .ai-score.low::after {
            content: ' ⚡';
        }
        .ai-score.high { color: #22c55e; }
        .ai-score.medium { color: #f59e0b; }
        .ai-score.low { color: #ef4444; }
        .ai-score.critical { color: #f87171; }
        .ai-score.medium::after {
            content: ' ⚡';
        }
        .ai-score.low::after {
            content: ' ⚡';
        }
        .ai-score.high::after {
            content: ' ✓';
        }
        .ai-score.critical::after {
            content: ' ⚠️';
        }
        .ai-score.medium::after {
            content: ' ⚡';
        }
        .ai-score.low::after {
            content: ' ⚡';
        }
        .ai-score.high { color: #22c55e; }
        .ai-score.medium { color: #f59e0b; }
        .ai-score.low { color: #ef4444; }
        .ai-score.critical { color: #f87171; }
        .ai-score.medium::after {
            content: ' ⚡';
        }
        .ai-score.low::after {
            content: ' ⚡';
        }
        .ai-score.high::after {
            content: ' ✓';
        }
        .ai-score.critical::after {
            content: ' ⚠️';
        }
        .ai-score.medium::after {
            content: ' ⚡';
        }
        .ai-score.low::after {
            content: ' ⚡';
        }
        .ai-score.high { color: #22c55e; }
        .ai-score.medium { color: #f59e0b; }
        .ai-score.low { color: #ef4444; }
        .ai-score.critical { color: #f87171; }
        .ai-score.medium::after {
            content: ' ⚡';
        }
        .ai-score.low::after {
            content: ' ⚡';
        }
        .ai-score.high::after {
            content: ' ✓';
        }
        .ai-score.critical::after {
            content: ' ⚠️';
        }
        .ai-score.medium::after {
            content: ' ⚡';
        }
        .ai-score.low::after {
            content: ' ⚡';
        }
        .ai-score.high { color: #22c55e; }
        .ai-score.medium { color: #f59e0b; }
        .ai-score.low { color: #ef4444; }
        .ai-score.critical { color: #f87171; }
        .ai-score.medium::after {
            content: ' ⚡';
        }
        .ai-score.low::after {
            content: ' ⚡';
        }
        .ai-score.high::after {
            content: ' ✓';
        }
        .ai-score.critical::after {
            content: ' ⚠️';
        }
        .ai-score.medium::after {
            content: ' ⚡';
        }
        .ai-score.low::after {
            content: ' ⚡';
        }
        .ai-score.high { color: #22c55e; }
        .ai-score.medium { color: #f59e0b; }
        .ai-score