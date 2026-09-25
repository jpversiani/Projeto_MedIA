```html:backend/app/static/farmacia_dispensacao.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmácia Dispensação - UBS | Consulta e Baixa de Prescrição</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #0f172a; color: #e2e8f0; }
        .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(148, 163, 184, 0.1); }
        .glass-card { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(8px); border: 1px solid rgba(148, 163, 184, 0.08); }
        .glass-card:hover { border-color: rgba(148, 163, 184, 0.15); }
        .scan-ring { animation: pulse-ring 2s infinite; }
        @keyframes pulse-ring {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.05); opacity: 0.5; }
            100% { transform: scale(1); opacity: 1; }
        }
        .scan-ring::before {
            content: '';
            position: absolute;
            inset: -4px;
            border-radius: 50%;
            border: 2px solid #3b82f6;
            animation: rotate 1s linear infinite;
        }
        @keyframes rotate { to { transform: rotate(360deg); } }
        .scan-ring::after {
            content: '';
            position: absolute;
            inset: -8px;
            border-radius: 50%;
            border: 1px solid #3b82f6;
            animation: rotate 2s linear infinite reverse;
        }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }
        .scan-ring::before { animation: rotate 1s linear infinite; }
        .scan-ring::after { animation: rotate 2s linear infinite reverse; }