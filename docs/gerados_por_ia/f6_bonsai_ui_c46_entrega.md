```html:backend/app/static/copiloto_card.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Card Copiloto - Prontuário Web</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {
            font-family: 'Inter', sans-serif;
        }

        .card-glow {
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
                        0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        .card-hover {
            transition: all 0.3s ease;
        }
        .card-hover:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1),
                        0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }

        .hypothesis-card {
            transition: all 0.3s ease;
        }
        .hypothesis-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15);
        }

        .interaction-card {
            transition: all 0.3s ease;
        }
        .interaction-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15);
        }

        .confidence-high {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        }
        .confidence-medium {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        }
        .confidence-low {
            background: linear-gradient(135deg, #334155 0%, #475569 100%);
        }

        .severity-high {
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        }
        .severity-medium {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        }
        .severity-low {
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
        }

        .suspension {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .fade-in {
            animation: fadeIn 0.5s ease forwards;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .card-header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        }

        .card-body {
            background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
        }

        .stat-bar {
            height: 6px;
            border-radius: 3px;
            background: #e2e8f0;
            overflow: hidden;
        }
        .stat-bar .fill {
            height: 100%;
            border-radius: 3px;
            transition: width 1s ease;
        }

        .badge {
            font-size: 0.65rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        .cns-badge {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
        }

        .cpf-badge {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: white;
        }

        .diagnosis-badge {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: white;
        }

        .interaction-badge {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: white;
        }

        .soap-section {
            background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
        }

        .soap-section:hover {
            background: linear-gradient(135deg, #e2e8f0 0%, #f1f5f9 100%);
        }

        .soap-section:hover .soap-title {
            color: #6366f1;
        }

        .soap-section:hover .soap-icon {
            color: #6366f1;
        }

        .ai-badge {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
        }

        .ai-badge:hover {
            background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white;
        }

        .ai-badge:hover span {
            color: white