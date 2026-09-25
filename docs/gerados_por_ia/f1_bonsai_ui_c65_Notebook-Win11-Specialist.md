```python
# Arquivo: backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta — MedIA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            overflow: hidden;
        }
        .glass-panel {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.08);
        }
        .glass-panel-hover:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel-hover:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel-hover:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel-hover:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(148, 163, 184, 0.15);
        }
        .glass-panel:hover {
            background: rgba(30