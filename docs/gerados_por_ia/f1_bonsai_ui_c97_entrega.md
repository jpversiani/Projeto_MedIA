```python:backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta — SUS/APS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            height: 100vh;
            overflow: hidden;
        }

        /* ── Header ── */
        .header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border-bottom: 1px solid #334155;
            padding: 0 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 64px;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .header-brand i {
            color: #38bdf8;
            font-size: 1.5rem;
        }

        .header-brand span {
            font-weight: 700;
            font-size: 1.1rem;
            letter-spacing: 0.02em;
        }

        .header-brand span small {
            display: block;
            font-size: 0.7rem;
            color: #94a3b8;
            font-weight: 400;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .header-actions button {
            background: transparent;
            border: 1px solid #334155;
            color: #94a3b8;
            padding: 0.4rem 0.75rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.2s;
        }

        .header-actions button:hover {
            background: #1e293b;
            color: #e2e8f0;
            border-color: #475569;
        }

        .header-actions button.active {
            background: #38bdf8;
            color: #0f172a;
            border-color: #38bdf8;
        }

        /* ── Main Layout ── */
        .main-layout {
            display: grid;
            grid-template-columns: 1fr 340px;
            grid-template-rows: auto 1fr;
            height: calc(100vh - 64px);
            gap: 0;
        }

        /* ── Video Grid ── */
        .video-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 1rem;
            padding: 1rem;
            background: #0f172a;
            position: relative;
        }

        .video-card {
            position: relative;
            aspect-ratio: 4/3;
            border-radius: 12px;
            overflow: hidden;
            background: #1e293b;
            border: 2px solid #334155;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        .video-card.active {
            border-color: #38bdf8;
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.15);
        }

        .video-card.active .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card .video-card