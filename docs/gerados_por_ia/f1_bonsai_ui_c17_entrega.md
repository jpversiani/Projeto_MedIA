```html:backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR" class="min-h-screen">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta - Sistema MedIA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #0a0a0f;
            color: #e2e8f0;
            overflow: hidden;
        }
        .glass-panel {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .glass-panel-hover:hover {
            background: rgba(15, 23, 42, 0.95);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass-panel-hover:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }
        .glass