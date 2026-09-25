```html:backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR" class="min-h-screen bg-gray-900">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta — MedIA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Inter+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #0a0a0f;
            color: #e2e8f0;
            overflow: hidden;
        }
        .glass {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.06);
        }
        .glass-panel {
            background: rgba(10, 15, 30, 0.92);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.05);
        }
        .glass-card {
            background: rgba(20, 28, 50, 0.7);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.04);
        }
        .glass-card:hover {
            border-color: rgba(255,255,255,0.1);
        }
        .glass-card.active {
            border-color: rgba(59, 130, 246, 0.3);
            background: rgba(30, 41, 79, 0.85);
        }
        .glass-card.active::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background: linear-gradient(to bottom, #3b82f6, #6366f1);
            border-radius: 3px 0 0 3px;
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover::before {
            width: 4px;
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .glass-card.active:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
       