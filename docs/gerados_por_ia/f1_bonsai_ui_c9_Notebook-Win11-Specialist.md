```html:backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta — MedIA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            height: 100vh;
            overflow: hidden;
        }
        .glass-panel {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .glass-panel-light {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .glass-panel-dark {
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .glass-panel-card {
            background: rgba(30, 41, 59, 0.5);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {
            background: rgba(30, 41, 59, 0.7);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-card-hover:hover {