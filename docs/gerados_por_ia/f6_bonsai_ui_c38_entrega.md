```python:backend/app/static/copiloto_card.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Card Copiloto — Hipóteses e Interações Farmacológicas</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
        .card-header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        }
        .diagnostic-card {
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .diagnostic-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        }
        .interaction-badge {
            transition: all 0.2s ease;
        }
        .interaction-badge:hover {
            transform: scale(1.05);
        }
        .cns-bar {
            background: linear-gradient(90deg, #0f172a, #1e293b);
        }
        .cns-bar span {
            color: #ffffff;
            font-weight: 700;
            letter-spacing: 0.05em;
        }
        .cns-bar .separator {
            color: #64748b;
        }
        .diagnostic-card .hypothesis-number {
            background: #3b82f6;
            color: white;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            font-weight: 700;
            font-size: 0.85rem;
        }
        .diagnostic-card .hypothesis-number.alt {
            background: #64748b;
        }
        .diagnostic-card .hypothesis-number.lesser {
            background: #94a3b8;
        }
        .interaction-badge.danger {
            background: #ef4444;
            color: white;
        }
        .interaction-badge.warning {
            background: #f59e0b;
            color: white;
        }
        .interaction-badge.info {
            background: #3b82f6;
            color: white;
        }
        .diagnostic-card .confidence-bar {
            width: 100%;
            height: 6px;
            background: #e2e8f0;
            border-radius: 3px;
            overflow: hidden;
        }
        .diagnostic-card .confidence-bar .fill {
            height: 100%;
            border-radius: 3px;
            transition: width 0.5s ease;
        }
        .diagnostic-card .confidence-bar .fill.high {
            background: #22c55e;
        }
        .diagnostic-card .confidence-bar .fill.medium {
            background: #f59e0b;
        }
        .diagnostic-card .confidence-bar .fill.low {
            background: #ef4444;
        }
        .diagnostic-card .diagnosis-name {
            font-size: 1.1rem;
            font-weight: 700;
            color: #0f172a;
        }
        .diagnostic-card .diagnosis-name.alt {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .diagnostic-card .diagnosis-name.alt strong {
            color: #64748b;
        }
        .diagnostic-card .diagnosis-name.lesser strong {
            color: #94a3b8;
        }
        .di