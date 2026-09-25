```python:backend/app/static/copiloto_card.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Copiloto - Prontuário Web - Hipóteses Diagnósticas</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f0f2f5;
        }
        .card-glow {
            box-shadow: 0 4px 24px rgba(99, 102, 241, 0.15);
        }
        .card-hover:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 32px rgba(99, 102, 241, 0.25);
        }
        .stat-bar {
            transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .pulse-dot {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.5); }
        }
        .gradient-text {
            background: linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .suspicion-badge {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border-radius: 9999px;
            font-size: 0.7rem;
            padding: 0.25rem 0.75rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .drug-interaction-badge {
            background: linear-gradient(135deg, #ef4444, #f97316);
            color: white;
            border-radius: 9999px;
            font-size: 0.7rem;
            padding: 0.25rem 0.75rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .confidence-ring {
            position: relative;
            width: 60px;
            height: 60px;
        }
        .confidence-ring svg {
            transform: rotate(-90deg);
        }
        .confidence-ring .circle {
            fill: none;
            stroke-width: 4;
            stroke-dasharray: 160;
            stroke-dashoffset: 160;
            animation: progress 1.5s ease-out forwards;
        }
        @keyframes progress {
            to { stroke-dashoffset: 0; }
        }
        .tab-active {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
        }
        .tab-inactive {
            background: #e5e7eb;
            color: #6b7280;
        }
        .tab-inactive:hover {
            background: #d1d5db;
            color: #374151;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }
        .tab-active:focus {
            outline: 2px solid #818cf8;
            outline-offset: 2px;
        }
        .tab-inactive:focus {
            outline: 2px solid #6366f1;
            outline-offset: 2px;
        }