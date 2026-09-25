```html:backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta — SUS/APS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #0f172a; color: #e2e8f0; margin: 0; min-height: 100vh; }
        .glass {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.08);
        }
        .glass-panel {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(148, 163, 184, 0.06);
        }
        .glass-panel:hover { border-color: rgba(148, 163, 184, 0.12); }
        .glass-card {
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(6px);
            border: 1px solid rgba(148, 163, 184, 0.06);
        }
        .glass-card:hover { border-color: rgba(148, 163, 184, 0.12); }
        .glass-card.active {
            background: rgba(59, 130, 246, 0.15);
            border-color: rgba(59, 130, 246, 0.3);
        }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 0.4); }
        .glass-card.active:hover { background: rgba(59, 130, 246, 0.2); }
        .glass-card.active:hover { border-color: rgba(59, 130, 246, 